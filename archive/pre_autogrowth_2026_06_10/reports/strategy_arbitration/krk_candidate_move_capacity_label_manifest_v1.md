# KRK CandidateMoveFrame Capacity Label Manifest v1

This manifest proposes a capped protected-only offline label slice. It does not run labels and does not authorize runtime selection.

## Decision

- status: `bounded_candidate_move_capacity_manifest_ready`
- labels_run_by_this_artifact: `False`
- selector_allowed: `False`
- recommended_next_step: `run_bounded_offline_candidate_move_capacity_labels`

## Summary

- candidate_pool_count: 282
- job_count: 12
- job_cap: 12
- job_count_by_stage: `{'stage4': 4, 'stage5': 4, 'stage6': 4}`
- selected_move_job_count: 0
- stage7_job_count: 0

## Jobs

### cmcap.v1.001

- source_stage: `stage4`
- active_landmark_label: `wrong_tempo_control`
- candidate_move_uci: `e5e8`
- selected_move_before_observation: `f6f7`
- label_semantics: `forced_first_move_capacity_not_runtime_ownership_label`

### cmcap.v1.002

- source_stage: `stage5`
- active_landmark_label: `fence_established`
- candidate_move_uci: `h7h8`
- selected_move_before_observation: `c6b6`
- label_semantics: `forced_first_move_capacity_not_runtime_ownership_label`

### cmcap.v1.003

- source_stage: `stage6`
- active_landmark_label: `drive_to_edge`
- candidate_move_uci: `a1a8`
- selected_move_before_observation: `a1g1`
- label_semantics: `forced_first_move_capacity_not_runtime_ownership_label`

### cmcap.v1.004

- source_stage: `stage4`
- active_landmark_label: `wrong_tempo_control`
- candidate_move_uci: `e5h5`
- selected_move_before_observation: `f6f7`
- label_semantics: `forced_first_move_capacity_not_runtime_ownership_label`

### cmcap.v1.005

- source_stage: `stage5`
- active_landmark_label: `fence_established`
- candidate_move_uci: `e7g7`
- selected_move_before_observation: `e7e8`
- label_semantics: `forced_first_move_capacity_not_runtime_ownership_label`

### cmcap.v1.006

- source_stage: `stage6`
- active_landmark_label: `drive_to_edge`
- candidate_move_uci: `a1a8`
- selected_move_before_observation: `a1d1`
- label_semantics: `forced_first_move_capacity_not_runtime_ownership_label`

### cmcap.v1.007

- source_stage: `stage4`
- active_landmark_label: `wrong_tempo_control`
- candidate_move_uci: `e5e7`
- selected_move_before_observation: `f6f7`
- label_semantics: `forced_first_move_capacity_not_runtime_ownership_label`

### cmcap.v1.008

- source_stage: `stage5`
- active_landmark_label: `fence_established`
- candidate_move_uci: `h7a7`
- selected_move_before_observation: `h7c7`
- label_semantics: `forced_first_move_capacity_not_runtime_ownership_label`

### cmcap.v1.009

- source_stage: `stage6`
- active_landmark_label: `drive_to_edge`
- candidate_move_uci: `a1c1`
- selected_move_before_observation: `a1d1`
- label_semantics: `forced_first_move_capacity_not_runtime_ownership_label`

### cmcap.v1.010

- source_stage: `stage4`
- active_landmark_label: `wrong_tempo_control`
- candidate_move_uci: `e5g5`
- selected_move_before_observation: `f6f7`
- label_semantics: `forced_first_move_capacity_not_runtime_ownership_label`

### cmcap.v1.011

- source_stage: `stage5`
- active_landmark_label: `fence_established`
- candidate_move_uci: `h7b7`
- selected_move_before_observation: `h7c7`
- label_semantics: `forced_first_move_capacity_not_runtime_ownership_label`

### cmcap.v1.012

- source_stage: `stage6`
- active_landmark_label: `drive_to_edge`
- candidate_move_uci: `a1a7`
- selected_move_before_observation: `a1g1`
- label_semantics: `forced_first_move_capacity_not_runtime_ownership_label`

## Boundary

These jobs are offline capacity-label requests only. They are not runtime inputs, selector labels, guardrails, or promotion evidence.
