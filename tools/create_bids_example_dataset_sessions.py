# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL
from pathlib import Path
from tempfile import TemporaryDirectory

import datalad.api as dl


dst = "git@gin.g-node.org:/juaml/datalad-example-bids-ses.git"

with TemporaryDirectory() as tmpdir_name:
    tmpdir = Path(tmpdir_name)
    ds = dl.create(tmpdir)  # type: ignore

    base_dir = tmpdir / "example_bids_ses"
    base_dir.mkdir()

    for i_sub in range(1, 10):
        t_sub = f"sub-{i_sub:02d}"
        sub_dir = base_dir / t_sub
        sub_dir.mkdir()

        for i_ses in range(1, 4):
            t_ses = f"ses-{i_ses:02d}"
            ses_dir = sub_dir / t_ses
            ses_dir.mkdir()

            for dname in ["anat", "func"]:
                (ses_dir / dname).mkdir()

            fnames = [
                f"anat/{t_sub}_{t_ses}_T1w.nii.gz",
                f"anat/{t_sub}_{t_ses}_brain_mask.nii.gz",
                f"anat/{t_sub}_{t_ses}_from-MNI152NLin2009cAsym_to-T1w_xfm.h5",
                f"anat/{t_sub}_{t_ses}_from-T1w_to-MNI152NLin2009cAsym_xfm.h5",
            ]
            if i_ses != 3:  # Session 3 does not have functional data
                fnames.extend(
                    [
                        f"func/{t_sub}_{t_ses}_task-rest_bold.nii.gz",
                        f"func/{t_sub}_{t_ses}_task-rest_bold.json",
                        f"func/{t_sub}_{t_ses}_task-rest_brain_mask.nii.gz",
                        f"func/{t_sub}_{t_ses}_task-rest_confounds_regressors.tsv",
                    ]
                )
            for fname in fnames:
                with open(ses_dir / fname, "w") as f:
                    f.write("placeholder-{fname}")

    ds.save(recursive=True)
    ds.siblings("add", name="gin", url=dst)
    ds.push(to="gin", force="all")
