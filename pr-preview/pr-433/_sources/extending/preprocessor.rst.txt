.. include:: ../links.inc

.. _extending_preprocessors:

Creating Preprocessors
======================

As already mentioned in the introduction, ``junifer`` does not do traditional
MRI pre-processing but can perform minimal preprocessing of the data that the
DataGrabber provides, for example, smoothing after confound regression or
transforming data to subject-native space before feature extraction. While
there are a few Preprocessors available already and we are constantly adding
new ones, you might need something specific and then you can create your
own Preprocessor.

While implementing your own Preprocessor, you need to always inherit from
:class:`.BasePreprocessor` and implement a few methods:

#. ``get_valid_inputs``: This method should return a list of strings
   representing the valid data types that the Preprocessor can work on.
   Check :ref:`data types <data_types>` for reference.
#. ``get_output_type``: This method should just return the input as it
   is unused as of now.
#. ``preprocess``: The method that given the data, preprocesses the data.
#. ``__init__``: The initialisation method, where the Preprocessor is
   configured.

As an example, we will develop a ``NilearnSmoothing`` Preprocessor, which
smoothens the data using :func:`nilearn.image.smooth_img`. This is often
desirable in cases where your data is preprocessed using ``fMRIPrep``, as
``fMRIPrep`` does not perform smoothing.

.. _extending_preprocessors_input_output:

Step 1: Configure input and output
----------------------------------

In this step, we define the input and output data types of the Preprocessor.
For input we can accept ``T1w``, ``T2w`` and ``BOLD``
:ref:`data types <data_types>`.

.. code-block:: python

    ...


    def get_valid_inputs(self) -> list[str]:
        return ["T1w", "T2w", "BOLD"]


    ...

The output definition of the Preprocessor is unused now but is kept for
completeness.

.. code-block:: python

    ...


    def get_output_type(self, input_type: str) -> str:
        return input_type


    ...

.. _extending_preprocessors_init:

Step 2: Initialise the Preprocessor
-----------------------------------

Now we need to define our Preprocessor class' constructor which is also how
you configure it. Our class will have the following arguments:

1. ``fwhm``: The smoothing strength as a full-width at half maximum
   (in millimetres). Since we depend on :func:`nilearn.image.smooth_img`, we
   pass the value to it.
2. ``on``: The data type we want the Preprocessor to work on. If the user does
   not specify, it will work on all the data types given by the
   ``get_valid_inputs`` function.

.. attention::

   Only basic types (*int*, *bool* and *str*), lists, tuples and dictionaries
   are allowed as parameters. This is because the parameters are stored in
   JSON format, and JSON only supports these types.

.. code-block:: python

    from typing import Literal

    from numpy.typing import ArrayLike


    ...


    def __init__(
        self,
        fwhm: int | float | ArrayLike | Literal["fast"] | None,
        on: str | list[str] | None = None,
    ) -> None:
        self.fwhm = fwhm
        super().__init__(on=on)


    ...

.. caution::

   Parameters of the Preprocessor must be stored as object attributes without
   using ``_`` as prefix. This is because any attribute that starts with ``_``
   will not be considered as a parameter and not stored as part of the metadata
   of the Preprocessor.

.. _extending_preprocessors_preprocess:

Step 3: Preprocess the data
---------------------------

Finally, we will write the actual logic of the Preprocessor. This method will
be called by ``junifer`` when needed, using the data provided by the
DataGrabber, as configured by the user. The method ``preprocess`` has two
arguments:

* ``input``: A dictionary with the data to be used by the Preprocessor. This
  will be the corresponding element in the :ref:`Data Object<data_object>`
  already indexed. Thus, the dictionary has at least two keys: ``data`` and
  ``path``. The first one contains the data, while the second one contains the
  path to the data. The dictionary can also contain other keys, depending on the
  data type.
* ``extra_input``: The rest of the :ref:`Data Object<data_object>`. This is
  useful if you want to use other data (e.g., ``Warp`` can be used to provide
  the transformation matrix file for transformation to subject-native space).

and it has two return values:

* First is the ``input`` dictionary with necessary data modified. Usually, you
  want to replace the ``input["data"]`` with the preprocessed data.
* Second is a dictionary just like ``input`` or ``extra_input`` but with only
  specific key-value pairs which you would like to pass down to the Markers.
  For example, if your Preprocessor computes some mask with the preprocessed
  data, you could pass it through this which would be added and available
  in the Marker step with the same key you pass here. Usually, you would
  want to pass ``None``.

.. code-block:: python

    from typing import Any

    from nilearn import image as nimg


    ...


    def preprocess(
        self,
        input: dict[str, Any],
        extra_input: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        input["data"] = nimg.smooth_img(imgs=input["data"], fwhm=self.fwhm)
        return input, None


    ...


Step 4: Finalise the Preprocessor
---------------------------------

Now we just need to combine everything we have above and throw in a couple of
other stuff to get our Preprocessor ready.

First, we specify the :ref:`dependencies <specifying_dependencies>` for our
class, which are basically the packages that are required by the class. This is
used for validation before running to ensure all the packages are installed and
also to keep track of the dependencies and their versions in the metadata. We
define it using a class attribute like so:

.. code-block:: python

    _DEPENDENCIES = {"nilearn"}

Then, we just need to register the Preprocessor using ``@register_preprocessor``
decorator and our final code should look like this:

.. code-block:: python

    from typing import Any, Literal

    from junifer.api.decorators import register_preprocessor
    from junifer.preprocess import BasePreprocessor

    from nilearn import image as nimg
    from numpy.typing import ArrayLike


    @register_preprocessor
    class NilearnSmoothing(BasePreprocessor):

        _DEPENDENCIES = {"nilearn"}

        def __init__(
            self,
            fwhm: int | float | ArrayLike | Literal["fast"] | None,
            on: str | list[str] | None = None,
        ) -> None:
            self.fwhm = fwhm
            super().__init__(on=on)

        def get_valid_inputs(self) -> list[str]:
            return ["T1w", "T2w", "BOLD"]

        def get_output_type(self, input_type: str) -> str:
            return input_type

        def preprocess(
            self,
            input: dict[str, Any],
            extra_input: dict[str, Any] | None = None,
        ) -> tuple[dict[str, Any], dict[str, Any] | None]:
            input["data"] = nimg.smooth_img(imgs=input["data"], fwhm=self.fwhm)
            return input, None


.. _extending_preprocessors_template:

Template for a custom Preprocessor
----------------------------------

.. code-block:: python

    from junifer.api.decorators import register_preprocessor
    from junifer.preprocess import BasePreprocessor


    @register_preprocessor
    class TemplatePreprocessor(BasePreprocessor):

        def __init__(self, on=None):
            # TODO: add preprocessor-specific parameters
            super().__init__(on=on)

        def get_valid_inputs(self):
            # TODO: Complete with the valid inputs
            valid = []
            return valid

        def get_output_type(self, input_type):
            return input_type

        def preprocess(self, input, extra_input):
            # TODO: add the preprocessor logic
            return input, None
