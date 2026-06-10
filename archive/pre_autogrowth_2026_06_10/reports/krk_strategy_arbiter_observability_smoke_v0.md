# KRK Strategy Arbiter Observability Smoke v0

This smoke test checks the default-off, trace-only `krk_strategy_arbiter_observability_skeleton_v0` authorized by `reports/krk_strategy_arbiter_architecture_review_v1.json`.

## Setup

- Topology: `snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile/topology/krk_entry_topology.json`
- Profile: `handoff_composition_v1`
- Label: `fence_established`
- Samples: `1`
- Seed: `7`
- Playout horizon: `4`

## Default-Off Equivalence

The default-off and enabled runs matched on behavior/outcome metrics:

- Playouts: `{'max_plies': 1}` in both runs.
- One-ply status: `{'failed': 1}` in both runs.
- Conversion status: `{'failed': 1}` in both runs.
- Average reward: `-0.75` in both runs.
- Average oracle reward: `0.14900000000000002` in both runs.
- Handoff packets: `3` in both runs.
- Shadow candidates: `0` in both runs.

The only expected delta was observation metadata:

- Default off observation count: `0`
- Enabled observation count: `1`

## Metadata Shape

The enabled diagnostic run emitted `krk_strategy_arbiter_observation.v0` metadata with:

- `causal_status = non_causal_observation`
- `direct_request = false`
- `score_delta = 0.0`
- `recommendation_only = true`
- `proposal_count = 10`
- `selected_provider_before_observation = krk.stage0_basin`

Required keys were present:

- `schema_version`
- `arbiter_id`
- `causal_status`
- `direct_request`
- `score_delta`
- `selected_provider_before_observation`
- `recommendation_only`
- `source_terms`
- `proposal_count`
- `provider_candidates`

## Decision

Status: `observability_skeleton_smoke_passed`

This does not authorize runtime arbitration. It only supports collecting small non-causal observation frames on protected controls and Stage 7 holdouts.
