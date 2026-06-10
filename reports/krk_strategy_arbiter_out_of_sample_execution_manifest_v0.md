# KRK Strategy Arbiter Out-of-Sample Execution Manifest v0

This is a non-causal execution manifest. It does not run labels, change runtime behavior, implement a selector, promote Stage 7, or train Stage 8.

## Summary

- Job count: `12`
- Jobs by stage: `{'stage4': 4, 'stage5': 4, 'stage6': 4}`
- Jobs by source kind: `{'deterministic_curriculum_sample': 10, 'replay_free_existing_control': 2}`
- All bindings valid: `True`
- Required stage coverage met: `True`
- Missing path count: `0`
- Decision: `execution_manifest_ready_for_review`

## Bounds

- Max states: `12`
- Per-stage max: `4`
- Horizon: `h40`
- Stage 7 training rows: `0`

## Jobs

- `job.krk.out_of_sample_control.87e4e2b0e724` stage=`stage5` state=`state.3dca34326fca` source=`replay_free_existing_control` label=`fence_established` prior=`max_plies`
- `job.krk.out_of_sample_control.51d3f56d8ce5` stage=`stage6` state=`state.69711173114a` source=`replay_free_existing_control` label=`drive_to_edge` prior=`mate`
- `job.krk.out_of_sample_control.678147e30d2d` stage=`stage4` state=`state.ea634c29ece7` source=`deterministic_curriculum_sample` label=`edge_trap_wrong_tempo`
- `job.krk.out_of_sample_control.99505412b76a` stage=`stage4` state=`state.2f5f57c82e5b` source=`deterministic_curriculum_sample` label=`edge_trap_wrong_tempo`
- `job.krk.out_of_sample_control.789de8265a5a` stage=`stage4` state=`state.6ed5d7581360` source=`deterministic_curriculum_sample` label=`edge_trap_wrong_tempo`
- `job.krk.out_of_sample_control.c7efcd313480` stage=`stage4` state=`state.e99b2e731810` source=`deterministic_curriculum_sample` label=`edge_trap_wrong_tempo`
- `job.krk.out_of_sample_control.55f8cad4eef7` stage=`stage5` state=`state.7cab65617cd8` source=`deterministic_curriculum_sample` label=`fence_established`
- `job.krk.out_of_sample_control.74900f2d8408` stage=`stage5` state=`state.7b116c49a009` source=`deterministic_curriculum_sample` label=`fence_established`
- `job.krk.out_of_sample_control.dd43b5f1679f` stage=`stage5` state=`state.388d05197dd9` source=`deterministic_curriculum_sample` label=`fence_established`
- `job.krk.out_of_sample_control.4bbcc80b2558` stage=`stage6` state=`state.e65bbd1e9f0c` source=`deterministic_curriculum_sample` label=`drive_to_edge`
- `job.krk.out_of_sample_control.1502108d8abf` stage=`stage6` state=`state.cb9f8eea01fd` source=`deterministic_curriculum_sample` label=`drive_to_edge`
- `job.krk.out_of_sample_control.41645e9be76b` stage=`stage6` state=`state.df10abc0731f` source=`deterministic_curriculum_sample` label=`drive_to_edge`

## Recommended Next Step

`review_execution_manifest_before_any_h40_label_run`

Do not execute h40 labels until this manifest is reviewed.
