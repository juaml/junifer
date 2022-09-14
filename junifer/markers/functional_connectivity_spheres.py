"""Provide base class for markers."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from typing import Dict, List

from nilearn.connectome import ConnectivityMeasure
from nilearn.maskers import NiftiSpheresMasker
from sklearn.covariance import EmpiricalCovariance

from ..api.decorators import register_marker
from ..utils import logger, raise_error
from .base import BaseMarker
from ..data.coordinates import load_coordinates


@register_marker
class FunctionalConnectivitySpheres(BaseMarker):
    """Class for functional connectivity.

     Parameters
    ----------
    seeds
    mask_img
    agg_method
    agg_method_params
    cor_method
    cor_method_params
    name
    # ToDo: add mask_img

    """

    def __init__(
        self,
        coords,
        radius,
        agg_method="mean",
        agg_method_params=None,
        cor_method="covariance",
        cor_method_params=None,
        preproc_params=None,
        name=None,
    ) -> None:
        """Initialize the class."""
        self.coords = coords
        self.radius = radius
        if radius is None or radius <= 0:
            raise_error(f'radius should be > 0: provided {radius}')
        self.agg_method = agg_method
        self.agg_method_params = (
            {} if agg_method_params is None else agg_method_params
        )
        self.cor_method = cor_method
        self.cor_method_params = (
            {} if cor_method_params is None else cor_method_params
        )
        self.preproc_params = (
            {} if preproc_params is None else preproc_params
        )
        on = ["BOLD"]
        # default to nilearn behavior
        self.cor_method_params["empirical"] = self.cor_method_params.get(
            "empirical", False
        )

        super().__init__(on=on, name=name)


    def get_output_kind(self, input: List[str]) -> List[str]:
        """Get output kind.

        Parameters
        ----------
        input : list of str
            The input to the marker. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        list of str
            The updated list of output kinds, as storage possibilities.

        """
        outputs = ["matrix"]
        return outputs

    def compute(self, input: Dict) -> Dict:
        """Compute.

        Parameters
        ----------
        input : Dict[str, Dict]
            The input to the pipeline step. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        A dict with
            FC matrix as a 2D numpy array.
            Row names as a list.
            Col names as a list.

        """
        coords, labels = load_coordinates(self.coords)

        # allow_overlap=False, smoothing_fwhm=None, standardize=False, 
        # standardize_confounds=True, high_variance_confounds=False, 
        # detrend=False, low_pass=None, high_pass=None, t_r=None
        mask_img = (None if self.preproc_params['mask_img'] 
                        is None else self.preproc_params['mask_img'])
        allow_overlap = (True if self.preproc_params['allow_overlap'] 
                        is None else self.preproc_params['allow_overlap'])
        smoothing_fwhm = (None if self.preproc_params['smoothing_fwhm'] 
                        is None else self.preproc_params['smoothing_fwhm'])
        standardize = (False if self.preproc_params['standardize'] 
                        is None else self.preproc_params['standardize'])
        standardize_confounds = (True if self.preproc_params['standardize_confounds'] 
                        is None else self.preproc_params['standardize_confounds'])
        high_variance_confounds = (False if self.preproc_params['high_variance_confounds'] 
                        is None else self.preproc_params['high_variance_confounds'])
        detrend = (False if self.preproc_params['detrend'] 
                        is None else self.preproc_params['detrend'])
        low_pass = (None if self.preproc_params['low_pass'] 
                        is None else self.preproc_params['low_pass'])
        high_pass = (None if self.preproc_params['high_pass'] 
                        is None else self.preproc_params['high_pass'])
        t_r = (None if self.preproc_params['t_r'] 
                        is None else self.preproc_params['t_r'])
        # params for fit_transform
        confounds = (None if self.preproc_params['confounds'] 
                        is None else self.preproc_params['confounds'])
        sample_mask = (None if self.preproc_params['sample_mask'] 
                        is None else self.preproc_params['sample_mask'])

        masker = NiftiSpheresMasker(
        coords, self.radius, 
        mask_img=mask_img, allow_overlap=allow_overlap, 
        smoothing_fwhm=smoothing_fwhm, detrend=detrend, standardize=standardize,
        standardize_confounds=standardize_confounds, high_variance_confounds=high_variance_confounds,
        detrend=detrend, low_pass=low_pass, high_pass=high_pass, t_r=t_r
        )
        # get the 2D timeseries
        ts = masker.fit_transform(input['data'],
                                   confounds=[confounds])[0]

        if self.cor_method_params["empirical"]:
            cm = ConnectivityMeasure(
                cov_estimator=EmpiricalCovariance(), kind=self.cor_method
            )
        else:
            cm = ConnectivityMeasure(kind=self.cor_method)
        out = {}
        out["data"] = cm.fit_transform([ts])[0]
        # create column names
        out["row_names"] = ts["columns"]
        out["col_names"] = ts["columns"]
        out["kind"] = "tril"
        return out

    # TODO: complete type annotations
    def store(self, kind: str, out: Dict, storage) -> None:
        """Store.

        Parameters
        ----------
        input
        out

        """
        logger.debug(f"Storing {kind} in {storage}")
        storage.store_matrix2d(**out)
