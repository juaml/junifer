"""Provide concrete implementation for UKB VBM DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Literal

from pydantic import HttpUrl

from ....api.decorators import register_datagrabber
from ....datagrabber import DataType, PatternDataladDataGrabber
from ....typing import DataGrabberPatterns


__all__ = ["JuselessDataladUKBVBM"]


@register_datagrabber
class JuselessDataladUKBVBM(PatternDataladDataGrabber):
    """Concrete implementation for Juseless UKB VBM data fetching.

    Implements a DataGrabber to access the UKB VBM data in Juseless.

    Parameters
    ----------
    datadir : pathlib.Path, optional
        That path where the datalad dataset will be cloned.
        If not specified, the datalad dataset will be cloned into a temporary
        directory.

    """

    uri: HttpUrl = "ria+http://ukb.ds.inm7.de#~cat_m0wp1"
    rootdir: Path = Path("m0wp1")
    types: list[Literal[DataType.VBM_GM]] = [DataType.VBM_GM]  # noqa: RUF012
    patterns: DataGrabberPatterns = {  # noqa: RUF012
        "VBM_GM": {
            "pattern": "m0wp1{subject}_ses-{session}_T1w.nii.gz",
            "space": "IXI549Space",
        },
    }
    replacements: list[str] = ["subject", "session"]  # noqa: RUF012
