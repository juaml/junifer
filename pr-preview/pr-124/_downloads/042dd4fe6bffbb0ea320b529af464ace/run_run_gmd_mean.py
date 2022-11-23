"""
UKB VBM GMD Extraction
======================

Authors: Federico Raimondo

License: BSD 3 clause
"""
import tempfile

import junifer.testing.registry  # noqa: F401
from junifer.api import run


datagrabber = {
    "kind": "OasisVBMTestingDatagrabber",
}

markers = [
    {
        "name": "Schaefer1000x7_TrimMean80",
        "kind": "ParcelAggregation",
        "parcellation": "Schaefer1000x7",
        "method": "trim_mean",
        "method_params": {"proportiontocut": 0.2},
    },
    {
        "name": "Schaefer1000x7_Mean",
        "kind": "ParcelAggregation",
        "parcellation": "Schaefer1000x7",
        "method": "mean",
    },
    {
        "name": "Schaefer1000x7_Std",
        "kind": "ParcelAggregation",
        "parcellation": "Schaefer1000x7",
        "method": "std",
    },
]

storage = {
    "kind": "SQLiteFeatureStorage",
}

with tempfile.TemporaryDirectory() as tmpdir:
    uri = f"{tmpdir}/test.sqlite"
    storage["uri"] = uri
    run(
        workdir="/tmp",
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
    )
