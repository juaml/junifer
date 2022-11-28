"""Provide tests for pipeline mixin."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import pytest

from junifer.pipeline.pipeline_step_mixin import PipelineStepMixin


def test_PipelineStepMixin() -> None:
    """Test PipelineStepMixin."""
    mixin = PipelineStepMixin()
    with pytest.raises(NotImplementedError):
        mixin.validate_input([])
    with pytest.raises(NotImplementedError):
        mixin.get_output_type("")
    with pytest.raises(NotImplementedError):
        mixin.fit_transform({})
