# Changelog

All notable changes to the facet library are recorded here per
PRD 02 §7.4. Grouped under Added / Changed / Deprecated / Removed.

## [Unreleased]

## [0.1.0] — 2026-04-17

### Added
- Initial library scaffold: `LIBRARY.yaml`, validation CLI (`crm-facet-lint`),
  Python loader API, GitHub Actions validation workflow.
- Seed facets (8 total):
  - `history.relationship.temporal_modeling`
  - `history.relationship.retention`
  - `history.field.audit_trail`
  - `entity.field.types.multi_enum`
  - `entity.relationship.cardinality`
  - `process.trigger.on_field_change`
  - `permission.field_level`
  - `api.rate_limit`
