# Internal randomized trial use: pre-outcome protocol

This is an experimental extension on `codex/residual-shadow-nomination`, based on
the history-preserving live TRIAL at `16f61e9c`. Main retains the stable learner.
The purpose is to acquire outcome-grounded evidence about a trial's contribution.
This change does not yet use that signal for nomination, retention, maturity or
adaptive rates, so a performance improvement is not assumed.

## Internal mechanism

After the existing episode-128 attachment, independently enable the trial with
probability 0.5 before each of the next 128 actual actions. A separate local RNG
leaves ordinary actor exploration untouched. An internal leaf terminal carries
that assignment; an AND wrapper combines permission with the original Boolean
condition. AND, OR and exactly-one XOR keep their original pattern semantics.
Disabled trials cannot confirm the contribution gate or receive action credit.
Ordinary actor weights continue learning from the submitted action's scalar
outcome; no hypothetical or unexecuted action receives feedback.

The coach never chooses the assignment or reads the graph. The local record binds
assignment, actual action, eligibility and final scalar outcome. Invalid or
duplicate feedback cannot mutate it. Checkpoints retain the additional RNG,
history and pending-feedback restriction; pruning retains applicable history and
removes private wrapper nodes. Evaluation enables normal contributions without
sampling or learning. Outside the fixed window the trial is normally available.

Use **all** assigned episodes to compare enabled and disabled rewards. Filtering
by activation would condition on an effect of the intervention itself and bias
the comparison. Report group counts, means, participation counts, their mean
difference, and the propensity-weighted contrast
`mean(enabled * reward / p - disabled * reward / (1-p))`.
This estimates immediate access value averaged along the current learning history.
It is not lifetime topology value, a per-position matched counterfactual, or the
effect of retraining without a condition. Do not attach an iid confidence interval
or maturity label to this short adaptive run. Imbalanced exposure can make these
two estimates disagree; retain both and the counts. Sparse evidence stays uncertain.

## Fixed comparison, declared before outcomes

- Same development seeds 1, 2, 3 and existing train/validation pool as the previous
  live experiment; previously viewed validation remains development data.
- Five arms per seed: no addition, always-ranked, always-random, probed-ranked,
  probed-random. The first three use the unchanged prior implementation.
- Every arm replays the identical 128-action prefix, then learns for 128 further
  actions. Preserve all nomination rules, budgets and coefficients. Random may
  choose the ranked winner. No missing/colliding nominee is substituted or dropped.
- Each final actor plays all 128 development validation positions without learning
  or random gating. Each of the four addition actors is also evaluated on a clone
  with only the trial's coefficient zeroed. These are offline interventions only.
- Primary mechanism evidence: generic useful-AND versus correlated-but-irrelevant
  fixtures; in chess, signed randomized access estimates, assignment counts and
  disabled-credit invariants. The signal is collected but does not control policy
  in this implementation, so it cannot yet demonstrate better structural selection.
- Secondary: matched training and final-validation costs/benefits of probing,
  current-policy ablation and exact reproduction of the prior three controls.
  Do not equate either offline comparison with the online adaptive-use estimate.
- Fixed budget: 3,840 training moves, including replayed prefixes, plus 1,920
  normal validation and 1,536 ablation moves = **7,296 actual moves**. Three seed
  workers, at most 1,200 seconds per seed. No automatic extensions or score tuning.
- Record source hashes, schedules, definitions and budgets before play. Reject
  training/validation symmetry overlap. Keep the final test unopened. Preserve
  incomplete runs as failures rather than partial success summaries.

Train SHA256: `6007840a71af73552e78ca3a272ce0af1b4639258246b39fa578f842a5a2a8f2`.
Validation SHA256: `dd92f3740e916f89665f459f9165088bac563a465c8bd803404a241f48798c2e`.
Publish aggregate records and anonymous outcome rows, not trained weights, raw
boards, moves or assignment/action transcripts. Local evidence may retain the
actual action bindings; public output contains only its digest.

## Git and claim discipline

Use the experiment branch freely for bounded changes. A successful test run means
that a mechanism passed those checks, not that it solves M1 or grows generally.
Main receives summaries and continuation instructions; experimental learner code
requires a separate explicit promotion decision. A commit SHA plus protocol,
runtime identity and results is already a reproducible milestone. Reserve tags
for deliberate stable releases or major evidence milestones; do not create a
new tag for every exploratory result or rewrite an old one. Keep failed results.

## Verification before the chess run

All 151 focused tests passed in one regression run, including 23 new checks.
New coverage includes actual-use discrimination in generic fixtures, preservation
of AND/OR/XOR semantics, shared weight identity, disabled-credit exclusion,
enabled-but-inactive outcomes in the estimate, feedback binding, bounded windows,
checkpoint continuity, pruning cleanup, one real chess move per outcome, opaque
coaching, read-only evaluation/ablation, serial/parallel parity and exact equality
of the old three controls in the small runner test. No base actor, old live-TRIAL
mechanism, old runner, coach or formal engine source changed.

The generic fixture plants its candidate and starting coefficient to isolate this
mechanism; it is not evidence that chess training discovered that fixture. Both
ordinary actor bias and participating trial weights remain plastic.

Reproduce the declared run with Python 3.12, chess 1.11.2 and numpy 2.3.5:

```bash
PYTHONPATH=src:libs/recon-lite/src python scripts/autogrowth/run_trial_usefulness.py \
  --pool reports/autogrowth/runs/m1-coach-smoke-pool \
  --output reports/autogrowth/runs/trial-usefulness-seeds123 \
  --seeds 1 2 3 --conditions 32 --candidates 64 --discovery 64 \
  --after-episode 128 --suffix 128 --window 128 --probability 0.5 \
  --min-support 4 --workers 3 --wall-seconds 1200
```

Use a fresh output directory for an intentional reproduction. The script sets
deterministic hash/thread defaults; the manifest records the actual runtime.
