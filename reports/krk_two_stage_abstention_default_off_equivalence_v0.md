# KRK Two-Stage Abstention Default-Off Equivalence v0

Status: `default_off_equivalent`

Compared baseline Stage 5 `fence_established` against the same topology with the two-stage abstention selector flags present but disabled. The selector made no penalties and the compared metrics were identical.

- Topology: `snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json`
- Profile: `handoff_composition_v1`
- Samples: `3`
- Seed: `7`
- Horizon: `h40`
- Baseline artifact: `reports/krk_two_stage_abstention_default_off_baseline_stage5_3_h40.json`
- Disabled artifact: `reports/krk_two_stage_abstention_default_off_disabled_stage5_3_h40.json`

Acceptance:

- Same core metrics: `true`
- Disabled penalized count: `0`
- Disabled selected-penalized count: `0`
- Conversion status: `passed`
- Playouts: `{"mate": 3}`
- Shadow candidates: `0`

Next step: `enabled_tiny_smoke`
