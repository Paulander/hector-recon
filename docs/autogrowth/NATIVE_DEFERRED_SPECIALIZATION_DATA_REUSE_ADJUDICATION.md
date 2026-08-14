# Deferred-specialization data-reuse adjudication

Status: **DESIGN NOTE ONLY — NO OPTION CHOSEN OR EXECUTED**

## What was consumed

The failed attempt constructed and verified an outcome-free observation cache
for all 640 frozen rows. Cache construction did not consume outcomes. During
Stage-A initialization, however, each of the 32 genome seeds used the same 64
`parent_discovery` rows to mint grounded discovery receipts and grow its own
organism. Thus 64 distinct discovery outcomes were consumed, in the frozen
order, once per seed: 2,048 seed-row discovery receipt interactions. The
ordered 64-row ID digest is
`03f0ac2e85d31e6848a76e863923f475bb119fd6b2238ab18a948ee7829c85e7`.

Candidate growth occurred transiently before the deterministic wrapper error,
but no Stage-A shard completed and no candidate payload or scientific candidate
result was persisted. No parent-prospective exposure, exposure-gate result,
engagement result, child certification, sealed evaluation, or performance
result was observed. The later 32-seed initialization canary measured candidate
parity for engineering purposes only and stopped before prospective evidence.

## Cache status

The existing 640-row cache is strictly outcome-free. Its committed verifier
passed all records; the top-level declarations are `contains_outcomes=false`
and `contains_competence_or_matching=false`. Records bind R0 action, ordered
signals, typed terminal signals and sources, semantic trace, successor, exact
row identity/FEN, and R0 source-state digests. They contain no observed outcome,
competence classification, matching-cell identity, pending event, receipt,
child information, or mutable V2 state. The cache SHA-256 is
`2d364c274fab22863082daa09fc51d4e402df41c44ebb0d692539f0967c5403f`.

A future attempt could technically bind this cache by that hash together with
its source R0, continuation, stream, row-order, and per-record digests. Such a
binding is an execution optimization; it does not make the already-used 64
discovery outcomes fresh and does not itself authorize data reuse. The current
reclosure makes no reuse choice.

## Options for external review

### A. Repaired attempt on the original frozen cohort

A separately authorized attempt could retain the original 32 seeds, 640 rows,
row order, arms, thresholds, gates, and inference, while declaring that the
64-row discovery prefix has already been consumed for all seeds. It could bind
the verified outcome-free cache by hash or reconstruct an equivalent cache
inside the authorized execution. All later outcome regions remain unopened.
External review must decide whether the engineering failure and deterministic
repair permit this cohort reuse and how it is labelled.

### B. Entirely new cohort

A separately frozen cohort could use new rows and outcomes, with a new stream
identity and new performance manifest while holding the mechanism and
scientific rules fixed. Its cache would be constructed only inside that later
authorized execution. This avoids reusing the consumed discovery outcomes but
requires a complete new cohort freeze and review.

Neither option is selected, preferred, implemented, or authorized here. No
future command was executed.
