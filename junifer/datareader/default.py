"""Provide class for default data reader."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import Dict, List

import nibabel as nib
import pandas as pd

from ..markers.base import PipelineStepMixin
from ..utils.logging import logger, warn_with_log


# Map each file extension to a kind
_extensions = {
    ".nii": "NIFTI",
    ".nii.gz": "NIFTI",
    ".csv": "CSV",
    ".tsv": "TSV",
}

# Map each kind to a function and arguments
_readers = {}
_readers["NIFTI"] = {"func": nib.load, "params": None}
_readers["CSV"] = {"func": pd.read_csv, "params": None}
_readers["TSV"] = {"func": pd.read_csv, "params": {"sep": "\t"}}


class DefaultDataReader(PipelineStepMixin):
    """Mixin class for default data reader."""

    # TODO: complete type annotations
    def validate_input(self, input: List[str]) -> None:
        """Validate input.

        Parameters
        ----------
        input

        """
        # Nothing to validate, any input is fine
        pass

    # TODO: complete type annotations
    def get_output_kind(self, input):
        """Get output kind.

        Parameters
        ----------
        input

        """
        # It will output the same kind of data as the input
        return input

    # TODO: complete type annotations
    def fit_transform(self, input, params=None) -> Dict:
        """Fit and transform.

        Parameters
        ----------
        input
        params

        Returns
        -------
        dict

        """
        # For each kind of data, try to read it

        # out is the same, but with the 'data' key set in
        # each kind dictionary, except for meta
        out = input.copy()
        if params is None:
            params = {}
        for kind in input.keys():
            if kind == "meta":
                out["meta"] = input["meta"]
                continue
            if "path" not in input[kind]:
                warn_with_log(
                    f"Input kind {kind} does not provide a path. Skipping."
                )
                continue
            t_path = input[kind]["path"]
            t_params = params.get(kind, {})

            # Convert to Path if datareader is not well done
            if not isinstance(t_path, Path):
                t_path = Path(t_path)
                out[kind]["path"] = t_path
            logger.info(f"Reading {kind} from {t_path.as_posix()}")
            fread = None

            fname = t_path.name.lower()
            for ext, ftype in _extensions.items():
                if fname.endswith(ext):
                    logger.info(f"{kind} is type {ftype}")
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
            out[kind]["data"] = fread
            if "meta" not in out:
                out["meta"] = {}
            out["meta"]["datareader"] = self.get_meta()
        return out
