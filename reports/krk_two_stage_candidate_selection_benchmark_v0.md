# KRK Two-Stage Candidate / Selection Benchmark v0

This non-causal benchmark separates candidate-generation recall from selector suppression.

## Candidate Generation

- `current_runtime_proposal_frames`: `{'positive_capacity_recall_count': 0, 'positive_capacity_total': 11, 'positive_capacity_recall_rate': 0.0, 'negative_capacity_inclusion_count': 0, 'negative_capacity_total': 5, 'negative_capacity_inclusion_rate': 0.0}`
- `validated_provider_candidate_set_expansion`: `{'positive_capacity_recall_count': 11, 'positive_capacity_total': 11, 'positive_capacity_recall_rate': 1.0, 'negative_capacity_inclusion_count': 5, 'negative_capacity_total': 5, 'negative_capacity_inclusion_rate': 1.0}`

## Strategy Selection

- `source_probe_status`: `state_local_contrast_signal_not_ready`
- `training_row_count`: `12`
- `training_state_count`: `8`
- `training_label_counts`: `{'negative': 3, 'positive': 9}`
- `stage7_eval_row_count`: `8`
- `stage7_training_leakage`: `False`
- `best_objective`: `stage_family_rank_score`
- `best_accuracy`: `0.75`
- `best_positive_precision`: `0.75`
- `best_positive_recall`: `1.0`
- `best_negative_suppression`: `0.0`
- `selector_ready`: `False`

## Interpretation

- `candidate_generation`: `Validated-provider expansion fixes recall for known protected positive-capacity providers.`
- `selection`: `Existing selector evidence is not ready because negative suppression remains poor/underpowered.`
- `combined`: `Runtime work remains blocked until candidate generation and selection both pass non-causal benchmarks.`

## Decision

- `status`: `candidate_generation_recall_improves_selection_not_ready`
- `recommended_next_step`: `improve_selector_label_balance_or_candidate_scoring_non_causal`
- `runtime_work_allowed`: `False`
- `candidate_generator_runtime_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
