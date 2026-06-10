# KRK Hard-Negative Selector Target Training Semantics Review v0

This review authorizes offline benchmarking only. It does not authorize runtime selector training.

## Summary

- `target_row_count`: `16`
- `hard_negative_capacity_count`: `5`
- `positive_capacity_context_count`: `11`
- `stage7_row_count`: `0`
- `current_training_row_count`: `0`

## Approved Non-Causal Uses

- `offline_hard_negative_selector_benchmark`
- `feature_ablation_for_negative_suppression`
- `candidate_generator_precision_review`

## Blocked Uses

- `runtime_selector_training`
- `runtime_provider_suppression`
- `runtime_provider_boost`
- `topology_mutation`
- `Stage7 promotion`
- `Stage8 training`

## Training Semantics

- `hard_negative_capacity`: May be used as an offline benchmark negative for candidate scoring. It means forced first-move ownership failed h40, not that the provider is globally bad or should be suppressed at runtime.
- `positive_capacity_context`: May be used as offline positive-capacity context. It is still not selected-playout success and should not be mixed with runtime proposal labels without channel separation.

## Requirements For Future Training

- `explicit objective separates capacity, runtime proposal, and selected-playout channels`
- `leave-state-out negative suppression improves above baseline`
- `hard-negative false positives are inspected`
- `Stage 7 remains held out`
- `guardrail suite passes before any causal sandbox`

## Decision

- `status`: `hard_negative_targets_approved_for_offline_benchmark_only`
- `recommended_next_step`: `run_hard_negative_selector_feature_ablation_v0`
- `offline_benchmark_allowed`: `True`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
