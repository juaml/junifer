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


__all__ = ["DataladAOMICID1000"]


@register_datagrabber
class DataladAOMICID1000(PatternDataladDataGrabber):
    """Concrete implementation for datalad-based data fetching of AOMIC ID1000.

    Parameters
    ----------
    datadir : str or Path or None, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    types: {"BOLD", "T1w", "VBM_CSF", "VBM_GM", "VBM_WM", "DWI", \
           "FreeSurfer"} or list of the options, optional
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
                    "derivatives/fmriprep/{subject}/func/"
                    "{subject}_task-moviewatching_"
                    "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
                "mask": {
                    "pattern": (
                        "derivatives/fmriprep/{subject}/func/"
                        "{subject}_task-moviewatching_"
                        "space-MNI152NLin2009cAsym_"
                        "desc-brain_mask.nii.gz"
                    ),
                    "space": "MNI152NLin2009cAsym",
                },
                "confounds": {
                    "pattern": (
                        "derivatives/fmriprep/{subject}/func/"
                        "{subject}_task-moviewatching_"
                        "desc-confounds_regressors.tsv"
                    ),
                    "format": "fmriprep",
                },
            },
            "T1w": {
                "pattern": (
                    "derivatives/fmriprep/{subject}/anat/"
                    "{subject}_space-MNI152NLin2009cAsym_"
                    "desc-preproc_T1w.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
                "mask": {
                    "pattern": (
                        "derivatives/fmriprep/{subject}/anat/"
                        "{subject}_space-MNI152NLin2009cAsym_"
                        "desc-brain_mask.nii.gz"
                    ),
                    "space": "MNI152NLin2009cAsym",
                },
            },
            "VBM_CSF": {
                "pattern": (
                    "derivatives/fmriprep/{subject}/anat/"
                    "{subject}_space-MNI152NLin2009cAsym_label-"
                    "CSF_probseg.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
            },
            "VBM_GM": {
                "pattern": (
                    "derivatives/fmriprep/{subject}/anat/"
                    "{subject}_space-MNI152NLin2009cAsym_label-"
                    "GM_probseg.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
            },
            "VBM_WM": {
                "pattern": (
                    "derivatives/fmriprep/{subject}/anat/"
                    "{subject}_space-MNI152NLin2009cAsym_label-"
                    "WM_probseg.nii.gz"
                ),
                "space": "MNI152NLin2009cAsym",
            },
            "DWI": {
                "pattern": (
                    "derivatives/dwipreproc/{subject}/dwi/"
                    "{subject}_desc-preproc_dwi.nii.gz"
                ),
            },
            "FreeSurfer": {
                "pattern": "derivatives/freesurfer/[!f]{subject}/mri/T1.mg[z]",
                "aseg": {
                    "pattern": (
                        "derivatives/freesurfer/[!f]{subject}/mri/aseg.mg[z]"
                    )
                },
                "norm": {
                    "pattern": (
                        "derivatives/freesurfer/[!f]{subject}/mri/norm.mg[z]"
                    )
                },
                "lh_white": {
                    "pattern": (
                        "derivatives/freesurfer/[!f]{subject}/surf/lh.whit[e]"
                    )
                },
                "rh_white": {
                    "pattern": (
                        "derivatives/freesurfer/[!f]{subject}/surf/rh.whit[e]"
                    )
                },
                "lh_pial": {
                    "pattern": (
                        "derivatives/freesurfer/[!f]{subject}/surf/lh.pia[l]"
                    )
                },
                "rh_pial": {
                    "pattern": (
                        "derivatives/freesurfer/[!f]{subject}/surf/rh.pia[l]"
                    )
                },
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
                            "derivatives/fmriprep/{subject}/anat/"
                            "{subject}_desc-preproc_T1w.nii.gz"
                        ),
                        "space": "native",
                        "mask": {
                            "pattern": (
                                "derivatives/fmriprep/{subject}/anat/"
                                "{subject}_desc-brain_mask.nii.gz"
                            ),
                            "space": "native",
                        },
                    },
                    "Warp": {
                        "pattern": (
                            "derivatives/fmriprep/{subject}/anat/"
                            "{subject}_from-MNI152NLin2009cAsym_to-T1w_"
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
