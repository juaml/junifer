"""
Run junifer and julearn.
========================

This example uses a ParcelAggregation marker to compute the mean of each parcel
using the Schaefer parcellation (100 rois, 7 Yeo networks) for a 3D nifti to
extract some features for machine learning using julearn to predict some other
data.

Authors: Leonard Sasse, Sami Hamdan, Nicolas Nieto, Synchon Mandal

License: BSD 3 clause
"""

import tempfile

import nilearn
import pandas as pd
from julearn import run_cross_validation

import junifer.testing.registry  # noqa
from junifer.api import collect, run
from junifer.storage.sqlite import SQLiteFeatureStorage
from junifer.utils import configure_logging


###############################################################################
# Set the logging level to info to see extra information:
configure_logging(level="INFO")


###############################################################################
# Define the markers you want:

marker_dicts = [
    {
        "name": "Schaefer100x17_TrimMean80",
        "kind": "ParcelAggregation",
        "parcellation": "Schaefer100x17",
        "method": "trim_mean",
        "method_params": {"proportiontocut": 0.2},
    },
    {
        "name": "Schaefer200x17_Mean",
        "kind": "ParcelAggregation",
        "parcellation": "Schaefer200x17",
        "method": "mean",
    },
]


###############################################################################
# Define target and confounds for julearn machine learning:
y = "age"
confound = "sex"


###############################################################################
# Load the VBM phenotype data for machine learning data:
# - Fetch the Oasis dataset
oasis_dataset = nilearn.datasets.fetch_oasis_vbm()
age = oasis_dataset.ext_vars[y][:10]
sex = (
    pd.Series(oasis_dataset.ext_vars["mf"][:10])
    .map(lambda x: 1 if x == "F" else 0)
    .values
)


###############################################################################
# Create a temporary directory for junifer feature extraction:
with tempfile.TemporaryDirectory() as tmpdir:

    storage = {"kind": "SQLiteFeatureStorage", "uri": f"{tmpdir}/test.sqlite"}
    # run the defined junifer feature extraction pipeline
    run(
        workdir="/tmp",
        datagrabber={"kind": "OasisVBMTestingDatagrabber"},
        markers=marker_dicts,
        storage=storage,
    )

    # read in extracted features and add confounds and targets
    # for julearn run cross validation
    collect(storage)
    db = SQLiteFeatureStorage(uri=storage["uri"])

    df_vbm = db.read_df(feature_name="VBM_GM_Schaefer200x17_Mean")
    oasis_subjects = [x[0] for x in df_vbm.index]
    df_vbm.index = oasis_subjects


###############################################################################
# Using julearn for machine learning:
# We predict the age given our vbm features and sex as a confound.
X = list(df_vbm.columns)
df_vbm[y] = age
df_vbm[confound] = sex

scores = run_cross_validation(
    X=X,
    confounds=confound,
    y=y,
    data=df_vbm,
    problem_type="regression",
    model="ridge",
    cv=3,
    preprocess_X=["zscore", "remove_confound"],
)
print(scores)

###############################################################################
# Interpretation of results:
# Doing machine learning with only 10 datapoints is not meaningful.
# This explains the big variation in scores
# for different cross-validation folds.
