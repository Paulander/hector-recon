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

The execution manifest binds all `12` planned forced-provider control-label jobs to explicit topology/profile/checkpoint metadata. Stage5 jobs bind to the frozen Stage5 topology; Stage6 jobs bind to the promoted Stage6 overlay-composed topology. All bindings are valid and use `handoff_composition_v1`. The manifest generates no labels and changes no runtime behavior. Recommended next step: `run_bounded_forced_provider_control_labels`.

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
```

No runtime behavior should change while Stage 7 is paused.
