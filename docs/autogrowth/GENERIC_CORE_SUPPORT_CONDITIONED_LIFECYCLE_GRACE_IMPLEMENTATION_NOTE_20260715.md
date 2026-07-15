# Support-Conditioned Lifecycle Grace Implementation Note

Date: 2026-07-15. Track: generic-core science. Status: implemented and
validated before fresh admission. Frozen contract:
`GENERIC_CORE_SUPPORT_CONDITIONED_LIFECYCLE_GRACE_WORK_PACKAGE_20260715.md`.
No seed in 20262401--20262440 was touched during implementation or validation.

## Implemented boundary

Unsupported lifecycle grace is now materialized as candidate-local graph state.
Each fixed-six or conditioned-six trial owns four internal TERMINALs
(`EVIDENCE_DEFICIT`, `EVIDENCE_PROGRESS`, `REQUEST_ACTIVE`, and
`GRACE_BUDGET_REMAINING`) and a disconnected AND `DEFER_PRUNING_REQUEST`
SCRIPT. The lifecycle host consumes only the SCRIPT emission. Fixed and
conditioned modes share identical graph topology; only the progress/request
measurement backends differ. Reaching exact retained support 32 bypasses grace
and enters the unchanged ordinary rent adjudication.

The progress terminal uses interval retained-support high-water marks over the
frozen trailing two-review window. Birth time, review age, history, and the
six-review budget survive reservoir eviction and deepcopy/checkpoint restore.
The fixed control emits on unsupported reviews 1--5 and adjudicates at review 6.
Conditioned grace additionally requires measured progress and an ordinary exact
evidence request since the prior review/birth.

The lifecycle audit now records candidate birth, every review, current/lifetime/
interval support, comparison high-water, request baselines, all terminal values
and backends, SCRIPT activation/emission, extensions, transitions, pruning
reason, live occupancy, challenger blocking, displaced eligible proposals, and
end-of-phase right-censoring. An incomplete trial is marked `right_censored`
without being pruned or misclassified as an ordinary unsupported death.

The separately versioned canonical runner freezes the five preregistered arms,
20262401--20262440 capped admission pool, first twenty admissions, and the exact
independent integrity, more-life, conditioned-evidence, maturation,
self-regulation-versus-fixed-six, behavior, and stability gates. Priority is
reported descriptively and cannot bind the grace verdict. The runner calls phase
finalization before evaluation and persists after every arm and seed.

## Validation

- Focused lifecycle, causal-rent, internal-terminal, and runner integration:
  **48 passed in 2.20 seconds**.
- Retired full-horizon protocol smoke: seed 20262301, 4,096 phase-0 and 4,096
  phase-1 episodes per arm, reduced 64-row evaluation pools. All five arms ran;
  measurement/integrity passed. This smoke is non-evidence. Its conditioned arm
  improved paired minimum target support by 24 over two-review, tied fixed-six
  on minimum support, and reduced mean live-trial occupancy by only about 0.9%,
  correctly failing the 10% self-regulation clause.
- Full repository validation: **868 passed in 2,136.77 seconds (35m36s)**.

The earlier 512-episode retired smoke failed admission 0/1 and stopped before
phase 1, as required; it is not a protocol or implementation failure.

## Fresh lock

Fresh execution remains prohibited until this implementation commit is pushed.
The canonical process must use `--pause-after-admission`, commit and push the
exact admission manifest while the same process remains alive, verify its bytes
from HEAD, and only then resume phase 1. No threshold, seed, lifecycle, request,
learning, reward, rent, capacity, cadence, or row factor may change after that
point.
