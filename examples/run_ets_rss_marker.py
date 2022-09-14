"""

Extracting root sum of squares from edge-wise timeseries.
=========================================================
This example uses a RSSETSMarker to compute root sum of squares
of the edge-wise timeseries using the Schaefer atlas
(100 rois and 200 rois, 17 Yeo networks) for a 4D nifti BOLD file.

Authors: Leonard Sasse, Sami Hamdan, Nicolas Nieto, Synchon Mandal

License: BSD 3 clause

"""

import tempfile

import junifer.testing.registry  # noqa: F401
from junifer.utils import configure_logging


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
# At the end you can read the extracted data into a ``pandas.DataFrame``.
with tempfile.TemporaryDirectory() as tmpdir:

    storage = {"kind": "SQLiteFeatureStorage", "uri": f"{tmpdir}/test.db"}
    # run the defined junifer feature extraction pipeline
    # TODO: needs SQLiteFeatureStorage.store_timeseries() to be
    # implemented first
    # run(
    #     workdir="/tmp",
    #     datagrabber={"kind": "SPMAuditoryTestingDatagrabber"},
    #     markers=marker_dicts,
    #     storage=storage,
    # )

    # read in extracted features and add confounds and targets
    # for julearn run cross validation
    # This will not run for now as store_timeseries() is not implemented yet
    # collect(storage)
    # db = SQLiteFeatureStorage(uri=storage["uri"], single_output=True)
    # df_vbm = db.read_df(feature_name="Schaefer100x17")
