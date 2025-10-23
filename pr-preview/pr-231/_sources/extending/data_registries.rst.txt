.. include:: ../links.inc

.. _data_registries:

Creating a Data Registry
========================

What is a data registry
-----------------------

Data Registry is an object which manages pipeline data (like parcellations,
coordinates and masks) based on the scope. ``junifer`` comes with the
following in-built data registries:

* :class:`.ParcellationRegistry` for parcellations
* :class:`.CoordinatesRegistry` for coordinates
* :class:`.MaskRegistry` for masks

You interact with them indirectly via :func:`.get_data`, :func:`.load_data`,
:func:`.list_data`, :func:`.register_data` and :func:`.deregister_data`. The
``kind`` parameter in them directs which data registry to interact with. These
in turn supply preprocessors and markers with their necessary data for computation.

How to make a data registry
---------------------------

Ideally you would not need to create a custom data registry if you work with fMRI data.
In case you work with other modalities like EEG, you might want to create a
data registry for montages. Here is how you would go about it:

#. Check :ref:`extending junifer <extending_extension>` on how to create a
   *junifer extension* if you have not done so.
#. Create the data registry in the *extension script* like so:

   .. code-block:: python

     from junifer.api.decorators import register_data_registry
     from junifer.data import BasePipelineDataRegistry


     @register_data_registry("montage")
     class MontageDataRegistry(BasePipelineDataRegistry):
         def __init__(self):
             super().__init__()

         def register(self):
             pass

         def deregister(self):
             pass

         def load(self):
             pass

         def get(self):
             pass


   * :func:`.register_data_registry` registers a class with the name passed in
     the argument, ``"montage"`` in this case.
   * Inheriting from :class:`.BasePipelineDataRegistry` takes care of the class
     acting as a data registry.
   * :meth:`.BasePipelineDataRegistry.register`,
     :meth:`.BasePipelineDataRegistry.deregister`,
     :meth:`.BasePipelineDataRegistry.load` and
     :meth:`.BasePipelineDataRegistry.get` need to be implemented
     (check other registries for reference implementations).

#. Pass ``kind="montage"`` in ``*_data`` functions to
   verify if your data registry is set up properly.
