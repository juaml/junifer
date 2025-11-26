.. include:: ../links.inc

.. _adding_coordinates:

Adding Coordinates
==================

Instead of using whole-brain parcellations to aggregate voxel-wise signals from
MR images (as for example in the :class:`.ParcelAggregation` marker), ``junifer``
allows you to specify a set of coordinates around which to draw spheres to
aggregate (for example using the :class:`.SphereAggregation` marker) the MR
signals from individual voxels. Now, before you start specifying your own sets
of coordinates, check the coordinates that ``junifer`` already has
:ref:`built in <builtin>`. If you simply want to use a well known set of
coordinates from the literature, there is a reasonable chance, that ``junifer``
provides them already.

If you checked the in-built coordinates, and they are not there already (for
example if you came up with your own set of coordinates), then ``junifer``
provides an easy way for you to register them using the
:func:`.register_data` function, so you can use your own set of
coordinates within a ``junifer`` pipeline.

From the API reference, we can see that it has 3 positional arguments:

* ``kind``
* ``name``
* ``space``

as well as one optional keyword argument: ``overwrite``.
As the ``kind`` needs to be ``"coordinates"``, we can check
``CoordinatesRegistry.register`` for keyword arguments to be passed:

* ``coordinates``
* ``voi_names``

The ``name`` argument takes a string indicating the name you want to give to
this set of coordinates. This ``name`` can be used to obtain and operate on a
set of coordinates in ``junifer``. For example, you can obtain your coordinates
after registration by providing ``name`` to :func:`.load_data` with
``kind="coordinates"``. We could simply call it ``"my_set_of_coordinates"``,
but likely you want a more descriptive and more informative name most of the time.

The ``coordinates`` argument takes the actual coordinates as a 2-dimensional
:class:`numpy.ndarray`. It contains one row for every location, and three
columns (one for each spatial dimension). That is, the first, second, and third
columns indicate the x-, y-, and z-coordinates in MNI space respectively.
The number of rows in the array correspond to the number of coordinates that
belong to this set.

The ``voi_names`` argument takes a list of strings
indicating the names of each coordinate (i.e. volume-of-interest) in the
``coordinates`` array. Therefore, the length of this list should correspond to
the number of rows in the coordinates array. Now, we know everything we need to
know to register a set of coordinates.

Lastly, we specify the ``space`` that the coordinates are in, for example,
``"MNI"`` or ``"native"`` (scanner-native space).

Step 1: Prepare code to register a set of coordinates
-----------------------------------------------------

Let's make a simple script to register our coordinates. We could simply call it
``register_custom_coordinates.py``. We may start by importing the appropriate
packages:

.. code-block:: python

  import numpy as np
  from junifer.data import register_data

For the sake of this example, we can create a set of coordinates that belong
to the Default Mode Network (DMN), and register this set of coordinates with
``junifer``. Note, that ``junifer`` already has a
:ref:`set of coordinates built-in <builtin>` ("DMNBuckner") that is associated
with the DMN. Here, we use the DMN coordinates used in a
`nilearn example <https://nilearn.github.io/dev/auto_examples/03_connectivity/plot_sphere_based_connectome.html>`_.

.. code-block:: python

  dmn_coords = np.array(
      [[0, -52, 18], [-46, -68, 32], [46, -68, 32], [1, 50, -5]]
  )
  voi_names = [
      "Posterior Cingulate Cortex",
      "Left Temporoparietal junction",
      "Right Temporoparietal junction",
      "Medial prefrontal cortex",
  ]

As you can see, we have four rows, and therefore four locations in the brain
associated with this set of coordinates. The variable ``voi_names`` reflects this
as it contains four strings indicating the name of each location. We can now
simply use this to register our coordinates:

.. code-block:: python

  register_data(
      kind="coordinates",
      name="DMNCustom",
      coordinates=dmn_coords,
      voi_names=voi_names,
      space="MNI",
  )

Now, when we run this script, ``junifer`` registers these coordinates and we can
use them in subsequent analyses. Let's now consider how to use coordinate
registration in combination with
:ref:`codeless configuration using a YAML file <codeless>`.

Step 2: Add coordinate registration to the YAML file
----------------------------------------------------

In order to register your coordinates for a pipeline configured by a YAML file,
you can use the ``with`` keyword provided by ``junifer``:

.. code-block:: yaml

  with:
    - register_custom_coordinates.py

Afterwards continue configuring the rest of your pipeline in this YAML file,
and you will be able to use this set of coordinates using the name you gave it
during registration (in our example "DMNCustom"). We can add a
:class:`.SphereAggregation` to demonstrate how this can be done:

.. code-block:: yaml

  markers:
    - name: DMNCustom_mean
      kind: SphereAggregation
      coords: DMNCustom
      radius: 5
      method: mean

This will aggregate signals from a sphere around each of our coordinates with a
radius of 5mm.
