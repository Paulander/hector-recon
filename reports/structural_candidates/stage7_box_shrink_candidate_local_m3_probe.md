# Candidate-Local M3 Warmup Probe

Schema: `candidate_local_m3_warmup_probe.v1`
Causal status: `non_causal`
Target role: `krk.box_shrink_to_drive_repair`
Target provider: `krk.drive_to_edge`
Probe result: `blocked_no_candidate_provider_eligibility`
Recommended next action: `compile_visible_role_provider_support_or_owner_eligibility_before_m3`

## Counts

- `role_contract_met`: 5
- `role_met_provider_not_selected`: 5
- `role_met_selected:krk.stage0_basin`: 5
- `eligible_edge_count`: 21
- `candidate_edge_eligibility_events`: 0

## Diagnostic Labels

- `role_contract_met_provider_not_selected`
- `candidate_edges_not_firing`
- `topology_present_but_not_eligible_for_weight_update`

## Safety

- `m4_consolidation_enabled`: `False`
- `protected_provider_mutation_enabled`: `False`
- `topology_mutation_enabled`: `False`
- hard block: `do_not_train_stage8`
- hard block: `do_not_promote_stage7`
- hard block: `do_not_enable_stage7_repair_by_default`
- hard block: `do_not_make_packets_stats_or_candidates_causal`
