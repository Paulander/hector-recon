# Recursive continuation: six versus twelve cumulative splits

Declared 2026-09-14 before experimental play. Follow-up to the completed
recursive retention attribution. No learner, feature, credit, pruning, candidate
ranking or reward mechanism changes. This is a budget intervention in a lab.

## Fixed cloud comparison

- Continue all three saved guided actors, seeds 4/5/6, at event 1024. Their
  development scores are 15/16, 16/16 and 14/16. Checkpoint hashes are fixed in
  the runner. Verify the earlier source manifest and checkpoint hashes first.
- Clone each into cumulative split caps 6 and 12. The control still performs
  its ordinary shallow growth/pruning and weight updates. Both start with six
  prior splits; the larger cap allows at most six more. No diagnostic nominee
  or fitted weight is supplied. Only `RecursiveConfig.max_splits` differs.
- Keep eta .3, exploration .25, 24 live weighted contributions, depth 4,
  12 previously sampled contexts, 160 definitions and 4096 physical vertices.
  The finite vocabulary and other caps can prevent further useful growth.
- Each arm receives 768 further actions, events 1024 through 1791. Six blocks
  of 128: first three mostly B (each B row 14 times, A row twice), last three
  mostly A (reverse counts). Shuffle with `recursive-budget:{seed}`. The reward
  rule remains x when z is false, y when z is true, using actual chosen actions.
  The learner receives no phase labels. Both arms see the same order and paired
  exploration draws; realized policies, rewards, topology and compute may differ.
- Frozen disposable evaluations of all sixteen rows at the source and every
  block. Report final totals, row gains/losses at every milestone, retention of
  newly acquired B rows after returning to mostly A, and topology sizes/depth.
  Capacity analysis, if performed, is offline and does not influence the run.
- Exactly **4608 training + 624 evaluation = 5232 actions**, 36 completed
  block journals and 45 checkpoints (including three copied anchors). Frozen
  verification adds 624 evaluation actions, separately counted. No new training
  during verification. Run every arm to its fixed endpoint regardless of scores.

## Independent Mac Mini replication

Use the same runner and unchanged learner on **fresh seeds 7/8/9**, without
selecting favorable actors. Construct each source with the earlier retention
schedule: 256 A-only prefix actions at cap16, then 768 guided A/B/A continuation
actions at cap24 and split cap6. Evaluate after the prefix and six continuation
blocks. Then run the exact new six/twelve comparison above, including any actor
that remains weak or perfect. Do not require that it used all six earlier splits.

The independent run executes **7680 training + 912 evaluation = 8592 actions**,
60 block journals and 75 checkpoints, including three copied anchors. Verification
adds 912 frozen actions. Its fresh seeds are a replication, not additional paired
observations of the cloud seeds. No cloud-result-based tuning is permitted.

## Resource and evidence limits

One worker process; numeric libraries limited to one thread. Linux CPU affinity
is one core, hard address space 2 GiB; macOS lacks that affinity interface and
uses the single-thread worker plus an independently polled 2 GiB RSS limit.
There is no GPU requirement. Worker wall budget 600 seconds and CPU budget
602/605 seconds, 64 MiB per file. Independent supervisor stops after 620 seconds
and terminates the process group, with a five-second TERM grace then KILL.
The supervisor checks worker RSS every half second; macOS RSS policing is sampled,
not an instantaneous allocation cap. No worker subprocesses are created.

Use the already verified write-once recorder with retained progress copies.
Preserve all actual actions, completed checkpoints, source snapshots and any
incomplete block. Never delete logs or automatically retry/resume. A failure
requires diagnosis before another attempt. Existing raw runs remain untouched.

The frozen verification has its own 120-second limit. The scientific claim is
narrow: whether additional opportunities help acquisition and retention under
this supplied recursive growth law. This is not proof of safe continual learning,
graph-learned developmental control, independent goal modules, or chess mastery.

Implementation: `scripts/autogrowth/run_recursive_budget.py`; independent guard:
`scripts/autogrowth/guard_recursive_budget.py`. Results are recorded separately
to preserve this protocol's source hash. Code/report publication is not authorized.
