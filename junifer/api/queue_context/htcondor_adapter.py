"""Define concrete class for generating HTCondor assets."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import shutil
import textwrap
from pathlib import Path
from typing import Optional

from ...typing import Elements
from ...utils import logger, make_executable, raise_error, run_ext_cmd
from .queue_context_adapter import QueueContextAdapter


__all__ = ["HTCondorAdapter"]


class HTCondorAdapter(QueueContextAdapter):
    """Class for generating queueing scripts for HTCondor.

    Parameters
    ----------
    job_name : str
        The job name to be used by HTCondor.
    job_dir : pathlib.Path
        The path to the job directory.
    yaml_config_path : pathlib.Path
        The path to the YAML config file.
    elements : list of str or tuple
        Element(s) to process. Will be used to index the DataGrabber.
    pre_run : str or None, optional
        Extra bash commands to source before the run (default None).
    pre_collect : str or None, optional
        Extra bash commands to source before the collect (default None).
    env : dict, optional
        The Python environment configuration. If None, will run without a
        virtual environment of any kind (default None).
    verbose : str, optional
        The level of verbosity (default "info").
    verbose_datalad : str or None, optional
        The level of verbosity for datalad. If None, will be the same
        as ``verbose`` (default None).
    cpus : int, optional
        The number of CPU cores to use (default 1).
    mem : str, optional
        The size of memory (RAM) to use (default "8G").
    disk : str, optional
        The size of disk (HDD or SSD) to use (default "1G").
    extra_preamble : str or None, optional
        Extra commands to pass to HTCondor (default None).
    collect : {"yes", "on_success_only", "no"}, optional
        Whether to submit "collect" task for junifer (default "yes").
        Valid options are:

            * "yes": Submit "collect" task and run even if some of the jobs
                fail.
            * "on_success_only": Submit "collect" task and run only if all jobs
                succeed.
            * "no": Do not submit "collect" task.

    submit : bool, optional
        Whether to submit the jobs. In any case, .dag files will be created
        for submission (default False).

    Raises
    ------
    ValueError
        If ``collect`` is invalid or if ``env`` is invalid.

    See Also
    --------
    QueueContextAdapter :
        The base class for QueueContext.
    GnuParallelLocalAdapter :
        The concrete class for queueing via GNU Parallel (local).

    """

    def __init__(
        self,
        job_name: str,
        job_dir: Path,
        yaml_config_path: Path,
        elements: Elements,
        pre_run: Optional[str] = None,
        pre_collect: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
        verbose: str = "info",
        verbose_datalad: Optional[str] = None,
        cpus: int = 1,
        mem: str = "8G",
        disk: str = "1G",
        extra_preamble: Optional[str] = None,
        collect: str = "yes",
        submit: bool = False,
    ) -> None:
        """Initialize the class."""
        self._job_name = job_name
        self._job_dir = job_dir
        self._yaml_config_path = yaml_config_path
        self._elements = elements
        self._pre_run = pre_run
        self._pre_collect = pre_collect
        self._check_env(env)
        self._verbose = verbose
        self._verbose_datalad = verbose_datalad
        self._cpus = cpus
        self._mem = mem
        self._disk = disk
        self._extra_preamble = extra_preamble
        self._collect = self._check_collect(collect)
        self._submit = submit

        self._log_dir = self._job_dir / "logs"
        self._pre_run_path = self._job_dir / "pre_run.sh"
        self._pre_collect_path = self._job_dir / "pre_collect.sh"
        self._submit_run_path = self._job_dir / f"run_{self._job_name}.submit"
        self._submit_collect_path = (
            self._job_dir / f"collect_{self._job_name}.submit"
        )
        self._dag_path = self._job_dir / f"{self._job_name}.dag"

    def _check_env(self, env: Optional[dict[str, str]]) -> None:
        """Check value of env parameter on init.

        Parameters
        ----------
        env : dict or None
            The value of env parameter.

        Raises
        ------
        ValueError
            If ``env.kind`` is invalid or
            if ``env.shell`` is invalid.

        """
        # Set env related variables
        if env is None:
            env = {"kind": "local"}
        # Check env kind
        valid_env_kinds = ["conda", "venv", "local"]
        if env["kind"] not in valid_env_kinds:
            raise_error(
                f"Invalid value for `env.kind`: {env['kind']}, "
                f"must be one of {valid_env_kinds}"
            )
        else:
            # Check shell
            shell = env.get("shell", "bash")
            valid_shells = ["bash", "zsh"]
            if shell not in valid_shells:
                raise_error(
                    f"Invalid value for `env.shell`: {shell}, "
                    f"must be one of {valid_shells}"
                )
            self._shell = shell
            # Set variables
            if env["kind"] == "local":
                # No virtual environment
                self._executable = "junifer"
                self._arguments = ""
            else:
                self._executable = f"run_{env['kind']}.{self._shell}"
                self._arguments = f"{env['name']} junifer"
                self._exec_path = self._job_dir / self._executable

    def _check_collect(self, collect: str) -> str:
        """Check value of collect parameter on init.

        Parameters
        ----------
        collect : str
            The value of collect parameter.

        Returns
        -------
        str
            The checked value of collect parameter.

        Raises
        ------
        ValueError
            If ``collect`` is invalid.

        """
        valid_options = ["yes", "no", "on_success_only"]
        if collect not in valid_options:
            raise_error(
                f"Invalid value for `collect`: {collect}, "
                f"must be one of {valid_options}"
            )
        else:
            return collect

    def pre_run(self) -> str:
        """Return pre-run commands."""
        fixed = (
            f"#!/usr/bin/env {self._shell}\n\n"
            "# This script is auto-generated by junifer.\n\n"
            "# Force datalad to run in non-interactive mode\n"
            "DATALAD_UI_INTERACTIVE=false\n"
        )
        var = self._pre_run or ""
        return fixed + "\n" + var

    def run(self) -> str:
        """Return run commands."""
        verbose_args = f"--verbose {self._verbose} "
        if self._verbose_datalad is not None:
            verbose_args = (
                f"{verbose_args} --verbose-datalad {self._verbose_datalad} "
            )
        junifer_run_args = (
            "run "
            f"{self._yaml_config_path.resolve()!s} "
            f"{verbose_args}"
            "--element $(element)"
        )
        log_dir_prefix = (
            f"{self._log_dir.resolve()!s}/junifer_run_$(log_element)"
        )
        fixed = (
            "# This script is auto-generated by junifer.\n\n"
            "# Environment\n"
            "universe = vanilla\n"
            "getenv = True\n\n"
            "# Resources\n"
            f"request_cpus = {self._cpus}\n"
            f"request_memory = {self._mem}\n"
            f"request_disk = {self._disk}\n\n"
            "# Executable\n"
            f"initial_dir = {self._job_dir.resolve()!s}\n"
            f"executable = $(initial_dir)/{self._executable}\n"
            f"transfer_executable = False\n\n"
            f"arguments = {self._arguments} {junifer_run_args}\n\n"
            "# Logs\n"
            f"log = {log_dir_prefix}.log\n"
            f"output = {log_dir_prefix}.out\n"
            f"error = {log_dir_prefix}.err\n"
        )
        var = self._extra_preamble or ""
        return fixed + "\n" + var + "\n" + "queue"

    def pre_collect(self) -> str:
        """Return pre-collect commands."""
        fixed = (
            f"#!/usr/bin/env {self._shell}\n\n"
            "# This script is auto-generated by junifer.\n"
        )
        var = self._pre_collect or ""
        # Add commands if collect="yes"
        if self._collect == "yes":
            var += 'if [ "${1}" == "4" ]; then\n    exit 1\nfi\n'
        return fixed + "\n" + var

    def collect(self) -> str:
        """Return collect commands."""
        verbose_args = f"--verbose {self._verbose} "
        if self._verbose_datalad is not None:
            verbose_args = (
                f"{verbose_args} --verbose-datalad {self._verbose_datalad} "
            )

        junifer_collect_args = (
            "collect "
            f"{self._yaml_config_path.resolve()!s} "
            f"{verbose_args}"
        )
        log_dir_prefix = f"{self._log_dir.resolve()!s}/junifer_collect"
        fixed = (
            "# This script is auto-generated by junifer.\n\n"
            "# Environment\n"
            "universe = vanilla\n"
            "getenv = True\n\n"
            "# Resources\n"
            f"request_cpus = {self._cpus}\n"
            f"request_memory = {self._mem}\n"
            f"request_disk = {self._disk}\n\n"
            "# Executable\n"
            f"initial_dir = {self._job_dir.resolve()!s}\n"
            f"executable = $(initial_dir)/{self._executable}\n"
            "transfer_executable = False\n\n"
            f"arguments = {self._arguments} {junifer_collect_args}\n\n"
            "# Logs\n"
            f"log = {log_dir_prefix}.log\n"
            f"output = {log_dir_prefix}.out\n"
            f"error = {log_dir_prefix}.err\n"
        )
        var = self._extra_preamble or ""
        return fixed + "\n" + var + "\n" + "queue"

    def dag(self) -> str:
        """Return HTCondor DAG commands."""
        fixed = ""
        for idx, element in enumerate(self._elements):
            # Stringify elements if tuple for operation
            str_element = (
                ",".join(element) if isinstance(element, tuple) else element
            )
            # Stringify elements if tuple for logging
            log_element = (
                "-".join(element) if isinstance(element, tuple) else element
            )
            fixed += (
                f"JOB run{idx} {self._submit_run_path}\n"
                f'VARS run{idx} element="{str_element}" '  # needs to be
                f'log_element="{log_element}"\n\n'  # double quoted
            )
        var = ""
        if self._collect == "yes":
            var += (
                f"FINAL collect {self._submit_collect_path}\n"
                f"SCRIPT PRE collect {self._pre_collect_path.as_posix()} "
                "$DAG_STATUS\n"
            )
        elif self._collect == "on_success_only":
            var += f"JOB collect {self._submit_collect_path}\n" "PARENT "
            for idx, _ in enumerate(self._elements):
                var += f"run{idx} "
            var += "CHILD collect\n"

        return fixed + "\n" + var

    def prepare(self) -> None:
        """Prepare assets for submission."""
        logger.info("Creating HTCondor job")
        # Create logs
        logger.info(
            f"Creating logs directory under " f"{self._job_dir.resolve()!s}"
        )
        self._log_dir.mkdir(exist_ok=True, parents=True)
        # Copy executable if not local
        if hasattr(self, "_exec_path"):
            logger.info(
                f"Copying {self._executable} to "
                f"{self._exec_path.resolve()!s}"
            )
            shutil.copy(
                src=Path(__file__).parent.parent / "res" / self._executable,
                dst=self._exec_path,
            )
            make_executable(self._exec_path)
        # Create pre run
        logger.info(
            f"Writing {self._pre_run_path.name} to "
            f"{self._job_dir.resolve()!s}"
        )
        self._pre_run_path.touch()
        self._pre_run_path.write_text(textwrap.dedent(self.pre_run()))
        make_executable(self._pre_run_path)
        # Create run
        logger.debug(
            f"Writing {self._submit_run_path.name} to "
            f"{self._job_dir.resolve()!s}"
        )
        self._submit_run_path.touch()
        self._submit_run_path.write_text(textwrap.dedent(self.run()))
        # Create pre collect
        logger.info(
            f"Writing {self._pre_collect_path.name} to "
            f"{self._job_dir.resolve()!s}"
        )
        self._pre_collect_path.touch()
        self._pre_collect_path.write_text(textwrap.dedent(self.pre_collect()))
        make_executable(self._pre_collect_path)
        # Create collect
        logger.debug(
            f"Writing {self._submit_collect_path.name} to "
            f"{self._job_dir.resolve()!s}"
        )
        self._submit_collect_path.touch()
        self._submit_collect_path.write_text(textwrap.dedent(self.collect()))
        # Create DAG
        logger.debug(
            f"Writing {self._dag_path.name} to " f"{self._job_dir.resolve()!s}"
        )
        self._dag_path.touch()
        self._dag_path.write_text(textwrap.dedent(self.dag()))
        # Submit if required
        condor_submit_dag_cmd = [
            "condor_submit_dag",
            "-include_env HOME",
            f"{self._dag_path.resolve()!s}",
        ]
        if self._submit:
            run_ext_cmd(name="condor_submit_dag", cmd=condor_submit_dag_cmd)
        else:
            logger.info(
                f"HTCondor job files created, to submit the job, run:\n"
                f"{' '.join(condor_submit_dag_cmd)}"
            )
