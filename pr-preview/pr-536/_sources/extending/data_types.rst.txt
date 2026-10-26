.. include:: ../links.inc

.. _adding_data_types:

Adding Data Types
=================

``junifer`` supports most of the :ref:`data types <data_types>` required for fMRI
but also provides a way to add custom data types in case you work with other
modalities like EEG.

How to add a data type
----------------------

#. Check :ref:`extending junifer <extending_extension>` on how to create a
   *junifer extension* if you have not done so.
#. Define the data type schema in the *extension script* like so:

   .. code-block:: python

     from junifer.datagrabber import DataTypeSchema


     dtype_schema: DataTypeSchema = {
         "mandatory": ["pattern"],
         "optional": {
             "mask": {
                 "mandatory": ["pattern"],
                 "optional": [],
             },
         },
     }

   * The :obj:`.DataTypeSchema` has two mandatory keys:

     * ``mandatory`` : list of str
     * ``optional`` : dict of str and :obj:`.OptionalTypeSchema`

   * ``mandatory`` defines the keys that must be present when defining a *pattern*
     in a DataGrabber.
   * ``optional`` defines the mapping from *sub-types* that are optional, to their patterns.
     The patterns in turn require a ``mandatory`` key and an ``optional`` key both
     just being the keys that must be there if the optional key is found. It's
     possible that the *sub-type* (``mask`` in the example) can be absent from the dataset.

#. Register the data type before defining / using a DataGrabber like so:

   .. code-block:: python

      from junifer.datagrabber import register_data_type
      ...


      # registers the data type as "dtype"
      register_data_type(name="dtype", schema=dtype_schema)

      ...
