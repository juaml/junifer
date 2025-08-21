.. include:: ../links.inc

.. _adding_maps:

Adding Maps
===========

Maps in ``junifer`` are basically probabilistic atlases. They are differentiated
from parcellations for ease of computation and to handle edge cases in a sane manner.
Before you start adding your own maps, check whether ``junifer`` has
the map(s) :ref:`in-built already <builtin>`. Perhaps, what is available
there will suffice to achieve your goals. However, of course ``junifer`` will not
have every map(s) available that you may want to use, and if so, it will
be nice to be able to add it yourself using a format that ``junifer`` understands.

Similarly, you may even be interested in creating your own custom maps
and then adding them to ``junifer``, so you can use ``junifer`` to obtain
different Markers to assess and validate your own maps. So, how can you do
this?

Since both of these use-cases are quite common, and not being able to use your
favourite map(s) is of course quite a buzzkill, ``junifer`` actually
provides the easy-to-use :func:`.register_data` function to do just that.
Let's try to understand the API reference and then use this function to register our
own map(s).

From the API reference, we can see that it has 3 positional arguments:

* ``kind``
* ``name``
* ``space``

as well as one optional keyword argument: ``overwrite``.
As the ``kind`` needs to be ``"maps"``, we can check
``MapsRegistry.register`` for keyword arguments to be passed:

* ``maps_path``
* ``maps_labels``

The ``name`` of the map(s) is up to you and will be the name that
``junifer`` will use to refer to this particular maps. You can think of
this as being similar to a key in a Python dictionary, i.e. a key that is used to
obtain and operate on the actual maps data. This ``name`` must always
be a string. For example, we could call our map(s)
``"my_custom_maps"`` (Note, that in a real-world use case this is
likely not a good name, and you should try to choose a meaningful name that
conveys as much relevant information about your maps as necessary).

The ``maps_path`` must be a ``str`` or ``Path`` object indicating a
path to a valid 4D NIfTI image, which contains floating-point labels indicating the
individual regions-of-interest (ROIs) of your map(s).

We also want to make sure that we can associate each label with
a human readable name (i.e. the name for each ROI). This serves naming the
features that maps-based markers produce in an unambiguous way, such
that a user can easily identify which ROIs were used to produce a specific
feature (multiple ROIs, because some features consist of information from two
or more ROIs, as for example in functional connectivity). Therefore, we provide
junifer with a list of strings, that contains the names for each ROI. In this
list, the label at the i-th position indicates the i-th index in the 4th dimension
of the NIfTI image.

Lastly, we specify the ``space`` that the map(s) is in, for example,
``"MNI152NLin6Asym"`` or ``"native"`` (scanner-native space).

Step 1: Prepare code to register a maps
---------------------------------------

Now we know everything that we need to know to make sure ``junifer`` can use our
own map(s) to compute any maps-based Marker. A simple example could
look like this:

.. code-block:: python

  from pathlib import Path

  import numpy as np
  from junifer.data import register_data


  # these are of course just example paths, replace it with your own:
  path_to_maps = (
      Path.cwd() / "my_custom_maps.nii.gz"
  )
  path_to_labels = (
      Path.cwd() / "my_custom_maps_labels.txt"
  )

  my_labels = list(np.loadtxt(path_to_labels, dtype=str))

  register_data(
      kind="maps",
      name="my_custom_maps",
      maps_path=path_to_maps,
      maps_labels=my_labels,
      space="MNI152NLin6Asym",
  )

We can run this code and it seems to work, however, how can we actually
include the custom map(s) in a ``junifer`` pipeline using a
:ref:`code-less YAML configuration <codeless>`?

Step 2: Add maps registration to the YAML file
----------------------------------------------

In order to use the maps in a ``junifer`` pipeline configured by a YAML
file, we can save the above code in a Python file, say
``registering_my_maps.py``. We can then simply add this file using the
``with`` keyword provided by ``junifer``:

.. code-block:: yaml

  with:
    - registering_my_maps.py

Afterwards continue configuring the rest of the pipeline in this YAML file, and
you will be able to use this maps using the name you gave the
maps when registering it. For example, we can add a
:class:`.MapsAggregation` Marker to demonstrate how this can be done:

.. code-block:: yaml

  markers:
    - name: CustomMaps_mean
      kind: MapsAggregation
      maps: my_custom_maps

Now, you can simply use this YAML file to run your pipeline.

.. important::

   It's important to keep in mind that if the paths given in
   ``registering_my_maps.py`` are relative paths, they will be interpreted
   by ``junifer`` as relative to the jobs directory (i.e. where ``junifer`` will
   create submit files, logs directory and so on). For simplicity, you may just
   want to use absolute paths to avoid confusion, yet using relative paths is
   likely a better way to make your pipeline directory / repository more portable
   and therefore more reproducible for others. Really, once you understand how
   these paths are interpreted by ``junifer``, it is quite easy.
