"""Functions for parcellation manipulation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import io
import shutil
import tarfile
import tempfile
import typing
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import httpx
import nibabel as nib
import numpy as np
import pandas as pd
from nilearn import datasets, image

from ..pipeline import WorkDirManager
from ..utils import logger, raise_error, run_ext_cmd, warn_with_log
from .template_spaces import get_template, get_xfm
from .utils import closest_resolution


if TYPE_CHECKING:
    from nibabel import Nifti1Image


__all__ = [
    "register_parcellation",
    "list_parcellations",
    "get_parcellation",
    "load_parcellation",
    "merge_parcellations",
]


# A dictionary containing all supported parcellations and their respective
# valid parameters.

# Each entry is a dictionary that must contain at least the following keys:
# * 'family': the parcellation's family name (e.g. 'Schaefer', 'SUIT')
# * 'space': the parcellation's space (e.g., 'MNI', 'SUIT')

# Optional keys:
# * 'valid_resolutions': a list of valid resolutions for the parcellation
# (e.g. [1, 2])

# TODO: have separate dictionary for built-in
_available_parcellations: Dict[str, Dict[Any, Any]] = {
    "SUITxSUIT": {"family": "SUIT", "space": "SUIT"},
    "SUITxMNI": {"family": "SUIT", "space": "MNI152NLin6Asym"},
}

# Add Schaefer parcellation info
for n_rois in range(100, 1001, 100):
    for t_net in [7, 17]:
        t_name = f"Schaefer{n_rois}x{t_net}"
        _available_parcellations[t_name] = {
            "family": "Schaefer",
            "n_rois": n_rois,
            "yeo_networks": t_net,
            "space": "MNI152NLin6Asym",
        }
# Add Tian parcellation info
for scale in range(1, 5):
    t_name = f"TianxS{scale}x7TxMNI6thgeneration"
    _available_parcellations[t_name] = {
        "family": "Tian",
        "scale": scale,
        "magneticfield": "7T",
        "space": "MNI152NLin6Asym",
    }
    t_name = f"TianxS{scale}x3TxMNI6thgeneration"
    _available_parcellations[t_name] = {
        "family": "Tian",
        "scale": scale,
        "magneticfield": "3T",
        "space": "MNI152NLin6Asym",
    }
    t_name = f"TianxS{scale}x3TxMNInonlinear2009cAsym"
    _available_parcellations[t_name] = {
        "family": "Tian",
        "scale": scale,
        "magneticfield": "3T",
        "space": "MNI152NLin2009cAsym",
    }
# Add AICHA parcellation info
for version in (1, 2):
    _available_parcellations[f"AICHA_v{version}"] = {
        "family": "AICHA",
        "version": version,
        "space": "IXI549Space",
    }
# Add Shen parcellation info
for year in (2013, 2015, 2019):
    if year == 2013:
        for n_rois in (50, 100, 150):
            _available_parcellations[f"Shen_{year}_{n_rois}"] = {
                "family": "Shen",
                "year": 2013,
                "n_rois": n_rois,
                "space": "MNI152NLin2009cAsym",
            }
    elif year == 2015:
        _available_parcellations["Shen_2015_268"] = {
            "family": "Shen",
            "year": 2015,
            "n_rois": 268,
            "space": "MNI152NLin2009cAsym",
        }
    elif year == 2019:
        _available_parcellations["Shen_2019_368"] = {
            "family": "Shen",
            "year": 2019,
            "n_rois": 368,
            "space": "MNI152NLin2009cAsym",
        }
# Add Yan parcellation info
for n_rois in range(100, 1001, 100):
    # Add Yeo networks
    for yeo_network in [7, 17]:
        _available_parcellations[f"Yan{n_rois}xYeo{yeo_network}"] = {
            "family": "Yan",
            "n_rois": n_rois,
            "yeo_networks": yeo_network,
            "space": "MNI152NLin6Asym",
        }
    # Add Kong networks
    _available_parcellations[f"Yan{n_rois}xKong17"] = {
        "family": "Yan",
        "n_rois": n_rois,
        "kong_networks": 17,
        "space": "MNI152NLin6Asym",
    }
# Add Brainnetome parcellation info
for threshold in [0, 25, 50]:
    _available_parcellations[f"Brainnetome_thr{threshold}"] = {
        "family": "Brainnetome",
        "threshold": threshold,
        "space": "MNI152NLin6Asym",
    }


def register_parcellation(
    name: str,
    parcellation_path: Union[str, Path],
    parcels_labels: List[str],
    space: str,
    overwrite: bool = False,
) -> None:
    """Register a custom user parcellation.

    Parameters
    ----------
    name : str
        The name of the parcellation.
    parcellation_path : str or pathlib.Path
        The path to the parcellation file.
    parcels_labels : list of str
        The list of labels for the parcellation.
    space : str
        The template space of the parcellation, for e.g., "MNI152NLin6Asym".
    overwrite : bool, optional
        If True, overwrite an existing parcellation with the same name.
        Does not apply to built-in parcellations (default False).

    Raises
    ------
    ValueError
        If the parcellation name is already registered and overwrite is set to
        False or if the parcellation name is a built-in parcellation.

    """
    # Check for attempt of overwriting built-in parcellations
    if name in _available_parcellations:
        if overwrite is True:
            logger.info(f"Overwriting {name} parcellation")
            if (
                _available_parcellations[name]["family"]
                != "CustomUserParcellation"
            ):
                raise_error(
                    f"Cannot overwrite {name} parcellation. "
                    "It is a built-in parcellation."
                )
        else:
            raise_error(
                f"Parcellation {name} already registered. Set "
                "`overwrite=True` to update its value."
            )
    # Convert str to Path
    if not isinstance(parcellation_path, Path):
        parcellation_path = Path(parcellation_path)
    # Add user parcellation info
    _available_parcellations[name] = {
        "path": str(parcellation_path.absolute()),
        "labels": parcels_labels,
        "family": "CustomUserParcellation",
        "space": space,
    }


def list_parcellations() -> List[str]:
    """List all the available parcellations.

    Returns
    -------
    list of str
        A list with all available parcellations.

    """
    return sorted(_available_parcellations.keys())


def get_parcellation(
    parcellation: List[str],
    target_data: Dict[str, Any],
    extra_input: Optional[Dict[str, Any]] = None,
) -> Tuple["Nifti1Image", List[str]]:
    """Get parcellation, tailored for the target image.

    Parameters
    ----------
    parcellation : list of str
        The name(s) of the parcellation(s).
    target_data : dict
        The corresponding item of the data object to which the parcellation
        will be applied.
    extra_input : dict, optional
        The other fields in the data object. Useful for accessing other data
        kinds that needs to be used in the computation of parcellations
        (default None).

    Returns
    -------
    Nifti1Image
        The parcellation image.
    list of str
        Parcellation labels.

    Raises
    ------
    RuntimeError
        If warp / transformation file extension is not ".mat" or ".h5".
    ValueError
        If ``extra_input`` is None when ``target_data``'s space is native.

    """
    # Check pre-requirements for space manipulation
    target_space = target_data["space"]
    # Set target standard space to target space
    target_std_space = target_space
    # Extra data type requirement check if target space is native
    if target_space == "native":
        # Check for extra inputs
        if extra_input is None:
            raise_error(
                "No extra input provided, requires `Warp` and `T1w` "
                "data types in particular for transformation to "
                f"{target_data['space']} space for further computation."
            )
        # Set target standard space to warp file space source
        target_std_space = extra_input["Warp"]["src"]

    # Get the min of the voxels sizes and use it as the resolution
    target_img = target_data["data"]
    resolution = np.min(target_img.header.get_zooms()[:3])

    # Create component-scoped tempdir
    tempdir = WorkDirManager().get_tempdir(prefix="parcellations")
    # Create element-scoped tempdir so that warped parcellation is
    # available later as nibabel stores file path reference for
    # loading on computation
    element_tempdir = WorkDirManager().get_element_tempdir(
        prefix="parcellations"
    )

    # Load the parcellations
    all_parcellations = []
    all_labels = []
    for name in parcellation:
        img, labels, _, space = load_parcellation(
            name=name,
            resolution=resolution,
        )

        # Convert parcellation spaces if required
        if space != target_std_space:
            # Get xfm file
            xfm_file_path = get_xfm(src=space, dst=target_std_space)
            # Get target standard space template
            target_std_space_template_img = get_template(
                space=target_std_space,
                target_data=target_data,
                extra_input=extra_input,
            )

            # Save parcellation image to a component-scoped tempfile
            parcellation_path = tempdir / f"{name}.nii.gz"
            nib.save(img, parcellation_path)

            # Save template
            target_std_space_template_path = (
                tempdir / f"{target_std_space}_T1w_{resolution}.nii.gz"
            )
            nib.save(
                target_std_space_template_img, target_std_space_template_path
            )

            # Set warped parcellation path
            warped_parcellation_path = element_tempdir / (
                f"{name}_warped_from_{space}_to_" f"{target_std_space}.nii.gz"
            )

            logger.debug(
                f"Using ANTs to warp {name} "
                f"from {space} to {target_std_space}"
            )
            # Set antsApplyTransforms command
            apply_transforms_cmd = [
                "antsApplyTransforms",
                "-d 3",
                "-e 3",
                "-n 'GenericLabel[NearestNeighbor]'",
                f"-i {parcellation_path.resolve()}",
                f"-r {target_std_space_template_path.resolve()}",
                f"-t {xfm_file_path.resolve()}",
                f"-o {warped_parcellation_path.resolve()}",
            ]
            # Call antsApplyTransforms
            run_ext_cmd(name="antsApplyTransforms", cmd=apply_transforms_cmd)

            raw_img = nib.load(warped_parcellation_path)
            # Remove extra dimension added by ANTs
            img = image.math_img("np.squeeze(img)", img=raw_img)

        # Resample parcellation to target image
        img_to_merge = image.resample_to_img(
            source_img=img,
            target_img=target_img,
            interpolation="nearest",
            copy=True,
        )

        all_parcellations.append(img_to_merge)
        all_labels.append(labels)

    # Avoid merging if there is only one parcellation
    if len(all_parcellations) == 1:
        resampled_parcellation_img = all_parcellations[0]
        labels = all_labels[0]
    # Parcellations are already transformed to target standard space
    else:
        resampled_parcellation_img, labels = merge_parcellations(
            parcellations_list=all_parcellations,
            parcellations_names=parcellation,
            labels_lists=all_labels,
        )

    # Warp parcellation if target space is native
    if target_space == "native":
        # Save parcellation image to a component-scoped tempfile
        prewarp_parcellation_path = tempdir / "prewarp_parcellation.nii.gz"
        nib.save(resampled_parcellation_img, prewarp_parcellation_path)

        # Create an element-scoped tempfile for warped output
        warped_parcellation_path = (
            element_tempdir / "parcellation_warped.nii.gz"
        )

        # Check for warp file type to use correct tool
        warp_file_ext = extra_input["Warp"]["path"].suffix
        if warp_file_ext == ".mat":
            logger.debug("Using FSL for parcellation warping")
            # Set applywarp command
            applywarp_cmd = [
                "applywarp",
                "--interp=nn",
                f"-i {prewarp_parcellation_path.resolve()}",
                # use resampled reference
                f"-r {target_data['reference_path'].resolve()}",
                f"-w {extra_input['Warp']['path'].resolve()}",
                f"-o {warped_parcellation_path.resolve()}",
            ]
            # Call applywarp
            run_ext_cmd(name="applywarp", cmd=applywarp_cmd)

        elif warp_file_ext == ".h5":
            logger.debug("Using ANTs for parcellation warping")
            # Set antsApplyTransforms command
            apply_transforms_cmd = [
                "antsApplyTransforms",
                "-d 3",
                "-e 3",
                "-n 'GenericLabel[NearestNeighbor]'",
                f"-i {prewarp_parcellation_path.resolve()}",
                # use resampled reference
                f"-r {target_data['reference_path'].resolve()}",
                f"-t {extra_input['Warp']['path'].resolve()}",
                f"-o {warped_parcellation_path.resolve()}",
            ]
            # Call antsApplyTransforms
            run_ext_cmd(name="antsApplyTransforms", cmd=apply_transforms_cmd)

        else:
            raise_error(
                msg=(
                    "Unknown warp / transformation file extension: "
                    f"{warp_file_ext}"
                ),
                klass=RuntimeError,
            )

        # Load nifti
        resampled_parcellation_img = nib.load(warped_parcellation_path)

    # Delete tempdir
    WorkDirManager().delete_tempdir(tempdir)

    return resampled_parcellation_img, labels  # type: ignore


def load_parcellation(
    name: str,
    parcellations_dir: Union[str, Path, None] = None,
    resolution: Optional[float] = None,
    path_only: bool = False,
) -> Tuple[Optional["Nifti1Image"], List[str], Path, str]:
    """Load a brain parcellation (including a label file).

    If it is a built-in parcellation and the file is not present in the
    ``parcellations_dir`` directory, it will be downloaded.

    Parameters
    ----------
    name : str
        The name of the parcellation. Check valid options by calling
        :func:`.list_parcellations`.
    parcellations_dir : str or pathlib.Path, optional
        Path where the parcellations files are stored. The default location is
        "$HOME/junifer/data/parcellations" (default None).
    resolution : float, optional
        The desired resolution of the parcellation to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None).
    path_only : bool, optional
        If True, the parcellation image will not be loaded (default False).

    Returns
    -------
    Nifti1Image or None
        Loaded parcellation image.
    list of str
        Parcellation labels.
    pathlib.Path
        File path to the parcellation image.
    str
        The space of the parcellation.

    Raises
    ------
    ValueError
        If ``name`` is invalid or if the parcellation values and labels
        don't have equal dimension or if the value range is invalid.

    """
    # Check for valid parcellation name
    if name not in _available_parcellations:
        raise_error(
            f"Parcellation {name} not found. "
            f"Valid options are: {list_parcellations()}"
        )

    # Copy parcellation definition to avoid edits in original object
    parcellation_definition = _available_parcellations[name].copy()
    t_family = parcellation_definition.pop("family")
    # Remove space conditionally
    if t_family not in ["SUIT", "Tian"]:
        space = parcellation_definition.pop("space")
    else:
        space = parcellation_definition["space"]

    # Check if the parcellation family is custom or built-in
    if t_family == "CustomUserParcellation":
        parcellation_fname = Path(parcellation_definition["path"])
        parcellation_labels = parcellation_definition["labels"]
    else:
        parcellation_fname, parcellation_labels = _retrieve_parcellation(
            family=t_family,
            parcellations_dir=parcellations_dir,
            resolution=resolution,
            **parcellation_definition,
        )

    # Load parcellation image and values
    logger.info(f"Loading parcellation {parcellation_fname.absolute()!s}")
    parcellation_img = None
    if path_only is False:
        # Load image via nibabel
        parcellation_img = nib.load(parcellation_fname)
        # Get unique values
        parcel_values = np.unique(parcellation_img.get_fdata())
        # Check for dimension
        if len(parcel_values) - 1 != len(parcellation_labels):
            raise_error(
                f"Parcellation {name} has {len(parcel_values) - 1} parcels "
                f"but {len(parcellation_labels)} labels."
            )
        # Sort values
        parcel_values.sort()
        # Check if value range is invalid
        if np.any(np.diff(parcel_values) != 1):
            raise_error(
                f"Parcellation {name} must have all the values in the range  "
                f"[0, {len(parcel_values)}]."
            )

    # Type-cast to remove errors
    parcellation_img = typing.cast("Nifti1Image", parcellation_img)
    return parcellation_img, parcellation_labels, parcellation_fname, space


def _retrieve_parcellation(
    family: str,
    parcellations_dir: Union[str, Path, None] = None,
    resolution: Optional[float] = None,
    **kwargs,
) -> Tuple[Path, List[str]]:
    """Retrieve a brain parcellation object from nilearn or online source.

    Only returns one parcellation per call. Call function multiple times for
    different parameter specifications. Only retrieves parcellation if it is
    not yet in parcellations_dir.

    Parameters
    ----------
    family : {"Schaefer", "SUIT", "Tian", "AICHA", "Shen", "Yan"}
        The name of the parcellation family.
    parcellations_dir : str or pathlib.Path, optional
        Path where the retrieved parcellations file are stored. The default
        location is "$HOME/junifer/data/parcellations" (default None).
    resolution : float, optional
        The desired resolution of the parcellation to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None).
    **kwargs
        Use to specify parcellation-specific keyword arguments found in the
        following section.

    Other Parameters
    ----------------
    * Schaefer :
      ``n_rois`` : {100, 200, 300, 400, 500, 600, 700, 800, 900, 1000}
            Granularity of parcellation to be used.
       ``yeo_network`` : {7, 17}, optional
            Number of Yeo networks to use (default 7).
    * Tian :
        ``scale`` : {1, 2, 3, 4}
            Scale of parcellation (defines granularity).
        ``space`` : {"MNI152NLin6Asym", "MNI152NLin2009cAsym"}, optional
            Space of parcellation (default "MNI152NLin6Asym"). (For more
            information see https://github.com/yetianmed/subcortex)
        ``magneticfield`` : {"3T", "7T"}, optional
            Magnetic field (default "3T").
    * SUIT :
        ``space`` : {"MNI152NLin6Asym", "SUIT"}, optional
            Space of parcellation (default "MNI"). (For more information
            see http://www.diedrichsenlab.org/imaging/suit.htm).
    * AICHA :
        ``version`` : {1, 2}, optional
            Version of parcellation (default 2).
    * Shen :
        ``year`` : {2013, 2015, 2019}, optional
            Year of the parcellation to use (default 2015).
        ``n_rois`` : int, optional
            Number of ROIs to use. Can be ``50, 100, or 150`` for
            ``year = 2013`` but is fixed at ``268`` for ``year = 2015`` and at
            ``368`` for ``year = 2019``.
    * Yan :
        ``n_rois`` : {100, 200, 300, 400, 500, 600, 700, 800, 900, 1000}
            Granularity of the parcellation to be used.
        ``yeo_networks`` : {7, 17}, optional
            Number of Yeo networks to use (default None).
        ``kong_networks`` : {17}, optional
            Number of Kong networks to use (default None).
    * Brainnetome :
        ``threshold`` : {0, 25, 50}
            Threshold for the probabilistic maps of subregion.

    Returns
    -------
    pathlib.Path
        File path to the parcellation image.
    list of str
        Parcellation labels.

    Raises
    ------
    ValueError
        If the parcellation's name is invalid.

    """
    if parcellations_dir is None:
        parcellations_dir = (
            Path().home() / "junifer" / "data" / "parcellations"
        )
        # Create default junifer data directory if not present
        parcellations_dir.mkdir(exist_ok=True, parents=True)
    # Convert str to Path
    elif not isinstance(parcellations_dir, Path):
        parcellations_dir = Path(parcellations_dir)

    logger.info(f"Fetching one of {family} parcellations.")

    # Retrieval details per family
    if family == "Schaefer":
        parcellation_fname, parcellation_labels = _retrieve_schaefer(
            parcellations_dir=parcellations_dir,
            resolution=resolution,
            **kwargs,
        )
    elif family == "SUIT":
        parcellation_fname, parcellation_labels = _retrieve_suit(
            parcellations_dir=parcellations_dir,
            resolution=resolution,
            **kwargs,
        )
    elif family == "Tian":
        parcellation_fname, parcellation_labels = _retrieve_tian(
            parcellations_dir=parcellations_dir,
            resolution=resolution,
            **kwargs,
        )
    elif family == "AICHA":
        parcellation_fname, parcellation_labels = _retrieve_aicha(
            parcellations_dir=parcellations_dir,
            resolution=resolution,
            **kwargs,
        )
    elif family == "Shen":
        parcellation_fname, parcellation_labels = _retrieve_shen(
            parcellations_dir=parcellations_dir,
            resolution=resolution,
            **kwargs,
        )
    elif family == "Yan":
        parcellation_fname, parcellation_labels = _retrieve_yan(
            parcellations_dir=parcellations_dir,
            resolution=resolution,
            **kwargs,
        )
    elif family == "Brainnetome":
        parcellation_fname, parcellation_labels = _retrieve_brainnetome(
            parcellations_dir=parcellations_dir,
            resolution=resolution,
            **kwargs,
        )
    else:
        raise_error(
            f"The provided parcellation name {family} cannot be retrieved."
        )

    return parcellation_fname, parcellation_labels


def _retrieve_schaefer(
    parcellations_dir: Path,
    resolution: Optional[float] = None,
    n_rois: Optional[int] = None,
    yeo_networks: int = 7,
) -> Tuple[Path, List[str]]:
    """Retrieve Schaefer parcellation.

    Parameters
    ----------
    parcellations_dir : pathlib.Path
        The path to the parcellation data directory.
    resolution : float, optional
        The desired resolution of the parcellation to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None). Available resolutions for this
        parcellation are 1mm and 2mm.
    n_rois : {100, 200, 300, 400, 500, 600, 700, 800, 900, 1000}, optional
        Granularity of the parceallation to be used (default None).
    yeo_networks : {7, 17}, optional
        Number of Yeo networks to use (default 7).

    Returns
    -------
    pathlib.Path
        File path to the parcellation image.
    list of str
        Parcellation labels.

    Raises
    ------
    ValueError
        If invalid value is provided for ``n_rois`` or ``yeo_networks`` or if
        there is a problem fetching the parcellation.

    """
    logger.info("Parcellation parameters:")
    logger.info(f"\tresolution: {resolution}")
    logger.info(f"\tn_rois: {n_rois}")
    logger.info(f"\tyeo_networks: {yeo_networks}")

    # Check n_rois value
    _valid_n_rois = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    if n_rois not in _valid_n_rois:
        raise_error(
            f"The parameter `n_rois` ({n_rois}) needs to be one of the "
            f"following: {_valid_n_rois}"
        )

    # Check networks
    _valid_networks = [7, 17]
    if yeo_networks not in _valid_networks:
        raise_error(
            f"The parameter `yeo_networks` ({yeo_networks}) needs to be one "
            f"of the following: {_valid_networks}"
        )

    # Check resolution
    _valid_resolutions = [1, 2]
    resolution = closest_resolution(resolution, _valid_resolutions)

    # Define parcellation and label file names
    parcellation_fname = (
        parcellations_dir
        / "schaefer_2018"
        / (
            f"Schaefer2018_{n_rois}Parcels_{yeo_networks}Networks_order_"
            f"FSLMNI152_{resolution}mm.nii.gz"
        )
    )
    parcellation_lname = (
        parcellations_dir
        / "schaefer_2018"
        / (f"Schaefer2018_{n_rois}Parcels_{yeo_networks}Networks_order.txt")
    )

    # Check existence of parcellation
    if not (parcellation_fname.exists() and parcellation_lname.exists()):
        logger.info(
            "At least one of the parcellation files are missing. "
            "Fetching using nilearn."
        )
        datasets.fetch_atlas_schaefer_2018(
            n_rois=n_rois,
            yeo_networks=yeo_networks,
            resolution_mm=resolution,  # type: ignore we know it's 1 or 2
            data_dir=parcellations_dir.resolve(),
        )

    # Load labels
    labels = [
        "_".join(x.split("_")[1:])
        for x in pd.read_csv(parcellation_lname, sep="\t", header=None)
        .iloc[:, 1]
        .to_list()
    ]

    return parcellation_fname, labels


def _retrieve_tian(
    parcellations_dir: Path,
    resolution: Optional[float] = None,
    scale: Optional[int] = None,
    space: str = "MNI152NLin6Asym",
    magneticfield: str = "3T",
) -> Tuple[Path, List[str]]:
    """Retrieve Tian parcellation.

    Parameters
    ----------
    parcellations_dir : pathlib.Path
        The path to the parcellation data directory.
    resolution : float, optional
        The desired resolution of the parcellation to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None). Available resolutions for this
        parcellation depend on the space and magnetic field.
    scale : {1, 2, 3, 4}, optional
        Scale of parcellation (defines granularity) (default None).
    space : {"MNI152NLin6Asym", "MNI152NLin2009cAsym"}, optional
        Space of parcellation (default "MNI152NLin6Asym"). (For more
        information see https://github.com/yetianmed/subcortex)
    magneticfield : {"3T", "7T"}, optional
        Magnetic field (default "3T").

    Returns
    -------
    pathlib.Path
        File path to the parcellation image.
    list of str
        Parcellation labels.

    Raises
    ------
    RuntimeError
        If there is a problem fetching files.
    ValueError
        If invalid value is provided for ``scale`` or ``magneticfield`` or
        ``space``.

    """
    logger.info("Parcellation parameters:")
    logger.info(f"\tresolution: {resolution}")
    logger.info(f"\tscale: {scale}")
    logger.info(f"\tspace: {space}")
    logger.info(f"\tmagneticfield: {magneticfield}")

    # Check scale
    _valid_scales = [1, 2, 3, 4]
    if scale not in _valid_scales:
        raise_error(
            f"The parameter `scale` ({scale}) needs to be one of the "
            f"following: {_valid_scales}"
        )

    # Check resolution
    _valid_resolutions = []  # avoid pylance error
    if magneticfield == "3T":
        _valid_spaces = ["MNI152NLin6Asym", "MNI152NLin2009cAsym"]
        if space == "MNI152NLin6Asym":
            _valid_resolutions = [1, 2]
        elif space == "MNI152NLin2009cAsym":
            _valid_resolutions = [2]
        else:
            raise_error(
                f"The parameter `space` ({space}) for 3T needs to be one of "
                f"the following: {_valid_spaces}"
            )
    elif magneticfield == "7T":
        _valid_resolutions = [1.6]
        if space != "MNI152NLin6Asym":
            raise_error(
                f"The parameter `space` ({space}) for 7T needs to be "
                f"MNI152NLin6Asym"
            )
    else:
        raise_error(
            f"The parameter `magneticfield` ({magneticfield}) needs to be "
            f"one of the following: 3T or 7T"
        )
    resolution = closest_resolution(resolution, _valid_resolutions)

    # Define parcellation and label file names
    if magneticfield == "3T":
        parcellation_fname_base_3T = (
            parcellations_dir / "Tian2020MSA_v1.1" / "3T" / "Subcortex-Only"
        )
        parcellation_lname = parcellation_fname_base_3T / (
            f"Tian_Subcortex_S{scale}_3T_label.txt"
        )
        if space == "MNI152NLin6Asym":
            parcellation_fname = parcellation_fname_base_3T / (
                f"Tian_Subcortex_S{scale}_{magneticfield}.nii.gz"
            )
            if resolution == 1:
                parcellation_fname = (
                    parcellation_fname_base_3T
                    / f"Tian_Subcortex_S{scale}_{magneticfield}_1mm.nii.gz"
                )
        elif space == "MNI152NLin2009cAsym":
            space = "2009cAsym"
            parcellation_fname = parcellation_fname_base_3T / (
                f"Tian_Subcortex_S{scale}_{magneticfield}_{space}.nii.gz"
            )
    elif magneticfield == "7T":
        parcellation_fname_base_7T = (
            parcellations_dir / "Tian2020MSA_v1.1" / "7T"
        )
        parcellation_fname_base_7T.mkdir(exist_ok=True, parents=True)
        parcellation_fname = (
            parcellations_dir
            / "Tian2020MSA_v1.1"
            / f"{magneticfield}"
            / (f"Tian_Subcortex_S{scale}_{magneticfield}.nii.gz")
        )
        # define 7T labels (b/c currently no labels file available for 7T)
        scale7Trois = {1: 16, 2: 34, 3: 54, 4: 62}
        labels = [
            ("parcel_" + str(x)) for x in np.arange(1, scale7Trois[scale] + 1)
        ]
        parcellation_lname = parcellation_fname_base_7T / (
            f"Tian_Subcortex_S{scale}_7T_labelnumbering.txt"
        )
        with open(parcellation_lname, "w") as filehandle:
            for listitem in labels:
                filehandle.write(f"{listitem}\n")
        logger.info(
            "Currently there are no labels provided for the 7T Tian "
            "parcellation. A simple numbering scheme for distinction was "
            "therefore used."
        )

    # Check existence of parcellation
    if not (parcellation_fname.exists() and parcellation_lname.exists()):
        logger.info(
            "At least one of the parcellation files are missing, fetching."
        )
        # Set URL
        url = (
            "https://www.nitrc.org/frs/download.php/12012/Tian2020MSA_v1.1.zip"
        )

        logger.info(f"Downloading TIAN from {url}")
        # Store initial download in a tempdir
        with tempfile.TemporaryDirectory() as tmpdir:
            # Make HTTP request
            try:
                resp = httpx.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise_error(
                    f"Error response {exc.response.status_code} while "
                    f"requesting {exc.request.url!r}",
                    klass=RuntimeError,
                )
            else:
                # Set tempfile for storing initial content and unzipping
                zip_fname = Path(tmpdir) / "Tian2020MSA_v1.1.zip"
                # Open tempfile and write content
                with open(zip_fname, "wb") as f:
                    f.write(resp.content)
                # Unzip tempfile
                with zipfile.ZipFile(zip_fname, "r") as zip_ref:
                    zip_ref.extractall(parcellations_dir.as_posix())
                # Clean after unzipping
                if (parcellations_dir / "__MACOSX").exists():
                    shutil.rmtree((parcellations_dir / "__MACOSX").as_posix())

    # Load labels
    labels = pd.read_csv(parcellation_lname, sep=" ", header=None)[0].to_list()

    return parcellation_fname, labels


def _retrieve_suit(
    parcellations_dir: Path,
    resolution: Optional[float],
    space: str = "MNI152NLin6Asym",
) -> Tuple[Path, List[str]]:
    """Retrieve SUIT parcellation.

    Parameters
    ----------
    parcellations_dir : pathlib.Path
        The path to the parcellation data directory.
    resolution : float, optional
        The desired resolution of the parcellation to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None). Available resolutions for this parcellation
        are 1mm and 2mm.
    space : {"MNI152NLin6Asym", "SUIT"}, optional
        Space of parcellation (default "MNI152NLin6Asym"). (For more
        information see http://www.diedrichsenlab.org/imaging/suit.htm).

    Returns
    -------
    pathlib.Path
        File path to the parcellation image.
    list of str
        Parcellation labels.

    Raises
    ------
    RuntimeError
        If there is a problem fetching files.
    ValueError
        If invalid value is provided for ``space``.

    """
    logger.info("Parcellation parameters:")
    logger.info(f"\tresolution: {resolution}")
    logger.info(f"\tspace: {space}")

    # Check space
    _valid_spaces = ["MNI152NLin6Asym", "SUIT"]
    if space not in _valid_spaces:
        raise_error(
            f"The parameter `space` ({space}) needs to be one of the "
            f"following: {_valid_spaces}"
        )

    # Check resolution
    _valid_resolutions = [1]
    resolution = closest_resolution(resolution, _valid_resolutions)

    # Format space if MNI; required for the file name
    if space == "MNI152NLin6Asym":
        space = "MNI"

    # Define parcellation and label file names
    parcellation_fname = (
        parcellations_dir / "SUIT" / (f"SUIT_{space}Space_{resolution}mm.nii")
    )
    parcellation_lname = (
        parcellations_dir / "SUIT" / (f"SUIT_{space}Space_{resolution}mm.tsv")
    )

    # Check existence of parcellation
    if not (parcellation_fname.exists() and parcellation_lname.exists()):
        logger.info(
            "At least one of the parcellation files is missing, fetching."
        )
        # Create local directory if not present
        parcellation_fname.parent.mkdir(exist_ok=True, parents=True)
        # Set URL
        url_basis = (
            "https://github.com/DiedrichsenLab/cerebellar_atlases/raw"
            "/master/Diedrichsen_2009"
        )
        if space == "MNI":
            url = f"{url_basis}/atl-Anatom_space-MNI_dseg.nii"
        else:  # if not MNI, then SUIT
            url = f"{url_basis}/atl-Anatom_space-SUIT_dseg.nii"
        url_labels = f"{url_basis}/atl-Anatom.tsv"

        # Make HTTP requests
        with httpx.Client(follow_redirects=True) as client:
            # Download parcellation file
            logger.info(f"Downloading SUIT parcellation from {url}")
            try:
                img_resp = client.get(url)
                img_resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise_error(
                    f"Error response {exc.response.status_code} while "
                    f"requesting {exc.request.url!r}",
                    klass=RuntimeError,
                )
            else:
                with open(parcellation_fname, "wb") as f:
                    f.write(img_resp.content)
            # Download label file
            logger.info(f"Downloading SUIT labels from {url_labels}")
            try:
                label_resp = client.get(url_labels)
                label_resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise_error(
                    f"Error response {exc.response.status_code} while "
                    f"requesting {exc.request.url!r}",
                    klass=RuntimeError,
                )
            else:
                # Load labels
                labels = pd.read_csv(
                    io.StringIO(label_resp.content.decode("utf-8")),
                    sep="\t",
                    usecols=["name"],
                )
                labels.to_csv(parcellation_lname, sep="\t", index=False)

    # Load labels
    labels = pd.read_csv(parcellation_lname, sep="\t", usecols=["name"])[
        "name"
    ].to_list()

    return parcellation_fname, labels


def _retrieve_aicha(
    parcellations_dir: Path,
    resolution: Optional[float] = None,
    version: int = 2,
) -> Tuple[Path, List[str]]:
    """Retrieve AICHA parcellation.

    Parameters
    ----------
    parcellations_dir : pathlib.Path
        The path to the parcellation data directory.
    resolution : float, optional
        The desired resolution of the parcellation to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None). Available resolution for this
        parcellation is 2mm.
    version : {1, 2}, optional
        The version of the parcellation to use (default 2).

    Returns
    -------
    pathlib.Path
        File path to the parcellation image.
    list of str
        Parcellation labels.

    Raises
    ------
    RuntimeError
        If there is a problem fetching files.
    ValueError
        If invalid value is provided for ``version``.

    Warns
    -----
    RuntimeWarning
        Until the authors confirm the space, the warning will be issued.

    Notes
    -----
    The resolution of the parcellation is 2mm and although v2 provides
    1mm, it is only for display purpose as noted in the release document.

    """
    # Issue warning until space is confirmed by authors
    warn_with_log(
        "The current space for AICHA parcellations are IXI549Space, but are "
        "not confirmed by authors, until that this warning will be issued."
    )

    logger.info("Parcellation parameters:")
    logger.info(f"\tresolution: {resolution}")
    logger.info(f"\tversion: {version}")

    # Check version
    _valid_version = [1, 2]
    if version not in _valid_version:
        raise_error(
            f"The parameter `version` ({version}) needs to be one of the "
            f"following: {_valid_version}"
        )

    # Check resolution
    _valid_resolutions = [1]
    resolution = closest_resolution(resolution, _valid_resolutions)

    # Define parcellation and label file names
    parcellation_fname = (
        parcellations_dir / f"AICHA_v{version}" / "AICHA" / "AICHA.nii"
    )
    parcellation_lname = Path()
    if version == 1:
        parcellation_lname = (
            parcellations_dir
            / f"AICHA_v{version}"
            / "AICHA"
            / "AICHA_vol1.txt"
        )
    elif version == 2:
        parcellation_lname = (
            parcellations_dir
            / f"AICHA_v{version}"
            / "AICHA"
            / "AICHA_vol3.txt"
        )

    # Check existence of parcellation
    if not (parcellation_fname.exists() and parcellation_lname.exists()):
        logger.info(
            "At least one of the parcellation files are missing, fetching."
        )
        # Set file name on server according to version
        server_filename = ""
        if version == 1:
            server_filename = "aicha_v1.zip"
        elif version == 2:
            server_filename = "AICHA_v2.tar.zip"
        # Set URL
        url = f"http://www.gin.cnrs.fr/wp-content/uploads/{server_filename}"

        logger.info(f"Downloading AICHA v{version} from {url}")
        # Store initial download in a tempdir
        with tempfile.TemporaryDirectory() as tmpdir:
            # Make HTTP request
            try:
                resp = httpx.get(url, follow_redirects=True)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise_error(
                    f"Error response {exc.response.status_code} while "
                    f"requesting {exc.request.url!r}",
                    klass=RuntimeError,
                )
            else:
                # Set tempfile for storing initial content and unzipping
                parcellation_zip_path = Path(tmpdir) / server_filename
                # Open tempfile and write content
                with open(parcellation_zip_path, "wb") as f:
                    f.write(resp.content)
                # Unzip tempfile
                with zipfile.ZipFile(parcellation_zip_path, "r") as zip_ref:
                    if version == 1:
                        zip_ref.extractall(
                            (parcellations_dir / "AICHA_v1").as_posix()
                        )
                    elif version == 2:
                        zip_ref.extractall(Path(tmpdir).as_posix())
                        # Extract tarfile for v2
                        with tarfile.TarFile(
                            Path(tmpdir) / "aicha_v2.tar", "r"
                        ) as tar_ref:
                            tar_ref.extractall(
                                (parcellations_dir / "AICHA_v2").as_posix()
                            )
                # Cleanup after unzipping
                if (
                    parcellations_dir / f"AICHA_v{version}" / "__MACOSX"
                ).exists():
                    shutil.rmtree(
                        (
                            parcellations_dir
                            / f"AICHA_v{version}"
                            / "__MACOSX"
                        ).as_posix()
                    )

    # Load labels
    labels = pd.read_csv(
        parcellation_lname, sep="\t", header=None, skiprows=[0]  # type: ignore
    )[0].to_list()

    return parcellation_fname, labels


def _retrieve_shen(  # noqa: C901
    parcellations_dir: Path,
    resolution: Optional[float] = None,
    year: int = 2015,
    n_rois: int = 268,
) -> Tuple[Path, List[str]]:
    """Retrieve Shen parcellation.

    Parameters
    ----------
    parcellations_dir : pathlib.Path
        The path to the parcellation data directory.
    resolution : float, optional
        The desired resolution of the parcellation to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None). Available resolutions for this parcellation
        are 1mm and 2mm for ``year = 2013`` and ``year = 2015`` but fixed to
        1mm for ``year = 2019``.
    year : {2013, 2015, 2019}, optional
        The year of the parcellation to use (default 2015).
    n_rois : int, optional
        Number of ROIs. Can be ``50, 100, or 150`` for ``year = 2013`` but is
        fixed at ``268`` for ``year = 2015`` and at ``368`` for
        ``year = 2019``.

    Returns
    -------
    pathlib.Path
        File path to the parcellation image.
    list of str
        Parcellation labels.

    Raises
    ------
    RuntimeError
        If there is a problem fetching files.
    ValueError
        If invalid value or combination is provided for ``year`` and
        ``n_rois``.

    """
    logger.info("Parcellation parameters:")
    logger.info(f"\tresolution: {resolution}")
    logger.info(f"\tyear: {year}")
    logger.info(f"\tn_rois: {n_rois}")

    # Check resolution
    _valid_resolutions = [1, 2]
    resolution = closest_resolution(resolution, _valid_resolutions)

    # Check year value
    _valid_year = (2013, 2015, 2019)
    if year not in _valid_year:
        raise_error(
            f"The parameter `year` ({year}) needs to be one of the "
            f"following: {_valid_year}"
        )

    # Check n_rois value
    _valid_n_rois = [50, 100, 150, 268, 368]
    if n_rois not in _valid_n_rois:
        raise_error(
            f"The parameter `n_rois` ({n_rois}) needs to be one of the "
            f"following: {_valid_n_rois}"
        )

    # Check combinations
    if resolution == 2 and year == 2019:
        raise_error(
            "The parameter combination `resolution = 2` and `year = 2019` is "
            "invalid"
        )
    if n_rois in (268, 368) and year == 2013:
        raise_error(
            f"The parameter combination `resolution = {resolution}` and "
            "`year = 2013` is invalid"
        )
    if n_rois in (50, 100, 150) and year in (2015, 2019):
        raise_error(
            f"The parameter combination `resolution = {resolution}` and "
            f"`year = {year}` is invalid"
        )
    if (n_rois == 268 and year == 2019) or (n_rois == 368 and year == 2015):
        raise_error(
            f"The parameter combination `resolution = {resolution}` and "
            f"`year = {year}` is invalid"
        )

    # Define parcellation and label file names
    if year == 2013:
        parcellation_fname = (
            parcellations_dir
            / "Shen_2013"
            / "shenetal_neuroimage2013"
            / f"fconn_atlas_{n_rois}_{resolution}mm.nii"
        )
        parcellation_lname = (
            parcellations_dir
            / "Shen_2013"
            / "shenetal_neuroimage2013"
            / f"Group_seg{n_rois}_BAindexing_setA.txt"
        )
    elif year == 2015:
        parcellation_fname = (
            parcellations_dir
            / "Shen_2015"
            / f"shen_{resolution}mm_268_parcellation.nii.gz"
        )
    elif year == 2019:
        parcellation_fname = (
            parcellations_dir
            / "Shen_2019"
            / "Shen_1mm_368_parcellation.nii.gz"
        )

    # Check existence of parcellation
    if not parcellation_fname.exists():
        logger.info(
            "At least one of the parcellation files are missing, fetching."
        )

        # Set URL based on year
        url = ""
        if year == 2013:
            url = "https://www.nitrc.org/frs/download.php/5785/shenetal_neuroimage2013_funcatlas.zip"
        elif year == 2015:
            # Set URL based on resolution
            if resolution == 1:
                url = "https://www.nitrc.org/frs/download.php/7976/shen_1mm_268_parcellation.nii.gz"
            elif resolution == 2:
                url = "https://www.nitrc.org/frs/download.php/7977/shen_2mm_268_parcellation.nii.gz"
        elif year == 2019:
            url = "https://www.nitrc.org/frs/download.php/11629/shen_368.zip"

        logger.info(f"Downloading Shen {year} from {url}")
        # Store initial download in a tempdir
        with tempfile.TemporaryDirectory() as tmpdir:
            # Make HTTP request
            try:
                resp = httpx.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise_error(
                    f"Error response {exc.response.status_code} while "
                    f"requesting {exc.request.url!r}",
                    klass=RuntimeError,
                )
            else:
                if year in (2013, 2019):
                    parcellation_zip_path = Path(tmpdir) / f"Shen{year}.zip"
                    # Open tempfile and write content
                    with open(parcellation_zip_path, "wb") as f:
                        f.write(resp.content)
                    # Unzip tempfile
                    with zipfile.ZipFile(
                        parcellation_zip_path, "r"
                    ) as zip_ref:
                        zip_ref.extractall(
                            (parcellations_dir / f"Shen_{year}").as_posix()
                        )
                    # Cleanup after unzipping
                    if (
                        parcellations_dir / f"Shen_{year}" / "__MACOSX"
                    ).exists():
                        shutil.rmtree(
                            (
                                parcellations_dir / f"Shen_{year}" / "__MACOSX"
                            ).as_posix()
                        )
                elif year == 2015:
                    img_dir_path = parcellations_dir / "Shen_2015"
                    # Create local directory if not present
                    img_dir_path.mkdir(parents=True, exist_ok=True)
                    img_path = (
                        img_dir_path
                        / f"shen_{resolution}mm_268_parcellation.nii.gz"
                    )
                    # Create local file if not present
                    img_path.touch(exist_ok=True)
                    # Open tempfile and write content
                    with open(img_path, "wb") as f:
                        f.write(resp.content)

    # Load labels based on year
    if year == 2013:
        labels = (
            pd.read_csv(
                parcellation_lname,  # type: ignore
                sep=",",  # type: ignore
                header=None,  # type: ignore
                skiprows=[0],  # type: ignore
            )[1]
            .map(lambda x: x.strip())  # fix formatting
            .to_list()
        )
    elif year == 2015:
        labels = list(range(1, 269))
    elif year == 2019:
        labels = list(range(1, 369))

    return parcellation_fname, labels


def _retrieve_yan(
    parcellations_dir: Path,
    resolution: Optional[float] = None,
    n_rois: Optional[int] = None,
    yeo_networks: Optional[int] = None,
    kong_networks: Optional[int] = None,
) -> Tuple[Path, List[str]]:
    """Retrieve Yan parcellation.

    Parameters
    ----------
    parcellations_dir : pathlib.Path
        The path to the parcellation data directory.
    resolution : float, optional
        The desired resolution of the parcellation to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None). Available resolutions for this
        parcellation are 1mm and 2mm.
    n_rois : {100, 200, 300, 400, 500, 600, 700, 800, 900, 1000}, optional
        Granularity of the parcellation to be used (default None).
    yeo_networks : {7, 17}, optional
        Number of Yeo networks to use (default None).
    kong_networks : {17}, optional
        Number of Kong networks to use (default None).

    Returns
    -------
    pathlib.Path
        File path to the parcellation image.
    list of str
        Parcellation labels.

    Raises
    ------
    RuntimeError
        If there is a problem fetching files.
    ValueError
        If invalid value is provided for ``n_rois``, ``yeo_networks`` or
        ``kong_networks``.

    """
    logger.info("Parcellation parameters:")
    logger.info(f"\tresolution: {resolution}")
    logger.info(f"\tn_rois: {n_rois}")
    logger.info(f"\tyeo_networks: {yeo_networks}")
    logger.info(f"\tkong_networks: {kong_networks}")

    # Allow single network type
    if (not yeo_networks and not kong_networks) or (
        yeo_networks and kong_networks
    ):
        raise_error(
            "Either one of `yeo_networks` or `kong_networks` need to be "
            "specified."
        )

    # Check resolution
    _valid_resolutions = [1, 2]
    resolution = closest_resolution(resolution, _valid_resolutions)

    # Check n_rois value
    _valid_n_rois = list(range(100, 1001, 100))
    if n_rois not in _valid_n_rois:
        raise_error(
            f"The parameter `n_rois` ({n_rois}) needs to be one of the "
            f"following: {_valid_n_rois}"
        )

    parcellation_fname = Path()
    parcellation_lname = Path()
    if yeo_networks:
        # Check yeo_networks value
        _valid_yeo_networks = [7, 17]
        if yeo_networks not in _valid_yeo_networks:
            raise_error(
                f"The parameter `yeo_networks` ({yeo_networks}) needs to be "
                f"one of the following: {_valid_yeo_networks}"
            )
        # Define image and label file according to network
        parcellation_fname = (
            parcellations_dir
            / "Yan_2023"
            / (
                f"{n_rois}Parcels_Yeo2011_{yeo_networks}Networks_FSLMNI152_"
                f"{resolution}mm.nii.gz"
            )
        )
        parcellation_lname = (
            parcellations_dir
            / "Yan_2023"
            / f"{n_rois}Parcels_Yeo2011_{yeo_networks}Networks_LUT.txt"
        )
    elif kong_networks:
        # Check kong_networks value
        _valid_kong_networks = [17]
        if kong_networks not in _valid_kong_networks:
            raise_error(
                f"The parameter `kong_networks` ({kong_networks}) needs to be "
                f"one of the following: {_valid_kong_networks}"
            )
        # Define image and label file according to network
        parcellation_fname = (
            parcellations_dir
            / "Yan_2023"
            / (
                f"{n_rois}Parcels_Kong2022_{kong_networks}Networks_FSLMNI152_"
                f"{resolution}mm.nii.gz"
            )
        )
        parcellation_lname = (
            parcellations_dir
            / "Yan_2023"
            / f"{n_rois}Parcels_Kong2022_{kong_networks}Networks_LUT.txt"
        )

    # Check for existence of parcellation:
    if not parcellation_fname.exists() and not parcellation_lname.exists():
        logger.info(
            "At least one of the parcellation files are missing, fetching."
        )

        # Set URL based on network
        img_url = ""
        label_url = ""
        if yeo_networks:
            img_url = (
                "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/"
                "master/stable_projects/brain_parcellation/Yan2023_homotopic/"
                f"parcellations/MNI/yeo{yeo_networks}/{n_rois}Parcels_Yeo2011"
                f"_{yeo_networks}Networks_FSLMNI152_{resolution}mm.nii.gz"
            )
            label_url = (
                "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/"
                "master/stable_projects/brain_parcellation/Yan2023_homotopic/"
                f"parcellations/MNI/yeo{yeo_networks}/freeview_lut/{n_rois}"
                f"Parcels_Yeo2011_{yeo_networks}Networks_LUT.txt"
            )
        elif kong_networks:
            img_url = (
                "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/"
                "master/stable_projects/brain_parcellation/Yan2023_homotopic/"
                f"parcellations/MNI/kong17/{n_rois}Parcels_Kong2022"
                f"_17Networks_FSLMNI152_{resolution}mm.nii.gz"
            )
            label_url = (
                "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/"
                "master/stable_projects/brain_parcellation/Yan2023_homotopic/"
                f"parcellations/MNI/kong17/freeview_lut/{n_rois}Parcels_"
                "Kong2022_17Networks_LUT.txt"
            )

        # Make HTTP requests
        with httpx.Client() as client:
            # Download parcellation file
            logger.info(f"Downloading Yan 2023 parcellation from {img_url}")
            try:
                img_resp = client.get(img_url)
                img_resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise_error(
                    f"Error response {exc.response.status_code} while "
                    f"requesting {exc.request.url!r}",
                    klass=RuntimeError,
                )
            else:
                parcellation_img_path = Path(parcellation_fname)
                # Create local directory if not present
                parcellation_img_path.parent.mkdir(parents=True, exist_ok=True)
                # Create local file if not present
                parcellation_img_path.touch(exist_ok=True)
                # Open file and write content
                with open(parcellation_img_path, "wb") as f:
                    f.write(img_resp.content)
            # Download label file
            logger.info(f"Downloading Yan 2023 labels from {label_url}")
            try:
                label_resp = client.get(label_url)
                label_resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise_error(
                    f"Error response {exc.response.status_code} while "
                    f"requesting {exc.request.url!r}",
                    klass=RuntimeError,
                )
            else:
                parcellation_labels_path = Path(parcellation_lname)
                # Create local file if not present
                parcellation_labels_path.touch(exist_ok=True)
                # Open file and write content
                with open(parcellation_labels_path, "wb") as f:
                    f.write(label_resp.content)

    # Load label file
    labels = pd.read_csv(parcellation_lname, sep=" ", header=None)[1].to_list()

    return parcellation_fname, labels


def _retrieve_brainnetome(
    parcellations_dir: Path,
    resolution: Optional[float] = None,
    threshold: Optional[int] = None,
) -> Tuple[Path, List[str]]:
    """Retrieve Brainnetome parcellation.

    Parameters
    ----------
    parcellations_dir : pathlib.Path
        The path to the parcellation data directory.
    resolution : {1.0, 1.25, 2.0}, optional
        The desired resolution of the parcellation to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None). Available resolutions for this
        parcellation are 1mm, 1.25mm and 2mm.
    threshold : {0, 25, 50}, optional
        The threshold for the probabilistic maps of subregion (default None).

    Returns
    -------
    pathlib.Path
        File path to the parcellation image.
    list of str
        Parcellation labels.

    Raises
    ------
    RuntimeError
        If there is a problem fetching files.
    ValueError
        If invalid value is provided for ``threshold``.

    """
    logger.info("Parcellation parameters:")
    logger.info(f"\tresolution: {resolution}")
    logger.info(f"\tthreshold: {threshold}")

    # Check resolution
    _valid_resolutions = [1.0, 1.25, 2.0]
    resolution = closest_resolution(resolution, _valid_resolutions)

    # Check threshold value
    _valid_threshold = [0, 25, 50]
    if threshold not in _valid_threshold:
        raise_error(
            f"The parameter `threshold` ({threshold}) needs to be one of the "
            f"following: {_valid_threshold}"
        )
    # Correct resolution for further stuff
    if resolution in [1.0, 2.0]:
        resolution = int(resolution)

    parcellation_fname = (
        parcellations_dir
        / "BNA246"
        / f"BNA-maxprob-thr{threshold}-{resolution}mm.nii.gz"
    )

    # Check for existence of parcellation
    if not parcellation_fname.exists():
        # Set URL
        url = f"http://neurovault.org/media/images/1625/BNA-maxprob-thr{threshold}-{resolution}mm.nii.gz"

        logger.info(f"Downloading Brainnetome from {url}")
        # Make HTTP request
        try:
            resp = httpx.get(url, follow_redirects=True)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise_error(
                f"Error response {exc.response.status_code} while "
                f"requesting {exc.request.url!r}",
                klass=RuntimeError,
            )
        else:
            # Create local directory if not present
            parcellation_fname.parent.mkdir(parents=True, exist_ok=True)
            # Create file if not present
            parcellation_fname.touch(exist_ok=True)
            # Open file and write bytes
            parcellation_fname.write_bytes(resp.content)

    # Load labels
    labels = (
        sorted([f"SFG_L(R)_7_{i}" for i in range(1, 8)] * 2)
        + sorted([f"MFG_L(R)_7_{i}" for i in range(1, 8)] * 2)
        + sorted([f"IFG_L(R)_6_{i}" for i in range(1, 7)] * 2)
        + sorted([f"OrG_L(R)_6_{i}" for i in range(1, 7)] * 2)
        + sorted([f"PrG_L(R)_6_{i}" for i in range(1, 7)] * 2)
        + sorted([f"PCL_L(R)_2_{i}" for i in range(1, 3)] * 2)
        + sorted([f"STG_L(R)_6_{i}" for i in range(1, 7)] * 2)
        + sorted([f"MTG_L(R)_4_{i}" for i in range(1, 5)] * 2)
        + sorted([f"ITG_L(R)_7_{i}" for i in range(1, 8)] * 2)
        + sorted([f"FuG_L(R)_3_{i}" for i in range(1, 4)] * 2)
        + sorted([f"PhG_L(R)_6_{i}" for i in range(1, 7)] * 2)
        + sorted([f"pSTS_L(R)_2_{i}" for i in range(1, 3)] * 2)
        + sorted([f"SPL_L(R)_5_{i}" for i in range(1, 6)] * 2)
        + sorted([f"IPL_L(R)_6_{i}" for i in range(1, 7)] * 2)
        + sorted([f"PCun_L(R)_4_{i}" for i in range(1, 5)] * 2)
        + sorted([f"PoG_L(R)_4_{i}" for i in range(1, 5)] * 2)
        + sorted([f"INS_L(R)_6_{i}" for i in range(1, 7)] * 2)
        + sorted([f"CG_L(R)_7_{i}" for i in range(1, 8)] * 2)
        + sorted([f"MVOcC _L(R)_5_{i}" for i in range(1, 6)] * 2)
        + sorted([f"LOcC_L(R)_4_{i}" for i in range(1, 5)] * 2)
        + sorted([f"LOcC_L(R)_2_{i}" for i in range(1, 3)] * 2)
        + sorted([f"Amyg_L(R)_2_{i}" for i in range(1, 3)] * 2)
        + sorted([f"Hipp_L(R)_2_{i}" for i in range(1, 3)] * 2)
        + sorted([f"BG_L(R)_6_{i}" for i in range(1, 7)] * 2)
        + sorted([f"Tha_L(R)_8_{i}" for i in range(1, 9)] * 2)
    )

    return parcellation_fname, labels


def merge_parcellations(
    parcellations_list: List["Nifti1Image"],
    parcellations_names: List[str],
    labels_lists: List[List[str]],
) -> Tuple["Nifti1Image", List[str]]:
    """Merge all parcellations from a list into one parcellation.

    Parameters
    ----------
    parcellations_list : list of niimg-like object
        List of parcellations to merge.
    parcellations_names: list of str
        List of names for parcellations at the corresponding indices.
    labels_lists : list of list of str
        A list of lists. Each list in the list contains the labels for the
        parcellation at the corresponding index.

    Returns
    -------
    parcellation : niimg-like object
        The parcellation that results from merging the list of input
        parcellations.
    labels : list of str
        List of labels for the resultant parcellation.

    """
    # Check for duplicated labels
    labels_lists_flat = [item for sublist in labels_lists for item in sublist]
    if len(labels_lists_flat) != len(set(labels_lists_flat)):
        warn_with_log(
            "The parcellations have duplicated labels. "
            "Each label will be prefixed with the parcellation name."
        )
        for i_parcellation, t_labels in enumerate(labels_lists):
            labels_lists[i_parcellation] = [
                f"{parcellations_names[i_parcellation]}_{t_label}"
                for t_label in t_labels
            ]
    overlapping_voxels = False
    ref_parc = parcellations_list[0]
    parc_data = ref_parc.get_fdata()

    labels = labels_lists[0]

    for t_parc, t_labels in zip(parcellations_list[1:], labels_lists[1:]):
        if t_parc.shape != ref_parc.shape:
            warn_with_log(
                "The parcellations have different resolutions!"
                "Resampling all parcellations to the first one in the list."
            )
            t_parc = image.resample_to_img(
                t_parc, ref_parc, interpolation="nearest", copy=True
            )

        # Get the data from this parcellation
        t_parc_data = t_parc.get_fdata().copy()  # must be copied
        # Increase the values of each ROI to match the labels
        t_parc_data[t_parc_data != 0] += len(labels)

        # Only set new values for the voxels that are 0
        # This makes sure that the voxels that are in multiple
        # parcellations are assigned to the parcellation that was
        # first in the list.
        if np.any(parc_data[t_parc_data != 0] != 0):
            overlapping_voxels = True

        parc_data[parc_data == 0] += t_parc_data[parc_data == 0]
        labels.extend(t_labels)

    if overlapping_voxels:
        warn_with_log(
            "The parcellations have overlapping voxels. "
            "The overlapping voxels will be assigned to the "
            "parcellation that was first in the list."
        )

    parcellation_img_res = image.new_img_like(parcellations_list[0], parc_data)

    return parcellation_img_res, labels
