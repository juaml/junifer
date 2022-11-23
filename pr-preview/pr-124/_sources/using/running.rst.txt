.. include:: ../links.inc

.. _running:

Running jobs
============

Once we have the :ref:`code-less configuration file <codeless>`, we can use the command line interface to extract the
features. This is achieved in a two-step process: ``run`` and ``collect``.

The ``run`` command is used to extract the features from each element in the dataset. However, depending on the
storage interface, this may create one file per subject. The ``collect`` command is then used to collect all of the
individual results into a single file.

Assuming that we have a configuration file named ``config.yaml``, the following commands will extract the features:

.. code-block:: console

    junifer run config.yaml

The ``run`` command accepts the following additional arguments:

* ``--help``: Show a help message.
* ``--verbose`` Set the verbosity level. Options are ``warning``, ``info``, ``debug``.
* ``--element``: The *element* to run. If not specified, all elements will be run. This parameter can be specified 
  multiple times to run multiple elements. If the *element* requires several parameters, they can be specified
  by separating them with ``,``.


Example on running two elements:

.. code-block:: console

    junifer run config.yaml --element sub-01 --element sub-02

Example on elements with multiple parameters and verbose output:

.. code-block:: console

    junifer run --verbose info config.yaml --element sub-01,ses-01

.. _collect:

Collecting results
==================

Once the ``run`` command has been executed, the results are stored in the output directory. However, depending on the
storage interface, this may create one file per subject. The ``collect`` command is then used to collect all of the
individual results into a single file.

Assuming that we have a configuration file named ``config.yaml``, the following commands will collect the results:

.. code-block:: console

    junifer collect config.yaml

The ``collect`` command accepts the following additional arguments:

* ``--help``: Show a help message.
* ``--verbose`` Set the verbosity level. Options are ``warning``, ``info``, ``debug``.
