import numpy as np
from nilearn import datasets
import nibabel as nib

from nilearn.image import resample_to_img, math_img
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker
oasis_dataset = datasets.fetch_oasis_vbm(n_subjects=1)

vbm = oasis_dataset.gray_matter_maps[0]
atlas = datasets.fetch_atlas_schaefer_2018(n_rois=100)

nifti_masker = NiftiLabelsMasker(labels_img=atlas.maps)
auto = nifti_masker.fit_transform(vbm)


img = nib.load(vbm)

atlas_img_res = resample_to_img(
    atlas.maps,
    img,
    interpolation='nearest',
)
atlas_bin = math_img(
    'img != 0',
    img=atlas_img_res,
)


masker = NiftiMasker(atlas_bin, target_affine=img.affine)

data = masker.fit_transform(img)
atlas_values = masker.transform(atlas_img_res)
atlas_values = np.squeeze(atlas_values)

manual = []
for t_v in sorted(np.unique(atlas_values)):
    t_values = np.mean(data[:, atlas_values == t_v])
    manual.append(t_values)