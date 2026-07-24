.. include:: ../links.inc

.. _generate_yaml:

Generating YAML from metadata
=============================

``junifer`` stores the pipeline metadata for a run along with the extracted feature data.
So, the metadata for all the "elements" processed with a pipeline is unique. The metadata
contains all the necessary information to recreate the configuration used for the processing.

If one wants to generate the processing YAML, :func:`.generate_yaml` can be used for that.
The only requirement is providing the metadata which can be extracted by following the initial steps of
:ref:`analysing results <analysing_extracted_features>`.
