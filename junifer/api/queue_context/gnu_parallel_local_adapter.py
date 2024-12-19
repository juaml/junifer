"""Define concrete class for generating GNU Parallel (local) assets."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import shutil
import textwrap
from pathlib import Path
from typing import Optional

from ...typing import Elements
from ...utils import logger, make_executable, raise_error, run_ext_cmd
from .queue_context_adapter import QueueContextAdapter


__all__ = ["GnuParallelLocalAdapter"]


class GnuParallelLocalAdapter(QueueContextAdapter):
    """Class for generating commands for GNU Parallel (local).

    Parameters
    ----------
    job_name : str
        The job name.
    job_dir : pathlib.Path
        The path to the job directory.
    yaml_config_path : pathlib.Path
        The path to the YAML config file.
    elements : list of str or tuple
        Element(s) to process. Will be used to index the DataGrabber.
    pre_run : str or None, optional
        Extra shell commands to source before the run (default None).
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
    submit : bool, optional
        Whether to submit the jobs (default False).

    Raises
    ------
    ValueError
        If ``env.kind`` is invalid or
        if ``env.shell`` is invalid.

    See Also
    --------
    QueueContextAdapter :
        The base class for QueueContext.
    HTCondorAdapter :
        The concrete class for queueing via HTCondor.

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
        self._submit = submit

        self._log_dir = self._job_dir / "logs"
        self._pre_run_path = self._job_dir / "pre_run.sh"
        self._pre_collect_path = self._job_dir / "pre_collect.sh"
        self._run_path = self._job_dir / f"run_{self._job_name}.sh"
        self._collect_path = self._job_dir / f"collect_{self._job_name}.sh"
        self._run_joblog_path = self._job_dir / f"run_{self._job_name}_joblog"
        self._elements_file_path = self._job_dir / "elements"

    def _check_env(self, env: Optional[dict[str, str]]) -> None:
        """Check value of env parameter on init.

        Parameters
        ----------
        env : dict or None
            The value of env parameter.

        Raises
        ------
        ValueError
            If ``env.kind`` is invalid.

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

    def elements(self) -> str:
        """Return elements to run."""
        elements_to_run = []
        for element in self._elements:
            # Stringify elements if tuple for operation
            str_element = (
                ",".join(element) if isinstance(element, tuple) else element
            )
            elements_to_run.append(str_element)

        return "\n".join(elements_to_run)

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
        verbose_args = f"--verbose {self._verbose}"
        if self._verbose_datalad:
            verbose_args = (
                f"{verbose_args} --verbose-datalad {self._verbose_datalad}"
            )
        return (
            f"#!/usr/bin/env {self._shell}\n\n"
            "# This script is auto-generated by junifer.\n\n"
            "# Run pre_run.sh\n"
            f"sh {self._pre_run_path.resolve()!s}\n\n"
            "# Run `junifer run` using `parallel`\n"
            "parallel --bar --resume --resume-failed "
            f"--joblog {self._run_joblog_path} "
            "--delay 60 "  # wait 1 min before next job is spawned
            f"--results {self._log_dir} "
            f"--arg-file {self._elements_file_path.resolve()!s} "
            f"{self._job_dir.resolve()!s}/{self._executable} "
            f"{self._arguments} run "
            f"{self._yaml_config_path.resolve()!s} "
            f"{verbose_args} "
            f"--element"
        )

    def pre_collect(self) -> str:
        """Return pre-collect commands."""
        fixed = (
            f"#!/usr/bin/env {self._shell}\n\n"
            "# This script is auto-generated by junifer.\n"
        )
        var = self._pre_collect or ""
        return fixed + "\n" + var

    def collect(self) -> str:
        """Return collect commands."""
        verbose_args = f"--verbose {self._verbose}"
        if self._verbose_datalad:
            verbose_args = (
                f"{verbose_args} --verbose-datalad {self._verbose_datalad}"
            )
        return (
            f"#!/usr/bin/env {self._shell}\n\n"
            "# This script is auto-generated by junifer.\n\n"
            "# Run pre_collect.sh\n"
            f"sh {self._pre_collect_path.resolve()!s}\n\n"
            "# Run `junifer collect`\n"
            f"{self._job_dir.resolve()!s}/{self._executable} "
            f"{self._arguments} collect "
            f"{self._yaml_config_path.resolve()!s} "
            f"{verbose_args}"
        )

    def prepare(self) -> None:
        """Prepare assets for submission."""
        logger.info("Preparing for local queue via GNU parallel")
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
        # Create elements file
        logger.info(
            f"Writing {self._elements_file_path.name} to "
            f"{self._elements_file_path.resolve()!s}"
        )
        self._elements_file_path.touch()
        self._elements_file_path.write_text(textwrap.dedent(self.elements()))
        # Create pre run
        logger.info(
            f"Writing {self._pre_run_path.name} to "
            f"{self._job_dir.resolve()!s}"
        )
        self._pre_run_path.touch()
        self._pre_run_path.write_text(textwrap.dedent(self.pre_run()))
        make_executable(self._pre_run_path)
        # Create run
        logger.info(
            f"Writing {self._run_path.name} to " f"{self._job_dir.resolve()!s}"
        )
        self._run_path.touch()
        self._run_path.write_text(textwrap.dedent(self.run()))
        make_executable(self._run_path)
        # Create pre collect
        logger.info(
            f"Writing {self._pre_collect_path.name} to "
            f"{self._job_dir.resolve()!s}"
        )
        self._pre_collect_path.touch()
        self._pre_collect_path.write_text(textwrap.dedent(self.pre_collect()))
        make_executable(self._pre_collect_path)
        # Create collect
        logger.info(
            f"Writing {self._collect_path.name} to "
            f"{self._job_dir.resolve()!s}"
        )
        self._collect_path.touch()
        self._collect_path.write_text(textwrap.dedent(self.collect()))
        make_executable(self._collect_path)
        # Submit if required
        run_cmd = f"sh {self._run_path.resolve()!s}"
        collect_cmd = f"sh {self._collect_path.resolve()!s}"
        if self._submit:
            logger.info(
                "Shell scripts created, the following will be run:\n"
                f"{run_cmd}\n"
                "After successful completion of the previous step, run:\n"
                f"{collect_cmd}"
            )
            run_ext_cmd(name=f"{self._run_path.resolve()!s}", cmd=[run_cmd])
        else:
            logger.info(
                "Shell scripts created, to start, run:\n"
                f"{run_cmd}\n"
                "After successful completion of the previous step, run:\n"
                f"{collect_cmd}"
            )
