# KRK Stage 4 Caveat Diagnostic Matrix v0

Status: `stage4_caveat_diagnostic_matrix_ready`

- Observed h40 caveat: `{'total': 300, 'mate': 268, 'max_plies': 32, 'overlay_vs_base_control_delta': {'improved_delta': 0, 'worsened_delta': 0, 'optimal_delta': 0, 'mate_delta': 0, 'max_plies_delta': 0, 'mate_rate_delta': 0.0, 'max_plies_rate_delta': 0.0, 'shadow_candidate_delta': 0}}`

Hypotheses:

- `local_move_shape_weakness` confidence=`medium` next=`stage4_observation_only_trace_collection_if_explicitly_approved`
- `sequence_followup_gap` confidence=`medium` next=`trace_stage4_selected_failure_windows`
- `candidate_generation_gap` confidence=`high` next=`approve_stage4_observation_only_trace_collection_max_6_rows`
- `horizon_or_label_issue` confidence=`low` next=`defer_h80_unless_stage4_trace_collection_is_inconclusive`
- `existing_provider_solved_if_arbitrated` confidence=`medium` next=`stage4_joined_trace_ownership_collection_non_causal`

Boundary: replay-free diagnostic only; no runtime behavior authorized.
