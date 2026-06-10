# KRK Selector Provenance Feature Dataset v0

This replay-free dataset decomposes provider identity into explicit non-causal provenance and maturity fields.

## Summary

- Rows: `63`
- Training rows: `42`
- Rows with provider provenance: `54`
- Stage7 training rows: `0`
- Label counts: `{'negative': 31, 'none': 9, 'positive': 23}`
- Provider maturity counts: `{'foundation_frozen': 20, 'unknown': 9, 'validated_low_plasticity': 34}`
- Provider family counts: `{'edge_trap': 34, 'stage0_basin': 20, 'unknown': 9}`

## Decision

Status: `selector_provenance_feature_dataset_built`
Runtime arbiter allowed: `False`
Sandbox ready: `False`
Recommended next step: `probe_selector_provenance_features_non_causal`
