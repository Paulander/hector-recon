# Ordinary M1 continuation: protocol before outcomes

Branch: `codex/residual-shadow-nomination`, from `3c8fe39d`.
The [fixed-topology comparison](FIXED_TOPOLOGY_RECOVERY.md) did not improve any
final score. Each actor had only 384 training decisions. This experiment asks
whether another 640 ordinary decisions improve the same always-enabled actors.
It changes no reward, feature, graph chooser, nomination, credit or lifecycle law.
No claim that more experience must solve the remaining problem is assumed.

## Fixed design

- Seeds 1, 2, 3; roles no addition, ranked, random. No new probing or fixed mode.
- Inherit the previous actor/shadow configuration and first 384 scheduled
  positions exactly: base budget 32, 64 candidates, 64 discovery actions,
  minimum support 4, attachment at 128, separate exploration stream after 256.
- Reproduce prefix/comparison/recovery transcripts, episode-256 state, and the
  new normal episode-384 state, development outcomes, ablations and history.
  A mismatch stops the comparison; historical answers never enter the actor.
- Continue to exactly **1,024 training decisions per actor**, with normal birth,
  pruning and edge learning active. The same training pool is reshuffled by the
  existing seeded schedule. The coach remains unchanged and opaque.
- Evaluate the same 128 development rows only at 384 and 1,024. At each endpoint,
  ablate the trial coefficient on an offline clone in each addition role. No
  intermediate score selects a checkpoint, pruning decision, rate or action.
- **9,216 training + 2,304 normal evaluation + 1,536 ablation = 13,056 nominal
  actual moves.** Three seed workers; **3,000 seconds per seed**, fixed before
  outcomes. No automatic retries, extra seeds or endpoint extensions.
- Use the previous 256 training rows and disjoint development symmetry orbits.
  Final-test rows stay unopened. Reused development data cannot establish sealed
  mastery. Equal seed 2 nominees/trajectories are not independent replications.

The committed reference is
`reports/autogrowth/development/FIXED_TOPOLOGY_RECOVERY_20260907.json`.
Its file hash, source/runtime, pool hashes, inherited definitions/configuration,
full new schedules and budgets are recorded in the manifest before play.
The runner refuses different reference code, runtime dependencies or pools.

Primary outcome: episode-1,024 minus episode-384 development mates for every
seed/role. Also report orbit coverage, paired errors, training counts by fixed
block, lifecycle changes, trial survival and final-policy ablations. Improved
no-addition performance is not a benefit of residual nomination. No consistent
improvement would motivate a representation/credit investigation; it is not a
reason to insert chess strategies or correctness labels into training.

## Private checkpoints and interruption

Checkpoints contain the opaque organism and its schedule/progress together.
They are saved after 128, 256 and 384 training decisions, after fixed evaluations,
and every further 128 decisions through 1,024. Payloads are immutable compressed
pickles; an atomic pointer references a fully written, hashed payload. Old
boundaries remain available. Save requires completed action-bound feedback.
Before continuing beyond 384, every actor is actually reloaded from its checkpoint
and its learned-state digest is checked. Serialization supplies no new experience.

Resume validates the experiment/source/runtime before unpickling, checks payload
transport and progress, and preserves both random streams, shared weight objects
and hypothesis evidence. Only load trusted checkpoint files from this workflow.
Private state is stored separately from public aggregates and excluded from git.
It is not an external action selector or an additional training input.

Each seed's original absolute deadline persists. Paused time counts against that
cap; `--resume` does not grant more time. This is intentionally conservative for
this bounded experiment. A private checkpoint can support a separately declared
future study even if this experiment's cap has expired; it cannot silently extend
this experiment or become its claimed fixed endpoint.

Create `STOP` in the public run directory to pause at a completed work boundary;
remove it and use `--resume` to continue within the original cap. An abrupt
interruption may require replaying the uncommitted unit. The runner retains the
pending unit and reports the possible extra actual moves separately, rather than
subtracting wasted play from history. A committed evaluation can recover its
public record without replay. Completed seeds can be restored without new play.
A seed lock prevents simultaneous writers; after an abrupt process death, remove
that lock only after confirming the previous worker has stopped.

A complete uninterrupted run has exactly 13,056 actual moves. A resumed run with
uncommitted work reports lower/upper bounds including the possible replay overhead.
Failure records remain in place. A paused or failed run cannot publish a complete
summary. No time cap is reset and no score chooses whether to retry.

## Run and verification

Python 3.12, chess 1.11.2, numpy 2.3.5; launcher fixes `PYTHONHASHSEED=0` and
defaults native-library thread counts to one.

```bash
PYTHONPATH=src:libs/recon-lite/src python scripts/autogrowth/run_ordinary_m1.py \
  --pool reports/autogrowth/runs/m1-coach-smoke-pool \
  --reference reports/autogrowth/development/FIXED_TOPOLOGY_RECOVERY_20260907.json \
  --output reports/autogrowth/runs/ordinary-m1-seeds123 \
  --private snapshots/autogrowth/ordinary-m1-seeds123 \
  --seeds 1 2 3 --episodes 1024 --continuation-block 128 \
  --workers 3 --wall-seconds 3000
```

Both output directories must be fresh; use identical arguments plus `--resume`
only for an interrupted/paused invocation. Main receives summaries and guidance;
the new runner remains isolated on the experimental branch.

Run `tests/autogrowth/test_ordinary_m1.py` and the existing focused suite in
`AGENTS.md` before the experiment. New checks cover actual move accounting and
closed final-test access, terminal-only measurements, exact historical anchors,
clean resume and shared trial evidence, interrupted-block replay accounting,
recovery of committed output, unchanged expired budgets, completed-seed recovery,
serial/parallel parity, source/transport checks before unpickling, atomic pointer
preservation and rejection of pending feedback.
