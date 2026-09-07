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
