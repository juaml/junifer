import tempfile
import pytest
from numpy.testing import assert_array_equal

from junifer.data.atlases import register_atlas, list_atlases, load_atlas


def test_register_atlas():
    """Test register_atlas"""

    atlases = list_atlases()
    assert 'testatlas' not in atlases

    register_atlas('testatlas', 'testatlas.nii.gz', ['1', '2', '3'])

    atlases = list_atlases()
    assert 'testatlas' in atlases

    _, lbl, fname = load_atlas('testatlas', path_only=True)

    assert lbl == ['1', '2', '3']
    assert fname.name == 'testatlas.nii.gz'  # type: ignore

    with pytest.raises(ValueError, match=r"already registered."):
        register_atlas('testatlas', 'testatlas.nii.gz',  ['1', '2', '3'])

    with pytest.raises(ValueError, match=r"built-in atlas"):
        register_atlas('SUITxSUIT', 'testatlas.nii.gz', ['1', '2', '3'],
                       overwrite=True)

    register_atlas('testatlas', 'testatlas_2.nii.gz', ['1', '2', '6'],
                   overwrite=True)

    _, lbl, fname = load_atlas('testatlas', path_only=True)

    assert lbl == ['1', '2', '6']
    assert fname.name == 'testatlas_2.nii.gz'  # type: ignore


def test_schaefer_atlas():
    """Test Schaefer atlas"""

    atlases = list_atlases()

    for n_rois in range(100, 1001, 100):
        for t_net in [7, 17]:
            t_name = f'Schaefer{n_rois}x{t_net}'
            assert t_name in atlases

    with tempfile.TemporaryDirectory() as tmpdir:
        fname1 = 'Schaefer2018_100Parcels_7Networks_order_FSLMNI152_1mm.nii.gz'
        fname2 = 'Schaefer2018_100Parcels_7Networks_order_FSLMNI152_1mm.nii.gz'

        img, lbl, fname = load_atlas('Schaefer100x7', atlas_dir=tmpdir)

        assert img is not None
        assert fname.name == fname1  # type: ignore

        assert len(lbl) == 100
        assert_array_equal(img.header['pixdim'][1:4], [1, 1, 1])

        img2, lbl, fname = load_atlas(
            'Schaefer100x7', atlas_dir=tmpdir, resolution=3)
        assert fname.name == fname2  # type: ignore
        assert len(lbl) == 100
        assert img2 is not None
        assert_array_equal(img2.header['pixdim'][1:4], [2, 2, 2])

        img2, lbl, fname = load_atlas(
            'Schaefer100x7', atlas_dir=tmpdir, resolution=2.1)
        assert fname.name == fname2  # type: ignore
        assert len(lbl) == 100
        assert img2 is not None
        assert_array_equal(img2.header['pixdim'][1:4], [2, 2, 2])

        img2, lbl, fname = load_atlas(
            'Schaefer100x7', atlas_dir=tmpdir, resolution=1.99)
        assert fname.name == fname1  # type: ignore
        assert len(lbl) == 100
        assert img2 is not None
        assert_array_equal(img2.header['pixdim'][1:4], [1, 1, 1])


def test_suit():
    """Test SUIT atlas"""

    atlases = list_atlases()
    assert 'SUITxSUIT' in atlases
    assert 'SUITxMNI' in atlases

    with tempfile.TemporaryDirectory() as tmpdir:
        img, lbl, fname = load_atlas('SUITxSUIT', atlas_dir=tmpdir)
        fname1 = 'SUIT_SUITSpace_1mm.nii'
        assert img is not None
        assert fname.name == fname1  # type: ignore
        assert len(lbl) == 34
        assert_array_equal(img.header['pixdim'][1:4], [1, 1, 1])

        img, lbl, fname = load_atlas('SUITxSUIT', atlas_dir=tmpdir)
        fname1 = 'SUIT_SUITSpace_1mm.nii'
        assert img is not None
        assert fname.name == fname1  # type: ignore
        assert len(lbl) == 34
        assert_array_equal(img.header['pixdim'][1:4], [1, 1, 1])
