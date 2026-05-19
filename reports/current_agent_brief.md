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
- A replay-free protected-stage audit is recorded in `reports/krk_protected_stage_status.md` and `reports/krk_protected_stage_status.json`: Stage 1, Stage 5, and Stage 6 are clean protected/promoted components; Stage 4 is clean in the 500-sample `handoff_composition_v1` profile but carries a separate h40 overlay-control caveat that reproduces on the frozen Stage 5 base and is not Stage 6 interference.
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
- The offline training-objective benchmark did not justify a runtime sandbox: simple pairwise/ranked visible-term scoring underperformed the current learned scorer, visible log-odds/box heuristics improved top-1 only modestly while worsening hard-negative/draw behavior, and oracle ceilings remain high. The internal-monitor-augmented offline scorer used non-causal `InternalTerminalSpec` evidence only as diagnostic features and did not improve over the visible-term baseline. The hard decision gate selected `model_expression_gap_persists_stage7_micro_work_stops`; Stage 7 micro-work should stop pending architecture review.
- Stage 7 post-decision closure is complete. The closure verified the benchmark/gate artifacts and records `model_expression_gap_persists_stage7_micro_work_stops` as the current hard stop. Any future sequence-policy/model-expression redesign requires explicit architecture review before implementation.
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

Missing-feature candidate audit:

- `reports/strategy_arbitration/krk_strategy_missing_feature_candidates.json`
- `reports/strategy_arbitration/krk_strategy_missing_feature_candidates.md`

The audit proposed six non-causal terminal/affordance candidates: `edge_net_affordance`, `king_support_conversion_affordance`, `box_shrink_exit_condition`, `phase_boundary_near_edge`, `fence_or_cut_repair_affordance`, and `plan_selection_needed`. These remain `proposed` and non-causal. The next step is architecture review before any terminal/affordance runtime sandbox.

Feature candidate validation:

- `reports/strategy_arbitration/krk_feature_candidate_validation_v0.json`
- `reports/strategy_arbitration/krk_feature_candidate_validation_v0.md`

The validation typed all six candidates without finding any sandbox-ready term. `edge_net_affordance` and `phase_boundary_near_edge` need companion terms, `king_support_conversion_affordance` is too broad as defined, `box_shrink_exit_condition` is only a possible owner-release condition needing more evidence, `fence_or_cut_repair_affordance` is failure-correlated and should be treated as a risk/repair-pressure monitor, and `plan_selection_needed` is a Stage7-only growth-pressure/internal monitor. No candidate authorizes runtime arbiter work, causal terminals, Stage 7 repair, Stage 7 promotion, or Stage 8 training.

KRK Strategy Monitor v0 plan:

- `reports/strategy_arbitration/krk_strategy_monitor_v0_plan.json`
- `reports/strategy_arbitration/krk_strategy_monitor_v0_plan.md`

The accepted interpretation is that the six candidates are monitor/internal-terminal candidates, not causal move-support affordances. The next non-causal direction is StrategyMonitorRecord extraction over existing artifacts if it can be done replay-free and cheaply. The monitor classes are `PhaseBoundaryMonitor`, `OwnerExitMonitor`, `RepairNeededMonitor`, `PlanSelectionNeededMonitor`, and `GrowthPressureMonitor`. No monitor is authorized to route providers, choose moves, mutate topology, or change runtime defaults.

KRK Strategy Monitor records v0:

- `reports/strategy_arbitration/krk_strategy_monitor_records_v0.json`
- `reports/strategy_arbitration/krk_strategy_monitor_records_v0.md`

The replay-free extraction produced five monitor definitions, one rejected definition, and `108` non-causal StrategyMonitorRecord entries over the existing arbitration dataset. `PhaseBoundaryMonitor` and `OwnerExitMonitor` remain mixed-outcome and require companion terms before any sandbox; `RepairNeededMonitor` and `PlanSelectionNeededMonitor` are failure-oriented internal monitors. The extraction does not authorize runtime terminals, provider routing, Stage 7 repair, Stage 7 promotion, or Stage 8 training. The next step is architecture review or targeted companion-term design.

KRK Strategy Monitor companion terms v0:

- `reports/strategy_arbitration/krk_strategy_monitor_companion_terms_v0.json`
- `reports/strategy_arbitration/krk_strategy_monitor_companion_terms_v0.md`

The companion-term design proposes non-causal term sets for phase-boundary, owner-exit, repair-needed, plan-selection, and king-support redesign tracks. It explicitly keeps all terms non-causal and recommends only a replay-free companion-term availability audit or architecture review next. It does not authorize runtime terminals, a runtime arbiter, monitor-to-provider routing, Stage 7 repair, Stage 7 promotion, or Stage 8 training.

KRK Strategy Monitor companion audit v0:

- `reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v0.json`
- `reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v0.md`

The replay-free audit found `3` exact terms, `1` expression term, `16` proxy-only terms, and `14` terms missing from the current dataset. Phase-boundary and plan-selection companions are proxy-only; owner-exit, repair-needed, and king-support redesign are only partly available. The audit recommends architecture review before adding new visible extraction terms. It does not authorize runtime terminals, runtime arbitration, monitor-to-provider routing, Stage 7 repair, Stage 7 promotion, or Stage 8 training.

KRK visible monitor terms v0 and companion audit v1:

- `reports/strategy_arbitration/krk_visible_monitor_terms_v0.json`
- `reports/strategy_arbitration/krk_visible_monitor_terms_v0.md`
- `reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v1.json`
- `reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v1.md`

The Tier 1 diagnostic extraction added six non-causal visible monitor terms: `king_support_improves_after_move`, `cut_or_fence_restored_after_move`, `safe_repair_move_exists`, `box_area_no_longer_decision_relevant`, `post_plan_stagnation`, and `local_provider_competition_failed`. The v1 companion audit moved six terms to extracted status and better grounded owner-exit, repair-needed, plan-selection, and king-support redesign monitors. It still leaves `11` terms missing, keeps phase-boundary companions proxy-only, and identifies `safe_repair_move_exists`, `king_support_improves_after_move`, and `box_area_no_longer_decision_relevant` as broad monitor evidence rather than affordances. The sparse terms `post_plan_stagnation` and `local_provider_competition_failed` are possible future internal-terminal candidates, but no runtime use is authorized.

KRK Strategy Monitor maturity gate v0:

- `reports/strategy_arbitration/krk_strategy_monitor_maturity_gate_v0.json`
- `reports/strategy_arbitration/krk_strategy_monitor_maturity_gate_v0.md`

The maturity gate classifies extracted terms before any runtime/sandbox work. `box_area_no_longer_decision_relevant` and `king_support_improves_after_move` are context features, `safe_repair_move_exists` is too broad, `cut_or_fence_restored_after_move` is a repair monitor candidate, and `post_plan_stagnation` plus `local_provider_competition_failed` are the strongest sparse internal-terminal candidates. No term is causal-ready. High-priority backlog terms remain `edge_net_pressure_increases_after_move`, `safe_edge_net_tighten_move_exists`, `king_support_aligned_with_edge_net`, `handoff_success_after_plan`, and `multi_step_progress_required`.

KRK internal-terminal candidates v0:

- `reports/strategy_arbitration/krk_internal_terminal_candidates_v0.json`
- `reports/strategy_arbitration/krk_internal_terminal_candidates_v0.md`
- `reports/strategy_arbitration/krk_internal_terminal_validation_v0.json`
- `reports/strategy_arbitration/krk_internal_terminal_validation_v0.md`

Four non-causal `InternalTerminalSpec` candidates are defined: `terminal.krk.local_provider_competition_failed`, `terminal.krk.post_plan_stagnation`, `terminal.krk.box_shrink_owner_exit_pressure`, and `terminal.krk.repair_needed_monitor`. Replay-free validation keeps `local_provider_competition_failed` and `post_plan_stagnation` as the strongest internal-terminal candidates, but both are sparse and Stage7-only. `box_shrink_owner_exit_pressure` and `repair_needed_monitor` remain monitoring-only / companion-dependent. No runtime terminal, causal affordance, routing change, Stage 7 repair, Stage 7 promotion, or Stage 8 training is authorized.

KRK internal-terminal evidence/design review v1:

- `reports/strategy_arbitration/krk_internal_terminal_evidence_v1.json`
- `reports/strategy_arbitration/krk_internal_terminal_evidence_v1.md`
- `reports/strategy_arbitration/krk_internal_terminal_design_review_v1.json`
- `reports/strategy_arbitration/krk_internal_terminal_design_review_v1.md`

The v1 evidence aggregation broadens the non-causal review without new playouts. `local_provider_competition_failed` and `post_plan_stagnation` remain the closest future runtime-visible non-causal internal-terminal candidates, but they are still sparse and Stage7-only. `repair_needed_monitor` has broader cross-stage evidence but is noisy, and `box_shrink_owner_exit_pressure` still needs companion handoff-target terms. No terminal is causal-ready; the next safe direction is broader replay-free evidence collection or review, not runtime implementation.

KRK self-expansion architecture gate v0:

- `reports/krk_self_expansion_architecture_gate_v0.json`
- `reports/krk_self_expansion_architecture_gate_v0.md`

The gate synthesizes the protected Stage 1/4/5/6 stack, Stage 7 hard stop, strategy-arbitration decision gate, internal-terminal review, and sequence-policy redesign note. It selects `krk_control_plane_evidence_contract_v0` as the next architecture goal: a non-causal data contract that unifies protected provider provenance, strategy proposal frames, internal monitor records, plan-capsule windows, sequence training examples, guardrail summaries, GrowthGovernor status, and promotion-gate status. This is the path toward arbitrary KRK coverage without reopening Stage 7 micro-repairs or implementing a runtime arbiter.

KRK control-plane evidence contract v0:

- `reports/krk_control_plane_evidence_contract_v0.json`
- `reports/krk_control_plane_evidence_contract_v0.md`

The contract defines non-causal `ControlPlaneEvidenceFrame` evidence and required subschemas: protected provider provenance, strategy proposal frames, internal monitor evidence, plan-capsule window evidence, sequence training examples, guardrail summaries, GrowthGovernor status, and PromotionGate status. Its recommended next slice is `control_plane_manifest_from_existing_artifacts_v0`: map existing artifacts into the contract replay-free, with no new playouts, no runtime consumers, no Stage 7 promotion, and no Stage 8 training.

KRK control-plane manifest v0:

- `reports/krk_control_plane_manifest_v0.json`
- `reports/krk_control_plane_manifest_v0.md`

The manifest maps existing artifacts into the control-plane contract without adding playouts. Existing coverage includes `33` strategy records, `87` StrategyProposalFrame entries, `108` monitor records, `13` Stage7 plan windows, `25` seed sequence steps, and `195` expanded sequence steps. The main gaps are: no unified per-state `ControlPlaneEvidenceFrame` export yet, GrowthGovernor status is not frame-level, sequence examples are Stage7-only, and plan windows are Stage7-only. Recommended next slice: `stratified_control_plane_gap_report_v0`.

KRK control-plane gap report v0:

- `reports/krk_control_plane_gap_report_v0.json`
- `reports/krk_control_plane_gap_report_v0.md`

The gap report keeps the architecture work non-causal and selects `export_replay_free_control_plane_frames_v0` as the next implementation slice. It defers new sequence data collection, runtime strategy arbiter sandboxing, runtime internal-terminal sandboxing, Stage 8 training, and Stage 7 promotion until after unified per-state control-plane frames exist.

KRK control-plane frames v0:

- `reports/krk_control_plane_frames_v0.json`
- `reports/krk_control_plane_frames_v0.md`

The frame export creates `33` non-causal `ControlPlaneEvidenceFrame` records from existing artifacts only, with `87` strategy proposal frames, `224` attached monitor records, `13` plan-capsule window records, and `5` matched offline sequence-training examples. It adds no playouts and no runtime consumers. Remaining gaps: sequence examples and plan windows are Stage7-only, GrowthGovernor status is inferred from summary/design artifacts rather than runtime-exported frame status, and cross-domain bridge frames are not exported yet. Recommended next slice: `control_plane_frame_quality_report_v0`.

KRK control-plane frame quality report v0:

- `reports/krk_control_plane_frame_quality_report_v0.json`
- `reports/krk_control_plane_frame_quality_report_v0.md`

The quality report says the frame export is ready for non-causal strategy-arbitration probing only with dedupe and missing-proposal caveats. It is not ready for a general KRK sequence-policy benchmark because sequence examples and plan windows remain Stage7-only. Runtime sandboxing, Stage 7 promotion, and Stage 8 training remain blocked. Recommended next slice: `control_plane_frame_dedupe_and_quality_filters_v0`.

KRK control-plane filtered frames v0:

- `reports/krk_control_plane_filtered_frames_v0.json`
- `reports/krk_control_plane_filtered_frames_v0.md`

The filtered export adds non-causal benchmark-role and dedupe metadata to the `33` control-plane frames. It identifies `28` frames ready for offline strategy-arbitration probing (`10` Stage6, `8` Stage5, `6` Stage4, `4` Stage7), keeps `5` frames as context-only, and confirms sequence-policy benchmarking remains blocked for general KRK because sequence examples are Stage7-only. Runtime sandboxing, Stage 7 promotion, and Stage 8 training remain blocked. Recommended next slice: `offline_strategy_arbitration_probe_filtered_v0`.

KRK control-plane strategy arbitration probe v0:

- `reports/krk_control_plane_strategy_arbitration_probe_v0.json`
- `reports/krk_control_plane_strategy_arbitration_probe_v0.md`

The filtered offline probe remains non-causal and does not justify a runtime arbiter. A label-parser correction now recognizes both `known_outcome_label.result` and `known_outcome_label.playout_result`. With that correction, all `28` strategy-benchmark frames have provider-level labels and `14` frames have a known provider-mate option, so the result is `provider_labels_sufficient_for_small_probe`. Raw-score, normalized-score, and provider-rank selectors remain mixed rather than promotion evidence. Recommended next slice: `offline_strategy_arbitration_baseline_v1`, not a sandbox.

KRK provider label coverage plan v0:

- `reports/krk_provider_label_coverage_plan_v0.json`
- `reports/krk_provider_label_coverage_plan_v0.md`

The corrected coverage plan now reports provider labels for all benchmark proposals: `24` Stage7, `16` Stage5, `20` Stage6, and `6` Stage4 labels. There are no unknown provider labels in the current filtered-frame artifact. The bounded p0/p1/p2 label plan remains documented as a fallback if future coverage gaps reopen, but no p0 label run is needed before the next non-causal arbitration baseline.

KRK control-plane strategy arbitration baseline v1:

- `reports/krk_control_plane_strategy_arbitration_baseline_v1.json`
- `reports/krk_control_plane_strategy_arbitration_baseline_v1.md`

The baseline is a non-causal selector comparison over the `28` filtered control-plane benchmark frames. It finds `14` frames with a known provider-mate option and `14` frames where all labeled provider proposals max out. Raw score, normalized score, provider-local rank, and stage-prior heuristics recover most converting providers when one is present, but selected mate rate remains about half because many frames have no labeled converting provider. The decision is `strategy_arbitration_promising`, with next class `non_causal_strategy_arbiter_sandbox_design`. This does not authorize implementing a runtime arbiter, runtime terminals, Stage 7 promotion, or Stage 8 training.

KRK strategy arbiter sandbox design v0:

- `reports/krk_strategy_arbiter_sandbox_design_v0.json`
- `reports/krk_strategy_arbiter_sandbox_design_v0.md`

The design records the next architecture-review package for a possible future default-off KRK strategy arbiter. It is design-only and explicitly blocks runtime implementation without review. Open risks are mixed provider-label semantics, max-only frames that may indicate capacity or missing-proposal gaps, weak context-only heuristics, and Stage 7 overfit risk. Recommended next step: `architecture_review_before_any_runtime_sandbox`.

KRK strategy arbiter evidence risk review v0:

- `reports/krk_strategy_arbiter_evidence_risk_review_v0.json`
- `reports/krk_strategy_arbiter_evidence_risk_review_v0.md`

The pre-sandbox risk review separates provider-label semantics and max-only frame types. It finds mixed label semantics: `24` forced-provider outcomes, `24` selected-provider playouts, and `18` same-move unselected-provider playouts. The `14` max-only frames split into `2` Stage7 forced existing-provider capacity/horizon gaps and `12` protected-stage selected-playout guardrail/horizon caveats. Decision: `runtime_sandbox_blocked_pending_semantics_review`; next step is `stratified_non_causal_arbiter_evaluation_v2`, not runtime implementation.

KRK strategy arbiter stratified probe v2:

- `reports/krk_strategy_arbiter_stratified_probe_v2.json`
- `reports/krk_strategy_arbiter_stratified_probe_v2.md`

The stratified probe evaluates selected-provider playout labels, forced-provider labels, and same-move unselected-provider labels separately. Selected protected-control labels are easy for simple selectors (`1.0` best positive-hit rate), but forced Stage7 provider labels remain weak (`0.5` best positive-hit rate) and sparse. Decision: `selected_playout_controls_promising_forced_stage7_still_weak`; runtime sandbox remains blocked. Recommended next step: `collect_or_review_forced_provider_controls_before_sandbox`.

KRK forced provider control label plan v0:

- `reports/krk_forced_provider_control_label_plan_v0.json`
- `reports/krk_forced_provider_control_label_plan_v0.md`

The plan creates `12` bounded non-causal label jobs for protected Stage5/6 frames (`6` per stage) so future evidence can compare protected controls using the same forced-provider semantics as the Stage7 residual labels. It generates no labels and changes no runtime behavior. Recommended next step: `run_bounded_forced_provider_control_labels_if_runner_available`; runtime arbiter implementation remains blocked until these controls are reviewed or collected.

KRK forced provider label execution manifest v0:

- `reports/krk_forced_provider_label_execution_manifest_v0.json`
- `reports/krk_forced_provider_label_execution_manifest_v0.md`

The execution manifest binds all `12` planned forced-provider control-label jobs to explicit topology/profile/checkpoint metadata. Stage5 jobs bind to the Stage5 frozen provider pack as carried inside the promoted Stage6 overlay-composed topology, because the raw Stage5 topology predates canonical `skill_id` metadata and cannot be safely forced by `krk.*` provider id. Stage6 jobs also bind to the promoted Stage6 overlay-composed topology. All bindings are valid and use `handoff_composition_v1`. The manifest generates no labels and changes no runtime behavior. Recommended next step: `run_bounded_forced_provider_control_labels`.

KRK forced provider control labels v0:

- `reports/krk_forced_provider_control_labels_v0.json`
- `reports/krk_forced_provider_control_labels_v0.md`
- `reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json`
- `reports/krk_control_plane_filtered_frames_with_forced_controls_v0.md`

The bounded label run generated `12` non-causal forced-provider control labels. Stage5 controls are `6/6` mate and Stage6 controls are `3` mate / `3` max_plies. The original filtered frames remain unchanged; the labels are attached only in the separate augmented evidence artifact.

Updated KRK strategy arbiter stratified probe v2:

The stratified probe now uses the augmented forced-control evidence. Protected selected-control and forced-control labels are both promising (`1.0` best positive-hit rates), while forced Stage7 residual labels remain weaker (`0.5`). Decision: `protected_forced_controls_promising_stage7_gap_confirmed`. Runtime sandbox remains blocked until architecture review, and Stage7 residuals should stay held out from tuning.

KRK strategy arbiter architecture review v1:

- `reports/krk_strategy_arbiter_architecture_review_v1.json`
- `reports/krk_strategy_arbiter_architecture_review_v1.md`

The review allows only a default-off, trace-only `krk_strategy_arbiter_observability_skeleton_v0`. It explicitly does not authorize runtime provider selection, score changes, support adapters, Stage 7 repair, Stage 7 promotion, Stage 8 training, runtime DTM/tablebase, gameplay-time topology mutation, or M3/M4 arbitration updates. The next implementation, if attempted, must prove default-off equivalence and may attach only non-causal observation metadata when explicitly enabled.

KRK strategy arbiter observability skeleton v0:

- Implemented in `scripts/test_krk_landmark_progress.py` behind `--enable-krk-strategy-arbiter-observability`.
- Default off means no `krk_strategy_arbiter_observation` metadata is emitted.
- When explicitly enabled, the harness records non-causal `krk_strategy_arbiter_observation.v0` metadata after normal move selection.
- The observation records already-materialized provider candidates, selected provider before observation, visible source terms, `direct_request=false`, `score_delta=0.0`, and blocked causal actions.
- It does not change scores, selected moves, selected providers, topology, runtime defaults, DTM/tablebase use, or M1-M4 behavior.
- A tiny paired evaluator check showed identical one-ply/conversion outcome metrics with the flag off vs on; the enabled run only added observation count.

KRK strategy arbiter observability smoke v0:

- `reports/krk_strategy_arbiter_observability_smoke_v0.json`
- `reports/krk_strategy_arbiter_observability_smoke_v0.md`

The smoke records the paired default-off check. Behavior/outcome metrics matched between the default-off and enabled runs; the only intended delta was one non-causal observation frame. This supports collecting small non-causal observation frames next, but still does not authorize runtime arbitration, score changes, provider routing, Stage 7 repair, Stage 7 promotion, or Stage 8 training.

KRK strategy arbiter observation frames v0:

- `scripts/collect_krk_strategy_arbiter_observation_frames.py`
- `reports/krk_strategy_arbiter_observation_frames_v0.json`
- `reports/krk_strategy_arbiter_observation_frames_v0.md`

The collector performs one-ply trace-only observation over existing control-plane FENs using `handoff_composition_v1`. It generated `12` non-causal records: `9` Stage 7 held-out challenge rows, `2` Stage 4 control rows, and `1` Stage 5 control row. It ran no conversion playouts, training, runtime routing, DTM/tablebase lookup, topology mutation, or default changes. The selected providers were mostly `krk.stage0_basin` (`11/12`), with one `krk.fence_established` control row. The next allowed step is review of observation-frame separability before any sandbox.

KRK strategy arbiter observation separability review v0:

- `scripts/review_krk_strategy_arbiter_observation_separability.py`
- `reports/krk_strategy_arbiter_observation_separability_review_v0.json`
- `reports/krk_strategy_arbiter_observation_separability_review_v0.md`

The first review found the observation layer was audit-useful but under-instrumented. The trace-only observation was then enriched with existing KRK context terms and all-provider summaries without writing those terms back to runtime blackboard state or affecting selection. The regenerated review now reports source-term counts between `13` and `21`, `7` provider families in each observation summary, and status `observation_frames_ready_for_non_causal_selector_probe`. Runtime arbitration remains blocked. The next allowed step is a replay-free observation selector probe only; no provider support, score changes, Stage 7 repair, Stage 7 promotion, or Stage 8 training is authorized.

KRK strategy arbiter observation selector probe v0:

- `scripts/probe_krk_strategy_arbiter_observation_selector.py`
- `reports/krk_strategy_arbiter_observation_selector_probe_v0.json`
- `reports/krk_strategy_arbiter_observation_selector_probe_v0.md`

The replay-free selector probe found the observation rows are still under-labeled for sandbox review. Only `3/12` rows have provider labels, Stage 7 held-out rows are unlabeled, and the probe status is `observation_selector_probe_underlabeled`. Runtime arbiter work remains blocked. The next allowed evidence slice is small labeled observation controls before any sandbox review, not a runtime selector.

KRK strategy arbiter labeled observation controls v0:

- `scripts/collect_krk_strategy_arbiter_labeled_observation_controls.py`
- `reports/krk_strategy_arbiter_labeled_observation_controls_v0.json`
- `reports/krk_strategy_arbiter_labeled_observation_controls_v0.md`
- `scripts/probe_krk_strategy_arbiter_labeled_controls.py`
- `reports/krk_strategy_arbiter_labeled_controls_probe_v0.json`
- `reports/krk_strategy_arbiter_labeled_controls_probe_v0.md`

The labeled control export collected `21` trace-only records: `5` Stage 4, `6` Stage 5, `4` Stage 6, and `6` Stage 7 held-out rows. The replay-free probe found `14` labeled controls, with selected labels `9` positive, `5` negative, and `7` unknown. Stage 7 remains unlabeled holdout (`6` unknown). Status: `labeled_controls_mixed_no_sandbox`. Runtime arbitration is still blocked; the next step must be architecture review of selector objective/label semantics or more labels, not implementation of a runtime selector.

KRK strategy arbiter control-plane review v0:

- `reports/krk_strategy_arbiter_control_plane_review_v0.json`
- `reports/krk_strategy_arbiter_control_plane_review_v0.md`

The review closes the current observability/control-label package. Decision: `selector_objective_and_label_semantics_review_required`. The observation layer is now useful for offline selector research, but the target label space mixes selected playout success, forced-provider conversion, same-move provider compatibility, held-out Stage 7 challenge status, and guardrail safety. Runtime arbiter and sandbox work remain blocked. The next non-causal architecture step is `krk_selector_objective_label_semantics_v0`.

KRK selector objective label semantics v0:

- `reports/krk_selector_objective_label_semantics_v0.json`
- `reports/krk_selector_objective_label_semantics_v0.md`

The label contract separates `selected_playout_success`, `forced_provider_conversion`, `same_move_provider_compatibility`, `guardrail_safety`, `handoff_or_plan_success`, and `held_out_challenge`. It explicitly states that forced-provider conversion is not a direct runtime-selection label, selected playout failure is not provider incapacity by itself, and Stage 7 held-out rows must stay excluded from training targets until review reclassifies them. The next allowed slice is `build_krk_selector_target_dataset_v0`, replay-free and non-causal.

KRK selector target dataset/probe v0:

- `scripts/build_krk_selector_target_dataset.py`
- `reports/krk_selector_target_dataset_v0.json`
- `reports/krk_selector_target_dataset_v0.md`
- `scripts/probe_krk_selector_target_dataset.py`
- `reports/krk_selector_target_probe_v0.json`
- `reports/krk_selector_target_probe_v0.md`

The replay-free dataset maps existing labels into explicit target kinds. It has `63` rows: `42` selected-playout examples, `12` forced-provider diagnostic examples, and `9` held-out Stage 7 challenge rows. Stage 7 contributes `0` training rows. The target probe reports training label counts `28` negative / `14` positive and status `target_dataset_ready_for_non_causal_baseline_probe`. Runtime arbiter and sandbox work remain blocked.

KRK selector baseline probe v0:

- `scripts/probe_krk_selector_baselines.py`
- `reports/krk_selector_baseline_probe_v0.json`
- `reports/krk_selector_baseline_probe_v0.md`

The non-causal baseline probe evaluates only `selected_playout_success` target rows. It has `42` rows with label counts `28` negative / `14` positive. Majority-label accuracy is `0.667`; provider-prior leave-one-out accuracy is `0.833`; stage and active-landmark priors are `0.595`. Status: `simple_selector_baseline_promising_non_causal`. This suggests provider identity carries useful control-plane signal, but it does not authorize a runtime arbiter. The next non-causal step is to join selector targets with trace-only observation features.

KRK selector feature dataset/probe/review v0:

- `scripts/build_krk_selector_feature_dataset.py`
- `reports/krk_selector_feature_dataset_v0.json`
- `reports/krk_selector_feature_dataset_v0.md`
- `scripts/probe_krk_selector_feature_baselines.py`
- `reports/krk_selector_feature_baseline_probe_v0.json`
- `reports/krk_selector_feature_baseline_probe_v0.md`
- `reports/krk_selector_feature_architecture_review_v0.json`
- `reports/krk_selector_feature_architecture_review_v0.md`

The joined feature dataset adds trace-only observation terms and provider summaries to explicit selector targets. The feature baseline probe did not improve over the provider-prior baseline: best remains `provider_prior_loo` at `0.833`. Decision: `provider_prior_remains_best_no_selector_sandbox`. Runtime arbiter and selector sandbox work remain blocked. The next decision is whether to expand protected-control labels, define state-local contrastive selector labels, or pause selector work and return to broader curriculum integration.

KRK provider identity / maturity review v0:

- `scripts/review_krk_provider_identity_maturity_signal.py`
- `reports/krk_provider_identity_maturity_review_v0.json`
- `reports/krk_provider_identity_maturity_review_v0.md`

The review explains the provider-prior result as a strong but non-causal provider identity/provenance signal. Raw provider ID is not a principled runtime selector; it can encode dataset and label bias. Decision: `provider_identity_signal_requires_provenance_decomposition`. Runtime arbiter and selector sandbox work remain blocked. The next safe slice is to add explicit non-causal provider provenance/maturity fields to selector evidence before any further selector baseline or sandbox review.

KRK selector provenance feature dataset/probe v0:

- `scripts/build_krk_selector_provenance_feature_dataset.py`
- `reports/krk_selector_provenance_feature_dataset_v0.json`
- `reports/krk_selector_provenance_feature_dataset_v0.md`
- `scripts/probe_krk_selector_provenance_features.py`
- `reports/krk_selector_provenance_feature_probe_v0.json`
- `reports/krk_selector_provenance_feature_probe_v0.md`

The provenance probe decomposes the provider-prior signal into explicit non-causal fields. `provider_family`, `provider_maturity`, `provider_source_stage`, and `family_maturity` all match the raw provider-id LOO accuracy of `0.833` on the current selected-playout control labels. This supports keeping provenance/maturity in evidence records, but it still does not authorize a runtime arbiter or selector sandbox because the labels are small and can encode horizon/control artifacts. Current decision: `provenance_features_explain_provider_prior_non_causal`; next step requires architecture review of selector objective or more labels before any sandbox.

KRK selector objective architecture review v1:

- `reports/krk_selector_objective_architecture_review_v1.json`
- `reports/krk_selector_objective_architecture_review_v1.md`

The review closes the selector-prior branch. Decision: `selector_objective_needs_stratified_label_expansion_before_sandbox`. The next safe slice is a bounded non-causal stratified label plan (`collect_small_stratified_selector_labels_v1`) that separates selected-playout success, forced-provider conversion, same-move compatibility, and guardrail-safe ownership while keeping Stage 7 held out. Runtime arbiter, selector sandbox, Stage 7 repair/promotion, and Stage 8 training remain blocked.

KRK selector stratified label plan v1:

- `scripts/plan_krk_selector_stratified_labels_v1.py`
- `reports/krk_selector_stratified_label_plan_v1.json`
- `reports/krk_selector_stratified_label_plan_v1.md`

The label plan is bounded and non-causal. It proposes `11` h40 protected-control jobs across Stage 4/5/6, keeps Stage 7 training rows at `0`, and does not execute labels. Existing evidence already contains selected-playout, forced-provider, and held-out challenge labels, but it still needs cleaner guardrail/same-move compatibility labels before sandbox review. Runtime arbiter and selector sandbox remain blocked; the plan should be reviewed or replay-free extraction should be preferred before any label execution.

KRK selector label plan replay-free review v1:

- `scripts/review_krk_selector_label_plan_replay_free.py`
- `reports/krk_selector_label_plan_replay_free_review_v1.json`
- `reports/krk_selector_label_plan_replay_free_review_v1.md`

The review found all `11` planned protected-control label jobs can be filled from existing artifacts (`compatible_target_label_available`) and require no new playouts. Decision: `planned_labels_replay_free_fillable`. The next safe step is to build a replay-free stratified selector label dataset from existing labels, not execute h40 jobs. Runtime arbiter, selector sandbox, Stage 7 repair/promotion, and Stage 8 training remain blocked.

KRK selector stratified label dataset/balance v1:

- `scripts/build_krk_selector_stratified_label_dataset_v1.py`
- `reports/krk_selector_stratified_label_dataset_v1.json`
- `reports/krk_selector_stratified_label_dataset_v1.md`
- `scripts/probe_krk_selector_stratified_label_balance.py`
- `reports/krk_selector_stratified_label_balance_probe_v1.json`
- `reports/krk_selector_stratified_label_balance_probe_v1.md`

The replay-free stratified dataset contains `11` protected-control rows but is underbalanced (`10` positive / `1` negative). Decision: `stratified_labels_underbalanced_no_selector_probe`. It is useful guardrail-positive evidence, but it is not enough to train/evaluate a selector or justify a sandbox. The next safe evidence step is to identify or collect negative protected-control labels, not use Stage 7 residuals as training labels.

KRK selector negative controls / balanced labels v1:

- `scripts/build_krk_selector_negative_control_manifest_v1.py`
- `reports/krk_selector_negative_control_manifest_v1.json`
- `reports/krk_selector_negative_control_manifest_v1.md`
- `scripts/build_krk_selector_balanced_label_dataset_v1.py`
- `reports/krk_selector_balanced_label_dataset_v1.json`
- `reports/krk_selector_balanced_label_dataset_v1.md`
- `scripts/probe_krk_selector_balanced_labels.py`
- `reports/krk_selector_balanced_label_probe_v1.json`
- `reports/krk_selector_balanced_label_probe_v1.md`

Replay-free negative protected controls were identified from existing selector labels (`9` controls across Stage 4/5/6). The balanced dataset has `18` rows (`9` positive / `9` negative), with Stage 7 training rows still `0`. The balanced probe finds a non-causal provider/provenance signal (`provider_id`, `provider_family`, and `provider_maturity` LOO accuracy `0.778`), while active-landmark/stage-only baselines are weak. Decision: `balanced_labels_support_non_causal_selector_signal`. This still does not authorize a runtime arbiter or selector sandbox; it requires architecture review and explicit guardrail criteria first.

KRK selector balanced architecture review v1:

- `reports/krk_selector_balanced_architecture_review_v1.json`
- `reports/krk_selector_balanced_architecture_review_v1.md`

The balanced-label architecture review records the current selector status as `selector_signal_promising_sandbox_blocked_pending_readiness_criteria`. Explicit provider provenance/maturity can explain the useful signal, but the evidence remains too small and control-derived for runtime use. The next allowed slice is a design-only sandbox readiness criteria document. Runtime arbiter, selector sandbox implementation, Stage 7 repair/promotion, Stage 8 training, and M3/M4 arbitration updates remain blocked.

KRK strategy arbiter sandbox readiness criteria v0:

- `reports/krk_strategy_arbiter_sandbox_readiness_criteria_v0.json`
- `reports/krk_strategy_arbiter_sandbox_readiness_criteria_v0.md`

The readiness criteria are now explicit. Current status: `readiness_criteria_defined_sandbox_still_blocked`. The main evidence gap is out-of-sample protected controls; any future sandbox must be default-off, KRK/profile scoped, traceable through `StrategyProposalFrame` plus provider provenance/maturity metadata, and guardrail-validated against Stage 4/5/6/1 and M1-M4. Runtime arbiter implementation remains blocked until architecture review or out-of-sample control collection.

KRK strategy arbiter out-of-sample control plan v0:

- `reports/krk_strategy_arbiter_out_of_sample_control_plan_v0.json`
- `reports/krk_strategy_arbiter_out_of_sample_control_plan_v0.md`

The out-of-sample plan defines a bounded protected-control evidence slice (`max_states=12`, h40, Stage 4/5/6 only, Stage 7 training rows `0`) but does not execute it. Decision: `out_of_sample_control_plan_defined_execution_blocked`. The next step should be review, then an execution manifest only if new labels are truly needed.

KRK strategy arbiter out-of-sample plan review v0:

- `scripts/review_krk_strategy_arbiter_out_of_sample_plan.py`
- `reports/krk_strategy_arbiter_out_of_sample_plan_review_v0.json`
- `reports/krk_strategy_arbiter_out_of_sample_plan_review_v0.md`

The plan review found the plan is consistent with invariants, but replay-free out-of-sample coverage is insufficient after excluding balanced-label states: only `2` replay-free candidates remain (`1` Stage 5 negative, `1` Stage 6 positive) and Stage 4 has no replay-free out-of-sample candidate. Decision: `plan_review_passed_execution_manifest_needed`. The next step is to generate a concrete non-causal execution manifest with topology/profile/checkpoint bindings before any h40 label execution. Runtime arbiter, selector sandbox, Stage 7 repair/promotion, and Stage 8 training remain blocked.

KRK strategy arbiter out-of-sample execution manifest v0:

- `scripts/generate_krk_strategy_arbiter_out_of_sample_execution_manifest.py`
- `reports/krk_strategy_arbiter_out_of_sample_execution_manifest_v0.json`
- `reports/krk_strategy_arbiter_out_of_sample_execution_manifest_v0.md`

The manifest defines `12` non-causal protected-control label jobs: `4` Stage 4, `4` Stage 5, and `4` Stage 6. It keeps `2` replay-free controls and fills missing coverage with `10` deterministic curriculum samples while excluding balanced-label states. All jobs bind to `handoff_composition_v1` on the Stage 6 overlay-composed topology with explicit protected provider/checkpoint metadata. Decision: `execution_manifest_ready_for_review`. It does not execute labels; h40 collection must be reviewed before running. Runtime arbiter, selector sandbox, Stage 7 repair/promotion, and Stage 8 training remain blocked.

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
reports/strategy_arbitration/krk_strategy_missing_feature_candidates.json
reports/strategy_arbitration/krk_strategy_missing_feature_candidates.md
reports/strategy_arbitration/krk_feature_candidate_validation_v0.json
reports/strategy_arbitration/krk_feature_candidate_validation_v0.md
reports/strategy_arbitration/krk_strategy_monitor_v0_plan.json
reports/strategy_arbitration/krk_strategy_monitor_v0_plan.md
reports/strategy_arbitration/krk_strategy_monitor_records_v0.json
reports/strategy_arbitration/krk_strategy_monitor_records_v0.md
reports/strategy_arbitration/krk_strategy_monitor_companion_terms_v0.json
reports/strategy_arbitration/krk_strategy_monitor_companion_terms_v0.md
reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v0.json
reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v0.md
reports/strategy_arbitration/krk_visible_monitor_terms_v0.json
reports/strategy_arbitration/krk_visible_monitor_terms_v0.md
reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v1.json
reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v1.md
reports/strategy_arbitration/krk_strategy_monitor_maturity_gate_v0.json
reports/strategy_arbitration/krk_strategy_monitor_maturity_gate_v0.md
reports/strategy_arbitration/krk_internal_terminal_candidates_v0.json
reports/strategy_arbitration/krk_internal_terminal_candidates_v0.md
reports/strategy_arbitration/krk_internal_terminal_validation_v0.json
reports/strategy_arbitration/krk_internal_terminal_validation_v0.md
reports/strategy_arbitration/krk_internal_terminal_evidence_v1.json
reports/strategy_arbitration/krk_internal_terminal_evidence_v1.md
reports/strategy_arbitration/krk_internal_terminal_design_review_v1.json
reports/strategy_arbitration/krk_internal_terminal_design_review_v1.md
reports/structural_candidates/stage7_training_objective_decision_gate.json
reports/structural_candidates/stage7_training_objective_decision_gate.md
reports/structural_candidates/stage7_post_decision_closure.json
reports/structural_candidates/stage7_post_decision_closure.md
reports/structural_candidates/stage7_sequence_policy_redesign_note.json
reports/structural_candidates/stage7_sequence_policy_redesign_note.md
reports/krk_protected_stage_status.json
reports/krk_protected_stage_status.md
reports/krk_self_expansion_architecture_gate_v0.json
reports/krk_self_expansion_architecture_gate_v0.md
reports/krk_control_plane_evidence_contract_v0.json
reports/krk_control_plane_evidence_contract_v0.md
reports/krk_control_plane_manifest_v0.json
reports/krk_control_plane_manifest_v0.md
reports/krk_control_plane_gap_report_v0.json
reports/krk_control_plane_gap_report_v0.md
reports/krk_control_plane_frames_v0.json
reports/krk_control_plane_frames_v0.md
reports/krk_control_plane_frame_quality_report_v0.json
reports/krk_control_plane_frame_quality_report_v0.md
reports/krk_control_plane_filtered_frames_v0.json
reports/krk_control_plane_filtered_frames_v0.md
reports/krk_control_plane_strategy_arbitration_probe_v0.json
reports/krk_control_plane_strategy_arbitration_probe_v0.md
reports/krk_provider_label_coverage_plan_v0.json
reports/krk_provider_label_coverage_plan_v0.md
reports/krk_strategy_arbiter_architecture_review_v1.json
reports/krk_strategy_arbiter_architecture_review_v1.md
reports/krk_strategy_arbiter_observability_smoke_v0.json
reports/krk_strategy_arbiter_observability_smoke_v0.md
reports/krk_strategy_arbiter_observation_frames_v0.json
reports/krk_strategy_arbiter_observation_frames_v0.md
reports/krk_strategy_arbiter_observation_separability_review_v0.json
reports/krk_strategy_arbiter_observation_separability_review_v0.md
reports/krk_strategy_arbiter_observation_selector_probe_v0.json
reports/krk_strategy_arbiter_observation_selector_probe_v0.md
reports/krk_strategy_arbiter_labeled_observation_controls_v0.json
reports/krk_strategy_arbiter_labeled_observation_controls_v0.md
reports/krk_strategy_arbiter_labeled_controls_probe_v0.json
reports/krk_strategy_arbiter_labeled_controls_probe_v0.md
reports/krk_strategy_arbiter_control_plane_review_v0.json
reports/krk_strategy_arbiter_control_plane_review_v0.md
reports/krk_selector_objective_label_semantics_v0.json
reports/krk_selector_objective_label_semantics_v0.md
reports/krk_selector_target_dataset_v0.json
reports/krk_selector_target_dataset_v0.md
reports/krk_selector_target_probe_v0.json
reports/krk_selector_target_probe_v0.md
reports/krk_selector_baseline_probe_v0.json
reports/krk_selector_baseline_probe_v0.md
reports/krk_selector_feature_dataset_v0.json
reports/krk_selector_feature_dataset_v0.md
reports/krk_selector_feature_baseline_probe_v0.json
reports/krk_selector_feature_baseline_probe_v0.md
reports/krk_selector_feature_architecture_review_v0.json
reports/krk_selector_feature_architecture_review_v0.md
reports/krk_provider_identity_maturity_review_v0.json
reports/krk_provider_identity_maturity_review_v0.md
reports/krk_selector_provenance_feature_dataset_v0.json
reports/krk_selector_provenance_feature_dataset_v0.md
reports/krk_selector_provenance_feature_probe_v0.json
reports/krk_selector_provenance_feature_probe_v0.md
reports/krk_selector_objective_architecture_review_v1.json
reports/krk_selector_objective_architecture_review_v1.md
reports/krk_selector_stratified_label_plan_v1.json
reports/krk_selector_stratified_label_plan_v1.md
reports/krk_selector_label_plan_replay_free_review_v1.json
reports/krk_selector_label_plan_replay_free_review_v1.md
reports/krk_selector_stratified_label_dataset_v1.json
reports/krk_selector_stratified_label_dataset_v1.md
reports/krk_selector_stratified_label_balance_probe_v1.json
reports/krk_selector_stratified_label_balance_probe_v1.md
reports/krk_selector_negative_control_manifest_v1.json
reports/krk_selector_negative_control_manifest_v1.md
reports/krk_selector_balanced_label_dataset_v1.json
reports/krk_selector_balanced_label_dataset_v1.md
reports/krk_selector_balanced_label_probe_v1.json
reports/krk_selector_balanced_label_probe_v1.md
reports/krk_selector_balanced_architecture_review_v1.json
reports/krk_selector_balanced_architecture_review_v1.md
reports/krk_strategy_arbiter_sandbox_readiness_criteria_v0.json
reports/krk_strategy_arbiter_sandbox_readiness_criteria_v0.md
reports/krk_strategy_arbiter_out_of_sample_control_plan_v0.json
reports/krk_strategy_arbiter_out_of_sample_control_plan_v0.md
reports/krk_strategy_arbiter_out_of_sample_plan_review_v0.json
reports/krk_strategy_arbiter_out_of_sample_plan_review_v0.md
reports/krk_strategy_arbiter_out_of_sample_execution_manifest_v0.json
reports/krk_strategy_arbiter_out_of_sample_execution_manifest_v0.md
```

No runtime behavior should change while Stage 7 is paused.
