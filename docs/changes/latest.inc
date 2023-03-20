.. NOTE: we are now using links to highlight new functions and classes.
   Please follow the examples below like
   :func:`julearn.api.run_cross_validation`, so the
   whats_new page will have a link to the function/class documentation.

.. NOTE: there are 3 separate sections for changes, based on type:
   - "Enhancements" for new features
   - "Bugs" for bug fixes
   - "API changes" for backward-incompatible changes

.. NOTE: add the contributors and reference to the github issue/PR at the end
   Example:
     - Implemented feature X (:gh:`151` by `Sami Hamdan`_).

.. _current:

Current (0.0.2.dev)
-------------------

Enhancements
~~~~~~~~~~~~

- Allow :class:`junifer.testing.datagrabbers.PartlyCloudyTestingDataGrabber` to be accessible
  via ``import junifer.testing.registry`` (:gh:`160` by `Synchon Mandal`_).

- Update docstrings and fix typo in log message (:gh:`165` by `Synchon Mandal`_).

- Add support for ``Power`` coordinates (:gh:`167` by `Synchon Mandal`_).

- Add support for ``Dosenbach`` coordinates (:gh:`168` by `Synchon Mandal`_).

- Organize functional connectivity markers in ``junifer.markers.functional_connectivity``
  (:gh:`107` by `Synchon Mandal`_).

- Add :class:`junifer.markers.EdgeCentricFCParcels` and :class:`junifer.markers.EdgeCentricFCSpheres`
  (:gh:`64` by `Leonard Sasse`_).

- Change HCP datagrabber tests to decrease CI running time (:gh:`155` by `Fede Raimondo`_).

- Add support for nilearn computed masks (``compute_epi_mask``, ``compute_brain_mask``, ``compute_background_mask``,
  ``fetch_icbm152_brain_gm_mask``) (:gh:`175` by `Fede Raimondo`_).

- Add fMRIPrep brain masks to the datagrabber patterns for all datagrabbers in the aomic sub-package
  (:gh:`177` by `Leonard Sasse`_).

- Add :class:`junifer.markers.TemporalSNRParcels` and :class:`junifer.markers.TemporalSNRSpheres`
  (:gh:`163` by `Leonard Sasse`_).

- Add support for HDF5 feature storage via :class:`junifer.storage.HDF5FeatureStorage`
  (:gh:`147` by `Synchon Mandal`_).

- Add ``pre_run`` parameter to ``_queue_condor`` (:gh:`188` by `Fede Raimondo`_).

- Allow for empty spheres in :class:`junifer.external.nilearn.JuniferNiftiSpheresMasker`, that will result in NaNs (:gh:`190` by `Fede Raimondo`_).

- Expose ``allow_overlap`` parameter in  :class:`junifer.markers.SphereAggregation` and related markers (:gh:`190` by `Fede Raimondo`_).

- Add aggregation function :func:`junifer.stats.count` that returns the number of elements in a given axis. This allows to count the number of voxels per sphere/parcel when used as ``method`` in markers (:gh:`190` by `Fede Raimondo`_).

- Modify the behaviour of the ``collect`` parameter in HTCondor ``queue`` function to run a collect job even if some of the previous jobs fail. This is useful to collect the results of a pipeline even if some of the jobs fail (:gh:`190` by `Fede Raimondo`_).

- Allow for empty parcels in :class:`junifer.markers.ParcelAggregation`, that will result in NaNs (:gh:`194` by `Fede Raimondo`_).

- Improve metadata and data I/O for :class:`junifer.storage.HDF5FeatureStorage` (:gh:`196` by `Synchon Mandal`_).

Bugs
~~~~

- Fix ``junifer run`` to respect preprocess step specified in the pipeline (:gh:`159` by `Synchon Mandal`_).

- Fix :class:`junifer.markers.AmplitudeLowFrequencyFluctuationParcels`, :class:`junifer.markers.AmplitudeLowFrequencyFluctuationSpheres`
  :class:`junifer.markers.ReHoSpheres` and :class:`junifer.markers.ReHoParcels` pass the ``extra_input`` parameter (:gh:`187` by `Fede Raimondo`_).

- Fix several markers that did not properly handle the ``extra_input`` parameter (:gh:`189` by `Fede Raimondo`_).

- Fix an issue with datalad cache and locks in which the user-specific configuration might create a conflict in high throughput systems (:gh:`192` by `Fede Raimondo`_).

- Fix a bug in which :func:`junifer.stats.count` will not be correctly applied across an axis (:gh:`195` by `Fede Raimondo`_).

- Fix an issue with datalad cache and locks in which the overriden settings in Junifer were not propagated to subprocesses, resulting in using the default settings (:gh:`199` by `Fede Raimondo`_).

- Fix a bug in which :class:`junifer.markers.ParcelAggregation` could yield duplicated column names if two or more parcels were used and label names were not unique (:gh:`194` by `Fede Raimondo`_).

- Fix a bug in which :func:`junifer.data.masks.get_mask` fails for FunctionalConnectivityBase class, because of missing extra_input parameter (:gh:`200` by `Leonard Sasse`_)

API changes
~~~~~~~~~~~

- Add ``confounds_format`` parameter to :class:`junifer.datagrabber.PatternDataGrabber` constructor for
  improved handling of confounds specified via ``BOLD_confounds`` data type (:gh:`158` by `Synchon Mandal`_).

- Rename ``store_table()`` to ``store_vector()`` for storage-like objects and adapt marker-like objects to
  use ``"vector"`` in place of ``"table"`` for storage. Also, improve the logic of storing vectors
  (:gh:`181` by `Synchon Mandal`_).