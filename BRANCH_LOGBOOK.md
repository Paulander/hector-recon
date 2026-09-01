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
| V7 bounded R0 -> R1 shot | Semantic commit `5efc88ce`; seed `2026082801`; one process/core; fixed viewed 48/16/16 pools; cooperative `7200 s` / `8192 MiB` epoch-boundary ceilings | R0 passed at epoch 72 with validation/regression `1.0/1.0`; no first R1 epoch boundary was persisted before the two-hour scope ended. The stop landed in a full graph `deepcopy` that source places on each observed REAL-action path. No R1 or mate-in-2 conclusion is supported. |
| Epoch-scoped frozen-R0 execution | Commit `60e3c9b8`; mixed REAL/VIRTUAL parity canary; focused authority, history, handover and curriculum suites | Exact one-shot/session parity; one isolated R0 runtime clone per epoch session instead of per frame; frozen-source audits remain constant within a session; `57 passed`. |
| Full-work development launch | Commit `60e3c9b8`; seed `2026082801`; one process/core; fixed viewed 48/16/16 pools; unchanged learner; `21600 s` / `8192 MiB` safe-epoch-boundary ceilings | Launched 09:58 CEST; R0 passed at epoch 72 with validation/regression `1.0/1.0` at 10:22; the Codex-managed execution was reaped at 12:02 after about `2 h 04 m`, exactly 90 minutes after its owning task ended. No handled-exit artifact exists. R1 snapshots/progress are written only every 20 epochs, so the absent R1 artifact does not establish that zero R1 epochs completed. |
| Current V7 realistic runtime profile | HEAD `2b517ded`, behavior `60e3c9b8`; already-viewed R0 with 4,535 nodes/210,612 edges/842 triplets; one core; exact viewed REAL sequence | First 48 REAL events took `426.572 s`; 64 took `574.615 s` with stable per-event cost and `94.66%` in frame inference. The event-64 frontier produced and materialized 62 children in `561.914 s`; all checks and exact continuation parity passed. The path is costly but finite and cannot explain the epoch-1 artifact loss. |
| Adaptive-boundary preflights | Base `2f1b68c9`; local uncommitted hybrid implementation; development-only data | Preserved one immediate configuration rejection, one seed whose R0 gate failed, and one initialization-identity failure. None entered usable R1 learning. |
| Adaptive-boundary v6 canary | Seed `2026082801`; random 8/4/4 R1 pools; one process/core; hash-ranked local candidates; stopped after exact epoch 4 | R0 `16/16`; R1 heldout `0/4`, retention `15/16`; 42 buds, 37 successors, depth 2, but zero AVAILABLE, handoffs or value. Recursion was live; function was absent. |
| Adaptive-boundary v7 red-team stop | Same canary; contrastive candidate work in progress | Stopped before R1 after review found adaptive children could not themselves request refinement. No scientific or R1 result. |
| Adaptive-boundary v8 residual-beam canary | Seed `2026082801`; random 8/4/4 R1 pools; one process/core; residual-guided beam; repaired recursive lifecycle; exact epoch-4 checkpoint | R0 `16/16`; R1 heldout `0/4`, retention `15/16`; 40 buds, 38 successors and depth 2. All 9 positive buds died; 20 negative buds promoted; zero AVAILABLE, handoffs or value. Stopped by predeclared no-functional-signal rule. |
| Adaptive-boundary v9 multi-seed discriminator | Base `2f1b68c9`; local hybrid implementation; seeds `2026083101/02/03` in parallel plus viewed reference seed `2026082801`; one process/seed and numerical threads fixed to one; random 8/4/4 R1; exact epoch 4 | `3101` failed R0 validation (`13/16`) and never entered R1. The other three completed the primary arm at `0/16` exhaustive mate-in-2 and zero handoff/value. `3103` produced 5 surprise mates, 87 buds, 2 positive promotions and 23 live successors; `2801` produced 3 surprise mates and recursive refinement through generation 4 with 18 live successors; neither produced certified AVAILABLE authority. Durable epoch snapshots were preserved and the processes were stopped before control arms. |
| Adaptive-boundary V14 mechanism gate | Implementation `55e940a9`; report repair `4cf1711b`; five fresh seeds, of which three passed R0 and two reached durable R1 snapshots | Bounded local turnover and positive promotion worked, but no post-birth certification, AVAILABLE envelope, handoff, successor value, or mate-in-2 conversion appeared. **NO-GO** for a longer run. |
| Adaptive-boundary V15 mechanism follow-through | Commit `58fbd0d8`; fresh independent seeds `2026090103/0104`; one process and one numerical thread; random `8/4/4` R1; exact eight-epoch runs | `0103`: wall `4932.0426137079485 s`, R1 full/control `1920.303802/1939.51825 s`; R0 `16/16` validation and `16/16` report regression. `0104`: wall `4845.015892208088 s`, R1 full/control `1885.137376/1912.423199 s`; R0 `16/16` validation and `12/16` report regression. Only `0104` full intrinsic reached the mechanism chain; both seeds/arms were `0/4` mate-in-2. **NO-GO**. |
| Adaptive-boundary V16 native-local closure canary | Source `8e158397`; fresh seed `2026090106`; `canary`; one numerical thread; random `8/4/4`; `7200 s`/`8192 MiB` ceilings | R0 validation `16/16`, report-only regression `14/16`; the old native admission report authorized `14/16` positives and `0/16` negatives, then stopped before R1 after exact wall `645.8366680829786 s`. No R1 or mate-in-2 claim. Repair `67414302` makes native-authority coverage/specificity report-only; after the existing R0 mastery transition, only authority runtime integrity can veto R1 entry. |

## Purpose and validity scope

Quick-scan ledger for the current development branch. Raw artifacts remain
authoritative. Every benchmark below is labeled
`DEVELOPMENT_VIEWED_NOT_SCIENTIFIC`: it may support software-runtime and exact
semantic-parity claims only, never a scientific ReCoN result or a frozen-run
inference. The constructed benchmark uses one persistent black knight to stay
materially disjoint from the protected pure-KRK corpora; its two D4 geometries
are not representative workload samples.

Current branch: `codex/adaptive-boundary-ecology`, based on
`2f1b68c992eb6868b468148004d8e5a4746c88ab`. The final adaptive implementation
is committed before the V14 experiments; use the exact implementation commit
recorded in the V14 entry below as their source identity.

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
- `60e3c9b8b085e49db069b9db53422e3899c116fb` — reuses one isolated frozen-R0
  inference runtime across each R1 epoch session, with exact boundary guards
  and structural-session rotation.
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

### V7 fixed two-hour development shot — first R1 boundary not reached

- Conditions: fresh local output; semantic source `5efc88ce`, branch-log tip
  `8ba352e4`; fixed viewed seed `2026082801` and 48/16/16 R0/R1 pools; one
  Python process/core with BLAS/OpenMP thread counts fixed to one; unchanged
  learner; `7200 s` wall and `8192 MiB` peak-RSS settings. Approximate launch
  was 2026-08-28 22:47 CEST and the single operator interrupt was approximately
  2026-08-29 00:49 CEST. The output directory was new and no snapshot resumed.
- Persisted result: R0 passed at epoch 72 with validation/regression `1.0/1.0`,
  V2 prospective mode and ecology UUID `ac9481307138d07143ee38b9`. The exact
  target contains only the 302-byte atomic `progress.json`; its SHA-256 is
  `1980773b196dab7e8ccf545d9f73bf5c21690665d3c38e01006f953261078882`.
  `completed_r1_arms` is empty, and no R1 snapshot, `attempt.json`,
  `result.json` or partial file exists.
- Boundedness result: `--max-wall-seconds` is checked only after a complete R1
  epoch. Epoch 1 had not reached that safe boundary when the nominal two-hour
  scope expired, so the runner could not enforce a hard wall limit itself. It
  was stopped once with Ctrl-C; atomic completed output remained intact.
- Direct hot-path observation: the interrupt stack was
  `_v2_r0_observe_training_successor -> open_real_event ->
  emit_action_with_trace -> frame_runtime_copy -> copy.deepcopy`. Source
  control flow invokes this full learned-graph copy for every nonduplicate
  nonterminal R1 successor sent to the V2 REAL observer. The same unique event
  also performs four frozen-R0 persistent-identity audits and two canonical
  semantic-graph traversals through its pre/post guards; those audits sort
  edge-sized collections. This proves repeated whole-graph work remains on the
  per-observation path; one stack observation does not by itself attribute all
  elapsed time to `deepcopy`.
- Interpretation: the shot confirms fixed-pool R0 and same-run V2 authority
  construction, but it did not exercise an exact R1 epoch boundary. Therefore
  it supplies no end-to-end evidence about mixed requests, specialized
  children, AVAILABLE handoffs, R1 learning or mate-in-2 capability. Before
  another curriculum shot, benchmark and remove the full per-frame graph copy
  with exact trace/isolation parity, and give the development launcher a real
  external hard-wall guard in addition to safe-boundary snapshots.

### Full-work launch termination and current-code profile

- Conditions: behavior commit `60e3c9b8`; branch-log tip `2b517ded`; seed
  `2026082801`; fixed viewed 48/16/16 pools; unchanged learner; one
  process/core; `21600 s` / `8192 MiB` cooperative epoch-boundary ceilings.
- Exit forensics: launch was 2026-08-29 09:58:24 CEST. Its owning Codex task
  ended at 10:32:25, and the managed execution became `failed`, exit code
  `-1`, at 12:02:25 -- exactly `5400.000 s` later. macOS independently records
  the accompanying `caffeinate` client dying at that instant after `02:04:00`.
  There was no nearby sleep/reboot or Python crash report. Normal success, a
  cooperative ceiling, or a caught Python exception would have written
  `result.json` or `attempt.json`; neither exists. This strongly identifies
  managed-session cleanup, while the exact terminating signal is unknown.
- Persistence limit: normal R1 progress and snapshots are written only every
  20 epochs. Epoch 1 is evaluated but not persisted unless a ceiling or other
  forced stop is observed at its safe boundary. Therefore the last R0-only
  progress file proves no exact R1 boundary, but it does not prove that zero
  R1 epochs ran before the external termination.
- Realistic current-code profile: the already-viewed R0 has 4,535 nodes,
  210,612 edges and 842 triplets. The exact viewed first 48 REAL events took
  `426.572 s`; 64 events took `574.615 s` with no growing per-event slope.
  Frame open/inference was `94.66%` of REAL time. At frontier 96, all 62 V7
  requests materialized; seal/open/consume/materialize/reopen took `561.914 s`
  and performed 127 explicit full-authority copies. Session-close parity and
  full-history verification passed. This is finite CPU-bound work and occurs
  only after 64 prospective events, so it cannot explain an epoch-1 loss.
- Interpretation: the launch failed because its process lifetime was tied to
  the wrong execution owner. Residual formal inference and structural-copy
  costs remain worthwhile optimization targets, but neither supplies evidence
  of nontermination or of a ReCoN exception in this launch.

## Adaptive boundary ecology — local hybrid branch

- Binding: audited base `2f1b68c992eb6868b468148004d8e5a4746c88ab`;
  branch `codex/adaptive-boundary-ecology`. This section records the earlier
  uncommitted development phase; the final implementation identity is recorded
  in V14 below. The hybrid lets local prediction errors nominate cheap
  micropattern buds, but commits the resulting graph mutations atomically at
  deterministic content-blind epoch safe points. Discovery receipts are
  excluded from certification, children start with zero authority, and
  contradicted descendants can recursively request narrower descendants.
- Exact software gate: the artifact-independent competence, authority,
  incremental-history, all-reply, ecology, curriculum, action-order and runner
  suites passed `132 tests in 198.08 s`; the focused lifecycle/beam subset
  passed `51 tests in 126.20 s`. Historical tests whose protected artifacts are
  absent were not reconstructed or counted.
- Preserved preflights: seed `2026083101` first rejected an invalid balanced
  8/4/4 split in `2.42 s`, then completed only R0 in `579.33 s` and failed its
  `1.0` gate (`13/16` validation, `12/16` regression). Seed `2026082801` later
  stopped in `1396.97 s` on an initialization-identity invariant before a
  usable R1 boundary; the invariant defect was repaired and exactly tested.
- V6: seed `2026082801`, one process with numerical-library threads fixed to
  one, random 8/4/4 R1 pools, eight-epoch cap, checkpoint every epoch. At exact
  epoch 4 (`2987.13 s` R1 duration): 32 episodes, 30 unique REAL observations,
  3 mating outcomes, 42 buds (28 DEAD, 10 DORMANT, 4 ACTIVE), 37 successors,
  recursive specialization depth 2, `0/4` heldout, R0 retention `15/16`, and
  zero AVAILABLE responses, handoffs or successor value. This used the
  superseded hash-ranked candidate allocator.
- V7: the contrastive candidate run was deliberately interrupted before R1
  when review showed adaptive-origin children were omitted from the recursive
  request basis. Its empty log/checkpoint state is preserved.
- V8: same seed, pools and process limits, now using the repaired recursive
  lifecycle and staged residual-guided beam. At exact epoch 4 (`2984.94 s` R1
  duration): 32 episodes, 30 unique REAL observations, 3 mating outcomes, 40
  buds (17 DEAD, 21 DORMANT, 2 ACTIVE), 20 local promotions and 18 recursive
  materializations. The authority held 38 new successors across structural
  generations 1-4, reached specialization depth 2, and certified 23; every new
  successor was REFUTED. All 9 positive buds died on contradiction; the 20
  promotions were negative. Heldout was `0/4`, R0 retention `15/16`, and
  AVAILABLE/handoff/successor value were all zero. The process was interrupted
  during epoch 5 only after the epoch-4 snapshot was durable; exit `130` is the
  intentional stop.
- Decision: **NO-GO for a longer or multi-seed curriculum run.** The old
  one-frontier structural lockout is removed, but the present ecology spends
  finite successor capacity on abundant negative vetoes while rare positive
  candidates die before post-birth certification. Before another canary,
  implement deterministic local retirement/replacement with a bounded
  exploration reserve, separate validation-based selection from untouched
  final regression, and require exact R0 behavioral retention plus a certified
  positive handoff/value signal.

### V9 positive-shell discrimination before the final repair

- Conditions: development-only random `8/4/4` R1 canaries, four epochs,
  validation and snapshots every epoch, one process/seed and one numerical
  thread. Every directory below is independent and preserved; completed
  primary arms were intentionally interrupted before the redundant control.
- Seed `2026083101` never entered R1: R0 stopped at epoch 96 with `13/16`
  validation and `12/16` regression, so its exact `1.0` gate correctly blocked.
- Seed `2026083102` passed R0 at epoch 24, completed 32 R1 episodes, retained
  `15/16` R0 validation cases and converted `0/4` mate-in-2 validation and
  `0/4` regression cases. It produced no surprise-success bud, AVAILABLE
  handoff, or successor value.
- Seed `2026083103` passed R0 at epoch 16 and retained `16/16`; five surprise
  mating outcomes produced 87 lifetime buds, 28 live candidates, two positive
  promotions, and 23 live authority successors. None certified AVAILABLE;
  handoff/value and both `4`-case mate-in-2 evaluations remained zero.
- Reference seed `2026082801` passed R0 at epoch 72 and retained `15/16`;
  three surprise successes produced 56 buds and recursive authority growth
  through generation 4, but every one of 16 certified successors was
  non-AVAILABLE. Both mate-in-2 evaluations and handoff/value remained zero.
- Interpretation: these runs were made before regression-withholding,
  positive-only promotion, renewable slot reuse, and exact worst-reply TD
  credit were all simultaneously present. They are preserved as mechanism
  diagnostics, not evidence for the corrected branch.

### V10 local ecology, metabolism, and scientific-gate repair

- Local positive ecology now births only from surprise REAL mate success,
  treats failures as contrast, refines contradicted coarse shells into
  abstaining residual children, forbids negative boundary promotion, and
  keeps a bounded staged beam with deterministic exploration.
- Authority settlement is event-driven and atomic. Pending requests remain
  retryable on capacity failure; weak adaptive leaves retire by a deterministic
  tier order; core and live/pending parents are protected; retired slots are
  reused without deleting evidence; unique tombstones and exact replay remain
  mandatory.
- R0/R1 stopping and maturation read validation only. Regression is queried
  once for terminal reporting. All-reply handoff is explicitly grounded and
  sends the exact minimum reply value into TD credit; UNKNOWN/partial envelopes
  send no value. The development runner no longer equates completion with a
  scientific pass.
- Pre-experiment verification: `184 passed` across focused credit, all-reply,
  ecology, lineage, curriculum, runner, capacity, rollback and replay suites;
  `34` further adjacent settlement/handover tests passed. Historical
  artifact-backed tests remain
  unavailable in this clone, and the deliberately changed authority source no
  longer matches its retired protected hash. Targeted `compileall` and
  `git diff --check` pass.

### V11 three-seed post-repair epoch-4 gate

- Conditions: seeds `2026083104`, `2026083105`, and `2026083106`; fresh
  independent directories; balanced-location `48/16/16` R0; random `8/4/4`
  R1; four primary epochs; one process and one numerical thread per seed;
  `7200 s`/`8192 MiB` per-process ceilings. The three seeds ran concurrently.
- `2026083106` stopped honestly at the R0 gate after `561.20 s`: epoch 96,
  validation `13/16`, final report-only regression `15/16`, and no R1 work.
- `2026083105` had passed the validation-only R0 gate but failed closed during
  same-run authority construction after `304.78 s`: one frozen R0 action did
  not match the harness's predeclared discovery-row role. No R1 evidence was
  consumed. This exposed a label-like harness assertion, not a learner defect.
- `2026083104` passed R0 at epoch 24 (`16/16` validation) and completed the
  primary epoch-4 snapshot. Its 32 R1 episodes took `2727.98 s`: 30 unique
  REAL observations, four surprise mating outcomes, 19 local buds, nine
  refinements, 16 live ecology candidates, 88 recursively consumed requests,
  66 live successors and authority generation 4. It had zero boundary
  promotions, zero certified adaptive nodes, zero AVAILABLE all-reply
  envelopes, zero handoffs, and zero successor value. Mate-in-2 validation and
  regression were both `0/4`; R0 retention was `15/16` on both. The redundant
  control was interrupted immediately after primary reporting; all four
  history snapshots and the latest snapshot are preserved.
- Interpretation: local budding and recursive growth are now reachable, so
  this is not the prior structural lockout. Four epochs did not provide enough
  repeated local support for a positive promotion/certification, and the
  prespecified functional gate was not met. Do not extend this exact source;
  first remove the discovery role assertion so actual environmental outcomes
  alone determine receipt polarity, then repeat independent canaries.

### V12 neutral discovery and bounded event paths

- Discovery no longer trusts pool roles. A content-ranked training-only tape is
  executed by the frozen native R0, and signed REAL outcomes determine polarity.
  No move answer, mate-distance label, held-out outcome, or external chess
  engine enters learning.
- REAL/VIRTUAL observation now uses maintained live/request indexes, rolling
  commitments, and reversible local mutation journals instead of copying or
  canonically rescanning the complete authority on every event. Exact replay
  remains mandatory at explicit checkpoint/load boundaries.
- Regression remains a one-time terminal report split; validation alone may
  stop, mature, or select. Missing grounding and malformed gate fields fail
  closed. Development reports distinguish learner-oracle freedom from
  exhaustive harness-only evaluation.

### V13 pre-core-route three-seed mechanism gate

- Conditions: seeds `2026083109`, `2026083110`, and `2026083111`; fresh
  independent directories; random `8/4/4` R1 canary; four-epoch cap; one
  process and one numerical thread per seed. All three entered R1 after exact
  `16/16` initial R0 validation. They were deliberately stopped with exit
  `130` after durable snapshots when execution-level core interference was
  identified; none was resumed after source changes.
- Seed `2026083109`: epoch 3, 24 episodes, `1962.23 s`; three surprise
  successes, 53 lifetime buds, 44 refinements, no promotions, AVAILABLE
  envelopes, handoffs, successor value, or validation conversion; R0 retention
  measured `16/16`.
- Seed `2026083110`: epoch 3, 24 episodes, `1853.13 s`; six surprise successes,
  38 buds, 23 refinements, six promotions, three AVAILABLE all-reply envelopes,
  two handoffs, and successor-value sum `1.2454048740`; mate-in-2 validation
  remained `0/4`, and shared-grown-graph R0 retention was `15/16`.
- Seed `2026083111`: epoch 4, 32 episodes, `1529.84 s`; one surprise success,
  three live buds, no promotion/handoff/value, `0/4` validation, and `15/16`
  shared-grown-graph R0 retention. Its no-bootstrap control completed epoch 1
  with eight episodes and no births or handoffs.
- Diagnosis: the immutable authority-owned R0 still solved `16/16`; the grown
  graph restricted to old triplet IDs solved `15/16` because new shared
  topology changed execution. The repair therefore routes through the actual
  frozen local core first, delegates to grounded V2 only on core abstention,
  then explores with the grown graph. These V13 artifacts are useful
  mechanism evidence but are not a scientific go decision.

### V14 final causal, replay, and boundedness preflight

- Positive-shell settlement now permits birth only from surprise-success REAL
  evidence. Failures provide local contrast; a contradicted coarse positive
  shell abstains and may produce one bounded residual refinement instead of
  installing a global negative veto. Only positive descendants can become
  AVAILABLE.
- Local decisions are committed at content-blind safe points. Weak adaptive
  leaves retire by deterministic lineage-local order, their slots are reused,
  the frozen mate-in-1 core retains routing precedence, and tombstones plus
  exact replay preserve every lifetime decision without keeping every retired
  leaf computationally active.
- Birth and certification evidence are separated by exact ordinals. Compact V4
  causal contracts are rederived from immutable requests and candidates;
  coherent future-frontier tampering, discovery reuse, and mutation rollback
  fail closed. The REAL hot path uses maintained indexes and one-pass local
  journals rather than growing-history scans; full reclosure remains confined
  to explicit checkpoint/load trust boundaries.
- R1 evaluation executes each selected first move against every legal reply and
  reads only those outcomes. The learner receives neither correct-move labels
  nor mate distance; only a fully grounded minimum-reply envelope may hand a
  successor value to exact worst-reply TD credit. Validation alone controls
  stopping/selection; regression is one terminal report.
- Exact-tree verification before fresh experiments: the focused source suite
  passed `128/128`; the adjacent source suite passed `114/114`; a changed-file
  subset passed `34/34`; targeted adversarial/replay batches passed `7/7`,
  `3/3`, and `1/1`; and the tiny real-native/resume selection suite passed
  `7/7`. After the final two-line deepcopy index restoration correction, the
  bounded REAL transaction suite passed `12/12` and an independent reviewer
  passed `55/55`. Targeted `compileall` and `git diff --check` are clean.
- Residual observation item, not a mechanism-gate blocker: explicit snapshots
  deliberately perform a full history reclosure. Longer gates must record
  whether serialization duration grows materially, but this work does not add
  a monitoring framework or weaken the checkpoint trust boundary.

### V14 five-seed mechanism gate and compact-report repair

- Binding and conditions: implementation commit
  `55e940a992909174b6e6893c3f5674f420cf9f77`; fresh independent directories;
  seeds `2026090101..2026090105`; one process per seed with every numerical
  thread pool fixed to one; random `8/4/4` R1 canary, exact four-epoch cap,
  `7200 s`/`8192 MiB` safe-boundary ceilings. Seeds `0104/0105` were the next
  predetermined replacements after `0101/0102` failed before R1; all failures
  remain preserved and counted.
- Seeds `0101` and `0102` stopped honestly at the epoch-96 R0 gate after
  `556.585 s` and `552.469 s`. Both validation scores were `14/16`; report-only
  regression was `15/16` and `16/16`. Neither executed R1.
- Seed `0103` passed R0 `16/16` at epoch 1 and saved exact R1 epoch 4 after
  `929.183 s` of R1 work (`1423.812 s` attempt wall). Its 32 episodes produced
  31 unique REAL observations, 67 lifetime buds, 46 tombstones, 21 live or
  refining candidates under the cap of 32, five positive promotions, five
  live authority roots and authority generation 4. It nevertheless had zero
  post-birth certification receipts, zero certified roots, zero AVAILABLE
  envelopes, zero handoffs, zero successor value, `0/4` exhaustive mate-in-2
  validation, and final R0 retention `15/16`.
- Seed `0104` passed R0 `16/16` at epoch 1 and was deliberately stopped after
  seed `0103` crossed the branch stop rule. Its durable epoch-2 snapshot records
  `459.522 s` of R1 work, 16 episodes, 25 buds, 18 live/refining candidates,
  seven tombstones, three positive promotions and three live authority roots.
  It retained R0 `16/16`, but again had zero certification receipts, AVAILABLE
  envelopes, handoffs, successor value, or `4`-case mate-in-2 conversion.
- Seed `0105` passed R0 `16/16` at epoch 8 but was stopped before a first R1
  snapshot after the same branch-level stop condition. The two stopped
  processes exited `130`; their completed atomic artifacts remain intact.
- Seed `0103` then failed closed only while building its final report. The V4
  request for candidate `37bb8671539c2d44aa4b3e13b8ce9c20` committed exactly
  to 30 inspected receipts from trigger ordinal 33 through frontier 62, but
  its bounded four-ID diagnostic witness list did not include the trigger.
  The old report audit incorrectly treated witnesses as the complete set.
  Authority restoration, full-history validation, inspected/support commitment
  reclosure and certification-discovery separation all passed; this was not
  evidence leakage or a corrupt snapshot.
- Repair commit `4cf1711b9c09b374fc6c55ea33a58d4c0c3d11ee` keeps the legacy
  literal-list rule but reconstructs and verifies the complete trigger-to-
  frontier interval for compact V4 requests. It reports commitment manifests
  separately from bounded witnesses. A deterministic regression fails at the
  exact implementation commit and passes with the repair; the preserved
  epoch-4 snapshot now audits as five lineages, five live roots and zero leaks.
  The exact post-fix focused suite passed `244/244` in `442.55 s`; targeted
  `compileall` and `git diff --check` are clean.
- Decision: **NO-GO for the 1–2-hour gate or a real mate-in-2 curriculum run.**
  The implementation demonstrates renewable local birth, refinement, bounded
  active ecology, retirement pressure, compact replay-safe commitments and
  positive authority promotion. It does not yet demonstrate the indispensable
  next link: a promoted root acquiring post-birth evidence and becoming
  AVAILABLE. Seed `0103` had four roots with authority `birth_frontier=55`
  and event frontier `56`; seven later REAL receipts (ordinals `56..62`) did
  not structurally match them. Its fifth root had `birth_frontier=62` and event
  frontier `63`, leaving no later window. Seed `0104`'s three roots likewise
  had no post-birth window. Thus zero certification is not evidence that the
  roots can never certify; the canaries simply supplied no matching later
  REAL evidence. Even so, the predeclared staged rule required handoff and
  successor-value evidence before authorizing a longer run. That gate was not
  met, so no further seed was launched.

### V15 predeclared post-promotion follow-through

- Purpose: distinguish a real downstream lockout from the V14 horizon effect.
  In seed `0103`, four roots had authority `birth_frontier=55` and event
  frontier `56`, followed by seven nonmatching REAL receipts at ordinals
  `56..62`; the fifth root had authority `birth_frontier=62` and event
  frontier `63`, with no later window. Seed `0104`'s three roots had no
  post-birth window. This is a mechanism follow-through, not a mate-in-2
  performance estimate or a new seed search.
- Post-launch implementation/provenance clarification (no protocol, gate or
  configuration change): literal reuse of `online_composition.py` and
  `episodic_composition.py` was audited and rejected. Their periodic numeric
  pair/global-credit semantics do not preserve V2's positive-only,
  receipt-grounded, event-driven evidence boundary. The implementation instead
  reuses the native `StemCellState`, native graph and native authority
  primitives, while keeping local budding, certification and mutation
  semantics in the V2 ecology/authority path.
- Profile implementation: `4a87eaa0ebd59d85d328c495dfedd4196899783d`.
  The development-only `follow-through` profile differs from `canary` only in
  `r1_epochs = 8` instead of `4`. Random `8/4/4` R1 pools, per-epoch validation
  and snapshots, R0 training/gates, learner parameters, reply policy, action
  ordering, oracle boundary, and resource controls remain byte-equivalent.
- Conditions: fresh runs for deterministic qualifying seeds `2026090103` and
  `2026090104`; one process per seed; all numerical thread pools fixed to one;
  independent output directories; `7200 s`/`8192 MiB` safe-boundary ceilings;
  no resume of V14 snapshots because the source fingerprint changed.
- Required causal chain: post-birth matching REAL evidence, then a certified
  positive root, then an AVAILABLE all-reply envelope, child handoff, nonzero
  exact worst-reply successor value, and finally an exhaustive mate-in-2
  conversion without R0 loss. Certification leakage, replay mismatch,
  uncontrolled active growth or changed protected-core identity stop the run.
- Decision rule: the balanced 1–2-hour gate remains unauthorized unless both
  seeds retain R0 `16/16`, have zero leakage, and show nonzero certification,
  AVAILABLE/handoff and successor-value evidence; at least one actual `4`-case
  mate-in-2 conversion is also required. Otherwise preserve the snapshots and
  stop at the fixed epoch-8 boundary.

### V15 completed outcome

- Provenance and execution: implementation commit
  `58fbd0d8f0f6e8101d8e340570abb8026eb4b201`; fresh independent output
  directories for seeds `2026090103` and `2026090104`; one process per seed
  with one numerical thread; random `8/4/4` R1 pools; exact eight-epoch runs;
  no learner or pool change; `7200 s`/`8192 MiB` safe-boundary ceilings.
  Attempt wall times were `4932.0426137079485 s` and `4845.015892208088 s`;
  R1 full-intrinsic/control times were respectively
  `1920.303802/1939.51825 s` and `1885.137376/1912.423199 s`.
- R0 gate and retention: R0 training took `9.412854/9.320284 s` for
  `0103/0104`. Initial R0 validation/regression were `16/16, 16/16` for
  `0103` and `16/16, 12/16` for `0104`; validation-only R0 entry passed in
  both, while the report-level final R0 pass was true/false. Final
  full-intrinsic and no-bootstrap retention was identical within each seed:
  `0103` validation/regression `15/16, 16/16`; `0104` `16/16, 12/16`.
- Seed `0103` completed 64 R1 episodes with 63 REAL observations and seven
  structural transitions. Full/control ecology slot turnover was
  lifetime births/active/tombstones/promotions/refinements
  `106/103`, `28/27`, `78/76`, `8/10`, `84/81`. Total authority
  candidates/live successors/materialized children were `161/163`,
  `87/89`, `79/79`; the adaptive-positive subset was
  lineages/certification receipts/certified roots `8/10`, `5/5`, `0/0`.
  Authority retirement was `0` candidates and `0` retirement tombstones in
  both arms; the ecology tombstones above are slot turnover, not authority
  retirement. Both arms had zero AVAILABLE all-reply envelopes, zero handoffs
  and successor value `0.0`; exhaustive validation/regression conversion was
  `0/4` and `0/4` (reply mate rate `0.0`).
- Seed `0104` completed 64 R1 episodes with 63 REAL observations and eight
  structural transitions. Full/control ecology slot turnover was
  lifetime births/active/tombstones/promotions/refinements
  `69/67`, `14/10`, `55/57`, `15/17`, `44/41`. Total authority
  candidates/live successors/materialized children were `188/190`,
  `105/107`, `90/90`; the adaptive-positive subset was
  lineages/certification receipts/certified roots `15/17`, `41/39`, `3/2`.
  Authority retirement was again `0` candidates and `0` retirement tombstones
  in both arms. Full intrinsic reached two AVAILABLE all-reply envelopes,
  two child handoffs, and exact worst-reply successor-value sum
  `1.2454048740321941`; its no-bootstrap control also had two AVAILABLE
  envelopes but zero handoffs and zero successor value. Exhaustive
  validation/regression conversion was `0/4` and `0/4` in both arms (reply
  mate rate `0.0`).
- Final graph size from an initial `1` node/`0` edges/`0` triplets was
  `902/27778/111` (nodes/edges/triplets) for `0103` and
  `891/27262/109` for `0104`, identical between the two arms within each
  seed. All adaptive certification records were post-birth and discovery
  disjoint; certification-discovery leaks were `0`, serialized authority
  round-trips were exact, replay cached-outcome mismatches and formal replay
  failures were `0`, and duplicate-VIRTUAL counts were `0`.
- The no-bootstrap controls did not produce a positive causal contrast:
  `development_directional_effect_vs_no_bootstrap=false` and
  `r1_causal_positive_vs_no_bootstrap=false` in both reports. The artifacts'
  focused probe supports only eight-position in-memory deepcopy choice
  equality; it explicitly records serialized snapshot resume as unimplemented,
  so no actual resume-parity claim is made here.
- Post-run production-path verification closes two previously synthetic-only
  gaps without changing learner semantics: an actual event-driven V2 authority
  plus actual boundary ecology now matches uninterrupted execution after an
  epoch snapshot/resume, and a multi-reply policy test proves exhaustive
  virtual enumeration, one minimum-selected REAL challenge and the exact
  minimum-value TD equation. Full relevant suites passed `46/46`, `20/20` and
  `22/22`; targeted `compileall` and `git diff --check` were clean. This test
  evidence does not retroactively turn either fresh V15 run into a resumed run.
- Decision: the mechanism chain (post-birth certification → certified root →
  AVAILABLE envelope → handoff → nonzero successor value) was achieved only
  by seed `0104`'s full-intrinsic arm and was not replicated. Both seeds/arms
  remained at `0/4` exhaustive mate-in-2 conversion, and the R0 gate
  requirement fails (`0103` final validation retention `15/16`; `0104`
  report regression `12/16`). These are viewed development mechanism
  evidence, not independent efficacy. The runner's narrower
  `scientific_gate_passed` curriculum-status field was false for both runs.
  **Strict NO-GO for a balanced/full run.**

### V16 native-local closure implementation and pre-canary gate

- Implementation commit `444b927f07882ae1c197b6006fad1c0672ef2245`
  replaces adaptive R1 hash-scheduled experience selection with local
  UCB-like competition over persistent graph evidence and formal
  `AnonymousChoiceGenome` emission. Only the emitted exact triplet is grown,
  and observed TD credit must return that same identity.
- Adaptive evaluation now uses the corresponding exploration-free local
  policy for the first move and direct fail-closed V2 successor authority.
  Unsupported local patterns are excluded before evaluation competition; an
  empty policy abstains. The old prototype gate, host child-priority cascade,
  and plastic fallback are tripwired as unreachable in this mode.
- Same-run authority construction now partitions the 64 training-only rows
  into 32 digest-selected discovery and 32 disjoint certification rows.
  Nomination closes first; every certification row is a REAL environmental
  interaction followed by content-blind atomic settlement before the next
  row. Receipt, physical-interaction, post-birth, leakage and round-trip audits
  fail closed.
- The complete curriculum is not yet claimed pure-native: R0 pretraining still
  uses content-blind scheduled legal-action exploration, and a domain-generic
  Python adapter retrieves local graph sources and computes normalization,
  curiosity and alias rotation before formal choice. Neither path can read a
  chess answer, held-out outcome, FEN identity, epoch or external oracle.
- Data-free focused verification passed `87/87`; targeted `py_compile` and
  `git diff --check` were clean. Independent review found and closed one
  evaluation blocker (zero-state lucky guessing) and found no remaining
  canary-blocking routing, closure, replay or snapshot defect.
- The predeclared next gate was one fresh seed `2026090106`, `canary` profile,
  an independent output directory, one numerical thread, and
  `7200 s`/`8192 MiB` safe-boundary ceilings; its result is recorded below.

### V16 fresh native-local canary outcome and admission-boundary correction

- Binding: the fresh canary used seed `2026090106` and source commit
  `8e1583972cca391fc10a0d689ebd89f86387471b`, with no learner oracle, tuning,
  protected outcomes, or legacy hash/round-robin first-move picker. Attempt
  wall time was exactly `645.8366680829786 s`; R0 training took `10.239902 s`
  for 48 episodes (2 observed mates, 45 nonterminal outcomes, one failure).
- R0 result: validation was `16/16`; the report-only regression was `14/16`
  (`0.875`). The recorded pre-repair native admission report had
  `14/16` positive authorized/mating responses and `0/16` negative AVAILABLE
  responses, so its old coverage/specificity `pass` was false. The final graph
  grew from `1/0/0` to `555/12006/48` nodes/edges/triplets, with 48 frozen
  policy triplets and 56 total authority candidates.
- This run stopped honestly at R0: `r1_executed=false`, no R1 arm progress was
  written, `curriculum_gate_passed=false`, and `scientific_gate_passed=false`.
  It therefore supplies no R1 result and no mate-in-2 claim. The artifact's
  focused eight-position in-memory deepcopy probe had equal choices, but
  serialized snapshot resume was explicitly unimplemented; no resume-parity
  claim is made.
- Repair `67414302390040bc1047ef4c43489467a2162b38`: R0 authority coverage and specificity remain
  in the read-only admission report (`scientific_coverage_specificity_pass`),
  but no longer add a second global veto after the existing validation-derived
  R0 mastery transition. The native-authority entry check now requires only the
  outcome-blind `runtime_integrity_pass`: immutable authority/source
  continuation, every emitted actuation legal, and every AVAILABLE response
  backed by a legal non-null actuation. An `UNKNOWN` authority response is a
  local abstention: it supplies no successor bootstrap/value and does not
  globally block unrelated R1 environmental experience. R0 mastery and later
  R1 validation stopping/consolidation remain outer scientific-harness stage
  decisions; they do not select or rank moves. The recorded V16 canary predates
  this separation and is not a post-repair R1 test.
- Alias handling now unions only formally confirmed graph signals for aliases
  of the same actuator, so emitted-action trace evidence is alias-invariant.
  Option identity and activation/strength remain local to each triplet alias;
  this normalization does not collapse local option competition or use
  outcomes, labels, or board identity.
- Post-repair verification: 106 focused core tests and 61 additional
  ecology/authority tests passed. Thirty-one historical-compatibility cases
  could not run because two pre-existing result fixtures are absent from this
  checkout; no executed behavioral assertion failed.

### V18 native-local canary and exact failure discrimination

- Fresh development canary: seed `2026090106`, exact source
  `0373c0cc26f719997dd1c8a6e723ef9ce32c92d0`, `canary` profile, one numerical
  thread, independent directory
  `native_local_closure_v18_seed_2026090106_0373c0cc_canary`, `7200 s` wall and
  `8192 MiB` safe-boundary ceilings. It completed in exactly
  `2916.2569021661766 s` with status `COMPLETED_R1_GATE_FAILED`.
- R0: validation `16/16`; terminal report-only regression `14/16`; isolated
  frozen native-policy retention after R1 `16/16`. The evolving V2 shell
  covered only `6/16`; this is jurisdiction coverage, not graph forgetting.
- R1 full arm: 32 episodes over four epochs, 30 fresh REAL successor events,
  three AVAILABLE all-reply envelopes, one child handoff, nonzero successor
  value, and two TD-credit events; exhaustive mate-in-2 validation remained
  `0/4`. All 32 first-move pattern exposures were unique, so neither credited
  decision was revisited and no ranking change can be inferred.
- The run still inherited the old mixed 32/32 bootstrap authority. Its ecology
  recorded zero adaptive births. The observed availability/handoff therefore
  did not demonstrate self-grown outward closure. One exact learned candidate
  could also be lost behind the global retrieval cap, and full TD was copied
  into many shared atoms.
- Decision: preserve V18 as a negative mechanism discriminator. Do not extend
  it and do not infer mate-in-2 learning.

### V19 empty-shell strict adaptive repair and pre-canary gate

- `deedcb90` reserves the exact local branch and one learned incumbent per
  remaining action before challenger capacity, localizes curiosity to the
  current competitor population, and conserves TD responsibility across
  shared atoms according to graph normalization.
- `58abe72d` separates frozen native-policy retention from V2-shell coverage,
  makes V2 integrity fail closed, repairs same-pattern revisit reporting, and
  prevents synthetic nonmate outcomes from being trained as positive.
- `b1a8ed1f` makes R0 and R1 use native local action competition, runs fixed
  budgets with validation outcome mastery report-only, skips the prototype
  gate, and starts adaptive V2 from an evidence-empty positive shell with no
  scheduled frontier. Surprise REAL successes alone can bud future boundary
  hypotheses; discovery evidence remains excluded from certification.
- The adaptive entrypoint now rejects configurations that re-enable scheduled
  actions, memoized R0 replay moves, validation-controlled transitions,
  non-V2 routing, or disabled ecology. A strict no-prototype-gate R1 snapshot
  crash found by independent review was fixed and covered by actual interval
  snapshot/resume tests.
- Purity boundary: learned evidence/credit and exactly-one emission are native;
  the generic adapter still enumerates legal affordances, computes bounded
  curiosity/alias rotation, ranks the adversarial counterexample reply, and
  commits structure at content-blind safe points. The training-outcome R0
  maturity/freeze boundary remains harness-controlled. No whole-curriculum
  endogenous or pure in-graph arbitration claim is made.
- Verification at `b1a8ed1f`: six directly affected compatibility suites
  passed `137/137` in `274.99 s`; targeted strict/no-gate tests passed `5/5`,
  adaptive runner tests passed `21/21`, compilation and `git diff --check` were
  clean. No fresh V19 chess canary had been run when this entry was written.
