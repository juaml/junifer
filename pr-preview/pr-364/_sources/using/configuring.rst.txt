.. include:: ../links.inc

.. _configuring:

Configuring Pipeline Behaviour
==============================

It is also possible to configure some internal :ref:`pipeline <pipeline>` behaviour via :obj:`.ConfigManager`.
It can be done either via the command-line interface (CLI) or the application programming
interface (API).

To use via the CLI, one would do:

.. code-block:: bash

   <CONFIG-KEY>=<CONFIG-VAL> junifer run ...

and via the API like so:

.. code-block:: python

    from junifer.utils import config

    # Add config
    config.set(key="<config-key>", val=<config-val>)

    # do feature extraction
    ...

    # Remove config
    config.delete("<config-key>")

.. _available_configurations:

Available Configurations
------------------------

.. list-table::
   :widths: auto
   :header-rows: 1

   * - CLI Key
     - API Key
     - Value
     - Description
   * - ``JUNIFER_DATA_LOCATION``
     - ``data.location``
     - str
     - Alternative location for ``junifer-data``
   * - ``JUNIFER_DATAGRABBER_SKIPIDCHECK``
     - ``datagrabber.skipidcheck``
     - bool
     - Skip DataLad-based DataGrabber's ID check
   * - ``JUNIFER_DATAGRABBER_SKIPDIRTYCHECK``
     - ``datagrabber.skipdirtycheck``
     - bool
     - Skip Git "dirty" check for a DataLad dataset clone of a DataGrabber
   * - ``JUNIFER_PREPROCESSING_DUMP_LOCATION``
     - ``preprocessing.dump.location``
     - str
     - Dump location of pre-processed data for debugging purposes
   * - ``JUNIFER_PREPROCESSING_DUMP_GRANULARITY``
     - ``preprocessing.dump.granularity``
     - "full" or "final"
     - Dump all pre-processing steps or just the final pre-processed data
