# KRK Strategy Arbitration Probe v0

This probe is non-causal. It compares arbitration baselines using only labels already present in dataset v0.

## Decision

- Status: `missing_feature_first`
- Next step: Propose non-causal terminal/affordance candidates and a separability audit.
- Runtime behavior changed: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Baseline Metrics

- Raw global score hit rate: `0.929` over `14` labeled records
- Provider-local rank1 coverage: `1.000`
- Normalized provider score hit rate: `0.929`
- Visible heuristic hit rate: `0.071`

## Context Summaries

- Box relevance by edge bucket: `{'central_or_midboard|high': 7, 'at_edge|low': 25, 'near_edge|medium': 1}`
- Stage 7 phase context counts: `{'result=None|edge=central_or_midboard|box=high': 4, 'result=None|edge=at_edge|box=low': 1, 'result=max_plies|edge=near_edge|box=medium': 1, 'result=max_plies|edge=central_or_midboard|box=high': 3}`
- Stage 7 raw owner by result counts: `{'None:krk.stage0_basin': 3, 'max_plies:krk.drive_to_edge': 4}`

## Answers

- raw_provider_score_incomparability_suspected: `True`
- provider_local_rank_helps: `False`
- box_area_relevance_correlates_with_edge_distance: `True`
- stage7_failures_cluster_by_phase_boundary: `True`
- missing_terms_obvious: `True`

## Forbidden Runtime Work

- train_stage8
- promote_stage7
- implement_runtime_arbiter
- add_stage7_repair
- use_runtime_dtm_or_tablebase
- mutate_topology_during_gameplay
