"""Provide tests for SpaceWarper."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket
from typing import TYPE_CHECKING, Tuple

import pytest
from numpy.testing import assert_array_equal, assert_raises

from junifer.datagrabber import DataladHCP1200, DMCC13Benchmark
from junifer.datareader import DefaultDataReader
from junifer.pipeline.utils import _check_ants, _check_fsl
from junifer.preprocess import SpaceWarper


if TYPE_CHECKING:
    from junifer.datagrabber import BaseDataGrabber


@pytest.mark.parametrize(
    "datagrabber, element, using",
    [
        [
            DMCC13Benchmark(
                types=["BOLD", "T1w", "Warp"],
                sessions=["wave1bas"],
                tasks=["Rest"],
                phase_encodings=["AP"],
                runs=["1"],
                native_t1w=True,
            ),
            ("f9057kp", "wave1bas", "Rest", "AP", "1"),
            "ants",
        ],
        [
            DataladHCP1200(
                tasks=["REST1"],
                phase_encodings=["LR"],
                ica_fix=True,
            ),
            ("100206", "REST1", "LR"),
            "fsl",
        ],
    ],
)
@pytest.mark.skipif(_check_fsl() is False, reason="requires FSL to be in PATH")
@pytest.mark.skipif(
    _check_ants() is False, reason="requires ANTs to be in PATH"
)
@pytest.mark.skipif(
    socket.gethostname() != "juseless",
    reason="only for juseless",
)
def test_SpaceWarper_native(
    datagrabber: "BaseDataGrabber", element: Tuple[str, ...], using: str
) -> None:
    """Test SpaceWarper for native space warping.

    Parameters
    ----------
    datagrabber : DataGrabber-like object
        The parametrized DataGrabber objects.
    element : tuple of str
        The parametrized elements.
    using : str
        The parametrized implementation method.

    """
    with datagrabber as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg[element])
        # Preprocess data
        output, _ = SpaceWarper(
            using=using,
            reference="T1w",
            on="BOLD",
        ).preprocess(
            input=element_data["BOLD"],
            extra_input=element_data,
        )
        # Check
        assert isinstance(output, dict)


@pytest.mark.parametrize(
    "datagrabber, element, space",
    [
        [
            DMCC13Benchmark(
                types=["T1w"],
                sessions=["wave1bas"],
                tasks=["Rest"],
                phase_encodings=["AP"],
                runs=["1"],
                native_t1w=False,
            ),
            ("f9057kp", "wave1bas", "Rest", "AP", "1"),
            "MNI152NLin2009aAsym",
        ],
        [
            DMCC13Benchmark(
                types=["T1w"],
                sessions=["wave1bas"],
                tasks=["Rest"],
                phase_encodings=["AP"],
                runs=["1"],
                native_t1w=False,
            ),
            ("f9057kp", "wave1bas", "Rest", "AP", "1"),
            "MNI152NLin6Asym",
        ],
    ],
)
@pytest.mark.skipif(
    _check_ants() is False, reason="requires ANTs to be in PATH"
)
def test_SpaceWarper_multi_mni(
    datagrabber: "BaseDataGrabber",
    element: Tuple[str, ...],
    space: str,
) -> None:
    """Test SpaceWarper for MNI space warping.

    Parameters
    ----------
    datagrabber : DataGrabber-like object
        The parametrized DataGrabber objects.
    element : tuple of str
        The parametrized elements.
    space : str
        The parametrized template space to transform to.

    """
    with datagrabber as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg[element])
        pre_xfm_data = element_data["BOLD"]["data"].get_fdata().copy()
        # Preprocess data
        output, _ = SpaceWarper(
            using="ants",
            reference=space,
            on=["T1w"],
        ).preprocess(
            input=element_data["T1w"],
            extra_input=element_data,
        )
        # Checks
        assert isinstance(output, dict)
        assert output["space"] == space
        with assert_raises(AssertionError):
            assert_array_equal(pre_xfm_data, output["data"])
