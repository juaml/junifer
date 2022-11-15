.. include:: ../links.inc

.. _extending_markers:

Creating Markers
================

Computing a marker (a.k.a. *feature*) is the main goal of junifer. While we aim to provide as many markers as possible,
it might be the case that the marker you are looking for is not available. In this case, you can create your own marker
by following this tutorial.

Most of the functionality of a junifer marker has been taken care by the :class:`junifer.markers.BaseMarker` class. 
Thus, only a few methods are required:

1. ``get_valid_inputs``: a method to obtain the list of valid inputs for the marker. This is used to check that the
   inputs provided by the user are valid. This method should return a list of strings, representing 
   :ref:`data types <data_types>`
2. ``get_output_kind``: a method to obtain the kind of output of the marker. This is used to check that the output
   of the marker is compatible with the storage. This method should return a string, representing 
   :ref:`storage types <storage_types>`
3. ``compute``: the method that given the data, computes the marker.
4. ``store``: the method that stores the computed marker.
5. ``__init__``: the initialization method, where the marker is configured.

As an example, we will develop a Parcel Mean marker, that is, a marker that first applies a parecellation and
then computes the mean of the data in each parcel. This is a very simple example, but it will show you how to create
a new marker.

.. _extending_markers_input_output:

Step 1: Configure input and output
----------------------------------



