# Native V2 R0 handover development result

Result: **closed before handover measurement**. The fixed seed did not satisfy
the preregistered natural-R0 competence gates, so no retired-65 child-query
measurement, Mate-in-2 parent action, causal canary, fresh row, or R1 learning
was executed.

- Source tag: `tg26m-v2-portable-outcome-result`
- Package freeze: `a888b009fa5f85f9d085eb055016d70dddd5d7e7`
- Fixed genome seed: `927199493097905893`
- Closed artifact SHA-256:
  `2b5e69031a37b84d43d9c1ea02915eea3e23c76a86bb723d48e58015d710d3cd`
- Preserved pre-handover attempt-01 failure SHA-256:
  `a263198d349aacc2d75482fc420cecfe779b1a54da824714f27d9aab8b2fb985`

## Interface result

The two reviewed defects were confirmed and repaired in place:

1. V2 virtual queries now classify the exact frozen R0 graph trace through the
   prospectively certified V2 authority and emit binary constant-strength child
   availability with certification provenance as telemetry only.
2. Parent exploitation now requires a legal actuator, a nonempty reply set,
   and all replies AVAILABLE. Zero-strength child responses cannot qualify an
   exploit option; immediate mate uses a separate completion route.

Focused verification passed: 18 expanded V2 transaction, certification,
revocation, serialization, topology and handover checks, followed by 12 final
package/interface checks. REAL/VIRTUAL trace and action parity, serialization
availability parity, and R0 retention all passed in the closed run.

## Touched-data gates

| Split | TP | FP | TN | FN | Abstentions | Availability coverage |
|---|---:|---:|---:|---:|---:|---:|
| Validation (16 positive + 16 decoy) | 14 | 2 | 0 | 0 | 16 | 50.000% |
| Regression (16 positive + 16 decoy) | 11 | 0 | 0 | 0 | 21 | 34.375% |

- Combined positive availability: **25/32**, below the required 29/32.
- Validation decoy false positives: **2/16**, above the required 0/16.
- Regression positive availability: **11/16**, below the required 14/16.
- Identical typed-trace mixed-outcome groups: **0**; the required UNKNOWN
  check could not be established.
- Exact evidence/handover board overlap: **0**; symmetry-orbit overlap: **2**,
  so the disjointness gate also failed.
- R0 retained behavior: **32/32**.
- Prospectively certified cells: **2**; contradiction-driven clearings: **0**.

The first ordered kill boundary was
`validation_zero_of_16_decoy_fp`. This is a substantive selectivity failure,
not a transport failure. Per preregistration, the package stops here without
threshold tuning, another seed, another mechanism, or Mate-in-2 execution.
