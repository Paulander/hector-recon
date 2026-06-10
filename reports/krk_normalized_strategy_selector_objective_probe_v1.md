# KRK Normalized Strategy Selector Objective Probe v1

This offline probe uses existing labels only. It does not train or enable a runtime selector.

## Dataset Summary

### `balanced`

- `row_count`: `18`
- `label_counts`: `{'positive': 9, 'negative': 9}`
- `provider_family_counts`: `{'stage0_basin': 9, 'edge_trap': 9}`
- `target_kind_counts`: `{'guardrail_safe_selected_playout': 8, 'same_move_provider_compatibility_or_forced_alternative': 1, 'selected_playout_success': 9}`
- `stage7_training_rows`: `0`
- `heldout_stage7_rows`: `0`

### `provenance_labeled`

- `row_count`: `54`
- `label_counts`: `{'positive': 23, 'negative': 31}`
- `provider_family_counts`: `{'stage0_basin': 20, 'edge_trap': 34}`
- `target_kind_counts`: `{'selected_playout_success': 42, 'forced_provider_conversion': 12}`
- `stage7_training_rows`: `0`
- `heldout_stage7_rows`: `0`

### `heldout_stage7`

- `row_count`: `9`
- `label_counts`: `{'None': 9}`
- `provider_family_counts`: `{'None': 9}`
- `target_kind_counts`: `{'held_out_challenge': 9}`
- `stage7_training_rows`: `0`
- `heldout_stage7_rows`: `9`

## Required Field Gaps

- `balanced` missing rows: `{'provider_local_rank': 18, 'normalized_score': 18}`
- `provenance_labeled` missing rows: `{'provider_local_rank': 0, 'normalized_score': 0}`

## Best Results

- `balanced`: `{'objective': 'family_maturity_target_kind', 'accuracy': 0.8888888888888888}`
- `provenance`: `{'objective': 'family_rank_score_bucket', 'accuracy': 0.8888888888888888}`

## Result Tables

### `balanced_leave_one_out`

- `provider_family` accuracy=`0.7777777777777778` precision=`0.7777777777777778` recall=`0.7777777777777778` negative_suppression=`0.7777777777777778`
- `provider_maturity` accuracy=`0.7777777777777778` precision=`0.7777777777777778` recall=`0.7777777777777778` negative_suppression=`0.7777777777777778`
- `family_maturity` accuracy=`0.7777777777777778` precision=`0.7777777777777778` recall=`0.7777777777777778` negative_suppression=`0.7777777777777778`
- `family_maturity_target_kind` accuracy=`0.8888888888888888` precision=`1.0` recall=`0.7777777777777778` negative_suppression=`1.0`
- `source_stage_family` accuracy=`0.7777777777777778` precision=`0.7777777777777778` recall=`0.7777777777777778` negative_suppression=`0.7777777777777778`
- `provider_rank_bucket` accuracy=`0.0` precision=`0.0` recall=`0.0` negative_suppression=`0.0`
- `family_rank_bucket` accuracy=`0.7777777777777778` precision=`0.7777777777777778` recall=`0.7777777777777778` negative_suppression=`0.7777777777777778`
- `family_rank_score_bucket` accuracy=`0.7777777777777778` precision=`0.7777777777777778` recall=`0.7777777777777778` negative_suppression=`0.7777777777777778`
- `family_maturity_rank_target_kind` accuracy=`0.8888888888888888` precision=`1.0` recall=`0.7777777777777778` negative_suppression=`1.0`

### `provenance_leave_one_out`

- `provider_family` accuracy=`0.7962962962962963` precision=`0.8` recall=`0.6956521739130435` negative_suppression=`0.8709677419354839`
- `provider_maturity` accuracy=`0.7962962962962963` precision=`0.8` recall=`0.6956521739130435` negative_suppression=`0.8709677419354839`
- `family_maturity` accuracy=`0.7962962962962963` precision=`0.8` recall=`0.6956521739130435` negative_suppression=`0.8709677419354839`
- `family_maturity_target_kind` accuracy=`0.8148148148148148` precision=`0.7407407407407407` recall=`0.8695652173913043` negative_suppression=`0.7741935483870968`
- `source_stage_family` accuracy=`0.7407407407407407` precision=`0.7647058823529411` recall=`0.5652173913043478` negative_suppression=`0.8709677419354839`
- `provider_rank_bucket` accuracy=`0.5740740740740741` precision=`None` recall=`0.0` negative_suppression=`1.0`
- `family_rank_bucket` accuracy=`0.7962962962962963` precision=`0.8` recall=`0.6956521739130435` negative_suppression=`0.8709677419354839`
- `family_rank_score_bucket` accuracy=`0.8888888888888888` precision=`0.84` recall=`0.9130434782608695` negative_suppression=`0.8709677419354839`
- `family_maturity_rank_target_kind` accuracy=`0.8148148148148148` precision=`0.7407407407407407` recall=`0.8695652173913043` negative_suppression=`0.7741935483870968`

## Interpretation

- Full normalized objective testable: `True`
- Stage 7 training leakage: `False`
- Finding: Existing provenance labels can test normalized rank/score proxies via target_provider_best_rank and target_provider_best_raw_score, but the dataset is still too small and Stage7 remains held out.

## Decision

- Status: `normalized_objective_probe_underpowered_fields_available`
- Recommended next step: `review_normalized_probe_before_runtime_tests`
- Runtime test allowed next: `False`
- Stage 7 promotion allowed: `False`
- Stage 8 training allowed: `False`
