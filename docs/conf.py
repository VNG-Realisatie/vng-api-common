# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

import django
from django.conf import settings

sys.path.insert(0, os.path.abspath(".."))

from vng_api_common import __version__  # noqa isort:skip
from vng_api_common.conf import api as api_settings  # noqa isort:skip

settings.configure(
    INSTALLED_APPS=[
        "django.contrib.sites",
        "rest_framework",
        "django_filters",
        "vng_api_common",
        "vng_api_common.notifications",
        "drf_yasg",
        "solo",
    ],
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "docs",
            "USER": "docs",
            "PASSWORD": "docs",
        }
    },
    BASE_DIR=sys.path[0],
    **{name: getattr(api_settings, name) for name in api_settings.__all__}
)
django.setup()

# -- Project information -----------------------------------------------------

project = "Commonground-API-common"
copyright = "2022, VNG-Realisatie, Maykin Media"
author = "VNG-Realisatie, Maykin Media"

# The full version, including alpha/beta/rc tags
release = __version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.autodoc"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The master toctree document.
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

linkcheck_ignore = [
    r"http://localhost:\d+/",
    r"https://img.shields.io/.*",  # slow...
]
