.. include:: ../links.inc

.. _extending_extension:

Creating a junifer extension
============================

Junifer is designed to be easily extensible. Through the use of a registry and
decorators, you can easily add new functionality to junifer during runtime. This
is done by creating a new Python module and importing it before running junifer.

A special consideration has to be made when using the
:ref:`code-less configuration<codeless>`. In this case, the
``with`` statement can be used to import a module or run a Python file.

In the following example, we instruct junifer to first import ``my_module`` and
then run the ``my_file.py`` file.

.. code-block:: yaml

    with:
      - my_module
      - my_file.py

Thus, the code from ``my_file.py`` will be executed before running junifer. This
is the ideal place to include junifer extensions.

.. important::

   Some junifer commands will not consider files imported from files included
   in the ``with`` statement. If ``my_file.py`` imports ``my_other_file.py``,
   some of the junifer commands will not consider ``my_other_file.py``. Either
   place all the code in one file or add multiple files to the ``with``
   statement.
