# KRK Control-Plane Strategy Arbitration Probe v0

This is a non-causal offline probe over filtered control-plane frames. It does not implement a runtime arbiter or authorize a sandbox.

## Label Coverage

- `strategy_benchmark_frame_count`: `24`
- `provider_labeled_frame_count`: `24`
- `frames_with_known_provider_mate`: `12`
- `frames_with_raw_scores`: `24`
- `frames_with_normalized_scores`: `24`
- `label_status`: `provider_labels_sufficient_for_small_probe`

## Selector Results

### raw_global_score

- Selected count: `24`
- Known selected count: `24`
- Mate / max_plies / unknown: `12` / `12` / `0`
- Known selected mate rate: `0.5`

### normalized_score

- Selected count: `24`
- Known selected count: `24`
- Mate / max_plies / unknown: `12` / `12` / `0`
- Known selected mate rate: `0.5`

### provider_local_rank

- Selected count: `24`
- Known selected count: `24`
- Mate / max_plies / unknown: `12` / `12` / `0`
- Known selected mate rate: `0.5`

## Decision

- Status: `provider_labels_sufficient_for_small_probe`
- Interpretation: Provider labels are sufficient for a small non-causal arbitration benchmark.
- Recommended next slice: `offline_strategy_arbitration_baseline_v1`
- Causal next step allowed: `False`
