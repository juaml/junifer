"""Provide class for temporal slicing."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar, Optional, Union

import nibabel as nib
import nilearn.image as nimg

from ..api.decorators import register_preprocessor
from ..pipeline import WorkDirManager
from ..typing import Dependencies
from ..utils import logger, raise_error
from .base import BasePreprocessor


__all__ = ["TemporalSlicer"]


@register_preprocessor
class TemporalSlicer(BasePreprocessor):
    """Class for temporal slicing.

    Parameters
    ----------
    start : float
        Starting time point, in second.
    stop : float or None
        Ending time point, in second. If None, stops at the last time point.
        Can also do negative indexing and has the same meaning as standard
        Python slicing except it represents time points.
    duration : float or None, optional
        Time duration to add to ``start``, in second. If None, ``stop`` is
        respected, else error is raised.
    t_r : float, optional
        Repetition time, in second (sampling period).
        If None, it will use t_r from nifti header (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"nilearn"}

    def __init__(
        self,
        start: float,
        stop: Union[float, None],
        duration: Union[float, None] = None,
        t_r: Optional[float] = None,
    ) -> None:
        """Initialize the class."""
        self.start = start
        self.stop = stop
        self.duration = duration
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

        Raises
        ------
        RuntimeError
            If no time slicing will be performed or
            if ``stop`` is not None when ``duration`` is provided.

        """
        logger.debug("Temporal slicing")

        # Get BOLD data
        bold_img = input["data"]

        # Check if slicing is not required
        if self.start == 0:
            if (
                self.stop is None
                or self.stop == -1
                or self.stop == bold_img.shape[3]
            ):
                raise_error(
                    "No temporal slicing will be performed as "
                    f"`start` = {self.start} and "
                    f"`stop` = {self.stop}, hence you "
                    "should remove the TemporalSlicer from the preprocess "
                    "step.",
                    klass=RuntimeError,
                )

        # Sanity check for stop and duration combination
        if self.duration is not None and self.stop is not None:
            raise_error(
                "`stop` should be None if `duration` is not None. "
                "Set `stop` = None for TemporalSlicer to continue.",
                klass=RuntimeError,
            )

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

        # Check stop; duration is None
        if self.stop is None:
            if self.duration is not None:
                stop = self.start + self.duration
            else:
                stop = bold_img.shape[3]
        else:
            # Calculate stop index if going from end
            if self.stop < 0:
                stop = bold_img.shape[3] + 1 + self.stop
            else:
                stop = self.stop
        # Slice image after converting slice range from seconds to indices
        index = slice(int(self.start // t_r), int(stop // t_r))
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
