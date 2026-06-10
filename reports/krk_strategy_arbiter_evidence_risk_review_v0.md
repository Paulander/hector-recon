# KRK Strategy Arbiter Evidence Risk Review v0

This is a replay-free, non-causal review of the two pre-sandbox risks: mixed provider-label semantics and max-only frame classification.

## Summary

- `benchmark_frame_count`: `28`
- `provider_mate_frame_count`: `14`
- `max_only_frame_count`: `14`
- `label_semantic_counts`: `{'forced_provider_outcome': 24, 'selected_provider_playout': 24, 'same_move_unselected_provider_playout': 18}`
- `provider_mate_frames_by_semantic`: `{'forced_provider_outcome': 2, 'selected_provider_playout': 12, 'same_move_unselected_provider_playout': 1}`
- `max_only_classification_counts`: `{'forced_existing_provider_capacity_or_horizon_gap': 2, 'selected_playout_guardrail_or_horizon_caveat': 12}`

## Max-Only Frames

- `cp.krk.state.0afbf11aa123` stage=`stage7` class=`forced_existing_provider_capacity_or_horizon_gap` semantics=`{'forced_provider_outcome': 6}`
- `cp.krk.state.38aed2f35911` stage=`stage7` class=`forced_existing_provider_capacity_or_horizon_gap` semantics=`{'forced_provider_outcome': 6}`
- `cp.krk.state.02feb8593cc6` stage=`stage5` class=`selected_playout_guardrail_or_horizon_caveat` semantics=`{'selected_provider_playout': 1, 'same_move_unselected_provider_playout': 2}`
- `cp.krk.state.326222aefdf1` stage=`stage5` class=`selected_playout_guardrail_or_horizon_caveat` semantics=`{'selected_provider_playout': 1, 'same_move_unselected_provider_playout': 2}`
- `cp.krk.state.3dca34326fca` stage=`stage5` class=`selected_playout_guardrail_or_horizon_caveat` semantics=`{'selected_provider_playout': 1}`
- `cp.krk.state.02feb8593cc6` stage=`stage5` class=`selected_playout_guardrail_or_horizon_caveat` semantics=`{'selected_provider_playout': 1, 'same_move_unselected_provider_playout': 2}`
- `cp.krk.state.699f0003a511` stage=`stage6` class=`selected_playout_guardrail_or_horizon_caveat` semantics=`{'selected_provider_playout': 1, 'same_move_unselected_provider_playout': 2}`
- `cp.krk.state.699f0003a511` stage=`stage6` class=`selected_playout_guardrail_or_horizon_caveat` semantics=`{'selected_provider_playout': 1, 'same_move_unselected_provider_playout': 2}`
- `cp.krk.state.699f0003a511` stage=`stage6` class=`selected_playout_guardrail_or_horizon_caveat` semantics=`{'selected_provider_playout': 1, 'same_move_unselected_provider_playout': 2}`
- `cp.krk.state.699f0003a511` stage=`stage6` class=`selected_playout_guardrail_or_horizon_caveat` semantics=`{'selected_provider_playout': 1, 'same_move_unselected_provider_playout': 2}`
- `cp.krk.state.699f0003a511` stage=`stage6` class=`selected_playout_guardrail_or_horizon_caveat` semantics=`{'selected_provider_playout': 1, 'same_move_unselected_provider_playout': 2}`
- `cp.krk.state.256a3da30f0f` stage=`stage4` class=`selected_playout_guardrail_or_horizon_caveat` semantics=`{'selected_provider_playout': 1}`

## Decision

- Status: `runtime_sandbox_blocked_pending_semantics_review`
- Runtime sandbox allowed: `False`
- Interpretation: Provider labels are useful for offline design, but selected-playout, same-move unselected-provider, and forced-provider semantics are mixed. A runtime sandbox should not be implemented until the arbiter evaluation separates those semantics.
- Recommended next step: `stratified_non_causal_arbiter_evaluation_v2`
