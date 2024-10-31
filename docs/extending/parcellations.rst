.. include:: ../links.inc

.. _adding_parcellations:

Adding Parcellations
====================

Before you start adding your own parcellations, check whether ``junifer`` has
the parcellation :ref:`in-built already <builtin>`. Perhaps, what is available
there will suffice to achieve your goals. However, of course ``junifer`` will not
have every parcellation available that you may want to use, and if so, it will
be nice to be able to add it yourself using a format that ``junifer`` understands.
Similarly, you may even be interested in creating your own custom parcellations
and then adding them to ``junifer``, so you can use ``junifer`` to obtain
different Markers to assess and validate your own parcellation. So, how can you do
this?

Since both of these use-cases are quite common, and not being able to use your
favourite parcellation is of course quite a buzzkill, ``junifer`` actually
provides the easy-to-use :func:`.register_data` function to do just that.
Let's try to understand the API reference and then use this function to register our
own parcellation.

From the API reference, we can see that it has 3 positional arguments:

* ``kind``
* ``name``
* ``space``

as well as one optional keyword argument: ``overwrite``.
As the ``kind`` needs to be ``"parcellation"``, we can check
``ParcellationRegistry.register`` for keyword arguments to be passed:

* ``parcellation_path``
* ``parcels_labels``

The ``name`` of the parcellation is up to you and will be the name that
``junifer`` will use to refer to this particular parcellation. You can think of
this as being similar to a key in a Python dictionary, i.e. a key that is used to
obtain and operate on the actual parcellation data. This ``name`` must always
be a string. For example, we could call our parcellation
``"my_custom_parcellation"`` (Note, that in a real-world use case this is
likely not a good name, and you should try to choose a meaningful name that
conveys as much relevant information about your parcellation as necessary).

The ``parcellation_path`` must be a ``str`` or ``Path`` object indicating a
path to a valid NIfTI image, which contains integer labels indicating the
individual regions-of-interest (ROIs) of your parcellation. The background in
this parcellation should be indicated by 0, and the labels of ROIs should go
from 1 to N (where N is the total number of ROIs in your parcellation). Now,
we nearly have everything we need.

We also want to make sure that we can associate each integer label with
a human readable name (i.e. the name for each ROI). This serves naming the
features that parcellation-based markers produce in an unambiguous way, such
that a user can easily identify which ROIs were used to produce a specific
feature (multiple ROIs, because some features consist of information from two
or more ROIs, as for example in functional connectivity). Therefore, we provide
junifer with a list of strings, that contains the names for each ROI. In this
list, the label at the i-th position indicates the i-th integer label (i.e. the
first label in this list corresponds to the first integer label in the
parcellation and so on).

Lastly, we specify the ``space`` that the parcellation is in, for example,
``"MNI152NLin2009cAsym"`` or ``"native"`` (scanner-native space).

Step 1: Prepare code to register a parcellation
-----------------------------------------------

Now we know everything that we need to know to make sure ``junifer`` can use our
own parcellation to compute any parcellation-based Marker. A simple example could
look like this:

.. code-block:: python

  from pathlib import Path

  import numpy as np
  from junifer.data import register_data


  # these are of course just example paths, replace it with your own:
  path_to_parcellation = (
      Path("..") / ".." / "parcellations" / "my_custom_parcellation.nii.gz"
  )
  path_to_labels = (
      Path("..") / ".." / "labels" / "my_custom_parcellation_labels.txt"
  )

  my_labels = list(np.loadtxt(path_to_labels, dtype=str))

  register_data(
      kind="parcellation",
      name="my_custom_parcellation",
      parcellation_path=path_to_parcellation,
      parcels_labels=my_labels,
      space="MNI152NLin2009cAsym",
  )

We can run this code and it seems to work, however, how can we actually
include the custom parcellation in a ``junifer`` pipeline using a
:ref:`code-less YAML configuration <codeless>`?

Step 2: Add parcellation registration to the YAML file
------------------------------------------------------

In order to use the parcellation in a ``junifer`` pipeline configured by a YAML
file, we can save the above code in a Python file, say
``registering_my_parcellation.py``. We can then simply add this file using the
``with`` keyword provided by ``junifer``:

.. code-block:: yaml

  with:
    - registering_my_parcellation.py

Afterwards continue configuring the rest of the pipeline in this YAML file, and
you will be able to use this parcellation using the name you gave the
parcellation when registering it. For example, we can add a
:class:`.ParcelAggregation` Marker to demonstrate how this can be done:

.. code-block:: yaml

  markers:
    - name: CustomParcellation_mean
      kind: ParcelAggregation
      parcellation: my_custom_parcellation
      method: mean

Now, you can simply use this YAML file to run your pipeline.

.. important::

   It's important to keep in mind that if the paths given in
   ``registering_my_parcellation.py`` are relative paths, they will be interpreted
   by ``junifer`` as relative to the jobs directory (i.e. where ``junifer`` will
   create submit files, logs directory and so on). For simplicity, you may just
   want to use absolute paths to avoid confusion, yet using relative paths is
   likely a better way to make your pipeline directory / repository more portable
   and therefore more reproducible for others. Really, once you understand how
   these paths are interpreted by ``junifer``, it is quite easy.
