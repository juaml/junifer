"""Provide concrete implementation for datalad-based HCP1200 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import BeforeValidator, HttpUrl

from ...api.decorators import register_datagrabber
from ...utils import ensure_list
from ..base import DataType
from ..datalad_base import DataladDataGrabber
from .hcp1200 import HCP1200


__all__ = ["DataladHCP1200"]


_types = Literal[DataType.BOLD, DataType.T1w, DataType.Warp]


@register_datagrabber
class DataladHCP1200(DataladDataGrabber, HCP1200):
    """Concrete implementation for datalad-based data fetching of HCP1200.

    Parameters
    ----------
    types : {``DataType.BOLD``, ``DataType.T1w``, ``DataType.Warp``} \
            or list of them, optional
        The data type(s) to grab.
    datadir : pathlib.Path, optional
        That path where the datalad dataset will be cloned.
        If not specified, the datalad dataset will be cloned into a temporary
        directory.
    tasks : list of :enum:`.HCP1200Task`, optional
        HCP task sessions.
        By default, all available task sessions are selected.
    phase_encodings : list of :enum:`.HCP1200PhaseEncoding`, optional
        HCP phase encoding directions.
        By default, all are used.
    ica_fix : bool, optional
        Whether to retrieve data that was processed with ICA+FIX.
        Only ``HCP1200Task.REST1`` and ``HCP1200Task.REST2`` tasks
        are available with ICA+FIX
        (default False).

    """

    uri: HttpUrl = HttpUrl(
        "https://github.com/datalad-datasets/"
        "human-connectome-project-openaccess.git"
    )
    types: Annotated[
        Union[_types, list[_types]], BeforeValidator(ensure_list)
    ] = [  # noqa: RUF012
        DataType.BOLD,
        DataType.T1w,
        DataType.Warp,
    ]
    rootdir: Path = Path("HCP1200")

    # Needed here as HCP1200's subjects are sub-datasets, so will not be
    # found when elements are checked.
    @property
    def skip_file_check(self) -> bool:
        """Skip file check existence."""
        return True
