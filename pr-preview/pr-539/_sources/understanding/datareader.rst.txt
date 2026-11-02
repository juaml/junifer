.. include:: ../links.inc

.. _datareader:

Data Reader
===========

Description
-----------

The ``DataReader`` is an object that is responsible for actually reading data
files in ``junifer``. It reads the value of the key ``path`` for each
:ref:`data type <data_types>` in the :ref:`Data object <data_object>` and loads
them into memory. After reading the data into memory, it adds the key ``data``
to the same level as ``path`` and the value is the actual data in the memory.

DataReaders are meant to be used inside the DataGrabber context but you can
operate on them outside the context as long as the actual data is in the memory
and the Python runtime has not garbage-collected it.

For data formats not supported by ``junifer`` yet, you can either make your own
DataReader or open an issue on `junifer Github`_ and we can help you out.

File Formats
------------

We already provide a concrete implementation :class:`.DefaultDataReader` which
knows how to read the following file formats:

.. list-table::
   :widths: auto
   :header-rows: 1

   * - File extension
     - File type
     - Description
   * - ``.nii``
     - NIfTI (uncompressed)
     - Uncompressed NIfTI
   * - ``.nii.gz``
     - NIfTI (compressed)
     - Compressed NIfTI
   * - ``.csv``
     - CSV
     - Comma-separated values file
   * - ``.tsv``
     - TSV
     - Tab-separated values file
