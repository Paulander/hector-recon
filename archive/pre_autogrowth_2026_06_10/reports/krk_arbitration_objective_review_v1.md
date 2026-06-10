# KRK Arbitration Objective Review v1

This non-causal review decides what arbitration objective should replace broad additive support before any further runtime tests.

## Evidence Statuses

- `runtime_test_review`: `runtime_sandbox_safe_but_additive_support_not_ready_to_scale`
- `selector_objective_review`: `selector_objective_needs_stratified_label_expansion_before_sandbox`
- `balanced_selector_review`: `selector_signal_promising_sandbox_blocked_pending_readiness_criteria`
- `strategy_owner_contrast`: `strategy_owner_contrast_signal_present_selector_sandbox_blocked`
- `selector_readiness_v3`: `selector_readiness_v3_sandbox_design_review_allowed`

## Objective Assessment

### `broad_additive_support`

- Status: `reject_as_next_runtime_objective`
- Reason: Low support is observable but not effective for Stage7; high support can perturb protected one-ply ownership before safe Stage7 evidence exists.

### `raw_provider_id_prior`

- Status: `non_causal_evidence_only`
- Reason: Provider-prior signal can encode maturity/provenance and dataset bias; it does not prove guardrail-safe runtime ownership.

### `provider_provenance_maturity`

- Status: `promising_non_causal_feature_family`
- Reason: Provenance/maturity reproduced the provider-prior signal in prior probes.

### `selected_playout_labels`

- Status: `insufficient_alone`
- Reason: Current raw selected-provider observations are stage0-dominant.

### `forced_and_contrast_labels`

- Status: `useful_for_training_contrast_not_direct_runtime_policy`
- Reason: Conversion-positive provider diversity exists in protected contrast labels.

### `stage7_heldout_rows`

- Status: `challenge_only`
- Reason: Stage7 remains unresolved and must not become training evidence for a selector.

## Key Metrics

- `balanced_best_accuracy`: `0.7777777777777778`
- `contrast_training_positive_label_count`: `13`
- `contrast_training_negative_label_count`: `11`
- `contrast_positive_provider_families`: `['drive_to_edge', 'edge_trap', 'fence_established']`
- `contrast_heldout_provider_family_rates`: `{'drive_to_edge': {'negative': 3, 'positive': 1, 'positive_rate': 0.25, 'total': 4}, 'edge_trap': {'negative': 12, 'positive': 0, 'positive_rate': 0.0, 'total': 12}, 'fence_established': {'negative': 3, 'positive': 1, 'positive_rate': 0.25, 'total': 4}, 'stage0_basin': {'negative': 4, 'positive': 0, 'positive_rate': 0.0, 'total': 4}}`
- `readiness_v3_hard_blockers`: `[]`

## Next Objective Contract

- Name: `normalized_contrastive_strategy_selector_objective`
- Causal status: `non_causal_design_only`

Must use:
- `StrategyProposalFrame-compatible proposal rows`
- `provider family/provenance/maturity metadata`
- `provider-local rank or normalized within-provider score`
- `separate selected-playout, forced-provider, and same-move compatibility labels`
- `protected Stage4/5/6 controls`
- `Stage7 residuals as held-out challenge cases only`

Must not use:
- `raw global additive score scale as sole arbitration mechanism`
- `runtime DTM/tablebase`
- `state-hash exceptions`
- `hidden provider routing`
- `unpromoted InternalTerminalSpec/StructuralCandidate/PlanCapsuleSpec as causal inputs`

## Decision

- Status: `additive_support_objective_rejected_design_normalized_selector_objective`
- Recommended next step: `design_non_causal_normalized_strategy_selector_objective_v1`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`

## Blocked Next Steps

- `higher_additive_support_playout`
- `stage7_repair`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`
- `causal_internal_terminal`
