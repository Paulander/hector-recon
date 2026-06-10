# KRK Control-Plane Manifest v0

This replay-free manifest maps existing KRK artifacts into the non-causal control-plane evidence contract. It adds no labels, playouts, runtime consumers, terminals, arbiters, promotions, or topology changes.

## Summary

- Strategy records: `33`
- Strategy proposal frames: `87`
- Monitor records: `108`
- Plan windows: `13`
- Sequence seed steps: `25`
- Expanded sequence steps: `195`
- New playouts added: `0`
- Recommended next slice: `stratified_control_plane_gap_report_v0`

## Field Coverage

### protected_provider_provenance

- Coverage: `covered_summary_level`
- Sources: `reports/krk_protected_stage_status.json`, `reports/stage6_overlay_validation_manifest.md`
- Summary: `protected_or_promoted_stages=['stage1_backchain', 'stage4_wrong_tempo', 'stage5_fence', 'stage6_drive_overlay']`, `cleanest_solved_components=['stage1_backchain', 'stage5_fence', 'stage6_drive_overlay']`, `solved_with_caveat=['stage4_wrong_tempo']`

### strategy_proposal_frames

- Coverage: `covered_record_level`
- Sources: `reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json`
- Summary: `record_count=33`, `proposal_count=87`, `records_by_source_stage={'stage4': 6, 'stage5': 8, 'stage6': 10, 'stage7': 9}`

### internal_monitor_records

- Coverage: `covered_record_level`
- Sources: `reports/strategy_arbitration/krk_strategy_monitor_records_v0.json`, `reports/strategy_arbitration/krk_internal_terminal_evidence_v1.json`
- Summary: `monitor_record_count=108`, `internal_terminal_count=4`, `causal_ready_terminals=[]`, `strongest_candidates=['terminal.krk.local_provider_competition_failed', 'terminal.krk.post_plan_stagnation']`

### plan_capsule_window_records

- Coverage: `covered_stage7_only`
- Sources: `reports/structural_candidates/stage7_plan_capsule_owned_window_25_h40.json`, `reports/structural_candidates/stage7_post_box_plan_capsule_audit.json`
- Summary: `window_count=13`, `plan_audit_schema=stage7_post_box_plan_capsule_audit.v1`

### sequence_training_examples

- Coverage: `covered_stage7_only_offline`
- Sources: `reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.json`, `reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.jsonl`, `reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_expanded_h40.json`, `reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_expanded_h40.jsonl`, `reports/structural_candidates/stage7_training_objective_benchmark.json`
- Summary: `seed_trajectory_count=2`, `seed_step_count=25`, `expanded_trajectory_count=18`, `expanded_step_count=195`, `benchmark_status=None`

### guardrail_result_summaries

- Coverage: `covered_summary_level`
- Sources: `reports/krk_protected_stage_status.json`, `snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/promotion_eval_stage6_overlay.json`
- Summary: `stage6_promotion_status=promoted`, `stage7_status=local_valid_composition_quarantined`, `protected_or_promoted_stages=['stage1_backchain', 'stage4_wrong_tempo', 'stage5_fence', 'stage6_drive_overlay']`

### growth_governor_status

- Coverage: `partial_design_only`
- Sources: `reports/structural_candidates/stage7_box_shrink_growth_governor_plan.json`
- Summary: `source_schema=growth_governor_evaluation_plan.v1`, `gap=No unified per-frame GrowthGovernorStatus export exists yet.`

### promotion_gate_status

- Coverage: `covered_summary_level`
- Sources: `snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/promotion_eval_stage6_overlay.json`, `reports/structural_candidates/stage7_training_objective_decision_gate.json`, `reports/structural_candidates/stage7_post_decision_closure.json`
- Summary: `stage6_promotion_status=promoted`, `stage7_training_gate=model_expression_gap_persists_stage7_micro_work_stops`, `stage7_closure_status={'benchmark_status': 'model_expression_gap_persists', 'next_implementation_requires_explicit_review': True, 'required_conclusion': 'Stage 7 micro-work is stopped pending architecture review.', 'selected_outcome': 'model_expression_gap_persists_stage7_micro_work_stops'}`

## Gaps

- `unified_frame_export_missing`: Artifacts map to contract fields, but no per-state ControlPlaneEvidenceFrame export exists yet. Next: `frame_exporter_design_or_replay_free_export`
- `growth_governor_status_not_frame_level`: GrowthGovernor evidence is available as design/status artifacts, not per-frame status. Next: `non_causal_status_export`
- `sequence_examples_stage7_only`: Offline DTM/trajectory sequence labels are concentrated in Stage 7 residuals. Next: `stratified_data_collection_plan`
- `plan_windows_stage7_only`: Plan-capsule window evidence is mostly Stage 7-specific. Next: `cross_stage_window_evidence_design`

## Blocked Next Steps

- `stage7_runtime_repair`
- `stage7_promotion`
- `stage8_training`
- `runtime_arbiter`
- `runtime_internal_terminal`
- `support_adapter_or_score_bonus`
- `provider_penalty_or_stage0_suppression`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`
- `monolithic_later_stage_replacement`
