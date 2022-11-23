"""Provide class for IXI VBM juseless datalad datagrabber."""

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
    """Juseless IXI VBM Data Grabber class.

    Implements a Data Grabber to access the IXI VBM data in Juseless.

    Parameters
    ----------
    datadir : str or pathlib.Path, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    sites : {"Guys", "HH", "IOP"} or list of the options, optional.
        Which sites to access data from. If None, all available sites are
        selected (default None).
    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
        sites: Union[str, List[str], None] = None,
    ) -> None:
        uri = (
            "ria+http://cat_12.5.ds.inm7.de"
            "#b7107c52-8408-11ea-89c6-a0369f287950"
        )
        types = ["VBM_GM"]
        replacements = ["site", "subject"]
        patterns = {
            "VBM_GM": "{site}/sub-{subject}/mri/m0wp1sub-{subject}.nii.gz"
        }

        # validate and/or transform 'site' input
        all_sites = ["HH", "Guys", "IOP"]
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
            replacements=replacements,
            patterns=patterns,
        )
