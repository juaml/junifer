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

Current (0.0.0.dev)
-------------------

Enhancements
~~~~~~~~~~~~
- Implemented SPM Auditory testing datagrabber X (:gh:`52` by `Fede Raimondo`_).

- Created a the repository based on the mockup by by `Fede Raimondo`_.

- Added comments to datalad grabber and changed to use datalad-clone instead of
  datalad-install (:gh: `55` by `Benjamin Poldrack`_).

- Added an example how to use junifer and julearn (:gh: `40` by `Leonard Sasse_`,
  `Nicolas Nieto_`, and `Sami Hamdan_`) in one pipeline to extract features
  and do machine learning

- Implement matrix storage in SQliteFeatureStorage (:gh:`42` by `Fede Raimondo`_).

- Marker for functional connectivity using an atlas (:gh:`41` by
  `Amir Omidvarnia`_ and `Kaustubh R. Patil`_)

- Added documentation for the datagrabbers (by `Leonard Sasse_`,
  `Nicolas Nieto_`, and `Sami Hamdan_`)

- Implement coordinate register, list and load (:gh:`11` by `Fede Raimondo`_).

- Added datagrabber for AOMIC1000 dataset including tests and creation of mock
  dataset for testing (:gh:`60` by `Vera Komeyer`_, `Xuan Li`_).

- Added support to access other input in the data object in the `compute` method
  (by `Fede Raimondo`_).

- Implemented the edge time series RSS marker (:gh: `51` by `Leonard Sasse`_,
  `Nicolas Nieto`_, `Sami Hamdan`_)

- Implement SphereAggregation marker (by `Fede Raimondo`_).

Bugs
~~~~

API changes
~~~~~~~~~~~
