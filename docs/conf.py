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
    "sphinx_multiversion",  # self-hosted versioned documentation
    "numpydoc",  # support for NumPy style docstrings
    "gh_substitutions",  # custom GitHub substitutions
]

# Add any paths that contain templates here, relative to this directory.
templates_path = [
    "_templates",
]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

nitpicky = True

nitpick_ignore_regex = [
    ("py:class", "numpy._typing.*"),
    ("py:obj", "trimboth"),  # python 3.11 error
    ("py:obj", "tmean"),  # python 3.11 error
    ("py:obj", "subclass"),  # python 3.11 error
    ("py:class", "typing.Any"),  # python 3.11 error
    # ('py:class', 'numpy.typing.ArrayLike')
    ("py:obj", "sqlalchemy.engine.Engine"),  # ignore sqlalchemy
]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages. See the documentation for
# a list of builtin themes.
#
html_theme = "furo"

html_logo = "./images/junifer_logo.png"

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    "css/custom.css",
]

html_js_files = [
    "js/custom.js",
]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_sidebars = {
    "**": [
        "sidebar/scroll-start.html",
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/navigation.html",
        "versions.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
    ]
}

# -- sphinx.ext.autodoc configuration ----------------------------------------

autoclass_content = "both"
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# -- sphinx.ext.autosummary configuration ------------------------------------

autosummary_generate = True

# -- sphinx.ext.intersphinx configuration ------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sklearn": ("https://scikit-learn.org/stable", None),
    "nilearn": ("https://nilearn.github.io/stable/", None),
    "julearn": ("https://juaml.github.io/julearn/main", None),
    "nibabel": ("https://nipy.org/nibabel/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/dev", None),
    # "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
}

# -- numpydoc configuration --------------------------------------------------

numpydoc_show_class_members = False
numpydoc_xref_param_type = True
numpydoc_xref_aliases = {
    "Path": "pathlib.Path",
    "Nifti1Image": "nibabel.nifti1.Nifti1Image",
    "Nifti2Image": "nibabel.nifti2.Nifti2Image",
    # "Engine": "sqlalchemy.engine.Engine",
}
numpydoc_xref_ignore = {
    "of",
    "shape",
    "optional",
    "or",
    "the",
    "options",
    "function",
    "object",
    "class",
    "objects",
    "Engine",
    "positive",
    "negative",
}
# numpydoc_validation_checks = {
#     "all",
#     "GL01",
#     "GL02",
#     "GL03",
#     "ES01",
#     "SA01",
#     "EX01",
# }

# -- Sphinx-Gallery configuration --------------------------------------------

sphinx_gallery_conf = {
    "examples_dirs": ["../examples"],
    "gallery_dirs": ["auto_examples"],
    "filename_pattern": "/(plot|run)_",
    "backreferences_dir": "generated",
}

# -- sphinx-multiversion configuration ---------------------------------------

smv_rebuild_tags = False
smv_tag_whitelist = r"^v\d+\.\d+.\d+$"
smv_branch_whitelist = r"main"
smv_released_pattern = r"^tags/v.*$"
