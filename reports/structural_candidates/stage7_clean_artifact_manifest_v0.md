# Stage 7 Clean Artifact Manifest v0

Status: `clean_artifact_manifest_ready`

Replay-free classification of existing Stage 7 artifacts for clean-control recovery.

## Summary

- artifact_count: `336`
- classification_counts: `{'metadata_or_design_only': 184, 'clean_current_profile_candidate': 8, 'repair_sandbox_sourced': 118, 'ambiguous_needs_manual_review': 1, 'clean_default_off_candidate': 23, 'clean_baseline_candidate': 2}`
- clean_candidate_count: `33`
- repair_sandbox_sourced_count: `118`
- ambiguous_count: `1`

## Clean Candidates

- `reports/krk_two_stage_abstention_stage7_baseline_3_seed11_h40.json`: `clean_current_profile_candidate`, playouts=`{'max_plies': 2, 'mate': 1}`
- `reports/structural_candidates/stage7_2cc_frozen_model_default_off_smoke_5_h20.json`: `clean_default_off_candidate`, playouts=`{'mate': 2, 'max_plies': 3}`
- `reports/structural_candidates/stage7_box_shrink_support_adapter_default_off_local_1.json`: `clean_default_off_candidate`, playouts=`{}`
- `reports/structural_candidates/stage7_candidate_move_layer_default_off_10_h40.json`: `clean_default_off_candidate`, playouts=`{'mate': 5, 'max_plies': 5}`
- `reports/structural_candidates/stage7_candidate_move_layer_default_off_25_h40.json`: `clean_default_off_candidate`, playouts=`{'mate': 12, 'max_plies': 13}`
- `reports/structural_candidates/stage7_default_off_equiv_A_no_adapter_3_h5.json`: `clean_default_off_candidate`, playouts=`{'max_plies': 3}`
- `reports/structural_candidates/stage7_default_off_equiv_B_edge_adapter_off_3_h5.json`: `clean_default_off_candidate`, playouts=`{'max_plies': 3}`
- `reports/structural_candidates/stage7_default_off_equiv_B_support_adapter_off_3_h5.json`: `clean_default_off_candidate`, playouts=`{'max_plies': 3}`
- `reports/structural_candidates/stage7_drive_fence_paired_off_25_h80.json`: `clean_baseline_candidate`, playouts=`{'mate': 12, 'max_plies': 13}`
- `reports/structural_candidates/stage7_family_ac_fence_noaugment_default_off_5_h40.json`: `clean_current_profile_candidate`, playouts=`{'mate': 2, 'max_plies': 3}`
- `reports/structural_candidates/stage7_family_drive_default_off_A_base_5_h40.json`: `clean_current_profile_candidate`, playouts=`{'mate': 2, 'max_plies': 3}`
- `reports/structural_candidates/stage7_family_drive_default_off_B_sandbox_5_h40.json`: `clean_default_off_candidate`, playouts=`{'mate': 2, 'max_plies': 3}`
- `reports/structural_candidates/stage7_family_drive_moveshape_default_off_A_base_5_h40.json`: `clean_current_profile_candidate`, playouts=`{'mate': 2, 'max_plies': 3}`
- `reports/structural_candidates/stage7_family_drive_moveshape_default_off_B_sandbox_5_h40.json`: `clean_default_off_candidate`, playouts=`{'mate': 2, 'max_plies': 3}`
- `reports/structural_candidates/stage7_king_tempo_baseline_10_h40.json`: `clean_default_off_candidate`, playouts=`{'max_plies': 10}`
- `reports/structural_candidates/stage7_king_tempo_baseline_25_h40.json`: `clean_default_off_candidate`, playouts=`{'max_plies': 25}`
- `reports/structural_candidates/stage7_king_tempo_default_off_A_base_3_h5.json`: `clean_default_off_candidate`, playouts=`{'max_plies': 3}`
- `reports/structural_candidates/stage7_king_tempo_default_off_B_sandbox_3_h5.json`: `clean_default_off_candidate`, playouts=`{'max_plies': 3}`
- `reports/structural_candidates/stage7_king_tempo_refined_default_off_A_base_3_h5.json`: `clean_default_off_candidate`, playouts=`{'max_plies': 3}`
- `reports/structural_candidates/stage7_king_tempo_refined_default_off_B_sandbox_3_h5.json`: `clean_default_off_candidate`, playouts=`{'max_plies': 3}`
- `reports/structural_candidates/stage7_king_tempo_single_use_default_off_A_base_3_h5.json`: `clean_default_off_candidate`, playouts=`{'max_plies': 3}`
- `reports/structural_candidates/stage7_king_tempo_single_use_default_off_B_sandbox_3_h5.json`: `clean_default_off_candidate`, playouts=`{'max_plies': 3}`
- `reports/structural_candidates/stage7_learnable_capsule_marker_default_off_smoke_5_h20.json`: `clean_current_profile_candidate`, playouts=`{'mate': 2, 'max_plies': 3}`
- `reports/structural_candidates/stage7_plan_capsule_default_off_base_10_h20.json`: `clean_default_off_candidate`, playouts=`{'mate': 5, 'max_plies': 5}`
- `reports/structural_candidates/stage7_plan_capsule_default_off_base_10_h20_rerun.json`: `clean_default_off_candidate`, playouts=`{'mate': 5, 'max_plies': 5}`
- `reports/structural_candidates/stage7_plan_capsule_default_off_sandbox_10_h20.json`: `clean_default_off_candidate`, playouts=`{'mate': 5, 'max_plies': 5}`
- `reports/structural_candidates/stage7_plan_capsule_default_off_sandbox_10_h20_rerun.json`: `clean_default_off_candidate`, playouts=`{'mate': 5, 'max_plies': 5}`
- `reports/structural_candidates/stage7_plan_capsule_owned_arb_default_off_base_5_h10.json`: `clean_default_off_candidate`, playouts=`{'mate': 2, 'max_plies': 3}`
- `reports/structural_candidates/stage7_plan_capsule_owned_arb_default_off_sandbox_5_h10.json`: `clean_default_off_candidate`, playouts=`{'mate': 2, 'max_plies': 3}`
- `reports/structural_candidates/stage7_post_box_learnable_capsule_base_smoke_5_h20.json`: `clean_baseline_candidate`, playouts=`{'mate': 2, 'max_plies': 3}`
- `reports/structural_candidates/stage7_post_box_learnable_capsule_default_off_smoke_5_h20.json`: `clean_current_profile_candidate`, playouts=`{'mate': 2, 'max_plies': 3}`
- `reports/structural_candidates/stage7_role_owned_default_off_5_h40.json`: `clean_current_profile_candidate`, playouts=`{'mate': 2, 'max_plies': 3}`
- `reports/structural_candidates/stage7_strict_neg_capsule_default_off_smoke_5_h20.json`: `clean_current_profile_candidate`, playouts=`{'mate': 2, 'max_plies': 3}`

## Ambiguous

- `reports/structural_candidates/stage7_069_guard_stage4_wrong_tempo_50_h40_disabled_control.json`

Next step: `recover_clean_sequence_controls_from_manifest_candidates`
