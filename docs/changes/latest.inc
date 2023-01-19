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

Bugs
~~~~

- Fix ``junifer run`` to respect preprocess step specified in the pipeline (:gh:`159` by `Synchon Mandal`_).

API changes
~~~~~~~~~~~

- Add ``confounds_format`` parameter to :class:`junifer.datagrabber.PatternDataGrabber` constructor for
  improved handling of confounds specified via ``BOLD_confounds`` data type (:gh:`158` by `Synchon Mandal`_).