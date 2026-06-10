# KRK Selector Target Dataset v0

This replay-free dataset maps existing labels into explicit selector target kinds.

## Summary

- Rows: `63`
- Training rows: `42`
- Target kind counts: `{'forced_provider_conversion': 12, 'held_out_challenge': 9, 'selected_playout_success': 42}`
- Label counts: `{'negative': 31, 'none': 9, 'positive': 23}`
- Split counts: `{'candidate_training_or_eval': 42, 'diagnostic_capacity_only': 12, 'held_out_challenge': 9}`
- Stage7 training rows: `0`

## Decision

Status: `selector_target_dataset_built`
Runtime arbiter allowed: `False`
Sandbox ready: `False`
Recommended next step: `probe_selector_targets_by_target_kind_replay_free`
