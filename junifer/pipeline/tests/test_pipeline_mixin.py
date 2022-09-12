"""Provide tests for pipeline mixin."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from junifer.pipeline.pipeline_mixin import PipelineStepMixin


def test_PipelineStepMixin() -> None:
    """Test PipelineStepMixin."""
    mixin = PipelineStepMixin()
    with pytest.raises(NotImplementedError):
        mixin.validate_input([])
    with pytest.raises(NotImplementedError):
        mixin.get_output_kind([])
    with pytest.raises(NotImplementedError):
        mixin.fit_transform({})


def test_pipeline_step_mixin_meta():
    """Test metadata for PipelineStepMixin."""
    pipemixin = PipelineStepMixin()
    t_meta = pipemixin.get_meta()
    assert t_meta["class"] == "PipelineStepMixin"
