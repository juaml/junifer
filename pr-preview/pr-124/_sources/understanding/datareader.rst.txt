.. include:: ../links.inc

.. _datareader:

Data Reader
===========

Description
-----------

The *Data Reader* is an object that is responsible for actually reading data files in junifer.
It reads the value of the key ``path`` for each :ref:`data type <data_types>` in the :ref:`Data object <data_object>`
and loads them to memory. After reading the data into memory, it adds the key ``data`` to the same level as ``path``
and the value is the actual data in the memory.

Datareaders are meant to be used inside the datagrabber context but you can operate on them outside the context as long
as the actual data is in the memory and the Python runtime has not garbage-collected it.

For data formats not supported by junifer yet, you can either make your own *Data Reader* or open an issue on
`junifer Github`_ and we can help you out.

Currently supported file-formats
--------------------------------

We already provide a concrete implementation :class:`junifer.datareader.DefaultDataReader` which knows how to
read the following file formats:

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
