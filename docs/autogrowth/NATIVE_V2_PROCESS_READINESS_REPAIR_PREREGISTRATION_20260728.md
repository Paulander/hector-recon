# Native V2 Process Readiness Repair — Preregistration and Compliance

Date: 2026-07-28

Starting commit:
`f9f0afde10b7ad2bf6ad817bd04c2d47fefabb74`

Package:
`native_v2_process_readiness_repair.v1`

This is a bounded, data-free, outer-orchestration repair. Every existing
package, artifact, cohort, seed, organism, ecology, target, threshold, graph
rule, and statistical rule is immutable. Real exposure, outcomes, KRK R1,
retired-65, historical regression, and learning are forbidden.

## Pre-implementation compliance table

| Requirement | Frozen implementation | Required proof / stop |
|---|---|---|
| Preserve prior work | New module, package ID, paths, tests, manifests, readiness, and result only. Existing files are hash-bound and unchanged. | Repository comparison from the starting commit must show no prior-file change. |
| Small outer repair | Reuse the existing production unit builders, registry, unit-analysis rules, graph/learner code, and canonical driver validation. | If a large driver or any learner/registry/laboratory implementation must be copied, stop without implementation. |
| Correct runtime verification | One new `verify_runtime_inputs` helper performs preserved-byte verification. Readiness and the production runtime builder both call it. The retired import-sensitive verifier is absent from the new call graph. | Execute the real runtime-builder call path with data-free substitute dependencies and call counters; a retired-verifier sentinel must remain untouched. |
| Journal admission before outcomes | Reconstruct production bindings, analyze the exact journal, require 96 complete commits and no unfinished/foreign record, bind chain/unit/recomputation counts, then rebuild exposure and execution solely from committed results and byte-compare committed files. | Deletion, alteration, truncation, reordering, replacement, incomplete preparation, and foreign suffix all stop before the science marker. |
| Restart semantics | Keep the existing outcome-blind recomputation law and exact committed-record comparison. | Documentation must state that checkpoints preserve correctness and completed records, but restarts currently regenerate earlier committed units and need not preserve all prior computation time. |
| Complete science marker | Existing markers must match schema, package, experiment, consumed-suffix declaration, cohort/map identities, exposure, execution, and completion identities. | Change any field and marker validation stops. |
| Partial outcome accounting | Validate the durable hash chain, canonical seed/row/arm/event order, transition identities, and checkpoint progression. Reuse the driver’s complete-seed sequence validator. | Any semantic inconsistency reports `unknown`; zero is known only for a valid empty canonical prefix. |
| Interrupted temporary files | Use one precisely named package-specific temporary path per final target. A byte-identical fsynced temporary may complete its rename; divergence or ambiguity stops with the exact path. | Tests interrupt after fsync/before rename, prove exact recovery or exact stop, and reject unrelated worktree files. |
| Production service recorder | Every launch receives a unique attempt ID, service, stdout, and stderr path. It binds exact HEAD, committed readiness hash, literal four-item Python command, environment, and working directory; rejects concurrent matching work; polls to a terminal state and records process/timing/status/runtime-limit/log facts. | No shell, no wall limit, no fixed shared service/log, no attempt overwrite. Lawful restart requires a new attempt namespace. |
| Detached canary | Use the exact production launch/poll/final-record path for a low-cost sleeping child lasting at least 1,080 seconds. | Launch returns immediately. Short polling commands observe it. The final record must show a distinct process, terminal success, effective unlimited runtime, and exact logs. |
| Validation boundary | Focused and adjacent suites only; actual production paths use data-free substitutes in tests. | Any unexpected scientific access, prior-file mutation, or need to change a frozen factor stops the package. |
| Delivery boundary | Commit/push preregistration, source/tests, manifests, launch readiness, detached-canary record, final readiness/result, and BRIEF update in distinct logical stages. | Stop for independent review with real exposure and outcomes unopened/not evaluated. |

## Fixed engineering choices

- Arms, seeds, rows, admission thresholds, statistics, and outcome rules are
  inherited byte-for-byte from the prior package.
- Exposure remains 96 ordered units: A/0–31, B/0–31, C/0–31.
- The completion marker remains the authority for exact unit count, journal
  chain, and recomputation count.
- The long canary duration is 1,085 seconds and performs only a sleep plus one
  final JSON write.
- User-level transient services use `Type=exec`, `RemainAfterExit=yes`, unique
  file outputs, no shell, and no `RuntimeMaxUSec` limit.
- A service attempt is never reused. An interrupted lawful production run is
  continued only by launching the same frozen command under a new attempt ID;
  the durable experiment journal determines remaining work.
