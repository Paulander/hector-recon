# Stage 7 Diverse Clean Sampling Runner v0

Status: `stage7_diverse_clean_sampling_runner_executed_success`

This is an approval-gated label-run wrapper. By default it is dry-run only. It does not authorize runtime behavior, selector training, Stage 7 promotion, or Stage 8 training.

## Summary

- job_count: `8`
- processed_job_count: `0`
- executed_job_count: `0`
- historical_processed_job_count: `8`
- historical_executed_job_count: `8`
- skipped_existing_output_count: `0`
- failed_job_count: `0`
- dry_run: `False`
- current_label_run_allowed: `False`
- historical_label_run_allowed_by_runner: `True`
- max_jobs: `None`
- job_timeout_seconds: `900`
- overwrite_existing_outputs: `False`
- execution_readiness_source: `live_recomputed`
- execution_readiness_status: `stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval`
- execution_readiness_jobs_passing: `8`
- execution_readiness_all_jobs_pass: `True`
- output_validation_status: `stage7_diverse_clean_sampling_outputs_valid_ready_for_integration`
- invalid_existing_output_count: `0`
- timed_out_job_count: `0`
- refresh_after_run_requested: `True`
- refresh_after_run_performed: `True`
- stage7_training_row_count: `0`
- runtime_authorization_row_count: `0`

## Commands

- `stage7.diverse_clean.box_small.seed101.samples8.h40` current_would_execute=`False` historical_executed_under_prior_approval=`True` output=`reports/structural_candidates/stage7_diverse_clean_box_small_seed101_8_h40.json`
- `stage7.diverse_clean.box_medium.seed103.samples8.h40` current_would_execute=`False` historical_executed_under_prior_approval=`True` output=`reports/structural_candidates/stage7_diverse_clean_box_medium_seed103_8_h40.json`
- `stage7.diverse_clean.edge_fence_deep.seed107.samples8.h40` current_would_execute=`False` historical_executed_under_prior_approval=`True` output=`reports/structural_candidates/stage7_diverse_clean_edge_fence_deep_seed107_8_h40.json`
- `stage7.diverse_clean.box_small_medium.seed109.samples8.h40` current_would_execute=`False` historical_executed_under_prior_approval=`True` output=`reports/structural_candidates/stage7_diverse_clean_box_small_medium_seed109_8_h40.json`
- `stage7.diverse_clean.box_medium_edge_deep.seed113.samples8.h40` current_would_execute=`False` historical_executed_under_prior_approval=`True` output=`reports/structural_candidates/stage7_diverse_clean_box_medium_edge_deep_seed113_8_h40.json`
- `stage7.diverse_clean.all_stage7_sources_a.seed127.samples8.h40` current_would_execute=`False` historical_executed_under_prior_approval=`True` output=`reports/structural_candidates/stage7_diverse_clean_all_stage7_sources_a_seed127_8_h40.json`
- `stage7.diverse_clean.all_stage7_sources_b.seed131.samples8.h40` current_would_execute=`False` historical_executed_under_prior_approval=`True` output=`reports/structural_candidates/stage7_diverse_clean_all_stage7_sources_b_seed131_8_h40.json`
- `stage7.diverse_clean.all_stage7_sources_c.seed137.samples8.h40` current_would_execute=`False` historical_executed_under_prior_approval=`True` output=`reports/structural_candidates/stage7_diverse_clean_all_stage7_sources_c_seed137_8_h40.json`

## Post-Run Refresh

- status: `krk_suite_passive_advancement_ready_for_protected_failure_contrast_collection`
- sequence_policy_inputs_ready: `True`

## Decision

- recommended_next_step: `run_passive_sequence_policy_refresh`
- label_run_allowed: `false`
- historical_label_run_allowed_by_runner: `true`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
