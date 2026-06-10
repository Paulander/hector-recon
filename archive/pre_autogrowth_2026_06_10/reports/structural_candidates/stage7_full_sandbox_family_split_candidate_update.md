# Stage 7 Family-Split Candidate Update

Stage 7 status: `local_valid_composition_quarantined`

## Result

Stop broad Stage 7 drive-repair tuning. Use family-specific visible roles for controlled-provider-success families and classify state.6ed746a91c76 before training a new overlay.

## Families

### state.ff6652c8832c

FEN: `8/8/8/8/4R3/2k5/4K3/8 w - - 2 2`
Runtime: `krk.stage7_drive_repair` / `e2e3`
Diagnosis: `existing_provider_can_convert_under_controlled_ownership`
Next: `derive_family_specific_visible_role_or_weight_calibration_probe`
Controlled mating providers:
- `krk.drive_to_edge` h40 mate in 11 via `e4h4`
- `krk.drive_to_edge` h50 mate in 11 via `e4h4`

### state.38aed2f35911

FEN: `8/8/8/R7/4k3/8/8/3K4 w - - 2 2`
Runtime: `krk.stage7_drive_repair` / `a5b5`
Diagnosis: `existing_provider_can_convert_under_controlled_ownership`
Next: `derive_family_specific_visible_role_or_weight_calibration_probe`
Controlled mating providers:
- `krk.stage0_basin` h40 mate in 29 via `d1e2`
- `krk.stage0_basin` h50 mate in 29 via `d1e2`
- `krk.edge_trap_close` h40 mate in 29 via `d1e2`
- `krk.edge_trap_close` h50 mate in 29 via `d1e2`
- `krk.edge_trap_enemy_between` h40 mate in 29 via `d1e2`
- `krk.edge_trap_enemy_between` h50 mate in 29 via `d1e2`
- `krk.fence_established` h40 mate in 29 via `d1e2`
- `krk.fence_established` h50 mate in 29 via `d1e2`

### state.6ed746a91c76

FEN: `8/8/8/2k5/8/8/3K4/3R4 w - - 2 2`
Runtime: `krk.stage7_drive_repair` / `d2c1`
Diagnosis: `no_legal_first_conversion_at_h50_under_current_graph`
Next: `classify_as_capacity_or_horizon_gap_before_new_overlay_training`
- No controlled provider mate found at h40/h50.
- Legal-first h50: no mating move under current graph.

## Candidate Status

- `cand.krk.box_shrink.stage7_drive_repair.v1`: `overbroad_adapter_candidate`; next `do_not_promote_or_warm_up_current_broad_drive_repair; split by family evidence`
- `cand.krk.box_shrink.family_ff6652c8832c.drive_to_edge_adapter.v1`: `sandbox_ready_if_visible_terms_separate`; next `derive_narrow_visible_role_from family ff6652c8832c; avoid broad stage7_drive_repair`
- `cand.krk.box_shrink.family_38aed2f35911.controlled_existing_provider_continuation.v1`: `needs_role_or_continuation_calibration`; next `derive visible post-box continuation role or controlled ownership calibration; do not train new provider first`
- `cand.krk.box_shrink.family_6ed746a91c76.unresolved_continuation.v1`: `capacity_or_horizon_gap_candidate`; next `deeper horizon/tablebase-style audit or narrow post-box continuation overlay training candidate`
