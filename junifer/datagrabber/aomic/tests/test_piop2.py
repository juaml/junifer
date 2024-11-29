"""Provide tests DataladAOMICPIOP2 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Optional, Union

import pytest

from junifer.datagrabber import DataladAOMICPIOP2


URI = "https://gin.g-node.org/juaml/datalad-example-aomicpiop2"


@pytest.mark.parametrize(
    "type_, nested_types, tasks, space",
    [
        (
            "BOLD",
            ["confounds", "mask", "reference"],
            None,
            "MNI152NLin2009cAsym",
        ),
        ("BOLD", ["confounds", "mask", "reference"], None, "native"),
        (
            "BOLD",
            ["confounds", "mask", "reference"],
            ["restingstate"],
            "MNI152NLin2009cAsym",
        ),
        (
            "BOLD",
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
            "BOLD",
            ["confounds", "mask", "reference"],
            ["workingmemory"],
            "MNI152NLin2009cAsym",
        ),
        ("T1w", ["mask"], None, "MNI152NLin2009cAsym"),
        ("T1w", ["mask"], None, "native"),
        ("VBM_CSF", None, None, "MNI152NLin2009cAsym"),
        ("VBM_CSF", None, None, "native"),
        ("VBM_GM", None, None, "MNI152NLin2009cAsym"),
        ("VBM_GM", None, None, "native"),
        ("VBM_WM", None, None, "MNI152NLin2009cAsym"),
        ("VBM_WM", None, None, "native"),
        ("DWI", None, None, "MNI152NLin2009cAsym"),
        ("FreeSurfer", None, None, "MNI152NLin2009cAsym"),
    ],
)
def test_DataladAOMICPIOP2(
    type_: str,
    nested_types: Optional[list[str]],
    tasks: Optional[list[str]],
    space: str,
) -> None:
    """Test DataladAOMICPIOP2 DataGrabber.

    Parameters
    ----------
    type_ : str
        The parametrized type.
    nested_types : list of str or None
        The parametrized nested types.
    tasks : list of str or None
        The parametrized task values.
    space: str
        The parametrized space.

    """
    dg = DataladAOMICPIOP2(types=type_, tasks=tasks, space=space)
    # Set URI to Gin
    dg.uri = URI

    with dg:
        # Get all elements
        all_elements = dg.get_elements()
        # Get test element
        test_element = all_elements[0]
        # Get test element data
        out = dg[test_element]
        # Assert data type
        assert type_ in out
        # Check task name if BOLD
        if type_ == "BOLD" and tasks is not None:
            assert test_element[1] in out[type_]["path"].name
        assert out[type_]["path"].exists()
        assert out[type_]["path"].is_file()
        # Asserts data type metadata
        assert "meta" in out[type_]
        meta = out[type_]["meta"]
        assert "element" in meta
        assert "subject" in meta["element"]
        assert test_element[0] == meta["element"]["subject"]
        # Assert nested data type if not None
        if nested_types is not None:
            for nested_type in nested_types:
                assert out[type_][nested_type]["path"].exists()
                assert out[type_][nested_type]["path"].is_file()


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
    types: Union[str, list[str]],
) -> None:
    """Test DataladAOMICPIOP2 DataGrabber partial data access.

    Parameters
    ----------
    types : str or list of str
        The parametrized types.

    """
    dg = DataladAOMICPIOP2(types=types)
    # Set URI to Gin
    dg.uri = URI

    with dg:
        # Get all elements
        all_elements = dg.get_elements()
        # Get test element
        test_element = all_elements[0]
        # Get test element data
        out = dg[test_element]
        # Assert data type
        if isinstance(types, list):
            for type_ in types:
                assert type_ in out
        else:
            assert types in out


def test_DataladAOMICPIOP2_incorrect_data_type() -> None:
    """Test DataladAOMICPIOP2 DataGrabber incorrect data type."""
    with pytest.raises(
        ValueError, match="`patterns` must contain all `types`"
    ):
        _ = DataladAOMICPIOP2(types="Vesta")


def test_DataladAOMICPIOP2_invalid_tasks():
    """Test DataladAOMICIDPIOP2 DataGrabber invalid tasks."""
    with pytest.raises(
        ValueError,
        match=(
            "thisisnotarealtask is not a valid task in "
            "the AOMIC PIOP2 dataset!"
        ),
    ):
        DataladAOMICPIOP2(tasks="thisisnotarealtask")
