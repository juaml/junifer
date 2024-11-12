"""Provide concrete implementation for datalad-based HCP1200 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Union

from junifer.datagrabber.datalad_base import DataladDataGrabber

from ...api.decorators import register_datagrabber
from .hcp1200 import HCP1200


__all__ = ["DataladHCP1200"]


@register_datagrabber
class DataladHCP1200(DataladDataGrabber, HCP1200):
    """Concrete implementation for datalad-based data fetching of HCP1200.

    Parameters
    ----------
    datadir : str or Path or None, optional
        The directory where the datalad dataset will be cloned. If None,
        the datalad dataset will be cloned into a temporary directory
        (default None).
    tasks : {"REST1", "REST2", "SOCIAL", "WM", "RELATIONAL", "EMOTION", \
            "LANGUAGE", "GAMBLING", "MOTOR"} or list of the options or None \
            , optional
        HCP task sessions. If None, all available task sessions are selected
        (default None).
    phase_encodings : {"LR", "RL"} or list of the options or None, optional
        HCP phase encoding directions. If None, both will be used
        (default None).
    ica_fix : bool, optional
        Whether to retrieve data that was processed with ICA+FIX.
        Only "REST1" and "REST2" tasks are available with ICA+FIX (default
        False).

    Raises
    ------
    ValueError
        If invalid value is passed for ``tasks`` or ``phase_encodings``.

    """

    def __init__(
        self,
        datadir: Union[str, Path, None] = None,
        tasks: Union[str, list[str], None] = None,
        phase_encodings: Union[str, list[str], None] = None,
        ica_fix: bool = False,
    ) -> None:
        uri = (
            "https://github.com/datalad-datasets/"
            "human-connectome-project-openaccess.git"
        )
        rootdir = "HCP1200"
        super().__init__(
            datadir=datadir,
            tasks=tasks,
            phase_encodings=phase_encodings,
            uri=uri,
            rootdir=rootdir,
            ica_fix=ica_fix,
        )

    # Needed here as HCP1200's subjects are sub-datasets, so will not be
    # found when elements are checked.
    @property
    def skip_file_check(self) -> bool:
        """Skip file check existence."""
        return True
