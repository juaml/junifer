"""Provide abstract base class for pattern-based datalad datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Optional

from ..api.decorators import register_datagrabber
from .datalad_base import DataladDataGrabber
from .pattern import PatternDataGrabber
from .utils import validate_patterns


@register_datagrabber
class PatternDataladDataGrabber(DataladDataGrabber, PatternDataGrabber):
    """Abstract base class for pattern-based data fetching via Datalad.

    Defines a DataGrabber that gets data from a datalad sibling,
    interpreting patterns.

    Parameters
    ----------
    types : list of str, optional
        The types of data to be grabbed (default None).
    patterns : dict, optional
        Patterns for each type of data as a dictionary. The keys are the types
        and the values are the patterns. Each occurrence of the string
        `{subject}` in the pattern will be replaced by the indexed element
        (default None).
    **kwargs
        Keyword arguments passed to superclass.

    See Also
    --------
    DataladDataGrabber
    PatternDataGrabber

    """

    def __init__(
        self,
        types: Optional[List[str]] = None,
        patterns: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> None:
        """Initialize the class."""
        # Validate patterns
        validate_patterns(types=types, patterns=patterns)

        super().__init__(types=types, patterns=patterns, **kwargs)
        self.patterns = patterns
