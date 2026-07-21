# Native prospective evidence authority V2 - compliance matrix

Status: engineering contract plus reviewed repair. V1 remains immutable at
`726e74a`. The initial V2 implementation at `2553ffd` is preserved in
history but was blocked by external review. This document now describes the
bounded authority repair; it does not authorize preregistration or execution.

## Ownership matrix

| contract | owner | persisted evidence | prohibited host authority | causal test |
|---|---|---|---|---|
| Historical compatibility | organism escrow | complete accepted historical ledger, internally derived maximum frontier, live frozen structure, tombstone manifest | reconstructed nomination provenance, caller frontier, treating PRUNED tombstones as hypotheses | exact 155-cell artifact: 152 tombstones excluded and 3 live cells escrowed |
| New-candidate birth law | graph-owned nomination plus birth metadata | fixed discovery-only polarity and exact categorized read set | post-hoc provenance reconstruction, polarity=None on a live candidate | ordinary/specialized exact-read tests; missing growth metadata fails hard |
| Graph-native measurement | authority terminals | frozen pattern/polarity, current authority, prospective counters, Wilson state, grounded receipt | precomputed matching, maturity, or revocation ID sets | connected maturity/revocation and terminal-disconnection controls |
| Live structure | organism invariant | members, polarity, lineage, depth, structural state, authority node IDs/topology identity | silent rebasing after mutation | open/consume/restore checks and atomic member/lineage/state failures |
| REAL transaction | organism controller plus environment terminal | pending token, exact trace/typed-signal/source/action/structure identities | post-outcome matching, retrospective authority, host outcome relabeling | ordering, issuer, receipt-ID, trace, typed-signal, source, action, successor and terminal checks |
| Replay/remint | organism ledger | consumed receipt/token IDs and stable interaction fingerprints | ordinal-based identity, remint, gap, collision | idempotent replay and new-ID remint failure |
| REAL/VIRTUAL split | capability boundary | REAL commitments only | VIRTUAL receipt, authority, ordinal, or later REAL pairing | virtual isolation and cross-frame failure |
| Exposure | read-only graph commitment scanner | canonical raw opportunity rows and digest | outcomes, caller `qualifies`, ordinal-distinct duplicates | 4 same -> 1; 4 distinct -> 4; raw cohort recomputation |
| Interpretation | report-only aggregation | pre-outcome rows and separate context/seed summaries | final reclassification gate or causal-child wording | wording and evidence-boundary audit |
| Stop integrity | future canonical runner | exact abort rows and hashes | in-place repair or selective rerun | no runner exists in this package |

## 1. Historical escrow and exact future birth

Historical PRUNED cells, including `polarity=None` tombstones, are retired
records rather than live hypotheses. They are excluded from authority topology
and preserved in a separate immutable tombstone manifest.

Historical MATURE/SPECIALIZED and PROBATION cells retain members, polarity,
lineage, depth and structural state. Because their original nomination read
sets were not recorded, their escrow conservatively treats the complete prior
accepted-receipt ledger as pre-escrow discovery evidence and derives the
frontier as its maximum ordinal. This is deliberately labelled
`historical_complete_accepted_ledger`; it does not claim reconstructed exact
nomination provenance.

A genuinely new live candidate is stricter. Its birth metadata must contain the
exact read categories `direct`, `parent_support`, `eligibility` and
`contradiction_trigger`. Ordinary candidates require nonempty direct reads;
specializations require all four relevant categories. Their canonical union is
the discovery ledger and its maximum ordinal is the birth frontier. Missing
metadata closes as `prospective_provenance_unavailable`; the wrapper never
reconstructs it from later state.

The current historical growth interface does not yet emit this metadata. That
is an explicit integration blocker, not silently repaired in this package.
V2 scientific preregistration is therefore not authorized.

## 2. Substantive graph authority

The organism owns a canonical authority topology with seven terminal roles per
live cell: commitment, AVAILABLE, REFUTED, support, contradiction, maturity and
revocation. Each terminal measures the frozen recursive pattern against the
committed typed trace. Lifecycle terminals additionally measure post-frontier
receipt identity, fixed polarity, current counters, Wilson lower bound and
current prospective authority.

Python supplies generic terminal measurements, validates the environment
receipt and materializes graph emissions. It does not precompute or inject
matching, maturity or revocation cell-ID sets. The production API has no
disconnection argument and `consume` has no maturity/revocation-ID parameter.
Focused controls replace a terminal predicate only inside pytest: satisfied
Python-side counters cannot mature without the graph leg, and a grounded
contradiction cannot revoke without the graph leg.

## 3. Frozen live structure

Every live cell has a canonical invariant covering members, polarity, lineage
parent, specialization depth, structural StemCell state, all authority-node
identities and its topology identity. The aggregate authority topology is also
persisted.

The invariant is verified at initialization, REAL-event opening, receipt
consumption, serialization and restore. Mutation between open and consume
fails before receipt accounting or authority transition. A legitimate
nomination explicitly appends a new invariant and records a topology-extension
event; it never silently rebaselines an existing cell.

Nested matching preserves historical semantics: a nested child can use a
MATURE/SPECIALIZED parent, or its own lineage parent while that parent is in
PROBATION. The structural state itself remains frozen during the escrow.

## 4. Strict REAL transaction and receipt integrity

The lawful order remains:

`open REAL -> graph commitment -> execute graph action -> environment receipt
-> validate exact pending event -> graph lifecycle -> materialize emission
-> nomination may follow`.

The pending event persists REAL frame identity, exact graph trace, typed-signal
digest, source organism/state, predecessor, selected `GraphActuation`,
pre-outcome classification, graph-emitted commitments, live-structure digest,
token, ordinal and terminal identity.

Receipt validation requires the expected issuer, valid signature, recomputed
receipt ID, exact REAL trace and typed-signal digest, source identity, selected
action, predecessor, deterministic successor, completion terminal, observed
environment outcome and stable interaction fingerprint. Matching is repeated
by the graph at consumption and must equal the pre-outcome commitment.

## 5. Replay, remint and frame capability

The interaction fingerprint excludes ordinal and includes source
organism/state, predecessor, exact typed trace, selected actuation,
deterministic successor and terminal identity. Exact duplicate receipt delivery
is idempotent. A new receipt identity for the same interaction fails atomically.

VIRTUAL sessions remain read-only. They cannot open a certification event,
reserve an ordinal, mint or consume a receipt, emit a commitment or mutate
authority. An exact REAL pending transaction and consumed transaction both
round-trip through serialization.

## 6. Outcome-blind exposure

One raw opportunity is a post-frontier REAL graph commitment identified by the
stable interaction fingerprint plus matched frozen cell. The raw manifest
contains source organism/state, predecessor, exact trace, action, deterministic
successor, terminal, cell, interaction fingerprint and opportunity ID.
Repeated identical interactions collapse regardless of how often supplied.

Cohort adjudication accepts only raw manifests, verifies their digests,
recomputes interaction and opportunity identities, rejects mixed/VIRTUAL
sources and caller-supplied `qualifies`, then recomputes the fixed
four-opportunity per-organism rule. The frozen cohort rule remains at least
24/32 organisms.

## 7. Scientific package boundaries

The original synthetic and viewed-KRK arm contracts remain conceptually frozen:
candidate-identical discovery; truthful environment shuffle; prospective versus
legacy same-ledger authority; no KRK shuffled-authority runtime; only
pre-outcome predictions in inferential comparisons. No stream, seed, manifest,
runner or scientific result has been constructed in this repair.

Viewed KRK remains development data. It can support transaction integrity,
mechanism engagement, graph-local revocation, exposure starvation or
selectivity failure only. It cannot establish fresh generalization,
prospective superiority or historical causal dominance.

## Frozen prohibitions and current stop

No fresh data, R1, retired-65, unopened validation/regression, KRK exposure
scan, outcome consumption, recursion, feature addition, quorum, ensemble,
threshold/lifetime/capacity change, V1 repair, V2 runner, preregistration or
stream generation occurred.

The next permitted action after external review is to close the nomination
birth-metadata interface. Until that is designed and reviewed, V2 remains an
engineering mechanism, not an executable scientific package.
