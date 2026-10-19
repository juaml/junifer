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

.. _datagrabber_elements:

Elements
--------

A DataGrabber gives the data of a dataset in small units called *elements*. An
element is the smallest unit of data that can be processed: it has one file
for each :ref:`data type <data_types>` (e.g., one ``T1w`` image and one
``BOLD`` image). Each element is identified by the values of its *keys*, e.g.,
the element ``("sub-01", "rest")`` has the value ``sub-01`` for the key
``subject`` and ``rest`` for the key ``task``.

To see how this works, we will use this small dataset with two subjects, a
``T1w`` image for each subject and a ``BOLD`` image for each subject and task
(``sub-02`` has no ``movie`` task):

.. code-block:: text

    sub-01/anat/sub-01_T1w.nii.gz
    sub-01/func/sub-01_task-rest_bold.nii.gz
    sub-01/func/sub-01_task-movie_bold.nii.gz
    sub-02/anat/sub-02_T1w.nii.gz
    sub-02/func/sub-02_task-rest_bold.nii.gz

A :class:`.PatternDataGrabber` describes the files of each data type with a
*pattern*, where the parts that change between the files (the *replacements*)
are written between braces:

.. code-block:: yaml

  datagrabber:
    kind: PatternDataGrabber
    datadir: /data/example
    types:
      - T1w
      - BOLD
    patterns:
      T1w:
        pattern: "{subject}/anat/{subject}_T1w.nii.gz"
        space: native
      BOLD:
        pattern: "{subject}/func/{subject}_task-{task}_bold.nii.gz"
        space: native
    replacements:
      - subject
      - task

Which data types are grabbed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The DataGrabber finds the elements by searching the dataset for the files that
match the patterns. The keys of the elements are the replacements in the
patterns of the data types to grab (``types``), and an element is only
available if it has a file for each of these data types:

.. list-table::
   :widths: auto
   :header-rows: 1

   * - ``types``
     - Keys
     - Elements
   * - ``T1w``
     - ``subject``
     - ``sub-01``, ``sub-02``
   * - ``BOLD``
     - ``subject``, ``task``
     - ``(sub-01, movie)``, ``(sub-01, rest)``, ``(sub-02, rest)``
   * - ``T1w``, ``BOLD``
     - ``subject``, ``task``
     - ``(sub-01, movie)``, ``(sub-01, rest)``, ``(sub-02, rest)``

With only ``T1w``, the elements do not have the ``task`` key, as the ``T1w``
image does not depend on the task: each ``T1w`` image is processed once. With
``BOLD``, the elements need the task, so the ``T1w`` image of ``sub-01`` is part
of two elements, ``(sub-01, movie)`` and ``(sub-01, rest)``.

Which values are grabbed
^^^^^^^^^^^^^^^^^^^^^^^^

By default, all the values found in the dataset are grabbed. They can be
restricted with ``replacements``, giving the values to grab for each
replacement (or ``null`` to grab all of them). For example, to only grab the
``rest`` task:

.. code-block:: yaml

    replacements:
      subject: null
      task:
        - rest

The :doc:`built-in DataGrabbers <../builtin>` have parameters for this instead,
e.g., ``tasks`` in :class:`.DataladAOMICPIOP1`. The values only restrict the
elements of the data types that use the replacement:

.. list-table::
   :widths: auto
   :header-rows: 1

   * - ``types``
     - Values to grab
     - Elements
   * - ``BOLD``
     - ``task``: ``rest``
     - ``(sub-01, rest)``, ``(sub-02, rest)``
   * - ``BOLD``
     - ``subject``: ``sub-02``
     - ``(sub-02, rest)``
   * - ``T1w``
     - ``task``: ``rest``
     - ``sub-01``, ``sub-02`` (the ``T1w`` image does not depend on the task)

The elements with other values are not listed, and asking for them (e.g.,
``(sub-01, movie)`` when only ``rest`` is grabbed) raises an error. See
:ref:`extending_datagrabbers_replacement_values` for more details, and
:ref:`extending_datagrabbers_path_expansion` for patterns with ``*``, e.g., to
match files whose names change with the task.

Which elements are processed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``list-elements`` command lists the elements of the dataset. By default,
the ``run`` and ``queue`` commands process all of them, but the ``--element``
option can select some of them, with the values of the keys separated by
``,``. With ``BOLD``:

.. list-table::
   :widths: auto
   :header-rows: 1

   * - ``--element``
     - Elements processed
   * - ``sub-01,rest``
     - ``(sub-01, rest)``: a *complete* element (a value for each key, in
       order), the dataset is not searched
   * - ``sub-01``
     - ``(sub-01, movie)``, ``(sub-01, rest)``: a *partial* element selects all
       the elements with its values
   * - ``rest``
     - ``(sub-01, rest)``, ``(sub-02, rest)``
   * - ``sub-03``
     - None: an error is raised, as no element matches it

See :ref:`running_elements` for more details.

.. _datagrabber_multiple:

Combining datasets
------------------

The :class:`.MultipleDataGrabber` combines several DataGrabbers, e.g., to use
data from different datasets. For example, we can take the ``BOLD`` and
``T1w`` images from a dataset with the fMRIPrep derivatives, the ``VBM_GM``
images from a dataset with the CAT12 derivatives, and the confounds of the
``BOLD`` images from a third dataset:

.. code-block:: yaml

  datagrabber:
    kind: MultipleDataGrabber
    datagrabbers:
      # BOLD and T1w from the fMRIPrep derivatives
      - kind: DataladAOMICPIOP1
        types:
          - BOLD
          - T1w
        tasks:
          - restingstate
      # VBM from the CAT12 derivatives
      - kind: PatternDataladDataGrabber
        uri: https://example.org/aomic-piop1-cat12
        types:
          - VBM_GM
        patterns:
          VBM_GM:
            pattern: "{subject}/mri/mwp1{subject}_T1w.nii"
            space: MNI152NLin2009cAsym
        replacements:
          - subject
      # Only the confounds of the BOLD images
      - kind: PatternDataladDataGrabber
        uri: https://example.org/aomic-piop1-confounds
        types:
          - BOLD
        patterns:
          BOLD:
            confounds:
              pattern: "{subject}/func/{subject}_task-{task}_acq-*_desc-confounds.tsv"
              format: fmriprep
        replacements:
          - subject
          - task
        partial_pattern_ok: true

The DataGrabbers are combined with these rules:

* **Each data type is grabbed by one DataGrabber**, which is chosen with the
  ``types`` of each DataGrabber. Here, the first one grabs ``BOLD`` and
  ``T1w``, and the second one ``VBM_GM``. If the first one also grabbed
  ``VBM_GM`` (e.g., without setting its ``types``), an error would be raised,
  asking to remove it from the ``types`` of one of them.
* **A DataGrabber that only grabs the nested data types of a data type**
  (without the main file of the data type) replaces these nested data types
  of the other DataGrabber. Here, the third one only grabs the ``confounds``
  of ``BOLD``, so they replace the ones of the first DataGrabber, regardless
  of the order of the DataGrabbers.
* **The elements are the ones available in all the DataGrabbers.** The
  DataGrabbers can have different keys: the element keys are the ones of the
  first DataGrabber, followed by the other keys of the other DataGrabbers, and
  each DataGrabber grabs an element with its own keys. The keys with the same
  name must have the same values in all the datasets (e.g., the same subject
  names).

For the element ``(sub-0001, restingstate)``:

.. list-table::
   :widths: auto
   :header-rows: 1

   * - DataGrabber
     - Keys
     - Grabs
   * - First (fMRIPrep)
     - ``subject``, ``task``
     - ``(sub-0001, restingstate)``: the ``BOLD`` image (with its mask) and
       the ``T1w`` image
   * - Second (CAT12)
     - ``subject``
     - ``sub-0001``: the ``VBM_GM`` image
   * - Third (confounds)
     - ``subject``, ``task``
     - ``(sub-0001, restingstate)``: the confounds of the ``BOLD`` image

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
       | DataGrabber, you need to override the ``get_element_keys``,
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
   * - :class:`.MultipleDataGrabber`
     - | It combines several DataGrabbers, e.g., to use data from different
       | datasets (see :ref:`datagrabber_multiple`).
