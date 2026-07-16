# Native frame purity and competence authority closure result

Date: 2026-07-16
Package: NATIVE_FRAME_PURITY_AND_COMPETENCE_AUTHORITY_CLOSURE
Status: engineering canary passed; stop for external review
Preserved scientific result: commit 1501a18 and its canonical admission abort

## Scope and provenance

This package did not rerun the competence package, update or grow the competence
envelope, update R1, or access validation, regression, the 65 retired successors,
final, or fresh pools. It used only the already-touched 48 R0-train and 16
train-decoy event tape. The implementation was frozen in commit 3ce6d2b before
the one admission-only canary ran.

Canonical artifact:
reports/autogrowth/native_authority/native_frame_purity_competence_authority_closure.json

- artifact SHA-256:
  cfb48cb8f772d95ae4bb20f6eab5aef479e06b702bd761863e32a572ef8c1f53
- tape SHA-256:
  91a195b2feed4f59dad49437163af5c24588af9622cacaabe4ecf8270a84a3b2
- permutation SHA-256:
  9bfda19f03665787011ac55620ead343db9717754cc073e5d51f6cfcba5e961f
- permutation seed: 2026071701
- runtime: 1957.68 seconds (32 minutes 37.68 seconds)

## Counts persisted before gates

| Subgroup | Success | Failure | Response-present failure | Total |
|---|---:|---:|---:|---:|
| R0 train | 40 | 8 | 8 | 48 |
| Train decoy | 0 | 16 | 16 | 16 |
| Overall | 40 | 24 | 24 | 64 |

All 64 evidence keys were unique. Both outcome classes were present, and the
predeclared minimum of 12 observations in each class passed. Every failure still
had a policy response. This demonstrates that the ability to emit an action is
not evidence that the child is competent in that frame.

The prior canonical abort recorded 46/18 under the pre-purity implementation.
That abort remains immutable. The corrected frame-local inference path records
40/24 on the same touched tape. This is an engineering behavior change caused by
removing persistent transient runtime from inference, not a rerun or result of
the competence learner.

## Frame purity

Natural order, a repeated natural order, and the frozen permutation produced
identical per-frame actions and complete ChildResponse values for all 64 frames.
Cross-frame contamination count was zero.

The following hashes were byte-identical initially, after the real pass, after
all virtual passes, and finally:

| Persistent component | SHA-256 |
|---|---|
| Topology | 0a81d006e46bbb523b53f81472134300359f50ec9337eae8be6e2de13f52da68 |
| Weights | 2d4fa0269c8f31ffb5c79dd41284be601862d2f8433f3c02f2df298d83ea6e1c |
| Credit | 7fbab646098511a55b3f280870c79d365aefe03e60030e7ad85b8835479940d2 |
| Lifecycle | 6e4ec98eff5110fcea0e210fcc48201b12e8d3ba03f57d5e4aa6e733499d9bb1 |
| Exact state, including transient fields and telemetry | 0cd83f20af8b5beaee9faa2ee2276339138709a2e37a639ad036c2110d9da533 |
| Normalized serialized state | 141431a9e1ff1146bb5d92b3eaf547b4e944f8b67ed1f3e0ba1424bfbec2ea05 |

The exact audit includes runtime fields and scheduler telemetry. Passing is
therefore proof of non-mutation, not the result of weakening a digest.

## Competence authority

A serialized and restored NativeR0CompetenceOrganism was passed directly to
NativeHandoverGenome.query_child_slots. It produced 23 child-slot queries. The
unlearned envelope correctly marked every response unavailable, persistent
state remained exact, and no experiment-level availability injection was used.

The connected learned path is covered by a fail-hard contract preventing calls
to experiment-level response_with_availability. Laboratory injection and
shuffle helpers remain restricted to explicitly named control paths.

The causal synthetic check also passed:

- the mature connected envelope selected target e4d3;
- disconnection fell back to g2b2;
- the shuffled envelope selected its preserved-multiset target e4d4, not e4d3;
- no competence growth occurred.

Thus a mature competence envelope can causally control the native handover via
the actual wrapper/dream-session path. This does not show that such an envelope
can yet be learned.

## Validation and binding interpretation

Focused validation passed: 47 tests in 156.62 seconds, including eight new
frame-purity/authority contracts. Full repository validation passed: 904 tests
in 2413.11 seconds (40 minutes 13 seconds).

Every canary gate passed: evidence uniqueness and class balance, zero fabricated
reward, real and virtual persistent identity, frame-order invariance, direct
wrapper authority, causal synthetic envelope, and zero competence growth.

This closes the engineering boundary only. It makes no competence-learning,
native R1, curriculum, or fresh-data claim. Stop for external review; do not
grow the envelope or reopen the preserved competence package from this result.
