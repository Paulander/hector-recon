# Fresh-seed replication of late condition-budget expansion

Protocol declared before outcomes. Previous seeds 2 and 3 showed that additional
ordinary learning can escape an apparent plateau: seed 3 improved from 66 to
111/128 with the same 32-condition budget. Raising the budget to 64 helped seed 2
by four mates and tied seed 3. That does **not** identify a learning rate that was
too low: ordinary training changes both weights and topology, and the learning
rate was not varied. A fixed-graph impossibility certificate is not a limit on
the growing learner.

This experiment repeats the same late capacity intervention on fresh seeds,
without choosing weak or promising actors first. It adds only an experiment
runner around the existing no-addition actor and capacity comparison. No learner,
formal engine, terminal, feature, reward, growth or pruning law changes.

## Fixed schedule

- Seeds **4, 5, 6, 7, 8, 9**, all retained regardless of performance.
- Start each seed from a new empty ordinary no-addition actor. Keep the existing
  work-branch profile: 32 conditions, 2 births per episode, edge learning rate
  0.3, exploration 0.25, grace 256, prune threshold 0.02; remaining defaults also
  unchanged and recorded in the manifest. No ranked condition is attached.
- Preserve the original inert shadow prefix and the existing separate exploration
  stream after event 256. These are the same actor as the preceding capacity
  comparison, not an added mechanism or a claim that shadows help behavior.
- Train one shared prefix of **1,024** decisions per seed, in fixed 128-decision
  blocks. Evaluate at **384 and 1,024**, with learning disabled, then actually
  restore the saved checkpoint before continuing. Evaluations do not select a
  checkpoint, seed, exercise, rate or structural intervention.
- At **1,024**, clone into two arms: keep 32 conditions, or set only
  `max_conditions=64`. Both receive the same next **256** scheduled positions and
  matched exploration draws. Both continue ordinary growth/pruning and scalar
  outcome credit. Evaluate each once at **1,280**.
- This tests **expansion after training**, not 64 conditions from birth. Main's
  pre-existing 96-condition default remains unchanged.
- Use the same 256 training and 128 development positions as before. Training hash
  `6007840a71af73552e78ca3a272ce0af1b4639258246b39fa578f842a5a2a8f2`,
  development hash `dd92f3740e916f89665f459f9165088bac563a465c8bd803404a241f48798c2e`.
  Symmetry orbits must be disjoint. The final test stays unopened.
- **9,216 training + 3,072 evaluation = 12,288 actual moves.** Shared prefixes count
  once; copying history does not create more play. Six seed workers, **2,400
  seconds per seed**, one attempt, no automatic retry, extension or extra seed.
- Save private checkpoints initially, after each training block and evaluation.
  Preserve adverse results and incomplete attempts. The runner has no resume
  flag; saved states support a separately declared continuation. Partial
  unreported blocks/evaluations must not be silently excluded from move accounting.

## Comparisons and limits

Primary: final 64-minus-32 development mates for every seed, and counts of positive,
zero and negative differences. Report mean paired difference descriptively; six
seeds do not establish a generally optimal budget. Secondary: each 32-condition
trajectory at 384, 1,024 and 1,280; paired gained/lost rows, solved symmetry orbits,
actual training mates, births/retirements and graph cost. A better intermediate
checkpoint is not substituted for a worse final one.

Fresh seeds test variation in initialization and experience order on the same
viewed development positions. They are not a fresh chess test set. Observations
within symmetry families and across cloned arms are dependent. No mastery,
adaptive proposal selection, maturity, learned retention or handover claim follows
just from higher scores. Growth remains generic random proposal plus ordinary
outcome-based weighting and pruning. No diagnostic alternatives, fitted weights
or chosen actions enter training.

If expansion is consistently beneficial, evaluate that profile more broadly
before adopting it. If effects are mixed or negligible, retain the result and
choose one supported attribution question; do not add a controller or infer
that a short plateau requires a new learning law. Continued-play gains alone
cannot distinguish a slow edge learning rate from topology/exploration effects.

## Run and verify

Use Python 3.12, chess 1.11.2 and numpy 2.3.5. The launcher fixes hash seed 0 and
numerical-library threads to one:

```bash
python scripts/autogrowth/run_m1_capacity_replication.py \
  --pool reports/autogrowth/runs/m1-coach-smoke-pool \
  --output reports/autogrowth/runs/m1-capacity-replication-seeds4-9 \
  --private snapshots/autogrowth/m1-capacity-replication-seeds4-9 \
  --seeds 4 5 6 7 8 9 --workers 6 --wall-seconds 2400
```

The new focused tests cover actual move counts, terminal-only observations, no
diagnostic access, fixed milestones, paired exploration, source-bound restoration,
unchanged learning rate and continued-training equivalence across evaluation and
reload. Run the complete required branch suite in `AGENTS.md` before play. Public
results contain aggregates and transport hashes; trained weights remain private.

## Completed result — 2026-09-07

Implementation and this protocol were published before play at
[`bca4f0ad`](https://github.com/Paulander/hector-recon/commit/bca4f0add0727f404087133912c8727e903912fc).
All **196 required branch tests passed** before the experiment. The new tiny
fixture initially used a discovery interval too short for its active/inactive
support requirement; that fixture was corrected before play. No learner change
or failed chess attempt was involved.

The [public aggregate](../../reports/autogrowth/development/M1_CAPACITY_REPLICATION_20260907.json)
records every seed, fixed manifest, outcomes, lifecycle counts and private
checkpoint hashes. All **12,288 actual moves** completed in one attempt:
**9,216 training** (5,342 mates) and **3,072 frozen evaluation**. There were no
diagnostic laboratory transitions in this study. Seed times ranged from
1,169.170 to 1,275.818 seconds, within the 2,400-second caps. No retry, extension,
intermediate checkpoint selection or final-test access occurred.

Development mates out of 128:

| Seed | 384 decisions, 32 | 1,024 decisions, 32 | 1,280 decisions, 32 | 1,280 decisions, 64 | 64 minus 32 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4 | 122 | 122 | 123 | 128 | +5 |
| 5 | 106 | 128 | 124 | 128 | +4 |
| 6 | 66 | 120 | 128 | 128 | 0 |
| 7 | 62 | 62 | 97 | 103 | +6 |
| 8 | 62 | 62 | 115 | 125 | +10 |
| 9 | 66 | 111 | 111 | 111 | 0 |

### More ordinary experience

Every 32-condition actor improved its final total relative to 384 decisions.
The mean rose from 80.67/128 to 116.33/128 (63.02% to 90.89%). In particular,
seeds 7 and 8 remained at 62 at both 384 and 1,024, then reached 97 and 115 with
another 256 ordinary decisions. The earlier observed plateau was not evidence
that their current growing process could not improve.

Progress was not monotonic. Seed 5 reached 128 at 1,024 and fell to 124 with the
same budget at 1,280, losing four previously solved rows. Seed 4's late net gain
of one hides four gains and three losses. Longer training must therefore measure
both gains and retention; do not select the best historical score as the final
result or claim that sufficient patience guarantees convergence.

The edge learning rate remained **0.3** throughout. These results do not establish
that it was too small, that a faster rate would help, or whether particular gains
came from weight changes, new conditions, pruning or exploratory experience.

### More capacity

The larger budget improved four seed pairs and tied two; it worsened none. Across
the 768 paired development rows it gained 25 mates and lost none: a mean of
**4.17 mates per seed**, or **3.26 percentage points**. Its mean final score was
120.5/128 (94.14%). Three larger-budget actors solved all 25 development symmetry
orbits, versus one 32-condition actor. Seed 7 still solved only 18/25 and seed 9
also 18/25; these are not generally competent M1 solvers.

All six pairs had matching exploration streams, unchanged inherited states,
identical initial settings except the budget, and unchanged completed shadow
histories. Every evaluation preserved learned state. The six final prefix and
twelve final arm checkpoints were independently restored and checked against
their reports. All **114 immutable private payloads** were retained, including
the stronger intermediate seed 5 state and the worse final control.

During the additional 256 decisions, 32-budget actors made 5–11 births and 5–11
retirements; 64-budget actors made 35–43 births and 3–10 retirements. Final live
counts were 31–32 and 63–64. The budget is a ceiling, not a promise that every
slot is populated after pruning. Physical vertices ranged from 1,469–1,592 versus
2,489–2,690, so the benefit also has a real graph cost. The public aggregate gives
every individual count. Births still came from the unchanged generic random
grammar, not a supplied chess composition or learned adaptive proposal law.

### Interpretation and next target

The evidence now supports two narrower conclusions: early endpoints understated
what ordinary learning could achieve in these seeds, and late random-capacity
expansion helped repeatedly in this fixed development setting. The proposed
explanation “the learning rate was too slow” remains untested. No new scaffolding,
feature, controller, reward shaping or learning law was needed for these gains.

Use **64 as a provisional experimental budget** for the next longer ordinary-play
study, starting from all six saved 1,280-decision larger-budget actors. Declare
the complete endpoint and intermediate evaluation schedule before further play;
report gained and lost rows, and preserve every checkpoint rather than choosing
the best one. Keep the learning rate, exploration, growth and pruning unchanged.
Do not automatically alter rates from these evaluation outcomes. Main's original
96-condition default and learner source remain unchanged.

This follow-up asks whether more ordinary experience improves the remaining weak
histories and preserves stronger ones. It is not another causal comparison of
32 versus 64 unless both budgets receive matched new play. A later learning-rate
comparison must vary that parameter explicitly; neither increasing nor decreasing
it is established by this study. Fresh positions and a deliberately frozen final
test will still be needed for mastery claims. Adaptive structural selection and
the independently trained child-competence/delegation task remain separate work;
the delegation experiment need not wait for perfect structural discovery. This
replication is complete and closed.
