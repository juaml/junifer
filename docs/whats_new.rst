.. include:: links.inc
.. include:: changes/contributors.inc

.. _whats_new:

What's new
==========

.. towncrier release notes start

junifer 0.0.1 (2022-12-20)
--------------------------

API Changes
^^^^^^^^^^^

- Change the ``single_output`` default parameter in storage classes from
  ``False`` to ``True`` by `Fede Raimondo`_ (:gh:`134`)

Bugfixes
^^^^^^^^

- Fix a bug in which a :class:`junifer.datagrabber.PatternDataGrabber` would
  now work with relative ``datadir`` paths (reported by `Leonard Sasse`_,
  fixed by `Fede Raimondo`_) (:gh:`96`, :gh:`98`)

- Fix a bug in which :class:`junifer.datagrabber.DataladAOMICPIOP2` datagrabber
  did not use user input to constrain elements based on tasks by
  `Leonard Sasse`_ (:gh:`105`)

- Fix a bug in which a datalad dataset could remove a user-cloned dataset by
  `Fede Raimondo`_ (:gh:`53`)

- Fix a bug in which CLI command would not work using elements with more than
  one field by `Fede Raimondo`_

- Fix a bug in which the generated DAG for HTCondor will not work by
  `Fede Raimondo`_ (:gh:`143`)

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

- Add comments to :class:`junifer.datagrabber.DataladDataGrabber` datagrabber
  and change to use ``datalad-clone`` instead of ``datalad-install`` by
  `Benjamin Poldrack`_ (:gh:`55`)

- Upgrade storage interface for storage-like objects by `Synchon Mandal`_
  (:gh:`84`)

- Add missing type annotations by `Synchon Mandal`_ (:gh:`74`)

- Refactor markers ``on`` attribute and ``get_valid_inputs`` to verify that the
  marker can be computed on the input data types by `Fede Raimondo`_

- Add test for :class:`junifer.datagrabber.DataladHCP1200` datagrabber by
  `Synchon Mandal`_ (:gh:`93`)

- Rename "atlas" to "parcellation" by `Fede Raimondo`_ (:gh:`116`)

- Refactor the :class:`junifer.datagrabber.BaseDataGrabber` class to allow for
  easier subclassing by `Fede Raimondo`_ (:gh:`123`)

- Allow custom aggregation method for :class:`junifer.markers.SphereAggregation`
  by `Synchon Mandal`_ (:gh:`102`)

- Add support for "masks" by `Fede Raimondo`_ (:gh:`79`)

- Allow :class:`junifer.markers.ParcelAggregation` to apply multiple
  parcellations at once by `Fede Raimondo`_ (:gh:`131`)

- Refactor :class:`junifer.pipeline.PipelineStepMixin` to improve its
  implementation and validation for pipeline steps by `Synchon Mandal`_
  (:gh:`152`)

Features
^^^^^^^^

- Implement :class:`junifer.testing.datagrabbers.SPMAuditoryTestingDatagrabber`
  datagrabber by `Fede Raimondo`_ (:gh:`52`)

- Implement matrix storage in SQliteFeatureStorage by `Fede Raimondo`_
  (:gh:`42`)

- Implement :class:`junifer.markers.FunctionalConnectivityParcels` marker for
  functional connectivity using a parcellation by `Amir Omidvarnia`_ and
  `Kaustubh R. Patil`_ (:gh:`41`)

- Implement coordinate register, list and load by `Fede Raimondo`_ (:gh:`11`)

- Add :class:`junifer.datagrabber.DataladAOMICID1000` datagrabber for AOMIC
  ID1000 dataset including tests and creation of mock dataset for testing by
  `Vera Komeyer`_ and `Xuan Li`_ (:gh:`60`)

- Add support to access other input in the data object in the ``compute`` method
  by `Fede Raimondo`_

- Implement :class:`junifer.markers.RSSETSMarker` marker by `Leonard Sasse`_,
  `Nicolas Nieto`_ and `Sami Hamdan`_ (:gh:`51`)

- Implement :class:`junifer.markers.SphereAggregation` marker by
  `Fede Raimondo`_

- Implement :class:`junifer.datagrabber.DataladAOMICPIOP1` and
  :class:`junifer.datagrabber.DataladAOMICPIOP2` datagrabbers for AOMIC PIOP1
  and PIOP2 datasets respectively and refactor
  :class:`junifer.datagrabber.DataladAOMICID1000` slightly by `Leonard Sasse`_
  (:gh:`94`)

- Implement :class:`junifer.configs.juseless.datagrabbers.JuselessDataladCamCANVBM`
  datagrabber by `Leonard Sasse`_ (:gh:`99`)

- Implement :class:`junifer.configs.juseless.datagrabbers.JuselessDataladIXIVBM`
  CAT output datagrabber for juseless by `Leonard Sasse`_ (:gh:`48`)

- Add ``junifer wtf`` to report environment details by `Synchon Mandal`_
  (:gh:`33`)

- Add ``junifer selftest`` to report environment details by `Synchon Mandal`_
  (:gh:`9`)

- Implement :class:`junifer.configs.juseless.datagrabbers.JuselessDataladAOMICID1000VBM`
  datagrabber for accessing AOMIC ID1000 VBM from juseless by `Felix Hoffstaedter`_
  and `Synchon Mandal`_ (:gh:`57`)

- Add :class:`junifer.preprocess.fMRIPrepConfoundRemover` by `Fede Raimondo`_
  and `Leonard Sasse`_ (:gh:`111`)

- Implement :class:`junifer.markers.CrossParcellationFC` marker by
  `Leonard Sasse`_ and `Kaustubh R. Patil`_ (:gh:`85`)

- Add :class:`junifer.configs.juseless.datagrabbers.JuselessUCLA` datagrabber
  for the UCLA dataset available on juseless by `Leonard Sasse`_ (:gh:`118`)

- Introduce a singleton decorator for marker computations by `Synchon Mandal`_
  (:gh:`151`)

- Implement :class:`junifer.markers.ReHoParcels` and
  :class:`junifer.markers.ReHoSpheres` markers by `Synchon Mandal`_ (:gh:`36`)

- Implement :class:`junifer.markers.ALFFParcels` and
  :class:`junifer.markers.ALFFSpheres` markers by `Fede Raimondo`_ (:gh:`35`)

Misc
^^^^

- Create the repository based on the mockup by `Fede Raimondo`_
