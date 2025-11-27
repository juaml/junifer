"""Provide tests for DataladAOMICPIOP1 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Optional, Union

import pytest
from pydantic import HttpUrl

from junifer.datagrabber import DataladAOMICPIOP1


URI = HttpUrl("https://gin.g-node.org/juaml/datalad-example-aomicpiop1")


@pytest.mark.parametrize(
    "type_, nested_types, tasks, space",
    [
        (
            "BOLD",
            ["confounds", "mask", "reference"],
            "anticipation",
            "MNI152NLin2009cAsym",
        ),
        (
            ["BOLD"],
            ["confounds", "mask", "reference"],
            ["emomatching", "faces"],
            "MNI152NLin2009cAsym",
        ),
        (
            "BOLD",
            ["confounds", "mask", "reference"],
            "restingstate",
            "MNI152NLin2009cAsym",
        ),
        (
            ["BOLD"],
            ["confounds", "mask", "reference"],
            ["workingmemory", "gstroop"],
            "MNI152NLin2009cAsym",
        ),
        (
            ["BOLD"],
            ["confounds", "mask", "reference"],
            ["anticipation", "faces", "restingstate"],
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
def test_DataladAOMICPIOP1(
    type_: Union[str, list[str]],
    nested_types: Optional[list[str]],
    tasks: Union[str, list[str]],
    space: str,
) -> None:
    """Test DataladAOMICPIOP1 DataGrabber.

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

    """
    dg = DataladAOMICPIOP1(uri=URI, types=type_, tasks=tasks, space=space)
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
                # Depending on task 'acquisition is different'
                task_acqs = {
                    "anticipation": "seq",
                    "emomatching": "seq",
                    "faces": "mb3",
                    "gstroop": "seq",
                    "restingstate": "mb3",
                    "workingmemory": "seq",
                }
                assert task_acqs[test_element[1]] in out[t]["path"].name
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
def test_DataladAOMICPIOP1_partial_data_access(
    types: Union[str, list[str]],
) -> None:
    """Test DataladAOMICPIOP1 DataGrabber partial data access.

    Parameters
    ----------
    types : str or list of str
        The parametrized types.

    """
    dg = DataladAOMICPIOP1(uri=URI, types=types)
    with dg:
        all_elements = dg.get_elements()
        test_element = all_elements[0]
        out = dg[test_element]
        # Assert data type
        if isinstance(types, str):
            types = [types]
        for t in types:
            assert t in out
