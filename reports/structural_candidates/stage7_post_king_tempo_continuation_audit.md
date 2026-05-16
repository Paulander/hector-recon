# Stage 7 Post-King-Tempo Continuation Audit

- Candidate: `cand.krk.box_shrink.post_king_tempo_continuation.v1`
- Causal status: `non_causal`
- Diagnosis: `post_king_tempo_followup_selection_problem`
- Counts: {'records': 25, 'families': 2, 'outcome_counts': {'max_plies': 12, 'mate': 13}, 'failed_support': 12}
- Family classes: {'post_king_tempo_lacks_corner_net_pressure': 1, 'post_king_tempo_converts': 1}

## Families

### `stage7.post_king_tempo.family_01`

- Support: 12
- Outcomes: {'max_plies': 12}
- Class: `post_king_tempo_lacks_corner_net_pressure`
- Post-reply FEN: `3k4/R7/8/8/8/8/4K3/8 w - - 2 2`
- King-tempo move: `e2f2`
- Post-tempo FEN: `3k4/R7/8/8/8/8/5K2/8 b - - 3 2`
- Metrics: {'current_box_area': 7, 'post_box_area': 7, 'current_enemy_edge_distance': 0, 'post_enemy_edge_distance': 0, 'current_enemy_corner_distance': 3, 'post_enemy_corner_distance': 3, 'current_white_king_enemy_distance': 6, 'post_white_king_enemy_distance': 6}
- Context terms: ['box_shrink_available', 'enemy_king_near_edge', 'enemy_king_restricted', 'fence_exists', 'fence_needs_repair', 'post_fence_conversion_needed', 'rook_safe', 'wrong_tempo_detected']

Replay:

- h=20: max_plies in 20 plies; first white `f2g3` via `krk.stage0_basin`
- h=40: max_plies in 40 plies; first white `f2g3` via `krk.stage0_basin`
- h=60: max_plies in 60 plies; first white `f2g3` via `krk.stage0_basin`

Legal-first follow-up sweep:

- First White FEN: `4k3/R7/8/8/8/8/5K2/8 w - - 4 3`
- Tested moves: 7
- Converting moves: ['a7c7']

### `stage7.post_king_tempo.family_02`

- Support: 13
- Outcomes: {'mate': 13}
- Class: `post_king_tempo_converts`
- Post-reply FEN: `6k1/R7/8/8/8/8/5K2/8 w - - 2 2`
- King-tempo move: `f2e2`
- Post-tempo FEN: `6k1/R7/8/8/8/8/4K3/8 b - - 3 2`
- Metrics: {'current_box_area': 7, 'post_box_area': 7, 'current_enemy_edge_distance': 0, 'post_enemy_edge_distance': 0, 'current_enemy_corner_distance': 1, 'post_enemy_corner_distance': 1, 'current_white_king_enemy_distance': 6, 'post_white_king_enemy_distance': 6}
- Context terms: ['box_shrink_available', 'enemy_king_near_edge', 'enemy_king_restricted', 'fence_exists', 'fence_needs_repair', 'post_fence_conversion_needed', 'rook_safe', 'wrong_tempo_detected']

Replay:

- h=20: mate in 18 plies; first white `a7a8` via `krk.stage0_basin`
- h=40: mate in 18 plies; first white `a7a8` via `krk.stage0_basin`
- h=60: mate in 18 plies; first white `a7a8` via `krk.stage0_basin`

Legal-first follow-up sweep:

- First White FEN: `5k2/R7/8/8/8/8/4K3/8 w - - 4 3`
- Tested moves: 7
- Converting moves: ['a7a8']

## Candidate Update

```json
{
  "schema_version": "structural_candidate_update.v1",
  "candidate_id": "cand.krk.box_shrink.post_king_tempo_continuation.v1",
  "candidate_status": "proposed",
  "diagnostic_labels": [
    "post_king_tempo_converts",
    "post_king_tempo_lacks_corner_net_pressure"
  ],
  "source_monitor_script": "growth.monitor.successor_miscalibration",
  "source_terms": [
    "stage7_king_tempo_license_confirmed",
    "selected_successor_miscalibrated",
    "repeated_conversion_failure"
  ],
  "trigger_failure_classes": [
    "selected_successor_miscalibrated",
    "repeated_conversion_failure",
    "high_score_conversion_failure"
  ],
  "target_skill": "krk.box_shrink",
  "parent_skill": "krk.drive_to_edge",
  "proposed_change": {
    "kind": "post_king_tempo_continuation_role_audit",
    "candidate_role": "krk.post_king_tempo_continuation",
    "notes": "The first king-tempo handoff improves Stage 7 but leaves a compact repeated post-tempo failure family. Next repair should target follow-up ownership after the king-tempo move, not broaden the first king-tempo license.",
    "legal_first_followup_summary": {
      "outcome_counts": {
        "max_plies": 6,
        "mate": 2,
        "draw": 6
      },
      "converting_moves": {
        "stage7.post_king_tempo.family_01": [
          "a7c7"
        ],
        "stage7.post_king_tempo.family_02": [
          "a7a8"
        ]
      },
      "outcomes_by_family": {
        "stage7.post_king_tempo.family_01": {
          "max_plies": 3,
          "mate": 1,
          "draw": 3
        },
        "stage7.post_king_tempo.family_02": {
          "mate": 1,
          "max_plies": 3,
          "draw": 3
        }
      },
      "common_converting_terms_by_family": {
        "stage7.post_king_tempo.family_01": [
          "box_area_decreases_after_move",
          "box_area_not_increased_after_move",
          "box_area_not_increased_after_worst_reply",
          "box_shrink_available",
          "candidate_is_rook_move",
          "candidate_is_rook_transfer",
          "cut_preserved_after_move",
          "edge_rook_transfer_recovery_available",
          "edge_trap_shape_available",
          "enemy_corner_distance_not_increased_after_move",
          "enemy_edge_distance_not_increased_after_move",
          "enemy_king_near_edge",
          "enemy_king_restricted",
          "fence_exists",
          "fence_exists_after_move",
          "fence_needs_repair",
          "king_approach_after_fence_available",
          "king_support_improvement_move_exists",
          "no_draw_after_worst_reply",
          "post_fence_conversion_needed",
          "repair_or_reestablish_cut_available",
          "rook_destination_not_adjacent_enemy",
          "rook_has_safe_lateral_transfer",
          "rook_lateral_transfer",
          "rook_safe",
          "rook_safe_after_candidate",
          "rook_safe_after_move",
          "rook_transfer_after_fence_available",
          "safe_check_available",
          "safe_rook_edge_transfer_available",
          "safe_rook_long_transfer_available",
          "white_king_can_improve_support",
          "wrong_tempo_detected"
        ],
        "stage7.post_king_tempo.family_02": [
          "box_area_not_increased_after_move",
          "box_shrink_available",
          "candidate_is_rook_move",
          "checking_line_created",
          "corner_net_pressure_available",
          "cut_preserved_after_move",
          "edge_rook_transfer_recovery_available",
          "edge_trap_shape_available",
          "enemy_corner_distance_not_increased_after_move",
          "enemy_edge_distance_not_increased_after_move",
          "enemy_king_near_edge",
          "enemy_king_restricted",
          "fence_exists",
          "fence_exists_after_move",
          "fence_needs_repair",
          "king_approach_after_fence_available",
          "king_support_improvement_move_exists",
          "no_draw_after_worst_reply",
          "post_fence_conversion_needed",
          "repair_or_reestablish_cut_available",
          "rook_destination_far_from_enemy",
          "rook_destination_not_adjacent_enemy",
          "rook_has_safe_lateral_transfer",
          "rook_safe",
          "rook_safe_after_candidate",
          "rook_safe_after_move",
          "rook_safe_after_worst_reply",
          "rook_to_checking_line",
          "rook_to_edge_file",
          "rook_to_edge_rank",
          "rook_transfer_after_fence_available",
          "rook_transfer_vertical",
          "safe_check_available",
          "safe_check_created",
          "safe_rook_edge_transfer_available",
          "safe_rook_long_transfer_available",
          "white_king_can_improve_support",
          "wrong_tempo_detected"
        ]
      }
    }
  },
  "promotion_status": "proposed",
  "causal_status": "non_causal",
  "credit": 0.0
}
```
