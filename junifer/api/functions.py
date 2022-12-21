"""Provide functions for cli."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import shutil
import subprocess
import textwrap
import typing
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import yaml

from ..datagrabber.base import BaseDataGrabber
from ..markers.base import BaseMarker
from ..markers.collection import MarkerCollection
from ..pipeline.registry import build
from ..preprocess.base import BasePreprocessor
from ..storage.base import BaseFeatureStorage
from ..utils import logger, raise_error
from ..utils.fs import make_executable


def _get_datagrabber(datagrabber_config: Dict) -> BaseDataGrabber:
    """Get datagrabber.

    Parameters
    ----------
    datagrabber_config : dict
        The config to get the datagrabber using.

    Returns
    -------
    dict
        The datagrabber.

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
    preprocessor: Optional[Dict] = None,
    elements: Union[str, List[Union[str, Tuple]], Tuple, None] = None,
) -> None:
    """Run the pipeline on the selected element.

    Parameters
    ----------
    workdir : str or pathlib.Path
        Directory where the pipeline will be executed.
    datagrabber : dict
        Datagrabber to use. Must have a key ``kind`` with the kind of
        datagrabber to use. All other keys are passed to the datagrabber
        init function.
    markers : list of dict
        List of markers to extract. Each marker is a dict with at least two
        keys: ``name`` and ``kind``. The ``name`` key is used to name the
        output marker. The ``kind`` key is used to specify the kind of marker
        to extract. The rest of the keys are used to pass parameters to the
        marker calculation.
    storage : dict
        Storage to use. Must have a key ``kind`` with the kind of
        storage to use. All other keys are passed to the storage
        init function.
    preprocessor : dict, optional
        Preprocessor to use. Must have a key ``kind`` with the kind of
        preprocessor to use. All other keys are passed to the preprocessor
        init function (default None).
    elements : str or tuple or list of str or tuple, optional
        Element(s) to process. Will be used to index the datagrabber
        (default None).

    """
    # Convert str to Path
    if isinstance(workdir, str):
        workdir = Path(workdir)

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
    if preprocessor is not None:
        preprocessor_object = _get_preprocessor(preprocessor)
    else:
        preprocessor_object = None

    # Create new marker collection
    mc = MarkerCollection(
        markers=built_markers,
        preprocessing=preprocessor_object,
        storage=storage_object,
    )
    # Fit elements
    with datagrabber_object:
        if elements is not None:
            for t_element in elements:
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
        init function.

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
    kind : {"HTCondor", "SLURM"}
        The kind of job queue system to use.
    jobname : str, optional
        The name of the job (default "junifer_job").
    overwrite : bool, optional
        Whether to overwrite if job directory already exists (default False).
    elements : str or tuple or list of str or tuple, optional
        Element(s) to process. Will be used to index the datagrabber
        (default None).
    **kwargs : dict
        The keyword arguments to pass to the job queue system.

    Raises
    ------
    ValueError
        If the value of ``kind`` is invalid.

    """
    # Create a folder within the CWD to store the job files / config
    cwd = Path.cwd()
    jobdir = cwd / "junifer_jobs" / jobname
    logger.info(f"Creating job in {str(jobdir.absolute())}")
    if jobdir.exists():
        if not overwrite:
            raise_error(
                f"Job folder for {jobname} already exists. "
                "This error is raised to prevent overwriting job files "
                "that might be scheduled but not yet executed. "
                f"Either delete the directory {str(jobdir.absolute())} "
                "or set overwrite=True."
            )
        else:
            logger.info(
                f"Deleting existing job directory at {str(jobdir.absolute())}"
            )
            shutil.rmtree(jobdir)
    jobdir.mkdir(exist_ok=True, parents=True)

    if "with" in config:
        to_load = config["with"]
        # If there is a list of files to load, copy and remove the path
        # component
        fixed_load = []
        if not isinstance(to_load, list):
            to_load = [to_load]
        for item in to_load:
            if item.endswith(".py"):
                logger.debug(f"Copying {item} to jobdir ({jobdir.absolute()})")
                shutil.copy(item, jobdir)
                fixed_load.append(Path(item).name)
            else:
                fixed_load.append(item)
        config["with"] = fixed_load

    yaml_config = jobdir / "config.yaml"
    logger.info(f"Writing YAML config to {str(yaml_config.absolute())}")
    with open(yaml_config, "w") as f:
        f.write(yaml.dump(config))

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

    # TODO: Fix typing of elements
    if not isinstance(elements, list):
        elements = [elements]  # type: ignore

    typing.cast(List[Union[str, Tuple]], elements)

    if kind == "HTCondor":
        _queue_condor(
            jobname=jobname,
            jobdir=jobdir,
            yaml_config=yaml_config,
            elements=elements,  # type: ignore
            config=config,
            **kwargs,
        )
    elif kind == "SLURM":
        _queue_slurm(
            jobname=jobname,
            jobdir=jobdir,
            yaml_config=yaml_config,
            elements=elements,  # type: ignore
            config=config,
            **kwargs,
        )
    else:
        raise_error(f"Unknown queue kind: {kind}")

    logger.info("Queue done")


def _queue_condor(
    jobname: str,
    jobdir: Path,
    yaml_config: Path,
    elements: List[Union[str, Tuple]],
    config: Dict,
    env: Optional[Dict[str, str]] = None,
    mem: str = "8G",
    cpus: int = 1,
    disk: str = "1G",
    extra_preamble: str = "",
    verbose: str = "info",
    collect: bool = True,
    submit: bool = False,
) -> None:
    """Submit job to HTCondor.

    Parameters
    ----------
    jobname : str
        The name of the job.
    jobdir : pathlib.Path
        The path to the job directory.
    yaml_config : pathlib.Path
        The path to the YAML config file.
    elements : list of str or tuple
        Element(s) to process. Will be used to index the datagrabber.
    config : dict
        The configuration to be used for queueing the job.
    env : dict, optional
        The environment variables passed as dictionary (default None).
    mem : str, optional
        The size of memory (RAM) to use (default "8G").
    cpus : int, optional
        The number of CPU cores to use (default 1).
    disk : str, optional
        The size of disk (HDD or SSD) to use (default "1G").
    extra_preamble : str, optional
        Extra commands to pass to HTCondor (default "").
    verbose : str, optional
        The level of verbosity (default "info").
    collect : bool, optional
        Whether to submit "collect" task for junifer (default True).
    submit : bool, optional
        Whether to submit the jobs. In any case, .dag files will be created
        for submission (default False).

    Raises
    ------
    ValueError
        If the value of `env` is invalid.

    """
    logger.debug("Creating HTCondor job")
    run_junifer_args = (
        f"run {str(yaml_config.absolute())} "
        f"--verbose {verbose} --element $(element)"
    )
    collect_junifer_args = (
        f"collect {str(yaml_config.absolute())} --verbose {verbose} "
    )

    # Set up the env_name, executable and arguments according to the
    # environment type
    if env is None:
        env = {"kind": "local"}
    if env["kind"] == "conda":
        env_name = env["name"]
        executable = "run_conda.sh"
        arguments = f"{env_name} junifer"
        exec_path = jobdir / executable
        logger.info(f"Copying {executable} to {str(exec_path.absolute())}")
        shutil.copy(Path(__file__).parent / "res" / executable, exec_path)
        make_executable(exec_path)
    elif env["kind"] == "venv":
        env_name = env["name"]
        executable = "run_venv.sh"
        arguments = f"{env_name} junifer"
        # TODO: Copy run_venv.sh to jobdir
    elif env["kind"] == "local":
        executable = "junifer"
        arguments = ""
    else:
        raise ValueError(f'Unknown env kind: {env["kind"]}')

    # Create log directory
    log_dir = jobdir / "logs"
    log_dir.mkdir(exist_ok=True, parents=True)

    # Add preamble data
    run_preamble = f"""
        # The environment
        universe = vanilla
        getenv = True

        # Resources
        request_cpus = {cpus}
        request_memory = {mem}
        request_disk = {disk}

        # Executable
        initial_dir = {str(jobdir.absolute())}
        executable = $(initial_dir)/{executable}
        transfer_executable = False

        arguments = {arguments} {run_junifer_args}

        {extra_preamble}

        # Logs
        log = {str(log_dir.absolute())}/junifer_run_$(log_element).log
        output = {str(log_dir.absolute())}/junifer_run_$(log_element).out
        error = {str(log_dir.absolute())}/junifer_run_$(log_element).err
        """

    submit_run_fname = jobdir / f"run_{jobname}.submit"
    submit_collect_fname = jobdir / f"collect_{jobname}.submit"
    dag_fname = jobdir / f"{jobname}.dag"

    # Write to run submit files
    with open(submit_run_fname, "w") as submit_file:
        submit_file.write(textwrap.dedent(run_preamble))
        submit_file.write("queue\n")

    collect_preamble = f"""
        # The environment
        universe = vanilla
        getenv = True

        # Resources
        request_cpus = {cpus}
        request_memory = {mem}
        request_disk = {disk}

        # Executable
        initial_dir = {str(jobdir.absolute())}
        executable = $(initial_dir)/{executable}
        transfer_executable = False

        arguments = {arguments} {collect_junifer_args}

        {extra_preamble}

        # Logs
        log = {str(log_dir.absolute())}/junifer_collect.log
        output = {str(log_dir.absolute())}/junifer_collect.out
        error = {str(log_dir.absolute())}/junifer_collect.err
        """

    # Now create the collect submit file
    with open(submit_collect_fname, "w") as submit_file:
        submit_file.write(textwrap.dedent(collect_preamble))
        submit_file.write("queue\n")

    with open(dag_fname, "w") as dag_file:
        # Get all subject and session names from file list
        for i_job, t_elem in enumerate(elements):
            str_elem = (
                ",".join(t_elem) if isinstance(t_elem, tuple) else t_elem
            )
            log_elem = (
                "_".join(t_elem) if isinstance(t_elem, tuple) else t_elem
            )
            dag_file.write(f"JOB run{i_job} {submit_run_fname}\n")
            dag_file.write(
                f'VARS run{i_job} element="{str_elem}" '
                f'log_element="{log_elem}"\n\n'
            )
        if collect is True:
            dag_file.write(f"JOB collect {submit_collect_fname}\n")
            dag_file.write("PARENT ")
            for i_job, _t_elem in enumerate(elements):
                dag_file.write(f"run{i_job} ")
            dag_file.write("CHILD collect\n\n")

    # Submit job(s)
    if submit is True:
        logger.info("Submitting HTCondor job")
        subprocess.run(["condor_submit_dag", dag_fname])
        logger.info("HTCondor job submitted")
    else:
        cmd = f"condor_submit_dag {str(dag_fname.absolute())}"
        logger.info(
            f"HTCondor job files created, to submit the job, run `{cmd}`"
        )


def _queue_slurm(
    jobname: str,
    jobdir: Path,
    yaml_config: Path,
    elements: List[Union[str, Tuple]],
    config: Dict,
) -> None:
    """Submit job to SLURM.

    Parameters
    ----------
    jobname : str
        The name of the job.
    jobdir : pathlib.Path
        The path to the job directory.
    yaml_config : pathlib.Path
        The path to the YAML config file.
    elements : str or tuple or list[str or tuple], optional
        Element(s) to process. Will be used to index the datagrabber
        (default None).
    config : dict
        The configuration to be used for queueing the job.
    """
    pass
    # logger.debug("Creating SLURM job")
    # run_junifer_args = (
    #     f"run {str(yaml_config.absolute())} "
    #     f"--verbose {verbose} --element $(element)"
    # )
    # collect_junifer_args = \
    #     f"collect {str(yaml_config.absolute())} --verbose {verbose} "

    # # Set up the env_name, executable and arguments according to the
    # # environment type
    # if env is None:
    #     env = {
    #         "kind": "local",
    #     }
    # if env["kind"] == "conda":
    #     env_name = env["name"]
    #     executable = "run_conda.sh"
    #     arguments = f"{env_name} junifer"
    #     # TODO: Copy run_conda.sh to jobdir
    #     exec_path = jobdir / executable
    #     shutil.copy(Path(__file__).parent / "res" / executable, exec_path)
    #     make_executable(exec_path)
    # elif env["kind"] == "venv":
    #     env_name = env["name"]
    #     executable = "run_venv.sh"
    #     arguments = f"{env_name} junifer"
    #     # TODO: Copy run_venv.sh to jobdir
    # elif env["kind"] == "local":
    #     executable = "junifer"
    #     arguments = ""
    # else:
    #     raise ValueError(f"Unknown env kind: {env['kind']}")

    # # Create log directory
    # log_dir = jobdir / 'logs'
    # log_dir.mkdir(exist_ok=True, parents=True)

    # # Add preamble data
    # run_preamble = f"""
    #     #!/bin/bash

    #     #SBATCH --job-name={}
    #     #SBATCH --account={}
    #     #SBATCH --partition={}
    #     #SBATCH --time={}
    #     #SBATCH --ntasks={}
    #     #SBATCH --cpus-per-task={cpus}
    #     #SBATCH --mem-per-cpu={mem}
    #     #SBATCH --mail-type={}
    #     #SBATCH --mail-user={}
    #     #SBATCH --output={}
    #     #SBATCH --error={}

    #     # Executable
    #     initial_dir = {str(jobdir.absolute())}
    #     executable = $(initial_dir)/{executable}
    #     transfer_executable = False

    #     arguments = {arguments} {run_junifer_args}

    #     {extra_preamble}

    #     # Logs
    #     log = {str(log_dir.absolute())}/junifer_run_$(element).log
    #     output = {str(log_dir.absolute())}/junifer_run_$(element).out
    #     error = {str(log_dir.absolute())}/junifer_run_$(element).err
    #     """

    # submit_run_fname = jobdir / f'run_{jobname}.sh'
    # submit_collect_fname = jobdir / f'collect_{jobname}.sh'

    # # Write to run submit files
    # with open(submit_run_fname, 'w') as submit_file:
    #     submit_file.write(run_preamble)
    #     submit_file.write('queue\n')

    # collect_preamble = f"""
    #     # The environment
    #     universe = vanilla
    #     getenv = True

    #     # Resources
    #     request_cpus = {cpus}
    #     request_memory = {mem}
    #     request_disk = {disk}

    #     # Executable
    #     initial_dir = {str(jobdir.absolute())}
    #     executable = $(initial_dir)/{executable}
    #     transfer_executable = False

    #     arguments = {arguments} {collect_junifer_args}

    #     {extra_preamble}

    #     # Logs
    #     log = {str(log_dir.absolute())}/junifer_collect.log
    #     output = {str(log_dir.absolute())}/junifer_collect.out
    #     error = {str(log_dir.absolute())}/junifer_collect.err
    #     """

    # # Now create the collect submit file
    # with open(submit_collect_fname, 'w') as submit_file:
    #     submit_file.write(collect_preamble)  # Eval preamble here
    #     submit_file.write('queue\n')

    # with open(dag_fname, 'w') as dag_file:
    #     # Get all subject and session names from file list
    #     for i_job, t_elem in enumerate(elements):
    #         dag_file.write(f'JOB run{i_job} {submit_run_fname}\n')
    #         dag_file.write(f'VARS run{i_job} element="{t_elem}"\n\n')
    #     if collect is True:
    #         dag_file.write(f'JOB collect {submit_collect_fname}\n')
    #         dag_file.write('PARENT ')
    #         for i_job, _t_elem in enumerate(elements):
    #             dag_file.write(f'run{i_job} ')
    #         dag_file.write('CHILD collect\n\n')

    # # Submit job(s)
    # if submit is True:
    #     logger.info('Submitting SLURM job')
    #     subprocess.run(['condor_submit_dag', dag_fname])
    #     logger.info('HTCondor SLURM submitted')
    # else:
    #     cmd = f"condor_submit_dag {str(dag_fname.absolute())}"
    #     logger.info(
    #         f"SLURM job files created, to submit the job, run `{cmd}`"
    #     )
