# KRK Selector Objective Seed Manifest v1

This manifest adds bounded joined trace/ownership collection rows to the non-causal selector-objective seed set. It is not selector training data.

## Decision

- status: `selector_objective_seed_manifest_v1_ready_non_causal`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `probe_selector_objective_seed_manifest_v1`

## Summary

- input_seed_v0_row_count: `4`
- collection_joined_row_count: `8`
- added_collection_seed_row_count: `8`
- seed_row_count: `12`
- objective_channel_counts: `{'candidate_switch_contrast_seed': 4, 'safe_preservation_contrast_seed': 8}`
- recovery_class_counts: `{'safe_preservation_with_visible_positive_alternative': 8, 'selected_failure_with_visible_positive_alternative': 4}`
- source_stage_counts: `{'stage5': 8, 'stage6': 4}`
- candidate_switch_contrast_seed_count: `4`
- safe_preservation_contrast_seed_count: `8`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`

## Seed Rows

- `state.02feb8593cc6` channel=`safe_preservation_contrast_seed` selected=krk.fence_established label=selected_owner_converted positive_trace_candidates=12
- `state.0b1f2153179b` channel=`candidate_switch_contrast_seed` selected=krk.stage0_basin label=selected_owner_failed positive_trace_candidates=10
- `state.18cfccc9c4c1` channel=`safe_preservation_contrast_seed` selected=krk.stage0_basin label=selected_owner_converted positive_trace_candidates=10
- `state.2c1d6da27ea1` channel=`safe_preservation_contrast_seed` selected=krk.stage0_basin label=selected_owner_converted positive_trace_candidates=10
- `state.326222aefdf1` channel=`safe_preservation_contrast_seed` selected=krk.edge_trap_close label=selected_owner_converted positive_trace_candidates=12
- `state.388d05197dd9` channel=`safe_preservation_contrast_seed` selected=krk.stage0_basin label=selected_owner_converted positive_trace_candidates=10
- `state.3dca34326fca` channel=`candidate_switch_contrast_seed` selected=krk.stage0_basin label=selected_owner_failed positive_trace_candidates=3
- `state.52085d244e9d` channel=`safe_preservation_contrast_seed` selected=krk.stage0_basin label=selected_owner_converted positive_trace_candidates=10
- `state.67a88e3b1dd2` channel=`candidate_switch_contrast_seed` selected=krk.stage0_basin label=selected_owner_failed positive_trace_candidates=10
- `state.69711173114a` channel=`safe_preservation_contrast_seed` selected=krk.stage0_basin label=selected_owner_converted positive_trace_candidates=10
- `state.699f0003a511` channel=`candidate_switch_contrast_seed` selected=krk.edge_trap_close label=selected_owner_failed positive_trace_candidates=1
- `state.6e84c77a4520` channel=`safe_preservation_contrast_seed` selected=krk.stage0_basin label=selected_owner_converted positive_trace_candidates=10
