# KRK Selector Objective Diverse Collection Review Packet v0

This packet defines a future bounded Stage 5/6 observation-only collection. It is not approval to execute the collection.

## Decision

- status: `selector_objective_diverse_collection_review_ready`
- runtime_review_ready: `True`
- implementation_authorized_by_this_packet: `False`
- selector_training_allowed: `False`
- recommended_next_step: `explicit_approval_required_before_diverse_observation_collection`

## Summary

- review_row_count: `8`
- stage_counts: `{'stage5': 7, 'stage6': 1}`
- owner_label_counts: `{'selected_owner_converted': 6, 'selected_owner_failed': 2}`
- provider_family_counts: `{'edge_trap': 3, 'fence_established': 1, 'stage0_basin': 4}`
- switch_contrast_candidate_count: `2`
- safe_preservation_candidate_count: `6`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- runtime_collection_allowed_row_count: `0`
- stage4_row_count: `0`
- stage7_row_count: `0`
- stage8_row_count: `0`

## Review Rows

- `selector_objective_diverse_collection.01` state=state.02feb8593cc6 stage=stage5 provider=krk.fence_established label=selected_owner_converted reason=non_stage0_safe_seed_needs_joined_observation
- `selector_objective_diverse_collection.02` state=state.326222aefdf1 stage=stage5 provider=krk.edge_trap_close label=selected_owner_converted reason=non_stage0_safe_seed_needs_joined_observation
- `selector_objective_diverse_collection.03` state=state.3dca34326fca stage=stage5 provider=krk.stage0_basin label=selected_owner_failed reason=switch_seed_needs_joined_observation
- `selector_objective_diverse_collection.04` state=state.699f0003a511 stage=stage6 provider=krk.edge_trap_close label=selected_owner_failed reason=non_stage0_switch_seed_needs_joined_observation
- `selector_objective_diverse_collection.05` state=state.87b1160e68b9 stage=stage5 provider=krk.edge_trap_close label=selected_owner_converted reason=unseeded_non_stage0_safe_ownership_row
- `selector_objective_diverse_collection.06` state=state.7b116c49a009 stage=stage5 provider=krk.stage0_basin label=selected_owner_converted reason=stage5_6_safe_preservation_fill_row
- `selector_objective_diverse_collection.07` state=state.7bd8961882ad stage=stage5 provider=krk.stage0_basin label=selected_owner_converted reason=stage5_6_safe_preservation_fill_row
- `selector_objective_diverse_collection.08` state=state.7cab65617cd8 stage=stage5 provider=krk.stage0_basin label=selected_owner_converted reason=stage5_6_safe_preservation_fill_row
