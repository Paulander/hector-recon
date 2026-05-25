# KRK Selector Objective Benchmark Review Packet v2

This packet reviews the non-causal selector-objective benchmark v2. It does not authorize runtime selector implementation.

## Decision

- status: `selector_objective_benchmark_review_ready_for_independent_validation`
- runtime_review_ready: `False`
- independent_validation_review_ready: `True`
- implementation_authorized_by_this_packet: `False`
- selector_allowed: `False`
- selector_training_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `run_bounded_independent_protected_selector_objective_validation`

## Best Visible Model

- model_id: `visible_failure_risk_heuristic_v2`
- model_kind: `fixed_visible_heuristic_probe`
- accuracy: `1.0`
- switch_precision: `1.0`
- switch_recall: `1.0`
- preserve_recall: `1.0`
- abstain_recall: `1.0`
- runtime_feature_eligible: `True`
- notes: `Non-causal visible-term probe only. Passing thresholds here justifies independent validation or a review packet, not runtime selector use.`

## Independent Validation Acceptance

- protected_stages: `['stage4', 'stage5', 'stage6']`
- excluded_stages: `['stage7', 'stage8']`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- max_new_rows_first_slice: `12`
- target_metrics: `{'switch_precision_min': 0.7, 'switch_recall_min': 0.7, 'preserve_recall_min': 0.8, 'abstain_recall_min': 0.6}`

## Risks

- `best visible heuristic may be overfit to the current 18-row seed`
- `capacity evidence remains separate from ownership labels`
- `passing benchmark does not authorize runtime selector behavior`
- `Stage 7 remains held out and must not enter readiness training rows`

## Explicitly Forbidden

- `runtime_selector`
- `selector_training`
- `score_changes`
- `provider_suppression`
- `direct_provider_routing`
- `capacity_labels_as_ownership_labels`
- `stage7_training_or_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`
