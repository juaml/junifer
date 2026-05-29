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


Configuration for ``julio``
---------------------------

When generating a registry with `julio`_, we can configure the YAML generation process. For now, only
DataGrabbers can be configured through the use of ``_dump_exclude`` class variable, like so:

   .. code-block:: python

     from typing import ClassVar

     from junifer.api.decorators import register_datagrabber
     from junifer.datagrabber import PatternDataladDataGrabber


     @register_datagrabber
     class MyDataGrabber(PatternDataladDataGrabber):

         _dump_exclude: ClassVar[set[str]] = {
            "patterns",
            "replacements",
            "confounds_format",
            "partial_pattern_ok",
            "uri",
            "rootdir",
            "datadir",
            "datalad_id",
            "datalad_dirty",
            "datalad_commit_id",
        }


The above can be considered a standard setup for a custom DataGrabber inheriting from :class:`.PatternDataladDataGrabber`.


.. admonition:: Tip

   - For DataGrabbers inheriting from :class:`.BaseDataGrabber` custom setup is possible but not required.
   - For DataGrabbers inheriting from :class:`.PatternDataGrabber` no extra setup should be required.
   - For :class:`.PatternDataladDataGrabber`\s specified via the YAML, it is not possible
     to customise and is usually not required. If such a need arises, creating a custom DataGrabber is the only way.
