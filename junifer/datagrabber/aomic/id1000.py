"""Provide concrete implementation for AOMIC ID1000 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Dict, Union

from ...api.decorators import register_datagrabber
from ..pattern_datalad import PatternDataladDataGrabber


@register_datagrabber
class DataladAOMICID1000(PatternDataladDataGrabber):
    """Concrete implementation for datalad-based data fetching of AOMIC ID1000.

    Parameters
    ----------
    datadir : str or Path or None, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).

    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
    ) -> None:
        # The types of data
        types = [
            "BOLD",
            "BOLD_confounds",
            "BOLD_mask",
            "T1w",
            "T1w_mask",
            "probseg_CSF",
            "probseg_GM",
            "probseg_WM",
            "DWI",
        ]
        # The patterns
        patterns = {
            "BOLD": (
                "derivatives/fmriprep/sub-{subject}/func/"
                "sub-{subject}_task-moviewatching_"
                "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
            ),
            "BOLD_confounds": (
                "derivatives/fmriprep/sub-{subject}/func/"
                "sub-{subject}_task-moviewatching_"
                "desc-confounds_regressors.tsv"
            ),
            "BOLD_mask": (
                "derivatives/fmriprep/sub-{subject}/func/"
                "sub-{subject}_task-moviewatching_"
                "space-MNI152NLin2009cAsym_"
                "desc-brain_mask.nii.gz"
            ),
            "T1w": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_"
                "desc-preproc_T1w.nii.gz"
            ),
            "T1w_mask": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_"
                "desc-brain_mask.nii.gz"
            ),
            "probseg_CSF": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_label-"
                "CSF_probseg.nii.gz"
            ),
            "probseg_GM": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_label-"
                "GM_probseg.nii.gz"
            ),
            "probseg_WM": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_label-"
                "WM_probseg.nii.gz"
            ),
            "DWI": (
                "derivatives/dwipreproc/sub-{subject}/dwi/"
                "sub-{subject}_desc-preproc_dwi.nii.gz"
            ),
        }
        # The replacements
        replacements = ["subject"]
        uri = "https://github.com/OpenNeuroDatasets/ds003097.git"
        super().__init__(
            types=types,
            datadir=datadir,
            uri=uri,
            patterns=patterns,
            replacements=replacements,
            confounds_format="fmriprep",
        )

    def get_item(self, subject: str) -> Dict:
        """Index one element in the dataset.

        Parameters
        ----------
        subject : str
            The subject ID.

        Returns
        -------
        out : dict
            Dictionary of paths for each type of data required for the
            specified element.

        """
        out = super().get_item(subject=subject)
        out["BOLD"]["mask_item"] = "BOLD_mask"
        out["T1w"]["mask_item"] = "T1w_mask"
        return out
