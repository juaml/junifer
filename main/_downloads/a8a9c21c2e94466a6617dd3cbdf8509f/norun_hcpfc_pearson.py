"""
HCP FC Extraction
======================
Authors: Leonard Sasse
License: BSD 3 clause
"""


from junifer.api import run_pipeline

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
     'method': 'Spearman'
     'confound_strategy': 'ICAAROMA'},
    {'name': 'Schaefer400x17_FCSpearman',
     'kind': 'FunctionalConnectivity',
     'atlas': 'Schaefer400x17',
     'method': 'Spearman'
     'confound_strategy': 'path/to/predefined/confound_file.tsv'}
]

run_pipeline(
    workdir='/tmp',
    datagrabber='HCPOpenAccess',
    element='100408',
    markers=markers,
    storage='SQLDataFrameStorage',
    storage_params={'outpath': '/data/project/juniferexample'},
)
