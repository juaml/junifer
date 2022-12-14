.. include:: ../links.inc

.. _extending_markers:

Creating Markers
================

Computing a marker (a.k.a. *feature*) is the main goal of junifer. While we aim to provide as many markers as possible,
it might be the case that the marker you are looking for is not available. In this case, you can create your own marker
by following this tutorial.

Most of the functionality of a junifer marker has been taken care by the :class:`junifer.markers.BaseMarker` class. 
Thus, only a few methods are required:

1. ``get_valid_inputs``: a method to obtain the list of valid inputs for the marker. This is used to check that the
   inputs provided by the user are valid. This method should return a list of strings, representing 
   :ref:`data types <data_types>`
2. ``get_output_type``: a method to obtain the kind of output of the marker. This is used to check that the output
   of the marker is compatible with the storage. This method should return a string, representing 
   :ref:`storage types <storage_types>`
3. ``compute``: the method that given the data, computes the marker.
4. ``__init__``: the initialization method, where the marker is configured.

As an example, we will develop a Parcel Mean marker, that is, a marker that first applies a parcellation and
then computes the mean of the data in each parcel. This is a very simple example, but it will show you how to create
a new marker.

.. _extending_markers_input_output:

Step 1: Configure input and output
----------------------------------

This step is quite simple: we need to define the input and output of the marker. Based on the current
:ref:`data types <data_types>`, we can define as valid inputs ``BOLD``, ``VBM_WM`` and ``VBM_GM``.

.. code-block:: python

    def get_valid_inputs(self):
        return ['BOLD', 'VBM_WM', 'VBM_GM']

The output of the marker depends on the input. For ``BOLD``, it will be ``timeseries``, while for the rest of the inputs,
it will be ``table``. Thus, we can define the output as:

.. code-block:: python

    def get_output_type(self, input_kind):
        if input_kind == 'BOLD':
            return 'timeseries'
        else:
            return 'table'

.. _extending_markers_init:

Step 2: Initialize the marker
-----------------------------

In this step we need to define the parameters of the marker. That is, all the parameters that the user can provide
to configure how the marker will behave.

The parameters of the marker are defined in the ``__init__`` method. The :class:`junifer.markers.BaseMarker` class
requires two optional parameters:

1. ``name``: the name of the marker. This is used to identify the marker in the configuration file.
2. ``on``: a list or string with the data types that the marker will be applied to.

.. attention:: Only basic types (*int*, *bool* and *str*) as well as Lists, Tuples and Dictionaries are allowed as
               parameters. This is because the parameters are stored in a JSON file, and JSON only supports these types.


In this example, the is only paramater required for the computation is the name of the parcellation to use. Thus, we can
define the ``__init__`` method as follows:

.. code-block:: python
    
    def __init__(self, parcellation_name, on=None, name=None):
        self.parcellation_name = parcellation_name
        super().__init__(on=on, name=name)

.. caution:: Parameters of the marker must be stored as object attributes without using ``_`` as prefix. This is
             because any attribute that starts with ``_`` will not be considered as a parameter and not stored as 
             part of the metadata of the marker.


.. _extending_markers_compute:

Step 3: Compute the marker
--------------------------

In this step, we will define the method that computes the marker. This method will be called by junifer when needed,
using the data provided by the datagrabber, as configured by the user. The function ``compute`` has two arguments:

* ``input``: a dictionary with the data to be used to compute the marker. This will be the corresponding element in the 
  :ref:`Data Object<data_object>` alredy indexing. Thus, the dictionary has at least two keys: ``data`` and ``path``.
  The first one contains the data, while the second one contains the path to the data. The dictionary can also contain
  other keys, depending on the data type.
* ``extra_input``: the rest of the :ref:`Data Object<data_object>`. This is useful if you want to use other data to
  compute the marker (e.g.: ``BOLD_confounds`` can be used to de-confound the ``BOLD`` data).

Following the example, we will compute the mean of the data in each parcel using
:class:`nilearn.maskers.NiftiLabelsMasker`. Importantly, the output of the compute function must be a dictionary.
This dictionary will later be passed onto the ``store`` method.

.. hint:: To simplify the ``store`` method, define keys of the dictionary based on the corresponding store functions
          in the :ref:`storage types <storage_types>`. For example, if the output is a ``table``, the keys of the
          dictionary should be ``data`` and ``columns``.

.. code-block:: python

    from nilearn.maskers import NiftiLabelsMasker
    from junifer.data import load_parcellation

    def compute(self, input, extra_input):
        # Get the data
        data = input["data"]

        # Get the min of the voxels sizes and use it as the resolution
        resolution = np.min(data.header.get_zooms()[:3])

        # Load the parcellation
        t_parcellation, t_labels, _ = load_parcellation(
            name=self.parcellation_name,
            resolution=resolution,
        )

        # Create a masker
        masker = NiftiLabelsMasker(
            labels_img=t_parcellation,
            standardize=True,
            memory='nilearn_cache',
            verbose=5,
        )

        # mask the data
        out_values = masker.fit_transform([data])

        # Create the output dictionary
        out = {"data": out_values, "columns": t_labels}

        # If its 3D (BOLD), name each row as "scan"
        if out_values.shape[0] > 1:
            out["row_names"] = "scan"
        return out


.. _extending_markers_finalize:

Step 4: Finalize the marker
---------------------------

Once all of the above steps are done, we just need to give our marker a name, state its *dependencies* and register it
using the ``@register_marker`` decorator.

The *dependencies* are the core packages that are required to compute the marker. This will be later used to keep track
of the versions of the packages used to compute the marker. To inform junifer about the dependencies of a marker,
we need to define a ``_DEPENDENCIES`` attribute in the class. This attribute must be a set, with the names of the
packages as strings. For example, the ``ParcelMean`` marker has the following dependencies:

.. code-block:: python

    _DEPENDENCIES = {"nilearn"}

Finally, we need to register the marker using the ``@register_marker`` decorator. This decorator takes the name of the

.. code-block:: python

    from nilearn.maskers import NiftiLabelsMasker
    from junifer.data import load_parcellation
    from junifer.api.decorators import register_marker
    from junifer.markers.base import BaseMarker

    @register_marker
    class ParcelMean(BaseMarker):

         _DEPENDENCIES = {"nilearn", "numpy"}

        def __init__(self, parcellation_name, on=None, name=None):
            self.parcellation_name = parcellation_name
            super().__init__(on=on, name=name)
        
        def get_valid_inputs(self):
            return ['BOLD', 'VBM_WM', 'VBM_GM']

        def get_output_type(self, input_kind):
            if input_kind == 'BOLD':
                return 'timeseries'
            else:
                return 'table'

        def compute(self, input, extra_input):
            # Get the data
            data = input["data"]

            # Get the min of the voxels sizes and use it as the resolution
            resolution = np.min(data.header.get_zooms()[:3])

            # Load the parcellation
            t_parcellation, t_labels, _ = load_parcellation(
                name=self.parcellation_name,
                resolution=resolution,
            )

            # Create a masker
            masker = NiftiLabelsMasker(
                labels_img=t_parcellation,
                standardize=True,
                memory='nilearn_cache',
                verbose=5,
            )

            # mask the data
            out_values = masker.fit_transform([data])

            # Create the output dictionary
            out = {"data": out_values, "columns": t_labels}

            # If its 3D (BOLD), name each row as "scan"
            if out_values.shape[0] > 1:
                out["row_names"] = "scan"
            return out


.. _extending_markers_template:

Template for a custom Marker
----------------------------

.. code-block:: python

    from junifer.api.decorators import register_marker
    from junifer.markers.base import BaseMarker

    @register_marker
    class TemplateMarker(BaseMarker):

        def __init__(self, on=None, name=None):
            # TODO: add marker-specific parameters
            super().__init__(on=on, name=name)
        
        def get_valid_inputs(self):
            # TODO: Complete with the valid inputs
            valid = []
            return valid

        def get_output_type(self, input_kind):
            # TODO: Return the valid output kind for each input kind
            pass

        def compute(self, input, extra_input):
            # TODO: compute the marker and create the output dictionary

            # Create the output dictionary
            out = {"data": None, "columns": None}
            return out
