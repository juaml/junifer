"""Provide tests DataladAOMICPIOP2 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import AnyUrl

from junifer.datagrabber import DataladAOMICPIOP2
from junifer.utils import config


URI = AnyUrl(
    "https://cerebra.fz-juelich.de/junifer/datalad-example-aomicpiop2"
)


@pytest.fixture(scope="session")
def aomic_datadir(tmp_path_factory) -> Iterator[Path]:
    """Return the path to the AOMIC data directory.

    Parameters
    ----------
    tmp_path_factory : pathlib.Path
        The path to the test directory.

    Returns
    -------
    pathlib.Path
        The path to the AOMIC data directory.

    """
    datadir = tmp_path_factory.mktemp("aomic_data")
    datadir.mkdir(parents=True, exist_ok=True)
    config.set("datagrabber.skipidcheck", True)
    dg = DataladAOMICPIOP2(uri=URI, types=["T1w"], datadir=datadir)
    with dg:
        yield datadir
    config.set("datagrabber.skipidcheck", False)


@pytest.mark.parametrize(
    "type_, nested_types, tasks, space",
    [
        (
            "BOLD",
            ["confounds", "mask", "reference"],
            "restingstate",
            "MNI152NLin2009cAsym",
        ),
        (
            ["BOLD"],
            ["confounds", "mask", "reference"],
            ["restingstate", "stopsignal"],
            "MNI152NLin2009cAsym",
        ),
        (
            "BOLD",
            ["confounds", "mask", "reference"],
            ["workingmemory", "stopsignal"],
            "MNI152NLin2009cAsym",
        ),
        (
            ["BOLD"],
            ["confounds", "mask", "reference"],
            "workingmemory",
            "MNI152NLin2009cAsym",
        ),
        (["T1w"], ["mask"], "restingstate", "MNI152NLin2009cAsym"),
        ("T1w", ["mask"], ["restingstate"], "native"),
        (["VBM_CSF"], None, "restingstate", "MNI152NLin2009cAsym"),
        ("VBM_CSF", None, ["restingstate"], "native"),
        (["VBM_GM"], None, "restingstate", "MNI152NLin2009cAsym"),
        ("VBM_GM", None, ["restingstate"], "native"),
        (["VBM_WM"], None, "restingstate", "MNI152NLin2009cAsym"),
        ("VBM_WM", None, ["restingstate"], "native"),
        (["DWI"], None, "restingstate", "MNI152NLin2009cAsym"),
        (["FreeSurfer"], None, ["restingstate"], "MNI152NLin2009cAsym"),
    ],
)
def test_DataladAOMICPIOP2(
    type_: str | list[str],
    nested_types: list[str] | None,
    tasks: str | list[str],
    space: str,
    aomic_datadir: Path,
) -> None:
    """Test DataladAOMICPIOP2 DataGrabber.

    Parameters
    ----------
    type_ : str or list of str
        The parametrized type.
    nested_types : list of str or None
        The parametrized nested types.
    tasks : str or list of str
        The parametrized task values.
    space: str
        The parametrized space.
    aomic_datadir: Path
        The path to the AOMIC data directory.

    """
    dg = DataladAOMICPIOP2(
        uri=URI, types=type_, tasks=tasks, space=space, datadir=aomic_datadir
    )
    with dg:
        all_elements = dg.get_elements()
        test_element = all_elements[0]
        out = dg[test_element]
        # Assert data type
        if isinstance(type_, str):
            type_ = [type_]
        for t in type_:
            assert t in out
            # Check task name if BOLD
            if t == "BOLD":
                assert test_element[1] in out[t]["path"].name
            assert out[t]["path"].exists()
            assert out[t]["path"].is_file()
            # Asserts data type metadata
            assert "meta" in out[t]
            meta = out[t]["meta"]
            assert "element" in meta
            assert "subject" in meta["element"]
            assert test_element[0] == meta["element"]["subject"]
            # Assert nested data type if not None
            if nested_types is not None:
                for nested_type in nested_types:
                    assert out[t][nested_type]["path"].exists()
                    assert out[t][nested_type]["path"].is_file()


@pytest.mark.parametrize(
    "types",
    [
        "BOLD",
        "T1w",
        "VBM_CSF",
        "VBM_GM",
        "VBM_WM",
        "DWI",
        ["BOLD", "VBM_CSF"],
        ["T1w", "VBM_CSF"],
        ["VBM_GM", "VBM_WM"],
        ["DWI", "BOLD"],
    ],
)
def test_DataladAOMICPIOP2_partial_data_access(
    types: str | list[str],
    aomic_datadir: Path,
) -> None:
    """Test DataladAOMICPIOP2 DataGrabber partial data access.

    Parameters
    ----------
    types : str or list of str
        The parametrized types.
    aomic_datadir : pathlib.Path
        The path to the AOMIC data directory.

    """
    dg = DataladAOMICPIOP2(uri=URI, types=types, datadir=aomic_datadir)
    with dg:
        all_elements = dg.get_elements()
        test_element = all_elements[0]
        out = dg[test_element]
        # Assert data type
        if isinstance(types, str):
            types = [types]
        for t_ in types:
            assert t_ in out
