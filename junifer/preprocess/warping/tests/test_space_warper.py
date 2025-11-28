"""Provide tests for SpaceWarper."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import socket

import pytest
from numpy.testing import assert_array_equal, assert_raises

from junifer.datagrabber import (
    DataladHCP1200,
    DataType,
    DMCC13Benchmark,
    DMCCPhaseEncoding,
    DMCCRun,
    DMCCSession,
    DMCCTask,
    HCP1200PhaseEncoding,
    HCP1200Task,
)
from junifer.datareader import DefaultDataReader
from junifer.pipeline.utils import _check_ants, _check_fsl
from junifer.preprocess import SpaceWarper, SpaceWarpingImpl
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber
from junifer.typing import DataGrabberLike


@pytest.mark.parametrize(
    "using, reference, error_type, error_msg",
    [
        (SpaceWarpingImpl.ants, "MNI152NLin2009cAsym", RuntimeError, "remove"),
        (SpaceWarpingImpl.fsl, "MNI152NLin2009cAsym", RuntimeError, "ANTs"),
    ],
)
def test_SpaceWarper_errors(
    using: SpaceWarpingImpl,
    reference: str,
    error_type: type[Exception],
    error_msg: str,
) -> None:
    """Test SpaceWarper errors.

    Parameters
    ----------
    using : SpaceWarpingImpl
        The parametrized implementation method.
    reference : str
        The parametrized reference to use.
    error_type : Exception-like object
        The parametrized exception to check.
    error_msg : str
        The parametrized exception message to check.

    """
    with PartlyCloudyTestingDataGrabber() as dg:
        element_data = DefaultDataReader().fit_transform(dg["sub-01"])
        with pytest.raises(error_type, match=error_msg):
            SpaceWarper(
                using=using,
                reference=reference,
                on=DataType.BOLD,
            ).preprocess(
                input=element_data["BOLD"],
                extra_input=element_data,
            )


@pytest.mark.parametrize(
    "datagrabber, element, using",
    [
        [
            DMCC13Benchmark(
                types=[DataType.BOLD, DataType.T1w, DataType.Warp],
                sessions=DMCCSession.Wave1Bas,
                tasks=DMCCTask.Rest,
                phase_encodings=DMCCPhaseEncoding.AP,
                runs=DMCCRun.One,
                native_t1w=True,
            ),
            ("sub-f9057kp", "ses-wave1bas", "Rest", "AP", "1"),
            SpaceWarpingImpl.ants,
        ],
        [
            DataladHCP1200(
                tasks=HCP1200Task.REST1,
                phase_encodings=HCP1200PhaseEncoding.LR,
                ica_fix=True,
            ),
            ("100206", "REST1", "LR"),
            SpaceWarpingImpl.fsl,
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
    datagrabber: DataGrabberLike,
    element: tuple[str, ...],
    using: SpaceWarpingImpl,
) -> None:
    """Test SpaceWarper for native space warping.

    Parameters
    ----------
    datagrabber : DataGrabber-like object
        The parametrized DataGrabber objects.
    element : tuple of str
        The parametrized elements.
    using : SpaceWarpingImpl
        The parametrized implementation method.

    """
    with datagrabber as dg:
        element_data = DefaultDataReader().fit_transform(dg[element])
        output = SpaceWarper(
            using=using,
            reference="T1w",
            on=DataType.BOLD,
        ).preprocess(
            input=element_data["BOLD"],
            extra_input=element_data,
        )
        assert isinstance(output, dict)


@pytest.mark.parametrize(
    "datagrabber, element, space",
    [
        [
            DMCC13Benchmark(
                types=DataType.T1w,
                sessions=DMCCSession.Wave1Bas,
                tasks=DMCCTask.Rest,
                phase_encodings=DMCCPhaseEncoding.AP,
                runs=DMCCRun.One,
                native_t1w=False,
            ),
            ("sub-f9057kp", "ses-wave1bas", "Rest", "AP", "1"),
            "MNI152NLin2009aAsym",
        ],
        [
            DMCC13Benchmark(
                types=DataType.T1w,
                sessions=DMCCSession.Wave1Bas,
                tasks=DMCCTask.Rest,
                phase_encodings=DMCCPhaseEncoding.AP,
                runs=DMCCRun.One,
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
        element_data = DefaultDataReader().fit_transform(dg[element])
        pre_xfm_data = element_data["T1w"]["data"].get_fdata().copy()
        output = SpaceWarper(
            using=SpaceWarpingImpl.ants,
            reference=space,
            on=DataType.T1w,
        ).preprocess(
            input=element_data["T1w"],
            extra_input=element_data,
        )
        assert isinstance(output, dict)
        assert output["space"] == space
        with assert_raises(AssertionError):
            assert_array_equal(pre_xfm_data, output["data"])
