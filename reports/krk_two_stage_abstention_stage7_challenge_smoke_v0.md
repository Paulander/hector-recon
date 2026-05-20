# KRK Two-Stage Abstention Stage 7 Challenge Smoke v0

Status: `stage7_challenge_no_target_improvement`

The two-stage abstention selector was enabled on the held-out Stage 7 `box_shrink` challenge with the explicit Stage 7 allow flag. It fired, but no penalized suggestion became selected and target conversion did not improve.

- Topology: `snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json`
- Profile: `handoff_composition_v1`
- Samples: `3`
- Seed: `11`
- Horizon: `h40`
- Penalty: `1.0`
- Unsafe threshold: `0.45`
- Preserve threshold: `0.5`

| Run | Playouts | Conversion | Shadows | Penalized | Selected penalized |
| --- | --- | --- | ---: | ---: | ---: |
| Baseline | `{"max_plies": 2, "mate": 1}` | `failed` | 3 | 0 | 0 |
| Enabled | `{"max_plies": 2, "mate": 1}` | `failed` | 3 | 12 | 0 |

Interpretation: the selector can fire on Stage 7 when explicitly allowed, but the penalized suggestions were not selected and target conversion did not improve. This does not justify scaling or threshold tuning as the next action.

Next step: `go_no_go_review`
