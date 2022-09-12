"""Provide class for marker collection."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections import Counter
from typing import Dict, List, Optional

from ..datareader.default import DefaultDataReader
from ..markers.base import BaseMarker
from ..pipeline import PipelineStepMixin
from ..storage.base import BaseFeatureStorage
from ..utils import logger


class MarkerCollection:
    """Class for marker collection.

    Parameters
    ----------
    markers
    datareader
    preprocessing
    storage

    """

    def __init__(
        self,
        markers: List[BaseMarker],
        datareader: Optional[PipelineStepMixin] = None,
        preprocessing: Optional[PipelineStepMixin] = None,
        storage: Optional[BaseFeatureStorage] = None,
    ):
        """Initialize the class."""
        # Check that the markers have different names
        marker_names = [m.name for m in markers]
        if len(set(marker_names)) != len(marker_names):
            counts = Counter(marker_names)
            raise ValueError(
                "Markers must have different names. "
                f"Current names are: {counts}"
            )
        self._markers = markers
        if datareader is None:
            datareader = DefaultDataReader()
        self._datareader = datareader
        self._preprocessing = preprocessing
        self._storage = storage

    def fit(self, input: Dict[str, Dict]) -> Optional[Dict]:
        """Fit the pipeline.

        Parameters
        ----------
        input
            The input data to fit the pipeline on. Should be the output of
            indexing the DataGrabber with one element.

        Returns
        -------
        output : dict or None
            The output of the pipeline. Each key represents a marker name and
            the values are the computer marker values. If the pipeline has a
            storage configured, then the output will be None.

        """
        logger.info("Fitting pipeline")
        data = self._datareader.fit_transform(input)
        if self._preprocessing is not None:
            logger.info("Preprocessing data")
            data = self._preprocessing.fit_transform(data)
        out = {}
        for marker in self._markers:
            logger.info(f"Fitting marker {marker.name}")
            m_value = marker.fit_transform(data, storage=self._storage)
            if self._storage is None:
                out[marker.name] = m_value
        logger.info("Marker collection fitting done")
        return None if self._storage else out

    # TODO: complete type annotations
    def validate(self, datagrabber) -> None:
        """Validate the pipeline.

        Without doing any computation, check if the Marker Collection can
        be fit without problems. That is, the data required for each marker is
        present and streamed down the steps. Also, if a storage is configured,
        check that the storage can handle the markers output.

        Parameters
        ----------
        datagrabber

        """
        logger.info("Validating Marker Collection")
        t_data = datagrabber.get_types()
        logger.info(f"DataGrabber output type: {t_data}")

        logger.info("Validating Data Reader:")
        t_data = self._datareader.validate(t_data)
        logger.info(f"Data Reader output type: {t_data}")

        for marker in self._markers:
            logger.info(f"Validating Marker: {marker.name}")
            m_data = marker.validate(t_data)
            logger.info(f"Marker output type: {m_data}")
            if self._storage is not None:
                logger.info(f"Validating storage for {marker.name}")
                self._storage.validate(m_data)
