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
