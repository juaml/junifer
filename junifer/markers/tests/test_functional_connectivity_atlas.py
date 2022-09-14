"""Provide test for parcel aggregation."""

# Authors: Amir Omidvarnia <a.omidvarnia@fz-juelich.de>
#          Kaustubh R. Patil <k.patil@fz-juelich.de>
# License: AGPL

from nilearn import datasets, image
from nilearn.maskers import NiftiLabelsMasker
from nilearn.connectome import ConnectivityMeasure
from numpy.testing import assert_array_almost_equal, assert_array_equal

from junifer.markers.parcel import ParcelAggregation
from junifer.markers.functional_connectivity_atlas \
    import FunctionalConnectivityAtlas


def test_FunctionalConnectivityAtlas() -> None:
    """Test FunctionalConnectivityAtlas."""

    # get a dataset
    ni_data = datasets.fetch_spm_auditory(subject_id='sub001')
    fmri_img = image.concat_imgs(ni_data.func)  # type: ignore

    fc = FunctionalConnectivityAtlas(atlas='Schaefer100x7')
    out = fc.compute({'data': fmri_img})

    assert 'data' in out
    assert 'row_names' in out
    assert 'col_names' in out
    assert out['data'].shape[0] == 100
    assert out['data'].shape[1] == 100
    assert len(set(out['row_names'])) == 100
    assert len(set(out['col_names'])) == 100

    # get the timeseries using pa
    pa = ParcelAggregation(atlas='Schaefer100x7', method='mean',
                           on="BOLD")
    ts = pa.compute({"data": fmri_img})

    # compare with nilearn
    # Get the testing atlas (for nilearn)
    atlas = datasets.fetch_atlas_schaefer_2018(n_rois=100, yeo_networks=7,
                                               resolution_mm=2)
    masker = NiftiLabelsMasker(labels_img=atlas['maps'], standardize=False)
    ts_ni = masker.fit_transform(fmri_img)

    # check the TS are almost equal
    assert_array_equal(ts_ni, ts['data'])

    # Check that FC are almost equal
    cm = ConnectivityMeasure(kind='covariance')
    out_ni = cm.fit_transform([ts_ni])[0]
    assert_array_almost_equal(out_ni, out['data'], decimal=3)
