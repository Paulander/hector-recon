# Stage 7 Clean Sequence Control Recovery v0

Status: `clean_sequence_controls_recovered_for_offline_source_bias_audit`

Replay-free recovery of clean Stage 7 sequence controls from manifest-approved current-profile/default-off artifacts.

## Summary

- control_count: `50`
- role_counts: `{'clean_sequence_hard_negative': 39, 'clean_sequence_success_control': 11}`
- result_counts: `{'max_plies': 39, 'mate': 11}`
- selected_provider_counts: `{'krk.edge_trap_close': 6, 'krk.stage0_basin': 33, 'None': 1, 'krk.drive_to_edge': 9, 'krk.fence_established': 1}`
- source_classification_counts: `{'clean_current_profile_candidate': 5, 'clean_default_off_candidate': 5, 'clean_baseline_candidate': 40}`
- source_artifact_counts: `{'reports/krk_two_stage_abstention_stage7_baseline_3_seed11_h40.json': 3, 'reports/structural_candidates/stage7_2cc_frozen_model_default_off_smoke_5_h20.json': 1, 'reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_a_seed149_8_h40.json': 8, 'reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_b_seed151_8_h40.json': 8, 'reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_c_seed157_8_h40.json': 8, 'reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_d_seed163_8_h40.json': 8, 'reports/structural_candidates/stage7_candidate_move_layer_default_off_10_h40.json': 2, 'reports/structural_candidates/stage7_diverse_clean_edge_fence_deep_seed107_8_h40.json': 8, 'reports/structural_candidates/stage7_family_ac_fence_noaugment_default_off_5_h40.json': 2, 'reports/structural_candidates/stage7_king_tempo_baseline_10_h40.json': 2}`
- skipped_counts: `{'non_mate_not_h40': 68, 'duplicate_control': 193, 'horizon_above_h40': 25}`
- duplicate_source_key_count: `10`
- usable_for_offline_benchmark: `True`
- usable_for_runtime_authorization: `False`

## Acceptance

- clean_sequence_success_controls_required: `5`
- clean_sequence_hard_negatives_required: `5`
- clean_sequence_success_controls_met: `True`
- clean_sequence_hard_negatives_met: `True`
- runtime_authorization_allowed: `False`

## Controls

- `clean.4d979dff05b0` clean_sequence_hard_negative result=`max_plies` provider=`krk.edge_trap_close` source=`reports/krk_two_stage_abstention_stage7_baseline_3_seed11_h40.json`
- `clean.5026622a62dd` clean_sequence_success_control result=`mate` provider=`krk.edge_trap_close` source=`reports/krk_two_stage_abstention_stage7_baseline_3_seed11_h40.json`
- `clean.3b9c91ab4afd` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/krk_two_stage_abstention_stage7_baseline_3_seed11_h40.json`
- `clean.d11f73c6a7d7` clean_sequence_success_control result=`mate` provider=`None` source=`reports/structural_candidates/stage7_2cc_frozen_model_default_off_smoke_5_h20.json`
- `clean.a009a84526ac` clean_sequence_success_control result=`mate` provider=`krk.drive_to_edge` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_a_seed149_8_h40.json`
- `clean.94b02c4c0090` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_a_seed149_8_h40.json`
- `clean.1ca478f93a90` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_a_seed149_8_h40.json`
- `clean.68e7a0bb85c7` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_a_seed149_8_h40.json`
- `clean.f76de7b3de8d` clean_sequence_hard_negative result=`max_plies` provider=`krk.drive_to_edge` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_a_seed149_8_h40.json`
- `clean.07d6cd11e606` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_a_seed149_8_h40.json`
- `clean.220c65493fd4` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_a_seed149_8_h40.json`
- `clean.71acf7cfe8f6` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_a_seed149_8_h40.json`
- `clean.a3d42336dd63` clean_sequence_hard_negative result=`max_plies` provider=`krk.drive_to_edge` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_b_seed151_8_h40.json`
- `clean.92872c0a3c4b` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_b_seed151_8_h40.json`
- `clean.e09a71bf6570` clean_sequence_success_control result=`mate` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_b_seed151_8_h40.json`
- `clean.dad828f0a217` clean_sequence_hard_negative result=`max_plies` provider=`krk.fence_established` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_b_seed151_8_h40.json`
- `clean.835f5f087455` clean_sequence_success_control result=`mate` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_b_seed151_8_h40.json`
- `clean.89d81a850d6d` clean_sequence_success_control result=`mate` provider=`krk.edge_trap_close` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_b_seed151_8_h40.json`
- `clean.d7c7a4dc15d3` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_b_seed151_8_h40.json`
- `clean.589546d8d3d0` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_b_seed151_8_h40.json`
- `clean.a8b39f35fe02` clean_sequence_success_control result=`mate` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_c_seed157_8_h40.json`
- `clean.d0ada980ab96` clean_sequence_hard_negative result=`max_plies` provider=`krk.drive_to_edge` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_c_seed157_8_h40.json`
- `clean.defa7ff9fb3a` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_c_seed157_8_h40.json`
- `clean.c2eb8f0e2845` clean_sequence_hard_negative result=`max_plies` provider=`krk.drive_to_edge` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_c_seed157_8_h40.json`
- `clean.e456cb4f4d92` clean_sequence_hard_negative result=`max_plies` provider=`krk.edge_trap_close` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_c_seed157_8_h40.json`
- `clean.43ee495ac0cd` clean_sequence_success_control result=`mate` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_c_seed157_8_h40.json`
- `clean.3034b8803793` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_c_seed157_8_h40.json`
- `clean.7fb8006ed812` clean_sequence_success_control result=`mate` provider=`krk.edge_trap_close` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_c_seed157_8_h40.json`
- `clean.a88cbe80b582` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_d_seed163_8_h40.json`
- `clean.02298bc0f2eb` clean_sequence_hard_negative result=`max_plies` provider=`krk.drive_to_edge` source=`reports/structural_candidates/stage7_additional_clean_edge_fence_deep_followup_d_seed163_8_h40.json`
- ... `20` additional controls omitted

Next step: `build_clean_selected_path_dataset_and_source_bias_audit`
