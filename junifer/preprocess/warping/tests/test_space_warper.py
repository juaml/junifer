"""Provide tests for SpaceWarper."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket

import pytest
from numpy.testing import assert_array_equal, assert_raises

from junifer.datagrabber import DataladHCP1200, DMCC13Benchmark
from junifer.datareader import DefaultDataReader
from junifer.pipeline.utils import _check_ants, _check_fsl
from junifer.preprocess import SpaceWarper
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber
from junifer.typing import DataGrabberLike


@pytest.mark.parametrize(
    "using, reference, error_type, error_msg",
    [
        ("jam", "T1w", ValueError, "`using`"),
        ("ants", "juice", ValueError, "reference"),
        ("ants", "MNI152NLin2009cAsym", RuntimeError, "remove"),
        ("fsl", "MNI152NLin2009cAsym", RuntimeError, "ANTs"),
    ],
)
def test_SpaceWarper_errors(
    using: str,
    reference: str,
    error_type: type[Exception],
    error_msg: str,
) -> None:
    """Test SpaceWarper errors.

    Parameters
    ----------
    using : str
        The parametrized implementation method.
    reference : str
        The parametrized reference to use.
    error_type : Exception-like object
        The parametrized exception to check.
    error_msg : str
        The parametrized exception message to check.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        # Read data
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        # Preprocess data
        with pytest.raises(error_type, match=error_msg):
            SpaceWarper(
                using=using,
                reference=reference,
                on="BOLD",
            ).preprocess(
                input=element_data["BOLD"],
                extra_input=element_data,
            )


@pytest.mark.parametrize(
    "datagrabber, element, using",
    [
        [
            DMCC13Benchmark(
                types=["BOLD", "T1w", "Warp"],
                sessions=["ses-wave1bas"],
                tasks=["Rest"],
                phase_encodings=["AP"],
                runs=["1"],
                native_t1w=True,
            ),
            ("sub-f9057kp", "ses-wave1bas", "Rest", "AP", "1"),
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
    datagrabber: DataGrabberLike, element: tuple[str, ...], using: str
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
                sessions=["ses-wave1bas"],
                tasks=["Rest"],
                phase_encodings=["AP"],
                runs=["1"],
                native_t1w=False,
            ),
            ("sub-f9057kp", "ses-wave1bas", "Rest", "AP", "1"),
            "MNI152NLin2009aAsym",
        ],
        [
            DMCC13Benchmark(
                types=["T1w"],
                sessions=["ses-wave1bas"],
                tasks=["Rest"],
                phase_encodings=["AP"],
                runs=["1"],
                native_t1w=False,
            ),
            ("sub-f9057kp", "ses-wave1bas", "Rest", "AP", "1"),
            "MNI152NLin6Asym",
        ],
    ],
)
@pytest.mark.skipif(
    _check_ants() is False, reason="requires ANTs to be in PATH"
)
def test_SpaceWarper_multi_mni(
    datagrabber: DataGrabberLike,
    element: tuple[str, ...],
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
        pre_xfm_data = element_data["T1w"]["data"].get_fdata().copy()
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
