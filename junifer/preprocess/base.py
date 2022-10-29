"""Provide base class for preprocessor."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Tuple, Any


from ..pipeline import PipelineStepMixin
from ..utils import logger, raise_error


class BasePreprocessor(ABC, PipelineStepMixin):
    """Abstract base class for all preprocessors.

    Parameters
    ----------
    on : str or list of str
        The kind of data to apply the preprocessor to. If None,
        will work on all available data (default: None).

    """

    def __init__(
        self,
        on: Optional[Union[List[str], str]] = None,
    ) -> None:
        """Initialize the class."""
        if on is None:
            on = self.get_valid_inputs()
        if not isinstance(on, list):
            on = [on]

        if any(x not in self.get_valid_inputs() for x in on):
            name = self.__class__.__name__
            wrong_on = [x for x in on if x not in self.get_valid_inputs()]
            raise ValueError(f"{name} cannot be computed on {wrong_on}")
        self._on = on

    def validate_input(self, input: List[str]) -> None:
        """Validate input.

        Parameters
        ----------
        input : list of str
            The input to the pipeline step. The list must contain the
            available Junifer Data dictionary keys.

        Raises
        ------
        ValueError
            If the input does not have the required data.

        """
        if not any(x in input for x in self._on):
            raise_error(
                "Input does not have the required data."
                f"\t Input: {input}"
                f"\t Required (any of): {self._on}"
            )

    @abstractmethod
    def get_output_kind(self, input: List[str]) -> List[str]:
        """Get output kind.

        Parameters
        ----------
        input : list of str
            The input to the marker. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        list of str
            The updated list of output kinds, as storage possibilities.

        """
        raise_error(
            msg="Concrete classes need to implement get_output_kind().",
            klass=NotImplementedError,
        )

    def get_valid_inputs(self) -> List[str]:
        """Get valid data types for input.

        Returns
        -------
        list of str
            The list of data types that can be used as input for this marker

        """
        raise_error(
            msg="Concrete classes need to implement get_valid_inputs().",
            klass=NotImplementedError,
        )

    def get_meta(self, kind: str) -> Dict:
        """Get metadata.

        Parameters
        ----------
        kind : str
            The kind of pipeline step.

        Returns
        -------
        dict
            The metadata as a dictionary with the only key 'marker'.

        """
        s_meta = super().get_meta()
        # same marker can be "fit"ted into different kinds, so the name
        # is created from the kind and the name of the marker
        s_meta["kind"] = kind
        return {"preprocess": s_meta}

    def fit_transform(
        self,
        input: Dict[str, Dict],
    ) -> Dict:
        """Fit and transform.

        Parameters
        ----------
        input : dict
            The Junifer Data object.

        Returns
        -------
        dict
            The processed output as a dictionary.

        """
        out = input
        for kind in self._on:
            if kind in input.keys():
                logger.info(f"Computing {kind}")
                t_input = input[kind]
                extra_input = input.copy()
                extra_input.pop(kind)
                t_meta = t_input.get("meta", {})  # input kind meta
                t_meta.update(self.get_meta(kind))
                key, t_out = self.preprocess(
                    input=t_input, extra_input=extra_input)
                t_out.update(meta=t_meta)
                out[key] = t_out
        return out

    @abstractmethod
    def preprocess(
        self,
        input: Dict[str, Any],
        extra_input: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Preprocess.

        Parameters
        ----------
        input : Dict[str, Dict]
            A single input from the pipeline data object in which to compute
            the marker.
        extra_input : Dict, optional
            The other fields in the pipeline data object. Useful for accessing
            other data kind that needs to be used in the computation. For
            example, the functional connectivity markers can make use of the
            confounds if available (default None).

        Returns
        -------
        key : str
            The key to store the output in the Junifer Data object.
        object : dict
            The computed result as dictionary. This will be stored in the
            Junifer Data object under the key 'key'.

        """
        raise_error(
            msg="Concrete classes need to implement preprocess().",
            klass=NotImplementedError,
        )
