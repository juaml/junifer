# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

import numpy as np
import pandas as pd
from nibabel import Nifti1Image
from nilearn._utils.niimg_conversions import check_niimg_4d
import random
import string
from junifer.preprocess.confounds import FelixConfoundRemover

np.random.seed(1234567)


def generate_conf_name(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def _simu_img():

    # Random 4D volume with 100 time points
    vol = 100 + 10 * np.random.randn(5, 5, 2, 100)
    img = Nifti1Image(vol, np.eye(4))
    # Create an nifti image with the data, and corresponding mask
    mask = Nifti1Image(np.ones([5, 5, 2]), np.eye(4))
    return img, mask


def test_felixconfoundremover():
    # Generate a simulated BOLD img
    siimg, simsk = _simu_img()

    # generate random confound dataframe with Felix's column naming
    confound_column_names = []

    confound_column_names.append('FD')

    for i in range(1, 7):
        confound_column_names.append(f'RP.{i}')
        confound_column_names.append(f'RP^2.{i}')
        confound_column_names.append(f'DRP.{i}')
        confound_column_names.append(f'DRP^2.{i}')

    for conf in ['WM', 'CSF', 'GS']:
        confound_column_names.append(conf)
        confound_column_names.append(f'{conf}^2')

    # add some random irrelevant confounds
    for i in range(10):
        confound_column_names.append(generate_conf_name())

    np.random.shuffle(confound_column_names)
    n_cols = len(confound_column_names)
    confounds_df = pd.DataFrame(
        np.random.randint(0, 100, size=(100, n_cols)),
        columns=confound_column_names
    )

    # generate confound removal strategies with varying numbers of parameters
    list_of_strategy_tuples = []

    # 36 params
    strat1 = {
        'motion': 'full',
        'wm_csf': 'full',
        'global_signal': 'full'
    }
    list_of_strategy_tuples.append((strat1, 36))

    # 24 params
    strat2 = {
        'motion': 'full',
    }
    list_of_strategy_tuples.append((strat2, 24))

    # 9 params
    strat3 = {
        'motion': 'basic',
        'wm_csf': 'basic',
        'global_signal': 'basic'
    }
    list_of_strategy_tuples.append((strat3, 9))

    # 6 params
    strat4 = {
        'motion': 'basic',
    }
    list_of_strategy_tuples.append((strat4, 6))

    # 2 params
    strat5 = {
        'wm_csf': 'basic',
    }
    list_of_strategy_tuples.append((strat5, 2))

    # generate a junifer pipeline data object dictionary
    input_data_obj = {}
    input_data_obj['meta'] = {}
    input_data_obj['BOLD'] = {}
    input_data_obj['BOLD']['data'] = siimg
    input_data_obj['confounds'] = confounds_df

    # run confound removal
    for spike in [None, 0.25]:
        for strategy, n_params in list_of_strategy_tuples:
            FCR = FelixConfoundRemover(
                strategy=strategy,
                spike=spike,
                mask_img=simsk,
                t_r=0.75
            )

            # first test some methods manually
            FCR.validate_input(input_data_obj)
            out_type = FCR.get_output_kind(input_data_obj)

            assert out_type in ['BOLD']

            selected_conf_frame = FCR.read_confounds(confounds_df)
            timepoints, n_sel_confs = selected_conf_frame.shape

            assert timepoints == 100
            assert isinstance(selected_conf_frame, pd.DataFrame)

            if spike is None:
                assert n_sel_confs == n_params
            else:
                assert n_sel_confs == n_params + 1

            cl_bold = FCR.remove_confounds(siimg, selected_conf_frame)
            check_niimg_4d(cl_bold)

            # finally test fit_transform
            output_data_obj = FCR.fit_transform(input_data_obj)

            for key in ['BOLD', 'confounds', 'meta']:
                assert key in output_data_obj

            check_niimg_4d(output_data_obj['BOLD']['data'])
