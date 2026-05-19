# KRK Control-Plane Strategy Arbitration Probe v0

This is a non-causal offline probe over filtered control-plane frames. It does not implement a runtime arbiter or authorize a sandbox.

## Label Coverage

- `strategy_benchmark_frame_count`: `28`
- `provider_labeled_frame_count`: `4`
- `frames_with_known_provider_mate`: `2`
- `frames_with_raw_scores`: `24`
- `frames_with_normalized_scores`: `28`
- `label_status`: `provider_labels_underpowered`

## Selector Results

### raw_global_score

- Selected count: `0`
- Known selected count: `0`
- Mate / max_plies / unknown: `0` / `0` / `0`
- Known selected mate rate: `None`

### normalized_score

- Selected count: `4`
- Known selected count: `4`
- Mate / max_plies / unknown: `1` / `3` / `0`
- Known selected mate rate: `0.25`

### provider_local_rank

- Selected count: `4`
- Known selected count: `4`
- Mate / max_plies / unknown: `1` / `3` / `0`
- Known selected mate rate: `0.25`

## Decision

- Status: `provider_labels_underpowered`
- Interpretation: The filtered control-plane frames are useful as a common evidence substrate, but provider-level conversion labels are too sparse for a reliable learned strategy-arbitration benchmark.
- Recommended next slice: `provider_label_coverage_plan_v0`
- Causal next step allowed: `False`
