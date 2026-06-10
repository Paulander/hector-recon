# KRK Selected Provider Diversity Architecture Review v0

This review interprets replay-free and sampled selected-provider evidence. It does not implement a selector or authorize a sandbox.

## Evidence

- Replay-free selected provider families: `{'edge_trap': 5, 'stage0_basin': 18}`
- Replay-free distinct families: `2`
- Replay-free max dominance: `0.7826`
- Sampled selected provider families: `{'stage0_basin': 20}`
- Sampled distinct families: `1`
- Sampled max dominance: `1.0`
- Contrast findings: `['protected_conversion_positive_provider_diversity_present', 'protected_label_balance_present', 'selected_provider_family_diversity_still_missing', 'heldout_stage7_contains_unresolved_all_negative_rows']`

## Interpretation

- Current selected-provider diversity: `failed_by_current_arbitration_stage0_dominance`
- Contrast evidence: `provider_contrast_signal_present`

Replay-free selected records only show stage0_basin/edge_trap, and bounded protected selection sampling selected stage0_basin for every sampled state. This is a property of the current raw arbitration policy, not evidence that other providers lack conversion value.

Requiring diverse normal selected providers before testing an arbiter may be too hard, because the proposed arbiter is intended to correct current selected-provider dominance.

## Decision

- Status: `selected_provider_diversity_requirement_should_be_reframed`
- Recommended next step: `define_selector_readiness_v3_proposal_diversity_criteria`
- Runtime arbiter and selector sandbox remain blocked.

## Proposed Readiness v3 Direction

- Replace hard requirement: `distinct_current_selected_provider_families`
- Selected-provider dominance role: diagnostic blocker for promotion, but not necessarily a blocker for a default-off sandbox design review if proposal/forced contrast evidence is strong.

- `diverse_strategy_proposal_families_present`
- `diverse_forced_or_compatible_conversion_positive_families_present`
- `stage7_held_out_challenge_preserved`
- `default_off_equivalence_required_before_any_sandbox`
- `guardrail_regression_zero_tolerance_for_protected_stack`
