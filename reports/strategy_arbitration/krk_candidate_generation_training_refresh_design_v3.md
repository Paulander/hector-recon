# KRK Candidate-Generation Training Refresh Design v3

Define an offline candidate-generation refresh benchmark that learns which provider families should be visible as candidates in protected Stage 4/5/6 contexts. This is candidate generation only, not ownership selection.

## Decision

- status: `candidate_generation_training_refresh_v3_design_ready`
- implementation_allowed_by_this_artifact: `False`
- selector_allowed: `False`
- recommended_next_step: `implement_offline_candidate_generation_training_refresh_v3_benchmark`

## Training Target

- positive: `protected positive forced-provider capacity rows`
- negative: `protected negative forced-provider capacity rows`
- objective: `candidate_generation_recall_with_negative_capacity_suppression`
- not_objective: `runtime_ownership_or_move_selection`

## Feature Groups

- `source_stage`
- `active_landmark_label`
- `candidate_strategy_family`
- `provider_id`
- `trace_feature_source`
- `stage_family_context`
- `visible_source_terms`
- `selected_provider_before_observation_context`

## Evaluation Protocol

- protected_stages: `['stage4', 'stage5', 'stage6']`
- heldout_challenge_stages: `['stage7']`
- splits: `['leave_stage_out', 'leave_family_out', 'leave_state_out_if_enough_rows']`
- metrics: `['positive_capacity_recall', 'negative_capacity_suppression', 'precision', 'stage_family_coverage', 'stage7_heldout_candidate_visibility_only']`

## Forbidden Uses

- `runtime_selector`
- `score_changes`
- `provider_routing`
- `provider_suppression`
- `guardrail_campaign`
- `stage7_promotion`
- `stage8_training`
