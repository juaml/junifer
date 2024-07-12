"""DataGrabbers for datasets' data description."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


# These 4 need to be in this order, otherwise it is a circular import
from .base import BaseDataGrabber
from .datalad_base import DataladDataGrabber
from .pattern import PatternDataGrabber
from .pattern_datalad import PatternDataladDataGrabber

from .aomic import DataladAOMICID1000, DataladAOMICPIOP1, DataladAOMICPIOP2
from .hcp1200 import HCP1200, DataladHCP1200
from .multiple import MultipleDataGrabber
from .dmcc13_benchmark import DMCC13Benchmark

from .pattern_validation_mixin import PatternValidationMixin

__all__ = [
    "BaseDataGrabber",
    "DataladDataGrabber",
    "PatternDataGrabber",
    "PatternDataladDataGrabber",
    "DataladAOMICID1000",
    "DataladAOMICPIOP1",
    "DataladAOMICPIOP2",
    "HCP1200",
    "DataladHCP1200",
    "MultipleDataGrabber",
    "DMCC13Benchmark",
    "PatternValidationMixin",
]
