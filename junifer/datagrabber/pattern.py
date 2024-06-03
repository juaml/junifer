"""Provide concrete implementation for pattern-based DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import re
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from ..api.decorators import register_datagrabber
from ..utils import logger, raise_error
from .base import BaseDataGrabber
from .utils import validate_patterns, validate_replacements


__all__ = ["PatternDataGrabber"]


# Accepted formats for confounds specification
_CONFOUNDS_FORMATS = ("fmriprep", "adhoc")


@register_datagrabber
class PatternDataGrabber(BaseDataGrabber):
    """Concrete implementation for pattern-based data fetching.

    Implements a DataGrabber that understands patterns to grab data.

    Parameters
    ----------
    types : list of str
        The types of data to be grabbed.
    patterns : dict
        Data type patterns as a dictionary. It has the following schema:

        * ``"T1w"`` :

          .. code-block:: none

            {
              "mandatory": ["pattern", "space"],
              "optional": {
                  "mask": {
                      "mandatory": ["pattern", "space"],
                      "optional": []
                  }
              }
            }

        * ``"T2w"`` :

          .. code-block:: none

            {
              "mandatory": ["pattern", "space"],
              "optional": {
                  "mask": {
                      "mandatory": ["pattern", "space"],
                      "optional": []
                  }
              }
            }

        * ``"BOLD"`` :

          .. code-block:: none

            {
              "mandatory": ["pattern", "space"],
              "optional": {
                  "mask": {
                      "mandatory": ["pattern", "space"],
                      "optional": []
                  }
                  "confounds": {
                      "mandatory": ["pattern", "format"],
                      "optional": []
                  }
              }
            }

        * ``"Warp"`` :

          .. code-block:: none

            {
              "mandatory": ["pattern", "src", "dst"],
              "optional": []
            }

        * ``"VBM_GM"`` :

          .. code-block:: none

            {
              "mandatory": ["pattern", "space"],
              "optional": []
            }

        * ``"VBM_WM"`` :

          .. code-block:: none

            {
              "mandatory": ["pattern", "space"],
              "optional": []
            }

        Basically, for each data type, one needs to provide ``mandatory`` keys
        and can choose to also provide ``optional`` keys. The value for each
        key is a string. So, one needs to provide necessary data types as a
        dictionary, for example:

        .. code-block:: none

          {
              "BOLD": {
                "pattern": "...",
                "space": "...",
              },
              "T1w": {
                "pattern": "...",
                "space": "...",
              },
              "Warp": {
                "pattern": "...",
                "src": "...",
                "dst": "...",
              }
          }

        taken from :class:`.HCP1200`.
    replacements : str or list of str
        Replacements in the ``pattern`` key of each data type. The value needs
        to be a list of all possible replacements.
    datadir : str or pathlib.Path
        The directory where the data is / will be stored.
    confounds_format : {"fmriprep", "adhoc"} or None, optional
        The format of the confounds for the dataset (default None).

    Raises
    ------
    ValueError
        If ``confounds_format`` is invalid.

    """

    def __init__(
        self,
        types: List[str],
        patterns: Dict[str, Dict[str, str]],
        replacements: Union[List[str], str],
        datadir: Union[str, Path],
        confounds_format: Optional[str] = None,
    ) -> None:
        # Validate patterns
        validate_patterns(types=types, patterns=patterns)
        self.patterns = patterns

        # Convert replacements to list if not already
        if not isinstance(replacements, list):
            replacements = [replacements]
        # Validate replacements
        validate_replacements(replacements=replacements, patterns=patterns)
        self.replacements = replacements

        # Validate confounds format
        if (
            confounds_format is not None
            and confounds_format not in _CONFOUNDS_FORMATS
        ):
            raise_error(
                "Invalid value for `confounds_format`, should be one of "
                f"{_CONFOUNDS_FORMATS}."
            )
        self.confounds_format = confounds_format

        super().__init__(types=types, datadir=datadir)
        logger.debug("Initializing PatternDataGrabber")
        logger.debug(f"\tpatterns = {patterns}")
        logger.debug(f"\treplacements = {replacements}")
        logger.debug(f"\tconfounds_format = {confounds_format}")

    @property
    def skip_file_check(self) -> bool:
        """Skip file check existence."""
        return False

    def _replace_patterns_regex(
        self, pattern: str
    ) -> Tuple[str, str, List[str]]:
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
        # Remove negated unix glob pattern i.e., [!...] for re_pattern
        re_pattern = re.sub(r"\[!.?\]", "", re_pattern)
        # Remove enclosing square brackets from unix glob pattern i.e., [...]
        # for re_pattern
        re_pattern = re.sub(r"\[|\]", "", re_pattern)
        # Iteratively replace the first of each with a named group definition
        for t_r in t_replacements:
            re_pattern = re_pattern.replace(f"{{{t_r}}}", f"(?P<{t_r}>.*)", 1)
        # Iteratively replace the second appearance of each with the named
        # group back reference
        for t_r in t_replacements:
            re_pattern = re_pattern.replace(f"{{{t_r}}}", f"(?P={t_r})")
        # Ops on glob_pattern
        # Iteratively replace replacements with wildcard i.e., *
        # for glob_pattern
        for t_r in t_replacements:
            glob_pattern = glob_pattern.replace(f"{{{t_r}}}", "*")

        return re_pattern, glob_pattern, t_replacements

    def _replace_patterns_glob(self, element: Dict, pattern: str) -> str:
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
        if list(element.keys()) != self.replacements:
            raise_error(
                f"The element keys must be {self.replacements}, "
                f"element has {list(element.keys())}."
            )
        # Remove negated unix glob pattern i.e., [!...]
        pattern = re.sub(r"\[!.?\]", "", pattern)
        # Remove enclosing square brackets from unix glob pattern i.e., [...]
        pattern = re.sub(r"\[|\]", "", pattern)
        return pattern.format(**element)

    def _get_path_from_patterns(
        self, element: Dict, pattern: str, data_type: str
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
        # Resolve path for wildcard
        if "*" in resolved_pattern:
            t_matches = list(self.datadir.absolute().glob(resolved_pattern))
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
            path = self.datadir / resolved_pattern
            if not self.skip_file_check:
                if not path.exists() and not path.is_symlink():
                    raise_error(
                        f"Cannot access {data_type} for {element}: "
                        f"File {path} does not exist",
                        klass=RuntimeError,
                    )

        return path

    def get_element_keys(self) -> List[str]:
        """Get element keys.

        For each item in the "element" tuple, this functions returns the
        corresponding key, that is, the ``replacements`` of patterns defined
        in the constructor.

        Returns
        -------
        list of str
            The element keys.

        """
        return self.replacements

    def get_item(self, **element: str) -> Dict[str, Dict]:
        """Implement single element indexing for the datagrabber.

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
            # Iterate to check for nested "types" like mask
            for k, v in t_pattern.items():
                # Resolve pattern for base data type
                if k == "pattern":
                    logger.info(f"Resolving path from pattern for {t_type}")
                    # Resolve pattern
                    base_data_type_pattern_path = self._get_path_from_patterns(
                        element=element,
                        pattern=v,
                        data_type=t_type,
                    )
                    # Remove pattern key
                    out[t_type].pop("pattern")
                    # Add path key
                    out[t_type].update({"path": base_data_type_pattern_path})
                # Resolve pattern for nested data type
                if isinstance(v, dict) and "pattern" in v:
                    # Set nested type key for easier access
                    t_nested_type = f"{t_type}.{k}"
                    logger.info(
                        f"Resolving path from pattern for {t_nested_type}"
                    )
                    # Resolve pattern
                    nested_data_type_pattern_path = (
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
                        {"path": nested_data_type_pattern_path}
                    )

        return out

    def get_elements(self) -> List:
        """Implement fetching list of elements in the dataset.

        It will use regex to search for "replacements" in the "patterns" and
        return the intersection of the results for each type i.e., build a
        list of elements that have all the required types.

        Returns
        -------
        list
            The list of elements that can be grabbed in the dataset.

        """
        elements = None

        # Iterate by number of replacements. At least one pattern must have
        # all of them.
        replacement_in_patterns = [
            np.sum([x in self.patterns[t_type] for x in self.replacements])
            for t_type in self.types
        ]
        order = np.argsort(replacement_in_patterns)

        # Start from the one with the most replacements and then
        # filter out elements based on the ones with less replacements.
        for t_idx in reversed(order):
            t_type = self.types[t_idx]
            types_element = set()
            # Get the pattern
            t_pattern = self.patterns[t_type]
            # Replace the pattern
            (
                re_pattern,
                glob_pattern,
                t_replacements,
            ) = self._replace_patterns_regex(t_pattern["pattern"])
            for fname in self.datadir.glob(glob_pattern):
                suffix = fname.relative_to(self.datadir).as_posix()
                m = re.match(re_pattern, suffix)
                if m is not None:
                    # Find the groups of replacements present in the pattern
                    # If one replacement is not present, set it to None.
                    # We will take care of this in the intersection
                    t_element = tuple([m.group(k) for k in t_replacements])
                    if len(self.replacements) == 1:
                        t_element = t_element[0]
                    types_element.add(t_element)
            # TODO: does this make sense as elements is always None
            if elements is None:
                elements = types_element
            else:
                # Do the intersection by filtering out elements in which
                # the replacements are not None
                if t_replacements == self.replacements:
                    elements.intersection(types_element)
                else:
                    t_repl_idx = [
                        i
                        for i, v in enumerate(self.replacements)
                        if v in t_replacements
                    ]
                    new_elements = set()
                    for t_element in elements:
                        if (
                            tuple(np.array(t_element)[t_repl_idx])
                            in types_element
                        ):
                            new_elements.add(t_element)
                    elements = new_elements
        if elements is None:
            elements = set()
        return list(elements)
