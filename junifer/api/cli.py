import click

from .parser import parse_yaml
from .functions import run as api_run
from .functions import collect as api_collect
from .functions import queue as api_queue
from ..utils.logging import configure_logging, logger, warn


def _parse_elements(element, config):
    logger.debug(f'Parsing elements: {element}')
    if len(element) == 0:
        return None
    # TODO: If len == 1, check if its a file, then parse elements from file
    elements = [x.split(',') if ',' in x else x for x in element]
    logger.debug(f'Parsed elements: {elements}')
    if elements is not None and 'elements' in config:
        warn('One or more elements have been specified in both the command '
             'line and in the config file. The command line has precedence '
             'over the configuration file. That is, the elements specified '
             'in the command line will be used. The elements specified in '
             'the configuration file will be ignored. To remove this warning, '
             'please remove the "elements" item from the configuration file.')
    elif elements is None:
        elements = config.get('elements', None)
    return elements


@click.group()
def cli():
    pass


@cli.command()
@click.argument('filepath', type=click.File('r'))
@click.option('-v', '--verbose',
              type=click.Choice(['warning', 'info', 'debug'],
                                case_sensitive=False),
              default='info')
@click.option('--element', type=str, multiple=True)
def run(filepath, element, verbose):
    configure_logging(level=verbose.upper())
    config = parse_yaml(filepath)
    workdir = config['workdir']
    datagrabber = config['datagrabber']
    markers = config['markers']
    storage = config['storage']
    elements = _parse_elements(element, config)
    api_run(
        workdir=workdir, datagrabber=datagrabber,  markers=markers,
        storage=storage, elements=elements)


@cli.command()
@click.argument('filepath', type=click.File('r'))
@click.option('-v', '--verbose',
              type=click.Choice(['warning', 'info', 'debug'],
                                case_sensitive=False),
              default='info')
def collect(filepath, verbose):
    configure_logging(level=verbose.upper())
    config = parse_yaml(filepath)
    storage = config['storage']
    api_collect(storage)


@cli.command()
@click.argument(
    'filepath',
    type=click.Path(exists=True, readable=True, dir_okay=False))
@click.option('-v', '--verbose',
              type=click.Choice(['warning', 'info', 'debug'],
                                case_sensitive=False),
              default='info')
@click.option('--overwrite', is_flag=True)
@click.option('--submit', is_flag=True)
@click.option('--element', type=str, multiple=True)
def queue(filepath, element, overwrite, submit, verbose):
    configure_logging(level=verbose.upper())
    config = parse_yaml(filepath)
    elements = _parse_elements(element, config)
    queue_config = config.pop('queue')
    kind = queue_config.pop('kind')
    api_queue(config, kind=kind, overwrite=overwrite, submit=submit,
              elements=elements, **queue_config)
