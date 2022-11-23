.. include:: ../links.inc

.. _extending:

Extending junifer
=================

While we aim to provide as many datasets and markers as possible, we are also
interested in allowing users to extend the functionality with their own
datagrabbers, preprocessing, markers, etc.

This does not mean that the new functionality will have to be included in
junifer before the user can use them. Instead, the user can simply
create a new python file, code the desired functionality and use it with
junifer. This is the first step towards including the new functionality in
the junifer package.

In this section we will show how to extend junifer, by creating new
datagrabbers, preprocessing and markers, following the *junifer* way.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   extension
   datagrabber
   marker