.. include:: links.inc

Contributing to junifer
=======================


Setting up the local development environment
--------------------------------------------

1. Fork the https://github.com/juaml/junifer repository on GitHub. If you
   have never done this before, `follow the official guide
   <https://guides.github.com/activities/forking/>`_.
2. Clone your fork locally as described in the same guide.
3. Install your local copy into a Python virtual environment. You can `read
   this guide to learn more
   <https://realpython.com/python-virtual-environments-a-primer/>`_ about them
   and how to create one.

   .. code-block:: console

       pip install -e ".[dev]"

4. Create a branch for local development using the ``dev`` branch as a
   starting point. Use ``fix``, ``refactor``, or ``feat`` as a prefix.

   .. code-block:: console

       git checkout dev
       git checkout -b <prefix>/<name-of-your-branch>

   Now you can make your changes locally.

5. When making changes locally, it is helpful to ``git commit`` your work
   regularly. On one hand to save your work and on the other hand, the smaller
   the steps, the easier it is to review your work later. Please use `semantic
   commit messages
   <http://karma-runner.github.io/2.0/dev/git-commit-msg.html>`_.

   .. code-block:: console

       git add .
       git commit -m "<prefix>: <summary of changes>"

6. When you're done making changes, check that your changes pass our test suite.
   This is all included with ``tox``.

   .. code-block:: console

       tox

   You can also run all ``tox`` tests in parallel. As of ``tox 3.7``, you can run::

   .. code-block:: console

       tox --parallel


7. Push your branch to GitHub.

   .. code-block:: console

       git push origin <prefix>/<name-of-your-branch>

8. Open the link displayed in the message when pushing your new branch in order
   to submit a pull request. Please follow the template presented to you in the
   web interface to complete your pull request.


GitHub Pull Request guidelines
------------------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests in the respective ``tests`` directory.
   Except in rare circumstances, code coverage must not decrease (as reported
   by codecov which runs automatically when you submit your pull request).
2. If the pull request adds functionality, the docs should be
   updated. Consider creating a Python file that demonstrates the usage in
   ``examples`` directory.
3. The pull request should also include a short one-liner of your contribution
   in `docs/changes/latest.inc`. If it's your first contribution, also add
   yourself to `docs/changes/contributors.inc`.
3. The pull request will be tested for several different Python versions.
4. Someone from the core team will review your work and guide you to a successful
   contribution.


Running unit tests
------------------

junifer uses `pytest <http://docs.pytest.org/en/latest/>`_ for its
unit-tests and new features should in general always come with new
tests that make sure that the code runs as intended.

To run all tests::

.. code-block:: console

    tox -e test


Adding and building documentation
---------------------------------

Building the documentation requires some extra packages and can be installed by::

.. code-block:: console

    pip install -e ".[docs]"

To build the docs::

.. code-block:: bash

    cd docs
    make html

To view the documentation, open `docs/_build/html/index.html`.

In case you remove some files or change their filenames, you can run into
errors when using ``make html``. In this situation you can use ``make clean``
to clean up the already build files and then re-run ``make html``.


Writing Examples
----------------

Examples are run and displayed in HTML format using `sphinx gallery`_. To add an
example, just create a ``.py`` file that starts either with ``plot_`` or ``run_``,
dependending on whether the example generates a figure or not.

The first lines of the example should be a python block comment with a title,
a description of the example an the following include directive to be able to
use the links.

The format used for text is reST. Check the `sphinx reST reference`_ for more
details.

Example of the first lines:


.. code-block:: python

    """
    Simple Binary Classification
    ============================

    This example uses the 'iris' dataset and performs a simple binary
    classification using a Support Vector Machine classifier.

    .. include:: ../../links.inc
    """


The rest of the script will be executed as normal Python code. In order to
render the output and embed formatted text within the code, you need to add
a 79 ``#`` (a full line) at the point in which you want to render and add text.
Each line of text shall be preceded with ``#``. The code that is not
commented will be executed.

The following example will create 3 texts and render the output between the
texts.

.. code-block:: python

    ###############################################################################
    # Imports needed for the example
    from seaborn import load_dataset
    from julearn import run_cross_validation
    from julearn.utils import configure_logging

    ###############################################################################
    df_iris = load_dataset('iris')

    ###############################################################################
    # The dataset has three kind of species. We will keep two to perform a binary
    # classification.
    df_iris = df_iris[df_iris['species'].isin(['versicolor', 'virginica'])]


Finally, when the example is done, you can run as a normal Python script.
To generate the HTML, just build the docs:

.. code-block:: bash

    cd docs
    make html
