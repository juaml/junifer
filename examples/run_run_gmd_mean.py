"""
UKB VBM GMD Extraction
======================

Authors: Federico Raimondo

License: BSD 3 clause
"""
import tempfile

from junifer.api import run
from junifer.testing import register_testing


register_testing()

markers = [
    {'name': 'Schaefer1000x7_TrimMean80',
     'kind': 'ParcelAggregation',
     'atlas': 'Schaefer1000x7',
     'method': 'trim_mean',
     'method_params': {'proportiontocut': 0.2}},
    {'name': 'Schaefer1000x7_Mean',
     'kind': 'ParcelAggregation',
     'atlas': 'Schaefer1000x7',
     'method': 'mean'},
    {'name': 'Schaefer1000x7_Std',
     'kind': 'ParcelAggregation',
     'atlas': 'Schaefer1000x7',
     'method': 'std'}
]

with tempfile.TemporaryDirectory() as tmpdir:
    uri = f'{tmpdir}/test.db'
    run(
        workdir='/tmp',
        datagrabber='OasisVBMTestingDatagrabber',
        markers=markers,
        storage='SQLiteFeatureStorage',
        storage_params={'uri': uri},
    )
