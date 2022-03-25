from pathlib import Path
import tempfile
import yaml
from junifer.api.cli import run, collect

from click.testing import CliRunner


runner = CliRunner()


def _modify_path(tmpdir, in_file):
    """Modify the path to use the temporary directory"""
    if not isinstance(tmpdir, Path):
        tmpdir = Path(tmpdir)
    with open(in_file, 'r') as f:
        contents = yaml.safe_load(f)
    outfile = tmpdir / 'in.yaml'
    outdir = tmpdir / 'out'
    workdir = tmpdir / 'work'
    contents['storage']['uri'] = outdir.as_posix()
    contents['workdir'] = workdir.as_posix()
    with open(outfile, 'w') as f:
        yaml.dump(contents, f)
    return outfile


def test_run_collect():
    """Test run and collect"""
    infile = Path(__file__).parent / 'data' / 'gmd_mean.yaml'
    with tempfile.TemporaryDirectory() as _tmpdir:
        runfile = _modify_path(_tmpdir, infile)
        run_args = [runfile.as_posix(), '--verbose', 'debug', '--element',
                    'sub-01', '--element', 'sub-02', '--element', 'sub-03']
        response = runner.invoke(run, run_args)
        assert response.exit_code == 0

        # TODO: Check that there are 3 files in the output directory

        collect_args = [runfile.as_posix(), '--verbose', 'debug']
        response = runner.invoke(collect, collect_args)
        assert response.exit_code == 0

        # TODO: Check that there are 4 files in the output directory
        # TODO: Check that the collected file has the correct number of rows

        run_args = [runfile.as_posix(), '--verbose', 'debug', '--element',
                    'sub-01', '--element', 'sub-02', '--element', 'sub-04']
        response = runner.invoke(run, run_args)
        assert response.exit_code == 0

        # TODO: Check that there are 5 files in the output directory
        # TODO: Check that the collected file has 3 rows (sub-04 is not there)

        collect_args = [runfile.as_posix(), '--verbose', 'debug']
        response = runner.invoke(collect, collect_args)
        assert response.exit_code == 0

        # TODO: Check that there are 5 files in the output directory
        # TODO: Check that the collected file has 4 rows (sub-04 is there)
