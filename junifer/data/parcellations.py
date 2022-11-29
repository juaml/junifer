"""Provide functions for parcellation."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import io
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import nibabel as nib
import numpy as np
import pandas as pd
import requests
from nilearn import datasets

from ..utils.logging import logger, raise_error
from .utils import closest_resolution


if TYPE_CHECKING:
    from nibabel import Nifti1Image


"""
A dictionary containing all supported parcellations and their respective valid
parameters.

Each entry is a dictionary that must contain at least the following keys:
* 'family': the parcellation's family name (e.g. 'Schaefer', 'SUIT')

Optional keys:
* 'valid_resolutions': a list of valid resolutions for the parcellation
(e.g. [1, 2])

"""
# TODO: have separate dictionary for built-in
_available_parcellations: Dict[str, Dict[Any, Any]] = {
    "SUITxSUIT": {"family": "SUIT", "space": "SUIT"},
    "SUITxMNI": {"family": "SUIT", "space": "MNI"},
}

# Add Schaefer parcellation info
for n_rois in range(100, 1001, 100):
    for t_net in [7, 17]:
        t_name = f"Schaefer{n_rois}x{t_net}"
        _available_parcellations[t_name] = {
            "family": "Schaefer",
            "n_rois": n_rois,
            "yeo_networks": t_net,
        }
# Add Tian parcellation info
for scale in range(1, 5):
    t_name = f"TianxS{scale}x7TxMNI6thgeneration"
    _available_parcellations[t_name] = {
        "family": "Tian",
        "scale": scale,
        "magneticfield": "7T",
        "space": "MNI6thgeneration",
    }
    t_name = f"TianxS{scale}x3TxMNI6thgeneration"
    _available_parcellations[t_name] = {
        "family": "Tian",
        "scale": scale,
        "magneticfield": "3T",
        "space": "MNI6thgeneration",
    }
    t_name = f"TianxS{scale}x3TxMNInonlinear2009cAsym"
    _available_parcellations[t_name] = {
        "family": "Tian",
        "scale": scale,
        "magneticfield": "3T",
        "space": "MNInonlinear2009cAsym",
    }


def register_parcellation(
    name: str,
    parcellation_path: Union[str, Path],
    parcels_labels: List[str],
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
                f"Parcellation {name} already registered. Set `overwrite=True`"
                "to update its value."
            )
    # Convert str to Path
    if not isinstance(parcellation_path, Path):
        parcellation_path = Path(parcellation_path)
    # Add user parcellation info
    _available_parcellations[name] = {
        "path": str(parcellation_path.absolute()),
        "labels": parcels_labels,
        "family": "CustomUserParcellation",
    }


def list_parcellations() -> List[str]:
    """List all the available parcellations.

    Returns
    -------
    list of str
        A list with all available parcellations.
    """
    return sorted(_available_parcellations.keys())


# def _check_resolution(resolution, valid_resolution):
#     if resolution is None:
#         return None
#     if resolution not in valid_resolution:
#         raise ValueError(f'Invalid resolution: {resolution}')
#     return resolution


# TODO: keyword arguments are not passed, check
def load_parcellation(
    name: str,
    parcellations_dir: Union[str, Path, None] = None,
    resolution: Optional[float] = None,
    path_only: bool = False,
) -> Tuple[Optional["Nifti1Image"], List[str], Path]:
    """Load a brain parcellation (including a label file).

    If it is a built-in parcellaions and file is not present in the
    `parcellations_dir` directory, it will be downloaded.

    Parameters
    ----------
    name : str
        The name of the parcellation. Check valid options by calling
        :func:`junifer.data.parcellations.list_parcellations`.
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
    """
    # Invalid parcellation name
    if name not in _available_parcellations:
        raise_error(
            f"Parcellation {name} not found. "
            f"Valid options are: {list_parcellations()}"
        )

    parcellation_definition = _available_parcellations[name].copy()
    t_family = parcellation_definition.pop("family")

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

    logger.info(f"Loading parcellation {str(parcellation_fname.absolute())}")

    parcellation_img = None
    if path_only is False:
        parcellation_img = nib.load(parcellation_fname)
        parcel_values = np.unique(parcellation_img.get_fdata())
        if len(parcel_values) - 1 != len(parcellation_labels):
            raise_error(
                f"Parcellation {name} has {len(parcel_values) - 1} parcels "
                f"but {len(parcellation_labels)} labels."
            )
        parcel_values.sort()
        if np.any(np.diff(parcel_values) != 1):
            raise_error(
                f"Parcellation {name} must have all the values in the range  "
                f"[0, {len(parcel_values)}]."
            )

    return parcellation_img, parcellation_labels, parcellation_fname


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
    family : str
        The name of the parcellation's family, e.g. 'Schaefer'.
    parcellations_dir : str or pathlib.Path, optional
        Path where the retrieved parcellations file are stored. The default
        location is "$HOME/junifer/data/parcellations" (default None).
    resolution : float, optional
        The desired resolution of the parcellation to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None).

    Other Parameters
    ----------------
    **kwargs
        Use to specify parcellation-specific keyword arguments:

    * Schaefer :
      ``n_rois`` : {100, 200, 300, 400, 500, 600, 700, 800, 900, 1000}
            Granularity of parcellation to be used.
       ``yeo_network`` : {7, 17}, optional
            Number of yeo networks to use (default 7).
    * Tian :
        ``scale`` : {1, 2, 3, 4}
            Scale of parcellation (defines granularity).
        ``space`` : {"MNI6thgeneration", "MNInonlinear2009cAsym"}, optional
            Space of parcellation (default "MNI6thgeneration"). (For more
            information see https://github.com/yetianmed/subcortex)
        ``magneticfield`` : {"3T", "7T"}, optional
            Magnetic field (default "3T").
    * SUIT :
        ``space`` : {"MNI", "SUIT"}, optional
            Space of parcellation (default "MNI"). (For more information
            see http://www.diedrichsenlab.org/imaging/suit.htm).

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
        parcellation_fname, parcellation_labesl = _retrieve_schaefer(
            parcellations_dir=parcellations_dir,
            resolution=resolution,
            **kwargs,
        )
    elif family == "SUIT":
        parcellation_fname, parcellation_labesl = _retrieve_suit(
            parcellations_dir=parcellations_dir,
            resolution=resolution,
            **kwargs,
        )
    elif family == "Tian":
        parcellation_fname, parcellation_labesl = _retrieve_tian(
            parcellations_dir=parcellations_dir,
            resolution=resolution,
            **kwargs,
        )
    else:
        raise_error(
            f"The provided parcellation name {family} cannot be retrieved."
        )

    return parcellation_fname, parcellation_labesl


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
        The path to the parcallations' data directory.
    resolution : float, optional
        The desired resolution of the parcellation to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None). Available resolutions for this
        parcellation are 1mm and 2mm.
    n_rois : {100, 200, 300, 400, 500, 600, 700, 800, 900, 1000}, optional
        Granularity of the parceallation to be used (default None).
    yeo_networks : {7, 17}, optional
        Number of yeo networks to use (default 7).

    Returns
    -------
    pathlib.Path
        File path to the parcellation image.
    list of str
        Parcellation labels.

    Raises
    ------
    ValueError
        If invalid value is provided for `n_rois` or `yeo_networks` or if
        there is a problem fetching the parcellation.
    """
    logger.info("Parcellatikon parameters:")
    logger.info(f"\tn_rois: {n_rois}")
    logger.info(f"\tyeo_networks: {yeo_networks}")
    logger.info(f"\tresolution: {resolution}")

    _valid_n_rois = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    _valid_networks = [7, 17]
    _valid_resolutions = [1, 2]

    if n_rois not in _valid_n_rois:
        raise_error(
            f"The parameter `n_rois` ({n_rois}) needs to be one of the "
            f"following: {_valid_n_rois}"
        )
    if yeo_networks not in _valid_networks:
        raise_error(
            f"The parameter `yeo_networks` ({yeo_networks}) needs to be one "
            f"of the following: {_valid_networks}"
        )

    resolution = closest_resolution(resolution, _valid_resolutions)

    # define file names
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

    # check existence of parcellation
    if not (parcellation_fname.exists() and parcellation_lname.exists()):
        logger.info(
            "At least one of the parcellation files are missing. "
            "Fetching using nilearn."
        )
        datasets.fetch_atlas_schaefer_2018(
            n_rois=n_rois,
            yeo_networks=yeo_networks,
            resolution_mm=resolution,  # type: ignore we know it's 1 or 2
            data_dir=str(parcellations_dir.absolute()),
        )

        if not (
            parcellation_fname.exists() and parcellation_lname.exists()
        ):  # pragma: no cover
            raise_error("There was a problem fetching the parcellations.")

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
    space: str = "MNI6thgeneration",
    magneticfield: str = "3T",
) -> Tuple[Path, List[str]]:
    """Retrieve Tian parcellation.

    Parameters
    ----------
    parcellations_dir : pathlib.Path
        The path to the parcellation data directory.
    resolution : float, optional
    resolution : float, optional
        The desired resolution of the parcellation to load. If it is not
        available, the closest resolution will be loaded. Preferably, use a
        resolution higher than the desired one. By default, will load the
        highest one (default None). Available resolutions for this
        parcellation depend on the space and magnetic field.
    scale : {1, 2, 3, 4}, optional
        Scale of parcellation (defines granularity) (default None).
    space : {"MNI6thgeneration", "MNInonlinear2009cAsym"}, optional
        Space of parcellation (default "MNI6thgeneration"). (For more
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
    ValueError
        If invalid value is provided for `scale` or `magneticfield` or `space`
        or if there is a problem fetching the parcellation.
    """
    # show parameters to user
    logger.info("Parcellation parameters:")
    logger.info(f"\tscale: {scale}")
    logger.info(f"\tspace: {space}")
    logger.info(f"\tmagneticfield: {magneticfield}")
    logger.info(f"\tresolution: {resolution}")
    # check validity of parameters
    _valid_scales = [1, 2, 3, 4]
    if scale not in _valid_scales:
        raise_error(
            f"The parameter `scale` ({scale}) needs to be one of the "
            f"following: {_valid_scales}"
        )

    _valid_resolutions = []  # avoid pylance error
    if magneticfield == "3T":
        _valid_spaces = ["MNI6thgeneration", "MNInonlinear2009cAsym"]
        if space == "MNI6thgeneration":
            _valid_resolutions = [1, 2]
        elif space == "MNInonlinear2009cAsym":
            _valid_resolutions = [2]
        else:
            raise_error(
                f"The parameter `space` ({space}) for 3T needs to be one of "
                f"the following: {_valid_spaces}"
            )
    elif magneticfield == "7T":
        _valid_resolutions = [1.6]
        if space != "MNI6thgeneration":
            raise_error(
                f"The parameter `space` ({space}) for 7T needs to be "
                f"MNI6thgeneration"
            )
    else:
        raise_error(
            f"The parameter `magneticfield` ({magneticfield}) needs to be "
            f"one of the following: 3T or 7T"
        )

    resolution = closest_resolution(resolution, _valid_resolutions)

    # define file names
    if magneticfield == "3T":
        parcellation_fname_base_3T = (
            parcellations_dir / "Tian2020MSA_v1.1" / "3T" / "Subcortex-Only"
        )
        parcellation_lname = parcellation_fname_base_3T / (
            f"Tian_Subcortex_S{scale}_3T_label.txt"
        )
        if space == "MNI6thgeneration":
            parcellation_fname = parcellation_fname_base_3T / (
                f"Tian_Subcortex_S{scale}_{magneticfield}.nii.gz"
            )
            if resolution == 1:
                parcellation_fname = (
                    parcellation_fname_base_3T
                    / f"Tian_Subcortex_S{scale}_{magneticfield}_1mm.nii.gz"
                )
        elif space == "MNInonlinear2009cAsym":
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
                filehandle.write("%s\n" % listitem)
        logger.info(
            "Currently there are no labels provided for the 7T Tian "
            "parcellation. A simple numbering scheme for distinction was "
            "therefore used."
        )
    else:  # pragma: no cover
        raise_error("This should not happen. Please report this error.")

    # check existence of parcellation
    if not (parcellation_fname.exists() and parcellation_lname.exists()):
        logger.info(
            "At least one of the parcellation files are missing, fetching."
        )

        url_basis = (
            "https://www.nitrc.org/frs/download.php/12012/Tian2020MSA_v1.1.zip"
        )

        logger.info(f"Downloading TIAN from {url_basis}")
        with tempfile.TemporaryDirectory() as tmpdir:
            parcellation_download = requests.get(url_basis)
            parcellation_zip_fname = Path(tmpdir) / "Tian2020MSA_v1.1.zip"
            with open(parcellation_zip_fname, "wb") as f:
                f.write(parcellation_download.content)
            with zipfile.ZipFile(parcellation_zip_fname, "r") as zip_ref:
                zip_ref.extractall(parcellations_dir.as_posix())
            # clean after unzipping
            if (parcellations_dir / "__MACOSX").exists():
                shutil.rmtree((parcellations_dir / "__MACOSX").as_posix())

        labels = pd.read_csv(parcellation_lname, sep=" ", header=None)[
            0
        ].to_list()

        if not (parcellation_fname.exists() and parcellation_lname.exists()):
            raise_error("There was a problem fetching the parcellations.")

    labels = pd.read_csv(parcellation_lname, sep=" ", header=None)[0].to_list()

    return parcellation_fname, labels


def _retrieve_suit(
    parcellations_dir: Path, resolution: Optional[float], space: str = "MNI"
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
    space : {"MNI", "SUIT"}, optional
        Space of parcellation (default "MNI"). (For more information
        see http://www.diedrichsenlab.org/imaging/suit.htm).

    Returns
    ------
    pathlib.Path
        File path to the parcellation image.
    list of str
        Parcellation labels.

    Raises
    ------
    ValueError
        If invalid value is provided for `space` or if there is a problem
        fetching the parcellation.
    """
    logger.info("Parcellation parameters:")
    logger.info(f"\tspace: {space}")

    _valid_spaces = ["MNI", "SUIT"]

    # check validity of parameters
    if space not in _valid_spaces:
        raise_error(
            f"The parameter `space` ({space}) needs to be one of the "
            f"following: {_valid_spaces}"
        )

    # TODO: Validate this with Vera
    _valid_resolutions = [1]

    resolution = closest_resolution(resolution, _valid_resolutions)

    # define file names
    parcellation_fname = (
        parcellations_dir / "SUIT" / (f"SUIT_{space}Space_{resolution}mm.nii")
    )
    parcellation_lname = (
        parcellations_dir / "SUIT" / (f"SUIT_{space}Space_{resolution}mm.tsv")
    )

    # check existence of parcellation
    if not (parcellation_fname.exists() and parcellation_lname.exists()):
        parcellation_fname.parent.mkdir(exist_ok=True, parents=True)
        logger.info(
            "At least one of the parcellation files is missing, fetching."
        )

        url_basis = (
            "https://github.com/DiedrichsenLab/cerebellar_atlases/raw"
            "/master/Diedrichsen_2009/"
        )
        url_MNI = url_basis + "atl-Anatom_space-MNI_dseg.nii"
        url_SUIT = url_basis + "atl-Anatom_space-SUIT_dseg.nii"
        url_labels = url_basis + "atl-Anatom.tsv"

        if space == "MNI":
            logger.info(f"Downloading {url_MNI}")
            parcellation_download = requests.get(url_MNI)
            with open(parcellation_fname, "wb") as f:
                f.write(parcellation_download.content)
        else:  # if not MNI, then SUIT
            logger.info(f"Downloading {url_SUIT}")
            parcellation_download = requests.get(url_SUIT)
            with open(parcellation_fname, "wb") as f:
                f.write(parcellation_download.content)

        labels_download = requests.get(url_labels)
        labels = pd.read_csv(
            io.StringIO(labels_download.content.decode("utf-8")),
            sep="\t",
            usecols=["name"],
        )

        labels.to_csv(parcellation_lname, sep="\t", index=False)
        if (
            not parcellation_fname.exists() and parcellation_lname.exists()
        ):  # pragma: no cover
            raise_error("There was a problem fetching the parcellations.")

    labels = pd.read_csv(parcellation_lname, sep="\t", usecols=["name"])[
        "name"
    ].to_list()

    return parcellation_fname, labels
