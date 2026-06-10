# KRK Strategy Arbiter Architecture Review v1

This review gates the next architecture slice after the protected forced-provider control labels and stratified arbiter probe.

## Decision

Status: `trace_only_observability_skeleton_allowed`

The evidence supports a default-off, trace-only KRK strategy-arbiter observability skeleton. It does not authorize a runtime provider-selection arbiter, score bonus, support adapter, Stage 7 repair, Stage 7 promotion, or Stage 8 training.

## Evidence

Protected selected-provider and forced-provider controls are promising:

- Selected-provider labels have best positive-hit rate `1.0`.
- Forced-provider controls contain `12` labels: `9` mate and `3` max_plies.
- Stage 5 forced controls are `6/6` mate.
- Stage 6 forced controls are `3` mate and `3` max_plies.

Stage 7 remains a held-out challenge gap:

- Forced Stage 7 residual labels have best positive-hit rate `0.5`.
- Stage 7 stays `local_valid_composition_quarantined`.
- Stage 7 residuals should test future arbitration and plan-selection machinery, not drive local repair.

## Blocked

The following remain blocked:

- Runtime provider-selection arbiter.
- Provider score bonus, provider penalty, or support adapter.
- Stage 7 runtime repair or promotion.
- Stage 8 training.
- Runtime DTM/tablebase lookup.
- Gameplay-time topology mutation.
- Direct unsafe role-SCRIPT -> provider SUB edges.
- M3/M4 arbitration updates.

## Allowed Next Slice

Allowed implementation: `krk_strategy_arbiter_observability_skeleton_v0`

Scope:

- Default off.
- Trace-only when explicitly enabled.
- Recommendation/observation metadata only.
- No score changes.
- No selected-move changes.
- No selected-provider changes.
- No provider requests.
- No topology mutation.
- No M3/M4 updates.

Required trace fields:

- `schema_version`
- `arbiter_id`
- `causal_status`
- `direct_request`
- `score_delta`
- `selected_provider_before_observation`
- `recommendation_only`
- `source_terms`
- `proposal_count`
- `provider_candidates`

## Required Tests

Before any further work, the observability skeleton must prove:

- Default-off equivalence.
- Enabled observations are visible and non-causal.
- Enabled observations do not alter scores or selected moves.
- No runtime DTM/tablebase path is introduced.
- No hidden provider routing is introduced.

## Stop Conditions

Stop if:

- Default-off equivalence fails.
- The implementation needs score or provider-selection changes.
- The trace cannot explain observation source terms.
- Stage 7 repair pressure reappears.
- Protected provider behavior regresses.
- Runtime defaults change.

## Recommendation

Implement only the default-off trace-only observability skeleton next. Do not implement causal strategy arbitration until a later review authorizes a default-off sandbox with guardrails.
