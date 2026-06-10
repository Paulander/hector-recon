# KRK Selected-Owner Failure-Risk Visible Proxy Probe v0

Non-causal probe of visible failure-risk proxy candidates.

## Summary

- `row_count`: `40`
- `failure_risk_target_count`: `7`
- `stage7_row_count`: `0`
- `selected_owner_failure_risk_proxy_precision`: `1.0`
- `selected_owner_failure_risk_proxy_recall`: `1.0`
- `safe_preservation_recall`: `1.0`
- `review_threshold_met`: `True`

## Candidate Proxy

- `term_id`: `selected_owner_failure_risk_proxy_v0`
- `definition`: `stage0_vs_edge_trap_selected_king_stalls_box OR edge_trap_drive_context_rook_expands_box`
- `requires_visible_competing_provider_proposal`: `True`
- `requires_out_of_sample_validation`: `True`
- `causal_status`: `non_causal_candidate`
- `term_name`: `selected_owner_failure_risk_proxy_v0`
- `true_positive`: `7`
- `false_positive`: `0`
- `true_negative`: `33`
- `false_negative`: `0`
- `precision`: `1.0`
- `recall`: `1.0`
- `safe_preservation_recall`: `1.0`

## Decision

- `status`: `visible_failure_risk_proxy_candidate_needs_out_of_sample_validation`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `recommended_next_step`: `validate_proxy_candidate_on_independent_protected_pairs`
