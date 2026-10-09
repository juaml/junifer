"""Provide concrete implementation for pattern-based DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import glob
import re
from collections import defaultdict
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import ClassVar

from aenum import Enum as AEnum
from aenum import extend_enum
from pydantic import Field

from ..api.decorators import register_datagrabber
from ..typing import DataGrabberPatterns, Elements
from ..utils import ensure_list, raise_error
from .base import BaseDataGrabber, logger
from .pattern_validation_mixin import PatternValidationMixin


__all__ = [
    "ConfoundsFormat",
    "PatternDataGrabber",
    "register_confounds_format",
]


class ConfoundsFormat(str, AEnum):
    """Accepted confounds format."""

    FMRIPrep = "fmriprep"
    AdHoc = "adhoc"


def register_confounds_format(name: str, alias: str) -> None:
    """Register custom confounds format.

    Parameters
    ----------
    name : str
        The confounds format name to be referred.
    alias : str
        The confounds format alias for string representation.

    """
    extend_enum(ConfoundsFormat, name, alias)


def _value(value: object) -> object:
    """Get the value of an enum member, or the value itself.

    Parameters
    ----------
    value : object
        The value.

    Returns
    -------
    object
        The value.

    """
    return value.value if isinstance(value, Enum) else value


def _join_elements(
    left: set[tuple[str, ...]],
    left_keys: list[str],
    right: set[tuple[str, ...]],
    right_keys: list[str],
) -> tuple[set[tuple[str, ...]], list[str]]:
    """Join two sets of elements on their common keys.

    Each data type (or pattern) has its own elements, with the values of the
    replacements in its pattern. The elements of the datagrabber are the ones
    available for all the data types, so the elements of two data types are
    joined like database tables: an element of the first set is combined with
    each element of the second set that has the same values for the common
    keys, adding the values of the keys that only the second set has. An
    element without a match in the other set is dropped.

    For example, with BOLD elements ``(subject, session, task)``:
    ``(sub-01, ses-1, rest)``, ``(sub-01, ses-1, movie)`` and
    ``(sub-02, ses-1, rest)``:

    * VBM elements ``(subject)``: ``(sub-01)`` and ``(sub-03)`` keep the BOLD
      elements of ``sub-01``, as the VBM data only depends on the subject.
    * DWI elements ``(subject, run)``: ``(sub-01, 1)`` and ``(sub-01, 2)``
      give the elements ``(subject, session, task, run)`` for each BOLD
      element of ``sub-01`` with each run, i.e., all the combinations.

    The result is the same regardless of which set is first (except for the
    order of the keys), so the order of the data types does not matter.

    Parameters
    ----------
    left : set of tuple of str
        The first elements, as tuples of the values of ``left_keys``.
    left_keys : list of str
        The keys of the first elements.
    right : set of tuple of str
        The second elements, as tuples of the values of ``right_keys``.
    right_keys : list of str
        The keys of the second elements.

    Returns
    -------
    set of tuple of str
        The elements with the values of the first and the second elements that
        have the same values for the common keys.
    list of str
        The keys of the elements: ``left_keys`` and the other ``right_keys``.

    """
    common = [k for k in right_keys if k in left_keys]
    other = [i for i, k in enumerate(right_keys) if k not in left_keys]
    # Values of the other keys of the second elements, by the common values
    right_by_common = defaultdict(list)
    for element in right:
        common_values = tuple(element[right_keys.index(k)] for k in common)
        right_by_common[common_values].append(tuple(element[i] for i in other))
    joined = {
        element + other_values
        for element in left
        for other_values in right_by_common[
            tuple(element[left_keys.index(k)] for k in common)
        ]
    }
    return joined, left_keys + [right_keys[i] for i in other]


@register_datagrabber
class PatternDataGrabber(BaseDataGrabber, PatternValidationMixin):
    """Concrete implementation for pattern-based data fetching.

    Implements a DataGrabber that understands patterns to grab data.

    Parameters
    ----------
    types : :enum:`.DataType` or list of variants
        The data type(s) to grab.
    datadir : pathlib.Path
        The path where the data is stored.
    patterns : ``DataGrabberPatterns``
        The datagrabber patterns. Check :class:`.DataTypeSchema` for the \
        schema.
    replacements : list of str or dict
        All possible replacements in ``patterns.<data_type>.pattern``. As a
        dictionary, the keys are the replacements and the values are the lists
        of values to grab (or None to grab all of them), e.g.,
        ``{"subject": None, "task": ["rest", "movie"]}`` to grab all the
        subjects and only these tasks.
    confounds_format : :enum:`.ConfoundsFormat` or None, optional
        The format of the confounds for the dataset (default None).
    partial_pattern_ok : bool, optional
        Whether to raise error if partial pattern for a data type is found.
        This allows to bypass mandatory key check and issue a warning
        instead of raising error. This allows one to have a DataGrabber
        with data types without the corresponding mandatory keys and is
        powerful when used with :class:`.MultipleDataGrabber`
        (default True).

    Attributes
    ----------
    skip_file_check

    """

    patterns: DataGrabberPatterns = Field(frozen=True)
    replacements: list[str] | dict[str, list[str] | None] = Field(frozen=True)

    # Fields with the values of the replacements to grab, by replacement, e.g.,
    # ``{"task": "tasks"}``
    _REPLACEMENT_FIELDS: ClassVar[dict[str, str]] = {}
    confounds_format: ConfoundsFormat | None = Field(None, frozen=True)
    partial_pattern_ok: bool = Field(False, frozen=True)

    def validate_datagrabber_params(self) -> None:
        """Run extra logical validation for datagrabber."""
        # Validate patterns
        self.validate_patterns(
            types=self.types,
            replacements=list(self.replacements),
            patterns=self.patterns,
            partial_pattern_ok=self.partial_pattern_ok,
        )
        # Validate the fields with the values of the replacements
        for replacement, field in self._REPLACEMENT_FIELDS.items():
            if replacement not in self.replacements:
                raise_error(
                    msg=(
                        f"Replacement: `{replacement}` of the field `{field}` "
                        f"is not one of the replacements: "
                        f"{list(self.replacements)}"
                    ),
                    klass=ValueError,
                )
            if (
                isinstance(self.replacements, dict)
                and self.replacements[replacement] is not None
            ):
                raise_error(
                    msg=(
                        f"The values of the replacement `{replacement}` are "
                        f"given by the field `{field}`, they cannot be given "
                        "in `replacements`"
                    ),
                    klass=ValueError,
                )
        logger.debug("Initializing PatternDataGrabber")
        logger.debug(f"\tpatterns = {self.patterns}")
        logger.debug(f"\treplacements = {self.replacements}")
        logger.debug(f"\tconfounds_format = {self.confounds_format}")

    @property
    def skip_file_check(self) -> bool:
        """Skip file check existence."""
        return False

    def _replace_patterns_regex(
        self, pattern: str
    ) -> tuple[str, str, list[str]]:
        """Replace the patterns in ``pattern`` with the named groups.

        It allows elements to be obtained from the filesystem.

        Parameters
        ----------
        pattern : str
            The pattern to be replaced.

        Returns
        -------
        re_pattern : str
            The regular expression with the named groups.
        glob_pattern : str
            The search pattern to be used with glob.
        replacements : list of str
            The replacements present in the pattern.

        """
        re_pattern = pattern
        glob_pattern = pattern
        t_replacements = [
            x for x in self.replacements if f"{{{x}}}" in pattern
        ]
        # Ops on re_pattern
        # Remove negated unix glob pattern i.e., [!...] for re_pattern, as the
        # character is part of the following replacement (e.g., [!f]{subject})
        re_pattern = re.sub(r"\[!.?\]", "", re_pattern)
        # Remove enclosing square brackets from unix glob pattern i.e., [...]
        # for re_pattern
        re_pattern = re.sub(r"\[|\]", "", re_pattern)
        # Translate the replacements to named groups (the first appearance of
        # each) or back references (the others), the unix glob wildcards to
        # their regular expressions and escape the rest
        parts = []
        seen = set()
        for token in re.split(r"(\{[^{}]*\}|\*|\?)", re_pattern):
            name = token[1:-1]
            if token.startswith("{") and name in t_replacements:
                if name in seen:
                    parts.append(f"(?P={name})")
                else:
                    parts.append(f"(?P<{name}>.*)")
                    seen.add(name)
            elif token == "*":
                parts.append("[^/]*")
            elif token == "?":
                parts.append("[^/]")
            else:
                parts.append(re.escape(token))
        re_pattern = "".join(parts)
        # Ops on glob_pattern
        # Iteratively replace replacements with wildcard i.e., *
        # for glob_pattern
        for t_r in t_replacements:
            glob_pattern = glob_pattern.replace(f"{{{t_r}}}", "*")

        return re_pattern, glob_pattern, t_replacements

    def _replace_patterns_glob(self, element: dict, pattern: str) -> str:
        """Replace ``pattern`` with the ``element`` so it can be globbed.

        Parameters
        ----------
        element : dict
            The element to be used in the replacement.
        pattern : str
            The pattern to be replaced.

        Returns
        -------
        str
            The pattern with the element replaced.

        Raises
        ------
        ValueError
            If element keys do not match with replacements.

        """
        if list(element.keys()) != self.get_element_keys():
            raise_error(
                f"The element keys must be {self.get_element_keys()}, "
                f"element has {list(element.keys())}."
            )
        # Remove negated unix glob pattern i.e., [!...]
        pattern = re.sub(r"\[!.?\]", "", pattern)
        # Remove enclosing square brackets from unix glob pattern i.e., [...]
        pattern = re.sub(r"\[|\]", "", pattern)
        return pattern.format(**element)

    def _get_path_from_patterns(
        self, element: dict, pattern: str, data_type: str
    ) -> Path:
        """Get path from resolved patterns.

        Parameters
        ----------
        element : dict
            The element to be used in the replacement.
        pattern : str
            The pattern to be replaced.
        data_type : str
            The data type of the pattern.

        Returns
        -------
        pathlib.Path
            The path for the resolved pattern.

        Raises
        ------
        RuntimeError
            If more than one file matches for a data type's pattern or
            if no file matches for a data type's pattern or
            if file cannot be accessed for an element.

        """
        # Replace element in the pattern for globbing
        resolved_pattern = self._replace_patterns_glob(element, pattern)
        # Resolve path for wildcards
        if "*" in resolved_pattern or "?" in resolved_pattern:
            # glob.glob (unlike pathlib before Python 3.12) also matches the
            # broken symbolic links, e.g., the files of a DataLad dataset that
            # are not downloaded yet.
            # TODO: go back to Path.glob once Python 3.11 is dropped (end of
            # life in October 2027)
            fulldir = self.fulldir.absolute()
            t_matches = [
                fulldir / x
                for x in glob.glob(resolved_pattern, root_dir=fulldir)
            ]
            # Multiple matches
            if len(t_matches) > 1:
                raise_error(
                    f"More than one file matches for {element} / {data_type}:"
                    f" {t_matches}",
                    klass=RuntimeError,
                )
            # No matches
            elif len(t_matches) == 0:
                raise_error(
                    f"No file matches for {element} / {data_type}",
                    klass=RuntimeError,
                )
            path = t_matches[0]
        else:
            # Absolute path, as for the patterns with wildcards
            path = self.fulldir.absolute() / resolved_pattern
            if not self.skip_file_check:
                if not path.exists() and not path.is_symlink():
                    raise_error(
                        f"Cannot access {data_type} for {element}: "
                        f"File {path} does not exist",
                        klass=RuntimeError,
                    )

        return path

    def _get_type_patterns(self, data_type: str) -> list[str]:
        """Get the patterns of a data type, including the nested ones.

        Parameters
        ----------
        data_type : str
            The data type.

        Returns
        -------
        list of str
            The patterns.

        """
        dtype_val = self.patterns[data_type]
        # Conditional for list dtype vals like Warp
        if not isinstance(dtype_val, list):
            dtype_val = [dtype_val]
        patterns = []
        for val in dtype_val:
            if "pattern" in val:
                patterns.append(val["pattern"])
            patterns.extend(
                v["pattern"]
                for v in val.values()
                if isinstance(v, dict) and "pattern" in v
            )
        return patterns

    def get_element_keys(self) -> list[str]:
        """Get element keys.

        For each item in the "element" tuple, this functions returns the
        corresponding key, that is, the ``replacements`` of the patterns of
        the data types to grab (e.g., without ``task`` if only anatomical
        data types are grabbed).

        Returns
        -------
        list of str
            The element keys.

        """
        patterns = [
            pattern
            for t_type in self.get_types()
            for pattern in self._get_type_patterns(t_type)
        ]
        return [
            x
            for x in self.replacements
            if any(f"{{{x}}}" in pattern for pattern in patterns)
        ]

    def get_replacement_values(self) -> dict[str, list[str]]:
        """Get the values of the replacements to grab.

        The values are given by ``replacements`` (as a dictionary) or by the
        fields of the replacements (see ``_REPLACEMENT_FIELDS``).

        Returns
        -------
        dict
            The lists of values of the replacements to grab, by replacement.
            The replacements without values (to grab all of them) are not
            included.

        """
        values = {}
        if isinstance(self.replacements, dict):
            values = {
                k: list(v)
                for k, v in self.replacements.items()
                if v is not None
            }
        for replacement, field in self._REPLACEMENT_FIELDS.items():
            field_values = getattr(self, field)
            if field_values is not None:
                values[replacement] = [
                    _value(x) for x in ensure_list(field_values)
                ]
        return values

    def _check_element(self, element: dict) -> None:
        """Check the element has values of the replacements to grab.

        Parameters
        ----------
        element : dict
            The element, as given to :meth:`.get_item`.

        Raises
        ------
        ValueError
            If a value of the element is not one of the values to grab.

        """
        for key, values in self.get_replacement_values().items():
            if key in element and _value(element[key]) not in values:
                raise_error(
                    msg=(
                        f"The value `{element[key]}` of `{key}` is not one of "
                        f"the values to grab: {values}"
                    ),
                    klass=ValueError,
                )

    def get_item(self, **element: dict) -> dict[str, dict]:
        """Get the specified item from the dataset.

        This method constructs a real path to the requested item's data, by
        replacing the ``patterns`` with actual values passed via ``**element``.

        Parameters
        ----------
        element : dict
            The element to be indexed. The keys must be the same as the
            replacements.

        Returns
        -------
        dict
            Dictionary of dictionaries for each type of data required for the
            specified element.

        """
        out = {}
        for t_type in self.types:
            # Data type dictionary
            t_pattern = self.patterns[t_type]
            # Copy data type dictionary in output
            out[t_type] = deepcopy(t_pattern)
            # Conditional for list dtype vals like Warp
            if isinstance(t_pattern, list):
                for idx, entry in enumerate(t_pattern):
                    logger.info(
                        f"Resolving path from pattern for {t_type}.{idx}"
                    )
                    # Resolve pattern
                    dtype_pattern_path = self._get_path_from_patterns(
                        element=element,
                        pattern=entry["pattern"],
                        data_type=f"{t_type}.{idx}",
                    )
                    # Remove pattern key
                    out[t_type][idx].pop("pattern")
                    # Add path key
                    out[t_type][idx].update({"path": dtype_pattern_path})
            else:
                # Iterate to check for nested "types" like mask
                for k, v in t_pattern.items():
                    # Resolve pattern for base data type
                    if k == "pattern":
                        logger.info(
                            f"Resolving path from pattern for {t_type}"
                        )
                        # Resolve pattern
                        base_dtype_pattern_path = self._get_path_from_patterns(
                            element=element,
                            pattern=v,
                            data_type=t_type,
                        )
                        # Remove pattern key
                        out[t_type].pop("pattern")
                        # Add path key
                        out[t_type].update({"path": base_dtype_pattern_path})
                    # Resolve pattern for nested data type
                    if isinstance(v, dict) and "pattern" in v:
                        # Set nested type key for easier access
                        t_nested_type = f"{t_type}.{k}"
                        logger.info(
                            f"Resolving path from pattern for {t_nested_type}"
                        )
                        # Resolve pattern
                        nested_dtype_pattern_path = (
                            self._get_path_from_patterns(
                                element=element,
                                pattern=v["pattern"],
                                data_type=t_nested_type,
                            )
                        )
                        # Remove pattern key
                        out[t_type][k].pop("pattern")
                        # Add path key
                        out[t_type][k].update(
                            {"path": nested_dtype_pattern_path}
                        )

        return out

    def get_elements(self) -> Elements:
        """Implement fetching list of elements in the dataset.

        It will use regex to search for "replacements" in the "patterns" and
        join the results for each type on their common replacements i.e.,
        build a list of elements that have all the required types.

        Returns
        -------
        list
            The list of elements that can be grabbed in the dataset.

        """
        # The elements found so far, as tuples of the values of `keys`
        elements = None
        keys = []
        for t_type in self.get_types():
            # Data type dictionary
            patterns = self.patterns[t_type]
            # Conditional for list dtype vals like Warp
            if not isinstance(patterns, list):
                patterns = [patterns]
            for t_pattern in patterns:
                # Conditional fetch of base pattern for getting elements
                pattern = None
                # Try for data type pattern
                pattern = t_pattern.get("pattern")
                # Try for nested data type pattern
                if pattern is None and self.partial_pattern_ok:
                    for v in t_pattern.values():
                        if isinstance(v, dict) and "pattern" in v:
                            pattern = v["pattern"]
                            break

                # Find the elements of the pattern
                (
                    re_pattern,
                    glob_pattern,
                    t_keys,
                ) = self._replace_patterns_regex(pattern)
                t_elements = set()
                # glob.glob (unlike pathlib before Python 3.12) also matches
                # the broken symbolic links, e.g., the files of a DataLad
                # dataset that are not downloaded yet.
                # TODO: go back to Path.glob once Python 3.11 is dropped (end
                # of life in October 2027)
                for fname in glob.glob(glob_pattern, root_dir=self.fulldir):
                    suffix = Path(fname).as_posix()
                    m = re.match(re_pattern, suffix)
                    if m is not None:
                        t_elements.add(tuple(m.group(k) for k in t_keys))
                # Keep the elements with the values to grab
                replacement_values = self.get_replacement_values()
                restricted = [
                    (i, set(replacement_values[k]))
                    for i, k in enumerate(t_keys)
                    if k in replacement_values
                ]
                t_elements = {
                    element
                    for element in t_elements
                    if all(element[i] in values for i, values in restricted)
                }
                # Keep the elements available for all the data types
                if elements is None:
                    elements, keys = t_elements, t_keys
                else:
                    elements, keys = _join_elements(
                        elements, keys, t_elements, t_keys
                    )
        if elements is None:
            return []
        # Sort the values as the element keys
        element_keys = self.get_element_keys()
        idx = [keys.index(k) for k in element_keys]
        out = sorted(tuple(element[i] for i in idx) for element in elements)
        if len(element_keys) == 1:
            out = [element[0] for element in out]
        return out
