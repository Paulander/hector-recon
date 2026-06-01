# KRK Refined Selector Initial Owner Behavior Review Packet v0

## Decision

- status: `refined_selector_initial_owner_behavior_review_packet_ready`
- implementation_authorized_by_this_packet: `False`
- runtime_changes_allowed_by_this_packet: `False`
- selector_runtime_ready: `False`
- recommended_next_step: `human_review_before_any_default_off_behavior_sandbox_approval`

## Evidence

- preserve_on_failure_count: `0`
- switch_on_safe_owner_count: `0`
- abstain_missed_switch_count: `1`
- unsafe_if_causal_count: `0`
- stage7_training_row_count: `0`
- selector_training_row_count: `0`
- capacity_label_used_as_ownership_label_count: `0`
- runtime_behavior_changed: `False`
- continuation_recommendation_count: `0`

## Proposed Future Sandbox

- name: `default_off_initial_owner_selector_behavior_sandbox`
- implementation_status: `not_implemented`
- default_off_required: `True`
- initial_owner_only: `True`
- continuation_recommendations_allowed: `False`
- allowed_behavior_if_separately_approved: `bounded_switch_to_visible_alternative_only_when_recommendation_is_prefer_visible_alternative`
- preserve_selected_owner_effect: `no_op`
- abstain_context_only_effect: `no_op`
- score_delta: `0.0`
- direct_request: `False`

## Required Vetoes

- `no_switch_if_not_initial_owner_decision`
- `no_switch_if_recommendation_is_preserve_selected_owner`
- `no_switch_if_recommendation_is_abstain_context_only`
- `no_switch_if_visible_alternative_missing`
- `no_switch_if_capacity_label_would_be_treated_as_ownership_label`
- `no_switch_if_stage7_or_training_row`
- `no_switch_if_source_or_explanation_terms_missing`

## Residual Risks

- small initial-owner sample
- one abstain missed-switch row reduces target recall but is not unsafe as no-op
- capacity evidence must remain provenance-only, not ownership evidence
- first behavior-changing selector sandbox would require explicit approval
