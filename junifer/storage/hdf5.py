"""Provide concrete implementation for feature storage via HDF5."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL


from collections import defaultdict
from functools import reduce
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

import numpy as np
import pandas as pd
from tqdm import tqdm

from ..api.decorators import register_storage
from ..external.h5io.h5io import ChunkedArray, has_hdf5, read_hdf5, write_hdf5
from ..utils import logger, raise_error
from .base import BaseFeatureStorage
from .utils import element_to_prefix, matrix_to_vector, store_matrix_checks


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
        :meth:`junifer.storage.HDF5FeatureStorage.collect`. If the file count
        is smaller than the value, the minimum is used (default 100).

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
        storage_types = ["vector", "timeseries", "matrix"]

        super().__init__(
            uri=uri,
            storage_types=storage_types,
            single_output=single_output,
        )

        self.overwrite = overwrite
        self.compression = compression
        self.force_float32 = force_float32
        self.chunk_size = chunk_size

    def get_valid_inputs(self) -> List[str]:
        """Get valid storage types for input.

        Returns
        -------
        list of str
            The list of storage types that can be used as input for this
            storage.

        """
        return ["matrix", "vector", "timeseries"]

    def _fetch_correct_uri_for_io(self, element: Optional[Dict]) -> str:
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
                    "`element` must be provided when `single_output` "
                    "is False"
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
        self, element: Optional[Dict[str, str]] = None
    ) -> Dict[str, Dict[str, Any]]:
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
        logger.info(f"Loading HDF5 metadata from: {uri}")
        metadata = read_hdf5(
            fname=uri,
            title="meta",
            slash="ignore",
        )
        logger.info(f"Loaded HDF5 metadata from: {uri}")

        return metadata

    def list_features(self) -> Dict[str, Dict[str, Any]]:
        """List the features in the storage.

        Returns
        -------
        dict
            List of features in the storage. The keys are the feature MD5 to
            be used in :meth:`junifer.storage.HDF5FeatureStorage.read_df`
            and the values are the metadata of each feature.

        """
        # Read metadata
        metadata = read_hdf5(
            fname=str(self.uri.resolve()),  # type: ignore
            title="meta",
            slash="ignore",
        )
        return metadata

    def _read_data(
        self, md5: str, element: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
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
        logger.info(f"Loading HDF5 data for {md5} from: {uri}")
        data = read_hdf5(
            fname=uri,
            title=md5,
            slash="ignore",
        )
        logger.info(f"Loaded HDF5 data for {md5} from: {uri}")

        return data

    def read_df(
        self,
        feature_name: Optional[str] = None,
        feature_md5: Optional[bool] = None,
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
        reshaped_data = hdf_data["data"]

        # Generate index for the data
        logger.debug(f"Generating pandas.MultiIndex for {md5} ...")

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
            for idx, element in enumerate(hdf_data["element"]):
                # Get row count for the element
                n_rows, _ = hdf_data["data"][:, :, idx].shape
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
            reshaped_data = hdf_data["data"].reshape(-1, 1)

        # Create dataframe for index
        idx_df = pd.DataFrame(data=element_idx)  # type: ignore
        # Create multiindex from dataframe
        hdf_data_idx = pd.MultiIndex.from_frame(df=idx_df)
        logger.debug(f"Generated pandas.MultiIndex for {md5} ...")

        # Convert to DataFrame
        logger.debug(f"Converting HDF5 data for {md5} to pandas.DataFrame ...")
        df = pd.DataFrame(
            data=reshaped_data,
            index=hdf_data_idx,
            columns=columns,  # type: ignore
            dtype=hdf_data["data"].dtype,
        )
        logger.debug(f"Converted HDF5 data for {md5} to pandas.DataFrame ...")

        return df

    def _write_processed_data(
        self, fname: str, processed_data: Dict[str, Any], title: str
    ) -> None:
        """Write processed data to HDF5 (should not be called directly).

        This is used primarily in
        :func:`junifer.storage.HDF5FeatureStorage.store_metadata` and
        ``_store_data``.

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
        element: Dict[str, str],
        meta: Dict[str, Any],
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
        element: List[Dict[str, str]],
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
        kind : {"matrix", "vector", "timeseries"}
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
        if data.dtype == np.dtype("float64") and self.force_float32:
            data = data.astype(dtype=np.dtype("float32"), casting="same_kind")

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
            # Existing entry; append to existing
            # "element" and "data"
            data_to_write.update(
                {
                    "element": stored_data["element"] + element,
                    "data": np.concatenate(
                        (stored_data["data"], data), axis=-1
                    ),
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
        element: Dict[str, str],
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
        element: Dict[str, str],
        data: Union[np.ndarray, List],
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
        element: Dict[str, str],
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
            data=data[:, :, np.newaxis],  # convert to 3D
            column_headers=col_names,
            row_header_column_name="timepoint",
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
        globbed_files = self.uri.parent.glob(  # type: ignore
            f"*{self.uri.name}"  # type: ignore
        )

        # Create new storage instance
        out_storage = HDF5FeatureStorage(uri=self.uri, overwrite="update")

        # Run loop to collect metadata
        logger.info(
            "Collecting metadata from "
            f"{self.uri.parent}/*{self.uri.name}"  # type: ignore
        )
        # Collect element files per feature MD5
        elements_per_feature_md5 = defaultdict(list)
        for file_ in tqdm(globbed_files, desc="file-metadata"):
            logger.debug(f"Reading HDF5 file: {file_} ...")
            # Create new storage instance to load metadata
            in_storage = HDF5FeatureStorage(uri=file_)
            # Load metadata from new instance
            in_metadata = in_storage._read_metadata()

            logger.info(f"Updating HDF5 metadata with metadata from: {file_}")
            # Load metadata; empty dictionary if first entry;
            # can be replaced with store_metadata() if run on a loop
            # for the metadata entries from in_storage
            try:
                out_metadata = out_storage._read_metadata()
            except IOError:
                out_metadata = {}
            # Update metadata
            out_metadata.update(in_metadata)
            # Save metadata
            out_storage._write_processed_data(
                fname=str(self.uri.resolve()),  # type: ignore
                processed_data=out_metadata,
                title="meta",
            )
            # Update element files for found MD5s
            for feature_md5 in in_metadata.keys():
                elements_per_feature_md5[feature_md5].append(file_)

        # Run loop to collect data per feature per file
        logger.info(
            "Collecting data from "
            f"{self.uri.parent}/*{self.uri.name}"  # type: ignore
        )
        for feature_md5, element_files in tqdm(
            elements_per_feature_md5.items(), desc="feature"
        ):
            element_count = len(element_files)
            # Chunk size for collecting
            chunk_size = min(self.chunk_size, element_count)
            # Operate on chunks
            for chunk_idx, chunk_start in tqdm(
                enumerate(range(0, element_count, chunk_size)), desc="chunk"
            ):
                # Store the chunk files' data
                stored_data_for_chunk: List[Dict[str, Any]] = []
                # Read the files of a chunk
                for i in tqdm(
                    range(chunk_start, chunk_start + chunk_size),
                    desc="file-data",
                ):
                    file_ = element_files[i]
                    logger.debug(
                        f"Reading feature MD5: '{feature_md5}' "
                        f"from HDF5 file: {file_} ..."
                    )
                    # Read from HDF5 and collect data
                    stored_data_for_chunk.append(
                        read_hdf5(
                            fname=str(file_),
                            title=feature_md5,
                            slash="ignore",
                        )
                    )

                # Concatenate the features data for a chunk
                features_data = np.concatenate(
                    [x["data"] for x in stored_data_for_chunk], axis=-1
                )
                # Make dictionary to write the collected data;
                # first the static data then the dynamic data
                data_to_write = {
                    key: val
                    for key, val in stored_data_for_chunk[0].items()
                    if key not in ("data", "element")
                }
                # Join the features element for a chunk
                data_to_write["element"] = reduce(
                    lambda acc, elem: acc + elem,
                    [x["element"] for x in stored_data_for_chunk],
                    [],
                )
                # Write data in chunks to avoid memory usage spikes
                # Start with the case for 2D
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
                # Write chunked array
                data_to_write["data"] = ChunkedArray(
                    data=features_data,
                    shape=tuple(array_shape),
                    chunk_size=tuple(array_chunk_size),
                    n_chunk=chunk_idx,
                )
                # Write to HDF5
                write_hdf5(
                    fname=str(self.uri.resolve()),  # type: ignore
                    data=data_to_write,
                    overwrite=self.overwrite,  # type: ignore
                    compression=0,
                    title=feature_md5,
                    slash="error",
                    use_json=False,
                )
