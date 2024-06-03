"""Provide concrete implementation for CamCAN VBM DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Union

from ....api.decorators import register_datagrabber
from ....datagrabber import PatternDataladDataGrabber


__all__ = ["JuselessDataladCamCANVBM"]


@register_datagrabber
class JuselessDataladCamCANVBM(PatternDataladDataGrabber):
    """Concrete implementation for Juseless CamCAN VBM data fetching.

    Implements a DataGrabber to access the CamCAN VBM data in Juseless.

    Parameters
    ----------
    datadir : str or pathlib.Path or None, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).

    """

    def __init__(self, datadir: Union[str, Path, None] = None) -> None:
        uri = (
            "ria+http://cat_12.5.ds.inm7.de"
            "#a139b26a-8406-11ea-8f94-a0369f287950"
        )
        types = ["VBM_GM"]
        replacements = ["subject"]
        patterns = {
            "VBM_GM": {
                "pattern": "{subject}/mri/m0wp1{subject}.nii.gz",
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
