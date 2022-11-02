"""Provide base class for pattern-based datalad datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List

from ..api.decorators import register_datagrabber
from .datalad_base import DataladDataGrabber
from .pattern import PatternDataGrabber
from .utils import validate_patterns


@register_datagrabber
class PatternDataladDataGrabber(DataladDataGrabber, PatternDataGrabber):
    """Base class for pattern-based data fetching via Datalad.

    Defines a DataGrabber that gets data from a datalad sibling,
    interpreting patterns.

    Parameters
    ----------
    types : list of str
        The types of data to be grabbed.
    patterns : dict, optional
        Patterns for each type of data as a dictionary. The keys are the types
        and the values are the patterns. Each occurrence of the string
        `{subject}` in the pattern will be replaced by the indexed element
        (default None).
    **kwargs
        Keyword arguments passed to superclass.

    See Also
    --------
    DataladDataGrabber:
        Base class for data fetching via Datalad.
    PatternDataGrabber:
        Base class for pattern-based data fetching.
    """

    def __init__(
        self,
        types: List[str],
        patterns: Dict[str, str],
        **kwargs,
    ) -> None:
        # Validate patterns
        validate_patterns(types=types, patterns=patterns)

        super().__init__(types=types, patterns=patterns, **kwargs)
        self.patterns = patterns
