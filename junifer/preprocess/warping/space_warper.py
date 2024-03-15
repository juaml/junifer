"""Provide class for warping data to other template spaces."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar, Dict, List, Optional, Tuple, Type, Union

from templateflow import api as tflow

from ...api.decorators import register_preprocessor
from ...utils import logger, raise_error
from ..base import BasePreprocessor
from ._ants_native_warper import ANTsNativeWarper
from ._ants_template_warper import ANTsTemplateWarper
from ._fsl_native_warper import FSLNativeWarper


__all__ = ["SpaceWarper"]


@register_preprocessor
class SpaceWarper(BasePreprocessor):
    """Class for warping data to other template spaces.

    Parameters
    ----------
    using : {"fsl_native", "ants_native", "ants_template}
        Implementation to use for warping:

        * "fsl_native" : Use FSL's ``applywarp`` for native space warping
        * "ants_native" : Use ANTs' ``antsApplyTransforms`` for native space
                          warping
        * "ants_template" : Use ANTs' ``antsApplyTransforms`` for template
                            space warping

    reference : str
        The data type to use as reference for warping, can be either a data
        type like ``"T1w"`` or a template space like ``"MNI152NLin2009cAsym"``.
        Use ``"T1w"`` for native space warping and named templates for
        template space warping.
    on : {"T1w", "BOLD", "VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"} or list \
         of the options
        The data type to warp.

    Raises
    ------
    ValueError
        If ``using`` is invalid or
        if ``reference`` is invalid.

    """

    _CONDITIONAL_DEPENDENCIES: ClassVar[List[Dict[str, Union[str, Type]]]] = [
        {
            "using": "fsl_native",
            "depends_on": FSLNativeWarper,
        },
        {
            "using": "ants_native",
            "depends_on": ANTsNativeWarper,
        },
        {
            "using": "ants_template",
            "depends_on": ANTsTemplateWarper,
        },
    ]

    def __init__(
        self, using: str, reference: str, on: Union[List[str], str]
    ) -> None:
        """Initialize the class."""
        # Validate `using` parameter
        valid_using = [dep["using"] for dep in self._CONDITIONAL_DEPENDENCIES]
        if using not in valid_using:
            raise_error(
                f"Invalid value for `using`, should be one of: {valid_using}"
            )
        self.using = using
        self.reference = reference
        # Set required data types based on reference and
        # initialize superclass
        if self.reference == "T1w":
            required_data_types = [self.reference, "Warp"]
            # Listify on
            if not isinstance(on, list):
                on = [on]
            # Extend required data types
            required_data_types.extend(on)

            super().__init__(
                on=on,
                required_data_types=required_data_types,
            )
        elif self.reference in tflow.templates():
            super().__init__(on=on)
        else:
            raise_error(f"Unknown reference: {self.reference}")

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this
            preprocessor.

        """
        return ["T1w", "BOLD", "VBM_GM", "VBM_WM", "fALFF", "GCOR", "LCOR"]

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

    def preprocess(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Dict[str, Any]]]]:
        """Preprocess.

        Parameters
        ----------
        input : dict
            The input from the Junifer Data object.
        extra_input : dict, optional
            The other fields in the Junifer Data object.

        Returns
        -------
        dict
            The computed result as dictionary.
        None
            Extra "helper" data types as dictionary to add to the Junifer Data
            object.

        Raises
        ------
        ValueError
            If ``extra_input`` is None when transforming to native space
            i.e., using ``"T1w"`` as reference.
        RuntimeError
            If the data is in the correct space and does not require
            warping.

        """
        logger.info(f"Warping to {self.reference} space using SpaceWarper")
        # Transform to native space
        if self.reference == "T1w":
            # Check for extra inputs
            if extra_input is None:
                raise_error(
                    "No extra input provided, requires `Warp` and "
                    f"`{self.reference}` data types in particular."
                )
            # Conditional preprocessor
            if self.using == "fsl_native":
                input = FSLNativeWarper().preprocess(
                    input=input,
                    extra_input=extra_input,
                )
            elif self.using == "ants_natice":
                input = ANTsNativeWarper().preprocess(
                    input=input,
                    extra_input=extra_input,
                )
        # Transform to template space
        else:
            # Check pre-requirements for space manipulation
            if self.reference == input["space"]:
                raise_error(
                    (
                        "Skipped warping as the data is in "
                        f"{self.reference} space which would mean that you "
                        "can remove the SpaceWarper from the preprocess step."
                    ),
                    klass=RuntimeError,
                )
            else:
                input = ANTsTemplateWarper().preprocess(
                    input=input,
                    dst=self.reference,
                )

        return input, None
