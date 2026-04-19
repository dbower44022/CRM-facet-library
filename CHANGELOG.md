# Changelog

All notable changes to the facet library are recorded here per
PRD 02 §7.4. Grouped under Added / Changed / Deprecated / Removed.

## [Unreleased]

## [0.1.1] — 2026-04-19

### Added
- Four new seed facets exercising previously-uncovered dimensions surfaced
  by the 2026-04-19 C1 corpus expansion (higher-education + healthcare RFPs):
  - `ui.persona_driven_view_composition` — persona-as-capability (internal
    multi-role staff + external lifecycle-stage portals); covers REQ-033
    (self-service student portal) and REQ-039 (care-coordinator task queue)
  - `field.computed_classification` — materialized tier/classification
    fields with cadence refresh, history, and explainability; covers
    REQ-038 (patient risk tier) and REQ-032 (student retention alerts)
  - `data.identity_resolution` — multi-source de-duplication with
    configurable match rules, manual review queue, per-field source
    lineage, reversible unmerge; covers REQ-035 (unified patient record)
  - `integration.bidirectional_sync` — per-field direction, configurable
    conflict resolution, change attribution; covers REQ-034 (SIS/LMS
    integration) and the email/LMS/marketing integrations in the Cleveland
    corpus
- Family directories `ui/`, `field/`, `data/`, `integration/` — previously
  defined in `LIBRARY.yaml` but not yet populated.

### Changed
- Refreshed `source_hints.corpus_refs` on all 6 pre-existing facets that
  carried placeholder references (`REQ-001-employment-history`,
  `REQ-007-subscription-periods`, `REQ-015-status-change-timeline`) to
  actual C1 corpus IDs from the CRMinventory `docs/corpus/c1-requirements/`
  directory. Affected facets: `entity.relationship.cardinality`,
  `history.queryability.point_in_time`, `history.relationship.retention`,
  `history.relationship.temporal_modeling`, `history.field.audit_trail`,
  `process.trigger.on_field_change`.
- Refreshed stale "employment history" examples on 3 history facets to
  use real-corpus mentor/client engagement scenarios (cosmetic — the
  facet questions themselves remain generic).

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
