# KRK Provider Identity / Maturity Review v0

This non-causal review explains why provider identity is currently the strongest selector baseline and why that does not authorize runtime arbitration.

## Summary

- Rows: `42` selected-playout training examples
- Provider-prior LOO accuracy: `0.8333333333333334`
- Decision: `provider_identity_signal_requires_provenance_decomposition`
- Runtime arbiter allowed: `False`
- Selector sandbox ready: `False`

## Provider Outcomes

- `krk.edge_trap_close` count=`9` positive_rate=`0.1111111111111111` labels=`{'negative': 8, 'positive': 1}` maturity=`validated_low_plasticity`
- `krk.edge_trap_enemy_between` count=`9` positive_rate=`0.1111111111111111` labels=`{'negative': 8, 'positive': 1}` maturity=`validated_low_plasticity`
- `krk.edge_trap_wrong_tempo` count=`9` positive_rate=`0.1111111111111111` labels=`{'negative': 8, 'positive': 1}` maturity=`validated_low_plasticity`
- `krk.stage0_basin` count=`15` positive_rate=`0.7333333333333333` labels=`{'negative': 4, 'positive': 11}` maturity=`foundation_frozen`

## Interpretation

- Provider identity currently beats trace-only observation terms on selected-playout labels.
- The signal is mostly a maturity/provenance prior: stage0_basin selected-playout controls are often positive while edge-trap variants are often negative in this dataset.
- Raw provider id can encode dataset and label bias, so it should be decomposed into explicit provenance, maturity, scope, and validation-status features before any future sandbox.
- Stage7 rows remain held out and should not be used to tune a selector.

## Required Future Features

- `provider_maturity`
- `provider_version`
- `source_stage`
- `validated_profile`
- `frozen_provider`
- `overlay_provider`
- `guardrail_status`
- `plasticity_scope`
- `promotion_status`
- `protected_provider`

## Blocked

- `runtime_arbiter`
- `selector_sandbox`
- `raw_provider_id_runtime_prior`
- `provider_support_adapter`
- `score_bonus_or_penalty`
- `stage7_repair`
- `stage7_promotion`
- `stage8_training`
- `runtime_dtm_or_tablebase`
- `gameplay_topology_mutation`

## Recommended Next Step

`add_provider_provenance_maturity_features_non_causal`

Decompose provider identity into explicit non-causal provenance/maturity features before considering more selector baselines or any sandbox design.
