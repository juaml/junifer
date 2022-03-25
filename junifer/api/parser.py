import yaml
import importlib
from pathlib import Path

from ..utils.logging import raise_error, logger


def parse_yaml(filepath):
    if not isinstance(filepath, Path):
        filepath = Path(filepath)
    logger.info(f'Parsing yaml file: {filepath.as_posix()}')
    if not filepath.exists():
        raise_error(f'File does not exist: {filepath.as_posix()}')
    with open(filepath, 'r') as f:
        contents = yaml.safe_load(f)

    if 'with' in contents:
        to_load = contents['with']
        if not isinstance(to_load, list):
            to_load = [to_load]
        for t_module in to_load:
            logger.info(f'Importing module {t_module}')
            importlib.import_module(t_module)

    return contents
