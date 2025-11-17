"""Provide concrete implementation for IXI VBM DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from enum import Enum
from typing import Literal

from pydantic import HttpUrl

from ....api.decorators import register_datagrabber
from ....datagrabber import DataType, PatternDataladDataGrabber
from ....typing import DataGrabberPatterns


__all__ = ["IXISite", "JuselessDataladIXIVBM"]


class IXISite(str, Enum):
    """Accepted IXI sites."""

    Guys = "Guys"
    HH = "HH"
    IOP = "IOP"


@register_datagrabber
class JuselessDataladIXIVBM(PatternDataladDataGrabber):
    """Concrete implementation for Juseless IXI VBM data fetching.

    Implements a DataGrabber to access the IXI VBM data in Juseless.

    Parameters
    ----------
    datadir : pathlib.Path, optional
        That path where the datalad dataset will be cloned.
        If not specified, the datalad dataset will be cloned into a temporary
        directory.
    sites : list of :obj:`IXISite`, optional
        IXI sites.
        By default, all available sites are selected.

    """

    uri: HttpUrl = (
        "ria+http://cat_12.5.ds.inm7.de#b7107c52-8408-11ea-89c6-a0369f287950"
    )
    types: list[Literal[DataType.VBM_GM]] = [DataType.VBM_GM]  # noqa: RUF012
    sites: list[IXISite] = [IXISite.Guys, IXISite.HH, IXISite.IOP]  # noqa: RUF012
    patterns: DataGrabberPatterns = {  # noqa: RUF012
        "VBM_GM": {
            "pattern": ("{site}/{subject}/mri/m0wp1{subject}.nii.gz"),
            "space": "IXI549Space",
        },
    }
    replacements: list[str] = ["site", "subject"]  # noqa: RUF012
