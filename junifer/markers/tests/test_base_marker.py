import pytest
from junifer.markers.base import BaseMarker, PipelineStepMixin


def test_pipelinestepmixing():
    mixin = PipelineStepMixin()
    with pytest.raises(NotImplementedError):
        mixin.validate_input(None)
    with pytest.raises(NotImplementedError):
        mixin.get_output_kind(None)
    with pytest.raises(NotImplementedError):
        mixin.fit_transform(None)


def test_meta():
    """Test metadata"""
    pipemixin = PipelineStepMixin()
    t_meta = pipemixin.get_meta()
    assert t_meta['class'] == 'PipelineStepMixin'

    base = BaseMarker(on=['bold', 'dwi'])

    t_meta = base.get_meta()
    assert t_meta['marker']['class'] == 'BaseMarker'
    assert t_meta['marker']['name'] == 'BaseMarker'

    base = BaseMarker(on=['bold', 'dwi'], name='mymarker')

    t_meta = base.get_meta()
    assert t_meta['marker']['name'] == 'mymarker'


def test_base():
    """Test base class"""
    base = BaseMarker(on=['bold', 'dwi'], name='mymarker')
    input = {'bold': {'path': 'test'}, 't2': {'path': 'test'}}
    base.validate_input(input)

    wrong_input = {'t2': {'path': 'test'}}
    with pytest.raises(ValueError):
        base.validate_input(wrong_input)

    output = base.get_output_kind(input)
    assert output is None

    with pytest.raises(NotImplementedError):
        base.fit_transform(input)

    base.compute = lambda x: dict(data=1)  # type: ignore

    out = base.fit_transform(input)
    assert out['bold']['data'] == 1
    assert out['bold']['meta']['marker']['name'] == 'mymarker'
    assert out['bold']['meta']['marker']['class'] == 'BaseMarker'

    base2 = BaseMarker(on='bold', name='mymarker')
    base2.compute = lambda x: dict(data=1)  # type: ignore
    out2 = base2.fit_transform(input)
    assert out2['bold']['data'] == 1
    assert out2['bold']['meta']['marker']['name'] == 'mymarker'
    assert out2['bold']['meta']['marker']['class'] == 'BaseMarker'
