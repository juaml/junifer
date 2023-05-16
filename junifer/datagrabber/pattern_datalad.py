"""Provide concrete implementation for pattern + datalad based DataGrabber."""

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
    """Concrete implementation for pattern and datalad based data fetching.

    Implements a DataGrabber that gets data from a datalad sibling,
    interpreting patterns.

    Parameters
    ----------
    types : list of str
        The types of data to be grabbed.
    patterns : dict
        Patterns for each type of data as a dictionary. The keys are the types
        and the values are the patterns. Each occurrence of the string
        ``{subject}`` in the pattern will be replaced by the indexed element.
    **kwargs
        Keyword arguments passed to superclass.

    See Also
    --------
    DataladDataGrabber:
        Abstract base class for datalad-based data fetching.
    PatternDataGrabber:
        Concrete implementation for pattern-based data fetching.

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
