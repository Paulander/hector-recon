# KRK Selector Feature Architecture Review v0

This review closes the joined-feature selector probe.

## Decision

Status: `provider_prior_remains_best_no_selector_sandbox`

The selector feature dataset is useful, but it does not justify runtime arbitration or a default-off selector sandbox.

## Evidence

- Selector target rows: `42`
- Label counts: `28` negative / `14` positive
- Best baseline: `provider_prior_loo`
- Best baseline accuracy: `0.8333333333333334`
- Trace-only observation features did not improve over provider prior.

## Interpretation

Provider identity is currently the strongest non-causal selector signal. Trace-only context terms are useful audit metadata, but they do not yet improve selector prediction over provider priors.

That is not enough for a runtime arbiter. Provider-prior success can encode dataset bias and does not prove guardrail-safe ownership.

## Allowed Next Work

- Collect more labeled controls if review authorizes it.
- Define state-local contrastive selector labels.
- Design a non-causal provider-maturity prior.
- Return to broader curriculum integration review.

## Blocked

- Runtime arbiter.
- Default-off selector sandbox.
- Provider support adapter.
- Score bonus or provider penalty.
- Stage 7 repair or promotion.
- Stage 8 training.
- Runtime DTM/tablebase.
- Gameplay-time topology mutation.

## Recommended Next Step

`review_provider_prior_vs_more_labels`

Decide whether to expand protected-control labels, create state-local contrastive labels, or pause selector work and return to broader curriculum integration.
