# V2 fresh discriminator review repair V2 — preregistration

Date: 2026-07-26
Starting commit: `bd2ceb788340c6f7ccc30e7ba1e8440cce4a7270`

## Bounded purpose

This package replaces the superseded pre-run freeze without changing the V2.1
learner, graph behavior, candidate nomination, polarity, thresholds, topology,
lifecycle, arms, endpoints, tests, or interpretation. It repairs only the outer
experiment driver before any new learner interaction.

The experiment namespace is
`native_v2_fresh_discriminator_review_repair_v2.v1`; all outputs live under
`reports/autogrowth/native_authority/v2_fresh_discriminator_review_repair_v2/`.
The `bd2ceb7` package and artifacts remain unchanged.

## Frozen corrections

1. The engagement decision includes the C control receiving its frozen
   contradiction dose in at least 24/32 seeds, a graph-emitted clearing for
   every contradiction that occurs while a cell contributes decision weight,
   and the complete per-seed conjunction in at least 24/32 seeds. Any missing
   required clearing, or a C dose below 24/32, prevents a positive verdict.
2. Each committed seed is rebuilt from exactly 16 ordered row records, one A/B/C
   record per row, and exactly 48 ordered environment results. Endpoint totals
   are recalculated from row increments. Final cell states, supports,
   contradictions, clearing state, sequence position, and continuation are read
   independently from the three restored final graphs and must agree with the
   row and journal records.
3. Immediately before the first environment result, the driver restores all 96
   frozen graphs into memory, rechecks prefix/candidate metadata, reconstructs
   all visible-signal and matching-cell rows, recomputes target opportunities
   and the 24/32 admission result, and compares them with the frozen exposure
   and execution manifests. Those exact in-memory graphs are retained for play.
4. The exposure stage writes a later execution manifest that binds source,
   package, seed, ecology, prefix/candidate, all 96 graph snapshots, exposure,
   row parity, target admission, zero environment-result reads, and the complete
   restored-graph identity.
5. The excluded-position manifest contains every starting and resulting FEN
   from all earlier V2 ecologies and canaries, including the unused `bd2ceb7`
   freeze. Every new starting and resulting FEN must be unique within the new
   ecology and absent from that manifest. Complete transitions and stable
   interaction IDs remain separated as well.
6. Command restart uses the journal's next unfinished seed. It verifies every
   completed seed and final graph plus the full frozen baseline before opening
   another environment result. If all 32 seeds are complete, it builds the final
   summary from committed rows without replay.

## Unchanged scientific design

All 32 commit-derived genome seeds are retained. A/B/C construction, the fixed
64-row discovery prefix, fixed 16-row suffix, target selection, exposure dose,
24/32 admission, `D_safe`, `D_signal`, exact paired sign tests, two-test Holm
correction, 17/32 favorable-seed requirement, and 20,000 deterministic
bootstrap descriptions remain unchanged.

The strongest null remains: after adequate recurring target opportunities and
complete engagement, post-birth certification is no safer than the same-ledger
comparison and no better than the truthfully permuted C control.

## Pre-data stop

This package may run only focused tests, the already-retired actual-graph
canary, the selected adjacent suite, legal-position enumeration, graph-visible
parity checks used to construct the new ecology, and hashing. It must stop after
committing and pushing source plus predata manifests.

It must not run the new discovery prefix, exposure scan, environment results,
historical regression, R1, retired-65, or any held-out pool.
