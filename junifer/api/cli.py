import click

from .parser import parse_yaml
from .run import run as api_run
from .run import collect as api_collect
from ..utils.logging import configure_logging


@click.group()
def cli():
    pass


@cli.command()
@click.argument('filepath')
@click.option('-v', '--verbose',
              type=click.Choice(['warning', 'info', 'debug'],
                                case_sensitive=False),
              default='warning')
def run(filepath, verbose):
    configure_logging(level=verbose.upper())
    contents = parse_yaml(filepath)
    workdir = contents['workdir']
    datagrabber = contents['datagrabber']
    markers = contents['markers']
    storage = contents['storage']
    elements = contents.get('elements', None)
    api_run(
        workdir=workdir, datagrabber=datagrabber,  markers=markers,
        storage=storage, elements=elements)


@cli.command()
@click.argument('filepath')
@click.option('-v', '--verbose',
              type=click.Choice(['warning', 'info', 'debug'],
                                case_sensitive=False),
              default='warning')
def collect(filepath, verbose):
    configure_logging(level=verbose.upper())
    contents = parse_yaml(filepath)
    storage = contents['storage']
    api_collect(storage)


@cli.command()
def queue():
    click.echo('queue')
