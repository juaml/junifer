.. include:: ../links.inc

.. _using_masks:

Masks
=====

Masks are essentially boolean arrays that are used to constrain the extraction
of features to voxels that are meaningful. For example, in an fMRI imaging
study, a mask can be used to constrain the extraction of features to voxels that
contain a certain ratio of gray matter to white matter / cerebrospinal fluid,
ensuring that the features are not extracted from voxels that contain mostly
white matter or cerebrospinal fluid, which could add noise to the BOLD signal.

``junifer`` provides a number of built-in masks, which can be listed using
:func:`.list_data` with ``kind="mask"``. Some masks are images, while other
masks can be computed using :ref:`nilearn` functions.

For markers and steps that accept ``masks`` as an argument, the mask can be
specified as a string, which will be the name of a built-in mask, or as a
dictionary in which the **only** key is the built-in mask name and the value is
a dictionary of keyword arguments to pass to the mask function.

For example, the following is a valid mask specification that specified the
``GM_prob0.2`` mask:

.. code-block:: yaml

    masks: GM_prob0.2

The following is a valid mask specification that specifies the
``compute_brain_mask`` mask, with a threshold of ``0.5``.

.. code-block:: yaml

    masks:
        compute_brain_mask:
            threshold: 0.5

Furthermore, junifer allows you to combine several masks using
:func:`nilearn.masking.intersect_masks`. This is done by specifying a list of
masks, where each mask is a string or dictionary as described above. For example,
the following is a valid mask specification that specifies the intersection of
the ``GM_prob0.2`` and ``compute_brain_mask`` masks.

.. code-block:: yaml

    masks:
        - GM_prob0.2
        - compute_brain_mask:
            threshold: 0.5

We can also specify the arguments of :func:`nilearn.masking.intersect_masks`
(``threshold`` and ``connected``). The following example combines the same masks
as the previous one, but computing the full intersection.

.. code-block:: yaml

    masks:
        - GM_prob0.2
        - compute_brain_mask:
            threshold: 0.5
        - threshold: 1  # intersection

Alternatively, we can also compute the union, even if the voxels do not form a
connected component:

.. code-block:: yaml

    masks:
        - GM_prob0.2
        - compute_brain_mask:
            threshold: 0.5
        - threshold: 0  # union
        - connected: False  # keep disconnected components
