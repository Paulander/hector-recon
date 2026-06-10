# KRK Control-Plane Frame Quality Report v0

This is a non-causal quality report for the replay-free frame export. It does not authorize runtime arbitration, runtime terminals, Stage 7 promotion, Stage 8 training, or new playouts.

## Coverage

- Frames: `33`
- Frames by stage: `{'stage7': 9, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Outcome distribution: `{'unknown': 5, 'max_plies': 16, 'mate': 12}`
- Strategy proposal coverage: `{'frames_with': 31, 'total_attached_records': 87, 'frames_with_by_stage': {'stage7': 7, 'stage5': 8, 'stage6': 10, 'stage4': 6}}`
- Monitor coverage: `{'frames_with': 33, 'total_attached_records': 224, 'frames_with_by_stage': {'stage7': 9, 'stage5': 8, 'stage6': 10, 'stage4': 6}}`
- Plan-window coverage: `{'frames_with': 4, 'total_attached_records': 13, 'frames_with_by_stage': {'stage7': 4}}`
- Sequence-example coverage: `{'frames_with': 3, 'total_attached_records': 5, 'frames_with_by_stage': {'stage7': 3}}`

## Quality Flags

### some_frames_lack_strategy_proposals

- Severity: `medium`
- Count: `2`
- Interpretation: These frames can still carry context/monitor evidence but are not usable for provider-ranking benchmarks without additional proposal extraction.

### monitor_records_duplicate_across_duplicate_state_frames

- Severity: `medium`
- Count: `116`
- Interpretation: Monitor attachments exceed unique monitor IDs because some state IDs appear in multiple strategy records. Consumers should group by frame_id and dedupe by monitor_id when measuring monitor support.

### plan_windows_stage7_only

- Severity: `high`
- Count: `1`
- Interpretation: Plan-window evidence is not yet general across protected Stage 4/5/6 contexts.

### sequence_examples_stage7_only

- Severity: `high`
- Count: `1`
- Interpretation: Offline sequence examples remain concentrated in Stage 7 residual states; do not train a general KRK sequence policy from this alone.

### plan_window_duplicate_attachment

- Severity: `low`
- Count: `9`
- Interpretation: Several plan-window records share the same state/progress/outcome signature; this is useful evidence but should be deduped for statistical claims.

## Readiness

- `offline_strategy_arbitration_probe`: `ready_with_dedupe_and_missing_proposal_caveat`
- `offline_sequence_policy_benchmark`: `not_ready_general_krk_stage7_only`
- `internal_monitor_training_dataset`: `ready_for_non_causal_monitor_quality_analysis_only`
- `runtime_sandbox`: `blocked`
- `stage8_training`: `blocked`
- `stage7_promotion`: `blocked`

## Recommended Next Slice

- Slice: `control_plane_frame_dedupe_and_quality_filters_v0`
- Causal: `False`
- New playouts allowed: `False`
- Reason: Before using the frames for offline arbitration or sequence benchmarks, add dedupe/filter metadata and separate benchmark-ready frames from context-only frames.
