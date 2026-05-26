# KRK Sequence-Policy Benchmark Design v0

Status: `sequence_policy_benchmark_design_ready_non_causal`

This is a non-causal benchmark design/readiness artifact. It does not train a model, implement a sandbox, or authorize runtime behavior.

## Readiness

- stage4_first_move_contrast_sandbox_review_ready: `True`
- stage7_clean_success_controls: `11`
- stage7_clean_failure_controls: `39`
- stage7_clean_success_controls_required: `5`
- stage7_clean_success_controls_met: `True`
- stage7_clean_failure_controls_met: `True`
- post_box_sandbox_sourced_success_controls: `16`
- post_box_controls_runtime_authorization_eligible: `False`
- plan_capsule_stage7_only_evidence: `True`
- protected_plan_window_frame_count: `20`
- protected_plan_window_evidence_met: `True`
- cross_stage_sequence_evidence_met: `True`
- plan_capsule_policy_succeeded: `False`
- benchmark_ready: `True`
- current_benchmark_review_status: `sequence_policy_benchmark_mixed_plan_window_underpowered`
- current_benchmark_review_next_step: `obtain_matching_approval_receipt_before_protected_failure_contrast_collection`
- current_benchmark_review_available: `True`
- forbidden_training_or_runtime_input_blocked: `False`
- forbidden_training_or_runtime_input_blockers: `[]`

## Candidate Objectives

### state_local_first_move_contrast

- uses: Stage 4 forced-first-move contrast rows
- target: rank converting visible candidate moves above h40-failing drift moves within same state family
- runtime_ready: `False`

### post_box_sequence_success_vs_hard_negative

- uses: clean Stage 7 controls when enough success controls exist
- target: distinguish closed-loop sequence controls from hard negatives without using Stage 7 as promotion base
- runtime_ready: `False`

### plan_capsule_entry_progress_exit_abort

- uses: PlanCapsule marker/source terms plus protected plan-window frames where available
- target: predict when a bounded plan should enter, continue, hand off, or abort
- runtime_ready: `False`

### cross_stage_owner_preservation_vs_switch

- uses: protected Stage 4/5/6 ownership-seed context rows
- target: preserve safe owners while identifying switch/abstain contexts
- runtime_ready: `False`

## Minimum Data Before Benchmark

- at least 5 clean Stage 7 success controls and 5 clean Stage 7 hard negatives
- explicit held-out split by source family and state id
- PlanCapsule sequence fields represented outside Stage 7 or protected plan-window evidence marked as non-causal
- no row marked as selector-training or runtime-authorization evidence

## Metrics

- family-held-out top1/top3 conversion-positive ranking
- hard-negative suppression
- safe-owner preservation
- plan entry/progress/exit/abort classification
- first miss per sequence
- stage7 held-out challenge result

## Decision

- recommended_next_step: `obtain_matching_approval_receipt_before_protected_failure_contrast_collection`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
