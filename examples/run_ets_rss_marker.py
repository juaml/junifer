"""
Run junifer and julearn.
========================
This example uses a ParcelAggregation marker to compute the mean of each parcel
using the Schaefer atlas (100 rois, 7 Yeo networks) for a 3D nifti to extract
some features for machine learning using julearn to predict some other data.
Authors: Leonard Sasse, Sami Hamdan, Nicolas Nieto, Synchon Mandal
License: BSD 3 clause
"""

import tempfile

import nilearn
import pandas as pd
from julearn import run_cross_validation

import junifer.testing.registry
from junifer.api import collect, run
from junifer.storage.sqlite import SQLiteFeatureStorage
from junifer.utils import configure_logging
from ptpython.ipython import embed

###############################################################################
# Set the logging level to info to see extra information:
configure_logging(level="INFO")


###############################################################################
# Define the markers you want:

marker_dicts = [
    {
        "name": "Schaefer100x17_RSSETS",
        "kind": "RSSETSMarker",
        "atlas": "Schaefer100x17",
    },
    {
        "name": "Schaefer200x17_RSSETS",
        "kind": "RSSETSMarker",
        "atlas": "Schaefer200x17",
    },
]


###############################################################################
# Create a temporary directory for junifer feature extraction:
# At the end you can read the extracted data into a pandas.DataFrame.
with tempfile.TemporaryDirectory() as tmpdir:

    storage = {"kind": "SQLiteFeatureStorage", "uri": f"{tmpdir}/test.db"}
    # run the defined junifer feature extraction pipeline 
    run(
        workdir="/tmp",
        datagrabber={"kind": "SPMAuditoryTestingDatagrabber"},
        markers=marker_dicts,
        storage=storage,
    )

    # read in extracted features and add confounds and targets
    # for julearn run cross validation
    # This will not run for now as store_timeseries() is not implemented yet
    collect(storage)
    db = SQLiteFeatureStorage(uri=storage["uri"], single_output=True)
    df_vbm = db.read_df(feature_name="Schaefer100x17")
