"""Provide class for marker collection."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections import Counter
from typing import Optional

from ..datareader import DefaultDataReader
from ..pipeline import PipelineStepMixin, WorkDirManager
from ..typing import DataGrabberLike, MarkerLike, PreprocessorLike, StorageLike
from ..utils import logger, raise_error


__all__ = ["MarkerCollection"]


class MarkerCollection:
    """Class for marker collection.

    Parameters
    ----------
    markers : list of marker-like
        The markers to compute.
    datareader : DataReader-like object, optional
        The DataReader to use (default None).
    preprocessors : list of preprocessing-like, optional
        The preprocessors to apply (default None).
    storage : storage-like, optional
        The storage to use (default None).

    Raises
    ------
    ValueError
        If ``markers`` have same names.

    """

    def __init__(
        self,
        markers: list[MarkerLike],
        datareader: Optional[PipelineStepMixin] = None,
        preprocessors: Optional[list[PreprocessorLike]] = None,
        storage: Optional[StorageLike] = None,
    ):
        # Check that the markers have different names
        marker_names = [m.name for m in markers]
        if len(set(marker_names)) != len(marker_names):
            counts = Counter(marker_names)
            raise_error(
                "Markers must have different names. "
                f"Current names are: {counts}"
            )
        self._markers = markers
        if datareader is None:
            datareader = DefaultDataReader()
        self._datareader = datareader
        self._preprocessors = preprocessors
        self._storage = storage

    def fit(self, input: dict[str, dict]) -> Optional[dict]:
        """Fit the pipeline.

        Parameters
        ----------
        input : dict
            The input data to fit the pipeline on. Should be the output of
            indexing the Data Grabber with one element.

        Returns
        -------
        dict or None
            The output of the pipeline. Each key represents a marker name and
            the values are the computer marker values. If the pipeline has a
            storage configured, then the output will be None.

        """
        logger.info("Fitting pipeline")

        # Fetch actual data using datareader
        data = self._datareader.fit_transform(input)

        # Apply preprocessing steps
        if self._preprocessors is not None:
            for preprocessor in self._preprocessors:
                logger.info(
                    "Preprocessing data with "
                    f"{preprocessor.__class__.__name__}"
                )
                # Mutate data after every iteration
                data = preprocessor.fit_transform(data)

        # Compute markers
        out = {}
        for marker in self._markers:
            logger.info(f"Fitting marker {marker.name}")
            m_value = marker.fit_transform(data, storage=self._storage)
            if self._storage is None:
                out[marker.name] = m_value
        logger.info("Marker collection fitting done")

        # Cleanup element directory
        WorkDirManager().cleanup_elementdir()

        return None if self._storage else out

    def validate(self, datagrabber: DataGrabberLike) -> None:
        """Validate the pipeline.

        Without doing any computation, check if the marker collection can
        be fitted without problems i.e., the data required for each marker is
        present and streamed down the steps. Also, if a storage is configured,
        check that the storage can handle the markers' output.

        Parameters
        ----------
        datagrabber : DataGrabber-like
            The DataGrabber to validate.

        """
        logger.info("Validating Marker Collection")
        t_data = datagrabber.get_types()
        logger.info(f"DataGrabber output type: {t_data}")

        logger.info("Validating Data Reader:")
        t_data = self._datareader.validate(t_data)
        logger.info(f"Data Reader output type: {t_data}")

        if self._preprocessors is not None:
            for preprocessor in self._preprocessors:
                logger.info(
                    "Validating Preprocessor: "
                    f"{preprocessor.__class__.__name__}"
                )
                # Copy existing data types
                old_t_data = t_data.copy()
                logger.info(f"Preprocessor input type: {t_data}")
                # Validate preprocessor
                new_t_data = preprocessor.validate(old_t_data)
                # Set new data types
                t_data = list(set(old_t_data) | set(new_t_data))
                logger.info(f"Preprocessor output type: {t_data}")

        for marker in self._markers:
            logger.info(f"Validating Marker: {marker.name}")
            # Validate marker
            m_data = marker.validate(input=t_data)
            logger.info(f"Marker output type: {m_data}")
            # Check storage for the marker
            if self._storage is not None:
                logger.info(f"Validating storage for {marker.name}")
                # Validate storage
                self._storage.validate(input_=m_data)
