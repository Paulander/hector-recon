# Recursive split-budget comparison — completed play, independently verified

2026-09-14. Fixed [protocol](RECURSIVE_SPLIT_BUDGET.md), cloud saved seeds 4/5/6.
No learner, feature, reward, learning rate or nomination-rule change. The Mac
replication on fresh seeds 7/8/9 is prepared but has not run in the cloud.

Increasing the cumulative split cap from six to twelve **produced the missing
ranking capacity in seed 4 and temporarily achieved 16/16**, but did not retain
that policy through the endpoint. Both caps finish 14/16, 16/16 and 16/16.
Additional structure helped representation; it did not solve retention.

## Scores on all sixteen development rows

Each arm received 768 further training actions, from event 1024 to 1792. The
first three blocks mostly exercise B; the final three mostly exercise A.

| Seed | Split cap | Start 1024 | 1152 | 1280 | 1408 | 1536 | 1664 | Final 1792 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 6 | 15 | 14 | 14 | 14 | 14 | 14 | 14 |
| 4 | 12 | 15 | 14 | 14 | 14 | 16 | 16 | 14 |
| 5 | 6 | 16 | 16 | 16 | 16 | 16 | 16 | 16 |
| 5 | 12 | 16 | 16 | 16 | 16 | 16 | 16 | 16 |
| 6 | 6 | 14 | 16 | 16 | 16 | 16 | 16 | 16 |
| 6 | 12 | 14 | 16 | 16 | 16 | 16 | 16 | 16 |

The two caps have identical final solved/failed row partitions for each seed.
Both finish 46/48 aggregate, from 45/48. That total hides the following:

- Seed 4 loses A row 4 at the first new measurement. Both arms later recover
  rows 4/5, including the originally unsolved row 5, but finish by losing B rows
  6/7. The six-cap arm loses those B rows at 1536; twelve-cap retains them at
  1536 and 1664, then loses them by 1792. Each final policy gains one original
  failure and loses two original successes. Only twelve of fifteen original
  successes remain solved at every new measurement.
- Seed 5 retains all sixteen at every scheduled measurement under both caps.
- Seed 6 learns B rows 6/7 by 1152 and retains both at every subsequent
  measurement, including the return to mostly A, under either cap. All fourteen
  original successes are also retained at the measured checkpoints.

These are observations at fixed milestones, not a claim of stability after every
training update. For seed 4 there are no newly learned B rows at the middle anchor
because it already solved all B rows initially; an empty acquisition denominator
must not be presented as perfect retention.

## Representation versus learned weights

Offline tie-aware linear feasibility tests examine each starting and block-end
graph. A correct option a needs a strictly positive relative margin; b may tie,
matching the formal chooser. Feasible witnesses are checked against every row;
infeasible final graphs receive a verified rational contradiction certificate.
No fitted weights or candidate nominations enter an actor.

- Seed 4, cap6: all seven measured graphs lack joint sixteen-row ranking capacity.
- Seed 4, cap12: the first measured graph with joint capacity is at 1408, after
  nine cumulative splits. Capacity remains at 1536, 1664 and 1792. Actual learning
  reaches 16/16 at 1536, then loses two rows despite sufficient final structure.
- Seeds 5 and 6: all measured graphs under both caps have joint capacity.

We did not locate every update causing the last regression in this new trajectory.
Final capacity does not by itself attribute the change exclusively to weight
credit rather than earlier structural changes; the saved action journals permit
that next accounting step. The stronger conclusion already supported is that
simply increasing split opportunities does not guarantee retained performance.

## Growth and resource costs

All three larger-cap actors use all six additional opportunities. Their maximum
live expression depth reaches four and descendant generation reaches three.
The controls remain at depth three and generation two, while ordinary shallow
growth, pruning and weight learning continue. This is recursive specialization
of contributions, not learned independent goal modules or graph-owned growth control.

| Seed | Cap | New recursive splits | New shallow births | New prunings | Final contributions | Definitions | Physical nodes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 6 | 0 | 4 | 1 | 17 | 42 | 147 |
| 4 | 12 | 6 | 0 | 2 | 18 | 50 | 199 |
| 5 | 6 | 0 | 5 | 4 | 13 | 39 | 129 |
| 5 | 12 | 6 | 0 | 2 | 16 | 50 | 203 |
| 6 | 6 | 0 | 4 | 2 | 13 | 42 | 129 |
| 6 | 12 | 6 | 0 | 0 | 17 | 51 | 193 |

This matches opportunities and initial state, not final parameter counts or
computation. Training and block checks took **306.246 seconds**, one CPU core,
peak **35,756 KiB (34.92 MiB)** RSS. Limits: 600-second worker, 620-second independent
supervisor, 2 GiB hard Linux address space, one numeric-library thread. No GPU.
No training process remains running.

## Verification correction — preserved rather than hidden

Every scheduled block completed before the whole-run verifier raised
`AssertionError: fork changed actor state`. The original `result.json` therefore
records `status=incomplete`; it has not been rewritten. The cause was seed 4's
equal `seen` sets being pickled in different element orders after restoration.
Both contain the same expressions. All other compared state, graph metadata,
weights and random generators match. This was a verifier defect, not missing play.

The corrected comparator checks each field's values, all graph indexes/metadata,
and random-generator states, with the existing checkpoint alias checks retained.
A regression test accepts reordered equal sets and rejects changed graph metadata.
The independent audit verifies all original source snapshots and current runtime
hashes, allowing only the two explicitly changed verifier functions; it preserves
the original error and records the old/new verifier hashes. It then verifies all
blocks and reproduces every frozen evaluation. The exact audit code is retained
under `verification-source` in the raw evidence. The Mac bundle has the corrected
verifier before any local experimental play.

**20 distinct focused tests pass.** All **4608 actual training actions, 624 scheduled
evaluation actions, 36 completed block journals and 45 checkpoints** verify.
Independent reproduction adds **624 frozen evaluation actions**, no training.
The LP analysis adds zero actual environment actions. No training was repeated,
no action record was reconstructed and no checkpoint was replaced.

The adjudicated status is `verified_complete_after_verifier_correction`, recorded
in `independent-verification.json` alongside the original report. Do not summarize
the raw `incomplete` status without this resolution or erase the original failure.

## Next use of the evidence

Run the prepared Mac fresh-seed replication unchanged, keeping its results separate
from these deliberately selected source actors. For the next cloud investigation,
trace seed 4 cap12's final 1664→1792 interval: which actual credit/pruning changes
displace rows 6/7, and whether the newly available context separation receives the
needed updates. That should precede another capacity increase or a new retention
mechanism. No further training has been started by this report.

[Combined machine-readable result](../../reports/autogrowth/development/RECURSIVE_SPLIT_BUDGET_20260914.json).
[Mac agent prompt](MAC_SPLIT_BUDGET_PROMPT.md).
All code and reports remain local; nothing was pushed to GitHub.
