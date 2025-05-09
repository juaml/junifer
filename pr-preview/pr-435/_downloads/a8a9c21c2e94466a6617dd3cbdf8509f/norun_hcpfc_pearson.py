"""
HCP FC Extraction
======================

Authors: Leonard Sasse
License: BSD 3 clause
"""


from junifer.api import run


datagrabber = {
    "kind": "HCPOpenAccess",
    "modality": "fMRI",
    "preprocessed": "ICA+FIX",
    "space": "volumetric",
}

custom_confound_strategy = {
    "filter": "butterworth",
    "detrend": True,
    "high_pass": 0.01,
    "low_pass": 0.08,
    "standardize": True,
    "confounds": ["csf", "wm", "gsr"],
    "derivatives": True,
    "squares": True,
    "other": [],
}

markers = [
    {
        "name": "Power264_FCPearson",
        "kind": "FunctionalConnectivity",
        "parcellation": "Power264",
        "method": "Pearson",
        "confound_strategy": "Params36",
    },
    {
        "name": "Schaefer400x17_FCPearson",
        "kind": "FunctionalConnectivity",
        "parcellation": "Schaefer400x17",
        "method": "Pearson",
        "confound_strategy": "Params24",
    },
    {
        "name": "Power264_FCSpearman",
        "kind": "FunctionalConnectivity",
        "parcellation": "Power264",
        "method": "Spearman",
        "confound_strategy": "ICAAROMA",
    },
    {
        "name": "Schaefer400x17_FCSpearman",
        "kind": "FunctionalConnectivity",
        "parcellation": "Schaefer400x17",
        "method": "Spearman",
        "confound_strategy": "path/to/predefined/confound_file.tsv",
    },
    {
        "name": "Schaefer400x17_FCSpearman",
        "kind": "FunctionalConnectivity",
        "parcellation": "Schaefer400x17",
        "method": "Spearman",
        "confound_strategy": custom_confound_strategy,
    },
]

storage = {
    "kind": "SQLiteFeatureStorage",
    "uri": "/data/project/juniferexample",
}

run(
    workdir="/tmp",
    datagrabber=datagrabber,
    elements=[("100408", "REST1", "LR")],
    markers=markers,
    storage=storage,
)
