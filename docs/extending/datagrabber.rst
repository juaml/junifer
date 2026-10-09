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

When the DataGrabber only grabs some of the data types, the elements only have
the items that these data types need. For example, if only the ``T1w`` image is
grabbed, the elements are (``subject``, ``session``), e.g., (``sub001``,
``ses1``), so that the same ``T1w`` image is not processed once for each task.
For the :class:`.PatternDataGrabber` (see below), the items that the data types
need are the replacements in their patterns.

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

    from junifer.datagrabber import PatternDataGrabber, DataType
    from junifer.typing import DataGrabberPatterns


    class ExampleBIDSDataGrabber(PatternDataGrabber):

        types: list[DataType] = [DataType.T1w, DataType.BOLD]
        patterns: DataGrabberPatterns = {
            "T1w": {
                "pattern": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
                "space": "native",
            },
            "BOLD": {
                "pattern": "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
                "space": "MNI152NLin6Asym",
            },
        }
        replacements: list[str] = ["subject", "session"]

Our DataGrabber is ready to be used by ``junifer``. However, it is still unknown
to the library. We need to register it in the library. To do so, we need to
use the :func:`.register_datagrabber` decorator.


.. code-block:: python

    from pathlib import Path

    from junifer.api.decorators import register_datagrabber
    from junifer.datagrabber import PatternDataGrabber
    from junifer.typing import DataGrabberPatterns


    @register_datagrabber
    class ExampleBIDSDataGrabber(PatternDataGrabber):

        types: list[DataType] = [DataType.T1w, DataType.BOLD]
        patterns: DataGrabberPatterns = {
            "T1w": {
                "pattern": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
                "space": "native",
            },
            "BOLD": {
                "pattern": "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
                "space": "MNI152NLin6Asym",
            },
        }
        replacements: list[str] = ["subject", "session"]


Now, we can use our DataGrabber in ``junifer``, by setting the ``datagrabber``
kind in the yaml file to ``ExampleBIDSDataGrabber``. Remember that we still need
to set the ``datadir``.

.. code-block:: yaml

      datagrabber:
         kind: ExampleBIDSDataGrabber
         datadir: /data/project/test/data

The DataGrabber finds the elements by searching the dataset for the files that
match the pattern of each data type. An element is only available if it has the
files of all the data types to grab. In our BIDS example, ``ses-03`` only has
anatomical data, so the elements with ``ses-03`` are only available when only
the ``T1w`` data type is grabbed.


.. _extending_datagrabbers_replacement_values:

Restricting the values of the replacements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the DataGrabber grabs all the values of the replacements found in
the dataset. To only grab some of them, ``replacements`` can be a dictionary
with the values to grab for each replacement (or ``None`` to grab all of them).
For example, to only grab the first two sessions of our BIDS example with the
:class:`.PatternDataGrabber` in the YAML file:

.. code-block:: yaml

      datagrabber:
         kind: PatternDataGrabber
         datadir: /data/project/test/data
         types:
            - T1w
            - BOLD
         patterns:
            T1w:
               pattern: "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz"
               space: native
            BOLD:
               pattern: "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz"
               space: MNI152NLin6Asym
         replacements:
            subject: null
            session:
               - ses-01
               - ses-02

The elements with other values are not listed, and grabbing them raises an
error. The values are ignored if the data types to grab do not use the
replacement, e.g., the ``session`` values with a data type that is the same for
all the sessions.

A DataGrabber can also take the values to grab from one of its fields, e.g.,
``sessions``, by linking the field to the replacement with
``_REPLACEMENT_FIELDS``. The values of the field can be strings or enumerations
(a :class:`enum.StrEnum` is recommended, so its members are also the strings),
and the replacement cannot have values in ``replacements`` too:

.. code-block:: python

    from enum import StrEnum
    from typing import ClassVar

    from junifer.api.decorators import register_datagrabber
    from junifer.datagrabber import DataType, PatternDataGrabber
    from junifer.typing import DataGrabberPatterns


    class Sessions(StrEnum):
        ses_01 = "ses-01"
        ses_02 = "ses-02"
        ses_03 = "ses-03"


    @register_datagrabber
    class ExampleBIDSDataGrabber(PatternDataGrabber):

        types: list[DataType] = [DataType.T1w, DataType.BOLD]
        patterns: DataGrabberPatterns = {
            "T1w": {
                "pattern": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
                "space": "native",
            },
            "BOLD": {
                "pattern": "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
                "space": "MNI152NLin6Asym",
            },
        }
        replacements: list[str] = ["subject", "session"]
        sessions: list[Sessions] = list(Sessions)
        # Only grab the sessions in the `sessions` field
        _REPLACEMENT_FIELDS: ClassVar[dict[str, str]] = {"session": "sessions"}

Then, the sessions to grab can be set in the YAML file:

.. code-block:: yaml

      datagrabber:
         kind: ExampleBIDSDataGrabber
         datadir: /data/project/test/data
         sessions:
            - ses-01
            - ses-02


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

In the example, the dataset is hosted in cerebra.fz-juelich.de
(``https://cerebra.fz-juelich.de/junifer/datalad-example-bids-ses.git``).

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

    uri = "https://cerebra.fz-juelich.de/junifer/datalad-example-bids-ses.git"
    rootdir = "example_bids_ses"

And we can create our DataGrabber:

.. code-block:: python

    from pathlib import Path

    from junifer.api.decorators import register_datagrabber
    from junifer.datagrabber import PatternDataladDataGrabber
    from pydantic import AnyUrl


    @register_datagrabber
    class ExampleBIDSDataGrabber(PatternDataladDataGrabber):

        uri: AnyUrl = "https://cerebra.fz-juelich.de/junifer/datalad-example-bids-ses.git"
        types: list[DataType] = ["T1w", "BOLD"]
        patterns: DataGrabberPatterns = {
            "T1w": {
                "pattern": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
                "space": "native",
            },
            "BOLD": {
                "pattern": "{subject}/{session}/func/{subject}_{session}_task-rest_bold.nii.gz",
                "space": "MNI152NLin6Asym",
            },
        }
        replacements: list[str] = ["subject", "session"]
        rootdir: Path = "example_bids_ses"

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
     uri: "https://cerebra.fz-juelich.de/junifer/datalad-example-bids-ses.git"
     rootdir: example_bids_ses

.. _extending_datagrabbers_path_expansion:

Advanced: Using Unix-like path expansion directives
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is also possible to use some advanced Unix-like path expansion tricks to
define our patterns.

A very common thing would be to use ``*`` to match any number of characters
or ``?`` to match a single character, both to find the elements and to grab
their data. For example, if the acquisition of the BOLD images depends on the
task (e.g., ``sub-01_task-rest_acq-mb3_bold.nii.gz`` and
``sub-01_task-stroop_acq-seq_bold.nii.gz``), the pattern can match any
acquisition, so the task values are ``rest`` and ``stroop``:

.. code-block:: python

    "{subject}/func/{subject}_task-{task}_acq-*_bold.nii.gz"

Similarly, ``?`` can match the first character of ``rfMRI`` (resting-state)
and ``tfMRI`` (task) in the HCP dataset:

.. code-block:: python

    "{subject}/MNINonLinear/Results/?fMRI_{task}_{phase_encoding}/?fMRI_{task}_{phase_encoding}.nii.gz"

The pattern must match exactly one file for each element, and we cannot use
``*`` right after a replacement like:

.. code-block:: python

    "derivatives/freesurfer/{subject}*"

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

   If the DataGrabber requires any extra parameter, they could be defined as
   class attributes.

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
- ``format``: the format of the confounds file. Check :enum:`.ConfoundsFormat`
  for options.

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
