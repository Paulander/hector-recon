# KRK Diverse Contrast Labels v1

This bounded label run forces each configured provider for the first White move, then releases to the normal topology. It is non-causal evidence only.

## Summary

- `forced_successor_available_counts`: `{'True': 12}`
- `label_count`: `12`
- `result_counts`: `{'mate': 4, 'max_plies': 8}`
- `result_counts_by_provider_family`: `{'drive_to_edge:max_plies': 2, 'edge_trap:mate': 1, 'edge_trap:max_plies': 2, 'fence_established:max_plies': 2, 'stage0_basin:mate': 3, 'stage0_basin:max_plies': 2}`
- `result_counts_by_stage`: `{'stage5:mate': 2, 'stage6:mate': 2, 'stage7:max_plies': 8}`
- `stage7_eval_only_label_count`: `8`
- `trace_failures_only`: `True`
- `training_label_count`: `4`
- `wall_time_seconds`: `247.048`
- `full_failure_traces_elided`: `True`

## Labels

- `job.krk.diverse_contrast.e24a9ac89a84` stage=`stage5` stratum=`protected_stage5_fence` provider=`krk.edge_trap_close` forced_move=`h7c7` result=`mate` plies=`15` stage7_eval=`False`
- `job.krk.diverse_contrast.beb3c750ca71` stage=`stage5` stratum=`protected_stage5_fence` provider=`krk.stage0_basin` forced_move=`a7a8` result=`mate` plies=`17` stage7_eval=`False`
- `job.krk.diverse_contrast.71312289ffab` stage=`stage6` stratum=`protected_stage6_drive` provider=`krk.stage0_basin` forced_move=`a8f8` result=`mate` plies=`3` stage7_eval=`False`
- `job.krk.diverse_contrast.4b14d68ad836` stage=`stage6` stratum=`protected_stage6_drive` provider=`krk.stage0_basin` forced_move=`a1d1` result=`mate` plies=`3` stage7_eval=`False`
- `job.krk.diverse_contrast.4f2168a0720a` stage=`stage7` stratum=`stage7_challenge_eval_only` provider=`krk.drive_to_edge` forced_move=`e3a3` result=`max_plies` plies=`40` stage7_eval=`True`
- `job.krk.diverse_contrast.b8907fba6ef0` stage=`stage7` stratum=`stage7_challenge_eval_only` provider=`krk.edge_trap_close` forced_move=`e4f4` result=`max_plies` plies=`40` stage7_eval=`True`
- `job.krk.diverse_contrast.fd828977ac83` stage=`stage7` stratum=`stage7_challenge_eval_only` provider=`krk.fence_established` forced_move=`e3a3` result=`max_plies` plies=`40` stage7_eval=`True`
- `job.krk.diverse_contrast.9f2aa0bbf901` stage=`stage7` stratum=`stage7_challenge_eval_only` provider=`krk.stage0_basin` forced_move=`e3a3` result=`max_plies` plies=`40` stage7_eval=`True`
- `job.krk.diverse_contrast.2ff0babf8a3e` stage=`stage7` stratum=`stage7_challenge_eval_only` provider=`krk.drive_to_edge` forced_move=`a5a8` result=`max_plies` plies=`40` stage7_eval=`True`
- `job.krk.diverse_contrast.0f8f89a9915a` stage=`stage7` stratum=`stage7_challenge_eval_only` provider=`krk.edge_trap_close` forced_move=`d1e2` result=`max_plies` plies=`40` stage7_eval=`True`
- `job.krk.diverse_contrast.9b8477aef635` stage=`stage7` stratum=`stage7_challenge_eval_only` provider=`krk.fence_established` forced_move=`d1e2` result=`max_plies` plies=`40` stage7_eval=`True`
- `job.krk.diverse_contrast.629e41440493` stage=`stage7` stratum=`stage7_challenge_eval_only` provider=`krk.stage0_basin` forced_move=`d1e2` result=`max_plies` plies=`40` stage7_eval=`True`

## Decision

- Status: `diverse_contrast_labels_completed`
- Recommended next step: `merge_diverse_contrast_labels_and_probe_selector`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
