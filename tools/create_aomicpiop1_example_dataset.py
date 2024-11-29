"""Create an example/testing dataset for PIOP1 with mock data."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from pathlib import Path
from tempfile import TemporaryDirectory

import datalad.api as dl


# repo has to be created on gin manually beforehand if not owner
dst = "git@gin.g-node.org:/juaml/datalad-example-aomicpiop1.git"

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
                ]

                tasks = [
                    "anticipation_acq-seq",
                    "emomatching_acq-seq",
                    "faces_acq-mb3",
                    "gstroop_acq-seq",
                    "restingstate_acq-mb3",
                    "workingmemory_acq-seq",
                ]
                for t in tasks:
                    # BOLD native
                    fnames.append(
                        f"func/{t_sub}_task-{t}_space-"
                        "T1w_desc-preproc_bold.nii.gz"
                    )
                    # BOLD MNI152NLin2009cAsym
                    fnames.append(
                        f"func/{t_sub}_task-{t}_space-"
                        "MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
                    )
                    fnames.append(
                        f"func/{t_sub}_task-{t}_space-"
                        "T1w_desc-preproc_bold.json"
                    )
                    fnames.append(
                        f"func/{t_sub}_task-{t}_space-"
                        "MNI152NLin2009cAsym_desc-preproc_bold.json"
                    )
                    # BOLD brain mask native
                    fnames.append(
                        f"func/{t_sub}_task-{t}_space-"
                        "T1w_desc-brain_mask.nii.gz"
                    )
                    # BOLD brain mask MNI152NLin2009cAsym
                    fnames.append(
                        f"func/{t_sub}_task-{t}_space-"
                        "MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
                    )
                    # BOLD confounds
                    fnames.append(
                        f"func/{t_sub}_task-{t}_desc-confounds"
                        "_regressors.tsv"
                    )
                    fnames.append(
                        f"func/{t_sub}_task-{t}_desc-confounds"
                        "_regressors.json"
                    )
                    # BOLD reference native
                    fnames.append(
                        f"func/{t_sub}_task-{t}_" "space-T1w_boldref.nii.gz"
                    )
                    # BOLD reference MNI152NLin2009cAsym
                    fnames.append(
                        f"func/{t_sub}_task-{t}_"
                        "space-MNI152NLin2009cAsym_boldref.nii.gz"
                    )

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
    # (org_name/repo_basename).as_posix(), name='gin', existing='reconfigure',
    # api=dst_api, access_protocol='ssh')
    ds.siblings("add", name="gin", url=dst)
    ds.push(to="gin", force="all")
