"""YAML loader that keeps ``yes`` / ``no`` as strings (PRD 02 §2.3 boolean
answer schemas use ``yes`` / ``no`` as allowed values, not YAML booleans).
"""
from __future__ import annotations

import re

import yaml


class FacetYamlLoader(yaml.SafeLoader):
    """SafeLoader that treats only ``true`` / ``false`` as booleans."""


_KEEP_TAG = "tag:yaml.org,2002:bool"
FacetYamlLoader.yaml_implicit_resolvers = {
    ch: [(tag, regex) for tag, regex in resolvers if tag != _KEEP_TAG]
    for ch, resolvers in FacetYamlLoader.yaml_implicit_resolvers.items()
}
FacetYamlLoader.add_implicit_resolver(
    _KEEP_TAG,
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def load_yaml(text: str):
    return yaml.load(text, Loader=FacetYamlLoader)
