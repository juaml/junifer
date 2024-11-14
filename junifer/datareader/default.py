"""Provide concrete implementation for default DataReader."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Optional, Union

import nibabel as nib
import pandas as pd

from ..api.decorators import register_datareader
from ..pipeline import PipelineStepMixin, UpdateMetaMixin
from ..utils.logging import logger, warn_with_log


__all__ = ["DefaultDataReader"]


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

    def validate_input(self, input: list[str]) -> list[str]:
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

    def get_output_type(self, input_type: str) -> str:
        """Get output type.

        Parameters
        ----------
        input_type : str
            The data type input to the reader.

        Returns
        -------
        str
            The data type output by the reader.

        """
        # It will output the same type of data as the input
        return input_type

    def _fit_transform(
        self,
        input: dict[str, dict],
        params: Optional[dict] = None,
    ) -> dict:
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
        for type_key, type_val in input.items():
            # Skip Warp and FreeSurfer data type
            if type_key in ["Warp", "FreeSurfer"]:
                continue

            # Check for malformed datagrabber specification
            if "path" not in type_val:
                warn_with_log(
                    f"Input type {type_key} does not provide a path. Skipping."
                )
                continue

            # Iterate to check for nested "types" like mask;
            # need to copy to avoid runtime error for changing dict size
            for k, v in type_val.copy().items():
                # Read data for base data type
                if k == "path":
                    # Convert str to Path
                    if not isinstance(v, Path):
                        v = Path(v)
                    # Update path
                    out[type_key]["path"] = v
                    logger.info(f"Reading {type_key} from {v.absolute()!s}")
                    # Retrieve loading params for the data type
                    t_params = params.get(type_key, {})
                    # Read data
                    out[type_key]["data"] = _read_data(
                        data_type=type_key, path=v, read_params=t_params
                    )
                # Read data for nested data type
                if isinstance(v, dict) and "path" in v:
                    # Set path
                    nested_path = v["path"]
                    # Convert str to Path
                    if not isinstance(nested_path, Path):
                        nested_path = Path(nested_path)
                    # Update path
                    out[type_key][k]["path"] = nested_path
                    # Set nested type key for easier access
                    nested_type = f"{type_key}.{k}"
                    logger.info(
                        f"Reading {nested_type} from "
                        f"{nested_path.absolute()!s}"
                    )
                    # Retrieve loading params for the nested data type
                    nested_params = params.get(nested_type, {})
                    # Read data
                    out[type_key][k]["data"] = _read_data(
                        data_type=nested_type,
                        path=nested_path,
                        read_params=nested_params,
                    )

            # Update metadata for step
            self.update_meta(out[type_key], "datareader")

        return out


def _read_data(
    data_type: str, path: Path, read_params: dict
) -> Union[nib.Nifti1Image, pd.DataFrame, None]:
    """Read data for data type.

    Parameters
    ----------
    data_type : str
        The data type being read.
    path : pathlib.Path
        The path to read data from.
    read_params : dict
        Parameters for reader function.

    Returns
    -------
    nibabel.Nifti1Image or pandas.DataFrame or pandas.TextFileReader or None
        The data loaded in memory if file type is known else None.

    """
    # Initialize variable for file data
    fread = None
    # Lowercase path
    fname = path.name.lower()
    # Loop through extensions to find the correct one
    for ext, ftype in _extensions.items():
        if fname.endswith(ext):
            logger.info(f"{data_type} is of type {ftype}")
            # Retrieve reader function
            reader_func = _readers[ftype]["func"]
            # Retrieve reader function params
            reader_params = _readers[ftype]["params"]
            # Update reader function params
            if reader_params is not None:
                read_params.update(reader_params)
            logger.debug(f"Calling {reader_func!s} with {read_params}")
            # Read data
            fread = reader_func(path, **read_params)
            break
    # If no file data is found due to unknown extension
    if fread is None:
        logger.info(f"Unknown file type {path.absolute()!s}, skipping reading")

    return fread
