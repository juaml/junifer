"""Provide imports for complexity sub-package."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from importlib.util import find_spec

from ..utils import raise_error


# Check if neurokit2 is found
if find_spec("neurokit2") is None:
    raise_error(
        msg="Could not find `neurokit2`, make sure the package is installed.",
        klass=ImportError,
    )
else:
    # Import markers
    from .hurst_exponent import HurstExponent
    from .range_entropy import RangeEntropy
    from .range_entropy_auc import RangeEntropyAUC
    from .perm_entropy import PermEntropy
    from .weighted_perm_entropy import WeightedPermEntropy
    from .sample_entropy import SampleEntropy
    from .multiscale_entropy_auc import MultiscaleEntropyAUC

    __all__ = [
        "HurstExponent",
        "RangeEntropy",
        "RangeEntropyAUC",
        "PermEntropy",
        "WeightedPermEntropy",
        "SampleEntropy",
        "MultiscaleEntropyAUC",
    ]
