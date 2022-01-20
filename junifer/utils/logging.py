import logging
import subprocess
import sys
from distutils.version import LooseVersion
from pathlib import Path

logging.basicConfig(stream=sys.stdout, level=logging.WARN)
logger = logging.getLogger('JUNIFER')


def _get_git_head(path):
    """Aux function to read HEAD from git"""
    if not path.exists():
        raise ValueError('This path does not exist: {}'.format(path))
    command = ('cd {gitpath}; '
               'git rev-parse --verify HEAD').format(gitpath=path)
    process = subprocess.Popen(command,
                               stdout=subprocess.PIPE,
                               shell=True)
    proc_stdout = process.communicate()[0].strip()
    del process
    return proc_stdout


def get_versions(sys):
    """Import stuff and get versions if module
    Parameters
    ----------
    sys : module
        The sys module object.
    Returns
    -------
    module_versions : dict
        The module names and corresponding versions.
    """
    module_versions = {}
    for name, module in sys.modules.items():
        if '.' in name:
            continue
        if name in ['_curses']:
            continue
        vstring = str(getattr(module, '__version__', None))
        module_version = LooseVersion(vstring)
        module_version = getattr(module_version, 'vstring', None)
        if module_version is None:
            module_version = None
        elif 'git' in module_version:
            git_path = Path(module.__file__).resolve().parent
            head = _get_git_head(git_path)
            module_version += '-HEAD:{}'.format(head)

        module_versions[name] = module_version
    return module_versions


def get_ext_versions(tbox_path):
    """ Get versions of external tools used by JUNIFER."""
    versions = {}
    # spm_path = tbox_path / 'spm12'
    # if spm_path.exists():
    #     head = _get_git_head(spm_path)
    #     module_version = 'SPM12-HEAD:{}'.format(head)
    #     versions['spm'] = module_version
    return versions


def _safe_log(versions, name):
    if name in versions:
        logger.info(f'{name}: {versions[name]}')


def log_versions(tbox_path=None):
    versions = get_versions(sys)

    logger.info('===== Lib Versions =====')
    _safe_log(versions, 'numpy')
    _safe_log(versions, 'scipy')
    _safe_log(versions, 'nipype')
    _safe_log(versions, 'nitime')
    _safe_log(versions, 'nilearn')
    _safe_log(versions, 'nibabel')
    logger.info('========================')

    if tbox_path is not None:
        # ext_versions = get_ext_versions(tbox_path)
        # logger.info('spm: {}'.format(ext_versions['spm']))
        logger.info('========================')


def configure_logging(fname=None, level=logging.DEBUG):
    finish_logging()
    logger.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if fname is not None:
        fh = logging.FileHandler(fname, mode='a')
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def finish_logging():
    for h in list(logger.handlers):
        logger.removeHandler(h)


def raise_error(msg):
    logger.error(msg)
    raise ValueError(msg)


class LoggerWriter:
    # Got this from StackOverflow to redirect stdout and stderr to the logger
    # log = logging.getLogger('foobar')
    # sys.stdout = LoggerWriter(log.debug)
    # sys.stderr = LoggerWriter(log.warning)
    def __init__(self, level):
        # self.level is really like using log.debug(message)
        self.level = level

    def write(self, message):
        # if statement reduces the amount of newlines that are
        # printed to the logger
        if message != '\n':
            self.level(message)

    def flush(self):
        # create a flush method so things can be flushed when
        # the system wants to. Not sure if simply 'printing'
        # sys.stderr is the correct way to do it, but it seemed
        # to work properly for me.
        self.level(sys.stderr)
