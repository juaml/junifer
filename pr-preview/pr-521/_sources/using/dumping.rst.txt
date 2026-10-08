.. include:: ../links.inc

.. _dumping:

Dumping Pipeline Data
=====================

It is usually not required to check the :ref:`data object <data_object>` but
for debugging purposes one can do that. Since, there is no direct way to interact
with it, ``junifer`` provides a way to dump the object before, in between and / or after
pre-processing. It is controlled by the ``JUNIFER_PREPROCESSING_DUMP_LOCATION`` and
``JUNIFER_PREPROCESSING_DUMP_GRANULARITY`` :ref:`configuration options <available_configurations>`.

``junifer`` dumps the ``"data"`` attribute of the data object as proper files in their respective formats,
for example, ``nibabel.Nifti1Image`` gets dumped as a ``.nii.gz`` file. As of now, ``junifer`` can dump
``nibabel.Nifti1Image`` and ``pandas.DataFrame`` (confound files) file formats. In case you
:ref:`add custom data types <adding_data_types>` which support different file formats, you can create and
register a :ref:`custom dumper <adding_data_dump_assets>`.
