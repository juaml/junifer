"""Provide concrete implementation for feature storage via HDF5."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
#          Federico Raimondo <f.raimondo@fz-juelich.de>
# License: AGPL


from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

import numpy as np
import pandas as pd
from h5io import read_hdf5, write_hdf5
from tqdm import tqdm

from ..api.decorators import register_storage
from ..utils import logger, raise_error
from .base import BaseFeatureStorage
from .utils import element_to_prefix


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
    **kwargs : dict
        The keyword arguments passed to the superclass.

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
        **kwargs: str,
    ) -> None:
        # Convert str to Path
        if not isinstance(uri, Path):
            uri = Path(uri)

        # Create parent directories if not present
        if not uri.parent.exists():
            logger.info(
                f"Output directory ({str(uri.parent.absolute())}) "
                "does not exist, creating now."
            )
            uri.parent.mkdir(parents=True, exist_ok=True)

        # Available storage kinds
        storage_types = ["table", "timeseries", "matrix"]

        super().__init__(
            uri=uri,
            storage_types=storage_types,
            single_output=single_output,
            **kwargs,
        )

        self.overwrite = overwrite
        self.compression = compression
        # Tracks whether to bypass element checks after collection
        self._collected = False

    def get_valid_inputs(self) -> List[str]:
        """Get valid storage types for input.

        Returns
        -------
        list of str
            The list of storage types that can be used as input for this
            storage.

        """
        return ["matrix", "table", "timeseries"]

    def _fetch_correct_uri_for_io(self, element: Optional[Dict]) -> str:
        """Return proper URI for I/O based on `element`.

        Parameters
        ----------
        element : dict, optional
            The element as dictionary (default None).

        Returns
        -------
        str
            Formatted URI for accessing metadata and data.

        """
        prefix = ""
        if not self.single_output:
            if not element and not self._collected:
                raise_error(
                    msg=(
                        "`element` must be provided when `single_output` "
                        "is False"
                    ),
                    klass=RuntimeError,
                )
            elif element and not self._collected:
                prefix = element_to_prefix(element=element)
        # Format URI
        return f"{self.uri.parent}/{prefix}{self.uri.name}"  # type: ignore

    def _read_metadata(
        self, element: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Read metadata (should not be called directly).

        Parameters
        ----------
        element : dict, optional
            The element as dictionary (default None).

        Returns
        -------
        list of dict
            The stored metadata for the element.

        Raises
        ------
        IOError
            If HDF5 file does not exist.

        """
        # Get correct URI for element;
        # is different from uri if single_output is False
        uri = self._fetch_correct_uri_for_io(element=element)

        try:
            logger.info(f"Loading HDF5 metadata from: {uri}")
            metadata = read_hdf5(
                fname=uri,
                title="meta",
                slash="ignore",
            )
        except IOError:
            raise_error(
                msg=f"HDF5 file not found at: {uri}",
                klass=IOError,
            )
        else:
            logger.info(f"Loaded HDF5 metadata from: {uri}")
            # Convert to list if single entry found
            if not isinstance(metadata, list):
                metadata = [metadata]
            return metadata

    def list_features(self) -> Dict[str, Dict[str, Any]]:
        """List the features in the storage.

        Returns
        -------
        dict
            List of features in the storage. The keys are the feature names to
            be used in :func:`read_df` and the values are the metadata of each
            feature.

        """
        # Read metadata
        metadata = self._read_metadata()

        # Initialize dictionary to populate
        meta_listing = {}
        for meta in metadata:
            # Make a copy so as not to affect original metadata
            meta_copy = meta.copy()
            # Format metadata as key-value pair
            meta_key = meta_copy.pop("meta_md5")
            meta_listing[meta_key] = meta_copy

        return meta_listing

    def _read_data(
        self, md5: str, element: Optional[Dict[str, str]] = None
    ) -> Dict:
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
        IOError
            If HDF5 file does not exist.

        """
        # Get correct URI for element;
        # is different from uri if single_output is False
        uri = self._fetch_correct_uri_for_io(element=element)

        try:
            logger.info(f"Loading HDF5 data for {md5} from: {uri}")
            data = read_hdf5(
                fname=uri,
                title=md5,
                slash="ignore",
            )
        except IOError:
            raise_error(
                msg=f"HDF5 file not found at: {uri}",
                klass=IOError,
            )
        else:
            logger.info(f"Loaded HDF5 data for {md5} from: {uri}")
            return data

    def _index_dict_to_multiindex(
        self,
        index_dict: Dict[Union[str, Iterable[str]], Union[str, Iterable[str]]],
        index_columns_order: List[str],
        n_rows: int,
    ) -> pd.MultiIndex:
        """Convert index to pandas.MultiIndex (should not be called directly).

        Parameters
        ----------
        index_dict : dict
            The index data as returned by
            :func:`_element_metadata_to_index_dict`.
        index_columns_order: list of str
            The ordering for index columns.
        n_rows : int
            Number of rows for the index.

        Returns
        -------
        pandas.MultiIndex
            The multi-index for use in :func:`read_df`.

        """
        logger.debug("Converting index dictionary to pandas MultiIndex ...")
        # Create multi-index; dict comprehension required to undo keys sorting
        # during serialization / deserialization
        index = pd.MultiIndex.from_frame(
            pd.DataFrame(
                data={key: index_dict[key] for key in index_columns_order},
                index=range(n_rows),
            )
        )
        logger.debug("Converted index dictionary to pandas MultiIndex ...")
        return index

    def read_df(
        self,
        feature_name: Optional[str] = None,
        feature_md5: Optional[bool] = None,
        element: Optional[Dict[str, str]] = None,
    ) -> pd.DataFrame:
        """Read feature into a pandas DataFrame.

        Either one of ``feature_name`` or ``feature_md5`` needs to be
        specified.

        Parameters
        ----------
        feature_name : str, optional
            Name of the feature to read (default None).
        feature_md5 : str, optional
            MD5 hash of the feature to read (default None).
        element : dict, optional
            The element as dictionary (default None).

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
        # Parameter check pass
        else:
            # Read metadata
            metadata = self._read_metadata(element=element)
            # Get correct URI for element;
            # is different from uri if single_output is False
            uri = self._fetch_correct_uri_for_io(element=element)
            # Initialize MD5 variable
            md5: str = ""

            # Consider feature_md5
            if feature_md5 and not feature_name:
                logger.debug(
                    f"Validating feature MD5 '{feature_md5}' in metadata "
                    f"for: {uri} ..."
                )
                # Validate MD5
                for meta in metadata:
                    if meta["meta_md5"] == feature_md5:
                        md5 = feature_md5  # type: ignore
                if not md5:
                    raise_error(msg=f"Feature MD5 {feature_md5} not found")

            # Consider feature_name
            elif not feature_md5 and feature_name:
                logger.debug(
                    f"Validating feature name '{feature_name}' in metadata "
                    f"for: {uri} ..."
                )
                # Retrieve MD5 for feature_name
                # Implicit counter for duplicate feature_name
                feature_name_query = []
                for meta in metadata:
                    if meta["name"] == feature_name:
                        feature_name_query.append(meta)

                # Check for no / duplicate feature_name
                if len(feature_name_query) == 0:
                    raise_error(msg=f"Feature {feature_name} not found")
                elif len(feature_name_query) > 1:
                    raise_error(
                        msg=(
                            f"More than one feature with name {feature_name} "
                            "found. You can bypass this issue by specifying "
                            "a `feature_md5`."
                        )
                    )

                md5 = feature_name_query[0]["meta_md5"]

            # Read data from HDF5
            hdf_data = self._read_data(md5=md5, element=element)

            # Generate index for the data
            hdf_data_index = self._index_dict_to_multiindex(
                index_dict=hdf_data["idx_data"],
                index_columns_order=hdf_data["idx_columns_order"],
                n_rows=hdf_data["n_rows"],
            )

            logger.debug(
                f"Converting HDF5 data for {md5} to pandas.DataFrame ..."
            )
            # Convert to DataFrame
            df = pd.DataFrame(
                data=hdf_data["data"],
                index=hdf_data_index,
                columns=hdf_data["column_headers"],
                dtype=hdf_data["data"].dtype,
            )
            logger.debug(
                f"Converted HDF5 data for {md5} to pandas.DataFrame ..."
            )

            return df

    def _write_processed_data(
        self, fname: str, processed_data: Dict[str, Any], title: str
    ) -> None:
        """Write processed data to HDF5 (should not be called directly).

        This is used primarily in ``_store_metadata`` and ``_store_data``.

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

    def store_metadata(self, meta_md5: str, element: Dict, meta: Dict) -> None:
        """Store metadata.

        This method first loads existing metadata (if any) using
        ``_read_metadata`` and appends to it the new metadata and then saves
        the updated metadata using ``_write_processed_data``.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        meta : dict
            The metadata as a dictionary.

        """
        # Update meta dictionary with MD5
        meta.update({"meta_md5": meta_md5})

        # Read metadata; if no file found, create an empty list
        try:
            metadata = self._read_metadata(element=element)
        except IOError:
            logger.debug(f"Creating new metadata list for {meta_md5} ...")
            metadata = []

        logger.debug(f"HDF5 metadata for {meta_md5} updated ...")
        # Update metadata
        metadata.append(meta)

        # Get correct URI for element;
        # is different from uri if single_output is False
        uri = self._fetch_correct_uri_for_io(element=element)

        logger.info(f"Writing HDF5 metadata for {meta_md5} to: {uri}")
        logger.debug(f"HDF5 overwrite is set to: {self.overwrite} ...")
        logger.debug(
            f"HDF5 gzip compression level is set to: {self.compression} ..."
        )

        # Write metadata
        self._write_processed_data(
            fname=uri,
            processed_data=meta,
            title="meta",
        )

        logger.info(f"Wrote HDF5 metadata for {meta_md5} to: {uri}")

    def _element_metadata_to_index_dict(
        self,
        element: Dict,
        n_rows: int = 1,
        row_headers: Union[str, Iterable[str], None] = None,
    ) -> Dict[
        str,
        Union[Dict[Union[str, Iterable[str]], Union[str, Iterable[str]]], int],
    ]:
        """Convert the element meta to index (should not be called directly).

        This method is only used in ``_store_data``.

        Parameters
        ----------
        element : dict
            The element as dictionary.
        n_rows : int, optional
            Number of rows to create (default 1).
        row_headers: str, list or tuple of str, optional
            The column name to use in case ``n_rows`` > 1. If None and
            ``n_rows`` > 1, the name will be "idx" (default None).

        Returns
        -------
        dict
            The index to store. Is used for creating index for
            pandas.DataFrame returned by :func:`read_df`.

        """
        logger.debug(
            "Converting element metadata to index dictionary for "
            "HDF5 storage ..."
        )

        # Check row_headers
        if not row_headers:
            row_headers = "idx"

        # Create dictionary with element access options as keys
        # and corresponding access values as values for n_rows
        element_index: Dict[
            Union[str, Iterable[str]], Union[str, Iterable[str]]
        ] = {key: [val] * n_rows for key, val in element.items()}
        # Set index value for row_headers
        element_index[row_headers] = np.arange(n_rows)

        logger.debug(
            "Converted element metadata to index dictionary for "
            "HDF5 storage ..."
        )

        return {
            "idx_data": element_index,
            # required as deserialization sorts keys of the index dict
            "idx_columns_order": list(element_index.keys()),  # type: ignore
            "n_rows": n_rows,
        }

    def _store_data(
        self,
        meta_md5: str,
        element: Dict[str, str],
        data: Union[np.ndarray, List],
        column_headers: Union[str, Iterable[str], None] = None,
        row_headers: Union[str, Iterable[str], None] = None,
    ) -> None:
        """Store data.

        This method first prepares the index for the element's metadata
        using :func:`_element_metadata_to_index_dict` and updates
        the `data` with the index and then saves the data using
        :func:`_write_processed_data`.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as dictionary.
        data : numpy.ndarray or list
            The data to store.
        column_headers : str, list or tuple of str, optional
            The column labels (default None).
        row_headers : str, list or tuple of str, optional
            The column label to use in case number of rows greater than 1.
            If None and number of rows greater than 1, then the name will be
            "idx". For matrix storage, they are the row labels. (default None).

        """
        # Get correct URI for element;
        # is different from uri if single_output is False
        uri = self._fetch_correct_uri_for_io(element=element)

        # Initialize dictionary to aggregate data to write
        data_to_write = {
            "md5": meta_md5,
            "element": element,
            "data": data,
            "column_headers": column_headers,
            "row_headers": row_headers,
        }
        # Add index data to store
        index_data = self._element_metadata_to_index_dict(
            element=element,
            n_rows=len(data),
            row_headers=row_headers,
        )
        data_to_write.update(index_data)  # type: ignore

        logger.info(f"Writing HDF5 data to: {uri}")
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

        logger.info(f"Wrote HDF5 data to: {uri}")

    def store_matrix(
        self,
        meta_md5: str,
        element: Dict[str, str],
        data: np.ndarray,
        col_names: Optional[Iterable[str]] = None,
        row_names: Optional[Iterable[str]] = None,
        matrix_kind: Optional[str] = "full",
        diagonal: bool = True,
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
            Whether to store the diagonal. If `matrix_kind` is "full", setting
            this to False will raise an error (default True).

        """
        # diagonal validation
        if diagonal is False and matrix_kind not in ["triu", "tril"]:
            raise_error(
                msg="Diagonal cannot be False if kind is not full",
                klass=ValueError,
            )
        # matrix_kind and shape validation
        if matrix_kind in ["triu", "tril"]:
            if data.shape[0] != data.shape[1]:
                raise_error(
                    "Cannot store a non-square matrix as a triangular matrix",
                    klass=ValueError,
                )
        # matrix_kind validation and computation
        if matrix_kind == "triu":
            k = 0 if diagonal is True else 1
            data_idx = np.triu_indices(data.shape[0], k=k)
        elif matrix_kind == "tril":
            k = 0 if diagonal is True else -1
            data_idx = np.tril_indices(data.shape[0], k=k)
        elif matrix_kind == "full":
            data_idx = (
                np.repeat(np.arange(data.shape[0]), data.shape[1]),
                np.tile(np.arange(data.shape[1]), data.shape[0]),
            )
        else:
            raise_error(msg=f"Invalid kind {matrix_kind}", klass=ValueError)

        # Row data and label validation
        if row_names is None:
            row_names = [f"r{i}" for i in range(data.shape[0])]
        elif len(row_names) != data.shape[0]:  # type: ignore
            raise_error(
                msg="Number of row names does not match number of rows",
                klass=ValueError,
            )

        # Column data and label validation
        if col_names is None:
            col_names = [f"c{i}" for i in range(data.shape[1])]
        elif len(col_names) != data.shape[1]:  # type: ignore
            raise_error(
                msg="Number of column names does not match number of columns",
                klass=ValueError,
            )

        # Subset data
        flat_data = data[data_idx]
        # Format column names
        columns = [
            f"{row_names[i]}~{col_names[j]}"  # type: ignore
            for i, j in zip(data_idx[0], data_idx[1])
        ]
        # Store
        self._store_data(
            meta_md5=meta_md5,
            element=element,
            data=flat_data[None, :],
            column_headers=columns,
            row_headers=None,
        )

    def store_table(
        self,
        meta_md5: str,
        element: Dict[str, str],
        data: Union[np.ndarray, List],
        columns: Optional[Iterable[str]] = None,
        rows_col_name: Optional[str] = None,
    ) -> None:
        """Store table.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as dictionary.
        data : numpy.ndarray or list
            The table data to store.
        columns : list or tuple of str, optional
            The columns (default None).
        rows_col_name : str, optional
            The column name to use in case number of rows greater than 1.
            If None and number of rows greater than 1, then the name will be
            "index" (default None).

        """
        self._store_data(
            meta_md5=meta_md5,
            element=element,
            data=data,
            column_headers=columns,
            row_headers=rows_col_name,
        )

    def store_timeseries(
        self,
        meta_md5: str,
        element: Dict[str, str],
        data: np.ndarray,
        columns: Optional[Iterable[str]] = None,
    ) -> None:
        """Implement timeseries storing.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as dictionary.
        data : numpy.ndarray
            The timeseries data to store.
        columns : list or tuple of str, optional
            The column labels (default None).

        """
        self._store_data(
            meta_md5=meta_md5,
            element=element,
            data=data,
            column_headers=columns,
            row_headers="timepoint",
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

        logger.info(
            "Collecting data from "
            f"{self.uri.parent}/*{self.uri.name}"  # type: ignore
        )

        # Create new storage instance
        out_storage = HDF5FeatureStorage(uri=self.uri, overwrite="update")

        # Glob files
        globbed_files = self.uri.parent.glob(
            f"*{self.uri.name}"
        )  # type: ignore

        # Run loop to aggregate
        for file in tqdm(globbed_files, desc="file"):
            logger.debug(f"Reading HDF5 file: {file.resolve()} ...")
            # Create new storage instance to load data
            in_storage = HDF5FeatureStorage(uri=file)

            # Load metadata from new instance
            in_metadata = in_storage._read_metadata()

            logger.info(
                f"Updating HDF5 metadata with metadata from: {file.resolve()}"
            )
            # Load metadata; empty list if first entry
            try:
                out_metadata = out_storage._read_metadata()
            except IOError:
                out_metadata = []
            # Update metadata
            out_metadata.append(in_metadata)
            # Save metadata
            out_storage._write_processed_data(
                fname=self.uri.resolve(),
                processed_data=out_metadata,
                title="meta",
            )

            for meta in tqdm(in_metadata, desc="feature"):
                logger.debug(f"Collecting feature MD5: {meta['meta_md5']} ...")
                # Load data from new instance
                in_data = in_storage._read_data(md5=meta["meta_md5"])

                logger.info(
                    f"Updating HDF5 data with data from: {meta['meta_md5']}"
                )
                # Save data
                out_storage._write_processed_data(
                    fname=self.uri.resolve(),
                    processed_data=in_data,
                    title=meta["meta_md5"],
                )

        # Toggle check to bypass element checks
        self._collected = True
