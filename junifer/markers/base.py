"""Provide base class for markers."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict, List, Optional, Union

from ..pipeline import PipelineStepMixin
from ..utils import logger, raise_error


class BaseMarker(PipelineStepMixin):
    """Base class for all markers.

    Parameters
    ----------
    on : list of str
        The kind of data to work on. Defaults to None, which means
        to work on all available data.
    name : str, optional
        The name of the marker (default None).

    """

    def __init__(
        self, on: Union[List[str], str], name: Optional[str] = None
    ) -> None:
        """Initialize the class."""
        if not isinstance(on, list):
            on = [on]
        self._valid_inputs = on
        self.name = self.__class__.__name__ if name is None else name

    def get_meta(self, kind: str) -> Dict:
        """Get metadata.

        Parameters
        ----------
        kind : str
            The kind of pipeline step.

        Returns
        -------
        dict
            The metadata as a dictionary.

        """
        s_meta = super().get_meta()
        # same marker can be "fit"ted into different kinds, so the name
        # is created from the kind and the name of the marker
        s_meta["name"] = f"{kind}_{self.name}"
        s_meta["kind"] = kind
        return {"marker": s_meta}

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
        if not any(x in input for x in self._valid_inputs):
            raise_error(
                "Input does not have the required data."
                f"\t Input: {input}"
                f"\t Required (any of): {self._valid_inputs}"
            )

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
            msg="get_output_kinds() not implemented", klass=NotImplementedError
        )

    def compute(self, input: Dict, extra_input: Optional[Dict] = None) -> Dict:
        """Compute.

        Parameters
        ----------
        input : Dict[str, Dict]
            A single input from the pipeline data object in which to compute
            the marker.
        extra_input : Dict, optional
            The other fields in the pipeline data object. Useful for accessing
            other data kind that needs to be used in the computation. For
            example, the functional connectivity markers can make use of the
            confounds if available.

        Returns
        -------
        dict
            The computed result as dictionary. This will be either returned
            to the user or stored in the storage by calling the store method
            with this as a parameter.

        """
        raise_error(msg="compute() not implemented", klass=NotImplementedError)

    # TODO: complete type annotations
    def store(self, kind: str, out: Dict, storage) -> None:
        """Store.

        Parameters
        ----------
        input
        out

        """
        raise_error(msg="store() not implemented", klass=NotImplementedError)

    # TODO: complete type annotations
    def fit_transform(self, input: Dict[str, Dict], storage=None) -> Dict:
        """Fit and transform.

        Parameters
        ----------
        input
        storage

        Returns
        -------
        dict

        """
        out = {}
        meta = input.get("meta", {})
        for kind in self._valid_inputs:
            if kind in input.keys():
                logger.info(f"Computing {kind}")
                t_input = input[kind]
                extra_input = input.copy()
                extra_input.pop(kind)
                t_meta = meta.copy()
                t_meta.update(t_input.get("meta", {}))
                t_meta.update(self.get_meta(kind))
                t_out = self.compute(t_input, extra_input)
                t_out.update(meta=t_meta)
                if storage is not None:
                    logger.info(f"Storing in {storage}")
                    self.store(kind, t_out, storage)
                else:
                    logger.info("No storage specified, returning dictionary")
                    out[kind] = t_out

        return out
