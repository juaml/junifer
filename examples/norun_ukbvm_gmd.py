"""
UKB VBM GMD Extraction
======================

Authors: Federico Raimondo

License: BSD 3 clause
"""


from junifer.api import run_pipeline

markers = [
    {'name': 'Schaefer1000x7_TrimMean80',
     'kind': 'ParcelAggregation',
     'atlas': 'Schaefer1000x7',
     'method': 'trimmean80'},
    {'name': 'Schaefer1000x7_Mean',
     'kind': 'ParcelAggregation',
     'atlas': 'Schaefer1000x7',
     'method': 'mean'},
    {'name': 'Schaefer1000x7_Std',
     'kind': 'ParcelAggregation',
     'atlas': 'Schaefer1000x7',
     'method': 'std'}
]

run_pipeline(
    workdir='/tmp',
    datagrabber='JuselessUKBVBM',
    element='sub-1627474',
    markers=markers,
    storage='SQLDataFrameStorage',
    storage_params={'outpath': '/data/project/juniferexample'},
)
