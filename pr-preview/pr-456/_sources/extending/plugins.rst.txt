.. include:: ../links.inc

.. _plugins:

Creating a ``junifer`` plugin
=============================

What is a plugin
----------------

Plugins are additional components that extend the functionality of ``junifer``.
Technically, plugins can also be called as extensions, but we clearly differentiate
them in ``junifer`` as :ref:`extensions<extending_extension>` serve a different
purpose. ``junifer`` plugins are command line programs which can be used
independently but also integrates with the core ``junifer`` command line interface
(CLI) framework.

When a plugin is installed, we basically inject new behaviours into the ``junifer`` CLI
while promoting modularity and allowing for easier maintenance and updates to the core
application. A great plugin example is `junifer-data`_ which is well-integrated
in ``junifer`` to access assets like parcellations, coordinates and masks, but also
remains modular enough to update its CLI without disturbing that of ``junifer``.

How to make a plugin
--------------------

A key distinction between a ``junifer`` extension and a ``junifer`` plugin is that a
plugin will have its own CLI and be a Python package in its own right, for example,
`junifer-data`_.

The following steps should lead you to make a successful plugin:

#. Create CLI for your plugin. As ``junifer`` uses `click`_ for its CLI, a plugin
   should be creating its own ``click.Group`` as shown here:
   `<https://click.palletsprojects.com/en/stable/commands/#commands-and-groups>`_.

#. Integrate the `click`_-based plugin CLI with `setuptools`_ as shown here:
   `<https://click.palletsprojects.com/en/stable/setuptools/#setuptools-integration>`_.

#. Make sure the plugin CLI independently works as intended.

#. Follow the steps here:
   `<https://setuptools.pypa.io/en/latest/userguide/entry_point.html#entry-points-for-plugins>`_
   and make a new entry point with the *name* as the sub-command you want under ``junifer`` command
   and the *group* as ``"junifer.ext"``. The *name* should refer to the ``click.Group`` of your
   plugin CLI.

#. After you install your plugin in the same environment as your ``junifer`` installation, you can
   observe your plugin being added as a new sub-command under ``junifer`` and working exactly as it
   did independently.
