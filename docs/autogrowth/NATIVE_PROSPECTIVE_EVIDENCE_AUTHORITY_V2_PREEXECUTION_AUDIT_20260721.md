# Native prospective evidence authority V2 - pre-execution implementation audit

Status: bounded engineering repair after external review. V1 remains immutable
at `726e74a`. The compliance matrix was frozen at `9362475`. The initial
implementation and audit at `2553ffd` remain in Git history, but the authority
claims made there are superseded by this document.

No V2 preregistration, runner, stream, KRK exposure scan, KRK outcome
consumption, fresh data, R1, retired-65 or unopened validation/regression pool
was created or accessed.

## Retraction and external-review disposition

The `2553ffd` audit called activation and lifecycle decisions graph-owned even
though Python had already calculated matching, `projected_mature` and
`projected_revoke` ID sets for membership terminals to echo. That description
was too strong and is withdrawn.

| blocking review finding | repaired disposition |
|---|---|
| historical PRUNED `polarity=None` cells failed initialization | PRUNED tombstones are preserved separately and excluded from live authority |
| historical escrow claimed reconstructed nomination provenance | all accepted historical receipts are conservatively marked pre-escrow; provenance explicitly says historical complete ledger |
| new birth had no exact nomination-read contract | exact categorized birth metadata is mandatory; absent metadata fails hard |
| Python selected matching/maturity/revocation IDs | graph terminals directly measure frozen patterns, receipts, counters, Wilson state and authority |
| lifecycle disconnection was not causal | pytest disconnects the terminal predicate; counters update but authority cannot transition |
| live structure lacked a binding invariant | canonical cell and topology invariants are checked at init/open/consume/restore |
| exposure identity used ordinal and accepted caller qualification | ordinal-free raw manifests are deduplicated and cohort qualification is recomputed |
| issuer, receipt ID and typed-signal checks were incomplete | all are explicit gates before accounting |

## Requirement-to-code map

Line anchors refer to the repaired source before the final documentation commit.

| requirement | implementation | adversarial evidence |
|---|---|---|
| historical/full-ledger versus exact-new provenance | source lines 72, 566, 1128 and 1186 | tests lines 254, 327, 853 |
| tombstone/live distinction | source 566-645 | exact historical artifact test 254; new-live birth test 327 |
| frozen live structure and topology | source 155, 680-739 | member/lineage/state failures 423; serialization 626 |
| recursive pattern and PROBATION-parent semantics | source 347-390 | nested child test 291 |
| graph terminal measurement | source 392-451 | maturity test 500; revocation/REFUTED test 544 |
| canonical graph and emissions | source 454-500 | lifecycle controls; no production disconnection argument |
| one-shot REAL commitment | source 777-907 | transaction and structural test 423 |
| receipt issuer/ID/typed/source/action/successor validation | source 908-1011 | receipt mutation matrix 423 |
| graph lifecycle plus generic materialization | source 1012-1127 | lifecycle tests 500 and 544 |
| exact nomination read-set attachment | source 1128-1265 | ordinary/specialized/missing metadata test 327 |
| VIRTUAL and serialization isolation | source 1313-1398 | test 626 |
| raw stable exposure and cohort recomputation | source 1399-1655 | tests 736 and 806 |

## Causal authority table

| operation | owner | Python implementation role | resulting authority |
|---|---|---|---|
| R0 action | frozen native R0 graph | opens frame and receives exact actuation/trace | graph-owned |
| pattern activation | per-cell commitment terminal | predicate reads frozen structure and typed signals | graph measured; no matching-ID input |
| AVAILABLE/REFUTED | per-cell authority terminals and formal roots | materializes classification from emitted roots | graph gated |
| support/contradiction | grounded-receipt terminals | validates receipt, then increments only emitted cells | graph measured |
| maturity | per-cell maturity terminal | predicate computes projected count and Wilson law; Python sets bit only for emission | graph decided |
| revocation | per-cell revocation terminal | predicate reads contradiction/current authority; Python clears bit only for emission | graph decided |
| nomination pattern/polarity | wrapped genome plus required birth metadata | sync validates metadata and records invariant | organism-owned, integration-blocked |
| environment transition/outcome | chess adapter and signed completion terminal | executes graph action and measures checkmate | environment-owned |
| serialization/replay | organism transaction ledger | canonical manifest, HMAC and validation | organism-owned |
| exposure | commitment graph plus scanner | canonicalizes raw interactions and recomputes fixed gate | measurement only |

The production graph builder/runner has no disconnection parameter. Production
`consume` accepts only one grounded receipt. Tests disconnect by monkeypatching
a terminal predicate inside pytest; there is no organism API for injected
matching, maturity, revocation or qualification IDs.

## Historical compatibility result

The sole authorized read-only compatibility test loads the exact already-viewed
ordinal-0 local-contrast artifact and checks its committed compressed,
uncompressed and continuation-V3 digests.

Observed immutable facts:

- 155 total historical cells;
- 152 PRUNED tombstones, all with `polarity=None`;
- 3 live MATURE/PROBATION hypotheses;
- 96 accepted historical receipts;
- each live escrow uses exactly those 96 receipts as conservative historical
  discovery evidence;
- the internally derived frontier is the maximum accepted ordinal;
- serialization/restore is exact;
- the source organism digest is unchanged.

This is compatibility evidence only. It is not a KRK exposure or outcome run.

## Graph lifecycle causal result

On the touched fixture, four distinct post-frontier grounded supports cause the
connected graph maturity leg to emit authority. With the maturity terminal
disconnected, the same cells reach support count four while authority remains
false. There is no Python maturity-ID argument.

After connected maturity, one grounded contradiction makes the connected
revocation terminal clear authority. With the revocation terminal disconnected,
the contradiction is accounted but authority remains set. A separate
fixed-polarity REFUTED cell matures from four real noncompletion receipts and
emits REFUTED on its next matching trace.

These are engineering causal tests, not a scientific V2 result.

## Structure, receipt and exposure integrity

Members, lineage parent and StemCell structural state are each mutated after a
REAL event opens. Every mutation fails before receipt accounting or authority
change. Open and consumed states serialize exactly.

Receipt controls reject wrong issuer, a re-signed but invalid receipt ID, wrong
source, ordinal gap, wrong token, changed trace, typed-signal mismatch, wrong
successor and wrong terminal. Exact replay is idempotent; a new receipt identity
for the same interaction fails as reminting.

The scanner reads no outcome field. Four copies of one exact interaction
collapse to one opportunity per matched cell; four genuinely distinct traces
produce four. VIRTUAL and mixed-organism traces fail. Scanner and receipt
fingerprints agree for the same pending REAL interaction.

Cohort adjudication rejects caller `qualifies`, bad raw digests, mixed source
identities and malformed opportunity identities. It derives the 24/32 decision
only from verified raw per-cell opportunity IDs.

## Remaining architectural blocker

The existing historical growth code does not record
`prospective_nomination_read_set` at the actual birth event. The wrapper can
enforce and consume an exact read set, and tests demonstrate ordinary and
specialization semantics, but no claim is made that the current growth runtime
already supplies it.

Runner construction and scientific preregistration remain blocked. The next
review should decide where the genome records direct, parent-support,
eligibility and contradiction-trigger receipt IDs atomically with nomination.
They must not be reconstructed afterward.

## Validation and stop

Focused repaired suite before final API tightening: 10 passed in 1,023.71
seconds (0:17:03). Focused maturity/revocation rerun after removing the
production disconnection argument: 2 passed, 8 deselected in 530.29 seconds
(0:08:50).

Full repository suite: 994 passed in 4,910.68 seconds (1:21:50). No
scientific runner or data path was exercised by these commands.

This package stops after documentation, commit and push. It does not proceed
to a V2 runner, freeze, stream, exposure scan or outcome consumption.

## 2026-07-21 integration closure addendum

This addendum supersedes the remaining-blocker section above. Work began from
exact clean commit `644a213`; the binding implementation matrix was updated,
committed as `ec1d0d8`, and pushed before code changed. No preregistration,
scientific runner, synthetic/KRK outcome stream, unopened pool, R1, fresh data,
or retired-65 data was opened. The engineering tests reconstruct already-viewed
retired train and validation-named development material; no fresh or unopened
confirmation data were accessed. Prior artifacts and negative results remain
untouched.

### Closed mechanism boundaries

- `ProspectiveAuthorityState` is now a checked cache. Every authority-bearing
  operation replays the accepted V2 receipt ledger, pre-outcome commitments,
  and graph lifecycle emissions and requires exact support, contradiction,
  Wilson, transition, certification, revocation, token, fingerprint, emission,
  ordinal and transaction parity.
- Every hypothesis has a canonical immutable digest covering structure, fixed
  polarity, lineage/depth/native state, initialization origin, categorized
  operation reads, transitive ancestors, conservative exclusion and the
  organism-derived frontier.
- The serialized native organism owns the discovery epoch. Prefix discovery
  receipts expand the historical exclusion ledger. Before freeze, only the
  native legal `MATURE -> PROBATION` revocation can alter an already-open live
  structural state. Candidate sync, prefix nomination and closure validate on
  a deep copy and adopt only after success.
- Ordinary and specialization materializers create and validate immutable
  `NominationEscrow` before cell insertion. Pruned post-epoch births preserve
  the same escrow in their tombstones. Prefix closure freezes the exact
  candidate identity manifest and blocks all later births/sync.
- Native maturity parity is exact: MATURE is authoritative; lineage-specific
  PROBATION follows the native recursive matcher; TRIAL is rejected as an
  unsupported historical contract; PRUNED is a tombstone; SPECIALIZED is not
  silently treated as mature.
- Exposure is now an organism-issued, HMAC-bound, exact-schema pre-outcome
  commitment. The scanner verifies canonical terminal, trace/action, source
  manifest/state, deterministic successor, frozen candidate/topology, matching
  cells and ordinal-free physical interaction identity. It cannot qualify a
  caller-authored probe or multiply one interaction through terminal aliases.

### Causal authority after integration

| operation | authority owner | host role |
|---|---|---|
| observation and completion | chess environment adapter | execute the graph action and mint the one grounded terminal receipt |
| action and typed signal trace | frozen native R0 graph | open the REAL or isolated VIRTUAL frame |
| ordinary/specialized proposal | native graph request plus generic genome | materialize the emitted mutation only |
| polarity and nomination evidence | atomically created native `NominationEscrow` | no runner-supplied polarity, frontier, read set, historical flag or target ID |
| candidate freeze | serialized organism discovery epoch | transactional sync/serialization |
| support, contradiction, maturity, revocation | prospective authority graph replayed from grounded receipts | persist checked caches and execute graph emissions |
| outcome-blind exposure | organism-issued canonical commitment | deduplicate and report; no outcome access or qualification input |

The earlier statement that native materialization lacked exact nomination
provenance is therefore closed for this engineering path. This does not make a
scientific V2 claim: no competence learner was run, no gate was evaluated, and
no KRK generalization or R1 handover evidence was produced. Live suffix growth
remains deliberately absent.

### Validation

- exact frozen historical artifact compatibility: passed; committed source
  continuation digest unchanged;
- adjacent native envelope, trace-authority, contradiction-specialization and
  preserved V1 authority suites: **42 passed in 665.45 s**;
- final V2 adversarial module: **16 passed in 1,376.36 s (22m56s)**;
- full repository suite: `1000 passed in 4,913.32 s (1:21:53)`.

Stop remains external review after clean commit and push. Scientific package
construction and execution are not authorized by this addendum.


## 2026-07-22 execution-readiness abort

The final readiness package stopped at its binding behavior-preservation
control. On an identical four-receipt already-viewed engineering tape, native
growth selected `context:competence_context_0001` while trigger-fixed escrow
instrumentation selected `context:v2_child` at structural round 2/request 0.
The same base atom and materialized cell ID were retained, so this is a context-
choice divergence rather than metadata.

The exact regression passed on the restored reviewed baseline: 1 passed and 16
deselected in 277.73 seconds (4m37s). This passing diagnostic preserves the
abort; it is not a parity pass. The implementation draft was discarded, and
registry, adjacent-suite and full-suite stages were not run after the stop.
No canonical runner, stream, fresh/unopened confirmation data, R1, or retired-65
access occurred. External adjudication is required before readiness work or a
scientific discriminator resumes. See
`docs/autogrowth/NATIVE_PROSPECTIVE_EVIDENCE_AUTHORITY_V2_EXECUTION_READINESS_ABORT_20260722.md`.


## 2026-07-22 matched-ledger adjudication

The `de790fd` abort was causally confounded. Its ordinary arm reviewed
four records, while prospective wrapping silently imported eight historical
receipts and reviewed twelve. The original abort text is preserved, but it is
not evidence against fixed-at-nomination polarity.

Prospective wrapping now rejects noncanonical receipt/evidence ledgers before
mutation and performs no implicit migration. The exact frozen historical
organism passes with 96 receipts and 96 exact derived evidence records.
Corrected state-identical growth produced exact proposals, graph
activation/error values, lifecycle/statistics, topology, classifications and
actions in both the 8+4 fixture and the frozen 96+4 smoke. The only permitted
differences were escrow/provenance metadata and polarity retained solely on
final non-authoritative PRUNED tombstones. Phase A passed; execution-readiness
repair may continue without weakening fixed polarity.
