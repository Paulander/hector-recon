# Native competence continuation manifest V2

Date: 2026-07-19. This is an append-only clarification; no prior artifact or
mature-cell falsification verdict is changed.

The previously named `complete_canonical_manifest.v1` was complete for the
closed mature-falsification package replication contract, but it was not an
exhaustive continuation-state serialization. In particular, it represented
evidence by keys and did not freeze all private continuation counters and future
lineage state. Historical `to_manifest()` behavior remains unchanged.

`continuation_manifest.v2` is the exact continuation contract. It adds full
evidence-record payloads, all cell and StemCell lifecycle fields, member
specifications, next-cell and review counters, correction/growth audits, the
graph snapshot, and specialization request/proposal counters and lineage. Its
canonical SHA-256 digest changes when an evidence payload, continuation counter,
member specification, or lineage field changes. A serialization canary also
requires source and restored envelopes given the same next real observation to
emit the same correction, nominate the same child, make the same lifecycle
transition, and finish with identical V2 manifests.

This clarification does not rerun or reinterpret the closed falsification
experiment.

