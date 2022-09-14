"""Provide concrete implementations for HCP data access."""

# from itertools import product
from pathlib import Path
from typing import Union

from junifer.datagrabber import PatternDataladDataGrabber

from ..api.decorators import register_datagrabber


@register_datagrabber
class DataladAOMIC1000(PatternDataladDataGrabber):
    """Concrete implementation for pattern-based data fetching of AOMIC1000.

    Parameters
    ----------
    datadir : str or Path, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    tasks : {"moviewatching"} AOMIC 1000 tasks.
        If None, moviewatching is selected.
        (default None).
    **kwargs
        Keyword arguments passed to superclass.

    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
        # tasks: Union[str, List[str], None] = None,
        **kwargs,
    ) -> None:

        # The types of data
        types = [
            "BOLD",
            "BOLD_confounds",
            "ANAT",
            "ANAT_probseg_CSF",
            "ANAT_probseg_GM",
            "ANAT_probseg_WM",
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
            "ANAT": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_"
                "desc-preproc_T1w.nii.gz"
            ),
            "ANAT_probseg_CSF": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_label-"
                "CSF_probseg.nii.gz"
            ),
            "ANAT_probseg_GM": (
                "derivatives/fmriprep/sub-{subject}/anat/"
                "sub-{subject}_space-MNI152NLin2009cAsym_label-"
                "GM_probseg.nii.gz"
            ),
            "ANAT_probseg_WM": (
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
        )
