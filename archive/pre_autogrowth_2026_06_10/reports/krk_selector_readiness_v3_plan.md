# KRK Selector Readiness v3 Plan

This design-only plan reframes selector-readiness criteria after selected-provider sampling showed the current raw arbiter is stage0-dominant. It does not implement a sandbox.

## Reason

Selected-provider diversity from the current raw arbiter is stage0-dominant; requiring it as a pre-sandbox hard gate blocks the mechanism meant to correct that dominance.

## Readiness Checks

- `proposal_family_diversity` status=`passed` observed=`{'distinct_strategy_proposal_families': 3}`
- `conversion_positive_provider_diversity` status=`passed` observed=`{'distinct_conversion_positive_provider_families': 3, 'families': ['drive_to_edge', 'edge_trap', 'fence_established']}`
- `label_balance` status=`passed` observed=`{'positive': 13, 'negative': 11}`
- `protected_stage_coverage` status=`passed` observed=`{'row_count_by_stage': {'stage4': 2, 'stage5': 4, 'stage6': 3, 'stage7': 4}}`
- `stage7_heldout_boundary` status=`passed` observed=`{'stage7_training_rows': 0}`
- `current_selected_provider_diversity` status=`diagnostic_only_not_sandbox_blocker` observed=`{'v2_blockers': ['insufficient_selected_provider_family_diversity']}`

## Sandbox Design Requirements

- `default_off`
- `default_off_equivalence_before_enabled_tests`
- `visible_source_terms_and_provider_metadata`
- `no_runtime_dtm_or_tablebase`
- `no_gameplay_topology_mutation`
- `stage7_held_out_challenge_only`
- `guardrail_validation_before_promotion`

## Decision

- Status: `selector_readiness_v3_sandbox_design_review_allowed`
- Hard blockers: `[]`
- Recommended next step: `design_default_off_strategy_arbiter_sandbox_for_review`
- Runtime arbiter and selector sandbox remain blocked until explicit design review.
