"""Provide class for juseless datalad datagrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import List, Union

from ....api.decorators import register_datagrabber
from ....datagrabber import PatternDataladDataGrabber
from ....utils import raise_error


@register_datagrabber
class JuselessDataladIXIVBM(PatternDataladDataGrabber):
    """Juseless IXI VBM DataGrabber class.

    Implements a DataGrabber to access the IXI VBM data in Juseless.

    Parameters
    -----------
    datadir : str or pathlib.Path, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    sites : {"Guys", "HH", "IOP"} or list of the
        options, optional.
        Which sites to access data from. If None, all available sites are
        selected (default None).
    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
        sites: Union[str, List[str], None] = None,
    ) -> None:
        """Initialize the class."""
        uri = "git@jugit.fz-juelich.de:inm7/datasets/datasets_repo.git"
        types = ["VBM_GM"]
        rootdir = "processed/cat_12.5/IXI"
        replacements = ["site", "subject"]
        patterns = {
            "VBM_GM": "{site}/sub-{subject}/mri/m0wp1sub-{subject}.nii.gz"
        }

        # validate and/or transform 'site' input
        all_sites = "HH", "Guys", "IOP"
        if sites is None:
            sites = all_sites

        if isinstance(sites, str):
            sites = [sites]

        for s in sites:
            if s not in all_sites:
                raise_error(
                    f"{s} not a valid site in IXI VBM dataset!"
                    f"Available sites are {all_sites}"
                )
        self.sites = sites
        super().__init__(
            types=types,
            datadir=datadir,
            uri=uri,
            rootdir=rootdir,
            replacements=replacements,
            patterns=patterns,
        )

    def get_elements(self) -> List:
        """Implement fetching list of subjects in the dataset.

        Returns
        -------
        elements : list of str
            The list of subjects in the dataset.
        """
        self._dataset.get(self.datadir, get_data=False, source="inm7-storage")

        elements = []
        for site in self.sites:
            site_dir = self.datadir / site
            site_elements = [
                (site, x.as_posix().split("-")[1])
                for x in site_dir.glob("sub-*")
            ]
            elements += site_elements

        return elements
