# KRK Selector Objective Architecture Review v1

This review closes the current selector-prior branch and decides what evidence is still missing before any runtime strategy arbiter can be considered.

## Current Result

The selector evidence is useful but not sandbox-ready.

- Provider-prior leave-one-out accuracy is `0.833` on `42` selected-playout control rows.
- Trace-only observation terms did not improve over the provider prior.
- Explicit provider provenance fields reproduce the provider-prior signal: `provider_family`, `provider_maturity`, `provider_source_stage`, and `family_maturity` all reach `0.833`.
- Stage 7 rows remain held out and contribute `0` training rows.

## Interpretation

The signal is not “raw provider ID should control runtime ownership.”

The better interpretation is:

- Provider identity is carrying maturity/provenance information.
- Foundation-frozen `stage0_basin` selected-playout controls are often positive in this dataset.
- Validated edge-trap providers are often negative under these selected-playout labels.
- This may reflect label semantics and horizon/control artifacts, not true provider incapacity.

So provider provenance belongs in non-causal evidence records, but it is not a runtime selector.

## Decision

Status:

```text
selector_objective_needs_stratified_label_expansion_before_sandbox
```

Runtime arbiter allowed:

```text
false
```

Selector sandbox ready:

```text
false
```

## Recommended Next Slice

```text
collect_small_stratified_selector_labels_v1
```

The next slice should first create a bounded label plan, not run a large playout batch.

It should separate:

- selected-playout success,
- forced-provider conversion,
- same-move provider compatibility,
- guardrail-safe ownership,
- held-out Stage 7 challenge status.

Bounds:

- maximum `12` new states,
- h40 practical horizon,
- diagnostic caches,
- trace failures only,
- no exhaustive legal-first sweeps,
- Stage 7 training rows remain `0`.

If existing artifacts already contain enough labels, use replay-free extraction instead of new playouts.

## Blocked

- Runtime arbiter.
- Selector sandbox.
- Raw provider-id runtime prior.
- Provider support adapter.
- Score bonus or provider penalty.
- Stage 7 repair.
- Stage 7 promotion.
- Stage 8 training.
- Runtime DTM/tablebase.
- Gameplay-time topology mutation.
- M3/M4 arbitration update.
