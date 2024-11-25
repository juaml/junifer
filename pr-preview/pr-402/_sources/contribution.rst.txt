.. include:: links.inc

.. _contribution_guidelines:

Contributing
============

Setting up the local development environment
--------------------------------------------

#. Fork the https://github.com/juaml/junifer repository on GitHub. If you
   have never done this before, `follow the official guide
   <https://guides.github.com/activities/forking/>`_.
#. Clone your fork locally as described in the same guide but also add the
   flag to sync the submodules as well by appending the following to the
   clone command:

   .. code-block:: bash

      ... --recurse-submodules

#. Install your local copy into a Python virtual environment. You can `read
   this guide to learn more
   <https://realpython.com/python-virtual-environments-a-primer/>`_ about them
   and how to create one.

   .. code-block:: bash

       pip install -e ".[dev]"

#. Create a branch for local development using the ``main`` branch as a
   starting point. Use ``fix``, ``refactor``, or ``feat`` as a prefix.

   .. code-block:: bash

       git checkout main
       git checkout -b <prefix>/<name-of-your-branch>

   Now you can make your changes locally.

#. Make sure you install git pre-commit hooks like so:

   .. code-block:: bash

       pre-commit install

#. When making changes locally, it is helpful to ``git commit`` your work
   regularly. On one hand to save your work and on the other hand, the smaller
   the steps, the easier it is to review your work later. Please use `semantic
   commit messages
   <http://karma-runner.github.io/2.0/dev/git-commit-msg.html>`_.

   .. code-block:: bash

       git add .
       git commit -m "<prefix>: <summary of changes>"

   In case, you want to commit some WIP (work-in-progress) code, please indicate
   that in the commit message and use the flag ``--no-verify`` with
   ``git commit`` like so:

   .. code-block:: bash

       git commit --no-verify -m "WIP: <summary of changes>"

#. When you're done making changes, check that your changes pass our test suite.
   This is all included with ``tox``.

   .. code-block:: bash

       tox

   You can also run all ``tox`` tests in parallel. As of ``tox 3.7``, you can run

   .. code-block:: bash

       tox --parallel

#. Push your branch to GitHub.

   .. code-block:: bash

       git push origin <prefix>/<name-of-your-branch>

#. Open the link displayed in the message when pushing your new branch in order
   to submit a pull request. Please follow the template presented to you in the
   web interface to complete your pull request.


GitHub Pull Request guidelines
------------------------------

Before you submit a pull request, check that it meets these guidelines:

#. The pull request should include tests in the respective ``tests`` directory.
   Except in rare circumstances, code coverage must not decrease (as reported
   by codecov which runs automatically when you submit your pull request).
#. If the pull request adds functionality, the docs should be
   updated. Consider creating a Python file that demonstrates the usage in
   ``examples/`` directory.
#. Make sure to create a Draft Pull Request. If you are not sure how to do it,
   check
   `here <https://github.blog/2019-02-14-introducing-draft-pull-requests/>`_.
#. Note the pull request ID assigned after completing the previous step and
   create a short one-liner file of your contribution named as
   ``<pull-request-ID>.<type>`` in ``docs/changes/newsfragments/``, ``<type>``
   being as per the following convention:

   * API change : ``change``
   * Bug fix : ``bugfix``
   * Enhancement : ``enh``
   * Feature : ``feature``
   * Documentation improvement : ``doc``
   * Miscellaneous : ``misc``
   * Deprecation and API removal : ``removal``

   For example, a basic documentation improvement can be recorded in a file
   ``101.doc`` with the content:

   .. code-block::

       Fixed a typo in intro by `junifer's biggest fan`_

#. If it's your first contribution, also add yourself to
   ``docs/changes/contributors.inc``.
#. The pull request will be tested against several Python versions.
#. Someone from the core team will review your work and guide you to a successful
   contribution.


Running unit tests
------------------

junifer uses `pytest <http://docs.pytest.org/en/latest/>`_ for its
unit-tests and new features should in general always come with new
tests that make sure that the code runs as intended.

To run all tests

.. code-block:: bash

    tox -e test


Adding and building documentation
---------------------------------

Building the documentation requires some extra packages and can be installed by

.. code-block:: bash

    pip install -e ".[docs]"

To build the docs

.. code-block:: bash

    cd docs
    make local

To view the documentation, open ``docs/_build/html/index.html``.

In case you remove some files or change their filenames, you can run into
errors when using ``make local``. In this situation you can use ``make clean``
to clean up the already build files and then re-run ``make local``.

Also, we follow British English for the documentation.


Writing Examples
----------------

The format used for text is reST. Check the `sphinx reST reference`_ for more
details. The examples are run and displayed in HTML format using
`sphinx gallery`_. To add an example, just create a ``.py`` file that starts
either with ``plot_`` or ``run_``, depending on whether the example generates
a figure or not.

The first lines of the example should be a Python block comment with a title,
a description of the example, authors and license name.

The following is an example of how to start an example

.. code-block:: python

    """
    Generic BIDS datagrabber for datalad.
    =====================================

    This example uses a generic BIDS datagraber to get the data from a BIDS dataset
    store in a datalad remote sibling.

    Authors: Federico Raimondo

    License: BSD 3 clause
    """

The rest of the script will be executed as normal Python code. In order to
render the output and embed formatted text within the code, you need to add
a 79 ``#`` (a full line) at the point in which you want to render and add text.
Each line of text shall be preceded with ``#``. The code that is not
commented will be executed.

The following example will create texts and render the output between the
texts.

.. code-block:: python

    from junifer.datagrabber import PatternDataladDataGrabber
    from junifer.utils import configure_logging


    ###############################################################################
    # Set the logging level to info to see extra information
    configure_logging(level="INFO")


    ###############################################################################
    # The BIDS datagrabber requires three parameters: the types of data we want,
    # the specific pattern that matches each type, and the variables that will be
    # replaced in the patterns.
    types = ["T1w", "BOLD"]
    patterns = {
        "T1w": "{subject}/anat/{subject}_T1w.nii.gz",
        "BOLD": "{subject}/func/{subject}_task-rest_bold.nii.gz",
    }
    replacements = ["subject"]
    ###############################################################################
    # Additionally, a datalad datagrabber requires the URI of the remote sibling
    # and the location of the dataset within the remote sibling.
    repo_uri = "https://gin.g-node.org/juaml/datalad-example-bids"
    rootdir = "example_bids"

    ###############################################################################
    # Now we can use the datagrabber within a `with` context
    # One thing we can do with any datagrabber is iterate over the elements.
    # In this case, each element of the datagrabber is one session.
    with PatternDataladDataGrabber(
        rootdir=rootdir,
        types=types,
        patterns=patterns,
        uri=repo_uri,
        replacements=replacements,
    ) as dg:
        for elem in dg:
            print(elem)

    ###############################################################################
    # Another feature of the datagrabber is the ability to get a specific
    # element by its name. In this case, we index `sub-01` and we get the file
    # paths for the two types of data we want (T1w and bold).
    with PatternDataladDataGrabber(
        rootdir=rootdir,
        types=types,
        patterns=patterns,
        uri=repo_uri,
        replacements=replacements,
    ) as dg:
        sub01 = dg["sub-01"]
        print(sub01)

Finally, when the example is done, you can run it as a normal Python script.
To generate the HTML, just build the docs.
