# One live TRIAL: protocol declared before outcomes

This experiment extends `codex/residual-shadow-nomination`. The original shadow
class remains isolated. `TrialDevelopment` tests whether one internally nominated
definition can enter actual action selection with its history intact. It does
not implement general growth regulation, maturity or strategic handover.

## Mechanism and information boundary

Only terminal predicates read the typed feature port. The formal graph selects
and executes a legal binding. The opaque M1 coach supplies the submitted action's
scalar result (+1 actual mate, -1 otherwise), bound to event and action. There is
no mate oracle in the learner, after-state scoring, move label or coach inspection
of a graph. Offline comparison and ablation are explicitly scientific controls.

The 64 random shadow definitions use the existing generic AND/OR/exactly-one XOR
grammar; there is no marginal usefulness prerequisite. Discovery ends after 64
actual actions; the existing residual ranking and matched random nomination are
retained unchanged. All actor and shadow coefficients continue learning through
episode 128. Then the organism makes one attachment decision from its own history.

The selected definition, original support/residual record and signed coefficient
are preserved. The coefficient initializes the live shared SUR weight; live
participation statistics start empty and remain separate from prediction history.
There is no double update: all shadow requests and updates stop in every arm
after episode 128. The attached condition uses ordinary actor credit and pruning,
stays TRIAL, and shares a single weight across separate action-binding replicas.
Its tombstone retains history if retired. A collision with an existing or retired
definition is reported without substitution. There is one lifetime attachment;
no automatic replacement or promotion.

The ordinary random-birth budget is 32 shared definitions; this experiment adds
one explicit trial slot (at most 33 live definitions). It does not change the
baseline birth law or require the actor to fail before a young trial can act.
At this horizon no condition is old enough for normal age-based retirement, so
retirement continuity is a unit-tested mechanism, not an actual-play result.

## Fixed actual-play comparison

- Seeds: 1, 2, 3, following up the already viewed shadow development run.
- Roles per seed: no addition, ranked nominee, matched random nominee. The random
  pool includes the ranked winner. Identical nominees are retained and reported.
- Each role independently replays the same 128-action prefix, then trains for
  128 further actions on the same scheduled exercises. All actor weights remain
  plastic. Prefix behavior and retained shadow history must match across roles.
- Each final actor plays the existing 128-position development validation pool
  with learning and exploration disabled. For ranked/random, a separate clone
  also plays those positions with only its trial contribution set to zero.
  This ablation measures immediate dependence after training, not what training
  would have learned without the trial. The no-addition role is that control.
- Primary comparison: final validation mates, ranked minus none, random minus
  none, and ranked minus random per seed. Secondary: suffix training mates,
  orbit-macro success, paired ablation outcome changes and action changes.
- Budget: 2,304 training moves (including repeated common prefixes), 1,152 normal
  validation moves, 768 ablation moves: 4,224 actual moves total. Three seed workers,
  at most 1,200 seconds per seed. No automatic extension, extra seed or tuning.
- Missing/colliding nominees remain in results. Ablation is a no-op if there is no
  live trial. A timeout/error preserves the manifest and writes an incomplete
  result; there is no partial success summary.

Use the existing `m1-coach-smoke-pool`: train hash
`6007840a71af73552e78ca3a272ce0af1b4639258246b39fa578f842a5a2a8f2`,
validation hash `dd92f3740e916f89665f459f9165088bac563a465c8bd803404a241f48798c2e`.
Require disjoint training/validation symmetry orbits. The final test stays closed.
The runner writes source hashes, configurations, candidate plans, exercise order
and budgets before play. Publish only aggregate reports, anonymous outcome rows,
random structural definitions and digests, not trained weights/checkpoints or
raw board/action transcripts.

## Interpretation agreed in advance

Attachment affecting a graph-selected action demonstrates a live developmental
connection. Better training/validation in one seed is not reliable adaptive
growth. The ranked method needs repeated advantage over random and no addition
before claiming a useful discovery policy. A harmful attachment is retained in
the report; predictive residual fitting does not establish causal action value.
Fixed schedules/rates are experimental controls, not a permanent training recipe.

## Implementation and verification

Implementation/protocol commit:
[`3e9d236e`](https://github.com/Paulander/hector-recon/commit/3e9d236e8a2b2ded2e7e8c6d2e9212bfa24ff412).
The learning mechanism is in a separate generic subclass. The coach,
base actor, residual shadow learner and formal engine were not modified for this
experiment. The remaining new code is the runner and focused mechanism tests.

128 distinct focused tests passed: 127 in the full selected regression run, then
the corrected action-change fixture. The initial fixture failures were integer
zeros assigned to float weights and an incorrect tie-break expectation; both
were test corrections, with no change to the learner or declared experiment.
New coverage includes attachment timing, signed weight/history continuity,
AND-dependent action changes, shared weights across new bindings, no duplicate
shadow credit, rejection of invalid outcomes, checkpoint continuation, retained
pruning tombstones, terminal-only chess interaction, opaque coaching, read-only
ablation, exact actual-move counts and serial/parallel parity. Test-only planted
nominees isolate attachment semantics; the chess experiment generates and selects
its nominees internally from actual training history.

Reproduce with Python 3.12, chess 1.11.2 and numpy 2.3.5:

```bash
PYTHONPATH=src:libs/recon-lite/src python scripts/autogrowth/run_live_trial.py \
  --pool reports/autogrowth/runs/m1-coach-smoke-pool \
  --output reports/autogrowth/runs/live-trial-seeds123 \
  --seeds 1 2 3 --conditions 32 --candidates 64 \
  --discovery 64 --after-episode 128 --suffix 128 --min-support 4 \
  --workers 3 --wall-seconds 1200
```

Use a new output path for an intentional reproduction; the runner will not
overwrite an existing run. The script sets deterministic hash/thread defaults.

## Completed result: 2026-09-06

All 4,224 planned actual moves completed within the original budget. All six
additions attached, stayed TRIAL, and received ordinary actor learning. Every
128-action prefix reproduced the earlier shadow experiment's complete
action/outcome digest and shadow history. No shadow history changed afterwards.
No final-test positions were read. The full public record is
`reports/autogrowth/development/LIVE_TRIAL_20260906.json`.

Final greedy development validation, out of 128 positions / 25 symmetry orbits:

| Seed | No addition | Ranked | Random | Ranked minus random |
| --- | ---: | ---: | ---: | ---: |
| 1 | 126 | 126 | 128 | -2 |
| 2 | 93 | 101 | 101 | 0; identical nominee |
| 3 | 66 | 66 | 66 | 0 |

The suffix training scores, out of 128 actual moves, were respectively
103/102/103, 86/92/92 and 45/45/45 in none/ranked/random order. These are different
exercises from the prefix; their raw rates are not a matched before/after test.

Offline masking of only the new condition's final contribution:

| Seed / role | Normal → masked mates | Actions changed | Mates lost / gained when masked |
| --- | ---: | ---: | ---: |
| 1 ranked | 126 → 126 | 0 | 0 / 0 |
| 1 random | 128 → 124 | 4 | 4 / 0 |
| 2 ranked | 101 → 91 | 54 | 32 / 22 |
| 2 random | 101 → 91 | 54 | 32 / 22 |
| 3 ranked | 66 → 66 | 0 | 0 / 0 |
| 3 random | 66 → 66 | 0 | 0 / 0 |

Seed 2's two-reader AND condition was the same in ranked and random; their actual
suffix action/outcome digests and all evaluation/ablation results were identical.
This is one useful composition, not two independent confirmations. It tests
`target_aligned_black_king_file == false AND kings_aligned_file == false`.
Those literals came from the random grammar and their credit from actual play;
this description is an interpretation after learning, not a supplied chess plan.
The experiment does not prove that those two inputs were individually useless,
that an atomic model could not learn an alternative, or that an opposition
strategy has been discovered. The zero-marginal-signal Boolean fixture is separate
mechanism evidence from the prior shadow tests.

Seed 1's useful random condition was a single reader at
`target_white_king_file_distance == 2`. In its final policy it supported four
otherwise missed mates, but its training trajectory improved only two mates over
the no-addition actor. Other weights adapted differently during training. Do not
equate immediate ablation dependence with the benefit of adding a node to a
learning system.

There is no reliable ranking advantage: ranked never beat random here. The
successful seed 2 condition participated in 4 positive and 13 negative outcomes.
Negative outcomes must not simply mean discarding a condition: signed weights can
learn to discourage actions. Conversely seed
3's ranked condition participated in 35 positive and 2 negative outcomes, yet
masking it changed no validation actions. Neither activation nor positive
correlation establishes marginal value. Zero ablation effect on this pool also
does not prove a condition is useless in every context or throughout training.

All arms ended with 32 baseline conditions; additions ended with 33. Physical
counts (including disconnected, now inactive shadow nodes) were 1,548–1,751
vertices and 4,190–4,776 edges. These are replicas across action bindings, not
thousands of independent learned concepts. There was no age-based retirement at
this horizon. No consolidation-retention, general growth regulation, full M1/KRK
mastery, learned world model or strategic handover claim follows.

## What changed and the next bounded target

The new capability is the complete connection from internally acquired candidate
history to a live formal graph contribution that keeps learning from actual
outcomes. It can help on other training-disjoint development positions, including
through a two-reader composition. This closes the previous shadow-only gap. The
coach still has no graph access, action scorer or correct-move labels. The fixed
trial schedule and random proposal grammar are generic experimental mechanisms,
not a discovered general developmental policy.

The remaining weakness is deciding which additions actually contribute. Do not
respond by adding more node types, declaring maturity from correlations, or
freezing the actor. The next proposed implementation is a small **internal trial
usefulness signal from randomized actual use**, before automatic retention:

1. In a bounded TRIAL window, make an internal random decision before action
   selection to enable or disable that trial's contribution for the episode.
   The graph still selects and executes the move. The coach returns its ordinary
   actual scalar result; it never reads or sets the intervention.
2. Preserve the assignment, actual eligibility and both favorable/unfavorable
   outcome records locally. Only eligible enabled contributions receive ordinary
   credit. Keep the rest of the actor plastic. No virtual/alternative move gets
   a reward, and disabled observations must not be fabricated as participation.
3. First test this generic signal with a useful AND fixture and a correlated but
   decision-irrelevant fixture. Test outcome binding, frozen evaluation, retained
   history and continued base learning. Random use measures the effect of access
   at the current learning stage, not the lifetime causal value of a topology.
4. Then predeclare one matched M1 comparison against this unchanged residual
   method and random control. Keep sample/resource budgets fixed and include a
   continued-learning baseline. Sparse or inconclusive evidence stays uncertain;
   do not add an automatic maturity/retirement threshold in the same change.

This target is proposed, not implemented or confirmed. It should earn a behavior
benefit before driving a growth-rate regulator. A separate tiny independently
trained two-child competence/delegation experiment can proceed without waiting
for perfect structural discovery; strategic handover is still unimplemented.
