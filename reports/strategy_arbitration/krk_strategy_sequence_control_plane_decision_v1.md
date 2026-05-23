# KRK Strategy/Sequence Control Plane Decision v1

This decision gate closes the candidate-frame source benchmark without authorizing runtime behavior.

## Decision

- status: `candidate_generation_control_plane_ready_for_architecture_review`
- recommended_next_step: `architecture_review_for_default_off_candidate_generation_sandbox_scope`
- runtime_sandbox_allowed_by_this_packet: `False`

## Evidence

- protected_positive_capacity_candidates: 11
- protected_negative_capacity_ratio: 0.3125
- progress_window_supported_move_h40_mate_count: 0
- stage7_training_row_count: 0
- runtime_flags_false: `True`

## Blockers Before Runtime

- selector policy remains blocked
- capacity labels are not ownership labels
- progress-window supported moves remain held-out target failures
- no runtime candidate generator has review authorization

## Still Forbidden

- `general_runtime_selector`
- `default_runtime_candidate_generator`
- `Stage7_promotion`
- `Stage8_training_from_unresolved_Stage7`
- `runtime_DTM_or_tablebase`
- `gameplay_topology_mutation`
- `hidden_Python_routing`
