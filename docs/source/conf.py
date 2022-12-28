# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


import pathlib
import sys

import toml

ROOT_DIR = pathlib.Path(__file__).parents[2].resolve()
sys.path.insert(0, ROOT_DIR.as_posix())

pyproject = toml.load((ROOT_DIR / "pyproject.toml").as_posix())
poetry = pyproject["tool"]["poetry"]

project = poetry["name"]
copyright = "2022, Tom Wojcik"
author = poetry["authors"][0]
release = poetry["version"]

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
]

templates_path = ["_templates"]
exclude_patterns = []


html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]


# Autodoc specific stuff
# https://autodoc-pydantic.readthedocs.io/en/stable/users/configuration.html
extensions.append(
    "sphinxcontrib.autodoc_pydantic",
)
autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config = False
autodoc_pydantic_model_show_field_summary = False
autodoc_pydantic_model_show_validator_summary = False

# autodoc_pydantic_model_show_config_member = False
# autodoc_pydantic_model_show_validator_members = False
# autodoc_pydantic_field_list_validators = True

# autodoc_pydantic_model_members = True

"""
   :settings-show-json: False
   :settings-show-config-member: False
   :settings-show-config-summary: False
   :settings-show-validator-members: False
   :settings-show-validator-summary: False
   :field-list-validators: False
"""
