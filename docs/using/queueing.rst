.. include:: ../links.inc

.. _queueing:

Queueing jobs (HPC, HTC)
========================

Yet another interesting feature of junifer is the ability to queue jobs on computational clusters. This is done by
adding the ``queue`` section in the :ref:`codeless` file and executing the  ``junifer queue`` command.

While junifer is meant to support `HTCondor`_, `SLURM`_ and local queueing using `GNU Parallel`_, only HTCondor is
currently supported. This will be implemented in future relases of junifer. If you are in immediate need of any of these
schedulers, please create an issue on the `junifer github`_ repository.

The ``queue`` section of the :ref:`codeless` must start by defining the following general parameters:

* ``jobname``: name of the job to be queued. This will be used to name the folder where the job files will be created,
  as well as any relevant file. Depending on the scheduler, it will also be listed in the queueing system with this
  name.
* ``kind``: The kind of scheduler to be used. Currently, only ``HTCondor`` is supported.

Example:

.. code-block:: yaml

  queue:
    jobname: TestHTCondorQueue
    kind: HTCondor


The rest of the parameters depend on the scheduler you are using.

.. _queueing_condor:

HTCondor
--------

When using HTCondor, junifer will use a DAG to queue one job per element (``junifer run``). As an option, the DAG can
include a final job (``junifer collect``) to collect the results once all of the individual element jobs are finished.

The following parameters are avilable for HTCondor:

* ``env``: Definition of the Python enviroment. It must provide two variables: ``kind`` and ``name``. The ``kind``
  corresponds to the kind of virtual environment to use: ``conda``,  ``virtualenv`` (not yet supported) or 
  ``local`` (no virtual enviroment). The ``name`` is the name of the enviroment to use in case a virtual environment
  is used.
* ``mem``: Memory to be used by the job. It must be provided as a string with the units (e.g. ``2GB``).
* ``cpus``: Number of CPUs to be used by the job. It must be provided as an int.
* ``disk``: Disk space to be used by the job. It must be provided as a string with the units (e.g. ``2GB``). Keep in 
  mind that junifer uses a local working directory for each job, and datalad datasets might be cloned in this temporary
  directory.
* ``extra_preamble``: Extra lines to be added to the HTCondor submit file. This can be used to add
  extra parameters to the job, such as ``requirements``.
* ``collect``: If ``true``, a final job will be added to the DAG to collect the results once all of the individual
  element jobs are finished. This is useful if you want to run a ``junifer collect`` job only once all of the
  individual element jobs are finished. If not specified, it will default to ``true``.


Example:

.. code-block:: yaml

  queue:
    jobname: TestHTCondorQueue
    kind: HTCondor
    env:
      kind: conda
      name: junifer
    mem: 8G
    disk: 2GB
    collect: true


Once the :ref:`codeless` file is ready, including the ``queue`` section, you can queue the jobs by executing 
the ``junifer queue`` command. 

The ``queue`` command will create a folder with the name of the job (``jobname``) under the ``junifer_jobs`` directory
in the current working directory.

The ``queue`` command accepts the following arguments:

* ``--help``: Show a help message.
* ``--verbose`` Set the verbosity level. Options are ``warning``, ``info``, ``debug``.
* ``--submit``: Submit the jobs to the queueing system. If not specified, the job submit files will be created but not
  submitted.
* ``--overwrite``: Overwrite the job folder if it already exists. If not specified, the command will fail if the job
  folder already exists.
* ``--element``: Queue only the specified element(s). If not specified, all elements will be queued.
