.. include:: links.inc

Installing junifer
==================


Requirements
------------

junifer is compatible with `Python`_ >= 3.8 and requires the following packages:

* ``click>=8.1.3,<8.2``
* ``numpy>=1.22,<1.24``
* ``datalad>=0.15.4,<0.19``
* ``pandas>=1.4.0,<1.6``
* ``nibabel>=3.2.0,<4.1``
* ``nilearn>=0.9.0,<=0.10.0``
* ``sqlalchemy>=1.4.27,<= 1.5.0``
* ``ruamel.yaml>=0.17,<0.18``
* ``h5py>=3.8.0,<3.9``

Depending on the installation method, these packages might be installed
automatically.

Installation
------------

Depending on your use-case, junifer can be installed differently:

* Install the :ref:`install_latest_release`. This is the most suitable approach
  for end users.
* Install from :ref:`install_development_git`. This is the most suitable approach
  for developers.


Either way, we strongly recommend using
`virtual environments <https://realpython.com/python-virtual-environments-a-primer>`_.


.. _install_latest_release:

Stable release
~~~~~~~~~~~~~~

Use ``pip`` to install julearn from `PyPI <https://pypi.org>`_, like so:

.. code-block:: bash

    pip install junifer

You can also install via ``conda``, like so:

.. code-block:: bash

    conda install -c conda-forge junifer

.. attention::

   Installation on macOS and Windows might fail via ``conda`` due to ``datalad``.
   In that case, please refer to
   `Datalad installation instructions
   <http://handbook.datalad.org/en/latest/intro/installation.html>`_ for solutions.
   In case the problem persists, please install it via ``pip`` as mentioned earlier.

.. _install_development_git:

Local Git repository
~~~~~~~~~~~~~~~~~~~~

Follow the `detailed contribution guidelines <contribution.rst>`_.


.. _installation_ext:

Installing external dependencies
================================

Some markers will require optional external dependencies to be installed. In
this section you will find a list of all external dependencies that are required
for specific markers.

AFNI
----

To install AFNI, you can always follow the `AFNI official instructions
<https://afni.nimh.nih.gov/pub/dist/doc/htmldoc/background_install/main_toc.html>`_.
Additionally, you can also follow the following steps to install and configure
the AFNI Docker container in your local system.

.. important::

   The AFNI Docker container wrappers add the commands required by junifer. Using
   these commands have some limitations, mostly related to handling files and
   paths. Junifer knows about this and uses these commands in the proper way.
   Keep this in mind if you try to use the AFNI Docker wrappers outside of
   junifer. These caveats and limitations are not documented.

1. Install Docker. You can follow the
   `Docker official instructions <https://docs.docker.com/get-docker/>`_.
2. Pull the AFNI Docker image from
   `Docker Hub <https://hub.docker.com/r/afni/afni>`_:

.. code-block:: bash

  docker pull afni/afni_make_build

3. Add the Junifer AFNI scripts to your PATH environmental variable. Run the
   following command:

.. code-block:: bash

  junifer setup afni-docker

Take the last line and copy it to your ``.bashrc`` or ``.zshrc`` file.

Or, alternatively, you can execute this command which will update the
``~/.bashrc`` for you:

.. code-block:: bash

  junifer setup afni-docker | grep "PATH=" | xargs | >> ~/.bashrc
