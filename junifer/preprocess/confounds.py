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

    def __init__(
        self,
        strategy={
            'motion': 'full',
            'wm_csf': 'full',
            'global_signal': 'full'
        },
        spike=None,
        detrend=True,
        standardize=True,
        low_pass=None,
        high_pass=None,
        t_r=None,
        mask_img=None
    ):
        """ Initialise a BaseConfoundReader object

        Confound removal is based on nilearn.image.clean_img

        Parameters
        -----------
        strategy : dict
            keys of dictionary should correspond to names of noise components
            to include:
            - 'motion'
            - 'wm_csf'
            - 'global_signal'
            values of dictionary should correspond to types of confounds
            extracted from each signal:
            - 'basic' - only the confounding time series
            - 'power2' - signal + quadratic term
            - 'derivatives' - signal + derivatives
            - 'full' - signal + deriv. + quadratic terms + power2 deriv.
        spike : None (default) | float
            If None, no spike regressor is added. If spike is a float, it will
            add a spike regressor for every point at which FD exceeds the
            specified float.
        detrend : bool
            If detrending should be applied on timeseries
            (before confound removal). Default=True.
        standardize : bool
            If True, returned signals are set to unit variance. Default=True.
        low_pass : float
            Low cutoff frequencies, in Hertz.
        high_pass : float
            High cutoff frequencies, in Hertz.
        t_r : float
            Repetition time, in second (sampling period).
            If set to None it will use t_r from nifti header.
        mask_img: Niimg-like object
            If provided, signal is only cleaned from voxels inside the mask.
            If mask is provided, it should have same shape and affine as imgs.
            If not provided, a mask is computed using
            nilearn.masking.compute_brain_mask

        """

        self.strategy = strategy
        self.spike = spike
        self.detrend = detrend
        self.standardize = standardize
        self.low_pass = low_pass
        self.high_pass = high_pass
        self.t_r = t_r
        self.mask_img = mask_img

        for k, v in self.strategy.items():
            if k not in ['motion', 'wm_csf', 'global_signal']:
                raise_error(
                    f'{k} not a valid noise component to include!\n'
                    f'If {k} is a valid parameter in '
                    'nilearn.interfaces.fmriprep.load_confounds we may '
                    'include it in the future', ValueError
                )
            if v not in ['basic', 'power2', 'derivatives', 'full']:
                raise_error(
                    f'{v} not a valid type of confound to extract from {k} '
                    'signal!', ValueError
                )

    def validate_input(self, input):
        """Validate the input to the pipeline step.

        Parameters
        ----------
        input : Junifer Data dictionary
            The input to the pipeline step.

        Raises
        ------
        ValueError:
            If the input does not have the required data.
        """
        if 'BOLD' not in input:
            raise_error(
                'Input does not have the required data. \n'
                f'Input: {input} \n'
                f'Required: BOLD \n', ValueError
            )
        if 'data' not in input['BOLD']:
            raise_error(
                'Input does not have the required data. \n'
                f'Input: {input} \n'
                f'Required: [\'BOLD\'][\'data\'] \n', ValueError
            )

        # check that keys actually return a valid 4d image
        # and that confounds are a dataframe
        check_niimg_4d(input['BOLD']['data'])
        if not isinstance(input['confounds'], pd.DataFrame):
            raise_error(
                'Input does not have the required data.', ValueError
            )

    def get_output_kind(self, input):
        """Get the kind of the pipeline step.

        Parameters
        ----------
        input : Junifer Data dictionary
            The input to the pipeline step.

        Returns
        -------
        output : Junifer Data dictionary
            The output of the pipeline step.
        """
        return 'BOLD'

    def read_confounds(self, confound_dataframe):
        """ Select relevant confounds from the specified file """

        logger.warning(
            'BaseConfoundRemover removes all confounds from the file without'
            ' applying any selection strategy!'
        )
        return confound_dataframe

    def remove_confounds(self, bold_img, confounds_df):
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

        assert bold_img.get_fdata().shape[3] == confounds_array.shape[0], (
            'Image time series and confounds have different length!'
        )

        if self.t_r is None:
            logger.warning('No t_r specified, using t_r from nifti header!')
            zooms = bold_img.header.get_zooms()
            self.t_r = zooms[3]

        if self.mask_img is None:
            self.mask_img = compute_brain_mask(bold_img)

        clean_bold = clean_img(
            imgs=bold_img,
            detrend=self.detrend,
            standardize=self.standardize,
            confounds=confounds_array,
            low_pass=self.low_pass,
            high_pass=self.high_pass,
            t_r=self.t_r,
            mask_img=self.mask_img
        )

        return clean_bold

    def fit_transform(self, input):
        self.validate_input(input)
        out = {}
        meta = input.get('meta', {})
        bold_img = input['BOLD']['data']
        confounds_df = self.read_confounds(input['confounds'])
        out['BOLD'] = {}
        out['BOLD']['data'] = self.remove_confounds(bold_img, confounds_df)
        out['confounds'] = confounds_df
        out['meta'] = meta

        return out


class FelixConfoundRemover(BaseConfoundRemover):
    """ A class to read confounds from confound files generated by Felix's
    pipeline using CAT and some other custom scripts. It is meant to emulate
    the new nilearn.interfaces.fmriprep.load_confounds as closely as possible.

    """

    def read_confounds(self, confound_dataframe):

        confounds_to_select = []
        # for some confounds we need to manually calculate derivatives using
        # numpy and add them to the output
        derivatives_to_calculate = []

        for comp, param in self.strategy.items():
            if comp == 'motion':
                confounds = []
                # there should be six rigid body parameters
                for i in range(1, 7):
                    # select basic
                    confounds_to_select.append(f'RP.{i}')

                    # select squares
                    if param in ['power2', 'full']:
                        confounds_to_select.append(f'RP^2.{i}')

                    # select derivatives
                    if param in ['derivatives', 'full']:
                        confounds_to_select.append(f'DRP.{i}')

                    # if 'full' we should not forget the derivative
                    # of the squares
                    if param in ['full']:
                        confounds_to_select.append(f'DRP^2.{i}')

            elif comp == 'wm_csf':
                confounds = ['WM', 'CSF']
            elif comp == 'global_signal':
                confounds = ['GS']

            for conf in confounds:

                confounds_to_select.append(conf)

                # select squares
                if param in ['power2', 'full']:
                    confounds_to_select.append(f'{conf}^2')

                # we have to calculate derivatives (not included in felix'
                # confound files)
                if param in ['derivatives', 'full']:
                    derivatives_to_calculate.append(conf)

                if param in ['full']:
                    derivatives_to_calculate.append(f'{conf}^2')

        confounds_to_remove = confound_dataframe[confounds_to_select]

        # calc additional derivatives
        for conf in derivatives_to_calculate:
            confounds_to_remove[f'D{conf}'] = np.append(
                np.diff(confound_dataframe[conf]), 0
            )

        # add binary spike regressor if needed at given threshold
        if self.spike is not None:
            fd = confound_dataframe["FD"].copy()
            fd.loc[fd > self.spike] = 1
            fd.loc[fd != 1] = 0
            confounds_to_remove['spike'] = fd

        return confounds_to_remove


class FmriprepConfoundRemover(BaseConfoundRemover):
    """ A ConfoundRemover class for fmriprep output utilising
    nilearn's nilearn.interfaces.fmriprep.load_confounds
    """

    def read_confounds(self):
        raise NotImplementedError('read_confounds not implemented')
