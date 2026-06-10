# KRK Selector Balanced Label Probe v1

This non-causal probe checks simple selector signals on the replay-free balanced label dataset.

## Summary

- Rows: `18`
- Label counts: `{'negative': 9, 'positive': 9}`
- Best baseline: `{'name': 'provider_id_loo', 'accuracy': 0.7777777777777778}`
- Decision: `balanced_labels_support_non_causal_selector_signal`
- Runtime arbiter allowed: `False`
- Selector sandbox ready: `False`

## Baselines

- `provider_id_loo` accuracy=`0.7777777777777778` correct=`14` total=`18`
- `provider_family_loo` accuracy=`0.7777777777777778` correct=`14` total=`18`
- `provider_maturity_loo` accuracy=`0.7777777777777778` correct=`14` total=`18`
- `active_landmark_loo` accuracy=`0.16666666666666666` correct=`3` total=`18`
- `source_stage_loo` accuracy=`0.16666666666666666` correct=`3` total=`18`
- `provider_family_landmark_loo` accuracy=`0.6111111111111112` correct=`11` total=`18`
- `provider_maturity_landmark_loo` accuracy=`0.6111111111111112` correct=`11` total=`18`

## Interpretation

- Balanced replay-free labels are suitable for a small non-causal signal check.
- A high score here is not sandbox evidence because the dataset is small and constructed from existing controls.
- Runtime arbiter work remains blocked pending architecture review and guardrail criteria.
