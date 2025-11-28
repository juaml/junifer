"""Provide concrete implementation for CamCAN VBM DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Literal

from pydantic import AnyUrl

from ....api.decorators import register_datagrabber
from ....datagrabber import DataType, PatternDataladDataGrabber
from ....typing import DataGrabberPatterns


__all__ = ["JuselessDataladCamCANVBM"]


@register_datagrabber
class JuselessDataladCamCANVBM(PatternDataladDataGrabber):
    """Concrete implementation for Juseless CamCAN VBM data fetching.

    Implements a DataGrabber to access the CamCAN VBM data in Juseless.

    Parameters
    ----------
    datadir : pathlib.Path, optional
        That path where the datalad dataset will be cloned.
        If not specified, the datalad dataset will be cloned into a temporary
        directory.

    """

    uri: AnyUrl = AnyUrl(
        "ria+http://cat_12.5.ds.inm7.de#a139b26a-8406-11ea-8f94-a0369f287950"
    )
    types: list[Literal[DataType.VBM_GM]] = [DataType.VBM_GM]  # noqa: RUF012
    patterns: DataGrabberPatterns = {  # noqa: RUF012
        "VBM_GM": {
            "pattern": "{subject}/mri/m0wp1{subject}.nii.gz",
            "space": "IXI549Space",
        },
    }
    replacements: list[str] = ["subject"]  # noqa: RUF012
