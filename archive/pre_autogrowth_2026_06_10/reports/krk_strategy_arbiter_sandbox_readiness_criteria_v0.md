# KRK Strategy Arbiter Sandbox Readiness Criteria v0

This document defines what must be true before any future KRK strategy-arbiter sandbox is implemented.

It does not implement a runtime arbiter.

## Current Status

```text
readiness_criteria_defined_sandbox_still_blocked
```

The current evidence is promising but insufficient:

- Balanced replay-free protected controls exist.
- Provider family/maturity can reproduce the provider-prior signal.
- Stage 7 residuals remain held out.
- No runtime selector, score delta, provider boost, or topology mutation is authorized.

## Minimum Evidence

- Balanced protected-control selector labels across Stage 4/5/6.
- Stage 7 residuals remain held-out challenge cases, not training rows.
- Provider provenance/maturity fields are explicit.
- Out-of-sample protected controls exist for validation.
- Route evidence contract is defined for every selector suggestion.

Current gap:

```text
out_of_sample_controls
```

## Required Default-Off Tests

- Baseline vs flag-off selected move equivalence.
- Baseline vs flag-off selected provider equivalence.
- Baseline vs flag-off local result equivalence.
- Baseline vs flag-off conversion result equivalence.
- Baseline vs flag-off shadow-candidate equivalence.
- No metadata emitted when flag is off.
- Metadata-only delta when observability is on.

## Required Sandbox Tests

- Selector suggestions are traceable.
- Selector never uses runtime DTM/tablebase.
- Selector never mutates topology.
- Selector never directly requests a provider without visible contract evidence.
- Selector score delta is explicit and bounded.
- Stage 7 residuals stay challenge-only.
- M1-M4 causal inputs are unchanged.
- Promotion gate defaults to blocked.

## Required Guardrails

- Stage 4 wrong-tempo paired controls.
- Stage 5 fence/handoff controls.
- Stage 6 drive_to_edge controls.
- Stage 1 / KRK entry if cheap.
- M1-M4 preservation suite.
- KPK-to-KQK bridge sanity if cross-domain routing is touched.

## Sandbox Profile Constraints

Any future sandbox must be:

- default-off,
- KRK-scoped,
- initially scoped to `handoff_composition_v1`,
- based on `StrategyProposalFrame` and explicit provider provenance/maturity metadata,
- forbidden from runtime DTM/tablebase,
- forbidden from state-hash exceptions,
- forbidden from making handoff packets, stats, shadow candidates, StructuralCandidates, GrowthGovernor, PlanCapsuleSpec, or InternalTerminalSpec causal.

## Promotion Rules

- No promotion from selector target improvement alone.
- Protected Stage 4/5/6 controls must improve or hold.
- Stage 7 residuals must not be used as training rows.
- M1-M4 preservation must not regress.
- Every affected suggestion must have readable route evidence.
- Any protected guardrail regression means quarantine.

## Decision

Runtime arbiter:

```text
blocked
```

Selector sandbox:

```text
blocked
```

Recommended next step:

```text
architecture_review_or_out_of_sample_control_collection
```

Do not implement a runtime arbiter before that review.
