# KRK Selector Objective Seed Manifest v0

This manifest converts joined ownership-label and trace-context evidence into seed rows for future non-causal selector-objective review. It is not selector training data.

## Decision

- status: `selector_objective_seed_manifest_ready_non_causal`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `design_selector_objective_probe_from_seed_manifest`

## Summary

- seed_row_count: `4`
- objective_channel_counts: `{'candidate_switch_contrast_seed': 2, 'safe_preservation_contrast_seed': 2}`
- recovery_class_counts: `{'safe_preservation_with_visible_positive_alternative': 2, 'selected_failure_with_visible_positive_alternative': 2}`
- candidate_switch_contrast_seed_count: `2`
- safe_preservation_contrast_seed_count: `2`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`

## Seed Rows

- `state.02feb8593cc6` channel=`safe_preservation_contrast_seed` selected=krk.fence_established label=selected_owner_converted positive_trace_candidates=12
- `state.326222aefdf1` channel=`safe_preservation_contrast_seed` selected=krk.edge_trap_close label=selected_owner_converted positive_trace_candidates=12
- `state.3dca34326fca` channel=`candidate_switch_contrast_seed` selected=krk.stage0_basin label=selected_owner_failed positive_trace_candidates=3
- `state.699f0003a511` channel=`candidate_switch_contrast_seed` selected=krk.edge_trap_close label=selected_owner_failed positive_trace_candidates=1
