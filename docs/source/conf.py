# ABOUTME: Sphinx configuration for the fountain-py documentation site.
# The version comes from the installed package metadata, so docs builds run inside the uv environment.
from __future__ import annotations

from importlib.metadata import version as get_version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sphinx.application import Sphinx

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html
project = "fountain-py"
copyright = "2025, Mason Egger"
author = "Mason Egger"
release = get_version("fountain-py")
version = release

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx_copybutton",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"
html_title = f"{project} {version}"
html_static_path: list[str] = []

# Furo theme options
html_theme_options = {
    "sidebar_hide_name": True,
    "light_css_variables": {
        "color-brand-primary": "#1f4f99",
        "color-brand-content": "#1f4f99",
    },
    "dark_css_variables": {
        "color-brand-primary": "#4c8be3",
        "color-brand-content": "#4c8be3",
    },
    "source_repository": "https://github.com/MasonEgger/fountain-py/",
    "source_branch": "main",
    "source_directory": "docs/source/",
}

# -- Extension configuration -------------------------------------------------

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": False,
    "exclude-members": "__weakref__",
}
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# Copy button configuration
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# Doctest settings
doctest_default_flags = 0
doctest_global_setup = """
import fountain
from fountain import FountainParser, FountainDocument, ElementType
"""

# MyST parser settings
myst_enable_extensions = [
    "deflist",
    "tasklist",
    "colon_fence",
]


# Skip regex pattern constants from documentation
def autodoc_skip_member(app: Sphinx, what: str, name: str, obj: object, skip: bool, options: object) -> bool:
    # Skip all uppercase constants (regex patterns and other constants)
    if name.isupper() and "_" in name:
        return True
    return skip


def setup(app: Sphinx) -> None:
    app.connect("autodoc-skip-member", autodoc_skip_member)
