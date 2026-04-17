"""Load the bundled facet library from disk into memory.

Resolution order:

1. ``CRM_FACET_LIBRARY_PATH`` environment variable, if set.
2. The library bundled inside the installed package.

Consumers typically just call :func:`load_library` with no arguments.
"""
from __future__ import annotations

import os
from pathlib import Path

from ._yaml import load_yaml
from .models import Facet, Library, LibraryMeta

_BUNDLED_ROOT = Path(__file__).parent
_LIBRARY_FILE = "LIBRARY.yaml"
_FACETS_DIR = "facets"


def _resolve_root(override: str | os.PathLike[str] | None) -> Path:
    if override is not None:
        return Path(override)
    env = os.environ.get("CRM_FACET_LIBRARY_PATH")
    if env:
        return Path(env)
    return _BUNDLED_ROOT


def load_library(root: str | os.PathLike[str] | None = None) -> Library:
    """Load and return the facet library.

    :param root: Override path containing ``LIBRARY.yaml`` + ``facets/``.
        Defaults to the bundled location.
    """

    root_path = _resolve_root(root)
    meta_path = root_path / _LIBRARY_FILE
    if not meta_path.is_file():
        raise FileNotFoundError(f"LIBRARY.yaml not found at {meta_path}")

    meta = LibraryMeta.model_validate(load_yaml(meta_path.read_text()))

    facets: dict[str, Facet] = {}
    facets_dir = root_path / _FACETS_DIR
    if facets_dir.is_dir():
        for yaml_path in sorted(facets_dir.rglob("*.yaml")):
            data = load_yaml(yaml_path.read_text())
            if data is None:
                continue
            facet = Facet.model_validate(data)
            facets[facet.id] = facet

    return Library(meta=meta, facets=facets)
