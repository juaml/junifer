.. include:: ../links.inc

.. _datagrabber:

Data Grabber
============

Description
-----------

The ``DataGrabber`` is an object that can provide an interface to datasets you
want to work with in ``junifer``. Every concrete implementation of a DataGrabber
is aware of a particular dataset's structure and thus allows you to fetch
specific elements of interest from the dataset. It adds the ``path`` key to each
:ref:`data type <data_types>` in the :ref:`Data object <data_object>`.

DataGrabbers are intended to be used as context managers. When used within a
context, a DataGrabber takes care of any pre and post steps for interacting with
the dataset, for example, downloading and cleaning up. As the interface
is consistent, you always use the same procedure to interact with the DataGrabber.

For example, a concrete implementation of :class:`.DataladDataGrabber` can
provide ``junifer`` with data from a Datalad dataset. Of course, DataGrabbers are
not only meant to work with Datalad datasets but any dataset.

If you are interested in using already provided DataGrabbers, please go to
:doc:`../builtin`. And, if you want to implement your own DataGrabber, you need
to provide concrete implementations of abstract base classes already provided.

Base Classes
------------

In this section, we showcase different abstract and concrete base classes you
might want to use to implement your own DataGrabber.

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - Description
   * - :class:`.BaseDataGrabber`
     - | The abstract base class providing you an interface to implement your
       | own DataGrabber. You should try to avoid using this directly and
       | instead use :class:`.PatternDataGrabber` or
       | :class:`.DataladDataGrabber`. To build your own custom *low-level*
       | DataGrabber, you need to override the ``get_elements_keys``,
       | ``get_elements`` and ``get_item`` methods, and most of the time you
       | should also override other existing methods like ``__enter__`` and
       | ``__exit__``.
   * - :class:`.PatternDataGrabber`
     - | It implements functionality to help you define the pattern of the
       | dataset you want to get. For example, you know that T1w images are
       | found in a directory following the pattern:
       | ``{subject}/anat/{subject}_T1w.nii.gz`` inside of the dataset. Now you
       | can provide this to the :class:`.PatternDataGrabber` and it will be
       | able to get the file.
   * - :class:`.DataladDataGrabber`
     - | It implements functionality to deal with Datalad datasets. Specifically,
       | the ``__enter__`` and ``__exit__`` methods take care of cloning and
       | removing the Datalad dataset.
   * - :class:`.PatternDataladDataGrabber`
     - | It is a combination of :class:`.PatternDataGrabber` and
       | :class:`.DataladDataGrabber`. This is probably the class you are looking
       | for when using Datalad datasets.
