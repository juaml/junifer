import numpy as np

from nilearn.maskers import NiftiMasker
from nilearn.image import resample_to_img, math_img

from .base import BaseMarker
from ..stats import get_aggfunc_by_name
from ..data import load_atlas


class ParcelAggregation(BaseMarker):
    def __init__(self, atlas, method, method_params=None, on=None):
        if on is None:
            on = ['T1w', 'BOLD', 'VBM_GM', 'VBM_WM']
        super().__init__(on=on)
        self.atlas = atlas
        self.method = method
        self.method_params = {} if method_params is None else method_params

    def compute(self, input):
        t_input = input['data']
        agg_func = get_aggfunc_by_name(
            self.method, func_params=self.method_params)
        # Get the min of the voxels sizes and use it as the resolution
        resolution = np.min(t_input.header.get_zooms()[:3])
        t_atlas, t_labels, _ = load_atlas(
            self.atlas, resolution=resolution)
        atlas_img_res = resample_to_img(
            t_atlas,
            t_input,
            interpolation='nearest',
        )
        atlas_bin = math_img(
            'img != 0',
            img=atlas_img_res,
        )

        masker = NiftiMasker(atlas_bin, target_affine=t_input.affine)

        # Mask the input data and the atlas
        data = masker.fit_transform(t_input)
        atlas_values = masker.transform(atlas_img_res)
        atlas_values = np.squeeze(atlas_values).astype(int)

        # Get the values for each parcel and apply agg function
        atlas_roi_vals = sorted(np.unique(atlas_values))
        out_labels = []
        out_values = []
        # Iterate over the parcels (existing)
        for t_v in atlas_roi_vals:
            t_values = agg_func(data[:, atlas_values == t_v], axis=-1)
            out_values.append(t_values)
            # Update the labels just in case a parcel has no voxels
            # in it
            out_labels.append(t_labels[t_v - 1])

        out_values = np.array(out_values).transpose()
        out =  dict(data=out_values, labels=out_labels)
        return out
