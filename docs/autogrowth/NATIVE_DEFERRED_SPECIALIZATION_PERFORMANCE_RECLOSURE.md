# Deferred specialization performance reclosure

Status: **PERFORMANCE RECLOSED — NOT EXECUTED**

Starting commit: `3d4fc8b08fecd7e68ca115b66c8f3fceaa3e5b5f`

This is an execution-only reclosure of the frozen 32-seed deferred
specialization discriminator. The original program, source manifest, stream,
and result placeholder remain byte-exact. Seeds, 640-row order, three arms,
parent selection, evidence rules and frontiers, exposure gate, evaluation,
paired inference, and stopping rules are unchanged. No frozen row was evaluated
and no fresh outcome was opened during development.

## Profile and correction

Isolated profiling on already-viewed reference rows measured raw R0 action and
trace production at 6.342 seconds per call and V2 graph matching/classification
at 0.002303 seconds per call. A complete REAL event plus receipt consumption
fell from 23.012 to 16.877 seconds with the immutable trace cache; sealed
evaluation fell from 22.941 to 6.261 seconds. Exact continuation parity held.
The detailed call counts, timings, memory, and projection model are in
`reports/autogrowth/native_authority/native_deferred_specialization_performance_profile.json`.

The cache stores only the bound frozen-R0 observation: row/FEN, actuation,
ordered and typed terminals, terminal sources, semantic trace and successor.
It stores no outcome, competence, matching cell, pending event, receipt, or
child information. It explicitly binds the invariant R0 topology, weights,
credit, and lifecycle digests plus source organism/state identities. Cache
construction uses the already-established normalized mechanical deepcopy
baseline; raw-versus-normalized action and semantic-trace parity is required.

Each seed is split into atomic Stage A and Stage B files. All three arms remain
coupled in one seed process. The complete verified 32-seed Stage-A cohort is
required before the unchanged aggregate exposure gate is calculated; no Stage
B shard can start before a passing gate. Completed shards are verified and
read, while STARTED or FAILED shards are terminal and cannot rerun. Final seed
aggregation is canonical by frozen ordinal, independent of seed scheduling.

Measured three-arm process peak was 396,452 KiB. Eight workers plus the
coordinator project to 3.40 GiB, below half of available memory at reclosure,
so the precommitted memory-only maximum is eight. Conservative current-host
projections are 189.3, 95.6, 48.7, and 25.3 hours at 1, 2, 4, and 8 workers.
At 2–3× faster per-core performance, the eight-worker projection is 12.7–8.4
hours.

## Focused validation

- cache binding, tamper closure, live/cached action, signal, terminal-source,
  successor, V2 matching/classification, receipt, and final-state parity;
- sealed cached evaluation parity and mutation freedom;
- STARTED/FAILED no-rerun and completed-shard read semantics;
- immutable attempt/stage/seed identities and complete 32-seed gate;
- exact aggregate artifact equality for sequential, two-worker, and reversed
  viewed-row scheduling;
- original frozen package byte identity and new manifest scientific identity.

Focused performance result: `14/14 passed` (`13 passed in 403.76s`, followed by
the added live-VIRTUAL/cached exposure parity check in `286.28s`). The preserved
frozen-program regression file also passed `19/19 in 3.56s`. The complete
repository suite was deliberately not repeated because no pre-existing
production module changed.

## Future execution boundary

The only future command is:

```text
PYTHONPATH=src .venv/bin/python -m recon_lite_chess.autogrowth.native_deferred_specialization_performance_reclosure --execute-frozen-shards --attempt-dir reports/autogrowth/runs/native_deferred_specialization_performance_attempt_v1 --workers 8
```

It has not been run. Fresh cache construction, Stage A, Stage B, and outcome
access remain unstarted.
