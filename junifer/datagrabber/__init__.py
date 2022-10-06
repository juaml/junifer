"""Provide imports for datagrabber sub-package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from .base import BaseDataGrabber
from .datalad_base import DataladDataGrabber
from .hcp import DataladHCP1200, HCP1200
from .multiple import MultipleDataGrabber
from .pattern import PatternDataGrabber
from .pattern_datalad import PatternDataladDataGrabber
from .aomic import DataladAOMICID1000, DataladAOMICPIOP1, DataladAOMICPIOP2
