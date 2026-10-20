"""Provide tests for generating the YAML from the metadata of a feature."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

import copy
import io
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import junifer.testing.registry  # noqa: F401
from junifer.api import collect, generate_yaml, parse_yaml, run
from junifer.api.functions import _component_config
from junifer.pipeline import PipelineComponentRegistry
from junifer.storage import HDF5FeatureStorage, SQLiteFeatureStorage
from junifer.storage.utils import _without_keys, get_dependency_version
from junifer.utils import yaml


_NOT_HASHED = ("_fields_set", "_with")
_PARCELLATION = "Schaefer100x7"
_MAPS = "Smith_rsn_10"
_COORDS = "DMNBuckner"
_PATTERNS = {
    "BOLD": {"pattern": "{subject}/bold.nii", "space": "MNI152NLin6Asym"}
}
_T1W_PATTERNS = {"T1w": {"pattern": "{subject}/t1w.nii", "space": "native"}}

# The parameters to create each built-in component
_COMPONENTS = {
    "datagrabber": {
        "DMCC13Benchmark": {"native_t1w": True},
        "DataladAOMICID1000": {"space": "native"},
        "DataladAOMICPIOP1": {"tasks": ["restingstate"]},
        "DataladAOMICPIOP2": {"tasks": ["restingstate"]},
        "DataladHCP1200": {"tasks": ["REST1"], "ica_fix": True},
        "HCP1200": {"tasks": ["REST1"], "ica_fix": True},
        "PatternDataGrabber": {
            "types": ["BOLD"],
            "patterns": _PATTERNS,
            "replacements": ["subject"],
        },
        "PatternDataladDataGrabber": {
            "types": ["BOLD"],
            "patterns": _PATTERNS,
            "replacements": ["subject"],
            "uri": "https://example.com/data.git",
        },
    },
    "preprocessing": {
        "Smoothing": {
            "on": "BOLD",
            "using": "nilearn",
            "smoothing_params": {"fwhm": 4},
        },
        "SpaceWarper": {
            "on": "BOLD",
            "using": "ants",
            "reference": "MNI152NLin6Asym",
        },
        "TemporalFilter": {"low_pass": 0.08},
        "TemporalSlicer": {"start": 0, "stop": 10},
        "fMRIPrepConfoundRemover": {"spike": 0.2},
    },
    "marker": {
        "ALFFMaps": {"using": "junifer", "maps": _MAPS},
        "ALFFParcels": {"using": "junifer", "parcellation": _PARCELLATION},
        "ALFFSpheres": {"using": "junifer", "coords": _COORDS, "radius": 5},
        "BrainPrint": {},
        "CrossParcellationFC": {
            "parcellation_one": _PARCELLATION,
            "parcellation_two": "TianxS1x3TxMNInonlinear2009cAsym",
        },
        "EdgeCentricFCMaps": {"maps": _MAPS},
        "EdgeCentricFCParcels": {"parcellation": _PARCELLATION},
        "EdgeCentricFCSpheres": {"coords": _COORDS, "radius": 5},
        "FunctionalConnectivityMaps": {"maps": _MAPS},
        "FunctionalConnectivityParcels": {
            "parcellation": _PARCELLATION,
            "conn_method_params": {"empirical": True},
        },
        "FunctionalConnectivitySpheres": {"coords": _COORDS, "radius": 5},
        "MapsAggregation": {"maps": _MAPS},
        "ParcelAggregation": {
            "parcellation": _PARCELLATION,
            "method": "mean",
            "on": "BOLD",
        },
        "RSSETSMarker": {"parcellation": _PARCELLATION},
        "ReHoMaps": {"using": "junifer", "maps": _MAPS},
        "ReHoParcels": {"using": "junifer", "parcellation": _PARCELLATION},
        "ReHoSpheres": {"using": "junifer", "coords": _COORDS, "radius": 5},
        "SphereAggregation": {"coords": _COORDS, "radius": 5},
        "TemporalSNRMaps": {"maps": _MAPS},
        "TemporalSNRParcels": {"parcellation": _PARCELLATION},
        "TemporalSNRSpheres": {"coords": _COORDS, "radius": 5},
    },
}


def _build(step: str, kind: str, params: dict) -> object:
    """Build a component, as from the YAML."""
    return PipelineComponentRegistry().build_component_instance(
        step=step, name=kind, baseclass=object, init_params=params
    )


def _meta(component: object) -> dict:
    """Get the metadata of a component."""
    data = {}
    component.update_meta(data, "step")  # type: ignore
    return data["meta"]["step"]


def test_all_builtin_components() -> None:
    """Test all the built-in components are tested."""
    # Abstract or tested elsewhere
    skip = {
        "BaseDataGrabber",
        "DataladDataGrabber",
        "MultipleDataGrabber",
        "BasePreprocessor",
        "BaseMarker",
    }
    registry = PipelineComponentRegistry()
    for step, components in _COMPONENTS.items():
        assert registry._builtins[step] - skip == set(components)


@pytest.mark.parametrize(
    "step, kind",
    [(step, kind) for step, kinds in _COMPONENTS.items() for kind in kinds],
)
def test_component_config(tmp_path: Path, step: str, kind: str) -> None:
    """Test the configuration of a component gives the same metadata.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    step : str
        The parametrized step of the component.
    kind : str
        The parametrized kind of component.

    """
    params = copy.deepcopy(_COMPONENTS[step][kind])
    if step == "datagrabber":
        params["datadir"] = tmp_path
    meta = _meta(_build(step, kind, copy.deepcopy(params)))
    issues = []
    config, with_ = _component_config(copy.deepcopy(meta), step, issues)
    assert issues == []
    assert with_ == []
    # Only the parameters set
    assert config.pop("kind") == kind
    assert set(config) == set(params)
    assert _meta(_build(step, kind, config)) == meta


def _feature_meta(**kwargs) -> dict:
    """Get the metadata of a feature of ParcelAggregation."""
    meta = {
        "datagrabber": {
            "class": "PatternDataGrabber",
            "_fields_set": ["types", "datadir", "patterns", "replacements"],
            "types": ["BOLD"],
            "datadir": "/data",
            "patterns": _PATTERNS,
            "replacements": ["subject"],
            "confounds_format": None,
        },
        "dependencies": {
            "junifer": get_dependency_version("junifer"),
            "nilearn": "0.14.1",
        },
        "_element_keys": ["subject"],
        "datareader": {"class": "DefaultDataReader", "_fields_set": []},
        "preprocess": [
            {
                "class": "TemporalSlicer",
                "_fields_set": ["start", "stop"],
                "start": 0,
                "stop": 10.0,
                "on": None,
            }
        ],
        "type": "BOLD",
        "marker": {
            "class": "ParcelAggregation",
            "_fields_set": ["parcellation", "method", "name"],
            "name": "mean_aggregation",
            "parcellation": [_PARCELLATION],
            "method": "mean",
            "on": ["BOLD"],
        },
        "name": "BOLD_mean_aggregation",
    }
    meta.update(kwargs)
    return meta


def _dump(config: dict) -> str:
    """Dump a YAML to a string."""
    stream = io.StringIO()
    yaml.dump(config, stream)
    return stream.getvalue()


def test_generate_yaml() -> None:
    """Test generating the YAML of a feature."""
    out = generate_yaml(_feature_meta())
    assert out == {
        "workdir": "",
        "datagrabber": {
            "kind": "PatternDataGrabber",
            "types": ["BOLD"],
            "datadir": "/data",
            "patterns": _PATTERNS,
            "replacements": ["subject"],
        },
        "preprocess": [{"kind": "TemporalSlicer", "start": 0, "stop": 10.0}],
        "markers": [
            {
                "kind": "ParcelAggregation",
                "parcellation": [_PARCELLATION],
                "method": "mean",
                "name": "mean",
            }
        ],
        "storage": {"kind": "HDF5FeatureStorage", "uri": ""},
    }
    text = _dump(out)
    assert "# Auto-generated by junifer" in text
    assert "BOLD_mean_aggregation" in text
    assert "#   nilearn==0.14.1" in text
    assert "datagrabber.datadir" in text
    # Computed with the same version of junifer
    assert "Notes" not in text
    assert "Issues" not in text
    # Other storage
    out = generate_yaml(_feature_meta(), storage_kind="SQLiteFeatureStorage")
    assert out["storage"]["kind"] == "SQLiteFeatureStorage"


@pytest.mark.parametrize(
    "kind, data_type, name, expected",
    [
        ("ParcelAggregation", "BOLD", "mean_aggregation", "mean"),
        ("ParcelAggregation", "T1w", "mean_aggregation", "mean"),
        # The default name
        ("ParcelAggregation", "BOLD", "ParcelAggregation_aggregation", None),
        # Several outputs
        ("ALFFParcels", "BOLD", "lff_alff", "lff"),
        ("ALFFParcels", "BOLD", "lff_falff", "lff"),
        # The name of the marker ends with the name of the output
        ("ALFFParcels", "BOLD", "falff_falff", "falff"),
        (
            "FunctionalConnectivityParcels",
            "BOLD",
            "fc_functional_connectivity",
            "fc",
        ),
    ],
)
def test_generate_yaml_marker_name(
    kind: str, data_type: str, name: str, expected: str | None
) -> None:
    """Test the name of the marker, without the name of the feature.

    Parameters
    ----------
    kind : str
        The parametrized kind of marker.
    data_type : str
        The parametrized data type of the feature.
    name : str
        The parametrized name of the marker in the metadata.
    expected : str or None
        The parametrized name of the marker in the YAML (None if the
        default).

    """
    marker = {"class": kind, "name": name, "parcellation": [_PARCELLATION]}
    # The name is set unless it is the default one
    marker["_fields_set"] = ["parcellation"] + (
        ["name"] if expected is not None else []
    )
    out = generate_yaml(_feature_meta(marker=marker, type=data_type))
    if expected is None:
        assert "name" not in out["markers"][0]
    else:
        assert out["markers"][0]["name"] == expected


def test_generate_yaml_unknown_marker() -> None:
    """Test the name of a marker that is not available."""
    marker = {
        "class": "MyMarker",
        "_fields_set": ["name"],
        "name": "foo_bar",
    }
    out = generate_yaml(_feature_meta(marker=marker))
    assert out["markers"][0] == {"kind": "MyMarker", "name": "foo_bar"}
    assert "with" not in out
    text = _dump(out)
    assert "`MyMarker` is not a built-in component" in text
    assert "remove the name of the feature from `foo_bar`" in text


def test_generate_yaml_with() -> None:
    """Test the modules to load the components that are not built-in."""
    meta = _feature_meta()
    meta["datagrabber"] = {
        "class": "PartlyCloudyTestingDataGrabber",
        "_fields_set": ["n_timepoints"],
        "_with": "junifer.testing.registry",
        "n_timepoints": 5,
    }
    meta["preprocess"][0]["_with"] = "/path/to/my_preprocessors.py"
    meta["marker"]["_with"] = "junifer.testing.registry"
    out = generate_yaml(meta)
    # Once each
    assert out["with"] == [
        "junifer.testing.registry",
        "/path/to/my_preprocessors.py",
    ]
    assert out["datagrabber"] == {
        "kind": "PartlyCloudyTestingDataGrabber",
        "n_timepoints": 5,
    }
    assert "Issues" not in _dump(out)
    # Without the module (e.g., junifer <= 0.0.8)
    del meta["datagrabber"]["_with"]
    out = generate_yaml(meta)
    assert "junifer.testing.registry" in out["with"]
    assert "`PartlyCloudyTestingDataGrabber` is not a built-in" in _dump(out)


@pytest.mark.parametrize("dirty", [False, True])
def test_generate_yaml_datalad(dirty: bool) -> None:
    """Test the YAML of a feature computed with a datalad dataset.

    Parameters
    ----------
    dirty : bool
        The parametrized state of the datalad dataset.

    """
    meta = _feature_meta()
    meta["datagrabber"] = {
        "class": "PatternDataladDataGrabber",
        "_fields_set": ["types", "patterns", "replacements", "uri"],
        "types": ["BOLD"],
        "patterns": _PATTERNS,
        "replacements": ["subject"],
        "uri": "https://example.com/data.git",
        "rootdir": ".",
        "datalad_dirty": dirty,
        "datalad_commit_id": "abc123",
        "datalad_id": "my-dataset-id",
    }
    out = generate_yaml(meta)
    # The state of the dataset is not a parameter
    assert out["datagrabber"] == {
        "kind": "PatternDataladDataGrabber",
        "types": ["BOLD"],
        "patterns": _PATTERNS,
        "replacements": ["subject"],
        "uri": "https://example.com/data.git",
    }
    text = _dump(out)
    assert "my-dataset-id at commit abc123" in text
    assert ("no strict data provenance" in text) == dirty
    # No datadir to set
    assert "datagrabber.datadir" not in text


def test_generate_yaml_multiple_datagrabber() -> None:
    """Test the YAML of a feature computed with a MultipleDataGrabber."""
    meta = _feature_meta()
    meta["datagrabber"] = {
        "class": "MultipleDataGrabber",
        "_fields_set": ["datagrabbers"],
        "types": ["BOLD", "T1w"],
        "datagrabbers": [
            {
                "class": "PatternDataGrabber",
                "_fields_set": [
                    "types",
                    "patterns",
                    "replacements",
                    "datadir",
                ],
                "types": ["T1w"],
                "patterns": _T1W_PATTERNS,
                "replacements": ["subject"],
                "datadir": "/data",
            },
            {
                "class": "PatternDataGrabber",
                "_fields_set": [
                    "types",
                    "patterns",
                    "replacements",
                    "datadir",
                ],
                "_with": "my.datagrabbers",
                "types": ["BOLD"],
                "patterns": _PATTERNS,
                "replacements": ["subject"],
                "datadir": "/data",
            },
        ],
    }
    out = generate_yaml(meta)
    # The modules of the nested components
    assert out["with"] == ["my.datagrabbers"]
    assert "Issues" not in _dump(out)
    assert out["datagrabber"] == {
        "kind": "MultipleDataGrabber",
        "datagrabbers": [
            {
                "kind": "PatternDataGrabber",
                "types": ["T1w"],
                "patterns": _T1W_PATTERNS,
                "replacements": ["subject"],
                "datadir": "/data",
            },
            {
                "kind": "PatternDataGrabber",
                "types": ["BOLD"],
                "patterns": _PATTERNS,
                "replacements": ["subject"],
                "datadir": "/data",
            },
        ],
    }


def test_generate_yaml_without_preprocessors() -> None:
    """Test the YAML of a feature computed without preprocessors."""
    meta = _feature_meta()
    del meta["preprocess"]
    assert "preprocess" not in generate_yaml(meta)


@pytest.mark.parametrize("step", ["datagrabber", "preprocess", "marker"])
def test_generate_yaml_incompatible(step: str) -> None:
    """Test the YAML of a feature computed with junifer <= 0.0.8.

    The parameters set to create the components are not known, so the YAML
    cannot be generated.

    Parameters
    ----------
    step : str
        The parametrized step without the parameters set.

    """
    meta = _feature_meta()
    meta["dependencies"]["junifer"] = "0.0.8"
    if step == "preprocess":
        del meta["preprocess"][0]["_fields_set"]
    else:
        del meta[step]["_fields_set"]
    with pytest.raises(ValueError, match=r"computed with junifer 0\.0\.8"):
        generate_yaml(meta)


def test_generate_yaml_incompatible_single_preprocessor() -> None:
    """Test the YAML of a feature with a single preprocessor (junifer < 0.0.8).

    The metadata of the preprocessors was a dictionary (only the last one).

    """
    meta = _feature_meta()
    meta["preprocess"] = meta["preprocess"][0]
    with pytest.raises(ValueError, match="cannot be generated"):
        generate_yaml(meta)


def test_generate_yaml_failed_to_instantiate() -> None:
    """Test a component that cannot be created with its parameters.

    For example, with metadata of another version of junifer, in which the
    parameters of the component changed.

    """
    meta = _feature_meta()
    meta["marker"]["_fields_set"].append("aggregation")
    meta["marker"]["aggregation"] = "mean"
    out = generate_yaml(meta)
    # All the parameters
    assert out["markers"][0] == {
        "kind": "ParcelAggregation",
        "name": "mean",
        "parcellation": [_PARCELLATION],
        "method": "mean",
        "on": ["BOLD"],
        "aggregation": "mean",
    }
    text = _dump(out)
    assert "`ParcelAggregation` failed to instantiate with junifer" in text
    assert "Extra inputs are not permitted" in text


def test_generate_yaml_junifer_version() -> None:
    """Test the note about the version of junifer of the feature."""
    meta = _feature_meta()
    meta["dependencies"]["junifer"] = "0.0.5"
    text = _dump(generate_yaml(meta))
    assert "computed with junifer 0.0.5: check the components" in text


@pytest.fixture
def my_marker(tmp_path: Path) -> Iterator[Path]:
    """Write a marker to load with ``with`` in the YAML.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    path = tmp_path / "my_marker.py"
    path.write_text(
        "from junifer.api.decorators import register_marker\n"
        "from junifer.markers import ParcelAggregation\n\n\n"
        "@register_marker\n"
        "class MyParcelAggregation(ParcelAggregation):\n"
        '    """Parcel aggregation loaded from a file."""\n'
    )
    yield path
    registry = PipelineComponentRegistry()
    if "MyParcelAggregation" in registry.step_components("marker"):
        registry.deregister(
            step="marker",
            klass=registry.get_class(
                step="marker", name="MyParcelAggregation"
            ),
        )


def _run(config_path: Path) -> None:
    """Run a YAML and collect its features, as from the command line."""
    config = parse_yaml(config_path)
    run(
        workdir=config["workdir"],
        datagrabber=config["datagrabber"],
        markers=config["markers"],
        storage=config["storage"],
        preprocessors=config.get("preprocess"),
        elements=["sub-01"],
    )
    collect(storage=config["storage"])


def _features(storage: HDF5FeatureStorage | SQLiteFeatureStorage) -> dict:
    """Get the metadata and data of the features of a storage."""
    return {
        md5: (meta, storage.read_df(feature_md5=md5))
        for md5, meta in storage.list_features().items()
    }


@pytest.mark.parametrize(
    "storage_kind, suffix",
    [("HDF5FeatureStorage", "hdf5"), ("SQLiteFeatureStorage", "sqlite")],
)
def test_generate_yaml_run(
    tmp_path: Path, my_marker: Path, storage_kind: str, suffix: str
) -> None:
    """Test computing the features again with the YAML of each feature.

    The features are the same: same MD5, name, metadata and data.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.
    my_marker : pathlib.Path
        The path to a marker to load with ``with``.
    storage_kind : str
        The parametrized kind of storage.
    suffix : str
        The parametrized suffix of the storage file.

    """
    parcellation = "TianxS1x3TxMNInonlinear2009cAsym"
    config = {
        "workdir": str(tmp_path / "work"),
        "with": ["junifer.testing.registry", my_marker.name],
        "datagrabber": {
            "kind": "PartlyCloudyTestingDataGrabber",
            "datadir": str(tmp_path / "data"),
            "n_subjects": 1,
            "n_timepoints": 30,
        },
        "preprocess": [{"kind": "TemporalSlicer", "start": 0, "stop": 25}],
        "markers": [
            {
                "name": "tian_mean",
                "kind": "ParcelAggregation",
                "parcellation": parcellation,
                "method": "mean",
            },
            # Several outputs
            {
                "name": "tian_lff",
                "kind": "ALFFParcels",
                "using": "junifer",
                "parcellation": parcellation,
            },
            # Loaded from a file, with the default name
            {"kind": "MyParcelAggregation", "parcellation": parcellation},
        ],
        "storage": {"kind": storage_kind, "uri": f"features.{suffix}"},
    }
    config_path = tmp_path / "config.yaml"
    yaml.dump(config, config_path)
    _run(config_path)
    klass = HDF5FeatureStorage if suffix == "hdf5" else SQLiteFeatureStorage
    features = _features(klass(uri=tmp_path / f"features.{suffix}"))
    assert len(features) == 4

    for i, (md5, (meta, data)) in enumerate(features.items()):
        out = generate_yaml(copy.deepcopy(meta), storage_kind)
        assert "Issues" not in _dump(out)
        t_dir = tmp_path / f"run_{i}"
        t_dir.mkdir()
        out["workdir"] = str(t_dir / "work")
        out["storage"]["uri"] = f"features.{suffix}"
        yaml.dump(out, t_dir / "config.yaml")
        _run(t_dir / "config.yaml")
        t_features = _features(klass(uri=t_dir / f"features.{suffix}"))
        # The feature of the marker, with the same metadata and data (other
        # features of the marker, if any, are also computed)
        assert md5 in t_features
        t_meta, t_data = t_features[md5]
        assert t_meta == meta
        pd.testing.assert_frame_equal(t_data, data)
        assert np.isfinite(t_data.to_numpy()).any()
        # Without the parameters set (junifer <= 0.0.8), it is not generated
        with pytest.raises(ValueError, match="cannot be generated"):
            generate_yaml(_without_keys(meta, _NOT_HASHED), storage_kind)

    # Another parameter gives another feature
    md5, (meta, _) = next(iter(features.items()))
    out = generate_yaml(copy.deepcopy(meta), storage_kind)
    out["preprocess"][0]["stop"] = 20
    t_dir = tmp_path / "run_changed"
    t_dir.mkdir()
    out["workdir"] = str(t_dir / "work")
    out["storage"]["uri"] = f"features.{suffix}"
    yaml.dump(out, t_dir / "config.yaml")
    _run(t_dir / "config.yaml")
    t_features = _features(klass(uri=t_dir / f"features.{suffix}"))
    assert md5 not in t_features
    assert meta["name"] in {
        t_meta["name"] for t_meta, _ in t_features.values()
    }
