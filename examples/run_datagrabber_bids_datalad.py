"""
Generic BIDS datagrabber for datalad.
=====================================

Authors: Federico Raimondo

License: BSD 3 clause
"""

from junifer.datagrabber.base import BIDSDataladDataGrabber

repo_uri = 'https://gin.g-node.org/juaml/datalad-example-bids'


types = ['T1w', 'bold']
patterns = {
    'T1w': 'anat/{subject}_T1w.nii.gz',
    'bold': 'func/{subject}_task-rest_bold.nii.gz'
}


with BIDSDataladDataGrabber(rootdir='example_bids', types=types,
                            patterns=patterns, uri=repo_uri) as dg:
    for elem in dg:
        print(elem)

    sub01 = dg['sub-01']
    print(sub01)
