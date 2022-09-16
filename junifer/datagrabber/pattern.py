"""Provide concrete implementation for pattern-based datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import re
from typing import Dict, List, Tuple, Union

from ..api.decorators import register_datagrabber
from ..utils import logger, raise_error
from .base import BaseDataGrabber
from .utils import validate_patterns, validate_replacements


@register_datagrabber
class PatternDataGrabber(BaseDataGrabber):
    """Concrete implementation for data fetching using patterns.

    Implements a DataGrabber that understands patterns to grab data.

    Parameters
    ----------
    types : list of str
        The types of data to be grabbed (default None).
    patterns : dict
        Patterns for each type of data as a dictionary. The keys are the types
        and the values are the patterns. Each occurrence of the string
        `{subject}` in the pattern will be replaced by the indexed element.
    replacements: list of str
        Replacements in the patterns for each item in the "element" tuple.
    datadir : str or pathlib.Path
        The directory where the data is / will be stored.
    **kwargs
        Keyword arguments passed to superclass.

    See Also
    --------
    BaseDataGrabber

    """

    def __init__(
        self,
        types: List[str],
        patterns: Dict[str, str],
        replacements: List[str],
        **kwargs,
    ) -> None:
        """Initialize the class."""
        # Validate patterns
        validate_patterns(types=types, patterns=patterns)

        if not isinstance(replacements, list):
            replacements = [replacements]
        # Validate replacements
        validate_replacements(replacements=replacements, patterns=patterns)

        super().__init__(types=types, **kwargs)
        logger.debug("Initializing PatternDataGrabber")
        logger.debug(f"\tpatterns = {patterns}")
        logger.debug(f"\treplacements = {replacements}")
        self.patterns = patterns
        self.replacements = replacements

    def _replace_patterns_regex(self, pattern: str) -> Tuple[str, str]:
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

        """
        re_pattern = pattern
        glob_pattern = pattern
        for t_r in self.replacements:
            # Replace the first of each with a named group definition
            re_pattern = re_pattern.replace(f"{{{t_r}}}", f"(?P<{t_r}>.*)", 1)

        for t_r in self.replacements:
            # Replace the second appearance of each with the named group
            # back reference
            re_pattern = re_pattern.replace(f"{{{t_r}}}", f"(?P={t_r})")

        for t_r in self.replacements:
            glob_pattern = glob_pattern.replace(f"{{{t_r}}}", "*")
        return re_pattern, glob_pattern

    def _replace_patterns_glob(self, element: Tuple, pattern: str) -> str:
        """Replace patterns with the element so it can be globbed.

        Parameters
        ----------
        element : tuple
            The element to be used in the replacement.
        pattern : str
            The pattern to be replaced.

        Returns
        -------
        str
            The pattern with the element replaced.

        """
        if len(element) != len(self.replacements):
            raise_error(
                f"The element length must be {len(self.replacements)}, "
                f"indicating {self.replacements}."
            )
        to_replace = dict(zip(self.replacements, element))
        return pattern.format(**to_replace)

    def __getitem__(self, element: Union[str, Tuple]) -> Dict[str, Dict]:
        """Implement single element indexing in the database.

        Each occurrence of the strings in "replacements" is replaced by the
        corresponding item in the element tuple.

        Parameters
        ----------
        element : str or tuple
            The element to be indexed. If one string is provided, it is
            assumed to be a tuple with only one item. If a tuple is provided,
            each item in the tuple is the value for the replacement string
            specified in "replacements".

        Returns
        -------
        dict
            Dictionary of dictionaries for each type of data required for the
            specified element.

        """
        out = super().__getitem__(element)
        if not isinstance(element, tuple):
            element = (element,)
        for t_type in self.types:
            t_pattern = self.patterns[t_type]
            t_replace = self._replace_patterns_glob(element, t_pattern)
            if "*" in t_replace:
                t_matches = list(self.datadir.glob(t_replace))
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
                if not t_out.exists():
                    raise_error(
                        f"Cannot access {t_type} for {element}: "
                        f"File {t_out} does not exist"
                    )
            out[t_type] = {"path": t_out}
        # Meta here is element and types
        out["meta"]["element"] = dict(zip(self.replacements, element))
        return out

    def get_elements(self) -> List:
        """Implement fetching list of elements in the dataset.

        It will use regex to search for "replacements" in the "patterns" and
        return the intersection of the results for each type i.e., build a
        list of elements that have all the required types.

        Returns
        -------
        elements : list
            The list of elements that can be grabbed in the dataset. Each
            element is a subject in the BIDS database.

        """
        elements = None
        for t_type in self.types:
            types_element = set()
            # Get the pattern
            t_pattern = self.patterns[t_type]
            # Replace the pattern
            re_pattern, glob_pattern = self._replace_patterns_regex(t_pattern)
            for fname in self.datadir.glob(glob_pattern):
                suffix = fname.relative_to(self.datadir).as_posix()
                m = re.match(re_pattern, suffix)
                if m is not None:
                    t_element = tuple(m.group(k) for k in self.replacements)
                    if len(self.replacements) == 1:
                        t_element = t_element[0]
                    types_element.add(t_element)
            # TODO: does this make sense as elements is always None
            if elements is None:
                elements = types_element
            else:
                elements = elements.intersection(types_element)
        if elements is None:
            elements = set()
        return list(elements)
