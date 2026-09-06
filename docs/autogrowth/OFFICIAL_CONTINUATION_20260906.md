# Official continuation: terminal ReCoN restart

Status: accepted 2026-09-06. `main` is the official continuation line after the
promotion commit containing this record. Earlier branches and reports remain
provenance and a parts library, not active specifications.

## Decision

Continue from the terminal M1 substrate introduced at `e3900df`. Reset the active
scientific claims. We are not carrying forward a claim that the project already
solved autonomous topology development, KRK or strategic handover.

The current baseline is useful because its complete observation-to-action path is
clean enough to develop from:

```text
board owned by environment
  -> declared feature measurements through input terminals
  -> Boolean SCRIPT confirmations and plastic SUR contributions
  -> formal graph action choice
  -> output terminal executes that binding
  -> coach returns the submitted action's scalar outcome
```

The previous instance reviewed the exact implementation and found no hidden mate
solver or coach-side action selection. It accurately characterized the learner as
a formal ReCoN action graph implementing a random Boolean-feature contextual
bandit over a strong, explicitly supplied KRK state-action geometry.

That is the baseline, not the destination.

## Accepted corrections before promotion

- Rename the root from `goal` to `action_choice`; confirmation means selection,
  not success or competence.
- Keep randomly proposed conditions in TRIAL. Activation count and correlation do
  not nominate them for PROBATION.
- Retain tombstones and evidence for pruned hypotheses so identical conditions do
  not silently return with erased history.
- Limit checkpoint source identity to the actual clean runtime dependency set,
  excluding unrelated historical autogrowth runners.
- Treat fast-to-slow transfer as behavior-neutral bookkeeping until retention is
  demonstrated.
- Describe terminals as individually sparse while acknowledging that the first
  run covered 70 of the 80 possible atomic literals.
- Report 3,385 physical vertices as replicas of 166 shared definitions: 96
  conditions plus 70 readers, across 20 action-binding slots.

The exact trained artifact remains reproducible at `e3900df`. The semantic fixes
change runtime source identity, so that historical checkpoint is analyzed with
its original commit rather than resumed under the corrected baseline.

## Bounded evidence retained from the engineering run

At `e3900df`, 182 real M1 moves with scalar outcomes improved the viewed
development validation from 4/128 to 124/128. This establishes an engineering
result for terminal-mediated weight learning on the supplied representation.

Read-only interventions on the same checkpoint and 25 development symmetry
orbits produced:

| Arm | Rows mated | Orbits with every row mated | Orbits with any row mated |
| --- | ---: | ---: | ---: |
| No-op clone | 124/128 | 24/25 | 25/25 |
| Multi-reader condition weights zeroed | 75/128 | 6/25 | 25/25 |
| All condition weights zeroed | 4/128 | 0/25 | 4/25 |

Thus learned condition contributions drove the result, and multi-reader
compositions materially affected behavior. The structures themselves were
randomly proposed, so this does not establish experience-directed topology
growth. The report is
`reports/autogrowth/development/TERMINAL_M1_WEIGHT_ABLATION_20260906.json`.

The training pool contains only positions where M1 exists, and the organism has
no abstention action. It has therefore not learned an M1 availability or
competence envelope suitable for handover.

## Promotion scope

The previous `main` at `2b8642c0` was an ancestor of the candidate: zero commits
were unique to `main`. Promotion deliberately fast-forwards the complete branch
history, including the large historical `reports/` and `archive/` trees. Those
files remain provenance; their presence on `main` does not make them active
instructions or current evidence. The previous main tip and the exact e3900df
engineering baseline are preserved as named archival branches.

## Next decision sequence

The next implementation track is `codex/residual-shadow-nomination`. Main remains
the stable baseline while that experiment is developed. See
[LEARNING_SEQUENCE.md](LEARNING_SEQUENCE.md) for mechanism order and the distinction
between experimental controls and continuous learning in a future competent agent.

### Separate branch status: completed residual-shadow experiment

The first shadow-only implementation and results were recorded on
`codex/residual-shadow-nomination` at
[`e55bfd88`](https://github.com/Paulander/hector-recon/commit/e55bfd88ab273f6d30c16ddf694893a2ef80f458).
Read the [branch experiment and continuation instructions](https://github.com/Paulander/hector-recon/blob/e55bfd88ab273f6d30c16ddf694893a2ef80f458/docs/autogrowth/RESIDUAL_SHADOW_NOMINATION.md)
before resuming. Main has summaries and architecture guidance only; it has not
adopted the experimental learner hook or shadow implementation.

The generic mechanism nominates from random terminal/SCRIPT candidates using
residuals from actual action-bound rewards. Candidates read only the selected
binding, remain disconnected from the actor, and commit predictions before later
outcomes score them. Both actor and shadow weights continue learning.

Verification: 111 distinct focused tests, including useful joint signal with zero
marginal atom signal, reward-dependent nomination, terminal-only observations,
opaque coaching and serial/parallel reproducibility. Six runs completed 768 real
moves. For every seed, shadows preserved the full action/outcome digest and final
learned actor state. Neither validation nor final-test positions were opened.

Across seeds 1/2/3, ranked versus random prospective MSE reduction was +0.027642,
0 (same nominee) and -0.001159. This is a working nomination/evidence mechanism,
not reliable ranking superiority, causal usefulness or live adaptive growth.
Support matching was coarse and subsequent activation counts changed materially
as the actor learned. Do not treat its three-seed mean as confirmation.

This led to the live TRIAL experiment below. Young structures do not require an
established superiority claim before participating in a declared learning trial.

### Previous milestone: completed live TRIAL experiment

Live materialization results commit:
[`16f61e9c`](https://github.com/Paulander/hector-recon/commit/16f61e9ccdf00ba9d17b4512f16cdc48939c7758).
The implementation and predeclared protocol are at
[`3e9d236e`](https://github.com/Paulander/hector-recon/commit/3e9d236e8a2b2ded2e7e8c6d2e9212bfa24ff412).
Read the [live TRIAL mechanism, full results and next target](https://github.com/Paulander/hector-recon/blob/16f61e9ccdf00ba9d17b4512f16cdc48939c7758/docs/autogrowth/LIVE_TRIAL_MATERIALIZATION.md)
and [aggregate record](https://github.com/Paulander/hector-recon/blob/16f61e9ccdf00ba9d17b4512f16cdc48939c7758/reports/autogrowth/development/LIVE_TRIAL_20260906.json).
Main retains its stable learner and records these results only as branch status.

`TrialDevelopment` attaches one internally nominated definition after 128 actual
actions. Its signed weight and original predictive evidence survive attachment;
new live participation records are separate. Shadow requests/updates stop in
every arm. Ordinary graph selection and actor credit continue, with at most 33
live definitions versus the original budget of 32. No coach-side move scorer,
graph inspection, correct-action label or hypothetical reward was introduced.

All 128 distinct focused tests passed, and all 4,224 planned actual moves finished:
2,304 training, 1,152 normal development validation, 768 read-only ablation. The
earlier shadow prefixes were reproduced exactly, including history digests.
Final-test positions stayed closed. Final validation mates out of 128:

| Seed | No addition | Ranked | Random |
| --- | ---: | ---: | ---: |
| 1 | 126 | 126 | 128 |
| 2 | 93 | 101 | 101 |
| 3 | 66 | 66 | 66 |

Seed 2's ranked and random selectors chose the same two-reader AND condition.
Masking its final contribution changed 54 evaluation moves and reduced 101 mates
to 91: 32 mates were lost and 22 gained. This confirms useful live composition in
that policy. It does not establish that the atoms were marginally useless or
that an atomic alternative could not learn the task. Seed 1's random addition
fell from 128 to 124 when masked; its no-addition training control scored 126.
Immediate dependence and the benefit of adding a node during learning differ.

Ranked nomination did not beat random in any seed. Seed 3's ranked trial had 35
positive and 2 negative participations, but zero evaluation action changes when
masked. Do not turn correlation into a usefulness/maturity claim. All additions
remained TRIAL; no age-based retirement occurred. Checkpoint/tombstone continuity
was tested, but long-run retention, automatic regulation, full KRK and handover
were not established.

### Previous milestone: randomized-use probe remains experimental

Implementation/protocol:
[`567dd40f`](https://github.com/Paulander/hector-recon/commit/567dd40f095fec45e0c3c928ac02d7805ef817fe).
Results and continuation:
[`9268b1db`](https://github.com/Paulander/hector-recon/commit/9268b1db37790393a2e879289208f9c1fd7a75c5).
Read the [complete protocol, results and next target](https://github.com/Paulander/hector-recon/blob/9268b1db37790393a2e879289208f9c1fd7a75c5/docs/autogrowth/TRIAL_USEFULNESS.md).
Main has not adopted the new learner code.

An internal leaf terminal randomly permits one TRIAL's graph contribution before
each actual action in a fixed window. Disabled trials receive no action credit;
all assigned outcomes enter the local comparison. The coach remains opaque and
ordinary actor learning continues. The signal is collected but does not select,
retain, mature or prune structures. Generic fixtures distinguish useful AND from
irrelevant success correlation without freezing ordinary bias/edge learning.

All 151 focused tests passed. All 7,296 planned real moves completed: 3,840
training, 1,920 normal development validation and 1,536 ablation. Every old control
record reproduced exactly apart from timing, including action/outcome and learned
state digests. The final test stayed closed. Final development mates /128:

| Seed | None | Always ranked | Always random | Probed ranked | Probed random |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 126 | 126 | 128 | 122 | 126 |
| 2 | 93 | 101 | 101 | 94 | 94 |
| 3 | 66 | 66 | 66 | 66 | 66 |

Half-time probing reduced or matched every corresponding final score. Short
enabled-minus-disabled reward estimates were +0.0694, -0.0049 and -0.0347, identical
for ranked/random within each seed. These did not establish reliable usefulness
discrimination. Seed 1's two probes even had identical actual suffix transcripts
despite different participation counts and final validation.

Co-adaptation is the strongest finding. The same seed 2 AND definition helped the
always-enabled policy (101 → 91 when masked) but harmed the probed policy
(94 → 117 when masked; 2 mates lost, 25 gained). The online estimate averaged
earlier adaptive outcomes and did not clearly identify that large final effect.
**117/128 is an offline ablation result, not an autonomous score.** Do not have the
coach remove the candidate on that basis or infer a learned removal capability.

Keep the always-enabled actor as the work-track reference. Do not promote 50%
probing, claim reliable causal maturity, or add a retention controller on this
evidence. The separately declared recovery follow-up is complete below. It added
128 normal-access actions with all ordinary learning active and recorded natural
pruning; it does not attribute recovery solely to edge updates. Merely probing
less also gives fewer control observations.
Independent child competence and strategic handover remain separate work.

### Latest branch result: partial recovery with lifecycle turnover

Results/continuation commit:
[`57b7d67e`](https://github.com/Paulander/hector-recon/commit/57b7d67e9f24bfe458459ef965e2c74fd43020f3).
Read the [recovery protocol, complete results and next target](https://github.com/Paulander/hector-recon/blob/57b7d67e9f24bfe458459ef965e2c74fd43020f3/docs/autogrowth/TRIAL_RECOVERY.md)
and [aggregate record](https://github.com/Paulander/hector-recon/blob/57b7d67e9f24bfe458459ef965e2c74fd43020f3/reports/autogrowth/development/TRIAL_RECOVERY_20260906.json).
The runner adds an optional fixed recovery phase and saves each finished arm's
evidence. It changes no learner or coach mechanism. Main receives guidance only.

157 distinct focused tests passed. An execution interruption ended the first
attempt after ten arm summaries, at least 6,016 actual moves plus uncounted
in-flight work. That attempt is preserved as incomplete. The identical retry
completed all 9,216 planned moves within the same 1,800-second per-seed cap.
All 15 episode-256 action/outcome records and learned-state digests reproduced;
all six probe histories remained unchanged, and all ten interrupted-arm summaries
reproduced except timing. The final test stayed unopened.

Development mates before → after 128 further training actions:

| Seed | None | Always ranked | Always random | Probed ranked | Probed random |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 126 → 126 | 126 → 128 | 128 → 128 | 122 → 124 | 126 → 128 |
| 2 | 93 → 115 | 101 → 101 | 101 → 101 | 94 → 98 | 94 → 98 |
| 3 | 66 → 66 | 66 → 66 | 66 → 66 | 66 → 66 |

Some probing costs recover, but no probed arm beats its always-enabled reference.
Seed 2's probed final policy still improves under offline masking, 98 → 113:
35 actions change, 10 mates are lost and 25 gained. Its same AND helps the
always-enabled policy, 101 → 94 when masked, while the separately trained
no-addition actor reaches 115. Current-policy dependence and the benefit of an
addition during learning differ. The masked 113 is not an autonomous policy score.
Ranked/random chose the same candidate in seed 2, with matching trajectories
within each pair; these are not independent confirmations.

Real-play lifecycle behavior is now observed: 10–14 base conditions retired and
9–13 replacements were born per arm, with retained tombstones. All twelve added
trials survived, including the harmful probed ones. Final populations contain
31–32 live definitions: the original 32-condition birth cap does not replenish a
permanent extra slot for the one lifetime attachment. This is actual operation
of the existing lifecycle, not evidence for causally useful pruning or maturity.

**Next bounded target:** isolate edge learning from lifecycle turnover during
recovery. Reproduce the same first 256 actions, then compare the existing normal
lifecycle with a laboratory control that suppresses birth/pruning for the next
128 actions while all edge learning remains active. Predeclare resources and test
the complete boundary. Use the result to choose a credit or lifecycle correction
before a usefulness controller. This is not a permanent freeze or automatic
extension of the completed experiment. The tiny independently trained two-child
competence/delegation task remains a separate next capability; M1/M2 mastery and
learned strategic handover remain unproved.

### Baseline sequence

Progress update: step 1 is complete on main; see
[M1_GROWTH_ATTRIBUTION.md](M1_GROWTH_ATTRIBUTION.md). Random birth added little to
final M1 scores, and mixed-versus-atomic effects varied by seed. Steps 2 and the
single live-TRIAL part of step 3 are complete on the separate branch described
above. Main's production learner is unchanged. Resume the next target above;
do not reimplement the already completed nomination and attachment experiments.

1. Run matched multi-seed controls: online random reveal, the same random
   condition set installed at initialization, and atomic-only representation.
   This attributes gradual birth and nonlinear composition without pretending the
   current random proposal law is adaptive.
2. Port only residual-ranked nomination and shadow comparison from the earlier
   generic composition work. Candidates learn without decision influence, then
   later real outcomes compare prediction with and without them. Match random
   proposals by budget, support and opportunity.
3. Let one nominated TRIAL act and learn with persistent hypothesis history.
   Compare ranked/random/no-addition trajectories and ablate its final live
   contribution. Do not confuse permitting a trial with confirming maturity.
4. Test competence and delegation first in a tiny two-context/two-child task.
   Train children independently from scalar outcomes; let a parent observe only
   typed child-response terminals; compare connected, disconnected and permuted
   responses while preserving child policies.
5. Use the resulting interface for M2: imagined successor contexts may query the
   M1 child, but virtual success never becomes reward. Actual play and final
   observed outcome remain grounding.

The original pause before longer training addressed weak lifecycle claims; it
was not evidence that more experience could not help. Keep edge learning active
and include a continued-training control in growth experiments. The smaller
32-condition work-branch budget is also distinct from the earlier 96-condition
engineering run. Do not compare their raw scores as if only growth changed.

## What “starting over” means

It means one live architecture contract, a clean runtime path and reset claims.
It does not mean deleting correct formal primitives, internal terminals, virtual
frame types, intrinsic eligibility or residual-composition code. Reuse those only
in small pieces after verifying that they obey the current boundary.

Future reports should be short: what mechanism changed, what information it saw,
what actual behavior occurred, which null was tested and what remains unknown.
