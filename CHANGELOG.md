# Changelog

All notable changes to the facet library are recorded here per
PRD 02 §7.4. Grouped under Added / Changed / Deprecated / Removed.

## [Unreleased]

## [0.1.2] — 2026-04-20

### Added
- **62 new facets** from PRD 03 W1 LLM-led extraction against the full C1
  corpus (39 items across 3 industries). Library goes from 12 → 74 facets.
  Candidates were extracted by Claude Sonnet 4.6 (prompt v1.0), validated
  structurally, human-triaged per `staging/candidates-2026-04-19/TRIAGE.md`
  in the CRMinventory repo, and promoted with status `active`.
- New families first populated this release: `data` (9 facets), `field` (3),
  `integration` (9), `ui` (7), `workflow` (7), `relationship` (1).
- Two new synthetic facets authored by hand as merger survivors of pairs
  the reviewer wanted combined:
  - `workflow.decision_rationale` — merges capture-at-action and
    capture-at-status-transition rationale capabilities.
  - `integration.external_readonly_ingestion` — merges read-only external
    system-of-record display and scheduled external signal ingestion.

### Changed
- **LIBRARY.yaml** documents the `workflow` vs. `process` family convention:
  `process` = automation primitives (triggers, actions, notifications);
  `workflow` = multi-step sequencing, branching, gating, review processes.
  Codified per TRIAGE.md BD-1.
- **Seed `compliance.data_retention_policy`** — backfilled missing
  `corpus_refs` (REQ-005, REQ-011, REQ-017). Resolves the model-flagged
  audit finding from W1 pilot batch notes.
- Question-trim pass: 10 candidates whose questions exceeded the 200-char
  linter limit were shortened during promotion per TRIAGE.md.
- Name-trim pass: 11 candidates whose `name` field exceeded 60 chars were
  shortened to pass the linter.
- Cross-reference repair: 7 `related_facets` entries pointing at stale
  candidate ids (pre-rename or pre-merge) were rewritten to their
  post-promotion targets.

### Absorbed (reviewer merges; candidates NOT separately promoted)
- `integration.survey.native_vs_external` → `process.survey.native_builder`
- `integration.web_form_to_record` → `integration.inbound_webhook.form_to_record`
- `process.transactional_notification` → `process.notification.status_change_transactional`
- `field.rollup_count` → `field.rollup_aggregate.child_to_parent`
- `entity.lead.conversion_with_attribution` → `process.attribution.lifecycle_persistence`
- `integration.external_id_crossref` → `entity.external_identifier.multi_source`
- `workflow.decision_rationale_capture` + `workflow.review.decision_rationale`
  → synthetic `workflow.decision_rationale`
- `integration.inbound_readonly.external_system_of_record` +
  `integration.external_signal_ingestion` → synthetic
  `integration.external_readonly_ingestion`

### Renamed (3 domain-specific candidates generalized)
- `entity.contribution.polymorphic_transaction_modeling` →
  `entity.transaction.polymorphic_typing`
- `entity.care_plan.nested_goal_intervention_tracking` →
  `entity.hierarchy.nested_with_versioning`
- `field.adherence_metric.computed_with_drift_alert` →
  `field.computed_metric.with_drift_alert`

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
