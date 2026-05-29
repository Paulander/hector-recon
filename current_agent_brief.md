# Current Agent Brief

## Active KRK Gate

- Completed the explicitly approved bounded joined trace/ownership observation collection.
- Collection artifact: `reports/strategy_arbitration/krk_joined_trace_ownership_collection_v0.json`.
- Seed artifacts: `reports/strategy_arbitration/krk_selector_objective_seed_manifest_v1.json` and `reports/strategy_arbitration/krk_selector_objective_seed_probe_v1.json`.
- Follow-up non-causal feature probe ran and is blocked: `selector_feature_probe_blocks_runtime_needs_diverse_evidence`.

## Verified Invariants

- Scope stayed Stage 5/6 only, max 8 rows; Stage 4/7/8 excluded.
- Observation-only trace/proposal/ownership data; no selector training and no runtime selector authorization.
- Selected move/provider unchanged; score and routing deltas are zero.
- Runtime DTM/tablebase use is false.
- Gameplay-time topology mutation is false.
- Stage 7 promotion and Stage 8 training remain blocked.

## Next Needed Work

- Collect or review more diverse joined trace/ownership evidence before any selector runtime review.
- Do not set runtime-selector-ready from the current seed or feature probe.
