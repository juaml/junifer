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

The :ref:`Markers <marker>` are responsible for mapping the input
:ref:`data type <data_types>` to its output :ref:`storage type <storage_types>`
as shown :ref:`here <extending_markers_input_output>`.
The storage object in turn declares and provides implementation for
specific *storage type*. For example, :class:`.HDF5FeatureStorage` supports
saving ``matrix``, ``vector`` and ``timeseries`` via ``store_matrix``,
``store_vector`` and ``store_timeseries`` methods respectively.

For storage interfaces not supported by ``junifer`` yet, you can either make
your own ``Storage`` by providing a concrete implementation of
:class:`.BaseFeatureStorage` or open an issue on `junifer Github`_ and we can
help you out.

The data of each element is stored only once: running the same elements again
with the same configuration (e.g., after trying a few elements and then running
all of them), or collecting the files of the elements again, does not change
the data already stored, which is not stored again. The data that does not
depend on all the keys of the element (e.g., the ``VBM_GM`` data of a subject,
for elements with the subject and the task) is stored once for its keys (see
:ref:`internals`).

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
   * - ``timeseries_2d``
     - A 3D(2D+1D) square or non-square matrix of scalar values with column names across sessions
     - ``col_names``
     - :meth:`.BaseFeatureStorage.store_timeseries_2d`
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
     - ``matrix``, ``vector``, ``timeseries``, ``timeseries_2d``, ``scalar_table``

.. note::

   :class:`.HDF5FeatureStorage` is the recommended storage.
   :class:`.SQLiteFeatureStorage` is only kept for compatibility with features
   stored in previous versions of ``junifer`` and should not be used for new
   analyses.
