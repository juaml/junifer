"""Provide class for coordinates space warping via FSL FLIRT."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any

import numpy as np
from numpy.typing import ArrayLike

from ...pipeline import WorkDirManager
from ...utils import logger, run_ext_cmd


__all__ = ["FSLCoordinatesWarper"]


class FSLCoordinatesWarper:
    """Class for coordinates space warping via FSL FLIRT.

    This class uses FSL FLIRT's ``img2imgcoord`` for transformation.

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
        warp_data : dict
            The warp data item of the data object.

        Returns
        -------
        numpy.ndarray
            The transformed coordinates.

        """
        logger.debug("Using FSL for coordinates transformation")

        # Create element-specific tempdir for storing post-warping assets
        element_tempdir = WorkDirManager().get_element_tempdir(
            prefix="fsl_coordinates_warper"
        )

        # Save existing coordinates to a tempfile
        pretransform_coordinates_path = (
            element_tempdir / "pretransform_coordinates.txt"
        )
        np.savetxt(pretransform_coordinates_path, seeds)

        # Create a tempfile for transformed coordinates output
        transformed_coords_path = (
            element_tempdir / "coordinates_transformed.txt"
        )
        # Set img2imgcoord command
        img2imgcoord_cmd = [
            "cat",
            f"{pretransform_coordinates_path.resolve()}",
            "| img2imgcoord -mm",
            f"-src {target_data['path'].resolve()}",
            f"-dest {target_data['reference']['path'].resolve()}",
            f"-warp {warp_data['path'].resolve()}",
            f"> {transformed_coords_path.resolve()};",
            f"sed -i 1d {transformed_coords_path.resolve()}",
        ]
        # Call img2imgcoord
        run_ext_cmd(name="img2imgcoord", cmd=img2imgcoord_cmd)

        # Load coordinates
        return np.loadtxt(transformed_coords_path)
