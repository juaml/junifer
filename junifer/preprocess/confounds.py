# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

import numpy as np
import pandas as pd

from nilearn._utils.niimg_conversions import check_niimg_4d
from nilearn.masking import compute_brain_mask
from nilearn.image import clean_img

from junifer.markers.base import PipelineStepMixin
from ..utils.logging import logger, raise_error


class BaseConfoundRemover(PipelineStepMixin):
    """ A base class to read confound files and select columns according to
    a pre-defined strategy

    """

    # lower priority
    # TODO: implement more strategies from
    # nilearn.interfaces.fmriprep.load_confounds for Felix's confound files,
    # in particular scrubbing
    # TODO: Implement read_confounds for fmriprep data

    def __init__(self, strategy=None, spike=None, detrend=True,
                 standardize=True, low_pass=None, high_pass=None, t_r=None,
                 mask_img=None):
        """ Initialise a BaseConfoundReader object

        Confound removal is based on nilearn.image.clean_img

        Parameters
        -----------
        strategy : dict[str -> str]
            The keys of the dictionary should correspond to names of noise
            components to include:
            - 'motion'
            - 'wm_csf'
            - 'global_signal'
            The values of dictionary should correspond to types of confounds
            extracted from each signal:
            - 'basic': only the confounding time series
            - 'power2': signal + quadratic term
            - 'derivatives': signal + derivatives
            - 'full': signal + deriv. + quadratic terms + power2 deriv.
        spike : float | None (default)
            If None, no spike regressor is added. If spike is a float, it will
            add a spike regressor for every point at which FD exceeds the
            specified float.
        detrend : bool
            If True (default), detrending will be applied on timeseries
            (before confound removal).
        standardize : bool
            If True (default), returned signals are set to unit variance.
        low_pass : float | None (default)
            Low cutoff frequencies, in Hertz. If None, no filtering is applied.
        high_pass : float | None (default)
            High cutoff frequencies, in Hertz. If None, no filtering is
            applied.
        t_r : float
            Repetition time, in second (sampling period).
            If None (default) it will use t_r from nifti header.
        mask_img: Niimg-like object
            If provided, signal is only cleaned from voxels inside the mask.
            If mask is provided, it should have same shape and affine as imgs.
            If not provided, a mask is computed using
            nilearn.masking.compute_brain_mask
        """
        if strategy is None:
            strategy = {
                'motion': 'full',
                'wm_csf': 'full',
                'global_signal': 'full'
            }

        self.strategy = strategy
        self.spike = spike
        self.detrend = detrend
        self.standardize = standardize
        self.low_pass = low_pass
        self.high_pass = high_pass
        self.t_r = t_r
        self.mask_img = mask_img

        self._valid_components = ['motion', 'wm_csf', 'global_signal']
        self._valid_confounds = ['basic', 'power2', 'derivatives', 'full']

        if any(not isinstance(k, str) for k in strategy.keys()):
            raise_error(
                'Strategy keys must be strings', ValueError
            )

        if any(not isinstance(v, str) for v in strategy.values()):
            raise_error(
                'Strategy values must be strings', ValueError
            )

        if any(x not in self._valid_components for x in strategy.keys()):
            raise_error(
                f'Invalid component names {list(strategy.keys())}. '
                f'Valid components are {self._valid_components}.\n'
                f'If any of them is a valid parameter in '
                'nilearn.interfaces.fmriprep.load_confounds we may '
                'include it in the future', ValueError
            )

        if any(x not in self._valid_confounds for x in strategy.values()):
            raise_error(
                f'Invalid component names {list(strategy.values())}. '
                f'Valid confound types are {self._valid_confounds}.\n'
                f'If any of them is a valid parameter in '
                'nilearn.interfaces.fmriprep.load_confounds we may '
                'include it in the future', ValueError
            )

    def validate_input(self, input):
        """Validate the input to the pipeline step.

        Parameters
        ----------
        input : list[str]
            The input to the pipeline step. The list must contain the
            available Junifer Data dictionary keys.

        Raises
        ------
        ValueError:
            If the input does not have the required data.
        """
        _required_inputs = ['BOLD', 'confounds']
        if any(x not in input for x in _required_inputs):
            raise_error(
                'Input does not have the required data. \n'
                f'Input: {input} \n'
                f'Required (all off): {_required_inputs} \n', ValueError
            )

    def get_output_kind(self, input):
        """Get the kind of the pipeline step.

        Parameters
        ----------
        input : list[str]
            The input to the pipeline step. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        output : list[str]
            The updated list of available Junifer Data dictionary keys after
            the pipeline step.
        """
        # Does not add any new keys
        return input

    def _pick_confounds(self, input):
        """ Select relevant confounds from the specified file """
        to_select = []
        confounds_df = input['data']
        confounds_spec = input['names']['spec']
        derivatives_to_compute = input['names'].get('derivatives', {})
        spike_name = input['names']['spike']

        # Get all the column names according to the strategy
        for comp, param in self.strategy.items():
            to_select.extend(confounds_spec[comp][param])

        # Add derivatives if needed
        to_compute = [x in derivatives_to_compute.keys() for x in to_select]
        out_df = confounds_df.copy()
        if any(to_compute):
            for t_dst, t_src in derivatives_to_compute.items():
                out_df[t_dst] = np.append(  # type: ignore
                    np.diff(out_df[t_src]), 0)  # type: ignore
        out_df = out_df[to_select]
        # add binary spike regressor if needed at given threshold
        if self.spike is not None:
            fd = confounds_df[spike_name].copy()
            fd.loc[fd > self.spike] = 1
            fd.loc[fd != 1] = 0
            out_df['spike'] = fd

        return out_df

    def _remove_confounds(self, bold_img, confounds_df):
        """ Remove confounds from the BOLD image

        bold_img : Niimg-like object
            4D image. The signals in the last dimension are filtered
            (see http://nilearn.github.io/manipulating_images/input_output.html
            for a detailed description of the valid input types).
        confounds_df : pd.DataFrame
            Dataframe containing confounds to remove. Number of rows should
            correspond to number of volumes in the BOLD image.

        returns
        --------
        clean_bold : Niimg-like object
            input image, cleaned.

        """

        confounds_array = confounds_df.values

        t_r = self.t_r
        if t_r is None:
            logger.info('No t_r specified, using t_r from nifti header!')
            zooms = bold_img.header.get_zooms()
            t_r = zooms[3]
            logger.info(f'Read t_r from nifti header: {t_r}', )

        mask_img = self.mask_img
        if mask_img is None:
            logger.info('Computing brain mask from image')
            mask_img = compute_brain_mask(bold_img)

        clean_bold = clean_img(
            imgs=bold_img,
            detrend=self.detrend,
            standardize=self.standardize,
            confounds=confounds_array,
            low_pass=self.low_pass,
            high_pass=self.high_pass,
            t_r=t_r,
            mask_img=mask_img
        )

        return clean_bold

    def _validate_data(self, input):
        # Bold must be 4D niimg
        check_niimg_4d(input['BOLD']['data'])

        # Confounds must be a dataframe
        if not isinstance(input['confounds']['data'], pd.DataFrame):
            raise_error(
                'confounds data must be a pandas dataframe', ValueError
            )

        confound_df = input['confounds']['data']
        bold_img = input['BOLD']['data']
        if bold_img.get_fdata().shape[3] != len(confound_df):
            raise_error(
                'Image time series and confounds have different length!\n'
                f'\tImage time series: { bold_img.get_fdata().shape[3]}\n'
                f'\tConfounds: {len(confound_df)}')

        # Check the column names of the dataframe and the spec
        # spec must be a dictionary:
        # {
        # 'motion': {
        #     'basic': [(list of columns)]
        #     'power2', [(list of columns)]
        #     'derivatives', [(list of columns)]
        #     'full', [(list of columns)]},
        # 'wm_csf': {
        #     'basic': [(list of columns)]
        #     'power2', [(list of columns)]
        #     'derivatives', [(list of columns)]
        #     'full', [(list of columns)]}
        # 'global_signal': {
        #     'basic': [(list of columns)]
        #     'power2', [(list of columns)]
        #     'derivatives', [(list of columns)]
        #     'full', [(list of columns)]}
        # }

        # Check the columns in the dataframe
        conf_spec = input['confounds']['names']['spec']
        if any(x not in conf_spec.keys() for x in self._valid_components):
            raise_error(
                'All of the component types must be in the confounds data '
                'object `spec`. Please check your datagrabber.', ValueError)

        if any(x not in v.keys() for x in self._valid_confounds
               for v in conf_spec.values()):
            raise_error(
                'All of the confound types must be in the confounds data '
                'object `spec`. Please check your datagrabber.', ValueError)

        spike_name = input['confounds']['names']['spike']

        derivatives_to_compute = input['confounds']['names'].get(
            'derivatives', {})
        if not(isinstance(derivatives_to_compute, dict)):
            raise_error(
                'input["confounds"]["names"]["derivatives"] '
                'must be a dictionary. Please check your datagrabber',
                ValueError)

        if any(not (isinstance(k, str) or isinstance(v, str))
               for k, v in derivatives_to_compute.items()):
            raise_error(
                'input["confounds"]["names"]["derivatives"] '
                'must be a dictionary with string keys and values. '
                'Please check your datagrabber',
                ValueError)

        missing_derivatives = [
            x for x in derivatives_to_compute.values()
            if x not in confound_df.columns]
        if len(missing_derivatives) > 0:
            raise_error(
                'Some of the derivatives to calculate are not in the confounds'
                f' dataframe: {missing_derivatives}.'
                'Please check your data '
                f'({input["confounds"]["path"].as_posix()}) '
                'and the datagrabber.', ValueError)

        t_conf_spec = {k: input['confounds']['names']['spec'][k][v]
                       for k, v in self.strategy.items()}

        column_names = set([x for y in t_conf_spec.values() for x in y])
        column_names.add(spike_name)

        missing_columns = [
            x for x in column_names
            if x not in confound_df.columns and
            x not in derivatives_to_compute.keys()]

        if len(missing_columns) > 0:
            raise_error(
                'Some of the columns in the confound spec are not in the '
                f'confounds dataframe: {missing_columns}. '
                'Please check your data '
                f'({input["confounds"]["path"].as_posix()}) '
                'and the datagrabber.', ValueError)

    def fit_transform(self, input):
        self._validate_data(input)
        bold_img = input['BOLD']['data']
        confounds_df = self._pick_confounds(input['confounds'])
        input['BOLD']['data'] = self._remove_confounds(bold_img, confounds_df)

        # TODO: Update meta
        return input


# class FelixConfoundRemover(BaseConfoundRemover):
#     """ A class to read confounds from confound files generated by Felix's
#     pipeline using CAT and some other custom scripts. It is meant to emulate
#     the new nilearn.interfaces.fmriprep.load_confounds as closely as
#     possible.

#     """

#     def read_confounds(self, confound_dataframe):

#         confounds_to_select = []
#         # for some confounds we need to manually calculate derivatives using
#         # numpy and add them to the output
#         derivatives_to_compute = []

#         for comp, param in self.strategy.items():
#             if comp == 'motion':
#                 confounds = []
#                 # there should be six rigid body parameters
#                 for i in range(1, 7):
#                     # select basic
#                     confounds_to_select.append(f'RP.{i}')

#                     # select squares
#                     if param in ['power2', 'full']:
#                         confounds_to_select.append(f'RP^2.{i}')

#                     # select derivatives
#                     if param in ['derivatives', 'full']:
#                         confounds_to_select.append(f'DRP.{i}')

#                     # if 'full' we should not forget the derivative
#                     # of the squares
#                     if param in ['full']:
#                         confounds_to_select.append(f'DRP^2.{i}')

#             elif comp == 'wm_csf':
#                 confounds = ['WM', 'CSF']
#             elif comp == 'global_signal':
#                 confounds = ['GS']

#             for conf in confounds:

#                 confounds_to_select.append(conf)

#                 # select squares
#                 if param in ['power2', 'full']:
#                     confounds_to_select.append(f'{conf}^2')

#                 # we have to calculate derivatives (not included in felix'
#                 # confound files)
#                 if param in ['derivatives', 'full']:
#                     derivatives_to_compute.append(conf)

#                 if param in ['full']:
#                     derivatives_to_compute.append(f'{conf}^2')

#         confounds_to_remove = confound_dataframe[confounds_to_select]

#         # calc additional derivatives
#         for conf in derivatives_to_compute:
#             confounds_to_remove[f'D{conf}'] = np.append(
#                 np.diff(confound_dataframe[conf]), 0
#             )

#         # add binary spike regressor if needed at given threshold
#         if self.spike is not None:
#             fd = confound_dataframe["FD"].copy()
#             fd.loc[fd > self.spike] = 1
#             fd.loc[fd != 1] = 0
#             confounds_to_remove['spike'] = fd

#         return confounds_to_remove


# class FmriprepConfoundRemover(BaseConfoundRemover):
#     """ A ConfoundRemover class for fmriprep output utilising
#     nilearn's nilearn.interfaces.fmriprep.load_confounds
#     """

#     def read_confounds(self):
#         raise NotImplementedError('read_confounds not implemented')
