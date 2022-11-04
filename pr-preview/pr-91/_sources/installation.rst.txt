.. include:: links.inc

Installing junifer
==================


Requirements
------------

junifer is compatible with `Python`_ >= 3.8 and requires the following packages:

* ``click>=8.1.3,<8.2``
* ``numpy>=1.22,<1.24``
* ``datalad>=0.15.4,<0.18``
* ``pandas>=1.4.0,<1.6``
* ``nibabel>=3.2.0,<4.1``
* ``nilearn>=0.9.0,<1.0``
* ``sqlalchemy>=1.4.27,<= 1.5.0``
* ``pyyaml>=5.1.2,<7.0``

Depending on the installation method, these packages might be installed automatically.

Installation
------------

Depending on your use-case, junifer can be installed differently:

* Install the :ref:`install_latest_release`. This is the most suitable approach
  for end users.
* Install from :ref:`install_development_git`. This is the most suitable approach
  for developers.


Either way, we strongly recommend using `virtual environments <https://realpython.com/python-virtual-environments-a-primer>`_.


.. _install_latest_release:

Stable release
~~~~~~~~~~~~~~

Use ``pip`` to install julearn from `PyPI <https://pypi.org>`_, like so:

.. code-block:: bash

    pip install junifer


.. _install_development_git:

Local Git repository
~~~~~~~~~~~~~~~~~~~~

Follow the `detailed contribution guidelines <contribution.rst>`_.
