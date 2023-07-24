.. include:: links.inc
.. include:: changes/contributors.inc

.. _whats_new:

What's new
==========

.. towncrier release notes start

Junifer 0.0.3 (2023-07-21)
---------------------------------

Bugfixes
^^^^^^^^

- Enable YAML 1.2 support and allow multiline strings in YAML which would not
  work earlier by `Synchon Mandal`_ (:gh:`223`)
- Handle ``datalad.IncompleteResultsError`` exception for partial clone in
  :class:`.DataladDataGrabber` by `Synchon Mandal`_ (:gh:`235`)


API Changes
^^^^^^^^^^^

- Expose ``types`` parameter for :class:`.DataladAOMICID1000`,
  :class:`.DataladAOMICPIOP1`, :class:`.DataladAOMICPIOP2` and
  :class:`.JuselessUCLA` by `Synchon Mandal`_ (:gh:`132`)
- Rename ``junifer.testing.datagrabbers.SPMAuditoryTestingDatagrabber`` to
  :class:`.SPMAuditoryTestingDataGrabber` and
  ``junifer.testing.datagrabbers.OasisVBMTestingDatagrabber`` to
  :class:`.OasisVBMTestingDataGrabber` by `Synchon Mandal`_ (:gh:`222`)
- Add :meth:`.BaseFeatureStorage.read` method for storage-like objects by
  `Synchon Mandal`_ (:gh:`236`)


Improved Documentation
^^^^^^^^^^^^^^^^^^^^^^

- Improve general prose, formatting and code blocks in docs and set line length
  for ``.rst`` files to 80 by `Synchon Mandal`_ (:gh:`220`)
- Update ``julearn`` example under ``examples`` by `Synchon Mandal`_
  (:gh:`242`)


Enhancements
^^^^^^^^^^^^

- Change validation of ``types`` against ``patterns`` to allow a subset of
  ``patterns``'s types to be used for ``DataGrabber`` data fetch by `Synchon
  Mandal`_ (:gh:`132`)
- Rename instances of "Datagrabber" to "DataGrabber" especially in
  ``junifer.testing`` to be consistent by `Synchon Mandal`_ (:gh:`222`)
- Use ``ruamel.yaml`` instead of ``pyyaml`` as YAML I/O library by `Synchon
  Mandal`_ (:gh:`223`)
- Adopt ``DataGrabber`` consistently throughout codebase to match with the
  documentation by `Synchon Mandal`_ (:gh:`226`)
- Adopt ``DataReader`` consistently throughout codebase to match with the
  documentation by `Synchon Mandal`_ (:gh:`227`)
- Enable ``stdout`` and ``stderr`` capture for AFNI commands by `Synchon
  Mandal`_ (:gh:`234`)
- Adapt :meth:`.HDF5FeatureStorage.read_df` due to addition of
  :meth:`.HDF5FeatureStorage.read` by `Synchon Mandal`_ (:gh:`236`)


Features
^^^^^^^^

- Add ``AICHA v1`` and ``AICHA v2`` parcellations to ``junifer.data`` by
  `Synchon Mandal`_ (:gh:`173`)
- Add ``Shen 2013``, ``Shen 2015`` and ``Shen 2019`` parcellations to
  ``junifer.data`` by `Synchon Mandal`_ (:gh:`184`)
- Add ``Yan 2023`` parcellation to ``junifer.data`` by `Synchon Mandal`_
  (:gh:`225`)
- Introduce :mod:`.onthefly` sub-module and :func:`.read_transform` for quick
  transform operations on stored data by `Synchon Mandal`_ (:gh:`237`)


Misc
^^^^

- Consistent docstrings for pytest fixtures used in the test suite by `Synchon
  Mandal`_ (:gh:`228`)
- Adopt ``ruff`` as the only linter for the codebase by `Synchon Mandal`_
  (:gh:`229`)
- Improve ``codespell`` support by fixing typos in documentation by `Synchon
  Mandal`_ (:gh:`230`)
- Adopt ``pre-commit`` for adding and managing git pre-commit hooks by
  `Synchon Mandal`_ (:gh:`232`)
- Improve docstrings and code style and parametrize remaining tests for
  ``junifer.data.parcellations`` by `Synchon Mandal`_ (:gh:`238`)
- Bump ``numpy`` version constraint to ``>=1.24,<1.26`` by `Synchon Mandal`_
  (:gh:`241`)


Junifer 0.0.2 (2023-03-31)
--------------------------

Bugfixes
^^^^^^^^

- Fix a bug in which relative storage URIs will be computed relative to the CWD
  and not to the location of the YAML file by `Fede Raimondo`_. (:gh:`127`)
- Fix ``junifer run`` to respect preprocess step specified in the pipeline by
  `Synchon Mandal`_ (:gh:`159`)
- Fix a bug in which only ``REST1`` and ``REST2`` tasks could be accessed in
  :class:`.DataladHCP1200` and :class:`.HCP1200` datagrabbers by `Fede
  Raimondo`_ (:gh:`183`)
- Fix a bug in which fitting a marker (e.g. ``SphereAggregation``) on a
  specific type (e.g.: ``BOLD``) will fail if another non-supported type (e.g.:
  ``BOLD_confounds``) is present in the data object by `Fede Raimondo`_
  (:gh:`185`)
- Fix :class:`.ALFFParcels`, :class:`.ALFFSpheres`, :class:`.ReHoSpheres` and
  :class:`.ReHoParcels` pass the ``extra_input`` parameter by `Fede Raimondo`_
  (:gh:`187`)
- Fix several markers that did not properly handle the ``extra_input``
  parameter by `Fede Raimondo`_ (:gh:`189`)
- Fix a bug in which relative paths in the YAML ``with`` directive would be
  computed relative to the current working directory of the process instead of
  the location of the YAML file by `Fede Raimondo`_. (:gh:`191`)
- Fix an issue with datalad cache and locks in which the user-specific
  configuration might create a conflict in high throughput systems by `Fede
  Raimondo`_ (:gh:`192`)
- Fix a bug in which :class:`.ParcelAggregation` could yield duplicated column
  names if two or more parcels were used and label names were not unique by
  `Fede Raimondo`_ (:gh:`194`)
- Fix a bug in which :func:`.count` will not be correctly applied across an
  axis by `Fede Raimondo`_ (:gh:`195`)
- Fix an issue with datalad cache and locks in which the overridden settings in
  Junifer were not propagated to subprocesses, resulting in using the default
  settings by `Fede Raimondo`_ (:gh:`199`)
- Fix a bug in which :func:`.get_mask` fails for FunctionalConnectivityBase
  class, because of missing extra_input parameter by `Leonard Sasse`_
  (:gh:`200`)
- Fix the output of :class:`.RSSETSMarker` to be 2D by `Synchon Mandal`_
  (:gh:`215`)


API Changes
^^^^^^^^^^^

- Add ``confounds_format`` parameter to :class:`.PatternDataGrabber`
  constructor for improved handling of confounds specified via
  ``BOLD_confounds`` data type by `Synchon Mandal`_ (:gh:`158`)
- Rename ``store_table()`` to ``store_vector()`` for storage-like objects and
  adapt marker-like objects to use ``"vector"`` in place of ``"table"`` for
  storage. Also, improve the logic of storing vectors by `Synchon Mandal`_
  (:gh:`181`)
- Add ``ica_fix`` parameter to :class:`.DataladHCP1200` and :class:`.HCP1200`
  datagrabbers to allow for selecting data processed with ICA+FIX. Default
  value is ``False`` which changes behaviour since 0.0.1 release. By `Fede
  Raimondo`_ (:gh:`183`)
- Add ``pre_run`` parameter to ``_queue_condor`` by `Fede Raimondo`_
  (:gh:`188`)
- Expose ``allow_overlap`` parameter in  :class:`.SphereAggregation` and
  related markers by `Fede Raimondo`_ (:gh:`190`)
- Rename ``AmplitudeLowFrequencyFluctuationParcels`` and
  ``AmplitudeLowFrequencyFluctuationSpheres`` to :class:`.ALFFParcels` and
  :class:`.ALFFSpheres` by `Synchon Mandal`_ (:gh:`216`)


Improved Documentation
^^^^^^^^^^^^^^^^^^^^^^

- Add more documentation on registering parcellations, coordinates, and masks
  by `Leonard Sasse`_ (:gh:`166`)
- Migrate and document changelog creation and maintenance via ``towncrier`` by
  `Synchon Mandal`_ (:gh:`203`)
- Add copy button to documentation code blocks by `Synchon Mandal`_ (:gh:`205`)
- Add sections *starting* and *help* in the documentation by `Fede Raimondo`_
  (:gh:`210`)
- Shorten Sphinx references across code and docs, and add ``black`` shield in
  README by `Synchon Mandal`_ (:gh:`218`)


Enhancements
^^^^^^^^^^^^

- Organize functional connectivity markers in
  ``junifer.markers.functional_connectivity`` by `Synchon Mandal`_ (:gh:`107`)
- Change HCP datagrabber tests to decrease CI running time by `Fede Raimondo`_
  (:gh:`155`)
- Allow :class:`.PartlyCloudyTestingDataGrabber` to be accessible via ``import
  junifer.testing.registry`` by `Synchon Mandal`_ (:gh:`160`)
- Update docstrings and fix typo in log message by `Synchon Mandal`_
  (:gh:`165`)
- Add fMRIPrep brain masks to the datagrabber patterns for all datagrabbers in
  the aomic sub-package by `Leonard Sasse`_ (:gh:`177`)
- Improved logging output for preprocessing, collecting and pipeline building
  from YAML by `Fede Raimondo`_ (:gh:`185`)
- Allow for empty spheres in :class:`.JuniferNiftiSpheresMasker`, that will
  result in NaNs. Also, modify the behaviour of the ``collect`` parameter in
  HTCondor ``queue`` function to run a collect job even if some of the previous
  jobs fail. This is useful to collect the results of a pipeline even if some
  of the jobs fail by `Fede Raimondo`_ (:gh:`190`)
- Allow for empty parcels in :class:`.ParcelAggregation`, that will result in
  NaNs by `Fede Raimondo`_ (:gh:`194`)
- Improve metadata and data I/O for :class:`.HDF5FeatureStorage` by `Synchon
  Mandal`_ (:gh:`196`)
- Force datalad to be non-interactive on *queued* jobs by `Fede Raimondo`_
  (:gh:`201`)
- Add missing ``abstractmethod`` decorators for ``get_valid_inputs`` methods of
  :class:`.BaseMarker` and :class:`.BasePreprocessor` by `Synchon Mandal`_
  (:gh:`214`)


Features
^^^^^^^^

- Add :class:`.EdgeCentricFCParcels` and :class:`.EdgeCentricFCSpheres` by
  `Leonard Sasse`_ (:gh:`64`)
- Expose a :func:`.merge_parcellations` function to merge a list of
  parcellations by `Leonard Sasse`_ (:gh:`146`)
- Add support for HDF5 feature storage via :class:`.HDF5FeatureStorage` by
  `Synchon Mandal`_ (:gh:`147`)
- Add :class:`.TemporalSNRParcels` and :class:`.TemporalSNRSpheres` by `Leonard
  Sasse`_ (:gh:`163`)
- Add support for ``Power`` coordinates by `Synchon Mandal`_ (:gh:`167`)
- Add support for ``Dosenbach`` coordinates by `Synchon Mandal`_ (:gh:`168`)
- Add support for nilearn computed masks (``compute_epi_mask``,
  ``compute_brain_mask``, ``compute_background_mask``,
  ``fetch_icbm152_brain_gm_mask``) by `Fede Raimondo`_ (:gh:`175`)
- Add aggregation function :func:`.count` that returns the number of elements
  in a given axis. This allows to count the number of voxels per sphere/parcel
  when used as ``method`` in markers by `Fede Raimondo`_ (:gh:`190`)


Junifer 0.0.1 (2022-12-20)
--------------------------

Bugfixes
^^^^^^^^

- Fix a bug in which a :class:`.PatternDataGrabber` would now work with
  relative ``datadir`` paths (reported by `Leonard Sasse`_, fixed by
  `Fede Raimondo`_) (:gh:`96`, :gh:`98`)

- Fix a bug in which :class:`.DataladAOMICPIOP2` datagrabber did not use user
  input to constrain elements based on tasks by `Leonard Sasse`_ (:gh:`105`)

- Fix a bug in which a datalad dataset could remove a user-cloned dataset by
  `Fede Raimondo`_ (:gh:`53`)

- Fix a bug in which CLI command would not work using elements with more than
  one field by `Fede Raimondo`_

- Fix a bug in which the generated DAG for HTCondor will not work by
  `Fede Raimondo`_ (:gh:`143`)


API Changes
^^^^^^^^^^^

- Change the ``single_output`` default parameter in storage classes from
  ``False`` to ``True`` by `Fede Raimondo`_ (:gh:`134`)


Improved Documentation
^^^^^^^^^^^^^^^^^^^^^^

- Add an example how to use ``junifer`` and ``julearn`` in one pipeline to
  extract features and do machine learning by `Leonard Sasse`_,
  `Nicolas Nieto`_, and `Sami Hamdan`_ (:gh:`40`)

- Add documentation for the datagrabbers by `Leonard Sasse`_,
  `Nicolas Nieto`_, and `Sami Hamdan`_

- Change documentation template to furo. Fix references and standardize
  documentation by `Fede Raimondo`_ (:gh:`114`)


Enhancements
^^^^^^^^^^^^

- Add comments to :class:`.DataladDataGrabber` datagrabber and change to use
  ``datalad-clone`` instead of ``datalad-install`` by `Benjamin Poldrack`_
  (:gh:`55`)

- Upgrade storage interface for storage-like objects by `Synchon Mandal`_
  (:gh:`84`)

- Add missing type annotations by `Synchon Mandal`_ (:gh:`74`)

- Refactor markers ``on`` attribute and ``get_valid_inputs`` to verify that the
  marker can be computed on the input data types by `Fede Raimondo`_

- Add test for :class:`.DataladHCP1200` datagrabber by `Synchon Mandal`_
  (:gh:`93`)

- Refactor :class:`.DataladAOMICID1000` slightly by `Leonard Sasse`_ (:gh:`94`)

- Rename "atlas" to "parcellation" by `Fede Raimondo`_ (:gh:`116`)

- Refactor the :class:`.BaseDataGrabber` class to allow for easier subclassing
  by `Fede Raimondo`_ (:gh:`123`)

- Allow custom aggregation method for :class:`.SphereAggregation` by
  `Synchon Mandal`_ (:gh:`102`)

- Add support for "masks" by `Fede Raimondo`_ (:gh:`79`)

- Allow :class:`.ParcelAggregation` to apply multiple parcellations at once by
  `Fede Raimondo`_ (:gh:`131`)

- Refactor :class:`.PipelineStepMixin` to improve its implementation and
  validation for pipeline steps by `Synchon Mandal`_ (:gh:`152`)


Features
^^^^^^^^

- Implement :class:`.SPMAuditoryTestingDataGrabber` datagrabber by
  `Fede Raimondo`_ (:gh:`52`)

- Implement matrix storage in SQliteFeatureStorage by `Fede Raimondo`_
  (:gh:`42`)

- Implement :class:`.FunctionalConnectivityParcels` marker for functional
  connectivity using a parcellation by `Amir Omidvarnia`_ and
  `Kaustubh R. Patil`_ (:gh:`41`)

- Implement :func:`.register_coordinates`, :func:`.list_coordinates` and
  :func:`.load_coordinates` by `Fede Raimondo`_ (:gh:`11`)

- Add :class:`.DataladAOMICID1000` datagrabber for AOMIC ID1000 dataset
  including tests and creation of mock dataset for testing by
  `Vera Komeyer`_ and `Xuan Li`_ (:gh:`60`)

- Add support to access other input in the data object in the ``compute`` method
  by `Fede Raimondo`_

- Implement :class:`.RSSETSMarker` marker by `Leonard Sasse`_, `Nicolas Nieto`_
  and `Sami Hamdan`_ (:gh:`51`)

- Implement :class:`.SphereAggregation` marker by `Fede Raimondo`_ (:gh:`83`)

- Implement :class:`.DataladAOMICPIOP1` and :class:`.DataladAOMICPIOP2`
  datagrabbers for AOMIC PIOP1 and PIOP2 datasets respectively by
  `Leonard Sasse`_ (:gh:`94`)

- Implement :class:`.JuselessDataladCamCANVBM` datagrabber by `Leonard Sasse`_
  (:gh:`99`)

- Implement :class:`.JuselessDataladIXIVBM` CAT output datagrabber for juseless
  by `Leonard Sasse`_ (:gh:`48`)

- Add ``junifer wtf`` to report environment details by `Synchon Mandal`_
  (:gh:`33`)

- Add ``junifer selftest`` to report environment details by `Synchon Mandal`_
  (:gh:`9`)

- Implement :class:`.JuselessDataladAOMICID1000VBM` datagrabber for accessing
  AOMIC ID1000 VBM from juseless by `Felix Hoffstaedter`_ and `Synchon Mandal`_
  (:gh:`57`)

- Add :class:`.fMRIPrepConfoundRemover` by `Fede Raimondo`_ and `Leonard Sasse`_
  (:gh:`111`)

- Implement :class:`.CrossParcellationFC` marker by `Leonard Sasse`_ and
  `Kaustubh R. Patil`_ (:gh:`85`)

- Add :class:`.JuselessUCLA` datagrabber for the UCLA dataset available on
  juseless by `Leonard Sasse`_ (:gh:`118`)

- Introduce a singleton decorator for marker computations by `Synchon Mandal`_
  (:gh:`151`)

- Implement :class:`.ReHoParcels` and :class:`.ReHoSpheres` markers by
  `Synchon Mandal`_ (:gh:`36`)

- Implement :class:`.ALFFParcels` and :class:`.ALFFSpheres` markers by
  `Fede Raimondo`_ (:gh:`35`)


Misc
^^^^

- Create the repository based on the mockup by `Fede Raimondo`_
