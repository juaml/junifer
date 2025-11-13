"""Provide concrete implementation for pattern-based HCP1200 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from enum import Enum
from itertools import product
from typing import Literal

from ...api.decorators import register_datagrabber
from ...typing import DataGrabberPatterns
from ...utils import raise_error
from ..base import DataType
from ..pattern import PatternDataGrabber


__all__ = ["HCP1200", "HCP1200PhaseEncoding", "HCP1200Task"]


class HCP1200Task(str, Enum):
    """Accepted HCP1200 tasks."""

    REST1 = "REST1"
    REST2 = "REST2"
    SOCIAL = "SOCIAL"
    WM = "WM"
    RELATIONAL = "RELATIONAL"
    EMOTION = "EMOTION"
    LANGUAGE = "LANGUAGE"
    GAMBLING = "GAMBLING"
    MOTOR = "MOTOR"


class HCP1200PhaseEncoding(str, Enum):
    """Accepted HCP1200 phase encoding directions."""

    LR = "LR"
    RL = "RL"


@register_datagrabber
class HCP1200(PatternDataGrabber):
    """Concrete implementation for pattern-based data fetching of HCP1200.

    Parameters
    ----------
    types : list of {``DataType.BOLD``, ``DataType.T1w``, ``DataType.Warp``}, \
            optional
        The data type(s) to grab.
    datadir : pathlib.Path
        The path where the data is stored.
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

    types: list[Literal[DataType.BOLD, DataType.T1w, DataType.Warp]] = [  # noqa: RUF012
        DataType.BOLD,
        DataType.T1w,
        DataType.Warp,
    ]
    tasks: list[HCP1200Task] = [  # noqa: RUF012
        HCP1200Task.REST1,
        HCP1200Task.REST2,
        HCP1200Task.SOCIAL,
        HCP1200Task.WM,
        HCP1200Task.RELATIONAL,
        HCP1200Task.EMOTION,
        HCP1200Task.LANGUAGE,
        HCP1200Task.GAMBLING,
        HCP1200Task.MOTOR,
    ]
    phase_encodings: list[HCP1200PhaseEncoding] = [  # noqa: RUF012
        HCP1200PhaseEncoding.RL,
        HCP1200PhaseEncoding.LR,
    ]
    ica_fix: bool = False
    patterns: DataGrabberPatterns = {  # noqa: RUF012
        "BOLD": {
            "pattern": (
                "{subject}/MNINonLinear/Results/"
                "{task}_{phase_encoding}/"
                "{task}_{phase_encoding}"
                "{suffix}.nii.gz"
            ),
            "space": "MNI152NLin6Asym",
        },
        "T1w": {
            "pattern": "{subject}/T1w/T1w_acpc_dc_restore.nii.gz",
            "space": "native",
        },
        "Warp": [
            {
                "pattern": (
                    "{subject}/MNINonLinear/xfms/standard2acpc_dc.nii.gz"
                ),
                "src": "MNI152NLin6Asym",
                "dst": "native",
                "warper": "fsl",
            },
            {
                "pattern": (
                    "{subject}/MNINonLinear/xfms/acpc_dc2standard.nii.gz"
                ),
                "src": "native",
                "dst": "MNI152NLin6Asym",
                "warper": "fsl",
            },
        ],
    }
    replacements: list[str] = ["subject", "task", "phase_encoding"]  # noqa: RUF012

    def validate_datagrabber_params(self) -> None:
        """Run extra logical validation for datagrabber."""
        if self.ica_fix:
            if not all(task in ["REST1", "REST2"] for task in self.tasks):
                raise_error(
                    "ICA+FIX is only available for 'REST1' and 'REST2' tasks."
                )
        suffix = "_hp2000_clean" if self.ica_fix else ""
        self.patterns["BOLD"]["pattern"] = self.patterns["BOLD"][
            "pattern"
        ].replace("{suffix}", suffix)
        super().validate_datagrabber_params()

    def get_item(self, subject: str, task: str, phase_encoding: str) -> dict:
        """Get the specified item from the dataset.

        Parameters
        ----------
        subject : str
            The subject ID.
        task : {"REST1", "REST2", "SOCIAL", "WM", "RELATIONAL", "EMOTION", \
               "LANGUAGE", "GAMBLING", "MOTOR"}
            The task.
        phase_encoding : {"LR", "RL"}
            The phase encoding.

        Returns
        -------
        dict
            Dictionary of dictionaries for each type of data required for the
            specified element.

        """
        # Resting task
        if "REST" in task:
            new_task = f"rfMRI_{task}"
        else:
            new_task = f"tfMRI_{task}"

        return super().get_item(
            subject=subject, task=new_task, phase_encoding=phase_encoding
        )

    def get_elements(self) -> list:
        """Implement fetching list of elements in the dataset.

        Returns
        -------
        list
            The list of elements that can be grabbed in the dataset.

        """
        subjects = [
            x.name
            for x in self.datadir.iterdir()
            if x.is_dir() and not x.name.startswith(".")
        ]
        elems = []
        for subject, task, phase_encoding in product(
            subjects, self.tasks, self.phase_encodings
        ):
            elems.append((subject, task, phase_encoding))

        return elems
