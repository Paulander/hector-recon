# Touched R0 Competence-Envelope Engineering Result

Date: 2026-07-16. Status: canonical package closed at admission. This is an
instrument abort, not a competence-envelope result, KRK gain, or fresh claim.

## Verdict

The package stopped before learning at the preregistered
`evidence_admission` boundary. Source, pool, event-tape, and permutation hashes
matched. All 64 real executions had unique evidence keys; all 16 gate-train
decoys were response-present noncompletions; fabricated reward and all three
legacy-authority tripwires were zero.

The added `positive_completion_48_of_48` gate failed. The compact frozen source
artifact independently records 46 positive prototype outcomes. Those labels are
constructed by `_gate_example` from actual immediate completion of the frozen
R0 policy over the same 48 R0-train plus 16 train-decoy contexts. Since the
canonical admission observed all 16 decoys fail, frozen R0 completed 46/48
historical R0-train contexts and failed two.

The actual admission stream was therefore 46 successes and 18 response-present
local failures. It was nondegenerate and satisfied the external authorization's
stated requirements: both outcome classes and at least 12 response-present
training failures.

## Design error and binding stop

The external work package did not require every historically named R0-train
context to remain a current policy success. I incorrectly promoted the scheduling
category "R0 train" into an expected 48/48 outcome gate while amending the
preregistration. That was stricter than the authorization and conflated pool
provenance with observed competence.

Because commits `6e55baa`, `c8ce114`, and `4ef6916` froze that extra gate
before execution, the canonical process stopped correctly under its own rules.
It must not be repaired or rerun inside this package.

## What was not tested

- zero competence-context proposals were materialized;
- AVAILABLE, REFUTED, UNKNOWN, and AVAILABILITY_ERROR learning were not exercised
  on the canonical data;
- no validation row was used;
- regression remained untouched;
- all 65 retired successors remained untouched;
- no competence organism snapshot was produced;
- no R1 learning occurred.

This result supplies no evidence for or against growth authority, topology
growth, lifecycle, selectivity, abstention, retired generalization, stability, or
the controls.

## Canonical evidence

Artifact:
`reports/autogrowth/native_authority/touched_r0_competence_envelope_engineering.json`.

Artifact SHA-256:
`6db9935fa2d2eff5aec8d8e92e07d41eabcfb41ba2df794288fca602cecfb051`.

Focused validation: 37 passed in 6.21 seconds. Full repository validation:
896 passed in 2,312.32 seconds.

Runtime: 428.38 seconds. Canonical boundary: `evidence_admission`.
Fresh data: none. Final-pool touches: zero. R1 updates: zero.

The exact 46/48 count is an artifact-only inference from the frozen source
artifact's `r0.consolidation.gate.positive_prototype_count` plus the canonical
16/16 decoy failures. The early-stop artifact persisted the gate boolean but not
the positive count; that instrumentation omission is recorded and not repaired
post hoc.

## External decision required

A future package may correct admission to use observed outcomes only:

- both completion and noncompletion must be present;
- at least 12 policy-response noncompletions must be present;
- historical pool names must not assert current competence;
- the exact observed class counts must be persisted before the gate decision.

That correction requires a new authorization and preregistration. It does not
authorize changing the frozen estimator, thresholds, capacity, structural
rounds, member-choice genome, controls, or R0 policy, and it does not authorize
fresh data or R1 learning.
