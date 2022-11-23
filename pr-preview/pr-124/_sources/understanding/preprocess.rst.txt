.. include:: ../links.inc

.. _preprocess:

Preprocess
==========

Description
-----------

The ``Preprocess`` step of the pipeline is meant for pre-processing before or after :ref:`Marker <marker>` step
depending on the use-case. For example, you might want to perform confound removal on ``BOLD`` data before
feature extraction.

This step is still under development and is an optional one for the pipeline to work.

.. _preprocess_confounds:

Confound Removal
----------------

The *Confound Removal* step is meant to remove *confounds* from the ``BOLD`` data. The confounds are
extracted from the ``BOLD_confounds`` data (must be provided by the :ref:`Data Grabber <datagrabber>`).
The confounds are then regressed out from the ``BOLD`` data using :func:`nilearn.image.clean_img`.

Currently, junifer supports only one confound removal class: 
:class:`junifer.preprocess.fMRIPrepConfoundRemover`. This class is meant to remove confounds as described
before, using the output of `fMRIPrep`_ as reference.

Strategy
~~~~~~~~

This confound remover uses the `nilearn`_ API from :func:`nilearn.interfaces.fmriprep.load_confounds`. That is,
define a *strategy* to extract the confounds from the ``BOLD_confounds`` data. The *strategy* is defined
by choosing the *noise components* to be used and the *confounds* to be extracted from each noise components.
The *noise components* currently supported are:

* ``motion``
* ``wm_csf``
* ``global_signal``

The confounds options for each *noise component* are:

* ``basic``: the basic confounds for each *noise component*. For example, for ``motion``, the basic confounds
  are the 6 motion parameters (3 translations and 3 rotations). For ``wm_csf``, the basic
  confounds are the mean signal of the white matter and CSF regions. For ``global_signal``, the basic confound
  is the mean signal of the whole brain.
* ``power2``: the basic confounds plus the square of each basic confound.
* ``derivatives``: the basic confounds plus the derivative of each basic confound.
* ``full``: the basic confounds, the derivative of each basic confound, the square of each basic confound and the
  square of each derivative of each basic confound.

The *strategy* is defined as a dictionary, with the *noise components* as keys and the *confounds* as values.

Example in python format:

.. code-block:: 

    strategy = {
        "motion": "basic",
        "wm_csf": "full",
        "global_signal": "derivatives"
    }

or in YAML format:

.. code-block:: 
    
    strategy:
        motion: basic
        wm_csf: full
        global_signal: derivatives

The default value is to use all the *noise components* with the ``full`` *confounds*:

.. code-block:: 

    strategy = {
        "motion": "full",
        "wm_csf": "full",
        "global_signal": "full"
    }

Other parameters
~~~~~~~~~~~~~~~~

Additionaly, the :class:`junifer.preprocess.fMRIPrepConfoundRemover` supports the following parameters:

.. list-table::
   :widths: 10, 30, 5
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``spike``
     - Add a spike regressor in the timepoints when the framewise displacement exceeds this threshold.
     - deactivated
   * - ``detrend``
     - Apply detrending on timeseries, before confound removal.
     - activated
   * - ``standardize``
     - Scale signals to unit variance.
     - activated
   * - ``low_pass``
     - Low cutoff frequencies, in Hertz.
     - deactivated
   * - ``high_pass``
     - High cutoff frequencies, in Hertz.
     - deactivated
   * - ``t_r``
     - Repetition time, in second (sampling period).
     - from nifti header
   * - ``mask``
     - If provided, signal is only cleaned from voxels inside the mask. If not, a mask is computed using :func:`nilearn.masking.compute_brain_mask`.
     - compute