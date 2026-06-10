# Stage 7 Post-Box Family Diagnosis

Schema: `stage7_post_box_family_diagnosis.v1`
Causal status: `non_causal`
Stage 7 status: `local_valid_composition_quarantined`
Families: `4`

## Family Counts

- `existing_provider_can_convert_if_family_role_selects_it`: 2
- `unresolved_by_existing_forced_providers_at_h80`: 2

## Families

### stage7.post_box.family_ff6652c8832c

- State: `state.ff6652c8832c`
- FEN: `8/8/8/8/4R3/2k5/4K3/8 w - - 2 2`
- Diagnosis: `existing_provider_can_convert_if_family_role_selects_it`
- Best forced provider: `krk.drive_to_edge`
- Candidate: `cand.krk.box_shrink.family_ff6652c8832c.drive_to_edge_adapter.v1`
- Candidate status: `sandbox_ready_if_terms_separate`

### stage7.post_box.family_0afbf11aa123

- State: `state.0afbf11aa123`
- FEN: `8/8/8/8/4K3/4R3/3k4/8 w - - 2 2`
- Diagnosis: `unresolved_by_existing_forced_providers_at_h80`
- Best forced provider: `None`
- Candidate: `cand.krk.box_shrink.family_0afbf11aa123.unresolved_continuation.v1`
- Candidate status: `needs_legal_first_or_longer_horizon_sweep`

### stage7.post_box.family_38aed2f35911

- State: `state.38aed2f35911`
- FEN: `8/8/8/R7/4k3/8/8/3K4 w - - 2 2`
- Diagnosis: `unresolved_by_existing_forced_providers_at_h80`
- Best forced provider: `None`
- Candidate: `cand.krk.box_shrink.family_38aed2f35911.unresolved_continuation.v1`
- Candidate status: `needs_legal_first_or_longer_horizon_sweep`

### stage7.post_box.family_ac0b7ed500ea

- State: `state.ac0b7ed500ea`
- FEN: `8/8/8/4k3/R7/8/3K4/8 w - - 2 2`
- Diagnosis: `existing_provider_can_convert_if_family_role_selects_it`
- Best forced provider: `krk.fence_established`
- Candidate: `cand.krk.box_shrink.family_ac0b7ed500ea.fence_established_adapter.v1`
- Candidate status: `sandbox_ready_if_terms_separate`

## Adapter Status

- Candidate: `cand.krk.box_shrink_to_drive_repair.visible_provider_support.v1`
- Status: `overbroad_adapter_candidate`
- Adapter fires: `12`
- Next action: `do_not_run_m3_on_current_broad_adapter`

## Recommended Next Actions

- `compile_no_broad_stage7_repair`
- `derive_narrow_family_terms_for_forced-success_families`
- `run_targeted_legal_first_longer_horizon_for_unresolved_families`
- `do_not_train_stage8`
- `do_not_promote_stage7`
- `do_not_run_m3_on_current_broad_drive_adapter`
