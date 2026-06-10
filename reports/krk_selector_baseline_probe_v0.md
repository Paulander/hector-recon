# KRK Selector Baseline Probe v0

This non-causal probe evaluates simple baselines for `selected_playout_success` labels.

## Summary

- Rows: `42`
- Label counts: `{'negative': 28, 'positive': 14}`
- Best baseline: `{'name': 'provider_prior_loo', 'accuracy': 0.8333333333333334}`

## Baselines

- `majority_label` accuracy=`0.6666666666666666` correct=`28` total=`42`
- `provider_prior_loo` accuracy=`0.8333333333333334` correct=`35` total=`42`
- `stage_prior_loo` accuracy=`0.5952380952380952` correct=`25` total=`42`
- `active_landmark_prior_loo` accuracy=`0.5952380952380952` correct=`25` total=`42`

## Decision

Status: `simple_selector_baseline_promising_non_causal`
Sandbox ready: `False`
Runtime arbiter allowed: `False`
Recommended next step: `join_selector_targets_with_observation_features_non_causal`
