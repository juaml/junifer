"""Provide class for coordinates space warping via FSL FLIRT."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, Dict

import numpy as np
from numpy.typing import ArrayLike

from ...pipeline import WorkDirManager
from ...utils import logger, raise_error, run_ext_cmd


__all__ = ["FSLCoordinatesWarper"]


class FSLCoordinatesWarper:
    """Class for coordinates space warping via FSL FLIRT.

    This class uses FSL FLIRT's ``img2imgcoord`` for transformation.

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
            data kinds that needs to be used in the computation of coordinates.

        Returns
        -------
        numpy.ndarray
            The transformed coordinates.

        Raises
        ------
        RuntimeError
            If warp file path could not be found in ``extra_input``.

        """
        logger.debug("Using FSL for coordinates transformation")

        # Get warp file path
        warp_file_path = None
        for entry in extra_input["Warp"]:
            if entry["dst"] == "native":
                warp_file_path = entry["path"]
        if warp_file_path is None:
            raise_error(
                klass=RuntimeError, msg="Could not find correct warp file path"
            )

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
            f"-dest {target_data['reference_path'].resolve()}",
            f"-warp {warp_file_path.resolve()}",
            f"> {transformed_coords_path.resolve()};",
            f"sed -i 1d {transformed_coords_path.resolve()}",
        ]
        # Call img2imgcoord
        run_ext_cmd(name="img2imgcoord", cmd=img2imgcoord_cmd)

        # Load coordinates
        return np.loadtxt(transformed_coords_path)