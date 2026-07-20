# Native terminal-trace authority closure result

Date: 2026-07-20
Branch: `codex/native-krk-resume-composition`
Base: `660c4eb7718bc7cc8ceccb04716e405dc4215ae4`
Scope: behavior-preserving engineering only; touched 64-event training tape plus already-viewed 32-row development tape.

## Verdict

PASS. The production competence organism now learns and infers from the selected formal graph trace and environment-minted grounded-outcome receipts. The laboratory no longer supplies active signals, completion booleans, lifecycle wiring, specialization mode, genome, parent/member identities, or eligible specialization sets through the production observation path.

This is an authority and continuation-contract closure, not new KRK evidence.

## Canonical result

- artifact: `reports/autogrowth/native_authority/native_terminal_trace_authority_closure.json`
- SHA-256: `2cd0010559599b10b7ff3cd5246cae96a8587b274513417201d882d640bf8bef`
- runtime: 4652.798 seconds
- serialized organisms: 96 compressed artifacts (32 organisms x 3 arms), 27 MiB
- trace admission: 64/64 touched training receipts and 32/32 viewed-development receipts; zero mismatches
- all 32 source reconstructions: exact
- all direct/serialized/VIRTUAL classifications: exact
- all 96 V3 restore checks: exact
- all before/after persistent-state checks: exact
- regression, retired-65, fresh, and R1 access: zero

## Frozen behavior reproduced

| Arm | TP | FP | safe-narrow | strict |
|---|---:|---:|---:|---:|
| local contrast | 220 | 0 | 30/32 | 3/32 |
| demotion only | 119 | 0 | 17/32 | 1/32 |
| counterexample blind | 169 | 0 | 22/32 | 3/32 |

Local and blind specialization each reproduced 37 requests, 37 attempts, and 37 admissions. Local children ended at 34 MATURE and 3 PROBATION; blind ended at 12 MATURE.

## Engineering localization during closure

A preliminary replay exposed one non-behavioral V3 failure: `cell_complete_state_sha256` used raw pickle bytes, whose memo/layout representation changed across serialization even when the complete cell fields, V2 manifest, canonical graph, actions, and learning behavior were identical. The run was stopped after two organisms.

The checksum was repaired by canonical recursive encoding of every persistent cell field, including nested XP and lifecycle state. It was not rounded, omitted, or tolerance-relaxed. A populated-cell round-trip regression now proves exact V3 restoration and nested XP sensitivity. The entire canonical package was then rerun from the beginning.

## Validation

- focused authority and behavior-preservation suites: passed
- populated-cell V3 round-trip regression: 1 passed in 69.37 seconds
- clean full repository suite: 976 passed in 3565.24 seconds (59m25s)

## Interpretation and stop rule

The frozen competence behavior survives removal of the laboratory evidence/eligibility authority. This establishes the trace-native organism artifacts needed for the separately frozen inference-only historical regression package. It does not establish fresh generalization, R1 handover, or end-to-end KRK.

Stage 2 may begin only after this result, implementation, tests, and all 96 artifacts are committed and pushed, followed by a separate preregistration/manifest commit and push before any regression FEN is constructed or logged.
