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


## Pre-execution integration addendum - binding before code

This addendum supersedes any weaker implementation detail above. It authorizes
one mechanism-definition repair only and still forbids preregistration,
scientific runners, stream generation, KRK exposure/outcome consumption,
unopened validation/regression, fresh data, R1 and retired-65.

| integration contract | required implementation | exact focused test |
|---|---|---|
| Ledger-derived authority | Persist an immutable hypothesis digest. Reconstruct support/contradiction IDs and counts, Wilson values, transitions, certification and revocation only from accepted grounded receipts plus pre-outcome commitments plus graph emissions. Mutable cached fields have no authority. | `test_ledger_reconstruction_rejects_mutated_authority_caches`; `test_hypothesis_digest_and_frontier_mutation_fail_atomically`; `test_restore_reconstructs_then_consumes_and_rejects_replay` |
| Native structural parity | Define MATURE, PROBATION, TRIAL, PRUNED and SPECIALIZED exactly as `CompetenceContextCell.is_mature` and the native recursive matcher do. Cover both polarities, nested context, arms and restore. | `test_native_state_semantics_and_nested_matching_parity`; `test_available_refuted_arm_and_restore_parity` |
| Discovery epoch | Serialize one organism-owned epoch boundary. Only cells predating it can receive historical escrow. Post-epoch cells require native escrow at atomic birth. Candidate nomination closes once; certification requires closure; later birth/sync fails. | `test_discovery_epoch_distinguishes_historical_and_post_epoch_cells`; `test_nomination_closure_blocks_birth_sync_and_first_certification` |
| Ordinary atomic escrow | Before insertion, freeze polarity from the grounded discovery receipt plus graph availability-error/request, direct triggering receipt, actual classification/genome reads, transitive context ancestors, complete visible-prefix exclusion set and internal frontier. | `test_ordinary_materialization_creates_atomic_native_escrow`; `test_ordinary_nested_context_without_lineage_includes_ancestor_reads`; `test_birth_polarity_cannot_switch` |
| Specialization atomic escrow | Before insertion, inherit parent polarity and record grounded contradiction, actual eligibility traversal, parent support with transitive ancestry, child direct matches and complete visible-prefix exclusion. | `test_specialization_materialization_creates_atomic_native_escrow`; `test_specialization_omitted_ancestor_or_eligibility_read_fails` |
| Tombstone escrow | Pruning cannot erase or rewrite a cell's immutable birth escrow or hypothesis digest. | `test_pruned_post_epoch_cell_retains_birth_escrow` |
| Provenance validation | Reject missing, extra, duplicate, category-inconsistent, unknown, post-birth or polarity-inconsistent reads. The genome/runner cannot supply polarity, read sets, frontier, historical status or target IDs. | `test_nomination_escrow_rejects_noncanonical_provenance`; production-signature inspection in the same test |
| Strict REAL transaction | Preserve receipt-before-prediction, one pending event, issuer/signature/receipt ID, exact typed trace/source/action/predecessor/successor/terminal, replay/remint, and VIRTUAL separation across restore. | `test_real_transaction_adversarial_matrix`; `test_restore_reconstructs_then_consumes_and_rejects_replay` |
| Bound outcome-blind exposure | Accept only canonical graph-produced pre-outcome commitments/probes. Bind canonical terminal, trace actuation, source manifest, deterministic successor, frozen candidate/topology digests and exact non-outcome schema. | `test_exposure_rejects_fake_terminal_source_topology_and_extra_fields`; `test_exposure_rejects_action_trace_successor_and_outcome_fields` |
| Physical exposure identity | Terminal aliases cannot multiply one physical interaction. Invented organism/state clones fail. Raw cohort manifests remain source/candidate bound. | `test_physical_exposure_deduplicates_terminal_aliases`; `test_raw_cohort_rejects_invented_source_clone` |
| Prefix-only candidate freeze | The organism nominates once through its native graph/genome path, closes nomination, and exposes one frozen candidate/polarity/escrow manifest for later arm cloning. No suffix growth is connected. | `test_prefix_nomination_freezes_one_cloneable_candidate_manifest`; `test_suffix_growth_api_is_absent_or_fail_closed` |
| V1 adversarial preservation | Restore any causal/integrity check lost in the prior rewrite, including bad signature, dual pending, cross-frame pairing and functional post-restore consumption. | covered by the REAL transaction and restore tests above |

### Immutable hypothesis identity

The hypothesis digest must cover:

- exact members/pattern and fixed polarity;
- lineage parent, specialization depth and native structural state;
- initialization origin: historical or prospective;
- exact categorized nomination operation reads;
- complete transitive ancestor provenance;
- complete discovery-exclusion receipt set;
- organism-derived birth frontier.

The digest is checked at initialization, REAL opening, consumption, dump and
restore. Changing the hypothesis, escrow, exclusion set or frontier is an
atomic integrity failure.

### Derived-state law

`ProspectiveAuthorityState` may persist caches for inspection, but none may
be trusted. Before every authority-bearing operation the organism independently
replays its accepted V2 ledger in ordinal order. Each receipt must be grounded,
previously committed while outcome-blind, post-frontier, graph-matched to the
same frozen cell and accompanied by the persisted graph lifecycle emission.
The replay derives support/contradiction membership, counts, Wilson values,
transition sequence, current certification and revocation. Persisted caches
must equal that derivation exactly or the operation fails before mutation.

### Native state law

No local reinterpretation may broaden native authority. Maturity is whatever
the authoritative `CompetenceContextCell.is_mature` property returns.
PROBATION may be usable only through the same lineage-specific nested rule as
the native matcher. TRIAL and PRUNED are not authoritative. SPECIALIZED must
not be treated as mature unless the native property does so. The historical
TRIAL policy remains fail-hard rather than being silently reclassified.

### Organism-owned epoch and atomic materialization

`from_organism` opens and serializes the prospective discovery epoch using
organism state, not runner cell flags. Existing eligible cells are historical.
Thereafter, ordinary and specialization materializers must construct and
validate a `NominationEscrow` before inserting the cell. Closing nomination
freezes the candidate manifest irreversibly. The first certification event
requires closure. This package permits exactly one prefix nomination phase and
does not connect certification suffix receipts to further growth.

### Exposure schema law

Exposure input is a canonical graph-produced pre-outcome object, not caller
terminal text. The accepted raw schema is exact and outcome-free. It binds the
source manifest identity, source state, frozen candidate-manifest digest,
authority-topology digest, predecessor, trace, trace actuation, recomputed
successor, canonical completion terminal and matched frozen cell. Unknown
fields, outcome fields, invented identities, topology changes and action
disagreement fail. Interaction identity uses the canonical terminal and cannot
be multiplied by aliases.

### Stop rule

After implementation: run focused adversarial tests once, run the full
repository suite once, update the audit, commit and push, then stop for external
review. Do not create a runner or scientific artifact in this package.
