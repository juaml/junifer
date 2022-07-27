"""Provide test for parcel aggregation."""

import numpy as np
from numpy.testing import assert_array_equal, assert_array_almost_equal
from scipy.stats import trim_mean
import nibabel as nib

from nilearn import datasets
from nilearn.image import resample_to_img, math_img, concat_imgs
from nilearn.maskers import NiftiMasker, NiftiLabelsMasker

from junifer.markers.parcel import ParcelAggregation


def test_ParcelAggregation_3D():
    """Test ParcelAggregation object on 3D images."""

    # Get the testing atlas (for nilearn)
    atlas = datasets.fetch_atlas_schaefer_2018(n_rois=100)

    # Get the oasis VBM data:
    oasis_dataset = datasets.fetch_oasis_vbm(n_subjects=1)
    vbm = oasis_dataset.gray_matter_maps[0]
    img = nib.load(vbm)

    # Mask atlas manually
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

    # Compute the mean manually
    manual = []
    for t_v in sorted(np.unique(atlas_values)):
        t_values = np.mean(data[:, atlas_values == t_v])
        manual.append(t_values)
    manual = np.array(manual)[np.newaxis, :]

    nifti_masker = NiftiLabelsMasker(labels_img=atlas.maps)
    auto = nifti_masker.fit_transform(img)

    assert_array_almost_equal(auto, manual)

    # Use the ParcelAggregation object
    marker = ParcelAggregation(
        atlas='Schaefer100x7', method='mean', name='gmd_schaefer100x7_mean',
        on='VBM_GM')   # Test passing "on" as a keyword argument
    input = dict(VBM_GM=dict(data=img))
    jun_values3d_mean = marker.fit_transform(input)['VBM_GM']['data']

    assert jun_values3d_mean.ndim == 2
    assert jun_values3d_mean.shape[0] == 1
    assert_array_equal(manual, jun_values3d_mean)

    meta = marker.get_meta('VBM_GM')['marker']
    assert meta['method'] == 'mean'
    assert meta['atlas'] == 'Schaefer100x7'
    assert meta['name'] == 'VBM_GM_gmd_schaefer100x7_mean'
    assert meta['class'] == 'ParcelAggregation'
    assert meta['kind'] == 'VBM_GM'
    assert meta['method_params'] == {}

    # Test using another function (std)
    manual = []
    for t_v in sorted(np.unique(atlas_values)):
        t_values = np.std(data[:, atlas_values == t_v])
        manual.append(t_values)
    manual = np.array(manual)[np.newaxis, :]

    # Use the ParcelAggregation object
    marker = ParcelAggregation(atlas='Schaefer100x7', method='std')
    input = dict(VBM_GM=dict(data=img))
    jun_values3d_std = marker.fit_transform(input)['VBM_GM']['data']

    assert jun_values3d_std.ndim == 2
    assert jun_values3d_std.shape[0] == 1
    assert_array_equal(manual, jun_values3d_std)

    meta = marker.get_meta('VBM_GM')['marker']
    assert meta['method'] == 'std'
    assert meta['atlas'] == 'Schaefer100x7'
    assert meta['name'] == 'VBM_GM_ParcelAggregation'
    assert meta['class'] == 'ParcelAggregation'
    assert meta['kind'] == 'VBM_GM'
    assert meta['method_params'] == {}

    # Test using another function with parameters
    manual = []
    for t_v in sorted(np.unique(atlas_values)):
        t_values = trim_mean(
            data[:, atlas_values == t_v], proportiontocut=0.1,
            axis=None)  # type: ignore
        manual.append(t_values)
    manual = np.array(manual)[np.newaxis, :]

    # Use the ParcelAggregation object
    marker = ParcelAggregation(
        atlas='Schaefer100x7', method='trim_mean',
        method_params={'proportiontocut': 0.1})
    input = dict(VBM_GM=dict(data=img))
    jun_values3d_tm = marker.fit_transform(input)['VBM_GM']['data']

    assert jun_values3d_tm.ndim == 2
    assert jun_values3d_tm.shape[0] == 1
    assert_array_equal(manual, jun_values3d_tm)

    meta = marker.get_meta('VBM_GM')['marker']
    assert meta['method'] == 'trim_mean'
    assert meta['atlas'] == 'Schaefer100x7'
    assert meta['name'] == 'VBM_GM_ParcelAggregation'
    assert meta['class'] == 'ParcelAggregation'
    assert meta['kind'] == 'VBM_GM'
    assert meta['method_params'] == {'proportiontocut': 0.1}


def test_ParcelAggregation_4D():
    """Test ParcelAggregation object on 4D images."""

    # Get the testing atlas (for nilearn)
    atlas = datasets.fetch_atlas_schaefer_2018(
        n_rois=100, yeo_networks=7, resolution_mm=2)

    # Get the SPM auditory data:
    subject_data = datasets.fetch_spm_auditory()
    fmri_img = concat_imgs(subject_data.func)  # type: ignore

    nifti_masker = NiftiLabelsMasker(labels_img=atlas.maps)
    auto4d = nifti_masker.fit_transform(fmri_img)

    marker = ParcelAggregation(atlas='Schaefer100x7', method='mean')
    input = dict(BOLD=dict(data=fmri_img))
    jun_values4d = marker.fit_transform(input)['BOLD']['data']

    assert jun_values4d.ndim == 2
    assert_array_equal(auto4d.shape, jun_values4d.shape)
    assert_array_equal(auto4d, jun_values4d)

    meta = marker.get_meta('BOLD')['marker']
    assert meta['method'] == 'mean'
    assert meta['atlas'] == 'Schaefer100x7'
    assert meta['name'] == 'BOLD_ParcelAggregation'
    assert meta['class'] == 'ParcelAggregation'
    assert meta['kind'] == 'BOLD'
    assert meta['method_params'] == {}
