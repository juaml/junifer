.. include:: ../links.inc

.. _extending_extension:

Creating a ``junifer`` extension
================================

``junifer`` is designed to be easily extensible. Through the use of a registry
and decorators, you can easily add new functionality to ``junifer`` during
runtime. This is done by creating a new Python module and importing it before
running ``junifer``.

A special consideration has to be made when using the
:ref:`code-less configuration<codeless>`. In this case, the
``with`` statement can be used to import a module or run a Python file.

In the following example, we instruct ``junifer`` to first import ``my_module``
and then run the ``my_file.py`` file:

.. code-block:: yaml

    with:
      - my_module
      - my_file.py

Thus, the code from ``my_file.py`` will be executed before running ``junifer``.
This is the ideal place to include ``junifer`` extensions.

.. important::

   Some ``junifer`` commands will not consider files imported from files
   included in the ``with`` statement, unless this is known to junifer. If
   ``my_file.py`` imports ``my_other_file.py``, the ``run`` command will work,
   but ``queue`` will not create a proper job. This is because we need to
   let junifer know that ``my_other_file.py`` is also part of the code. To do
   so, we need to include a special function in ``my_file.py`` which tells
   ``junifer`` about the dependencies of the module:

   .. code-block:: python

      def junifer_module_deps() -> List[str]:
          """Return the dependencies of the module.

          Returns
          -------
          list of str
              The list of dependencies.

          """

          return ["my_other_file.py"]
