"""Provide class for temporal slicing."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar, Optional

import nibabel as nib
import nilearn.image as nimg

from ..api.decorators import register_preprocessor
from ..pipeline import WorkDirManager
from ..typing import Dependencies
from ..utils import logger
from .base import BasePreprocessor


__all__ = ["TemporalSlicer"]


@register_preprocessor
class TemporalSlicer(BasePreprocessor):
    """Class for temporal slicing.

    Parameters
    ----------
    start : int
        Starting time point, in second.
    stop : int
        Ending time point, in second.
    t_r : float, optional
        Repetition time, in second (sampling period).
        If None, it will use t_r from nifti header (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"nilearn"}

    def __init__(
        self,
        start: int,
        stop: int,
        t_r: Optional[float] = None,
    ) -> None:
        """Initialize the class."""
        self.start = start
        self.stop = stop
        self.t_r = t_r
        super().__init__(on="BOLD", required_data_types=["BOLD"])

    def get_valid_inputs(self) -> list[str]:
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
        input: dict[str, Any],
        extra_input: Optional[dict[str, Any]] = None,
    ) -> tuple[dict[str, Any], Optional[dict[str, dict[str, Any]]]]:
        """Preprocess.

        Parameters
        ----------
        input : dict
            The input from the Junifer Data object.
        extra_input : dict, optional
            The other fields in the Junifer Data object.

        Returns
        -------
        dict
            The computed result as dictionary.
        None
            Extra "helper" data types as dictionary to add to the Junifer Data
            object.

        """
        logger.debug("Temporal slicing")

        # Get BOLD data
        bold_img = input["data"]
        # Set t_r
        t_r = self.t_r
        if t_r is None:
            logger.info("No `t_r` specified, using t_r from NIfTI header")
            t_r = bold_img.header.get_zooms()[3]  # type: ignore
            logger.info(
                f"Read t_r from NIfTI header: {t_r}",
            )

        # Create element-specific tempdir for storing generated data
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="temporal_slicer"
        )

        # Slice image after converting slice range from seconds to indices
        index = slice(int(self.start // t_r), int(self.stop // t_r))
        sliced_img = nimg.index_img(bold_img, index)
        # Fix t_r as nilearn messes it up
        sliced_img.header["pixdim"][4] = t_r
        # Save sliced data
        sliced_img_path = element_tempdir / "sliced_data.nii.gz"
        nib.save(sliced_img, sliced_img_path)

        logger.debug("Updating `BOLD`")
        input.update(
            {
                # Update path to sync with "data"
                "path": sliced_img_path,
                # Update data
                "data": sliced_img,
            }
        )

        return input, None
