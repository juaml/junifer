"""Junifer CLI components."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from importlib.metadata import entry_points

import lazy_loader as lazy


__getattr__, __dir__, __all__ = lazy.attach_stub(__name__, __file__)


# Register extensions
from .cli import cli

for ep in entry_points(group="junifer.ext"):
    cli.add_command(ep.load(), name=ep.name)
