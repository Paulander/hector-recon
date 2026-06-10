# Plan Capsule Owned-Window Analysis

Schema: `plan_capsule_owned_window_analysis.v1`
Causal status: `non_causal`
Capsule: `krk.post_box_shrink_continuation`
TTL white moves: `3`
Windows: `5`
TTL failures: `3`

## Windows

- sample `1` result `max_plies`
  moves: `e2d1, d1c1, c1c2`
  progress: `box_area_preserved_over_owned_window, enemy_edge_distance_not_worse_over_owned_window`
  ttl_failure: `True`
- sample `2` result `max_plies`
  moves: `e4f3, f3g4, g4f3`
  progress: `box_area_preserved_over_owned_window, enemy_edge_distance_not_worse_over_owned_window, enemy_corner_distance_not_worse_over_owned_window, white_king_support_improved_over_owned_window`
  ttl_failure: `False`
- sample `3` result `max_plies`
  moves: `a6a8, a8d8, d1e2`
  progress: `box_area_decreased_over_owned_window, enemy_edge_distance_not_worse_over_owned_window, enemy_corner_distance_not_worse_over_owned_window, white_king_support_improved_over_owned_window`
  ttl_failure: `False`
- sample `6` result `max_plies`
  moves: `a5h5, h5h8, h8d8`
  progress: `box_area_preserved_over_owned_window, enemy_edge_distance_not_worse_over_owned_window, enemy_corner_distance_not_worse_over_owned_window`
  ttl_failure: `True`
- sample `9` result `max_plies`
  moves: `a5h5, h5h8, h8d8`
  progress: `box_area_preserved_over_owned_window, enemy_edge_distance_not_worse_over_owned_window, enemy_corner_distance_not_worse_over_owned_window`
  ttl_failure: `True`

Next action: `use_owned_window_monitor_as_non_causal_capsule_validation_signal`
