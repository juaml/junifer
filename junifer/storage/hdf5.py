"""Provide concrete implementation for feature storage via HDF5."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL

from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np
import pandas as pd
from tqdm import tqdm

from ..api.decorators import register_storage
from ..external.h5io.h5io import (
    ChunkedArray,
    ChunkedList,
    has_hdf5,
    read_hdf5,
    write_hdf5,
)
from ..utils import logger, raise_error
from .base import BaseFeatureStorage
from .utils import (
    element_to_prefix,
    matrix_to_vector,
    store_matrix_checks,
    store_timeseries_2d_checks,
    timeseries2d_to_vector,
)


__all__ = ["HDF5FeatureStorage"]


def _create_chunk(
    chunk_data: list[np.ndarray],
    kind: str,
    element_count: int,
    chunk_size: int,
    i_chunk: int,
) -> Union[ChunkedArray, ChunkedList]:
    """Create chunked array or list.

    Parameters
    ----------
    chunk_data : list of numpy.ndarray
        The data to be chunked.
    kind : str
        The kind of data to be chunked.
    element_count : int
        The total number of elements.
    chunk_size : int
        The chunk size.
    i_chunk : int
        The chunk index.

    Returns
    -------
    ChunkedArray or ChunkedList
        The chunked array or list.

    Raises
    ------
    ValueError
        If `kind` is not one of ['vector', 'matrix', 'timeseries',
        'scalar_table'].

    """
    if kind in ["vector", "matrix"]:
        features_data = np.concatenate(chunk_data, axis=-1)
        array_shape = [features_data.shape[0]]
        array_chunk_size = [features_data.shape[0]]
        # Append second dimension for 3D
        if features_data.ndim == 3:
            array_shape.append(features_data.shape[1])
            array_chunk_size.append(features_data.shape[1])
        # Append final dimension of element count
        array_shape.append(element_count)
        # Append final dimension of chunk size
        array_chunk_size.append(chunk_size)
        out = ChunkedArray(
            data=features_data,
            shape=tuple(array_shape),
            chunk_size=tuple(array_chunk_size),
            n_chunk=i_chunk,
        )
    elif kind in ["timeseries", "scalar_table", "timeseries_2d"]:
        out = ChunkedList(
            data=chunk_data,
            size=element_count,
            offset=i_chunk * chunk_size,
        )
    else:
        raise_error(
            f"Invalid kind: {kind}. "
            "Must be one of ['vector', 'matrix', 'timeseries', "
            "'timeseries_2d', 'scalar_table']."
        )
    return out


@register_storage
class HDF5FeatureStorage(BaseFeatureStorage):
    """Concrete implementation for feature storage via HDF5.

    Parameters
    ----------
    uri : str or pathlib.Path
        The path to the file to be used.
    single_output : bool, optional
        If False, will create one HDF5 file per element. The name
        of the file will be prefixed with the respective element.
        If True, will create only one HDF5 file as specified in the
        ``uri`` and store all the elements in the same file. Concurrent
        writes should be handled with care (default True).
    overwrite : bool or "update", optional
        Whether to overwrite existing file. If True, will overwrite and
        if "update", will update existing entry or append (default "update").
    compression : {0-9}, optional
        Level of gzip compression: 0 (lowest) to 9 (highest) (default 7).
    force_float32 : bool, optional
        Whether to force casting of numpy.ndarray values to float32 if float64
        values are found (default True).
    chunk_size : int, optional
        The chunk size to use when collecting data from element files in
        :meth:`.collect`. If the file count is smaller than the value, the
        minimum is used (default 100).

    See Also
    --------
    SQLiteFeatureStorage : The concrete class for SQLite-based feature storage.

    """

    def __init__(
        self,
        uri: Union[str, Path],
        single_output: bool = True,
        overwrite: Union[bool, str] = "update",
        compression: int = 7,
        force_float32: bool = True,
        chunk_size: int = 100,
    ) -> None:
        # Convert str to Path
        if not isinstance(uri, Path):
            uri = Path(uri)

        # Create parent directories if not present
        if not uri.parent.exists():
            logger.info(
                f"Output directory: '{uri.parent.resolve()}' "
                "does not exist, creating now"
            )
            uri.parent.mkdir(parents=True, exist_ok=True)

        # Available storage kinds
        storage_types = ["vector", "timeseries", "matrix", "scalar_table"]

        super().__init__(
            uri=uri,
            storage_types=storage_types,
            single_output=single_output,
        )

        self.overwrite = overwrite
        self.compression = compression
        self.force_float32 = force_float32
        self.chunk_size = chunk_size

    def get_valid_inputs(self) -> list[str]:
        """Get valid storage types for input.

        Returns
        -------
        list of str
            The list of storage types that can be used as input for this
            storage.

        """
        return ["matrix", "vector", "timeseries", "scalar_table"]

    def _fetch_correct_uri_for_io(self, element: Optional[dict]) -> str:
        """Return proper URI for I/O based on `element`.

        If `element` is None, will return `self.uri`.

        Parameters
        ----------
        element : dict, optional
            The element as dictionary (default None).

        Returns
        -------
        str
            Formatted URI for accessing metadata and data.

        """
        if not self.single_output and not element:
            raise_error(
                msg=(
                    "`element` must be provided when `single_output` is False"
                ),
                klass=RuntimeError,
            )
        elif not self.single_output and element:
            # element access for multi output only
            prefix = element_to_prefix(element=element)
        else:
            # parent access for single output, ignore element
            prefix = ""
        # Format URI based on prefix
        return f"{self.uri.parent}/{prefix}{self.uri.name}"  # type: ignore

    def _read_metadata(
        self, element: Optional[dict[str, str]] = None
    ) -> dict[str, dict[str, Any]]:
        """Read metadata (should not be called directly).

        Parameters
        ----------
        element : dict, optional
            The element as dictionary (default None).

        Returns
        -------
        dict of dict
            The stored metadata for the element.

        Raises
        ------
        FileNotFoundError
            If HDF5 file does not exist.
        RuntimeError
            If ``meta`` does not exist in the file.

        """
        # Get correct URI for element;
        # is different from uri if single_output is False
        uri = self._fetch_correct_uri_for_io(element=element)

        # Check if file exists
        if not Path(uri).exists():
            raise_error(
                f"HDF5 file not found at: {uri}",
                klass=FileNotFoundError,
            )

        # Check if group is found in the storage
        if not has_hdf5(fname=uri, title="meta"):
            raise_error(
                f"Invalid junifer HDF5 file at: {uri}",
                klass=RuntimeError,
            )

        # Read metadata
        logger.debug(f"Loading HDF5 metadata from: {uri}")
        metadata = read_hdf5(
            fname=uri,
            title="meta",
            slash="ignore",
        )
        logger.debug(f"Loaded HDF5 metadata from: {uri}")

        return metadata

    def list_features(self) -> dict[str, dict[str, Any]]:
        """List the features in the storage.

        Returns
        -------
        dict
            List of features in the storage. The keys are the feature MD5 to
            be used in :meth:`.read_df` and the values are the metadata of each
            feature.

        """
        # Read metadata
        metadata = read_hdf5(
            fname=str(self.uri.resolve()),  # type: ignore
            title="meta",
            slash="ignore",
        )
        return metadata

    def _read_data(
        self, md5: str, element: Optional[dict[str, str]] = None
    ) -> dict[str, Any]:
        """Read data (should not be called directly).

        Parameters
        ----------
        md5 : str
            The MD5 used as the HDF5 group name.
        element : dict, optional
            The element as dictionary (default None).

        Returns
        -------
        dict
            The retrieved data.

        Raises
        ------
        FileNotFoundError
            If HDF5 file does not exist.
        RuntimeError
            If the specified ``md5`` does not exist in the file.

        """
        # Get correct URI for element;
        # is different from uri if single_output is False
        uri = self._fetch_correct_uri_for_io(element=element)

        # Check if file exists
        if not Path(uri).exists():
            raise_error(
                f"HDF5 file not found at: {uri}",
                klass=FileNotFoundError,
            )

        # Check if group is found in the storage
        if not has_hdf5(fname=uri, title=md5):
            raise_error(
                f"{md5} not found in HDF5 file at: {uri}",
                klass=RuntimeError,
            )

        # Read data
        logger.debug(f"Loading HDF5 data for {md5} from: {uri}")
        data = read_hdf5(
            fname=uri,
            title=md5,
            slash="ignore",
        )
        logger.debug(f"Loaded HDF5 data for {md5} from: {uri}")

        return data

    def read(
        self,
        feature_name: Optional[str] = None,
        feature_md5: Optional[str] = None,
    ) -> dict[
        str, Union[str, list[Union[int, str, dict[str, str]]], np.ndarray]
    ]:
        """Read stored feature.

        Parameters
        ----------
        feature_name : str, optional
            Name of the feature to read (default None).
        feature_md5 : str, optional
            MD5 hash of the feature to read (default None).

        Returns
        -------
        dict
            The stored feature as a dictionary.

        Raises
        ------
        IOError
            If HDF5 file does not exist.

        """
        # Parameter conflict
        if feature_md5 and feature_name:
            raise_error(
                msg=(
                    "Only one of `feature_name` or `feature_md5` can be "
                    "specified."
                )
            )
        # Parameter absence
        elif not feature_md5 and not feature_name:
            raise_error(
                msg=(
                    "At least one of `feature_name` or `feature_md5` "
                    "must be specified."
                )
            )
        # Parameter check pass; read metadata
        metadata = read_hdf5(
            fname=str(self.uri.resolve()),  # type: ignore
            title="meta",
            slash="ignore",
        )
        # Initialize MD5 variable
        md5: str = ""

        # Consider feature_md5
        if feature_md5:
            logger.debug(
                f"Validating feature MD5 '{feature_md5}' in metadata "
                f"for: {self.uri.resolve()} ..."  # type: ignore
            )
            # Validate MD5
            if feature_md5 in metadata:
                md5 = feature_md5  # type: ignore
            else:
                raise_error(msg=f"Feature MD5 '{feature_md5}' not found")

        # Consider feature_name
        elif feature_name:
            logger.debug(
                f"Validating feature name '{feature_name}' in metadata "
                f"for: {self.uri.resolve()} ..."  # type: ignore
            )
            # Retrieve MD5 for feature_name
            # Implicit counter for duplicate feature_name with different
            # MD5; happens when something is wrong with marker computation
            feature_name_duplicates_with_different_md5 = []
            for md5, meta in metadata.items():
                if meta["name"] == feature_name:
                    feature_name_duplicates_with_different_md5.append(md5)

            # Check for no / duplicate feature_name
            if len(feature_name_duplicates_with_different_md5) == 0:
                raise_error(msg=f"Feature '{feature_name}' not found")
            elif len(feature_name_duplicates_with_different_md5) > 1:
                raise_error(
                    msg=(
                        "More than one feature with name "
                        f"'{feature_name}' found. You can bypass this "
                        "issue by specifying a `feature_md5`."
                    )
                )

            md5 = feature_name_duplicates_with_different_md5[0]

        # Read data from HDF5
        hdf_data = read_hdf5(
            fname=str(self.uri.resolve()),  # type: ignore
            title=md5,
            slash="ignore",
        )
        return hdf_data

    def read_df(
        self,
        feature_name: Optional[str] = None,
        feature_md5: Optional[str] = None,
    ) -> pd.DataFrame:
        """Read feature into a pandas.DataFrame.

        Either one of ``feature_name`` or ``feature_md5`` needs to be
        specified.

        Parameters
        ----------
        feature_name : str, optional
            Name of the feature to read (default None).
        feature_md5 : str, optional
            MD5 hash of the feature to read (default None).

        Returns
        -------
        pandas.DataFrame
            The features as a dataframe.

        Raises
        ------
        IOError
            If HDF5 file does not exist.

        """
        hdf_data = self.read(
            feature_name=feature_name, feature_md5=feature_md5
        )
        reshaped_data = hdf_data["data"]

        # Generate index for the data
        logger.debug(
            "Generating pandas.MultiIndex for feature "
            f"{feature_name or feature_md5} ..."
        )

        if hdf_data["kind"] == "matrix":
            # Set index for element
            element_idx = hdf_data["element"]
            # Flatten data and get column headers for dataframe
            flat_data, columns = matrix_to_vector(
                data=hdf_data["data"],
                col_names=hdf_data["column_headers"],
                row_names=hdf_data["row_headers"],
                matrix_kind=hdf_data["matrix_kind"],
                diagonal=bool(hdf_data["diagonal"]),
            )
            # Convert data to proper 2D
            reshaped_data = flat_data.T
        elif hdf_data["kind"] == "vector":
            # Set index for element
            element_idx = hdf_data["element"]
            # Set column headers for dataframe
            columns = hdf_data["column_headers"]
            # Convert data to proper 2D
            reshaped_data = hdf_data["data"].T
        elif hdf_data["kind"] == "timeseries":
            # Create dictionary for aggregating index data
            element_idx = defaultdict(list)
            all_data = []
            for idx, element in enumerate(hdf_data["element"]):
                # Get row count for the element
                t_data = hdf_data["data"][idx]
                all_data.append(t_data)
                n_rows, _ = t_data.shape
                # Set rows for the index
                for key, val in element.items():
                    element_idx[key].extend([val] * n_rows)
                # Add extra column for timepoints
                element_idx[hdf_data["row_header_column_name"]].extend(
                    np.arange(n_rows)
                )
            # Set column headers for dataframe
            columns = hdf_data["column_headers"]
            # Convert data from 3D to 2D
            reshaped_data = np.concatenate(all_data, axis=0)
        elif hdf_data["kind"] == "timeseries_2d":
            # Create dictionary for aggregating index data
            element_idx = defaultdict(list)
            all_data = []
            for idx, element in enumerate(hdf_data["element"]):
                # Get row count for the element
                t_data = hdf_data["data"][idx]
                flat_data, columns = timeseries2d_to_vector(
                    data=t_data,
                    col_names=hdf_data["column_headers"],
                    row_names=hdf_data["row_headers"],
                )
                all_data.append(flat_data)
                n_timepoints = flat_data.shape[0]
                # Set rows for the index
                for key, val in element.items():
                    element_idx[key].extend([val] * n_timepoints)
                # Add extra column for timepoints
                element_idx["timepoint"].extend(np.arange(n_timepoints))
            # Convert data from 3D to 2D
            reshaped_data = np.concatenate(all_data, axis=0)
        elif hdf_data["kind"] == "scalar_table":
            # Create dictionary for aggregating index data
            element_idx = defaultdict(list)
            all_data = []
            for idx, element in enumerate(hdf_data["element"]):
                # Get row count for the element
                t_data = hdf_data["data"][idx]
                all_data.append(t_data)
                n_rows = len(hdf_data["row_headers"])
                # Set rows for the index
                for key, val in element.items():
                    element_idx[key].extend([val] * n_rows)
                # Add extra column for row header column name
                element_idx[hdf_data["row_header_column_name"]].extend(
                    hdf_data["row_headers"]
                )
            # Set column headers for dataframe
            columns = hdf_data["column_headers"]
            # Convert data from 3D to 2D
            reshaped_data = np.concatenate(all_data, axis=0)

        # Create dataframe for index
        idx_df = pd.DataFrame(data=element_idx)  # type: ignore
        # Create multiindex from dataframe
        hdf_data_idx = pd.MultiIndex.from_frame(df=idx_df)
        logger.debug(
            "Generated pandas.MultiIndex for feature "
            f"{feature_name or feature_md5} ..."
        )

        # Convert to DataFrame
        logger.debug(
            "Converting HDF5 data for feature "
            f"{feature_name or feature_md5} to pandas.DataFrame ..."
        )
        df = pd.DataFrame(
            data=reshaped_data,
            index=hdf_data_idx,
            columns=columns,  # type: ignore
            dtype=reshaped_data.dtype,
        )
        logger.debug(
            "Converted HDF5 data for feature "
            f"{feature_name or feature_md5} to pandas.DataFrame ..."
        )

        return df

    def _write_processed_data(
        self, fname: str, processed_data: dict[str, Any], title: str
    ) -> None:
        """Write processed data to HDF5 (should not be called directly).

        This is used primarily in :meth:`.store_metadata` and ``_store_data``.

        Parameters
        ----------
        fname : str
            The HDF5 file to store data.
        processed_data : dict
            The processed data as dictionary.
        title : str
            The top-level directory name.

        """
        logger.debug(f"Writing processed HDF5 data to: {fname} ...")
        # Write to HDF5
        write_hdf5(
            fname=fname,
            data=processed_data,
            overwrite=self.overwrite,  # type: ignore
            compression=self.compression,
            title=title,
            slash="error",
            use_json=True,
        )
        logger.debug(f"Wrote processed HDF5 data to: {fname} ...")

    def store_metadata(
        self,
        meta_md5: str,
        element: dict[str, str],
        meta: dict[str, Any],
    ) -> None:
        """Store metadata.

        This method first loads existing metadata (if any) using
        ``_read_metadata`` and appends to it the new metadata and then saves
        the updated metadata using ``_write_processed_data``. It will only
        store metadata if ``meta_md5`` is not found already.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        meta : dict
            The metadata as a dictionary.

        """
        # Get correct URI for element;
        # is different from uri if single_output is False
        uri = self._fetch_correct_uri_for_io(element=element)

        # Check if file exists, then read metadata else create empty dictionary
        if Path(uri).exists():
            metadata = self._read_metadata(element=element)
        else:
            logger.debug(f"Creating new file at {uri} ...")
            metadata = {}

        # Only add entry if MD5 is not present
        if meta_md5 not in metadata:
            logger.debug(f"HDF5 metadata for {meta_md5} not found, adding ...")
            # Update metadata
            metadata[meta_md5] = meta

            logger.info(f"Writing HDF5 metadata for {meta_md5} to: {uri}")
            logger.debug(f"HDF5 overwrite is set to: {self.overwrite} ...")
            logger.debug(
                "HDF5 gzip compression level is set to: "
                f"{self.compression} ..."
            )

            # Write metadata
            self._write_processed_data(
                fname=uri,
                processed_data=metadata,
                title="meta",
            )

            logger.info(f"Wrote HDF5 metadata for {meta_md5} to: {uri}")
        else:
            logger.debug(
                f"HDF5 metadata for {meta_md5} found, skipping store ..."
            )

    def _store_data(
        self,
        kind: str,
        meta_md5: str,
        element: list[dict[str, str]],
        data: np.ndarray,
        **kwargs: Any,
    ) -> None:
        """Store data.

        This method first loads existing data (if any) using
        ``_read_data`` and appends to it the `element` and `data`
        values, and writes them and other information passed via
        `**kwargs` using ``_write_processed_data``.

        Parameters
        ----------
        kind : {"matrix", "vector", "timeseries", "scalar_table"}
            The storage kind.
        meta_md5 : str
            The metadata MD5 hash.
        element : list of dict
            The element as list of dictionary.
        data : numpy.ndarray
            The data to store.
        **kwargs : dict
            Keyword arguments passed from the calling method.

        """
        # Get correct URI for element;
        # is different from uri if single_output is False
        uri = self._fetch_correct_uri_for_io(element=element[0])

        # Check if MD5 exists, then read data else create empty dictionary
        # File should be present here already
        if has_hdf5(fname=uri, title=meta_md5):
            stored_data = self._read_data(md5=meta_md5, element=element[0])
        else:
            logger.debug(f"Creating new data map for {meta_md5} ...")
            stored_data = {}

        # Initialize dictionary to aggregate data to write
        data_to_write = kwargs

        # Optional casting of float64 values to float32 for numpy.ndarray
        if isinstance(data, np.ndarray):
            if data.dtype == np.dtype("float64") and self.force_float32:
                data = data.astype(
                    dtype=np.dtype("float32"), casting="same_kind"
                )
        elif isinstance(data, list):
            if self.force_float32:
                data = [
                    (
                        x.astype(
                            dtype=np.dtype("float32"), casting="same_kind"
                        )
                        if x.dtype == np.dtype("float64")
                        else x
                    )
                    for x in data
                ]
        # Handle cases for existing and new entry
        if not stored_data:
            logger.debug(f"Writing new data for {meta_md5} ...")
            # New entry; add as is
            data_to_write.update(
                {
                    "element": element,
                    "data": data,
                    # for serialization / deserialization of storage type
                    "kind": kind,
                }
            )
        elif stored_data:
            # Set up stored kwargs
            stored_kwargs = [
                key
                for key in stored_data.keys()
                if key not in ("element", "data")
            ]
            # Set up to be stored kwargs
            to_be_stored_kwargs = kwargs
            # Update with kind
            to_be_stored_kwargs["kind"] = kind
            # Validate the kwargs
            if set(stored_kwargs) != set(to_be_stored_kwargs):
                raise_error(
                    msg=(
                        f"The additional data for {meta_md5} do not match "
                        "the ones already stored. This can be due "
                        "to some changes in marker computation, please "
                        "verify and try again."
                    ),
                    klass=RuntimeError,
                )

            # Check for duplicate elements; if found, return immediately
            logger.debug(f"Checking duplicate elements for {meta_md5} ...")
            for stored_element in stored_data["element"]:
                if stored_element == element[0]:
                    logger.info(
                        f"Duplicate element: {element[0]} found for "
                        f"{meta_md5}, skipping store ... "
                    )
                    return None
            logger.debug(f"No duplicate elements found for {meta_md5} ...")

            logger.debug(
                f"Existing data found for {meta_md5}, appending to it ..."
            )

            t_data = stored_data["data"]
            if kind in ["timeseries", "scalar_table", "timeseries_2d"]:
                t_data += data
            else:
                t_data = np.concatenate((t_data, data), axis=-1)
            # Existing entry; append to existing
            # "element" and "data"
            data_to_write.update(
                {
                    "element": stored_data["element"] + element,
                    "data": t_data,
                    # for serialization / deserialization of storage type
                    "kind": kind,
                }
            )

        logger.info(f"Writing HDF5 data for {meta_md5} to: {uri}")
        logger.debug(f"HDF5 overwrite is set to: {self.overwrite} ...")
        logger.debug(
            f"HDF5 gzip compression level is set to: {self.compression} ..."
        )

        # Write data
        self._write_processed_data(
            fname=uri,
            processed_data=data_to_write,
            title=meta_md5,
        )

        logger.info(f"Wrote HDF5 data for {meta_md5} to: {uri}")

    def store_matrix(
        self,
        meta_md5: str,
        element: dict[str, str],
        data: np.ndarray,
        col_names: Optional[Iterable[str]] = None,
        row_names: Optional[Iterable[str]] = None,
        matrix_kind: str = "full",
        diagonal: bool = True,
        row_header_col_name: str = "ROI",
    ) -> None:
        """Store matrix.

        This method performs parameter checks and then calls
        ``_store_data`` for storing the data.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as dictionary.
        data : numpy.ndarray
            The matrix data to store.
        col_names : list or tuple of str, optional
            The column labels (default None).
        row_names : list or tuple of str, optional
            The row labels (default None).
        matrix_kind : str, optional
            The kind of matrix:

            * ``triu`` : store upper triangular only
            * ``tril`` : store lower triangular
            * ``full`` : full matrix

            (default "full").
        diagonal : bool, optional
            Whether to store the diagonal. If ``matrix_kind`` is "full",
            setting this to False will raise an error (default True).
        row_header_col_name : str, optional
            The column name for the row header column (default "ROI").

        Raises
        ------
        ValueError
            If invalid ``matrix_kind`` is provided, ``diagonal = False``
            for ``matrix_kind = "full"``, non-square data is provided
            for ``matrix_kind = {"triu", "tril"}``, length of ``row_names``
            do not match data row count, or length of ``col_names`` do not
            match data column count.

        """
        # Row data validation
        if row_names is None:
            row_names = [f"r{i}" for i in range(data.shape[0])]
        # Column data validation
        if col_names is None:
            col_names = [f"c{i}" for i in range(data.shape[1])]
        # Parameter checks
        store_matrix_checks(
            matrix_kind=matrix_kind,
            diagonal=diagonal,
            data_shape=data.shape,
            row_names_len=len(row_names),  # type: ignore
            col_names_len=len(col_names),  # type: ignore
        )
        # Store
        self._store_data(
            kind="matrix",
            meta_md5=meta_md5,
            element=[element],  # convert to list
            data=data[:, :, np.newaxis],  # convert to 3D
            column_headers=col_names,
            row_headers=row_names,
            matrix_kind=matrix_kind,
            diagonal=diagonal,
            row_header_column_name=row_header_col_name,
        )

    def store_vector(
        self,
        meta_md5: str,
        element: dict[str, str],
        data: Union[np.ndarray, list],
        col_names: Optional[Iterable[str]] = None,
    ) -> None:
        """Store vector.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as dictionary.
        data : numpy.ndarray or list
            The vector data to store.
        col_names : list or tuple of str, optional
            The column labels (default None).

        """
        if isinstance(data, list):
            logger.debug(
                f"Flattening and converting vector data list for {meta_md5}, "
                "to numpy.ndarray ..."
            )
            # Flatten out list and convert to np.ndarray
            processed_data = np.array(np.ravel(data))
        elif isinstance(data, np.ndarray):
            logger.debug(
                f"Flattening vector data numpy.ndarray for {meta_md5} ..."
            )
            # Flatten out array
            processed_data = data.ravel()

        self._store_data(
            kind="vector",
            meta_md5=meta_md5,
            element=[element],  # convert to list
            data=processed_data[:, np.newaxis],  # convert to 2D
            column_headers=col_names,
        )

    def store_timeseries(
        self,
        meta_md5: str,
        element: dict[str, str],
        data: np.ndarray,
        col_names: Optional[Iterable[str]] = None,
    ) -> None:
        """Store timeseries.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as dictionary.
        data : numpy.ndarray
            The timeseries data to store.
        col_names : list or tuple of str, optional
            The column labels (default None).

        """
        self._store_data(
            kind="timeseries",
            meta_md5=meta_md5,
            element=[element],  # convert to list
            data=[data],  # convert to list
            column_headers=col_names,
            row_header_column_name="timepoint",
        )

    def store_timeseries_2d(
        self,
        meta_md5: str,
        element: dict[str, str],
        data: np.ndarray,
        col_names: Optional[Iterable[str]] = None,
        row_names: Optional[Iterable[str]] = None,
    ) -> None:
        """Store a 2D timeseries.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as dictionary.
        data : numpy.ndarray
            The 2D timeseries data to store.
        col_names : list or tuple of str, optional
            The column labels (default None).
        row_names : list or tuple of str, optional
            The row labels (default None).

        """
        store_timeseries_2d_checks(
            data_shape=data.shape,
            row_names_len=len(row_names),  # type: ignore
            col_names_len=len(col_names),  # type: ignore
        )
        self._store_data(
            kind="timeseries_2d",
            meta_md5=meta_md5,
            element=[element],  # convert to list
            data=[data],  # convert to list
            column_headers=col_names,
            row_headers=row_names,
        )

    def store_scalar_table(
        self,
        meta_md5: str,
        element: dict,
        data: np.ndarray,
        col_names: Optional[Iterable[str]] = None,
        row_names: Optional[Iterable[str]] = None,
        row_header_col_name: Optional[str] = "feature",
    ) -> None:
        """Store table with scalar values.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        data : numpy.ndarray
            The scalar table data to store.
        col_names : list or tuple of str, optional
            The column labels (default None).
        row_names : str, optional
            The row labels (default None).
        row_header_col_name : str, optional
            The column name for the row header column (default "feature").

        """
        self._store_data(
            kind="scalar_table",
            meta_md5=meta_md5,
            element=[element],  # convert to list
            data=[data],  # convert to list
            column_headers=col_names,
            row_headers=row_names,
            row_header_column_name=row_header_col_name,
        )

    def collect(self) -> None:
        """Implement data collection.

        This method globs the element files and runs a loop
        over them while reading metadata and then runs a loop
        over all the stored features in the metadata, storing
        the metadata and the feature data right after reading.

        Raises
        ------
        NotImplementedError
            If ``single_output`` is True.

        """
        if self.single_output is True:
            raise_error(
                msg="collect() is not implemented for single output.",
                klass=NotImplementedError,
            )

        # Glob files
        globbed_files = list(
            self.uri.parent.glob(f"*_{self.uri.name}")  # type: ignore
        )

        # Create new storage instance
        out_storage = HDF5FeatureStorage(uri=self.uri, overwrite="update")

        # Run loop to collect metadata
        logger.info(
            f"Collecting metadata from {self.uri.parent}/*_{self.uri.name}"  # type: ignore
        )
        # Collect element files per feature MD5
        elements_per_feature_md5 = defaultdict(list)
        out_metadata = {}
        for file_ in tqdm(globbed_files, desc="file-metadata"):
            logger.debug(f"Reading HDF5 file: {file_} ...")
            # Create new storage instance to load metadata
            in_storage = HDF5FeatureStorage(uri=file_)
            # Load metadata from new instance
            in_metadata = in_storage._read_metadata()

            logger.debug(f"Updating HDF5 metadata with metadata from: {file_}")

            # Update metadata to store
            out_metadata.update(in_metadata)

            # Update element files for found MD5s
            for feature_md5 in in_metadata.keys():
                elements_per_feature_md5[feature_md5].append(file_)

        logger.info("Writing metadata to HDF5 file ...")
        # Save metadata out metadata
        out_storage._write_processed_data(
            fname=str(self.uri.resolve()),  # type: ignore
            processed_data=out_metadata,
            title="meta",
        )

        # Run loop to collect data per feature per file
        logger.info(
            f"Collecting data from {self.uri.parent}/*_{self.uri.name}"  # type: ignore
        )
        logger.info(f"Will collect {len(elements_per_feature_md5)} features.")

        # Print info before to avoid tqdm progress bar interference
        for feature_md5, element_files in elements_per_feature_md5.items():
            logger.info(
                f"Collecting {len(element_files)} files for feature MD5: "
                f"{feature_md5}."
            )

        for feature_md5, element_files in tqdm(
            elements_per_feature_md5.items(), desc="feature"
        ):
            element_count = len(element_files)

            i_file = 0
            i_chunk = 0
            t_chunk_size = min(self.chunk_size, element_count)
            chunk_data = []
            elements = []
            static_data = None
            kind = None
            for file_ in tqdm(element_files, desc="file-data"):
                logger.debug(
                    f"Reading feature MD5: '{feature_md5}' "
                    f"from HDF5 file: {file_} ..."
                )

                # Read the data
                t_data = read_hdf5(
                    fname=str(file_),
                    title=feature_md5,
                    slash="ignore",
                )
                if i_file == 0:
                    # Store the "static" data
                    static_data = {
                        k: v
                        for k, v in t_data.items()
                        if k not in ["data", "element"]
                    }
                    kind = static_data["kind"]

                # Append the "dynamic" data
                if kind in ["timeseries", "scalar_table", "timeseries_2d"]:
                    chunk_data.extend(t_data["data"])
                else:
                    chunk_data.append(t_data["data"])
                elements.extend(t_data["element"])

                i_file += 1
                if (i_file % t_chunk_size == 0) or i_file == element_count:
                    # If we have reached the chunk size or the end of the
                    # elements, write the data

                    # Store one chunk of data
                    to_write = static_data.copy()
                    to_write["element"] = []
                    # Write data in chunks to avoid memory usage spikes
                    # Start with the case for 2D
                    # Write chunked array
                    to_write["data"] = _create_chunk(
                        chunk_data=chunk_data,
                        kind=kind,
                        element_count=element_count,
                        chunk_size=t_chunk_size,
                        i_chunk=i_chunk,
                    )
                    if i_file == element_count:
                        to_write["element"] = elements

                    # Write to HDF5
                    write_hdf5(
                        fname=str(self.uri.resolve()),  # type: ignore
                        data=to_write,
                        overwrite="update",  # type: ignore
                        compression=0,
                        title=feature_md5,
                        slash="error",
                        use_json=False,
                    )

                    # Increment counters and data
                    i_chunk += 1
                    chunk_data = []
