"""Provide functions for template spaces."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Union

import httpx

from ..utils import logger, raise_error


def get_xfm(
    src: str, dst: str, xfms_dir: Union[str, Path, None] = None
) -> Path:  # pragma: no cover
    """Fetch warp files to convert from ``src`` to ``dst``.

    Parameters
    ----------
    src : str
        The template space to transform from.
    dst : str
        The template space to transform to.
    xfms_dir : str or pathlib.Path, optional
        Path where the retrieved transformation files are stored.
        The default location is "$HOME/junifer/data/xfms" (default None).

    Returns
    -------
    pathlib.Path
        The path to the transformation file.

    Raises
    ------
    RuntimeError
        If there is a problem fetching files.

    """
    if xfms_dir is None:
        xfms_dir = Path().home() / "junifer" / "data" / "xfms"
        logger.debug(f"Creating xfm directory at: {xfms_dir.resolve()}")
        # Create default junifer data directory if not present
        xfms_dir.mkdir(exist_ok=True, parents=True)
    # Convert str to Path
    elif not isinstance(xfms_dir, Path):
        xfms_dir = Path(xfms_dir)

    # Set local file prefix
    xfm_file_prefix = f"{src}_to_{dst}"
    # Set local file dir
    xfm_file_dir = xfms_dir / xfm_file_prefix
    # Create local directory if not present
    xfm_file_dir.mkdir(exist_ok=True, parents=True)
    # Set file name with extension
    xfm_file = f"{src}_to_{dst}_Composite.h5"
    # Set local file path
    xfm_file_path = xfm_file_dir / xfm_file
    # Check if the file exists
    if xfm_file_path.exists():
        logger.info(
            f"Found existing xfm file for {src} to {dst} at "
            f"{xfm_file_path.resolve()}"
        )
        return xfm_file_path

    # Set URL
    url = (
        "https://gin.g-node.org/juaml/human-template-xfms/raw/main/xfms/"
        f"{xfm_file_prefix}/{xfm_file}"
    )
    # Create the file before proceeding
    xfm_file_path.touch()

    logger.info(f"Downloading xfm file for {src} to {dst} from {url}")
    # Steam response
    with httpx.stream("GET", url) as resp:
        try:
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise_error(
                f"Error response {exc.response.status_code} while "
                f"requesting {exc.request.url!r}",
                klass=RuntimeError,
            )
        else:
            with open(xfm_file_path, "ab") as f:
                for chunk in resp.iter_bytes():
                    f.write(chunk)

    return xfm_file_path
