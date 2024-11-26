"""Testing DataGrabbers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import tempfile
from pathlib import Path

import nibabel as nib
from nilearn import datasets, image

from ..datagrabber.base import BaseDataGrabber


__all__ = [
    "OasisVBMTestingDataGrabber",
    "PartlyCloudyTestingDataGrabber",
    "SPMAuditoryTestingDataGrabber",
]


class OasisVBMTestingDataGrabber(BaseDataGrabber):
    """DataGrabber for Oasis VBM testing data.

    Wrapper for :func:`nilearn.datasets.fetch_oasis_vbm`.

    """

    def __init__(self) -> None:
        # Create temporary directory
        datadir = tempfile.mkdtemp()
        # Define types
        types = ["VBM_GM"]
        super().__init__(types=types, datadir=datadir)

    def get_element_keys(self) -> list[str]:
        """Get element keys.

        Returns
        -------
        list of str
            The element keys.

        """
        return ["subject"]

    def get_item(self, subject: str) -> dict[str, dict]:
        """Implement indexing support.

        Parameters
        ----------
        subject : str
            The subject to retrieve.

        Returns
        -------
        dict
            The data along with the metadata.

        """
        out = {}
        i_sub = int(subject.split("-")[1]) - 1
        out["VBM_GM"] = {
            "path": Path(self._dataset.gray_matter_maps[i_sub]),
            "space": "MNI152Lin",
        }

        return out

    def __enter__(self) -> "OasisVBMTestingDataGrabber":
        """Implement context entry.

        Returns
        -------
        OasisVBMTestingDataGrabber

        """
        self._dataset = datasets.fetch_oasis_vbm(n_subjects=10)
        return self

    def get_elements(self) -> list[str]:
        """Get elements.

        Returns
        -------
        list of str
            List of elements that can be grabbed.

        """
        return [f"sub-{x:02d}" for x in list(range(1, 11))]


class SPMAuditoryTestingDataGrabber(BaseDataGrabber):
    """DataGrabber for SPM Auditory dataset.

    Wrapper for :func:`nilearn.datasets.fetch_spm_auditory`.

    """

    def __init__(self) -> None:
        # Create temporary directory
        datadir = tempfile.mkdtemp()
        # Define types
        types = ["BOLD", "T1w"]  # TODO: Check that they are T1w
        super().__init__(types=types, datadir=datadir)

    def get_element_keys(self) -> list[str]:
        """Get element keys.

        Returns
        -------
        list of str
            The element keys.

        """
        return ["subject"]

    def get_elements(self) -> list[str]:
        """Get elements.

        Returns
        -------
        list of str
            List of elements that can be grabbed.

        """
        return [f"sub{x:03d}" for x in list(range(1, 11))]

    def get_item(self, subject: str) -> dict[str, dict]:
        """Implement indexing support.

        Parameters
        ----------
        subject : str
            The subject to retrieve.

        Returns
        -------
        dict
            The data along with the metadata.

        """
        out = {}
        nilearn_data = datasets.fetch_spm_auditory(subject_id=subject)
        fmri_img = image.concat_imgs(nilearn_data.func)  # type: ignore
        anat_img = image.concat_imgs(nilearn_data.anat)  # type: ignore

        fmri_fname = self.datadir / f"{subject}_bold.nii.gz"
        anat_fname = self.datadir / f"{subject}_T1w.nii.gz"
        nib.save(fmri_img, fmri_fname)
        nib.save(anat_img, anat_fname)
        out["BOLD"] = {"path": fmri_fname, "space": "MNI152Lin"}
        out["T1w"] = {"path": anat_fname, "space": "native"}
        return out


class PartlyCloudyTestingDataGrabber(BaseDataGrabber):
    """DataGrabber for Partly Cloudy dataset.

    Wrapper for :func:`nilearn.datasets.fetch_development_fmri`.

    Parameters
    ----------
    reduce_confounds : bool, optional
        If True, the returned confounds only include 6 motion parameters,
        mean framewise displacement, signal from white matter, csf, and
        6 anatomical compcor parameters. This selection only serves the
        purpose of having realistic examples. Depending on your research
        question, other confounds might be more appropriate.
        If False, returns all :term:`fMRIPrep` confounds (default True).

    age_group : {"adult", "child", "both"}, optional
       Which age group to fetch:

        * ``adult`` : fetch adults only (n=33, ages 18-39)
        * ``child`` : fetch children only (n=122, ages 3-12)
        * ``both`` : fetch full sample (n=155)

        (default "both")

    """

    def __init__(
        self, reduce_confounds: bool = True, age_group: str = "both"
    ) -> None:
        """Initialize the class."""
        datadir = tempfile.mkdtemp()
        # Define types
        types = ["BOLD"]
        self.reduce_confounds = reduce_confounds
        self.age_group = age_group
        super().__init__(types=types, datadir=datadir)

    def __enter__(self) -> "PartlyCloudyTestingDataGrabber":
        """Implement context entry.

        Returns
        -------
        PartlyCloudyTestingDataGrabber

        """
        self._dataset = datasets.fetch_development_fmri(
            n_subjects=10,
            reduce_confounds=self.reduce_confounds,
            age_group=self.age_group,
        )
        return self

    def get_element_keys(self) -> list[str]:
        """Get element keys.

        Returns
        -------
        list of str
            The element keys.

        """
        return ["subject"]

    def get_elements(self) -> list[str]:
        """Get elements.

        Returns
        -------
        list of str
            List of elements that can be grabbed.

        """
        return [f"sub-{x:02d}" for x in list(range(1, 11))]

    def get_item(self, subject: str) -> dict[str, dict]:
        """Implement indexing support.

        Parameters
        ----------
        subject : str
            The subject to retrieve.

        Returns
        -------
        dict
            The data along with the metadata.

        """
        out = {}
        i_sub = int(subject.split("-")[1]) - 1
        out["BOLD"] = {
            "path": Path(self._dataset["func"][i_sub]),
            "space": "MNI152NLin2009cAsym",
            "confounds": {
                "path": Path(self._dataset["confounds"][i_sub]),
                "format": "fmriprep",
            },
        }

        return out
