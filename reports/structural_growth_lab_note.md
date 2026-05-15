# Structural Growth Lab Note

The Structural Growth Lab is not the cognitive mechanism itself. It is the compiler, evaluator, and safety harness around candidate structural changes.

The cognitive mechanism begins when ReCoN-visible monitor SCRIPTs emit candidate hypotheses with source terms.

External tooling may:

- load diagnostic artifacts,
- serialize candidate proposals,
- compile sandbox topologies,
- run paired validations,
- run guardrails,
- promote, quarantine, reject, or archive candidates.

External tooling must not become a hidden runtime controller.

## Growth Monitor v0

Growth Monitor v0 is non-causal. It turns compact failure evidence into explicit `StructuralCandidate` records.

Initial monitor families:

```text
growth.monitor.reward_contract_mismatch
growth.monitor.successor_miscalibration
growth.monitor.stage_overlay_quarantine
```

These monitors do not mutate topology, alter routing, change M3 plasticity, or modify M4 consolidation.

They only emit records such as:

```text
StructuralCandidate
  schema_version = structural_candidate.v1
  causal_status = non_causal
  credit = 0.0
  promotion_status = proposed / quarantined / ...
```

## Stage 7 Test Case

Stage 7 `box_shrink` is the first Growth Monitor v0 test case.

Observed evidence:

```text
local improvement exists
conversion fails
reward_contract_mismatch appears
selected_successor_miscalibrated appears
repeated_conversion_failure appears
promotion gate quarantines the overlay
```

The monitor-generated candidates should point to possible repair domains:

```text
box_shrink_reward_contract_refinement
box_shrink_visible_box_contraction_terms
box_shrink_to_edge_trap_or_stage0_handoff_refinement
box_shrink_overlay_quarantine_confirmed
```

This replaces a purely manual workflow:

```text
human sees failure -> human invents patch
```

with a more ReCoN-shaped workflow:

```text
ReCoN-visible evidence -> candidate hypothesis -> external validation
```

## Safety Boundary

No gameplay-time topology mutation is allowed in this milestone.

`HandoffPacket`, `ShadowStemCandidate`, `SkillContractStats`, provider-promotion events, and `StructuralCandidate` records remain non-causal evidence.

Promotion is an explicit offline M5 action after sandbox validation and guardrail checks.

## Plasticity Balance

The lab now follows the Plasticity Balance Protocol:

```text
First try existing structure.
Then try bounded weight/plasticity calibration.
Only then propose or sandbox new topology.
```

Structural candidates carry Growth Governor metadata and topology-vs-weight diagnosis fields. This prevents treating every failed candidate as missing topology.

Reference:

```text
reports/plasticity_balance_protocol.md
```
