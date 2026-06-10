# KRK Selector Target Probe v0

This replay-free probe checks the explicit target-kind dataset.

## Summary

- Rows: `63`
- Training rows: `42`
- Training label counts: `{'negative': 28, 'positive': 14}`
- Training positive rate: `0.3333333333333333`
- Target-kind label counts: `{'forced_provider_conversion': {'negative': 3, 'positive': 9}, 'held_out_challenge': {'none': 9}, 'selected_playout_success': {'negative': 28, 'positive': 14}}`
- Held-out training rows: `0`

## Decision

Status: `target_dataset_ready_for_non_causal_baseline_probe`
Runtime arbiter allowed: `False`
Sandbox ready: `False`
Recommended next step: `run_non_causal_selector_baselines_by_target_kind`
