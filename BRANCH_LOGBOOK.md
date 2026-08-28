# Branch logbook

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

## Code lineage

- `f9f12628cb303c9326a00acfc138e0d471410a65` — audited starting point for
  incremental-history runtime work.
- `93ffeba3ac46d47be30a5225ed092151bef03ec3` — incremental REAL-history
  validation reclosure; retained explicit full reconstruction at trust
  boundaries.
- `b6848ef4e3eb27d022ac6c67f3c903c962907737` — authority-graph settlement
  optimization; audited core for the v2 development benchmark.
- `97cce727442da25c4a5c443897550ccc9c6758b4` — bounded, atomic Phase-1
  checkpoint runner and tests; current HEAD.

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
