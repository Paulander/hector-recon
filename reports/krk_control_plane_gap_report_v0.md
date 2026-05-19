# KRK Control-Plane Gap Report v0

This is a non-causal gap report. It recommends replay-free evidence export, not runtime repair, Stage 7 promotion, Stage 8 training, or sandboxing.

## Coverage Snapshot

- Strategy records: `33`
- Strategy proposals: `87`
- Records by source stage: `{'stage4': 6, 'stage5': 8, 'stage6': 10, 'stage7': 9}`
- Monitor records: `108`
- Plan windows: `13`
- Sequence seed steps: `25`
- Expanded sequence steps: `195`
- New playouts added: `0`

## Stratified Gaps

### no_unified_control_plane_frames

- Priority: `p0`
- Evidence: Manifest coverage is field-level; downstream probes still need per-state ControlPlaneEvidenceFrame exports.
- Affected tracks: `strategy_arbitration, internal_monitors, sequence_policy, promotion_review`
- Minimum next step: `export_replay_free_control_plane_frames_v0`
- Causal allowed: `False`

### sequence_labels_stage7_only

- Priority: `p1`
- Evidence: Sequence labels have 25 seed steps and 195 expanded steps, concentrated in Stage 7 residuals.
- Affected tracks: `sequence_policy, curriculum_boundary_review`
- Minimum next step: `design_stratified_sequence_data_plan_before_training`
- Causal allowed: `False`

### plan_window_evidence_stage7_only

- Priority: `p1`
- Evidence: Plan-window evidence currently has 13 windows, primarily Stage 7.
- Affected tracks: `plan_capsule_self_monitoring, strategy_arbitration`
- Minimum next step: `define_cross_stage_plan_window_export_requirements`
- Causal allowed: `False`

### growth_governor_not_frame_level

- Priority: `p1`
- Evidence: GrowthGovernor status exists as plan/design evidence, not per-frame status.
- Affected tracks: `structural_growth, promotion_review`
- Minimum next step: `non_causal_growth_governor_frame_status_design`
- Causal allowed: `False`

### stage4_h40_caveat_not_explained

- Priority: `p2`
- Evidence: Stage 4 is clean in the 500-sample profile but has an h40 overlay/base-control caveat.
- Affected tracks: `guardrail_definition, arbitrary_krk_validation`
- Minimum next step: `keep_as_guardrail_definition_caveat_until_control_frames_exist`
- Causal allowed: `False`

### cross_domain_transfer_not_in_frame_contract_yet

- Priority: `p2`
- Evidence: KPK/KQK bridge sanity is referenced historically but not exported as control-plane frames.
- Affected tracks: `kpk_kqk_transfer, domain_generalization`
- Minimum next step: `add_cross_domain_frame_requirements_after_krk_frame_export`
- Causal allowed: `False`

## Recommended Next Slice

- Slice: `export_replay_free_control_plane_frames_v0`
- Reason: Before collecting new data or sandboxing any mechanism, existing evidence should be exported into unified per-state frames so strategy, monitor, sequence, and guardrail tracks can be compared without Stage 7-specific scripts.
- Causal: `False`
- New playouts allowed: `False`

## Deferred

- `new_sequence_training_data_collection`
- `runtime_strategy_arbiter_sandbox`
- `runtime_internal_terminal_sandbox`
- `stage8_training`
- `stage7_promotion`

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
