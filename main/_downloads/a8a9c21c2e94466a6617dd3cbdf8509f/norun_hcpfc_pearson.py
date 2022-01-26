"""
HCP FC Extraction
======================
Authors: Leonard Sasse
License: BSD 3 clause
"""


from junifer.api import run_pipeline

custom_confound_strategy = {
    'filter': 'butterworth',
    'detrend': True,
    'high_pass': 0.01,
    'low_pass': 0.08,
    'standardize': True,
    'confounds': ['csf', 'wm', 'gsr'],
    'derivatives': True,
    'squares': True,
    'other': []
}

markers = [
    {'name': 'Power264_FCPearson',
     'kind': 'FunctionalConnectivity',
     'atlas': 'Power264',
     'method': 'Pearson',
     'confound_strategy': 'Params36'},
    {'name': 'Schaefer400x17_FCPearson',
     'kind': 'FunctionalConnectivity',
     'atlas': 'Schaefer400x17',
     'method': 'Pearson',
     'confound_strategy': 'Params24'},
    {'name': 'Power264_FCSpearman',
     'kind': 'FunctionalConnectivity',
     'atlas': 'Power264',
     'method': 'Spearman',
     'confound_strategy': 'ICAAROMA'},
    {'name': 'Schaefer400x17_FCSpearman',
     'kind': 'FunctionalConnectivity',
     'atlas': 'Schaefer400x17',
     'method': 'Spearman',
     'confound_strategy': 'path/to/predefined/confound_file.tsv'}
    {'name': 'Schaefer400x17_FCSpearman',
     'kind': 'FunctionalConnectivity',
     'atlas': 'Schaefer400x17',
     'method': 'Spearman',
     'confound_strategy': custom_confound_strategy}
]

dg_params = {
    'modality': 'fMRI',
    'tasks':  ['REST1', 'REST2', 'SOCIAL'],
    'phase_encoding': ('LR', 'RL'),
    'preprocessed': 'ICA+FIX',
    'space': 'volumetric',
}

run_pipeline(
    workdir='/tmp',
    datagrabber='HCPOpenAccess',
    datagrabber_params = dg_params,
    element='100408',
    markers=markers,
    storage='SQLDataFrameStorage',
    storage_params={'outpath': '/data/project/juniferexample'},
)
