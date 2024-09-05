"""Provide YAML config definition for junifer use."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from ruamel.yaml import YAML


__all__ = ["yaml"]


# Configure YAML class once for further use
yaml = YAML()
yaml.default_flow_style = False
yaml.allow_unicode = True
yaml.indent(mapping=2, sequence=4, offset=2)
