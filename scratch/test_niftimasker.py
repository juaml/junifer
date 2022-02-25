from distutils.command.config import config
import numpy as np
from nilearn import datasets
import nibabel as nib
from junifer.utils import configure_logging

from nilearn.image import resample_to_img, math_img
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker

configure_logging(level='INFO')

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
atlas_values = np.squeeze(atlas_values).astype(int)

manual = []
for t_v in sorted(np.unique(atlas_values)):
    t_values = np.mean(data[:, atlas_values == t_v])
    manual.append(t_values)


from junifer.markers.parcel import ParcelAggregation

marker = ParcelAggregation(atlas='Schaefer100x7', method='mean')
input = dict(VBM_GM=dict(data=img))
jun_values3d = marker.fit_transform(input)['VBM_GM']['data']


# Now do the 4D case
from nilearn.datasets import fetch_spm_auditory
from nilearn.image import concat_imgs
subject_data = fetch_spm_auditory()
fmri_img = concat_imgs(subject_data.func)

nifti_masker = NiftiLabelsMasker(labels_img=atlas.maps)
auto4d = nifti_masker.fit_transform(fmri_img)

marker = ParcelAggregation(atlas='Schaefer100x7', method='mean')
input = dict(BOLD=dict(data=fmri_img))
jun_values4d = marker.fit_transform(input)['BOLD']['data']


print(auto.shape)
print(jun_values3d.shape)
print(auto4d.shape)
print(jun_values4d.shape)


# Now both
marker = ParcelAggregation(atlas='Schaefer100x7', method='mean')
input = dict(BOLD=dict(data=fmri_img), VBM_GM=dict(data=img))
jun_both = marker.fit_transform(input)