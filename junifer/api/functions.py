# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from pathlib import Path
import shutil
import yaml
import subprocess

from .registry import build
from ..utils import logger, raise_error
from ..utils.fs import make_executable
from ..datagrabber.base import BaseDataGrabber
from ..markers.base import BaseMarker
from ..storage.base import BaseFeatureStorage
from ..markers.collection import MarkerCollection


def _get_datagrabber(datagrabber_config):
    datagrabber_params = datagrabber_config.copy()
    datagrabber_kind = datagrabber_params.pop('kind')
    datagrabber = build(
        'datagrabber', datagrabber_kind, BaseDataGrabber,
        init_params=datagrabber_params)
    return datagrabber


def run(
        workdir, datagrabber,  markers, storage, elements=None):
    """Run the pipeline on the selected element

    Parameters
    ----------
    workdir : str or path-like object
        Directory where the pipeline will be executed
    datagrabber : dict
        Datagrabber to use. Must have a key 'kind' with the kind of
        datagrabber to use. All other keys are passed to the datagrabber
        init function.
    elements : str, tuple or list[str or tuple]
        Element(s) to process. Will be used to index the datagrabber.
    markers : list of dict
        List of markers to extract. Each marker is a dict with at least two
        keys: 'name' and 'kind'. The 'name' key is used to name the output
        marker. The 'kind' key is used to specify the kind of marker to
        extract. The rest of the keys are used to pass parameters to the
        marker calculation.
    storage : dict
        Storage to use. Must have a key 'kind' with the kind of
        storage to use. All other keys are passed to the storage
        init function.
    """
    storage_params = storage.copy()
    storage_kind = storage_params.pop('kind')

    if isinstance(workdir, str):
        workdir = Path(workdir)

    datagrabber = _get_datagrabber(datagrabber)
    # Copy to avoid changing the original dict
    _markers = [x.copy() for x in markers]
    built_markers = []
    for t_marker in _markers:
        kind = t_marker.pop('kind')
        t_m = build('marker', kind, BaseMarker, init_params=t_marker)
        built_markers.append(t_m)

    storage = build(
        'storage', storage_kind, BaseFeatureStorage,
        init_params=storage_params)

    mc = MarkerCollection(built_markers, storage=storage)

    with datagrabber:
        if elements is not None:
            for t_element in elements:
                mc.fit(datagrabber[t_element])
        else:
            for t_element in datagrabber:
                mc.fit(datagrabber[t_element])


def collect(storage):
    storage_params = storage.copy()
    storage_kind = storage_params.pop('kind')
    logger.info(f'Collecting data using {storage_kind}')
    logger.debug(f'\tStorage params: {storage_params}')
    storage = build(
        'storage', storage_kind, BaseFeatureStorage,
        init_params=storage_params)
    logger.debug('Running storage.collect()')
    storage.collect()
    logger.info('Collect done')


def queue(config, kind, jobname='junifer_job', overwrite=False, elements=None,
          **kwargs):
    """Queue a job to be executed later

    Parameters
    ----------
    kind : str
        The kind of job to queue.
    **kwargs : dict
        The parameters to pass to the job.
    """
    # Create a folder within the CWD to store the job files / config
    cwd = Path.cwd()
    job_dir = cwd / 'junifer_jobs' / jobname
    logger.info(f'Creating job in {job_dir.as_posix()}')
    if job_dir.exists():
        if overwrite is not True:
            raise_error(f'Job folder for {jobname} already exists. '
                        'This error is raise to prevent overwriting files '
                        'of jobs that might be scheduled but yet not '
                        'executed. Either delete the directory '
                        f'{job_dir.as_posix()} or set overwrite to True.')
    job_dir.mkdir(exist_ok=True, parents=True)

    yaml_config = job_dir / 'config.yaml'
    logger.info(f'Writing YAML config to {yaml_config}')
    with open(yaml_config, 'w') as f:
        f.write(yaml.dump(config))

    # Get list of elements
    if elements is None:
        if 'elements' in config:
            elements = config['elements']
        else:
            # If no elements are specified, use all elements from the
            # datagrabber
            datagrabber = _get_datagrabber(config['datagrabber'])
            with datagrabber as dg:
                elements = dg.get_elements()
    if kind == 'HTCondor':
        _queue_condor(job_dir, yaml_config, elements, **kwargs)
    elif kind == 'SLURM':
        _queue_slurm(job_dir, yaml_config, elements, **kwargs)
    else:
        raise ValueError(f'Unknown queue kind: {kind}')

    logger.info('Queue done')


def _queue_condor(job_dir, yaml_config, elements, env, mem='8G', cpus=1,
                  disk='1G', extra_preamble='', verbose='info', collect=True,
                  submit=False):
    logger.debug('Creating HTCondor job')
    run_junifer_args = (f'run {yaml_config.as_posix()} '
                        f'--verbose {verbose} --element $(element)')
    collect_junifer_args = \
        f'collect {yaml_config.as_posix()} --verbose {verbose} '

    # Set up the env_name, executable and arguments according to the
    # environment type
    if env is None:
        env = {'kind': 'local'}
    if env['kind'] == 'conda':
        env_name = env['name']
        executable = 'run_conda.sh'
        arguments = f'{env_name} junifer'
        # TODO: Copy run_conda.sh to job_dir
        exec_path = job_dir / executable
        shutil.copy(Path(__file__).parent / 'res' / executable, exec_path)
        make_executable(exec_path)
    elif env['kind'] == 'venv':
        env_name = env['name']
        executable = 'run_venv.sh'
        arguments =  f'{env_name} junifer'
        # TODO: Copy run_venv.sh to job_dir
    elif env['kind'] == 'local':
        executable = 'junifer'
        arguments = ''
    else:
        raise ValueError(f'Unknown env kind: {env["kind"]}')
    log_dir = job_dir / 'logs'
    log_dir.mkdir(exist_ok=True, parents=True)
    run_preamble = f"""
        # The environment
        universe = vanilla
        getenv = True

        # Resources
        request_cpus = {cpus}
        request_memory = {mem}
        request_disk = {disk}

        # Executable
        initial_dir = {job_dir.as_posix()}
        executable = $(initial_dir)/{executable}
        transfer_executable = False

        arguments = {arguments} {run_junifer_args}

        {extra_preamble}

        # Logs
        log = {log_dir.as_posix()}/junifer_run_$(element).log
        output = {log_dir.as_posix()}/junifer_run_$(element).out
        error = {log_dir.as_posix()}/junifer_run_$(element).err
        """

    submit_run_fname = job_dir / 'run.submit'
    submit_collect_fname = job_dir / 'collect.submit'
    dag_fname = job_dir / 'condor.dag'

    # Write to run submit files
    with open(submit_run_fname, 'w') as submit_file:
        submit_file.write(run_preamble)
        submit_file.write('queue\n')

    collect_preamble = f"""
        # The environment
        universe = vanilla
        getenv = True

        # Resources
        request_cpus = {cpus}
        request_memory = {mem}
        request_disk = {disk}

        # Executable
        initial_dir = {job_dir.as_posix()}
        executable = $(initial_dir)/{executable}
        transfer_executable = False

        arguments = {arguments} {collect_junifer_args}

        {extra_preamble}

        # Logs
        log = {log_dir.as_posix()}/junifer_collect.log
        output = {log_dir.as_posix()}/junifer_collect.out
        error = {log_dir.as_posix()}/junifer_collect.err
        """

    # Now create the collect submit file
    with open(submit_collect_fname, 'w') as submit_file:
        submit_file.write(collect_preamble)  # Eval preamble here
        submit_file.write('queue\n')

    with open(dag_fname, 'w') as dag_file:
        # Get all subject and session names from file list
        for i_job, t_elem in enumerate(elements):
            dag_file.write(f'JOB run{i_job} {submit_run_fname}\n')
            dag_file.write(f'VARS run{i_job} element={t_elem}\n\n')
        if collect is True:
            dag_file.write(f'JOB collect {submit_collect_fname}\n')
            dag_file.write('PARENT ')
            for i_job, t_elem in enumerate(elements):
                dag_file.write(f'run{i_job} ')
            dag_file.write(f'CHILD collect\n\n')

    if submit is True:
        logger.info('Submitting HTCondor job')
        subprocess.run(['condor_submit_dag', dag_fname])
        logger.info('HTCondor job submitted')


def _queue_slurm(job_dir, yaml_config, elements):
    pass
