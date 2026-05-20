# Stage 7 Clean h40 Label Run Review v0

Status: `bounded_label_run_no_novel_clean_success_controls`

Review of the single bounded current-default Stage 7 h40 label job.

## Summary

- run_mate_count: `3`
- run_max_plies_count: `7`
- recovered_from_run: `0`
- enabled_stage7_or_runtime_flag_count: `0`
- no_runtime_repair_flags_detected: `True`
- label_job_added_novel_controls: `False`

## Run

- total: `10`
- playouts: `{'max_plies': 7, 'mate': 3}`
- shadow_candidate_count: `8`
- enabled_stage7_or_runtime_flags: `[]`

## Recovery After Run

- control_count: `10`
- role_counts: `{'clean_sequence_hard_negative': 8, 'clean_sequence_success_control': 2}`
- source_artifact_counts: `{'reports/krk_two_stage_abstention_stage7_baseline_3_seed11_h40.json': 3, 'reports/structural_candidates/stage7_2cc_frozen_model_default_off_smoke_5_h20.json': 1, 'reports/structural_candidates/stage7_candidate_move_layer_default_off_10_h40.json': 2, 'reports/structural_candidates/stage7_family_ac_fence_noaugment_default_off_5_h40.json': 2, 'reports/structural_candidates/stage7_king_tempo_baseline_10_h40.json': 2}`
- controls_recovered_from_run: `0`
- clean_success_gap_closed: `False`

Next step: `review_sampling_diversity_or_architecture_boundary_before_more_labels`
