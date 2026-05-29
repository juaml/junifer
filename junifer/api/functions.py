"""Provide API functions."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import atexit
import datetime as dt
import importlib
import importlib.util
import io
import os
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

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
from ..utils import raise_error, warn_with_log, yaml


if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap


__all__ = [
    "collect",
    "generate_yaml",
    "list_elements",
    "parse_yaml",
    "queue",
    "reset",
    "run",
]

_log = structlog.get_logger("junifer")
logger = _log.bind(pkg="api")


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
    workdir: str | Path | dict,
    datagrabber: dict,
    markers: list[dict],
    storage: dict,
    preprocessors: list[dict] | None = None,
    elements: Elements | None = None,
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
    if isinstance(workdir, str | Path):
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
    atexit.register(WorkDirManager()._cleanup)

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
    elements: Elements | None = None,
    **kwargs: str | int | bool | dict | tuple | list,
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
            f"Invalid value for `kind`: {kind}, must be one of {valid_kind}"
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
    elements: Elements | None = None,
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


def parse_yaml(filepath: str | Path) -> dict:  # noqa: C901
    """Parse YAML.

    Parameters
    ----------
    filepath : str or pathlib.Path
        The filepath to read from.

    Returns
    -------
    dict
        The contents represented as dictionary.

    """
    # Convert str to Path
    if not isinstance(filepath, Path):
        filepath = Path(filepath)

    logger.info(f"Parsing yaml file: {filepath.absolute()!s}")
    # Filepath existence check
    if not filepath.exists():
        raise_error(f"File does not exist: {filepath.absolute()!s}")
    # Filepath reading
    contents = yaml.load(filepath)
    if "elements" in contents:
        if contents["elements"] is None:
            raise_error(
                "The elements key was defined but its content is empty. "
                "Please define the elements to operate on or remove the key."
            )
    # load modules
    if "with" in contents:
        to_load = contents["with"]
        # Convert load modules to list
        if not isinstance(to_load, list):
            to_load = [to_load]
        # Initialize list to have absolute paths for custom modules
        final_to_load = []
        for t_module in to_load:
            if t_module.endswith(".py"):
                logger.debug(f"Importing file: {t_module}")
                # This resolves both absolute and relative paths
                file_path = filepath.parent / t_module
                if not file_path.exists():
                    raise_error(
                        f"File in 'with' section does not exist: {file_path}"
                    )
                # Add the parent directory to the sys.path so that the
                # any imports from this module work correctly
                t_path = str(file_path.parent)
                if t_path not in sys.path:
                    sys.path.append(str(file_path.parent))

                spec = importlib.util.spec_from_file_location(
                    t_module, file_path
                )
                module = importlib.util.module_from_spec(spec)  # type: ignore
                sys.modules[t_module] = module
                spec.loader.exec_module(module)  # type: ignore

                # Add absolute path to final list
                final_to_load.append(str(file_path.resolve()))

                # Check if the module has junifer_module_deps function
                if hasattr(module, "junifer_module_deps"):
                    logger.debug(
                        f"Module {t_module} has junifer_module_deps function"
                    )
                    # Get the dependencies
                    deps = module.junifer_module_deps()
                    # Add the dependencies to the final list
                    for dep in deps:
                        if dep not in final_to_load:
                            final_to_load.append(
                                str((file_path.parent / dep).resolve())
                            )
            else:
                logger.info(f"Importing module: {t_module}")
                importlib.import_module(t_module)
                # Add module to final list
                final_to_load.append(t_module)

        # Replace modules to be loaded so that custom modules will take the
        # absolute path. This was not the case as found in #224. Similar thing
        # is done with the storage URI below.
        contents["with"] = final_to_load

    # Compute path for the URI parameter in storage files that are relative
    # This is a tricky thing that appeared in #127. The problem is that
    # the path in the URI parameter is relative to YAML file, not to the
    # current working directory. If we leave it as is in the contents
    # dict, then it will be used later in the ``build`` function as is,
    # which will be computed relative to the current working directory.
    # The solution is to compute the absolute path and replace the
    # relative path in the contents dict with the absolute path.

    # Check if the storage file is defined
    if "storage" in contents:
        if "uri" in contents["storage"]:
            # Check if the storage file is relative
            uri_path = Path(contents["storage"]["uri"])
            if not uri_path.is_absolute():
                # Compute the absolute path
                contents["storage"]["uri"] = str(
                    (filepath.parent / uri_path).resolve()
                )

    # Allow relative path if queue env kind is venv; same motivation as above
    if "queue" in contents:
        if "env" in contents["queue"]:
            if "venv" == contents["queue"]["env"]["kind"]:
                # Check if the env name is relative
                venv_path = Path(contents["queue"]["env"]["name"])
                if not venv_path.is_absolute():
                    # Compute the absolute path
                    contents["queue"]["env"]["name"] = str(
                        (filepath.parent / venv_path).resolve()
                    )

    return contents


def generate_yaml(meta: dict) -> "CommentedMap":
    """Generate the feature YAML from metadata.

    Parameters
    ----------
    meta : dict
        Feature metadata as dictionary.

    Returns
    -------
    ruamel.yaml.comments.CommentedMap
        Feature YAML.

    """
    y: dict[str, Any] = {}
    y["workdir"] = ""
    # Add "with" section if present
    if "with" in meta:
        y["with"] = meta["with"].copy()
    # Set datagrabber
    meta_dg = meta["datagrabber"].copy()
    a = meta_dg.pop("class")
    dg = PipelineComponentRegistry().get_class(step="datagrabber", name=a)
    dg_model = dg.model_construct(**meta_dg)
    y["datagrabber"] = {
        "kind": a,
        **dg_model.model_dump(
            mode="json",
            exclude=dg_model._dump_exclude
            if hasattr(dg_model, "_dump_exclude")
            else {},
            exclude_defaults=True,
            exclude_none=True,
        ),
    }
    # Set preprocessor(s)
    if "preprocess" in meta:
        y["preprocess"] = []
        meta_p = meta["preprocess"].copy()
        if not isinstance(meta_p, list):
            meta_p = [meta_p]
        for mp in meta_p:
            b = mp.pop("class")
            p = PipelineComponentRegistry().get_class(
                step="preprocessing", name=b
            )
            p_model = p.model_construct(**mp)
            y["preprocess"].append(
                {
                    "kind": b,
                    **p_model.model_dump(
                        mode="json",
                        exclude={"required_data_types"},
                        exclude_defaults=True,
                        exclude_none=True,
                    ),
                }
            )
    # Set marker
    meta_m = meta["marker"].copy()
    c = meta_m.pop("class")
    m = PipelineComponentRegistry().get_class(step="marker", name=c)
    m_model = m.model_construct(**meta_m)
    y["markers"] = []
    y["markers"].append(
        {
            "kind": c,
            **m_model.model_dump(
                mode="json",
                exclude_defaults=True,
                exclude_none=True,
            ),
        }
    )
    # Set storage
    y["storage"] = {
        "kind": "HDF5FeatureStorage",
        "uri": "",
    }
    # Set queue
    if "queue" in meta:
        y["queue"] = meta["queue"].copy()
    else:
        y["queue"] = {
            "jobname": meta["name"],
            "kind": "",
        }
    # Dump and load yaml to format
    f = io.StringIO()
    yaml.dump(y, stream=f)
    f.seek(0)
    d = yaml.load(f)
    # Add preamble
    pre = (
        "Auto-generated by junifer on "
        f"{dt.datetime.now(tz=dt.UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
    )
    if "dependencies" in meta:
        for k, v in meta["dependencies"].items():
            pre += f"{k}=={v}\n"
    d.yaml_set_start_comment(pre)
    # Add newline between sections
    for s in d.keys():
        d.yaml_set_comment_before_after_key(s, before="\n")
    return d
