.. include:: ../links.inc

.. _extending_datagrabbers:

Creating DataGrabbers
=====================

DataGrabbers are the first step of the pipeline. It's purpose is to interpret
the structure of a dataset and provide two specific functionalities:

1) Given an *element*, provide the path to each kind of data available for this
   element (e.g. the path to the T1 image, the path to the T2 image, etc.)
2) Provide the list of *elements* available in the dataset.

In this section, we will see how to create a datagrabber for a dataset. Basic
aspects of datagrabbers are covedered in the 
:ref:`Understanding DataGrabbers <datagrabbers>` section.

.. _extending_datagrabbers_think:

Step 1: Think about the element
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Like with any programming-related task, the first step is to think. When
creating a DataGrabber, we need to first define what an *element* is.
The *element* should be the smallest unit of data that can be processed. That
is, for each element, there should be a set of data that can be processed, but
only one of each *data type* (see :ref:`data_types`).

For example, if we have a dataset from an fMRI study in which:

a) both T1w and fMRI was acquired 
b) 20 subjects went through a experiment twice
c) the experiment included resting-stage fMRI and a task named *stroop*

then the *element* should be composed of 3 items:

*  ``subject``: The subject IDs, e.g. `sub001`, `sub002`, ... `sub020`
*  ``session``: The sesion number, e.g. `ses1`, `ses2`
*  ``task``: The task performed, e.g. `rest`, `stroop`

If any of this items were not part of the element, then we will have more than
one ``T1w`` and/or ``BOLD`` image for each subject, which is not allowed.

Importantly, nothing prevents that one image is part of two different elements.
For example, it is usually the case that the ``T1w`` image is not acquired for
each task, but once in the entire session. So in this case, the ``T1w`` image
for the element (``sub001``, ``ses1``, ``rest``) will be the same as the
``T1w`` image for the element (``sub001``, ``ses1``, ``stroop``).

We will now continue this section using as an example, a dataset in BIDS format
in which each 9 subjects (`sub-01` to `sub-09`) were scanned each in 3
sessions (`ses-01`, `ses-02`, `ses-03`) and each session included a `T1w` and
a `BOLD` image (resting-state), except for `ses-03` which was only anatomical.

Step 2: Think about the dataset's structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now that we have our element defined, we need to think about the structure of
the dataset. Mainly, because the structure of the dataset will determine how
the DataGrabber needs to be implemented.

Junifer provides an abstract class to deal with datasets that can be thought in
terms of *patterns*. A *pattern* is a string that contains placeholders that are
replaced by the actual values of the element. In our BIDS example, the path
to the T1w image of subject `sub-01` and session `ses-01`, relative to the
dataset location, is ``sub-01/ses-01/anat/sub-01_ses-01_T1w.nii.gz``. By 
replacing ``sub-01`` with ``sub-02``, we can obtain the T1w image of the first
session of the second subject. Indeed, the path to the T1w images can be
expressed as a pattern:

``{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz``

where ``{subject}`` is the replacement for the subject id and ``{session}}``
is the replacement for the session id.

Since it is a BIDS dataaset, the same happens with the BOLD images. The path to
the BOLD images can be expressed as a pattern:

``{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz``


This will be the norm in most of the datasets. If your dataset can be expressed
in terms of patterns, then follow :ref:`extending_datagrabbers_pattern`.
Otherwise, we recommend that you take time to re-think about your dataset
structure and why it does not have clear *patterns*. Feel free to open a
discussion in the `junifer Discussions`_ page. Most probably we can help you
get your dataset in order.

If there is no other way, then you can follow :ref:`extending_datagrabbers_base`
to create a DataGrabber from scratch.


.. _extending_datagrabbers_pattern:

Option A: Extending from PatternDataGrabber
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :py:class:`~junifer.datagrabber.PatternDataGrabber` class is an
abstract class that has the functionality of understanding patterns embeded
in it.

Before creating the datagrabber, we need to define 3 variables:

* ``types``: A list with the available :ref:`data_types` in our dataset 
* ``patterns``: A dictionary that specifies the pattern for each data type.
* ``replacements``: A list indicating which of the elements in the patterns
  should be replaced by the values of the element.

For example, in our BIDS example, the variables will be:

.. code-block:: python

    types = ["T1w", "BOLD"]
    patterns = {
       "T1w": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
       "BOLD": "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
    }
    replacements = ["subject", "session"]


An additional fourth variable is the ``datadir``, which should be the path to
where the dataset is located. For example, if the dataset is located in
``/data/project/test/data``, then ``datadir`` should be
``/data/project/test/data``. Or, if we want to allow the user to specify the
location of the dataset, we can expose the variable in the constructor, as in 
this example

With this defined, we can now create our datagrabber, we will name it
``ExampleBIDSDataGrabber``:


.. code-block:: python

    from junifer.datagrabber.pattern import PatternDataGrabber

    class ExampleBIDSDataGrabber(PatternDataGrabber):

        def __init__(self, datadir):
            types = ["T1w", "BOLD"]
            patterns = {
               "T1w": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
               "BOLD": "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
            }
            replacements = ["subject", "session"]
            super().__init__(
               datadir=datadir,
               types=types, 
               patterns=patterns,
               replacements=replacements)


Our datagrabber is ready to be used by junifer. However, it is still unknown
to the library. We need to register it in the library. To do so, we need to
use the :py:func:`~junifer.api.decorators.register_datagrabber` decorator.


.. code-block:: python

    from junifer.datagrabber.pattern import PatternDataGrabber
    from junifer.api.decorators import register_datagrabber


    @register_datagrabber
    class ExampleBIDSDataGrabber(PatternDataGrabber):

        def __init__(self, datadir):
            types = ["T1w", "BOLD"]
            patterns = {
               "T1w": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
               "BOLD": "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
            }
            replacements = ["subject", "session"]
            super().__init__(
               datadir=datadir,
               types=types, 
               patterns=patterns,
               replacements=replacements)


Now, we can use our datagrabber in junifer, by setting the ``datagrabber`` kind
in the yaml file to ``ExampleBIDSDataGrabber``. Remember that we still need to
set the ``datadir``.

.. code-block:: yaml
   
      datagrabber:
         kind: ExampleBIDSDataGrabber
         datadir: /data/project/test/data


Optional: Using datalad 
-----------------------

If you are using datalad, you can use the 
:py:class:`~junifer.datagrabber.PatternDataladDataGrabber` instead of the 
:py:class:`~junifer.datagrabber.PatternDataGrabber`. This class will also
interpret patterns, but will also use datalad to `clone` and `get` the data.

The main difference between the two is that the ``datadir`` is not the actual
location of the dataset, but the location where the dataset will be cloned. It 
can now be ``None``, which means that the data will be downloaded to a
temporary directory. To set the location of the dataset, you can use the
``uri`` argument in the constructor. Additionally, a ``rootdir`` argument can
be used to specify the path to the root directory of the dataset after doing
``datalad clone``

In the example, the dataset is hosted in gin 
(``https://gin.g-node.org/juaml/datalad-example-bids``).

When we clone this dataset, we will see the following structure:

.. code-block::

      .
      └── example_bids_ses
         ├── sub-01
         │   ├── ses-01
         │   ├── ses-02
         │   └── ses-03
         ├── sub-02
         │   ├── ses-01
         │   ├── ses-02
         │   └── ses-03
         ├── sub-03
         ...

So the patterns will start after ``example_bids_ses``. This is our ``rootdir``.

Now we have our 2 additional variables:

.. code-block:: python

    uri = "https://gin.g-node.org/juaml/datalad-example-bids"
    rootdir = "example_bids_ses"


And we can create our datagrabber:


.. code-block:: python

    from junifer.datagrabber.pattern import PatternDataladDataGrabber
    from junifer.api.decorators import register_datagrabber


    @register_datagrabber
    class ExampleBIDSDataGrabber(PatternDataladDataGrabber):

        def __init__(self):
            types = ["T1w", "BOLD"]
            patterns = {
               "T1w": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
               "BOLD": "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
            }
            replacements = ["subject", "session"]
            uri = "https://gin.g-node.org/juaml/datalad-example-bids"
            rootdir = "example_bids_ses"
            super().__init__(
               datadir=None,
               uri=uri,
               rootdir=rootdir,
               types=types, 
               patterns=patterns,
               replacements=replacements)


.. _extending_datagrabbers_base:

Option B: Extending from BaseDataGrabber
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^