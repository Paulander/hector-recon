# KRK Selector Feature Dataset v0

This replay-free dataset joins explicit selector targets with trace-only observation features.

## Summary

- Rows: `63`
- Training rows: `42`
- Rows with observation: `60`
- Stage counts: `{'stage4': 6, 'stage5': 22, 'stage6': 26, 'stage7': 9}`
- Target kind counts: `{'forced_provider_conversion': 12, 'held_out_challenge': 9, 'selected_playout_success': 42}`
- Label counts: `{'negative': 31, 'none': 9, 'positive': 23}`
- Stage7 training rows: `0`

## Decision

Status: `selector_feature_dataset_built`
Runtime arbiter allowed: `False`
Sandbox ready: `False`
Recommended next step: `probe_selector_feature_baselines_non_causal`
