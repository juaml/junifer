"""Provide class for temporal filtering."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    Any,
    ClassVar,
    Optional,
    Union,
)

import nibabel as nib
from nilearn import image as nimg
from nilearn._utils.niimg_conversions import check_niimg_4d

from ..api.decorators import register_preprocessor
from ..data import get_data
from ..pipeline import WorkDirManager
from ..typing import Dependencies
from ..utils import logger
from .base import BasePreprocessor


__all__ = ["TemporalFilter"]


@register_preprocessor
class TemporalFilter(BasePreprocessor):
    """Class for temporal filtering.

    Temporal filtering is based on :func:`nilearn.image.clean_img`.

    Parameters
    ----------
    detrend : bool, optional
        If True, detrending will be applied on timeseries (default True).
    standardize : bool, optional
        If True, returned signals are set to unit variance (default True).
    low_pass : float, optional
        Low cutoff frequencies, in Hertz. If None, no filtering is applied
        (default None).
    high_pass : float, optional
        High cutoff frequencies, in Hertz. If None, no filtering is
        applied (default None).
    t_r : float, optional
        Repetition time, in second (sampling period).
        If None, it will use t_r from nifti header (default None).
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).

    """

    _DEPENDENCIES: ClassVar[Dependencies] = {"numpy", "nilearn"}

    def __init__(
        self,
        detrend: bool = True,
        standardize: bool = True,
        low_pass: Optional[float] = None,
        high_pass: Optional[float] = None,
        t_r: Optional[float] = None,
        masks: Union[str, dict, list[Union[dict, str]], None] = None,
    ) -> None:
        """Initialize the class."""
        self.detrend = detrend
        self.standardize = standardize
        self.low_pass = low_pass
        self.high_pass = high_pass
        self.t_r = t_r
        self.masks = masks

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
            The input to the preprocessor.

        Returns
        -------
        str
            The data type output by the preprocessor.

        """
        # Does not add any new keys
        return input_type

    def _validate_data(
        self,
        input: dict[str, Any],
    ) -> None:
        """Validate input data.

        Parameters
        ----------
        input : dict
            Dictionary containing the ``BOLD`` data from the
            Junifer Data object.

        Raises
        ------
        ValueError
            If ``"data"`` is not 4D

        """
        # BOLD must be 4D niimg
        check_niimg_4d(input["data"])

    def preprocess(
        self,
        input: dict[str, Any],
        extra_input: Optional[dict[str, Any]] = None,
    ) -> tuple[dict[str, Any], Optional[dict[str, dict[str, Any]]]]:
        """Preprocess.

        Parameters
        ----------
        input : dict
            A single input from the Junifer Data object to preprocess.
        extra_input : dict, optional
            The other fields in the Junifer Data object.

        Returns
        -------
        dict
            The computed result as dictionary. If `self.masks` is not None,
            then the target data computed mask is updated for further steps.
        None
            Extra "helper" data types as dictionary to add to the Junifer Data
            object.

        """
        # Validate data
        self._validate_data(input)

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
        # and / or mask
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="temporal_filter"
        )

        # Set mask data
        mask_img = None
        if self.masks is not None:
            # Generate mask
            logger.debug(f"Masking with {self.masks}")
            mask_img = get_data(
                kind="mask",
                names=self.masks,
                target_data=input,
                extra_input=extra_input,
            )
            # Save generated mask for use later
            generated_mask_img_path = element_tempdir / "generated_mask.nii.gz"
            nib.save(mask_img, generated_mask_img_path)

            # Save BOLD mask and link it to the BOLD data type dict;
            # this allows to use "inherit" down the pipeline
            logger.debug("Setting `BOLD.mask`")
            input.update(
                {
                    "mask": {
                        # Update path to sync with "data"
                        "path": generated_mask_img_path,
                        # Update data
                        "data": mask_img,
                        # Should be in the same space as target data
                        "space": input["space"],
                    }
                }
            )

        signal_clean_kwargs = {}

        # Clean image
        logger.info("Temporal filter image using nilearn")
        logger.debug(f"\tdetrend: {self.detrend}")
        logger.debug(f"\tstandardize: {self.standardize}")
        logger.debug(f"\tlow_pass: {self.low_pass}")
        logger.debug(f"\thigh_pass: {self.high_pass}")
        logger.debug(f"\tt_r: {self.t_r}")

        cleaned_img = nimg.clean_img(
            imgs=bold_img,
            detrend=self.detrend,
            standardize=self.standardize,
            low_pass=self.low_pass,
            high_pass=self.high_pass,
            t_r=t_r,
            mask_img=mask_img,
            **signal_clean_kwargs,
        )
        # Fix t_r as nilearn messes it up
        cleaned_img.header["pixdim"][4] = t_r
        # Save filtered data
        filtered_data_path = element_tempdir / "filtered_data.nii.gz"
        nib.save(cleaned_img, filtered_data_path)

        logger.debug("Updating `BOLD`")
        input.update(
            {
                # Update path to sync with "data"
                "path": filtered_data_path,
                # Update data
                "data": cleaned_img,
            }
        )

        return input, None
