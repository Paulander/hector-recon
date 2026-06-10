# KRK Selector Balanced Architecture Review v1

This review closes the balanced-label selector slice.

## Evidence

- Balanced replay-free selector rows: `18`
- Label counts: `9` positive / `9` negative
- Best baseline: `provider_id_loo`
- Best baseline accuracy: `0.7777777777777778`
- Matching provenance baselines: `provider_family_loo`, `provider_maturity_loo`
- Stage 7 training rows: `0`

## Interpretation

The balanced control set confirms a non-causal provider/provenance signal.

That is useful, but it is not enough to implement a selector sandbox:

- The dataset is small.
- The labels are constructed from existing protected controls.
- Stage 7 residuals remain held out.
- Provider-family/maturity performance is promising, but it still needs explicit route evidence and guardrail validation before any causal use.

The important result is that raw provider ID is not necessary to explain the signal. Explicit provenance fields can carry the useful part of the evidence.

## Decision

```text
selector_signal_promising_sandbox_blocked_pending_readiness_criteria
```

Runtime arbiter:

```text
blocked
```

Selector sandbox:

```text
blocked
```

## Required Before Any Sandbox

- Default-off equivalence protocol.
- Explicit `StrategyProposalFrame` inputs.
- Provider provenance and maturity features.
- No hidden raw-provider-id prior.
- Route evidence for every selector suggestion.
- Guardrail validation plan for Stage 4/5/6/1.
- Stage 7 residuals remain held-out challenge cases.
- M1-M4 causal inputs unchanged.
- Promotion gate defaults to blocked.

## Recommended Next Step

```text
define_strategy_arbiter_sandbox_readiness_criteria
```

This should be a design/review artifact only. It should not implement a runtime arbiter.

## Blocked

- Runtime arbiter.
- Selector sandbox implementation.
- Provider support adapter.
- Score bonus or provider penalty.
- Stage 7 repair.
- Stage 7 promotion.
- Stage 8 training.
- Runtime DTM/tablebase.
- Gameplay-time topology mutation.
- M3/M4 arbitration update.
