"""Provide tests for pandas base feature storage."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from junifer.storage.pandas_base import PandasBaseFeatureStorage


def test_element_to_index() -> None:
    """Test element to index."""
    element = {"foo": "bar"}
    index = PandasBaseFeatureStorage.element_to_index(element)
    assert index.names == ["foo", "idx"]
    assert index.levels[0].name == "foo"
    assert index.levels[0].values[0] == "bar"
    assert all(x == "bar" for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)
    assert index.levels[1].name == "idx"
    assert all(x == i for i, x in enumerate(index.levels[1].values))
    assert index.levels[1].values.shape == (1,)

    index = PandasBaseFeatureStorage.element_to_index(element, n_rows=10)
    assert index.names == ["foo", "idx"]
    assert index.levels[0].name == "foo"
    assert all(x == "bar" for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)

    assert index.levels[1].name == "idx"
    assert all(x == i for i, x in enumerate(index.levels[1].values))
    assert index.levels[1].values.shape == (10,)

    index = PandasBaseFeatureStorage.element_to_index(
        element, n_rows=1, rows_col_name="scan"
    )
    assert index.names == ["foo", "scan"]
    assert index.levels[0].name == "foo"
    assert index.levels[0].values[0] == "bar"
    assert all(x == "bar" for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)
    assert index.levels[1].name == "scan"
    assert all(x == i for i, x in enumerate(index.levels[1].values))
    assert index.levels[1].values.shape == (1,)

    index = PandasBaseFeatureStorage.element_to_index(
        element, n_rows=7, rows_col_name="scan"
    )
    assert index.names == ["foo", "scan"]
    assert index.levels[0].name == "foo"
    assert all(x == "bar" for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)

    assert index.levels[1].name == "scan"
    assert all(x == i for i, x in enumerate(index.levels[1].values))
    assert index.levels[1].values.shape == (7,)

    element = {"subject": "sub-01", "session": "ses-01"}
    index = PandasBaseFeatureStorage.element_to_index(element, n_rows=10)

    assert index.levels[0].name == "subject"
    assert all(x == "sub-01" for x in index.levels[0].values)
    assert index.levels[0].values.shape == (1,)

    assert index.levels[1].name == "session"
    assert all(x == "ses-01" for x in index.levels[1].values)
    assert index.levels[1].values.shape == (1,)

    assert index.levels[2].name == "idx"
    assert all(x == i for i, x in enumerate(index.levels[2].values))
    assert index.levels[2].values.shape == (10,)
