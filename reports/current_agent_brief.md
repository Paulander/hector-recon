# Current Agent Brief

This file is the current source-of-truth brief for future coding agents. It summarizes the active architecture constraints and the next diagnostic direction without replacing historical logs such as `reports/krk_handoff_counterfactual_notes.md`.

## Project Goal

Build ReCoN-lite as an inspectable, self-growing chess architecture where visible SCRIPT/TERMINAL structure, bounded plasticity, and offline structural promotion cooperate without hidden runtime controllers.

The near-term KRK goal is to preserve the validated handoff/composition stack while moving beyond Stage 7 local repair into broader KRK strategy ownership and sequence-policy evidence.

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

Architecture decision:

```text
box_shrink_reclassified_as_local_evidence_handoff_trigger
```

Current interpretation:

- Local/one-ply behavior can be improved.
- Conversion remains unresolved.
- Stage 7 must not be promoted.
- Stage 8 must not be trained from unresolved Stage 7.
- Stage 7 is no longer a standalone repair target. `box_shrink` is retained as local evidence / handoff trigger / phase-boundary signal and Stage 7 residuals are held-out challenge cases for broader KRK strategy/sequence work.
- The current task is architecture/evidence work, not a Stage 7 runtime patch.
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
- The latest bounded runtime-test evidence (`krk_state_local_contrast_readiness_review_v2`) blocks runtime selector work: diverse forced-provider labels added Stage 7 held-out max_plies evidence, but protected training labels remain too sparse/positive-heavy and leave-state-out negative suppression is still `0.0`. Next step is architecture review before more runtime tests, not a causal selector.
- The runtime-test architecture review v3 keeps runtime selector work blocked and reframes the next selector objective as abstention-first: learn to reject unsafe ownership before ranking owners. `reports/krk_abstention_first_selector_objective_v0.md/json` defines minimum evidence requirements (`>=40` protected training rows, `>=12` protected negatives, Stage7 training rows `0`) before any runtime review.
- Replay-free abstention reconstruction (`krk_abstention_training_dataset_v0` / `krk_abstention_training_probe_v0`) recovered `28` protected rows but only `5` unsafe-owner examples. Leave-state-out negative suppression remains `0.0`; runtime selector work remains blocked until more protected negative controls or a better non-causal objective is available.
- Abstention v1 added selected-playout labels replay-free and reached the raw evidence threshold (`51` protected rows, `17` unsafe-owner examples), but the best leave-state-out negative suppression is only `0.176` with safe preservation `0.618`. This confirms that count alone is not enough; the abstention objective needs better state/context features or cleaner label semantics before any runtime review.
- `krk_abstention_feature_gap_review_v0` concludes the next safe step is replay-free only: join abstention labels with ControlPlaneEvidenceFrame terminal-space/proposal/monitor context. Runtime selector work remains blocked.
- `krk_abstention_context_feature_dataset_v0` / `krk_abstention_context_feature_probe_v0` joined all `51` abstention rows to replay-free control-plane context. Context features help negative suppression (`0.824` best via king-support bucket + provider family vs `0.176` baseline) but safe preservation is only `0.647`, below the `0.7` runtime-review threshold. Runtime selector work remains blocked; the next work, if any, must refine context labels/features non-causally or go back to architecture review.
- `krk_abstention_context_error_audit_v0` shows why runtime remains blocked: the best context objective has `12` false positives and over-rejects mostly known-safe Stage 5 `edge_trap` owners. The next safe step is a non-causal safe-preservation / label-semantics review, not a selector implementation.
- `krk_abstention_safe_preservation_label_review_v0` reframes the blocker as label semantics: forced-provider conversion and selected-playout success/failure should not be collapsed into one abstention target. It proposes a two-stage non-causal objective that first preserves validated safe owners, then suppresses unsafe owners. Runtime selector work remains blocked.
- `krk_two_stage_abstention_objective_probe_v0` found `12` threshold-passing offline objectives. The best preservation-gated result reaches negative suppression `0.706` and safe preservation `0.853`, which is the first abstention result to clear both non-causal review thresholds. This still does not authorize runtime behavior; it requires architecture review before any default-off selector sandbox.
- `krk_two_stage_abstention_runtime_review_packet_v0` packages that evidence for explicit review. It records the default-off sandbox requirements and keeps implementation blocked by this packet (`implementation_allowed_by_this_packet = false`). The next step requires an explicit decision before implementing a runtime selector.
- After explicit runtime-test approval, the two-stage abstention selector was implemented as default-off, opt-in, traceable, and reversible. Rollback tag: `pre-two-stage-abstention-runtime`. Default-off equivalence passed on a protected Stage 5 sample, and the enabled protected-control smoke caused no paired metric delta or shadow regression.
- `krk_two_stage_abstention_stage7_challenge_smoke_v0` found no Stage 7 target improvement: the selector fired with the Stage 7 allow flag, but selected no penalized suggestions and remained at `{"max_plies": 2, "mate": 1}`. `krk_two_stage_abstention_runtime_go_no_go_v0` therefore records `no_go_for_scaling_or_promotion`. Keep the selector default-off as a runtime-test scaffold; do not scale, promote, tune thresholds, or treat it as a Stage 7 repair.
- `stage7_selected_failure_path_audit_v0` shows why the abstention selector did not help: the actual selected max-plies path is `krk.stage0_basin` in all four replay-free selected failure families, while the selector penalized non-selected suggestions in the Stage 7 smoke. The selected failures split into two classes: two are strategy-ownership gaps where an existing provider converts if selected, and two are sequence/continuation-capacity gaps where tested providers/legal-first h40 still fail. Next work should model those two target classes separately, not tune a single penalty.
- `stage7_selected_path_target_spec_v0` formalizes that split as non-causal targets: `stage7.selected_path.strategy_ownership_gap.v0` and `stage7.selected_path.sequence_continuation_gap.v0`. No runtime behavior is authorized; the next allowed work is either a replay-free selected-path target dataset or an architecture review.
- `stage7_selected_path_target_dataset_v0` assembled a replay-free split-target dataset. The ownership target is minimally trainable but has only two Stage 7 positives; the sequence/continuation target is underpowered because no successful Stage 7 post-box sequence controls were recovered. Before another runtime selector or sequence-policy sandbox, recover or collect successful post-box sequence controls and hard-negative contrasts non-causally.
- `stage7_post_box_sequence_control_recovery_v0` recovered 14 replay-free successful post-box sequence controls from prior Stage 7 sandbox artifacts. `stage7_selected_path_target_dataset_v1` is now minimally ready for a non-causal split-target probe, with a strict caveat: the sequence controls are sandbox-sourced offline labels and do not authorize runtime behavior.
- `stage7_selected_path_target_probe_v0` found the split targets are separable offline, but the sequence target is source-biased because all recovered success controls are from prior sandbox artifacts. Decision: `split_targets_separable_but_source_biased_no_runtime`. Next step should be architecture review or clean sequence-control collection before any runtime work.
- `stage7_selected_path_architecture_review_v0` closes the selected-path runtime follow-up with `runtime_no_go_architecture_review_required`. The next allowed slice is a non-causal clean-control collection plan; runtime arbiter/selector work remains blocked.
- `stage7_clean_control_collection_plan_v0` defines the next evidence path: classify Stage 7 artifacts by clean/default-off versus repair-sandbox source, then recover clean h40 post-box controls before any runtime review. Next allowed slice: `implement_replay_free_clean_artifact_manifest`.
- `stage7_clean_artifact_manifest_v0` classifies existing Stage 7 artifacts for clean-control recovery. It found clean current-profile/default-off candidates in addition to repair-sandbox-sourced artifacts; next step is replay-free clean sequence-control recovery from the manifest candidates before any new label job.
- `stage7_clean_sequence_control_recovery_v0` recovers `10` replay-free clean controls from manifest-approved artifacts: `2` mate controls and `8` h40 max-plies hard negatives. The hard-negative requirement is met, but clean success controls remain insufficient (`2/5`). Decision: `clean_sequence_controls_insufficient`; next step is either a bounded clean h40 label job or architecture review, not runtime work.
- `stage7_clean_h40_label_manifest_v0` defines one bounded current-defaults label job (`10` samples, seed `17`, h40, no Stage 7 repair flags) to fill the remaining clean success-control gap. Decision: `bounded_clean_h40_label_manifest_ready`; it is a non-causal data-labeling job only.
- `stage7_clean_h40_label_run_review_v0` reviews that bounded label job. The run produced `3` mate / `7` max_plies with no Stage 7/runtime repair flags, but added `0` novel de-duplicated clean controls to the recovery set. Decision: `bounded_label_run_no_novel_clean_success_controls`; next step is review sampling diversity or the architecture boundary before more label jobs.
- `stage7_clean_control_sampling_review_v0` concludes clean success-control collection is currently blocked by sampling overlap: `2/5` clean success controls remain available despite the bounded h40 run producing mates. Decision: `clean_success_collection_blocked_by_sampling_overlap`; recommended next step is architecture review before more Stage 7 clean labels.
- `stage7_clean_control_architecture_review_v0` pauses the Stage 7 clean-control collection branch. It recommends returning to broader KRK strategy/sequence architecture review with Stage 7 as a held-out challenge, rather than running more unreviewed Stage 7 labels or runtime selector tests.
- `krk_strategy_sequence_architecture_review_v0` reframes the next work around two separate evidence tracks: strategy ownership and multi-step sequence policy. It keeps Stage 7 held out and recommends a bounded `krk_strategy_sequence_evidence_plan_v0` before any further runtime selector work.
- `krk_strategy_sequence_evidence_plan_v0` defines the next bounded non-causal evidence path: replay-free inventory first, then reviewed manifests only if gaps remain. Tracks are `strategy_ownership`, `sequence_policy`, and `curriculum_boundary`; Stage 7 remains held-out/evaluation-only.
- `krk_strategy_sequence_inventory_v0` completes the replay-free inventory. Strategy-ownership has some signal, but the state-holdout probe remains not ready and sequence-policy still has a clean success-control gap. Decision: `replay_free_inventory_complete_sequence_gap_blocks_runtime`; runtime work remains blocked.
- `stage7_curriculum_boundary_decision_v0` records the architecture decision to stop treating Stage 7 as a standalone problem to crack. `box_shrink` is now local evidence / handoff trigger / phase-boundary signal; Stage 7 rows may be used as held-out challenge evidence, not as training rows or promotion criteria.
- `krk_control_plane_stage7_boundary_refresh_v0` refreshes the broader control-plane strategy artifacts to honor that decision: Stage 7 contributes `7` held-out boundary frames and `0` strategy-ready training frames; protected Stage 4/5/6 provide `24` strategy-arbitration benchmark frames.
- After the refresh, `krk_control_plane_strategy_arbitration_baseline_v1` is computed only over protected Stage 4/5/6 strategy benchmark frames (`24` total). It still reports `strategy_arbitration_promising`, but remains non-causal and too small for runtime promotion.
- `krk_protected_max_only_frame_review_v0` shows the next broader bottleneck: `12/24` protected strategy frames have a labeled mate provider available, while `12/24` have only labeled max-plies provider proposals. The selector cannot solve missing-provider/capacity/label-coverage gaps; next step is a protected missing-provider capacity audit, not selector tuning.
- `krk_protected_missing_provider_capacity_audit_plan_v0` defines a non-causal reviewed-label plan for that bottleneck: `16` h40 forced-provider jobs across `6` protected max-only frames, with `0` Stage 7 jobs. It does not execute labels or authorize runtime behavior.
- `krk_protected_missing_provider_capacity_execution_manifest_v0` binds those jobs to the Stage 6 overlay-composed topology and `handoff_composition_v1`; `krk_protected_missing_provider_capacity_execution_manifest_review_v0` passes with `0` violations and allows only bounded non-causal label execution. Runtime work remains blocked.
- `krk_protected_missing_provider_capacity_labels_v0` executes the reviewed offline labels: `16` protected h40 forced-provider jobs, `11` mate / `5` max_plies, and `0` Stage 7 labels or training rows. This improves protected-control label coverage but remains non-causal; runtime selector/internal-terminal work is still blocked. Next allowed slice: merge these labels and refresh the strategy/sequence inventory.
- `krk_state_local_contrast_labels_v2` now includes the protected missing-provider label artifact as a source, but `krk_protected_missing_provider_label_merge_review_v0` shows all `16` protected labels are unmatched by the current ranked proposal-frame keys. The refreshed selector probe remains `state_local_contrast_signal_not_ready`; the next bottleneck is proposal-frame coverage for protected missing-provider states, not runtime selector tuning.
- `krk_ranked_proposal_frame_protected_provider_coverage_review_v0` confirms the coverage issue: all `16` protected label frames/states are present, but `0/16` forced providers are present in the current proposal frames. This includes `11` converting labels. Next allowed slice: design a non-causal proposal-coverage expansion for protected states; do not implement runtime selection.
- `krk_protected_proposal_coverage_expansion_plan_v0` defines that expansion as non-causal evidence rows only: create `16` protected provider candidate frames from forced labels plus existing state context, with `usable_for_training = false` initially and no runtime selector/topology effect. Next allowed slice: build `krk_protected_provider_coverage_frames_v0` and review whether those rows should remain capacity-only or become a separate training/evaluation channel.
- `krk_protected_provider_coverage_frames_v0` materializes those `16` rows as non-causal capacity evidence (`11` positive_capacity / `5` negative_capacity), with `0` Stage 7 rows, `0` training rows, and `0` runtime proposal rows. Next allowed slice: review capacity-frame training semantics before any selector use.
- `krk_protected_provider_capacity_frame_training_semantics_review_v0` blocks direct selector training from those rows. Forced-provider capacity is useful proposal/candidate-generation evidence, but it is not a runtime-proposal or ownership label. Next allowed slice: design a non-causal candidate-generator coverage audit.
- `krk_candidate_generator_coverage_audit_v0` confirms the candidate-generation recall gap: current proposal frames have `0.0` recall for `11` protected positive-capacity provider labels. Selector training remains blocked; next allowed slice is a non-causal validated-provider candidate-set audit.
- `krk_validated_provider_candidate_set_audit_v0` shows a validated-provider candidate-set expansion would recover the missing positive-capacity providers, but also includes `5` negative-capacity providers. Candidate generation and strategy selection must remain separate evidence tracks. Next allowed slice: a two-stage candidate-generation/selection design review, not runtime work.
- `krk_two_stage_candidate_selection_review_v0` records that split explicitly. Stage 1 should optimize candidate recall over validated providers; Stage 2 should select/suppress using separated label semantics. No runtime generator, selector training, Stage 7 promotion, or Stage 8 training is authorized. Next allowed slice: plan a non-causal two-stage benchmark.
- `krk_two_stage_candidate_selection_benchmark_plan_v0` defines that benchmark: candidate generation measured by protected positive-capacity recall and negative-capacity inclusion; strategy selection measured separately with selected-playout, runtime-proposal, and forced-capacity channels kept distinct. Next allowed slice: build the non-causal benchmark artifact; runtime work remains blocked.
- `krk_two_stage_candidate_selection_benchmark_v0` shows the validated-provider candidate set fixes positive-capacity recall (`1.0` versus `0.0` for current proposal frames), but selection remains not ready because the current selector evidence has poor negative suppression. Next work should improve selector label balance or candidate scoring non-causally; runtime remains blocked.
- `krk_selector_negative_suppression_evidence_v0` confirms the selector-side bottleneck: only `3` protected training negatives exist, all from one Stage 6 state and one provider family; all training normalized scores are `1.0`; the best offline rule produces `3` false positives / `0` true negatives. Directed next fix class: non-causal negative-balance and candidate-scoring feature work before any runtime selector.
- `krk_capacity_geometry_feature_audit_v0` adds simple visible geometry for protected capacity labels. It is diagnostic but not sufficient: all rows have black king edge distance `0`, positives and negatives share provider families, and simple king/rook distance deltas do not cleanly separate labels. Next allowed slice: run a non-causal geometry-augmented selector feature benchmark.
- `krk_geometry_augmented_selector_feature_probe_v0` confirms simple geometry features are insufficient on current evidence: all tested feature sets still have `0.0` negative suppression over protected capacity labels. Next work should collect or design more protected hard-negative evidence and explicit negative label semantics before runtime.
- `krk_selector_directed_fix_review_v0` consolidates the evidence and rejects runtime selector/generator work, forced-capacity-as-direct-positive training, simple-geometry-only fixes, and returning to Stage 7 patching. Recommended fix class: design a non-causal hard-negative selector target dataset with separated label semantics and geometry/post-move features.
- `krk_hard_negative_selector_target_dataset_v0` materializes that dataset: `16` protected non-causal target candidates, including `5` `hard_negative_capacity` rows and `11` `positive_capacity_context` rows, with `0` Stage 7 rows and `0` training rows. Next allowed slice: review hard-negative target training semantics.
- `krk_hard_negative_selector_target_training_semantics_review_v0` approves those rows for offline benchmarking only. Runtime work and selector training remain blocked. Next allowed slice: `run_hard_negative_selector_feature_ablation_v0`.
- `krk_hard_negative_selector_feature_ablation_v0` runs that offline benchmark. All tested simple feature sets still produce `0.0` negative suppression; the best result predicts all `5` hard negatives as positive. Directed next step: collect more balanced protected hard negatives before runtime work or selector training.
- `krk_balanced_hard_negative_label_plan_v0` / `krk_balanced_hard_negative_execution_manifest_v0` / review define a bounded protected h40 label expansion: `12` jobs across Stage 4/5/6, `10` states, `0` Stage 7 jobs. The reviewed run `krk_balanced_hard_negative_labels_v0` produced `9` mate / `3` max_plies labels, improving protected hard-negative diversity without changing runtime behavior.
- `krk_hard_negative_selector_target_dataset_v1` merges the new labels into the selector target evidence: `28` rows, `20` positive-capacity contexts, `8` hard-negative capacity contexts, `12` states, `4` hard-negative states, and `0` Stage 7 rows/training rows. `krk_hard_negative_selector_feature_ablation_v1` improves negative suppression only to `0.125` and remains underpowered; runtime selector work and selector training remain blocked. The next step should be either another reviewed protected hard-negative evidence slice or a label-semantics/objective review, not runtime behavior.
- A second bounded protected hard-negative pass (`krk_balanced_hard_negative_labels_v1`) added `12` more reviewed h40 labels (`11` mate / `1` max_plies) with `0` Stage 7 labels. `krk_hard_negative_selector_target_dataset_v2` now has `40` protected rows (`31` positive-capacity, `9` hard-negative-capacity), `14` states, and `0` Stage 7 rows/training rows. `krk_hard_negative_selector_feature_ablation_v2` gives the first nonzero but still weak signal: best negative suppression `0.222` with positive recall `1.0`, still underpowered. `krk_balanced_hard_negative_evidence_review_v0` recommends stopping blind label farming and reviewing label semantics or stronger selector features before any training/runtime work.
- `krk_hard_negative_label_semantics_review_v1` confirms these rows are forced-provider capacity labels, not direct runtime ownership labels: positives mean a provider can participate when forced, and negatives mean that forced path failed under h40, not that the provider should be globally suppressed. `krk_stronger_selector_feature_review_v0` finds a stronger non-causal capacity-risk signal: `piece_motion@0.5` reaches negative suppression `0.778` with positive recall `0.903`, improving over v2. This is review-ready evidence for capacity-risk features, but selector training/runtime work remains blocked until architecture review separates candidate capacity, ownership selection, and safe-owner preservation objectives.
- `krk_split_selector_objective_dataset_v0` fixes that semantics issue by splitting forced-provider evidence into four non-causal channels: capacity recall (`31` rows), capacity risk (`40` rows), safe preservation (`31` rows), and an explicit missing ownership-selection channel. `krk_split_selector_objective_readiness_v0` keeps selector training/runtime blocked: capacity-risk features are promising diagnostics, but ownership-selection labels must be collected or recovered from normal-routing/paired-selection evidence before any selector training or runtime test.
- `krk_ownership_selection_label_dataset_v0` recovers normal-routing ownership-selection labels replay-free from existing selected-playout evidence: `14` deduplicated protected rows (`9` selected-owner converted, `5` selected-owner failed) across Stage 4/5/6, with `0` Stage 7 rows. `krk_split_selector_objective_dataset_v1` replaces the missing ownership channel with these labels. `krk_ownership_selection_feature_probe_v0` is promising but underpowered (`raw_score_bucket@0.5`: negative suppression `0.6`, positive recall `1.0`). `krk_split_selector_objective_readiness_v1` records the blocker as reduced but not gone: ownership labels are available, but more normal-routing ownership labels or explicit architecture review are needed before selector training/runtime.
- Bounded selected-provider diversity ownership labels (`krk_selected_provider_diversity_ownership_labels_v0`) added protected normal-routing h40 evidence from `20` jobs: `16` selected-owner converted and `4` selected-owner failed, all currently selected by `krk.stage0_basin`. `krk_ownership_selection_label_dataset_v1` expands the deduplicated ownership set to `34` protected rows (`25` converted / `9` failed), with `0` Stage 7 rows and `0` selector-training rows. The v1/v2 ownership probe remains underpowered and not runtime-ready: best leave-state-out negative suppression is `0.556`, positive recall is `0.56`, and selector training/runtime remain blocked.
- A second fresh-seed diversity label slice (`krk_selected_provider_diversity_ownership_labels_v1`) produced `18` additional labels (`15` converted / `3` failed), but these were duplicate state/provider keys after deduplication and did not expand the ownership dataset beyond `34` rows. This is a sampling-overlap signal, not a reason for blind label farming. Next selector work should review sampling/source diversity and ownership-feature semantics before any runtime selector or candidate generator.
- `krk_ownership_selection_context_dataset_v0` joins those `34` ownership rows to replay-free FEN/selected-move geometry context (`34/34` exact joins). `krk_ownership_selection_context_feature_probe_v0` shows context helps safe-owner preservation in a balanced view (`provider_edge_support@0.75`: positive recall `0.88`, negative suppression `0.444`) but does not meet runtime-review thresholds. `krk_ownership_context_feature_review_v0` keeps selector/runtime work blocked and recommends source/provider diversity review or non-Stage7 normal-routing ownership labels with non-`stage0_basin` selected providers.
- `krk_ownership_selection_label_dataset_v3` recovers one supplemental non-`stage0_basin` selected-owner label (`fence_established`, failed) from selected-playout groups where the actual selected owner lacked a target row. `krk_ownership_selection_context_feature_probe_v1` improves the balanced context result to positive recall `0.88` and negative suppression `0.5`, while the max-suppression result reaches `0.7` at low recall `0.56`. Runtime remains blocked because no probe simultaneously clears preservation and suppression thresholds, and provider diversity is still too narrow (`31/35` rows are `stage0_basin`).
- `krk_ownership_source_diversity_review_v0` identifies the current evidence bottleneck precisely: replay-free artifacts contain non-`stage0_basin` selected owners, but the direct ownership dataset has only `4/35` non-stage0 rows. Random diversity sampling has already overlapped heavily. The next improvement should be a targeted non-stage0 ownership-label manifest or a routing-profile dominance review, not runtime selector work or more blind label farming.
- `krk_targeted_non_stage0_ownership_labels_v0` tested the source-diversity blocker directly on four historical non-`stage0_basin` owner states. Current `handoff_composition_v1` preserved all four non-stage0 owners (`3` `edge_trap_close`, `1` `fence_established`) with no collapse to `stage0_basin`; results were `3` mate / `1` max_plies. This means non-stage0 ownership evidence is recoverable and the earlier blocker was label/source coverage rather than current-profile inability to select non-stage0 providers.
- `krk_ownership_selection_label_dataset_v4` refreshes those four keys with bounded current-profile h40 labels, changing two stale labels and yielding `35` protected ownership rows (`27` converted / `8` failed, `0` Stage 7 rows). `krk_ownership_selection_context_feature_probe_v2` remains not runtime-ready: best max-suppression result is `0.625` negative suppression with `0.63` positive recall, while the best high-recall result reaches `0.926` positive recall but only `0.25` negative suppression. Next selector work should recover more true ownership negatives or review profile-dominance/source semantics before runtime work.
- `krk_targeted_ownership_negative_labels_v0` then targeted known false-positive risk cells with a six-job protected h40 run (`0` Stage 7 jobs). It added `4` converted and `2` failed current-profile ownership labels. `krk_ownership_selection_label_dataset_v5` now has `41` protected rows (`31` converted / `10` failed), but `krk_ownership_selection_context_feature_probe_v3` still fails runtime-review balance: best suppression is `0.6` with recall `0.58`, while best high-recall suppression is only `0.2`. Runtime selector work remains blocked; the next step is architecture review or a more principled ownership-negative objective, not further blind label collection.
- `krk_ownership_objective_architecture_review_v0` closes the current ownership-evidence branch with `ownership_objective_requires_state_local_pairing_review`. The issue is no longer just label count: global row classification cannot both preserve safe owners and suppress unsafe owners on the current sparse evidence. The next principled design should be a non-causal state-local/paired ownership objective that compares candidate owners within the same state/control context. No runtime selector, selector training, Stage 7 promotion, or Stage 8 training is authorized.
- `krk_state_local_paired_ownership_objective_plan_v0` defines that next objective as design-only. It separates same-state owner comparison, safe-preservation, forced-capacity, selected-playout, and abstention evidence. The next allowed implementation slice is a replay-free state-local pair inventory; it still does not authorize runtime behavior or selector training.
- `krk_state_local_paired_ownership_inventory_v0` materializes the first replay-free pair inventory from selected-owner labels plus protected forced-capacity alternatives. It has `15` protected pairs across `6` states, including `7` strong same-state conflicts and `0` Stage 7 rows. This is useful but below the plan requirements (`30` protected pairs and `8` same-state conflicts), so paired-objective benchmarking/training remains blocked pending more same-state conflict evidence or a reviewed inventory expansion.
- `krk_state_local_paired_ownership_work_package_v0` implements the paired-ownership work package constraints. `krk_state_local_paired_ownership_inventory_v1` expands replay-free evidence across protected capacity/contrast artifacts and meets thresholds without a new h40 run: `40` pairs, `9` strong same-state conflicts, `7` selected-failure-with-alternative-success cases, `23` safe-preservation pairs, and `0` Stage 7 rows. `krk_state_local_paired_ownership_probe_v0` shows useful but insufficient signal: best balanced result has prefer-capacity recall `0.857`, selected-preservation recall `0.76`, strong-conflict accuracy `0.889`, but safe-preservation recall only `0.739`. `krk_state_local_paired_ownership_review_v0` therefore records `feature_model_insufficient`; runtime selector work remains blocked and the next safe direction is stronger safe-preservation features/pair interactions, not more broad labels.
- `krk_state_local_paired_ownership_error_audit_v0` finds all v0 false positives are safe-preservation cases where the selected owner already converted but the model preferred a forced-capacity alternative. `krk_state_local_paired_ownership_probe_v1` validates the corrected semantics: safe-preservation/conflict-only semantic gates reach `1.0` on prefer-capacity recall, selected-preservation recall, safe-preservation recall, and strong-conflict accuracy. However, those passing models rely on offline outcome/evidence-channel labels and are not directly runtime-feature eligible. `krk_state_local_paired_selector_runtime_review_packet_v0` is therefore review-ready with a translation blocker: implementation is not authorized until visible runtime proxies for selected-owner failure risk and safe-preservation confidence are explicitly designed and approved.
- `krk_state_local_paired_runtime_proxy_design_v0` defines two non-causal visible proxy candidates: `terminal.krk.selected_owner_failure_risk_proxy` and `terminal.krk.safe_preservation_confidence_proxy`. The replay-free proxy probe keeps runtime-visible candidate features separate from lab/outcome labels. Result: safe-preservation confidence is easy to approximate conservatively (`recall=1.0`, precision `0.825`), but selected-owner failure-risk recall from visible proxies is `0.0` while the forbidden offline semantic ceiling remains `1.0`. Runtime selector work remains blocked; the next required architecture work is better visible selected-owner failure-risk evidence, not implementation.
- `krk_selected_owner_failure_risk_visible_terms_v0` extracts a non-causal visible proxy candidate for the selected-owner failure-risk blocker. On the current protected paired dataset, `selected_owner_failure_risk_proxy_v0 = stage0_vs_edge_trap_selected_king_stalls_box OR edge_trap_drive_context_rook_expands_box` reaches precision `1.0`, recall `1.0`, and safe-preservation recall `1.0`. This is promising but not runtime-ready: it was discovered on the same dataset it fits and requires a visible competing-provider proposal source plus independent protected-pair validation before any runtime-review packet.
- `krk_selected_owner_failure_risk_proxy_independent_validation_v0` runs that independent protected-pair validation (`8` jobs, Stage 4/5/6 only, `0` Stage 7 rows). The proxy fails out-of-sample: precision `0.0`, recall `0.0`, safe-preservation recall `0.429`. The only true failure-risk case was missed, and four proxy-positive cases were safe selected-owner conversions. No runtime-review packet is produced. Current conclusion: one-ply selected move-shape proxies are insufficient for selected-owner failure risk; the next step should be visible competing-proposal/progress-window evidence design or an architecture review, not runtime selector implementation.
- `krk_selected_owner_failure_risk_proxy_blocker_review_v0` formally closes the failed v0 proxy path: the discovery-fit one-ply move-shape proxy is rejected as overfit, runtime-review remains blocked, and the next allowed evidence slice is non-causal v1 evidence from visible competing-provider proposals and selected-owner progress-window failure signals.
- `krk_selected_owner_failure_risk_evidence_v1` / `krk_selected_owner_failure_risk_proxy_probe_v1` split those evidence tracks. Live competing-provider proposal evidence remains sparse (`5/48` rows), while selected-owner progress-window traces exist for a small subset (`6/48`). The conservative v1 proxy passes independent protected validation (`precision=1.0`, `recall=1.0`, `safe_preservation_recall=1.0`, `8` labels, `0` Stage 7 rows) but all-row performance remains weak (`precision=0.333`, `recall=0.25`) because it is progress-window scoped. `krk_state_local_paired_selector_runtime_proxy_review_packet_v1` is therefore review-ready only for a default-off progress-window monitor/reconsideration sandbox; it does not authorize implementation or an initial pre-decision selector.
- After explicit runtime-test approval, `sandbox.krk.progress_window_reconsideration_v0` was implemented as a default-off, opt-in, traceable runtime-test scaffold. `krk_progress_window_reconsideration_runtime_smoke_v0` passed default-off equivalence and activated on the intended progress-window failure row, but did not improve the h40 target outcome (`max_plies/40` remained `max_plies/40`). `krk_progress_window_reconsideration_runtime_test_review_v0` records `runtime_test_scaffold_wired_but_policy_insufficient`; do not advance this sandbox to guardrails, scaling, promotion, or default enablement without a new review.

## Hard Invariants

- No hidden Python controller.
- No runtime DTM/tablebase policy.
- No gameplay-time topology mutation.
- `HandoffPacket`, `SkillContractStats`, `ShadowStemCandidate`, `StructuralCandidate`, `GrowthGovernor`, provider-promotion events, and `PlanCapsuleSpec` remain non-causal unless explicitly compiled/promoted into visible topology or exposed through visible SCRIPT/TERMINAL state.
- Any causal runtime influence must cite visible SCRIPT/TERMINAL state, explicit adapter evidence, edge/provider metadata, or promoted topology.
- Preserve M1-M4 plasticity/consolidation semantics.
- Validated providers stay protected/frozen unless a sandbox explicitly says otherwise.
- Later-stage skills should be overlays, not monolithic replacements.
- Runtime defaults must not change during diagnostics or runtime-test sandboxes.
- Reviewed, default-off, reversible runtime sandboxes are allowed only when a runtime-review packet is present and the implementation remains scoped to that packet. Broad selectors, default-policy changes, unreviewed provider penalties/supports, Stage 7 promotion, and Stage 8 training remain blocked.

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

The immediate architecture decision has been updated by:

```text
reports/krk_runtime_sandbox_policy_update_v0.md
reports/krk_runtime_sandbox_policy_update_v0.json
```

Current immediate runtime-test result:

```text
runtime_test_scaffold_wired_but_policy_insufficient
```

The reviewed progress-window sandbox was allowed because `krk_state_local_paired_selector_runtime_proxy_review_packet_v1` was runtime-review-ready for progress-window scope only. The implementation remained default-off, but the smoke did not improve the targeted failure row. Do not run guardrails or scale this sandbox as if validated; the next step is architecture review or a narrower visible alternative-selection design.

After this runtime-test slice, the next architecture decision should choose among:

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

KRK strategy arbiter out-of-sample execution manifest review v0:

- `scripts/review_krk_strategy_arbiter_out_of_sample_execution_manifest.py`
- `reports/krk_strategy_arbiter_out_of_sample_execution_manifest_review_v0.json`
- `reports/krk_strategy_arbiter_out_of_sample_execution_manifest_review_v0.md`

The review validates manifest structure only. It found full Stage 4/5/6 coverage, all required target semantics present on all `12` jobs, no missing topology/checkpoint paths, no invalid jobs, and Stage 7 training rows `0`. Decision: `execution_manifest_review_passed_bounded_label_run_allowed`. The next allowed step is a bounded non-causal h40 label run from the reviewed manifest, stopping if runtime projects to hours. Runtime arbiter, selector sandbox, Stage 7 repair/promotion, and Stage 8 training remain blocked.

KRK strategy arbiter out-of-sample control labels v0:

- `scripts/run_krk_strategy_arbiter_out_of_sample_control_labels.py`
- `reports/krk_strategy_arbiter_out_of_sample_control_labels_v0.json`
- `reports/krk_strategy_arbiter_out_of_sample_control_labels_v0.md`

The bounded non-causal h40 label run completed `12` protected-control jobs in about `126` seconds. Selected playouts were `11` mate / `1` max_plies, and forced-selected-provider playouts were also `11` mate / `1` max_plies. Stage 5 and Stage 6 controls were `4/4` mate; Stage 4 was `3/4` mate with one max_plies. Stage 7 training rows remain `0`. The next allowed step is a replay-free probe of these out-of-sample labels before any selector sandbox review. Runtime arbiter, selector sandbox, Stage 7 repair/promotion, and Stage 8 training remain blocked.

KRK strategy arbiter out-of-sample control probe v0:

- `scripts/probe_krk_strategy_arbiter_out_of_sample_controls.py`
- `reports/krk_strategy_arbiter_out_of_sample_control_probe_v0.json`
- `reports/krk_strategy_arbiter_out_of_sample_control_probe_v0.md`

The replay-free probe finds the new controls mostly confirm protected-stack conversion (`11/12` mate, forced-selected agreement `1.0`) but do not provide enough selector evidence. All `12` selected providers are `krk.stage0_basin`, and labels are imbalanced (`11` mate / `1` max_plies). Decision: `out_of_sample_controls_guardrail_positive_selector_sandbox_blocked`. The next step should be architecture review of selector signal/readiness before any runtime sandbox, not implementation.

KRK strategy arbiter out-of-sample architecture review v0:

- `scripts/summarize_krk_strategy_arbiter_out_of_sample_architecture_review.py`
- `reports/krk_strategy_arbiter_out_of_sample_architecture_review_v0.json`
- `reports/krk_strategy_arbiter_out_of_sample_architecture_review_v0.md`

The review closes the current selector-readiness branch. It concludes the protected stack mostly converts on bounded out-of-sample controls, but the evidence does not establish a general strategy arbiter because selected-provider labels are class-imbalanced and dominated by `krk.stage0_basin`. Decision: `selector_sandbox_blocked_out_of_sample_controls_not_selector_diverse`. Next options are design-only `selector_readiness_v2` or a non-causal strategy-owner contrast dataset; runtime arbiter, selector sandbox, Stage 7 repair/promotion, and Stage 8 training remain blocked.

KRK selector readiness v2 plan:

- `scripts/summarize_krk_selector_readiness_v2_plan.py`
- `reports/krk_selector_readiness_v2_plan.json`
- `reports/krk_selector_readiness_v2_plan.md`

The v2 readiness plan blocks future selector sandbox review unless evidence has label balance, provider diversity, explicit label-semantics splits, Stage 4/5/6 protected coverage, Stage 7 held-out status, and selector improvement over non-selector baselines. Current blockers are class imbalance, selected-provider dominance, insufficient non-stage0 conversion-positive ownership examples, and missing same-move compatibility execution. Decision: `selector_readiness_v2_defined_runtime_sandbox_blocked`. The next allowed evidence slice is a non-causal `strategy_owner_contrast_dataset_v0`.

KRK strategy-owner contrast dataset v0:

- `scripts/build_krk_strategy_owner_contrast_dataset.py`
- `reports/krk_strategy_owner_contrast_dataset_v0.json`
- `reports/krk_strategy_owner_contrast_dataset_v0.md`

After merging the bounded contrast-control labels, the dataset contains `13` provider-contrast rows: `9` protected training-eligible rows and `4` Stage 7 held-out challenge rows. Stage 7 remains excluded from training (`stage7_training_rows = 0`). Protected controls now include `6` non-stage0-positive rows and positive provider families across `drive_to_edge`, `edge_trap`, and `fence_established`. The dataset is ready for a non-causal strategy-owner contrast probe, but selector sandbox remains blocked because selected-provider family diversity is still insufficient. Decision: `strategy_owner_contrast_dataset_ready_for_non_causal_probe_selector_sandbox_blocked`.

KRK strategy-owner contrast label plan v0:

- `scripts/plan_krk_strategy_owner_contrast_labels.py`
- `reports/krk_strategy_owner_contrast_label_plan_v0.json`
- `reports/krk_strategy_owner_contrast_label_plan_v0.md`

The bounded non-causal plan proposes `12` protected forced-provider contrast label jobs: `4` Stage 4, `4` Stage 5, and `4` Stage 6, with `0` Stage 7 jobs. It does not run labels. Execution remains review/binding-gated because Stage 4 forced-provider binding must be explicit and visible before any h40 label run. Decision: `protected_strategy_owner_contrast_label_plan_defined_execution_review_required`. Runtime arbiter, selector sandbox, Stage 7 repair/promotion, and Stage 8 training remain blocked.

KRK strategy-owner contrast label plan review v0:

- `scripts/review_krk_strategy_owner_contrast_label_plan.py`
- `reports/krk_strategy_owner_contrast_label_plan_review_v0.json`
- `reports/krk_strategy_owner_contrast_label_plan_review_v0.md`

The review passes the bounded label plan with `0` violations and confirms it may proceed only to an explicit execution-binding manifest. Labels are still not allowed until binding is reviewed. Required binding properties are explicit topology/profile per job, visible Stage 4 forced-provider skill matching, frozen Stage 5/6 provider metadata preservation, provider versions/checkpoints, and a separate binding-manifest review. Decision: `contrast_label_plan_review_passed_binding_required`.

KRK strategy-owner contrast execution manifest v0:

- `scripts/bind_krk_strategy_owner_contrast_labels.py`
- `reports/krk_strategy_owner_contrast_execution_manifest_v0.json`
- `reports/krk_strategy_owner_contrast_execution_manifest_v0.md`

The non-causal execution manifest binds all `12` reviewed jobs to `handoff_composition_v1` / `stage6_overlay_composed_v1` with explicit provider versions and checkpoints. All target provider skill IDs are present in the topology, missing path count is `0`, and Stage 7 jobs remain `0`. Labels are still not allowed until the manifest is reviewed. Decision: `contrast_execution_manifest_bound_review_required`.

KRK strategy-owner contrast execution manifest review v0:

- `scripts/review_krk_strategy_owner_contrast_execution_manifest.py`
- `reports/krk_strategy_owner_contrast_execution_manifest_review_v0.json`
- `reports/krk_strategy_owner_contrast_execution_manifest_review_v0.md`

The manifest review passes with `0` violations. It authorizes only a bounded offline h40 label run with `12` jobs, failure traces only, diagnostic caches, and no Stage 7 jobs. Runtime arbiter, selector sandbox, Stage 7 repair/promotion, and Stage 8 training remain blocked. Decision: `contrast_execution_manifest_review_passed_labels_allowed`.

KRK strategy-owner contrast control labels v0:

- `scripts/run_krk_strategy_owner_contrast_control_labels.py`
- `reports/krk_strategy_owner_contrast_control_labels_v0.json`
- `reports/krk_strategy_owner_contrast_control_labels_v0.md`

The bounded offline label run completed `12` protected jobs in `35.217` seconds. Results: `10` mate / `2` max_plies. Stage 5 and Stage 6 contrast jobs were all mate; Stage 4 produced `2` mate / `2` max_plies. Stage 7 labels remain `0`. These are non-causal outcome labels only. The next step is to merge the labels into the strategy-owner contrast dataset and reassess selector readiness; runtime arbiter, selector sandbox, Stage 7 repair/promotion, and Stage 8 training remain blocked.

KRK strategy-owner contrast probe v0:

- `scripts/probe_krk_strategy_owner_contrast_dataset.py`
- `reports/krk_strategy_owner_contrast_probe_v0.json`
- `reports/krk_strategy_owner_contrast_probe_v0.md`

The non-causal probe finds protected conversion-positive provider diversity and label balance are now present. It also confirms selector sandbox remains blocked: selected-provider evidence is still not diverse (`edge_trap` only), and held-out Stage 7 retains unresolved all-negative rows. Decision: `strategy_owner_contrast_signal_present_selector_sandbox_blocked`. The next step should be architecture review of selector readiness after contrast evidence, not runtime arbiter implementation.

KRK selector readiness after contrast probe review v0:

- `scripts/summarize_krk_selector_readiness_after_contrast_probe.py`
- `reports/krk_selector_readiness_after_contrast_probe_review_v0.json`
- `reports/krk_selector_readiness_after_contrast_probe_review_v0.md`

The architecture review accepts that protected strategy-owner contrast signal is now present, but it still blocks selector sandbox/runtime arbiter work because selected-provider evidence is not diverse and Stage 7 held-out rows remain unresolved challenge cases. Decision: `selector_sandbox_blocked_selected_provider_evidence_missing`. The next allowed options are design-only selected-provider diversity evidence planning, a non-causal strategy-owner feature probe v2, or pausing runtime selector work.

KRK selected-provider diversity evidence plan v0:

- `scripts/plan_krk_selected_provider_diversity_evidence.py`
- `reports/krk_selected_provider_diversity_evidence_plan_v0.json`
- `reports/krk_selected_provider_diversity_evidence_plan_v0.md`

The design-only plan scopes the remaining selector-readiness gap: find protected Stage 4/5/6 states where normal arbitration selects diverse validated provider families, with Stage 7 training rows still `0`. It permits only a replay-free scan first; any bounded sampling or label execution still requires a separate manifest and review. Decision: `selected_provider_diversity_evidence_plan_defined`.

KRK selected-provider diversity replay-free scan v0:

- `scripts/scan_krk_selected_provider_diversity_replay_free.py`
- `reports/krk_selected_provider_diversity_replay_free_scan_v0.json`
- `reports/krk_selected_provider_diversity_replay_free_scan_v0.md`

The replay-free scan confirms the remaining gap cannot be closed from existing selected-provider records. It found `23` protected selected records across Stage 4/5/6 and `0` Stage 7 records, but only two selected provider families: `stage0_basin` (`18`) and `edge_trap` (`5`), with dominance `0.7826`. Decision: `selected_provider_diversity_replay_free_insufficient`. Any next step would be a bounded protected sampling manifest, not runtime selector work.

KRK selected-provider diversity sampling manifest/review v0:

- `scripts/generate_krk_selected_provider_diversity_sampling_manifest.py`
- `scripts/review_krk_selected_provider_diversity_sampling_manifest.py`
- `reports/krk_selected_provider_diversity_sampling_manifest_v0.json`
- `reports/krk_selected_provider_diversity_sampling_manifest_v0.md`
- `reports/krk_selected_provider_diversity_sampling_manifest_review_v0.json`
- `reports/krk_selected_provider_diversity_sampling_manifest_review_v0.md`

The bounded selection-only manifest contains `20` protected observation jobs across Stage 4/5/6 and `0` Stage 7 jobs. The review passes with `0` violations and authorizes only a selection-observation scan, not playout labels or selector work. Runtime arbiter, selector sandbox, Stage 7 repair/promotion, and Stage 8 training remain blocked.

KRK selected-provider diversity observation scan v0:

- `scripts/run_krk_selected_provider_diversity_observation_scan.py`
- `reports/krk_selected_provider_diversity_observation_scan_v0.json`
- `reports/krk_selected_provider_diversity_observation_scan_v0.md`

The bounded selection-only scan completed `20` protected observations in `7.293` seconds. All `20` selected `krk.stage0_basin`; distinct selected provider families = `1`, dominance = `1.0`, and Stage 7 observations remain `0`. Decision: `selected_provider_diversity_observation_insufficient`. This strengthens the diagnosis that normal arbitration is stage0-dominant on sampled protected controls; runtime arbiter and selector sandbox remain blocked.

KRK selected-provider diversity architecture review v0:

- `scripts/summarize_krk_selected_provider_diversity_architecture_review.py`
- `reports/krk_selected_provider_diversity_architecture_review_v0.json`
- `reports/krk_selected_provider_diversity_architecture_review_v0.md`

The architecture review concludes the v2 selected-provider diversity requirement should be reframed. Current normal arbitration selects `stage0_basin` too dominantly to provide diverse selected-provider training evidence, while forced/proposal contrast already shows conversion-positive provider diversity. Decision: `selected_provider_diversity_requirement_should_be_reframed`. Next step is to define selector-readiness v3 around proposal diversity, forced/compatible conversion-positive provider diversity, held-out Stage 7 preservation, default-off equivalence, and guardrail preservation. Runtime arbiter and selector sandbox remain blocked until v3 criteria and review.

KRK selector readiness v3 plan:

- `scripts/summarize_krk_selector_readiness_v3_plan.py`
- `reports/krk_selector_readiness_v3_plan.json`
- `reports/krk_selector_readiness_v3_plan.md`

The v3 plan reframes selector readiness after selected-provider sampling showed the current raw arbiter is stage0-dominant. It treats current selected-provider diversity as diagnostic-only rather than a sandbox hard blocker, because requiring the current raw arbiter to already select diverse providers blocks the mechanism intended to correct that dominance. Proposal-family diversity, conversion-positive provider-family diversity, label balance, protected Stage 4/5/6 coverage, and Stage 7 held-out boundary all pass. Decision: `selector_readiness_v3_sandbox_design_review_allowed`. Runtime arbiter and selector sandbox are still not implemented or allowed; the next permitted step is only a default-off strategy-arbiter sandbox design review.

KRK strategy arbiter default-off design review v1:

- `scripts/summarize_krk_strategy_arbiter_default_off_design_review_v1.py`
- `reports/krk_strategy_arbiter_default_off_design_review_v1.json`
- `reports/krk_strategy_arbiter_default_off_design_review_v1.md`

The design review converts selector-readiness v3 into a future sandbox contract for external review only. It defines default-off requirements, allowed/forbidden inputs and outputs, default-off equivalence checks, enabled-smoke constraints, and promotion gates. Decision: `default_off_strategy_arbiter_design_ready_for_external_review`. Runtime arbiter implementation, selector sandbox implementation, Stage 7 repair/promotion, Stage 8 training, runtime DTM/tablebase, and gameplay topology mutation remain blocked.

KRK strategy arbiter runtime review packet v1:

- `scripts/summarize_krk_strategy_arbiter_runtime_review_packet_v1.py`
- `reports/krk_strategy_arbiter_runtime_review_packet_v1.json`
- `reports/krk_strategy_arbiter_runtime_review_packet_v1.md`

The runtime review packet packages the protected-stage status, selector-readiness v3, default-off sandbox design review, and strategy-owner contrast probe into a single external-review decision point. Decision: `runtime_review_packet_ready`. It asks whether to approve a future default-off strategy-arbiter sandbox implementation, request one bounded non-causal evidence slice, or reject the sandbox path for now. Implementation remains blocked until review.

KRK strategy arbiter runtime sandbox smoke v1:

- `scripts/run_krk_strategy_arbiter_runtime_sandbox_smoke_v1.py`
- `reports/krk_strategy_arbiter_runtime_sandbox_smoke_v1.json`
- `reports/krk_strategy_arbiter_runtime_sandbox_smoke_v1.md`

The first approved runtime-test slice adds a default-off KRK strategy-arbiter support sandbox in `scripts/test_krk_landmark_progress.py`. It only applies an explicit bounded support amount to already-materialized eligible provider-family proposals when `--enable-krk-strategy-arbiter-sandbox` and a positive `--krk-strategy-arbiter-support` are provided. It records `krk_strategy_arbiter_sandbox_support.v0` metadata with `direct_request=false` and blocks Stage 7 `box_shrink` challenge contexts by default. Smoke v1 passed flag-present default-off equivalence and observed trace-visible enabled support on a tiny protected `fence_established` sample. Decision: `runtime_sandbox_smoke_passed`; next safe runtime-test step is a tiny protected-control matrix, not Stage 7 repair or promotion.

KRK strategy arbiter protected-control matrix v1:

- `scripts/run_krk_strategy_arbiter_protected_control_matrix_v1.py`
- `reports/krk_strategy_arbiter_protected_control_matrix_v1.json`
- `reports/krk_strategy_arbiter_protected_control_matrix_v1.md`

The first protected runtime-test matrix ran baseline, flag-present default-off, and enabled support `0.05` on one h20 sample each for Stage 4 `edge_trap_wrong_tempo`, Stage 5 `fence_established`, and Stage 6 `drive_to_edge`, with Stage 7 rows still `0`. Default-off equivalence passed for all rows, enabled support was trace-visible (`15` supported proposals total), and there was no no-move/draw/conversion regression relative to baseline. Stage 4 remained max-plies in both baseline and enabled runs, so this did not solve the known Stage 4 h40/h20 caveat; it only confirms the sandbox did not worsen the tiny protected-control matrix. Decision: `protected_control_matrix_passed`.

KRK strategy arbiter Stage 7 holdout lock v1:

- `scripts/run_krk_strategy_arbiter_stage7_holdout_lock_v1.py`
- `reports/krk_strategy_arbiter_stage7_holdout_lock_v1.json`
- `reports/krk_strategy_arbiter_stage7_holdout_lock_v1.md`

The Stage 7 holdout-lock runtime test ran one h20 `box_shrink` sample with sandbox support enabled but `allow_stage7_challenge=false`. The enabled-blocked result matched baseline exactly and support count remained `0`. Decision: `stage7_holdout_lock_passed`. Stage 7 remains held out by default; any explicit Stage 7 challenge test must use a separate review/flag and must not be treated as promotion.

KRK strategy arbiter protected-control matrix v2:

- `scripts/run_krk_strategy_arbiter_protected_control_matrix_v2.py`
- `reports/krk_strategy_arbiter_protected_control_matrix_v2.json`
- `reports/krk_strategy_arbiter_protected_control_matrix_v2.md`

The scaled protected runtime-test matrix ran three h20 samples per protected label (`edge_trap_wrong_tempo`, `fence_established`, `drive_to_edge`) with Stage 7 rows still `0`. Default-off equivalence passed for all rows, enabled support was trace-visible (`45` supported proposals total), and there was no no-move/draw/conversion regression. Outcomes were unchanged: Stage 4 `3/3` mate, Stage 5 `2/3` mate and `1/3` max_plies, Stage 6 `0/3` mate and `3/3` max_plies under this small h20 sample. Decision: `protected_control_matrix_v2_passed`. The result supports sandbox safety at small scale, but not effectiveness or promotion.

KRK strategy arbiter Stage 7 challenge probe v1:

- `scripts/run_krk_strategy_arbiter_stage7_challenge_probe_v1.py`
- `reports/krk_strategy_arbiter_stage7_challenge_probe_v1.json`
- `reports/krk_strategy_arbiter_stage7_challenge_probe_v1.md`

The first explicit Stage 7 challenge runtime-test used three h20 `box_shrink` samples with `allow_stage7_challenge=true` and support `0.05`. It produced trace-visible support (`15` supported proposals) but selected-supported count stayed `0`, conversion stayed `0/3` mate, and shadow candidates did not change. Decision: `stage7_challenge_probe_no_regression`. This does not justify Stage 7 promotion or tuning; it shows the current bounded support is too weak or not aligned enough to affect Stage 7 ownership.

KRK strategy arbiter support sensitivity v1:

- `scripts/run_krk_strategy_arbiter_support_sensitivity_v1.py`
- `reports/krk_strategy_arbiter_support_sensitivity_v1.json`
- `reports/krk_strategy_arbiter_support_sensitivity_v1.md`

The one-ply support sensitivity runtime-test measured support values `0.0`, `0.05`, `1.0`, `5.0`, `20.0`, and `50.0` on protected labels plus the explicit Stage 7 challenge label. Low support up to `5.0` did not change Stage 7 ownership. At high support, protected `drive_to_edge` ownership changed before there was safe Stage 7 evidence. Decision: `support_sensitivity_measured`; recommended next step is `do_not_raise_support_without_arbitration_objective_review`. This blocks simply increasing the additive support bonus as the next repair.

KRK strategy arbiter runtime-test review v2:

- `scripts/summarize_krk_strategy_arbiter_runtime_test_review_v2.py`
- `reports/krk_strategy_arbiter_runtime_test_review_v2.json`
- `reports/krk_strategy_arbiter_runtime_test_review_v2.md`

The runtime-test review packages the default-off smoke, protected-control matrix, Stage 7 holdout lock, explicit Stage 7 challenge probe, and support sensitivity. Decision: `runtime_sandbox_safe_but_additive_support_not_ready_to_scale`. The sandbox contract and trace evidence are working, but additive support is not effective for Stage 7 at low support and is not safe to scale blindly because high support can perturb protected one-ply ownership. Next step should be non-causal arbitration-objective review before more runtime tests.

KRK arbitration objective review v1:

- `scripts/summarize_krk_arbitration_objective_review_v1.py`
- `reports/krk_arbitration_objective_review_v1.json`
- `reports/krk_arbitration_objective_review_v1.md`

The objective review rejects broad additive support as the next runtime objective. Provider provenance/maturity remains a promising non-causal feature family, while selected-playout labels alone remain insufficient because the raw arbiter is stage0-dominant. Decision: `additive_support_objective_rejected_design_normalized_selector_objective`. The next allowed class is design-only: a normalized contrastive strategy-selector objective using StrategyProposalFrame-compatible proposals, provider-local rank/normalized score, separated label semantics, protected Stage 4/5/6 controls, and Stage 7 held out as challenge cases.

KRK normalized strategy selector objective v1:

- `scripts/summarize_krk_normalized_strategy_selector_objective_v1.py`
- `reports/krk_normalized_strategy_selector_objective_v1.json`
- `reports/krk_normalized_strategy_selector_objective_v1.md`

The normalized selector objective design defines a non-causal offline objective contract. It separates selected-playout, forced-provider, same-move compatibility, and Stage 7 held-out challenge labels; requires StrategyProposalFrame-compatible proposal rows, provider provenance/maturity, provider-local rank, and normalized score; and explicitly blocks runtime support, Stage 7 repair, promotion, Stage 8, runtime DTM/tablebase, and topology mutation. Decision: `normalized_selector_objective_design_ready_for_offline_probe`; the next permitted step is an offline normalized selector objective probe, not a runtime test.

KRK normalized strategy selector objective probe v1:

- `scripts/probe_krk_normalized_strategy_selector_objective_v1.py`
- `reports/krk_normalized_strategy_selector_objective_probe_v1.json`
- `reports/krk_normalized_strategy_selector_objective_probe_v1.md`

The offline probe replays existing balanced/provenance labels without new playouts. Provenance-style baselines remain useful (`0.889` balanced LOO accuracy for `family_maturity_target_kind`). The provenance dataset already exposes equivalent rank/score fields (`target_provider_best_rank`, `target_provider_best_raw_score`), allowing a normalized proxy probe: `family_rank_score_bucket` reaches `0.889` provenance LOO accuracy with no Stage 7 training leakage. Balanced rows still lack rank/score fields, and the dataset remains underpowered, so this is not runtime-ready. Decision: `normalized_objective_probe_underpowered_fields_available`; next step is review before any runtime test.

KRK normalized selector probe review v1:

- `scripts/summarize_krk_normalized_selector_probe_review_v1.py`
- `reports/krk_normalized_selector_probe_review_v1.json`
- `reports/krk_normalized_selector_probe_review_v1.md`

The review finds a real but insufficient normalized-selector signal: `family_rank_score_bucket` improves over the family/maturity provenance baseline by about `0.093` accuracy on existing provenance rows. It is still not runtime-ready because the dataset is small, balanced rows lack rank/score fields, and Stage 7 remains held out. Decision: `normalized_selector_signal_promising_more_ranked_frames_required`; next step is to build ranked StrategyProposalFrame rows for balanced/protected controls before any further runtime test.

KRK ranked StrategyProposalFrame dataset v1:

- `scripts/build_krk_ranked_strategy_proposal_frames_v1.py`
- `reports/krk_ranked_strategy_proposal_frames_v1.json`
- `reports/krk_ranked_strategy_proposal_frames_v1.md`

The replay-free dataset exports existing `StrategyProposalFrame` records from control-plane frames with `provider_local_rank` and `normalized_score`. It contains `87` proposal rows across `22` frames, with `42` non-Stage7 usable context rows and `45` Stage7 challenge rows held out. No row is missing rank or normalized score. Labels are frame-level context only; the export explicitly does not treat every proposal in a mate frame as a positive owner. Decision: `ranked_strategy_proposal_frames_exported`; next step is an offline ranked-frame probe, not a runtime test.

KRK ranked StrategyProposalFrame probe v1:

- `scripts/probe_krk_ranked_strategy_proposal_frames_v1.py`
- `reports/krk_ranked_strategy_proposal_frame_probe_v1.json`
- `reports/krk_ranked_strategy_proposal_frame_probe_v1.md`

The offline probe evaluates ranked proposal context at frame level, not proposal-positive level. It has only `15` non-Stage7 training frames and `7` Stage7 challenge frames, so it remains underpowered. `top_family_raw_bucket` reaches `0.8` LOO accuracy, but negative suppression is only `0.5`; frame-level outcome labels are too coarse to identify the winning proposal inside a state. Decision: `ranked_frames_available_label_semantics_too_coarse`; next step is to derive state-local contrast labels before any runtime selector.

KRK state-local contrast labels/probe v1:

- `scripts/build_krk_state_local_contrast_labels_v1.py`
- `scripts/probe_krk_state_local_contrast_selector_v1.py`
- `reports/krk_state_local_contrast_labels_v1.json`
- `reports/krk_state_local_contrast_labels_v1.md`
- `reports/krk_state_local_contrast_selector_probe_v1.json`
- `reports/krk_state_local_contrast_selector_probe_v1.md`

The replay-free join matched ranked proposal frames to forced-provider labels by state/provider, producing `28` protected contrast rows across `8` states with `13` positive and `15` negative labels and no Stage 7 leakage. The leave-state-out probe is not selector-ready: best accuracy is only `0.464`, and negative suppression is `0.0`, meaning the current simple features do not distinguish failing forced providers under state holdout. Decision: `state_local_contrast_signal_not_ready`; runtime selector tests remain blocked.

KRK runtime selector readiness review v1:

- `scripts/summarize_krk_runtime_selector_readiness_review_v1.py`
- `reports/krk_runtime_selector_readiness_review_v1.json`
- `reports/krk_runtime_selector_readiness_review_v1.md`

The readiness review closes the current runtime-selector evidence branch. Positive results: default-off sandbox mechanics are trace-visible/default-safe, protected runtime tests showed no small-scale regression, Stage 7 is blocked by default, normalized rank/score has a non-causal signal, and ranked proposal frames can be exported replay-free. Blocking results: additive support is unsafe to scale blindly, frame-level labels are too coarse, state-local contrast labels are sparse and fail negative suppression, and Stage 7 remains unresolved/held out. Decision: `runtime_selector_not_ready_collect_better_contrast_labels`; next step is a small diverse state-local contrast label plan, not runtime behavior.

KRK diverse contrast label plan v1:

- `scripts/summarize_krk_diverse_contrast_label_plan_v1.py`
- `reports/krk_diverse_contrast_label_plan_v1.json`
- `reports/krk_diverse_contrast_label_plan_v1.md`

The plan defines the next non-causal evidence slice: at most `8` new states and `24` forced-provider h40 labels across protected Stage 4/5/6 plus Stage 7 challenge evaluation-only rows. It requires provider-local rank/normalized score, separated state-local contrast labels, diagnostic caches, trace failures only, and no runtime DTM/tablebase. Stage 7 rows remain held out and not training. Decision: `diverse_contrast_label_plan_ready`; runtime selector, Stage 7 promotion, and Stage 8 remain blocked.

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
reports/krk_strategy_arbiter_out_of_sample_execution_manifest_review_v0.json
reports/krk_strategy_arbiter_out_of_sample_execution_manifest_review_v0.md
reports/krk_strategy_arbiter_out_of_sample_control_labels_v0.json
reports/krk_strategy_arbiter_out_of_sample_control_labels_v0.md
reports/krk_strategy_arbiter_out_of_sample_control_probe_v0.json
reports/krk_strategy_arbiter_out_of_sample_control_probe_v0.md
reports/krk_strategy_arbiter_out_of_sample_architecture_review_v0.json
reports/krk_strategy_arbiter_out_of_sample_architecture_review_v0.md
reports/krk_selector_readiness_v2_plan.json
reports/krk_selector_readiness_v2_plan.md
reports/krk_strategy_owner_contrast_dataset_v0.json
reports/krk_strategy_owner_contrast_dataset_v0.md
reports/krk_strategy_owner_contrast_label_plan_v0.json
reports/krk_strategy_owner_contrast_label_plan_v0.md
reports/krk_strategy_owner_contrast_label_plan_review_v0.json
reports/krk_strategy_owner_contrast_label_plan_review_v0.md
reports/krk_strategy_owner_contrast_execution_manifest_v0.json
reports/krk_strategy_owner_contrast_execution_manifest_v0.md
reports/krk_strategy_owner_contrast_execution_manifest_review_v0.json
reports/krk_strategy_owner_contrast_execution_manifest_review_v0.md
reports/krk_strategy_owner_contrast_control_labels_v0.json
reports/krk_strategy_owner_contrast_control_labels_v0.md
reports/krk_strategy_owner_contrast_probe_v0.json
reports/krk_strategy_owner_contrast_probe_v0.md
reports/krk_selector_readiness_after_contrast_probe_review_v0.json
reports/krk_selector_readiness_after_contrast_probe_review_v0.md
reports/krk_selected_provider_diversity_evidence_plan_v0.json
reports/krk_selected_provider_diversity_evidence_plan_v0.md
reports/krk_selected_provider_diversity_replay_free_scan_v0.json
reports/krk_selected_provider_diversity_replay_free_scan_v0.md
reports/krk_selected_provider_diversity_sampling_manifest_v0.json
reports/krk_selected_provider_diversity_sampling_manifest_v0.md
reports/krk_selected_provider_diversity_sampling_manifest_review_v0.json
reports/krk_selected_provider_diversity_sampling_manifest_review_v0.md
reports/krk_selected_provider_diversity_observation_scan_v0.json
reports/krk_selected_provider_diversity_observation_scan_v0.md
reports/krk_selected_provider_diversity_architecture_review_v0.json
reports/krk_selected_provider_diversity_architecture_review_v0.md
reports/krk_selector_readiness_v3_plan.json
reports/krk_selector_readiness_v3_plan.md
reports/krk_strategy_arbiter_default_off_design_review_v1.json
reports/krk_strategy_arbiter_default_off_design_review_v1.md
reports/krk_strategy_arbiter_runtime_review_packet_v1.json
reports/krk_strategy_arbiter_runtime_review_packet_v1.md
reports/krk_strategy_arbiter_runtime_sandbox_smoke_v1.json
reports/krk_strategy_arbiter_runtime_sandbox_smoke_v1.md
reports/krk_strategy_arbiter_protected_control_matrix_v1.json
reports/krk_strategy_arbiter_protected_control_matrix_v1.md
reports/krk_strategy_arbiter_stage7_holdout_lock_v1.json
reports/krk_strategy_arbiter_stage7_holdout_lock_v1.md
reports/krk_strategy_arbiter_protected_control_matrix_v2.json
reports/krk_strategy_arbiter_protected_control_matrix_v2.md
reports/krk_strategy_arbiter_stage7_challenge_probe_v1.json
reports/krk_strategy_arbiter_stage7_challenge_probe_v1.md
```

No runtime behavior should change while Stage 7 is paused.
