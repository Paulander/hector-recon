# Authorized checkpoint recovery of the owner-trial comparison

The user explicitly requested, on2026-09-15: prepare comprehensive handover
first, then retry the previous step. This supersedes the original one-attempt
restriction for this recovery. Scientific source, seeds, settings and logical
schedule stay unchanged. Original interrupted evidence remains immutable.

## Recovery decision made before new play

Reuse the84 verified completed blocks and87 saved checkpoints from
`owner-trial-learning-20260915`: seed21 current/trial completed1,920 each,
learning-trial completed1,536. Copy files, never hard-link mutable output.
Do not copy the unfinished block into the new working trajectory or alter it.
Record every reused file's source/hash in the new provenance manifest.

Resume the revised learner from its exact1,536 checkpoint, including all weights,
trial clocks, history and RNG states. Execute the next64 scheduled actions against
the real Boolean environment. The first39 repeat previously recorded actual
executions after rollback. Compare their new complete records exactly against the
preserved39 records; abort on any difference. Old records serve only as an integrity
assertion outside the learner. They never supply an action, outcome, weight or
candidate to it. Do not replay logged feedback or install a reconstructed actor.
The original39 remain historical redundant work, not extra observations credited
twice in the recovered trajectory. An unrecorded original in-flight action cannot
be excluded; keep that uncertainty in cross-attempt physical-execution accounting.

Finish the remaining384 logical actions for revised seed21, then fresh seeds22/23,
all three roles,1,920 actions each. Reuse the two completed seed21 controls rather
than spending actions repeating their whole training. This is recovery of one
fixed cohort, not an independent replication or a new seed-based comparison.
No learner change, score-based extension, maturation knob, grammar change or
main merge is part of this retry.

## Exact accounting

| Category | Reused logical evidence | Newly executed in retry | Final logical experiment |
| --- | ---: | ---: | ---: |
| Training actions | 5,376 | 11,904 | 17,280 |
| Scheduled evaluation actions | 1,392 | 3,072 | 4,464 |
| Frozen reproduction actions | 0 | 4,464 | 4,464 |
| Training blocks | 84 | 186 | 270 |
| Checkpoints including fresh starts | 87 | 192 | 279 |

Newly executed retry actions total19,440. This includes39 repeated real training
actions within the11,904; it does not add39 again. Original recorded executions
were5,415 training+1,392 evaluation=6,807. Both attempts together therefore have
at least26,247 recorded physical environment actions if recovery completes,
versus26,208 distinct logical actions in the intended experiment. The difference
is39 known repeated training executions; original unrecorded in-flight work is
unknown. Mechanical fixtures are counted separately, using onlyseeds98/99.

## Execution and evidence

Prepare and publish the handover before launching recovery. Verify the recovery
wrapper with small actual-action fixtures and pin its source/protocol separately.
The86 original runtime source hashes must remain identical to the original
source pin, remote5277b06/local51140753. All checksums are authoritative in the
original run/source.json. The new wrapper changes orchestration only.

Use `scripts/autogrowth/retry_owner_trial_learning.py` with separate initialize,
step/status and verification operations. The wrapper is now implemented; three recovery fixtures passed before play.
The preparation handover was published first at48e184e3.
The separate directory is `snapshots/autogrowth/owner-trial-learning-retry-20260915`.
Each training worker restores a sealed checkpoint, runs one64-action block,
saves/reloads it, evaluates once and seals its journal. Workers exit after each
unit. This reduces dependence on one long-lived execution session and allows a
new instance to inspect the exact completed boundary. It does not guarantee
survival of a host/session failure during a unit.

An exclusive file lock prevents simultaneous coordinators. Before each worker,
write an intent recording unit identity/source; afterward write its exit/receipt
and duration. Status is derived from receipts/manifests, never just an optimistic
progress line. Record parent checkpoint hashes and reused provenance. Keep per-unit
limits of oneCPU,2GiB address space,64MiB per file,90seconds workerCPU/wall and
95seconds independent timeout with5seconds kill grace for training; allow up to
180seconds for an arm's frozen verification with185seconds independent timeout.
Cap cumulative active start/training/verification unit wall time at3,600seconds;
initialization/finalization have separate180-second non-play limits. Time spent
between worker calls is reported separately. An incomplete unit is charged its full allocated
limit for budget accounting if no final resource receipt survives.

These unit execution limits replace the original single3,600-second process
wrapper; they do not change the experiment's action/learning budget. No automatic
training reexecution of a newly interrupted block is hidden under the current
allocation. If another unit fails, preserve its files and account for its actions
before determining the remaining authorized work. A surviving sealed unit can
always be inspected/reused without asking the user again. Do not create a false
complete result to make a summarizer work.

At final verification reproduce all279 saved policies (4,464 actions), verify
block chains, source hashes, ownership, actual credit, birth/trial histories and
paired exploration states. Write evaluation receipts so progress and counts are
recoverable. The independent audit also checks raw probe flags/RNG histories and
rational capacity certificates without environment actions. Report retention,
acquisition, accepted/retired/pending trials and full stored-node/parameter costs.
Wall time for reused segments is unavailable for the interrupted arm; do not
invent a clean full-run runtime or rank arms by mismatched timing totals.

Save raw recovery evidence, update the handover/status, and publish the private
work branch. Further scientific interventions require a separate decision after
these fixed results, not automatic tuning from interim scores.
