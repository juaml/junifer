"""Provide testing datagrabbers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import tempfile
from typing import Dict, List

from nilearn import datasets, image
import nibabel as nib

from ..datagrabber.base import BaseDataGrabber


class OasisVBMTestingDatagrabber(BaseDataGrabber):
    """DataGrabber for Oasis VBM testing data."""

    def __init__(self) -> None:
        """Initialize the class."""
        # Create temporary directory
        datadir = tempfile.mkdtemp()
        # Define types
        types = ["VBM_GM"]
        super().__init__(types=types, datadir=datadir)

    def __getitem__(self, element: str) -> Dict:
        """Implement indexing support.

        Parameters
        ----------
        element : str
            The element to retrieve.

        Returns
        -------
        dict
            The data along with the metadata.

        """
        out = super().__getitem__(element)
        i_sub = int(element.split("-")[1]) - 1
        out["VBM_GM"] = {"path": self._dataset.gray_matter_maps[i_sub]}
        # Set the element accordingly
        out["meta"]["element"] = {"subject": element}
        return out

    def __enter__(self) -> "OasisVBMTestingDatagrabber":
        """Implement context entry.

        Returns
        -------
        OasisVBMTestingDatagrabber

        """
        self._dataset = datasets.fetch_oasis_vbm(n_subjects=10)
        return self

    def get_elements(self) -> List[str]:
        """Get elements.

        Returns
        -------
        list of str
            List of elements that can be grabbed.

        """
        return [f"sub-{x:02d}" for x in list(range(1, 11))]


class SPMAuditoryTestingDatagrabber(BaseDataGrabber):
    """DataGrabber for SPM Auditory dataset.

    Wrapper for nilearn.datasets.fetch_spm_auditory
    """

    def __init__(self) -> None:
        """Initialize the class."""
        # Create temporary directory
        datadir = tempfile.mkdtemp()
        # Define types
        types = ["BOLD", "T1w"]  # TODO: Check that they are T1w
        super().__init__(types=types, datadir=datadir)

    def get_elements(self) -> List[str]:
        """Get elements.

        Returns
        -------
        list of str
            List of elements that can be grabbed.

        """
        return [f"sub{x:03d}" for x in list(range(1, 11))]

    def __getitem__(self, element: str) -> Dict:
        """Implement indexing support.

        Parameters
        ----------
        element : str
            The element to retrieve.

        Returns
        -------
        dict
            The data along with the metadata.

        """
        out = super().__getitem__(element)

        nilearn_data = datasets.fetch_spm_auditory(subject_id=element)
        fmri_img = image.concat_imgs(nilearn_data.func)  # type: ignore
        anat_img = image.concat_imgs(nilearn_data.anat)  # type: ignore

        fmri_fname = self.datadir / f"{element}_bold.nii.gz"
        anat_fname = self.datadir / f"{element}_T1w.nii.gz"
        nib.save(fmri_img, fmri_fname)
        nib.save(anat_img, anat_fname)
        out["BOLD"] = {"path": fmri_fname}
        out["T1w"] = {"path": anat_fname}
        # Set the element accordingly
        out["meta"]["element"] = {"subject": element}
        return out
