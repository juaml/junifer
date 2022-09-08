"""Provide concrete implementation for feature storage via SQLite."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Union

import pandas as pd
from pandas.core.base import NoNewAttributesMixin
from pandas.io.sql import pandasSQL_builder
from sqlalchemy import create_engine, inspect
from tqdm import tqdm

from ..api.decorators import register_storage
from ..utils import logger, raise_error, warn_with_log
from .pandas_base import PandasBaseFeatureStorage
from .utils import element_to_index, element_to_prefix, process_meta


if TYPE_CHECKING:
    from sqlalchemy import Engine


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
        concurrency (default False).
    upsert : {"ignore", "update"}, optional
        Upsert mode. If "ignore" is used, the existing elements are ignored.
        If "update", the existing elements are updated (default "update").

    See Also
    --------
    PandasBaseFeatureStorage

    """

    def __init__(
        self,
        uri: Union[str, Path],
        single_output: bool = False,
        upsert: str = "update",
        **kwargs: str,
    ) -> None:
        """Initialize the class.

        Extra Parameters
        ----------------
        **kwargs : dict
            The keyword arguments passed to the superclass.

        """
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
        super().__init__(uri=uri, single_output=single_output, **kwargs)
        self._upsert = upsert
        self._valid_inputs = ["table", "timeseries"]

    def get_engine(self, meta: Optional[Dict] = None) -> "Engine":
        """Get engine.

        Parameters
        ----------
        meta : dict, optional
            The metadata as dictionary (default None).

        Returns
        -------
        sqlalchemy.Engine
            The sqlalchemy engine.

        """
        # Set metadata as empty dictionary if None
        if meta is None:
            meta = {}
        # Retrieve element key from metadata
        element = meta.get("element", None)
        # Functionality check
        if self.single_output is False and element is None:
            raise_error(
                msg="element must be specified when single_output is False."
            )
        # Prefixed elements
        prefix = ""
        if self.single_output is False:
            prefix = element_to_prefix(element)
        # Format URI for engine creation
        uri = f"sqlite:///{self.uri.parent}/{prefix}{self.uri.name}"
        return create_engine(uri, echo=False)

    def _save_upsert(
        self,
        df: pd.DataFrame,
        name: str,
        engine: Optional["Engine"] = None,
        if_exists: str = "append",
    ) -> None:
        """Implement UPSERT functionality.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame to save.
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

    # TODO: complete type annotations
    def store_2d(
        self,
        data,
        meta: Dict,
        columns: Optional[Iterable[str]] = None,
        rows_col_name: str = None,
    ) -> None:
        """Store 2D dataframe.

        Parameters
        ----------
        data
        meta : dict
            The metadata as a dictionary.
        columns : list or tuple of str, optional
            The columns (default None).
        rows_col_name : str, optional
            The column name to use in case number of rows greater than 1.
            If None and number of rows greater than 1, then the name will be
            "index" (default None).

        """
        n_rows = len(data)
        # Convert element metadata to index
        idx = element_to_index(
            meta=meta, n_rows=n_rows, rows_col_name=rows_col_name
        )
        # Prepare new dataframe
        data_df = pd.DataFrame(data, columns=columns, index=idx)
        # Store dataframe
        self.store_df(df=data_df, meta=meta)

    def validate(self, input_: List[str]) -> bool:
        """Implement input validation.

        Parameters
        ----------
        input_ : list of str
            The input to the pipeline step.

        Returns
        -------
        bool
            Whether the `input` is valid or not.

        """
        # Convert input to list
        if not isinstance(input_, list):
            input_ = [input_]

        return all(x in self._valid_inputs for x in input_)

    def list_features(
        self, return_df: bool = False
    ) -> Union[Dict[str, Dict], pd.DataFrame]:
        """Implement features listing from the storage.

        Parameters
        ----------
        return_df : bool, optional
            If True, returns a pandas DataFrame. If False, returns a
            dictionary (default False).

        Returns
        -------
        dict or pandas.DataFrame
            List of features in the storage. If dictionary is returned, the
            keys are the feature names to be used in read_features() and the
            values are the metadata of each feature.

        """
        meta_df = pd.read_sql(
            sql="meta",
            con=self.get_engine(),
            index_col="meta_md5",
        )
        out = meta_df
        # Return dictionary
        if return_df is False:
            out = meta_df.to_dict(orient="index")
        return out

    def read_df(
        self,
        feature_name: Optional[str] = None,
        feature_md5: Optional[str] = None,
    ) -> pd.DataFrame:
        """Implement feature reading from the storage.

        Either one of `feature_name` or `feature_md5` needs to be specified.

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
            t_df = meta_df.query(f"name == '{feature_name}'")
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

    def store_metadata(self, meta: Dict) -> str:
        """Implement metadata storing in the storage.

        Parameters
        ----------
        meta : dict
            The metadata as a dictionary.

        Returns
        -------
        str
            The MD5 hash of the metadata prefixed with "meta_" .

        """
        # Copy metadata
        t_meta = meta.copy()
        # Update metadata
        t_meta.update(self.get_meta())
        # Process metadata
        meta_md5, t_meta_row = process_meta(t_meta)
        # Get sqlalchemy engine
        engine = self.get_engine(meta=t_meta)
        if meta_md5 not in inspect(engine).get_table_names():
            # Convert metadata to dataframe
            meta_df = self._meta_row(meta=t_meta_row, meta_md5=meta_md5)
            # Save dataframe
            self._save_upsert(meta_df, "meta", engine)
        return f"meta_{meta_md5}"

    # TODO: complete type annotations
    def store_matrix2d(
        self,
        data,
        meta: Dict,
        col_names: Optional[Iterable[str]] = None,
        rows_col_name: str = None,
    ) -> None:
        """Implement 2D matrix storing.

        Parameters
        ----------
        data
        meta : dict
            The metadata as a dictionary.
        col_names : list or tuple of str, optional
            The column names (default None).
        rows_col_name : str, optional
            The column name to use in case number of rows greater than 1.
            If None and number of rows greater than 1, then the name will be
            "index" (default None).

        """
        # Same as store_2d, but order is important
        raise_error(
            msg="store_matrix2d() not implemented", klass=NotImplementedError
        )

    # TODO: complete type annotations
    def store_table(
        self,
        data,
        meta: Dict,
        columns: Optional[Iterable[str]] = None,
        rows_col_name: str = None,
    ) -> None:
        """Implement table storing.

        Parameters
        ----------
        data
        meta : dict
            The metadata as a dictionary.
        columns : list or tuple of str, optional
            The columns (default None).
        rows_col_name : str, optional
            The column name to use in case number of rows greater than 1.
            If None and number of rows greater than 1, then the name will be
            "index" (default None).

        """
        self.store_2d(
            data=data, meta=meta, columns=columns, rows_col_name=rows_col_name
        )

    def store_df(self, df: pd.DataFrame, meta: Dict) -> None:
        """Implement dataframe storing.

        Parameters
        ----------
        df : pandas.DataFrame
            The DataFrame to store.
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
        idx = element_to_index(meta)
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
            idx = element_to_index(meta, rows_col_name=extra[0])

        if any(x not in df.index.names for x in idx.names):
            raise_error(
                "The index of the dataframe is missing index items that are "
                "generated from the metadata."
            )
        # Get table name
        table_name = self.store_metadata(meta)
        # Get sqlalchemy engine
        engine = self.get_engine(meta)
        # Save data
        self._save_upsert(df, table_name, engine)

    # TODO: complete type annotations
    def store_timeseries(self, data, meta: Dict) -> None:
        """Implement timeseries storing.

        Parameters
        ----------
        data
        meta : dict
            The metadata as a dictionary.

        """
        raise_error(
            msg="store_timeseries() not implemented.",
            klass=NotImplementedError,
        )

    def collect(self) -> None:
        """Implement data collection.

        Raises
        ------
        NotImplementedError
            If `single_output` is True.

        """
        if self.single_output is True:
            raise_error(msg="collect() is not implemented for single output.")
        logger.info(f"Collecting data from {self.uri.parent}/*{self.uri.name}")
        # Create new instance
        out_storage = SQLiteFeatureStorage(
            uri=self.uri, single_output=True, upsert="ignore"
        )
        # Glob files
        files = self.uri.parent.glob(f"*{self.uri.name}")
        for elem in tqdm(files, desc="file"):
            logger.debug(f"Reading from {str(elem.absolute())}")
            in_storage = SQLiteFeatureStorage(uri=elem, single_output=True)
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
