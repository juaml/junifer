.. include:: ../links.inc

.. _specifying_dependencies:

Specifying Dependencies
=======================

This section describes how you can tackle different situations when writing
your custom Marker and / or Preprocessor and take care of the dependencies for
them.

You might have already come across listing out dependencies for your
:ref:`custom Markers <extending_markers>` and / or
:ref:`custom Preprocessors <extending_preprocessors>`, if not, check them out
first. If you have already gone through them, you are already familiar with using
class attribute ``_DEPENDENCIES`` to keep track of its dependencies. ``junifer``
is a bit more sophisticated about them and we will see here how you can make the
best use of them.

.. _component_dependencies:

Handling dependencies that come as Python packages
--------------------------------------------------

You have already seen this case handled by having a class attribute
``_DEPENDENCIES`` whose value is a set of all the package names that the
component depends on. For example, for :class:`.RSSETSMarker`, we have:

.. code-block:: python

    _DEPENDENCIES: ClassVar[Dependencies] = {"nilearn"}

The type annotation is for documentation and static type checking purposes.
Although not required, we highly recommend you use them, your future self
and others who use it will thank you.

.. _component_external_dependencies:

Handling external dependencies from toolboxes
---------------------------------------------

You can also specify dependencies of external toolboxes like AFNI, FSL and ANTs,
by having a class attribute like so:

.. code-block:: python

    _EXT_DEPENDENCIES: ClassVar[ExternalDependencies] = [
        {
            "name": "afni",
            "commands": ["3dReHo", "3dAFNItoNIFTI"],
        },
    ]

The above example is taken from the class which computes regional homogeneity
(ReHo) using AFNI. The general pattern is that you need to have the value of
``_EXT_DEPENDENCIES`` as a list of dictionary with two keys:

* ``name`` (str) : lowercased name of the toolbox
* ``commands`` (list of str) : actual names of the commands you need to use

This is simple but powerful as we will see in the following sub-sections.

.. _component_conditional_dependencies:

Handling conditional dependencies
---------------------------------

You might encounter situations where your Marker or Preprocessor needs to have
option for the user to either use a dependency that comes as a package or
use a dependency that relies on external toolboxes. With the foundation we laid
above, it is really simple to solve it while having validation before running
and letting the user know if some dependency is missing.

Let's look at an actual implementation, in this case :class:`.SpaceWarper`, so
that it shows the problem a bit better and how we solve it:

.. code-block:: python

    class SpaceWarper(BasePreprocessor):
        # docstring
        _CONDITIONAL_DEPENDENCIES: ClassVar[ConditionalDependencies] = [
            {
                "using": "fsl",
                "depends_on": FSLWarper,
            },
            {
                "using": "ants",
                "depends_on": ANTsWarper,
            },
            {
                "using": "auto",
                "depends_on": [FSLWarper, ANTsWarper],
            },
        ]

        def __init__(
            self, using: str, reference: str, on: Union[List[str], str]
        ) -> None:
            # validation and setting up
            ...


Here, you see a new class attribute ``_CONDITIONAL_DEPENDENCIES`` which is a
list of dictionaries with two keys:

* ``using`` (str) : lowercased name of the toolbox
* ``depends_on`` (object or list of objects) : a class or list of classes which \
  implements the particular tool's use

It is mandatory to have the ``using`` positional argument in the constructor in
this case as the validation starts with this and moves further. It is also
mandatory to only allow the value of ``using`` argument to be one of them
specified in the ``using`` key of ``_CONDITIONAL_DEPENDENCIES`` entries.

For some cases, like we have here, it might be worth to have ``"auto"`` for
``"using"`` which eases the choice of a particular tool by the user and
instead lets ``junifer`` do it automatically. In that case, ``"depends_on"``
needs to be a list of the tool implementation classes. This also requires the
user to have all the tools in the ``PATH``.

For brevity, we only show the ``FSLWarper`` here but ``ANTsWarper`` looks very
similar. ``FSLWarper`` looks like this (only the relevant part is shown here):

.. code-block:: python

    class FSLWarper:
        # docstring

        _EXT_DEPENDENCIES: ClassVar[ExternalDependencies] = [
            {
                "name": "fsl",
                "commands": ["flirt", "applywarp"],
            },
        ]

        _DEPENDENCIES: ClassVar[Dependencies] = {"numpy", "nibabel"}

        def preprocess(
            self,
            input: Dict[str, Any],
            extra_input: Dict[str, Any],
        ) -> Dict[str, Any]:
            # implementation
            ...

Here you can see the familiar ``_DEPENDENCIES`` and ``_EXT_DEPENDENCIES`` class
attributes. The validation process starts by looking up the ``using`` value of
the ``_CONDITIONAL_DEPENDENCIES`` entries and then retrieves the object pointed
by ``depends_on``. After that, the ``_DEPENDENCIES`` and ``_EXT_DEPENDENCIES``
class attributes are checked.

This might be a bit too much to get it right away so feel free to check the code
for a better understanding. You can also check ``ALFFBase`` for a Marker
having this pattern.
