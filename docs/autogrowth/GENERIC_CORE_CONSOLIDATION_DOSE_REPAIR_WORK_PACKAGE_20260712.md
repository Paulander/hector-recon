# Generic-Core Consolidation Dose Repair Work Package

Date: 2026-07-12. Track: generic-core development. Status: PI-authorized and
frozen before repair implementation.

## Predecessor failure

The first dose execution trained and evaluated all four arms on seeds
20261301--20261320, then failed before serialization because final budget
aggregation placed dictionary-valued `selection_count` inside a set. No scores
survived. Those seeds are consumed development data and remain retired.

## Scope and hypothesis

This is a laboratory repair, not a new scientific mechanism. The scientific
hypothesis, strongest null, learner/laboratory boundary, four doses, eligibility
gates, deterministic selection rule, environment, training budget, evaluation
budget, and transfer freeze are inherited unchanged from
`GENERIC_CORE_CONSOLIDATION_DOSE_WORK_PACKAGE_20260712.md`.

The repair hypothesis is only that direct equality can validate identical
per-arm budgets without attempting to hash dictionaries. The strongest null is
that the repaired runner still cannot complete, changes scientific inputs, or
misclassifies unequal action-count dictionaries as equal.

## Exactly one repair

Replace the set-of-tuples budget comparison with an explicit helper that:

1. chooses one arm as the reference;
2. directly compares training episode count, evaluation episode count,
   selection count dictionary, and RNG call count for every other arm;
3. returns false if any scalar or dictionary differs.

Add synthetic unit tests proving that identical records pass and that changes to
each checked field, including one action count, fail. Do not change learner code,
environment helpers, dose values, topology/plasticity configuration, gates,
selection ordering, or output measurements.

## Fresh execution

Use disjoint seeds 20261401--20261420 exactly once. All original frozen settings
remain:

- scales 0.10, 0.25, 0.50, and 1.00;
- 4,096 regime-0 then 4,096 regime-1 episodes, without replay or boundary event;
- 512 evaluation episodes per regime;
- identical per-task random seed across arms;
- terminal-only +/-1 reward;
- four-live/64-total renewable topology;
- selection only among eligible non-control doses by the original frozen
  worst-regime rule.

The artifact must identify both the original dose contract and this repair
contract and hash all reused helpers and the repaired runner.

## Gates and stop rule

Before generating a fresh task:

1. the synthetic aggregation tests pass;
2. the complete 50-test ReCoN core suite passes;
3. contract, repair, tests, and runner are committed and pushed.

Execute once. A runner exception, missing artifact, invariant failure, or
post-generation code change closes this package. A scientific gate failure
selects no dose and is a valid negative result. A selected dose remains a
development candidate only; no automatic confirmation, adaptive-law change, or
KRK transfer is authorized.
