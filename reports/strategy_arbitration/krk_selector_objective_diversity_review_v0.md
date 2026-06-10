# KRK Selector Objective Diversity Review v0

This non-causal review evaluates the selector-objective evidence path after the joined trace/ownership collection and feature probe. It does not authorize selector runtime work.

## Decision

- status: `selector_objective_diverse_collection_review_ready`
- selector_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `write_selector_objective_diverse_collection_review_packet_v0`

## Questions

- what_evidence_is_missing: `['more_selected_owner_failed_switch_rows', 'more_non_stage0_selected_owner_rows', 'joined_trace_observation_for_non_stage0_seed_rows', 'provider_family_diversity_beyond_stage0_basin', 'failure_type_diversity_beyond_current_stage0_basin_failures']`
- too_few_rows: `False`
- too_few_providers: `True`
- too_few_failure_types: `True`
- too_few_stages: `False`
- stage0_basin_dominance: `True`
- can_recover_more_replay_free_from_existing_artifacts: `False`
- why_replay_free_recovery_is_not_enough: `Stage5/6 replay-free ownership rows not already in the seed set add safe-preservation rows but do not add enough switch or non-stage0 ownership evidence, and rows without joined trace observation should not be promoted into trace/ownership seeds.`

## Summary

- collection_status: `joined_trace_ownership_collection_complete_seed_improved`
- seed_probe_status: `selector_objective_seed_ready_for_non_causal_feature_probe`
- feature_review_status: `selector_feature_probe_blocks_runtime_needs_diverse_evidence`
- seed_row_count: `12`
- seed_stage_counts: `{'stage5': 8, 'stage6': 4}`
- seed_owner_label_counts: `{'selected_owner_converted': 8, 'selected_owner_failed': 4}`
- seed_provider_family_counts: `{'edge_trap': 2, 'fence_established': 1, 'stage0_basin': 9}`
- seed_stage0_basin_ratio: `0.75`
- joined_collection_provider_counts: `{'krk.stage0_basin': 8}`
- stage5_6_ownership_context_row_count: `22`
- replay_free_extra_stage5_6_row_count: `10`
- replay_free_extra_owner_label_counts: `{'selected_owner_converted': 10}`
- replay_free_extra_provider_family_counts: `{'edge_trap': 1, 'stage0_basin': 9}`
- replay_free_recovery_enough: `False`
- future_collection_candidate_count: `8`
- future_collection_stage_counts: `{'stage5': 7, 'stage6': 1}`
- future_collection_owner_label_counts: `{'selected_owner_converted': 6, 'selected_owner_failed': 2}`
- future_collection_provider_family_counts: `{'edge_trap': 3, 'fence_established': 1, 'stage0_basin': 4}`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`
- brief_present: `True`

## Future Collection Candidates

- `state.02feb8593cc6` stage=stage5 provider=krk.fence_established label=selected_owner_converted reason=non_stage0_safe_seed_needs_joined_observation
- `state.326222aefdf1` stage=stage5 provider=krk.edge_trap_close label=selected_owner_converted reason=non_stage0_safe_seed_needs_joined_observation
- `state.3dca34326fca` stage=stage5 provider=krk.stage0_basin label=selected_owner_failed reason=switch_seed_needs_joined_observation
- `state.699f0003a511` stage=stage6 provider=krk.edge_trap_close label=selected_owner_failed reason=non_stage0_switch_seed_needs_joined_observation
- `state.87b1160e68b9` stage=stage5 provider=krk.edge_trap_close label=selected_owner_converted reason=unseeded_non_stage0_safe_ownership_row
- `state.7b116c49a009` stage=stage5 provider=krk.stage0_basin label=selected_owner_converted reason=stage5_6_safe_preservation_fill_row
- `state.7bd8961882ad` stage=stage5 provider=krk.stage0_basin label=selected_owner_converted reason=stage5_6_safe_preservation_fill_row
- `state.7cab65617cd8` stage=stage5 provider=krk.stage0_basin label=selected_owner_converted reason=stage5_6_safe_preservation_fill_row
