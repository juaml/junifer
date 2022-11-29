"""Provide concrete implementation for feature storage via SQLite."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

import json
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from pandas.core.base import NoNewAttributesMixin
from pandas.io.sql import pandasSQL_builder  # type: ignore
from sqlalchemy import create_engine, inspect
from tqdm import tqdm

from ..api.decorators import register_storage
from ..utils import logger, raise_error, warn_with_log
from .pandas_base import PandasBaseFeatureStorage
from .utils import element_to_prefix


if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


@register_storage
class SQLiteFeatureStorage(PandasBaseFeatureStorage):
    """Concrete implementation for feature storage via SQLite.

    Parameters
    ----------
    uri : str or pathlib.Path
        The path to the file to be used.
    single_output : bool, optional
        If False, will create one file per element. The name
        of the file will be prefixed with the respective element.
        If True, will create only one file as specified in the `uri` and
        store all the elements in the same file. This behaviour is only
        suitable for non-parallel executions. SQLite does not support
        concurrency (default True).
    upsert : {"ignore", "update"}, optional
        Upsert mode. If "ignore" is used, the existing elements are ignored.
        If "update", the existing elements are updated (default "update").
    **kwargs : dict
            The keyword arguments passed to the superclass.

    See Also
    --------
    PandasBaseFeatureStorage : The base class for Pandas-based feature storage.

    """

    def __init__(
        self,
        uri: Union[str, Path],
        single_output: bool = True,
        upsert: str = "update",
        **kwargs: str,
    ) -> None:
        # Check upsert argument value
        if upsert not in ["update", "ignore"]:
            raise_error(
                msg=(
                    "Invalid choice for `upsert`. "
                    "Must be either 'update' or 'ignore'."
                )
            )
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
        # Set upsert
        self._upsert = upsert

    def get_engine(self, element: Optional[Dict] = None) -> "Engine":
        """Get engine.

        Parameters
        ----------
        meta : dict, optional
            The metadata as dictionary (default None).

        Returns
        -------
        sqlalchemy.engine.Engine
            The sqlalchemy engine.

        """
        # Prefixed elements
        prefix = ""
        if self.single_output is False:
            if element is None:
                msg = "element must be specified when single_output is False."
                raise_error(msg)
            prefix = element_to_prefix(element)
        # Format URI for engine creation
        uri = (
            f"sqlite:///{self.uri.parent}/"  # type: ignore
            f"{prefix}{self.uri.name}"  # type: ignore
        )
        return create_engine(uri, echo=False)

    def _save_upsert(
        self,
        df: Union[pd.DataFrame, pd.Series],
        name: str,
        engine: Optional["Engine"] = None,
        if_exists: str = "append",
    ) -> None:
        """Implement UPSERT functionality.

        Parameters
        ----------
        df : pandas.DataFrame or pandas.Series
            The pandas DataFrame or Series to save.
        name : str
            Name of the table to save.
        engine : sqlalchemy.Engine, optional
            The sqlalchemy engine to use (default None).
        if_exists : {"replace", "nocheck", "append", "fail"}, optional
            Action to take if the table exists. If "replace", existing table
            will be dropped before inserting new values. If "nocheck",
            existing table will be ignored. If "append", the data will be
            appended to the existing table. If "fail", it will raise an error
            (default "append").

        Raises
        ------
        ValueError
            If the table exists and if_exists is "fail" or if invalid option is
            passed to `if_exists`.

        """
        # Get index names
        index_col = df.index.names
        # Get sqlalchemy engine if None
        if engine is None:
            engine = self.get_engine()
        # Write data
        with engine.begin() as con:
            # Check for table's existence
            if not inspect(engine).has_table(name):
                # New table, so no big issue
                df.to_sql(name=name, con=con, if_exists="append")
            else:
                if if_exists == "replace":
                    # Replace all the existing elements
                    df.to_sql(name=name, con=con, if_exists="replace")
                elif if_exists == "nocheck":
                    # Ignore check
                    df.to_sql(name, con=con, if_exists="append")
                elif if_exists == "append":
                    # TODO: improve
                    # Step 1: split incoming data into existing and new data
                    pk_indb = _get_existing_pk(
                        con, table_name=name, index_col=index_col
                    )
                    existing, new = _split_incoming_data(
                        df, pk_indb, index_col
                    )
                    # Step 2: upsert existing data
                    pandas_sql = pandasSQL_builder(con)
                    pandas_sql.meta.reflect(bind=con, only=[name])
                    table = pandas_sql.get_table(name)
                    update_stmts = NoNewAttributesMixin
                    if len(existing) > 0 and len(new) > 0:
                        warn_with_log(
                            f"Some rows (n={len(existing)}) are already "
                            "present in the database. The storage is "
                            f"configured to {self._upsert} the existing "
                            f"elements. The new rows (n={len(new)}) will be "
                            "appended. This warning is shown because normally "
                            "all of the elements should be updated."
                        )
                    if self._upsert == "update":
                        update_stmts = _generate_update_statements(
                            table, index_col, existing
                        )
                        for stmt in update_stmts:
                            con.execute(stmt)
                    # Step 3: insert new data
                    new.to_sql(name=name, con=con, if_exists="append")
                elif if_exists == "fail":
                    # Case 4: existing table, so we need to check if the index
                    # is present or not.
                    raise_error(msg=f"Table ({name}) already exists.")
                else:
                    raise_error(
                        msg=f"Invalid option {if_exists} for if_exists."
                    )

    def list_features(self) -> Dict:
        """List the features in the storage.

        Returns
        -------
        dict
            List of features in the storage. The keys are the feature names to
            be used in read_features() and the values are the metadata of each
            feature.

        """
        meta_df = pd.read_sql(
            sql="meta",
            con=self.get_engine(),
            index_col="meta_md5",
        )
        meta_df.index = meta_df.index.str.replace(r"meta_", "")
        out = meta_df.to_dict(orient="index")  # type: ignore
        for md5, t_meta in out.items():
            for k, v in t_meta.items():
                out[md5][k] = json.loads(v)
        return out

    def read_df(
        self,
        feature_name: Optional[str] = None,
        feature_md5: Optional[str] = None,
    ) -> pd.DataFrame:
        """Implement feature reading into a pandas DataFrame.

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
        ValueError
            If parameter values are invalid or feature is not found or
            multiple features are found.

        """
        # Get sqlalchemy engine
        engine = self.get_engine()
        # Parameter value check
        if feature_md5 is not None and feature_name is not None:
            raise_error(
                msg=(
                    "Only one of `feature_name` or `feature_md5` can be "
                    "specified."
                )
            )
        elif feature_md5 is None and feature_name is None:
            raise_error(
                msg=(
                    "At least one of `feature_name` or `feature_md5` "
                    "must be specified."
                )
            )
        elif feature_md5 is not None:
            table_name = f"meta_{feature_md5}"
        else:
            meta_df = pd.read_sql(
                sql="meta",
                con=engine,
                index_col="meta_md5",
            )

            # Wrap in double quotes as the fields are in JSON format
            t_df = meta_df.query(f"name == '\"{feature_name}\"'")
            if len(t_df) == 0:
                raise_error(msg=f"Feature {feature_name} not found")
            elif len(t_df) > 1:
                raise_error(
                    msg=(
                        f"More than one feature with name {feature_name} "
                        "found. This file is invalid. You can bypass this "
                        "issue by specifying a `feature_md5`."
                    )
                )
            table_name = f"meta_{t_df.index[0]}"
        if table_name not in inspect(engine).get_table_names():
            raise_error(msg=f"Feature MD5 {feature_md5} not found")
        # Read metadata from table
        df = pd.read_sql(sql=table_name, con=engine)

        # Read the index
        query = (
            "SELECT ii.name FROM sqlite_master AS m, "
            "pragma_index_list(m.name) AS il, "
            "pragma_index_info(il.name) AS ii "
            f"WHERE tbl_name='{table_name}' "
            "ORDER BY cid;"
        )
        index_names = (
            pd.read_sql(sql=query, con=engine).values.squeeze().tolist()
        )
        # Set index on dataframe
        df = df.set_index(index_names)
        return df

    def store_metadata(self, meta_md5: str, element: Dict, meta: Dict) -> None:
        """Implement metadata storing in the storage.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        meta : dict
            The metadata as a dictionary.
        """
        # Get sqlalchemy engine
        engine = self.get_engine(element=element)
        table_name = f"meta_{meta_md5}"
        if table_name not in inspect(engine).get_table_names():
            # Convert metadata to dataframe
            meta_df = self._meta_row(meta=meta, meta_md5=meta_md5)
            # Save dataframe
            self._save_upsert(meta_df, "meta", engine)

    def store_df(
        self, meta_md5: str, element: Dict, df: Union[pd.DataFrame, pd.Series]
    ) -> None:
        """Implement pandas DataFrame storing.

        Parameters
        ----------
        df : pandas.DataFrame or pandas.Series
            The pandas DataFrame or Series to store.
        meta : dict
            The metadata as a dictionary.

        Raises
        ------
        ValueError
            If the dataframe index has items that are not in the index
            generated from the metadata.

        """
        # TODO: Test this function
        # Check that the index generated by meta matches the one in
        # the dataframe.
        idx = self.element_to_index(element)
        # Given the meta, we might not know if there is an extra column added
        # when storing a timeseries or 2d elements. We need to check if the
        # extra element is only one.
        extra = [x for x in df.index.names if x not in idx.names]
        if len(extra) > 1:
            raise_error(
                "The index of the dataframe has extra items that are not "
                "in the index generated from the metadata."
            )
        elif len(extra) == 1:
            # The df has one extra index item, this should be the new name
            # of the missing element in the index
            idx = self.element_to_index(element, rows_col_name=extra[0])

        if any(x not in df.index.names for x in idx.names):
            raise_error(
                "The index of the dataframe is missing index items that are "
                "generated from the metadata."
            )

        table_name = f"meta_{meta_md5}"
        # Get sqlalchemy engine
        engine = self.get_engine(element)
        # Save data
        self._save_upsert(df, table_name, engine)

    def store_matrix(
        self,
        meta_md5: str,
        element: Dict,
        data: np.ndarray,
        col_names: Optional[List[str]] = None,
        row_names: Optional[List[str]] = None,
        matrix_kind: Optional[str] = "full",
        diagonal: bool = True,
    ) -> None:
        """Implement matrix storing.

        Parameters
        ----------
        meta_md5 : str
            The metadata MD5 hash.
        element : dict
            The element as a dictionary.
        data : numpy.ndarray
            The matrix data to store.
        meta : dict
            The metadata as a dictionary.
        col_names : list or tuple of str, optional
            The column names (default None).
        row_names : str, optional
            The column name to use in case number of rows greater than 1.
            If None and number of rows greater than 1, then the name will be
            "index" (default None).
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
        if diagonal is False and matrix_kind not in ["triu", "tril"]:
            raise_error(
                msg="Diagonal cannot be False if kind is not full",
                klass=ValueError,
            )

        if matrix_kind in ["triu", "tril"]:
            if data.shape[0] != data.shape[1]:
                raise_error(
                    "Cannot store a non-square matrix as a triangular matrix",
                    klass=ValueError,
                )

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

        if row_names is None:
            row_names = [f"r{i}" for i in range(data.shape[0])]
        elif len(row_names) != data.shape[0]:
            raise_error(
                msg="Number of row names does not match number of rows",
                klass=ValueError,
            )

        if col_names is None:
            col_names = [f"c{i}" for i in range(data.shape[1])]
        elif len(col_names) != data.shape[1]:
            raise_error(
                msg="Number of column names does not match number of columns",
                klass=ValueError,
            )

        flat_data = data[data_idx]
        columns = [
            f"{row_names[i]}~{col_names[j]}"
            for i, j in zip(data_idx[0], data_idx[1])
        ]

        # Convert element metadata to index
        n_rows = 1
        idx = self.element_to_index(
            element=element, n_rows=n_rows, rows_col_name=None
        )
        # Prepare new dataframe
        data_df = pd.DataFrame(flat_data[None, :], columns=columns, index=idx)

        if len(columns) > 2000:
            warn_with_log(
                msg="The number of columns is greater than 2000. "
                "The data will be stored in long format. "
                "This will make it slower to collect the data. "
                "Future versions of junifer will provide additional storage "
                "options that will not raise this warning.",
            )
            data_df = data_df.stack()
            new_names = [x for x in data_df.index.names[:-1]]
            new_names.append("pair")
            data_df.index.names = new_names

        # Store dataframe
        self.store_df(meta_md5=meta_md5, element=element, df=data_df)

    def collect(self) -> None:
        """Implement data collection.

        Raises
        ------
        NotImplementedError
            If ``single_output`` is True.

        """
        if self.single_output is True:
            raise_error(msg="collect() is not implemented for single output.")
        logger.info(
            "Collecting data from "
            f"{self.uri.parent}/*{self.uri.name}"  # type: ignore
        )
        # Create new instance
        out_storage = SQLiteFeatureStorage(uri=self.uri, upsert="ignore")
        # Glob files
        files = self.uri.parent.glob(f"*{self.uri.name}")  # type: ignore
        for elem in tqdm(files, desc="file"):
            logger.debug(f"Reading from {str(elem.absolute())}")
            in_storage = SQLiteFeatureStorage(uri=elem)
            in_engine = in_storage.get_engine()
            # Open "meta" table
            t_meta_df = pd.read_sql(
                sql="meta", con=in_engine, index_col="meta_md5"
            )
            # Save metadata
            out_storage._save_upsert(t_meta_df, "meta")
            # Save dataframes
            for meta_md5 in tqdm(t_meta_df.index, desc="feature"):
                logger.debug(f"Collecting feature {meta_md5}")
                # TODO: Fix this, needs that read_feature sets the index
                # properly
                table_name = f"meta_{meta_md5}"
                t_df = in_storage.read_df(feature_md5=meta_md5)
                # Save data
                out_storage._save_upsert(t_df, table_name, if_exists="nocheck")


# TODO: refactor
def _get_existing_pk(con, table_name, index_col):
    pk_cols = ", ".join(index_col)
    query = f"SELECT {pk_cols} FROM {table_name};"
    pk_indb = pd.read_sql(query, con=con)
    return pk_indb


# TODO: refactor
def _split_incoming_data(df, pk_indb, index_col):
    incoming_pk = df.reset_index()[index_col]
    exists_mask = (
        incoming_pk[index_col]
        .apply(tuple, axis=1)
        .isin(pk_indb[index_col].apply(tuple, axis=1))
    )
    existing, new = df.loc[exists_mask.values], df.loc[~exists_mask.values]
    return existing, new


# TODO: refactor
def _generate_update_statements(table, index_col, rows_to_update):
    from sqlalchemy import and_

    new_records = rows_to_update.to_dict(orient="records")
    pk_indb = rows_to_update.reset_index()[index_col]
    pk_cols = [table.c[key] for key in index_col]

    stmts = []
    for i, (_, keys) in enumerate(pk_indb.iterrows()):
        stmt = (
            table.update()
            .where(
                and_(col == keys[j] for j, col in enumerate(pk_cols))
            )  # type: ignore
            .values(new_records[i])
        )
        stmts.append(stmt)
    return stmts
