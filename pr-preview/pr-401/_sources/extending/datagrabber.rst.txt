.. include:: ../links.inc

.. _extending_datagrabbers:

Creating Data Grabbers
======================

Data Grabbers are the first step of the pipeline. Its purpose is to interpret
the structure of a dataset and provide two specific functionalities:

#. Given an *element*, provide the path to each kind of data available for this
   element (e.g. the path to the T1 image, the path to the T2 image, etc.)
#. Provide the list of *elements* available in the dataset.

In this section, we will see how to create a DataGrabber for a dataset. Basic
aspects of DataGrabbers are covered in the
:ref:`Understanding Data Grabbers <datagrabber>` section.

.. _extending_datagrabbers_think:

Step 1: Think about the element
-------------------------------

Like with any programming-related task, the first step is to think. When
creating a DataGrabber, we need to first define what an *element* is.
The *element* should be the smallest unit of data that can be processed. That
is, for each element, there should be a set of data that can be processed, but
only one of each *data type* (see :ref:`data_types`).

For example, if we have a dataset from a fMRI study in which:

a. both T1w and fMRI was acquired
b. 20 subjects went through an experiment twice
c. the experiment included resting-stage fMRI and a task named *stroop*

then the *element* should be composed of 3 items:

* ``subject``: The subject IDs, e.g. ``sub001``, ``sub002``, ... ``sub020``
* ``session``: The session number, e.g. ``ses1``, ``ses2``
* ``task``: The task performed, e.g. ``rest``, ``stroop``

If any of these items were not part of the element, then we will have more than
one ``T1w`` and / or ``BOLD`` image for each subject, which is not allowed.

Importantly, nothing prevents that one image being part of two different
elements. For example, it is usually the case that the ``T1w`` image is not
acquired for each task, but once in the entire session. So in this case, the
``T1w`` image for the element (``sub001``, ``ses1``, ``rest``) will be the same
as the ``T1w`` image for the element (``sub001``, ``ses1``, ``stroop``).

We will now continue this section using as an example, a dataset in BIDS format
in which 9 subjects (``sub-01`` to ``sub-09``) were scanned each during 3
sessions (``ses-01``, ``ses-02``, ``ses-03``) and each session included a
``T1w`` and a ``BOLD`` image (resting-state), except for ``ses-03`` which was
only anatomical data.

Step 2: Think about the dataset's structure
-------------------------------------------

Now that we have our element defined, we need to think about the structure of
the dataset. Mainly, because the structure of the dataset will determine how
the DataGrabber needs to be implemented.

``junifer`` provides a concrete class to deal with datasets that can be thought
in terms of *patterns*. A *pattern* is a string that contains placeholders that
are replaced by the actual values of the element. In our BIDS example, the path
to the T1w image of subject ``sub-01`` and session ``ses-01``, relative to the
dataset location, is ``sub-01/ses-01/anat/sub-01_ses-01_T1w.nii.gz``. By
replacing ``sub-01`` with ``sub-02``, we can obtain the T1w image of the first
session of the second subject. Indeed, the path to the T1w images can be
expressed as a pattern:

``{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz``

where ``{subject}`` is the replacement for the subject id and ``{session}``
is the replacement for the session id.

Since it is a BIDS dataset, the same happens with the BOLD images. The path to
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

Step 3: Create a Data Grabber
-----------------------------

Option A: Extending from PatternDataGrabber
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`.PatternDataGrabber` class is a concrete class that has the
functionality of understanding patterns embedded in it.

Before creating the DataGrabber, we need to define 3 variables:

* ``types``: A list with the available :ref:`data_types` in our dataset.
* ``patterns``: A dictionary that specifies the pattern and some additional
  information for each data type.
* ``replacements``: A list indicating which of the elements in the patterns
  should be replaced by the values of the element.

For example, in our BIDS example, the variables will be:

.. code-block:: python

    types = ["T1w", "BOLD"]
    patterns = {
        "T1w": {
            "pattern": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
            "space": "native",
        },
        "BOLD": {
            "pattern": "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
            "space": "MNI152NLin6Asym",
        },
    }
    replacements = ["subject", "session"]

An additional fourth variable is the ``datadir``, which should be the path to
where the dataset is located. For example, if the dataset is located in
``/data/project/test/data``, then ``datadir`` should be
``/data/project/test/data``. Or, if we want to allow the user to specify the
location of the dataset, we can expose the variable in the constructor, as in
the following example.

With the variables defined above, we can create our DataGrabber and name it
``ExampleBIDSDataGrabber``:

.. code-block:: python

    from pathlib import Path

    from junifer.datagrabber import PatternDataGrabber


    class ExampleBIDSDataGrabber(PatternDataGrabber):
        def __init__(self, datadir: str | Path) -> None:
            types = ["T1w", "BOLD"]
            patterns = {
                "T1w": {
                    "pattern": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
                    "space": "native",
                },
                "BOLD": {
                    "pattern": "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
                    "space": "MNI152NLin6Asym",
                },
            }
            replacements = ["subject", "session"]
            super().__init__(
                datadir=datadir,
                types=types,
                patterns=patterns,
                replacements=replacements,
            )

Our DataGrabber is ready to be used by ``junifer``. However, it is still unknown
to the library. We need to register it in the library. To do so, we need to
use the :func:`.register_datagrabber` decorator.


.. code-block:: python

    from pathlib import Path

    from junifer.api.decorators import register_datagrabber
    from junifer.datagrabber import PatternDataGrabber


    @register_datagrabber
    class ExampleBIDSDataGrabber(PatternDataGrabber):
        def __init__(self, datadir: str | Path) -> None:
            types = ["T1w", "BOLD"]
            patterns = {
                "T1w": {
                    "pattern": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
                    "space": "native",
                },
                "BOLD": {
                    "pattern": "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
                    "space": "MNI152NLin6Asym",
                },
            }
            replacements = ["subject", "session"]
            super().__init__(
                datadir=datadir,
                types=types,
                patterns=patterns,
                replacements=replacements,
            )


Now, we can use our DataGrabber in ``junifer``, by setting the ``datagrabber``
kind in the yaml file to ``ExampleBIDSDataGrabber``. Remember that we still need
to set the ``datadir``.

.. code-block:: yaml

      datagrabber:
         kind: ExampleBIDSDataGrabber
         datadir: /data/project/test/data


Optional: Using datalad
~~~~~~~~~~~~~~~~~~~~~~~

If you are using `datalad`_, you can use the :class:`.PatternDataladDataGrabber`
instead of the :class:`.PatternDataGrabber`. This class will not only
interpret patterns, but also use `datalad`_ to ``clone`` and ``get`` the data.

The main difference between the two is that the ``datadir`` is not the actual
location of the dataset, but the location where the dataset will be cloned. It
can now be ``None``, which means that the data will be downloaded to a
temporary directory. To set the location of the dataset, you can use the
``uri`` argument in the constructor. Additionally, a ``rootdir`` argument can
be used to specify the path to the root directory of the dataset after doing
``datalad clone``.

In the example, the dataset is hosted in Gin
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

And we can create our DataGrabber:

.. code-block:: python

    from junifer.api.decorators import register_datagrabber
    from junifer.datagrabber import PatternDataladDataGrabber


    @register_datagrabber
    class ExampleBIDSDataGrabber(PatternDataladDataGrabber):
        def __init__(self) -> None:
            types = ["T1w", "BOLD"]
            patterns = {
                "T1w": {
                    "pattern": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
                    "space": "native",
                },
                "BOLD": {
                    "pattern": "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
                    "space": "MNI152NLin6Asym",
                },
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
                replacements=replacements,
            )

This approach can be used directly from the YAML, like so:

.. code-block:: yaml

   datagrabber:
     kind: PatternDataladDataGrabber
     types:
       - BOLD
       - T1w
     patterns:
       BOLD:
         pattern: "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz"
         space: MNI152NLin6Asym
       T1w:
         pattern: "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz"
         space: native
     replacements:
       - subject
       - session
     uri: "https://gin.g-node.org/juaml/datalad-example-bids"
     rootdir: example_bids_ses

Advanced: Using Unix-like path expansion directives
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is also possible to use some advanced Unix-like path expansion tricks to
define our patterns.

A very common thing would be to use ``*`` to match any number of
characters but we cannot use it right after a replacement like:

.. code-block:: python

    "derivatives/freesurfer/{subject}*"

or if there are multiple files or no files which can be globbed.

We can also use ``[]`` and ``[!]`` to glob certain tricky files like with the
case of FreeSurfer derivatives. The file structure seen in a typical
FreeSurfer derivative of a dataset (like ``AOMIC`` ones) is like so:

.. code-block::

      .
      └── derivatives
          └── freesurfer
             ├── fsaverage
             │   ├── mri
             │   |   ├── T1.mgz
             │   |   └── ...
             │   └── ...
             ├── sub-01
             │   ├── mri
             │   |   ├── T1.mgz
             │   |   └── ...
             │   |   └── ...
             │   └── ...
             ...

With a structure like this, it would be cumbersome to write custom methods
for the class and thus we could use a pattern like this:

.. code-block:: python

    "derivatives/freesurfer/[!f]{subject}/mri/T1.mg[z]"

This would ignore the ``fsaverage`` directory as a subject and let ``T1.mgz`` be
fetched as there can be many files with the same prefix.

.. _extending_datagrabbers_base:

Option B: Extending from BaseDataGrabber
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

While we could not think of a use case in which the pattern-based DataGrabber
would not be suitable, it is still possible to create a DataGrabber extending
from the :class:`.BaseDataGrabber` class.

In order to create a DataGrabber extending from :class:`.BaseDataGrabber`, we
need to implement the following methods:

- ``get_item``: to get a single item from the dataset.
- ``get_elements``: to get the list of all elements present in the dataset
- ``get_element_keys``: to get the keys of the elements in the dataset.

.. note::

   The ``__init__`` method could also be implemented, but it is not mandatory.
   This is required if the DataGrabber requires any extra parameter.

We will now implement our BIDS example with this method.

The first method, ``get_item``, needs to obtain a single
item from the dataset. Since this dataset requires two variables, ``subject``
and ``session``, we will use them as parameters of ``get_item``:

.. code-block:: python

   def get_item(self, subject: str, session: str) -> dict[str, dict[str, str]]:
       out = {
           "T1w": {
               "path": f"{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
               "space": "native",
           },
           "BOLD": {
               "path": f"{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
               "space": "MNI152NLin6Asym",
           },
       }
       return out


The second method, ``get_elements``, needs to return a list of all the elements
in the dataset. In this case, we know that the dataset contains 3 subjects and 3
sessions, so we can create a list of all the possible combinations. However, we
need to remember that for session *ses-03* there is no BOLD data.

.. code-block:: python

   from itertools import product


   def get_elements(self) -> list[str]:
       subjects = ["sub-01", "sub-02", "sub-03"]
       sessions = ["ses-01", "ses-02"]

       # If we are not working on BOLD data, we can add "ses-03"
       if "BOLD" not in self.types:
           sessions.append("ses-03")
       elements = []
       for subject, element in product(subjects, sessions):
           elements.append({"subject": subject, "session": session})
       return elements


And finally, we can implement the ``get_element_keys`` method. This method needs
to return a list of the keys that represent each of the items in the element
tuple. As a rule of thumb, they should be the parameters of the ``get_item``
method, in the same order.

.. code-block:: python

   def get_element_keys(self) -> list[str]:
       return ["subject", "session"]


So, to summarise, our DataGrabber will look like this:

.. code-block:: python

   from junifer.api.decorators import register_datagrabber
   from junifer.datagrabber import BaseDataGrabber


   @register_datagrabber
   class ExampleBIDSDataGrabber(BaseDataGrabber):
       def get_item(
           self, subject: str, session: str
       ) -> dict[str, dict[str, str]]:
           out = {
               "T1w": {
                   "path": f"{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
                   "space": "native",
               },
               "BOLD": {
                   "path": f"{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
                   "space": "MNI152NLin6Asym",
               },
           }
           return out

       def get_elements(self) -> list[str]:
           subjects = ["sub-01", "sub-02", "sub-03"]
           sessions = ["ses-01", "ses-02"]

           # If we are not working on BOLD data, we can add "ses-03"
           if "BOLD" not in self.types:
               sessions.append("ses-03")
           elements = []
           for subject in subjects:
               for session in sessions:
                   elements.append({"subject": subject, "session": session})
           return elements

       def get_element_keys(self) -> list[str]:
           return ["subject", "session"]

Optional: Using datalad
~~~~~~~~~~~~~~~~~~~~~~~

If this dataset is in a datalad dataset, we can extend from
:class:`.DataladDataGrabber` instead of :class:`.BaseDataGrabber`. This will
allow us to use the datalad API to obtain the data.

Step 4: Optional: Adding *BOLD confounds*
-----------------------------------------

For some analyses, it is useful to have the confounds associated with the BOLD
data. This corresponds to the ``BOLD.confounds`` item in the
:ref:`Data Object <data_object>` (see :ref:`data_types`). However, the
``BOLD.confounds`` element does not only consists of a ``path``, but it requires
more information about the format of the confounds file. Thus, the
``BOLD.confounds`` element is a dictionary with the following keys:

- ``path``: the path to the confounds file.
- ``format``: the format of the confounds file. Currently, this can be either
  ``fmriprep`` or ``adhoc``.

The ``fmriprep`` format corresponds to the format of the confounds files
generated by `fMRIPrep`_. The ``adhoc`` format corresponds to a format that is
not standardised.

.. note::

   The ``mappings`` key is only required if the ``format`` is ``adhoc``. If the
   ``format`` is ``fmriprep``, the ``mappings`` key is not required.

Currently, ``junifer`` provides only one confound remover step
(:class:`.fMRIPrepConfoundRemover`), which relies entirely on the ``fmriprep``
confound variable names. Thus, if the confounds are not in ``fmriprep`` format,
the user will need to provide the mappings between the *ad-hoc* variable names
and the ``fmriprep`` variable names. This is done by specifying the ``adhoc``
format and providing the mappings as a dictionary in the ``mappings`` key.

In the following example, the confounds file has 3 variables that are not in the
``fmriprep`` format. Thus, we will provide the mappings for these variables to
the ``fmriprep`` format. For example, the ``get_item`` method could look like
this:

.. code-block:: python

   def get_item(self, subject: str, session: str) -> dict:
       out = {
           "BOLD": {
               "path": f"{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
               "space": "MNI152NLin6Asym",
               "confounds": {
                   "path": f"{subject}/{session}/func/{subject}_{session}_confounds.tsv",
                   "format": "adhoc",
                   "mappings": {
                       "fmriprep": {
                           "variable1": "rot_x",
                           "variable2": "rot_z",
                           "variable3": "rot_y",
                       },
                   },
               },
           },
       }

.. note::

   Not all of the mappings need to be provided. For the moment, this is used
   only by the :class:`.fMRIPrepConfoundRemover` step, which requires variables
   based on the strategy selected. However, it is recommended to provide all the
   mappings, as this will allow the user to choose different strategies with the
   same dataset.
