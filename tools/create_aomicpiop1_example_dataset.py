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

    for dtype in ["dwipreproc", "fmriprep"]:
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
                    (
                        f"anat/{t_sub}_space-MNI152NLin2009cAsym_desc-preproc"
                        "_T1w.nii.gz"
                    ),
                    (
                        f"anat/{t_sub}_space-MNI152NLin2009cAsym_label-"
                        "CSF_probseg.nii.gz"
                    ),
                    (
                        f"anat/{t_sub}_space-MNI152NLin2009cAsym_label-"
                        "GM_probseg.nii.gz"
                    ),
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
                    fnames.append(
                        (
                            f"func/{t_sub}_task-{t}_space-"
                            "MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
                        )
                    )
                    fnames.append(
                        (
                            f"func/{t_sub}_task-{t}_space-"
                            "MNI152NLin2009cAsym_desc-preproc_bold.json"
                        )
                    )
                    fnames.append(
                        (
                            f"func/{t_sub}_task-{t}_desc-confounds"
                            "_regressors.tsv"
                        )
                    )
                    fnames.append(
                        (
                            f"func/{t_sub}_task-{t}_desc-confounds"
                            "_regressors.json"
                        )
                    )

            elif dtype == "dwipreproc":
                dname = "dwi"
                (sub_dir / dname).mkdir()

                fnames = [
                    (f"{dname}/{t_sub}_desc-preproc_dwi.nii.gz"),
                ]

            for fname in fnames:
                with open(sub_dir / fname, "w") as f:
                    f.write("placeholder")

    ds.save(recursive=True)
    # use this to create the repo automatically, only possible for juaml owner
    # ds.create_sibling_gin(
    # (org_name/repo_basename).as_posix(), name='gin', existing='reconfigure',
    # api=dst_api, access_protocol='ssh')
    ds.siblings("add", name="gin", url=dst)
    ds.push(to="gin", force="all")
