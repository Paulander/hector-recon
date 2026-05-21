# KRK State-Local Paired Runtime Proxy Probe v0

Non-causal check of visible proxy candidates against the paired-ownership semantic targets.

## Summary

- `row_count`: `40`
- `state_count`: `14`
- `failure_risk_target_count`: `7`
- `safe_preservation_target_count`: `33`
- `safe_preservation_pair_count`: `23`
- `source_stage_counts`: `{'stage4': 13, 'stage5': 14, 'stage6': 13}`
- `comparison_label_counts`: `{'equivalent_positive_or_preserve_selected': 23, 'abstain_or_insufficient_safe_owner': 8, 'prefer_capacity_alternative': 7, 'prefer_selected_owner': 2}`
- `stage7_row_count`: `0`
- `selector_training_row_count`: `0`
- `runtime_visible_failure_proxy_model_count`: `2`
- `runtime_visible_preservation_proxy_model_count`: `3`
- `visible_proxy_review_ready`: `False`

## Best Visible Failure-Risk Proxy

- `model_id`: `failure_risk_visible_pair_context@0.25`
- `model_kind`: `leave_state_out_proxy_feature_model`
- `target`: `selected_owner_failure_risk_target`
- `features`: `['runtime:family_pair', 'runtime:source_stage', 'runtime:box_area_relevance', 'runtime:selected_piece', 'runtime:box_area_delta']`
- `threshold`: `0.25`
- `runtime_feature_eligible`: `True`
- `notes`: `Lower threshold visible proxy model, useful for sensitivity but risky for preservation.`
- `row_count`: `40`
- `true_positive`: `0`
- `false_positive`: `0`
- `true_negative`: `33`
- `false_negative`: `7`
- `accuracy`: `0.825`
- `precision`: `None`
- `recall`: `0.0`
- `negative_recall`: `1.0`

## Best Visible Safe-Preservation Proxy

- `model_id`: `safe_preservation_visible_pair_context@0.5`
- `model_kind`: `leave_state_out_proxy_feature_model`
- `target`: `safe_preservation_confidence_target`
- `features`: `['runtime:family_pair', 'runtime:source_stage', 'runtime:black_king_edge_bucket', 'runtime:white_king_support_bucket', 'runtime:box_area_delta']`
- `threshold`: `0.5`
- `runtime_feature_eligible`: `True`
- `notes`: `Visible pair/context preservation confidence model.`
- `row_count`: `40`
- `true_positive`: `33`
- `false_positive`: `7`
- `true_negative`: `0`
- `false_negative`: `0`
- `accuracy`: `0.825`
- `precision`: `0.825`
- `recall`: `1.0`
- `negative_recall`: `0.0`

## Proxy Gap Analysis

- `selected_owner_failure_risk_false_negative_count`: `7`
- `interpretation`: The available visible proxy terms mostly describe board context and owner families. They do not expose why the selected owner is failing in the current local control window, so leave-state-out failure-risk recall collapses to zero.
- `missing_visible_failure_risk_terms`:
- `selected_owner_progress_stagnation_visible`
- `selected_owner_repeated_failure_family_visible`
- `selected_owner_score_conflict_or_scale_gap_visible`
- `alternative_provider_live_proposal_with_role_license`
- `selected_owner_handoff_gap_visible`
- `normal_routing_selected_owner_failure_risk_prior_by_context`

## Decision

- `status`: `visible_runtime_proxy_features_insufficient`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `recommended_next_step`: `review_proxy_feature_gaps_before_runtime`
