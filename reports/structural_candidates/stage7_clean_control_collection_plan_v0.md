# Stage 7 Clean Control Collection Plan v0

Status: `plan_only`

Goal: collect clean non-sandbox Stage 7/post-box sequence controls and additional ownership-gap examples before any runtime selector, arbiter, or plan-capsule repair.

## Why

The selected-path probe found useful offline separation, but the sequence success controls are sourced from prior repair/sandbox artifacts. That is acceptable for exploratory benchmarking, but not for runtime authorization.

## Clean Control Definitions

Positive sequence control:

- `active_landmark_label == box_shrink`
- `playout_result == mate` within h40
- Artifact produced without Stage 7 repair sandbox flags
- No runtime DTM/tablebase lookup
- Trace includes initial selected move and enough handoff/plan evidence to classify post-box continuation
- Not sourced only from candidate repair, support adapter, role-owned arbitration, or plan-capsule micro-tuning runs

Hard negative sequence control:

- Same or nearby post-box family
- `playout_result == max_plies` or draw within h40
- No runtime repair sandbox flags
- Selected provider/move and failure class visible

Ownership-gap positive:

- Selected provider max-plies
- Alternative existing provider forced at h40 mates
- Current owner and target provider visible
- Protected lower-stage providers unchanged

Protected safe-owner control:

- Stage 4/5/6 protected state
- Selected owner converts at h40
- Monitor/phase terms may be present but should not imply forced owner exit
- Validated provider metadata remains frozen/protected

## Collection Phases

1. `replay_free_artifact_classification`: classify existing Stage 7 artifacts as clean-baseline/default-off versus repair-sandbox-sourced. No new playouts.
2. `replay_free_clean_control_recovery`: recover only clean h40 post-box mate/max_plies controls from baseline/default-off artifacts with selected move/provider evidence. No new playouts.
3. `bounded_missing_cell_labels`: if clean controls remain insufficient, run a tiny h40 label job with current defaults and no repair flags, tracing failures only.

Bounded label limits:

- Max samples: `10`
- Horizon: `40`
- Trace mode: `failures_only`
- Diagnostic caches: enabled
- Stop if projected to hours

## Minimum Acceptance Before Runtime Review

- Clean sequence success controls: `5`
- Paired sequence hard negatives: `5`
- Ownership-gap positives: `5`
- Protected safe-owner controls: `12`
- Held-out family split required: `true`
- Source-bias audit required: `true`

## Blocked Actions

- `runtime arbiter implementation`
- `abstention selector tuning`
- `Stage 7 support adapter`
- `Plan Capsule runtime repair`
- `Stage 7 promotion`
- `Stage 8 training`
- `causal internal terminals`

Next allowed slice: `implement_replay_free_clean_artifact_manifest`
