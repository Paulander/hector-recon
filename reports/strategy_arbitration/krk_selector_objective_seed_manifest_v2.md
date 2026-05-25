# KRK Selector Objective Seed Manifest v2

This manifest adds Stage 4 observation-only trace rows to the non-causal selector-objective seed set. It remains evidence only.

## Decision

- status: `selector_objective_seed_manifest_v2_ready_non_causal`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `probe_selector_objective_seed_manifest_v2`

## Summary

- input_seed_v1_row_count: `12`
- stage4_joined_row_count: `6`
- added_stage4_seed_row_count: `6`
- seed_row_count: `18`
- objective_channel_counts: `{'candidate_switch_contrast_seed': 5, 'failure_context_without_candidate_seed': 5, 'safe_preservation_contrast_seed': 8}`
- recovery_class_counts: `{'safe_preservation_with_visible_positive_alternative': 8, 'selected_failure_with_visible_positive_alternative': 4, 'stage4_selected_failure_trace_context_only': 5, 'stage4_selected_failure_with_visible_positive_capacity': 1}`
- source_stage_counts: `{'stage4': 6, 'stage5': 8, 'stage6': 4}`
- candidate_switch_contrast_seed_count: `5`
- safe_preservation_contrast_seed_count: `8`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`

## Seed Rows

- `state.02feb8593cc6` stage=stage5 channel=`safe_preservation_contrast_seed` selected=krk.fence_established label=selected_owner_converted positive_trace_candidates=12
- `state.0b1f2153179b` stage=stage5 channel=`candidate_switch_contrast_seed` selected=krk.stage0_basin label=selected_owner_failed positive_trace_candidates=10
- `state.18cfccc9c4c1` stage=stage5 channel=`safe_preservation_contrast_seed` selected=krk.stage0_basin label=selected_owner_converted positive_trace_candidates=10
- `state.256a3da30f0f` stage=stage4 channel=`candidate_switch_contrast_seed` selected=krk.stage0_basin label=selected_owner_failed positive_trace_candidates=3
- `state.2c1d6da27ea1` stage=stage5 channel=`safe_preservation_contrast_seed` selected=krk.stage0_basin label=selected_owner_converted positive_trace_candidates=10
- `state.326222aefdf1` stage=stage5 channel=`safe_preservation_contrast_seed` selected=krk.edge_trap_close label=selected_owner_converted positive_trace_candidates=12
- `state.388d05197dd9` stage=stage5 channel=`safe_preservation_contrast_seed` selected=krk.stage0_basin label=selected_owner_converted positive_trace_candidates=10
- `state.3dca34326fca` stage=stage5 channel=`candidate_switch_contrast_seed` selected=krk.stage0_basin label=selected_owner_failed positive_trace_candidates=3
- `state.44938ccb8ab7` stage=stage4 channel=`failure_context_without_candidate_seed` selected=krk.stage0_basin label=selected_owner_failed positive_trace_candidates=0
- `state.52085d244e9d` stage=stage6 channel=`safe_preservation_contrast_seed` selected=krk.stage0_basin label=selected_owner_converted positive_trace_candidates=10
- `state.67a88e3b1dd2` stage=stage6 channel=`candidate_switch_contrast_seed` selected=krk.stage0_basin label=selected_owner_failed positive_trace_candidates=10
- `state.69711173114a` stage=stage6 channel=`safe_preservation_contrast_seed` selected=krk.stage0_basin label=selected_owner_converted positive_trace_candidates=10
- `state.699f0003a511` stage=stage6 channel=`candidate_switch_contrast_seed` selected=krk.edge_trap_close label=selected_owner_failed positive_trace_candidates=1
- `state.6e84c77a4520` stage=stage5 channel=`safe_preservation_contrast_seed` selected=krk.stage0_basin label=selected_owner_converted positive_trace_candidates=10
- `state.80080a9a826d` stage=stage4 channel=`failure_context_without_candidate_seed` selected=krk.stage0_basin label=selected_owner_failed positive_trace_candidates=0
- `state.b09c954a787e` stage=stage4 channel=`failure_context_without_candidate_seed` selected=krk.stage0_basin label=selected_owner_failed positive_trace_candidates=0
- `state.b11124d658cf` stage=stage4 channel=`failure_context_without_candidate_seed` selected=krk.stage0_basin label=selected_owner_failed positive_trace_candidates=0
- `state.ea634c29ece7` stage=stage4 channel=`failure_context_without_candidate_seed` selected=krk.stage0_basin label=selected_owner_failed positive_trace_candidates=0
