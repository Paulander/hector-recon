# Generic-Core Consolidation Dose: Invalid Execution

Date: 2026-07-12. Track: generic-core development. Verdict: package aborted by
a frozen-runner aggregation defect. No scientific conclusion and no automatic
repair or rerun authorized.

## Frozen setup

The work-package contract was committed at `b7379ad`, its pre-data gate
correction at `0f07e8e`, and the runner at `3ccbad6`. Before any frozen task
was generated, the complete ReCoN core suite passed 50/50.

The runner then trained and evaluated all four fixed scales (0.10, 0.25, 0.50,
and 1.00) on all 20 fresh seeds 20261301--20261320. Its progress log reached
`completed task 20/20`. It did not print arm scores during execution.

## Failure

After all training/evaluation work, final invariant aggregation attempted to
construct a set of budget tuples containing `selection_count`. That value is
a per-action dictionary and therefore unhashable. Python raised:

```text
TypeError: unhashable type: 'dict'
scripts/autogrowth/run_generic_core_consolidation_dose.py:254
```

The process exited before serializing `task_rows`. No result artifact exists,
and the in-memory measurements were lost. The integer `rng_call_count` was not
the unhashable field.

## Evidence status

- The failure is laboratory aggregation code, not a learner exception.
- All 20 task seeds were nevertheless instantiated, trained, and evaluated, so
  they are consumed development data and may not be reused for confirmation.
- Because no measurements survived, the run provides no evidence for or
  against any consolidation dose.
- The contract's kill criterion explicitly covers a runner change after fresh
  task generation. Fixing the tuple representation and repeating these seeds
  would violate the frozen package.

Runner SHA-256:
`f940e51a330d08d5e201107400925b7790c5c529fa4e868b7912e6c5fe33fff8`.
Frozen source commit: `3ccbad66321ab1ce2209c3cee45be2157512ccdb`.

## Required PI decision

This package is closed as invalid. A new authorization is required to create a
repair package. The clean repair is bounded and non-scientific:

1. compare each arm's scalar training/evaluation/RNG counts directly;
2. compare `selection_count` dictionaries by canonical JSON or direct equality,
   never by hashing the dictionary;
3. add an aggregation unit test using synthetic arm records;
4. preregister a new disjoint seed range;
5. commit and push the repair and pass the full suite before one fresh execution.

Do not change doses, gates, learner code, environment, budget, or selection rule
in that repair. Do not infer or transfer anything to KRK from this invalid run.
