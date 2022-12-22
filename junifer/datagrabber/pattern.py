"""Provide concrete implementation for pattern-based datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from ..api.decorators import register_datagrabber
from ..utils import logger, raise_error
from .base import BaseDataGrabber
from .utils import validate_patterns, validate_replacements


# Accepted formats for confounds specification
_CONFOUNDS_FORMATS = ("fmriprep", "adhoc")


@register_datagrabber
class PatternDataGrabber(BaseDataGrabber):
    """Concrete implementation for data grabbing using patterns.

    Implements a Data Grabber that understands patterns to grab data.

    Parameters
    ----------
    types : list of str
        The types of data to be grabbed (default None).
    patterns : dict
        Patterns for each type of data as a dictionary. The keys are the types
        and the values are the patterns. Each occurrence of the string
        `{subject}` in the pattern will be replaced by the indexed element.
    replacements : list of str
        Replacements in the patterns for each item in the "element" tuple.
    datadir : str or pathlib.Path
        The directory where the data is / will be stored.
    confounds_format : {"fmriprep", "adhoc"}, optional
        The format of the confounds for the dataset (default None).

    """

    def __init__(
        self,
        types: List[str],
        patterns: Dict[str, str],
        replacements: Union[List[str], str],
        datadir: Union[str, Path],
        confounds_format: Optional[str] = None,
    ) -> None:
        # Validate patterns
        validate_patterns(types=types, patterns=patterns)

        if not isinstance(replacements, list):
            replacements = [replacements]
        # Validate replacements
        validate_replacements(replacements=replacements, patterns=patterns)

        # Validate confounds format
        if confounds_format and confounds_format not in _CONFOUNDS_FORMATS:
            raise_error(
                "Invalid value for `confounds_format`, should be one of "
                f"{_CONFOUNDS_FORMATS}."
            )
        self.confounds_format = confounds_format

        super().__init__(types=types, datadir=datadir)
        logger.debug("Initializing PatternDataGrabber")
        logger.debug(f"\tpatterns = {patterns}")
        logger.debug(f"\treplacements = {replacements}")
        self.patterns = patterns
        self.replacements = replacements

    @property
    def skip_file_check(self) -> bool:
        """Skip file check existence."""
        return False

    def _replace_patterns_regex(
        self, pattern: str
    ) -> Tuple[str, str, List[str]]:
        """Replace the patterns in `pattern` with the named groups.

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

        for t_r in t_replacements:
            # Replace the first of each with a named group definition
            re_pattern = re_pattern.replace(f"{{{t_r}}}", f"(?P<{t_r}>.*)", 1)

        for t_r in t_replacements:
            # Replace the second appearance of each with the named group
            # back reference
            re_pattern = re_pattern.replace(f"{{{t_r}}}", f"(?P={t_r})")

        for t_r in t_replacements:
            glob_pattern = glob_pattern.replace(f"{{{t_r}}}", "*")
        return re_pattern, glob_pattern, t_replacements

    def _replace_patterns_glob(self, element: Dict, pattern: str) -> str:
        """Replace patterns with the element so it can be globbed.

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

        """
        if list(element.keys()) != self.replacements:
            raise_error(
                f"The element keys must be {self.replacements}, "
                f"element has {list(element.keys())}."
            )
        return pattern.format(**element)

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
        """Implement single element indexing in the database.

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
            t_pattern = self.patterns[t_type]
            t_replace = self._replace_patterns_glob(element, t_pattern)
            if "*" in t_replace:
                t_matches = list(self.datadir.absolute().glob(t_replace))
                if len(t_matches) > 1:
                    raise_error(
                        f"More than one file matches for {element} / {t_type}:"
                        f" {t_matches}"
                    )
                elif len(t_matches) == 0:
                    raise_error(f"No file matches for {element} / {t_type}")
                t_out = t_matches[0]
            else:
                t_out = self.datadir / t_replace
                if not self.skip_file_check:
                    if not t_out.exists() and not t_out.is_symlink():
                        raise_error(
                            f"Cannot access {t_type} for {element}: "
                            f"File {t_out} does not exist"
                        )
            # Update path for the element
            out[t_type] = {"path": t_out}
            # Update confounds format for BOLD_confounds
            # (if found in the datagrabber)
            if t_type == "BOLD_confounds":
                if not self.confounds_format:
                    raise_error(
                        "`confounds_format` needs to be one of "
                        f"{_CONFOUNDS_FORMATS}, None provided. "
                        "As the datagrabber used specifies "
                        "'BOLD_confounds', None is invalid."
                    )
                # Set the format
                out[t_type].update({"format": self.confounds_format})

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
            ) = self._replace_patterns_regex(t_pattern)
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
