v0.0.1
------

Enhancements
~~~~~~~~~~~~

- Create the repository based on the mockup by `Fede Raimondo`_.

- Implement :class:`junifer.testing.datagrabbers.SPMAuditoryTestingDatagrabber` datagrabber
  (:gh:`52` by `Fede Raimondo`_).

- Add comments to :class:`junifer.datagrabber.DataladDataGrabber` datagrabber and change to
  use ``datalad-clone`` instead of ``datalad-install`` (:gh:`55` by `Benjamin Poldrack`_).

- Add an example how to use junifer and julearn in one pipeline to extract features
  and do machine learning (:gh:`40` by `Leonard Sasse`_, `Nicolas Nieto`_, and `Sami Hamdan`_).

- Implement matrix storage in SQliteFeatureStorage (:gh:`42` by `Fede Raimondo`_).

- Implement :class:`junifer.markers.FunctionalConnectivityParcels` marker for functional
  connectivity using a parcellation (:gh:`41` by `Amir Omidvarnia`_ and `Kaustubh R. Patil`_).

- Add documentation for the datagrabbers (by `Leonard Sasse`_,
  `Nicolas Nieto`_, and `Sami Hamdan`_).

- Implement coordinate register, list and load (:gh:`11` by `Fede Raimondo`_).

- Add :class:`junifer.datagrabber.DataladAOMICID1000` datagrabber for AOMIC ID1000 dataset
  including tests and creation of mock dataset for testing (:gh:`60` by `Vera Komeyer`_, `Xuan Li`_).

- Add support to access other input in the data object in the ``compute`` method
  (by `Fede Raimondo`_).

- Implement :class:`junifer.markers.RSSETSMarker` marker (:gh:`51` by `Leonard Sasse`_,
  `Nicolas Nieto`_, `Sami Hamdan`_).

- Implement :class:`junifer.markers.SphereAggregation` marker (by `Fede Raimondo`_).

- Implement :class:`junifer.datagrabber.DataladAOMICPIOP1` and
  :class:`junifer.datagrabber.DataladAOMICPIOP2` datagrabbers for AOMIC PIOP1 and PIOP2 datasets
  respectively and refactor :class:`junifer.datagrabber.DataladAOMICID1000` slightly
  (:gh:`94` by `Leonard Sasse`_)

- Implement :class:`junifer.configs.juseless.datagrabbers.JuselessDataladCamCANVBM` datagrabber
  (:gh:`99` by `Leonard Sasse`_)

- Implement :class:`junifer.configs.juseless.datagrabbers.JuselessDataladIXIVBM` CAT output
  datagrabber for juseless (:gh:`48` by `Leonard Sasse`_).

- Upgrade storage interface for storage-like objects (:gh:`84` by `Synchon Mandal`_).

- Add missing type annotations (:gh:`74` by `Synchon Mandal`_).

- Add ``junifer wtf`` to report environment details (:gh:`33` by `Synchon Mandal`_).

- Add ``junifer selftest`` to report environment details (:gh:`9` by `Synchon Mandal`_).

- Refactor markers ``on`` attribute and ``get_valid_inputs`` to verify that the marker can
  be computed on the input data types (by `Fede Raimondo`_)

- Implement :class:`junifer.configs.juseless.datagrabbers.JuselessDataladAOMICID1000VBM`
  datagrabber for accessing AOMIC ID1000 VBM from juseless (:gh:`57` by `Felix Hoffstaedter`_
  and `Synchon Mandal`_)

- Add test for :class:`junifer.datagrabber.DataladHCP1200` datagrabber (:gh:`93` by `Synchon Mandal`_).

- Change documentation template to furo. Fix references and standardize documentation (:gh:`114` by `Fede Raimondo`_).

- Add :class:`junifer.preprocess.fMRIPrepConfoundRemover` (:gh:`111` by `Fede Raimondo`_ and `Leonard Sasse`_).

- Implement :class:`junifer.markers.CrossParcellationFC` marker (:gh:`85` by `Leonard Sasse`_
  and `Kaustubh R. Patil`_)

- Add :class:`junifer.configs.juseless.datagrabbers.JuselessUCLA` datagrabber for the UCLA dataset
  available on juseless (:gh:`118` by `Leonard Sasse`_).

- Rename "atlas" to "parcellation" (:gh:`116` by `Fede Raimondo`_).

- Refactor the :class:`junifer.datagrabber.BaseDataGrabber` class to allow for easier subclassing (:gh:`123` by `Fede Raimondo`_).

- Allow custom aggregation method for :class:`junifer.markers.SphereAggregation` (:gh:`102` by `Synchon Mandal`_).

- Add support for "masks" (:gh:`79` by `Fede Raimondo`_).

- Allow :class:`junifer.markers.ParcelAggregation` to apply multiple parcellations at once (:gh:`131` by `Fede Raimondo`_).

- Introduce a singleton decorator for marker computations (:gh:`151` by `Synchon Mandal`_).

- Refactor :class:`junifer.pipeline.PipelineStepMixin` to improve its implementation and validation for pipeline steps
  (:gh:`152` by `Synchon Mandal`_).

- Implement :class:`junifer.markers.ReHoParcels` and :class:`junifer.markers.ReHoSpheres` markers (:gh:`36` by `Synchon Mandal`_).

- Implement :class:`junifer.markers.AmplitudeLowFrequencyFluctuationParcels` and
  :class:`junifer.markers.AmplitudeLowFrequencyFluctuationSpheres` markers (:gh:`35` by `Fede Raimondo`_).

Bugs
~~~~

- Fix a bug in which a :class:`junifer.datagrabber.PatternDataGrabber` would now work with relative ``datadir`` paths.
  (:gh:`96` by `Leonard Sasse`_, fixed in :gh:`98` by `Fede Raimondo`_).

- Fix a bug in which :class:`junifer.datagrabber.DataladAOMICPIOP2` datagrabber did not use user input to
  constrain elements based on tasks (:gh:`105` by `Leonard Sasse`_)

- Fix a bug in which a datalad dataset could remove a user-cloned dataset (:gh:`53` by `Fede Raimondo`_)

- Fix a bug in which CLI command would not work using elements with more than one field (by `Fede Raimondo`_).

- Fix a bug in which the generated DAG for HTCondor will not work (:gh:`143` by `Fede Raimondo`_).

API changes
~~~~~~~~~~~

- Change the ``single_output`` default parameter in storage classes from ``False`` to ``True`` (:gh:`134` by `Fede Raimondo`_).
