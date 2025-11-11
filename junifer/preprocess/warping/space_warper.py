"""Provide class for warping data to other template spaces."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from collections.abc import Sequence
from enum import Enum
from typing import Any, ClassVar, Literal

from templateflow import api as tflow

from ...api.decorators import register_preprocessor
from ...datagrabber import DataType
from ...typing import ConditionalDependencies
from ...utils import logger, raise_error
from ..base import BasePreprocessor
from ._ants_warper import ANTsWarper
from ._fsl_warper import FSLWarper


__all__ = ["SpaceWarper", "SpaceWarpingImpl"]


class SpaceWarpingImpl(str, Enum):
    """Accepted space warping implementations.

    * ``fsl`` : FSL's ``applywarp``
    * ``ants`` : ANTs' ``antsApplyTransforms``
    * ``auto`` : Auto-select tool when ``reference="T1w"``

    """

    fsl = "fsl"
    ants = "ants"
    auto = "auto"


@register_preprocessor
class SpaceWarper(BasePreprocessor):
    """Class for warping data to other template spaces.

    Parameters
    ----------
    using : :enum:`.SpaceWarpingImpl`
    reference : str
        The data type to use as reference for warping, can be either a data
        type like ``"T1w"`` or a template space like ``"MNI152NLin2009cAsym"``.
        Use ``"T1w"`` for native space warping and named templates for
        template space warping.
    on : list of {``DataType.T1w``, ``DataType.T2w``, ``DataType.BOLD``, \
         ``DataType.VBM_GM``, ``DataType.VBM_WM``, ``DataType.VBM_CSF``, \
         ``DataType.FALFF``, ``DataType.GCOR``, ``DataType.LCOR``}
        The data type(s) to warp.

    """

    _CONDITIONAL_DEPENDENCIES: ClassVar[ConditionalDependencies] = [
        {
            "using": SpaceWarpingImpl.fsl,
            "depends_on": [FSLWarper],
        },
        {
            "using": SpaceWarpingImpl.ants,
            "depends_on": [ANTsWarper],
        },
        {
            "using": SpaceWarpingImpl.auto,
            "depends_on": [FSLWarper, ANTsWarper],
        },
    ]
    _VALID_DATA_TYPES: ClassVar[Sequence[DataType]] = [
        DataType.T1w,
        DataType.T2w,
        DataType.BOLD,
        DataType.VBM_GM,
        DataType.VBM_WM,
        DataType.VBM_CSF,
        DataType.FALFF,
        DataType.GCOR,
        DataType.LCOR,
    ]

    using: SpaceWarpingImpl
    reference: str
    on: list[
        Literal[
            DataType.T1w,
            DataType.T2w,
            DataType.BOLD,
            DataType.VBM_GM,
            DataType.VBM_WM,
            DataType.VBM_CSF,
            DataType.FALFF,
            DataType.GCOR,
            DataType.LCOR,
        ]
    ]

    def validate_preprocessor_params(self) -> None:
        """Run extra logical validation for preprocessor."""
        # Set required data types based on reference
        if self.reference == "T1w":  # pragma: no cover
            # Update required data types
            self.required_data_types = [DataType.T1w, DataType.Warp]
            self.required_data_types.extend(self.on)
        elif self.reference not in tflow.templates():
            raise_error(f"Unknown reference: {self.reference}")

    def preprocess(  # noqa: C901
        self,
        input: dict[str, Any],
        extra_input: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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

        Raises
        ------
        ValueError
            If ``extra_input`` is None when transforming to native space
            i.e., using ``"T1w"`` as reference or converting from native to
            template space or
            if the ``reference`` key is missing from ``input`` when converting
            from native to template space.
        RuntimeError
            If warper could not be found in ``extra_input`` when
            ``using="auto"`` or converting from native space or
            if the data is in the correct space and does not require
            warping or
            if FSL or "auto" is used when ``reference!="T1w"``.

        """
        logger.info(f"Warping to {self.reference} space using SpaceWarper")
        # Transform to native space
        if self.reference == "T1w":  # pragma: no cover
            # Check for extra inputs
            if extra_input is None:
                raise_error(
                    "No extra input provided, requires `Warp` and "
                    f"`{self.reference}` data types in particular."
                )
            # Conditional preprocessor
            warper = None
            if self.using == "auto":
                for entry in extra_input["Warp"]:
                    if entry["dst"] == "native":
                        warper = entry["warper"]
                if warper is None:
                    raise_error(
                        klass=RuntimeError, msg="Could not find correct warper"
                    )
            else:
                warper = self.using
            if warper == "fsl":
                input = FSLWarper().preprocess(
                    input=input,
                    extra_input=extra_input,
                    reference=self.reference,
                )
            elif warper == "ants":
                input = ANTsWarper().preprocess(
                    input=input,
                    extra_input=extra_input,
                    reference=self.reference,
                )
        else:
            input_space = input["space"]
            # Check pre-requirements for space manipulation
            if self.using == "ants" and self.reference == input_space:
                raise_error(
                    (
                        f"The target data is in {self.reference} space "
                        "and thus warping will not be performed, hence you "
                        "should remove the SpaceWarper from the preprocess "
                        "step."
                    ),
                    klass=RuntimeError,
                )
            # Transform from native to MNI possible conditionally
            if input_space == "native":  # pragma: no cover
                # Check for reference as no T1w available
                if input.get("reference") is None:
                    raise_error(
                        "`reference` key missing from input data type."
                    )
                # Check for extra inputs
                if extra_input is None:
                    raise_error(
                        "No extra input provided, requires `Warp` "
                        "data type in particular."
                    )
                # Warp
                input_prewarp_space = input["prewarp_space"]
                warper = None
                for entry in extra_input["Warp"]:
                    if (
                        entry["src"] == input_space
                        and entry["dst"] == input_prewarp_space
                    ):
                        warper = entry["warper"]
                if warper is None:
                    raise_error(
                        klass=RuntimeError, msg="Could not find correct warper"
                    )
                if warper == "fsl":
                    input = FSLWarper().preprocess(
                        input=input,
                        extra_input=extra_input,
                        reference=input_prewarp_space,
                    )
                elif warper == "ants":
                    input = ANTsWarper().preprocess(
                        input=input,
                        extra_input=extra_input,
                        reference=input_prewarp_space,
                    )
                else:
                    raise_error(
                        klass=RuntimeError, msg="Could not find correct warper"
                    )
            else:
                # Transform from MNI to MNI template space not possible
                if self.using in ["fsl", "auto"]:
                    raise_error(
                        (
                            f"Warping from {input_space} space to "
                            f"{self.reference} space not possible with "
                            f"{self.using}, use ANTs instead."
                        ),
                        klass=RuntimeError,
                    )
                # Transform from MNI to MNI template space possible
                else:
                    input = ANTsWarper().preprocess(
                        input=input,
                        extra_input={},
                        reference=self.reference,
                    )
        logger.debug("Completed warping step")
        logger.debug("Warped data types: ")
        for k, v in input.items():
            if k in ["data", "meta"]:
                continue
            logger.debug(f"\t{k}: {v}")
        return input
