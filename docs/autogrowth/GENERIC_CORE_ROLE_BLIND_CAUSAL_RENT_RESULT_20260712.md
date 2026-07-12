# Generic-Core Role-Blind Causal-Rent Result

Date: 2026-07-12. Track: generic-core development. Source commit: `1aa5e38`.
Status: complete negative package; no confirmation or KRK claim.

## Verdict

Role-blind causal rent found real nomination signal and compressed topology when
no new capacity was needed, but it did not allocate/retain enough topology for
the highest hidden demand. The package fails its preregistered noninferiority
and occupancy-gradient gates and is closed without repair.

## Arm table

Medians are over 20 fresh seeds. `both` is the number of seeds with old and new
joint success each at least 0.85. Occupancy counts final MATURE candidates.

| demand | arm | old | new | both | occupancy |
|---:|---|---:|---:|---:|---:|
| 0 | fixed-8 ranked | 1.000 | 1.000 | 20/20 | 12.0 |
| 0 | fixed-8 random | 1.000 | 1.000 | 20/20 | 12.5 |
| 0 | causal-rent ranked | 1.000 | 1.000 | 20/20 | 7.0 |
| 0 | causal-rent shuffled | 1.000 | 1.000 | 20/20 | 7.0 |
| 1 | fixed-8 ranked | 1.000 | 1.000 | 19/20 | 18.5 |
| 1 | fixed-8 random | 0.859 | 0.992 | 11/20 | 20.0 |
| 1 | causal-rent ranked | 1.000 | 1.000 | 14/20 | 11.0 |
| 1 | causal-rent shuffled | 0.819 | 0.342 | 1/20 | 5.5 |
| 2 | fixed-8 ranked | 0.995 | 1.000 | 16/20 | 22.5 |
| 2 | fixed-8 random | 0.932 | 0.702 | 3/20 | 24.5 |
| 2 | causal-rent ranked | 0.814 | 0.634 | 0/20 | 10.0 |
| 2 | causal-rent shuffled | 0.814 | 0.000 | 0/20 | 5.0 |

## Frozen gate verdicts

| gate | verdict | evidence |
|---|---|---|
| fixed-8 replication/selectivity | PASS | ranked beat random 20/20 at `m=2`; median minimum-score advantage 0.274 |
| rent noninferior to fixed-8 | **FAIL** | median minimum-score difference -0.292; 0/20 rent tasks met both thresholds |
| rent nomination selectivity | PASS | ranked beat shuffled 20/20; median advantage 0.610 |
| hidden-demand occupancy gradient | **FAIL** | median occupancy 7 -> 11 -> 10; monotonic only 8/20; median `m2-m0` 2.5 < 4 |
| no-demand topology shedding | PASS | rent retained median 4.5 fewer than fixed ranked and stayed 1.0/1.0 |
| common-experience selectivity | PASS | ranked shadow beat shuffled 20/20; median rent advantage 0.122 |
| safety ceiling | PASS | zero binds in all causal cells |
| implementation invariants | PASS | 60/60 cells passed |

Development support is false because every gate was required.

## Mechanistic audit

All 20 phase-0 checkpoints passed the >=0.85 mastery gate; 19 were perfect and
one was 0.934. Quiescence removed 3--8 unfinished shadow trials per task
(median 5), left zero trials, and preserved decision-score digests on 20/20.

At `m=2`, causal-rent ranked made a median 9 proposals, promoted 6 candidates,
and retired 4. That produces only about +2 net candidates over the starting
topology, consistent with the observed median `m2-m0` rise of 2.5. The fixed
ranked ecology ended at median 22.5 mature candidates versus rent's 10.0.
There is therefore a clear topology-throughput shortfall, not absence of
nomination signal.

Old-retention checkpoint medians at episodes 512/1024/2048/4096 were:

- fixed-8 ranked, `m=2`: 0.755 / 0.902 / 0.956 / 0.992;
- causal-rent ranked, `m=2`: 0.619 / 0.830 / 0.818 / 0.824.

Rent recovered early but plateaued after 1,024 episodes. Its final mature
candidates were not merely noise: on changed-cue ablations, 92 had positive,
7 negative and 89 zero effects. Common-experience shadows independently showed
ranked nomination superiority in 20/20 seeds. Residual nomination is therefore
supported; the tested one-challenger/review/death law is not sufficient to turn
that signal into high-demand coexistence.

The artifact does not identify retirement alone as the cause. Mature weights
remain plastic during phase 1, and the final shortfall combines limited
promotion throughput, incumbent drift, and four median retirements. Separating
those factors would be a new scientific mechanism package, not an interpretation
of this one.

## Integrity and closure

- Fresh seeds: 20261901--20261920, used once.
- Phase-0 experience: 4,096 episodes; phase-1 experience: 4,096 per arm/cell.
- Reservoir: content-blind lifetime Algorithm R, capacity 2,048.
- Shared biases/primitives stayed byte-identical in every cell.
- Role/demand/correctness fields were absent from allocation records.
- Graph/update mismatch and trial-root leakage counts were zero.
- Maximum non-temporary/temporary topology stayed within 32/33.
- Focused freeze suite: 37 passed.
- Full repository suite: 780 passed in 2,360.62 seconds.
- Retired-seed end-to-end smoke completed before fresh execution.

Per the work-package kill criterion, no threshold, review cadence, reservoir,
candidate family or capacity is tuned from these rows. An independent reviewer
must adjudicate any next package. Plausible new factors include batched
challengers, incumbent-specific slow plasticity, or separate acquisition and
retention leases, but none is authorized by this result.

Canonical committed artifact (deterministic lossless gzip):
`reports/autogrowth/generic_core/role_blind_causal_rent_20260712.json.gz`.
Compressed SHA-256:
`6ce4653501fcb6bb8b28cbff05b218e13fe5fae179d819e346fc56e9b4391efa`.
Uncompressed JSON SHA-256:
`a546c446431add7ad3167f9c8d4a5ad7a5d04a4e4b121dbc8008de96e56336c8`.
