"""Provide class for default data reader."""

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
    """Mixin class for default data reader."""

    def validate_input(self, input: List[str]) -> None:
        """Validate input.

        Parameters
        ----------
        input : list of str
            The input to the pipeline step. The list must contain the
            available Junifer Data dictionary keys.

        """
        # Nothing to validate, any input is fine
        pass

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

        """
        # For each type of data, try to read it
        out = input.copy()
        if params is None:
            params = {}
        for type_ in input.keys():
            if "path" not in input[type_]:
                warn_with_log(
                    f"Input type {type_} does not provide a path. Skipping."
                )
                continue
            t_path = input[type_]["path"]
            t_params = params.get(type_, {})

            # Convert to Path if datareader is not well done
            if not isinstance(t_path, Path):
                t_path = Path(t_path)
                out[type_]["path"] = t_path
            logger.info(f"Reading {type_} from {t_path.as_posix()}")
            fread = None

            fname = t_path.name.lower()
            for ext, ftype in _extensions.items():
                if fname.endswith(ext):
                    logger.info(f"{type_} is type {ftype}")
                    reader_func = _readers[ftype]["func"]
                    reader_params = _readers[ftype]["params"]
                    if reader_params is not None:
                        t_params.update(reader_params)
                    logger.debug(f"Calling {reader_func} with {t_params}")
                    fread = reader_func(t_path, **t_params)
                    break
            if fread is None:
                logger.info(
                    f"Unknown file type {t_path.as_posix()}, skipping reading"
                )
            out[type_]["data"] = fread
            self.update_meta(out[type_], "datareader")
        return out
