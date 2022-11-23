"""Provide class for juseless datalad datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Union

from ....api.decorators import register_datagrabber
from ....datagrabber import PatternDataladDataGrabber


@register_datagrabber
class JuselessDataladUKBVBM(PatternDataladDataGrabber):
    """Juseless UKB VBM Data Grabber class.

    Implements a Data Grabber to access the UKB VBM data in Juseless.

    Parameters
    ----------
    datadir : str or pathlib.Path, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).

    """

    def __init__(self, datadir: Union[str, Path, None] = None) -> None:
        uri = "ria+http://ukb.ds.inm7.de#~cat_m0wp1"
        rootdir = "m0wp1"
        types = ["VBM_GM"]
        replacements = ["subject", "session"]
        patterns = {"VBM_GM": "m0wp1sub-{subject}_ses-{session}_T1w.nii.gz"}
        super().__init__(
            types=types,
            datadir=datadir,
            uri=uri,
            rootdir=rootdir,
            replacements=replacements,
            patterns=patterns,
        )
