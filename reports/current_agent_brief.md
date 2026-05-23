# Current Agent Brief

This file is the current source-of-truth brief for future coding agents. It summarizes the active architecture constraints, validated stack, rejected paths, runtime-sandbox policy, and current direction. It does not replace historical logs such as `reports/krk_handoff_counterfactual_notes.md`.

## Project Goal

Build ReCoN-lite / Hector as an inspectable, self-growing chess architecture where visible SCRIPT/TERMINAL structure, bounded plasticity, offline structural promotion, plan capsules, and internal monitors cooperate without hidden runtime controllers.

KRK is the controlled proving ground. The deeper goal is a scalable ReCoN architecture that can later compose KRK, KQK, KPK, tactics, full-game chess, and eventually non-chess domains.

Long-term roadmap:

```text
reports/recon_long_term_architecture_roadmap.md
reports/recon_long_term_architecture_roadmap.json
```

That roadmap is the current architecture reset after the quarantined progress-window runtime test.

## Current Validated Stack

- `handoff_composition_v1` is the stable experimental KRK handoff profile.
- Stage 5 fence/handoff machinery is validated enough to serve as protected base behavior.
- Stage 6 `drive_to_edge` is validated enough to serve as an overlay component when composed with frozen lower-stage providers.
- Stage 5/6 provider preservation uses frozen base providers plus later-stage overlays, not monolithic replacement topology.
- Stage 1, Stage 5, and Stage 6 are clean protected/promoted components according to the protected-stage audit.
- Stage 4 is mostly clean in the 500-sample `handoff_composition_v1` profile, but carries a separate h40 overlay-control caveat that reproduces on the frozen Stage 5 base and is not Stage 6 interference.
- KPK→KQK bridge behavior has been preserved through the contract/handoff machinery.
- M1-M4 plasticity/consolidation semantics must remain intact.

## Stage 7 Status

Stage 7 `box_shrink` status:

```text
local_valid_composition_quarantined
```

Architecture decision:

```text
box_shrink_reclassified_as_local_evidence_handoff_trigger
```

Current interpretation:

* Local/one-ply `box_shrink` behavior can be improved, but conversion remains unresolved.
* Stage 7 must not be promoted.
* Stage 8 must not be trained from unresolved Stage 7.
* Stage 7 is no longer a standalone repair target.
* `box_shrink` is retained as local evidence, handoff trigger, and phase-boundary signal.
* Stage 7 residuals are held-out challenge cases for broader KRK strategy/sequence work.
* Further Stage 7 micro-repair work is blocked unless explicitly re-authorized by architecture review.

Rejected Stage 7-local paths include:

* more local box-shrink move-shape tuning,
* broad drive repair,
* broad support adapters,
* broad provider penalties,
* broad `stage0_basin` suppression,
* unsafe direct role-SCRIPT → provider SUB edges,
* M3 on non-trainable scripted terminals,
* runtime DTM/tablebase,
* exact state-hash or exact-move runtime exceptions,
* treating Stage 7 local success as promotable conversion skill.

## Major Architectural Lessons From Stage 7

Stage 7 exposed general architecture problems rather than merely a bad local skill:

1. **Local skill success is not enough.**
   A local box-shrink move can improve local reward while failing conversion.

2. **Provider ownership is not enough.**
   A provider or Plan Capsule can own the decision and still fail closed-loop continuation.

3. **Score scales are not naturally comparable.**
   Raw provider scores can favor the wrong provider even when another provider converts when forced.

4. **Candidate generation and selection must be separated.**
   A selector cannot choose a converting provider if the candidate set does not contain one.

5. **Forced-provider capacity labels are not runtime ownership labels.**
   A provider converting under forced ownership means it has capacity, not that it should always own similar states.

6. **Plan Capsules require sequence-policy learning.**
   Entry/progress/exit markers can be meaningful while the learned continuation policy remains weak.

7. **Internal monitors are useful but immature.**
   Terms such as `local_provider_competition_failed` and `post_plan_stagnation` are promising, but still sparse and not causal-ready.

8. **Runtime sandboxes are valuable when reviewed and bounded.**
   The progress-window reconsideration sandbox proved the default-off runtime-test lifecycle works, even though that specific policy did not improve target play.

## Hard Invariants

* No hidden Python controller.
* No runtime DTM/tablebase policy.
* No gameplay-time topology mutation.
* Runtime defaults must not change during diagnostics or runtime-test sandboxes.
* `HandoffPacket`, `SkillContractStats`, `ShadowStemCandidate`, `StructuralCandidate`, `GrowthGovernor`, provider-promotion events, `PlanCapsuleSpec`, and `InternalTerminalSpec` remain non-causal unless explicitly compiled/promoted into visible topology or exposed through visible SCRIPT/TERMINAL state.
* Any causal runtime influence must cite visible SCRIPT/TERMINAL state, explicit adapter evidence, edge/provider metadata, or promoted topology.
* Preserve M1-M4 plasticity/consolidation semantics.
* Validated providers stay protected/frozen unless a sandbox explicitly says otherwise.
* Later-stage skills should be overlays, not monolithic replacements.

## Runtime Sandbox Policy

Runtime behavior is blocked by default, but reviewed runtime sandboxes are allowed when explicitly approved.

A runtime sandbox must be:

* default-off,
* opt-in by explicit flag,
* scoped to a specific monitor/candidate/profile,
* reversible by disabling the flag,
* traceable with visible source terms,
* non-default for all normal runs,
* evaluated first by default-off equivalence,
* evaluated next on a targeted smoke,
* promoted only after protected guardrails pass.

A runtime sandbox must not:

* use DTM/tablebase at runtime,
* use state-hash or exact-move exceptions,
* act as a hidden Python controller,
* mutate topology during gameplay,
* become default without promotion,
* route providers without visible SCRIPT/TERMINAL or explicit adapter evidence.

Runtime sandbox status values:

```text
runtime_blocked
runtime_review_ready
sandbox_approved_default_off
sandbox_wired_no_improvement
sandbox_quarantined
sandbox_guardrail_candidate
promoted
```

Status meanings:

* `runtime_blocked`: no runtime behavior may be implemented; continue evidence/design only.
* `runtime_review_ready`: evidence packet exists, but implementation still requires explicit approval.
* `sandbox_approved_default_off`: explicit approval granted for a scoped, default-off, reversible sandbox.
* `sandbox_wired_no_improvement`: sandbox is wired and default-off safe, but target behavior did not improve.
* `sandbox_quarantined`: sandbox must not be tuned, scaled, guardrailed, promoted, or enabled by default.
* `sandbox_guardrail_candidate`: target smoke improved and protected guardrails may be run.
* `promoted`: sandbox passed target validation and guardrails and was explicitly promoted.

Current progress-window reconsideration sandbox status:

```text
sandbox_wired_no_improvement
sandbox_quarantined
runtime_test_scaffold_wired_but_policy_insufficient
```

Meaning:

* The sandbox was wired, traceable, reversible, and default-off equivalent.
* It activated on the intended progress-window failure row.
* It did not improve the h40 target outcome.
* Post-activation audit classified the failure as `candidate_set_missing_good_alternative` with companion label `visible_support_terms_overbroad`.
* Do not tune, scale, guardrail, promote, or enable this sandbox.
* The next direction is candidate-generation / broader KRK strategy-sequence review, not support tuning.

## Current Control-Plane Direction

The current objective is no longer Stage 7 repair.

Current objective:

```text
candidate-generation / broader KRK strategy-sequence review
```

Immediate status:

```text
sandbox.krk.progress_window_reconsideration_v0:
  status: runtime_test_scaffold_wired_but_policy_insufficient
  promotion_status: quarantined_or_analysis_only
  next_action: candidate_generation_or_broader_strategy_sequence_review
```

Do not scale it, guardrail it, tune it, promote it, or enable it by default.

Stage 7 residuals are held-out challenge cases.

The control-plane work should separate:

1. **Candidate generation**
   Which providers, plans, or candidate moves should be considered?

2. **Strategy selection / arbitration**
   Which candidate should own this decision in this terminal-space context?

3. **Reconsideration**
   Should the current owner be reconsidered after a visible progress-window failure?

4. **Sequence policy**
   Can a Plan Capsule execute a multi-step continuation and hand off correctly?

5. **Internal monitoring**
   Can the system detect provider competition failure, plan stagnation, repair pressure, owner-exit pressure, and growth pressure?

## Current Known Artifacts And Status

### KRK Strategy Arbitration

* `reports/krk_strategy_arbitration_plan.md/json`
* `reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.md/json`
* `reports/strategy_arbitration/krk_strategy_arbitration_probe_v0.md/json`
* `reports/strategy_arbitration/krk_strategy_arbitration_decision_gate.md/json`

Current status:

```text
missing_feature_first
```

Meaning:

* Existing raw/normalized provider scores can recover some labels.
* Simple visible heuristics are not enough.
* The next direction is not a runtime arbiter; it is improving candidate/feature/monitor evidence.

### Strategy Monitor / Internal Terminal Work

Important artifacts:

* `reports/strategy_arbitration/krk_strategy_monitor_records_v0.md/json`
* `reports/strategy_arbitration/krk_strategy_monitor_companion_terms_v0.md/json`
* `reports/strategy_arbitration/krk_visible_monitor_terms_v0.md/json`
* `reports/strategy_arbitration/krk_internal_terminal_candidates_v0.md/json`
* `reports/strategy_arbitration/krk_internal_terminal_validation_v0.md/json`
* `reports/strategy_arbitration/krk_internal_terminal_evidence_v1.md/json`
* `reports/strategy_arbitration/krk_internal_terminal_design_review_v1.md/json`

Current status:

* `terminal.krk.local_provider_competition_failed` is promising but sparse and Stage7-only.
* `terminal.krk.post_plan_stagnation` is promising but sparse and Stage7-only.
* `terminal.krk.repair_needed_monitor` is broader but noisy.
* `terminal.krk.box_shrink_owner_exit_pressure` needs companion handoff-target evidence.
* No internal terminal is causal-ready.

### Candidate Generation / Selector Separation

Important artifacts include:

* `krk_candidate_generator_coverage_audit_v0`
* `krk_validated_provider_candidate_set_audit_v0`
* `krk_two_stage_candidate_selection_review_v0`
* `krk_two_stage_candidate_selection_benchmark_v0`
* `krk_selector_directed_fix_review_v0`
* hard-negative selector datasets and reviews
* split selector objective datasets/reviews
* ownership selection label datasets/reviews
* state-local paired ownership inventory/probes/reviews
* `reports/strategy_arbitration/krk_candidate_proposal_coverage_v0.md/json`
* `reports/strategy_arbitration/krk_candidate_generation_strategy_review_v0.md/json`
* `reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_v1.md/json`
* `reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.md/json`
* `reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_quality_v1.md/json`
* `reports/strategy_arbitration/krk_candidate_frame_source_benchmark_v1.md/json`
* `reports/strategy_arbitration/krk_strategy_sequence_control_plane_decision_v1.md/json`
* `reports/strategy_arbitration/krk_candidate_generation_sandbox_review_v0.md/json`
* `reports/strategy_arbitration/krk_candidate_generation_observation_sandbox_v0.md/json`
* `reports/strategy_arbitration/krk_candidate_generation_observation_coverage_analysis_v0.md/json`
* `reports/strategy_arbitration/krk_candidate_generation_observation_broadened_sample_v1.md/json`
* `reports/strategy_arbitration/krk_candidate_generation_observation_gap_review_v1.md/json`
* `reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v1.md/json`
* `reports/strategy_arbitration/krk_candidate_move_capacity_label_manifest_v1.md/json`
* `reports/strategy_arbitration/krk_candidate_move_capacity_labels_v1.md/json`
* `reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v2.md/json`
* `reports/strategy_arbitration/krk_candidate_generation_label_blocker_review_v1.md/json`
* `reports/strategy_arbitration/krk_candidate_proposal_quality_prioritization_review_v1.md/json`
* `reports/strategy_arbitration/krk_candidate_proposal_quality_dataset_v1.md/json`
* `reports/strategy_arbitration/krk_candidate_proposal_quality_probe_v1.md/json`
* `reports/strategy_arbitration/krk_candidate_proposal_quality_decision_v1.md/json`
* `reports/strategy_arbitration/krk_broader_strategy_sequence_candidate_source_design_v1.md/json`
* `reports/strategy_arbitration/krk_plan_capsule_sequence_candidate_observation_review_v1.md/json`
* `reports/strategy_arbitration/krk_broader_strategy_candidate_observation_review_v1.md/json`
* `reports/strategy_arbitration/krk_broader_strategy_sequence_candidate_source_review_v1.md/json`
* `reports/strategy_arbitration/krk_protected_strategy_monitor_frame_expansion_v1.md/json`
* `reports/strategy_arbitration/krk_protected_strategy_monitor_frame_quality_v1.md/json`
* `reports/strategy_arbitration/krk_protected_strategy_monitor_observation_source_review_packet_v1.md/json`

Current conclusion:

```text
candidate generation and strategy selection must remain separate evidence tracks
```

Forced-provider capacity labels are useful for candidate-generation coverage, not direct runtime selection.

Current candidate-generation review result:

```text
strategy_sequence_control_plane_v1_needed
```

The current protected replay-free proposal frames have `0.0` positive-capacity recall for the checked validated-provider alternatives: 11 protected positive-capacity alternatives are missing from visible proposal coverage, across Stage 4/5/6 and with 0 Stage 7 readiness rows. The validated-provider candidate pack would recover positive capacity, but it also includes negative capacity cases, so it is candidate-generation evidence only and must not become a direct selector label.

`StrategySequenceCandidateFrame v1` is now defined as a non-causal evidence-frame schema to separate validated-provider candidates, CandidateMoveFrame hypotheses, PlanCapsule sequence candidates, and broader KRK strategy candidates. The next safe slice is replay-free population of those frames, not runtime selection.

Replay-free StrategySequenceCandidateFrame v1 population is complete:

```text
strategy_sequence_frames_populated_non_causal
frame_quality_probe_supports_next_sequence_candidate_benchmark
```

The population has 256 non-causal frames across validated-provider candidates, candidate-move hypotheses, and broader strategy-monitor candidates. Stage 7 contributes held-out challenge frames only: `stage7_readiness_training_row_count = 0`. The quality probe keeps capacity labels separate from selector labels and reports no runtime behavior/default/topology changes.

Next safe non-causal slice:

```text
benchmark_candidate_frame_sources_before_runtime
```

Candidate-frame source benchmarking is complete:

```text
candidate_generation_sources_promising_selector_blocked
candidate_generation_control_plane_ready_for_architecture_review
```

Evidence: there are 11 protected positive-capacity candidates available for candidate generation, but protected forced-capacity sources also carry a `0.3125` negative-capacity ratio, so source expansion alone is not a selector. Progress-window supported move candidates still have 0 h40 mate outcomes in the held-out Stage 7 runtime-test target. Stage 7 readiness/training rows remain 0.

Candidate-generation sandbox scope review is complete:

```text
candidate_generation_observation_sandbox_review_ready
```

The review packet recommends only a default-off observation-only candidate-generation sandbox as the first possible runtime experiment, and it explicitly does not authorize implementation by itself. It forbids selection, score changes, suppression, direct provider routing, Stage 7 promotion, Stage 8 training, runtime DTM/tablebase, gameplay topology mutation, and hidden routing.

The default-off observation-only candidate-generation sandbox has now been explicitly approved, wired, and smoke-tested:

```text
observation_sandbox_ready_for_non_causal_coverage_analysis
```

The sandbox emits candidate/proposal frames only when `--enable-krk-candidate-generation-observability` is set. It records `direct_request = false`, `score_delta = 0.0`, `causal_status = observation_only`, candidate source, capacity evidence kind, and protected/held-out status. The smoke generated 93 candidate frames across protected Stage 5/6 and held-out Stage 7 cases with no selected move/provider delta and no h8 playout result/ply delta. It is not a selector and does not authorize guardrails or promotion.

Observation-frame coverage analysis confirms:

```text
observation_frames_usable_for_non_causal_coverage_analysis
```

The emitted frames include both `validated_provider_pack` and `candidate_move_frame` sources, expose positive/negative/unknown/held-out capacity classes, and have zero invariant failures. Selector work and guardrails remain blocked; the next safe step is to broaden the observation sample before any selector review.

Broadened observation-only sampling is complete:

```text
broadened_observation_sample_supports_coverage_analysis
observation_gap_review_blocks_selector_recommends_capacity_annotation
```

The broadened sample covers 19 Stage 4/5/6 protected plus Stage 7 held-out cases and emits 569 observation-only frames with zero invariant failures, zero default-off observation leakage, and zero selected move/provider deltas. The gap review keeps selector work blocked because most emitted frames still have unknown capacity evidence, negative-capacity provider-pack candidates are present, and runtime observation does not yet expose PlanCapsule sequence candidates or broader strategy candidates. The next safe step is non-causal candidate-frame capacity/quality annotation review, not selector implementation or guardrails.

Replay-free CandidateMoveFrame capacity annotation is complete:

```text
candidate_move_capacity_annotation_partial_selector_blocked
```

Existing protected forced-capacity evidence can annotate 10 of 292 protected observed CandidateMoveFrame hypotheses. This confirms a viable annotation path, but coverage is too sparse for selector review. Capacity labels remain offline evidence only and are not ownership labels. The next safe step, if continued, is a bounded protected-only candidate-move capacity label manifest, not runtime selection.

Bounded candidate-move capacity label manifest is complete:

```text
bounded_candidate_move_capacity_manifest_ready
```

The manifest proposes 12 protected-only offline jobs balanced across Stage 4/5/6, with 0 Stage 7 jobs and no labels run by the manifest artifact itself. Each job is explicitly `forced_first_move_capacity_not_runtime_ownership_label`; it must not become selector training or runtime input without a later review.

Bounded candidate-move capacity labels were run offline:

```text
bounded_candidate_move_capacity_labels_completed
candidate_move_capacity_annotation_improved_but_selector_blocked
candidate_generation_label_coverage_underpowered_selector_blocked
```

The 12 protected labels produced 11 mate and 1 max_plies outcomes with 0 Stage 7 labels. Merging them improved protected CandidateMoveFrame annotation from 10 to 22 rows, but protected annotation recall remains only 0.075. The blocker review recommends candidate proposal quality/prioritization review before any further labels or selector review; more blind label farming is not recommended.

Candidate proposal quality/prioritization review is complete:

```text
proposal_quality_prioritization_review_ready
```

The review reframes the next control-plane step away from more unprioritized labels. The candidate generator is visible but too broad and underannotated; the next useful non-causal artifact is a candidate proposal quality dataset/probe that separates source channel, visible term density, safety floor, known capacity contrast, selected-move relation, and protection scope before any selector review.

Candidate proposal quality dataset/probe/decision are complete:

```text
candidate_proposal_quality_not_selector_ready
```

The dataset has 569 observation rows and 38 known protected capacity rows. The best simple quality axis (`candidate_move_frame_source`) reaches positive recall 0.633 and negative suppression 0.625, below selector-review thresholds. This closes the current candidate-quality slice: selector work remains blocked, more blind labels are blocked, and the next architecture direction is broader strategy/sequence candidate sources rather than tuning a selector.

Broader strategy/sequence candidate source design is complete:

```text
broader_strategy_sequence_candidate_source_design_ready
```

This design defines observation-only contracts for `plan_capsule_sequence_candidate` and `broader_strategy_candidate` sources. It does not authorize implementation. Any runtime source expansion requires a separate review because the current observation sandbox only proved provider-pack and CandidateMoveFrame visibility.

PlanCapsule and broader-strategy observation source reviews are complete:

```text
source_reviews_complete_runtime_expansion_not_authorized
```

Both source contracts are schema-ready, but current evidence is Stage7-only or Stage7-dominated. PlanCapsule source evidence comes from the quarantined Stage 7 post-box capsule path; broader-strategy source evidence exists as 13 monitor-derived frames, all Stage 7 challenge rows. Runtime source expansion remains blocked. The next safe non-causal step is protected cross-stage strategy-monitor frame expansion.

Protected cross-stage strategy-monitor frame expansion is complete:

```text
protected_repair_monitor_observation_source_review_ready
```

Replay-free expansion produced 85 protected Stage 4/5/6 broader-strategy monitor frames with 0 Stage 7 rows. The quality probe found `terminal.krk.repair_needed_monitor` has failure precision 0.769 across 13 protected frames, while owner-exit and phase-boundary monitor families are ambiguous. A review packet exists for a future default-off observation-only repair-monitor source, but it explicitly does not authorize implementation. Runtime source expansion now requires explicit approval.

The default-off repair-monitor observation source was then explicitly approved and wired:

```text
repair_monitor_observation_source_wired_default_off_equivalent
repair_monitor_observation_source_coverage_ready_for_guarded_analysis
repair_monitor_observation_source_broadened_default_off_equivalent
```

Artifacts:

* `reports/strategy_arbitration/krk_repair_monitor_observation_source_smoke_v1.md/json`
* `reports/strategy_arbitration/krk_repair_monitor_observation_source_coverage_v1.md/json`
* `reports/strategy_arbitration/krk_repair_monitor_observation_source_broadened_v1.md/json`

The source emits `broader_strategy_candidate` frames for `terminal.krk.repair_needed_monitor` in protected Stage 4/5/6 contexts only. The smoke covered 3 protected cases, emitted 3 repair-monitor frames, and produced 0 selected move/provider deltas, 0 baseline frame leaks, 0 invariant failures, and 0 Stage 7 cases. This is observation-only: `direct_request=false`, `score_delta=0.0`, no selector, no routing, no guardrails, no Stage 7 training/readiness rows, no Stage 8.

The broadened protected sample covered 6 protected cases, emitted 6 repair-monitor frames, and again produced 0 selected move/provider deltas, 0 baseline frame leaks, 0 invariant failures, and 0 Stage 7 cases. Selected providers in that sample were `krk.stage0_basin`, `krk.edge_trap_close`, and `krk.fence_established`.

Next safe step:

```text
repair_monitor_observation_source_non_causal_quality_review
```

Do not implement selector behavior, run guardrails, tune scores, route providers, promote Stage 7, or train Stage 8 from this source.

### Progress-Window Reconsideration Runtime Test

Artifacts:

* `reports/krk_runtime_sandbox_policy_update_v0.md/json`
* `reports/krk_progress_window_reconsideration_runtime_smoke_v0.md/json`
* `reports/krk_progress_window_reconsideration_runtime_test_review_v0.md/json`
* `reports/krk_progress_window_reconsideration_post_activation_audit_v0.md/json`

Current status:

```text
runtime_test_scaffold_wired_but_policy_insufficient
quarantined_or_analysis_only
```

Do not continue tuning this sandbox.

The key lesson is:

```text
the system can reconsider, but the visible candidate set did not contain conversion-relevant alternatives
```

So the next bottleneck is candidate-generation / broader strategy-sequence proposal coverage.

## Rejected Paths

Do not pursue these paths without a new explicit architecture decision:

* Train Stage 8 while Stage 7 remains unresolved.
* Promote Stage 7 from local success alone.
* Add another broad Stage 7 provider bonus, support adapter, or provider penalty.
* Add another local box-shrink move-shape patch as the main path.
* Keep tuning the current Plan Capsule or post-box continuation policy as a micro-repair.
* Continue tuning the current progress-window reconsideration sandbox.
* Treat the progress-window sandbox as a general selector.
* Run guardrails for a sandbox that did not improve the target.
* Use DTM/tablebase as a runtime selector.
* Add state-hash or exact-move runtime exceptions.
* Create a broad `full_krk` continuation overlay to hide Stage 7 uncertainty.
* Train a selector directly from forced-provider capacity labels.
* Treat candidate generation and strategy selection as the same problem.
* Promote any internal terminal to causal use from current evidence.

## Active Hypotheses

Future diagnostics should distinguish these hypotheses rather than optimize only one:

1. **Strategy arbitration / phase-boundary issue**
   `box_shrink` or `stage0_basin` may own positions where edge-net, king-support, drive, or fence repair should own.

2. **Continuation-capacity issue**
   Existing providers may be unable to convert some post-box states even when selected.

3. **Missing-feature / ontology issue**
   Visible terms may not yet describe phase boundaries, box relevance, edge-net pressure, king-support pressure, owner-exit pressure, or post-box state families.

4. **Training-objective / model-expression issue**
   Learned post-box providers may own the state but fail to rank DTM-positive or conversion-positive moves reliably.

5. **Bad standalone curriculum boundary**
   Stage 7 `box_shrink` may not be a stable independent stage near the edge and may need reframing as part of a larger strategy family.

6. **Candidate-generation gap**
   The selector/reconsideration machinery may work, but the candidate set may not include conversion-relevant alternatives.

## Current Recommended Direction

Do **not** continue Stage 7-specific repair.

Do **not** continue progress-window reconsideration tuning.

Recommended direction:

```text
KRK candidate-generation / strategy-sequence control plane
```

The next architecture work should focus on:

* what candidate alternatives the system can generate,
* which providers/plans are visible in each state,
* whether conversion-relevant alternatives are missing,
* how candidate generation should use validated providers, candidate-move frames, plan capsules, and internal monitors,
* how selector training should remain separate from capacity labels,
* how Stage 7 residuals should remain held-out challenge cases.

A suitable next artifact has been produced:

```text
reports/strategy_arbitration/krk_candidate_proposal_coverage_v0.md
reports/strategy_arbitration/krk_candidate_proposal_coverage_v0.json
reports/strategy_arbitration/krk_candidate_generation_strategy_review_v0.md
reports/strategy_arbitration/krk_candidate_generation_strategy_review_v0.json
reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_v1.md
reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_v1.json
reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.md
reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.json
reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_quality_v1.md
reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_quality_v1.json
reports/strategy_arbitration/krk_candidate_frame_source_benchmark_v1.md
reports/strategy_arbitration/krk_candidate_frame_source_benchmark_v1.json
reports/strategy_arbitration/krk_strategy_sequence_control_plane_decision_v1.md
reports/strategy_arbitration/krk_strategy_sequence_control_plane_decision_v1.json
reports/strategy_arbitration/krk_candidate_generation_sandbox_review_v0.md
reports/strategy_arbitration/krk_candidate_generation_sandbox_review_v0.json
reports/strategy_arbitration/krk_candidate_generation_observation_sandbox_v0.md
reports/strategy_arbitration/krk_candidate_generation_observation_sandbox_v0.json
reports/strategy_arbitration/krk_candidate_generation_observation_coverage_analysis_v0.md
reports/strategy_arbitration/krk_candidate_generation_observation_coverage_analysis_v0.json
reports/strategy_arbitration/krk_candidate_generation_observation_broadened_sample_v1.md
reports/strategy_arbitration/krk_candidate_generation_observation_broadened_sample_v1.json
reports/strategy_arbitration/krk_candidate_generation_observation_gap_review_v1.md
reports/strategy_arbitration/krk_candidate_generation_observation_gap_review_v1.json
reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v1.md
reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v1.json
reports/strategy_arbitration/krk_candidate_move_capacity_label_manifest_v1.md
reports/strategy_arbitration/krk_candidate_move_capacity_label_manifest_v1.json
reports/strategy_arbitration/krk_candidate_move_capacity_labels_v1.md
reports/strategy_arbitration/krk_candidate_move_capacity_labels_v1.json
reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v2.md
reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v2.json
reports/strategy_arbitration/krk_candidate_generation_label_blocker_review_v1.md
reports/strategy_arbitration/krk_candidate_generation_label_blocker_review_v1.json
reports/strategy_arbitration/krk_candidate_proposal_quality_prioritization_review_v1.md
reports/strategy_arbitration/krk_candidate_proposal_quality_prioritization_review_v1.json
reports/strategy_arbitration/krk_candidate_proposal_quality_dataset_v1.md
reports/strategy_arbitration/krk_candidate_proposal_quality_dataset_v1.json
reports/strategy_arbitration/krk_candidate_proposal_quality_probe_v1.md
reports/strategy_arbitration/krk_candidate_proposal_quality_probe_v1.json
reports/strategy_arbitration/krk_candidate_proposal_quality_decision_v1.md
reports/strategy_arbitration/krk_candidate_proposal_quality_decision_v1.json
reports/strategy_arbitration/krk_broader_strategy_sequence_candidate_source_design_v1.md
reports/strategy_arbitration/krk_broader_strategy_sequence_candidate_source_design_v1.json
reports/strategy_arbitration/krk_plan_capsule_sequence_candidate_observation_review_v1.md
reports/strategy_arbitration/krk_plan_capsule_sequence_candidate_observation_review_v1.json
reports/strategy_arbitration/krk_broader_strategy_candidate_observation_review_v1.md
reports/strategy_arbitration/krk_broader_strategy_candidate_observation_review_v1.json
reports/strategy_arbitration/krk_broader_strategy_sequence_candidate_source_review_v1.md
reports/strategy_arbitration/krk_broader_strategy_sequence_candidate_source_review_v1.json
reports/strategy_arbitration/krk_protected_strategy_monitor_frame_expansion_v1.md
reports/strategy_arbitration/krk_protected_strategy_monitor_frame_expansion_v1.json
reports/strategy_arbitration/krk_protected_strategy_monitor_frame_quality_v1.md
reports/strategy_arbitration/krk_protected_strategy_monitor_frame_quality_v1.json
reports/strategy_arbitration/krk_protected_strategy_monitor_observation_source_review_packet_v1.md
reports/strategy_arbitration/krk_protected_strategy_monitor_observation_source_review_packet_v1.json
```

These artifacts answer:

* What alternatives should a ReCoN reconsideration/strategy arbiter be able to see?
* Which current proposal sources are missing those alternatives?
* Which alternatives require existing provider proposals?
* Which require CandidateMoveFrame generation?
* Which require PlanCapsule sequence candidates?
* Which require new broader KRK strategy proposals?
* How should candidate generation remain visible and non-hidden?
* What is the first non-causal candidate-generation benchmark?
* What, if anything, would justify a future default-off candidate-generation sandbox?

Next safe step after observation-only candidate-generation coverage analysis:

```text
repair_monitor_observation_source_non_causal_quality_review
```

Do not implement a selector, score change, provider route, guardrail campaign, Stage 7 promotion, or Stage 8 training. The narrow repair-monitor observation source has been wired as an explicitly approved, default-off observation-only source and passed broadened protected equivalence; the next work is non-causal quality review, not selection.

## Runtime Approval Rule

Runtime tests are allowed only when all of these are true:

1. There is a review packet.
2. The change is default-off.
3. The scope is narrow.
4. The mechanism is traceable.
5. Source terms are visible.
6. Default-off equivalence is tested first.
7. Target improvement is tested before guardrails.
8. Guardrails are required before any promotion.
9. Failure leads to quarantine, not tuning loops.

## Stop Conditions

Stop and ask for review if:

* a diagnostic becomes another Stage 7 micro-repair,
* a runtime sandbox is proposed without a review packet,
* default-off behavior changes,
* DTM/tablebase starts affecting runtime policy,
* topology mutates during gameplay,
* protected Stage 5/6 behavior regresses,
* a mechanism cannot cite visible source terms,
* candidate-generation and strategy-selection labels are mixed,
* forced-provider labels are treated as direct selector labels,
* an internal terminal is proposed for causal use without validation,
* a run becomes too slow for the intended slice.

## Summary For Future Agents

The project is no longer trying to “solve Stage 7” directly.

Stage 7 is a held-out stress test that revealed missing control-plane machinery.

The next serious architecture work is:

```text
candidate generation + strategy/sequence proposal coverage
```

not:

```text
more Stage 7 patches
```

Runtime work is not forbidden forever, but runtime sandboxes must be reviewed, default-off, scoped, reversible, and quickly quarantined if target behavior does not improve.

```
```
