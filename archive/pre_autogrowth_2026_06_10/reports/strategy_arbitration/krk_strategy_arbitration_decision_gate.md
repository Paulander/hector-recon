# KRK Strategy Arbitration Decision Gate v0

This decision gate is non-causal. It recommends the next diagnostic/design class only.

## Decision

- Selected status: `missing_feature_first`
- Next class: `non_causal_terminal_affordance_candidate_audit`
- Next step: Propose non-causal terminal/affordance candidates and a separability audit; do not implement them causally.
- Stop after next class: `True`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Evidence

- Dataset v0 has 33 records and 87 proposal frames.
- Probe v0 selected missing_feature_first.
- Raw global hit rate: 0.9285714285714286.
- Provider-local rank1 coverage: 1.0.
- Visible heuristic hit rate: 0.07142857142857142.
- Challenge manifest has 6 held-out Stage 7 families.

## Missing Evidence

- More successful Stage 5/6/7 provider-labeled records with terminal-space context.
- A separability audit for candidate terminal/affordance terms before any sandbox.
- Better visible heuristic features for edge-net, king-support, phase-boundary, and box-shrink exit conditions.

## Forbidden Next Steps

- train_stage8
- promote_stage7
- implement_runtime_arbiter
- add_stage7_runtime_repair
- add_support_adapter
- add_score_bonus_or_provider_penalty
- use_runtime_dtm_or_tablebase
- mutate_topology_during_gameplay
