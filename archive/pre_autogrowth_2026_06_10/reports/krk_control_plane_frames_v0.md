# KRK Control-Plane Frames v0

This replay-free export creates non-causal `ControlPlaneEvidenceFrame` records from existing artifacts. It does not add runtime consumers, DTM/tablebase lookup, terminals, arbiters, promotions, training, or topology changes.

## Summary

- Frames: `33`
- Frames by source stage: `{'stage7': 9, 'stage5': 8, 'stage6': 10, 'stage4': 6}`
- Strategy proposal frames: `87`
- Internal monitor records attached: `224`
- Plan-capsule window records attached: `13`
- Sequence training examples attached: `5`
- New playouts added: `0`

## Remaining Gaps

- `sequence_examples_are_stage7_only`
- `plan_capsule_windows_are_stage7_only`
- `growth_governor_status_is_inferred_summary_not_runtime_export`
- `cross_domain_bridge_frames_not_exported_yet`

## Recommended Next Slice

`control_plane_frame_quality_report_v0`
