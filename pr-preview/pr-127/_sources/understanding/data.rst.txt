.. include:: ../links.inc

.. _data_object:

The Data Object
===============

Description
-----------

This is the *object* that traverses the steps of the pipeline. It is indeed a
dictionary of dictionaries. The first level of keys are the :ref:`data types <data_types>`
and a special key named ``meta`` that contains all the information on the data
object including source and previous transformation steps.

The second level of keys are the actual data. So far, there are two keys used:

- ``path``: path to the file containing the data.
- ``data``: the data loaded in memory.

The :ref:`Data Grabber <datagrabber>` step will only fill the ``path`` value.
The ``data`` value will be filled by the :ref:`DataReader <datareader>` step, if it is one of the possible file types
that the datareader can read.

A point to note is that you never directly interact with the *data object* but it's important to know where and how the object is being manipulated to reason about your pipeline.

.. _data_types:

Data types
----------

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Name
     - Description
     - Example
   * - ``T1w``
     - T1w image (3D)
     - Preprocessed or Raw T1w image
   * - ``BOLD``
     - BOLD image (4D)
     - Preprocessed/Denoised BOLD image (fmriprep output)
   * - ``BOLD_confounds``
     - BOLD image confounds (CSV/TSV file)
     - Confounds that can be applied to the BOLD image.
   * - ``VBM_GM``
     - VBM Gray Matter segmentation (3D)
     - CAT output (`m0wp1` images)
   * - ``VBM_WM``
     - VBM White Matter segmentation (3D)
     - CAT output (`m0wp2` images)
   * - ``fALFF``
     - Voxel-wise fALFF image (3D)
     - fALFF computed with CONN toolbox
   * - ``GCOR``
     - Global Correlation image (3D)
     - GCOR computed with CONN toolbox
   * - ``LCOR``
     - Local Correlation image (3D)
     - LCOR computed with CONN toolbox