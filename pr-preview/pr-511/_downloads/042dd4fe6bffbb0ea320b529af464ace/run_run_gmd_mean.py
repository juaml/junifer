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
    "kind": "OasisVBMTestingDataGrabber",
}

markers = [
    {
        "name": "extDMN_TrimMean80",
        "kind": "SphereAggregation",
        "coords": "extDMN",
        "radius": 5.0,
        "masks": "compute_brain_mask",
        "method": "trim_mean",
        "method_params": {"proportiontocut": 0.2},
    },
    {
        "name": "extDMN_Mean",
        "kind": "SphereAggregation",
        "coords": "extDMN",
        "radius": 5.0,
        "masks": "compute_brain_mask",
        "method": "mean",
    },
    {
        "name": "extDMN_Std",
        "kind": "SphereAggregation",
        "coords": "extDMN",
        "radius": 5.0,
        "masks": "compute_brain_mask",
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
