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
- The offline training-objective benchmark did not justify a runtime sandbox: simple pairwise/ranked visible-term scoring underperformed the current learned scorer, visible log-odds/box heuristics improved top-1 only modestly while worsening hard-negative/draw behavior, and oracle ceilings remain high; current status is `ranking_calibration_gap`.
- The ranking calibration audit refined that to `term_collision_and_state_local_ranking_gap`: winning-nonoptimal hard negatives heavily outnumber positives and share broad visible progress/safety terms, so another runtime repair should wait for a state-local contrastive/interaction diagnosis or architecture review.
- The state-local contrast audit found positives are separable from hard negatives by single visible terms in most states and by term interactions in many others; current status is `state_local_single_terms_available`, with next step limited to non-causal visible-term refinement audit.
- The visible-term refinement audit found candidate positive terms, but several high-value terms are globally ambiguous and require companion/phase scope; current status is `visible_term_refinement_candidates_non_causal`, with no runtime patch justified.
- The scoped interaction benchmark was inconclusive: scoped models did not beat the visible-term baseline and increased hard-negative ranking relative to current/visible baselines. Current status is `scoped_interaction_benchmark_inconclusive`; pause Stage 7 runtime work or request architecture review.
- Stage 7 runtime repair is now paused pending an architecture-level decision. Stage 7 residuals should be treated as challenge cases for general KRK strategy arbitration / plan selection, not as the sole optimization target.

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

Stage 7-specific runtime implementation is paused. The current objective is to preserve the Stage 7 evidence as an architecture review and decide the next direction outside the local-repair loop.

The next architecture decision should choose among:

- a general KRK strategy-arbitration / plan-selection experiment,
- a stronger sequence-policy / Plan Capsule learner,
- a curriculum-boundary redesign where `box_shrink` becomes local evidence plus handoff trigger,
- or a broader KRK integration track that freezes Stage 7 as a known residual.

The recommended direction is to design a general KRK strategy-arbitration / plan-selection experiment and use Stage 7 residuals as held-out challenge cases. Do not implement a new Stage 7 runtime patch without a new explicit architecture decision.

The next architecture document is:

```text
reports/krk_strategy_arbitration_plan.md
reports/krk_strategy_arbitration_plan.json
```

That plan specifies the first future implementation slice as a non-causal KRK strategy arbitration dataset/probe v0. It does not authorize a runtime arbiter, Stage 7 repair, Stage 7 promotion, or Stage 8 training.

Phase 1 dataset status:

- `reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json`
- `reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.md`

Dataset v0 is replay-free and non-causal. It currently contains a small stratified set of Stage 7 challenge records plus Stage 5/6/4 validation records, with `33` records and `87` StrategyProposalFrame entries. It added no new h40 labels.

Probe v0 status:

- `reports/strategy_arbitration/krk_strategy_arbitration_probe_v0.json`
- `reports/strategy_arbitration/krk_strategy_arbitration_probe_v0.md`

Probe v0 selected `missing_feature_first`: raw/normalized provider scores hit existing labels often, but the simple visible heuristic failed badly. The next allowed step is non-causal terminal/affordance candidate proposal plus separability audit, not a runtime arbiter.

Stage 7 challenge set manifest:

- `reports/strategy_arbitration/stage7_challenge_set_manifest.json`
- `reports/strategy_arbitration/stage7_challenge_set_manifest.md`

The manifest defines six held-out challenge families for strategy arbitration: 0926-like candidate moves, 069-like drive/fence arbitration, 2cc-like post-box continuation, Plan Capsule owned residuals, reward/contract mismatch, and `stage0_basin` fallback failures.

Strategy arbitration decision gate:

- `reports/strategy_arbitration/krk_strategy_arbitration_decision_gate.json`
- `reports/strategy_arbitration/krk_strategy_arbitration_decision_gate.md`

The gate selected `missing_feature_first`. The next and final allowed slice before review is a non-causal terminal/affordance candidate audit and separability report. Runtime arbiter implementation remains blocked.

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

Current pause/review artifacts:

```text
reports/structural_candidates/stage7_pause_and_architecture_review.json
reports/structural_candidates/stage7_pause_and_architecture_review.md
reports/krk_strategy_arbitration_plan.json
reports/krk_strategy_arbitration_plan.md
reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json
reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.md
reports/strategy_arbitration/krk_strategy_arbitration_probe_v0.json
reports/strategy_arbitration/krk_strategy_arbitration_probe_v0.md
reports/strategy_arbitration/stage7_challenge_set_manifest.json
reports/strategy_arbitration/stage7_challenge_set_manifest.md
reports/strategy_arbitration/krk_strategy_arbitration_decision_gate.json
reports/strategy_arbitration/krk_strategy_arbitration_decision_gate.md
```

No runtime behavior should change while Stage 7 is paused.
