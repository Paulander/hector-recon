# KRK Sequence-Policy Input Probe v0

Status: `sequence_policy_input_probe_ready_for_full_non_causal_benchmark`

This is a partial non-causal probe over the currently assembled inputs. It does not train a model, authorize runtime behavior, promote Stage 7, or train Stage 8.

## Summary

- row_count: `118`
- benchmark_input_ready: `True`
- stage4_binary_heuristic_sufficient: `False`
- stage4_topk_signal: `True`
- protected_plan_window_failure_sparse: `True`
- stage7_underpowered: `False`
- selector_training_row_count: `0`
- runtime_authorization_row_count: `0`
- forbidden_training_or_runtime_input_blocked: `False`
- forbidden_training_or_runtime_input_blockers: `[]`
- current_benchmark_review_status: `sequence_policy_benchmark_mixed_plan_window_underpowered`
- current_benchmark_review_next_step: `explicitly_approve_protected_plan_window_failure_contrast_collection`
- current_benchmark_review_available: `True`

## Stage 4 First-Move Contrast

- row_count: `48`
- precision: `0.75`
- recall: `0.34615384615384615`
- negative_suppression: `0.8636363636363636`
- top1_conversion_positive_by_state: `0.75`
- top3_conversion_positive_by_state: `1.0`

## Protected Plan-Window Evidence

- row_count: `20`
- target_label_counts: `{'conversion_positive': 19, 'conversion_failure': 1}`
- failure_evidence_sparse: `True`

## Stage 7 Held-Out Controls

- success_controls: `11`
- failure_controls: `39`
- underpowered: `False`

## Decision

- recommended_next_step: `explicitly_approve_protected_plan_window_failure_contrast_collection`
- runtime_changes_allowed: `false`
- label_run_allowed: `false`
- selector_training_allowed: `false`
- Stage 7 promotion and Stage 8 training remain blocked.
