.. include:: ../links.inc

.. _extending_markers:

Creating Markers
================

Computing a marker (a.k.a. *feature(s)*) is the main goal of ``junifer``. While
we aim to provide as many Markers as possible, it might be the case that the
Marker you are looking for is not available. In this case, you can create your
own Marker by following this tutorial.

Most of the functionality of a ``junifer`` Marker has been taken care by the
:class:`.BaseMarker` class. Thus, only a few methods and class attributes are
required:

#. ``__init__``: The initialisation method, where the Marker is configured.
#. ``compute``: The method that given the data, computes the Marker.

As an example, we will develop a ``ParcelMean`` Marker, a Marker that first
applies a parcellation and then computes the mean of the data in each parcel.
This is a very simple example, but it will show you how to create a new Marker.

.. _extending_markers_input_output:

Step 1: Configure input and output
----------------------------------

This step is quite simple: we need to define the input and output of the Marker.
Based on the current :ref:`data types <data_types>`, we can have ``BOLD``,
``VBM_WM`` and ``VBM_GM`` as valid inputs. The output of the Marker depends on
the input. For ``BOLD``, it will be ``timeseries``, while for the rest of the
inputs, it will be ``vector``. Thus, we have a class attribute like so:

.. code-block:: python

    # NOTE: data type -> feature -> storage type
    # You can have multiple features for one data type,
    # each feature having same or different storage type
    _MARKER_INOUT_MAPPINGS = {
        "BOLD": {
            "parcel_mean": "timeseries",
        },
        "VBM_WM": {
            "parcel_mean": "vector",
        },
        "VBM_GM": {
            "parcel_mean": "vector",
        },
    }

.. _extending_markers_init:

Step 2: Initialise the Marker
-----------------------------

In this step we need to define the parameters of the Marker the user can provide
to configure how the Marker will behave.

The parameters of the Marker are defined in the ``__init__`` method. The
:class:`.BaseMarker` class requires two optional parameters:

1. ``name``: the name of the Marker. This is used to identify the Marker in the
   configuration file.
2. ``on``: a list or string with the data types that the Marker will be applied
   to.

.. attention::

   Only basic types (*int*, *bool* and *str*), lists, tuples and dictionaries
   are allowed as parameters. This is because the parameters are stored in
   JSON format, and JSON only supports these types.

In this example, only parameter required for the computation is the name of the
parcellation to use. Thus, we can define the ``__init__`` method as follows:

.. code-block:: python

    def __init__(
        self,
        parcellation: str,
        on: str | list[str] | None = None,
        name: str | None = None,
    ) -> None:
        self.parcellation = parcellation
        super().__init__(on=on, name=name)

.. caution::

   Parameters of the Marker must be stored as object attributes without using
   ``_`` as prefix. This is because any attribute that starts with ``_`` will
   not be considered as a parameter and not stored as part of the metadata of
   the Marker.

.. _extending_markers_compute:

Step 3: Compute the Marker
--------------------------

In this step, we will define the method that computes the Marker. This method
will be called by ``junifer`` when needed, using the data provided by the
DataGrabber, as configured by the user. The method ``compute`` has two
arguments:

* ``input``: a dictionary with the data to be used to compute the Marker. This
  will be the corresponding element in the :ref:`Data Object<data_object>`
  already indexed. Thus, the dictionary has at least two keys: ``data`` and
  ``path``. The first one contains the data, while the second one contains the
  path to the data. The dictionary can also contain other keys, depending on the
  data type.
* ``extra_input``: the rest of the :ref:`Data Object<data_object>`. This is
  useful if you want to use other data to compute the Marker.

Following the example, we will compute the mean of the data in each parcel using
:class:`nilearn.maskers.NiftiLabelsMasker`. Importantly, the output of the
compute function must be a dictionary. This dictionary will later be passed onto
the ``store`` method. The dictionary's first level of keys would the feature name
and the values would be a dictionary of storage type specific key-value pairs.

.. hint::

   To simplify the ``store`` method, define keys of the dictionary based on the
   corresponding store functions in the :ref:`storage types <storage_types>`.
   For example, if the output is a ``vector``, the keys of the dictionary should
   be ``data`` and ``col_names``.

.. code-block:: python

    from typing import Any

    from junifer.data import get_parcellation
    from nilearn.maskers import NiftiLabelsMasker


    def compute(
        self,
        input: dict[str, Any],
        extra_input: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Get the data
        data = input["data"]

        # Get the parcellation tailored for the target
        t_parcellation, t_labels, _ = get_parcellation(
            name=self.parcellation_name,
            target_data=input,
            extra_input=extra_input,
        )

        # Create a masker
        masker = NiftiLabelsMasker(
            labels_img=t_parcellation,
            standardize=True,
            memory="nilearn_cache",
            verbose=5,
        )

        # mask the data
        out_values = masker.fit_transform([data])

        # Create and return the output dictionary
        return {
            "parcel_mean": {
                "data": out_values,
                "col_names": t_labels,
            },
        }

.. _extending_markers_finalize:

Step 4: Finalise the Marker
---------------------------

Once all of the above steps are done, we just need to give our Marker a name,
state its *dependencies* and register it using the ``@register_marker``
decorator.

The :ref:`dependencies <specifying_dependencies>` are the core packages that are
required to compute the Marker. This will be later used to keep track of the
versions of the packages used to compute the Marker. To inform ``junifer``
about the dependencies of a Marker, we need to define a ``_DEPENDENCIES``
attribute in the class. This attribute must be a set, with the names of the
packages as strings. For example, the ``ParcelMean`` marker has the
following dependencies:

.. code-block:: python

    _DEPENDENCIES = {"nilearn", "numpy"}

Finally, we need to register the Marker using the ``@register_marker`` decorator.

.. code-block:: python

    from typing import Any, ClassVar

    from junifer.api.decorators import register_marker
    from junifer.data import get_parcellation
    from junifer.markers import BaseMarker
    from junifer.typing import Dependencies, MarkerInOutMappings
    from nilearn.maskers import NiftiLabelsMasker


    @register_marker
    class ParcelMean(BaseMarker):

        _DEPENDENCIES: ClassVar[Dependencies] = {"nilearn", "numpy"}

        _MARKER_INOUT_MAPPINGS: ClassVar[MarkerInOutMappings] = {
            "BOLD": {
                "parcel_mean": "timeseries",
            },
            "VBM_WM": {
                "parcel_mean": "vector",
            },
            "VBM_GM": {
                "parcel_mean": "vector",
            },
        }

        def __init__(
            self,
            parcellation: str,
            on: str | list[str] | None = None,
            name: str | None = None,
        ) -> None:
            self.parcellation = parcellation
            super().__init__(on=on, name=name)

        def compute(
            self,
            input: dict[str, Any],
            extra_input: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            # Get the data
            data = input["data"]

            # Get the parcellation tailored for the target
            t_parcellation, t_labels, _ = get_parcellation(
                name=self.parcellation_name,
                target_data=input,
                extra_input=extra_input,
            )

            # Create a masker
            masker = NiftiLabelsMasker(
                labels_img=t_parcellation,
                standardize=True,
                memory="nilearn_cache",
                verbose=5,
            )

            # mask the data
            out_values = masker.fit_transform([data])

            # Create and return the output dictionary
            return {
                "parcel_mean": {
                    "data": out_values,
                    "col_names": t_labels,
                },
            }

.. _extending_markers_template:

Template for a custom Marker
----------------------------

.. code-block:: python

    from junifer.api.decorators import register_marker
    from junifer.markers import BaseMarker


    @register_marker
    class TemplateMarker(BaseMarker):

        # TODO: add the dependencies
        _DEPENDENCIES = {}

        # TODO: add the input-output mappings
        _MARKER_INOUT_MAPPINGS = {}

        def __init__(self, on=None, name=None):
            # TODO: add marker-specific parameters
            super().__init__(on=on, name=name)

        def compute(self, input, extra_input):
            # TODO: compute the marker and create the output dictionary
