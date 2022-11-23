"""
Generic BIDS datagrabber for datalad.
=====================================

This example uses a generic BIDS datagraber to get the data from a BIDS dataset
store in a datalad remote sibling.

Authors: Federico Raimondo

License: BSD 3 clause
"""

from junifer.datagrabber import PatternDataladDataGrabber
from junifer.utils import configure_logging


###############################################################################
# Set the logging level to info to see extra information
configure_logging(level="INFO")


###############################################################################
# The BIDS datagrabber requires three parameters: the types of data we want,
# the specific pattern that matches each type, and the variables that will be
# replaced int he patterns.
types = ["T1w", "BOLD"]
patterns = {
    "T1w": "{subject}/anat/{subject}_T1w.nii.gz",
    "BOLD": "{subject}/func/{subject}_task-rest_bold.nii.gz",
}
replacements = ["subject"]
###############################################################################
# Additionally, a datalad datagrabber requires the URI of the remote sibling
# and the location of the dataset within the remote sibling.
repo_uri = "https://gin.g-node.org/juaml/datalad-example-bids"
rootdir = "example_bids"

###############################################################################
# Now we can use the datagrabber within a `with` context
# One thing we can do with any datagrabber is iterate over the elements.
# In this case, each element of the datagrabber is one session.
with PatternDataladDataGrabber(
    rootdir=rootdir,
    types=types,
    patterns=patterns,
    uri=repo_uri,
    replacements=replacements,
) as dg:
    for elem in dg:
        print(elem)

###############################################################################
# Another feature of the datagrabber is the ability to get a specific
# element by its name. In this case, we index `sub-01` and we get the file
# paths for the two types of data we want (T1w and bold).
with PatternDataladDataGrabber(
    rootdir=rootdir,
    types=types,
    patterns=patterns,
    uri=repo_uri,
    replacements=replacements,
) as dg:
    sub01 = dg["sub-01"]
    print(sub01)
