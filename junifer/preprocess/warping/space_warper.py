"""Provide class for warping data to other template spaces."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Any, ClassVar, Optional, Union

from templateflow import api as tflow

from ...api.decorators import register_preprocessor
from ...typing import ConditionalDependencies
from ...utils import logger, raise_error
from ..base import BasePreprocessor
from ._ants_warper import ANTsWarper
from ._fsl_warper import FSLWarper


__all__ = ["SpaceWarper"]


@register_preprocessor
class SpaceWarper(BasePreprocessor):
    """Class for warping data to other template spaces.

    Parameters
    ----------
    using : {"fsl", "ants", "auto"}
        Implementation to use for warping:

        * "fsl" : Use FSL's ``applywarp``
        * "ants" : Use ANTs' ``antsApplyTransforms``
        * "auto" : Auto-select tool when ``reference="T1w"``

    reference : str
        The data type to use as reference for warping, can be either a data
        type like ``"T1w"`` or a template space like ``"MNI152NLin2009cAsym"``.
        Use ``"T1w"`` for native space warping and named templates for
        template space warping.
    on : {"T1w", "T2w", "BOLD", "VBM_GM", "VBM_WM", "VBM_CSF", "fALFF", \
        "GCOR", "LCOR"} or list of the options
        The data type to warp.

    Raises
    ------
    ValueError
        If ``using`` is invalid or
        if ``reference`` is invalid.

    """

    _CONDITIONAL_DEPENDENCIES: ClassVar[ConditionalDependencies] = [
        {
            "using": "fsl",
            "depends_on": FSLWarper,
        },
        {
            "using": "ants",
            "depends_on": ANTsWarper,
        },
        {
            "using": "auto",
            "depends_on": [FSLWarper, ANTsWarper],
        },
    ]

    def __init__(
        self, using: str, reference: str, on: Union[list[str], str]
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

    def get_valid_inputs(self) -> list[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this
            preprocessor.

        """
        return [
            "T1w",
            "T2w",
            "BOLD",
            "VBM_GM",
            "VBM_WM",
            "VBM_CSF",
            "fALFF",
            "GCOR",
            "LCOR",
        ]

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
        input: dict[str, Any],
        extra_input: Optional[dict[str, Any]] = None,
    ) -> tuple[dict[str, Any], Optional[dict[str, dict[str, Any]]]]:
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
            If warper could not be found in ``extra_input`` when
            ``using="auto"`` or
            if the data is in the correct space and does not require
            warping or
            if FSL is used when ``reference="T1w"``.

        """
        logger.info(f"Warping to {self.reference} space using SpaceWarper")
        # Transform to native space
        if self.using in ["fsl", "ants", "auto"] and self.reference == "T1w":
            # Check for extra inputs
            if extra_input is None:
                raise_error(
                    "No extra input provided, requires `Warp` and "
                    f"`{self.reference}` data types in particular."
                )
            # Conditional preprocessor
            if self.using == "fsl":
                input = FSLWarper().preprocess(
                    input=input,
                    extra_input=extra_input,
                )
            elif self.using == "ants":
                input = ANTsWarper().preprocess(
                    input=input,
                    extra_input=extra_input,
                    reference=self.reference,
                )
            elif self.using == "auto":
                warper = None
                for entry in extra_input["Warp"]:
                    if entry["dst"] == "native":
                        warper = entry["warper"]
                if warper is None:
                    raise_error(
                        klass=RuntimeError, msg="Could not find correct warper"
                    )
                if warper == "fsl":
                    input = FSLWarper().preprocess(
                        input=input,
                        extra_input=extra_input,
                    )
                elif warper == "ants":
                    input = ANTsWarper().preprocess(
                        input=input,
                        extra_input=extra_input,
                        reference=self.reference,
                    )
        # Transform to template space with ANTs possible
        elif self.using == "ants" and self.reference != "T1w":
            # Check pre-requirements for space manipulation
            if self.reference == input["space"]:
                raise_error(
                    (
                        f"The target data is in {self.reference} space "
                        "and thus warping will not be performed, hence you "
                        "should remove the SpaceWarper from the preprocess "
                        "step."
                    ),
                    klass=RuntimeError,
                )

            input = ANTsWarper().preprocess(
                input=input,
                extra_input={},
                reference=self.reference,
            )
        # Transform to template space with FSL not possible
        elif self.using == "fsl" and self.reference != "T1w":
            raise_error(
                (
                    f"Warping to {self.reference} space not possible with "
                    "FSL, use ANTs instead."
                ),
                klass=RuntimeError,
            )

        return input, None
