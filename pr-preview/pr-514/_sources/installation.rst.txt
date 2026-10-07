.. include:: links.inc

Installing ``junifer``
======================

Depending on your use-case, ``junifer`` can be installed differently:

* Install the :ref:`latest stable release <install_latest_release>`. This is the most suitable approach
  for end users.
* Install from :ref:`latest development release <install_development_git>`. This is the most suitable approach
  for developers.


Either way, we strongly recommend using
`virtual environments <https://realpython.com/python-virtual-environments-a-primer>`_.


.. _install_latest_release:

Using a package manager
-----------------------

Use ``pip`` to install ``junifer`` from `PyPI <https://pypi.org>`_, like so:

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

From the source
---------------

Follow the `detailed contribution guidelines <contribution.rst>`_.


.. _installation_ext:

Installing external dependencies
================================

Some preprocessors and markers will require optional external dependencies to
be installed. In this section you will find a list of all external dependencies
that are required for specific markers.

.. important::

   The Docker container wrappers add the commands required by ``junifer``. Using
   these commands have some limitations, mostly related to handling files and
   paths. ``junifer`` knows about this and uses these commands in the proper way.
   Keep this in mind if you try to use the Docker wrappers outside of
   ``junifer``. These caveats and limitations are not documented.

AFNI
----

To install AFNI, you can always follow the `AFNI official instructions
<https://afni.nimh.nih.gov/pub/dist/doc/htmldoc/background_install/main_toc.html>`_.
Additionally, you can also follow the following steps to install and configure
the AFNI Docker container in your local system.

1. Install Docker. You can follow the
   `Docker official instructions <https://docs.docker.com/get-docker/>`_.
2. Pull the AFNI Docker image from
   `Docker Hub AFNI <https://hub.docker.com/r/afni/afni>`_:

.. code-block:: bash

  docker pull afni/afni_make_build

3. Add the Junifer AFNI scripts to your PATH environment variable. Run the
   following command:

.. code-block:: bash

  junifer setup afni-docker

Take the last line and copy it to your ``.bashrc`` or ``.zshrc`` file.

Or, alternatively, you can execute this command which will update the
``~/.bashrc`` for you:

.. code-block:: bash

  junifer setup afni-docker | grep "PATH=" | xargs | >> ~/.bashrc

FSL
---

To install FSL, you can always follow the `FSL official instructions
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation>`_.
Additionally, you can also follow the following steps to install and configure
the FSL Docker container in your local system.

1. Install Docker. You can follow the
   `Docker official instructions <https://docs.docker.com/get-docker/>`_.
2. Pull the FSL Docker image from
   `Docker Hub FSL <https://hub.docker.com/r/brainlife/fsl>`_:

.. code-block:: bash

  docker pull brainlife/fsl

3. Add the Junifer FSL scripts to your PATH environment variable. Run the
   following command:

.. code-block:: bash

  junifer setup fsl-docker

Take the last line and copy it to your ``.bashrc`` or ``.zshrc`` file.

Or, alternatively, you can execute this command which will update the
``~/.bashrc`` for you:

.. code-block:: bash

  junifer setup fsl-docker | grep "PATH=" | xargs | >> ~/.bashrc

ANTs
----

To install ANTs, you can always follow the `ANTs official instructions
<https://github.com/ANTsX/ANTs>`_. Additionally, you can also follow the
following steps to install and configure the ANTs Docker container in your
local system.

1. Install Docker. You can follow the
   `Docker official instructions <https://docs.docker.com/get-docker/>`_.
2. Pull the ANTs Docker image from
   `Docker Hub ANTs <https://hub.docker.com/r/antsx/ants>`_:

.. code-block:: bash

  docker pull antsx/ants

3. Add the Junifer ANTs scripts to your PATH environment variable. Run the
   following command:

.. code-block:: bash

  junifer setup ants-docker

Take the last line and copy it to your ``.bashrc`` or ``.zshrc`` file.

Or, alternatively, you can execute this command which will update the
``~/.bashrc`` for you:

.. code-block:: bash

  junifer setup ants-docker | grep "PATH=" | xargs | >> ~/.bashrc

FreeSurfer
----------

To install FreeSurfer, you can always follow the `FreeSurfer official instructions
<https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall>`_. Additionally, you can
also follow the following steps to install and configure the FreeSurfer Docker container
in your local system.

1. Install Docker. You can follow the
   `Docker official instructions <https://docs.docker.com/get-docker/>`_.
2. Pull the FreeSurfer Docker image from
   `Docker Hub FreeSurfer <https://hub.docker.com/r/freesurfer/freesurfer>`_:

.. code-block:: bash

  docker pull freesurfer/freesurfer

3. Add the Junifer FreeSurfer scripts to your PATH environment variable. Run the
   following command:

.. code-block:: bash

  junifer setup freesurfer-docker

Take the last line and copy it to your ``.bashrc`` or ``.zshrc`` file.

Or, alternatively, you can execute this command which will update the
``~/.bashrc`` for you:

.. code-block:: bash

  junifer setup freesurfer-docker | grep "PATH=" | xargs | >> ~/.bashrc
