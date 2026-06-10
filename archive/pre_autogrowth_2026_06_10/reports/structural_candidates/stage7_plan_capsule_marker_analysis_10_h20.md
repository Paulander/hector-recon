# Plan Capsule Marker Analysis

Schema: `plan_capsule_marker_analysis.v1`
Causal status: `non_causal`
Capsule: `krk.post_box_shrink_continuation`
Marker records: `8`

## Outcomes

- `mate`: 3
- `max_plies`: 5

## Diagnosis

- `entry_confirmed_mate_count`: 0
- `entry_confirmed_max_plies_count`: 5
- `mate_exit_count`: 3
- `max_plies_without_abort_count`: 5

## Recommendations

- `entry_terms_separate_candidate_ownership_from_already_successful_exit_states`
- `treat_mate_in_one_or_finish_terms_as_exit_interrupts`
- `add_owned_move_progress_or_ttl_failure_monitor_before_causal_capsule`

Next action: `design_non_causal_owned_move_progress_monitor`
