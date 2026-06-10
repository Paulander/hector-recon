# KRK Candidate Generation Strategy Review v0

Non-causal strategy/sequence review after the quarantined progress-window reconsideration sandbox.

## Findings

- `protected_positive_capacity_recall_current`: `0.0`
- `protected_positive_capacity_missing_count`: `11`
- `validated_provider_pack_positive_recall_if_included`: `1.0`
- `validated_provider_pack_negative_capacity_inclusion_rate`: `0.3125`
- `progress_window_supported_candidate_mate_count`: `0`
- `progress_window_unsupported_visible_candidate_mate_count`: `0`
- `sequence_policy_success_controls_met`: `False`
- `sequence_policy_ready_for_runtime_review`: `False`
- `strategy_ownership_ready_for_runtime_review`: `False`

## Candidate Channels

- `validated_provider_pack`: `recall_promising_but_selection_risk`; role=`candidate_generation`; causal=`non_causal`
- `candidate_move_frame`: `needed_for_provider_omission_cases`; role=`legal_move_hypothesis_generation`; causal=`non_causal_design_needed`
- `plan_capsule_sequence_candidate`: `needed_for_progress_window_and_stage7_sequence_gaps`; role=`multi_step_candidate_generation`; causal=`non_causal_design_needed`
- `broader_krk_strategy_proposal`: `needed_for_stage7_boundary_cases`; role=`phase_boundary_strategy_generation`; causal=`non_causal_design_needed`

## Answers

- alternatives_should_be_visible: `['validated provider candidates with protected positive-capacity evidence', 'candidate moves from CandidateMoveFrame when provider proposals omit legal progress moves', 'plan/capsule sequence candidates when one-ply provider moves do not convert', 'broader KRK strategy proposals when local stage labels are boundary signals']`
- missing_from_current_frames: `{'protected_positive_capacity_missing_count': 11, 'missing_provider_family_counts': {'edge_trap': 6, 'fence_established': 2, 'stage0_basin': 3}, 'missing_source_stage_counts': {'stage4': 3, 'stage5': 7, 'stage6': 1}}`
- existing_validated_provider_candidates: `['krk.edge_trap_close', 'krk.edge_trap_enemy_between', 'krk.edge_trap_wrong_tempo', 'krk.fence_established', 'krk.stage0_basin']`
- capacity_evidence_only: `['forced-provider h40 mate labels', 'forced-provider h40 max_plies labels', 'validated-provider candidate-set counterfactual rows']`

## Decision

- status: `strategy_sequence_control_plane_v1_needed`
- next: `define_non_causal_strategy_sequence_candidate_frame_v1`
- runtime_sandbox_allowed: `False`
