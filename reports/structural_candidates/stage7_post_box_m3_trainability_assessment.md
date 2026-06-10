# Stage 7 Post-Box M3 Trainability Assessment

Schema: `stage7_post_box_m3_trainability_assessment.v1`
Causal status: `non_causal`
Target role: `krk.post_box_shrink_continuation`
Target provider: `krk.stage7_post_box_continuation`
Probe result: `scripted_provider_selected_but_not_trainable_for_move_policy`
Recommended next action: `train_or_compile_learned_candidate_provider_before_m3_warmup`

## Counts

- `candidate_provider_selected`: 6
- `candidate_provider_selected_failed`: 6
- `candidate_provider_selected_max_plies`: 6
- `visible_license_met`: 6
- `trainable_internal_edge_count`: 0
- `activation_edge_count`: 1

## Diagnostic Labels

- `visible_provider_ownership_available`
- `candidate_selected_but_all_selected_outcomes_failed`
- `no_candidate_internal_m3_edges`
- `expressive_but_untrained_or_capacity_limited`

## Safety

- `dtm_or_tablebase_runtime_enabled`: `False`
- `m4_consolidation_enabled`: `False`
- `protected_provider_mutation_enabled`: `False`
- `topology_mutation_enabled`: `False`
- hard block: `do_not_train_stage8`
- hard block: `do_not_promote_stage7`
- hard block: `do_not_enable_by_default`
- hard block: `do_not_make_candidates_causal`
