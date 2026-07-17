# Deterministic native activation closure — result

The engineering closure passed. It used only the already-touched 64-event tape
and preserved commit `dd5728d` plus the V2 abort artifact byte-for-byte.

## Result

- Complete direct-organism versus serialized-wrapper `GraphActuation` parity:
  **64/64**, including bit-exact IEEE-754 activation.
- Field-level mismatch rows: **0**. The empty list was persisted before gate
  evaluation.
- Active competence-signal parity: **64/64**.
- Preserved discrete action/option parity: **64/64**; no action, actuator,
  option identity, candidate count, formal tick count, graph-owner flag, or
  fallback flag changed.
- Outcomes: **40 successes / 24 failures**, unchanged row by row.
- Evidence identities: **64/64 unchanged**.
- Persistent direct and serialized-wrapper organism state: **exactly
  unchanged**.
- Fabricated reward: **0**.
- Runtime: **1,315.515 seconds** (21m55.5s).

Validation after closure:

- Focused deterministic and planted-authority tests: **6 passed** in 9m39s.
- Full repository suite: **913 passed** in 51m41s.

The bounded planted mature-envelope authority regression also passed under the
corrected runtime. The connected mature envelope selected `e4d3` in exploit
mode. Empty and disconnected envelopes both selected `g2b2` in exploration
mode. Thus numerical canonicalization did not alter the previously established
causal authority result.

Canonical artifact:

- `reports/autogrowth/native_authority/deterministic_native_activation_closure.json`
- SHA-256: `d0940d7375aacd647b0d390c93d2c37f0308636569236740e7a1497ce32445b7`

The preserved V2 artifact remains:

- SHA-256: `dc0b5a7df130295b83075e5211f8237263fd1d59c271c39d47ee3996c4fcdb6b`

## Interpretation

The V2 admission abort was caused by a real determinism defect, not a changed
chess decision or competence signal. Unordered floating-point reductions
produced process-dependent activation drift below approximately `4e-16`.
Sorting contribution identities and combining their values with `math.fsum`
closed the exact contract without rounding, tolerances, hash-seed pinning, or
removing activation from the comparison.

This is an instrument/runtime closure, not evidence that competence can be
learned. V2 remains an abort and was not rerun. No validation, regression,
retired-successor, fresh, R1, or competence-growth data were touched.

The authorizing message referred to V3 “as described below” but supplied no V3
design. Therefore V3 was not inferred or run. The next action is to obtain and
freeze that missing specification.
