# KRK Split Selector Objective Readiness v2

Readiness review after expanding normal-routing ownership-selection labels.

## Summary

- `objective_channel_count`: `4`
- `selector_training_row_count`: `0`
- `stage7_row_count`: `0`
- `ownership_selection_available`: `True`
- `ownership_selection_row_count`: `34`
- `ownership_probe_negative_suppression`: `0.5555555555555556`
- `ownership_probe_positive_recall`: `0.56`
- `ownership_probe_underpowered`: `True`
- `capacity_risk_best_negative_suppression`: `0.7777777777777778`
- `capacity_risk_best_positive_recall`: `0.9032258064516129`

## Readiness

- `capacity_recall`: `available_for_candidate_recall_benchmark`
- `capacity_risk`: `promising_auxiliary_risk_signal`
- `safe_preservation`: `available_as_preservation_constraint`
- `ownership_selection`: `recovered_but_underpowered`

## Minimum Before Selector Training

- architecture review of recovered ownership-selection semantics
- safe-preservation gate combined with ownership and capacity-risk objectives
- default-off sandbox review if offline evidence is accepted
- no Stage 7 training rows and no runtime DTM/tablebase

## Decision

- `status`: `ownership_labels_recovered_but_underpowered`
- `recommended_next_step`: `collect_more_normal_routing_ownership_labels_or_review_underpowered_probe`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
