"""Script to generate example dataset for HCP1200."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from itertools import product
from tempfile import TemporaryDirectory
from pathlib import Path

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
        dataset = dl.create(path=str(basedir.absolute()))
        # Generate subject directories
        for sub in range(1, 10):
            subdir = basedir / f"sub-{sub:02d}"
            # Create subject directory
            subdir.mkdir()

            for (task, phase_encoding) in product(
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
                sub_datadir = (
                    subdir
                    / "MNINonLinear"
                    / "Results"
                    / f"{new_task}_{phase_encoding}"
                )
                # Create subject data directory
                sub_datadir.mkdir(parents=True)
                # Set subject data file
                sub_datafile = (
                    sub_datadir
                    / f"{new_task}_{phase_encoding}_hp2000_clean.nii.gz"
                )
                # Create subject data file
                with open(sub_datafile, "w") as f:
                    f.write("placeholder")

        # Save datalad dataset
        dataset.save(recursive=True)
        # Add datalad sibling
        dataset.siblings(action="add", name="gin", url=DST)
        # Push dataset to sibling
        dataset.push(to="gin", force="all")
