# KRK Candidate-Generation Scope Gap Review v0

This non-causal review identifies what is still missing before any new candidate-generation runtime boundary can be considered.

## Decision

- status: `candidate_generation_scope_gap_review_blocks_new_runtime_boundary`
- runtime_changes_allowed: `False`
- selector_allowed: `False`
- recommended_next_step: `candidate_source_gap_manifest_non_causal`

## Summary

- capacity_row_count: `36`
- trace_row_count: `31`
- capacity_by_stage: `{'stage4': 11, 'stage5': 16, 'stage6': 9}`
- trace_by_stage: `{'stage4': 1, 'stage5': 28, 'stage6': 2}`
- capacity_by_family: `{'drive_to_edge': 1, 'edge_trap': 18, 'fence_established': 3, 'stage0_basin': 14}`
- trace_by_family: `{'edge_trap': 19, 'fence_established': 3, 'stage0_basin': 3, 'terminal.krk.repair_needed_monitor': 6}`
- exact_positive_capacity_recall_from_refresh_trace: `0.19230769230769232`
- policy_cell_positive_capacity_recall_from_refresh_trace: `0.7692307692307693`
- policy_cell_negative_capacity_exposure_from_refresh_trace: `0.0`
- selector_training_row_count: `0`
- stage7_readiness_training_row_count: `0`

## Scope Gaps

- `exact_move_provider_coverage_partial`
- `ownership_selector_labels_absent`
- `plan_sequence_candidate_trace_missing`
- `stage7_held_out_only`

## Candidate Next Non-Causal Slices

- `candidate_source_gap_manifest`: Identify which positive-capacity stage/family cells lack exact runtime-observation trace coverage. runtime_allowed=`False`
- `protected_stage4_scope_review`: Decide whether Stage 4 can be added to candidate-generation observation scope without changing behavior. runtime_allowed=`False`
- `plan_sequence_candidate_trace_review`: Review whether PlanCapsule/sequence candidates need observation frames distinct from provider-pack candidates. runtime_allowed=`False`

## Still Forbidden

- `selector_training`
- `score_changes`
- `provider_routing`
- `new_runtime_sandbox_without_review_packet`
- `guardrail_campaign_from_context_only`
- `stage7_promotion`
- `stage8_training`
