# First combined owner-split and trial-acceptance result

Completed 2026-09-15 under [the fixed protocol](OWNER_SPLIT_TRIAL.md).
**The combined rule lost all three pairs. Keep the existing four-owner
residual/current learner as the reference.** This cohort is CLOSED; no retry,
extension, threshold adjustment or main merge was performed.

This is the explicit integration checkpoint requested by the user: owner-local
weight training and splitting now have an experimental trial-acceptance adapter.
It reuses the existing TRIAL/MATURE enum, local candidate statistics, internal
permission leaf and actual assigned-outcome records. It does not replace or
activate the older permanent pattern-sensor promotion subsystem. A split can
earn MATURE under this declared finite rule; its individual conditions remain
TRIAL and its weights remain plastic. Ordinary condition growth continues.

## Actual result

Fresh networks, seeds18/19/20,1920 training actions per arm. Scores below are
the 16-row Boolean evaluation with no learning/exploration. Pending split trials
use their continuing parent during evaluation: these are committed-policy scores.

| Seed | Current | Combined trial | Current final A/B | Trial final A/B | Accepted / retired unproven / pending trials |
| --- | ---: | ---: | --- | --- | --- |
| 18 | 16 | 12 | 8 / 8 | 8 / 4 | 0 / 4 / 0 |
| 19 | 14 | 12 | 8 / 6 | 4 / 8 | 1 / 4 / 1 |
| 20 | 14 | 12 | 8 / 6 | 8 / 4 | 1 / 4 / 1 |
| Total | **44 / 48** | **36 / 48** | | | **2 / 12 / 2** |

Current seed18 first reaches16 at1216 and holds every later measured checkpoint.
Neither other current seed exceeds14. None of the trial seeds ever exceeds12.
All three trial endpoints exactly follow a single input: x for18/20 and y for19.
The task requires x in A and y in B. A single-input policy solves12/16 but cannot
handle the four cases where the other input is required and x differs from y.

Retaining fewer acquired cases is not a retention improvement:

- Trial18 keeps all eight A640 successes, but its B1280 reference contains only
  four successes. Those stay correct; the other four B cases remain wrong.
- Trial19 keeps all eight B1280 successes but loses A640 rows8/9. It starts that
  retention comparison with only four A successes, versus eight for its control.
- Trial20 had all eight B rows correct at1280 and loses6/7/10/11 by1920.
  Its control retains all six of its B1280 successes.
- Current19 loses boundary B row11 and acquires another B row, retaining the same
  total of six. Current18 has uninterrupted B retention after1280; all current
  arms recover their A640 successes by the endpoint, with some intermediate loss.

The row histories and every measured gain/loss are in
`reports/autogrowth/development/OWNER_SPLIT_TRIAL_20260915.json`.

## What the trial mechanism did

Sixteen splits were nominated: fourteen reached their256-local-request limit,
two remained pending. Twelve were retired as **unproven**, two accepted. Across
the trial arms,3778 real actions had trial assignments;1871 were controlled by
split children and1907 by continuing parents. These are part of the fixed5760
treatment training actions, not extra or counterfactual feedback.

The accepted root splits both test y: seed19 accepts at945 with mean reward
gain0.2522, seed20 at1208 with gain0.1718. Both windows lie in mostly-B exposure.
That is local access evidence under the experienced distribution; it did not
establish retention of the other task context or solve the full Boolean function.

Two concrete rejection cases expose problems in the proposed rule:

1. **Learning time is penalized.** Seed19's child-owner6 c split, born979 and
   resolved1496, had mean reward gain+0.1605. Its first128 requests gave−0.0798
   and its second128 gave+0.3961. Both children had sufficient exposure. The
   requirement for positive benefit in *both* halves rejected it despite its
   later improvement. This is not proof it would remain useful if accepted.
2. **A rare child can be retired just short of support.** Seed20's child-owner8
   c split, born1323 and resolved1835, had gain+0.1344 and positive halves
   (+0.1532,+0.1199). One child had14 actual actions, below the16 minimum, so the
   trial was unproven. At7:1 region exposure and half-time trial access,256 region
   requests yield only16 rare-child actions in expectation. A fixed window ends
   near the support threshold; observed exposure fluctuates.

The rule also bars the same partition from another trial in the same owner.
Retaining evidence is necessary, but this permanent-within-owner exclusion is
stronger than retaining history. It can prevent reconsideration after the scorer
has developed. No rejected split was silently retried or its history discarded.

These findings motivate a smaller follow-up on **when a still-learning or
underexposed trial is assessed, suspended and reconsidered with its history**.
Possible warm-up, later prospective assessment and history-preserving return are
hypotheses, not fixes established by this run. Specify the next isolated change
before testing it; do not lower thresholds to admit these observed examples.

## Acquisition and real costs

Scoring births began at64 in every trial arm, versus444/439/441 in current.
Thus the integration removes the observed initial growth delay, but earlier
births alone did not improve performance. Births total26/23/24 versus24 each;
ordinary age/weight pruning removes1/2/3 conditions versus0/0/1. Trial rejection
is separate from these ordinary condition-pruning counts. Every scored birth
nomination materialized; no ordinary birth was blocked by the parameter ceiling
in this cohort, though temporary alternatives occupied much of it.

| Seed | Current final nodes / parameters | Trial final nodes / parameters | Trial peak nodes / parameters | Current / trial run seconds* |
| --- | --- | --- | --- | --- |
| 18 | 333 / 28 | 145 / 21 | 279 / 29 | 130.8 / 85.2 |
| 19 | 329 / 28 | 497 / 49 | 679 / 61 | 131.8 / 218.1 |
| 20 | 323 / 27 | 611 / 56 | 611 / 56 | 129.9 / 180.4 |

*Per-arm training loop includes immutable recording, checkpoint reloads and
scheduled evaluation, not the final independent verification. These are not
pure learner FLOP timings. The report also includes allocation summed over
training actions, explicitly labeled storage exposure rather than executed FLOPs.

Final trial committed owners are1/2/2; pending trials are0/1/1; stored scorers
are1/4/4. Seed19 peaks at six stored scorers: two committed parents with two
pending binary alternatives. It reserves a possible four-owner partition and
counts all57–61 concurrently stored parameters against the64 ceiling. The
original max-definitions256, nodes2048 and depth4 limits remain in effect.

## Capacity and verification

The final committed graphs of **all three trial arms lack16/16 ranking capacity**.
Current19/20 also lack it; current18 has capacity and actually achieves16.
Five exact nonnegative rational contradictions and one exact rational feasible
witness verify these claims. No fitted weight or diagnostic route was installed.
Capacity concerns these fixed saved graphs, not all possible future growth.
Pending children are excluded from committed-policy matrices, consistent with
the declared evaluation rule. Offline arithmetic reproduces all2976 recorded
evaluation choices, including checkpoints with pending alternatives.

Six new mechanical fixtures and58 focused tests passed. They check score-preserving
independent inheritance, real-action-only credit, invalid-feedback rejection,
irrelevant bias prediction differences, genuine conflicting learning earning
acceptance, continuing growth, history, checkpoint/RNG restoration and atomic
budgets. The old controls and formal engine checks are included.

The study completed11520 training actions,2976 scheduled evaluation actions and
2976 frozen reproductions:17472 environment actions,180 sealed blocks and186
checkpoints. Runtime1002.901709s, peak48880KiB, oneCPU,2GiB address-space limit.
The independent timeout exited successfully. No process remains running.

All84 runtime source hashes match their immutable copies. Of the previous
headroom run's81 sources,80 remain byte-identical; the sole changed old module is
`context_decision.py`, adding the leaf-budget counting hook. New modules hold the
trial adaptation. All probe flags independently match declared terminal values,
all assignment draws match the separate internal RNG, and owner visits/residuals
and trial outcomes/child counts reconstruct from actual records. Offline analyses
execute zero environment actions and do not modify any checkpoint.

Raw runner field `owners` means stored scorers. Its generic `accepted_trials`
field counts committed splits, including the current arm's automatic splits;
the published summary corrects that label and separately reports actual MATURE
trial counts. This reporting correction does not change raw evidence or policies.

## What remains established in the work package

Whole-decision ownership isolates different owners' parameter updates and preserves
scores at cloning. Context compatibility previously eliminated nine impossible
births and96 physical nodes without changing the observed trajectory. Residual
nomination and fresh growth have produced some sustained16/16 runs, including
the current seed18 here, but reliable acquisition/retention is still unsolved.
Inside-owner sharing remains a source of interference. This failed combined
experiment does not invalidate the mechanical isolation result or establish that
maturation is useless. It does reject this finite acceptance law as an improvement
on the current learner in this cohort.

Recombination/merging, common-trunk factoring, unrestricted learned abstraction
reuse, stronger-prefix protection and chess continuation remain separate work.
No external oracle, task-aware growth coach or macro/network controller was added.

Source local `41a9e44f3b70df040889a547509c207ae4d93206`, remote
`e3754ea4fa9fdd936a3fa5a19958ccc27ba5be63`, exact tree
`e2185a1f1a871d6087b45f75341dba7590ac9283`. Machine-readable summary, independent
audit and capacity certificates are the three `OWNER_SPLIT_TRIAL_*20260915.json`
reports in `reports/autogrowth/development/`. The fixed source/protocol remains
unchanged; main stays at`2aa1ce47a6a93e2571aaa0b02101e9543fe94955`.

Raw archive: `HECTOR_OWNER_SPLIT_TRIAL_20260915.zip`,25,111,467 bytes,23,969 members.
SHA256 `07a5e36d01dbd91d9e294925b9461c2fe03797fb011ecb732296299f0099d274`.
CRC and every payload hash match; code remains in Git. The archive assembly
initially stopped on dependency metadata without the study PYTHONPATH; its
missing metadata/manifest were added under the correct environment and all
bytes reverified. This was an artifact assembly correction, not a study retry.
