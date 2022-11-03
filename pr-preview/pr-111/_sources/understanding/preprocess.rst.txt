.. include:: ../links.inc

.. _preprocess:

Preprocess
==========

Description
^^^^^^^^^^^

The ``Preprocess`` step of the pipeline is meant for pre-processing before or after :ref:`Marker <marker>` step
depending on the use-case. For example, you might want to perform confound removal on ``BOLD`` data before
feature extraction.

This step is still under development and is an optional one for the pipeline to work.

.. _preprocess_confounds:

Confound Removal
^^^^^^^^^^^^^^^^

The *Confound Removal* step is meant to remove *confounds* from the ``BOLD`` data. The confounds are
extracted from the ``BOLD_confounds`` data (must be provided by the :ref:`DataGrabber <datagrabber>`).
The confounds are then regressed out from the ``BOLD`` data using :func:`nilearn.image.clean_img`.