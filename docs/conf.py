"""Provide configuration for Sphinx."""

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import sys
from pathlib import Path


curdir = Path(__file__).parent
sys.path.append((curdir / "sphinxext").as_posix())

# -- Project information -----------------------------------------------------

project = "junifer"
copyright = "2022, Authors of junifer"
author = "Fede Raimondo"


# -- General configuration ---------------------------------------------------


# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",  # include documentation from docstrings
    "sphinx.ext.autosummary",  # generate autodoc summaries
    "sphinx.ext.doctest",  # test snippets in the documentation
    "sphinx.ext.intersphinx",  # link to other projects’ documentation
    "sphinx.ext.mathjax",  # math support for HTML outputs in Sphinx
    "sphinx_gallery.gen_gallery",  # HTML gallery of examples
    "sphinx_rtd_theme",  # RTD theme
    "sphinx_multiversion",  # self-hosted versioned documentation
    "numpydoc",  # support for NumPy style docstrings
    "gh_substitutions",  # custom GitHub substitutions
    # "autoapi.extension",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

html_sidebars = {"**": ["globaltoc.html", "sourcelink.html", "searchbox.html"]}


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    "python": ("https://docs.python.org/", None),
    "sklearn": ("https://scikit-learn.org/stable", None),
    "nilearn": ("https://nilearn.github.io/stable/", None),
    "julearn": ("https://juaml.github.io/julearn/main", None),
}

sphinx_gallery_conf = {
    "examples_dirs": ["../examples"],
    "gallery_dirs": ["auto_examples"],
    "filename_pattern": "/(plot|run)_",
    "backreferences_dir": "generated",
}


autosummary_generate = True
numpydoc_show_class_members = False
autoclass_content = "both"

# sphinx-multiversion options
smv_rebuild_tags = False
smv_tag_whitelist = r'^v\d+\.\d+.\d+$'
smv_branch_whitelist = r'main'
smv_released_pattern = r'^tags/v.*$'

# Sphinx-AutoAPI configurations
autoapi_dirs = ["../junifer"]
suppress_warnings = ["autoapi.python_import_resolution"]
