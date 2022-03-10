# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import pytest
from junifer.datareader.default import DefaultDataReader
from junifer.markers import MarkerCollection, ParcelAggregation
from junifer.testing import OasisVBMTestingDatagrabber


def test_markercollection():
    """Test MarkerCollection"""
    wrong_markers = [
        ParcelAggregation(
            atlas='Schaefer100x7', method='mean',
            name='gmd_schaefer100x7_mean'),
        ParcelAggregation(
            atlas='Schaefer100x7', method='mean',
            name='gmd_schaefer100x7_mean'),
    ]

    with pytest.raises(ValueError, match=r"must have different names"):
        MarkerCollection(wrong_markers)

    markers = [
        ParcelAggregation(
            atlas='Schaefer100x7', method='mean',
            name='gmd_schaefer100x7_mean'),
        ParcelAggregation(
            atlas='Schaefer100x7', method='std',
            name='gmd_schaefer100x7_std'),
        ParcelAggregation(
            atlas='Schaefer100x7', method='trim_mean',
            method_params={'proportiontocut': 0.1},
            name='gmd_schaefer100x7_trim_mean90')
    ]
    mc = MarkerCollection(markers=markers)
    assert mc._markers == markers
    assert mc._preprocessing is None
    assert mc._storage is None
    assert isinstance(mc._datareader, DefaultDataReader)

    dg = OasisVBMTestingDatagrabber()
    mc.validate(dg)

    with dg:
        input = dg[1]
        out = mc.fit(input)
        assert out is not None
        assert isinstance(out, dict)
        assert len(out) == 3
        assert 'gmd_schaefer100x7_mean' in out
        assert 'gmd_schaefer100x7_std' in out
        assert 'gmd_schaefer100x7_trim_mean90' in out

        for t_marker in markers:
            t_name = t_marker.name
            assert 'VBM_GM' in out[t_name]
            t_vbm = out[t_name]['VBM_GM']
            assert 'data' in t_vbm
            assert 'columns' in t_vbm
            assert 'meta' in t_vbm
