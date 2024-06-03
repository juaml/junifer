"""Provide concrete implementation for AOMIC ID1000 VBM DataGrabber."""

# Authors: Felix Hoffstaedter <f.hoffstaedter@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Union

from ....api.decorators import register_datagrabber
from ....datagrabber import PatternDataladDataGrabber


__all__ = ["JuselessDataladAOMICID1000VBM"]


@register_datagrabber
class JuselessDataladAOMICID1000VBM(PatternDataladDataGrabber):
    """Concrete implementation for Juseless AOMIC ID1000 VBM data fetching.

    Implements a DataGrabber to access the AOMIC ID1000 VBM data in Juseless.

    Parameters
    ----------
    datadir : str or pathlib.Path or None, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).

    """

    def __init__(self, datadir: Union[str, Path, None] = None) -> None:
        uri = "https://gin.g-node.org/felixh/ds003097_ReproVBM"
        types = ["VBM_GM"]
        replacements = ["subject"]
        patterns = {
            "VBM_GM": {
                "pattern": ("{subject}/mri/mwp1{subject}_run-2_T1w.nii.gz"),
                "space": "IXI549Space",
            },
        }
        super().__init__(
            types=types,
            datadir=datadir,
            uri=uri,
            replacements=replacements,
            patterns=patterns,
        )
