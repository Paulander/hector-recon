# Active Brief: KRK Autogrowth v0

Status: learning-core reset branch.

The previous branch mode over-optimized for not approving bad mechanisms. This branch should optimize for allowing a minimal learner to act in sandbox, receive credit, promote or delete candidate topology, and prove whether the loop is alive.

## Current Direction

Build and evaluate one causal trace-derived topology-growth loop:

```text
rollout -> trace -> triplet candidate -> sandbox activation -> credit ->
M3 update -> promotion/deletion -> M4 consolidation -> held-out evaluation
```

The experiment is not "finish Stage7" or "prepare Stage8". It is:

> Can ReCoN grow one useful topology addition from traces that improves held-out KRK conversion without learner-visible stage labels?

## What To Keep Active

- Core ReCoN graph/request-confirmation engine.
- Triplet representation.
- Baseline-to-ReCoN compiler.
- KRK evaluation harness, refactored toward competence metrics.
- M3 fast plasticity and M4 consolidation as active experimental variables.
- A small promotion-boundary safety gate.

## What Is Historical Only

Archived under `archive/pre_autogrowth_2026_06_10/`:

- Old report/control-plane packets.
- Stage7/Stage8 completion/quarantine artifacts.
- Selector behavior/review artifacts.
- Previous external audit pack.
- Report-gate tests.

Do not rebuild those as the mainline workflow.

## Immediate Checkpoints

1. Keep the cleaned branch runnable with the core test suite.
2. Create a learner-visible feature firewall: generic board features only, no stage labels.
3. Generate locked train/dev/held-out KRK position sets.
4. Implement baseline and sham-growth arms.
5. Implement trace mining for before/action/after triplets.
6. Allow exactly one candidate topology addition in sandbox.
7. Wire M3/M4 into candidate scoring and promotion.
8. Run the three-arm held-out experiment and commit the result.

## Current No-Go List

- More readiness packets.
- More selector-runtime work.
- More Stage7/Stage8 patching.
- Report row IDs or stage labels as learner features.
- Runtime tablebase/DTM as a move provider.
- Direct provider override as the growth mechanism.

## Reporting Rule

One run should produce one machine-readable result artifact and, when useful, one short markdown summary. If a report does not summarize a run or decision that changes the next experiment, do not write it.
