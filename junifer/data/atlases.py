# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
# License: AGPL
from pathlib import Path
import io
import requests
import numpy as np
import pandas as pd

import nibabel as nib
from nilearn import datasets

from ..utils.logging import logger, raise_error

"""
A dictionary containing all supported atlases and their respective valid
parameters.

Each entry is a dictionary that must contain at least the following keys:
* 'family': the atlas family name (e.g. 'Schaefer', 'SUIT')

Optional keys:
* 'valid_resolutions': a list of valid resolutions for the atlas (e.g. [1, 2])

"""
_available_atlases = {
    'SUITxSUIT': {
        'family': 'SUIT',
        'sace': 'SUIT'
    },
    'SUITxMNI': {
        'family': 'SUIT',
        'space': 'MNI'
    },

}

for n_rois in range(100, 1001, 100):
    for t_net in [7, 17]:
        t_name = f'Schaefer{n_rois}x{t_net}'
        _available_atlases[t_name] = {
            'family': 'Schaefer',
            'n_rois': n_rois,
            'yeo_networks': t_net,
        }


def register_atlas(name, atlas_path, atl_labels, overwrite=False):
    """Register a custom user atlas.

    Parameters
    ----------
    name : str
        The name of the atlas.
    atlas_path : str
        The path to the atlas file.
    atl_labels : list(str)
        The list of labels for the atlas.
    overwrite : bool
        If True, overwrite an existing atlas with the same name. Defaults to
        False.

    Raises
    ------
    ValueError
        If the atlas name is already registered and overwrite is set to False
        or if the atlas name is a built-in atlas.
    """
    if name in _available_atlases:
        if overwrite is True:
            logger.info(f'Overwritting {name} atlas')
            if _available_atlases[name]['family'] != 'CustomUserAtlas':
                raise_error(
                    f'Cannot overwrite {name} atlas. It is a built-in atlas.')
        else:
            raise_error(
                f'Atlas {name} already registered. Set `overwrite=True` to '
                'update its value.')
    _available_atlases[name] = {
        'path': atlas_path, 'labels': atl_labels,
        'family': 'CustomUserAtlas'}


def list_atlases():
    """
    List all the available atlases.

    Returns
    -------
    out : list(str) or dict
        A list or dict with all available atlases.
    """
    return sorted(_available_atlases.keys())


def _check_resolution(resolution, valid_resolution):
    if resolution is None:
        return None
    if resolution not in valid_resolution:
        raise ValueError(f'Invalid resolution: {resolution}')
    return resolution


def load_atlas(name, atlas_dir=None, resolution=None, path_only=False):
    """
    Loads a brain atlas (including a label file).
    If it is built-in atlas and file is not present in the `atlas_dir`
    directory, it will be downloaded.

    Parameters
    ----------
    name : str
        The name of the atlas.
        Check valid options by calling `list_atlases`.
    atlas_dir: path
        Path where the atlas files are stored.
        Defaults to: $HOME/junifer/data/atlas
    resolution : int
        The (desired) resolution of the atlas to load. If its not available,
        the closest resolution will be loaded. Preferably, use a resolution
        higher than the desired one. Defaults to None (load the highest one).
    path_only : bool
        If True, the atlas image will not be loaded.

    Parameters (optional, atlas dependent)
    --------------------------------------
    Use to specify atlas specific keyword arguments. .

    Schaefer :
        n_rois (required) : int
            Granularity of atlas to be used. Valid values: between 100 and 1000
            (included) in steps of 100.
        yeo_network (optional) : int
            Number of yeo networks to use. Valid values: 7, 17. Defaults to 7.

    Tian :
        # TODO add

    SUIT :
        space (optional) : str
            Space of atlas can be either 'MNI' or 'SUIT' (for more information
            see http://www.diedrichsenlab.org/imaging/suit.htm). Defaults to
            'MNI'.

    Returns
    -------
    atlas_img : niimg-like object or None
        Loaded atlas image.
    atlas_labels : List of str
        Atlas labels.
    atlas_fname : Path
        File path to the atlas image.
    """

    atlas_definition = _available_atlases[name].copy()
    t_family = atlas_definition.pop('family')

    if t_family == 'CustomUserAtlas':
        atlas_fname = atlas_definition['path']
        atlas_labels = atlas_definition['labels']
    else:
        # retrieve atlases by passing arguments on to _retrieve_atlas()
        atlas_fname, atlas_labels = _retrieve_atlas(
            t_family, atlas_dir=atlas_dir, **atlas_definition)

    logger.info(
        f'Loading atlas {atlas_fname.as_posix()}')  # type: ignore

    atlas_img = None
    if path_only is False:
        atlas_img = nib.load(atlas_fname)

    return atlas_img, atlas_labels, atlas_fname


def _retrieve_atlas(family, atlas_dir=None, resolution=None, **kwargs):
    """
    Retrieves a brain atlas object either from nilearn or a specified online
    source. Only returns one atlas per call. Call function multiple times for
    different parameter specifications. Only retrieves atlas if it is not yet
    in atlas_dir.

    Parameters (required)
    ---------------------
    family : str
        Specify by name of atlas family, e.g. 'Schaefer'.
    atlas_dir: path
        Path to where to store the retrieved atlas file.
        Defaults to: $HOME/junifer/data/atlas
    resolution : int
        The (desired) resolution of the atlas to load. If its not available,
        the closest resolution will be loaded. Preferably, use a resolution
        higher than the desired one. Defaults to None (load the highest one).

    Parameters (optional, atlas dependent)
    --------------------------------------
    Use to specify atlas specific keyword arguments

    Schaefer :
        n_rois (required) : int
            Granularity of atlas to be used. Valid values: between 100 and 1000
            (included) in steps of 100.
        yeo_network (optional) : int
            Number of yeo networks to use [7 or 17]. Defaults to 7.
    SUIT :
        space (optional) : str
            Space of atlas can be either 'MNI' or 'SUIT' (for more information
            see http://www.diedrichsenlab.org/imaging/suit.htm). Defaults to
            'MNI'.

    Returns
    -------
    atlas_fname : Path
        File path to the atlas image.
    atlas_labels : List of str
        Atlas labels.
    """
    if atlas_dir is None:
        atlas_dir = Path().home() / 'junifer' / 'data' / 'atlas'
        atlas_dir.mkdir(exist_ok=True, parents=True)

    logger.info(f"Fetching one of {family} atlas.")

    # retrieval details per atlas
    if family == 'Schaefer':
        atlas_fname, atl_labels = \
            _retrieve_schaefer(atlas_dir, resolution=resolution, **kwargs)
    elif family == 'SUIT':
        atlas_fname, atl_labels = \
            _retrieve_suit(atlas_dir, resolution=resolution, **kwargs)
    else:
        raise_error(
            f"The provided atlas name {family} cannot be retrieved. ")

    return atlas_fname, atl_labels


def _closest_resolution(resolution, valid_resolution):
    closest = None
    if not isinstance(valid_resolution, np.ndarray):
        valid_resolution = np.array(valid_resolution)
    if resolution is None:
        logger.info('Resolution set to None, using highest resolution.')
        closest  = np.min(valid_resolution)
    elif any(x <= resolution for x in valid_resolution):
        # Case 1: get the highest closest resolution
        closest = np.max(valid_resolution[valid_resolution <= resolution])
    else:
        # Case 2: get the lower closest resolution
        closest = np.min(valid_resolution)

    return closest


def _retrieve_schaefer(atlas_dir, resolution, n_rois=None, yeo_networks=7):
    logger.info('Atlas parameters:')
    logger.info(f'\tn_rois: {n_rois}')
    logger.info(f'\tyeo_networks: {yeo_networks}')
    logger.info(f'\tresolution: {resolution}')

    _valid_n_rois = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    _valid_networks = [7, 17]
    _valid_resolutions = [1, 2]

    if n_rois not in _valid_n_rois:
        raise_error(
            f'The parameter `n_rois` ({n_rois}) needs to be one of the '
            f'following: {_valid_n_rois}')
    if yeo_networks not in _valid_networks:
        raise_error(
            f'The parameter `yeo_networks` ({yeo_networks}) needs to be one of'
            f' the following: {_valid_networks}')

    resolution = _closest_resolution(resolution, _valid_resolutions)

    # define file names
    atlas_fname = atlas_dir / 'schaefer_2018' / (
        f'Schaefer2018_{n_rois}Parcels_{yeo_networks}Networks_order_'
        f'FSLMNI152_{resolution}mm.nii.gz')
    atlas_lname = atlas_dir / 'schaefer_2018' / (
        f'Schaefer2018_{n_rois}Parcels_{yeo_networks}Networks_order.txt')

    # check existance of atlas
    if not (atlas_fname.exists() and atlas_lname.exists()):
        logger.info(
            'At least one of the atlas files is missing. '
            'Fetching using nilearn.')
        datasets.fetch_atlas_schaefer_2018(
            n_rois=n_rois,
            yeo_networks=yeo_networks,
            resolution_mm=resolution,
            data_dir=atlas_dir.as_posix())

        if not (atlas_fname.exists() and atlas_lname.exists()):
            raise_error('There was a problem fetching the atlases.')

    # Load labels
    labels = [
        '_'.join(x.split('_')[1:])
        for x in pd.read_csv(
            atlas_lname, sep='\t', header=None).iloc[:, 1].to_list()
    ]

    return atlas_fname, labels


def _retrieve_suit(atlas_path, resolution, space='MNI'):
    logger.info('Atlas parameters:')
    logger.info(f'\tspace: {space}')

    _valid_spaces = ['MNI', 'SUIT']

    # check validity of atlas parameters
    if space not in _valid_spaces:
        raise_error(
            f'The parameter `space` ({space}) needs to be one of the '
            f'following: {_valid_spaces}')

    # TODO: Validate this with Vera
    _valid_resolutions = [1]

    resolution = _closest_resolution(resolution, _valid_resolutions)

    # define file names
    atlas_fname = atlas_path / 'SUIT' / (
        f'SUIT_{space}Space_{resolution}mm.nii')
    atlas_lname = atlas_path / 'SUIT' / (
        f'SUIT_{space}Space_{resolution}mm.tsv')

    # check existance of atlas
    if not (atlas_fname.exists() and atlas_lname.exists()):
        logger.info(
            'At least one of the atlas files is missing. '
            'Fetching.')

        url_basis = (
            'https://github.com/DiedrichsenLab/cerebellar_atlases/blob'
            '/master/Diedrichsen_2009/')
        url_MNI = url_basis + 'atl-Anatom_space-MNI_dseg.nii'
        url_SUIT = url_basis + 'atl-Anatom_space-SUIT_dseg.nii'
        url_labels = url_basis + 'atl-Anatom.tsv'

        if space == 'MNI':
            logger.info(f'Downloading {url_MNI}')
            atlas_download = requests.get(url_MNI)
            with open(atlas_fname, 'wb') as f:
                f.write(atlas_download.content)
        elif space == 'SUIT':
            logger.info(f'Downloading {url_SUIT}')
            atlas_download = requests.get(url_SUIT)
            with open(atlas_fname, 'wb') as f:
                f.write(atlas_download.content)

        labels_download = requests.get(url_labels)
        labels = pd.read_csv(
            io.StringIO(labels_download.content.decode("utf-8")),
            sep='\t', usecols=['name'])

        labels.to_csv(atlas_lname, sep='\t', index=False)
        if not (atlas_fname.exists() and atlas_lname.exists()):
            raise_error('There was a problem fetching the atlases.')

    labels = pd.read_csv(
        atlas_lname, sep='\t', usecols=['name'])['name'].to_list()

    return atlas_fname, labels
