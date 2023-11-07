"""Provide class for warping BOLD via FSL FLIRT."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from ...api.decorators import register_preprocessor
from ...utils import logger, raise_error
from ..base import BasePreprocessor
from .apply_warper import _ApplyWarper


@register_preprocessor
class BOLDWarper(BasePreprocessor):
    """Class for warping BOLD NIfTI images via FSL FLIRT.

    Parameters
    ----------
    reference : str
        The data type to use as reference for warping.

    """

    _EXT_DEPENDENCIES: ClassVar[
        List[Dict[str, Union[str, bool, List[str]]]]
    ] = [
        {
            "name": "fsl",
            "optional": False,
            "commands": ["applywarp"],
        },
    ]

    def __init__(self, reference: str) -> None:
        """Initialize the class."""
        self.ref = reference
        super().__init__(
            on="BOLD", required_data_types=["BOLD", self.ref, "Warp"]
        )

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this
            preprocessor.

        """
        return ["BOLD"]

    def get_output_type(self, input: List[str]) -> List[str]:
        """Get output type.

        Parameters
        ----------
        input : list of str
            The input to the preprocessor. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        list of str
            The updated list of available Junifer Data object keys after
            the pipeline step.

        """
        # Does not add any new keys
        return input

    def preprocess(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Preprocess.

        Parameters
        ----------
        input : dict
            The BOLD input from the Junifer Data object.
        extra_input : dict, optional
            The other fields in the Junifer Data object. Must include the
            ``Warp`` and ``ref`` value's keys.

        Returns
        -------
        str
            The key to store the output in the Junifer Data object.
        dict
            The computed result as dictionary. This will be stored in the
            Junifer Data object under the key ``data`` of the data type.

        Raises
        ------
        ValueError
            If ``extra_input`` is None.

        """
        logger.debug("Warping BOLD using BOLDWarper")
        # Check for extra inputs
        if extra_input is None:
            raise_error(
                f"No extra input provided, requires `Warp` and `{self.ref}` "
                "data types in particular."
            )
        # Initialize ApplyWarper for computation
        apply_warper = _ApplyWarper(reference=self.ref, on="BOLD")
        # Replace original BOLD data with warped BOLD data
        _, input = apply_warper.preprocess(
            input=input,
            extra_input=extra_input,
        )
        return "BOLD", input
