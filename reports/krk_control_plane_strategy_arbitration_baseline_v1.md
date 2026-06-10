# KRK Control-Plane Strategy Arbitration Baseline v1

This is a non-causal offline selector baseline over existing filtered ControlPlaneEvidenceFrame records. It does not implement a runtime arbiter, add terminals, run playouts, train Stage 8, or promote Stage 7.

## Frame Summary

- `strategy_benchmark_frame_count`: `24`
- `stage_counts`: `{'stage5': 8, 'stage6': 10, 'stage4': 6}`
- `proposal_label_counts`: `{'mate': 14, 'max_plies': 28}`
- `frames_with_provider_mate`: `12`
- `frames_with_only_provider_max_plies`: `12`

## Selector Results

### raw_global_score

- Selected count: `24`
- Selected labels: `{'mate': 12, 'max_plies': 12}`
- Positive-available frames: `12`
- Positive hit count: `12`
- Positive hit rate: `1.0`
- Selected mate rate: `0.5`

### normalized_score

- Selected count: `24`
- Selected labels: `{'mate': 12, 'max_plies': 12}`
- Positive-available frames: `12`
- Positive hit count: `12`
- Positive hit rate: `1.0`
- Selected mate rate: `0.5`

### provider_local_rank

- Selected count: `24`
- Selected labels: `{'mate': 12, 'max_plies': 12}`
- Positive-available frames: `12`
- Positive hit count: `12`
- Positive hit rate: `1.0`
- Selected mate rate: `0.5`

### visible_context_heuristic

- Selected count: `0`
- Selected labels: `{'no_selection': 24}`
- Positive-available frames: `12`
- Positive hit count: `0`
- Positive hit rate: `0.0`
- Selected mate rate: `None`

### stage_prior_heuristic

- Selected count: `24`
- Selected labels: `{'mate': 12, 'max_plies': 12}`
- Positive-available frames: `12`
- Positive hit count: `12`
- Positive hit rate: `1.0`
- Selected mate rate: `0.5`

## Context Summary

- Box relevance by edge bucket: `{'at_edge|low': 24}`

## Decision

- Status: `strategy_arbitration_promising`
- Recommended next class: `non_causal_strategy_arbiter_sandbox_design`
- Interpretation: Existing provider labels are sufficient for a small offline baseline. At least one simple selector can recover many converting providers when one is present, but this remains non-causal and too small for runtime promotion.
- Causal next step allowed: `False`
