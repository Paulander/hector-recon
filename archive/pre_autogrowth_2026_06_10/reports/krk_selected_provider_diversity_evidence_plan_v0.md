# KRK Selected Provider Diversity Evidence Plan v0

This is a non-causal design plan. It does not sample, label, implement a selector, promote Stage 7, or train Stage 8.

## Purpose

Fill the remaining selector-readiness gap by finding protected Stage4/5/6 states where normal arbitration selects diverse validated providers, without using Stage7 training rows.

## Evidence Gap

- Gap: `selected_provider_family_diversity_missing`
- Current selected provider families: `['edge_trap']`
- Required selected provider families: `3`
- Stage 7 training rows allowed: `0`

## Allowed Collection Phases

- `replay_free_scan` status=`allowed`: Search existing Stage4/5/6 artifacts for selected provider families beyond stage0_basin/edge_trap.
- `bounded_protected_sampling_manifest` status=`design_only_until_reviewed`: If replay-free scan fails, propose small h40 protected-only sampling jobs with no Stage7 rows.
- `label_execution` status=`blocked_until_manifest_review`: Run labels only after an explicit manifest and review, with diagnostic caches and failure traces only.

## Decision

- Status: `selected_provider_diversity_evidence_plan_defined`
- Recommended next step: `run_replay_free_selected_provider_diversity_scan`
- Runtime arbiter and selector sandbox remain blocked.
