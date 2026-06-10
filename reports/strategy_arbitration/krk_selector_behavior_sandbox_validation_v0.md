# KRK Selector Behavior Sandbox Validation v0

This report validates the existing default-off narrow selector behavior sandbox on protected Stage 5/6 rows with h40 playout comparison. It does not promote, make default, train, or broaden selector logic.

## Decision

- status: `selector_behavior_sandbox_regresses_safe_controls`
- promote: `False`
- make_default: `False`
- run_full_broad_guardrails: `False`
- write_guardrail_review_packet_only_if_ready: `False`
- train_anything: `False`
- stage7_promotion_allowed: `False`
- stage8_training_allowed: `False`

## Summary

- sample_count: `8`
- sample_scope: `stage5_6_protected_joined_trace_h40`
- default_off_equivalence_passed: `True`
- enabled_switch_count: `0`
- target_improvement_count: `0`
- safe_regression_count: `1`
- preserve_noop_count: `6`
- abstain_noop_count: `0`
- selected_move_delta_count: `0`
- selected_provider_delta_count: `0`
- score_delta_count: `0`
- routing_delta_count: `0`
- h40_improvement_count: `0`
- h40_regression_count: `1`
- shadow_candidate_delta_available: `False`
- per_stage_breakdown: `{'stage5': 5, 'stage6': 3}`
- per_provider_breakdown: `{'krk.stage0_basin': 8}`
- switch_source_term_coverage: `[]`
- invalid_switch_count: `0`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- runtime_dtm_or_tablebase: `False`
- topology_mutation: `False`
- capacity_label_used_as_ownership_label_count: `0`

## Rows

- `joined_trace_ownership_1` stage=stage5 role=switch_contrast recommendation=`prefer_visible_alternative` action=`no_op` target_improved=False safe_regression=False h40=max_plies->max_plies
- `joined_trace_ownership_2` stage=stage6 role=switch_contrast recommendation=`prefer_visible_alternative` action=`no_op` target_improved=False safe_regression=False h40=max_plies->max_plies
- `joined_trace_ownership_3` stage=stage5 role=safe_preservation recommendation=`preserve_selected_owner` action=`no_op` target_improved=False safe_regression=False h40=mate->mate
- `joined_trace_ownership_4` stage=stage5 role=safe_preservation recommendation=`preserve_selected_owner` action=`no_op` target_improved=False safe_regression=True h40=mate->max_plies
- `joined_trace_ownership_5` stage=stage5 role=safe_preservation recommendation=`preserve_selected_owner` action=`no_op` target_improved=False safe_regression=False h40=mate->mate
- `joined_trace_ownership_6` stage=stage6 role=safe_preservation recommendation=`preserve_selected_owner` action=`no_op` target_improved=False safe_regression=False h40=mate->mate
- `joined_trace_ownership_7` stage=stage6 role=safe_preservation recommendation=`preserve_selected_owner` action=`no_op` target_improved=False safe_regression=False h40=mate->mate
- `joined_trace_ownership_8` stage=stage5 role=safe_preservation recommendation=`preserve_selected_owner` action=`no_op` target_improved=False safe_regression=False h40=mate->mate
