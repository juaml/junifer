"""Provide class for coordinates space warping via ANTs."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any

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
        target_data: dict[str, Any],
        warp_data: dict[str, Any],
    ) -> ArrayLike:
        """Warp ``seeds`` to correct space.

        Parameters
        ----------
        seeds : array-like
            The coordinates to transform.
        target_data : dict
            The corresponding item of the data object to which the coordinates
            will be applied.
        warp_data : dict or None
            The warp data item of the data object.

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
            element_tempdir / "pretransform_coordinates.csv"
        )
        # Convert LPS to RAS
        seeds[:, 0] *= -1
        seeds[:, 1] *= -1
        np.savetxt(
            pretransform_coordinates_path,
            seeds,
            delimiter=",",
            # Add header while saving to make ANTs work
            header="x,y,z",
            # Remove comment tag for header
            comments="",
        )

        # Create a tempfile for transformed coordinates output
        transformed_coords_path = (
            element_tempdir / "coordinates_transformed.csv"
        )
        # Set antsApplyTransformsToPoints command
        apply_transforms_to_points_cmd = [
            "antsApplyTransformsToPoints",
            "-d 3",
            "-p 1",
            "-f 0",
            f"-i {pretransform_coordinates_path.resolve()}",
            f"-o {transformed_coords_path.resolve()}",
            f"-t {warp_data['path'].resolve()}",
        ]
        # Call antsApplyTransformsToPoints
        run_ext_cmd(
            name="antsApplyTransformsToPoints",
            cmd=apply_transforms_to_points_cmd,
        )

        # Load coordinates
        transformed_seeds = np.loadtxt(
            # Skip header when reading
            transformed_coords_path,
            delimiter=",",
            skiprows=1,
        )
        # Convert RAS to LPS
        transformed_seeds[:, 0] *= -1
        transformed_seeds[:, 1] *= -1

        return transformed_seeds
