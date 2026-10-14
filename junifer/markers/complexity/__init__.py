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

# Not lazy: importing the sub-package (e.g., with ``with:`` in the YAML)
# registers the markers, as they are not built-in components of the registry
from .hurst_exponent import HurstExponent  # noqa: E402
from .range_entropy import RangeEntropy  # noqa: E402
from .range_entropy_auc import RangeEntropyAUC  # noqa: E402
from .perm_entropy import PermEntropy  # noqa: E402
from .weighted_perm_entropy import WeightedPermEntropy  # noqa: E402
from .sample_entropy import SampleEntropy  # noqa: E402
from .multiscale_entropy_auc import MultiscaleEntropyAUC  # noqa: E402


__all__ = [
    "HurstExponent",
    "RangeEntropy",
    "RangeEntropyAUC",
    "PermEntropy",
    "WeightedPermEntropy",
    "SampleEntropy",
    "MultiscaleEntropyAUC",
]
