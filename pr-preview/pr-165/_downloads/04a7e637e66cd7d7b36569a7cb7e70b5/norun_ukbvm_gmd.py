"""
UKB VBM GMD Extraction
======================

Authors: Federico Raimondo

License: BSD 3 clause
"""


from junifer.api import run


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

run(
    workdir="/tmp",
    datagrabber="JuselessUKBVBM",
    elements=("sub-1627474", "ses-2"),
    markers=markers,
    storage="SQLDataFrameStorage",
    storage_params={"outpath": "/data/project/juniferexample"},
)
