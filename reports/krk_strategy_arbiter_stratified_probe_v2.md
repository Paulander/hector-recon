# KRK Strategy Arbiter Stratified Probe v2

This is a non-causal, replay-free probe. It evaluates strategy-arbiter selectors separately for selected-provider playout labels, forced-provider labels, and same-move unselected-provider labels.

## Summary

- Benchmark frames: `28`
- Best selected-provider positive hit rate: `1.0`
- Best forced-provider positive hit rate: `0.5`
- Max-only classification counts: `{'forced_existing_provider_capacity_or_horizon_gap': 2, 'selected_playout_guardrail_or_horizon_caveat': 12}`

## Stratified Selector Results

### selected_provider_playout / raw_global_score

- Eligible frames: `24`
- Eligible stage counts: `{'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Selected labels: `{'mate': 12, 'max_plies': 12}`
- Positive hit rate: `1.0`
- Selected mate rate: `0.5`

### selected_provider_playout / normalized_score

- Eligible frames: `24`
- Eligible stage counts: `{'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Selected labels: `{'mate': 12, 'max_plies': 12}`
- Positive hit rate: `1.0`
- Selected mate rate: `0.5`

### selected_provider_playout / provider_local_rank

- Eligible frames: `24`
- Eligible stage counts: `{'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Selected labels: `{'mate': 12, 'max_plies': 12}`
- Positive hit rate: `1.0`
- Selected mate rate: `0.5`

### selected_provider_playout / stage_prior_heuristic

- Eligible frames: `24`
- Eligible stage counts: `{'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Selected labels: `{'mate': 12, 'max_plies': 12}`
- Positive hit rate: `1.0`
- Selected mate rate: `0.5`

### forced_provider_outcome / raw_global_score

- Eligible frames: `4`
- Eligible stage counts: `{'stage7': 4}`
- Selected labels: `{}`
- Positive hit rate: `0.0`
- Selected mate rate: `None`

### forced_provider_outcome / normalized_score

- Eligible frames: `4`
- Eligible stage counts: `{'stage7': 4}`
- Selected labels: `{'max_plies': 3, 'mate': 1}`
- Positive hit rate: `0.5`
- Selected mate rate: `0.25`

### forced_provider_outcome / provider_local_rank

- Eligible frames: `4`
- Eligible stage counts: `{'stage7': 4}`
- Selected labels: `{'max_plies': 3, 'mate': 1}`
- Positive hit rate: `0.5`
- Selected mate rate: `0.25`

### forced_provider_outcome / stage_prior_heuristic

- Eligible frames: `4`
- Eligible stage counts: `{'stage7': 4}`
- Selected labels: `{'max_plies': 3, 'mate': 1}`
- Positive hit rate: `0.5`
- Selected mate rate: `0.25`

### same_move_unselected_provider_playout / raw_global_score

- Eligible frames: `9`
- Eligible stage counts: `{'stage5': 4, 'stage6': 5}`
- Selected labels: `{'mate': 1, 'max_plies': 8}`
- Positive hit rate: `1.0`
- Selected mate rate: `0.1111111111111111`

### same_move_unselected_provider_playout / normalized_score

- Eligible frames: `9`
- Eligible stage counts: `{'stage5': 4, 'stage6': 5}`
- Selected labels: `{'mate': 1, 'max_plies': 8}`
- Positive hit rate: `1.0`
- Selected mate rate: `0.1111111111111111`

### same_move_unselected_provider_playout / provider_local_rank

- Eligible frames: `9`
- Eligible stage counts: `{'stage5': 4, 'stage6': 5}`
- Selected labels: `{'mate': 1, 'max_plies': 8}`
- Positive hit rate: `1.0`
- Selected mate rate: `0.1111111111111111`

### same_move_unselected_provider_playout / stage_prior_heuristic

- Eligible frames: `9`
- Eligible stage counts: `{'stage5': 4, 'stage6': 5}`
- Selected labels: `{'mate': 1, 'max_plies': 8}`
- Positive hit rate: `1.0`
- Selected mate rate: `0.1111111111111111`

## Decision

- Status: `selected_playout_controls_promising_forced_stage7_still_weak`
- Runtime sandbox allowed: `False`
- Recommended next step: `collect_or_review_forced_provider_controls_before_sandbox`
- Interpretation: Selected protected-control playout labels are easy for simple selectors, but forced-provider Stage7 labels remain the harder and smaller stratum.
