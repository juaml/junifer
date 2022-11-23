"""Provide class for CamCAN VBM juseless datalad datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Union

from ....api.decorators import register_datagrabber
from ....datagrabber import PatternDataladDataGrabber


@register_datagrabber
class JuselessDataladCamCANVBM(PatternDataladDataGrabber):
    """Juseless CamCAN VBM Data Grabber class.

    Implements a Data Grabber to access the CamCAN VBM data in Juseless.

    Parameters
    ----------
    datadir : str or pathlib.Path, optional
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
        patterns = {"VBM_GM": "sub-{subject}/mri/m0wp1sub-{subject}.nii.gz"}
        super().__init__(
            types=types,
            datadir=datadir,
            uri=uri,
            replacements=replacements,
            patterns=patterns,
        )
