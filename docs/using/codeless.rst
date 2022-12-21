.. include:: ../links.inc

.. _codeless:

Code-less configuration
=======================

On of the most important features of junifer is its capacity to run without writing a single line of code. This is
achieved by using a configuration file that is written in YAML_. In this file, we configure the different steps of
:ref:`pipeline`.

As a reminder, this is how the pipeline looks like:

.. image:: ../images/pipeline/pipeline.001.png

Thus, the configuration file must configure each of the sections of the pipeline, as well as some general parameters.

As an example, we will generate the configuration file for a pipeline that will extract the mean ``VBM_GM`` values
using two different parcellations and one set of coordinates, from the *Oasis VBM Testing dataset* included in
junifer.


General Parameters
------------------

The general parameters are the ones that are not specific to any of the sections of the pipeline, but configure
junifer as a whole. These parameters are:

* ``with``: A section used to specify modules and junifer extensions to use.
* ``workdir``: The working directory where junifer will store temporary files.

Since the example uses a specific datagrabber for testing, we need to add ``junifer.testing.registry`` to the
``with`` section. This will allow junifer to find the datagrabber. We will set the ``workdir`` to ``/tmp``.

.. code-block:: yaml

  with: junifer.testing.registry
  workdir: /tmp

Step-by-step configuration
--------------------------

In order to configure the pipeline, we need to configure each step:

* ``datagrabber``
* ``datareader``
* ``preprocess``
* ``markers``
* ``storage``

.. important:: The datareader step configuration is optional, as junifer only provides one datareader. Nevertheless,
    it is possible to extend junifer with custom datareaders, and thus, it is also possible to configure this step.


Data Grabber
^^^^^^^^^^^^

The ``datagrabber`` section must be configured using the ``kind`` key to specify the datagrabber to use. Additional
keys correspond to the parameters of the datagrabber.

For example, to use the :class:`junifer.datagrabber.DataladAOMICPIOP1` datagrabber, we just need to
specify its name as the ``kind`` key.

.. code-block:: yaml

  datagrabber:
    kind: DataladAOMICPIOP1

However, it is also possible to pass parameters to the datagrabber. In this case, we can restrict the datagrabber to
fetch only the  ``restingstate`` task.

.. code-block:: yaml

  datagrabber:
    kind: DataladAOMICPIOP1
    tasks: restingstate

In the *Oasis VBM Testing dataset* example, the section will look like this:

.. code-block:: yaml

  datagrabber:
    kind: OasisVBMTesting


Data Reader
^^^^^^^^^^^

As mentioned before, this section is entirely optional, as junifer only provides one data reader
(:class:`junifer.datareader.DefaultDataReader`), which is the default in case the section is not specified.

In any case, the syntax of the section is the same as for the ``datagrabber`` section, using the ``kind`` key to
specify the data reader to use, and additional keys to pass parameters to the data reader:

.. code-block:: yaml

    datareader:
      kind: DefaultDataReader


For the *Oasis VBM Testing dataset* example, we will not specify a ``datareader`` step.

Preprocessing
^^^^^^^^^^^^^

Preprocessing is also an optional step, as it might be the case that no pre-processing is needed. In the case that
preprocessing is needed, the section must be configured using the ``kind`` key to specify the preprocessor to use,
and additional keys to pass parameters to the preprocessor.

For example, to use the :class:`junifer.preprocess.fMRIPrepConfoundRemover` preprocessor, we just need to specify its
name as the ``kind`` key, as well as its parameters.


.. code-block:: yaml

  preprocess:
    kind: fMRIPrepConfoundRemover
    strategy:
      motion: full
      wm_csf: full
      global_signal: basic
    spike: 0.2
    detrend: false
    standardize: true


For the *Oasis VBM Testing dataset* example, we will not specify a preprocessing step.


Markers
^^^^^^^

The ``markers`` section diverges from the previous ones, as we need to specify a list of markers. Each marker has a
name that we can use to refer to it later, and a set of parameters that will be passed to the marker.

For the *Oasis VBM Testing dataset* example, we want to compute the mean ``VBM_GM`` value for each parcel using the
Schaefer parcellation (100 parcels, 7 networks), Schaefer parcellation (200 parcels, 7 networks), and the *DMNBuckner*
network, using 5mm spheres. Thus, we will configure the ``markers`` section as follows:

.. code-block:: yaml

  markers:
    - name: Schaefer100x7_mean
      kind: ParcelAggregation
      parcellation: Schaefer100x7
      method: mean
    - name: Schaefer200x7_mean
      kind: ParcelAggregation
      parcellation: Schaefer200x7
      method: mean
    - name: DMNBuckner_5mm_mean
      kind: SphereAggregation
      coords: DMNBuckner
      radius: 5
      method: mean


Storage
^^^^^^^

Finally, we need to define how and where the results will be stored. This is done using the ``storage`` section,
which must be configured using the ``kind`` key to specify the storage to use, and additional keys to pass parameters.

For example, to use the :class:`junifer.storage.SQLiteFeatureStorage` storage, we just need to specify where we want
to store the results:

.. code-block:: yaml

    storage:
      kind: SQLiteFeatureStorage
      uri: /data/junifer/example/oasis_vbm_testing.sqlite


The full example
----------------

This is how the full *Oasis VBM Testing dataset* example configuration file looks like:

.. code-block:: yaml

  with: junifer.testing.registry
  workdir: /tmp

  datagrabber:
    kind: OasisVBMTesting

  markers:
    - name: Schaefer100x7_mean
      kind: ParcelAggregation
      parcellation: Schaefer100x7
      method: mean
    - name: Schaefer200x7_mean
      kind: ParcelAggregation
      parcellation: Schaefer200x7
      method: mean
    - name: DMNBuckner_5mm_mean
      kind: SphereAggregation
      coords: DMNBuckner
      radius: 5
      method: mean

  storage:
    kind: SQLiteFeatureStorage
    uri: /data/junifer/example/oasis_vbm_testing.sqlite
