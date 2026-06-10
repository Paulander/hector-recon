# KRK Selected-Owner Failure-Risk Visible Terms v0

Non-causal extraction of candidate visible terms for selected-owner failure risk.

## Summary

- `row_count`: `40`
- `state_count`: `14`
- `failure_risk_target_count`: `7`
- `stage7_row_count`: `0`
- `selector_training_row_count`: `0`
- `context_join_count`: `40`
- `source_stage_counts`: `{'stage4': 13, 'stage5': 14, 'stage6': 13}`

## Term Metrics

- `selected_king_no_box_progress`: precision=`0.6666666666666666`, recall=`0.8571428571428571`, safe_preservation_recall=`0.9090909090909091`
- `selected_king_worsens_rook_support`: precision=`0.6666666666666666`, recall=`0.8571428571428571`, safe_preservation_recall=`0.9090909090909091`
- `stage0_vs_edge_trap_selected_king_stalls_box`: precision=`1.0`, recall=`0.8571428571428571`, safe_preservation_recall=`1.0`
- `edge_trap_drive_context_rook_expands_box`: precision=`1.0`, recall=`0.14285714285714285`, safe_preservation_recall=`1.0`
- `selected_owner_context_contention_visible`: precision=`0.23076923076923078`, recall=`0.8571428571428571`, safe_preservation_recall=`0.3939393939393939`
- `selected_owner_trace_stagnation_visible`: precision=`0.2`, recall=`0.14285714285714285`, safe_preservation_recall=`0.8787878787878788`
- `selected_owner_failure_risk_proxy_v0`: precision=`1.0`, recall=`1.0`, safe_preservation_recall=`1.0`

## Decision

- `status`: `visible_failure_risk_terms_extracted_for_probe`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `recommended_next_step`: `probe_visible_failure_risk_proxy_terms`
