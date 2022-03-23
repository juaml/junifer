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
        workdir, datagrabber,  markers, storage, elements=None):
    """Run the pipeline on the selected element

    Parameters
    ----------
    workdir : str or path-like object
        Directory where the pipeline will be executed
    datagrabber : dict
        Datagrabber to use. Must have a key 'kind' with the kind of
        datagrabber to use. All other keys are passed to the datagrabber
        init function.
    elements : str, tuple or list[str or tuple]
        Element(s) to process. Will be used to index the datagrabber.
    markers : list of dict
        List of markers to extract. Each marker is a dict with at least two
        keys: 'name' and 'kind'. The 'name' key is used to name the output
        marker. The 'kind' key is used to specify the kind of marker to
        extract. The rest of the keys are used to pass parameters to the
        marker calculation.
    storage : dict
        Storage to use. Must have a key 'kind' with the kind of
        storage to use. All other keys are passed to the storage
        init function.
    """
    datagrabber_params = datagrabber.copy()
    datagrabber_kind = datagrabber_params.pop('kind')
    storage_params = storage.copy()
    storage_kind = storage_params.pop('kind')

    if isinstance(workdir, str):
        workdir = Path(workdir)

    datagrabber = build(
        'datagrabber', datagrabber_kind, BaseDataGrabber,
        init_params=datagrabber_params)

    built_markers = []
    for t_marker in markers:
        kind = t_marker.pop('kind')
        t_m = build('marker', kind, BaseMarker, init_params=t_marker)
        built_markers.append(t_m)

    storage = build(
        'storage', storage_kind, BaseFeatureStorage,
        init_params=storage_params)

    mc = MarkerCollection(built_markers, storage=storage)

    with datagrabber:
        if elements is not None:
            for t_element in elements:
                mc.fit(datagrabber[t_element])
        else:
            for t_element in datagrabber:
                mc.fit(datagrabber[t_element])


def collect(storage):
    storage_params = storage.copy()
    storage_kind = storage_params.pop('kind')

    storage = build(
        'storage', storage_kind, BaseFeatureStorage,
        init_params=storage_params)
    storage.collect()
