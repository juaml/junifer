.. include:: links.inc

FAQs
====

What are the first steps to contribute to junifer?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* go to `contribution <https://juaml.github.io/junifer/main/contribution.html>`_ and follow the steps written here.


What is the easiest setup to contribute to junifer?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* Use VScode (or any other IDE (interactive developer environment) of your choice) with which you can fork the repository and git.

We followed the following steps to get started with contributing:

1. Fork the repository

   * copy the link and do ``git-clone``

2. Create the development environment

   * create the environment using conda ``conda env create -n {NameOfEnvironment} python=3.9``
   * update the environment ``conda env update -n {NameOfEnvironment} --file=conda-env.yml``. The relevant file is within the junifer directory.
   * activate the environment ``conda activate {NameOfEnvironment}``

3. install junifer

   * go to your junifer-directory ``cd {junifer-directory}`` and ``pip install -e .``

4. open VS code and start contributing


P.S.: if you want to contribute to the documentation go to
`7.4 <file:///Users/pat/Desktop/junifer/junifer_BH/docs/_build/contribution.html#adding-and-building-documentation>`_ and build the packages required for documentation
``pip install -e ".[docs]"
cd docs
make local``
You can change the content of the html sites by changing the related .rst-files.
to check how your chagnes look like in your browser, save the .rst-file after changing and type ``make local``. 
Afterwards, open the index.html file or other related html file in your browser



