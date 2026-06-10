# Growth Governor Evaluation Plan

Schema: `growth_governor_evaluation_plan.v1`
Causal status: `non_causal`
Candidate count: `3`
Recommended next action: `bounded_m3_warmup_for_box_shrink_to_drive_repair`

## Governor Status Counts

- `growth_allowed`: 2
- `growth_blocked_by_guardrail`: 1

## Role Plans

### krk.box_shrink_to_drive_repair

- Decision: `needs_more_weight_training`
- Phase: `phase_3_bounded_plasticity_warmup`
- Next action: `run_candidate_local_m3_warmup_probe`
- Labels: `parameter_miscalibrated`, `topology_present_untrained`, `trainable_candidate`

### krk.box_shrink_post_reply_continuation

- Decision: `growth_blocked_by_cooldown`
- Phase: `phase_2_forced_oracle_probe`
- Next action: `run_targeted_legal_first_or_longer_horizon_sweep`
- Labels: `provider_capacity_missing`
- Blocked reasons: `existing_provider_capacity_inconclusive`

### krk.stage0_basin_after_box_shrink

- Decision: `growth_blocked_by_guardrail`
- Phase: `phase_1_frozen_weight_probe`
- Next action: `do_not_sandbox_as_default_continuation`
- Labels: `parameter_miscalibrated`, `topology_overbroad`
- Blocked reasons: `negative_counterfactual_evidence`

## Hard Blocks

- `do_not_train_stage8`
- `do_not_promote_stage7`
- `do_not_enable_stage7_repair_by_default`
- `do_not_make_packets_stats_or_candidates_causal`
