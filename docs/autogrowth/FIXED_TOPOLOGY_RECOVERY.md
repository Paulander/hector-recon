# Fixed-topology recovery: protocol before outcomes

Experimental branch: `codex/residual-shadow-nomination`, from `57b7d67e`.
The previous [normal recovery](TRIAL_RECOVERY.md) mixed edge learning with
10–14 retirements and 9–13 random replacement births per actor. This comparison
asks whether holding those shared condition definitions changes recovery while
ordinary edge credit remains active. It adds an isolated laboratory control;
the production learner, original experiments, coach and formal engine stay intact.

## Matched design and the random-stream confound

The current base learner uses one RNG for both exploration and random births.
Simply suppressing births would shift later exploration draws, so the previous
completed recovery is insufficient as the primary normal-lifecycle control.

Reproduce the same first 256 actions separately for each seed and role. At that
fixed boundary, clone each organism into normal and fixed modes. Both modes use
an identically seeded, separate internal exploration stream during recovery;
birth proposals retain the original structural RNG. This reuses the existing
exploration terminal and graph chooser, without introducing an external action
selector. Completed-prefix RNG/weights/history remain exactly reproducible.

The new normal recovery deliberately has a different exploration stream from
the old run. Compare **new fixed versus new normal**. Old final scores are
historical context; their changes cannot be attributed solely to topology.
The paired recovery streams must end in the same state: in M1 both actors see
the same exercises and legal catalog sizes regardless of the previous outcome.
This matching argument does not automatically extend to multistep episodes.

Fixed mode suppresses birth and pruning only after the shared boundary. Outcome
256 includes its ordinary lifecycle operations; the first held feedback is 257.
It retains all live and retired condition identities/definitions and evidence.
Participating edge learning, bias learning, ordinary bias consolidation,
exploration and normal trial access remain active. This jointly holds retirement
and replacement; it does not separate their effects or implement learned rates.

"Fixed topology" means fixed shared learned definitions, not a fixed number of
physical binding replicas. A newly encountered legal binding slot may instantiate
the same definitions with the same weight objects. Restricting legal actions or
supplying a precomputed maximum binding catalog would change the question.
Existing additions begin with 33 conditions, versus the base budget of 32; normal
replacement uses that base cap. Retaining this extra definition is part of the
intervention, not an unnoticed equal-capacity claim.

## Fixed resources and outputs

- Seeds 1, 2, 3. Five roles: none, ranked, random, probe_ranked, probe_random.
- Same base budget 32, 64 shadow candidates, 64 discovery actions, minimum
  support 4, attachment at 128 and 128 comparison/probe actions at probability
  0.5. Then 128 normal-access recovery actions per mode. No extra probing.
- Each final actor has 384 actions of training experience. Shared prefixes are
  played once per role and cloned; copied history is not additional real play.
- **7,680 actual training moves + 3,840 normal validation moves + 3,072 offline
  coefficient-ablation moves = 14,592 actual moves.** Three workers, one per seed;
  **2,400 seconds per seed**, fixed before outcomes. No automatic extensions,
  extra seeds or score-dependent parameter changes.
- Use the same 256 training and 128 development rows, with disjoint symmetry
  orbits. Train SHA256 `6007840a71af73552e78ca3a272ce0af1b4639258246b39fa578f842a5a2a8f2`;
  development SHA256 `dd92f3740e916f89665f459f9165088bac563a465c8bd803404a241f48798c2e`.
  The final test remains unopened. Reused validation is development evidence.
- Write schedules, candidate definitions, source hashes, pool hashes and limits
  before play. Save every completed mode immediately; incomplete attempts retain
  their evidence but cannot produce a complete summary. No published trained
  weights/checkpoints or raw boards/actions.
- For each pair report all phase training counts/digests, boundary and final
  lifecycle, fixed-definition and weight-change checks, matched exploration,
  frozen probe history, final development outcomes and offline trial ablations.
  Evaluation never supplies learning feedback or chooses retention.

Primary outcome is fixed-minus-normal development mates within every seed/role.
Report the full table, recovery training outcomes, probe-versus-always differences
within each mode and final-policy ablations. Equal nominees/trajectories are not
independent confirmations. Fixed-mode improvement would implicate lifecycle
turnover in these runs; fixed-mode failure would show that holding topology alone
is insufficient. Neither establishes adaptive growth, usefulness-based retention,
world modelling, strategic handover or M1 mastery. A harmful final coefficient
can coexist with beneficial earlier participation; no offline removal becomes a
coach instruction or autonomous achievement.

## Reproduction and tests

Use Python 3.12, chess 1.11.2 and numpy 2.3.5:

```bash
PYTHONPATH=src:libs/recon-lite/src python scripts/autogrowth/run_fixed_topology_recovery.py \
  --pool reports/autogrowth/runs/m1-coach-smoke-pool \
  --output reports/autogrowth/runs/fixed-topology-recovery-seeds123 \
  --seeds 1 2 3 --conditions 32 --candidates 64 --discovery 64 \
  --after-episode 128 --window 128 --recovery 128 --probability 0.5 \
  --min-support 4 --workers 3 --wall-seconds 2400
```

Run the focused suite in `AGENTS.md`, including the two new fixed-topology test
files, before actual play. Tests cover the precise boundary, real weight/choice
changes under a hold, independent structural and matched exploration randomness,
feedback/checkpoint integrity, shared binding weights, terminal-only access,
prior-prefix equivalence, serial/parallel parity, actual move accounting, closed
final test and preservation of completed mode evidence after a later failure.

## Implementation verification

Implementation/protocol commit: `f847e878f3c172b5229957d9af393f74e4ef8751`.
Before the declared run, 169 distinct focused tests passed: 157 existing
regression checks, seven new control checks and five new experiment checks.
The weight/choice fixture demonstrated an actual action change under fixed
definitions and reward learning; the accelerated lifecycle fixture demonstrated
normal turnover with matched exploration despite different structural RNG states.
These are test-side fixtures, not planted conditions in the chess experiment.

## Completed comparison: 2026-09-07

All **14,592 actual moves** completed in one attempt: 7,680 training, 3,840
development evaluation and 3,072 offline ablation. Seed times were 2,366.284,
2,171.301 and 2,260.578 seconds; none exceeded the unchanged 2,400-second cap.
The complete aggregate, protocol manifest and source/artifact hashes are in
`reports/autogrowth/development/FIXED_TOPOLOGY_RECOVERY_20260907.json`.

All 15 episode-256 action/outcome histories and learned-state digests reproduced
the previous experiment. All 15 recovery pairs had matching exploration streams;
all 15 fixed arms retained their shared definitions and changed their weight
records. All 12 post-recovery probe reports reproduced their original evidence.
All 54 evaluations, including ablations, preserved learned state. The final test
stayed closed. Each final actor has 384 actions of training experience; cloning
the shared prefix did not add actual moves.

Development mates out of 128, **new normal / fixed topology**:

| Seed | No addition | Always ranked | Always random | Probed ranked | Probed random |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 124 / 124 | 128 / 126 | 128 / 128 | 124 / 122 | 128 / 128 |
| 2 | 121 / 116 | 98 / 98 | 98 / 98 | 98 / 98 | 98 / 98 |
| 3 | 66 / 66 | 66 / 66 | 66 / 66 | 66 / 66 | 66 / 66 |

Holding topology fixed improved zero pairs, tied twelve and worsened three.
These are descriptive comparisons, not fifteen independent replications:
ranked/random chose the same seed 2 nominee and produced matching trajectories
within each always/probed pair. The results do not support a blanket topology
hold as a repair for recovery. They do not prove the current random replacement
law is optimal, sufficient or experience-guided structural discovery.

Normal turnover retired 11–15 definitions and produced 10–15 replacement births
per arm. All normal populations ended at 32 live definitions. Fixed populations
retained 32 without addition and 33 with addition. All 24 added-trial instances
survived and stayed TRIAL, including the harmful probed seed 2 instances. Existing
tombstones/history were retained. Weight-record digests include live identities;
their change proves coefficient adaptation in fixed mode, while changes in normal
mode can also reflect turnover.

Equal totals can hide behavior differences. Seed 1's no-addition fixed policy
lost four previously solved rows and gained four others; its fully solved orbit
count fell from 24 to 23 despite both scoring 124. Four seed 3 pairs changed action
digests but kept identical outcome rows. Every seed 3 actor solved zero of the 25
development orbits completely. Keeping topology fixed did not remove that plateau.

## What the control separates

Continued edge learning can improve actual chess behavior without new definitions:
seed 2's no-addition policy rose from its reproducible episode-256 score of 93 to
116 under the hold; normal turnover reached 121. That does not make more training
uniformly beneficial: seed 1's no-addition policy fell from 126 to 124, and seed 3
remained at 66. This experiment cannot yet distinguish undertraining from a
representation, nomination or credit limitation.

The seed 2 probed policy remained at 98 with or without turnover. Offline masking
its trial reached 116 in both modes: 32 actions changed, seven mates were lost
and 25 gained. Thus that final-policy harm persists even when no definition is
retired or born. The same definition helped the always-enabled policy in both
modes (98 to 94 when masked: 54 changed actions, 29 mates lost and 25 gained),
while the independently trained no-addition actor reached 121/116. Current-policy
dependence and the effect of an addition on learning remain distinct.
**116 from masking is an offline result, not learned removal or an autonomous
probed-policy score.** The no-addition fixed actor's separate 116 is an actual
trained-policy score; these must not be conflated.

Seed 1 further illustrates context dependence: its ranked trial had no ablation
effect in normal mode, but masking cost two mates in fixed mode, both always and
probed. Masking its random trial cost four mates in all four corresponding modes.
All seed 3 trial ablations had zero action effect. Full outcomes and ablations
are retained in the aggregate; no score was used to alter training or retention.

Separating exploration randomness also changed some new normal scores relative
to the old shared-RNG recovery (for example, seed 2 no addition: old 115, new 121).
That is why the old final scores were historical references, not this control's
primary comparator. The shared prefix was still exact. Separate random streams
improve the comparison's attribution; this is not evidence that a shared RNG was
a chess-specific scaffold or itself an invalid learner.

## Continuation decision

Keep ordinary birth/pruning and always-enabled learning as the work-track
reference. Do not promote the topology hold, 50% probing or a usefulness-based
retirement controller. Neither a lifecycle defect nor a credit defect is
established strongly enough here to justify guessing a new rule.

The next bounded target is **substantially more ordinary M1 play with private,
resumable checkpoints**, before adding another mechanism. Each actor has seen
only 384 training decisions. Aim at a fixed 1,024-decision endpoint for the three
no-addition/ranked/random references in seeds 1, 2 and 3. Preserve current
parameters and normal lifecycle, reproduce these new normal episode-384 records,
and retain the separate recovery exploration stream. Do not repeat half-time
probing merely to rescue it. Declare the exact schedule, checkpoints, resources
and evaluations before that future run; this completed run is not extended.

Required implementation checks: checkpoint/resume must preserve actions, reward
history, random streams, hypothesis identities and shared weights; the coach must
remain opaque; evaluations must be read-only; interruption must retain complete
earlier checkpoint evidence without claiming the final endpoint. Keep trained
weights private and publish aggregate outcomes/hashes only. Use fixed evaluation
endpoints, never the best observed checkpoint, to decide whether more experience
helps across seeds. Failure to improve is evidence to retain and then use to
target the representation/credit question, not permission to insert chess advice.

The tiny independently trained two-child competence/delegation task remains a
separate planned capability. It need not wait for perfect structural discovery.
No result here demonstrates learned handover, a competence envelope, a world
model, reliable M1 mastery or M2/KRK. This experiment provides an attribution
result and a tested control, not a new autonomous developmental policy.
