"""Preprocessors for preprocessing data before feature extraction."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from .base import BasePreprocessor
from .confounds import fMRIPrepConfoundRemover
from .bold_warper import BOLDWarper
from .warping import SpaceWarper
from .smoothing import Smoothing
