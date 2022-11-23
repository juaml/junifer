.. include:: ../links.inc

.. _storage:

Storage
=======

Description
-----------

The ``Storage`` is an object that is responsible for storing extracted features as computed from :ref:`Marker <marker>`
step of the pipeline. If the pipeline is provided with a ``storage-like`` object, the extracted features are stored via
that object else they are kept in memory.

Storage is meant to be used inside the datagrabber context but you can operate on them outside the context as long
as the processed data is in the memory and the Python runtime has not garbage-collected it.

The :ref:`Markers <marker>` are responsible for defining what *storage kind* (``matrix``, ``table``, ``timeseries``)
they support for which :ref:`data type <data_types>` by overriding its ``store`` method. The storage object in turn
declares and provides implementation for specific *storage kind*. For example, :class:`junifer.storage.SQLiteFeatureStorage`
supports saving ``matrix``, ``table`` and ``timeseries`` via ``store_matrix``, ``store_table`` and ``store_timeseries``
methods respectively.

For storage interfaces not supported by junifer yet, you can either make your own ``Storage`` by providing a concrete
implementation of :class:`junifer.storage.BaseFeatureStorage` or open an issue on `junifer Github`_ and we can help you out.


.. _storage_types:

Currently supported storage types
---------------------------------

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Storage Type
     - Description
     - Options
     - Reference
   * - ``matrix``
     - A 2D matrix with row and column names
     -  ``col_names``, ``row_names``, ``matrix_kind``, ``diagonal``
     -  :meth:`junifer.storage.BaseFeatureStorage.store_matrix`
   * - ``table``
     - A vector of values with column names
     - ``columns``, ``row_names``
     -  :meth:`junifer.storage.BaseFeatureStorage.store_table`
   * - ``timeseries``
     - A 2D matrix of values with column names
     - ``columns``, ``row_names``
     -  :meth:`junifer.storage.BaseFeatureStorage.store_timeseries`
  
.. _storage_interfaces:

Currently supported storage interfaces
--------------------------------------

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Storage class
     - File extension
     - File type
     - Storage kinds
   * - :class:`junifer.storage.SQLiteFeatureStorage`
     - ``.sqlite``
     - SQLite
     - ``matrix``, ``table``, ``timeseries``
