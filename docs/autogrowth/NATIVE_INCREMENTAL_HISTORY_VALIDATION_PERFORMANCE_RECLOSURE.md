# Native incremental history-validation performance reclosure

Status: performance engineering only; no ReCoN scientific factor, learner
parameter, seed, genome, topology, threshold, capacity, arm, stream, or outcome
definition is changed.

## Scope and source identity

- Audited/source commit:
  `f9f12628cb303c9326a00acfc138e0d471410a65`.
- Development branch:
  `codex/incremental-history-validation-reclosure`.
- The active frozen 32-seed experiment was not opened, contacted, reproduced,
  stopped, or restarted. Its manifests and result placeholder were not changed.
- Verification uses a newly created synthetic KRK development canary. No fresh
  experiment outcome was opened or reconstructed.

## Runtime defect and bounded repair

Every routine call to `NativeProspectiveAuthorityV2._verify_invariants()` ended
by rebuilding all accepted REAL history. Event opening called the rebuild once;
atomic consumption called it before and after the event. At history length
`n`, one event therefore repeated `Theta(n)` receipt validation, graph replay,
lifecycle derivation, emission derivation, request derivation, and ledger
comparison. A seed with `n` events paid `Theta(n^2)` validation work even when
history was healthy and append-only.

The repair adds a non-authoritative, append-only canonical hash chain. Each
accepted REAL event commits its contiguous position, previous history digest,
pre-event continuation digest, canonical signed receipt, consumed transaction,
accepted physical reference, and graph emission. The live and cached REAL-event
openers commit the same predecessor. Receipt signature, ordinal, pending-token,
trace, graph commitment, stable physical identity, duplicate, successor, and
outcome checks remain unchanged and run once for the new event.

Routine invariants now compare constant-history chain/cardinality facts and the
open event's predecessor commitment. The authority graph never reads the new
chain. Complete reconstruction remains authoritative and fails closed at:

- explicit differential checks;
- restoration;
- serialization, including Stage-A and final frozen-authority payloads.

No mismatch is repaired. Boundary errors identify the boundary and distinguish
predecessor disagreement from final chain disagreement.

## Differential and adversarial evidence

The focused synthetic test compares incremental validation with the retained
legacy full-replay mode after every one of 12 accepted events. Pending events,
traces, signed receipts, emissions, candidate lifecycle state, topology,
requests, continuation manifests, and final serialized state are exact.

It also covers duplicate idempotence, both skipped and reordered ordinals,
reminting one physical interaction under a new receipt identity, midpoint
serialization/restoration followed by continued learning, injected predecessor
disagreement, injected chain-head disagreement, and exact live-versus-cached
opening through final consumed state.

Focused result: `4 passed`. Adjacent data-free composition/sharding result:
`22 passed`; one separately invoked byte-identity check could not run because
its sparse, frozen source-manifest file was not materialized. Fetching retired
report/serialized fixtures was rejected rather than risk opening an outcome
artifact. Historical manifest guards that bind the modified authority source
are expected to require a future package reclosure and were not rewritten.

## Synthetic timing curve

Environment: Apple arm64 Mac, macOS 26.6.1, Python 3.12.13. Values are medians
from a newly generated one-cell KRK canary; they are development evidence, not
an estimate for the active run.

| Accepted events | Incremental invariant | Legacy replay invariant | Validation speedup | Incremental whole event | Legacy whole event | Whole-event speedup |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.0494 s | 0.0532 s | 1.08x | 0.428 s | 0.436 s | 1.02x |
| 4 | 0.0500 s | 0.0705 s | 1.41x | 0.427 s | 0.508 s | 1.19x |
| 8 | 0.0497 s | 0.0862 s | 1.74x | 0.440 s | 0.560 s | 1.27x |
| 12 | 0.0490 s | 0.1037 s | 2.12x | 0.450 s | 0.610 s | 1.36x |
| 16 | 0.0501 s | 0.1222 s | 2.44x | 0.453 s | 0.673 s | 1.48x |
| 24 | 0.0490 s | 0.1566 s | 3.19x | 0.461 s | 0.791 s | 1.72x |
| 64 | 0.0495 s | 0.3285 s | 6.64x | 0.503 s | 1.360 s | 2.70x |

At 64 events, the intentional full-reconstruction boundary was 0.333 s,
serialization including that boundary was 0.389 s, restoration including it
was 0.493 s, and one graph measurement was 0.0011 s. Tracemalloc validation
peaks stayed approximately flat at 1.93 MiB incremental and 1.96 MiB legacy in
this small canary. The incremental invariant curve is flat over history length;
the boundary curve retains the expected linear reconstruction cost.

The remaining whole-event slope is dominated by the deliberately unchanged
`copy.deepcopy(self)` atomic transaction, serialized ledger growth, and explicit
boundary work—not authority-graph measurement. That is the next bottleneck, but
it is outside this first-mechanism reclosure.

## At most three next-run optimizations

1. Replace whole-authority deep copy with copy-on-write transaction state, while
   preserving atomic rollback and proving byte-exact continuation parity at
   every failure boundary.
2. Keep full reconstruction only at the present explicit trust boundaries and
   batch artifact serialization where the runner currently creates redundant
   round trips, without weakening any accepted-complete boundary.
3. Only after copy-on-write evidence, profile canonical JSON/pickle ledger
   materialization and consider a streaming serialization digest; do not alter
   learner inputs or evaluation semantics.
