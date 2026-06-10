# KRK Two-Stage Candidate / Selection Review v0

This architecture review separates candidate generation from strategy selection. It is non-causal and does not implement runtime behavior.

## Current Evidence

- `candidate_generation_recall_gap_confirmed`: `True`
- `positive_capacity_recovered_by_validated_provider_set`: `11`
- `negative_capacity_also_included`: `5`
- `direct_selector_training_allowed`: `False`
- `runtime_work_allowed`: `False`

## Two-Stage Architecture

- `stage_1_candidate_generation` purpose: Represent plausible validated providers/strategies so the selector can evaluate them.
- `stage_1_candidate_generation` evidence target: high recall for protected positive-capacity providers
- `stage_1_candidate_generation` must not: `['select moves', 'boost providers', 'suppress providers', 'mutate topology', 'use runtime DTM/tablebase']`
- `stage_2_strategy_selection` purpose: Choose among represented providers using separated label semantics.
- `stage_2_strategy_selection` evidence target: suppress negative-capacity and selected-failure candidates while preserving positive-capacity/selected-success candidates
- `stage_2_strategy_selection` must not: `['train on forced-provider capacity as direct runtime-positive labels', 'mix Stage 7 held-out residuals into protected training', 'ignore guardrail preservation']`

## Minimum Next Benchmark Requirements

- `candidate-generator recall for protected positive-capacity providers`
- `selector suppression of protected negative-capacity providers`
- `separate selected-playout, forced-capacity, and runtime-proposal label channels`
- `leave-state-out evaluation over protected Stage 4/5/6 rows`
- `Stage 7 held-out challenge evaluation only`
- `no runtime behavior changes`

## Blocked Paths

- `runtime_selector`
- `runtime_candidate_generator`
- `direct Stage 7 repair`
- `Stage 7 promotion`
- `Stage 8 training`
- `runtime DTM/tablebase`
- `gameplay topology mutation`

## Decision

- `status`: `two_stage_non_causal_benchmark_design_needed`
- `recommended_next_step`: `plan_two_stage_candidate_selection_benchmark_v0`
- `runtime_work_allowed`: `False`
- `candidate_generator_runtime_allowed`: `False`
- `selector_training_allowed`: `False`
- `stage7_promotion_allowed`: `False`
- `stage8_training_allowed`: `False`
