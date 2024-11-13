"""Script to generate example dataset for DMCC13Benchmark."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory

from datalad import api as dl


# Set destination URL
DST = "git@gin.g-node.org:/synchon/datalad-example-dmcc13-benchmark.git"


if __name__ == "__main__":
    with TemporaryDirectory() as tmpdir:
        # Convert str to Path
        tmpdir_path = Path(tmpdir)
        # Set dataset directory
        dataset_dir = tmpdir_path / "example_dmcc13_benchmark"
        # Create new datalad dataset
        dataset = dl.create(path=str(dataset_dir.resolve()))

        # Create base directory directory
        basedir = dataset_dir / "derivatives" / "fmriprep-1.3.2"
        basedir.mkdir(parents=True)

        # Generate subject directories
        for sub in range(1, 10):
            subdir = basedir / f"sub-{sub:02d}"
            # Create subject directory
            subdir.mkdir()

            # Sessions for functional data
            sessions = [
                "wave1bas",
                "wave1pro",
                "wave1rea",
            ]

            # Create data kind directories
            for kind in ("anat", *[f"ses-{ses}" for ses in sessions]):
                (subdir / kind).mkdir()
                # Make functional data directories
                if kind != "anat":
                    (subdir / kind / "func").mkdir()

            # Files to write, start with anatomical data
            files = [
                (
                    f"anat/sub-{sub:02d}_space-MNI152NLin2009cAsym_desc-preproc"
                    "_T1w.nii.gz"
                ),  # T1w
                (
                    f"anat/sub-{sub:02d}_space-MNI152NLin2009cAsym_desc-"
                    "brain_mask.nii.gz"
                ),  # T1w mask
                (
                    f"anat/sub-{sub:02d}_space-MNI152NLin2009cAsym_"
                    "label-CSF_probseg.nii.gz"
                ),  # probseg CSF
                (
                    f"anat/sub-{sub:02d}_space-MNI152NLin2009cAsym_"
                    "label-GM_probseg.nii.gz"
                ),  # probseg GM
                (
                    f"anat/sub-{sub:02d}_space-MNI152NLin2009cAsym_"
                    "label-WM_probseg.nii.gz"
                ),  # probseg WM
                (
                    f"anat/sub-{sub:02d}_desc-preproc_T1w.nii.gz"
                ),  # T1w in native
                (
                    f"anat/sub-{sub:02d}_desc-brain_mask.nii.gz"
                ),  # T1w mask in native
                (
                    f"anat/sub-{sub:02d}_from-MNI152NLin2009cAsym_to-T1w_"
                    "mode-image_xfm.h5"
                ),  # Warp to native
                (
                    f"anat/sub-{sub:02d}_from-T1w_to-MNI152NLin2009cAsym_"
                    "mode-image_xfm.h5"
                ),  # Warp from native
            ]

            # Tasks for functional data
            tasks = [
                "Rest",
                "Axcpt",
                "Cuedts",
                "Stern",
                "Stroop",
            ]
            # Phase encodings for functional data
            phase_encodings = ["AP", "PA"]

            # For wave1bas task
            for ses, task, phase_encoding in product(
                ["wave1bas"],
                tasks,
                phase_encodings,
            ):
                if phase_encoding == "AP":
                    run = "1"
                else:
                    run = "2"
                # BOLD
                files.append(
                    f"ses-{ses}/func/sub-{sub:02d}_ses-{ses}_task-{task}_acq-mb4"
                    f"{phase_encoding}_run-{run}_"
                    "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
                )
                # BOLD confounds
                files.append(
                    f"ses-{ses}/func/sub-{sub:02d}_ses-{ses}_task-{task}_acq-mb4"
                    f"{phase_encoding}_run-{run}_"
                    "desc-confounds_regressors.tsv"
                )
                # BOLD mask
                files.append(
                    f"ses-{ses}/func/sub-{sub:02d}_ses-{ses}_task-{task}_acq-mb4"
                    f"{phase_encoding}_run-{run}_"
                    "space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
                )

            # For wave1bas task
            for ses, task, phase_encoding in product(
                ["wave1pro", "wave1rea"],
                ["Rest"],
                phase_encodings,
            ):
                if phase_encoding == "AP":
                    run = "1"
                else:
                    run = "2"
                # BOLD
                files.append(
                    f"ses-{ses}/func/sub-{sub:02d}_ses-{ses}_task-{task}_acq-mb4"
                    f"{phase_encoding}_run-{run}_"
                    "space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
                )
                # BOLD confounds
                files.append(
                    f"ses-{ses}/func/sub-{sub:02d}_ses-{ses}_task-{task}_acq-mb4"
                    f"{phase_encoding}_run-{run}_"
                    "desc-confounds_regressors.tsv"
                )
                # BOLD mask
                files.append(
                    f"ses-{ses}/func/sub-{sub:02d}_ses-{ses}_task-{task}_acq-mb4"
                    f"{phase_encoding}_run-{run}_"
                    "space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
                )

            # Create files
            for file in files:
                with open(subdir / file, "w") as f:
                    f.write("placeholder")

        # Save datalad dataset
        dataset.save(recursive=True)
        # Add datalad sibling
        dataset.siblings(action="add", name="gin", url=DST)
        # Push dataset to sibling
        dataset.push(to="gin", force="all")
