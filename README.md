# CRM-facet-library

Shared capability facet library consumed by
[CRMinventory](https://github.com/dbower44022/CRMinventory) and
[CRMBuilder](https://github.com/dbower44022/crmbuilder).

Defines the vocabulary in which CRM capabilities are expressed and customer
requirements are decomposed. The authoritative specification is
[PRD 02 — Facet Library Schema & Conventions](https://github.com/dbower44022/CRMinventory/blob/main/docs/prd/02-facet-library-schema.md).

## Layout

```
src/crm_facet_library/
  LIBRARY.yaml                                  # library-wide metadata
  facets/<family>/<facet-id-minus-family>.yaml  # one facet per file
  __init__.py, models.py, validation.py         # Python API + CLI
CHANGELOG.md
```

The facet YAMLs live inside the Python package (rather than at repo root as
the logical spec in PRD 02 §6.1 depicts them) so they ship inside the
installed wheel and the loader can resolve them via `importlib.resources`.
The `crm-facet-lint` CLI auto-discovers the bundled location when called
with no arguments, so dev ergonomics are unchanged.

## Python API

```python
from crm_facet_library import load_library

lib = load_library()
print(lib.version)                                    # "0.1.0"
facet = lib.get("history.relationship.temporal_modeling")
```

## Validation

```bash
pip install -e ".[dev]"
crm-facet-lint                      # walks facets/ + LIBRARY.yaml
crm-facet-lint --json               # machine-readable output
```

## Installation as a dependency

Consumers pin a specific tag:

```toml
[project]
dependencies = [
  "crm-facet-library @ git+https://github.com/dbower44022/CRM-facet-library@v0.1.0",
]
```

## Authoring a facet

1. `git checkout -b facet/<short-name>`
2. Add or edit YAML under `facets/<family>/`.
3. `crm-facet-lint` locally.
4. Update `CHANGELOG.md`.
5. Open PR.

See PRD 04 §8.1 for the full workflow.
