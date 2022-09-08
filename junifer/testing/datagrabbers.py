"""Provide testing datagrabbers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import tempfile
from typing import Dict, List

from nilearn import datasets

from ..datagrabber.base import BaseDataGrabber


class OasisVBMTestingDatagrabber(BaseDataGrabber):
    """DataGrabber for Oasis VBM testing data."""

    def __init__(self) -> None:
        """Initialize the class."""
        # Create temporary directory
        datadir = tempfile.mkdtemp()
        # Define types
        types = ["VBM_GM"]
        super().__init__(types=types, datadir=datadir)

    def __getitem__(self, element: str) -> Dict:
        """Implement indexing support.

        Parameters
        ----------
        element : str
            The element to retrieve.

        Returns
        -------
        dict
            The data along with the metadata.

        """
        out = super().__getitem__(element)
        i_sub = int(element.split("-")[1]) - 1
        out["VBM_GM"] = {"path": self._dataset.gray_matter_maps[i_sub]}
        # Set the element accordingly
        out["meta"]["element"] = {"subject": element}
        return out

    def __enter__(self) -> "OasisVBMTestingDatagrabber":
        """Implement context entry.

        Returns
        -------
        OasisVBMTestingDatagrabber

        """
        self._dataset = datasets.fetch_oasis_vbm(n_subjects=10)
        return self

    def get_elements(self) -> List[str]:
        """Get elements.

        Returns
        -------
        list of str
            List of elements that can be grabbed.

        """
        return [f"sub-{x:02d}" for x in list(range(1, 11))]
