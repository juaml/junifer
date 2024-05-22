"""Provide tests for DataladAOMICID1000 DataGrabber."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Vera Komeyer <v.komeyer@fz-juelich.de>
#          Xuan Li <xu.li@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import List, Optional, Union

import pytest

from junifer.datagrabber.aomic.id1000 import DataladAOMICID1000


URI = "https://gin.g-node.org/juaml/datalad-example-aomic1000"


@pytest.mark.parametrize(
    "type_, nested_types",
    [
        ("BOLD", ["confounds", "mask"]),
        ("T1w", ["mask"]),
        ("VBM_CSF", None),
        ("VBM_GM", None),
        ("VBM_WM", None),
        ("DWI", None),
        ("FreeSurfer", None),
    ],
)
def test_DataladAOMICID1000(
    type_: str,
    nested_types: Optional[List[str]],
) -> None:
    """Test DataladAOMICID1000 DataGrabber.

    Parameters
    ----------
    type_ : str
        The parametrized type.
    nested_types : list of str or None
        The parametrized nested types.

    """
    dg = DataladAOMICID1000(types=type_)
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
        assert out[type_]["path"].exists()
        assert out[type_]["path"].is_file()
        # Asserts data type metadata
        assert "meta" in out[type_]
        meta = out[type_]["meta"]
        assert "element" in meta
        assert "subject" in meta["element"]
        assert test_element == meta["element"]["subject"]
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
def test_DataladAOMICID1000_partial_data_access(
    types: Union[str, List[str]],
) -> None:
    """Test DataladAOMICID1000 DataGrabber partial data access.

    Parameters
    ----------
    types : str or list of str
        The parametrized types.

    """
    dg = DataladAOMICID1000(types=types)
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


def test_DataladAOMICID1000_incorrect_data_type() -> None:
    """Test DataladAOMICID1000 DataGrabber incorrect data type."""
    with pytest.raises(
        ValueError, match="`patterns` must contain all `types`"
    ):
        _ = DataladAOMICID1000(types="Scooby-Doo")
