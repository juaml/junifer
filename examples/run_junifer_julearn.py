"""
Run junifer and julearn.
========================

This example uses a ParcelAggregation marker to compute the mean of each parcel
of the Tian subcortical parcellation (scale II, 32 ROIs) for a 3D nifti to
extract some features for machine learning using julearn to predict some other
data.

Authors: Leonard Sasse, Sami Hamdan, Nicolas Nieto, Synchon Mandal

License: BSD 3 clause
"""

import tempfile

from julearn import run_cross_validation, PipelineCreator

import junifer.testing.registry  # noqa: F401
from junifer.api import collect, run
from junifer.storage import HDF5FeatureStorage
from junifer.testing.datagrabbers import UCLACNPVBMTestingDataGrabber
from junifer.utils import configure_logging


###############################################################################
# Set the logging level to info to see extra information:
configure_logging(level="INFO")


###############################################################################
# Define the markers you want:

marker_dicts = [
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
]


###############################################################################
# Define target and confounds for julearn machine learning:
y = "age"
confound = "sex"


###############################################################################
# Load the phenotype data of the UCLA CNP subjects (OpenNeuro ds000030) for
# machine learning:
with UCLACNPVBMTestingDataGrabber() as dg:
    participants = dg.get_participants()


###############################################################################
# Create a temporary directory for junifer feature extraction:
with tempfile.TemporaryDirectory() as tmpdir:
    storage = {"kind": "HDF5FeatureStorage", "uri": f"{tmpdir}/test.hdf5"}
    # run the defined junifer feature extraction pipeline
    run(
        workdir="/tmp",
        datagrabber={"kind": "UCLACNPVBMTestingDataGrabber"},
        markers=marker_dicts,
        storage=storage,
    )

    # read in extracted features and add confounds and targets
    # for julearn run cross validation
    collect(storage)
    db = HDF5FeatureStorage(uri=storage["uri"])

    df_vbm = db.read_df(feature_name="VBM_GM_TianxS2_Mean_aggregation")
    df_vbm.index = [x[0] for x in df_vbm.index]


###############################################################################
# Using julearn for machine learning:
# We predict the age given our vbm features and sex as a confound.
X = list(df_vbm.columns)
# Match the phenotypes to the subjects by their identifier
df_vbm[y] = participants.loc[df_vbm.index, "age"].to_numpy()
df_vbm[confound] = (
    participants.loc[df_vbm.index, "gender"] == "F"
).to_numpy(dtype=int)

X_types = {
    "features": X,
    "confound": confound,
}

creator = PipelineCreator(problem_type="regression", apply_to="features")
creator.add("zscore", apply_to=["features", "confound"])
creator.add("confound_removal", apply_to="features", confounds="confound")
creator.add("ridge")

scores = run_cross_validation(
    X=X + [confound],
    y=y,
    X_types=X_types,
    data=df_vbm,
    model=creator,
    cv=3,
)
print(scores)

###############################################################################
# Interpretation of results:
# Doing machine learning with only 10 datapoints is not meaningful.
# This explains the big variation in scores
# for different cross-validation folds.
