"""Provide class for confound removal using fMRIPrep format."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from nilearn._utils.niimg_conversions import check_niimg_4d
from nilearn.image import clean_img
from nilearn.masking import compute_brain_mask

from ...api.decorators import register_preprocessor
from ...utils import logger, raise_error
from ..base import BasePreprocessor


if TYPE_CHECKING:
    from nibabel import MGHImage, Nifti1Image, Nifti2Image


FMRIPREP_BASICS = {
    "motion": [
        "trans_x",
        "trans_y",
        "trans_z",
        "rot_x",
        "rot_y",
        "rot_z",
    ],
    "wm_csf": ["csf", "white_matter"],
    "global_signal": ["global_signal"],
}

FMRIPREP_POWER2 = {
    "motion": [
        "trans_x_power2",
        "trans_y_power2",
        "trans_z_power2",
        "rot_x_power2",
        "rot_y_power2",
        "rot_z_power2",
    ],
    "wm_csf": ["csf_power2", "white_matter_power2"],
    "global_signal": ["global_signal_power2"],
}

FMRIPREP_DERIVATIVES = {
    "motion": [
        "trans_x_derivative1",
        "trans_y_derivative1",
        "trans_z_derivative1",
        "rot_x_derivative1",
        "rot_y_derivative1",
        "rot_z_derivative1",
    ],
    "wm_csf": ["csf_derivative1", "white_matter_derivative1"],
    "global_signal": ["global_signal_derivative1"],
}

FMRIPREP_DERIVATIVES_POWER2 = {
    "motion": [
        "trans_x_derivative1_power2",
        "trans_y_derivative1_power2",
        "trans_z_derivative1_power2",
        "rot_x_derivative1_power2",
        "rot_y_derivative1_power2",
        "rot_z_derivative1_power2",
    ],
    "wm_csf": ["csf_derivative1_power2", "white_matter_derivative1_power2"],
    "global_signal": ["global_signal_derivative1_power2"],
}

FMRIPREP_VALID_NAMES = [
    elem
    for x in [
        FMRIPREP_BASICS,
        FMRIPREP_POWER2,
        FMRIPREP_DERIVATIVES,
        FMRIPREP_DERIVATIVES_POWER2,
    ]
    for t_list in x.values()
    for elem in t_list
]


@register_preprocessor
class fMRIPrepConfoundRemover(BasePreprocessor):
    """Class for confound removal using fMRIPrep confounds format.

    Read confound files and select columns according to
    a pre-defined strategy.

    Confound removal is based on :func:`nilearn.image.clean_img`.

    Parameters
    ----------
    strategy : dict, optional
        The strategy to use for each component. If None, will use the *full*
        strategy for all components (default None).
        The keys of the dictionary should correspond to names of noise
        components to include:

        * ``motion``
        * ``wm_csf``
        * ``global_signal``

        The values of dictionary should correspond to types of confounds
        extracted from each signal:

        * ``basic`` : only the confounding time series
        * ``power2`` : signal + quadratic term
        * ``derivatives`` : signal + derivatives
        * ``full`` : signal + deriv. + quadratic terms + power2 deriv.

    spike : float, optional
        If None, no spike regressor is added. If spike is a float, it will
        add a spike regressor for every point at which framewise displacement
        exceeds the specified float (default None).
    detrend : bool, optional
        If True, detrending will be applied on timeseries, before confound
        removal (default True).
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
    mask_img: Niimg-like object, optional
        If provided, signal is only cleaned from voxels inside the mask.
        If mask is provided, it should have same shape and affine as imgs.
        If not provided, a mask is computed using
        :func:`nilearn.masking.compute_brain_mask` (default None).

    """

    _DEPENDENCIES = {"numpy", "nilearn"}

    def __init__(
        self,
        strategy: Optional[Dict[str, str]] = None,
        spike: Optional[float] = None,
        detrend: bool = True,
        standardize: bool = True,
        low_pass: Optional[float] = None,
        high_pass: Optional[float] = None,
        t_r: Optional[float] = None,
        mask_img: Optional["Nifti1Image"] = None,
    ) -> None:
        """Initialise the class."""
        if strategy is None:
            strategy = {
                "motion": "full",
                "wm_csf": "full",
                "global_signal": "full",
            }
        self.strategy = strategy
        self.spike = spike
        self.detrend = detrend
        self.standardize = standardize
        self.low_pass = low_pass
        self.high_pass = high_pass
        self.t_r = t_r
        self.mask_img = mask_img

        self._valid_components = ["motion", "wm_csf", "global_signal"]
        self._valid_confounds = ["basic", "power2", "derivatives", "full"]

        if any(not isinstance(k, str) for k in strategy.keys()):
            raise_error("Strategy keys must be strings", ValueError)

        if any(not isinstance(v, str) for v in strategy.values()):
            raise_error("Strategy values must be strings", ValueError)

        if any(x not in self._valid_components for x in strategy.keys()):
            raise_error(
                msg=f"Invalid component names {list(strategy.keys())}. "
                f"Valid components are {self._valid_components}.\n"
                f"If any of them is a valid parameter in "
                "nilearn.interfaces.fmriprep.load_confounds we may "
                "include it in the future",
                klass=ValueError,
            )

        if any(x not in self._valid_confounds for x in strategy.values()):
            raise_error(
                msg=f"Invalid confound types {list(strategy.values())}. "
                f"Valid confound types are {self._valid_confounds}.\n"
                f"If any of them is a valid parameter in "
                "nilearn.interfaces.fmriprep.load_confounds we may "
                "include it in the future",
                klass=ValueError,
            )
        super().__init__()

    def validate_input(self, input: List[str]) -> None:
        """Validate the input to the pipeline step.

        Parameters
        ----------
        input : list of str
            The input to the pipeline step. The list must contain the
            available Junifer Data object keys.

        Raises
        ------
        ValueError
            If the input does not have the required data.

        """
        _required_inputs = ["BOLD", "BOLD_confounds"]
        if any(x not in input for x in _required_inputs):
            raise_error(
                msg="Input does not have the required data. \n"
                f"Input: {input} \n"
                f"Required (all off): {_required_inputs} \n",
                klass=ValueError,
            )

    def get_output_type(self, input: List[str]) -> List[str]:
        """Get the kind of the pipeline step.

        Parameters
        ----------
        input : list of str
            The input to the pipeline step. The list must contain the
            available Junifer Data object keys.

        Returns
        -------
        list of str
            The updated list of available Junifer Data object keys after
            the pipeline step.

        """
        # Does not add any new keys
        return input

    def get_valid_inputs(self) -> List[str]:
        """Get the valid inputs for the pipeline step.

        Returns
        -------
        list of str
            The valid inputs for the pipeline step.

        """
        return ["BOLD"]

    def _map_adhoc_to_fmriprep(self, input: Dict[str, Any]) -> None:
        """Map the adhoc format to the fmpriprep format spec.

        Based on the spec, map the column names to match the fmriprep format.

        It assumes that the data is valid, meaning that all the mapping
        keys are in the confounds dataframe columns and all the mapped
        values are valid fmriprep column names.

        This method modifies the dataframe in place.

        Parameters
        ----------
        input : dict
            Dictionary containing the following keys:
            - data: the confounds file loaded in memory (dataframe)
            - format: format of the confounds file (must be "adhoc")
            - mappings: dictionary containing the mappings from the adhoc
            format to the fmriprep format as a dictionary with key "fmriprep"

        """

        confounds_df = input["data"]
        confounds_mapping = input["mappings"]["fmriprep"]

        # Rename the columns
        confounds_df.rename(columns=confounds_mapping, inplace=True)

    def _process_fmriprep_spec(
        self, input: Dict[str, Any]
    ) -> Tuple[List[str], Dict[str, str], Dict[str, str], str]:
        """Process the fmpriprep format spec from the specified file.

        Based on the strategy, find the relevant column names in the dataframe,
        as well as the required squared and derivatives to compute.

        Parameters
        ----------
        input : dict
            Dictionary containing the following keys:

            * path: path to the confounds file
            * data: the confounds file loaded in memory (dataframe)
            * format: format of the confounds file (must be "fmriprep")

        Returns
        -------
        to_select : list of str
            List of confounds to select from the confounds file, based on the
            strategy
        squares_to_compute : dict
            Dictionary containing the missing power2 confounds to compute
            (keys) and the corresponding confounds to square (values)
        derivatives_to_compute : dict
            Dictionary containing the missing derivatives confounds to compute
            (keys) and the corresponding confounds to compute the derivative
            from (values)
        spike_name : str
            Name of the confound to use for spike detection

        """
        confounds_df = input["data"]
        available_vars = confounds_df.columns

        # This function should build this 3 variables
        to_select = []  # the list of confounds to select
        squares_to_compute = {}  # the dictionary of missing squares
        derivatives_to_compute = {}  # the dictionary of missing derivatives

        for t_kind, t_strategy in self.strategy.items():
            t_basics = FMRIPREP_BASICS[t_kind]

            if any(x not in available_vars for x in t_basics):
                missing = [x for x in t_basics if x not in available_vars]
                raise ValueError(
                    "Invalid confounds file. Missing basic confounds: "
                    f"{missing}. "
                    "Check if this file is really an fmriprep confounds file. "
                    "You can also modify the confound removal strategy."
                )

            to_select.extend(t_basics)

            if t_strategy in ["power2", "full"]:
                for x in t_basics:
                    x_2 = f"{x}_power2"
                    to_select.append(x_2)
                    if x_2 not in available_vars:
                        squares_to_compute[x_2] = x

            if t_strategy in ["derivatives", "full"]:
                for x in t_basics:
                    x_derivative = f"{x}_derivative1"
                    to_select.append(x_derivative)
                    if x_derivative not in available_vars:
                        derivatives_to_compute[x_derivative] = x
                    if t_strategy == "full":
                        x_derivative_2 = f"{x_derivative}_power2"
                        to_select.append(x_derivative_2)
                        if x_derivative_2 not in available_vars:
                            squares_to_compute[x_derivative_2] = x_derivative
        spike_name = "framewise_displacement"
        if self.spike is not None:
            if spike_name not in available_vars:
                raise ValueError(
                    "Invalid confounds file. Missing framewise_displacement "
                    "(spike) confound. "
                    "Check if this file is really an fmriprep confounds file. "
                    "You can also deactivate spike (set spike = None)."
                )
        out = to_select, squares_to_compute, derivatives_to_compute, spike_name
        return out

    def _pick_confounds(self, input: Dict[str, Any]) -> pd.DataFrame:
        """Select relevant confounds from the specified file.

        Parameters
        ----------
        input : dict
            Dictionary containing the "BOLD_confounds" value from the
            Junifer Data object.

        Returns
        -------
        confounds_df : pandas.DataFrame
            Dataframe containing the relevant confounds.

        """

        confounds_format = input["format"]
        if confounds_format == "adhoc":
            self._map_adhoc_to_fmriprep(input)

        processed_spec = self._process_fmriprep_spec(input)

        (
            to_select,
            squares_to_compute,
            derivatives_to_compute,
            spike_name,
        ) = processed_spec
        # Copy the confounds
        out_df = input["data"].copy()

        # Add derivatives if needed
        for t_dst, t_src in derivatives_to_compute.items():
            out_df[t_dst] = np.insert(np.diff(out_df[t_src]), 0, np.nan)

        # Add squares (of base confounds and derivatives) if needed
        for t_dst, t_src in squares_to_compute.items():
            out_df[t_dst] = out_df[t_src] ** 2

        # add binary spike regressor if needed at given threshold
        if self.spike is not None:
            fd = out_df[spike_name].copy()
            fd.loc[fd > self.spike] = 1
            fd.loc[fd != 1] = 0
            out_df["spike"] = fd
            to_select.append("spike")

        # Now pick all the relevant confounds
        out_df = out_df[to_select]

        # Derivatives have NaN on the first row
        # Replace them by estimates at second time point,
        # otherwise nilearn will crash.
        mask_nan = np.isnan(out_df.values[0, :])
        out_df.iloc[0, mask_nan] = out_df.iloc[1, mask_nan]

        return out_df

    def _validate_data(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Validate input data.

        Parameters
        ----------
        input : dict
            Dictionary containing the "BOLD" value from the
            Junifer Data object.
        extra_input : dict, optional
            Dictionary containing the rest of the Junifer Data object. Must
            include the "BOLD_confounds" key.

        """

        # Bold must be 4D niimg
        check_niimg_4d(input["data"])

        if extra_input is None:
            raise_error("No extra input provided", ValueError)
        if "BOLD_confounds" not in extra_input:
            raise_error("No BOLD_confounds provided", ValueError)
        if "data" not in extra_input["BOLD_confounds"]:
            raise_error("No BOLD_confounds data provided", ValueError)
        # Confounds must be a dataframe
        if not isinstance(extra_input["BOLD_confounds"]["data"], pd.DataFrame):
            raise_error(
                "Confounds data must be a pandas dataframe", ValueError
            )

        confound_df = extra_input["BOLD_confounds"]["data"]
        bold_img = input["data"]
        if bold_img.get_fdata().shape[3] != len(confound_df):
            raise_error(
                "Image time series and confounds have different length!\n"
                f"\tImage time series: { bold_img.get_fdata().shape[3]}\n"
                f"\tConfounds: {len(confound_df)}"
            )

        if "format" not in extra_input["BOLD_confounds"]:
            raise_error(
                "Confounds format must be specified in "
                'input["BOLD_confounds"]'
            )

        t_format = extra_input["BOLD_confounds"]["format"]

        if t_format == "adhoc":
            if "mappings" not in extra_input["BOLD_confounds"]:
                raise_error(
                    "When using adhoc format, you must specify "
                    "the variables names mappings in "
                    'input["BOLD_confounds"]["mappings"]'
                )
            if "fmriprep" not in extra_input["BOLD_confounds"]["mappings"]:
                raise_error(
                    "When using adhoc format, you must specify "
                    "the variables names mappings to fmriprep format in "
                    'input["BOLD_confounds"]["mappings"]["fmriprep"]'
                )
            fmriprep_mappings = extra_input["BOLD_confounds"]["mappings"][
                "fmriprep"
            ]
            wrong_names = [
                x
                for x in fmriprep_mappings.values()
                if x not in FMRIPREP_VALID_NAMES
            ]
            if len(wrong_names) > 0:
                raise_error(
                    "The following mapping values are not valid fmriprep "
                    f"names: {wrong_names}"
                )
            # Check that all the required columns are present
            missing = [
                x
                for x in fmriprep_mappings.keys()
                if x not in confound_df.columns
            ]

            if len(missing) > 0:
                raise ValueError(
                    "Invalid confounds file. Missing columns: "
                    f"{missing}. "
                    "Check if this file matches the adhoc specification for "
                    "this dataset."
                )
        elif t_format != "fmriprep":
            raise ValueError(f"Invalid confounds format {t_format}")

    def _remove_confounds(
        self, bold_img: "Nifti1Image", confounds_df: pd.DataFrame
    ) -> Union["Nifti1Image", "Nifti2Image", "MGHImage", List]:
        """Remove confounds from the BOLD image.

        Parameters
        ----------
        bold_img : Niimg-like object
            4D image. The signals in the last dimension are filtered
            (see http://nilearn.github.io/manipulating_images/input_output.html
            for a detailed description of the valid input types).
        confounds_df : pd.DataFrame
            Dataframe containing confounds to remove. Number of rows should
            correspond to number of volumes in the BOLD image.

        Returns
        --------
        Niimg-like object
            Input image with confounds removed.

        """
        confounds_array = confounds_df.values

        t_r = self.t_r
        if t_r is None:
            logger.info("No `t_r` specified, using t_r from nifti header")
            zooms = bold_img.header.get_zooms()  # type: ignore
            t_r = zooms[3]
            logger.info(
                f"Read t_r from nifti header: {t_r}",
            )

        mask_img = self.mask_img
        if mask_img is None:
            logger.info("Computing brain mask from image")
            mask_img = compute_brain_mask(bold_img)

        logger.info("Cleaning image")
        logger.debug(f"\tdetrend: {self.detrend}")
        logger.debug(f"\tstandardize: {self.standardize}")
        logger.debug(f"\tlow_pass: {self.low_pass}")
        logger.debug(f"\thigh_pass: {self.high_pass}")
        clean_bold = clean_img(
            imgs=bold_img,
            detrend=self.detrend,
            standardize=self.standardize,
            confounds=confounds_array,
            low_pass=self.low_pass,
            high_pass=self.high_pass,
            t_r=t_r,
            mask_img=mask_img,
        )

        return clean_bold

    def preprocess(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Preprocess.

        Parameters
        ----------
        input : dict
            A single input from the Junifer Data object in which to preprocess.
        extra_input : dict, optional
            The other fields in the Junifer Data object. Must include the
            ``BOLD_confounds`` key.

        Returns
        -------
        key : str
            The key to store the output in the Junifer Data object.
        object : dict
            The computed result as dictionary. This will be stored in the
            Junifer Data object under the key ``key``.

        """
        self._validate_data(input, extra_input)
        assert extra_input is not None
        bold_img = input["data"]
        confounds_df = self._pick_confounds(extra_input["BOLD_confounds"])
        input["data"] = self._remove_confounds(bold_img, confounds_df)
        return "BOLD", input
