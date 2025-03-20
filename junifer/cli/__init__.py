"""Junifer CLI components."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import sys

import lazy_loader as lazy


if sys.version_info < (3, 11):  # pragma: no cover
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


__getattr__, __dir__, __all__ = lazy.attach_stub(__name__, __file__)


# Register extensions
from .cli import cli

for ep in entry_points(group="junifer.ext"):
    cli.add_command(ep.load(), name=ep.name)
