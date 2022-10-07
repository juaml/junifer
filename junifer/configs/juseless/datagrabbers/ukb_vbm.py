"""Provide class for juseless datalad datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import List, Union

from ....api.decorators import register_datagrabber
from ....datagrabber import PatternDataladDataGrabber


@register_datagrabber
class JuselessDataladUKBVBM(PatternDataladDataGrabber):
    """Juseless UKB VBM DataGrabber class.

    Implements a DataGrabber to access the UKB VBM data in Juseless.

    Parameters
    -----------
    datadir : str or pathlib.Path, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).

    """

    def __init__(self, datadir: Union[str, Path, None] = None) -> None:
        """Initialize the class."""
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


@register_datagrabber
class JuselessDataladCamCANVBM(PatternDataladDataGrabber):
    """Juseless CamCAN VBM DataGrabber class.

    Implements a DataGrabber to access the CamCAN VBM data in Juseless.

    Parameters
    -----------
    datadir : str or pathlib.Path, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).

    """

    def __init__(self, datadir: Union[str, Path, None] = None) -> None:
        """Initialize the class."""
        uri = "git@jugit.fz-juelich.de:inm7/datasets/datasets_repo.git"
        types = ["VBM_GM"]
        rootdir = "processed/cat_12.5/CamCAN"
        replacements = ["subject"]
        patterns = {"VBM_GM": "sub-{subject}/mri/m0wp1sub-{subject}.nii.gz"}
        super().__init__(
            types=types,
            datadir=datadir,
            uri=uri,
            rootdir=rootdir,
            replacements=replacements,
            patterns=patterns,
        )

    def get_elements(self) -> List:
        """Implement fetching list of subjects in the dataset.

        Returns
        -------
        elements : list of str
            The list of subjects in the dataset.

        """
        self._dataset.get(self.datadir, get_data=False, source="inm7-storage")
        return [x.as_posix().split("-")[1] for x in self.datadir.glob("sub-*")]
