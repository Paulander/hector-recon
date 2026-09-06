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
An average over the sampled positions can also obscure specialized usefulness in
a rare context. It is not a contextual competence model or authority to prune.

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

Implementation and pre-outcome protocol:
[`567dd40f`](https://github.com/Paulander/hector-recon/commit/567dd40f095fec45e0c3c928ac02d7805ef817fe).

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

## Completed result: 2026-09-06

All 7,296 planned moves completed: 3,840 training and 3,456 development evaluation
and ablation moves. Every record from the nine old control runs reproduced
exactly apart from wall time, including actual action/outcome digests, learned
state, structure and ablations. The final test stayed unopened. The aggregate
record is `reports/autogrowth/development/TRIAL_USEFULNESS_20260906.json`.

Final greedy development mates, out of 128 positions / 25 symmetry orbits:

| Seed | No addition | Always ranked | Always random | Probed ranked | Probed random |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 126 | 126 | 128 | 122 | 126 |
| 2 | 93 | 101 | 101 | 94 | 94 |
| 3 | 66 | 66 | 66 | 66 | 66 |

The new probing schedule improved none of these comparisons. Ranked probing
cost 4/7/0 mates versus always-ranked, and random probing cost 2/7/0 versus
always-random. Suffix training mates were 103/82/45 for both probed roles, versus
102/92/45 for always-ranked and 103/92/45 for always-random. This is an
experimental performance regression; it has not been adopted by main.

Each probe completed 128 assigned episodes with zero disabled participation
credit. Enabled/disabled counts were 62/66, 61/67 and 67/61 for seeds 1/2/3.
The following estimates were identical for ranked/random within each seed:

| Seed | Enabled minus disabled mean reward | Propensity-weighted contrast |
| --- | ---: | ---: |
| 1 | +0.069404 | +0.031250 |
| 2 | -0.004894 | -0.031250 |
| 3 | -0.034744 | -0.062500 |

These are observed estimates, not established positive/negative causal labels.
In seed 1, the two different candidates produced exactly the same suffix
action/outcome digest and reward estimates. Their actual enabled participation
counts were 1 and 36, and final validation differed (122 versus 126). Identical
observed behavior supplies no evidence to distinguish their access value on that
history, even though their differently trained parameters generalize differently.
Seed 2 had the same nominee in both roles and identical complete trajectories.

Final-policy ablation of the probed actors:

| Seed / role | Normal → masked mates | Action changes | Mates lost / gained when masked |
| --- | ---: | ---: | ---: |
| 1 ranked | 122 → 122 | 0 | 0 / 0 |
| 1 random | 126 → 126 | 0 | 0 / 0 |
| 2 ranked | 94 → 117 | 27 | 2 / 25 |
| 2 random | 94 → 117 | 27 | 2 / 25 |
| 3 ranked | 66 → 66 | 0 | 0 / 0 |
| 3 random | 66 → 66 | 0 | 0 / 0 |

The strongest finding is co-adaptation. Seed 2's same AND definition helped the
always-enabled trained policy (101 → 91 when masked) but harmed the probed trained
policy (94 → 117). It is not an intrinsically good or bad definition independent
of its coefficient, surrounding weights and learning history. The nearly zero
online estimate did not clearly identify this large final-policy effect. The
online estimate averages earlier adaptive outcomes; final ablation tests the
final policy on different development positions. Neither can replace the other.

**117/128 is an offline ablation result, not a new autonomously achieved score.**
Do not hard-remove the condition from the learner because an offline evaluator
found that result, or claim the network learned that removal decision.

## Confirmed capability and limits

The internal permission terminal and local outcome recorder work: the graph
decides and acts, ordinary weights remain plastic, disabled branches receive no
participation credit, and all assigned actual rewards enter retained history.
Generic fixtures distinguish a useful AND from irrelevant success correlation.
No coach-side move labels, graph decisions or hypothetical rewards were added.

This is a working measurement mechanism. It is not a useful automatic structural
selection policy yet. The signal does not influence nomination, retention or
pruning in this implementation. Its short, aggregate chess estimates did not
establish reliable usefulness discrimination, and the 50% schedule reduced final
performance. Do not promote that rate or turn these estimates into maturity.
No retirement occurred at this horizon; lifecycle cleanup was unit-tested.
Learned handover and general growth regulation remain separate open targets.

## Follow-up recovery protocol (now completed)

The matched follow-up is complete; see [TRIAL_RECOVERY.md](TRIAL_RECOVERY.md).
Recovery was partial, and ordinary lifecycle turnover occurred. The current next
target in that document isolates edge learning from that turnover. The protocol
below is retained as the pre-outcome rationale, not an instruction to rerun it.

Keep the always-enabled live TRIAL as the work-track reference and retain this
probe as an explicitly experimental option. Do not add an automatic retention
controller on this evidence. First test whether the observed damage recovers
through ordinary play:

1. Reproduce the same prefix and probing interval, then add one predeclared
   128-action interval with probing ended and normal trial access restored.
   All ordinary learning remains active. Apply the same total experience budget
   to the no-addition and always-enabled controls.
2. Record actual outcomes by phase. Evaluate and ablate only after the fixed run.
   Do not enable/disable a candidate from offline scores. The current mechanism
   already stops random gating after its declared window.
3. Keep the ordinary lifecycle unchanged and report any natural pruning/rebirth
   in the longer run. That makes this a recovery test of the complete learner,
   not an isolated causal claim about edge plasticity alone.
4. Before running, declare the full move/time budget and source identity again.
   This is a new experiment, not an automatic extension of the completed run.

If recovery occurs, it shows that the probe's cost was at least partly transient;
it still does not validate a usefulness-driven growth law. If it does not, inspect
the ordinary credit/opportunity problem before adding further machinery. Any
later estimator needs attention to recency, context and sample efficiency while
preserving historical evidence. Merely reducing the disable rate trades lower
interference for fewer control observations; it is not a free accuracy fix.
