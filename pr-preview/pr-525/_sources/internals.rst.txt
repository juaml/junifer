.. include:: links.inc

.. _internals:

Implementation details
======================

This section describes some of the assumptions and technical details of
``junifer``, for developers. See the docstrings of the mentioned functions and
classes for more details.

Elements
--------

* The keys of the elements of a :class:`.PatternDataGrabber`
  (:meth:`.PatternDataGrabber.get_element_keys`) are the replacements used by
  the patterns (including the nested ones) of the data types to grab, in the
  order of ``replacements``.
* :meth:`.PatternDataGrabber.get_elements` finds the elements of each pattern
  in the files (translating the Unix-like path expansion directives of the
  patterns to a regular expression) and joins the elements of the patterns on
  their common keys (``_join_elements``), so an element is available if it has
  the files of all the data types, regardless of their order.
* The values of the replacements to grab (:meth:`.PatternDataGrabber.get_replacement_values`)
  are given by ``replacements`` (as a dictionary) or by the fields linked to
  the replacements in ``_REPLACEMENT_FIELDS``, but not both. They filter the
  elements found in the files, and grabbing an element with other values
  raises an error (``_check_element``, called by
  ``BaseDataGrabber.__getitem__``).
* :meth:`.BaseDataGrabber.select_elements` selects the elements to run: the
  selectors must have the same number of values. If they have a value for
  each element key, they are the elements (the dataset is not searched),
  otherwise they select the elements of the dataset that have their values.
* :class:`.MultipleDataGrabber` joins the elements of its DataGrabbers on
  their common keys, and grabs an element with each DataGrabber using its
  keys. Each data type is grabbed by one DataGrabber, except for the nested
  data types grabbed by a DataGrabber without the main file of the data type,
  which replace the ones of the other DataGrabber.

Metadata
--------

The ``meta`` of each data type in the :ref:`data object <data_object>` is
built by the steps of the pipeline. Each step adds an entry with its class and
parameters (``UpdateMetaMixin.update_meta``) and its dependencies:

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Key
     - Added by
     - Content
     - In the MD5
   * - ``datagrabber``
     - DataGrabber
     - The class and parameters of the DataGrabber, e.g., ``types``,
       ``patterns`` and ``replacements``. For the DataLad-based ones, also the
       dataset ID and commit, and whether the dataset has local changes
       (``datalad_id``, ``datalad_commit_id`` and ``datalad_dirty``), so
       different versions of the dataset give different hashes. For :class:`.MultipleDataGrabber`, also
       ``datagrabbers`` with the entries of its DataGrabbers.
     - Yes, except ``datadir`` for the DataLad-based DataGrabbers (which is
       removed from the stored metadata too)
   * - ``element``
     - DataGrabber
     - The element being processed (see below).
     - No
   * - ``_element_keys``
     - DataGrabber
     - The keys of the element that the data depends on (see below).
     - Yes
   * - ``datareader``
     - DataReader
     - The class and parameters of the DataReader.
     - Yes
   * - ``preprocess``
     - Preprocessors
     - The list of the classes and parameters of the preprocessors that
       processed the data, in order.
     - Yes
   * - ``type``
     - Marker
     - The data type, e.g., ``BOLD``.
     - Yes
   * - ``marker``
     - Marker
     - The class and parameters of the marker, with ``name`` as the name of
       the marker followed by the name of the feature, e.g., ``mean_mean``.
     - Yes
   * - ``dependencies``
     - All the steps
     - The names of the dependencies of the steps (their ``_DEPENDENCIES``).
       When storing, they are replaced by their versions, with the version of
       ``junifer``, e.g., ``{'junifer': '0.0.8', 'nilearn': '0.14.1'}``.
     - Yes (the versions)
   * - ``name``
     - Storage (``process_meta``)
     - The name of the feature: the data type and the marker name, e.g.,
       ``BOLD_mean_mean``.
     - Yes

The DataGrabber adds two keys about the element to the ``meta`` of each data
type (``BaseDataGrabber.__getitem__``):

* ``element``: the element being processed, with all its keys. It is the same
  for all the data types of the element.
* ``_element_keys``: the keys of the element that the data of the data type
  depends on (:meth:`.BaseDataGrabber.get_type_element_keys`). 
  For a :class:`.PatternDataGrabber`, the replacements in the patterns of the
  data type.

For example, with ``BOLD`` data for each subject and task, and ``VBM_GM`` data
for each subject, the element ``(sub-01, rest)`` gives:

.. code-block::

   {'BOLD': {'meta': {'_element_keys': ['subject', 'task'],
                      'element': {'subject': 'sub-01', 'task': 'rest'},
                      ...},
             ...},
    'VBM_GM': {'meta': {'_element_keys': ['subject'],
                        'element': {'subject': 'sub-01', 'task': 'rest'},
                        ...},
               ...}}

When storing the output of a marker, ``process_meta`` (in ``junifer.storage.utils``):

* Removes ``element`` from the metadata and returns the element of the data,
  with only the keys in ``_element_keys`` (all the keys of ``element`` if it
  is not set).
* Computes the MD5 hash of the metadata, which identifies the feature. It
  includes ``_element_keys`` and the versions of the dependencies of the
  steps and of ``junifer``, but not ``element``: the data of all the elements
  of a feature have the same hash, and the features computed with different
  versions of ``junifer`` (or of the dependencies) have different hashes.

Storage
-------

* The data is stored for the element of the data (the element with only the
  keys in ``_element_keys``), so the data that does not depend on a key (e.g.,
  the ``VBM_GM`` data for the tasks of a subject) is stored once.
* :meth:`.BaseFeatureStorage.store` passes the element being processed to
  the methods storing the metadata and the data (``store_metadata``,
  ``store_vector``, etc.) as ``processed_element``, besides the element of the
  data (``element``). The storages that write a file for each element (with
  ``single_output=False``) name it after the element being processed, e.g.,
  ``element_sub-01_rest_out.hdf5``, so that the processes running different
  elements in parallel never write to the same file. The storages without
  files (e.g., databases) can ignore it, but their methods must accept it.
* The data already stored for an element is not stored again (the storages
  skip the existing elements, :class:`.SQLiteFeatureStorage` with
  ``upsert="ignore"`` by default).
* ``collect`` only collects the files of single elements (one element for
  each feature, as written for each element with ``single_output=False``),
  and raises an error otherwise. The data of an element can be in the files
  of several elements being processed (e.g., the ``VBM_GM`` data of
  ``sub-01`` in the files of each of its tasks), and it is only collected
  once.
* :meth:`.HDF5FeatureStorage.collect` works in two passes: the first one reads
  the metadata and the elements of each file, to know which files to collect
  for each feature (one for each element), and the second one collects the
  data of each feature from these files, in chunks. Each file is read once in
  the first pass, and once for each of its features in the second one.
