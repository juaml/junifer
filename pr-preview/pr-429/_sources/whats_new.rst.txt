.. include:: links.inc
.. include:: changes/contributors.inc

.. _whats_new:

What's new
==========

.. towncrier-draft-entries:: |release|

.. towncrier release notes start

Junifer 0.0.5 (2024-07-22)
--------------------------

Bugfixes
^^^^^^^^

- Remove extra dimension from parcellations warped via ANTs to other template
  spaces by `Synchon Mandal`_ (:gh:`324`)
- Remove extra dimension from parcellations warped via ANTs when merging
  parcellations by `Synchon Mandal`_ (:gh:`331`)
- Fix ``junifer reset`` to properly delete storage directory and handle
  ``junifer_jobs`` deletion if not empty by `Synchon Mandal`_ (:gh:`332`)
- Fix validation failure of multiple Preprocessors with different input data
  types requirement by `Synchon Mandal`_ (:gh:`339`)
- Remove extra dimension from masks warped via ANTs by `Synchon Mandal`_
  (:gh:`340`)


API Changes
^^^^^^^^^^^

- For :class:`.CrossParcellationFC`, ``aggregation_method`` and
  ``correlation_method`` have been renamed to ``agg_method`` and
  ``corr_method`` respectively and ``agg_method_params`` has been added; for
  ``FunctionalConnectivityBase``, :class:`.FunctionalConnectivityParcels`,
  :class:`.FunctionalConnectivitySpheres`, :class:`.EdgeCentricFCParcels` and
  :class:`.EdgeCentricFCSpheres`, ``cor_method`` and ``cor_method_params`` have
  been renamed to ``conn_method`` and ``conn_method_params`` by `Synchon
  Mandal`_ (:gh:`348`)
- ``fractional`` parameter for ``ALFFBase``, :class:`.ALFFParcels` and
  :class:`.ALFFSpheres` have been removed in favour of returning both ALFF and
  fALFF by `Synchon Mandal`_ (:gh:`349`)
- Add ``partial_pattern_ok`` argument to :class:`.PatternDataGrabber` to not
  raise error on missing mandatory key checks for data types by `Synchon
  Mandal`_ (:gh:`351`)


Improved Documentation
^^^^^^^^^^^^^^^^^^^^^^

- Improve sub-package level docstrings to better reflect their purposes by
  `Synchon Mandal`_ (:gh:`115`)
- Update "Queueing Jobs (HPC, HTC)" section by `Synchon Mandal`_ (:gh:`327`)
- Add missing DataGrabber ``types`` options in respective docstrings of
  :class:`.DataladAOMICID1000`, :class:`.DataladAOMICPIOP1`,
  :class:`.DataladAOMICPIOP2` and :class:`.DMCC13Benchmark` by `Synchon
  Mandal`_ (:gh:`330`)


Enhancements
^^^^^^^^^^^^

- Add test to be sure that :class:`.JuniferNiftiSpheresMasker` with mean
  aggregation function behaves exactly as
  :class:`nilearn.maskers.NiftiSpheresMasker` by `Synchon Mandal`_ (:gh:`136`)
- Refactor DataGrabber ``patterns`` to make helper types like ``*_mask`` as
  "nested types" of the actual data type by `Synchon Mandal`_ (:gh:`341`)
- Adapt :class:`.DataladAOMICID1000`, :class:`.DataladAOMICPIOP1` and
  :class:`.DataladAOMICPIOP2` to support ``FreeSurfer`` data type by `Synchon
  Mandal`_ (:gh:`346`)
- ``FunctionalConnectivity``-family Markers now use
  :class:`sklearn.covariance.EmpiricalCovariance` as the default covariance
  estimator and ``correlation`` as the default connecivity matrix kind by
  `Synchon Mandal`_ (:gh:`348`)
- Enable Markers to output multiple features by `Synchon Mandal`_ (:gh:`349`)
- Add support for ``UKB_15K_GM`` mask by `Synchon Mandal`_ (:gh:`350`)
- Adapt :class:`.MultipleDataGrabber` to handle "nested types" introduced in
  :gh:`341` by `Synchon Mandal`_ (:gh:`351`)


Features
^^^^^^^^

- Introduce :class:`.Smoothing` for smoothing / blurring images as a
  preprocessing step by `Synchon Mandal`_ (:gh:`161`)
- Add support for choosing between ``bash`` and ``zsh`` shells when queueing by
  `Synchon Mandal`_ (:gh:`273`)
- Add ``junifer list-elements`` to list out available elements for a
  DataGrabber based on filtering via ``--element`` by `Synchon Mandal`_
  (:gh:`323`)
- Introduce new storage type ``scalar_table`` and adapt
  :class:`.HDF5FeatureStorage` to support it by `Synchon Mandal`_ (:gh:`343`)
- Add support for `BrainPrint
  <https://github.com/Deep-MI/BrainPrint?tab=readme-ov-file>`_ marker by
  `Synchon Mandal`_ (:gh:`344`)
- Allow Unix path expansion directives to be used in
  :class:`.PatternDataGrabber` ``patterns`` by `Synchon Mandal`_ (:gh:`345`)
- Add support for ``FreeSurfer`` data type for :class:`.PatternDataGrabber` by
  `Synchon Mandal`_ (:gh:`346`)
- Introduce :class:`.JuniferConnectivityMeasure` for customising functional
  connectivity matrix kinds and measurements by `Synchon Mandal`_ (:gh:`348`)
- Introduce :class:`.PatternValidationMixin` to simplify validation for
  pattern-based DataGrabbers and :func:`.deep_update` for updating dictionary
  with varying width and depth by `Synchon Mandal`_ (:gh:`351`)


Miscellaneous
^^^^^^^^^^^^^

- Improve CI to allow external tool installation to fail gracefully and update
  necessary dependency version and conditional checks by `Synchon Mandal`_
  (:gh:`318`)
- Update ``pre-commit`` dependency versions, add ``blacken-docs`` to
  ``pre-commit``, add ``__all__`` for modules, sub-packages and package, update
  ``ruff`` and ``pytest`` configs in ``pyproject.toml`` by `Synchon Mandal`_
  (:gh:`337`)
- Add support for accessing FreeSurfer via Docker wrapper along with
  ``mri_binarize``, ``mri_pretess``, ``mri_mc`` and ``mris_convert`` by
  `Synchon Mandal`_ (:gh:`342`)
- Update core and docs dependencies by `Synchon Mandal`_ (:gh:`347`)
- Integrate ``warnings`` with ``logging`` respecting filters by `Fede
  Raimondo`_ (:gh:`351`)


Deprecations and Removals
^^^^^^^^^^^^^^^^^^^^^^^^^

- Remove ``Power`` coordinates, ``fetch_icbm152_brain_gm_mask`` mask,
  ``BOLDWarper`` Preprocessor by `Synchon Mandal`_ (:gh:`336`)


Junifer 0.0.4 (2024-04-05)
--------------------------

Bugfixes
^^^^^^^^

- Make copying of assets in ``with`` block of YAML, relative to YAML and not to
  current working directory by `Fede Raimondo`_ and `Synchon Mandal`_
  (:gh:`224`)
- Adapt ``junifer queue`` to properly use HTCondor >=10.4.0
  ``condor_submit_dag`` by `Fede Raimondo`_ and `Synchon Mandal`_ (:gh:`233`)
- Use 1 instead of 0 for successful FSL commands in ``_check_fsl()`` by
  `Synchon Mandal`_ (:gh:`272`)
- Store native warped parcellations, coordinates and masks in element-scoped
  tempdirs for the pipeline to work by `Synchon Mandal`_ (:gh:`274`)
- Change interpolation scheme for parcel and mask native space transformation
  to nearest neighbour by `Synchon Mandal`_ (:gh:`276`)
- Bypass FSL ``std2imgcoord`` stdin bug and use recommended piped input for
  coordinates transformation by `Synchon Mandal`_ (:gh:`278`)
- Add ``-std`` to FSL ``std2imgcoord`` for coordinates transformation by
  `Synchon Mandal`_ (:gh:`280`)
- Replace FSL ``std2imgcoord`` with ``img2imgcoord`` as the former is incorrect
  for coordinates transformation to other template spaces. (:gh:`281`)
- Propagate ReHo and fALFF maps, for aggregation to convert to other template
  spaces when required by `Synchon Mandal`_ (:gh:`282`)
- Allow :class:`junifer.pipeline.WorkDirManager` to accept str via the
  ``workdir`` parameter by `Synchon Mandal`_ (:gh:`283`)
- Avoid warping mask preprocessed with :class:`.fMRIPrepConfoundRemover` and
  used by markers with ``mask="inherit"`` in subject-native template space by
  `Fede Raimondo`_ and `Synchon Mandal`_ (:gh:`284`)
- Pass down input path if input space is "native" for ``ReHoEstimator`` and
  ``ALFFEstimator``, else use respective compute maps by `Fede Raimondo`_ and
  `Synchon Mandal`_ (:gh:`286`)
- Fix :class:`.HTCondorAdapter`'s script generation to use double quotes
  instead of single quotes for HTCondor's ``VARS`` by `Synchon Mandal`_
  (:gh:`312`)
- Fix element access for :class:`.DMCC13Benchmark` DataGrabber by `Synchon
  Mandal`_ (:gh:`314`)
- Add a validation step on the :func:`.run` function to validate the marker
  collection by `Fede Raimondo`_ (:gh:`320`)
- Add the executable flag to the ants docker scripts, fsl docker scripts and
  other running scripts by `Fede Raimondo`_ (:gh:`321`)
- Force ``str`` dtype when parsing elements from file by `Synchon Mandal`_
  (:gh:`322`)


API Changes
^^^^^^^^^^^

- Rename ``Power`` coordinates to ``Power2011`` by `Synchon Mandal`_
  (:gh:`245`)
- Add ``feature_md5`` argument to :func:`.read_transform()` by `Synchon
  Mandal`_ (:gh:`248`)
- Add ``native_t1w`` parameter to :class:`.DataladAOMICID1000`,
  :class:`.DataladAOMICPIOP1`, :class:`.DataladAOMICPIOP2`, enabling fetching
  of T1w data in subject-native space by `Synchon Mandal`_ (:gh:`252`)
- Modify ``preprocessor`` to ``preprocessors`` in :func:`.run` and
  ``preprocessing`` to ``preprocessors`` in :class:`.MarkerCollection` to
  accept multiple preprocessors by `Synchon Mandal`_ (:gh:`263`)
- Add ``space`` parameter to ``register_coordinates``,
  ``register_parcellation`` and ``register_mask`` and return space
  from ``load_coordinates``, ``load_parcellation`` and
  ``load_mask`` by `Synchon Mandal`_ and `Fede Raimondo`_ (:gh:`268`)
- Add ``template_type`` parameter to :func:`.get_template` by `Synchon Mandal`_
  (:gh:`299`)
- Change :meth:`.BasePreprocessor.preprocess` return values to preprocessed
  target data and "helper" data types as a dictionary by `Synchon Mandal`_
  (:gh:`310`)
- Add a positional argument ``using`` for Markers and Preprocessors having
  implementation-based variations, in particular :class:`.ReHoParcels`,
  :class:`.ReHoSpheres`, :class:`.ALFFParcels`, :class:`.ALFFSpheres` and
  ``BOLDWarper`` by `Synchon Mandal`_ (:gh:`311`)
- Change all ``probseg_`` types to ``VBM_`` types by `Fede Raimondo`_
  (:gh:`320`)
- Change the subject and session patterns for :class:`.DataladAOMICID1000`,
  :class:`.DataladAOMICPIOP1`, :class:`.DataladAOMICPIOP2` and
  :class:`.DMCC13Benchmark` so that they are consistent with their own
  ``"participants.tsv"`` file by `Fede Raimondo`_ (:gh:`325`)


Improved Documentation
^^^^^^^^^^^^^^^^^^^^^^

- Add Zenodo badge in ``README`` and improve general documentation by `Synchon
  Mandal`_ (:gh:`247`)
- Rename ``extMDN`` to ``extDMN`` (extended default mode network) and fix
  listing for ``eMDN`` (extended multiple-demand network) by `Synchon Mandal`_
  (:gh:`251`)
- Fixed typo in code example for adding masks from "register_custom_mask" to
  "register_mask" by `Tobias Muganga`_ (:gh:`291`)
- Rename ``Misc`` section to ``Miscellaneous`` in ``docs/whats_new.rst`` by
  `Synchon Mandal`_ (:gh:`300`)
- Improve documentation by adding information about space transformation and
  writing custom Preprocessors by `Synchon Mandal`_ (:gh:`317`)


Enhancements
^^^^^^^^^^^^

- Support element(s) to be specified via text file for ``--element`` option of
  ``junifer run`` by `Synchon Mandal`_ (:gh:`182`)
- Support element-scoped directory and temporary directories for
  :class:`junifer.pipeline.WorkDirManager` by `Synchon Mandal`_ (:gh:`258`)
- Improve element directory cleanup via
  ``junifer.pipeline.WorkDirManager.cleanup_elementdir`` method by `Synchon
  Mandal`_ (:gh:`259`)
- Improve :class:`.BasePreprocessor` for easy subclassing and adapt
  :class:`.fMRIPrepConfoundRemover` to it by `Synchon Mandal`_ (:gh:`260`)
- Add ``space`` information to existing datagrabbers, masks, parcellations and
  coordinates by `Synchon Mandal`_ and `Fede Raimondo`_ (:gh:`268`)
- Add ``mode`` as an aggregation function option in
  :func:`.get_aggfunc_by_name` by `Synchon Mandal`_ (:gh:`287`)
- Adapt ``BOLDWarper`` to use FSL or ANTs depending on warp file
  extension by `Synchon Mandal`_ (:gh:`293`)
- Rewrite ``compute_brain_mask`` to allow variable template fetching via
  templateflow, according to target data by `Synchon Mandal`_ (:gh:`299`)
- Replace ``requests`` with ``httpx`` for fetching parcellations by `Synchon
  Mandal`_ (:gh:`300`)
- Allow ``BOLDWarper`` to warp BOLD data to other MNI spaces by `Synchon
  Mandal`_ (:gh:`302`)
- Add support for local ``junifer queue`` via GNU Parallel by `Synchon Mandal`_
  (:gh:`306`)
- Improve :class:`.PatternDataGrabber` and
  :class:`.PatternDataladDataGrabber`'s ``patterns`` to enable ``space``,
  ``format``, ``mask_item`` and other metadata description handling via YAML by
  `Synchon Mandal`_ (:gh:`308`)
- Improve :class:`.BasePreprocessor` by revamping
  :meth:`.BasePreprocessor.preprocess` and ``BasePreprocessor._fit_transform``
  to handle "helper" data types better and make the pipeline explicit where
  data is being altered by `Synchon Mandal`_ (:gh:`310`)
- Improve external dependency handling for :class:`.PipelineStepMixin`-derived
  objects having implementation-based variations by `Synchon Mandal`_
  (:gh:`311`)


Features
^^^^^^^^

- Introduce complexity markers: :class:`.HurstExponent`,
  :class:`.MultiscaleEntropyAUC`, :class:`.PermEntropy`,
  :class:`.RangeEntropy`, :class:`.RangeEntropyAUC` and :class:`.SampleEntropy`
  by `Amir Omidvarnia`_ (:gh:`145`)
- Add ``junifer reset`` to reset storage and jobs directory by `Synchon
  Mandal`_ (:gh:`240`)
- Add support for ``Power2013`` coordinates by `Synchon Mandal`_ (:gh:`245`)
- Support ``venv`` as environment kind for queueing jobs by `Synchon Mandal`_
  (:gh:`249`)
- Add support for ``AutobiographicalMemory`` coordinates by `Synchon Mandal`_
  (:gh:`250`)
- Add support for subject-native space by `Synchon Mandal`_ and `Fede
  Raimondo`_ (:gh:`252`)
- Introduce :class:`junifer.pipeline.WorkDirManager` singleton class to manage
  working and temporary directories across pipeline by `Synchon Mandal`_
  (:gh:`254`)
- Introduce ``get_parcellation`` to fetch parcellation tailored for the
  data by `Synchon Mandal`_ (:gh:`264`)
- Introduce ``get_coordinates`` to fetch coordinates tailored for the data
  by `Synchon Mandal`_ (:gh:`265`)
- Introduce ``junifer.preprocess.fsl.apply_warper._ApplyWarper`` to wrap FSL's
  ``applywarp`` by `Synchon Mandal`_ (:gh:`266`)
- Introduce ``BOLDWarper`` for warping BOLD data via FSL's ``applywarp``
  by `Synchon Mandal`_ (:gh:`267`)
- Introduce :class:`.DMCC13Benchmark` to access `DMCC13benchmark dataset
  <https://openneuro.org/datasets/ds003452/versions/1.0.1>`_ by `Synchon
  Mandal`_ (:gh:`271`)
- Add ``Brainnetome 246`` parcellation to ``junifer.data`` by `Synchon Mandal`_
  (:gh:`275`)
- Introduce
  ``junifer.preprocess.ants.ants_apply_transforms_warper._AntsApplyTransformsWarper``
  to wrap ANTs' ``antsApplyTransforms`` by `Synchon Mandal`_ (:gh:`293`)
- Introduce :func:`.run_ext_cmd` to take care of the boilerplate code for
  running external commands from FSL, ANTs and others by `Synchon Mandal`_
  (:gh:`295`)
- Introduce :func:`.get_xfm` to fetch transformation files for moving between
  template spaces by `Synchon Mandal`_ (:gh:`297`)
- Introduce :func:`.get_template` to fetch template space image tailored to a
  target data by `Synchon Mandal`_ (:gh:`298`)
- Add support for on-the-fly template space transformation in
  ``get_parcellation`` and ``get_mask`` to allow parcellation and
  mask in different template spaces to work with a ``DataGrabber``'s data in a
  specified template space. (:gh:`299`)
- Introduce :class:`.SpaceWarper` for warping ``T1w``, ``BOLD``, ``VBM_GM``,
  ``VBM_WM``, ``fALFF``, ``GCOR`` and ``LCOR`` data to other spaces by `Synchon
  Mandal`_ (:gh:`301`)
- Introduce :class:`.QueueContextAdapter` as an abstract base class for job
  queueing and :class:`.HTCondorAdapter` as its implementation for HTCondor by
  `Synchon Mandal`_ (:gh:`309`)


Miscellaneous
^^^^^^^^^^^^^

- Update dependencies requirements by `Fede Raimondo`_ (:gh:`253`)
- Pin ``ruff`` to ``0.1.0`` as the lowest version and update ``pre-commit``
  config by `Synchon Mandal`_ (:gh:`261`)
- Add support for accessing FSL via Docker wrapper along with ``flirt``,
  ``applywarp``  and ``std2imgcoord`` commands by `Synchon Mandal`_ (:gh:`262`)
- Improve documentation, packaging and code style by `Synchon Mandal`_
  (:gh:`269`)
- Add support for Python 3.12 and make Python 3.11 the base for code coverage
  and CI checks by `Synchon Mandal`_ (:gh:`270`)
- Add support for accessing ANTs via Docker wrapper along with
  ``antsApplyTransforms`` and ``antsApplyTransformsToPoints`` by `Synchon
  Mandal`_ (:gh:`277`)
- Make the external tool wrappers output to stderr instead of stdout by
  `Synchon Mandal`_ (:gh:`279`)
- Add support for accessing FSL ``img2imgcoord`` via Docker wrapper command by
  `Synchon Mandal`_ (:gh:`281`)
- Make ``BOLDWarper`` tool-agnostic by moving it from
  ``junifer.preprocess.fsl`` to :mod:`junifer.preprocess` by `Synchon Mandal`_
  (:gh:`288`)
- Add support for accessing ANTs' ``ResampleImage`` via Docker wrapper by
  `Synchon Mandal`_ (:gh:`293`)
- Update ``pyproject.toml`` and add FAIR shield in ``README.md`` by `Synchon
  Mandal`_ (:gh:`294`)
- Update dependency listing in ``pyproject.toml``, add
  ``.github/dependabot.yml`` to auto-update GitHub Actions, add ``ANTs`` and
  ``FSL`` installation in CI and improve general code style by `Synchon
  Mandal`_ (:gh:`300`)


Deprecations and Removals
^^^^^^^^^^^^^^^^^^^^^^^^^

- Deprecate ``BOLDWarper`` and mark for removal in v0.0.4 by `Synchon
  Mandal`_ (:gh:`301`)


Junifer 0.0.3 (2023-07-21)
--------------------------

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


Miscellaneous
^^^^^^^^^^^^^

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
- Fix a bug in which ``get_mask`` fails for ``FunctionalConnectivityBase``
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
- Expose a ``merge_parcellations`` function to merge a list of
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

- Implement ``register_coordinates``, ``list_coordinates`` and
  ``load_coordinates`` by `Fede Raimondo`_ (:gh:`11`)

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


Miscellaneous
^^^^^^^^^^^^^

- Create the repository based on the mockup by `Fede Raimondo`_
