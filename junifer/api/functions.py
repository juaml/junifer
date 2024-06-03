"""Provide functions for cli."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import os
import shutil
import typing
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from ..datagrabber.base import BaseDataGrabber
from ..markers.base import BaseMarker
from ..markers.collection import MarkerCollection
from ..pipeline import WorkDirManager
from ..pipeline.registry import build
from ..preprocess.base import BasePreprocessor
from ..storage.base import BaseFeatureStorage
from ..utils import logger, raise_error
from .queue_context import GnuParallelLocalAdapter, HTCondorAdapter
from .utils import yaml


__all__ = ["run", "collect", "queue", "reset", "list_elements"]


def _get_datagrabber(datagrabber_config: Dict) -> BaseDataGrabber:
    """Get DataGrabber.

    Parameters
    ----------
    datagrabber_config : dict
        The config to get the DataGrabber using.

    Returns
    -------
    object
        The DataGrabber.

    """
    datagrabber_params = datagrabber_config.copy()
    datagrabber_kind = datagrabber_params.pop("kind")
    datagrabber = build(
        step="datagrabber",
        name=datagrabber_kind,
        baseclass=BaseDataGrabber,
        init_params=datagrabber_params,
    )
    datagrabber = typing.cast(BaseDataGrabber, datagrabber)
    return datagrabber


def _get_preprocessor(preprocessing_config: Dict) -> BasePreprocessor:
    """Get preprocessor.

    Parameters
    ----------
    preprocessing_config : dict
        The config to get the preprocessor using.

    Returns
    -------
    dict
        The preprocessor.

    """
    preprocessor_params = preprocessing_config.copy()
    preprocessor_kind = preprocessor_params.pop("kind")
    preprocessor = build(
        step="preprocessing",
        name=preprocessor_kind,
        baseclass=BasePreprocessor,
        init_params=preprocessor_params,
    )
    preprocessor = typing.cast(BasePreprocessor, preprocessor)
    return preprocessor


def run(
    workdir: Union[str, Path],
    datagrabber: Dict,
    markers: List[Dict],
    storage: Dict,
    preprocessors: Optional[List[Dict]] = None,
    elements: Union[str, List[Union[str, Tuple]], Tuple, None] = None,
) -> None:
    """Run the pipeline on the selected element.

    Parameters
    ----------
    workdir : str or pathlib.Path
        Directory where the pipeline will be executed.
    datagrabber : dict
        DataGrabber to use. Must have a key ``kind`` with the kind of
        DataGrabber to use. All other keys are passed to the DataGrabber
        constructor.
    markers : list of dict
        List of markers to extract. Each marker is a dict with at least two
        keys: ``name`` and ``kind``. The ``name`` key is used to name the
        output marker. The ``kind`` key is used to specify the kind of marker
        to extract. The rest of the keys are used to pass parameters to the
        marker calculation.
    storage : dict
        Storage to use. Must have a key ``kind`` with the kind of
        storage to use. All other keys are passed to the storage
        constructor.
    preprocessors : list of dict, optional
        List of preprocessors to use. Each preprocessor is a dict with at
        least a key ``kind`` specifying the preprocessor to use. All other keys
        are passed to the preprocessor constructor (default None).
    elements : str or tuple or list of str or tuple, optional
        Element(s) to process. Will be used to index the DataGrabber
        (default None).

    """
    # Convert str to Path
    if isinstance(workdir, str):
        workdir = Path(workdir)
    # Initiate working directory manager
    WorkDirManager(workdir)

    if not isinstance(elements, list) and elements is not None:
        elements = [elements]

    # Get datagrabber to use
    datagrabber_object = _get_datagrabber(datagrabber)

    # Copy to avoid changing the original dict
    _markers = [x.copy() for x in markers]
    built_markers = []
    for t_marker in _markers:
        kind = t_marker.pop("kind")
        t_m = build(
            step="marker",
            name=kind,
            baseclass=BaseMarker,
            init_params=t_marker,
        )
        built_markers.append(t_m)

    # Get storage engine to use
    storage_params = storage.copy()
    storage_kind = storage_params.pop("kind")
    if "single_output" not in storage_params:
        storage_params["single_output"] = False
    storage_object = build(
        step="storage",
        name=storage_kind,
        baseclass=BaseFeatureStorage,
        init_params=storage_params,
    )
    storage_object = typing.cast(BaseFeatureStorage, storage_object)

    # Get preprocessor to use (if provided)
    if preprocessors is not None:
        _preprocessors = [x.copy() for x in preprocessors]
        built_preprocessors = []
        for preprocessor in _preprocessors:
            preprocessor_object = _get_preprocessor(preprocessor)
            built_preprocessors.append(preprocessor_object)
    else:
        built_preprocessors = None

    # Create new marker collection
    mc = MarkerCollection(
        markers=built_markers,
        preprocessors=built_preprocessors,
        storage=storage_object,
    )
    mc.validate(datagrabber_object)

    # Fit elements
    with datagrabber_object:
        if elements is not None:
            for t_element in datagrabber_object.filter(
                elements  # type: ignore
            ):
                mc.fit(datagrabber_object[t_element])
        else:
            for t_element in datagrabber_object:
                mc.fit(datagrabber_object[t_element])


def collect(storage: Dict) -> None:
    """Collect and store data.

    Parameters
    ----------
    storage : dict
        Storage to use. Must have a key ``kind`` with the kind of
        storage to use. All other keys are passed to the storage
        constructor.

    """
    storage_params = storage.copy()
    storage_kind = storage_params.pop("kind")
    logger.info(f"Collecting data using {storage_kind}")
    logger.debug(f"\tStorage params: {storage_params}")
    if "single_output" not in storage_params:
        storage_params["single_output"] = False
    storage_object = build(
        step="storage",
        name=storage_kind,
        baseclass=BaseFeatureStorage,
        init_params=storage_params,
    )
    storage_object = typing.cast(BaseFeatureStorage, storage_object)
    logger.debug("Running storage.collect()")
    storage_object.collect()
    logger.info("Collect done")


def queue(
    config: Dict,
    kind: str,
    jobname: str = "junifer_job",
    overwrite: bool = False,
    elements: Union[str, List[Union[str, Tuple]], Tuple, None] = None,
    **kwargs: Union[str, int, bool, Dict, Tuple, List],
) -> None:
    """Queue a job to be executed later.

    Parameters
    ----------
    config : dict
        The configuration to be used for queueing the job.
    kind : {"HTCondor", "GNUParallelLocal"}
        The kind of job queue system to use.
    jobname : str, optional
        The name of the job (default "junifer_job").
    overwrite : bool, optional
        Whether to overwrite if job directory already exists (default False).
    elements : str or tuple or list of str or tuple, optional
        Element(s) to process. Will be used to index the DataGrabber
        (default None).
    **kwargs : dict
        The keyword arguments to pass to the job queue system.

    Raises
    ------
    ValueError
        If ``kind`` is invalid or
        if the ``jobdir`` exists and ``overwrite = False``.

    """
    valid_kind = ["HTCondor", "GNUParallelLocal"]
    if kind not in valid_kind:
        raise_error(
            f"Invalid value for `kind`: {kind}, "
            f"must be one of {valid_kind}"
        )

    # Create a folder within the CWD to store the job files / config
    jobdir = Path.cwd() / "junifer_jobs" / jobname
    logger.info(f"Creating job directory at {jobdir.resolve()!s}")
    if jobdir.exists():
        if not overwrite:
            raise_error(
                f"Job folder for {jobname} already exists. "
                "This error is raised to prevent overwriting job files "
                "that might be scheduled but not yet executed. "
                f"Either delete the directory {jobdir.absolute()!s} "
                "or set `overwrite=True.`"
            )
        else:
            logger.info(
                f"Deleting existing job directory at {jobdir.resolve()!s}"
            )
            shutil.rmtree(jobdir)
    jobdir.mkdir(exist_ok=True, parents=True)

    # Load modules
    if "with" in config:
        to_load = config["with"]
        # If there is a list of files to load, copy and remove the path
        # component
        fixed_load = []
        if not isinstance(to_load, list):
            to_load = [to_load]
        for item in to_load:
            if item.endswith(".py"):
                logger.debug(f"Copying {item} to ({jobdir.resolve()!s})")
                shutil.copy(src=item, dst=jobdir)
                fixed_load.append(Path(item).name)
            else:
                fixed_load.append(item)
        config["with"] = fixed_load

    # Save YAML
    yaml_config = jobdir / "config.yaml"
    logger.info(f"Writing YAML config to {yaml_config.resolve()!s}")
    yaml.dump(config, stream=yaml_config)

    # Get list of elements
    if elements is None:
        if "elements" in config:
            elements = config["elements"]
        else:
            # If no elements are specified, use all elements from the
            # datagrabber
            datagrabber = _get_datagrabber(config["datagrabber"])
            with datagrabber as dg:
                elements = dg.get_elements()
    # Listify elements
    if not isinstance(elements, list):
        elements: List[Union[str, Tuple]] = [elements]

    # Check job queueing system
    adapter = None
    if kind == "HTCondor":
        adapter = HTCondorAdapter(
            job_name=jobname,
            job_dir=jobdir,
            yaml_config_path=yaml_config,
            elements=elements,
            **kwargs,  # type: ignore
        )
    elif kind == "GNUParallelLocal":
        adapter = GnuParallelLocalAdapter(
            job_name=jobname,
            job_dir=jobdir,
            yaml_config_path=yaml_config,
            elements=elements,
            **kwargs,  # type: ignore
        )

    adapter.prepare()  # type: ignore
    logger.info("Queue done")


def reset(config: Dict) -> None:
    """Reset the storage and jobs directory.

    Parameters
    ----------
    config : dict
        The configuration to be used for resetting.

    """
    # Fetch storage
    storage = config["storage"]
    storage_uri = Path(storage["uri"])
    logger.info(f"Deleting {storage_uri.resolve()!s}")
    # Delete storage
    if storage_uri.exists():
        # Delete files in the job storage directory
        for file in storage_uri.parent.iterdir():
            file.unlink(missing_ok=True)
        # Remove job storage directory
        storage_uri.parent.rmdir()

    # Fetch job name (if present)
    if config.get("queue") is not None:
        queue = config["queue"]
        job_dir = (
            Path.cwd()
            / "junifer_jobs"
            / (queue.get("jobname") or "junifer_job")
        )
        logger.info(f"Deleting job directory at {job_dir.resolve()!s}")
        if job_dir.exists():
            # Remove files and directories
            shutil.rmtree(job_dir)
            # Remove parent directory (if empty)
            if not next(os.scandir(job_dir.parent), None):
                job_dir.parent.rmdir()


def list_elements(
    datagrabber: Dict,
    elements: Union[str, List[Union[str, Tuple]], Tuple, None] = None,
) -> str:
    """List elements of the datagrabber filtered using `elements`.

    Parameters
    ----------
    datagrabber : dict
        DataGrabber to index. Must have a key ``kind`` with the kind of
        DataGrabber to use. All other keys are passed to the DataGrabber
        constructor.
    elements : str or tuple or list of str or tuple, optional
        Element(s) to filter using. Will be used to index the DataGrabber
        (default None).

    """
    # Get datagrabber to use
    datagrabber_object = _get_datagrabber(datagrabber)

    # Fetch elements
    raw_elements_to_list = []
    with datagrabber_object:
        if elements is not None:
            for element in datagrabber_object.filter(elements):
                raw_elements_to_list.append(element)
        else:
            for element in datagrabber_object:
                raw_elements_to_list.append(element)

    elements_to_list = []
    for element in raw_elements_to_list:
        # Stringify elements if tuple for operation
        str_element = (
            ",".join(element) if isinstance(element, tuple) else element
        )
        elements_to_list.append(str_element)

    return "\n".join(elements_to_list)
