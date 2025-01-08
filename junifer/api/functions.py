"""Provide API functions."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import os
import shutil
from pathlib import Path
from typing import Optional, Union

from ..api.queue_context import GnuParallelLocalAdapter, HTCondorAdapter
from ..datagrabber import BaseDataGrabber
from ..markers import BaseMarker
from ..pipeline import (
    MarkerCollection,
    PipelineComponentRegistry,
    WorkDirManager,
)
from ..preprocess import BasePreprocessor
from ..storage import BaseFeatureStorage
from ..typing import (
    DataGrabberLike,
    Elements,
    MarkerLike,
    PreprocessorLike,
    StorageLike,
)
from ..utils import logger, raise_error, warn_with_log, yaml


__all__ = ["collect", "list_elements", "queue", "reset", "run"]


def _get_datagrabber(datagrabber_config: dict) -> DataGrabberLike:
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
    return PipelineComponentRegistry().build_component_instance(
        step="datagrabber",
        name=datagrabber_config.pop("kind"),
        baseclass=BaseDataGrabber,
        init_params=datagrabber_config,
    )


def _get_preprocessor(preprocessing_config: dict) -> PreprocessorLike:
    """Get Preprocessor.

    Parameters
    ----------
    preprocessing_config : dict
        The config to get the Preprocessor using.

    Returns
    -------
    dict
        The Preprocessor.

    """
    return PipelineComponentRegistry().build_component_instance(
        step="preprocessing",
        name=preprocessing_config.pop("kind"),
        baseclass=BasePreprocessor,
        init_params=preprocessing_config,
    )


def _get_marker(marker_config: dict) -> MarkerLike:
    """Get Marker.

    Parameters
    ----------
    marker_config : dict
        The config to get the Marker using.

    Returns
    -------
    object
        The Marker.

    """
    return PipelineComponentRegistry().build_component_instance(
        step="marker",
        name=marker_config.pop("kind"),
        baseclass=BaseMarker,
        init_params=marker_config,
    )


def _get_storage(storage_config: dict) -> StorageLike:
    """Get Storage.

    Parameters
    ----------
    storage_config : dict
        The config to get the Storage using.

    Returns
    -------
    dict
        The Storage.

    """
    return PipelineComponentRegistry().build_component_instance(
        step="storage",
        name=storage_config.pop("kind"),
        baseclass=BaseFeatureStorage,
        init_params=storage_config,
    )


def run(
    workdir: Union[str, Path, dict],
    datagrabber: dict,
    markers: list[dict],
    storage: dict,
    preprocessors: Optional[list[dict]] = None,
    elements: Optional[Elements] = None,
) -> None:
    """Run the pipeline on the selected element.

    Parameters
    ----------
    workdir : str or pathlib.Path or dict
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
    preprocessors : list of dict or None, optional
        List of preprocessors to use. Each preprocessor is a dict with at
        least a key ``kind`` specifying the preprocessor to use. All other keys
        are passed to the preprocessor constructor (default None).
    elements : list or None, optional
        Element(s) to process. Will be used to index the DataGrabber
        (default None).

    Raises
    ------
    ValueError
        If ``workdir.cleanup=False`` when ``len(elements) > 1``.
    RuntimeError
        If invalid element selectors are found.

    """
    # Conditional to handle workdir config
    if isinstance(workdir, (str, Path)):
        if isinstance(workdir, str):
            workdir = {"workdir": Path(workdir), "cleanup": True}
        else:
            workdir = {"workdir": workdir, "cleanup": True}
    elif isinstance(workdir, dict):
        workdir["workdir"] = workdir.pop("path")

    # Initiate working directory manager with correct variation
    if not workdir["cleanup"]:
        if elements is None or len(elements) > 1:
            raise_error(
                "Cannot disable `workdir.cleanup` as "
                f"{len(elements) if elements is not None else 'all'} "
                "elements will be processed"
            )
    WorkDirManager(**workdir)

    # Get datagrabber to use
    datagrabber_object = _get_datagrabber(datagrabber.copy())

    # Get markers to use
    built_markers = [_get_marker(marker) for marker in markers.copy()]

    # Get storage engine to use
    if "single_output" not in storage:
        storage["single_output"] = False
    storage_object = _get_storage(storage.copy())

    # Get preprocessor to use (if provided)
    if preprocessors is not None:
        built_preprocessors = [
            _get_preprocessor(preprocessor)
            for preprocessor in preprocessors.copy()
        ]
    else:
        built_preprocessors = None

    # Create new marker collection
    mc = MarkerCollection(
        markers=built_markers,
        preprocessors=built_preprocessors,
        storage=storage_object,
    )
    # Validate the marker collection for the datagrabber
    mc.validate(datagrabber_object)

    # Fit elements
    with datagrabber_object:
        if elements is not None:
            # Keep track of valid selectors
            valid_elements = []
            for t_element in datagrabber_object.filter(elements):
                valid_elements.append(t_element)
                mc.fit(datagrabber_object[t_element])
            # Compute invalid selectors
            invalid_elements = set(elements) - set(valid_elements)
            # Report if invalid selectors are found
            if invalid_elements:
                raise_error(
                    msg=(
                        "The following element selectors are invalid:\n"
                        f"{invalid_elements}"
                    ),
                    klass=RuntimeError,
                )
        else:
            for t_element in datagrabber_object:
                mc.fit(datagrabber_object[t_element])


def collect(storage: dict) -> None:
    """Collect and store data.

    Parameters
    ----------
    storage : dict
        Storage to use. Must have a key ``kind`` with the kind of
        storage to use. All other keys are passed to the storage
        constructor.

    """
    logger.info(f"Collecting data using {storage['kind']}")
    logger.debug(f"\tStorage params: {storage}")
    if "single_output" not in storage:
        storage["single_output"] = False
    storage_object = _get_storage(storage.copy())
    logger.debug("Running storage.collect()")
    storage_object.collect()
    logger.info("Collect done")


def queue(
    config: dict,
    kind: str,
    jobname: str = "junifer_job",
    overwrite: bool = False,
    elements: Optional[Elements] = None,
    **kwargs: Union[str, int, bool, dict, tuple, list],
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
    elements : list or None, optional
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

    # Check workdir config
    if "workdir" in config:
        if isinstance(config["workdir"], dict):
            if not config["workdir"]["cleanup"]:
                warn_with_log(
                    "`workdir.cleanup` will be set to True when queueing"
                )
            # Set cleanup
            config["workdir"]["cleanup"] = True

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
        elements: Elements = [elements]

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


def reset(config: dict) -> None:
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
    datagrabber: dict,
    elements: Optional[Elements] = None,
) -> str:
    """List elements of the datagrabber filtered using `elements`.

    Parameters
    ----------
    datagrabber : dict
        DataGrabber to index. Must have a key ``kind`` with the kind of
        DataGrabber to use. All other keys are passed to the DataGrabber
        constructor.
    elements : list or None, optional
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
