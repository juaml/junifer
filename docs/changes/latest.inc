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

Bugs
~~~~

- Fix ``junifer run`` to respect preprocess step specified in the pipeline (:gh:`159` by `Synchon Mandal`_).

API changes
~~~~~~~~~~~
