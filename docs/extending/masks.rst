.. include:: ../links.inc

.. _adding_masks:

Adding Masks
============

Many processing steps and Markers in ``junifer`` allow you to specify a binary
mask to select voxels you want to include in the analysis. There are a number
of masks :ref:`in-built in junifer already <builtin>`, so check if any of them
suit your needs. Check how to use these masks :ref:`here <using_masks>`. Once
you know how to use these masks, and you checked whether the in-built masks
suit your needs, and you have found that they don't, you can come back here to
learn how to use your own masks.

The principle is fairly simple and quite similar to :ref:`adding_parcellations`
and :ref:`adding_coordinates`. ``junifer`` provides a :func:`.register_data`
function that lets you register your own custom masks. It consists of three
positional arguments:

* ``kind``
* ``name``
* ``space``

and one optional keyword argument: ``overwrite``.
As the ``kind`` needs to be ``"mask"``, we can check
``MaskRegistry.register`` for keyword arguments to be passed:

* ``mask_path``

The ``name`` argument is a string indicating the name of the mask. This name
is used to refer to that mask in ``junifer`` internally in order to obtain the
actual mask data and perform operations on it. For example, using the name you
can load a mask after registration using the :func:`.load_data` with
``kind="mask"``.

The ``mask_path`` should contain the path to a valid NIfTI image with binary
voxel values (i.e. 0 or 1). This data can then be used by ``junifer`` to mask
other MR images.

Lastly, we specify the ``space`` that the coordinates are in, for example,
``"MNI152NLin6Asym"`` or ``"native"`` (scanner-native space).

Step 1: Prepare code to register a mask
---------------------------------------

A simple script called ``register_custom_mask.py`` to register a mask could
look as follows:

.. code-block:: python

  from pathlib import Path

  from junifer.data import register_data


  # this path is only an example, of course use the correct path
  # on your system:
  mask_path = Path("..") / ".." / "my_custom_mask.nii.gz"

  register_data(
      kind="mask",
      name="my_custom_mask",
      mask_path=mask_path,
      space="native",
  )

Simple, right? Now we just have to configure a YAML file to register this mask
so we can use it for :ref:`codeless configuration of junifer <codeless>`.

Step 2: Configure a YAML file for registration of a mask
--------------------------------------------------------

In order to do this, we can use the ``with`` keyword provided by ``junifer``:

.. code-block:: yaml

  with:
    - register_custom_mask.py

Then we can use this mask for any processing step or Marker that takes in a
mask as an argument. For example:

.. code-block:: yaml

  markers:
    - name: CustomMaskParcelAggregation_mean
      kind: ParcelAggregation
      parcellation: Schaefer200x17
      method: mean
      masks: "my_custom_mask"

Now, you can simply use this YAML file to run your pipeline.

.. important::

   It's important to keep in mind that if the paths given in
   ``register_custom_mask.py`` are relative paths, they will be interpreted
   by junifer as relative to the jobs directory (i.e. where ``junifer`` will
   create submit files, logs directory and so on). For simplicity, you may just
   want to use absolute paths to avoid confusion, yet using relative paths is
   likely a better way to make your pipeline directory / repository more portable
   and therefore more reproducible for others. Really, once you understand how
   paths are interpreted by ``junifer``, it is quite easy.
