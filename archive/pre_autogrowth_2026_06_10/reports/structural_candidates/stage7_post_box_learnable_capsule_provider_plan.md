# Stage 7 Learnable Plan Capsule Provider

This is a non-causal sandbox protocol. It does not promote Stage 7 and does not enable runtime behavior by default.

## Provider

- provider_skill_id: `krk.post_box_shrink_continuation`
- provider_version: `stage7_post_box_continuation_overlay_v1`
- plan_capsule_id: `krk.post_box_shrink_continuation`
- causal_status: `sandbox_opt_in`
- default_enabled: `False`
- ttl_white_moves: `4`
- can_m3_update: `True`
- can_m4_consolidate: `False`

## Offline Supervision

- trajectory_seed: `reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.json`
- trajectory_count: `2`
- white_training_step_count: `25`
- runtime DTM/tablebase lookup is forbidden.

## Evaluation Phases

- Phase 0: `default_off_equivalence` - compiled topology with provider disabled must match baseline behavior
- Phase 1: `targeted_unresolved_family_replay` - replay DTM-seeded post-box families with sandbox enabled
- Phase 2: `stage7_smoke_10_h40` - 10-sample Stage 7 smoke at h40, thin traces
- Phase 3: `stage7_validation_25_h40` - 25-sample Stage 7 validation only if smoke improves or classifies cleanly
- Phase 4: `protected_guardrails` - Stage 6/5/4/1 and M1-M4 guardrails only after target improvement
- Phase 5: `stage7_100_sample_candidate_validation` - larger target validation only after guardrails hold

## Hard Constraints

- `do_not_train_stage8`
- `do_not_promote_stage7`
- `do_not_use_dtm_or_tablebase_at_runtime`
- `do_not_use_hidden_python_routing`
- `do_not_mutate_topology_during_gameplay`
- `do_not_make_handoff_stats_shadow_candidates_structural_candidates_growth_governor_or_plan_capsule_specs_causal`
- `keep_m1_m4_semantics_intact`
- `default_off_sandbox_only`
