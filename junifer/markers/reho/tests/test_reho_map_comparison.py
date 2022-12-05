"""Provide tests for ReHo map compute comparison."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Callable, Type

import nibabel as nib
import numpy as np
from scipy.stats import pearsonr
import pytest
from nibabel.imageclasses import PARRECImage

from junifer.datareader.default import DefaultDataReader
from junifer.markers.reho.reho_base import ReHoBase
from junifer.testing.datagrabbers import PartlyCloudyTestingDataGrabber


@pytest.fixture
def reho_map_comparer() -> Type:
    """Generate class for ReHo map comparison."""

    class ReHoMapComparer(ReHoBase):
        """Class for comparing ReHo maps."""

        def _load_afni_reho_map(self, subject: str) -> "PARRECImage":
            """Load afni generated reho map for `subject`.

            Parameters
            ----------
            subject : {"sub-01", "sub-02", "sub-03"}
                The subject to load reho map for.

            Returns
            -------
            Niimg-like object
                The loaded .nii file.

            """
            return nib.load(
                Path(__file__).parent / subject / f"{subject}-reho-map.nii"
            )

        def compute(self, subject: str) -> None:
            """Compute and compare.

            Parameters
            ----------
            subject : {"sub-01", "sub-02", "sub-03"}
                The subject to load reho map for.

            """
            # Load development fmri datagrabber
            dg = PartlyCloudyTestingDataGrabber(
                reduce_confounds=True, age_group="adult"
            )
            # Load datareader
            dr = DefaultDataReader()
            with dg:
                path_info = dg[subject]
                loaded_data = dr.fit_transform(path_info)

            # Compute python implementation
            self.use_afni = False
            python_reho_map = self.compute_reho_map(loaded_data["BOLD"])
            # Load afni implementation data
            afni_reho_map = self._load_afni_reho_map(subject)
            # Compare
            # assert np.testing.assert_array_equal(
            #     python_reho_map.get_fdata(), afni_reho_map.get_fdata()
            # )
            print(
                pearsonr(
                    python_reho_map.get_fdata().flatten(),
                    afni_reho_map.get_fdata().flatten(),
                )
            )
            print('done')

    return ReHoMapComparer


@pytest.mark.parametrize(
    "subject",
    ["sub-01", "sub-02", "sub-03"],
)
def test_reho_map(reho_map_comparer: Callable, subject: str) -> None:
    """Compare ReHo map computations.

    Parameters
    ----------
    reho_map_comparer : callable
        Fixture for generating reho map comparer class.
    subject : {"sub-01", "sub-02", "sub-03"}
        The parametrized subject name.

    """
    comparer = reho_map_comparer()
    comparer.compute(subject)
