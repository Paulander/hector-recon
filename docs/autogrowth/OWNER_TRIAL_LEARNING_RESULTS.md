# Learning-before-assessment: completed recovered results

Completed 2026-09-15. The user requested comprehensive handover documents first,
then a retry of the interrupted step. The handover was published before recovery
implementation or new study play. Recovery finished the fixed seeds 21/22/23,
three-arm experiment without changing any of its 86 original runtime files.
The original failed attempt and its incomplete-status report remain historical
records, separate from this completed recovered cohort.

## Result and decision

The revised learning-trial rule improves on the original trial rule in two pairs
and ties one, but loses one pair and ties two against the current reference.
Keep the current reference. This result does not support promotion to main.
All scores below are greedy evaluation on the same 16 Boolean cases, after 1,920
training actions per learner; they are not chess results or exploratory training
accuracy. Each arm started fresh in the logical experiment; recovery restored
sealed state only where the first attempt had already run it.

| Seed | Current | Original trial | Learning-trial |
| --- | --- | --- | --- |
| 21 | 16/16 | 11/16 | 14/16 |
| 22 | 12/16 | 12/16 | 12/16 |
| 23 | 12/16 | 10/16 | 12/16 |
| Total | 40/48 | 33/48 | 38/48 |

The revised-minus-original differences are +3, 0, +2; revised-minus-current are
-2, 0, 0. Three paired seeds are descriptive evidence, not a broad reliability
estimate. No revised arm ever reached 16/16 at a measured checkpoint. Its maxima
were 14/12/12. Current maxima were 16/12/13; original trial maxima 11/12/10.
Only current seed 21 reached 16/16, retaining it from 1,792 through 1,920.

## What changed, and what remained combined

The scientific revision, pinned before original play, gives parent and both trial
children at least 64 real executed actions each before prospective assessment.
It reviews at 256 prospective local requests and, if still unproven, at 512;
its maximum local lifetime is 1,536 requests. Gain/support thresholds remain as
specified in OWNER_TRIAL_LEARNING.md. Live weights and ordinary condition growth
continue. Existing trial permission, actual feedback and lifecycle states are
reused; MATURE means accepted split evidence, not frozen weights or guaranteed
retention. This combines readiness, assessment timing and a second review. It
cannot estimate their separate causal contributions.

The recovery added bounded process/checkpoint orchestration, integrity checks and
receipts only. It did not tune learner thresholds, change seeds, install diagnostic
weights, replay old feedback or supply macro/network guidance. The current and
original-trial controls are unchanged. Earlier birth timing at action 64 is shared
by both trial arms; current births begin at 442/437/444 in this cohort.

## Acquisition and retention

A boundary is action 640, B boundary action 1280. Each context contains eight rows.
For each boundary-correct set, the table shows its size, its worst later measured
retention, and how many remain correct at the final checkpoint. The worst is over
scheduled checkpoints, not every intervening action. Final A/B also includes new
acquisition and therefore need not equal the number retained from the boundary.

| Seed | Arm | Final A/B | A boundary / worst / final retained | B boundary / worst / final retained |
| --- | --- | --- | --- | --- |
| 21 | current | 8/8 | 8 / 6 / 8 | 7 / 7 / 7 |
| 21 | trial | 6/5 | 6 / 5 / 5 | 6 / 4 / 4 |
| 21 | learning-trial | 8/6 | 8 / 8 / 8 | 5 / 3 / 5 |
| 22 | current | 8/4 | 6 / 5 / 6 | 6 / 4 / 4 |
| 22 | trial | 8/4 | 8 / 4 / 8 | 8 / 4 / 4 |
| 22 | learning-trial | 8/4 | 8 / 5 / 8 | 5 / 3 / 3 |
| 23 | current | 8/4 | 8 / 3 / 8 | 8 / 4 / 4 |
| 23 | trial | 5/5 | 4 / 3 / 3 | 6 / 3 / 5 |
| 23 | learning-trial | 8/4 | 8 / 4 / 8 | 4 / 4 / 4 |

Revised seed 21 keeps all eight A boundary rows at every later measurement.
However, it temporarily loses B rows 10/11 at 1,664 and recovers them at 1,792.
Its five B boundary rows are all correct at the end, but their worst retention is
3/5. The interrupted partial result could not reveal this later regression.
Its final unsolved rows 2/3 were never correct at a measured checkpoint.

Revised seed 22 retains all A rows at the end but temporarily drops to5/8. It
has lost B boundary rows 6/7 at the endpoint, retaining3/5 of that set.
Revised seed 23 keeps its four B boundary rows at all later measurements, but
acquired only half of B; its final policy matches the single input x. It also
temporarily drops to4/8 of its A boundary set. Stable retention of a small solved
subset must not be confused with solving the task. Retention remains unresolved.
The JSON summary contains every row's exact correct-checkpoint history.

## Trial decisions and readiness

Original trial: 15 nominations, one MATURE, 12 PRUNED and two still TRIAL.
Learning-trial: nine nominations, five MATURE, four PROBATION and none PRUNED.
All five accepted revised trials passed their first prospective review. All four
pending trials failed to establish acceptance at their first review and were
preserved. None reached the second 512-request review before action 1,920; none
expired at the lifetime bound. Preservation after first review was exercised,
but the scientific benefit of a completed second review remains unmeasured here.
Mechanical fixtures exercise that later transition; they are not study evidence.

Readiness and review episodes below are global training-action counts. Prospective
requests count local-region accesses after readiness. Raw route atoms name
measurements; the learner received no semantic labels for them.

| Seed | Parent | Raw route atom (bit, value) | Born | Ready | First review | Review gain | Final state | Prospective requests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 21 | 0 | (0, True) | 64 | 339 | 595 | +0.826456 | MATURE | 256 |
| 21 | 2 | (1, True) | 708 | 1242 | 1754 | +0.140947 | MATURE | 256 |
| 21 | 1 | (1, True) | 713 | 1301 | 1813 | +0.004048 | PROBATION | 306 |
| 22 | 0 | (0, True) | 64 | 326 | 582 | +0.114900 | MATURE | 256 |
| 22 | 1 | (1, True) | 665 | 1205 | 1722 | -0.351389 | PROBATION | 355 |
| 22 | 2 | (1, True) | 704 | 1216 | 1728 | -0.056156 | PROBATION | 352 |
| 23 | 0 | (0, True) | 64 | 307 | 563 | +0.712132 | MATURE | 256 |
| 23 | 2 | (3, False) | 576 | 1099 | 1610 | +0.187500 | MATURE | 256 |
| 23 | 1 | (1, False) | 686 | 1239 | 1760 | -0.132454 | PROBATION | 340 |

For seed 21's root x split, the two trial learners have identical first320 actual
records. The original rule rejects at 320 with gain -0.312366. The revision retains
the candidate, reaches readiness at 339, and accepts at 595 with gain +0.826456.
This is concrete evidence that an initially negative candidate can learn to help.
The deeper owner 2 candidate accepts at 1,754 after its full assessment window;
its negative partial-window state at the interruption was not a final decision.

Seed23 accepts an owner 2 partition on noise bit 3 at 1,610, with gain +0.1875.
Noise is irrelevant to the target function. Empirical benefit of the evolving
child scorers does not establish that the routing distinction is meaningful.
This is not enough to isolate a statistical false positive: child weights,
ordinary growth and allocation also differ during live assessment. The finding
should guide diagnosis, not an analyst-authored rule forbidding a particular bit.

At the endpoint, revised committed owners are 3/2/3, stored scorers5/6/5, and
pending trials1/2/1. All three reserve the full four-owner budget. Pending
alternatives occupy allocation while waiting for local exposure; the measured
cost of longer assessment must accompany any acceptance benefit.

## Capacity and cost

Independent arithmetic reproduces all 4,464 saved evaluation choices. Exact
certificates show eight final committed graphs cannot jointly rank all 16 answers
correctly, regardless of their weights; current seed 21 is the sole feasible one.
All three revised endpoints therefore have a structural limitation in their
committed graph, not merely a wrong set of weights. This says nothing conclusive
about pending children, future growth, or the general capacity of the architecture.
The rational witness and infeasibility certificates are diagnostic only; no
fitted weights were installed or used for training.

| Seed | Arm | Final nodes | Final parameters | Peak nodes | Peak parameters | Node-actions | Parameter-actions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 21 | current | 335 | 28 | 335 | 28 | 387642 | 27234 |
| 21 | trial | 143 | 21 | 313 | 33 | 319988 | 31940 |
| 21 | learning-trial | 451 | 38 | 493 | 42 | 597278 | 47783 |
| 22 | current | 339 | 28 | 339 | 28 | 393156 | 27273 |
| 22 | trial | 139 | 18 | 289 | 29 | 299974 | 27887 |
| 22 | learning-trial | 529 | 45 | 529 | 45 | 626732 | 50225 |
| 23 | current | 333 | 28 | 333 | 28 | 383848 | 27263 |
| 23 | trial | 755 | 64 | 755 | 64 | 804196 | 66610 |
| 23 | learning-trial | 421 | 36 | 433 | 38 | 553118 | 45499 |

Peaks and allocation sums here are measured at actual training actions, not only
scheduled checkpoints. Node-actions/parameter-actions sum stored allocation;
they are not executed FLOPs. The revised arm uses more final nodes, parameters
and cumulative allocation than current in every seed. Against original trial,
cost rises in seeds21/22 and falls in 23. Current conditions were never pruned;
original trial pruned2/4/0, revised 1/1/1. Birth totals were current 24/24/24,
original 26/25/23, revised 27/26/27. Fewer nodes alone cannot establish better learning.

## Recovery, action accounting and verification

84 sealed blocks and 87 checkpoints were reused with hashes/provenance. Revised
seed 21 resumed from 1,536. Its39 uncheckpointed actions were executed again against
the real environment and all complete records matched exactly. Historical logs
were used only as an external integrity assertion, never as actor feedback.
The restored learner credits these actions once. Both physical attempts remain
accounted for; the recovered study is not an independent additional cohort.

| Evidence/action category | Training | Scheduled evaluation | Frozen reproduction |
| --- | ---: | ---: | ---: |
| Reused sealed evidence | 5,376 | 1,392 | 0 |
| Newly executed during retry | 11,904 | 3,072 | 4,464 |
| Completed logical experiment | 17,280 | 4,464 | 4,464 |

The logical total is26,208 environment actions. The original attempt recorded
5,415 training and 1,392 evaluation actions. Across both attempts the known physical
total is26,247, including39 repeated training executions. An additional unrecorded
in-flight execution in the original interruption cannot be excluded, so this is
a known-recorded total, not a claim of exact total physical work. The initial
interruption's cause remains unknown; successful recovery does not diagnose it.

All270 blocks,279 checkpoints and 4,464 frozen reproductions verify. Every retry
worker has a normal result/exit receipt; no pending or failed unit remains.
Independent no-play audits reconstruct all 17,280 actual credit records, formal
measurement flags, assignment RNG draws, owner exposure/residual histories and
trial readiness/outcomes/child exposures. The audit and capacity scripts added
zero environment actions. No additional frozen verification was run afterward.

Three new recovery fixtures passed in 4.80s: exact restored reexecution, detection
of a corrupted tail, and refusal to advance past an unfinished unit. Their200
mechanical training and 48 evaluation actions use fixture seed 98 and are separate
from the study. Prior evidence covers35 distinct unchanged learner checks, with
five new lifecycle checks repeated on the original final source; prior original
trial controls had 58 focused checks. These were not all rerun during recovery.
All86 original runtime hashes remain unchanged, and all 88 retry source hashes
match repository and archived snapshot bytes.

Sum of retry start/training/frozen-verification unit wall time:1,245.295896s.
Peak observed unit RSS:47,468KiB. These exclude reused work, orchestration pauses,
initialization and final report assembly; do not call them full-cohort runtime or
whole-session peak memory. The bounds were one CPU/2GiB,90s play units with 95s
independent timeout,180s verification units with 185s timeout, and 3,600s cumulative
active play-unit budget. Initialization/finalization had separate180s bounds.

## Source, evidence and durable restoration

Handover was published first at remote
48e184e33df7307b5abc9926636b93b8456a75d1.
Original scientific source: remote 5277b06cc527cadaef20d818d70fb2d66db5409b,
local 51140753e256e8cbd9d50651cc3413aa14355810,
tree 5f1cfbbcf1a5e865a4c81d2adf9e4661817710f7.
Retry source: remotecebb51bd4e5682ce2f4a6b2e875b1628b3bdd63e,
localaa6ef44711ba00876dc99b92807ac4c12812299c,
tree 1051d2273833040eb417204f1baadc1085f2cc34.
Different local/remote commit IDs reflect connector publication; exact trees match.
Main remains2aa1ce47a6a93e2571aaa0b02101e9543fe94955.

Machine-readable reports in reports/autogrowth/development:

- OWNER_TRIAL_RETRY_20260915.json: trajectories, row histories, costs and timing scope.
- OWNER_TRIAL_RETRY_AUDIT_20260915.json: independent actual-record reconstruction.
- OWNER_TRIAL_RETRY_CAPACITY_20260915.json: arithmetic choices and exact certificates.
- OWNER_TRIAL_RETRY_PREFLIGHT_20260915.json: recovery fixture evidence before play.
- OWNER_TRIAL_RETRY_VERIFICATION_20260915.json: consolidated counts, pins and hashes.

Raw directory: snapshots/autogrowth/owner-trial-learning-retry-20260915.
The completed archive is HECTOR_OWNER_TRIAL_RETRY_20260915.zip, version 3 of
libfile_594e815364a881918743618e665c0e4e, file ID
file_0000000040b08210900c4d7ad39828be. It contains 36,641 members, with 36,640 payload
hashes and ZIP CRCs checked. Size36,276,210 bytes; SHA256:

`b1c09311fc891c8f0a5b898b924f4b9cf4871d7f52a9e09e51d5d1878de339ec`

Git-backed code/docs/reports remain in the private repository and are omitted
from the raw ZIP. Restore the source pin and validate run/source.json when
reconstructing source-snapshot. Original interrupted archive remains separate:
libfile_1f179c97dea081918faac4def83827cb, SHA256
`a4e0b2f9dbc66661f3b11239e7943891385c9ef1efea79f4dcbe37554b92c676`.
The handover's OPERATIONS_AND_RECOVERY.md explains restoration and authentication.

## Proposed next investigation, not an automatic new run

Preserve current as the reference and keep this cohort closed. The useful next
question is whether local split evidence identifies a distinction needing separate
parameters, versus a temporary advantage from separately evolving copies. Inspect
the accepted noise partition, the four pending allocations, and the remaining
within-owner failures using saved histories. Any new criterion should remain
local and action-feedback based, with a separately declared comparison. Do not
introduce semantic bit exclusions, task labels, a macro coach, diagnostic weight
installation, new timing knobs or another run implicitly. Richer compound
predicate reuse and recombination remain separate unfinished work.
