"""Provide common types for AOMIC DataGrabbers."""

from enum import Enum


class AOMICSpace(str, Enum):
    """Accepted spaces for AOMIC."""

    Native = "native"
    MNI152NLin2009cAsym = "MNI152NLin2009cAsym"


class AOMICTask(str, Enum):
    """Accepted tasks for AOMIC."""

    RestingState = "restingstate"
    Anticipation = "anticipation"
    EmoMatching = "emomatching"
    Faces = "faces"
    Gstroop = "gstroop"
    WorkingMemory = "workingmemory"
    StopSignal = "stopsignal"
