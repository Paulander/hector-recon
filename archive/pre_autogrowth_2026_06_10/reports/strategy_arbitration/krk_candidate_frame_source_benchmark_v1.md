# KRK Candidate Frame Source Benchmark v1

This non-causal benchmark compares populated StrategySequenceCandidateFrame source channels before any runtime work.

## Channel Summary

### internal_monitor_strategy_context

- frame_count: 13
- protected_count: 0
- stage7_challenge_count: 13
- candidate_generation_training_row_count: 0
- selector_training_row_count: 0
- capacity_label_counts: `{'none': 13}`
- outcome_counts: `{'max_plies': 9, 'unknown': 4}`

### progress_window_supported_move

- frame_count: 140
- protected_count: 0
- stage7_challenge_count: 140
- candidate_generation_training_row_count: 0
- selector_training_row_count: 0
- capacity_label_counts: `{'none': 140}`
- outcome_counts: `{'max_plies': 140}`

### protected_forced_capacity

- frame_count: 16
- protected_count: 16
- stage7_challenge_count: 0
- candidate_generation_training_row_count: 11
- selector_training_row_count: 0
- capacity_label_counts: `{'negative_capacity': 5, 'positive_capacity': 11}`
- outcome_counts: `{'unknown': 16}`

### visible_provider_proposal

- frame_count: 87
- protected_count: 42
- stage7_challenge_count: 45
- candidate_generation_training_row_count: 0
- selector_training_row_count: 42
- capacity_label_counts: `{'none': 87}`
- outcome_counts: `{'mate': 14, 'max_plies': 52, 'unknown': 21}`

## Decision

- status: `candidate_generation_sources_promising_selector_blocked`
- recommended_next_step: `design_non_causal_candidate_generation_source_benchmark_v2_or_review_runtime_scope`
- runtime_sandbox_allowed: `False`
