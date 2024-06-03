"""Provide concrete implementation for UKB VBM DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Union

from ....api.decorators import register_datagrabber
from ....datagrabber import PatternDataladDataGrabber


__all__ = ["JuselessDataladUKBVBM"]


@register_datagrabber
class JuselessDataladUKBVBM(PatternDataladDataGrabber):
    """Concrete implementation for Juseless UKB VBM data fetching.

    Implements a DataGrabber to access the UKB VBM data in Juseless.

    Parameters
    ----------
    datadir : str or pathlib.Path or None, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).

    """

    def __init__(self, datadir: Union[str, Path, None] = None) -> None:
        uri = "ria+http://ukb.ds.inm7.de#~cat_m0wp1"
        rootdir = "m0wp1"
        types = ["VBM_GM"]
        replacements = ["subject", "session"]
        patterns = {
            "VBM_GM": {
                "pattern": "m0wp1{subject}_ses-{session}_T1w.nii.gz",
                "space": "IXI549Space",
            },
        }
        super().__init__(
            types=types,
            datadir=datadir,
            uri=uri,
            rootdir=rootdir,
            replacements=replacements,
            patterns=patterns,
        )
