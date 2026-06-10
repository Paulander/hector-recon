# Stage 7 Selected Path Target Spec v0

Status: `split_targets_required`

This is a non-causal design spec. It does not implement a runtime selector, terminal, repair, or training run.

## Target Specs

### `stage7.selected_path.strategy_ownership_gap.v0`

- Type: `strategy_ownership_training_target`
- State count: `2`
- Positive label: existing provider converts under forced ownership while selected provider max-plies
- Control label: validated protected states where selected provider converts or forced alternatives do not improve outcome
- Future consumer if validated: `strategy arbiter or owner-exit monitor dataset`

| State | Selected provider | Selected move | Target provider | Evidence |
| --- | --- | --- | --- | --- |
| `state.ac0b7ed500ea` | `krk.stage0_basin` | `a1a4` | `krk.fence_established` | `forced_provider_mates_h40` |
| `state.ff6652c8832c` | `krk.stage0_basin` | `a4e4` | `krk.drive_to_edge` | `forced_provider_mates_h40` |

Required features:

- `current_owner`
- `selected_owner_failed_h40`
- `alternative_provider_known_conversion_h40`
- `local_provider_competition_failed`
- `provider_score_scale_gap`
- `provider_family`
- `active_landmark_label`
- `repair_or_phase_monitor_signature`

Minimum future evidence:

- more than two ownership-gap states
- protected Stage 5/6 controls with safe stage0/edge/fence ownership
- paired no-change default-off check before any sandbox
- false-positive review where alternate provider should not own

Forbidden now:

- `boost target provider`
- `penalize stage0_basin`
- `make local_provider_competition_failed causal`
- `promote Stage 7`

### `stage7.selected_path.sequence_continuation_gap.v0`

- Type: `sequence_policy_or_continuation_capacity_target`
- State count: `2`
- Positive label: multi-step trajectory or continuation policy converts from state without runtime oracle
- Control label: provider-best and legal-first h40 labels that remain max_plies or draw
- Future consumer if validated: `ranked sequence-policy benchmark or plan-capsule model-expression redesign`

| State | Selected provider | Selected move | Target provider | Evidence |
| --- | --- | --- | --- | --- |
| `state.0afbf11aa123` | `krk.stage0_basin` | `a3e3` | `None` | `forced_providers_and_legal_first_h40_no_mate` |
| `state.38aed2f35911` | `krk.stage0_basin` | `a3a5` | `None` | `forced_providers_and_legal_first_h40_no_mate` |

Required features:

- `post_plan_stagnation`
- `plan_selection_needed`
- `repair_needed_monitor`
- `handoff_success_after_plan`
- `multi_step_progress_required`
- `trajectory_progress_terms`
- `closed_loop_drift_class`

Minimum future evidence:

- offline successful trajectories for the unresolved states or nearby controls
- hard-negative contrast moves from current failed selected paths
- teacher-forced and closed-loop split metrics
- successful post-box controls outside Stage 7 residuals

Forbidden now:

- `train Stage 8`
- `use DTM/tablebase at runtime`
- `add full-KRK continuation overlay`
- `tune current plan capsule micro-repair`

## Decision Gate

- Status: `non_causal_targets_defined_no_runtime_work`
- Next allowed action: `build_replay_free_selected_path_target_dataset_or_request_architecture_review`
- Why: The selected failure path is mixed; a single selector, penalty, or provider boost would conflate ownership errors with continuation-capacity/sequence errors.
