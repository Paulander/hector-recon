# Stage 7 Pause And Architecture Review

This review is documentation-only and non-causal. It does not change runtime behavior, promote Stage 7, train Stage 8, use DTM/tablebase at runtime, or mutate topology during gameplay.

## Current Stage 7 Status

Stage 7 `box_shrink` remains:

```text
local_valid_composition_quarantined
```

- Stage 7 is not promoted.
- Stage 8 remains blocked.
- Runtime defaults are unchanged.
- Stage 7-specific runtime repair work is paused pending an architecture decision.

The latest scoped-interaction benchmark did not justify a new causal sandbox: it was inconclusive, did not beat the visible-term baseline, and worsened hard-negative ranking relative to current/visible baselines.

## Validated Mechanisms

- Growth Monitor / StructuralCandidate / GrowthGovernor path: Stage 7 failures can produce structured non-causal candidate evidence without becoming runtime control.
- Frozen-provider plus overlay discipline: later stages remain overlays and do not replace validated Stage 5/6 providers.
- Role-owned arbitration: useful as a diagnostic/sandbox pattern, but not justified as another Stage 7 causal change.
- CandidateMoveFrame layer: legal moves can be represented as ephemeral visible action hypotheses without persistent topology nodes.
- Plan Capsule marker / owned-window instrumentation: multi-ply plan entry, progress, exit, abort, and TTL became inspectable.
- Default-off sandbox discipline: experimental mechanisms stayed opt-in and traceable.
- Non-causal DTM / trajectory supervision boundary: DTM/tablebase evidence stayed offline and never became runtime policy.
- Guardrail-aware promotion/quarantine: Stage 7 remained quarantined despite local improvements.

## Rejected Or Insufficient Paths

- More local `box_shrink` move-shape tuning.
- Broad drive repair.
- Broad provider support adapters.
- Broad `stage0_basin` suppression.
- Direct role-to-provider SUB edges.
- M3 on scripted or non-trainable terminals.
- Current learned post-box overlay.
- Current Plan Capsule micro-tuning.
- Simple visible-term linear scorer.
- Simple pairwise/ranked scorer.
- Scoped interaction benchmark as currently implemented.
- Runtime DTM/tablebase.
- Training Stage 8 from this unresolved checkpoint.

## Evidence By Hypothesis

### Strategy Arbitration / Phase Boundary

Confidence: `medium`

Evidence for:

- Some Stage 7 families converted when existing providers were forced or arbitrated differently.
- Provider-score comparability and ownership repeatedly affected post-box behavior.
- Residuals look more like strategic phase-boundary cases than pure local move failures.

Evidence against:

- The first unified strategy arbitration probe was small and did not identify a better owner.
- Provider-local normalization and scoped interaction benchmarks did not justify causal arbitration.

Current read: still plausible at the architecture level, but not solved by the Stage 7-local arbitration variants tried so far.

### Continuation Capacity

Confidence: `medium`

Evidence for:

- The learnable post-box provider can own residual states but still max-plies.
- Some families were unresolved by existing forced providers within diagnostic horizons.
- Failures persisted after first-move visibility and ownership improvements.

Evidence against:

- Some failed families converted when existing providers were forced.
- DTM evidence shows theoretical wins within practical horizons, so the issue is not always absent chess capacity.

Current read: post-box continuation capacity remains plausible, but it is entangled with strategy ownership and sequence-policy quality.

### Missing Feature / Ontology

Confidence: `medium`

Evidence for:

- The 0926 CandidateMoveFrame role found exactly one converting move with visible terms.
- State-local contrast found positives separable from hard negatives by single terms or interactions in many states.
- Visible-term refinement identified useful candidates around king support, box progress, cut/fence, and rook geometry.

Evidence against:

- Simple visible-term scorers and scoped interaction benchmark did not cleanly solve ranking.
- Several high-value terms are globally ambiguous and need context rather than standalone causal use.

Current read: missing or under-scoped ontology is likely part of the problem, but current visible-term refinements are not sufficient as a runtime patch.

### Training Objective / Model Expression

Confidence: `high`

Evidence for:

- Learnable capsule ownership was achieved, but closed-loop conversion still failed.
- Expanded DTM-margin supervision improved top-1 only modestly and left hard-negative ranking unresolved.
- Simple pairwise/ranked and scoped interaction objectives failed to beat baseline cleanly.

Evidence against:

- Top-k signals and state-local separability show some useful representation exists.
- A broader strategy or curriculum-boundary issue could be causing the training objective to chase the wrong target.

Current read: the current ReCoN-visible representation and training objective are insufficient to learn the post-box continuation policy cleanly.

### Bad Standalone Curriculum Boundary

Confidence: `medium_high`

Evidence for:

- Stage 7 remains local-valid but composition-quarantined after many diagnostic paths.
- `box_shrink` near the edge appears noisy as an owner and may be better treated as local evidence or handoff trigger.
- Residuals increasingly point to strategy/plan selection rather than a standalone `box_shrink` actuator.

Evidence against:

- `box_shrink` local semantics are not useless and should remain available as evidence.
- A stronger strategy arbiter or sequence policy might make the existing boundary usable.

Current read: Stage 7 should not be promoted as an independent stage now; it may need reframing as a handoff signal inside a broader KRK strategy layer.

## Main Current Conclusion

The strongest conclusion is not:

```text
Stage 7 just needs another patch.
```

The stronger conclusion is:

```text
The current ReCoN-visible representation / training objective is insufficient
to learn the post-box continuation policy cleanly.
Stage 7 may be a noisy strategic boundary.
box_shrink may need to act as local evidence / handoff trigger rather than
a fully independent promoted stage.
```

## Architecture-Level Next Options

### A. Strategy Arbiter Track

Train/evaluate a domain-level KRK strategy arbiter over existing provider suggestions and terminal-space features.

Purpose: learn when `box_shrink` should yield to fence, edge-net, king-support, drive, or mate-basin strategies.

### B. Sequence Policy Track

Develop a stronger Plan Capsule sequence-policy learner.

Purpose: learn multi-step continuation from offline trajectories and closed-loop feedback, not one-ply ranking.

### C. Curriculum Boundary Track

Reclassify Stage 7 as an unstable boundary and redesign `box_shrink` as a handoff trigger rather than a promoted independent skill.

Purpose: preserve local box evidence while avoiding brittle stage ownership.

### D. Broader KRK Integration Track

Freeze Stage 7 as a known residual and train/evaluate a broader KRK continuation layer while preserving validated Stage 5/6.

Purpose: use Stage 7 residuals as regression cases for broader KRK plan learning.

## Recommended Next Architecture Direction

Pause Stage 7 repairs.

Do not train Stage 8 yet.

Design a general KRK strategy-arbitration / plan-selection experiment outside the Stage 7 local-repair loop. Use Stage 7 residuals as held-out challenge cases. Keep all new work non-causal until sandboxed and guardrail-validated.

Rationale:

- Stage 7 has become too narrow as an implementation target but valuable as a benchmark for strategy arbitration and plan learning.
- Continuing to patch Stage 7 risks overfitting the virtual lab.
- Moving up one architectural level is the cleaner path.

## Stop Conditions

- No runtime behavior changes.
- No Stage 7 promotion.
- No Stage 8 training.
- No hidden controller.
- No gameplay-time topology mutation.
- No runtime DTM/tablebase.
- Preserve M1-M4 plasticity/consolidation semantics.
- Keep validated Stage 5/6 providers protected/frozen unless an explicit sandbox says otherwise.
