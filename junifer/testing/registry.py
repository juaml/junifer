from .datagrabbers import OasisVBMTestingDatagrabber
from ..api.registry import register

register(
    'datagrabber', 'OasisVBMTestingDatagrabber',
    OasisVBMTestingDatagrabber)
