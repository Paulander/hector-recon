# Candidate-Local M3 Warmup Plan

Schema: `candidate_local_m3_warmup_plan.v1`
Causal status: `non_causal`
Target role: `krk.box_shrink_to_drive_repair`
Target providers: `krk.drive_to_edge`
Governor decision: `needs_more_weight_training`
Governor phase: `phase_3_bounded_plasticity_warmup`
Eligible M3 edges: `21`

## Safety

- `do_not_train_stage8`
- `do_not_promote_stage7`
- `do_not_enable_stage7_repair_by_default`
- `do_not_make_packets_stats_or_candidates_causal`
- M4 consolidation enabled: `False`
- Topology mutation enabled: `False`
- Protected provider mutation enabled: `False`

## Eligible Edge Reasons

- `candidate_provider_internal`: 12
- `candidate_provider_leg_selection`: 3
- `candidate_provider_triplet_temporal`: 6

## Excluded Edge Counts

- `non_trainable_link_type`: 656
- `not_m3_update_enabled`: 18
- `outside_candidate_provider_subtree`: 379
- `protected_frozen_provider`: 238
