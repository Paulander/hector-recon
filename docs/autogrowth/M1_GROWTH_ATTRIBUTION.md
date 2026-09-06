# M1 representation and birth-timing attribution

This is an offline experiment, not a replacement learner or adaptive-growth
mechanism. The production `TerminalDevelopment` and ordinary coach are unchanged.

## Question and controls

Does gradually revealing random conditions help compared with having precisely
those conditions from the beginning? Does a mixed Boolean representation help
compared with an additive atomic representation trained from scratch?

The strongest null is that fixed representation plus scalar weight learning
explains the result; gradual birth is unnecessary on this M1 distribution.

| Arm | Initially available | Later births | Final condition parameters |
| --- | --- | --- | --- |
| `online_random` | No learned conditions | Production random proposals on an outcome-blind schedule | 80 mixed conditions |
| `fixed_random` | Same 80 mixed conditions, zero weights | None | Exactly the same definitions and order |
| `atomic_only` | 80 unique equality literals, zero weights | None | Entire supplied atomic vocabulary |

A fixed arm is a laboratory control, not a proposed hand-authored chess policy.
Its grammar is generic and its weights start at zero. No board, outcome, answer
move or validation score enters the proposal plan.

The mixed plan uses the existing `_birth` implementation, including its duplicate
skips and AND/OR/exactly-one distribution. Proposal randomness is separate from
exploration randomness in **all three** arms. Thus it does not reproduce the
old seed-1 trajectory, where birth and exploration shared a stream. A fixed
schema and seed generate the plan before play; online birth reveals it after
completed episodes without reading their outcomes.

Training starts, exploration draws, scalar ±1 grading and learning configuration
are matched within each seed. Actions and outcomes may differ; that is what we
measure. Pruning is disabled in every arm, so this does not test survival.

## Matching limits

The schema has only 80 atomic literals. Duplicating atoms to reach the former
96-condition budget would change effective update rates without adding features.
This experiment therefore uses 80 separate trainable condition weights plus the
shared bias in each arm. This matches parameter counts, not effective rank.

Atomic-only sees the entire atomic vocabulary; a sampled mixed graph may not.
Mixed conditions also have more reader links and different counts of active
features, which affect the existing normalized update denominator. We report
these structural costs and elapsed time rather than claim equal compute. The
fixed-versus-atomic comparison tests these complete representations, not the
isolated effect of Boolean operators at identical coverage. The earlier weight
ablation answers the narrower contribution question at one trained checkpoint.

## Fixed first-run budget (before outcomes)

- Starting production baseline: `54a1eb87`.
- Seeds: 1, 2, 3; 128 actual training moves per arm, 80 conditions per arm.
- Pool: seed 20260905, 256 training positions and 128 viewed validation rows
  covering 25 symmetry orbits, with disjoint train/validation orbits.
- Nine arms total: 1,152 training moves and 1,152 evaluation moves.
- Three worker processes, one independent seed per worker; 600 seconds maximum
  per arm, including training and evaluation. No automatic budget extension.
- Primary quantity: paired seed differences in greedy validation mate rate for
  online minus fixed. Secondary: fixed minus atomic and orbit-macro differences.
- Expectation to test, not assume: online and fixed may be comparable; mixed
  conditions may outperform additive atoms. Either sign is retained as a result.
- Stop conditions: representation mismatch, invalid action, learned-state change
  in evaluation, train/validation orbit overlap, or time limit. Incomplete seeds
  are not averaged into a successful comparison.
- No parameter changes, score-triggered stopping, final-test opening or automatic
  curriculum advance. Three engineering seeds are not broad confirmation.

The runner writes its source identity, complete random plans and exercise order
to `manifest.json` before any play. The training loop sees only the usual opaque
organism interface. Structure audits and validation happen after training;
validation never sends feedback or saves an updated organism. Full seed results
and paired summaries are written to a new output directory; existing results
cannot be overwritten. No trained checkpoints are exported by this experiment.

## Run

Use the same Python 3.12 environment and requirements as `MATE_ONE_COACH.md`.
To regenerate the pool in a new directory (offline curation only):

```bash
python scripts/autogrowth/run_mate_one_coach.py prepare --pool reports/autogrowth/runs/m1-attribution-pool
python scripts/autogrowth/compare_mate_one_growth.py --pool reports/autogrowth/runs/m1-attribution-pool --output reports/autogrowth/runs/m1-attribution-seeds123 --seeds 1 2 3 --conditions 80 --episodes 128 --workers 3 --wall-seconds 600
```

Use `--workers 1` for sequential execution. On another computer, run the same
code and pool with a separate output directory; seeds are explicit, not inferred
from machine identity. This runner has no final-test switch and never reads
`test.txt`. A failed run leaves its manifest and failure record; it does not
silently resume, shorten one arm or increase its budget.

Tests: `tests/autogrowth/test_mate_one_attribution.py` covers grammar reuse,
definition/timing pairing, unshared random streams, actual terminal-only actions,
opaque training, serialization, final-test isolation, budget/overlap guards and
identical serial/parallel results.

## Completed first comparison

Implementation: `2188bf59`. All nine arms completed their exact budget; 93
focused tests passed. No production learner or coach code changed. Full frozen
plans, source identities, row/orbit summaries and structural costs are in the
[result JSON](../../reports/autogrowth/development/M1_GROWTH_ATTRIBUTION_20260906.json).
It contains no trained weights or raw board/move logs.

| Seed | Online random | Identical fixed random | Atomic-only |
| --- | ---: | ---: | ---: |
| 1 | 103/128 | 103/128 | 125/128 |
| 2 | 62/128 | 62/128 | 62/128 |
| 3 | 128/128 | 126/128 | 75/128 |
| Mean mate rate | 76.30% | 75.78% | 68.23% |

Online minus fixed has paired differences of 0, 0 and +2 mates: mean +0.52
percentage points, paired-seed standard deviation 0.90 points. The corresponding
orbit-macro differences are 0, 0 and +1.33 points. These results do not establish
a substantial reliable benefit from gradual random birth on this distribution.

Fixed mixed minus atomic has differences of -22, 0 and +51 mates: mean +7.55
points, but paired-seed standard deviation 29.26 points. The mean alone would be
misleading. The mixed representation is not consistently superior in these
three short runs. Atomic-only uses the same complete vocabulary in every seed,
so seed variation cannot be attributed solely to which random conditions exist;
experience/exploration order and optimization also vary.

The earlier ablation removed compositions from an already trained model. This
comparison trains the atomic model independently, letting it compensate with
other weights. Those are different questions, so the results do not conflict.
One 128/128 seed is not mastery, and three engineering seeds on viewed validation
are not sealed confirmation.

Next candidate implementation remains the smallest residual-guided nomination
and prospective shadow-comparison mechanism, using actual terminal responses
and scalar outcomes. Do not assume it will fix the weaker seeds: retain these
controls and separately test whether added structures help prediction and action.
No adaptive mechanism or additional training was triggered by this result.
