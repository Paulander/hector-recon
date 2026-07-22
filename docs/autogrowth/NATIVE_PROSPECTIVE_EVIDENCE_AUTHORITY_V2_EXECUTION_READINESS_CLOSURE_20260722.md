# Native prospective evidence authority V2 — execution-readiness closure

Date: 2026-07-22
Branch: `codex/native-krk-resume-composition`
Phase-A correction: `110e5c3`
Starting reviewed HEAD: `de790fdcdd85005372ba9cdbde685f4498edf0ee`

## Verdict

The engineering execution-readiness repair is **closed passing**. This is not a
scientific V2 result and does not authorize a canonical runner, synthetic
outcome stream, KRK exposure, fresh or unopened data, R1, or retired-65 access.

The preserved `de790fd` abort remains historical, but its fixed-polarity
causal interpretation is withdrawn. It compared unequal evidence ledgers
(4 records versus 12). On coherent ledgers, fixed-at-nomination polarity
preserves native growth and behavior exactly within the preregistered
comparison boundary.

## Phase A — instrument correction

Prospective wrapping now rejects a source before mutation unless:

- receipt IDs exactly equal evidence IDs;
- every native evidence record exactly equals the record reconstructed from its
  receipt, including ordered active signals, typed provenance, outcome,
  actuator, completion terminal and policy response;
- every cell evidence reference belongs to that exact ledger.

Epoch opening is copy-on-write and performs no silent evidence hydration.

Results:

- the historical 8-receipt/0-evidence fixture is rejected atomically;
- the coherent 8+4 comparison has 12/12 identical proposal rows and both arms
  choose `context:v2_child` at proposal row 8;
- exact graph requests and activation/error values, members, IDs, support,
  success/failure statistics, lifecycle, maturation, pruning, nesting,
  classifications, topology and selected actions match;
- differences are confined to escrow/provenance metadata and fixed polarity on
  final non-authoritative PRUNED tombstones;
- corrected 8+4 parity passed in 329.67 seconds;
- the frozen historical source contains 96 receipts and 96 exact evidence
  records; its 96+4 parity smoke passed in 152.78 seconds.

## Phase B — closed readiness contracts

| Contract | Closed implementation |
|---|---|
| Complete escrow | Operation, trigger, fixed polarity, graph request states, considered and selected contexts, categorized reads, transitive ancestors, complete exclusion set, nomination-read frontier, certification frontier and immutable escrow digest are persisted and independently revalidated. |
| Atomic specialization | Receipt acceptance, evidence insertion, eligibility, parent transition, escrow construction, actual child insertion, counter updates and wrapper synchronization run on a deep copy. Injected failure at every boundary leaves the continuation byte-identical. |
| Experimental identity | Schema, implementation, mode, source, closed epoch/event, candidate population, escrows, lineage, actual topology and arm initialization are sealed. A zero-argument organism method clones prospective and same-ledger arms from one closed candidate population. |
| Executed graph identity | The authority digest is derived from the graph snapshot actually built and evaluated, with nodes, edges, root policies, predicate identities, roles and lifecycle constants. A post-seal predicate change fails. |
| Laboratory registry | Exact serialized organisms and exact per-organism row/frame/FEN tapes are hashed outside the learner. Registry scans reload the payload, regenerate commitments from the organism, and reject altered tape/order, duplicate interactions, re-signed fabrication, post-outcome rows, open transactions, unclosed nomination and malformed nested schemas. |
| Version/native parity | V2 schema/implementation and exposure schemas are bumped; old V2 payloads are rejected; AVAILABLE and REFUTED behavior is retained; UNKNOWN live polarity and historical live TRIAL are rejected; coherent tombstone-only sources restore exactly. |
| Learner boundary | Registry, tape, cohort, run and package identities remain absent from learner continuation state and cannot enter nomination, terminals, action choice, credit, lifecycle or authority. |

The source-binding digest excludes transient scheduler telemetry and includes the
policy-critical topology, weights, credit and lifecycle identities. This fixed
a real-versus-restored commitment mismatch without rounding, tolerance, or
removing any policy-critical field.

The native learner source-hash lineage remains explicit: historical V3/V3B
hashes are unchanged as historical constants, while the additive readiness
source has its own current hash lock.

## Authority before and after

| Operation | Before repair | After repair |
|---|---|---|
| Source evidence admission | epoch opening could hydrate receipts into missing evidence | native organism must present one exact receipt/evidence ledger; no migration |
| Candidate nomination | partial provenance plus one overloaded frontier | graph/genome request plus complete native escrow and distinct read/certification frontiers |
| Specialization mutation | several in-place state changes | one copy-on-write organism transaction with rollback at every mutation class |
| Experimental arms | could be constructed independently | cloned from one sealed closed nomination result with identical candidates and polarity |
| Authority topology | separately authored expected manifest | snapshot and predicate identity of the graph actually evaluated |
| Exposure cohort/tape | caller label plus tamper-evident HMAC | laboratory registry binds exact payloads and exact row/frame/FEN manifests; HMAC remains only tamper evidence |
| Action and classification | graph-produced | unchanged graph-produced path; laboratory metadata is unavailable to the learner |

## Engineering canary

The 32-organism canary uses only already-viewed frozen engineering material.
It deliberately constructs 24 organisms with four distinct opportunities for
one frozen cell and eight organisms with four unique rows whose matching-cell
intersection is empty. This tests the registry and admission instrument; it is
not evidence that competence generalizes.

Final isolated result:

- exact scanner outcome: 24/32 qualifying; admission passes;
- all 128 consumed commitments are graph-produced, exact-tape-bound and
  regenerated from the corresponding serialized organism;
- duplicate, altered-order, fabricated, outcome-bearing, open and malformed
  controls fail closed;
- learner continuation state contains none of the laboratory identities;
- `1 passed, 25 deselected in 6458.81 s (1:47:38)`.

An earlier engineering attempt produced 23/32 because the harness called an
organism “capable” after any response, while admission requires four distinct
opportunities for the same cell; it also used a duplicate to create a
nonqualifier. That result was not accepted. The final canary uses the scanner's
exact same-cell contract and four unique rows in every organism.

## Validation

- Every focused V2 test passed, including corrected ledger tests, complete
  escrow semantics, transactional rollback, immutable seal, executed topology,
  V3/native-state parity and the 32-organism canary.
- Adjacent native envelope, trace-authority, contradiction-specialization, V1
  authority and V3/V3B hash-lineage suites: **54 passed in 644.94 s
  (10m44s)**.
- Full repository suite on the final implementation and test bytes:
  **1010 passed in 12734.63 s (3h32m14s)**.
- Final Python compile and Git diff checks passed.

## Remaining limitations and stop

- This is engineering readiness only. No learning discriminator or competence
  outcome stream was executed.
- Prefix-wide nomination closure remains a laboratory isolation mechanism, not
  the final continuously growing ReCoN architecture.
- The checked-in HMAC is tamper-evident, not external provenance proof.
- Scheduler telemetry is intentionally outside inference identity; topology,
  weights, credit and lifecycle remain inside it.
- No claim is made about KRK generalization, R1 handover, fresh confirmation,
  or autonomous competence learning.

Stop here for external review. Any scientific V2 package must be separately
frozen and must consume the candidate-identical arms through the actual V2 core
without learner-visible arm, tape, cohort or phase metadata.
