# KRK Diverse Contrast Execution Manifest v1

This non-causal manifest binds the bounded diverse contrast-label jobs. It does not run labels or change runtime behavior.

## Summary

- `job_count`: `12`
- `stage7_eval_only_job_count`: `8`
- `training_job_count`: `4`
- `job_count_by_stage`: `{'stage5': 2, 'stage6': 2, 'stage7': 8}`
- `job_count_by_provider_family`: `{'edge_trap': 3, 'stage0_basin': 5, 'drive_to_edge': 2, 'fence_established': 2}`
- `selected_state_count`: `6`
- `missing_path_count`: `0`
- `missing_paths`: `[]`
- `all_bindings_valid`: `True`
- `deferred_stages_due_to_runtime_risk`: `['stage4']`

## Jobs

- `job.krk.diverse_contrast.e24a9ac89a84` stage=`stage5` stratum=`protected_stage5_fence` state=`state.02feb8593cc6` provider=`krk.edge_trap_close` move=`h7c7` stage7_eval=`False`
- `job.krk.diverse_contrast.beb3c750ca71` stage=`stage5` stratum=`protected_stage5_fence` state=`state.2c1d6da27ea1` provider=`krk.stage0_basin` move=`a7a8` stage7_eval=`False`
- `job.krk.diverse_contrast.71312289ffab` stage=`stage6` stratum=`protected_stage6_drive` state=`state.52085d244e9d` provider=`krk.stage0_basin` move=`a8f8` stage7_eval=`False`
- `job.krk.diverse_contrast.4b14d68ad836` stage=`stage6` stratum=`protected_stage6_drive` state=`state.69711173114a` provider=`krk.stage0_basin` move=`a1d1` stage7_eval=`False`
- `job.krk.diverse_contrast.4f2168a0720a` stage=`stage7` stratum=`stage7_challenge_eval_only` state=`state.0afbf11aa123` provider=`krk.drive_to_edge` move=`e3a3` stage7_eval=`True`
- `job.krk.diverse_contrast.b8907fba6ef0` stage=`stage7` stratum=`stage7_challenge_eval_only` state=`state.0afbf11aa123` provider=`krk.edge_trap_close` move=`e4f4` stage7_eval=`True`
- `job.krk.diverse_contrast.fd828977ac83` stage=`stage7` stratum=`stage7_challenge_eval_only` state=`state.0afbf11aa123` provider=`krk.fence_established` move=`e3a3` stage7_eval=`True`
- `job.krk.diverse_contrast.9f2aa0bbf901` stage=`stage7` stratum=`stage7_challenge_eval_only` state=`state.0afbf11aa123` provider=`krk.stage0_basin` move=`e3a3` stage7_eval=`True`
- `job.krk.diverse_contrast.2ff0babf8a3e` stage=`stage7` stratum=`stage7_challenge_eval_only` state=`state.38aed2f35911` provider=`krk.drive_to_edge` move=`a5a8` stage7_eval=`True`
- `job.krk.diverse_contrast.0f8f89a9915a` stage=`stage7` stratum=`stage7_challenge_eval_only` state=`state.38aed2f35911` provider=`krk.edge_trap_close` move=`d1e2` stage7_eval=`True`
- `job.krk.diverse_contrast.9b8477aef635` stage=`stage7` stratum=`stage7_challenge_eval_only` state=`state.38aed2f35911` provider=`krk.fence_established` move=`d1e2` stage7_eval=`True`
- `job.krk.diverse_contrast.629e41440493` stage=`stage7` stratum=`stage7_challenge_eval_only` state=`state.38aed2f35911` provider=`krk.stage0_basin` move=`d1e2` stage7_eval=`True`

## Decision

- Status: `diverse_contrast_execution_manifest_ready`
- Recommended next step: `run_diverse_contrast_labels_v1`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
