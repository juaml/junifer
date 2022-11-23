"""Provide class for AOMIC1000 VBM juseless datalad datagrabber."""

# Authors: Felix Hoffstaedter <f.hoffstaedter@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Union

from ....api.decorators import register_datagrabber
from ....datagrabber import PatternDataladDataGrabber


@register_datagrabber
class JuselessDataladAOMICID1000VBM(PatternDataladDataGrabber):
    """Juseless AOMICID1000 VBM Data Grabber class.

    Implements a Data Grabber to access the AOMICID1000 VBM data in Juseless.

    Parameters
    ----------
    datadir : str or pathlib.Path, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).

    """

    def __init__(self, datadir: Union[str, Path, None] = None) -> None:
        uri = "https://gin.g-node.org/felixh/ds003097_ReproVBM"
        types = ["VBM_GM"]
        replacements = ["subject"]
        patterns = {
            "VBM_GM": "sub-{subject}/mri/mwp1sub-{subject}_run-2_T1w.nii.gz",
        }
        super().__init__(
            types=types,
            datadir=datadir,
            uri=uri,
            replacements=replacements,
            patterns=patterns,
        )
