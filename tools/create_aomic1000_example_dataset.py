"""Create a testing dataset for DataladAOMICID1000."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
# License: AGPL

from pathlib import Path
from tempfile import TemporaryDirectory

import datalad.api as dl


# repo has to be created on gin manually beforehand if not owner
dst = "git@gin.g-node.org:/juaml/datalad-example-aomic1000.git"

# Use this if you create repo directly when pushing (see below)
# dst_api = 'git@gin.g-node.org'
# org_name = PurePosixPath('juaml')
# repo_basename = PurePosixPath('datalad-example-aomic1000.git')

with TemporaryDirectory() as tmpdir_name:
    tmpdir = Path(tmpdir_name)
    ds = dl.create(tmpdir)  # type: ignore

    base_dir = tmpdir / "derivatives"
    base_dir.mkdir(exist_ok=True, parents=True)

    for dtype in ["dwipreproc", "fmriprep", "freesurfer"]:
        dtype_dir = base_dir / dtype
        dtype_dir.mkdir()

        for i_sub in range(1, 10):
            t_sub = f"sub-{i_sub:04d}"
            sub_dir = dtype_dir / t_sub
            sub_dir.mkdir()

            if dtype == "fmriprep":
                for dname in ["func", "anat"]:
                    (sub_dir / dname).mkdir()

                fnames = [
                    # T1w native
                    f"anat/{t_sub}_desc-preproc_T1w.nii.gz",
                    # T1w MNI152NLin2009cAsym
                    (
                        f"anat/{t_sub}_space-MNI152NLin2009cAsym_desc-preproc"
                        "_T1w.nii.gz"
                    ),
                    # T1w brain mask native
                    f"anat/{t_sub}_desc-brain_mask.nii.gz",
                    # T1w brain mask MNI152NLin2009cAsym
                    (
                        f"anat/{t_sub}_space-MNI152NLin2009cAsym_"
                        "desc-brain_mask.nii.gz"
                    ),
                    # CSF native
                    f"anat/{t_sub}_label-CSF_probseg.nii.gz",
                    # CSF MNI152NLin2009cAsym
                    (
                        f"anat/{t_sub}_space-MNI152NLin2009cAsym_label-"
                        "CSF_probseg.nii.gz"
                    ),
                    # GM native
                    f"anat/{t_sub}_label-GM_probseg.nii.gz",
                    # GM MNI152NLin2009cAsym
                    (
                        f"anat/{t_sub}_space-MNI152NLin2009cAsym_label-"
                        "GM_probseg.nii.gz"
                    ),
                    # WM native
                    f"anat/{t_sub}_label-WM_probseg.nii.gz",
                    # WM MNI152NLin2009cAsym
                    (
                        f"anat/{t_sub}_space-MNI152NLin2009cAsym_label-"
                        "WM_probseg.nii.gz"
                    ),
                    # BOLD native
                    (
                        f"func/{t_sub}_task-moviewatching_space-"
                        "T1w_desc-preproc_bold.nii.gz"
                    ),
                    # BOLD MNI152NLin2009cAsym
                    (
                        f"func/{t_sub}_task-moviewatching_space-"
                        "MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
                    ),
                    # BOLD brain mask native
                    (
                        f"func/{t_sub}_task-moviewatching_"
                        "space-T1w_desc-brain_mask.nii.gz"
                    ),
                    # BOLD brain mask MNI152NLin2009cAsym
                    (
                        f"func/{t_sub}_task-moviewatching_"
                        "space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
                    ),
                    (
                        f"func/{t_sub}_task-moviewatching_space-"
                        "T1w_desc-preproc_bold.json"
                    ),
                    (
                        f"func/{t_sub}_task-moviewatching_space-"
                        "MNI152NLin2009cAsym_desc-preproc_bold.json"
                    ),
                    # BOLD confounds
                    (
                        f"func/{t_sub}_task-moviewatching_desc-confounds"
                        "_regressors.tsv"
                    ),
                    (
                        f"func/{t_sub}_task-moviewatching_desc-confounds"
                        "_regressors.json"
                    ),
                    # BOLD reference native
                    (
                        f"func/{t_sub}_task-moviewatching_"
                        "space-T1w_boldref.nii.gz"
                    ),
                    # BOLD reference MNI152NLin2009cAsym
                    (
                        f"func/{t_sub}_task-moviewatching_"
                        "space-MNI152NLin2009cAsym_boldref.nii.gz"
                    ),
                ]

            elif dtype == "dwipreproc":
                dname = "dwi"
                (sub_dir / dname).mkdir()

                fnames = [
                    (f"{dname}/{t_sub}_desc-preproc_dwi.nii.gz"),
                ]

            elif dtype == "freesurfer":
                for dname in ["mri", "surf"]:
                    (sub_dir / dname).mkdir()

                fnames = [
                    ("mri/T1.mgz"),
                    ("mri/aseg.mgz"),
                    ("mri/norm.mgz"),
                    ("surf/lh.white"),
                    ("surf/rh.white"),
                    ("surf/lh.pial"),
                    ("surf/rh.pial"),
                ]

            for fname in fnames:
                with open(sub_dir / fname, "w") as f:
                    f.write("placeholder")

        if dtype == "freesurfer":
            for extra in ["fsaverage", "fsaverage5"]:
                extra_dir = dtype_dir / extra
                extra_dir.mkdir()

                for dname in ["mri", "surf"]:
                    (extra_dir / dname).mkdir()

                fnames = [
                    ("mri/T1.mgz"),
                    ("mri/aseg.mgz"),
                    ("mri/norm.mgz"),
                    ("surf/lh.white"),
                    ("surf/rh.white"),
                    ("surf/lh.pial"),
                    ("surf/rh.pial"),
                ]

                for fname in fnames:
                    with open(extra_dir / fname, "w") as f:
                        f.write("placeholder")

    ds.save(recursive=True)
    # use this to create the repo automatically, only possible for juaml owner
    # ds.create_sibling_gin(
    #   (org_name/repo_basename).as_posix(), name='gin', existing='reconfigure',
    #   api=dst_api, access_protocol='ssh')
    ds.siblings("add", name="gin", url=dst)
    ds.push(to="gin", force="all")
