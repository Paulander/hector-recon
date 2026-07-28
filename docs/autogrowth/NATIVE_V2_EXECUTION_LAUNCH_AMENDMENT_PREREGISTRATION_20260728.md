# Native V2 Execution Launch Amendment — Preregistration

Date: 2026-07-28

Starting commit:
`e6c4a292a4fd4a448ce7a1bb12aae713e656f8dd`

Package:
`native_v2_execution_launch_amendment.v1`

This is one bounded, data-free outer launch amendment. The complete
`native_v2_process_readiness_repair.v1` closure and its artifacts are immutable
pre-review inputs. The amendment imports and delegates its passed verification,
96-unit journal reconstruction, science-marker identity, partial-outcome
accounting, exposure implementation, and science implementation.

Real exposure, outcomes, learning, KRK R1, retired-65, and historical
regression are forbidden in this package.

## Compliance table

| Requirement | Frozen amendment | Required proof / stop |
|---|---|---|
| Preserve the pre-review closure | Use a new module, package ID, paths, manifests, launch readiness, canary, final readiness, service records, result, and tests. Hash-bind the existing source, tests, manifests, canary, readiness, and result document. | No path that existed at the starting commit may change except the append-only BRIEF update at final delivery. |
| Final readiness is a production prerequisite | One committed loader verifies the complete amendment readiness identity: source, binding, launch readiness, canary, pre-review closure, cohort, package map, zero access, and stop-before-exposure fields. Production launcher and both production child/admission paths call it. | Missing, uncommitted, or altered readiness stops before launch or delegated work. Canary preparation alone uses launch readiness. |
| Lawful restart | Canary launch requires a fully clean tree. Production launch permits only the exact runtime paths already defined by the pre-review package. | A valid partial exposure journal may relaunch under a new attempt ID; any unrelated or look-alike path stops. Existing journal recomputation law is unchanged. |
| Temporary ambiguity at entry | Scan only recognized pre-review temporaries and derive each exact target. Target-plus-temporary stops with both paths. Temporary-only state is left exclusively to the existing byte-exact atomic recovery path. | Actual science child entry with marker plus marker-temporary stops before its injected outcome-environment constructor. |
| Recorded production path | `run-exposure` and `run-science` children require a validated external launch record and environment context containing the unique attempt, launch digest, final-readiness identity, and exact command. | Manual child invocation stops before delegated work. |
| Production records | Terminal canary, exposure, and science records are copied automatically into precisely recognized amendment paths. Successful exposure records bind exposure, execution, and completion artifacts; science admission requires that committed record. Successful science records bind the outcome result and attempt identity. Failed/interrupted attempts remain preserved. | Missing, foreign, altered, unsuccessful, or uncommitted exposure record stops science. |
| Launch race | Acquire an atomic per-command external lock before concurrency inspection and attempt creation. Release only after the launch record and initial service observation are durable. | Two simultaneous launchers cannot both pass. A leftover lock stops without guessing. |
| Retained-service cleanup | Persist terminal metadata and log hashes externally before service cleanup. Then stop and reset the retained unit, persist cleanup, and finally persist the immutable final record. | Polling a finalized attempt is byte-idempotent. An interruption between terminal capture, cleanup, and finalization resumes without replaying cleanup actions already recorded. |
| Validation boundary | Use focused amendment tests plus the adjacent frozen process suites. Run one corrected detached canary longer than 1,060 seconds. | No production child, real row probe, outcome environment, or learning path may run. |

## Fixed design

- Public workflow:
  `launch-service --command run-exposure`, then
  `poll-service --attempt-id ...`; only after admitted exposure review,
  `launch-service --command run-science`.
- Each service child command remains a literal four-element Python command:
  interpreter, `-m`, immutable module path, exact child command.
- Launch context is an integrity binding, not a secret capability.
- External attempt records remain under a unique per-attempt directory.
- Repository terminal records use exact command/attempt paths and are
  append-only.
- The corrected canary duration is 1,085 seconds.
- A successful exposure service record can be consumed by science only after
  it and the bound exposure artifacts are committed.
- The eventual amendment science-result binding is written only after a
  successful terminal service record exists.
- Any implementation need to copy a large driver, replace module globals, or
  change a passed scientific factor terminates this package.
