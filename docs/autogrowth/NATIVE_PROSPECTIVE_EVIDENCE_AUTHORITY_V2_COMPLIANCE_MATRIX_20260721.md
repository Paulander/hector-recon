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
| Ledger-derived authority | Immutable hypothesis digest plus full replay of accepted receipts, pre-outcome commitments and graph emissions; mutable caches have no authority. | `test_ledger_reconstruction_rejects_mutated_authority_caches`; `test_hypothesis_digest_and_frontier_mutation_fail_atomically`; `test_serialization_duplicate_remint_and_virtual_isolation` |
| Native structural parity | MATURE, PROBATION, TRIAL, PRUNED and SPECIALIZED follow `CompetenceContextCell.is_mature` and the recursive native matcher exactly, in both authority arms and both polarities. | `test_historical_escrow_parity_and_probation_parent_matching`; `test_graph_revocation_refuted_authority_and_disconnect`; `test_native_specialized_is_not_mature_for_nested_authority` |
| Discovery epoch and ordinary atomic escrow | The serialized organism epoch distinguishes historical cells; ordinary materialization fixes polarity and complete read/exclusion/ancestor provenance before insertion; closure is irreversible. | `test_discovery_epoch_atomic_native_escrow_and_closure` |
| Specialization atomic escrow | Specialization inherits parent polarity and records the actual contradiction, eligibility traversal, support, ancestors, direct matches and full visible prefix before insertion. | `test_specialization_materialization_has_exact_native_escrow` |
| Tombstone escrow | Pruning cannot erase or rewrite immutable birth escrow. | `test_pruned_post_epoch_cell_retains_birth_escrow` |
| Provenance validation | Missing, changed, category-inconsistent, post-birth and polarity-inconsistent provenance fails; polarity/read/frontier/identity are organism-derived. | `test_discovery_epoch_atomic_native_escrow_and_closure`; `test_specialization_materialization_has_exact_native_escrow`; `test_frozen_hypothesis_rejects_nonexact_provenance` |
| Strict REAL transaction | Receipt-before-prediction, one pending event, issuer/signature/ID, typed trace, source/action/predecessor/successor/terminal, replay/remint and VIRTUAL separation are fail-closed across restore. | `test_complete_receipt_validation_and_atomic_structure_guard`; `test_real_transaction_order_signature_and_dual_pending`; `test_serialization_duplicate_remint_and_virtual_isolation` |
| Bound outcome-blind exposure and physical identity | Only organism-issued canonical pre-outcome commitments are accepted; source/candidate/topology/action/successor/terminal are bound and aliases deduplicate. | `test_bound_exposure_rejects_aliases_mutations_and_outcomes`; `test_exposure_receipt_interaction_alignment` |
| Prefix-only candidate freeze | One organism-native prefix nomination is transactionally imported and frozen; sync/birth after closure fails; suffix growth is absent. | `test_discovery_epoch_atomic_native_escrow_and_closure` |
| V1 adversarial preservation | The adjacent V1 authority, native envelope, trace authority and specialization suites remain green. | `test_native_prospective_evidence_authority.py` plus the three adjacent native focused modules |

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


## Final execution-readiness repair - binding before code

This addendum supersedes only implementation details that conflict with it. It
authorizes no scientific runner, stream, tape, canonical cohort registry,
preregistration, unopened confirmation data, R1, or retired-65 access.

| readiness contract | required implementation | exact focused test |
|---|---|---|
| Signed-receipt evidence identity | Validate every grounded receipt, reconstruct the native evidence record, and require exact active-signal, typed-provenance, outcome, actuator, completion-terminal, and policy-response parity before any epoch state is trusted. | `test_receipt_evidence_record_parity_rejects_each_mutated_field_atomically` |
| Complete escrow and two frontiers | Bind and semantically revalidate the complete native escrow operation, fixed polarity, trigger, categorized reads, graph request states, considered/selected contexts, transitive ancestors, exclusion set, exact nomination-read frontier, and conservative certification frontier. | `test_complete_escrow_frontiers_and_semantic_revalidation` |
| Atomic specialization | Run receipt validation, insertion, parent transition, eligibility, escrow, child registration, and wrapper sync under one copy-on-write transaction; injected failure at any boundary leaves the canonical continuation unchanged. | `test_specialization_transaction_rolls_back_every_failure_boundary` |
| Experimental seal and identical arms | Freeze schema/implementation, mode, source, epoch, close event, candidates, escrows, and topology in one initialization identity; clone prospective and legacy arms from one closed native nomination without regrowth. | `test_experimental_identity_and_candidate_identical_arms_are_immutable` |
| Executed graph identity | Hash the canonical graph snapshot actually evaluated, including roots, nodes, edges, confirmation policies, terminal roles/predicate identities, and lifecycle constants. | `test_topology_digest_tracks_executed_graph_semantics` |
| Laboratory cohort authority | Keep tape/cohort identity outside the learner; re-load exact frozen organisms through a laboratory registry and reject fabricated, post-outcome, open-transaction, unclosed, duplicate, and noncanonical commitments. | `test_registry_bound_exposure_rejects_fabrication_and_admits_24_of_32` |
| Version/native parity | Bump incompatible schemas, reject prior payloads explicitly, preserve AVAILABLE/REFUTED state and identity parity, keep confidence telemetry non-authoritative, fail on historical live TRIAL, and admit tombstone-only historical sources. | `test_v3_schema_native_parity_telemetry_and_tombstone_only_admission` |
| Behavior preservation | On one already-viewed engineering tape, compare ordinary native growth with and without escrow instrumentation and require exact proposal/cell order, members, state, mature polarity, lifecycle, nesting, and classification parity. | `test_prospective_escrow_instrumentation_preserves_viewed_tape_behavior` |

### Architecture boundary

Run IDs, cohort registries, tape identities/order, package hashes,
preregistration gates and artifact adjudication are laboratory state. They may
not become learner terminals, action features, nomination inputs, or permanent
dependencies of ordinary ReCoN operation. Integrity digests and the current
HMAC are tamper-evident checks, not proof against a caller that can execute the
repository code.

Prefix-only global nomination closure is an experimental isolation device. The
target continuously growing organism will use per-candidate birth transactions:
commit existing activations, execute, ground the outcome, update existing
cells, then nominate new cells. It will not require a permanent global or
human-authored learning phase.

`nomination_read_frontier` is the maximum ordinal among exact categorized and
transitive reads. `certification_frontier` is the maximum ordinal in the full
visible-prefix discovery exclusion set. Prospective authority uses only the
larger certification frontier.

### Validation and stop

Run the eight readiness tests, the adjacent native/V1 suites, one behavior-
preservation engineering control on already-viewed material, and one full
repository suite. No fresh or unopened confirmation data may be accessed.
Update the audit and `BRIEF`, commit and push if clean, then stop for external
review. The next reviewed package—not this one—may construct the candidate-
identical synthetic discriminator through the actual V2 core.


## 2026-07-22 readiness stop

The binding behavior-preservation control failed before the execution-readiness
repair could close. On the already-viewed engineering tape, ordinary native
growth and trigger-fixed escrow instrumentation selected different context
parents at structural round 2/request 0:

- native: `context:competence_context_0001`;
- escrow-instrumented: `context:v2_child`.

The base terminal and materialized cell identity were otherwise the same. This
is a causal proposal-input difference, not permitted metadata. The originally
planned parity test is superseded by the executable abort regression
`test_trigger_fixed_polarity_behavior_gate_aborts_on_context_divergence`.

Per the frozen stop rule, the uncommitted implementation draft was discarded.
The registry canary, adjacent suites and full suite were not run, and no
scientific runner was constructed. No fresh or unopened confirmation data were
accessed; the diagnostic reconstructs already-viewed retired train and
validation-named development material. See
`docs/autogrowth/NATIVE_PROSPECTIVE_EVIDENCE_AUTHORITY_V2_EXECUTION_READINESS_ABORT_20260722.md`.


## 2026-07-22 causal-instrument correction

External adjudication found that the preserved `de790fd` behavior
comparison used unequal evidence ledgers (4 native records versus 12 wrapper
records). That result remains an instrument abort, but its fixed-polarity causal
interpretation is withdrawn.

The source boundary now requires exact receipt/evidence identity and record
equality before prospective wrapping, validates all cell evidence references,
and opens the epoch copy-on-write without legacy hydration. The incoherent
8-receipt/0-evidence fixture aborts atomically. Corrected matched-ledger parity
passes for both the 8+4 engineering fixture and the exact frozen 96+4 historical
smoke. All learner-visible behavior is exact; only escrow/provenance metadata
and fixed polarity attached solely to final PRUNED tombstones may differ. Phase
A is therefore closed and the remaining readiness rows below are again
authorized for implementation.


## 2026-07-22 execution-readiness closure

The matched-ledger correction and all remaining readiness contracts are closed
passing. Complete two-frontier escrows, copy-on-write specialization, a sealed
candidate-identical arm constructor, digests of the graph actually executed,
and the outside-the-learner cohort registry are now implemented. The frozen
32-organism engineering canary admitted exactly 24/32 using 128 graph-produced
commitments; all adversarial authority controls failed closed. The final full
repository suite passed 1010 tests in 12734.63 seconds.

This is engineering readiness only. No scientific runner, competence outcome
stream, fresh or unopened data, R1, KRK outcome, or retired-65 successor was
accessed. The complete result and before/after authority table are in
`docs/autogrowth/NATIVE_PROSPECTIVE_EVIDENCE_AUTHORITY_V2_EXECUTION_READINESS_CLOSURE_20260722.md`.
