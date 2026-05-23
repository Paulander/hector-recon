# KRK Ownership Label Recovery Review v0

This review joins dataset v5 candidate-generation trace context with existing ownership labels. It is a non-causal label-recovery review, not selector training.

## Decision

- status: `ownership_label_recovery_seed_manifest_ready_selector_blocked`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `build_non_causal_selector_objective_seed_manifest`

## Summary

- ownership_row_count: `41`
- ownership_target_label_counts: `{'selected_owner_converted': 31, 'selected_owner_failed': 10}`
- ownership_source_stage_counts: `{'stage4': 19, 'stage5': 14, 'stage6': 8}`
- ownership_provider_family_counts: `{'edge_trap': 3, 'fence_established': 1, 'stage0_basin': 37}`
- selector_training_row_count: `0`
- stage7_row_count: `0`
- runtime_trace_provider_candidate_row_count: `28`
- joined_state_count: `4`
- joined_recovery_class_counts: `{'safe_preservation_with_visible_positive_alternative': 2, 'selected_failure_with_visible_positive_alternative': 2}`
- selected_failure_with_visible_positive_alternative_count: `2`
- safe_preservation_with_visible_positive_alternative_count: `2`
- paired_threshold_passing_model_count: `2`
- paired_runtime_feature_passing_model_count: `0`
- progress_sandbox_primary_failure_class: `candidate_set_missing_good_alternative`
- candidate_context_ready: `True`

## Label Recovery Gaps

- `ownership labels are still offline evidence and not selector-training rows`
- `provider-family diversity remains narrow, especially stage0_basin-heavy`
- `paired objective semantics pass only with offline outcome/channel labels`
- `runtime feature translation remains unresolved for a general selector`
- `progress-window sandbox failure showed candidate-set coverage can still be missing`

## Forbidden Uses

- `selector_training`
- `score_changes`
- `provider_routing`
- `capacity_labels_as_ownership_labels`
- `stage7_training_or_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`

## Joined Records

- `state.02feb8593cc6` selected_owner_converted krk.fence_established trace_candidates=12 positive_trace_candidates=12 class=`safe_preservation_with_visible_positive_alternative`
- `state.326222aefdf1` selected_owner_converted krk.edge_trap_close trace_candidates=12 positive_trace_candidates=12 class=`safe_preservation_with_visible_positive_alternative`
- `state.3dca34326fca` selected_owner_failed krk.stage0_basin trace_candidates=3 positive_trace_candidates=3 class=`selected_failure_with_visible_positive_alternative`
- `state.699f0003a511` selected_owner_failed krk.edge_trap_close trace_candidates=1 positive_trace_candidates=1 class=`selected_failure_with_visible_positive_alternative`
