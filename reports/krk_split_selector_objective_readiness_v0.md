# KRK Split Selector Objective Readiness v0

Readiness review after splitting forced-provider capacity evidence into separate objective channels.

## Summary

- `objective_channel_count`: `4`
- `selector_training_row_count`: `0`
- `stage7_row_count`: `0`
- `ownership_selection_available`: `False`
- `capacity_risk_best_objective`: `piece_motion@0.5`
- `capacity_risk_best_negative_suppression`: `0.7777777777777778`
- `capacity_risk_best_positive_recall`: `0.9032258064516129`

## Channel Readiness

- `capacity_recall` status=`offline_evidence_available` ready_for=`candidate_recall_benchmark_only` blocked_for=`runtime ownership selection`. positive capacity rows identify providers worth including, not selecting.
- `capacity_risk` status=`offline_feature_signal_promising` ready_for=`capacity-risk feature review` blocked_for=`runtime suppression or selector training`. best feature `piece_motion@0.5` reaches negative suppression `0.7777777777777778` but labels are forced-path risk, not ownership.
- `safe_preservation` status=`offline_evidence_available` ready_for=`preservation constraint design` blocked_for=`positive runtime ownership selection`. safe rows define what future suppressors must not break.
- `ownership_selection` status=`missing_label_channel` ready_for=`nothing beyond requirements definition` blocked_for=`selector training and runtime behavior`. forced-provider labels do not identify normal-routing owner choice.

## Minimum Before Selector Training

- ownership_selection labels from normal-routing or paired-selection evidence
- safe-preservation gate that protects validated converting providers
- capacity-risk feature reviewed as auxiliary risk, not direct target
- default-off sandbox review after offline objectives are separated

## Decision

- `status`: `split_objectives_fixed_semantics_runtime_still_blocked`
- `recommended_next_step`: `collect_or_recover_ownership_selection_labels_before_selector_training`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
