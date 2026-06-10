# KRK Stage 4 Caveat Sequence Review v0

Non-causal review of the single repeated Stage 4 h40 caveat failure.

## Decision

- status: `stage4_caveat_sequence_followup_gap_review_ready`
- selector_allowed: `False`
- selector_training_allowed: `False`
- runtime_changes_allowed: `False`
- recommended_next_step: `review_stage4_sequence_candidates_or_keep_as_known_residual`

## Summary

- target_state_id: `state.44938ccb8ab7`
- target_fen: `1R6/1K6/8/k7/8/8/8/8 w - - 0 1`
- target_selected_move: `b8h8`
- overlay_failure_packet_count: `32`
- base_failure_packet_count: `32`
- target_packet_count: `96`
- target_phase_counts: `{"('post_own_move', 'local_landmark_failed', 'failed')": 32, "('post_opponent_reply', 'max_plies', 'failed')": 32, "('playout_summary', 'max_plies', 'failed')": 32}`
- single_unique_failure: `True`
- base_control_reproduces_failure_count: `True`
- selector_training_row_count: `0`
- stage7_training_row_count: `0`

## Phase Snapshots

- `post_own_move`: `{'phase': 'post_own_move', 'status': 'failed', 'observed_outcome': 'local_landmark_failed', 'failed': ['reward_confirmed.edge_trap_wrong_tempo'], 'achieved': ['visible_fence_contract_confirmed'], 'fen': '1R6/1K6/8/k7/8/8/8/8 w - - 0 1', 'move': 'b8h8', 'post_reply_fen': None, 'black_reply': None, 'playout_result': None, 'plies': None, 'semantic_alignment_status': None, 'reward_confirmed': False, 'visible_fence_contract_confirmed': True, 'fence_survived_reply': None, 'handoff_gap': None, 'route_conflict': None, 'successor_selected_skill': None, 'selected_skill_source': None, 'selected_successor_contract_met': None, 'provider_selected_without_role_license': None, 'successor_best_score': None, 'successor_second_score': None, 'failure_classes': None, 'final_mate_in_one_available': None, 'stagnation_summary_present': False}`
- `post_opponent_reply`: `{'phase': 'post_opponent_reply', 'status': 'failed', 'observed_outcome': 'max_plies', 'failed': ['survived_opponent_reply'], 'achieved': ['visible_fence_survived_reply'], 'fen': '1R6/1K6/8/k7/8/8/8/8 w - - 0 1', 'move': 'b8h8', 'post_reply_fen': '7R/1K6/8/8/k7/8/8/8 w - - 2 2', 'black_reply': 'a5a4', 'playout_result': 'max_plies', 'plies': 40, 'semantic_alignment_status': 'visible_contract_without_reward', 'reward_confirmed': False, 'visible_fence_contract_confirmed': True, 'fence_survived_reply': True, 'handoff_gap': False, 'route_conflict': False, 'successor_selected_skill': 'krk.stage0_basin', 'selected_skill_source': 'actuator_score', 'selected_successor_contract_met': False, 'provider_selected_without_role_license': True, 'successor_best_score': 7.45560371055603, 'successor_second_score': None, 'failure_classes': [], 'final_mate_in_one_available': False, 'stagnation_summary_present': False}`
- `playout_summary`: `{'phase': 'playout_summary', 'status': 'failed', 'observed_outcome': 'max_plies', 'failed': ['conversion_to_mate'], 'achieved': [], 'fen': '1R6/1K6/8/k7/8/8/8/8 w - - 0 1', 'move': 'b8h8', 'post_reply_fen': None, 'black_reply': None, 'playout_result': 'max_plies', 'plies': 40, 'semantic_alignment_status': 'visible_contract_without_reward', 'reward_confirmed': None, 'visible_fence_contract_confirmed': None, 'fence_survived_reply': None, 'handoff_gap': None, 'route_conflict': None, 'successor_selected_skill': None, 'selected_skill_source': None, 'selected_successor_contract_met': None, 'provider_selected_without_role_license': None, 'successor_best_score': None, 'successor_second_score': None, 'failure_classes': [], 'final_mate_in_one_available': False, 'stagnation_summary_present': False}`

## Diagnosis

- primary: `stage4_sequence_followup_gap_single_state`
- support: `all Stage 4 h40 failures collapse to one unique state/move`
- support: `same failure count reproduces in the paired Stage 5 base control`
- support: `post-own move confirms visible fence but fails local reward confirmation`
- support: `post-reply continuation selects stage0_basin by actuator score without a visible role license`
- support: `failure is max_plies after follow-up, not immediate illegal move or runtime mutation`
- risk: `the target is a repeated curriculum state, so selector labels are too narrow`
- risk: `a direct state/move patch would violate the no exact-state runtime exception invariant`
- risk: `a broad stage0 penalty would risk protected safe-preservation cases`

## Recommended Next Options

- `stage4_sequence_candidate_review`: Need to identify visible follow-up candidates after b8h8/a5a4 before any runtime change. (`non_causal_review_first`)
- `synthetic_stage4_contrast_generation`: One repeated failure state is not enough for selector validation; generate stratified variants without hand-authoring policy. (`non_causal_data_design_first`)
- `keep_stage4_known_residual_guardrail`: The caveat is isolated and non-regressive; selector work can stay blocked while broader KRK sequence work proceeds. (`no_runtime_change`)
