# Branch logbook

## Current branch at a glance

Read this table first. The detailed evidence ledger below preserves exact
boundaries and artifact identities.

| Experiment | Conditions | Result |
| --- | --- | --- |
| Incremental-history Phase 1 | 32 events, three arms, incremental versus full replay after every event | Exact parity passed; event-wall speedups were `2.78x-4.37x`. |
| Incremental-history boundary | Restored event 32; incremental events 33-64; full reconstruction at event 64 | Additive-chain, full-history, checkpoint and round-trip parity passed. |
| Fixed-pool R0 depth | Seed `2026082801`; one core; fixed 48/16/16 pools | Joint validation/regression reached `1.0/1.0` at epoch 72; R0 training took `350.20 s`. |
| R1 epoch-1 integration gate | Same seed/pools; clean `1fef1bff`; one process/core; external `2700 s` watchdog | Exact epoch-1 snapshot passed in `2326.714 s`; cross-process resume then exposed a process-dependent pickle fingerprint. |
| Fixed two-hour development shot | Same seed/pools; clean `1fef1bff`; one process/core; `7200 s` cooperative ceiling | Exact epoch-4 stop after `7627.513 s`: 187 unique REAL observations, 29 mates, zero AVAILABLE handoffs; saved state is permanently availability-locked. |
| Resume repair canary | Data-free/test-scale resume; changed only wall/RSS controls; two hash seeds | Canonical base identity was stable across processes and resumed execution matched uninterrupted execution exactly. |
| VIRTUAL hot-path canary | Same saved epoch-4 artifact and query; runtime commit `7d56d5d5` | `48.241 -> 18.107 s` (`2.664x`); UNKNOWN, zero source mutation, exact continuation-manifest equality. |
| REAL rollback-clone canary | Same saved epoch-4 authority; runtime commit `7d56d5d5`; clone operation only | `5.114 -> 0.193 s` (`26.47x` clone-only); idempotent/rollback public transactions took `2.632/2.321 s` with exact parity. |
| Mixed-evidence request reachability | Commit `5efc88ce`; data-free `C,S,S,S,S` lifecycle, both polarities, incremental versus full replay | No request through S3; one request exactly at S4, anchored to the earliest C; parent remains UNKNOWN and never gains authority. |
| Specialized-child prospective gate | Same data-free fixture; actual birth, round-trip, then post-birth evidence | Child starts at zero; four clean supports certify it, while one matching contradiction plus four supports leaves it uncertified. Certified `S,S,S,S,C` revocation also remains exact. |

## Purpose and validity scope

Quick-scan ledger for the current development branch. Raw artifacts remain
authoritative. Every benchmark below is labeled
`DEVELOPMENT_VIEWED_NOT_SCIENTIFIC`: it may support software-runtime and exact
semantic-parity claims only, never a scientific ReCoN result or a frozen-run
inference. The constructed benchmark uses one persistent black knight to stay
materially disjoint from the protected pure-KRK corpora; its two D4 geometries
are not representative workload samples.

Current branch: `codex/v2-intrinsic-r0-r1-development`, forked from
`97cce727442da25c4a5c443897550ccc9c6758b4`. Use `git rev-parse HEAD` for the
current implementation commit.

`reports/autogrowth/development/` is local and untracked at this snapshot.

## Detailed evidence ledger

### Code lineage

- `f9f12628cb303c9326a00acfc138e0d471410a65` — audited starting point for
  incremental-history runtime work.
- `93ffeba3ac46d47be30a5225ed092151bef03ec3` — incremental REAL-history
  validation reclosure; retained explicit full reconstruction at trust
  boundaries.
- `b6848ef4e3eb27d022ac6c67f3c903c962907737` — authority-graph settlement
  optimization; audited core for the v2 development benchmark.
- `97cce727442da25c4a5c443897550ccc9c6758b4` — bounded, atomic Phase-1
  checkpoint runner and tests.
- `f482aac677228817d5924e6b139a824249110e85` — persistent V2 intrinsic R0 ->
  R1 development integration and exact snapshot/resume boundary.
- `a998acda2d97d7ac9cabf2d0abbe930097125344` — corrected the V2 duplicate
  index to derive predecessor FENs from signed discovery and consumed REAL
  receipts rather than the intentionally FEN-free reference schema.
- `1fef1bff3cf9be0b9f8273f2af3bf0ab768467c9` — hoisted the frozen-R0
  identity audit and removed unused exact/serialized audit work from each V3
  continuation manifest.
- `7d56d5d55af8459b9e1a053c54f8a103033fd7d6` — process-stable exact R1
  resume identity, snapshot edge-alias repair, guarded dream hot path, and
  frozen-R0-sharing REAL rollback transactions.
- `5efc88cecd9603e5f30016470a68bdfcce9813b0` — v7 mixed-evidence
  specialization reachability, exact causal request identity and boundary-only
  request-evidence reclosure.

## Evidenced experiments

### Prior 64-event incremental canary

- Conditions: newly generated one-cell KRK development canary on Apple arm64,
  macOS 26.6.1, Python 3.12.13; audited source `f9f12628`; focused tests
  `4 passed`, adjacent data-free tests `22 passed`.
- Result at 64 accepted events: incremental/legacy invariant medians
  `0.0495/0.3285 s` (`6.64x`); whole-event medians `0.503/1.360 s`
  (`2.70x`). Full-reconstruction boundary `0.333 s`.
- Scope: small synthetic validation canary only; not the later
  Stage-A-shaped benchmark and not an active/frozen-run estimate.
- Evidence:
  `docs/autogrowth/NATIVE_INCREMENTAL_HISTORY_VALIDATION_PERFORMANCE_RECLOSURE.md`;
  file SHA-256
  `89ed1403034de87db34ff86bffb45e854be0687c5209c42254b4dbb3c450f417`.

### v1 preflight-only block

- Binding: source `93ffeba3`; stream
  `890668c5b504469af2132ca9797227320d977b164f3d8e91f50a82b983932785`;
  superseded input identity
  `a2d3b3a35cd8dd157a6584355b56b2f1aa9a3a1c48ebccac984af7488e5f4fe9`.
- Result: `BLOCKED_BEFORE_PHASE1`; `phase1_events_opened=0` and
  `cohort_seeds_started=0`. Two pickle/set-order-sensitive diagnostic hashes
  were removed from cross-process identity; the frozen development stream and
  cache stayed byte-exact. Corrected prepared identity:
  `e3316e41911eccf311dca8020abe8b153229f838ab66092e329aec22147843c0`.
- Scope: preflight evidence only; there is no v1 Phase-1 result.
- Evidence:
  `reports/autogrowth/development/native_incremental_history_benchmark_v1/preflight_source_identity_failure.json`;
  file SHA-256
  `0152885aaa2183c67f28cf71498861fc6b9a15400f6f53cc581b118394e31619`.

### v2 Phase-1 checkpoint 32

- Binding: core `b6848ef4`, benchmark `97cce727`, input identity
  `39516f74ef6bc97028322ad3eeaf18db4c603de8c4648a745387531f20c852eb`,
  stream
  `f57f8b076c6edeeb6d51c10321c27d84633c0fe7a80d1a2b165ff57e9cdeb794`.
- Conditions: events 1-32; all three prospective arms; independently evolving
  incremental and legacy-full-replay strategies compared after every event.
  Stage wall/CPU `1155.295/1151.852 s`; peak RSS `641.109 MiB`.
- Result: exact per-event pending/trace/receipt/emission/outcome/full-state
  parity passed. Additive-chain rebuild, full-history boundaries, persisted
  state round-trips, and 64-row sealed-evaluation parity passed in every arm.
  Structural requests/children were `15/15` for `local_contrast`, `0/0` for
  `disconnected`, and `15/15` for `counterexample_blind`.
- Event-wall totals, incremental/legacy (speedup): `38.928/170.061 s`
  (`4.369x`) local contrast; `53.738/149.361 s` (`2.779x`) disconnected;
  `39.307/170.191 s` (`4.330x`) counterexample blind.
- Scope: exact per-event parity covers events 1-32 only.
- Evidence:
  `reports/autogrowth/development/native_incremental_history_benchmark_v2/phase1_checkpoints/032.json`;
  payload digest
  `dd7f79044f5891db379aa90b4c08d25f85f12b225918452441f26e8ee2e1e650`.

### v2 Phase-1 checkpoint 64

- Conditions: restored checkpoint 32; events 33-64 executed on the incremental
  path only. Stage wall/CPU `358.772/355.905 s`; peak RSS `1105.344 MiB`.
- Result: exact additive-chain rebuild, full-history reconstruction, checkpoint
  projection, and persisted-state round-trip passed in every arm. Incremental
  event-wall totals for events 33-64 were `37.449 s` local contrast,
  `56.611 s` disconnected, and `37.570 s` counterexample blind.
- Scope: the event-64 legacy-validation authority was reconstructed at the
  boundary, not independently evolved event by event. Therefore per-event
  incremental/legacy parity remains limited to events 1-32. The cumulative
  status is `BOUNDED_32_EVENT_GATE_WITH_EXPLICIT_BOUNDARIES`; events 65-256
  remain unexecuted/unclaimed in the recorded artifacts.
- Evidence:
  `reports/autogrowth/development/native_incremental_history_benchmark_v2/phase1_checkpoints/064.json`;
  payload digest
  `d3ba4106a8665a43059ce593068664d0c90d4ee94332c2456ce40e799b41eacc`;
  previous digest is the exact checkpoint-32 digest above.
- Current index:
  `reports/autogrowth/development/native_incremental_history_benchmark_v2/phase1_parity.json`;
  payload digest
  `8da13237f4bc0b2bfa4b8155fcdc13787b0bc16f56529cf428013cd2577fc810`.

## V2 intrinsic R0 -> R1 integration gates

### Implementation and data-free validation

- Conditions: same-run empty-start R0; V2 availability is committed before the
  REAL outcome; unique REAL training successors append evidence for later
  events; repeats and evaluation use mutation-free VIRTUAL queries; each arm
  has an independent serialized authority; structural reclosure is fixed at 64
  prospective events after the 32-receipt discovery prefix.
- Data boundary: seed `2026082801`; all 208 development input FENs use the exact
  fullmove namespace `900000..900207` while preserving geometry. Pool digest:
  `1d644c5e138e93b848e4e04838e69640e405401cc51140439fdbfb712f895d52`.
- Result: combined optimized-engine, incremental-history, and intrinsic tests
  `47 passed in 86.66 s`; intrinsic file alone `23 passed in 46.69 s`.
- Actual tiny V2 canary: two unique REAL observations, one fixed structural
  transition, full-history boundary, and dump/load continuation parity passed.
- Scope: software/semantic integration evidence only; no mate-in-2 result.

### Fixed-pool R0 depth diagnostics

- Conditions: same permanently viewed seed/pool above, one core, unchanged
  learner; only the diagnostic R0 epoch cap varied. Pool construction was
  `22.1-22.8 s` in the local runs.
- 8 epochs: `29.87 s`, validation `0.8125`, 375 triplets / 93,802 edges.
- 16 epochs: `61.09 s`, validation `0.8125`, 735 triplets / 183,850 edges.
- 32 epochs: `136.17 s`, validation `0.875`, 842 triplets / 210,612 edges.
- Exact fixed-cap audit: joint validation/regression reached `1.0/1.0` at epoch
  72; R0 training `350.20 s`, subsequent full validation/regression `54.34 s`.
- Interpretation: deeper R0 was necessary on this pool; graph topology stopped
  growing by the 24-32 epoch region, while weights continued changing.

### First fixed integration preflight — bounded stop

- Conditions: exact fixed 48/16/16 R0 and R1 pools, 96/240 caps, cooperative
  ceiling 120 s plus external hard watchdog, local development output only.
- Result: the external watchdog stopped the run before the first persisted
  R0/R1 boundary; no result, attempt, progress, or snapshot artifact exists.
  Phase isolation then measured pool construction at `22.56 s`, exact R0 at
  `350.20 s`, and post-R0 evaluation at `54.34 s`; authority/gate construction
  exceeded the remaining approximately 173 s of a separate 600 s audit.
- Related builder canary: a 32-triplet frozen R0 required `212.09 s` to build a
  45-candidate, 2.66 MB authority; serialized SHA-256
  `86a3c621135a12bc2c49cb2ea33aca9209a4e38b6a31df269e47652391a49066`.
- Decision: **NO-GO for the two-hour shot until an exact one-R1-epoch preflight
  reaches an atomic snapshot under a 45-minute hard watchdog.** A bounded stop
  before the control arm is runtime/integration evidence only, never a causal
  or mate-in-2 result.

### Exact epoch-1 preflight at `f482aac6` — integration failure

- Conditions: seed `2026082801`; fixed 48/16/16 R0 and 48/16/16 R1 pools;
  fullmove namespace starting at `900000`; cooperative wall ceiling `1 s`, RSS
  ceiling `8192 MiB`, and external `2700 s` watchdog; local single-process run.
- Result: R0 passed at epoch 72 with validation/regression `1.0/1.0`. After
  `1959.336 s`, R1 duplicate-index initialization failed before any arm epoch or
  snapshot: `AcceptedRealReference` intentionally has no `predecessor_fen`.
- Repair: derive the exact index from FEN-bearing discovery receipts plus
  accepted prospective `consumed_receipts`; do not change the generic reference
  schema. Real-authority receipt/round-trip, duplicate-VIRTUAL, and V2
  snapshot/resume regressions pass; combined affected suites: `49 passed in
  91.73 s`.
- Decision: preserve this failed attempt; rerun the exact epoch-1 gate from a
  fresh output directory before any bounded two-hour continuation. Scope remains
  `DEVELOPMENT_VIEWED_NOT_SCIENTIFIC`.

### Exact epoch-1 preflight at `a998acda` — performance-gate stop

- Conditions: same fixed seed/pools and `1 s` cooperative / `2700 s` external
  ceilings as above; duplicate-index repair present; clean tracked tree.
- Result: R0 again passed at epoch 72 with validation/regression `1.0/1.0`.
  The external watchdog stopped the process before an epoch-1 R1 snapshot; only
  the atomic R0 progress record exists. The prior schema exception did not recur.
- Diagnosis: each V3 continuation manifest recomputed the complete frozen-R0
  persistent audit four times; one REAL transaction invoked five manifests in a
  synthetic profile, hence 20 audits. Those audits deep-copy, scan, pickle, and
  hash the learned graph. This is finite repeated work, not nontermination.
- Exact repair canary: compute one four-component identity audit per manifest,
  while retaining the unchanged six-component full audit at trust boundaries.
  Three synthetic manifests improved `0.1592 -> 0.0136 s`; one REAL transaction
  improved `0.4552 -> 0.2277 s`. Manifest identity matched the full audit.
- Validation: data-free handover `7 passed`; combined authority-settlement,
  incremental-history, and intrinsic suites `50 passed in 69.38 s`.
- Decision: rerun the same exact epoch-1 gate from the repaired committed source;
  do not launch the two-hour continuation unless its atomic snapshot passes.

### Exact epoch-1 preflight at `1fef1bff` — gate passed

- Conditions: same seed, fixed pools, one process/core, clean tracked source,
  cooperative `1 s` ceiling checked only at an exact epoch boundary, `8192 MiB`
  RSS ceiling, and external `2700 s` watchdog.
- Result: R0 again reached validation/regression `1.0/1.0` at epoch 72. The
  full-intrinsic arm reached and atomically serialized epoch 1 in `2326.714 s`;
  status `CEILING_REACHED_AT_EXACT_EPOCH_SNAPSHOT`. Snapshot size was
  `81.8 MB`. This passed the predeclared 45-minute integration gate.
- A second process using only a longer wall ceiling rebuilt the deterministic
  prefix but rejected the saved snapshot: fingerprint `60861370...` versus
  `ebdc7381...`. The ceilings were already excluded. The actual defect was the
  process-dependent raw-pickle hash of graph sets; equivalent frozen policy and
  credit state produced different bytes under different hash seeds.
- Decision: preserve the snapshot and failed resume. Replace the pickle hash
  with a canonical base-state identity and regression-test cross-process hash
  stability; source changes necessarily make this old snapshot non-resumable.

### Fixed 7200-second development shot at `1fef1bff`

- Conditions: fresh output directory; seed `2026082801`; fixed 48/16/16 R0 and
  48/16/16 R1 pools; one process/core; full-intrinsic arm; R0/R1 caps 96/240;
  cooperative `7200 s` wall and `8192 MiB` RSS ceilings; external `8100 s`
  watchdog; exact clean commit `1fef1bff`. This is
  `DEVELOPMENT_VIEWED_NOT_SCIENTIFIC`, with no control arm completed.
- Result: exact atomic stop at epoch 4 after `7627.513 s` total wall
  (`7586.712 s` at the safe-boundary check): 192 R1 episodes, 187 unique REAL
  authority observations, zero duplicate-REAL evidence, one structural
  transition, 42 requests/children materialized, zero AVAILABLE queries, zero
  child handoffs, and zero successor-value sum. The epoch-1 heldout checkpoint
  had conversion `0/16` and R0 retention `15/16`; the forced epoch-4 checkpoint
  intentionally skipped heldout evaluation. Graph state was 1,031 triplets,
  257,888 edges and 5,508 nodes.
- Authority diagnosis: 112 states = 70 generation-0 plus 42 generation-1.
  Three generation-1 cells certified, all with REFUTED polarity. Each of the
  26 generation-0 candidate cells with AVAILABLE polarity had already
  accumulated a monotone contradiction; all 42 generated children were
  REFUTED; and the sole structural frontier was consumed. Therefore this exact
  continuation can never emit AVAILABLE or exercise R0 -> R1 bootstrap,
  however long it runs.
  The 187 REAL outcomes included 29 immediate mates, so zero availability is a
  certification/representation lockout rather than absence of positive world
  outcomes.
- Performance diagnosis: a saved-epoch VIRTUAL probe was interrupted after
  more than 90 seconds inside `NativeR0DreamSession.request` while recomputing a
  complete persistent-state audit. The session performs that graph-deepcopy /
  pickle audit at open, request and close; this is the next exact hot path.
- Evidence:
  `reports/autogrowth/development/native_intrinsic_v2_r0_r1_seed_2026082801_1fef1bff_shot_7200/attempt.json`
  SHA-256
  `032567ba8cd0236be07b87c1bbc068c51e67b99b95ebcffebceacd317b4a6379`;
  `progress.json` SHA-256
  `4704959ce859f9d3c854d70ccd95f49911f82d4ae4568d5366d32f9d86a07a12`;
  epoch-4 snapshot SHA-256
  `0e02f7fe69d2d3fd6a7d5316a42ecd3ba25ca1e4af770bf64988b3e9a4848244`.
- Decision: **do not resume this snapshot and do not start a longer curriculum
  shot.** First close the process-stable resume identity, remove exact audit
  work from the frame hot path with differential parity, and validate a
  prospective AVAILABLE path in a bounded mechanism canary.

### Post-shot exact runtime reclosure — `7d56d5d5`

- Resume identity: replaced the process-dependent raw `(graph, credit)` pickle
  hash with a canonical semantic graph and credit identity. It binds ordered
  nodes/edges, behaviorally active adjacency and retrieval indexes, prototype
  cache, composite indexes, edge aliases and credit event ordinal. Output
  paths, resume/write-retention controls, evaluation caps and resource ceilings
  remain operational. In a data-free/test-scale canary, two subprocesses with
  distinct `PYTHONHASHSEED` values produced one identity, and resume across
  changed wall/RSS ceilings matched uninterrupted execution exactly.
- Snapshot repair: the prior graph serializer deep-copied the formal graph but
  not its trainable-edge index, detaching edge objects after restore. The new
  serializer preserves aliases, while v1 loads deterministically rebind and
  validate them. The saved epoch-4 artifact repaired all `105306/105306` R0
  and `128944/128944` R1 trainable-edge references; a fresh current-code R0
  round trip retained exact semantic state and all aliases.
- Dream isolation: replaced three full six-component graph-copy/pickle audits
  per session request with a three-point inference-semantic guard. The graph
  and credit execution copies remain isolated and are still discarded per
  frame; full audits remain at serialization/test/trust boundaries. The same
  exact epoch-4 artifact and query measured `48.241 -> 18.107 s` (`2.664x`);
  the repaired query returned UNKNOWN with zero mutation and exact
  continuation-manifest equality. No fresh outcome was opened or consumed.
- REAL rollback clone: only the mature frozen R0 object is memo-shared while
  the evolving V2 authority is still copied. A pre/post inference guard fails
  if that shared object changes. On the exact epoch-4 snapshot, full authority
  clone versus guarded frozen-R0-sharing clone was `5.114/0.193 s` (`26.47x`
  for the rollback clone only), with exact continuation-manifest parity.
  Public idempotent and invalid-rollback transactions took `2.632/2.321 s`;
  both preserved the full six-hash source audit and R0 object identity.
- Validation: four affected suites `56 passed in 72.98 s`; exact uninterrupted
  versus resumed canonical-semantic state parity passes; `py_compile` and
  `git diff --check` pass. Historical artifact-backed V2/trace tests cannot run
  in this clone because their referenced `reports/autogrowth/native_*` inputs
  are absent; the observed setup errors are preserved as an environment
  limitation, not counted as passes.

### V7 mixed-evidence specialization reachability — `5efc88ce`

- Diagnosis: a generation-0 `MIXED_OUTCOME_SHADOW` previously requested a
  child only when it was already prospectively certified and the current REAL
  event contradicted it. An earlier monotone contradiction made certification
  impossible, so the exact epoch-4 continuation's 26 AVAILABLE-polarity
  shadows could never request a compensating child.
- Repair: an uncertified mixed shadow now emits one lifetime request at the
  first projected event with at least four prospective polarity-consistent
  supports and at least one contradiction. The request separately binds its
  emission receipt and its earliest contradiction anchor. The existing
  certified-revocation basis remains distinct. Request IDs bind the complete
  causal manifest, and live execution and full replay use one constructor.
- Data-free mechanism canary: fixed two-geometry KRK R0, local-contrast mode,
  both AVAILABLE and REFUTED polarities. For `C,S1,S2,S3,S4,S5`, incremental
  and legacy-full-replay authorities were compared after every event. No
  request appeared through S3; S4 emitted exactly one mixed-evidence request
  without revocation or parent authority; S5 emitted no repeat. Dump/load and
  full-history reconstruction remained exact.
- Child gate: the request was structurally consumed and materialized with zero
  support, successes and contradictions and with all pre-birth REAL receipts
  excluded. Four new matching supports certified the clean child. A separate
  physically valid matching contradiction followed by four supports produced
  `(successes, contradictions, certified) = (4, 1, False)` for both
  polarities. The certified `S,S,S,S,C` path still revoked and requested with
  contradiction anchor equal to request emission, then passed replay and
  round-trip checks.
- Runtime discipline: exact request-evidence/candidate reconstruction runs
  only at explicit full-history, serialization and restoration boundaries.
  Ordinary invariants retain request-ID, parent, queue and emission bindings
  without rescanning growing evidence tails. A tiny reviewer canary measured
  `0.50 ms` for the routine request check versus `2.59 ms` for exact reclosure;
  grounded-reference canonicalization occurs once per authority graph, not
  once per matching cell.
- Validation at the committed source: focused mixed/settlement/composition/
  incremental suites `49 passed in 61.98 s`; intrinsic/handover suites
  `42 passed in 46.57 s`; atomic-snapshot and development-benchmark harnesses
  `57 passed in 103.83 s` with the sandbox-only process-pool test explicitly
  deselected. `py_compile` and `git diff --check` pass; independent review
  found no remaining blocker. Missing historical `reports/autogrowth/native_*`
  inputs remain an environment limitation and are not counted as passes.
- Scope: this establishes mechanism reachability and exact software semantics,
  not mate-in-2 learning or generalization. The old epoch-4 continuation stays
  permanently locked and should not be resumed. The next evidence step is a
  bounded fresh development integration shot, not a full curriculum run.
