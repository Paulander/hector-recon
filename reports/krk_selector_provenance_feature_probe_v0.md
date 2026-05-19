# KRK Selector Provenance Feature Probe v0

This non-causal probe tests whether explicit provider provenance/maturity fields explain the provider-prior selector signal.

## Summary

- Rows: `42`
- Label counts: `{'negative': 28, 'positive': 14}`
- Best baseline: `{'name': 'provider_id_loo', 'accuracy': 0.8333333333333334}`
- Decision: `provenance_features_explain_provider_prior_non_causal`
- Runtime arbiter allowed: `False`
- Selector sandbox ready: `False`

## Baselines

- `provider_id_loo` accuracy=`0.8333333333333334` correct=`35` total=`42`
- `provider_family_loo` accuracy=`0.8333333333333334` correct=`35` total=`42`
- `provider_maturity_loo` accuracy=`0.8333333333333334` correct=`35` total=`42`
- `provider_source_stage_loo` accuracy=`0.8333333333333334` correct=`35` total=`42`
- `validated_role_loo` accuracy=`0.8333333333333334` correct=`35` total=`42`
- `protected_overlay_loo` accuracy=`0.6666666666666666` correct=`28` total=`42`
- `family_maturity_loo` accuracy=`0.8333333333333334` correct=`35` total=`42`

## Group Summaries

### provider_family
- `edge_trap` total=`27` positive_rate=`0.1111111111111111` labels=`{'negative': 24, 'positive': 3}`
- `stage0_basin` total=`15` positive_rate=`0.7333333333333333` labels=`{'negative': 4, 'positive': 11}`

### provider_maturity
- `foundation_frozen` total=`15` positive_rate=`0.7333333333333333` labels=`{'negative': 4, 'positive': 11}`
- `validated_low_plasticity` total=`27` positive_rate=`0.1111111111111111` labels=`{'negative': 24, 'positive': 3}`

### provider_source_stage
- `stage0` total=`15` positive_rate=`0.7333333333333333` labels=`{'negative': 4, 'positive': 11}`
- `stage5` total=`27` positive_rate=`0.1111111111111111` labels=`{'negative': 24, 'positive': 3}`

## Interpretation

- Provider provenance/maturity features can reproduce the current provider-prior signal when they distinguish foundation-frozen stage0_basin from validated edge-trap providers.
- This remains non-causal because the dataset is small and selected-playout labels can encode horizon/control artifacts.
- The result supports explicit provenance fields in evidence records, not a runtime provider prior.

## Blocked

- `runtime_arbiter`
- `selector_sandbox`
- `raw_provider_id_runtime_prior`
- `provider_support_adapter`
- `score_bonus_or_penalty`
- `stage7_repair`
- `stage7_promotion`
- `stage8_training`
