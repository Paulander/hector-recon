# KRK Protected Plan-Window Failure Contrast Execution Readiness v0

Status: `protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval`

This is a dry-run preflight only. It does not execute collection, run labels, change runtime behavior, train a selector, promote Stage 7, or train Stage 8.

## Summary

- job_count: `6`
- jobs_passing_readiness: `6`
- all_jobs_pass_readiness: `True`
- job_readiness_blocker_count: `0`
- manifest_status: `protected_plan_window_failure_contrast_manifest_ready_for_review`
- manifest_review_status: `protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval`
- manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- recorded_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- review_manifest_fingerprint: `5f6c196f2257a577c9a631959479219c03def25cea4506028f84a20350a55038`
- manifest_fingerprints_match: `True`
- execution_readiness_blockers: `[]`
- existing_output_count: `0`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- stage7_training_row_count: `0`
- readiness_fingerprint: `9e3760e042b380429e8c2b1b7c533296cb98bb59fbf31b287e2bfdae30abdc0d`

## Jobs

- `protected_plan_failure.01.planwin.a8dd289c75b7` ready=`True` output_exists=`False` blockers=`[]`
- `protected_plan_failure.02.planwin.6ffab60fb0d0` ready=`True` output_exists=`False` blockers=`[]`
- `protected_plan_failure.03.planwin.4f9789a608c4` ready=`True` output_exists=`False` blockers=`[]`
- `protected_plan_failure.04.planwin.e09fb2b8a021` ready=`True` output_exists=`False` blockers=`[]`
- `protected_plan_failure.05.planwin.23c0bb760d87` ready=`True` output_exists=`False` blockers=`[]`
- `protected_plan_failure.06.planwin.d90d6f3d623a` ready=`True` output_exists=`False` blockers=`[]`

## Decision

- recommended_next_step: `obtain_matching_approval_receipt_before_protected_failure_contrast_collection`
- collection_run_allowed: `false`
- label_run_allowed: `false`
- runtime_changes_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
