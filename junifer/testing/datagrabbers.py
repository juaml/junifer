"""Testing DataGrabbers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import tempfile
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

import nibabel as nib
import numpy as np
from nilearn import datasets, image

from ..datagrabber import BaseDataGrabber, DataType


__all__ = [
    "ADHDTestingDataGrabber",
    "OasisVBMTestingDataGrabber",
    "PartlyCloudyAgeGroup",
    "PartlyCloudyTestingDataGrabber",
    "SPMAuditoryTestingDataGrabber",
]


def _save_atomic(out_path: Path, save: Callable[[Path], None]) -> None:
    """Save a file by writing to a temporary file and renaming it.

    Concurrent test workers never read a partially written file.

    Parameters
    ----------
    out_path : pathlib.Path
        The path to save to.
    save : callable
        Function that writes the file to the path it is given.

    """
    tmp_path = out_path.with_name(f".{uuid4().hex}.{out_path.name}")
    save(tmp_path)
    tmp_path.replace(out_path)


class OasisVBMTestingDataGrabber(BaseDataGrabber):
    """DataGrabber for Oasis VBM testing data.

    Wrapper for :func:`nilearn.datasets.fetch_oasis_vbm`.

    """

    types: list[DataType] = [DataType.VBM_GM]  # noqa: RUF012
    datadir: Path = Path(tempfile.mkdtemp())
    _dataset: Any = None

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

    Parameters
    ----------
    n_timepoints : int or None, optional
        The number of BOLD timepoints to keep. If None, all the 96
        timepoints are kept (default None).

    """

    types: list[DataType] = [DataType.BOLD, DataType.T1w]  # noqa: RUF012
    datadir: Path = Path(tempfile.mkdtemp())
    n_timepoints: int | None = None

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
        # Each BOLD volume is a separate file, so keep only the ones needed
        fmri_img = image.concat_imgs(nilearn_data.func[: self.n_timepoints])
        anat_img = image.concat_imgs(nilearn_data.anat)

        tp_suffix = (
            f"_tp-{self.n_timepoints}" if self.n_timepoints is not None else ""
        )
        fmri_fname = self.datadir / f"{subject}{tp_suffix}_bold.nii.gz"
        anat_fname = self.datadir / f"{subject}_T1w.nii.gz"
        nib.save(fmri_img, fmri_fname)
        nib.save(anat_img, anat_fname)
        out["BOLD"] = {"path": fmri_fname, "space": "MNI152Lin"}
        out["T1w"] = {"path": anat_fname, "space": "native"}
        return out


class PartlyCloudyAgeGroup(str, Enum):
    """Age group to fetch.

    * ``Adult`` : fetch adults only (n=33, ages 18-39)
    * ``Child`` : fetch children only (n=122, ages 3-12)
    * ``Both`` : fetch full sample (n=155)

    """

    Adult = "adult"
    Child = "child"
    Both = "both"


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
       Age group to fetch (default ``PartlyCloudyAgeGroup.Both``).
    n_timepoints : int or None, optional
        The number of timepoints to keep. The truncated BOLD images and
        confounds are cached next to the original files in the nilearn data
        directory. If None, all the 168 timepoints are kept (default None).

    """

    types: list[DataType] = [DataType.BOLD]  # noqa: RUF012
    datadir: Path = Path(tempfile.mkdtemp())
    reduce_confounds: bool = True
    age_group: PartlyCloudyAgeGroup = PartlyCloudyAgeGroup.Both
    n_timepoints: int | None = None

    def __enter__(self) -> "PartlyCloudyTestingDataGrabber":
        """Implement context entry.

        Returns
        -------
        PartlyCloudyTestingDataGrabber

        """
        self._dataset = datasets.fetch_development_fmri(
            n_subjects=10,
            reduce_confounds=self.reduce_confounds,
            age_group=self.age_group.value
            if isinstance(self.age_group, Enum)
            else self.age_group,
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
        bold_path = Path(self._dataset["func"][i_sub])
        confounds_path = Path(self._dataset["confounds"][i_sub])
        if self.n_timepoints is not None:
            bold_path, confounds_path = self._truncate(
                bold_path, confounds_path
            )
        out["BOLD"] = {
            "path": bold_path,
            "space": "MNI152NLin2009cAsym",
            "confounds": {
                "path": confounds_path,
                "format": "fmriprep",
            },
        }

        return out

    def _truncate(
        self, bold_path: Path, confounds_path: Path
    ) -> tuple[Path, Path]:
        """Truncate the BOLD image and confounds to ``n_timepoints``.

        The truncated files are cached next to the original ones, so they
        are computed only once.

        Parameters
        ----------
        bold_path : pathlib.Path
            The path to the original BOLD image.
        confounds_path : pathlib.Path
            The path to the original confounds file.

        Returns
        -------
        pathlib.Path
            The path to the truncated BOLD image.
        pathlib.Path
            The path to the truncated confounds file.

        """
        n_tp = self.n_timepoints
        img = nib.load(bold_path)
        if n_tp >= img.shape[3]:
            return bold_path, confounds_path

        # Store uncompressed so it can be memory-mapped
        out_bold = bold_path.with_name(
            bold_path.name.replace("_bold.nii.gz", f"_tp-{n_tp}_bold.nii")
        )
        if not out_bold.exists():
            # Keep the raw values and the original scaling; letting nibabel
            # rescale the subset would re-quantize the data
            truncated = nib.Nifti1Image(
                np.asanyarray(img.dataobj.get_unscaled())[..., :n_tp],
                img.affine,
                img.header,
            )
            truncated.header.set_slope_inter(
                img.dataobj.slope, img.dataobj.inter
            )
            _save_atomic(out_bold, lambda x: nib.save(truncated, x))

        out_confounds = confounds_path.with_name(
            confounds_path.name.replace(
                "_regressors.tsv", f"_tp-{n_tp}_regressors.tsv"
            )
        )
        if not out_confounds.exists():
            # Copy the header and the first rows verbatim
            lines = confounds_path.read_text().splitlines(keepends=True)
            _save_atomic(
                out_confounds,
                lambda x: x.write_text("".join(lines[: n_tp + 1])),
            )
        return out_bold, out_confounds


class ADHDTestingDataGrabber(BaseDataGrabber):
    """DataGrabber for ADHD dataset.

    Wrapper for :func:`nilearn.datasets.fetch_adhd`. The BOLD images are
    truncated to the first ``n_timepoints``, resampled to the requested
    resolution on the MNI152NLin6Asym (FSL) grid and cached (uncompressed)
    next to the original files in the nilearn data directory.

    Parameters
    ----------
    resolution : float, optional
        The resolution (in mm) of the BOLD images. The original data is in
        3mm (default 2.0).
    n_timepoints : int or None, optional
        The number of timepoints to keep. If None, all the 176 timepoints
        are kept (default 50).

    """

    types: list[DataType] = [DataType.BOLD]  # noqa: RUF012
    datadir: Path = Path(tempfile.mkdtemp())
    resolution: float = 2.0
    n_timepoints: int | None = 50

    def __enter__(self) -> "ADHDTestingDataGrabber":
        """Implement context entry.

        Returns
        -------
        ADHDTestingDataGrabber

        """
        self._dataset = datasets.fetch_adhd(n_subjects=10)
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
            "path": self._get_bold(Path(self._dataset["func"][i_sub])),
            "space": "MNI152NLin6Asym",
        }

        return out

    def _get_bold(self, path: Path) -> Path:
        """Get the BOLD image truncated and resampled as requested.

        The resulting image is cached next to the original one, so it is
        computed only once.

        Parameters
        ----------
        path : pathlib.Path
            The path to the original BOLD image.

        Returns
        -------
        pathlib.Path
            The path to the BOLD image.

        """
        res = self.resolution
        n_tp = self.n_timepoints
        # FSL MNI152 grid: x is flipped and the bounding box is
        # 180 x 216 x 180 mm, with the origin at (90, -126, -72)
        target_affine = np.array(
            [
                [-res, 0, 0, 90],
                [0, res, 0, -126],
                [0, 0, res, -72],
                [0, 0, 0, 1],
            ]
        )
        target_shape = (
            round(180 / res) + 1,
            round(216 / res) + 1,
            round(180 / res) + 1,
        )
        img = nib.load(path)
        needs_resample = img.shape[:3] != target_shape or not np.allclose(
            img.affine, target_affine
        )
        needs_truncate = n_tp is not None and n_tp < img.shape[3]
        # Original data is already as requested
        if not needs_resample and not needs_truncate:
            return path

        # Store uncompressed so it can be memory-mapped; otherwise every
        # load decompresses the whole file again
        tp_suffix = f"_tp-{n_tp}" if needs_truncate else ""
        out_path = path.with_name(
            path.name.replace(".nii.gz", f"_res-{res:g}mm{tp_suffix}.nii")
        )
        if not out_path.exists():
            if needs_truncate:
                img = img.slicer[..., :n_tp]
            if needs_resample:
                tr = img.header.get_zooms()[3]
                img = image.resample_img(
                    img,
                    target_affine=target_affine,
                    target_shape=target_shape,
                    interpolation="continuous",
                )
                # Resampling creates a new header, so restore the TR
                img.header.set_zooms((res, res, res, tr))
                img.header.set_xyzt_units(xyz="mm", t="sec")
            img.set_data_dtype(np.float32)
            _save_atomic(out_path, lambda x: nib.save(img, x))
        return out_path
