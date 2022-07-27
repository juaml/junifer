"""Provide tests for package."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
# License: AGPL


def test_import():
    """Test junifer import."""
    import junifer
    print(junifer.__version__)
