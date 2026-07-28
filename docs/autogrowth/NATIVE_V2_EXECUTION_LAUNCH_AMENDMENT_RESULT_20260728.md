# Native V2 Execution Launch Amendment — Result

Date: 2026-07-28

Starting commit:
`e6c4a292a4fd4a448ce7a1bb12aae713e656f8dd`

Package:
`native_v2_execution_launch_amendment.v1`

## Verdict

**PASS — data-free production-launch readiness only. Stop before exposure.**

The bounded outer amendment now makes committed final readiness a prerequisite
of both production launch and both production child paths. It binds each
launch to an exact attempt, Git HEAD, final-readiness bytes and digest, literal
four-item Python command, environment, working directory, logs, and package
identity. A child invoked without that exact recorded context stops before
delegated work.

Canary preparation alone uses launch readiness. Final readiness revalidates its
complete source, binding, launch-readiness, canary, cohort, package-map,
zero-access, and stop-before-exposure identity every time it is loaded.

Real exposure was not run. No outcome environment was constructed and no
scientific outcome was read. Exposure qualification, exposure counts, outcome
counts, effects, probabilities, engagement, and all scientific gates are
**not evaluated**. The zero-access field is boundary telemetry, not an
experimental result.

## Closed boundaries

| Boundary | Final behavior |
|---|---|
| Final readiness | The production launcher, exposure child, completed-exposure/science admission, and science child all require the committed strict loader. Launch records bind final-readiness SHA-256 and canonical digest. |
| Recorded child path | Direct `run-exposure` and `run-science` child commands stop without the launch-service attempt ID, launch digest, final-readiness identity, exact command, and exact external launch record. |
| Launch identity | The child independently reconstructs and compares schema, package, command, service name, Git HEAD, Python argv, working directory, log paths, environment, package identity, and literal no-shell service command. |
| Lawful restart | Canary requires a clean tree. Production launch permits only the inherited exact journal, marker, carrier, exposure, execution, result, or failure paths, including the inherited deep filename scan. A valid partial exposure journal may relaunch under a new attempt ID; unrelated or look-alike files stop. |
| Interrupted files | Entry derives the exact target of each recognized pending temporary. Target-plus-temporary stops with both paths. Temporary-only state is reserved for the existing exact byte-recovery path. The actual science-child entry is tested to stop before its delegated outcome path when marker and temporary coexist. |
| Production records | Terminal exposure/science records have exact command/attempt repository paths. Successful exposure records bind exposure, execution, and completion artifacts and must be committed before science. Successful science records bind the corresponding attempt and scientific result. Failed or interrupted terminal records remain preserved. |
| Launch race | An atomic per-command external lock surrounds concurrency inspection, attempt creation, dispatch, and initial observation. A new attempt cannot overtake an active or unresolved matching attempt. |
| Cleanup | Terminal metadata and log hashes are durable before cleanup. Cleanup records exact `stop` and `reset-failed` commands, then independently requires the unit to be `not-found/inactive/dead` with PID 0. An exact already-unloaded response after successful stop is accepted; any other response or remaining unit fails. Finalized polling is byte-idempotent. |

No learner, graph, registry, laboratory, cohort, organism, seed, ecology,
target, threshold, journal-admission rule, statistic, exposure implementation,
or outcome implementation changed. The outer module imports and delegates the
previously passed implementations. No large scientific driver or module-global
replacement was introduced.

## Validation

- Final focused amendment suite: **63 passed in 9.53 seconds**.
- Final focused-plus-adjacent run: **202 passed in 384.71 seconds**.
  This comprises the 63 amendment tests plus 139 frozen process-readiness,
  execution-adapter, restart, and package-map tests.
- Full repository suite: not run, as instructed.
- Real exposure: not run.
- Outcomes: not run.

The final focused suite covers every final-readiness field, nested canary
launch identity, material canary gates, exact final-readiness use at launcher
and child entries, manual-child rejection, full recorded command/environment
reconstruction, exact runtime paths, partial-journal relaunch, atomic launch
locking, orphaned-attempt handling, marker/temporary ambiguity through the
science child, exposure service/artifact binding, failed-record preservation,
science-result binding, terminal capture before cleanup, exact unloaded-unit
adjudication, and idempotent final polling.

## Preserved provisional findings

Two development canaries found launch-only defects before the final freeze.
Both are preserved rather than overwritten.

1. `provisional_cleanup_gate_failure/`: the 1,085-second child exited zero, but
   `stop` unloaded the transient unit and the subsequent exact “unit not
   loaded” response from `reset-failed` was incorrectly treated as cleanup
   failure. The unit independently read `not-found/inactive/dead`, PID 0.
   The exact launch, dispatch, observation, terminal, cleanup, logs, and first
   manifests remain committed.
2. `provisional_final_readiness_gate_failure/`: the corrected cleanup path
   passed end to end, including an idempotent re-poll. Final-readiness creation
   then stopped before writing because it looked at `launch.readiness` instead
   of the schema's `launch.identity.readiness`. That source freeze and passing
   service record remain committed.

The final source factors the canary check into one function used by both
readiness creation and every later readiness load. The final authoritative
canary was launched anew under the resulting source manifest.

## Final detached canary

- Attempt:
  `20260728T194334475115Z-961f071e3cce4b86883dca4552464d14`
- Launch HEAD:
  `29147411ad4b2ea0c97c989cf146b72b7a399df1`
- PID: `1549546`
- Service timestamps: 21:43:34–22:00:51 CEST
- Child elapsed: `1085.0545391429914` seconds
- Effective runtime maximum: `infinity`
- Exit status: `0`; signal status: none
- Stdout: 640 bytes, SHA-256
  `316c96fa7859bffce9b21d7d96c91236f54b826f42fcd71efff262ff49be8b41`
- Stderr: 0 bytes, SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Terminal-capture digest:
  `f3284a2cd4ea11026e2aab571af03a2f137c15273a3ca7b075d0ba484ffbb165`
- Cleanup-adjudication digest:
  `8fde905ae10717920ecb7d4a322a2a619bb11c7ccc9ed9f6d49e13c3f8869974`
- Final-record digest:
  `152b0338981a582c664da3649c38247a29b8f0ce22cd64fac78d048d6fe198db`

The unit was confirmed absent after cleanup. The canary record is committed
and the strict final-readiness loader accepted it after final readiness was
committed.

## Canonical commits and hashes

- Preregistration commit: `431d1df`
- Final source-freeze commit:
  `d18306c230d84c8468317bcb0adeb5169ddc247b`
- Final manifest commit: `c64ef4b`
- Final launch-readiness commit: `2914741`
- Final canary-record commit: `863624f`
- Final-readiness commit: `59b2cf4`
- Source-manifest SHA-256:
  `957b727bcb9ec7bc31d9ceccedf1e6a23f094b0822fea26903794ee1e44ab318`
- Source-manifest digest:
  `754f9d5cd7f80b1410598f322d032a3b02691e3342cd5045092ffa9dfe30cf79`
- Artifact-binding SHA-256:
  `c19eecf528489d46256e013802f1008f08df063c7536499b4604530015fb7127`
- Artifact-binding digest:
  `7d67fb420042ea661ce6b34171eb6926cdb644888a8a01b5845972c1895b2364`
- Launch-readiness SHA-256:
  `ba9954ecd21803e7d6545f5822a6843fde0d3be50243b50b94bf7e2b885544d7`
- Launch-readiness digest:
  `4c64d97ad1424abd91e59c097a1341a96b5d8b26c624bc6ce9e2884b7f52e368`
- Canary-record SHA-256:
  `e7d26df842e35e1f39ab545a18bd0d572b9a1050551ecdd2db8ba82d564d426d`
- Final-readiness SHA-256:
  `11450ce7a49c34fe8b349f9eef554f95ccc4566f5caeec7becb0bd47bd3ec366`
- Final-readiness digest:
  `420622a02696ca0b352ff949a837d6705d062b8164fc7790f386d74a4612f74e`

## Frozen future workflow

Only the recorded service workflow is documented:

```text
.venv/bin/python3 -m recon_lite_chess.autogrowth.native_v2_execution_launch_amendment launch-service --command run-exposure
.venv/bin/python3 -m recon_lite_chess.autogrowth.native_v2_execution_launch_amendment poll-service --attempt-id <attempt-id>
```

Only after an admitted exposure, its execution artifacts, and its successful
terminal service record are reviewed and committed:

```text
.venv/bin/python3 -m recon_lite_chess.autogrowth.native_v2_execution_launch_amendment launch-service --command run-science
.venv/bin/python3 -m recon_lite_chess.autogrowth.native_v2_execution_launch_amendment poll-service --attempt-id <attempt-id>
```

Neither production launch was performed. The package stops here for
independent review.
