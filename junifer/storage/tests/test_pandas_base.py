"""Provide tests for pandas base feature storage."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from junifer.storage.pandas_base import PandasBaseFeatureStorage


def test_element_to_index() -> None:
    """Test element to index."""
    # First element
    element = {"foo": "bar"}

    # First test; no extra column
    index = PandasBaseFeatureStorage.element_to_index(element=element)
    # Check index name
    assert index.name == "foo"
    # # Check index values
    assert all(x == "bar" for x in index.values)  # type: ignore
    # Check index values shape
    assert index.shape == (1,)  # type: ignore

    # Second test; add extra column
    index = PandasBaseFeatureStorage.element_to_index(
        element=element, n_rows=10
    )
    # Check index names
    assert index.names == ["foo", "idx"]
    # Check first index level name
    assert index.levels[0].name == "foo"  # type: ignore
    # Check first index level values
    assert all(x == "bar" for x in index.levels[0].values)  # type: ignore
    # Check first index level values shape
    assert index.levels[0].values.shape == (1,)  # type: ignore
    # Check second index level name
    assert index.levels[1].name == "idx"  # type: ignore
    # Check second index level values
    assert all(
        x == i for i, x in enumerate(index.levels[1].values)  # type: ignore
    )
    # Check second index level values shape
    assert index.levels[1].values.shape == (10,)  # type: ignore

    # Third test; custom extra column name has no effect
    index = PandasBaseFeatureStorage.element_to_index(
        element=element, n_rows=1, rows_col_name="scan"
    )
    # Check index name
    assert index.name == "foo"
    # Check index values
    assert all(x == "bar" for x in index.values)  # type: ignore
    # Check index values shape
    assert index.shape == (1,)  # type: ignore

    # Fourth test; custom extra column name has effect
    index = PandasBaseFeatureStorage.element_to_index(
        element=element, n_rows=7, rows_col_name="scan"
    )
    # Check index names
    assert index.names == ["foo", "scan"]
    # Check first index level name
    assert index.levels[0].name == "foo"  # type: ignore
    # Check first index level values
    assert all(x == "bar" for x in index.levels[0].values)  # type: ignore
    # Check first index level values shape
    assert index.levels[0].values.shape == (1,)  # type: ignore
    # Check second index level name
    assert index.levels[1].name == "scan"  # type: ignore
    # Check second index level values
    assert all(
        x == i for i, x in enumerate(index.levels[1].values)  # type: ignore
    )
    # Check second index level values shape
    assert index.levels[1].values.shape == (7,)  # type: ignore

    # Second element
    element = {"subject": "sub-01", "session": "ses-01"}

    # Fifth test; default name for extra column and multi-level element access
    index = PandasBaseFeatureStorage.element_to_index(
        element=element, n_rows=10
    )
    # Check first index level name
    assert index.levels[0].name == "subject"  # type: ignore
    # Check first index level values
    assert all(x == "sub-01" for x in index.levels[0].values)  # type: ignore
    # Check first index level values shape
    assert index.levels[0].values.shape == (1,)  # type: ignore
    # Check second index level name
    assert index.levels[1].name == "session"  # type: ignore
    # Check second index level values
    assert all(x == "ses-01" for x in index.levels[1].values)  # type: ignore
    # Check second index level values shape
    assert index.levels[1].values.shape == (1,)  # type: ignore
    # Check third index level name
    assert index.levels[2].name == "idx"  # type: ignore
    # Check third index level values
    assert all(
        x == i for i, x in enumerate(index.levels[2].values)  # type: ignore
    )
    # Check third index level values shape
    assert index.levels[2].values.shape == (10,)  # type: ignore
