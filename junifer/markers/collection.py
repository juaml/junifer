"""Provide class for marker collection."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from ..utils import logger
from ..datareader import DefaultDataReader

from collections import Counter


class MarkerCollection():
    """Class for marker collection."""

    def __init__(
            self, markers, datareader=None, preprocessing=None, storage=None
    ):
        """Initialize the class."""
        if datareader is None:
            datareader = DefaultDataReader()
        self._datareader = datareader
        self._preprocessing = preprocessing
        self._markers = markers
        self._storage = storage

        # Check that the markers have different names
        marker_names = [m.name for m in self._markers]
        if len(set(marker_names)) != len(marker_names):
            counts = Counter(marker_names)
            raise ValueError(
                'Markers must have different names. '
                f'Current names are: {counts}')

    def fit(self, input):
        """Fit the pipeline.

        Parameters
        ----------
        input : Junifer Data dictionary (input)
            The input data to fit the pipeline on. Should be the output of
            indexing the DataGrabber with one element.

        Returns
        -------
        output : dict[str -> object] | None
            The output of the pipeline. Each key represents a marker name and
            the values are the computer marker values. If the pipeline has a
            storage configured, then the output will be None.
        """
        logger.info('Fitting pipeline')
        data = self._datareader.fit_transform(input)
        if self._preprocessing is not None:
            logger.info('Preprocessing data')
            data = self._preprocessing.fit_transform(data)
        out = {}
        for marker in self._markers:
            logger.info(f'Fitting marker {marker.name}')
            m_value = marker.fit_transform(data, storage=self._storage)
            if self._storage is None:
                out[marker.name] = m_value
        logger.info('Marker collection fitting done')
        return None if self._storage else out

    def validate(self, datagrabber):
        """Validate the pipeline.

        Without doing any computation, check if the Marker Collection can
        be fit without problems. That is, the data required for each marker is
        present and streamed down the steps. Also, if a storage is configured,
        check that the storage can handle the markers output.
        """
        logger.info('Validating Marker Collection')
        t_data = datagrabber.get_types()
        logger.info(f'DataGrabber output type: {t_data}')

        logger.info('Validating Data Reader:')
        t_data = self._datareader.validate(t_data)
        logger.info(f'Data Reader output type: {t_data}')

        for marker in self._markers:
            logger.info(f'Validating Marker: {marker.name}')
            m_data = marker.validate(t_data)
            logger.info(f'Marker output type: {m_data}')
            if self._storage is not None:
                logger.info(f'Validating storage for {marker.name}')
                self._storage.validate(m_data)
