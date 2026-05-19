# KRK Control-Plane Strategy Arbitration Baseline v1

This is a non-causal offline selector baseline over existing filtered ControlPlaneEvidenceFrame records. It does not implement a runtime arbiter, add terminals, run playouts, train Stage 8, or promote Stage 7.

## Frame Summary

- `strategy_benchmark_frame_count`: `28`
- `stage_counts`: `{'stage7': 4, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- `proposal_label_counts`: `{'max_plies': 50, 'mate': 16}`
- `frames_with_provider_mate`: `14`
- `frames_with_only_provider_max_plies`: `14`

## Selector Results

### raw_global_score

- Selected count: `24`
- Selected labels: `{'no_selection': 4, 'mate': 12, 'max_plies': 12}`
- Positive-available frames: `14`
- Positive hit count: `12`
- Positive hit rate: `0.8571428571428571`
- Selected mate rate: `0.5`

### normalized_score

- Selected count: `28`
- Selected labels: `{'max_plies': 15, 'mate': 13}`
- Positive-available frames: `14`
- Positive hit count: `13`
- Positive hit rate: `0.9285714285714286`
- Selected mate rate: `0.4642857142857143`

### provider_local_rank

- Selected count: `28`
- Selected labels: `{'max_plies': 15, 'mate': 13}`
- Positive-available frames: `14`
- Positive hit count: `13`
- Positive hit rate: `0.9285714285714286`
- Selected mate rate: `0.4642857142857143`

### visible_context_heuristic

- Selected count: `1`
- Selected labels: `{'max_plies': 1, 'no_selection': 27}`
- Positive-available frames: `14`
- Positive hit count: `0`
- Positive hit rate: `0.0`
- Selected mate rate: `0.0`

### stage_prior_heuristic

- Selected count: `28`
- Selected labels: `{'max_plies': 15, 'mate': 13}`
- Positive-available frames: `14`
- Positive hit count: `13`
- Positive hit rate: `0.9285714285714286`
- Selected mate rate: `0.4642857142857143`

## Context Summary

- Box relevance by edge bucket: `{'near_edge|medium': 1, 'central|high': 3, 'at_edge|low': 24}`

## Decision

- Status: `strategy_arbitration_promising`
- Recommended next class: `non_causal_strategy_arbiter_sandbox_design`
- Interpretation: Existing provider labels are sufficient for a small offline baseline. At least one simple selector can recover many converting providers when one is present, but this remains non-causal and too small for runtime promotion.
- Causal next step allowed: `False`
