# KRK Strategy-Sequence Dataset Design v3

Integrate the approved Stage 5/6 candidate-generation refresh observation frames into the strategy-sequence dataset as trace-only context, while preserving the split between candidate-generation capacity evidence and runtime ownership/selector labels.

## Decision

- status: `strategy_sequence_dataset_design_v3_ready`
- implementation_allowed_by_this_artifact: `False`
- selector_allowed: `False`
- recommended_next_step: `implement_strategy_sequence_dataset_v3_non_causal`

## New Trace Feature Sources

### stage5_6_candidate_generation_refresh

- source_artifact: `reports/strategy_arbitration/krk_strategy_sequence_stage5_6_refresh_trace_features_v0.json`
- allowed_use: `candidate_generation_context_and_proposal_coverage_analysis`
- forbidden_use: `selector_training_or_guardrail_trigger`
- trace_frame_count: 38
- stage7_trace_frame_count: 0
- selector_training_row_count: 0
- candidate_generation_training_row_count: 0

## Integration Rules

- `append trace-only rows without rewriting existing capacity labels`
- `set usable_for_selector_training_v3=false for all rows`
- `carry candidate-generation training rows only from protected positive capacity evidence`
- `preserve Stage 7 as held-out challenge evidence`
- `report runtime trace rows by source artifact`
- `block selector review unless explicit ownership labels exist`
