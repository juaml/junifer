"""Provide base class for smoothing."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import List, Optional, Union

from ..base import BasePreprocessor


__all__ = ["SmoothingBase"]


class SmoothingBase(BasePreprocessor):
    """Base class for smoothing.

    Parameters
    ----------
    on : {"T1w", "T2w", "BOLD"} or list of the options or None
        The data type to apply smoothing to. If None, will apply to all
        available data types.

    """

    def __init__(self, on: Optional[Union[List[str], str]]) -> None:
        """Initialize the class."""
        super().__init__(on=on, required_data_types=on)

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this
            preprocessor.

        """
        return ["T1w", "T2w", "BOLD"]

    def get_output_type(self, input_type: str) -> str:
        """Get output type.

        Parameters
        ----------
        input_type : str
            The data type input to the preprocessor.

        Returns
        -------
        str
            The data type output by the preprocessor.

        """
        # Does not add any new keys
        return input_type
