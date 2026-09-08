# M1 retention: saved structure and actual credit

Protocol declared before execution, following the exploration result at
`37e064ecbd6203163c8376c5a0882ed8070dbcae`. Seed 9 learned its entire old corner
failure family but lost four previously solved rows (one other orbit). Both
exploration rates ended with the same outcome partition. This attribution asks
whether current structure can retain both alternatives and how recorded credit
and structural changes account for the lost ordering. No learner changes.

## Fixed scope

- Use only the existing 256 training and 128 development positions. Final-test
  rows remain unopened. Grade every legal alternative once in the isolated
  laboratory: **7,039 transitions**. These answers never enter a learner.
- Restore and formally replay five saved actors: seed 9 at 0.25/events **4,096,
  4,608 and 6,144**; seed 9 at 0.50/event **6,144**; and recovered seed 7 at
  0.25/event **6,144**. Each acts once on every training/development row with
  learning and exploration disabled: **1,920 frozen actor moves**.
- Total **8,959 diagnostic executions, zero training moves, zero learner update
  calls**. One process, **2,400 seconds**, one attempt, no automatic retry or
  extension. Preserve completed reports and exact counts on interruption.
- Check the formal graph's supports and choices against the saved Boolean
  conditions and weights; reproduce historical development outcomes and digests.
  Check ranking feasibility on each split and their **combined union**. A feasible
  union is one shared set of possible weights, still not learned or generalizing
  performance. Discard all fitted coefficients. Use exact tie-aware checks when
  strict feasibility fails; numerical uncertainty stays explicit.
- Numerically inspect all 17 saved 128-decision boundaries for both seed 9 arms,
  without further actor actions. Track development rows **6, 9, 15 and 105**,
  orbit **10,54,0**. Separate changed retained weights, removed contributions and
  new definitions on fixed winning/finally-chosen comparisons. This is arithmetic
  attribution, not a counterfactual no-growth training experiment.

## Actual credit accounting

Use the two complete logs of actually submitted training actions and observed
rewards from events 4,096–6,143. The logged action selects which measurement vector
to examine; **only its recorded reward** enters the arithmetic. Never use a
laboratory grade as a substitute, select an alternative, call actor `act` or
`observe`, generate new experience or save an updated organism.

Reconstruct the existing one-step numerical update:
`delta = learning_rate * (observed_reward - selected_support) / (1 + active_count)`.
Add delta to the bias and each confirmed condition's fast weight. Reconstruct
the existing bias fast/slow transfer. Condition definitions, birth times and
request-count retirement times come from persistent saved history, not a new
proposal/pruning law. This is an audit calculation in separate Python numbers.

The complete live definition set and all fast/slow weights must match **every
subsequent saved boundary** within absolute 1e-8. If not, do not make an attribution
claim. Never deploy the reconstructed numbers or treat them as a trained policy.
Group actual credit to a representative lost position's fixed comparison by
time block, geometric family and reward sign. Track all four positions at saved
boundaries; a representative's credit explanation is not automatically proof
for every transformed choice. Keep the contribution of removals separate.

This can establish which actual updates and retirements account for a score
change. It does not establish what would happen under different actions,
retirements, weights or learning laws. Preserving a fixed action log while changing
policy would not be a valid on-policy comparison.

## Tests and execution

New focused tests cover numerical reconstruction through births and retirements,
both exploration rates, no environment transitions or learner updates during
credit accounting, rejection of incomplete/corrupted reward logs, joint-set
conflicts hidden by separate feasibility checks, trusted checkpoint identity and
terminal-only formal replay. Run the required full branch suite before execution.

```bash
python scripts/autogrowth/diagnose_m1_retention.py \
  --pool reports/autogrowth/runs/m1-coach-smoke-pool \
  --reference reports/autogrowth/development/M1_EXPLORATION_20260908.json \
  --private snapshots/autogrowth/m1-exploration-seeds479 \
  --output reports/autogrowth/runs/m1-retention-seeds79 \
  --wall-seconds 2400
```

Use Python 3.12, chess 1.11.2, numpy 2.3.5 and the existing SciPy installation,
hash seed 0 and single-thread numerical libraries. No runtime/learner source
changes or new trained payloads. The independent expert prompt accompanies this
study but does not supply a training rule or override its declared protocol.

The next learning experiment must follow the result: distinguish lack of current
capacity from reward-credit interference before selecting one generic correction
and a matched actual-play control. Do not assume more hierarchy, more exploration,
a global freeze, a corner detector or a retention controller is the answer.
