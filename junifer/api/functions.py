"""Provide API functions."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import atexit
import copy
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
from ..datagrabber import BaseDataGrabber, DataType
from ..markers import BaseMarker
from ..pipeline import (
    MarkerCollection,
    PipelineComponentRegistry,
    WorkDirManager,
)
from ..preprocess import BasePreprocessor
from ..storage import BaseFeatureStorage
from ..storage.utils import get_dependency_version
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


def _get_workdir_params(workdir: str | Path | dict | None) -> dict:
    """Get the parameters of the working directory manager.

    Parameters
    ----------
    workdir : str or pathlib.Path or dict or None
        The working directory as a path, or as a dictionary with the keys
        ``path`` and ``cleanup`` (default True). If None, the default of
        :class:`.WorkDirManager` is used.

    Returns
    -------
    dict
        The parameters for :class:`.WorkDirManager`.

    """
    if isinstance(workdir, dict):
        return {
            "workdir": Path(workdir["path"]),
            "cleanup": workdir.get("cleanup", True),
        }
    if workdir is None:
        return {"workdir": None, "cleanup": True}
    return {"workdir": Path(workdir), "cleanup": True}


def _setup_workdir(workdir: str | Path | dict | None) -> None:
    """Set up the working directory manager.

    Parameters
    ----------
    workdir : str or pathlib.Path or dict or None
        The working directory (see :func:`_get_workdir_params`).

    """
    WorkDirManager(**_get_workdir_params(workdir))
    atexit.register(WorkDirManager()._cleanup)


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
    # Initiate working directory manager with correct variation
    if not _get_workdir_params(workdir)["cleanup"]:
        if elements is None or len(elements) > 1:
            raise_error(
                "Cannot disable `workdir.cleanup` as "
                f"{len(elements) if elements is not None else 'all'} "
                "elements will be processed"
            )
    _setup_workdir(workdir)

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
            # Only get the elements of the dataset for partial selectors
            to_fit = datagrabber_object.select_elements(elements)
        else:
            to_fit = datagrabber_object.get_elements()
        for t_element in to_fit:
            mc.fit(datagrabber_object[t_element])


def collect(storage: dict, workdir: str | Path | dict | None = None) -> None:
    """Collect and store data.

    Parameters
    ----------
    storage : dict
        Storage to use. Must have a key ``kind`` with the kind of
        storage to use. All other keys are passed to the storage
        constructor.
    workdir : str or pathlib.Path or dict or None, optional
        The working directory, as in :func:`.run`. If None, the default of
        :class:`.WorkDirManager` is used (default None).

    """
    _setup_workdir(workdir)
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
    _setup_workdir(config.get("workdir"))
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
    _setup_workdir(config.get("workdir"))
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
    workdir: str | Path | dict | None = None,
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
    workdir : str or pathlib.Path or dict or None, optional
        Directory where the DataGrabber will be used, as in :func:`.run`.
        If None, the default of :class:`.WorkDirManager` is used
        (default None).

    """
    _setup_workdir(workdir)
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

    # Compute the absolute path of the data directory of the datagrabber (and
    # of the datagrabbers of a MultipleDataGrabber) if it is relative; same
    # motivation as above. Otherwise, it would be relative to the current
    # working directory, which is the job directory when queueing.
    if "datagrabber" in contents:
        datagrabbers = [
            contents["datagrabber"],
            *contents["datagrabber"].get("datagrabbers", []),
        ]
        for datagrabber in datagrabbers:
            if "datadir" in datagrabber:
                datadir = Path(datagrabber["datadir"])
                if not datadir.is_absolute():
                    datagrabber["datadir"] = str(
                        (filepath.parent / datadir).resolve()
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


# The fields of the datagrabbers with the state of the datalad dataset, which
# cannot be set
_DATALAD_STATE_FIELDS = ("datalad_dirty", "datalad_commit_id", "datalad_id")


# The names of the components of each step, for the comments
_COMPONENT_NAMES = {
    "datagrabber": "DataGrabber",
    "preprocessing": "preprocessor",
    "marker": "marker",
}


def _component_config(
    meta: dict, step: str, issues: list[str]
) -> tuple[dict, list[str]]:
    """Get the configuration of a pipeline component from its metadata.

    The parameters are the ones set when creating the component. If the
    component is available, it is created with them to check that they are
    still valid (e.g., not changed by changes in its API); if not, all its
    parameters are used.

    Parameters
    ----------
    meta : dict
        The metadata of the component.
    step : str
        The step of the component in the pipeline component registry.
    issues : list of str
        The issues found, to which the new ones are added.

    Returns
    -------
    dict
        The configuration of the component, with ``kind`` and its parameters.
    list of str
        The modules to load with ``with`` to use the component (and its
        nested components, if any).

    """
    kind = meta["class"]
    component = _COMPONENT_NAMES[step]
    registry = PipelineComponentRegistry()
    builtin = registry.is_builtin(step=step, name=kind)
    # All the parameters, except the state of the datalad dataset
    stored = {
        k: v
        for k, v in meta.items()
        if k not in ("class", "_fields_set", "_with", *_DATALAD_STATE_FIELDS)
    }
    with_ = []
    if meta.get("_with") is not None:
        with_.append(meta["_with"])
    elif not builtin:
        issues.append(
            f"`{kind}` is not a built-in component and the module to load it "
            "is unknown: add it to `with`."
        )
    # Nested components (e.g., the datagrabbers of a MultipleDataGrabber)
    for key, value in stored.items():
        if (
            isinstance(value, list)
            and len(value) > 0
            and all(isinstance(v, dict) and "class" in v for v in value)
        ):
            stored[key] = []
            for t_meta in value:
                t_config, t_with = _component_config(t_meta, step, issues)
                stored[key].append(t_config)
                with_.extend(t_with)
    # Only the parameters set when creating the component
    params = {k: stored[k] for k in meta["_fields_set"] if k in stored}
    # Check the parameters with the component, if available
    if kind in registry.step_components(step):
        try:
            registry.build_component_instance(
                step=step,
                name=kind,
                baseclass=object,
                init_params=copy.deepcopy(params),
            )
        except Exception as e:  # noqa: BLE001
            params = stored
            # The error, without the links to the documentation
            error = " ".join(
                line.strip()
                for line in str(e).splitlines()
                if line.strip()
                and not line.strip().startswith("For further information")
            )
            issues.append(
                f"`{kind}` failed to instantiate with junifer "
                f"{get_dependency_version('junifer')} "
                f"({error}) and thus could not be properly regenerated: all "
                "its parameters are in the YAML. Some of these entries might "
                "be redundant, not needed or changed (e.g., by changes in its "
                "API): please check the documentation/implementation of this "
                f"specific {component}."
            )
    return {"kind": kind, **params}, with_


def _marker_name(meta: dict, issues: list[str]) -> str:
    """Get the name of the marker of a feature.

    The name of the marker in the metadata is followed by the name of the
    feature (e.g., ``mean_aggregation`` for the ``aggregation`` feature of
    the ``mean`` marker), which is added again when computing it.

    Parameters
    ----------
    meta : dict
        The metadata of the feature.
    issues : list of str
        The issues found, to which the new ones are added.

    Returns
    -------
    str
        The name of the marker.

    """
    name = meta["marker"]["name"]
    kind = meta["marker"]["class"]
    try:
        klass = PipelineComponentRegistry().get_class(step="marker", name=kind)
        features = klass._MARKER_INOUT_MAPPINGS[DataType(meta["type"])]
    except (ValueError, KeyError, AttributeError):
        issues.append(
            f"The name of the `{kind}` marker could not be checked: remove "
            f"the name of the feature from `{name}`."
        )
        return name
    # The longest feature name, in case one is the end of another
    for feature in sorted(features, key=len, reverse=True):
        if name.endswith(f"_{feature}"):
            return name[: -len(feature) - 1]
    return name


def _check_generate_yaml_meta(meta: dict) -> None:
    """Check the YAML can be generated from the metadata of a feature.

    Parameters
    ----------
    meta : dict
        The metadata of the feature.

    Raises
    ------
    ValueError
        If the metadata of a component does not have the parameters set to
        create it, as stored by ``junifer`` > 0.0.8.

    """
    components = [
        meta.get("datagrabber"),
        *meta.get("preprocess", []),
        meta.get("marker"),
    ]
    if not all(isinstance(x, dict) and "_fields_set" in x for x in components):
        version = meta.get("dependencies", {}).get("junifer", "unknown")
        raise_error(
            f"The YAML of the feature {meta.get('name', '')} cannot be "
            f"generated: it was computed with junifer {version}, which does "
            "not store the parameters set to create the components (only "
            "junifer > 0.0.8 does)."
        )


def generate_yaml(
    meta: dict, storage_kind: str = "HDF5FeatureStorage"
) -> "CommentedMap":
    """Generate the YAML to compute a feature from its metadata.

    The YAML has the datagrabber, preprocessors and marker that computed the
    feature, with the parameters set to create them and the modules to load
    them with ``with``. Computing the feature with this YAML gives the same
    feature (with the same MD5), as long as the data and the versions of the
    dependencies are the same.

    The working directory and the URI of the storage are not part of the
    metadata, so they must be set in the YAML. The notes and issues found
    are written as comments at the start of the YAML.

    The parameters set to create the components and the modules to load them
    are only in the metadata of the features computed with ``junifer`` >
    0.0.8, so the YAML cannot be generated for the features computed with
    previous versions.

    Parameters
    ----------
    meta : dict
        The metadata of the feature, e.g., from
        :meth:`.BaseFeatureStorage.list_features`.
    storage_kind : str, optional
        The kind of storage for the YAML (default "HDF5FeatureStorage").

    Returns
    -------
    dict
        The YAML (a ``ruamel.yaml`` ``CommentedMap``, with the comments),
        which can be saved with ``junifer.utils.yaml.dump``.

    Raises
    ------
    ValueError
        If the feature was computed with a version of ``junifer`` that did not
        store the parameters set to create the components (``junifer`` <=
        0.0.8).

    """
    _check_generate_yaml_meta(meta)
    issues: list[str] = []
    datagrabber, with_ = _component_config(
        meta["datagrabber"], "datagrabber", issues
    )
    preprocess = []
    for t_meta in meta.get("preprocess", []):
        t_config, t_with = _component_config(t_meta, "preprocessing", issues)
        preprocess.append(t_config)
        with_.extend(t_with)
    marker, t_with = _component_config(meta["marker"], "marker", issues)
    with_.extend(t_with)
    name = _marker_name(meta, issues)
    if "name" in marker:
        marker["name"] = name
    elif name != meta["marker"]["class"]:
        # The name was not set, but it is not the default one
        marker["name"] = name

    config: dict[str, Any] = {"workdir": ""}
    if with_:
        config["with"] = list(dict.fromkeys(with_))
    config["datagrabber"] = datagrabber
    if preprocess:
        config["preprocess"] = preprocess
    config["markers"] = [marker]
    config["storage"] = {"kind": storage_kind, "uri": ""}
    # Format it as YAML
    stream = io.StringIO()
    yaml.dump(config, stream=stream)
    stream.seek(0)
    out = yaml.load(stream)

    # Comments, with the version of junifer as in the metadata
    junifer_version = get_dependency_version("junifer")
    now = dt.datetime.now(tz=dt.UTC).strftime("%Y-%m-%d %H:%M:%S")
    comment = (
        f"Auto-generated by junifer {junifer_version} on {now} UTC from the "
        f"metadata of the feature {meta.get('name', '')}\n"
    )
    dependencies = meta.get("dependencies", {})
    if not isinstance(dependencies, dict):
        dependencies = {}
    if dependencies:
        comment += "\nComputed with:\n" + "".join(
            f"  {k}=={v}\n" for k, v in sorted(dependencies.items())
        )
    comment += (
        "\nTo set:\n"
        "  - workdir: the working directory\n"
        "  - storage.uri: the file to store the features\n"
    )
    if "datadir" in datagrabber:
        comment += (
            "  - datagrabber.datadir: the directory of the data, if it is not "
            "the same\n"
        )
    notes = []
    computed_with = dependencies.get("junifer")
    if computed_with is not None and computed_with != junifer_version:
        notes.append(
            f"The feature was computed with junifer {computed_with}: check "
            "the components for possible changes in their API."
        )
    datalad_id = meta["datagrabber"].get("datalad_id")
    if datalad_id is not None:
        notes.append(
            f"DataLad dataset {datalad_id} at commit "
            f"{meta['datagrabber'].get('datalad_commit_id')}."
        )
        if meta["datagrabber"].get("datalad_dirty"):
            issues.append(
                "The DataLad dataset was dirty: while this YAML reproduces "
                "the computation, there is no guarantee that the same "
                "results will be obtained, as there is no strict data "
                "provenance."
            )
    if notes:
        comment += "\nNotes:\n" + "".join(f"  - {x}\n" for x in notes)
    if issues:
        comment += "\nIssues:\n" + "".join(f"  - {x}\n" for x in issues)
    out.yaml_set_start_comment(comment)
    # Add an empty line between the sections
    for key in list(out.keys())[1:]:
        out.yaml_set_comment_before_after_key(key, before="\n")
    return out
