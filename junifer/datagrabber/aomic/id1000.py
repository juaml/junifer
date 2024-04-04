"""Provide concrete implementation for AOMIC ID1000 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import List, Union

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
    types: {"BOLD", "BOLD_confounds", "T1w", "VBM_CSF", "VBM_GM", \
           "VBM_WM", "DWI"} or a list of the options, optional
        AOMIC data types. If None, all available data types are selected.
        (default None).
    native_t1w : bool, optional
        Whether to use T1w in native space (default False).

    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
        types: Union[str, List[str], None] = None,
        native_t1w: bool = False,
    ) -> None:
        # The patterns
        patterns = {
            "BOLD": {
                "pattern": (
                    "derivatives/fmriprep/sub-{subject}/func/"
                    "sub-{subject}_task-moviewatching_"
                    "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
                "mask_item": "BOLD_mask",
            },
            "BOLD_confounds": {
                "pattern": (
                    "derivatives/fmriprep/sub-{subject}/func/"
                    "sub-{subject}_task-moviewatching_"
                    "desc-confounds_regressors.tsv"
                ),
                "format": "fmriprep",
            },
            "BOLD_mask": {
                "pattern": (
                    "derivatives/fmriprep/sub-{subject}/func/"
                    "sub-{subject}_task-moviewatching_"
                    "space-MNI152NLin2009cAsym_"
                    "desc-brain_mask.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
            },
            "T1w": {
                "pattern": (
                    "derivatives/fmriprep/sub-{subject}/anat/"
                    "sub-{subject}_space-MNI152NLin2009cAsym_"
                    "desc-preproc_T1w.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
                "mask_item": "T1w_mask",
            },
            "T1w_mask": {
                "pattern": (
                    "derivatives/fmriprep/sub-{subject}/anat/"
                    "sub-{subject}_space-MNI152NLin2009cAsym_"
                    "desc-brain_mask.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
            },
            "VBM_CSF": {
                "pattern": (
                    "derivatives/fmriprep/sub-{subject}/anat/"
                    "sub-{subject}_space-MNI152NLin2009cAsym_label-"
                    "CSF_probseg.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
            },
            "VBM_GM": {
                "pattern": (
                    "derivatives/fmriprep/sub-{subject}/anat/"
                    "sub-{subject}_space-MNI152NLin2009cAsym_label-"
                    "GM_probseg.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
            },
            "VBM_WM": {
                "pattern": (
                    "derivatives/fmriprep/sub-{subject}/anat/"
                    "sub-{subject}_space-MNI152NLin2009cAsym_label-"
                    "WM_probseg.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
            },
            "DWI": {
                "pattern": (
                    "derivatives/dwipreproc/sub-{subject}/dwi/"
                    "sub-{subject}_desc-preproc_dwi.nii.gz"
                ),
            },
        }
        # Use native T1w assets
        self.native_t1w = False
        if native_t1w:
            self.native_t1w = True
            patterns.update(
                {
                    "T1w": {
                        "pattern": (
                            "derivatives/fmriprep/sub-{subject}/anat/"
                            "sub-{subject}_desc-preproc_T1w.nii.gz"
                        ),
                        "space": "native",
                        "mask_item": "T1w_mask",
                    },
                    "T1w_mask": {
                        "pattern": (
                            "derivatives/fmriprep/sub-{subject}/anat/"
                            "sub-{subject}_desc-brain_mask.nii.gz"
                        ),
                        "space": "native",
                    },
                    "Warp": {
                        "pattern": (
                            "derivatives/fmriprep/sub-{subject}/anat/"
                            "sub-{subject}_from-MNI152NLin2009cAsym_to-T1w_"
                            "mode-image_xfm.h5"
                        ),
                        "src": "MNI152NLin2009cAsym",
                        "dst": "native",
                    },
                }
            )
        # Set default types
        if types is None:
            types = list(patterns.keys())
        # Convert single type into list
        else:
            if not isinstance(types, list):
                types = [types]
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
