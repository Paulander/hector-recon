# Native R0 competence-envelope V3 training-only result

V3 passed all integrity gates and closed after the frozen three-round lifecycle.
Its scientific verdict is **nomination/responsibility failure**.

## Admission

The corrected runtime generated a new deterministic serialized-wrapper
reference and replayed the same already-touched 64 frames through the real
observation path.

- complete actuation and active-signal mismatches: **0/64**;
- outcomes: **40 successes / 24 failures**;
- policy responses: **64/64**;
- unique evidence identities: **64/64**;
- fabricated reward: **0**;
- direct and wrapper persistent state: **exact**;
- weighted-selector, provider-fallback, and child-priority tripwires: **0**.

The artifact persists all 64 reference rows. Its mismatch and failed-gate rows
are empty rather than collapsed into a Boolean. Reference digest:
`ff05c3712f9306e3fb999027a118c6a14967b377e853c615fa831af9faffde5e`.

## Frozen lifecycle arms

The connected and outcome-shuffled arms used identical V2 code and configuration:
support 4, lower bound 0.55, capacities 32/32 and 192/192, three rounds, genome
seed 2026071606, outcome-shuffle seed 2026071602, and baseline 0.625.

Each arm recorded 192 proposals: 49 admitted plus 15 duplicate rejections in
round 1, then 64 admitted in each of rounds 2 and 3. Thus each arm admitted 177
distinct cells. Both finished with:

- mature cells: **0**;
- available classifications: **0/64**;
- final pruned cells: **177**;
- actual-outcome pure mature cells: **0**.

The few pure proposed cells did not qualify for maturity: connected had one
support-2 refuted cell after round 2 and support-1/support-2 refuted cells at
final review; shuffled had the analogous support-2 and support-1/support-2
positive cells. All were below support 4. Neither arm beat the descriptive
global baseline or produced a competence envelope.

## Exhaustive bounded diagnostic

The post-run diagnostic tested every eligible base-signal singleton, pair, and
triple without retaining millions of pattern rows:

| Arity | Tested | Support-qualified | Pure | Attempted | Matured |
|---:|---:|---:|---:|---:|---:|
| 1 | 120 | 120 | 0 | 0 | 0 |
| 2 | 7,140 | 7,013 | 225 | 0 | 0 |
| 3 | 280,840 | 265,693 | 24,541 | 0 | 0 |
| **Total** | **288,100** | **272,826** | **24,766** | **0** | **0** |

Every pure support-qualified pattern was positive/AVAILABLE. The diagnostic
stored exact histograms, eight examples each for arities 2 and 3, no singleton
examples, and no complete pattern list. Deterministic pattern digest:
`1bc2c16307bf9d875816d0de78e941925f6289c6b69044789534c0ed8fede408`.

## Interpretation

Representation/selectivity is not the immediate binding boundary: many pure,
adequately supported pair/triple conjunctions exist. Proposal admission,
capacity, lifecycle, and evidence accounting were not tested on those useful
patterns because the genome never nominated one. More grace or raw proposal
throughput would not address this result.

The next isolated learning mechanism is **residual-responsibility internal
terminals**: local graph state must identify which active atoms/compositions
remain responsible for prediction error and route nomination toward those
conjunctions without outcome labels or host target knowledge.

Architectural debt remains separate. `extract_active_competence_signals`
reconstructs generic, label-blind signals from board/move/graph maps rather than
consuming actual frame-local terminal provenance. V3 remains valid, but a fully
self-contained native-ReCoN claim is premature. If residual-responsibility is
promising, graph-emitted internal-terminal provenance is the natural subsequent
authority closure.

No validation, regression, retired successor, R1, or fresh data were accessed.
Runtime was 993.659 seconds (16m33.7s).

Validation after closure:

- focused V2/V3 instrumentation and learner tests: **8 passed**;
- focused V3 plus deterministic-runtime tests: **9 passed**;
- full repository suite: **918 passed** in 53m01s.

Canonical artifact:

- `reports/autogrowth/native_authority/touched_r0_competence_envelope_v3_training_only.json`
- SHA-256: `91b3ae80773f2c2dd20cd00b82f5a1fde8190deef670623ea9ba39db9d514d94`
