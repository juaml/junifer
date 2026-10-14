"""Provide concrete implementation for datalad-based HCP1200 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from itertools import product
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AnyUrl, BeforeValidator

from ...api.decorators import register_datagrabber
from ...typing import Elements
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
    types : {"BOLD", "T1w", "Warp"} or list of the options, optional
        The data type(s) to grab.
    datadir : pathlib.Path, optional
        That path where the datalad dataset will be cloned.
        If not specified, the datalad dataset will be cloned into a temporary
        directory.
    tasks : {"REST1", "REST2", "SOCIAL", "WM", "RELATIONAL", "EMOTION", \
            "LANGUAGE", "GAMBLING", "MOTOR"} or list of the options, optional
        HCP task sessions.
        By default, all available task sessions are selected.
    phase_encodings : {"LR", "RL"} or list of the options, optional
        HCP phase encoding directions.
        By default, all are used.
    ica_fix : bool, optional
        Whether to retrieve data that was processed with ICA+FIX.
        Only ``HCP1200Task.REST1`` and ``HCP1200Task.REST2`` tasks
        are available with ICA+FIX
        (default False).

    """

    uri: AnyUrl = AnyUrl(
        "https://github.com/datalad-datasets/"
        "human-connectome-project-openaccess.git"
    )
    types: Annotated[_types | list[_types], BeforeValidator(ensure_list)] = [  # noqa: RUF012
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

    def get_elements(self) -> Elements:
        """Implement fetching list of elements in the dataset.

        The subjects are sub-datasets, whose files are only there once they
        are installed, so the files are not searched: the elements are all
        the subjects (the directories of the dataset) with the tasks and
        phase encodings to grab, even if some of them have no data.

        Returns
        -------
        list
            The list of elements that can be grabbed in the dataset.

        """
        subjects = sorted(
            x.name
            for x in self.fulldir.iterdir()
            if x.is_dir() and not x.name.startswith(".")
        )
        values = {"subject": subjects, **self.get_replacement_values()}
        element_keys = self.get_element_keys()
        elements = list(product(*(values[k] for k in element_keys)))
        if len(element_keys) == 1:
            return [element[0] for element in elements]
        return elements
