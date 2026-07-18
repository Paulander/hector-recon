# Formal explicit-OR instrument correction

This append-only note corrects the interpretation of the preserved V3B/V3C
competence-envelope artifacts through commit `9d19b28`. It does not overwrite,
retire, or silently reinterpret their recorded bytes.

## Defect

`Graph.set_confirm_policy` documents `confirm_policy="or"` as an explicit
confirmation-aggregation policy. `FormalReConEngine` handled explicit `and`,
`xor`, `k_of_n`, and `quorum`, but omitted explicit `or`. Such nodes therefore
fell through to legacy message timing. A child failure could permanently fail
the parent one tick before a different child confirmed.

The competence envelope uses explicit OR to aggregate positive mature context
cells and, separately, refuted mature context cells. Before repair, a minimal
two-cell envelope classified either single matching cell as UNKNOWN and only
classified the joint match as AVAILABLE. The intended contract is one-of-N.

## Consequence for preserved evidence

The V3C totals of 178 TP and 21 FP were produced by the faulty formal
classifier. They are valid records of that implementation but invalid evidence
about intended explicit-OR competence semantics. They must not be used as the
scientific estimate of envelope coverage or selectivity.

A descriptive recalculation over preserved V3C outputs predicts 313 TP, 39 FP,
31/32 connected organisms with any TP, 6/32 safe-narrow, 0/32 strict, and
shuffled 0 TP/0 FP. Those values remain diagnostic expectations until the
frozen organisms are replayed through the repaired formal engine. Because the
V3B topology grew while classification was faulty, even a successful replay
cannot substitute for regeneration from scratch under corrected semantics.

## Bounded repair

Only nodes that explicitly declare `confirm_policy="or"` now enter the settled
child-state quorum path with threshold one. They confirm as soon as any child
confirms, wait while success remains possible, and fail only after every child
fails. Scripts without an explicit confirmation policy retain legacy message
behavior.

This is an instrument-semantic repair, not a new learner, representation,
lifecycle, continual-correction mechanism, terminal-trace closure, or R1
transfer.

