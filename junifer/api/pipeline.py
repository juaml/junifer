# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL
from ..utils.logging import raise_error, logger

_valid_steps = [
    'datagrabber', 'datareader', 'preprocessing', 'marker', 'storage']

_registry = {x: {} for x in _valid_steps}


def register(step, name, klass):
    """Register a function to be used in a pipeline step

    Parameters
    ----------
    step : str
        Name of the step
    name : str
        Name of the function
    klass : class
        Class to be registered
    """
    if step not in _valid_steps:
        raise_error(f'Invalid step: {step}', ValueError)
    logger.info(f'Registering {name} in {step}')
    _registry[step][name] = klass


def run_pipeline(
        workdir, datagrabber, element, markers, storage, source_params=None,
        storage_params=None):
    """Run the pipeline on the selected element

    Parameters
    ----------
    workdir : str or path-like object
        Directory where the pipeline will be executed
    datagrabber : str
        Name of the datagrabber to use
    element : str
        Name of the element to process. Will be used to index the datagrabber.
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
