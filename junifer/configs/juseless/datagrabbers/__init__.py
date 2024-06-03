"""Custom DataGrabbers for FZJ INM-7's beloved juseless."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from .aomic_id1000_vbm import JuselessDataladAOMICID1000VBM
from .camcan_vbm import JuselessDataladCamCANVBM
from .ixi_vbm import JuselessDataladIXIVBM
from .ucla import JuselessUCLA
from .ukb_vbm import JuselessDataladUKBVBM


__all__ = [
    "JuselessDataladAOMICID1000VBM",
    "JuselessDataladCamCANVBM",
    "JuselessDataladIXIVBM",
    "JuselessUCLA",
    "JuselessDataladUKBVBM",
]
