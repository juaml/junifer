"""Provide concrete implementation for default DataReader."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Dict, List, Optional

import nibabel as nib
import pandas as pd

from ..api.decorators import register_datareader
from ..pipeline import PipelineStepMixin, UpdateMetaMixin
from ..utils.logging import logger, warn_with_log


# Map each file extension to a type
_extensions = {
    ".nii": "NIFTI",
    ".nii.gz": "NIFTI",
    ".csv": "CSV",
    ".tsv": "TSV",
}

# Map each type to a function and arguments
_readers = {}
_readers["NIFTI"] = {"func": nib.load, "params": None}
_readers["CSV"] = {"func": pd.read_csv, "params": None}
_readers["TSV"] = {"func": pd.read_csv, "params": {"sep": "\t"}}


@register_datareader
class DefaultDataReader(PipelineStepMixin, UpdateMetaMixin):
    """Concrete implementation for common data reading."""

    def validate_input(self, input: List[str]) -> List[str]:
        """Validate input.

        Parameters
        ----------
        input : list of str
            The input to the pipeline step. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        list of str
            The actual elements of the input that will be processed by this
            pipeline step.

        """
        # Nothing to validate, any input is fine
        return input

    def get_output_type(self, input: List[str]) -> List[str]:
        """Get output type.

        Parameters
        ----------
        input : list of str
            The input to the reader. The list must contain the
            available Junifer Data dictionary keys.

        Returns
        -------
        list of str
            The updated list of output types, as reading possibilities.

        """
        # It will output the same type of data as the input
        return input

    def _fit_transform(
        self,
        input: Dict[str, Dict],
        params: Optional[Dict] = None,
    ) -> Dict:
        """Fit and transform.

        Parameters
        ----------
        input : dict
            The Junifer Data object.
        params : dict, optional
            Extra parameters for data types (default None).

        Returns
        -------
        dict
            The processed output as dictionary. The "data" key is added to
            each data type dictionary.

        Warns
        -----
        RuntimeWarning
            If input data type has no key called ``"path"``.

        """
        # Copy input to not modify the original
        out = input.copy()
        # Set default extra parameters
        if params is None:
            params = {}
        # For each type of data, try to read it
        for type_ in input.keys():
            # Skip Warp data type
            if type_ == "Warp":
                continue

            # Check for malformed datagrabber specification
            if "path" not in input[type_]:
                warn_with_log(
                    f"Input type {type_} does not provide a path. Skipping."
                )
                continue

            # Retrieve actual path
            t_path = input[type_]["path"]
            # Retrieve loading params for the data type
            t_params = params.get(type_, {})

            # Convert str to Path
            if not isinstance(t_path, Path):
                t_path = Path(t_path)
                out[type_]["path"] = t_path

            logger.info(f"Reading {type_} from {t_path.as_posix()}")
            # Initialize variable for file data
            fread = None
            # Lowercase path
            fname = t_path.name.lower()
            # Loop through extensions to find the correct one
            for ext, ftype in _extensions.items():
                if fname.endswith(ext):
                    logger.info(f"{type_} is type {ftype}")
                    # Retrieve reader function
                    reader_func = _readers[ftype]["func"]
                    # Retrieve reader function params
                    reader_params = _readers[ftype]["params"]
                    # Update reader function params
                    if reader_params is not None:
                        t_params.update(reader_params)
                    logger.debug(f"Calling {reader_func} with {t_params}")
                    # Read data
                    fread = reader_func(t_path, **t_params)
                    break
            # If no file data is found due to unknown extension
            if fread is None:
                logger.info(
                    f"Unknown file type {t_path.as_posix()}, skipping reading"
                )

            # Set file data for output
            out[type_]["data"] = fread
            # Update metadata for step
            self.update_meta(out[type_], "datareader")

        return out
