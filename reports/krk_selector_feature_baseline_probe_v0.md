# KRK Selector Feature Baseline Probe v0

This non-causal probe checks whether trace-only observation features improve selector target prediction.

## Summary

- Rows: `42`
- Label counts: `{'negative': 28, 'positive': 14}`
- Best baseline: `{'name': 'provider_prior_loo', 'accuracy': 0.8333333333333334}`
- Feature improved over provider prior: `False`

## Baselines

- `majority_label` accuracy=`0.6666666666666666` correct=`28` total=`42`
- `provider_prior_loo` accuracy=`0.8333333333333334` correct=`35` total=`42`
- `stage_prior_loo` accuracy=`0.5952380952380952` correct=`25` total=`42`
- `provider_stage_prior_loo` accuracy=`0.7619047619047619` correct=`32` total=`42`
- `provider_selected_match_loo` accuracy=`0.8333333333333334` correct=`35` total=`42`
- `best_source_term_loo` accuracy=`0.6666666666666666` correct=`28` total=`42`
- `provider_shared_term_backoff_loo` accuracy=`0.8333333333333334` correct=`35` total=`42`

## Term Summary

- `box_area_large` total=`5` positive_rate=`1.0`
- `mate_basin_available` total=`3` positive_rate=`1.0`
- `mate_in_one_available` total=`3` positive_rate=`1.0`
- `fence_needs_repair` total=`29` positive_rate=`0.10344827586206896`
- `wrong_tempo_detected` total=`29` positive_rate=`0.10344827586206896`
- `white_king_can_improve_support` total=`31` positive_rate=`0.12903225806451613`
- `cut_stable` total=`13` positive_rate=`0.8461538461538461`
- `fence_already_satisfied` total=`13` positive_rate=`0.8461538461538461`
- `fence_stable` total=`13` positive_rate=`0.8461538461538461`
- `white_king_support_available` total=`13` positive_rate=`0.8461538461538461`
- `edge_trap_close_geometry` total=`10` positive_rate=`0.8`
- `king_approach_after_fence_available` total=`37` positive_rate=`0.24324324324324326`

## Decision

Status: `provider_prior_remains_best_non_causal_baseline`
Sandbox ready: `False`
Runtime arbiter allowed: `False`
Recommended next step: `architecture_review_before_selector_sandbox_or_more_control_labels`
