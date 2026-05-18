# Stage 7 Decision Gate

This decision gate recommends the next diagnostic/training class only. It does not implement a repair.

- Selected status: `proceed_to_training_objective_benchmark`
- Confidence: `medium_high`
- Primary hypothesis: `training_objective_model_expression`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Rationale

- The learnable post-box provider is selected in residual closed-loop replays but still max-plies.
- Trajectory fidelity remains weak after expanded DTM-margin supervision, while top-3 signal shows partial representation rather than complete absence.
- M3 trainability evidence indicates the previous scripted provider path lacked useful trainable internal move-policy edges.
- The first unified arbitration probe did not identify a better provider owner and did not support low box-area relevance as the main residual explanation.

## Minimum Next Step

Run an offline-only training-objective/model-expression benchmark on existing DTM trajectory states: compare current learned scoring against a ranked/pairwise preference objective and a visible-term baseline; report top-k fidelity and closed-loop drift diagnostics. Do not compile a runtime repair.

## Secondary Hypotheses

- continuation_capacity: plausible_secondary - Some states remain DTM-won/current-graph-failed and forced-provider unresolved.
- missing_feature_ontology: plausible_secondary - Candidate-move terms separate 0926 but do not yet explain all residual families.
- strategy_arbitration_phase_boundary: not_currently_dominant - First arbitration probe found no provider-local/rank1 advantage in sampled residuals.
- bad_standalone_curriculum_boundary: plausible_secondary - Stage 7 remains local-valid but composition-quarantined after multiple diagnostic paths.

## Blocked Next Steps

- train_stage8
- promote_stage7
- add_runtime_repair_or_causal_sandbox
- add_provider_bonus_or_penalty
- add_support_adapter
- use_runtime_dtm_or_tablebase
- mutate_topology_during_gameplay
