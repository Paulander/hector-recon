# Stage 7 2cc Continuation Protocol

Schema: `stage7_2cc_continuation_protocol.v1`
Causal status: `non_causal`
Candidate: `cand.krk.box_shrink.family_2cc.post_box_continuation_overlay.v1`
Promotion status: `sandbox_training_protocol_ready`
Diagnosis: `multi_step_continuation_policy_gap_not_single_move_gap`

## Evaluation Phases

- Phase 0: `static_sanity`
- Phase 1: `frozen_weight_probe`
- Phase 2: `bounded_candidate_local_plasticity`
- Phase 3: `target_validation`
- Phase 4: `protected_guardrails`

## Boundaries

- `do_not_train_stage8`
- `do_not_promote_stage7`
- `do_not_make_structural_candidates_causal`
- `do_not_mutate_topology_during_gameplay`
- `do_not_use_hidden_python_router`
- `do_not_train_until_protocol_is_explicitly_invoked`

Next action: `run bounded sandbox training/evaluation only after explicit validation command`
