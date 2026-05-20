# Stage 7 Clean Sequence Control Recovery v0

Status: `clean_sequence_controls_insufficient`

Replay-free recovery of clean Stage 7 sequence controls from manifest-approved current-profile/default-off artifacts.

## Summary

- control_count: `10`
- role_counts: `{'clean_sequence_hard_negative': 8, 'clean_sequence_success_control': 2}`
- result_counts: `{'max_plies': 8, 'mate': 2}`
- selected_provider_counts: `{'krk.edge_trap_close': 2, 'krk.stage0_basin': 7, 'None': 1}`
- source_classification_counts: `{'clean_current_profile_candidate': 5, 'clean_default_off_candidate': 5}`
- source_artifact_counts: `{'reports/krk_two_stage_abstention_stage7_baseline_3_seed11_h40.json': 3, 'reports/structural_candidates/stage7_2cc_frozen_model_default_off_smoke_5_h20.json': 1, 'reports/structural_candidates/stage7_candidate_move_layer_default_off_10_h40.json': 2, 'reports/structural_candidates/stage7_family_ac_fence_noaugment_default_off_5_h40.json': 2, 'reports/structural_candidates/stage7_king_tempo_baseline_10_h40.json': 2}`
- skipped_counts: `{'non_mate_not_h40': 68, 'duplicate_control': 127, 'horizon_above_h40': 25}`
- duplicate_source_key_count: `10`
- usable_for_offline_benchmark: `True`
- usable_for_runtime_authorization: `False`

## Acceptance

- clean_sequence_success_controls_required: `5`
- clean_sequence_hard_negatives_required: `5`
- clean_sequence_success_controls_met: `False`
- clean_sequence_hard_negatives_met: `True`
- runtime_authorization_allowed: `False`

## Controls

- `clean.4d979dff05b0` clean_sequence_hard_negative result=`max_plies` provider=`krk.edge_trap_close` source=`reports/krk_two_stage_abstention_stage7_baseline_3_seed11_h40.json`
- `clean.5026622a62dd` clean_sequence_success_control result=`mate` provider=`krk.edge_trap_close` source=`reports/krk_two_stage_abstention_stage7_baseline_3_seed11_h40.json`
- `clean.3b9c91ab4afd` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/krk_two_stage_abstention_stage7_baseline_3_seed11_h40.json`
- `clean.d11f73c6a7d7` clean_sequence_success_control result=`mate` provider=`None` source=`reports/structural_candidates/stage7_2cc_frozen_model_default_off_smoke_5_h20.json`
- `clean.9790bf83c082` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_candidate_move_layer_default_off_10_h40.json`
- `clean.0281198378bf` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_candidate_move_layer_default_off_10_h40.json`
- `clean.bf1c70839063` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_family_ac_fence_noaugment_default_off_5_h40.json`
- `clean.13b8d974ad33` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_family_ac_fence_noaugment_default_off_5_h40.json`
- `clean.2d746e6678a1` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_king_tempo_baseline_10_h40.json`
- `clean.11e67619c996` clean_sequence_hard_negative result=`max_plies` provider=`krk.stage0_basin` source=`reports/structural_candidates/stage7_king_tempo_baseline_10_h40.json`

Next step: `bounded_clean_h40_label_job_or_review`
