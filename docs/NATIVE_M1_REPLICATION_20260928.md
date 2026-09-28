# Native selective M1: eight-seed replication

Milestone recorded 2026-09-28. **Eight of eight fresh actors passed acquisition
and sampled retention on the complete declared 1,512-position KRK mate-in-one
population.** The predeclared operational hurdle was at least six of eight.

This is native chess learning: the graph chooses a legal move and receives the
scalar outcome of that selected move. It is not a Boolean-only result or an
evaluation of supplied trained scorers. Ordinary weight learning, births,
prospective refinement and pruning remained enabled throughout continuation.

## Result and measurement

Each actor received 2,048 acquisition actions and 1,024 further ordinary actions.
All actors continued, regardless of their scores. Greedy evaluations used
isolated copies at six checkpoints, with no evaluation feedback entering learning.

| Seed | 1,536 | 2,048 | 2,304 | 2,560 | 2,816 | 3,072 | Joint gate |
|---|---:|---:|---:|---:|---:|---:|---|
| 202609250801 | 1512 | 1512 | 1512 | 1512 | 1512 | 1512 | PASS |
| 202609250802 | 1512 | 1512 | 1512 | 1512 | 1512 | 1512 | PASS |
| 202609250803 | 1512 | 1512 | 1512 | 1512 | 1512 | 1512 | PASS |
| 202609250804 | 1512 | 1512 | 1512 | 1512 | 1512 | 1512 | PASS |
| 202609250805 | 1512 | 1512 | 1512 | 1512 | 1512 | 1512 | PASS |
| 202609250806 | 1512 | 1512 | 1512 | 1512 | 1512 | 1512 | PASS |
| 202609250807 | 1512 | 1512 | 1512 | 1512 | 1512 | 1512 | PASS |
| 202609250808 | 1512 | 1512 | 1512 | 1512 | 1512 | 1512 | PASS |

All scores are out of 1,512. Acquisition required perfection at 2,048; retention
required perfection at all four subsequent censuses. There were no observed
adjacent-checkpoint losses or losses from the fixed 2,048 solved set. The first
observation of perfection was 1,536, not a measurement of the exact first action
at which competence arose. Exploratory training itself is not claimed perfect.

The accepted cohort contains 24,576 training actions, 72,576 evaluation actions
and 200 checkpoints. Each actor has full independent native reconstruction of
all training/evaluation records and exact cold continuation at 2,048. The
two-sided exact 95% seed-level interval for joint success is [0.630583, 1.0];
eight successes do not prove that population reliability exceeds 75%. Positions
and census checkpoints are not independent seed replicates.

## Starting state, learning and growth

Fresh actors contain one generic zero-weight owned bias and no learned scoring
predicates or training history. The factory supplies 16 relational sensors,
generic state/action readers, candidate-generation rules and native execution
infrastructure. This is not a claim of starting with one physical graph node or
discovering the sensor vocabulary. No trained seed-61 or Boolean-study dictionary,
fitted weights, correct move or authored corner strategy initializes an actor.

The exact selective configuration retains learning rate 0.3, exploration 0.25,
pruning threshold 0.02, development every 64 actions, 96 owned parameters and
prospective refinement cost 0.25. Whole-owner splitting and reclosure are off.
The generic development controller is Python code; formal graph execution makes
the decisions. This is not a claim that the growth controller was itself learned.

| Seed suffix | Bud births | Approved refinements | Retirements | Final live contributors, including bias |
|---|---:|---:|---:|---:|
| 801 | 47 | 1 | 32 | 17 |
| 802 | 47 | 1 | 36 | 13 |
| 803 | 45 | 3 | 33 | 16 |
| 804 | 48 | 0 | 28 | 21 |
| 805 | 46 | 2 | 31 | 18 |
| 806 | 47 | 1 | 30 | 19 |
| 807 | 48 | 0 | 38 | 11 |
| 808 | 44 | 4 | 25 | 24 |

These are recorded lifecycle events, not causal ablations. In particular, two
successful actors had no approved refinements. Physical nodes replicated across
legal-action bindings are distinct from shared learned contributors. A branch
created at the terminal boundary has no subsequent learning opportunity; census
execution does not provide credit.

## Technical recovery and verification

The study completed under an explicit recovery amendment. Fully guarded and
independently verified 801/802 were retained. Original 803/804 producers had
complete scientific records but lacked resource-finalization receipts after an
interruption. The user authorized one complete fresh rerun of each original
seed; their new guarded runs and independent replays passed. Seeds 805–808 were
first executions. No low score triggered a retry or seed substitution.

Old/new 803/804 scientific receipts, semantic checkpoint sidecar projections,
topology and lifecycle records matched exactly under the declared comparison.
Permitted physical checkpoint hash references were distinguished from scientific
state; actions, rewards, weights, RNG and contributor order were not normalized.
Closure did not deserialize or independently replay the old checkpoints.
Their missing original resource receipts remain **unresolved**. New rerun
verification does not retrospectively establish old resource compliance.

The two superseded attempts add 6,144 training actions, 18,144 evaluation actions
and 50 checkpoints outside the accepted unique cohort. They are preserved and
are not extra independent seeds. Final cohort statistics, integrity, archive
readback and the archive worker's external final guard receipt all passed.

## Published implementation and reproducibility record

The selective implementation already landed on main in
[`b0bc0c6f`](https://github.com/Paulander/hector-recon/commit/b0bc0c6fe26eba5bd3a0985403ca5a7b5a0b0130).
The milestone publication checked all 32 original publication files and all 72
runtime dependency blobs against the validated local publication manifest; all
matched. This update changes documentation and evidence summaries only, not
learner behavior, runtime defaults, sensors or the packaged seed-61 artifact.

The fresh entry point is:

```python
from recon_lite_chess.coach.selective import create_actor

actor = create_actor(seed=202609250801, role="selective")
```

This constructs an untrained actor. The separately documented
[`load_pretrained_m1`](SELECTIVE_M1_BASELINE.md) loads the original trained seed-61
reference and is not the initializer used in the fresh replication.

The [compact evidence ledger](evidence/native_m1_replication_20260928.json)
records seed outcomes, configuration, source identities and hashes of the sealed
protocol, report, cohort, integrity and archive receipts. It is a portable
summary and integrity index, not a replacement for per-action evidence.

The complete research packages remain outside Git. Exact replay requires those
packages, their referenced historical dependencies and the pinned runtime/input
files. In particular, the recovery archive references the retained 801/802
evidence from `native-selective-m1-readiness-20260925`; it is not a standalone
bundle of all prior dependencies. Preserve those packages and do not represent
the constructor example or a seed-61 demo as reproduction of this cohort.

## Scope and next work

The population is the declared 1,512 legal White-to-move KRK mate-in-one piece
placements, 189 D4 symmetry orbits, without draw history. It is now known
development/regression material. The result does not establish unseen-position
generalization, all KRK play, availability recognition on non-M1 boards, M2,
uninterrupted retention between checkpoints, or a necessary individual growth
mechanism.

The milestone supplies a reproducible implementation reference and demonstrated
fresh-start outcomes for subsequent research. M2 sensor design and continuation
with M1 retention monitoring are separate decisions. Optimization is not a
prerequisite for recording this result; new mechanisms remain separate changes.
