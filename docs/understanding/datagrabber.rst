.. include:: ../links.inc

.. _datagrabber:

DataGrabber
===========


Description
^^^^^^^^^^^
A datagrabber is an object that can provide datasets you want to junifer.
For example, a DataladDataGrabber can provide data from a Datalad dataset to junifer.
Of course, datagrabbers are not only possible for Datalad but any origin of a dataset.
It is intended to use them as context managers.
If you are interested in just using already provided datagrabbers please go to :doc:`../builtin`.
If you want to implement your own Data Grabbers you need to inherit from different types of 
Data Grabbers we already provide.

Typical Data Grabbers
^^^^^^^^^^^^^^^^^^^^^
In this section we will showcase different types of datagrabber classes you might want to use
to implement your own datagrabbers for your own data.

.. list-table:: Data Grabbers Type
   :widths: 25 35
   :header-rows: 1

   * - Name
     - Description
   * - :py:class:`~junifer.datagrabber.base.BaseDataGrabber`
     - | An abstract class providing you an interface to implement for you own datagrabber.
       | This is not intedent to be used in general.
       | Instead you should use the DataladDataGrabber or PatternDataGrabber if possible.
       | You have to at least implement the ``get_elements`` method, but most of the time
       | you should also overwrite other existing methods like ``__enter__`` and ``__exit__``.
   * - :py:class:`~junifer.datagrabber.pattern.PatternDataGrabber`
     - | Implements some functionality to help you to define the pattern of the dataset you want to get. 
       | E.g. you know that T1 images are found in a directory following this pattern 
       | inside of the dataset "{subject}/anat/{subject}_T1w.nii.gz".
       | Now you can provide this to the PatternDataGrabber
       | and it will be able to get the image to junifer. 
   * - :py:class:`~junifer.datagrabber.datalad_base.DataladDataGrabber`
     - | Implements some functionality specific to basic usage of Datalad datasets. 
       | This mostly takes care of the ``__enter__`` and ``__exit__`` methods to clone your Datalad dataset
       | and remove it on  ``__exit__``.
       | This means that even if your code fails inside of the context of the 
       | datagrabber the DataladDataGrabber cleans up the created Datalad directories. 
   * - :py:class:`~junifer.datagrabber.pattern_datalad.PatternDataladDataGrabber`
     - | Combination of PatternDataGrabber and DataladDataGrabber.
       | Probably the class you are looking for when using Datalad. 

