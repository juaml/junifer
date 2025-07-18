.. include:: ../links.inc

.. _extending:

Extending ``junifer``
=====================

While we aim to provide as many datasets and markers as possible, we are also
interested in allowing users to extend the functionality with their own
DataGrabbers, Preprocessors, Markers, etc., .

It's not necessary to have the new functionality included in ``junifer`` before
the user can use them. The user can simply create a new Python file, code the
desired functionality and use it with ``junifer``. This is the first step towards
including the new functionality in the ``junifer`` pipeline.

In this section we will show how to extend ``junifer``, by creating new
DataGrabbers, Preprocessors, Markers, etc.,  following the *junifer* way.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   extension
   datagrabber
   marker
   preprocessor
   dependencies
   parcellations
   coordinates
   masks
