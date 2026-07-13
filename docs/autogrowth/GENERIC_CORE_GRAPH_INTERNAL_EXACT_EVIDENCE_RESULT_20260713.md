# Generic-Core Graph-Internal Exact Evidence Result

Date: 2026-07-13. Track: generic-core development. Status: canonical negative
completion. No KRK transfer is authorized.

Canonical payload is preserved losslessly at
`reports/autogrowth/generic_core/graph_internal_exact_evidence_20260713.json.gz`.
Its uncompressed SHA-256 is
`c735c7565428a80b14bf835abab1c7c99d89916fd5d000c7636ad269547aef9e`;
the committed gzip SHA-256 is
`1a79e6c21e5752e75a4598be1b85f7c609aba01bc9d4e958eeebc4bc1db1544e`.
Admission manifest SHA-256:
`b4552c17c331793fddb2119e95dc958e534889c918c2b976f1cdd1757e3c28d4`.
Preregistration, implementation, and admission-freeze commits are `325bc92`,
`bd6f95a`, and `c357e73` respectively.

## Verdict

The internal-terminal architecture and exact counter are valid, but exact-support
requests are closed negative at the frozen dose. They modestly improve evidence
acquisition over the activation proxy, yet not enough to reach support 32 before
the unchanged two-review lifecycle kills most tasks' weakest target. This is not
a topology-discovery failure: all 80 post-hoc target structures existed in every
request arm.

| Arm | Median old | Median new | Both >=0.85 | Median mature occupancy |
|---|---:|---:|---:|---:|
| Fixed-8 reference | 0.9795 | 1.0000 | 18/20 | 22 |
| Ordinary rent batch-4 | 0.9570 | 0.7256 | 3/20 | 12 |
| Graph activation directed | 0.9229 | 0.7090 | 1/20 | 12 |
| Graph exact directed | 0.9199 | 0.7090 | 3/20 | 12 |
| Graph exact shuffled | 0.9199 | 0.7090 | 4/20 | 12 |

## Independent gate adjudication

| Gate | Verdict | Frozen evidence |
|---|---|---|
| Measurement integrity | **Pass** | All 20 cells and 100 arms passed counter, graph, clone, RNG, budget, identity, firewall, root-isolation, and final-return checks. |
| Evidence acquisition | **Fail** | All four targets reached exact support 32 in 2/20, not 16/20; 18/80 died unsupported, not <=4/80. Exact beat activation minimum support in 14/20, but median gain was +2, not +12. |
| Maturation | **Fail** | All four targets obtained positive rent and matured in 2/20, not 16/20. |
| Priority exposure | **Not identified** | Across exact arms, 415/49,638 opportunities were multi-request and 393/49,638 had unequal strengths/could differ: 0.84% and 0.79%, below 20%/10%. |
| Priority effect | **Not tested** | Conditional gate remained null. Exact directed beat shuffled minimum support in 1/20, lost 1/20, and tied 18/20. |
| Behavior | **Fail** | Exact directed mastered old plus new in 3/20; paired median versus fixed was -0.2588. |
| Stability | **Pass** | Fixed reference mastered both in 18/20; medians were 0.9795/1.0. Seeds 20262306 and 20262310 remained below 0.85 jointly. |
| Transfer authorization | **Fail** | Evidence, maturation, behavior, and identified-priority requirements did not pass. |

## Mechanistic read

Exact measurement moved the weakest per-task target from median support 11 to
13. At target level, 62/80 exact targets reached 32 versus 60/80 activation
proxy targets. The gain is real but highly concentrated: paired per-task minimum
differences included +54 and +67, while five tasks worsened and one tied.

The 18 exact-directed targets pruned as unsupported had first/second review
support medians 7.5/12.5; their final reviewed supports ranged 5--22. Their raw
activation counts ranged 21--94, confirming again that activation is not retained
rent evidence. Exact terminals continued requesting the correct currency, but
ordinary scheduled exploration accumulated it too slowly within two reviews.
None of these deaths was a near-threshold 31/32 miss.

Every request arm consumed 24,819 matched phase-1 exploration events. Activation
directed emitted 3,330 probes; exact directed emitted 2,125 and exact shuffled
2,126. Exact support includes pre-proposal retained records, so some trials begin
with less deficit and stop at exact support 32; the smaller request count does not
indicate a mismatched event budget. Exact directed and shuffled had identical
median behavior and differed behaviorally on only one seed, against directed,
consistent with the preregistered `not_identified` priority verdict.

The planted canary remains important but separate: it produced simultaneous and
unequal requests on 100/100 opportunities, directed/shuffled selected different
actions on 53/100, and RNG/event parity passed. Thus the allocator can express
priority; the canonical ecology rarely presents a choice among requesters.

## Interpretation and next boundary

The preregistered branch binds: close exact-currency requests at this dose. The
next isolated scientific factor is support-conditioned lifecycle grace, not more
exploration throughput, changed reward, consolidation, action competition, or
virtual frames. The review trajectory suggests one fixed extra review would
usually be too small; any next contract should make continued trial survival
depend on local exact-support acquisition and impose a bounded generic cap.

This result does not authorize implementing or running that repair without the
next external adjudication/freeze. It also does not weaken the architectural
result: `EVIDENCE_DEFICIT` is now a real graph terminal, the host actuator bus did
not inspect candidate state, and the exact incremental measurement remained
correct under live Algorithm-R evictions. R2 remains closed; native KRK R1 is
unchanged.
