# KRK State-Local Paired Ownership Probe v1

Non-causal comparison of safer paired-ownership models.

## Summary

- `row_count`: `32`
- `state_count`: `13`
- `prefer_capacity_count`: `7`
- `preserve_selected_count`: `25`
- `safe_preservation_pair_count`: `23`
- `strong_conflict_pair_count`: `9`
- `stage7_row_count`: `0`
- `threshold_passing_model_count`: `2`
- `runtime_feature_passing_model_count`: `0`

## Best Result

- `objective`: `safe_preservation_gated_model`
- `model_id`: `safe_preservation_gated_model`
- `model_kind`: `semantic_rule`
- `runtime_feature_eligible`: `False`
- `notes`: `Uses offline owner_a/owner_b outcome semantics; validates objective semantics but is not directly runtime-feature eligible.`
- `row_count`: `32`
- `true_positive`: `7`
- `false_positive`: `0`
- `true_negative`: `25`
- `false_negative`: `0`
- `accuracy`: `1.0`
- `prefer_capacity_precision`: `1.0`
- `prefer_capacity_recall`: `1.0`
- `selected_preservation_recall`: `1.0`
- `strong_conflict_accuracy`: `1.0`
- `safe_preservation_recall`: `1.0`
- `safe_preservation_false_positive_count`: `0`
- `prefer_capacity_false_negative_count`: `0`

## Threshold-Passing Models

- `safe_preservation_gated_model`: prefer_capacity_recall=`1.0`, selected_preservation_recall=`1.0`, safe_preservation_recall=`1.0`, runtime_feature_eligible=`False`
- `conflict_only_model`: prefer_capacity_recall=`1.0`, selected_preservation_recall=`1.0`, safe_preservation_recall=`1.0`, runtime_feature_eligible=`False`

## Decision

- `status`: `semantic_gate_review_ready_runtime_feature_translation_needed`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `recommended_next_step`: `prepare_runtime_review_packet_for_explicit_approval`
