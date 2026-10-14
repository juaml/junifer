"""Provide test for registering the complexity markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import subprocess
import sys
from pathlib import Path

import pytest


pytest.importorskip("neurokit2")


def test_complexity_markers_with(tmp_path: Path) -> None:
    """Test the complexity markers are registered with ``with:``.

    It runs in a new Python process, so the markers are not registered by
    other tests.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    names = [
        "HurstExponent",
        "MultiscaleEntropyAUC",
        "PermEntropy",
        "RangeEntropy",
        "RangeEntropyAUC",
        "SampleEntropy",
        "WeightedPermEntropy",
    ]
    yaml_path = tmp_path / "config.yaml"
    script = (
        "from junifer.api.functions import parse_yaml\n"
        "from junifer.pipeline import PipelineComponentRegistry\n"
        "registry = PipelineComponentRegistry()\n"
        f"assert 'HurstExponent' not in registry.step_components('marker')\n"
        f"parse_yaml({str(yaml_path)!r})\n"
        f"for name in {names!r}:\n"
        "    registry.get_class('marker', name)\n"
    )
    yaml_path.write_text("with: junifer.markers.complexity\n")
    subprocess.run([sys.executable, "-c", script], check=True)
