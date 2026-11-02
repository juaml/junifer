.. include:: links.inc
.. include:: changes/contributors.inc

.. _whats_new:

What's new
==========

.. towncrier-draft-entries:: |release|

.. towncrier release notes start

Junifer 0.0.8 (2026-10-19)
--------------------------

Bugfixes
^^^^^^^^

- Allow :class:`.SpaceWarper` to convert data from native to template space
  when ``using="auto"`` by `Fede Raimondo`_ and `Synchon Mandal`_ (:gh:`482`)
- Fix pattern indexing logic for :meth:`.PatternDataGrabber.get_elements` by
  `Synchon Mandal`_ (:gh:`492`)
- Fix the data collected by :class:`.HDF5FeatureStorage` being stored as
  ``float32`` when ``force_float32=False`` and the ``h5py`` deprecation warning
  when collecting by `Fede Raimondo`_ (:gh:`504`)
- Fix :meth:`.PatternDataGrabber.get_elements` returning elements that miss
  some of the data types when several types use all the replacements by `Fede
  Raimondo`_ (:gh:`511`)
- Fix ReHo computation with ``using="junifer"`` including neighbours outside
  the mask, checking the wrong centre voxel for ``nneigh=125``, setting voxels
  outside the mask to 1 instead of 0, skipping voxels at the edges of the
  volume and setting fully tied neighbourhoods to 1 instead of 0, so that it
  matches AFNI's ``3dReHo`` by `Fede Raimondo`_ (:gh:`514`)
- Use the ``masks`` parameter of :class:`.ReHoMaps`, :class:`.ReHoParcels` and
  :class:`.ReHoSpheres` to restrict the ReHo computation for both
  ``using="junifer"`` and ``using="afni"``, instead of an MNI152 brain mask
  resampled to the input data (wrong for native space) only for
  ``using="junifer"``. Without ``masks``, both use the voxels with non-zero
  time series, so that both implementations give the same results by `Fede
  Raimondo`_ (:gh:`514`)
- Fix :class:`.JuniferConnectivityMeasure` not checking its input as
  ``nilearn``'s ``ConnectivityMeasure`` (e.g. tangent with a single subject)
  and not listing all the valid kinds in the error message by `Fede Raimondo`_
  (:gh:`516`)
- Fix ``dtype`` being ignored in :class:`.JuniferNiftiSpheresMasker` by `Fede
  Raimondo`_ (:gh:`516`)
- Fix the labels of the ``Brainnetome`` parcellations, which repeated each name
  for both hemispheres, by reading them from junifer-data (e.g. ``SFG_L_7_1``
  and ``SFG_R_7_1`` instead of ``SFG_L(R)_7_1`` twice), which changes their
  feature names by `Fede Raimondo`_ (:gh:`520`)
- Fix the labels of the ``Julich-Brain`` parcellations, which were the label
  values instead of the region names, which changes their feature names by
  `Fede Raimondo`_ (:gh:`520`)
- Fix the labels of the ``Yan`` parcellations, which were ``NaN`` or numbers
  instead of the region names, which changes their feature names by `Fede
  Raimondo`_ (:gh:`520`)
- Fix the labels of the ``Shen_2013`` parcellations, which were assigned to the
  wrong parcels, and add a ``-{i}`` suffix to the repeated ``No_BA_region``
  labels, which changes their feature names by `Fede Raimondo`_ (:gh:`520`)
- Fix the labels of parcellations with regions lost when resampling or warping
  to the target image, which shifted the labels of the following regions; the
  lost regions are kept (without data) and a warning lists them. The parcel
  markers are computed on the regions with data and give ``NaN`` for the lost
  ones (and :class:`.RSSETSMarker` only uses the edges with data) by `Fede
  Raimondo`_ (:gh:`520`, :gh:`521`)
- Fix :class:`.TemporalSNRParcels`, :class:`.TemporalSNRSpheres` and
  :class:`.TemporalSNRMaps` replacing the BOLD data with the tSNR map, so the
  markers computed after them in a pipeline used the tSNR map instead of the
  BOLD data by `Fede Raimondo`_ (:gh:`522`)
- Fix a relative ``datadir`` of the DataGrabber in the YAML being relative to
  the current directory (e.g., the job directory when queueing) instead of the
  YAML file by `Fede Raimondo`_ (:gh:`524`)
- Fix partial element selectors (e.g., only the subject) always being reported
  as invalid by :func:`.run`, after computing their elements by `Fede
  Raimondo`_ (:gh:`524`)
- Fix the same features being stored more than once: for each value of the
  element keys that the data does not depend on (e.g., the VBM features of a
  subject once per task), when running an element again, and when collecting
  again (:class:`.SQLiteFeatureStorage` also collected its own output file) by
  `Fede Raimondo`_ (:gh:`525`)
- Fix the metadata of the preprocessors being replaced by the one of the last
  preprocessor by `Fede Raimondo`_ (:gh:`525`)
- Fix the complexity markers (e.g., :class:`.HurstExponent`) not being
  available in the YAML file with ``with: junifer.markers.complexity`` by `Fede
  Raimondo`_ (:gh:`529`)
- Fix the Maps markers (e.g., :class:`.MapsAggregation`) not being available in
  the YAML file without importing their modules by `Fede Raimondo`_ (:gh:`529`)
- Fix ``junifer run`` and ``junifer list-elements`` ignoring the ``elements``
  of the YAML file when ``--element`` is not given by `Fede Raimondo`_
  (:gh:`529`)
- Fix the AFNI smoothing of :class:`.Smoothing` leaving ``3dFWHMx.1D`` and
  ``3dFWHMx.1D.png`` in the current directory by `Fede Raimondo`_ (:gh:`529`)


API Changes
^^^^^^^^^^^

- Rename the methods of :class:`.QueueContextAdapter` to ``pre_run_cmds``,
  ``run_cmds``, ``pre_collect_cmds`` and ``collect_cmds``; custom queue context
  adapters must rename theirs by `Synchon Mandal`_ (:gh:`503`)
- Sanitise the VOI names of built-in coordinates by replacing spaces with ``_``
  and adding a ``-{i}`` suffix to duplicated names, which changes the feature
  names of e.g. ``Dosenbach`` and ``Seitzman2018`` by `Fede Raimondo`_
  (:gh:`511`)
- Replace boolean values of ``standardize`` in :class:`.TemporalFilter`,
  :class:`.fMRIPrepConfoundRemover` and :class:`.JuniferConnectivityMeasure`
  with ``"zscore_sample"`` (default), ``"psc"`` or ``None``, following
  ``nilearn``; booleans raise an error. ``"zscore_sample"`` uses the sample
  standard deviation, while ``True`` used the population one, so standardized
  values change slightly by `Fede Raimondo`_ (:gh:`516`)
- Use the BIDS version of the SPM auditory dataset in
  :class:`.SPMAuditoryTestingDataGrabber`, which has 84 timepoints instead of
  96 by `Fede Raimondo`_ (:gh:`516`)
- Use :class:`enum.StrEnum` for the enumerations, so ``str()`` and formatting
  of their members give their value (e.g. ``"mean"``) instead of
  ``"AggFunc.Mean"`` by `Fede Raimondo`_ (:gh:`520`)
- Use only the replacements of the data types to grab as element keys in
  :class:`.PatternDataGrabber` (e.g., only ``subject`` with VBM data), so the
  data that does not depend on, e.g., the task is not processed once for each
  task by `Fede Raimondo`_ (:gh:`524`)
- Require the element selectors to have the same number of values, and each
  data type to be grabbed by only one of the DataGrabbers of
  :class:`.MultipleDataGrabber` by `Fede Raimondo`_ (:gh:`524`)
- Find the elements of :class:`.DataladAOMICPIOP1`,
  :class:`.DataladAOMICPIOP2`, :class:`.HCP1200` and :class:`.DMCC13Benchmark`
  in the dataset, so only the elements with data are listed
  (:class:`.DataladHCP1200` lists all the subjects, as they are datalad
  sub-datasets), and return absolute paths in :class:`.PatternDataGrabber` by
  `Fede Raimondo`_ (:gh:`524`, :gh:`528`)
- Add the version of ``junifer`` to the MD5 of the features, as for the
  dependencies of the markers and steps, for reproducibility: features computed
  with different versions of ``junifer`` are different features, so the
  differences between features (e.g., between datasets) can only come from the
  data. Running again with a new version stores the features again, with the
  same name, next to the ones computed with the previous version by `Fede
  Raimondo`_ (:gh:`525`)
- Raise an error in the ``collect`` method of :class:`.HDF5FeatureStorage` and
  :class:`.SQLiteFeatureStorage` if a file to collect has more than one
  element, as ``collect`` only compacts the files of single elements by `Fede
  Raimondo`_ (:gh:`525`)
- Use ``upsert="ignore"`` by default in :class:`.SQLiteFeatureStorage`, so the
  elements already stored are not stored again by `Fede Raimondo`_ (:gh:`525`)
- Add the ``processed_element`` argument to the ``store_*`` methods of
  :class:`.BaseFeatureStorage`, the element being processed, so the concrete
  storages can name the file of each element; custom storages must accept it by
  `Fede Raimondo`_ (:gh:`525`)
- Store the metadata of the preprocessors as a list, in order, in
  ``meta["preprocess"]`` by `Fede Raimondo`_ (:gh:`525`)
- Raise an error when installing the dataset of a
  :class:`.PatternDataladDataGrabber` if a pattern searches the files of a
  sub-dataset, which are only there once the sub-dataset is installed, instead
  of not finding the elements by `Fede Raimondo`_ (:gh:`528`)
- Use single precision in ``antsApplyTransforms`` (``--float 1``), halving its
  memory and giving float32 instead of float64 data, with differences below
  0.002% of the data range by `Fede Raimondo`_ (:gh:`530`)


Improved Documentation
^^^^^^^^^^^^^^^^^^^^^^

- Add documentation on adding confounds format by `Synchon Mandal`_ (:gh:`364`)
- Build the documentation of all the released versions with
  ``sphinx-polyversion`` instead of ``sphinx-multiversion``, using a ``uv``
  environment per version, and add a version selector and a banner showing
  whether the latest, an old or the development version is being viewed by
  `Fede Raimondo`_ (:gh:`513`)
- Use the UCLA CNP VBM testing data and the Tian parcellations in the examples
  and the codeless documentation, so no example needs warping by `Fede
  Raimondo`_ (:gh:`515`)
- Fix the docs build and the julearn example, whose scores were ``NaN`` with
  ``scikit-learn`` 1.8 by `Fede Raimondo`_ (:gh:`520`)
- Document the elements of the DataGrabbers, combining datasets with
  :class:`.MultipleDataGrabber`, complete and partial elements, and restricting
  the values of the replacements by `Fede Raimondo`_ (:gh:`524`)
- Add the "Implementation details" page with the elements, the fields of the
  metadata and the storage, and document the data types with different element
  keys when extending DataGrabbers by `Fede Raimondo`_ (:gh:`525`)
- Document that the DataGrabbers with files in datalad sub-datasets must list
  their elements and build the paths without searching the files by `Fede
  Raimondo`_ (:gh:`528`)
- Fix the ``collect_task`` option of the HTCondor queue being documented as
  ``collect``, document the ``elements`` key of the YAML file and the ``with``
  needed by the markers, and use the full width of the page for the content by
  `Fede Raimondo`_ (:gh:`529`)


Enhancements
^^^^^^^^^^^^

- Improve logging consistency of components by `Synchon Mandal`_ (:gh:`239`)
- Adopt Pydantic for user-facing core objects to perform automatic validation
  using typing annotations by `Synchon Mandal`_ (:gh:`364`, :gh:`502`,
  :gh:`510`)
- Move ``parse_yaml`` from ``junifer.cli`` to ``junifer.api`` by `Synchon
  Mandal`_ (:gh:`499`)
- Set up the working directory first in all the commands of the CLI (from
  ``workdir`` in the YAML) and in :func:`.run`, :func:`.collect`,
  :func:`.queue`, :func:`.reset` and :func:`.list_elements`, adding the
  ``workdir`` parameter to :func:`.collect` and :func:`.list_elements`, and
  create the working directory if it does not exist by `Synchon Mandal`_ and
  `Fede Raimondo`_ (:gh:`509`)
- Drop the files fetched by :class:`.DataladDataGrabber` in a single call and
  without checking their availability on the remote, making cleanup much faster
  by `Fede Raimondo`_ (:gh:`511`)
- Cache the available templateflow templates to speed up :func:`.get_template`
  by `Fede Raimondo`_ (:gh:`511`)
- Vectorize ReHo computation with ``using="junifer"``, making it about 5 times
  faster by `Fede Raimondo`_ (:gh:`514`)
- Add :class:`.UCLACNPVBMTestingDataGrabber` with grey matter probability maps
  from OpenNeuro ds000030 in MNI152NLin2009cAsym, add ``n_subjects`` to
  :class:`.PartlyCloudyTestingDataGrabber` and use the native 3mm resolution by
  default in :class:`.ADHDTestingDataGrabber` by `Fede Raimondo`_ (:gh:`515`)
- Speed up :class:`.ParcelAggregation` by not passing a target affine to the
  masker, which made ``nilearn`` crop and copy the input image even when the
  parcellation was already on its grid by `Fede Raimondo`_ (:gh:`515`)
- Raise an error if a marker changes its input data (which is shared with the
  other markers of a pipeline), checking the values and their contents (arrays,
  data frames and images) by `Fede Raimondo`_ (:gh:`522`, :gh:`531`)
- Run complete elements (with a value for each element key, e.g., in each
  queued job) without searching the dataset for its elements by `Fede
  Raimondo`_ (:gh:`524`)
- Store the features for the element with only the keys that the data type
  depends on (e.g., only ``subject`` for VBM data, when the elements also have
  ``task``), and skip the elements already stored by `Fede Raimondo`_
  (:gh:`525`)
- Write the intermediate images (e.g., the warped, smoothed or filtered data)
  uncompressed in the temporary directory of the element, as they are read
  right away and deleted after the element is processed, so there is no need to
  spend time compressing and decompressing them, and run the FSL commands with
  ``FSLOUTPUTTYPE=NIFTI`` to write them uncompressed by `Fede Raimondo`_
  (:gh:`530`)
- Warp the volumes of 4D data in chunks of ``preprocessing.warping.chunksize``
  volumes (default 100) in :class:`.SpaceWarper`, as the memory used by ANTs
  and FSL grows with the number of volumes (e.g., about 53 GB to warp 1200
  volumes to native space with ANTs) by `Fede Raimondo`_ (:gh:`530`)
- Keep the data of :class:`.fMRIPrepConfoundRemover`, :class:`.TemporalFilter`,
  :class:`.TemporalSlicer` and :class:`.Smoothing` (with nilearn) in the saved
  file (memory-mapped) instead of in memory, as for the other preprocessors,
  releasing its memory during the next steps of the pipeline (e.g., 5 GB for
  1200 volumes while running AFNI) by `Fede Raimondo`_ (:gh:`533`)
- Restrict the ALFF and fALFF computation of :class:`.ALFFParcels`,
  :class:`.ALFFSpheres` and :class:`.ALFFMaps` to the voxels in their ``masks``
  (with ``-mask`` for AFNI's ``3dRSFC``), as for ReHo, reducing the memory and
  time (e.g., from 14.5 GB to 9.4 GB and from 7 to 1 minutes for 1200 volumes
  with AFNI), and do not write the bandpassed time series with ``3dRSFC``
  (``-no_rs_out``), as only the parameters are used by `Fede Raimondo`_
  (:gh:`533`)
- Read only the signals of the voxels of the spheres, in chunks of
  ``markers.spheres.chunksize`` volumes (default 100), in
  :class:`.JuniferNiftiSpheresMasker`, instead of loading the whole 4D data,
  reducing the memory used by the sphere-based markers (e.g.,
  :class:`.SphereAggregation` and :class:`.FunctionalConnectivitySpheres`) on
  BOLD data, with the same results, and do not change the input data when it
  has NaN values by `Fede Raimondo`_ (:gh:`534`)


Features
^^^^^^^^

- Enable confounds format to be added by introducing
  :func:`.register_confounds_format` by `Synchon Mandal`_ (:gh:`364`)
- Add :class:`.ADHDTestingDataGrabber` and ``n_timepoints`` for
  :class:`.SPMAuditoryTestingDataGrabber` and
  :class:`.PartlyCloudyTestingDataGrabber` by `Fede Raimondo`_ (:gh:`511`)
- Allow restricting the values of the replacements to grab in
  :class:`.PatternDataGrabber`, with ``replacements`` as a dictionary or with
  fields linked with ``_REPLACEMENT_FIELDS`` (e.g., ``tasks`` in the built-in
  DataGrabbers), and using the ``*`` and ``?`` wildcards in the patterns to
  find the elements by `Fede Raimondo`_ (:gh:`524`)
- Allow :class:`.MultipleDataGrabber` to combine DataGrabbers with different
  element keys, joining their elements on the common keys, and to replace
  nested data types (e.g., the confounds of ``BOLD``) with a DataGrabber that
  only grabs them by `Fede Raimondo`_ (:gh:`524`)
- Add :meth:`.BaseDataGrabber.get_type_element_keys` to get the element keys
  that the data of a data type depends on by `Fede Raimondo`_ (:gh:`525`)


Miscellaneous
^^^^^^^^^^^^^

- Drop Python 3.9 and add Python 3.14 support, upgrade codebase to follow
  modern syntax, bump dependencies and add ``uv`` support by `Synchon Mandal`_
  (:gh:`474`)
- Use original ``h5io`` instead of junifer's fork, keeping support for reading
  the features collected with the fork by `Fede Raimondo`_ (:gh:`504`)
- Speed up the test suite, split CI into tests requiring external resources
  (self-hosted) and the rest (GitHub-hosted), build the docs on the self-hosted
  runner, make the examples faster and use :class:`.HDF5FeatureStorage`, and
  bump ``julearn`` to 0.3.5 by `Fede Raimondo`_ (:gh:`511`)
- Publish the junifer Docker image (``ghcr.io/juaml/junifer``) on every release
  with the matching junifer version, base it on Ubuntu 24.04 with native ANTs,
  AFNI and FSL installations and the junifer-data version used by junifer, and
  stop building the docs and CI images on GitHub Actions by `Fede Raimondo`_
  (:gh:`511`)
- Add the ``sphinx`` optional dependencies with the tools to build the
  documentation, make ``docs`` include everything needed to build it, and skip
  building the PR preview of the documentation when the PR is closed by `Fede
  Raimondo`_ (:gh:`513`)
- Speed up the test suite by freezing the objects alive after collection, so
  the full garbage collections forced by ``nilearn`` are much faster by `Fede
  Raimondo`_ (:gh:`515`)
- Speed up the external tests by using fewer subjects, the UCLA CNP VBM testing
  data and ``junifer-data`` 1.5.0, and bake the derived testing data and
  templateflow templates into the CI image by `Fede Raimondo`_ (:gh:`515`)
- Support ``nilearn`` 0.14 (required) by `Fede Raimondo`_ (:gh:`516`)
- Update the dependencies to their latest versions supporting Python 3.11 (e.g.
  ``numpy`` 2.4, ``pandas`` 3.0, ``scipy`` 1.17, ``click`` 8.5, ``datalad``
  1.7, ``templateflow`` 25), fixing the open security alerts, require
  ``junifer-data`` >= 1.6.1 and use junifer-data v8 by `Fede Raimondo`_
  (:gh:`520`)
- Pin ``neurokit2`` to 0.2.12, as 0.2.13 requires ``pandas`` < 3, and provide
  ``np.trapz`` (removed in ``numpy`` 2.4) while :class:`.MultiscaleEntropyAUC`
  calls ``neurokit2`` by `Fede Raimondo`_ (:gh:`520`)
- Read dependency versions from the distribution metadata instead of the
  deprecated ``__version__`` attributes, pass ``standardize=None`` to
  ``nilearn`` maskers to avoid deprecation warnings and skip the tests of
  vendored packages with a ``pytest_ignore_collect`` hook, as ``datalad``'s
  pytest plugin prevents ``collect_ignore`` from being applied by `Fede
  Raimondo`_ (:gh:`520`)
- Cap ``sphinx`` below 9, as ``enum-tools`` does not support it yet by `Fede
  Raimondo`_ (:gh:`520`)
- Use :class:`.HDF5FeatureStorage` instead of :class:`.SQLiteFeatureStorage` in
  the tests and documentation, as the latter is only kept for compatibility,
  and fix the component registry test leaving components de-registered by `Fede
  Raimondo`_ (:gh:`523`)


Deprecations and Removals
^^^^^^^^^^^^^^^^^^^^^^^^^

- Drop support for Python 3.10 by `Fede Raimondo`_ (:gh:`520`)


Junifer 0.0.7 (2026-03-04)
--------------------------

Bugfixes
^^^^^^^^

- Allow ``timeseries_2d`` storage for :class:`.HDF5FeatureStorage` by `Fede
  Raimondo`_ (:gh:`444`)
- Fix FSL presence checking status code by `Fede Raimondo`_ (:gh:`454`)
- Bypass warper check for callable masks on native data by `Synchon Mandal`_
  (:gh:`481`)
- Fix mask specification check involving dicts in
  :class:`junifer.data.MaskRegistry` when working in native space by `Synchon
  Mandal`_ (:gh:`487`)


API Changes
^^^^^^^^^^^

- ``fname``, ``overwrite`` and ``output_format`` have been removed from
  :func:`.configure_logging` by `Synchon Mandal`_ (:gh:`231`)
- ``ParcellationRegistry.get`` now returns labels as dictionary mapping from
  values to labels instead of a list of labels by `Synchon Mandal`_ (:gh:`257`)
- :func:`.read_transform` has a new parameter ``nan_policy`` to handle NaN
  values when transforming feature data by `Fede Raimondo`_ (:gh:`429`)
- :func:`.get_data`, :func:`.load_data`, :func:`.list_data`,
  :func:`.register_data` and :func:`.deregister_data` now support ``"maps"`` as
  a valid argument for ``kind`` by `Synchon Mandal`_ (:gh:`458`)


Improved Documentation
^^^^^^^^^^^^^^^^^^^^^^

- Add documentation on extending data registries by `Synchon Mandal`_
  (:gh:`450`)
- Add documentation on adding data types by `Synchon Mandal`_ (:gh:`451`)
- Add documentation on :class:`.ConfigManager`, dumping data object and
  extending data dump assets by `Synchon Mandal`_ (:gh:`452`)


Enhancements
^^^^^^^^^^^^

- Allow parcellation registration with non-continuous ranges as values by
  `Synchon Mandal`_ (:gh:`257`)
- Add support for Chatterjee's xi correlation in
  :class:`.JuniferConnectivityMeasure` by `Synchon Mandal`_ (:gh:`333`)
- Implement a NaN policy for :func:`.read_transform` by `Fede Raimondo`_
  (:gh:`429`)
- Add FreeSurfer 7.4.1 aseg parcellation to :class:`.ParcellationRegistry` by
  `Synchon Mandal`_ (:gh:`470`)
- Simplify ``Storage`` interface and implementations by `Synchon Mandal`_
  (:gh:`472`)
- Simplify ``Preprocess`` interface and implementations by `Synchon Mandal`_
  (:gh:`473`)
- Simplify :class:`.PipelineStepMixin` interface by `Synchon Mandal`_
  (:gh:`476`)
- Improve ``Marker`` interface and implementations by `Synchon Mandal`_
  (:gh:`477`)
- Add Glasser and Julich-Brain parcellations to :class:`.ParcellationRegistry`
  by `Synchon Mandal`_ (:gh:`486`)


Features
^^^^^^^^

- Introduce :class:`.TemporalFilter` preprocessor for temporally filtering BOLD
  data by `Fede Raimondo`_ (:gh:`432`)
- Introduce :class:`.TemporalSlicer` preprocessor for temporally slicing BOLD
  data by `Synchon Mandal`_ (:gh:`443`)
- Enable data registries to be extended by exposing
  :class:`.BasePipelineDataRegistry` and introducing
  :func:`.register_data_registry` decorator by `Synchon Mandal`_ (:gh:`450`)
- Enable data types to be added by introducing :func:`.register_data_type` by
  `Synchon Mandal`_ (:gh:`451`)
- Allow pipeline data object to be dumped by introducing
  :class:`.DataObjectDumper` and available dumping / loading assets to be
  extended by introducing :func:`.register_data_dump_asset` decorator by
  `Synchon Mandal`_ (:gh:`452`)
- Introduce :class:`.MapsRegistry` to centralise probabilistic atlas (maps)
  data management by `Synchon Mandal`_ (:gh:`458`)
- Introduce :class:`.MapsAggregation`, :class:`.FunctionalConnectivityMaps`,
  :class:`.EdgeCentricFCMaps`, :class:`.ReHoMaps`, :class:`.ALFFMaps` and
  :class:`.TemporalSNRMaps` by `Synchon Mandal`_ (:gh:`460`)
- Enable :class:`.SpaceWarper` to warp data from native space to template
  spaces via both FSL and ANTs by `Synchon Mandal`_ (:gh:`462`)


Miscellaneous
^^^^^^^^^^^^^

- Adopt ``structlog`` for logging infrastructure by `Synchon Mandal`_
  (:gh:`231`)
- Regular repository maintenance by updating ``.pre-commit-config.yaml``,
  replacing ``black`` with ``ruff-format`` and updating tool configs by
  `Synchon Mandal`_ (:gh:`441`)
- Bump ``junifer-data`` to ``v3`` for Docker images by `Synchon Mandal`_
  (:gh:`456`)
- Bump ``junifer-data`` to ``v3`` by `Synchon Mandal`_ (:gh:`457`)
- Constrain ``templateflow`` version to ``>=23.0.0,<25.0.0`` by `Synchon
  Mandal`_ (:gh:`458`)
- Add a new GitHub Action to mark stale issues by `Synchon Mandal`_ (:gh:`464`)
- Bump ``junifer-data`` to ``v4`` for Docker images by `Synchon Mandal`_
  (:gh:`465`)
- Bump ``junifer-data`` to ``v4`` by `Synchon Mandal`_ (:gh:`466`)
- Disable FSL installation for ``junifer-ci`` Docker image build with
  ``junifer-data`` v4 by `Synchon Mandal`_ (:gh:`467`)
- Pin ``junifer-ci`` Docker image to ``python:3.12-slim-bookworm`` and
  re-enable FSL installation by `Synchon Mandal`_ (:gh:`468`)
- Bump ``junifer-data`` to ``v5`` by `Synchon Mandal`_ (:gh:`470`)
- Bump ``junifer-data`` to ``v6`` for Docker images by `Synchon Mandal`_
  (:gh:`483`)
- Bump ``junifer-data`` to ``v7`` for Docker images by `Synchon Mandal`_
  (:gh:`485`)
- Bump ``junifer-data`` to ``v7`` by `Synchon Mandal`_ (:gh:`486`)
- Add Dockerfile and a corresponding action for building and publishing the
  image by `Fede Raimondo`_ and `Synchon Mandal`_ (:gh:`489`)


Junifer 0.0.6 (2025-03-24)
--------------------------

Bugfixes
^^^^^^^^

- Fix ``mri_binarize`` command preparation for structures with multiple indices
  in :class:`.BrainPrint` by `Fede Raimondo`_ (:gh:`356`)
- Enable ``spike`` mapping from ``adhoc`` to ``fmriprep`` for
  :class:`.fMRIPrepConfoundRemover` by `Leonard Sasse`_ and `Synchon Mandal`_
  (:gh:`360`)
- Correct listing for :class:`.fMRIPrepConfoundRemover` in
  ``junifer.pipeline.registry`` by `Synchon Mandal`_ (:gh:`369`)
- Add ``'emomatching'`` task to :class:`.DataladAOMICPIOP2` by `Leonard Sasse`_
  (:gh:`370`)
- Use correct return code for ANTs commands while checking presence of external
  commands by `Synchon Mandal`_ (:gh:`385`)
- Use the :class:`junifer.pipeline.WorkDirManager` for temporary directories in
  the :class:`.DataladDataGrabber` by `Fede Raimondo`_ (:gh:`386`)
- Fix coordinates space transformation using ANTs by `Synchon Mandal`_
  (:gh:`388`)
- Fix metadata update for :class:`.MultipleDataGrabber` and adjust
  :meth:`.PatternDataGrabber.get_elements` to check ``list``-like data type
  values by `Fede Raimondo`_ and `Synchon Mandal`_ (:gh:`398`)
- Use correct file output suffices for AFNI-based markers by `Synchon Mandal`_
  (:gh:`409`)
- Fix ``t_r`` tampering by :func:`nilearn.image.clean_img` in
  :class:`.fMRIPrepConfoundRemover` by `Fede Raimondo`_ and `Synchon Mandal`_
  (:gh:`420`)
- Fix coordinates fetching for Power and Dosenbach from ``junifer-data`` by
  `Synchon Mandal`_ (:gh:`431`)
- Remove ``Power2013`` from :class:`.CoordinatesRegistry` by `Synchon Mandal`_
  (:gh:`436`)
- Correct dispatch methods for ``*_data()`` functions by `Synchon Mandal`_
  (:gh:`439`)


API Changes
^^^^^^^^^^^

- ``get_parcellation``, ``load_parcellation``, ``list_parcellation``,
  ``register_parcellation`` , ``get_coordinates``, ``load_coordinates``,
  ``list_coordinates``, ``register_coordinates``, ``get_mask``, ``load_mask``,
  ``list_mask``, ``register_mask`` have been removed in favour of
  :func:`.get_data`, :func:`.load_data`, :func:`.list_data`,
  :func:`.register_data` and :func:`.deregister_data` by `Synchon Mandal`_
  (:gh:`387`)
- :class:`.SpaceWarper`'s ``using`` now supports ``"auto"`` allowing auto tool
  selection based on DataGrabber specification by `Synchon Mandal`_ (:gh:`390`)
- Allow ``workdir`` to also be a mapping in YAML, with ``path`` and ``cleanup``
  keys by `Synchon Mandal`_ (:gh:`402`)
- Add ``source`` parameter and resurrect ``extra_input`` parameter for
  ``compute_brain_mask`` by `Fede Raimondo`_ (:gh:`404`)
- ``native_t1w`` parameter has been replaced with ``space`` to allow
  :class:`.DataladAOMICID1000`, :class:`.DataladAOMICPIOP1` and
  :class:`.DataladAOMICPIOP2` to fetch data in all available spaces by `Fede
  Raimondo`_ (:gh:`405`)
- :meth:`.ParcellationRegistry.load` now has a new parameter ``target_space``
  to provide parcellation in highest possible resolution if it does not match
  the space of the parcellation by `Fede Raimondo`_ and `Synchon Mandal`_
  (:gh:`411`)
- Introduce new CLI parameter ``--verbose-datalad`` to control ``datalad``'s
  logging handler by `Fede Raimondo`_ (:gh:`412`)
- ``target_data`` parameter of :func:`.get_template` has been replaced with
  ``target_img`` by `Fede Raimondo`_ (:gh:`413`)
- Add ``template_space`` parameter for ``compute_brain_mask`` and
  ``resolution`` parameter for :func:`.get_template` by `Fede Raimondo`_
  (:gh:`415`)
- Add ``scrub``, ``fd_threshold`` and ``std_vars_threshold`` parameters to
  :class:`.fMRIPrepConfoundRemover` and allow ``"scrubbing"`` key of type bool
  for ``strategy`` by `Synchon Mandal`_ (:gh:`421`)


Improved Documentation
^^^^^^^^^^^^^^^^^^^^^^

- Improve Sphinx configuration and extensions by `Synchon Mandal`_ (:gh:`358`)
- Add documentation on analysing extracted features by `Synchon Mandal`_
  (:gh:`359`)
- Add documentation on how to make a ``junifer`` plugin by `Synchon Mandal`_
  (:gh:`366`)


Enhancements
^^^^^^^^^^^^

- Raise error when partial or complete element selectors are invalid when
  running the pipeline by `Synchon Mandal`_ (:gh:`319`)
- Add support for Spearman's correlation in
  :class:`.JuniferConnectivityMeasure` by `Leonard Sasse`_ (:gh:`335`)
- Set proper stdout encoding for :func:`.run_ext_cmd` to ease human readability
  by `Fede Raimondo`_ (:gh:`357`)
- Adapt usage of ``junifer-data`` client API to fetch parcellations, masks,
  coordinates and xfms by `Synchon Mandal`_ (:gh:`363`)
- Allow for external python files in the ``with`` section of the yaml to import
  other files by `Fede Raimondo`_ (:gh:`367`)
- Use ``datalad``-enabled repository for template space transform files in
  :func:`.get_xfm` by `Synchon Mandal`_ (:gh:`368`)
- Add a ``cleanup`` parameter to the :class:`junifer.pipeline.WorkDirManager`,
  which allows to disable cleaning up temporary directories by `Fede Raimondo`_
  (:gh:`389`)
- Update ``Warp`` data type to be a list of dictionaries and adapt to allow
  multiple transforms to be specified by `Synchon Mandal`_ (:gh:`390`)
- Refactor the masking logic in the pipeline to account for and optimise space
  transformations and merges by `Synchon Mandal`_ and `Fede Raimondo`_
  (:gh:`395`)
- Allow ``workdir`` mapping form in YAML for easy debugging of single element
  ``run`` by disabling cleanup of :class:`junifer.pipeline.WorkDirManager` by
  `Synchon Mandal`_ (:gh:`402`)
- Use :func:`junifer.utils.ConfigManager` to skip time-consuming dataset ID and
  dirty checks for :class:`.DataladDataGrabber` by `Fede Raimondo`_ (:gh:`403`)
- Enable ``compute_brain_mask`` to use subject-specific probseg files by `Fede
  Raimondo`_ (:gh:`404`)
- Update :class:`.DataladAOMICID1000`, :class:`.DataladAOMICPIOP1` and
  :class:`.DataladAOMICPIOP2` to fetch data in all available spaces by `Fede
  Raimondo`_ (:gh:`405`)
- Update Preprocessors to sync data their paths so that the results are
  idempotent by `Synchon Mandal`_ (:gh:`408`)
- Ease asset storage for AFNI-based markers by `Synchon Mandal`_ (:gh:`409`)
- Refactor the parcellation logic in the pipeline to account for and optimise
  space transformations and merges by `Synchon Mandal`_ and `Fede Raimondo`_
  (:gh:`411`)
- Adapt mask warpers to use correct interpolation method based on the type of
  data by `Synchon Mandal`_ and `Fede Raimondo`_ (:gh:`416`)
- Adapt usage of ``junifer-data`` DataLad dataset to fetch parcellations,
  masks, coordinates and xfms by `Synchon Mandal`_ (:gh:`418`)
- Add scrubbing support to :class:`.fMRIPrepConfoundRemover` by `Synchon
  Mandal`_ (:gh:`421`)
- Add commit SHA check for ``junifer_data`` to simplify data fetching by `Fede
  Raimondo`_ (:gh:`434`)


Features
^^^^^^^^

- Introduce :func:`.normalize` and :func:`.reweight` functions for downstream
  BrainPrint analysis in :mod:`.onthefly._brainprint` by `Synchon Mandal`_
  (:gh:`354`)
- Introduce :class:`junifer.pipeline.PipelineComponentRegistry` to centralise
  pipeline component management by `Synchon Mandal`_ (:gh:`362`)
- Add support for plugins by `Synchon Mandal`_ (:gh:`366`)
- Introduce :class:`junifer.data.CoordinatesRegistry`,
  :class:`junifer.data.ParcellationRegistry` and
  :class:`junifer.data.MaskRegistry` to centralise data management by `Synchon
  Mandal`_ (:gh:`387`)
- Introduce ``junifer.typing`` sub-module to organise internal and external
  type hints by `Synchon Mandal`_ (:gh:`392`)
- Introduce :class:`junifer.utils.ConfigManager` singleton class to manage
  global configuration by `Fede Raimondo`_ (:gh:`401`)
- Introduce ``BOLD.reference`` nested type and adapt :class:`.SpaceWarper` and
  necessary data components by `Fede Raimondo`_ (:gh:`407`)
- Allow masks to be warped, if found, in :class:`.SpaceWarper` by `Synchon
  Mandal`_ (:gh:`408`)
- Add support for coloured :class:`logging.Formatter` to use with ``junifer``'s
  :class:`logging.StreamHandler` based on environment by `Fede Raimondo`_
  (:gh:`412`)
- Allow storage of 2D timeseries, currently only supported by
  HDF5FeatureStorage by `Fede Raimondo`_ (:gh:`422`)


Miscellaneous
^^^^^^^^^^^^^

- Adopt lazy-import mechanism for the package by `Synchon Mandal`_ (:gh:`355`)
- Refactor ``api`` sub-package and introduce new ``cli`` sub-package by
  `Synchon Mandal`_ (:gh:`361`)
- Add ``junifer-data`` as a dependency by `Synchon Mandal`_ (:gh:`363`)
- Drop support for Python 3.8, add support for Python 3.13 and make Python 3.12
  the base for code coverage by `Synchon Mandal`_ (:gh:`372`)
- Add Dockerfile for docs CI and a corresponding action for building and
  publishing the image by `Synchon Mandal`_ (:gh:`373`)
- Adopt usage of custom docs CI image for building and previewing docs actions
  by `Synchon Mandal`_ (:gh:`374`)
- Update Dependabot GitHub Action to support groups by `Synchon Mandal`_
  (:gh:`380`)
- Add Dockerfile for CI and a corresponding action for building and publishing
  the image by `Synchon Mandal`_ (:gh:`382`)
- Adopt usage of custom CI image for testing junifer action by `Synchon
  Mandal`_ (:gh:`383`)
- Improve docs publishing action and add a manual trigger for it by `Synchon
  Mandal`_ (:gh:`384`)
- Refactor ``Singleton`` class to use a metaclass instead of a class decorator
  by `Fede Raimondo`_ (:gh:`391`)
- Update type hints across codebase to be Python>=3.9 compatible by `Synchon
  Mandal`_ (:gh:`393`)
- Update Docker image recipes and GitHub Actions workflows by `Synchon Mandal`_
  (:gh:`396`)
- Simplify logic for parcellation and mask space warping by `Synchon Mandal`_
  (:gh:`414`)
- Remove ``httpx`` as a dependency by `Synchon Mandal`_ (:gh:`418`)
- Fix coverage in CI by `Fede Raimondo`_ (:gh:`424`)
- Use ``junifer-data`` in CI images by `Synchon Mandal`_ (:gh:`427`)
- Improve GitHub Actions workflows by `Synchon Mandal`_ (:gh:`428`)
- Bump ``junifer-data`` to ``v2`` for CI workflows, remove ``Power`` and add
  ``Seitzman2018`` to :class:`.CoordinatesRegistry` by `Synchon Mandal`_
  (:gh:`437`)
- Bump ``junifer-data`` to ``v2`` for Docker images by `Synchon Mandal`_
  (:gh:`438`)


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
