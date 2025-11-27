"""

Extracting root sum of squares from edge-wise timeseries.
=========================================================
This example uses a ``RSSETSMarker`` to compute root sum of squares
of the edge-wise timeseries using the Schaefer parcellation
(100 rois and 200 rois, 17 Yeo networks) for a 4D nifti BOLD file.

Authors: Leonard Sasse, Sami Hamdan, Nicolas Nieto, Synchon Mandal

License: BSD 3 clause

"""

import tempfile

import junifer.testing.registry  # noqa: F401
from junifer.api import collect, run
from junifer.storage import SQLiteFeatureStorage
from junifer.utils import configure_logging


###############################################################################
# Set the logging level to info to see extra information:
configure_logging(level="INFO")

##############################################################################
# Define the DataGrabber interface
datagrabber = {
    "kind": "SPMAuditoryTestingDataGrabber",
}

###############################################################################
# Define the markers interface
markers = [
    {
        "name": "Schaefer100x17_RSSETS",
        "kind": "RSSETSMarker",
        "parcellation": "Schaefer100x17",
    },
    {
        "name": "Schaefer200x17_RSSETS",
        "kind": "RSSETSMarker",
        "parcellation": "Schaefer200x17",
    },
]

###############################################################################
# Create a temporary directory for junifer feature extraction:
# At the end you can read the extracted data into a ``pandas.DataFrame``.
with tempfile.TemporaryDirectory() as tmpdir:
    # Define the storage interface
    storage = {
        "kind": "SQLiteFeatureStorage",
        "uri": f"{tmpdir}/test.sqlite",
    }
    # Run the defined junifer feature extraction pipeline
    run(
        workdir=tmpdir,
        datagrabber=datagrabber,
        markers=markers,
        storage=storage,
        elements=["sub001"],  # we calculate for one subject only
    )
    # Collect extracted features data
    collect(storage=storage)
    # Create storage object to read in extracted features
    db = SQLiteFeatureStorage(uri=storage["uri"])

    # List all the features
    print(db.list_features())
    # Read extracted features
    df_rssets = db.read_df(feature_name="BOLD_Schaefer200x17_RSSETS_rss_ets")

###############################################################################
# Now we take a look at the dataframe
df_rssets.head()
