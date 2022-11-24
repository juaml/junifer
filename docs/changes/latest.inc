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

- Created a the repository based on the mockup by `Fede Raimondo`_.

- Implemented SPM Auditory testing datagrabber X (:gh:`52` by `Fede Raimondo`_).

- Added comments to datalad grabber and changed to use datalad-clone instead of
  datalad-install (:gh:`55` by `Benjamin Poldrack`_).

- Added an example how to use junifer and julearn (:gh:`40` by `Leonard Sasse`_,
  `Nicolas Nieto`_, and `Sami Hamdan`_) in one pipeline to extract features
  and do machine learning.

- Implement matrix storage in SQliteFeatureStorage (:gh:`42` by `Fede Raimondo`_).

- Marker for functional connectivity using a parcellation (:gh:`41` by
  `Amir Omidvarnia`_ and `Kaustubh R. Patil`_).

- Added documentation for the datagrabbers (by `Leonard Sasse`_,
  `Nicolas Nieto`_, and `Sami Hamdan`_).

- Implement coordinate register, list and load (:gh:`11` by `Fede Raimondo`_).

- Added datagrabber for AOMIC1000 dataset including tests and creation of mock
  dataset for testing (:gh:`60` by `Vera Komeyer`_, `Xuan Li`_).

- Added support to access other input in the data object in the `compute` method
  (by `Fede Raimondo`_).

- Implemented the edge time series RSS marker (:gh:`51` by `Leonard Sasse`_,
  `Nicolas Nieto`_, `Sami Hamdan`_).

- Implement SphereAggregation marker (by `Fede Raimondo`_).

- Implement PIOP1 and PIOP2 AOMIC datasets and refactor AOMICID1000 slightly
  (:gh:`94` by `Leonard Sasse`_)

- Implement a JuselessDataladCamCANVBM datagrabber class (:gh:`99` by `Leonard Sasse`_)

- Implement IXI CAT output datagrabber for juseless (:gh:`48` by `Leonard Sasse`_).

- Upgrade storage interface for storage-like objects (:gh:`84` by `Synchon Mandal`_).

- Add missing type annotations (:gh:`74` by `Synchon Mandal`_).

- Add ``junifer wtf`` to report environment details (:gh:`33` by `Synchon Mandal`_).

- Add ``junifer selftest`` to report environment details (:gh:`9` by `Synchon Mandal`_).

- Refactor markers ``on`` attribute and ``get_valid_inputs`` to verify that the marker can be computed on the input data types (by `Fede Raimondo`_)

- Implement JuselessDataladAOMICID1000VBM datagrabber for accessing AOMIC ID 1000 VBM from juseless (:gh:`57` by `Felix Hoffstaedter`_ and `Synchon Mandal`_)

- Add test for DataladHCP1200 datagrabber (:gh:`93` by `Synchon Mandal`_).

- Change documentation template to furo. Fix references and standardize documentation (:gh:`114` by `Fede Raimondo`_).

- Add :class:`junifer.preprocess.fMRIPrepConfoundRemover` (:gh:`111` by `Fede Raimondo`_ and `Leonard Sasse`_).

- Implement CrossParcellationFC marker (:gh:`85` by `Leonard Sasse`_ and `Kaustubh R. Patil`_)

- Add datagrabber implementation for the UCLA dataset available on juseless (:gh:`118` by `Leonard Sasse`_).

- Rename "atlas" to "parcellation" (:gh:`116` by `Fede Raimondo`_).

- Refactor the :class:`junifer.datagrabber.BaseDataGrabber` class to allow for easier subclassing (:gh:`123` by `Fede Raimondo`_).

- Allow custom aggregation method for :class:`junifer.markers.SphereAggregation` (:gh:`102` by `Synchon Mandal`_).

- Add support for "masks" (:gh:`79` by `Fede Raimondo`_).

- Allow :class:`junifer.markers.ParcelAggregation` to apply multiple parcellations at once (:gh:`131` by `Fede Raimondo`_).

Bugs
~~~~

- Fix a bug in which a PatternDatagrabber would now work with relative `datadir` paths.
  (:gh:`96` by `Leonard Sasse`_, fixed in :gh:`98` by `Fede Raimondo`_).

- Fix a bug in which AOMIC PIOP2 datagrabber did not use user input to constrain elements based on tasks (:gh:`105` by `Leonard Sasse`_)

- Fix a bug in which a datalad dataset could remove a user-cloned dataset (:gh:`53` by `Fede Raimondo`_)

- Fix a bug in which CLI command would not work using elements with more than one field (by `Fede Raimondo`_).

- Fix a bug in which the generated DAG for HTCondor will not work (:gh:`143` by `Fede Raimondo`_).

API changes
~~~~~~~~~~~

- Change the ``single_output`` default parameter in storage classes from ``False`` to ``True`` (:gh:`134` by `Fede Raimondo`_).
