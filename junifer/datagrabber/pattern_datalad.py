"""Provide concrete implementation for pattern + datalad based DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pydantic import ConfigDict

from ..api.decorators import register_datagrabber
from ..utils import logger
from .datalad_base import DataladDataGrabber
from .pattern import PatternDataGrabber


__all__ = ["PatternDataladDataGrabber"]


@register_datagrabber
class PatternDataladDataGrabber(DataladDataGrabber, PatternDataGrabber):
    """Concrete implementation for pattern and datalad based data fetching.

    Implements a DataGrabber that gets data from a datalad sibling,
    interpreting patterns.

    Parameters
    ----------
    uri : pydantic.AnyUrl
        URI of the datalad sibling.
    types : enum:`.DataType` or list of variants
        The data type(s) to grab.
    patterns : ``DataGrabberPatterns``
        The datagrabber patterns. Check :class:`DataTypeSchema` for the schema.
    replacements : list of str
        All possible replacements in ``patterns.<data_type>.pattern``.
    rootdir : pathlib.Path, optional
        The path within the datalad dataset to the root directory
        (default Path(".")).
    confounds_format : :enum:`.ConfoundsFormat` or None, optional
        The format of the confounds for the dataset (default None).
    datadir : pathlib.Path, optional
        That path where the datalad dataset will be cloned.
        If not specified, the datalad dataset will be cloned into a temporary
        directory.


    See Also
    --------
    DataladDataGrabber:
        Abstract base class for datalad-based data fetching.
    PatternDataGrabber:
        Concrete implementation for pattern-based data fetching.

    """

    model_config = ConfigDict(extra="allow")

    def validate_datagrabber_params(self) -> None:
        """Run extra logical validation for datagrabber."""
        super().validate_datagrabber_params()
        logger.debug("Initializing PatternDataladDataGrabber")
        for key, val in self.__pydantic_extra__.items():
            logger.debug(f"\t{key} = {val}")
