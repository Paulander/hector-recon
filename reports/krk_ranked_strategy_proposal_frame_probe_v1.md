# KRK Ranked Strategy Proposal Frame Probe v1

This offline probe evaluates frame-level ranked proposal context. It does not treat every proposal in a successful frame as a positive owner.

## Frame Summary

- `frame_count`: `22`
- `training_frame_count`: `15`
- `stage7_challenge_frame_count`: `7`
- `outcome_counts`: `{'unknown': 3, 'max_plies': 10, 'mate': 9}`
- `top_provider_family_counts`: `{'stage0_basin': 14, 'drive_to_edge': 4, 'edge_trap': 4}`
- `stage7_top_provider_family_counts`: `{'stage0_basin': 3, 'drive_to_edge': 4}`

## Results

- `top_provider_family` accuracy=`0.7333333333333333` precision=`0.7272727272727273` recall=`0.8888888888888888` negative_suppression=`0.5`
- `top_family_maturity` accuracy=`0.7333333333333333` precision=`0.7272727272727273` recall=`0.8888888888888888` negative_suppression=`0.5`
- `active_label_top_family` accuracy=`0.5333333333333333` precision=`0.5714285714285714` recall=`0.8888888888888888` negative_suppression=`0.0`
- `top_family_raw_bucket` accuracy=`0.8` precision=`0.75` recall=`1.0` negative_suppression=`0.5`
- `provider_family_set` accuracy=`0.7333333333333333` precision=`0.7272727272727273` recall=`0.8888888888888888` negative_suppression=`0.5`
- `source_stage_top_family` accuracy=`0.5333333333333333` precision=`0.5714285714285714` recall=`0.8888888888888888` negative_suppression=`0.0`

## Interpretation

- Stage 7 training leakage: `False`
- Finding: Ranked proposal-frame context is available, but frame-level outcome labels are too coarse to identify the winning proposal inside a frame.

## Decision

- Status: `ranked_frames_available_label_semantics_too_coarse`
- Recommended next step: `derive_state_local_contrast_labels_before_runtime_selector`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
