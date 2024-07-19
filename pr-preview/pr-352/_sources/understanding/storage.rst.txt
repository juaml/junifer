.. include:: ../links.inc

.. _storage:

Storage
=======

Description
-----------

The ``Storage`` is an object that is responsible for storing extracted features
as computed from :ref:`Marker <marker>` step of the pipeline. If the pipeline is
provided with a ``storage-like`` object, the extracted features are stored via
that object else they are kept in memory.

Storage is meant to be used inside the DataGrabber context but you can operate
on them outside the context as long as the processed data is in the memory and
the Python runtime has not garbage-collected it.

The :ref:`Markers <marker>` are responsible for defining what *storage kind*
(``matrix``, ``vector``, ``timeseries``, ``scalar_table``) they support for
which :ref:`data type <data_types>` by overriding its ``get_output_type``
method. The storage object in turn declares and provides implementation for
specific *storage kind*. For example, :class:`.SQLiteFeatureStorage` supports
saving ``matrix``, ``vector`` and ``timeseries`` via ``store_matrix``,
``store_vector`` and ``store_timeseries`` methods respectively.

For storage interfaces not supported by ``junifer`` yet, you can either make
your own ``Storage`` by providing a concrete implementation of
:class:`.BaseFeatureStorage` or open an issue on `junifer Github`_ and we can
help you out.

.. _storage_types:

Storage Types
-------------

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Storage Type
     - Description
     - Options
     - Reference
   * - ``matrix``
     - A 2D square matrix with row and column names
     - | ``col_names``, ``row_names``, ``matrix_kind``, ``diagonal``
       | ``row_header_col_name``
       | (only for :meth:`.HDF5FeatureStorage.store_matrix`)
     - :meth:`.BaseFeatureStorage.store_matrix`
   * - ``vector``
     - A 1D row vector of values with column names
     - ``col_names``
     - :meth:`.BaseFeatureStorage.store_vector`
   * - ``timeseries``
     - A 2D square or non-square matrix of scalar values with column names
     - ``col_names``
     - :meth:`.BaseFeatureStorage.store_timeseries`
   * - ``scalar_table``
     - | A 2D square or non-square matrix of scalar values with row name, column
       | name and row header column name
     - ``col_names``, ``row_names``, ``row_header_col_name``
     - :meth:`.BaseFeatureStorage.store_scalar_table`

.. _storage_interfaces:

Storage Interfaces
------------------

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Storage class
     - File extension
     - File type
     - Storage kinds
   * - :class:`.SQLiteFeatureStorage`
     - ``.sqlite``
     - SQLite
     - ``matrix``, ``vector``, ``timeseries``
   * - :class:`.HDF5FeatureStorage`
     - ``.hdf5``
     - HDF5
     - ``matrix``, ``vector``, ``timeseries``, ``scalar_table``
