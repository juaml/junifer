.. include:: ../links.inc

.. _datagrabber:

Data Grabber
============

Description
-----------

The *Data Grabber* is an object that can provide an interface to datasets you want to work with in junifer.
Every concrete implementation of a datagrabber is aware of a particular dataset's structure and thus allows
you to fetch specific elements of interest from the dataset. It adds the ``path`` key to each :ref:`data type <data_types>`
in the :ref:`Data object <data_object>`.

Datagrabbers are intended to be used as context managers. When used within a context, a datagrabber takes care
of any pre and post steps for interacting with the dataset, for example, downloading and cleaning up. As the interface
is consistent, you always use the same procedure to interact with the datagrabber.

For example, a concrete implementation of :class:`junifer.datagrabber.DataladDataGrabber` can provide junifer
with data from a Datalad dataset. Of course, datagrabbers are not only meant to work with Datalad datasets but
any dataset.

If you are interested in using already provided datagrabbers, please go to :doc:`../builtin`. And, if you want
to implement your own datagrabber, you need to provide concrete implementations of base classes already
provided.

Base classes
------------

In this section, we showcase different abstract base classes you might want to use to implement your own datagrabber.

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - Description
   * - :class:`junifer.datagrabber.BaseDataGrabber`
     - | The abstract base class providing you an interface to implement your own datagrabber.
       | You should try to avoid using this directly and instead use
       | :class:`junifer.datagrabber.PatternDataGrabber` or :class:`junifer.datagrabber.DataladDataGrabber`.
       | To build your own custom *low-level* datagrabber, you need to at least implement the ``get_elements`` method,
       | but most of the time you should also override other existing methods like ``__enter__`` and ``__exit__``.
   * - :class:`junifer.datagrabber.PatternDataGrabber`
     - | It implements functionality to help you define the pattern of the dataset you want to get. For example,
       | you know that T1 images are found in a directory following this pattern ``{subject}/anat/{subject}_T1w.nii.gz``
       | inside of the dataset. Now you can provide this to the **PatternDataGrabber** and it will be able to get the file.
   * - :class:`junifer.datagrabber.DataladDataGrabber`
     - | It implements functionality to deal with Datalad datasets. Specifically, the ``__enter__`` and ``__exit__`` methods
       | take care of cloning and removing the Datalad dataset.
   * - :class:`junifer.datagrabber.PatternDataladDataGrabber`
     - | It is a combination of :class:`junifer.datagrabber.PatternDataladDataGrabber` and
       | :class:`junifer.datagrabber.DataladDataGrabber`. This is probably the class you are looking for when using Datalad.
