# KRK Protected Plan-Window Failure Contrast Manifest Review v0

Status: `protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval`

This is a non-causal manifest review. Passing review does not execute collection or authorize labels; explicit approval is still required.

## Summary

- job_count: `6`
- max_collection_jobs: `6`
- stage_counts: `{'stage5': 2, 'stage6': 2, 'stage4': 2}`
- family_counts: `{'fence_handoff_plan_window': 2, 'drive_to_edge_plan_window': 2, 'wrong_tempo_plan_window': 2}`
- manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- recorded_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- manifest_fingerprint_matches: `True`
- required_stages_present: `True`
- violation_count: `0`
- violations: `[]`
- collection_run_allowed_now: `False`
- label_run_allowed_now: `False`
- runtime_work_allowed: `False`
- review_passed: `True`

## Decision

- recommended_next_step: `obtain_matching_approval_receipt_before_protected_failure_contrast_collection`
- collection_run_allowed: `false`
- label_run_allowed: `false`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
