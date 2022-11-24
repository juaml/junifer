"""Provide abstract class for computing fALFF."""
# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import numpy as np
from scipy import signal

from junifer.markers.base import BaseMarker
from junifer.utils import logger

if TYPE_CHECKING:
    from junifer.storage import BaseFeatureStorage


class AmplitudeLowFrequencyFluctuationBase(BaseMarker):
    """Class for computing fALFF/ALFF.

    Parameters
    ----------
    tr : float, optional
        The Repetition Time of the BOLD data. If None, will extract
        the TR from NIFTI header (default None).
    name : str, optional
        The name of the marker. If None, will use the class name (default
        None).

    Notes
    -----
        The `tr` parameter is crucial for the correctness of fALFF/ALFF
        computation. If a dataset is correctly preprocessed, the TR should be
        extracted from the NIFTI without any issue. However, it has been
        reported that some preprocessed data might not have the correct TR in
        the NIFTI header.
    """

    def __init__(
        self,
        highpass: float,
        lowpass: float,
        order: int,
        tr: Optional[float] = None,
        name: Optional[str] = None,
    ) -> None:
        if highpass <= 0:
            raise ValueError("Highpass must be positive")
        if lowpass <= 0:
            raise ValueError("Lowpass must be positive")
        if highpass >= lowpass:
            raise ValueError("Highpass must be lower than lowpass")
        self.highpass = highpass
        self.lowpass = lowpass
        if order <= 0:
            raise ValueError("Order must be positive")
        self.order = order
        self.tr = tr

        super().__init__(on="BOLD", name=name)

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker.

        """
        valid = ["BOLD"]
        return valid

    def get_output_kind(self, input: List[str]) -> List[str]:
        """Get output kind.

        Parameters
        ----------
        input : list of str
            The kind of data to work on.

        Returns
        -------
        list of str
            The list of storage kinds.

        """
        return ["table"]

    def get_meta(self, kind: str, fractional: bool) -> Dict:
        """Get metadata.

        Parameters
        ----------
        kind : str
            The kind of pipeline step.
        fractional : bool
            If true, get the meta for fractional ALFF.

        Returns
        -------
        dict
            The metadata as a dictionary with the only key 'marker'.

        """
        s_meta = super().get_meta(kind)
        suffix = "_fALFF" if fractional else "_ALFF"
        s_meta["marker"]["name"] += suffix
        return s_meta

    def fit_transform(
        self,
        input: Dict[str, Dict],
        storage: Optional["BaseFeatureStorage"] = None,
    ) -> Dict:
        """Fit and transform.

        Parameters
        ----------
        input : dict
            The Junifer Data object.
        storage : storage-like, optional
            The storage class, for example, SQLiteFeatureStorage.

        Returns
        -------
        dict
            The processed output as a dictionary. If `storage` is provided,
            empty dictionary is returned.

        """
        out = {}
        t_meta = input.get("meta", {}).copy()
        logger.info("Computing fALFF on BOLD")
        t_input = input["BOLD"]
        t_meta.update(t_input.get("meta", {}))

        # Compute ALFF and fALFF
        alff, falff = self.compute(input=t_input)

        alff_meta = t_meta.copy().update(
            self.get_meta("BOLD", fractional=False)
        )
        falff_meta = t_meta.copy().update(
            self.get_meta("BOLD", fractional=True)
        )

        alff.update(meta=alff_meta)
        falff.update(meta=falff_meta)
        if storage is not None:
            logger.info(f"Storing in {storage}")
            self.store(kind="BOLD", out=alff, storage=storage)
            self.store(kind="BOLD", out=falff, storage=storage)
        else:
            logger.info("No storage specified, returning dictionary")
            out["BOLD"] = {
                "ALFF": alff,
                "fALFF": falff,
            }
        return out

    def compute_falff(
        self, timeseries: np.ndarray, labels: List[str], tr: float
    ) -> Tuple[Dict, Dict]:
        """Compute ALFF and fALFF.

        Parameters
        ----------
        timeseries : np.ndarray
            The timeseries data.
        labels : np.ndarray
            The labels for each timeseries.
        tr : float
            The repetition time.

        Returns
        -------
        alff: dict
            The computed ALFF as dictionary. The dictionary has the following
            keys:

            * ``data`` : the actual computed values as a numpy.ndarray
            * ``columns`` : the column labels for the computed values as a list

        falff: dict
            The computed fALFF as dictionary. The dictionary has the following
            keys:

            * ``data`` : the actual computed values as a numpy.ndarray
            * ``columns`` : the column labels for the computed values as a list
        """
        # bandpass the data within the lowpass and highpass cutoff freqs
        Nq = 1 / (2 * tr)
        Wn = np.array([self.highpass / Nq, self.lowpass / Nq])

        b, a = signal.butter(N=self.order, Wn=Wn, btype="bandpass")
        ts_filt = signal.filtfilt(b, a, timeseries, axis=0)

        ALFF = np.std(ts_filt, axis=0)
        PSD_tot = np.std(timeseries, axis=0)

        fALFF = np.divide(ALFF, PSD_tot)

        out_alff = {"data": ALFF, "columns": labels}
        out_falff = {"data": fALFF, "columns": labels}

        return out_alff, out_falff

    def store(self, kind, out, storage):
        """Store.

        Parameters
        ----------
        kind : {"BOLD"}
            The data kind to store.
        out : dict
            The computed result as a dictionary to store.
        storage : storage-like
            The storage class, for example, SQLiteFeatureStorage.
        """
        logger.debug(f"Storing {kind} in {storage}")
        storage.store(kind="table", **out)
