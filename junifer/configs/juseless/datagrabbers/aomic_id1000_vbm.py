"""Provide concrete implementation for AOMIC ID1000 VBM DataGrabber."""

# Authors: Felix Hoffstaedter <f.hoffstaedter@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Literal

from pydantic import HttpUrl

from ....api.decorators import register_datagrabber
from ....datagrabber import DataType, PatternDataladDataGrabber
from ....typing import DataGrabberPatterns


__all__ = ["JuselessDataladAOMICID1000VBM"]


@register_datagrabber
class JuselessDataladAOMICID1000VBM(PatternDataladDataGrabber):
    """Concrete implementation for Juseless AOMIC ID1000 VBM data fetching.

    Implements a DataGrabber to access the AOMIC ID1000 VBM data in Juseless.

    Parameters
    ----------
    datadir : pathlib.Path, optional
        That path where the datalad dataset will be cloned.
        If not specified, the datalad dataset will be cloned into a temporary
        directory.

    """

    uri: HttpUrl = HttpUrl("https://gin.g-node.org/felixh/ds003097_ReproVBM")
    types: list[Literal[DataType.VBM_GM]] = [DataType.VBM_GM]  # noqa: RUF012
    patterns: DataGrabberPatterns = {  # noqa: RUF012
        "VBM_GM": {
            "pattern": ("{subject}/mri/mwp1{subject}_run-2_T1w.nii.gz"),
            "space": "IXI549Space",
        },
    }
    replacements: list[str] = ["subject"]  # noqa: RUF012
