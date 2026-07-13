# Graph-Internal Exact Evidence: Implementation Checkpoint

Date: 2026-07-13. Status: implemented and validated before fresh execution.
No seed in the frozen 20262301--20262340 range has been touched.

## Implemented boundary

- `LifetimeDecisionReservoir.add` returns an unambiguous append/rejection/
  replacement mutation while preserving Algorithm-R contents and RNG calls.
- One shared anonymous predicate defines full-scan rent support and incremental
  candidate support.
- Every causal-rent trial owns a disconnected graph-native `EVIDENCE_DEFICIT`
  TERMINAL and AND-gated exploration-request SCRIPT sharing its immutable member
  terminals. Mature and pruned candidates cannot request; pruning removes all
  request topology.
- Proxy and exact paths share request node/edge structure. Their only
  measurement difference is activation count versus exact retained reservoir
  support. The host actuator bus reads emitted graph strength, not candidate
  fields, and request topology has no path to `action_score`.
- Exact support initializes from pre-birth reservoir records, updates on retained
  insertion and eviction, and hard-checks against a fresh scan at enablement,
  proposal, review, checkpoints, and finalization.
- Final cumulative terminal return, zero/one/multi request exposure, unequal
  strengths, possible allocator divergence, selected requester, request graph
  identity, beneficiary trajectories, and RNG-state hashes are persisted.
- The five-arm admission-aware runner implements the frozen independent
  integrity, evidence, maturation, conditional-priority, behavior, stability,
  and transfer gates and persists after every admission candidate, arm, and seed.

## Pre-fresh evidence

Focused library/runner validation passed 43 tests. The complete `recon-lite`
suite passed 85 tests, and all generic-core autogrowth tests passed 53 tests.
Full repository validation passed 828 tests in 2,186.97 seconds.

The deterministic anonymous priority canary produced 100/100 simultaneous
multi-request opportunities, 100/100 unequal-strength opportunities, 100/100
opportunities where allocators could differ, and 53/100 different selected
actions under maximum-deficit versus shuffled responsibility. Main, support, and
event budgets matched exactly. This proves instrumentation identifiability only.

A full-dose, five-arm smoke used retired seed 20262201, 4,096 episodes per phase,
and 128-row development/evaluation slices. All integrity invariants passed. The
exact arm's per-target maximum review supports were 232/140/86/30 versus
activation proxy 236/153/82/24, so paired minimum support improved by 6; new-task
success was 0.555 versus 0.438. One target still died unsupported and neither
maturation nor behavior passed. Exact directed and exact shuffled were identical
on this task because only 6/2,440 canonical exact-arm opportunities were unequal
multi-request events. These are smoke facts, not a scientific claim.

The first smoke attempt found a genuine lifecycle bug: phase-0 candidates had no
initialized rent counter, so an eviction could subtract pre-birth support from
zero. Incremental accounting is now explicitly inactive before causal rent;
enablement performs the required full scan before any mutation is applied. A
regression test covers this boundary.

## Next action

Commit and push this implementation, then start the canonical fresh admission
process in one persistent PTY. At the manifest pause, keep the exact process and
admitted policy objects alive, commit/push the manifest bytes, verify HEAD, and
resume. Do not modify seeds, thresholds, lifecycle, mechanisms, or gates after
fresh phase 1 begins.
