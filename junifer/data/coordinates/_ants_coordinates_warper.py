"""Provide class for coordinates space warping via ANTs."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Dict

import numpy as np
from numpy.typing import ArrayLike

from ...pipeline import WorkDirManager
from ...utils import logger, run_ext_cmd


__all__ = ["ANTsCoordinatesWarper"]


class ANTsCoordinatesWarper:
    """Class for coordinates space warping via ANTs.

    This class uses ANTs ``antsApplyTransformsToPoints`` for transformation.

    """

    def warp(
        self,
        seeds: ArrayLike,
        target_data: Dict[str, Any],
        extra_input: Dict[str, Any],
    ) -> ArrayLike:
        """Warp ``seeds`` to correct space.

        Parameters
        ----------
        seeds : array-like
            The coordinates to transform.
        target_data : dict
            The corresponding item of the data object to which the coordinates
            will be applied.
        extra_input : dict, optional
            The other fields in the data object. Useful for accessing other
            data kinds that needs to be used in the computation of coordinates
            (default None).

        Returns
        -------
        numpy.ndarray
            The transformed coordinates.

        """
        logger.debug("Using ANTs for coordinates transformation")

        # Create element-specific tempdir for storing post-warping assets
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="ants_coordinates_warper"
        )

        # Save existing coordinates to a tempfile
        pretransform_coordinates_path = (
            element_tempdir / "pretransform_coordinates.txt"
        )
        np.savetxt(
            pretransform_coordinates_path,
            seeds,
            delimiter=",",
            # Add header while saving to make ANTs work
            header="x,y,z",
        )

        # Create a tempfile for transformed coordinates output
        transformed_coords_path = (
            element_tempdir / "coordinates_transformed.txt"
        )
        # Set antsApplyTransformsToPoints command
        apply_transforms_to_points_cmd = [
            "antsApplyTransformsToPoints",
            "-d 3",
            "-p 1",
            "-f 0",
            f"-i {pretransform_coordinates_path.resolve()}",
            f"-o {transformed_coords_path.resolve()}",
            f"-t {extra_input['Warp']['path'].resolve()};",
        ]
        # Call antsApplyTransformsToPoints
        run_ext_cmd(
            name="antsApplyTransformsToPoints",
            cmd=apply_transforms_to_points_cmd,
        )

        # Load coordinates
        return np.loadtxt(
            # Skip header when reading
            transformed_coords_path,
            delimiter=",",
            skiprows=1,
        )
