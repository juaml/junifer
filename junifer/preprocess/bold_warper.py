"""Provide class for warping BOLD to other template spaces."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

import nibabel as nib
from templateflow import api as tflow

from ..api.decorators import register_preprocessor
from ..data import get_template, get_xfm
from ..pipeline import WorkDirManager
from ..utils import logger, raise_error, run_ext_cmd
from .ants.ants_apply_transforms_warper import _AntsApplyTransformsWarper
from .base import BasePreprocessor
from .fsl.apply_warper import _ApplyWarper


@register_preprocessor
class BOLDWarper(BasePreprocessor):
    """Class for warping BOLD NIfTI images.

    .. deprecated:: 0.0.3
              `BOLDWarper` will be removed in v0.0.4, it is replaced by
              `SpaceWarper` because the latter works also with T1w data.

    Parameters
    ----------
    using : {"fsl", "ants"}
        Implementation to use for warping:

        * "fsl" : Use FSL's ``applywarp``
        * "afni" : Use ANTs' ``antsApplyTransforms``

    reference : str
        The data type to use as reference for warping, can be either a data
        type like "T1w" or a template space like "MNI152NLin2009cAsym".

    Raises
    ------
    ValueError
        If ``using`` is invalid or
        if ``reference`` is invalid.

    Notes
    -----
    If you are setting ``reference`` to a template space like
    "MNI152NLin2009cAsym", make sure ANTs is available for the
    transformation else it will fail during runtime. It is tricky to validate
    this beforehand and difficult to enforce this as a requirement, hence the
    heads-up.

    """

    _CONDITIONAL_DEPENDENCIES: ClassVar[List[Dict[str, Union[str, Type]]]] = [
        {
            "using": "fsl",
            "depends_on": _ApplyWarper,
        },
        {
            "using": "ants",
            "depends_on": _AntsApplyTransformsWarper,
        },
    ]

    def __init__(self, using: str, reference: str) -> None:
        """Initialize the class."""
        # Validate `using` parameter
        valid_using = [dep["using"] for dep in self._CONDITIONAL_DEPENDENCIES]
        if using not in valid_using:
            raise_error(
                f"Invalid value for `using`, should be one of: {valid_using}"
            )
        self.using = using
        self.ref = reference
        # Initialize superclass based on reference
        if self.ref == "T1w":
            super().__init__(
                on="BOLD", required_data_types=["BOLD", self.ref, "Warp"]
            )
        elif self.ref in tflow.templates():
            super().__init__(on="BOLD", required_data_types=["BOLD"])
        else:
            raise_error(f"Unknown reference: {self.ref}")

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this
            preprocessor.

        """
        return ["BOLD"]

    def get_output_type(self, input_type: str) -> str:
        """Get output type.

        Parameters
        ----------
        input_type : str
            The data type input to the preprocessor.

        Returns
        -------
        str
            The data type output by the preprocessor.

        """
        # Does not add any new keys
        return input_type

    def preprocess(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Dict[str, Any]]]]:
        """Preprocess.

        Parameters
        ----------
        input : dict
            The BOLD input from the Junifer Data object.
        extra_input : dict, optional
            The other fields in the Junifer Data object. Must include the
            ``Warp`` and ``ref`` value's keys if native space transformation is
            needed.

        Returns
        -------
        dict
            The computed result as dictionary.
        None
            Extra "helper" data types as dictionary to add to the Junifer Data
            object.

        Raises
        ------
        ValueError
            If ``extra_input`` is None when transforming to native space
            i.e., using "T1w" as reference.
        RuntimeError
            If warp / transformation file extension is not ".mat" or ".h5"
            when transforming to native space or
            if the BOLD data is in the correct space and does not require
            warping.

        """
        logger.info(f"Warping BOLD to {self.ref} space using BOLDWarper")
        # Transform to native space
        if self.ref == "T1w":
            # Check for extra inputs
            if extra_input is None:
                raise_error(
                    "No extra input provided, requires `Warp` and "
                    f"`{self.ref}` data types in particular."
                )
            # Check for warp file type to use correct tool
            warp_file_ext = extra_input["Warp"]["path"].suffix
            if warp_file_ext == ".mat":
                logger.debug("Using FSL with BOLDWarper")
                # Initialize ApplyWarper for computation
                apply_warper = _ApplyWarper(reference=self.ref, on="BOLD")
                # Replace original BOLD data with warped BOLD data
                _, input = apply_warper.preprocess(
                    input=input,
                    extra_input=extra_input,
                )
            elif warp_file_ext == ".h5":
                logger.debug("Using ANTs with BOLDWarper")
                # Initialize AntsApplyTransformsWarper for computation
                ants_apply_transforms_warper = _AntsApplyTransformsWarper(
                    reference=self.ref, on="BOLD"
                )
                # Replace original BOLD data with warped BOLD data
                _, input = ants_apply_transforms_warper.preprocess(
                    input=input,
                    extra_input=extra_input,
                )
            else:
                raise_error(
                    msg=(
                        "Unknown warp / transformation file extension: "
                        f"{warp_file_ext}"
                    ),
                    klass=RuntimeError,
                )
        # Transform to template space
        else:
            # Check pre-requirements for space manipulation
            if self.ref == input["space"]:
                raise_error(
                    (
                        f"Skipped warping as the BOLD data is in {self.ref} "
                        "space which would mean that you can remove the "
                        "BOLDWarper from the preprocess step."
                    ),
                    klass=RuntimeError,
                )
            else:
                # Get xfm file
                xfm_file_path = get_xfm(src=input["space"], dst=self.ref)
                # Get template space image
                template_space_img = get_template(
                    space=self.ref,
                    target_data=input,
                    extra_input=None,
                )

                # Create component-scoped tempdir
                tempdir = WorkDirManager().get_tempdir(prefix="boldwarper")
                # Create element-scoped tempdir so that warped BOLD is
                # available later as nibabel stores file path reference for
                # loading on computation
                element_tempdir = WorkDirManager().get_element_tempdir(
                    prefix="boldwarper"
                )

                # Save template
                template_space_img_path = tempdir / f"{self.ref}_T1w.nii.gz"
                nib.save(template_space_img, template_space_img_path)

                # Create a tempfile for warped output
                warped_bold_path = (
                    element_tempdir
                    / f"bold_warped_from_{input['space']}_to_{self.ref}.nii.gz"
                )

                logger.debug(
                    f"Using ANTs to warp BOLD "
                    f"from {input['space']} to {self.ref}"
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
                    f"-o {warped_bold_path.resolve()}",
                ]
                # Call antsApplyTransforms
                run_ext_cmd(
                    name="antsApplyTransforms", cmd=apply_transforms_cmd
                )

                # Modify target data
                input["data"] = nib.load(warped_bold_path)
                input["space"] = self.ref

        return input, None
