# Current Agent Brief

This file is the current source-of-truth brief for future coding agents. It summarizes the active architecture constraints and the next diagnostic direction without replacing historical logs such as `reports/krk_handoff_counterfactual_notes.md`.

## Project Goal

Build ReCoN-lite as an inspectable, self-growing chess architecture where visible SCRIPT/TERMINAL structure, bounded plasticity, and offline structural promotion cooperate without hidden runtime controllers.

The near-term KRK goal is to preserve the validated handoff/composition stack while diagnosing why Stage 7 `box_shrink` remains locally useful but composition-quarantined.

## Current Validated Stack

- `handoff_composition_v1` is the stable experimental KRK handoff profile.
- Stage 5 fence/handoff machinery is validated enough to serve as protected base behavior.
- Stage 6 `drive_to_edge` is validated enough to serve as an overlay component when composed with frozen lower-stage providers.
- Stage 5/6 provider preservation uses frozen base providers plus later-stage overlays, not monolithic replacement topology.
- M1-M4 plasticity/consolidation semantics must remain intact.

## Stage 7 Status

Stage 7 `box_shrink` status:

```text
local_valid_composition_quarantined
```

Current interpretation:

- Local/one-ply behavior can be improved.
- Conversion remains unresolved.
- Stage 7 must not be promoted.
- Stage 8 must not be trained from unresolved Stage 7.
- The current task is diagnostic, not a runtime patch.
- The learnable post-box Plan Capsule can own residual states, but closed-loop h40 replay still fails; expanded offline DTM-margin supervision improved DTM-positive top-1 only modestly and left the diagnosis as a trajectory-ranking/model-expression gap.
- The latest arbitration probe established shared terminal-space provider comparison infrastructure but did not justify a causal arbitration change.
- The first unified arbitration sample was intentionally small and underpowered; its sampled residuals were high `box_area_relevance`, so low box relevance / near-edge phase boundary is not yet established as the explanation.

## Hard Invariants

- No hidden Python controller.
- No runtime DTM/tablebase policy.
- No gameplay-time topology mutation.
- `HandoffPacket`, `SkillContractStats`, `ShadowStemCandidate`, `StructuralCandidate`, `GrowthGovernor`, provider-promotion events, and `PlanCapsuleSpec` remain non-causal unless explicitly compiled/promoted into visible topology or exposed through visible SCRIPT/TERMINAL state.
- Any causal runtime influence must cite visible SCRIPT/TERMINAL state, explicit adapter evidence, edge/provider metadata, or promoted topology.
- Preserve M1-M4 plasticity/consolidation semantics.
- Validated providers stay protected/frozen unless a sandbox explicitly says otherwise.
- Later-stage skills should be overlays, not monolithic replacements.
- Runtime defaults must not change during diagnostics.

## Rejected Paths

Do not pursue these paths without a new explicit architecture decision:

- Train Stage 8 while Stage 7 remains unresolved.
- Promote Stage 7 from local success alone.
- Add another broad Stage 7 provider bonus, support adapter, or provider penalty.
- Add another local box-shrink move-shape patch as the main path.
- Keep tuning the current Plan Capsule or post-box continuation policy as a micro-repair.
- Use DTM/tablebase as a runtime selector.
- Add state-hash or exact-move runtime exceptions.
- Create a broad `full_krk` continuation overlay to hide Stage 7 uncertainty.

## Active Hypotheses

The next diagnostic should distinguish these hypotheses rather than optimize only one:

1. **Strategy arbitration / phase-boundary issue**: `box_shrink` or `stage0_basin` may own positions where edge-net, king-support, drive, or fence repair should own.
2. **Continuation-capacity issue**: existing providers may be unable to convert some post-box states even when selected.
3. **Missing-feature / ontology issue**: visible terms may not yet describe the relevant phase boundary, box relevance, edge-net pressure, or post-box state family.
4. **Training-objective / model-expression issue**: learned post-box providers may own the state but fail to rank DTM-positive or conversion-positive moves reliably.
5. **Bad standalone curriculum boundary**: Stage 7 `box_shrink` may not be a stable independent stage near the edge and may need reframing as part of a larger strategy family.

## Current Diagnostic Objective

Produce the replay-free Stage 7 evidence merge / stratified diagnostic table recommended by the neutral matrix, then emit a decision gate.

The evidence merge should answer:

- Does provider-local/role-owned arbitration identify better ownership than raw score?
- Do edge distance and `box_area_relevance` explain where `box_shrink` should not own?
- Do forced-provider or bounded playout probes show existing continuation capacity?
- Do trajectory fidelity audits show training-objective or representation failure?
- Do missing visible terms explain separable state families?
- Is `box_shrink` itself an unstable curriculum boundary?

The output should be non-causal diagnostic artifacts and a decision gate, not a runtime change.

## Performance Rules

- Keep Stage 7 diagnostic probes small unless a previous result justifies scaling.
- Prefer replay-free augmentation when existing artifacts already contain traces.
- Do not run exhaustive legal-first sweeps by default.
- Cap provider labels per state for arbitration datasets.
- Use trace-free labels by default; trace failures only when needed for inspection.
- Use diagnostic caches and early-stop stable suggestions where available.
- If a diagnostic projects to hours, stop and add filtering/cache/parallelization before continuing.

## Stop Conditions

Stop and ask for review if:

- default-off behavior changes,
- a diagnostic requires hidden runtime routing,
- DTM/tablebase starts affecting runtime policy,
- topology mutates during gameplay,
- protected Stage 5/6 behavior regresses,
- Stage 7 repair pressure starts replacing neutral diagnosis,
- the mechanism cannot cite visible source terms or explicit metadata,
- the diagnostic cannot distinguish the active hypotheses,
- the run becomes too slow for the intended slice.

## Expected Next Artifacts

Likely next artifacts:

```text
reports/structural_candidates/stage7_evidence_merge_table.json
reports/structural_candidates/stage7_evidence_merge_table.md
reports/structural_candidates/stage7_decision_gate.json
reports/structural_candidates/stage7_decision_gate.md
```

Possible supporting code:

```text
scripts/summarize_stage7_evidence_merge_table.py
tests/test_stage7_unresolved_summary.py
```

No runtime behavior should change for the next diagnostic slice.
