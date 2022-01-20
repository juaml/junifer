.. include:: links.inc

Installing
==========


Requirements
^^^^^^^^^^^^

<PKG_NAME> requires the following packages:

Running the examples requires:

Depending on the installation method, this packages might be installed
automatically.

Installing
^^^^^^^^^^
There are different ways to install <PKG_NAME>:

* Install the :ref:`install_latest_release`. This is the most suitable approach
  for most end users.
* Install the :ref:`install_latest_development`. This version will have the
  latest features. However, it is still under development and not yet
  officially released. Some features might still change before the next stable
  release.
* Install from :ref:`install_development_git`. This is mostly suitable for
  developers that want to have the latest version and yet edit the code.


Either way, we strongly recommend using virtual environments:

* `venv`_
* `conda env`_


.. _install_latest_release:

Latest release
--------------

We have packaged <PKG_NAME> and published it in PyPi, so you can just install it
with `pip`.

.. code-block:: bash

    pip install -U <PKG_NAME>


.. _install_latest_development:

Latest Development Version
--------------------------
First, make sure that you have all the dependencies installed:

Then, install <PKG_NAME> from TestPypi

.. code-block:: bash

    pip install --index-url https://test.pypi.org/simple/ -U <PKG_NAME> --pre


.. _install_development_git:

Local git repository (for developers)
-------------------------------------
First, make sure that you have all the dependencies installed:

Then, clone `<PKG_NAME> Github`_ repository in a folder of your choice:

.. code-block:: bash

    git clone <GITHUB_URL>.git

Install development mode requirements:

.. code-block:: bash

    cd <PKG_NAME>
    pip install -r dev-requirements.txt

Finally, install in development mode:

.. code-block:: bash

    python setup.py develop

.. note:: Every time that you run ``setup.py develop``, the version is going to
  be automatically set based on the git history. Nevertheless, this change 
  should not be committed (changes to ``_version.py``). Running ``git stash``
  at this point will forget the local changes to ``_version.py``.
