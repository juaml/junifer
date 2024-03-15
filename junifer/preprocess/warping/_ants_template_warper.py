"""Provide class for template space warping via ANTs antsApplyTransforms."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Set,
    Union,
)

import nibabel as nib

from ...data import get_template, get_xfm
from ...pipeline import WorkDirManager
from ...utils import logger, run_ext_cmd


class ANTsTemplateWarper:
    """Class for template space warping via ANTs antsApplyTransforms.

    This class uses ANTs' ``antsApplyTransforms`` for transformation.

    """

    _EXT_DEPENDENCIES: ClassVar[List[Dict[str, Union[str, List[str]]]]] = [
        {
            "name": "ants",
            "commands": ["antsApplyTransforms"],
        },
    ]

    _DEPENDENCIES: ClassVar[Set[str]] = {"nibabel"}

    def preprocess(
        self,
        input: Dict[str, Any],
        dst: str,
    ) -> Dict[str, Any]:
        """Preprocess using ANTs.

        Parameters
        ----------
        input : dict
            A single input from the Junifer Data object in which to preprocess.
        dst : str
            Template space to warp to.

        Returns
        -------
        dict
            The ``input`` dictionary with modified ``data`` and ``space`` key
            values.

        """
        logger.debug(
            f"Using ANTs to warp data " f"from {input['space']} to {dst}"
        )

        # Get xfm file
        xfm_file_path = get_xfm(src=input["space"], dst=dst)
        # Get template space image
        template_space_img = get_template(
            space=dst,
            target_data=input,
            extra_input=None,
        )

        # Create component-scoped tempdir
        tempdir = WorkDirManager().get_tempdir(prefix="ants_template_warper")
        # Create element-scoped tempdir so that warped data is
        # available later as nibabel stores file path reference for
        # loading on computation
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="ants_template_warper"
        )

        # Save template
        template_space_img_path = tempdir / f"{dst}_T1w.nii.gz"
        nib.save(template_space_img, template_space_img_path)

        # Create a tempfile for warped output
        warped_output_path = element_tempdir / (
            f"data_warped_from_{input['space']}_to_" f"{dst}.nii.gz"
        )

        # Set antsApplyTransforms command
        apply_transforms_cmd = [
            "antsApplyTransforms",
            "-d 3",
            "-e 3",
            "-n LanczosWindowedSinc",
            f"-i {input['path'].resolve()}",
            f"-r {template_space_img_path.resolve()}",
            f"-t {xfm_file_path.resolve()}",
            f"-o {warped_output_path.resolve()}",
        ]
        # Call antsApplyTransforms
        run_ext_cmd(name="antsApplyTransforms", cmd=apply_transforms_cmd)

        # Delete tempdir
        WorkDirManager().delete_tempdir(tempdir)

        # Modify target data
        input["data"] = nib.load(warped_output_path)
        input["space"] = dst

        return input
