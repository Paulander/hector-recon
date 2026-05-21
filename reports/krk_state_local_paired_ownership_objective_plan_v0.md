# KRK State-Local Paired Ownership Objective Plan v0

This is a non-causal design plan. It does not train or implement a runtime selector.

## Motivation

- Global row classification over provider labels cannot preserve safe owners and suppress unsafe owners simultaneously.
- Ownership is state-relative: a provider is good or bad in a concrete state/control context, not globally.
- Forced-capacity, selected-playout, safe-preservation, and ownership-selection evidence must stay separated.

## Objective

- `objective_id`: `krk.selector.state_local_paired_ownership.v0`
- `status`: `design_only`
- `goal`: `learn non-causally whether one candidate owner should be preferred, rejected, or abstained relative to other owners in the same state`
- `unit`: `state_local_owner_pair`
- `not_a_runtime_policy`: `True`

## Label Rules

- `selected_owner_converted_vs_selected_owner_failed`: within comparable state/local context, converting selected owners outrank failing selected owners Risk: cross-state fallback only; weaker than same-state evidence
- `forced_alternative_converts_when_selected_owner_fails`: same-state alternative capacity can mark an ownership gap, but not direct runtime ownership until selection evidence exists Risk: forced capacity may overstate normal-routing suitability
- `safe_preservation_before_suppression`: validated safe selected owners should be preserved unless same-context failure evidence overrides Risk: over-preservation can miss rare failures
- `abstain_when_only_capacity_or_proposal_evidence`: do not train a preference pair when only proposal/capacity evidence exists and no selected/handoff outcome is known Risk: slower learning but avoids handcrafted policy leakage

## Minimum Benchmark Requirements

- `protected_pair_count`: `30`
- `same_state_conflict_pair_count`: `8`
- `selected_failure_with_alternative_success_count`: `4`
- `safe_preservation_pair_count`: `12`
- `stage7_training_rows`: `0`
- `leave_state_out_required`: `True`
- `family_holdout_required_if_possible`: `True`

## Future Pipeline

- build replay-free pair inventory from existing selected/forced/proposal artifacts
- classify pairs by evidence strength
- benchmark state-local pair scoring non-causally
- review whether same-state evidence improves negative suppression without sacrificing safe preservation
- only after explicit review, consider a default-off runtime sandbox design

## Decision

- `status`: `state_local_paired_ownership_objective_plan_ready`
- `recommended_next_step`: `build_replay_free_state_local_pair_inventory`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
