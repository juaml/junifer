"""Provide class for confound removal using fMRIPrep format."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

import numpy as np
import pandas as pd
from nilearn import image as nimg
from nilearn._utils.niimg_conversions import check_niimg_4d

from ...api.decorators import register_preprocessor
from ...data import get_mask
from ...utils import logger, raise_error
from ..base import BasePreprocessor


__all__ = ["fMRIPrepConfoundRemover"]


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
# NOTE: Check with @fraimondo about the spike mapping intent
# Add spike_name to FMRIPREP_VALID_NAMES
FMRIPREP_VALID_NAMES.append("framewise_displacement")


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
    masks : str, dict or list of dict or str, optional
        The specification of the masks to apply to regions before extracting
        signals. Check :ref:`Using Masks <using_masks>` for more details.
        If None, will not apply any mask (default None).

    """

    _DEPENDENCIES: ClassVar[Set[str]] = {"numpy", "nilearn"}

    def __init__(
        self,
        strategy: Optional[Dict[str, str]] = None,
        spike: Optional[float] = None,
        detrend: bool = True,
        standardize: bool = True,
        low_pass: Optional[float] = None,
        high_pass: Optional[float] = None,
        t_r: Optional[float] = None,
        masks: Union[str, Dict, List[Union[Dict, str]], None] = None,
    ) -> None:
        """Initialize the class."""
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
        self.masks = masks

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
        super().__init__(on="BOLD", required_data_types=["BOLD"])

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
            The input to the preprocessor.

        Returns
        -------
        str
            The data type output by the preprocessor.

        """
        # Does not add any new keys
        return input_type

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

            * ``data`` : the confounds file loaded in memory (dataframe)
            * ``format`` : format of the confounds file (must be "adhoc")
            * ``mappings`` : dictionary containing the mappings from the adhoc
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

            * ``path`` : path to the confounds file
            * ``data`` : the confounds file loaded in memory (dataframe)
            * ``format`` : format of the confounds file (must be "fmriprep")

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

        Raises
        ------
        ValueError
            If invalid confounds file is found.

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
                raise_error(
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
                raise_error(
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
            Dictionary containing the ``BOLD.confounds`` value from the
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
            If ``"confounds"`` is not found in ``input`` or
            if ``"data"`` key is not found in ``"input.confounds"`` or
            if ``"input.confounds.data"`` is not pandas.DataFrame or
            if image time series and confounds have different lengths or
            if ``format = "adhoc"`` and ``"mappings"`` key is not found or
            ``"fmriprep"`` key is not found in ``"mappings"`` or
            ``"fmriprep"`` has incorrect fMRIPrep mappings or required
            fMRIPrep mappings are not found or
            if invalid confounds format is found.

        """
        # BOLD must be 4D niimg
        check_niimg_4d(input["data"])
        # Check for confound data
        if "confounds" not in input:
            raise_error("`BOLD.confounds` data type not provided")
        if "data" not in input["confounds"]:
            raise_error("`BOLD.confounds.data` not provided")
        # Confounds must be a pandas.DataFrame;
        # if extension is unknown, will not be read, which will give None
        if not isinstance(input["confounds"]["data"], pd.DataFrame):
            raise_error("`BOLD.confounds.data` must be a `pandas.DataFrame`")

        confound_df = input["confounds"]["data"]
        bold_img = input["data"]
        if bold_img.get_fdata().shape[3] != len(confound_df):
            raise_error(
                "Image time series and confounds have different length!\n"
                f"\tImage time series: { bold_img.get_fdata().shape[3]}\n"
                f"\tConfounds: {len(confound_df)}"
            )

        # Check format
        t_format = input["confounds"]["format"]
        if t_format == "adhoc":
            if "mappings" not in input["confounds"]:
                raise_error(
                    "`BOLD.confounds.mappings` need to be set when "
                    "`BOLD.confounds.format == 'adhoc'`"
                )
            if "fmriprep" not in input["confounds"]["mappings"]:
                raise_error(
                    "`BOLD.confounds.mappings.fmriprep` need to be set when "
                    "`BOLD.confounds.format == 'adhoc'`"
                )
            fmriprep_mappings = input["confounds"]["mappings"]["fmriprep"]
            wrong_names = [
                x
                for x in fmriprep_mappings.values()
                if x not in FMRIPREP_VALID_NAMES
            ]
            if len(wrong_names) > 0:
                raise_error(
                    "The following mapping values are not valid fMRIPrep "
                    f"names: {wrong_names}"
                )
            # Check that all the required columns are present
            missing = [
                x
                for x in fmriprep_mappings.keys()
                if x not in confound_df.columns
            ]

            if len(missing) > 0:
                raise_error(
                    "Invalid confounds file. Missing columns: "
                    f"{missing}. "
                    "Check if this file matches the adhoc specification for "
                    "this dataset."
                )
        elif t_format != "fmriprep":
            raise_error(f"Invalid confounds format {t_format}")

    def preprocess(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Dict[str, Any]]]]:
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
        # Pick confounds
        confounds_df = self._pick_confounds(input["confounds"])  # type: ignore
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
        # Set mask data
        mask_img = None
        if self.masks is not None:
            logger.debug(f"Masking with {self.masks}")
            mask_img = get_mask(
                masks=self.masks, target_data=input, extra_input=extra_input
            )
            # Return the BOLD mask and link it to the BOLD data type dict;
            # this allows to use "inherit" down the pipeline
            logger.debug("Setting `BOLD.mask`")
            input.update(
                {
                    "mask": {
                        "data": mask_img,
                        "space": input["space"],
                    }
                }
            )
        # Clean image
        logger.info("Cleaning image using nilearn")
        logger.debug(f"\tdetrend: {self.detrend}")
        logger.debug(f"\tstandardize: {self.standardize}")
        logger.debug(f"\tlow_pass: {self.low_pass}")
        logger.debug(f"\thigh_pass: {self.high_pass}")
        input["data"] = nimg.clean_img(
            imgs=bold_img,
            detrend=self.detrend,
            standardize=self.standardize,
            confounds=confounds_df.values,
            low_pass=self.low_pass,
            high_pass=self.high_pass,
            t_r=t_r,
            mask_img=mask_img,
        )

        return input, None
