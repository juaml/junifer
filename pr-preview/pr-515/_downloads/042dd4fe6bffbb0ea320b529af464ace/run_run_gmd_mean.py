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
    "kind": "UCLACNPVBMTestingDataGrabber",
}

markers = [
    {
        "name": "TianxS2_TrimMean80",
        "kind": "ParcelAggregation",
        "parcellation": "TianxS2x3TxMNInonlinear2009cAsym",
        "method": "trim_mean",
        "method_params": {"proportiontocut": 0.2},
    },
    {
        "name": "TianxS2_Mean",
        "kind": "ParcelAggregation",
        "parcellation": "TianxS2x3TxMNInonlinear2009cAsym",
        "method": "mean",
    },
    {
        "name": "TianxS2_Std",
        "kind": "ParcelAggregation",
        "parcellation": "TianxS2x3TxMNInonlinear2009cAsym",
        "method": "std",
    },
]

storage = {
    "kind": "HDF5FeatureStorage",
}

with tempfile.TemporaryDirectory() as tmpdir:
    uri = f"{tmpdir}/test.hdf5"
    storage["uri"] = uri
    run(
        workdir="/tmp",
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
    )
