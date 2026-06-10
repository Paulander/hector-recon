# KRK Strategy Arbiter Sandbox Design v0

This is a non-causal design note. It does not implement a runtime arbiter, add runtime terminals, change defaults, promote Stage 7, train Stage 8, mutate topology, or use DTM/tablebase at runtime.

## Motivation

The corrected control-plane baseline now has provider-level labels for all `28` strategy benchmark frames. Fourteen frames contain at least one known provider-mate option, and fourteen contain only `max_plies` provider labels.

The baseline result is `strategy_arbitration_promising`: raw score, normalized score, provider-local rank, and stage-prior heuristics recover many converting providers when one is present. The simple visible-context heuristic remains weak, which means terminal-space context alone is not enough; a future arbiter must compare provider proposals, context terms, internal monitor records, and guardrail provenance together.

This is not Stage 7 repair work. Stage 7 remains `local_valid_composition_quarantined` and should stay a held-out challenge set.

## Proposed Future Sandbox

The future candidate, if explicitly approved later, would be:

```text
sandbox.krk.strategy_arbiter_v0
```

Properties:

- Default-off.
- KRK-domain scoped.
- Profile-scoped to an explicit sandbox.
- Traceable through visible proposal/context/monitor evidence.
- Unable to use DTM/tablebase at runtime.
- Unable to mutate topology during gameplay.
- Unable to directly request a provider through unsafe role-SCRIPT edges.

Inputs:

- `ControlPlaneEvidenceFrame.strategy_proposal_frames`
- Protected provider provenance
- Terminal-space context terms
- Internal monitor records
- Plan Capsule window records
- Promotion and guardrail status

Forbidden inputs:

- Runtime DTM/tablebase lookup
- State-hash exceptions
- Hidden Python router state
- Unpromoted `StructuralCandidate` as causal input
- Unpromoted `InternalTerminalSpec` as causal input

Candidate outputs:

- Non-causal provider ownership recommendation
- Sandbox-only visible arbitration support record
- Explanation of source terms and proposal metadata

Forbidden outputs:

- Direct move selection
- Direct provider request edge
- Topology mutation during gameplay
- Stage 7 promotion
- Stage 8 training trigger

## Minimum Before Implementation

- Architecture review explicitly authorizes a default-off sandbox implementation.
- Provider-label semantics are separated for selected-provider vs forced-provider labels.
- Positive-provider and max-only frames are separated in evaluation.
- Stage 7 challenge cases remain held out from sandbox tuning.
- Every recommendation can cite visible terms and proposal metadata.
- A default-off equivalence test plan exists before runtime code is added.
- Guardrails are listed before any candidate moves beyond sandbox.

## Future Evaluation Protocol

1. Phase 0: default-off equivalence against current runtime.
2. Phase 1: offline replay over `ControlPlaneEvidenceFrame` records.
3. Phase 2: tiny default-off/on sandbox smoke only if explicitly approved.
4. Phase 3: target KRK control-plane challenge validation.
5. Phase 4: protected Stage 6/5/4/1 guardrails only if target improves.
6. Phase 5: M1-M4 preservation suite before any promotion discussion.

## Guardrails

- Stage 6 `drive_to_edge`
- Stage 5 fence/handoff
- Stage 4 wrong-tempo with paired controls
- Stage 1 backchain / KRK entry if cheap
- M1-M4 preservation
- KPK->KQK bridge sanity if the arbiter generalizes beyond KRK

## Open Risks

- `provider_label_semantics_mixed`: some labels are selected-provider outcomes while others are forced-provider outcomes.
- `max_only_frames_need_classification`: half the current benchmark frames have no known converting provider proposal.
- `visible_context_heuristic_weak`: context-only ownership selection is insufficient.
- `stage7_overfit`: Stage 7 residuals must remain challenge cases, not the sole optimization target.

## Decision

Recommended next step:

```text
architecture_review_before_any_runtime_sandbox
```

Blocked next steps:

- Runtime arbiter implementation without review
- Runtime terminals
- Stage 7 promotion
- Stage 8 training
- Stage 7 repair
- Runtime DTM/tablebase
- Gameplay-time topology mutation
