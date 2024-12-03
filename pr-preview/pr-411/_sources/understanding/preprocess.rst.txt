.. include:: ../links.inc

.. _preprocess:

Preprocess
==========

Description
-----------

The ``Preprocess`` is an object meant for pre-processing before or after
:ref:`Marker <marker>` step depending on the use-case. For example, you might
want to perform confound removal on ``BOLD`` data before feature extraction.


.. note::

   This step is optional for the pipeline to work.

.. _preprocess_confounds:

Confound Removal
----------------

This step is meant to remove *confounds* from the ``BOLD`` data. The confounds
are extracted from the ``BOLD.confounds`` data (must be provided by the
:ref:`Data Grabber <datagrabber>`). The confounds are then regressed out from
the ``BOLD`` data using :func:`nilearn.image.clean_img`.

Currently, ``junifer`` supports only one confound removal class:
:class:`.fMRIPrepConfoundRemover`. This class is meant to remove confounds as
described before, using the output of `fMRIPrep`_ as reference.

Strategy
~~~~~~~~

This confound remover uses the `nilearn`_ API from
:func:`nilearn.interfaces.fmriprep.load_confounds`. That is, define a *strategy*
to extract the confounds from the ``BOLD.confounds`` data. The *strategy* is
defined by choosing the *noise components* to be used and the *confounds* to be
extracted from each noise components. The *noise components* currently supported
are:

* ``motion``
* ``wm_csf``
* ``global_signal``

The confounds options for each *noise component* are:

* ``basic``: the basic confounds for each *noise component*. For example, for
  ``motion``, the basic confounds are the 6 motion parameters (3 translations
  and 3 rotations). For ``wm_csf``, the basic confounds are the mean signal of
  the white matter and CSF regions. For ``global_signal``, the basic confound
  is the mean signal of the whole brain.
* ``power2``: the basic confounds plus the square of each basic confound.
* ``derivatives``: the basic confounds plus the derivative of each basic
  confound.
* ``full``: the basic confounds, the derivative of each basic confound, the
  square of each basic confound and the square of each derivative of each basic
  confound.

The *strategy* is defined as a dictionary, with the *noise components* as keys
and the *confounds* as values.

Example in python format:

.. code-block:: python

    strategy = {
        "motion": "basic",
        "wm_csf": "full",
        "global_signal": "derivatives",
    }

or in YAML format:

.. code-block:: yaml

    strategy:
        motion: basic
        wm_csf: full
        global_signal: derivatives

The default value is to use all the *noise components* with the ``full`` *confounds*:

.. code-block:: python

    strategy = {"motion": "full", "wm_csf": "full", "global_signal": "full"}

Other Parameters
~~~~~~~~~~~~~~~~

Additionally, the :class:`.fMRIPrepConfoundRemover` supports the following
parameters:

.. list-table::
   :widths: auto
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``spike``
     - | Add a spike regressor in the timepoints when the framewise
       | displacement exceeds this threshold.
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
     - from NIfTI header
   * - ``mask``
     - | If provided, signal is only cleaned from voxels inside the mask.
       | If not, a mask is computed using
       | :func:`nilearn.masking.compute_brain_mask`.
     - compute

.. _preprocess_warping:

Warping or Transformation to other spaces
-----------------------------------------

``junifer`` can also warp or transform any supported
:ref:`data type <data_types>` from the template space provided by the dataset
(e.g., ``MNI152NLin6Asym``) to either  the subject's
:ref:`native space <preprocess_warping_native>` or to any other
:ref:`template space <preprocess_warping_template>`
(e.g., ``MNI152NLin2009cAsym``). This functionality is provided by
:class:`.SpaceWarper` and depends on external tools like FSL and / or ANTs.

.. _preprocess_warping_native:

Warping to subject's native space
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To warp to subject's native space, the dataset needs to provide ``T1w`` and
``Warp`` data types and the DataGrabber needs to at least have
``["BOLD", "T1w", "Warp"]`` (if you are warping ``BOLD``) as the ``types``
parameter's value.

The :class:`.SpaceWarper`'s ``reference`` parameter needs
to be set to ``T1w``, which means that the ``BOLD`` data will be transformed
using the ``T1w`` as reference (it's resampled internally to match the
resolution of the ``BOLD``).

The ``Warp`` data type provides the warp or transformation file (can be linear,
non-linear or linear + non-linear transform) for the purpose. For ``using``
parameter, you can pass either ``fsl`` or ``ants`` depending on the warp or
transformation file format. You can also provide ``auto`` to ``using`` in which
case either ``FSL`` or ``ANTs`` will be used based on the file format provided
by the DataGrabber. This also requires that both the tools are in the ``PATH``.

And finally, you would need to set the ``on`` parameter to ``BOLD`` to make it
clear which data type you intend to warp, as the :class:`.SpaceWarper` is also
capable of warping ``T1w``.

An example YAML might look like this:

.. code-block:: yaml

      preprocess:
         - kind: SpaceWarper
           using: fsl
           reference: T1w
           on: BOLD

.. _preprocess_warping_template:

Warping to other template space
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In a situation where your dataset might provide the ``BOLD`` data (or any other
data type that you want to work on) in ``MNI152NLin6Asym`` template space but
you would like to compute features in ``MNI152NLin2009cAsym`` template space,
you can also use the :class:`.SpaceWarper` by setting the ``reference``
parameter to the template space's name, in this case,
``reference: MNI152NLin2009cAsym``. The ``using`` parameter needs to be set
to ``ants`` as we need it to warp the data.

.. note::

   We only support template spaces provided by `templateflow`_ and the naming
   is similar except that we omit the ``tpl-`` prefix used by ``templateflow``.

For an YAML example:

.. code-block:: yaml

      preprocess:
         - kind: SpaceWarper
           using: ants
           reference: MNI152NLin2009cAsym
           on: BOLD
