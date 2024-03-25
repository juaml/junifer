"""Define concrete class for generating GNU Parallel (local) assets."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

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
    env : dict, optional
        The Python environment configuration. If None, will run without a
        virtual environment of any kind (default None).
    verbose : str, optional
        The level of verbosity (default "info").
    submit : bool, optional
        Whether to submit the jobs (default False).

    Raises
    ------
    ValueError
        If``env`` is invalid.

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
        elements: List[Union[str, Tuple]],
        env: Optional[Dict[str, str]] = None,
        verbose: str = "info",
        submit: bool = False,
    ) -> None:
        """Initialize the class."""
        self._job_dir = job_dir
        self._yaml_config_path = yaml_config_path
        self._elements = elements
        self._check_env(env)
        self._verbose = verbose
        self._submit = submit

        self._run_joblog_path = self._job_dir / f"{job_name}_run_joblog.txt"
        self._collect_joblog_path = (
            self._job_dir / f"{job_name}_collect_joblog.txt"
        )

    def _check_env(self, env: Optional[Dict[str, str]]) -> None:
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
            # Set variables
            if env["kind"] == "local":
                # No virtual environment
                self._executable = "junifer"
                self._arguments = ""
            else:
                self._executable = f"run_{env['kind']}.sh"
                self._arguments = f"{env['name']} junifer"
                self._exec_path = self._job_dir / self._executable

    def run(self) -> str:
        """Return run commands."""
        junifer_run_cmd = (
            "parallel --bar --halt now,fail=1 "
            f"--joblog {self._run_joblog_path} "
            f"{self._job_dir.resolve()!s}/{self._executable} "
            f"{self._arguments} run "
            f"{self._yaml_config_path.resolve()!s} "
            f"--verbose {self._verbose} "
            f"--element :::"
        )
        for element in self._elements:
            # Stringify elements if tuple for operation
            str_element = (
                ",".join(element) if isinstance(element, tuple) else element
            )
            junifer_run_cmd += f" '{str_element}'"

        return junifer_run_cmd

    def collect(self) -> str:
        """Return collect commands."""
        return (
            f"parallel --joblog {self._collect_joblog_path} "
            f"{self._job_dir.resolve()!s}/{self._executable} "
            f"{self._arguments} collect "
            f"{self._yaml_config_path.resolve()!s} "
            f"--verbose {self._verbose}"
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
        # Generate run command
        logger.info(f"`junifer run` command:\n{self.run()}")
        # Generate collect command
        logger.info(f"`junifer collect` command:\n{self.collect()}")
        # Submit if required
        if self._submit:
            logger.info(
                "First the `junifer run` command as shown above will be run. "
                "After successful completion of the previous step, run the "
                "`junifer collect` command as shown above. "
                "If you need to retry any step, simply append "
                "`--resume-failed` after `--joblog <value>` option."
            )
            run_ext_cmd(name="parallel", cmd=[self.run()])
        else:
            logger.info(
                "First run the `junifer run` command as shown above. "
                "After successful completion of the previous step, run the "
                "`junifer collect` command as shown above. "
                "If you need to retry any step, simply append "
                "`--resume-failed` after `--joblog <value>` option."
            )
