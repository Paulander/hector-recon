# KRK Full Suite Unblocker Packet v0

## Decision

- status: `krk_suite_primary_unblocker_ready_pending_explicit_label_approval`
- recommended_next_step: `explicitly_approve_stage7_diverse_clean_label_execution`
- implementation_allowed_by_this_packet: `False`
- label_run_allowed: `False`
- runtime_changes_allowed: `False`

## Current State

- protected_stack_ready: `True`
- stage7_success_controls: `2`
- stage7_success_controls_required: `5`
- sequence_policy_inputs_ready: `False`
- sequence_policy_benchmark_ready: `False`
- stage8_training_ready: `False`
- stage7_output_validation_status: `stage7_diverse_clean_sampling_outputs_validation_pending`
- stage7_invalid_existing_output_count: `0`
- stage7_overwrite_existing_outputs: `False`
- stage7_processed_job_count: `0`
- stage7_executed_job_count: `0`
- stage7_skipped_existing_output_count: `0`

## Why Work Stops At This Gate

- The next highest-value action creates new Stage 7 h40 labels or implements a reviewed runtime sandbox.
- Those actions are gated by repository reports and architecture policy, not by a hidden disk config that limits session length.
- The current /goal authorizes autonomous safe work, but it does not by itself authorize gated label execution, runtime behavior, Stage 7 promotion, or Stage 8 training.

## Primary Unblocker

- id: `stage7_diverse_clean_label_execution`
- status: `ready_pending_explicit_approval`
- purpose: Fill held-out Stage 7 clean success controls so the sequence-policy benchmark can run.
- command_if_explicitly_approved: `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_stage7_diverse_clean_sampling_jobs_v0.py --execute-reviewed-label-run --refresh-after-run`
- resume_safe: `True`
- skip_existing_outputs_by_default: `True`
- invalid_existing_outputs_block_without_overwrite: `True`
- stage7_training_rows: `0`
- approval_required: `True`
- implementation_allowed_by_this_packet: `False`

## Secondary Unblocker

- id: `stage4_first_move_contrast_sandbox`
- status: `stage4_caveat_unblocker_ready_pending_explicit_runtime_approval`
- purpose: Address the separate Stage 4 h40 caveat through a reviewed default-off sandbox path.
- why_secondary: This may reduce Stage 4 debt, but it does not directly fill the Stage 7 clean success controls currently blocking sequence-policy benchmarking.

## Low-Value Safe Work Remaining

- More passive summaries can be written, but they will not unblock Stage 8 or the sequence-policy benchmark.
- Further non-causal candidate-generation analysis is lower leverage until Stage 7 clean success controls are filled.
