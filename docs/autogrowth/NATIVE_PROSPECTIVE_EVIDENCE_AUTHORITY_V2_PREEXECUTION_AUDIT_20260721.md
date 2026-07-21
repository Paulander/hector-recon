# Native prospective evidence authority V2 — pre-execution implementation audit

Status: engineering review package only. Compliance matrix commit: `9362475`. No V2 preregistration/freeze, canonical synthetic stream, KRK exposure scan, KRK outcome, fresh data, R1, or retired-65 access occurred.

## Requirement-to-code map

| compliance requirement | implementation | adversarial evidence |
|---|---|---|
| frozen pattern + discovery-only immutable polarity | `native_prospective_evidence_authority_v2.py:63-91`, `:344-374` | `test_native_prospective_evidence_authority_v2.py:161` |
| complete transitive parent/eligibility/contradiction provenance and exact frontier | `:344-424` | `:137`, `:161` |
| uniform historical escrow; structure separate from authority | `:322-342`, `:428-463`, `:465-496` | `:137`, `:248`, `:278` |
| one-shot REAL prediction/activation commitment | `:498-539` | `:189`, `:211` |
| environment-grounded native receipt with exact interaction fingerprint | `:168-213`, `:541-584` | `:211`, `:233` |
| contiguous ordinal/token/trace/action/successor/terminal validation | `:586-628` | `:211-245` |
| only precommitted cells update; four/zero/Wilson graph maturity; graph revocation | `:630-733` | `:233`, `:278` |
| duplicate idempotence, remint abort, OPEN/CONSUMED persistence | `:630-733`, `:787-820` | `:248-275` |
| organism-owned post-lifecycle nomination attachment | `:735-754` | `:189-208`, `:248-275` |
| retrospective/post-outcome/relabel/suffix host paths fail closed | `:756-768` | `:189-208`, `:315` |
| exact candidate/polarity parity | `:770-774` | `:137-159`, `:315` |
| VIRTUAL isolation and cross-frame refusal | `:776-785`, `:586-595` | `:293-312` |
| outcome-blind inert exposure scan and 24/32 gate | `:822-end` | `:315-end` |

Line anchors refer to the committed-candidate source as currently staged and must be regenerated if review changes code.

## Causal authority table

| operation | owner | Python role | authority status |
|---|---|---|---|
| R0 action prediction | frozen native R0 graph | wrapper opens REAL frame and receives exact `GraphActuation`/trace | graph-owned |
| cell pattern measurement | organism-owned existing recursive matcher | terminal backend computes structural match from typed trace | generic measurement, no runner labels |
| activation commitment | `FormalReConEngine` commitment terminals | organism persists graph-emitted IDs before outcome | graph-owned emission |
| AVAILABLE/REFUTED inference | authority-gated graph terminals | organism constructs read-only authority snapshot | graph-owned emission; both roots require authority |
| environment transition/outcome | chess adapter/environment terminal | copies board, executes exact graph action, measures checkmate, signs receipt | permitted environment authority |
| maturity/revocation | `FormalReConEngine` lifecycle terminals | organism computes frozen Wilson measurement and materializes emitted authority transition | graph-owned decision; Python measurement backend |
| hypothesis pattern/polarity/frontier | organism nomination audit + signed receipt ledger | organism recursively derives and freezes; caller supplies none | organism-owned |
| topology materialization | existing organism/genome, followed by zero-argument sync | wrapper detects cells already born inside organism | no host candidate selection |
| serialization/replay guard | organism transaction ledger | canonical hashing/HMAC | organism-owned |
| exposure admission | read-only organism scanner + fixed cohort adjudicator | iterates trace commitments without outcome access | measurement only; no learning/authority |

## Host-authority assessment

No production V2 method accepts a maturity Boolean, correctness label, authority outcome, frontier, polarity, pattern, candidate list, target identity, or cell ID for nomination. Python remains the implementation language for terminal measurement, cryptographic/canonical bookkeeping, environment board transition, and graph-emitted mutation materialization. Those roles are generic and inside the organism/environment boundary; they do not choose competence authority.

`sync_organism_nominations()` is deliberately zero-argument: it can only attach escrow to cells already materialized in the wrapped organism. It fails before inspection while a REAL event is open. The actual future growth genome is not invoked by this engineering package; therefore this package makes no topology-growth claim.

## Deliberately unexecuted/future runner work

The canonical synthetic discovery-prefix candidate freeze, truthfully shuffled synthetic environment, and two-arm viewed-KRK runner are not created or run here. The enforcement primitives needed by them are present: candidate manifest parity, immutable discovery/polarity/frontier, suffix/relabel fail-closed APIs, native two-phase receipts, outcome-blind exposure scan, and exact 24/32 adjudication. Their concrete streams, seeds, manifests, hashes, admission checks, reporting aggregation, and stop artifacts must be preregistered after external code review.

Accordingly this is not yet a V2 scientific package and makes no prospective-certification, KRK, generalization, superiority, or historical-cause claim. Same-tape final reclassification is not implemented as a gate. The historical 81 rows remain described only as co-supported by at least one mature depth-one child.

## Validation

Final focused adversarial suite: 9 passed in 602.65 seconds (0:10:02), including the exact pure 24-of-32 admission adjudicator. Full repository suite: 993 passed in 4,438.99 seconds (1:13:58). No V2 stream, freeze, exposure tape, or outcome run was opened by either validation command.
