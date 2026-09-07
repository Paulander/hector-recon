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

## Completed result — 2026-09-07

Implementation and the protocol above were published before play at
`846ca3d2c956299f77c84b791792ec151d75b344`.
The [public aggregate](../../reports/autogrowth/development/ORDINARY_M1_CONTINUATION_20260907.json)
contains the fixed manifest, full endpoint outcomes, paired comparisons, block
transcript hashes, source identities and private checkpoint transport hashes.

All **181 distinct focused tests passed**: 169 existing and 12 new. During test
development, a tiny resume fixture incorrectly assumed its random candidates
would nominate a trial. The fixture legitimately produced no nomination; that
assertion was corrected, and a separate generic materialized-trial fixture
verified shared weights, preserved hypothesis evidence and later credit after
restoration. No learner change was needed for that test correction.

The declared experiment completed in one attempt with **13,056 actual moves**:
9,216 training, 2,304 normal development evaluation and 1,536 offline ablation.
Each actor received exactly 1,024 training decisions. Seed wall times were
2,126.807, 1,891.990 and 2,005.432 seconds, within the original 3,000-second caps.
No interruption, retry, extension or score-selected checkpoint occurred.

All nine historical anchors matched, including their first three action/outcome
blocks and learned state. Every actor was actually reloaded at 384 before
continuing. All nine frozen shadow histories and paired exploration streams
remained consistent. All 30 evaluations preserved learned state. Offline
verification loaded all 18 evaluated endpoint payloads and matched their reported
state, and checked each completed seed pointer. There are 108 retained immutable
private payloads. The sealed final-test rows remain unopened.

Development mates out of 128, **384 → 1,024 training decisions**:

| Seed | No addition | Ranked addition | Random addition |
| --- | ---: | ---: | ---: |
| 1 | 124 → 124 | 128 → 128 | 128 → 128 |
| 2 | 121 → 124 | 98 → 124 | 98 → 124 |
| 3 | 66 → 66 | 66 → 66 | 66 → 66 |

Three actor totals improved and six tied; these are not nine independent
replications. Seed 2 ranked/random selected the same candidate and reproduced
the same training and evaluation trajectories. They gained 26 mates without
losing any previously solved row. Its no-addition actor gained three without a
loss. Seed 1's unchanged no-addition total hides four gained and four lost rows;
fully solved development orbits fell from 24 to 23. Final fully solved orbits out
of 25 are 23/25/25 for seed 1, 23/23/23 for seed 2, and 0/0/0 for seed 3.

Final-policy ablation (a frozen offline intervention, never training feedback):

| Seed | Addition | Normal → masked mates | Changed actions | Lost / gained mates |
| --- | --- | ---: | ---: | ---: |
| 1 | Ranked | 128 → 128 | 0 | 0 / 0 |
| 1 | Random | 128 → 124 | 4 | 4 / 0 |
| 2 | Ranked | 124 → 88 | 36 | 36 / 0 |
| 2 | Random | 124 → 88 | 36 | 36 / 0 |
| 3 | Ranked | 66 → 66 | 0 | 0 / 0 |
| 3 | Random | 66 → 66 | 1 | 0 / 0 |

Seed 2 now relies strongly on the added AND within its learned policy. This is
current-policy usefulness, not a ranking advantage: the independently trained
no-addition actor reaches the same 124 outcomes. Likewise, seed 1's ranked
coefficient has no final direct effect, although its training trajectory reaches
128 rather than the no-addition actor's 124. Removing a coefficient from a final
policy and training without that condition are different interventions.

Ordinary lifecycle remained active. Between 384 and 1,024, actors each retired
and replaced 16–28 base definitions; all ended with 32 live definitions. All six
added conditions survived and remained TRIAL. Seed 3 changed topology, weights
and training experience without improving its mate outcomes. This rules out a
frozen-topology explanation for these runs, but does not establish why the plateau
persists or that further experience could never help. Neither survival nor these
masking results constitute an implemented autonomous maturity decision.

### What this adds

The experimental actors now have source-bound private checkpoints with tested
interruption accounting and verified continuation. More ordinary play can improve
behavior substantially in some histories, including a policy using a live
composition. Stronger dependence on a condition is not evidence that nomination
reliably outperforms random proposals or the no-addition reference. Adaptive
structural selection, useful retirement, learned competence/delegation, a world
model, M2 and full KRK remain unproved. Main receives documentation only.

## Next bounded target

Use the saved 384/1,024 actors to investigate seed 3's persistent failure, with
seed 2's recovered actors as a reference. Separate two questions: can the current
terminal/gate representation distinguish the relevant alternatives, and does the
existing credit/choice process exploit the distinctions it already has? Inspect
these only in an explicitly offline diagnostic; the coach and ordinary learner
must continue to receive only their existing observations and scalar outcomes.
Any additional real moves require a separately declared budget and endpoint.
Offline answers, fitted weights or selected actions must not become learner
inputs or a deployed policy.

The result should motivate one generic change with a matched control, if a cause
is found: a proposal/composition correction for missing distinctions, or a
credit/choice correction for unused distinctions. Do not presume either defect,
add a retention controller, or silently extend this completed run. Preserve young
joint Boolean trials even when their atoms lack individual value. Test the
smallest correction through actual terminal-mediated play and scalar feedback.
The independently trained two-child competence/delegation experiment remains a
separate capability and need not wait for perfect structural discovery.
