# Native prospective evidence authority V2 — compliance matrix

Status: binding pre-implementation engineering contract. V1 is immutable at `726e74a`; V2 is a replacement package. No V2 runtime implementation may precede this matrix's separate commit and push.

## Ownership matrix

| contract | owning organism/graph component | persisted fields | prohibited host authority | discriminating tests |
|---|---|---|---|---|
| Complete hypothesis frozen at birth | organism-owned nomination escrow plus cell-local hypothesis record | pattern/members and polarity frozen together; lineage/depth; complete transitive consulted discovery-receipt IDs and digest; internally derived frontier | runner frontier, polarity, candidate list, maturity Boolean, target identity, reconstructed provenance | `polarity=None` rejection; polarity mutation rejection; parent-support/eligibility/contradiction provenance closure; missing provenance fail-hard; frontier derivation |
| Historical escrow initialization | organism inspects its own accepted receipt/audit state uniformly | pre-escrow consulted discovery set/digest; internally derived frontier; separate authority false/legacy authority from structure | per-cell host list, frontier, authority Boolean, target identity | candidate/structure/behavior parity across arms; unavailable authoritative provenance closes |
| Strict REAL transaction | organism one-shot event controller plus graph prediction/activation-commitment and lifecycle legs | next ordinal; one pending event/token; frame/trace/signal/source/actuation/classification/matching identities and state | post-outcome matching, retrospective authority scan, host update sets, early nomination | exact causal order; receipt-before-prediction; dual pending; born-during-event; post-outcome matching; retrospective scan; lifecycle-before-nomination |
| Replay/remint protection | organism receipt validator and interaction ledger | next expected ordinal; pending token; consumed receipt IDs/tokens; stable interaction fingerprints | gaps, relabeling, reminting, replay | out-of-order/gap/token mismatch; exact duplicate idempotence; new-ID fingerprint collision atomic abort; open/consumed restore |
| Structure versus authority | separate graph-consumed `prospectively_certified` state and graph maturity/revocation legs | authority state/transition receipts separate from unchanged stem structure | resetting MATURE/PROBATION/TRIAL; host gating inference; host authority initialization | both roots require authority; shadow remains active; behavior and nested matching parity, not hash-only parity |
| REAL/VIRTUAL capabilities | distinct REAL event capability and read-only VIRTUAL session | REAL pending/consumed state only | VIRTUAL ordinal/token/commitment/receipt/certification or later REAL pairing | every prohibited virtual action fail-hard with zero mutation; cross-frame pairing; open-pending serialization |
| Candidate-identical synthetic | nomination genome runs exactly once on prefix with maturity disconnected | frozen pattern, polarity, lineage, complete discovery IDs/digest/frontier and manifest hash | suffix nomination, per-arm candidates, replacement seed/search, authority relabeling | planted+spurious admission; exact arm manifest parity; no suffix birth; truthful environment shuffle |
| Truthful shuffled synthetic | synthetic environment applies frozen permutation before its terminal mints receipt | permutation, truthful transition/outcome, signed receipt | runner or authority rewriting receipt outcome | receipt truth/signature; marginals/exposure/order/candidates identical; planted discrimination |
| Two-arm viewed KRK | prospective escrow and legacy authority from uniform organism initialization | pattern/polarity/lineage/structure/behavior/trace/action/exposure parity | KRK shuffled authority, fabricated outcomes, selection, prospective-superiority gate | exact two-arm parity and prequential reporting; offline shuffle cannot mutate/emit/gate |
| Label-free exposure admission | read-only graph trace and frozen-cell commitment scanner | distinct qualifying opportunity IDs/digests per organism/cell; inert scan digest | outcome access, persistent update, dream certification | poisoned outcome field; before/after digest exact; frozen 24/32 gate |
| Interpretation | organism transaction ledger plus report-only aggregation | context-level and seed-level prequential rows; same-tape final rows marked descriptive | final reclassification gate; independence inflation; causal-child wording | comparisons use committed pre-outcome predictions; context/seed tables separate; wording regression |
| Stop integrity | canonical runner | exact abort field/frame/values and hashes | in-place repair/rerun or partial recovery | every mismatch persists atomic abort; canonical output refuses overwrite |

## 1. Complete hypothesis at birth

Pattern and polarity are frozen together when the hypothesis is born. Polarity is derived only from discovery evidence; `polarity=None` at candidate birth is forbidden. Certification evidence can never select or change polarity.

Each hypothesis persists the complete transitive set of grounded receipt IDs consulted by nomination and its deterministic digest. This set includes ordinary support plus all parent-support, eligibility, and contradiction-trigger receipts. The birth frontier is the maximum organism-accepted ordinal in that exact consulted set. It is neither an arbitrary maximum over the full ledger nor a runner-provided value.

If authoritative organism/audit state cannot supply the exact complete provenance, initialization fails hard and closes as `prospective_provenance_unavailable`. The runner may not reconstruct it.

For frozen historical patterns, V2 opens a graph-local authority-escrow epoch: existing pattern, fixed polarity, lineage, structural state, and nested matching remain unchanged; organism-owned prior consulted receipts are pre-escrow discovery only; the organism derives the frontier from its accepted ledger; old receipts certify nothing.

## 2. Strict one-shot REAL transaction

The only lawful order is fail-hard and complete:

`open REAL event -> graph prediction and activation commitment -> execute selected action -> environment terminal mints grounded receipt -> receipt references and exactly matches pending commitment -> consume receipt -> update only precommitted cells -> graph-local maturity/revocation -> nominate/materialize new cells`

Exactly one one-shot pending event may exist per organism. The organism reserves its next contiguous ordinal. There is no post-outcome pattern matching, no retrospective full-ledger authority scan, and no nomination before the current receipt's authority lifecycle completes. A cell born during an event cannot occur in the prior commitment and cannot certify on that event.

The persisted pending record contains REAL frame identity, exact trace and typed-signal digests, predecessor and source-state identities, selected `GraphActuation`, pre-outcome classification, exact graph-emitted matching cell identities/canonical digest, pending-token identity, ordinal, and OPEN/CONSUMED state.

## 3. Replay and remint protection

The stable grounded-interaction fingerprint includes exactly:

- source organism identity;
- source state identity;
- predecessor;
- exact trace;
- selected actuation;
- successor;
- outcome terminal identity.

It excludes event ordinal.

Receipt ordinal must equal `organism.next_expected_ordinal`; delivery is gapless. Exactly one pending token is consumed once. Identical receipt redelivery is idempotent with zero mutation. A different receipt ID/ordinal for an already-seen interaction fingerprint causes zero mutation and then an integrity abort. Pending token/state, next ordinal, consumed receipt IDs, consumed token IDs, and interaction-fingerprint ledger survive serialization exactly.

## 4. Structural state versus authority

Prospective source cells begin `prospectively_certified=false`; legacy cells begin true only where organism-owned historical structure already authorized them; new cells begin false. Only a graph-emitted prospective-maturity leg sets authority true. A graph-local contradiction clears it. Both AVAILABLE and REFUTED inference roots require prospective authority; shadow matching may continue without it.

Original MATURE/PROBATION/TRIAL state, members, lineage, and nested-context matching behavior remain unchanged. Arm initialization is uniform from organism state. The host supplies no per-cell list, frontier, or authority Boolean. Tests require behavior parity and nested-context parity, not merely matching structural hashes.

## 5. REAL/VIRTUAL capability separation

VIRTUAL execution cannot reserve or advance an ordinal, open a pending event, emit a certification activation commitment, mint or accept a certification receipt, mutate authority/lifecycle/persistent state, or later pair its trace/token with a REAL receipt. Receipt acceptance requires exact equality with the pending commitment generated from the embedded REAL trace. Cross-frame pairing fails hard. Serialization with an open REAL pending event and after consumption must be exact.

## 6. Synthetic arm contract

Nomination runs exactly once on the discovery prefix with maturity authority disconnected. The frozen candidate manifest includes complete pattern, fixed polarity, lineage, complete transitive discovery receipt set/digest, and internally derived frontier. Exact hashes of every field match across arms.

Arms are: prospective; legacy same-ledger; prospective under a truthfully shuffled synthetic environment. Legacy may certify frozen candidates from prefix evidence. Both prospective arms certify only from suffix receipts. No suffix nomination is permitted.

Admission requires both the planted persistent candidate and at least one prefix-perfect spurious candidate. Failure closes as `synthetic_candidate_admission_failure`; no replacement seed or candidate search is allowed. The shuffled environment applies its frozen permutation before receipt minting, so every signed receipt remains truthful. The authority layer and runner cannot relabel outcomes.

## 7. Viewed KRK arm contract

Only prospective authority escrow and legacy same-ledger authority arms exist. There is no KRK shuffled-authority arm and no prospective-superiority gate or claim. Any shuffled-label calculation is offline, report-only telemetry: it cannot alter state, emit authority, or enter a gate.

## 8. Exposure admission and starvation

One qualifying exposure is a distinct, post-frontier, REAL, pre-outcome activation commitment for a frozen cell. Admission requires at least 24/32 organisms, each with at least one frozen cell having at least four distinct prospective activation opportunities.

The scan is outcome-blind, read-only, and persistently inert. Failure closes before outcome consumption as `prospective_evidence_starvation`. After outcomes, fewer than four qualifying activations is exposure starvation; four or more activations plus any contradiction is selectivity failure, never starvation.

## 9. Claim boundary

Viewed KRK material is permanently development data. It can establish only transaction/instrument integrity, nonzero mechanism engagement, finite-tape prequential behavior, graph-local revocation, and exposure starvation or selectivity failure. It cannot establish corrected generalization, superiority of prospective certification, or that adaptive self-certification was the dominant historical cause.

Only predictions committed before outcomes may enter comparisons. Same-tape final reclassification is descriptive only. Context-level and seed-level results are separate because the same 32 historical contexts across organisms are not independent samples. The historical 81 rows were co-supported by at least one mature depth-one child; they were not child-ablation results or causally necessary child advantages.

## Frozen prohibitions and current stop

No fresh data, R1, retired-65, unopened pools, recursion, negative exceptions, all-reply structure, new chess features, quorum, ensembles, threshold/lifetime/capacity/exposure changes, parameter tuning, replay, or V1 repair.

This turn implements and adversarially tests these contracts only. It stops before V2 preregistration/freeze, synthetic generation/execution, KRK exposure scanning, KRK outcome consumption, or any scientific run.
