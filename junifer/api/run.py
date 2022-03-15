# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL

from pathlib import Path

from .registry import build
from ..datagrabber.base import BaseDataGrabber
from ..markers.base import BaseMarker
from ..storage.base import BaseFeatureStorage
from ..markers.collection import MarkerCollection


def run(
        workdir, datagrabber,  markers, storage, source_params=None,
        storage_params=None, elements=None):
    """Run the pipeline on the selected element

    Parameters
    ----------
    workdir : str or path-like object
        Directory where the pipeline will be executed
    datagrabber : str
        Name of the datagrabber to use
    elements : str, tuple or list[str or tuple]
        Element(s) to process. Will be used to index the datagrabber.
    markers : list of dict
        List of markers to extract. Each marker is a dict with at least two
        keys: 'name' and 'kind'. The 'name' key is used to name the output
        marker. The 'kind' key is used to specify the kind of marker to
        extract. The rest of the keys are used to pass parameters to the
        marker calculation.
    storage: str
        Name of the storage to use.
    source_params : dict
        Parameters to pass to the datagrabber.
    storage_params: dict
        Parameters to pass to the storage.
    """
    if source_params is None:
        source_params = {}

    if storage_params is None:
        storage_params = {}

    if isinstance(workdir, str):
        workdir = Path(workdir)

    datagrabber = build(
        'datagrabber', datagrabber, BaseDataGrabber, init_params=source_params)

    built_markers = []
    for t_marker in markers:
        kind = t_marker.pop('kind')
        t_m = build('marker', kind, BaseMarker, init_params=t_marker)
        built_markers.append(t_m)

    storage = build(
        'storage', storage, BaseFeatureStorage, init_params=storage_params)

    mc = MarkerCollection(built_markers, storage=storage)

    with datagrabber:
        if elements is not None:
            for t_element in elements:
                mc.fit(datagrabber[t_element])
        else:
            for t_element in datagrabber:
                mc.fit(datagrabber[t_element])
