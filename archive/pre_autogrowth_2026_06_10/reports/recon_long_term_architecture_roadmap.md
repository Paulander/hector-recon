# ReCoN Long-Term Architecture Roadmap

Date: 2026-05-22

## Purpose

This roadmap resets the architecture direction after the progress-window reconsideration runtime test.

The runtime-test lifecycle worked:

```text
evidence -> review packet -> default-off sandbox -> target smoke -> quarantine
```

The tested policy did not work:

```text
sandbox.krk.progress_window_reconsideration_v0:
  status: runtime_test_scaffold_wired_but_policy_insufficient
  promotion_status: quarantined_or_analysis_only
```

The next bottleneck is candidate generation / proposal coverage / broader KRK strategy-sequence policy, not another local Stage 7 rule.

## A. Current Validated Stack

Validated or reusable stack elements:

- `handoff_composition_v1` is the stable experimental KRK handoff profile.
- Frozen-provider plus overlay composition is the validated preservation pattern.
- Stage 5 is protected enough to serve as a base fence/handoff component.
- Stage 6 is protected enough to serve as a `drive_to_edge` overlay component.
- Stage 1, Stage 5, and Stage 6 are clean protected/promoted components in the protected-stage audit.
- Stage 4 is mostly clean in the 500-sample profile, with a separate known h40 overlay-control caveat.
- KPK->KQK bridge behavior has been preserved through contract/handoff machinery.
- M1-M4 plasticity/consolidation preservation is part of the regression discipline.
- GrowthMonitor / StructuralCandidate / GrowthGovernor evidence flow is reusable.
- Default-off runtime sandbox lifecycle is validated as a process, even though the first progress-window policy was quarantined.

## B. Stage 7 Conclusion

Stage 7 status:

```text
local_valid_composition_quarantined
```

Architecture decision:

```text
box_shrink_reclassified_as_local_evidence_handoff_trigger
```

Meaning:

- `box_shrink` can remain useful local evidence.
- `box_shrink` should act as a handoff trigger or phase-boundary signal when appropriate.
- Stage 7 should not be promoted.
- Stage 8 should not be trained from unresolved Stage 7.
- Stage 7 residuals are held-out challenge cases, not the main optimization target.
- The progress-window reconsideration sandbox is quarantined as policy-insufficient.
- No further Stage 7 local micro-patch should be added without explicit architecture review.

## C. Reusable Mechanisms Learned

Reusable architecture mechanisms:

- `SkillContractSpec`
- `HandoffPacket`
- `ShadowStemCandidate`
- `StructuralCandidate`
- `GrowthGovernor`
- Provider preservation / overlays
- `PlanCapsuleSpec`
- `CandidateMoveFrame`
- `InternalTerminalSpec` candidates
- `StrategyMonitorRecord`
- Role-owned arbitration
- StrategyProposalFrame-style evidence
- Default-off sandbox review process
- Promotion/quarantine manifests
- Guardrail-aware validation
- Held-out challenge-set discipline

These mechanisms are not all causal. Many are evidence, trace, or review objects unless explicitly compiled/promoted into visible topology or exposed through visible SCRIPT/TERMINAL state.

## D. Main Unresolved Architectural Gaps

The main remaining gaps before independent KRK learning are:

- Provider candidate generation / proposal coverage.
- Strategy arbitration among providers with incomparable score scales.
- Sequence-policy learning for Plan Capsules.
- Internal-terminal maturity and cross-stage validation.
- Robust owner reconsideration after visible progress failure.
- Training objective / model-expression for multi-step plans.
- Curriculum-boundary detection: when a local skill should become evidence rather than owner.
- Clean separation of forced-provider capacity, ownership selection, safe preservation, and sequence-policy labels.
- Avoiding over-diagnosis loops by forcing decision gates.

The progress-window post-activation audit sharpened the immediate bottleneck:

```text
candidate_set_missing_good_alternative
visible_support_terms_overbroad
```

The system could reconsider, but the visible candidate set did not contain conversion-relevant alternatives.

## E. Recommended Next Technical Milestone

Recommended next milestone:

```text
KRK Strategy/Sequence Control Plane v1
```

This should not be Stage 7-specific. Stage 7 residuals should be held-out challenge cases.

KRK Strategy/Sequence Control Plane v1 should include:

- Candidate generation over validated providers.
- Strategy proposal frames for provider/move candidates.
- Plan/capsule proposal frames for multi-step options.
- Internal monitor records for local provider failure, plan stagnation, repair pressure, and owner-exit pressure.
- Sequence-policy benchmark for Plan Capsule continuation.
- Candidate-generation coverage benchmark.
- Strategy arbitration benchmark over protected Stage 4/5/6 plus held-out Stage 7 challenges.
- Guarded default-off sandboxes only after review-ready evidence.

The next implementation should first answer:

```text
What conversion-relevant candidates should have been visible when reconsideration fired?
```

## F. Milestone Ladder

1. **Stabilize KRK protected stack**
   Preserve Stage 1/4/5/6, `handoff_composition_v1`, KPK->KQK bridge, and M1-M4 semantics.

2. **Build KRK Strategy/Sequence Control Plane v1**
   Separate candidate generation, strategy arbitration, reconsideration, sequence policy, and internal monitoring.

3. **Validate full KRK conversion from random won KRK positions**
   Move beyond staged curriculum labels. Measure mate rate, stagnation, shadow candidates, guardrail preservation, and trace explainability.

4. **Re-run KPK->KQK bridge with the same machinery**
   Treat material transition as a domain handoff with visible eligibility and explicit continuation.

5. **Add KQK direct conversion and KPK conversion**
   Reuse provider preservation, candidate generation, plan capsules, internal monitors, and promotion/quarantine.

6. **Add tactics interrupt layer**
   Build visible forcing-move candidates and safety vetoes for mate-in-one, forks, pins, skewers, hanging pieces, discovered attacks, and avoiding mate/material loss.

7. **Build full-game chess prototype**
   Combine opening scaffold, tactics interrupt, material/endgame router, strategy/plan layer, endgame modules, and shallow proposal generators without making search a hidden controller.

8. **Extract generic ReCoN library**
   Separate domain-independent graph/plasticity/growth machinery from chess-specific terminals and actuators.

9. **Apply to non-chess simple world / Pacman-like domain**
   Use a visually inspectable domain with hunger, danger, home/shelter, short-term tactics, long-term planning, and internal monitor states.

## G. Runtime Sandbox Policy

Runtime is blocked by default, not absolutely forbidden.

Runtime sandboxes are allowed only when all conditions hold:

- A review packet exists.
- Explicit approval is given.
- The sandbox is default-off.
- The sandbox is reversible by disabling a flag.
- The sandbox is scoped to a specific monitor/candidate/profile.
- The sandbox is traceable with visible source terms.
- It does not use runtime DTM/tablebase.
- It does not mutate topology during gameplay.
- It is not a hidden Python controller.
- It runs default-off equivalence first.
- It runs targeted smoke before guardrails.
- It runs protected guardrails before promotion.
- It is quarantined fast if target behavior does not improve.

Status ladder:

```text
runtime_blocked
runtime_review_ready
sandbox_approved_default_off
sandbox_wired_no_improvement
sandbox_quarantined
sandbox_guardrail_candidate
promoted
```

Current progress-window sandbox:

```text
sandbox_wired_no_improvement
sandbox_quarantined
```

## H. Diagnostic Discipline

Diagnostics must force decisions.

Rules:

- No broad diagnostic branch without a decision gate.
- No more Stage 7 local micro-patches.
- Do not diagnose the diagnosis indefinitely.
- If evidence reaches review-ready status, either approve a narrow sandbox or explicitly reject it.
- If a sandbox does not improve its target, quarantine it quickly.
- Do not run guardrails for a sandbox that failed its target smoke.
- Do not tune support amounts blindly.
- Do not turn failure-correlated terms into action affordances without maturity validation.
- Do not collapse capacity labels into ownership labels.

Pivot rules:

- Pivot from diagnostics to sandbox only when evidence is review-ready and the sandbox is scoped, default-off, and reversible.
- Pivot from sandbox to quarantine when target smoke fails.
- Pivot from local stage work to control-plane work when failures expose candidate-generation, sequence-policy, or strategy-boundary gaps.
- Pivot from chess-specific work to generic ReCoN library only after the KRK control-plane lifecycle is demonstrated end-to-end.

## M1-M4 and M5 Structural Growth

M1-M4 remain the bounded plasticity/consolidation layers:

- M1: immediate local adaptation signals.
- M2: short-term contextual adjustment.
- M3: temporary candidate/provider adaptation when there is real eligible evidence.
- M4: slow consolidation only after stable repeated evidence.

M5 structural growth is separate:

- Evidence accumulates through monitors, traces, candidates, and failures.
- StructuralCandidate records remain non-causal until reviewed.
- GrowthGovernor decides whether a candidate is worth sandboxing.
- Default-off sandbox tests causal behavior.
- Guardrails decide promotion or quarantine.

M1-M4 should not mutate topology during gameplay. M5 promotion must remain offline/reviewed and guardrail-aware.

## Internal Terminals and Plan Capsules

Internal terminals are visible self-monitoring candidates, not hidden controllers.

Useful internal-terminal directions:

- local provider competition failure
- post-plan stagnation
- repair-needed monitor
- owner-exit pressure
- growth pressure
- phase-boundary ambiguity

Plan Capsules are bounded multi-step commitment candidates:

- visible entry terms
- visible progress terms
- visible exit terms
- visible abort terms
- bounded TTL
- explicit handoff

The long-term self-growing architecture should let internal monitors and Plan Capsules feed evidence into GrowthMonitor and future strategy/sequence learners, but not directly choose moves until reviewed, sandboxed, guardrailed, and promoted.

## What Coding Agents Should Avoid Next

Do not:

- Tune `sandbox.krk.progress_window_reconsideration_v0`.
- Run guardrails for that sandbox as if target smoke passed.
- Add another Stage 7 runtime patch.
- Promote Stage 7.
- Train Stage 8 from unresolved Stage 7.
- Add broad provider bonuses or penalties.
- Add broad `stage0_basin` suppression.
- Use runtime DTM/tablebase.
- Add hidden Python routing.
- Mutate topology during gameplay.
- Treat forced-provider capacity labels as ownership labels.
- Start another open-ended diagnostic branch without a decision gate.

Do:

- Treat Stage 7 as held-out challenge evidence.
- Work on candidate-generation / strategy-sequence proposal coverage.
- Keep candidate generation, selection, reconsideration, sequence policy, and internal monitoring separate.
- Use reviewed, default-off sandboxes only when evidence is review-ready and explicitly approved.
