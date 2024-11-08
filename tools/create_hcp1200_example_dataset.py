"""Script to generate example dataset for HCP1200."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory

import datalad.api as dl


# Set destination URL
DST = "git@gin.g-node.org:/juaml/datalad-example-hcp1200.git"


if __name__ == "__main__":
    with TemporaryDirectory() as tmpdir:
        # Convert str to Path
        tmpdir_path = Path(tmpdir)
        # Set base directory
        basedir = tmpdir_path / "example_hcp1200"
        # Create new datalad dataset
        dataset = dl.create(path=str(basedir.absolute()))  # type: ignore
        # Generate subject directories
        for sub in range(1, 10):
            subdir = basedir / f"sub-{sub:02d}"
            # Create subject directory
            subdir.mkdir()

            # T1w data
            # Set subject data directory
            sub_t1w_datadir = subdir / "T1w"
            # Create subject data directory
            sub_t1w_datadir.mkdir(parents=True)
            # Set subject data file
            sub_t1w_datafile = sub_t1w_datadir / "T1w_acpc_dc_restore.nii.gz"
            # Write subject data file
            with open(sub_t1w_datafile, "w") as f:
                f.write("placeholder")

            # Warp data
            # Set subject data directory
            sub_warp_datadir = subdir / "MNINonLinear" / "xfms"
            # Create subject data directory
            sub_warp_datadir.mkdir(parents=True)
            # Set subject data files
            sub_warp_datafiles = [
                sub_warp_datadir / "standard2acpc_dc.nii.gz",
                sub_warp_datadir / "acpc_dc2standard.nii.gz",
            ]
            # Write subject data files
            for datafile in sub_warp_datafiles:
                with open(datafile, "w") as f:
                    f.write("placeholder")

            # BOLD data
            for task, phase_encoding in product(
                [
                    "REST1",
                    "REST2",
                    "SOCIAL",
                    "WM",
                    "RELATIONAL",
                    "EMOTION",
                    "LANGUAGE",
                    "GAMBLING",
                    "MOTOR",
                ],
                ["LR", "RL"],
            ):
                # Proper formatting of task name
                if "REST" in task:
                    new_task = f"rfMRI_{task}"
                else:
                    new_task = f"tfMRI_{task}"
                # Set subject data directory
                sub_bold_datadir = (
                    subdir
                    / "MNINonLinear"
                    / "Results"
                    / f"{new_task}_{phase_encoding}"
                )
                # Create subject data directory
                sub_bold_datadir.mkdir(parents=True)

                # Set subject data file
                sub_bold_datafile = (
                    sub_bold_datadir / f"{new_task}_{phase_encoding}.nii.gz"
                )
                # Create subject data file
                with open(sub_bold_datafile, "w") as f:
                    f.write("placeholder")

                if "REST" in task:
                    # Set subject data file with ICA+FIX
                    sub_bold_datafile = (
                        sub_bold_datadir
                        / f"{new_task}_{phase_encoding}_hp2000_clean.nii.gz"
                    )
                    # Create subject data file with ICA+FIX
                    with open(sub_bold_datafile, "w") as f:
                        f.write("placeholder")

        # Save datalad dataset
        dataset.save(recursive=True)
        # Add datalad sibling
        dataset.siblings(action="add", name="gin", url=DST)
        # Push dataset to sibling
        dataset.push(to="gin", force="all")
