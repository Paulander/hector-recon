# Stage 7 0926 Move-Shape Role Candidate

Schema: `stage7_0926_move_shape_role_export.v1`
Causal status: `non_causal`
Role: `krk.post_box.king_support_fence_stabilizer`
Source candidate: `cand.krk.box_shrink.family_0926.king_support_fence_stabilizer.v1`
Promotion status: `proposed`

## Entry Terms

- `active_landmark_label.box_shrink`
- `post_reply_state_reached`
- `conversion_not_immediate`
- `rook_safe`
- `plan_capsule_entry_confirmed`
- `no_mate_in_one_available`

## Move-Shape Terms

- `candidate_is_king_move`
- `king_moves_toward_enemy`
- `king_moves_toward_rook_support`

## Post-Move Terms

- `rook_safe_after_move`
- `box_area_not_increased_after_move`
- `fence_exists_after_move`
- `fence_stable_after_move`
- `cut_preserved_after_move`
- `white_king_distance_to_enemy_decreases`
- `white_king_distance_to_rook_decreases`

## Guardrails

- `no_runtime_default_change`
- `no_direct_request`
- `no_state_hash_exception`
- `no_topology_mutation_during_gameplay`
- `handoff_packets_stats_shadow_candidates_remain_non_causal`

Next action: `compile_default_off_sandbox_only_if_runtime_can expose candidate move generation visibly`
