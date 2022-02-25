import numpy as np

from nilearn.maskers import NiftiLabelsMasker

from .base import PipelineStepMixin
from ..stats import get_aggfunc_by_name
from ..data import load_atlas

class ParcelAggregation(PipelineStepMixin):
    def __init__(self, atlas, method, method_params=None):
        self.atlas = atlas
        self.method = method
        self.method_params = {} if method_params is None else method_params
        self._valid_inputs = ['T1w', 'BOLD', 'VBM_GM', 'VBM_WM']

    def validate_input(self, input):
        return any(x in input for x in self._valid_inputs)

    def get_output_kind(self, input):
        return None

    def fit_transform(self, input, storage=None):
        out = []
        agg_func = get_aggfunc_by_name(self.method, **self.method_params)
        for kind in self._valid_inputs:
            if kind in input.keys():
                t_input = input[kind].data

                # Get the min of the voxels sizes and use it as the resolution
                resolution = np.min(t_input.header.get_zooms()[:3])
                t_atlas, t_labels = load_atlas(
                    self.atlas, resolution=resolution)
                masker = NiftiLabelsMasker(
                    labels_img=t_atlas,
                    labels=t_labels
                    ,
                )

        return input