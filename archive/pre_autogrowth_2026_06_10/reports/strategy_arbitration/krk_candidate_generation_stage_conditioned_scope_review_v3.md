# KRK Candidate-Generation Stage-Conditioned Scope Review v3

Decide whether the candidate-generation refresh should be scoped by active protected stage/landmark instead of treated as a global cross-stage candidate policy.

## Decision

- status: `stage_conditioned_candidate_generation_scope_review_ready`
- selector_allowed: `False`
- runtime_candidate_generator_refresh_allowed: `False`
- recommended_next_step: `benchmark_stage_conditioned_candidate_generation_non_causal`

## Stage Scopes

### stage4

- positive_scope_families: `[]`
- risk_scope_families: `[]`
- mixed_scope_families: `['edge_trap', 'stage0_basin']`
- underpowered_families: `[]`

### stage5

- positive_scope_families: `['edge_trap', 'fence_established', 'stage0_basin']`
- risk_scope_families: `[]`
- mixed_scope_families: `[]`
- underpowered_families: `[]`

### stage6

- positive_scope_families: `['stage0_basin']`
- risk_scope_families: `['edge_trap']`
- mixed_scope_families: `[]`
- underpowered_families: `['drive_to_edge', 'fence_established']`

## Interpretation

- global_cross_stage_refresh_supported: `False`
- stage_conditioned_scope_supported_for_benchmark: `True`
- selector_supported: `False`
- runtime_refresh_supported: `False`
- capacity_labels_are_not_ownership_labels: `True`
- stage4_requires_companion_terms: `True`
- stage5_has_positive_capacity_scopes: `True`
- stage6_has_mixed_positive_and_risk_scopes: `True`

## Future Benchmark Requirements

- `benchmark stage-conditioned candidate emission separately from selection`
- `do not suppress risk-scope providers at runtime from capacity labels alone`
- `use mixed Stage 4 cells only with companion visible context terms`
- `keep Stage 7 held out as challenge evidence`
- `report candidate-generation recall and risk by protected stage`
- `require separate runtime review before any candidate-generator refresh`

## Forbidden Uses

- `runtime_selector`
- `provider_suppression`
- `score_delta`
- `direct_provider_routing`
- `stage7_training_rows`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
