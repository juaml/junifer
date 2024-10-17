.. include:: ../links.inc

.. _running:

Running Jobs
============

Once we have the :ref:`code-less configuration file <codeless>`, we can use the
command line interface to extract the features. This is achieved in a two-step
process: ``run`` and ``collect``.

The ``run`` command is used to extract the features from each element in the
dataset. However, depending on the storage interface, this may create one file
per subject. The ``collect`` command is then used to collect all of the
individual results into a single file.

Assuming that we have a configuration file named ``config.yaml``, the following
commands will extract the features:

.. code-block:: bash

    junifer run config.yaml

The ``run`` command accepts the following additional arguments:

* ``--help``: Show a help message.
* ``--verbose``: Set the verbosity level. Options are ``warning``, ``info``,
  ``debug``.
* ``--element``: The *element* to run. If not specified, all elements will be
  run. This parameter can be specified multiple times to run multiple elements.
  If the *element* requires several parameters, they can be specified by
  separating them with ``,``. It also accepts a file (e.g., ``elements.txt``)
  containing complete or partial element(s).

Example of running two elements:
--------------------------------

.. code-block:: bash

    junifer run config.yaml --element sub-01 --element sub-02

You can also specify the elements via a text file like so:

.. code-block:: bash

    junifer run config.yaml --element elements.txt

And the corresponding ``elements.txt`` would be like so:

.. code-block:: text

    sub-01
    sub-02

Example of elements with multiple parameters and verbose output:
----------------------------------------------------------------

.. code-block:: bash

    junifer run --verbose info config.yaml --element sub-01,ses-01

You can also specify the elements via a text file like so:

.. code-block:: bash

    junifer run --verbose info config.yaml --element elements.txt

And the corresponding ``elements.txt`` would be like so:

.. code-block:: text

    sub-01,ses-01

In case you wanted to run for all possible sessions (e.g., ``ses-01``,
``ses-02``, ``ses-03``) but only for ``sub-01``, you could also do:

.. code-block:: bash

    junifer run --verbose info config.yaml --element sub-01

or,

.. code-block:: bash

    junifer run --verbose info config.yaml --element elements.txt

and then the ``elements.txt`` would be like so:

.. code-block:: text

    sub-01


.. _collect:

Collecting Results
==================

Once the ``run`` command has been executed, the results are stored in the output
directory. However, depending on the storage interface, this may create one file
per subject. The ``collect`` command is then used to collect all of the
individual results into a single file.

Assuming that we have a configuration file named ``config.yaml``, the following
commands will collect the results:

.. code-block:: bash

    junifer collect config.yaml

The ``collect`` command accepts the following additional arguments:

* ``--help``: Show a help message.
* ``--verbose``: Set the verbosity level. Options are ``warning``, ``info``,
  ``debug``.


.. _analysing_extracted_features:

Analysing Results
=================

After ``collect``-ing the results into a single file, we can analyse them as we
wish. We would need to do this programmatically so feel free to choose your
Python interpreter of choice or use it via a Python script.

First we load the storage like so:

.. code-block:: python

    from junifer.storage import HDF5FeatureStorage

    # You need to import and use SQLiteFeatureStorage if you chose that
    # for storage while extracting features
    storage = HDF5FeatureStorage("<path/to/your/collected/file>")

The best way to start analysing would be to list all the extracted features
like so:

.. code-block:: python

    # This would output a dictionary with MD5 checksum of the features as keys
    # and metadata of the features as values
    storage.list_features()

.. code-block::

   {'eb85b61eefba61f13d712d425264697b': {'datagrabber': {'class': 'SPMAuditoryTestingDataGrabber',
                                                         'types': ['BOLD', 'T1w']},
                                          'dependencies': {'scikit-learn': '1.3.0', 'nilearn': '0.9.2'},
                                          'datareader': {'class': 'DefaultDataReader'},
                                          'type': 'BOLD',
                                          'marker': {'class': 'FunctionalConnectivityParcels',
                                                     'parcellation': 'Schaefer100x7',
                                                     'agg_method': 'mean',
                                                     'agg_method_params': None,
                                                     'cor_method': 'covariance',
                                                     'cor_method_params': {'empirical': False},
                                                     'masks': None,
                                                     'name': 'schaefer_100x7_fc_parcels'},
                                          '_element_keys': ['subject'],
                                          'name': 'BOLD_schaefer_100x7_fc_parcels'}}

Once we have this, we can retrieve a single feature like so:

.. code-block:: python

    feature_dict = storage.read("<name-key-from-feature-metadata>")

to get the stored dictionary or,

.. code-block:: python

    feature_df = storage.read_df("<name-key-from-feature-metadata>")

to get it as a :class:`pandas.DataFrame`.

If there are features with duplicate ``name`` s, then we would need to use
the MD5 checksum and pass it like so:

.. code-block:: python

    feature_df = storage.read_df(feature_md5="<md5-hash-of-feature>")

We can now manipulate the dictionary or the :class:`pandas.DataFrame` as we
wish or use the DataFrame directly with `julearn`_ if desired.


On-the-fly transforms
---------------------

``junifer`` supports performing some computationally cheap operations
(like computing brain connectivity or BrainPrint post-analysis) directly
on the storage objects. To make sure everything works, install ``junifer``
like so:

.. code-block:: bash

    pip install junifer[onthefly]

or if installed via ``conda``, everything should be there and no further action
is required.

Computing brain connectivity via `bctpy <https://github.com/aestrivex/bctpy>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can compute for example, the degree of each node considering an undirected
graph via `bctpy`_ like so:

.. code-block:: python

    from junifer.onthefly import read_transform

    transformed_df = read_transform(
        storage,
        # md5 hash can also be passed via `feature_md5`
        feature_name="<name-key-from-feature-metadata>",
        # format is `package_function`
        transform="bctpy_degrees_und",
    )

Post-analysis of BrainPrint results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To perform post-analysis on BrainPrint results, start by importing:

.. code-block:: python

    from junifer.onthefly import brainprint


Normalising:
~~~~~~~~~~~~

Surface normalisation can be done by:

.. code-block:: python

    surface_normalised_df = brainprint.normalize(
        storage,
        {
            "areas": {
                "feature_name": "<name-key-from-areas-feature>",
                # if md5 hash is passed, the above should be None
                "feature_md5": None,
            },
            "eigenvalues": {
                "feature_name": "<name-key-from-eigenvalues-feature>",
                "feature_md5": None,
            },
        },
        kind="surface",
    )

and volume normalisation can be done by:

.. code-block:: python

    volume_normalised_df = brainprint.normalize(
        storage,
        {
            "volumes": {
                "feature_name": "<name-key-from-volumes-feature>",
                "feature_md5": None,
            },
            "eigenvalues": {
                "feature_name": "<name-key-from-eigenvalues-feature>",
                "feature_md5": None,
            },
        },
        kind="volume",
    )

Re-weighting:
~~~~~~~~~~~~~

To perform re-weighting, run like so:

.. code-block:: python

    reweighted_df = brainprint.reweight(
        storage,
        # md5 hash can also be passed via `feature_md5`
        feature_name="<name-key-from-eigenvalues-feature>",
    )
