"""Provide configuration for Sphinx."""

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime
from functools import partial
from pathlib import Path

from setuptools_scm import get_version


# Check if sphinx-multiversion is installed
use_multiversion = False
try:
    import sphinx_multiversion  # noqa: F401

    use_multiversion = True
except ImportError:
    pass


# -- Path setup --------------------------------------------------------------

PROJECT_ROOT_DIR = Path(__file__).parents[1].resolve()
get_scm_version = partial(get_version, root=PROJECT_ROOT_DIR)

# -- Project information -----------------------------------------------------

github_url = "https://github.com"
github_repo_org = "juaml"
github_repo_name = "junifer"
github_repo_slug = f"{github_repo_org}/{github_repo_name}"
github_repo_url = f"{github_url}/{github_repo_slug}"

project = github_repo_name
author = f"{project} Contributors"
copyright = f"{datetime.date.today().year}, {author}"

# The version along with dev tag
release = get_scm_version(
    version_scheme="guess-next-dev",
    local_scheme="no-local-version",
)

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # Built-in extensions:
    "sphinx.ext.autodoc",  # include documentation from docstrings
    "sphinx.ext.autosummary",  # generate autodoc summaries
    "sphinx.ext.doctest",  # test snippets in the documentation
    "sphinx.ext.extlinks",  # markup to shorten external links
    "sphinx.ext.intersphinx",  # link to other projects` documentation
    "sphinx.ext.mathjax",  # math support for HTML outputs in Sphinx
    # Third-party extensions:
    "sphinx_gallery.gen_gallery",  # HTML gallery of examples
    "numpydoc",  # support for NumPy style docstrings
    "sphinx_copybutton",  # copy button for code blocks
    "sphinxcontrib.mermaid",  # mermaid support
    "sphinxcontrib.towncrier.ext",  # towncrier fragment support
]

if use_multiversion:
    extensions.append("sphinx_multiversion")

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
    ("py:class", "pipeline.Pipeline"),  # nilearn
    ("py:obj", "neurokit2.*"),  # ignore neurokit2
    ("py:obj", "datalad.*"),  # ignore datalad
]

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_title = "junifer documentation"
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
    "pandas": ("https://pandas.pydata.org/pandas-docs/dev", None),
    # "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
}

# -- sphinx.ext.extlinks configuration ---------------------------------------

extlinks = {
    "gh": (f"{github_repo_url}/issues/%s", "#%s"),
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
    "estimator",
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

# -- sphinxcontrib-towncrier configuration -----------------------------------

towncrier_draft_autoversion_mode = "draft"
towncrier_draft_include_empty = True
towncrier_draft_working_directory = PROJECT_ROOT_DIR
