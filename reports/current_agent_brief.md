# Current Agent Brief

This report is the canonical current-agent brief. The root `current_agent_brief.md`
is only a pointer to this file.

## Active KRK Gate

- Previous approved protected plan-window failure-contrast collection completed with status `collection_complete_underpowered`.
- Collection outputs: `reports/strategy_arbitration/protected_plan_window_failure_contrasts/`.
- Collection result: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_result_v0.json`.
- Follow-up packet: `reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_followup_review_packet_v0.json` with status `blocked_needs_human_approval`.
- Current gate exposes `review_protected_plan_window_failure_contrast_manifest`, not a collection command.
- Additional-collection decision note: `reports/strategy_arbitration/krk_protected_failure_contrast_additional_collection_decision_v1.json`.

## Current Decision

- Selector behavior branch closure v0: `reports/strategy_arbitration/krk_selector_behavior_branch_closure_v0.json` with status `selector_behavior_branch_closed_return_to_control_plane`.
- The behavior-changing selector sandbox is quarantined by `krk_selector_behavior_regression_decision_v0.json` (`selector_behavior_quarantined_due_to_safe_regression`).
- Trace-only selector observability and recommendation artifacts remain useful as non-causal evidence, but they do not authorize provider choice, move choice, scoring, routing, default, or suppression changes.
- Next direction: broader KRK strategy/sequence control plane, candidate generation, plan/sequence policy, and state-local paired ownership evidence; not selector behavior.
- Decision status: `protected_failure_contrast_collection_not_worth_running`.
- The currently reviewed v0 manifest is the already-spent manifest; its six outputs already exist and all are `conversion_positive`.
- The v0 manifest includes Stage 4 rows and does not satisfy the new Stage 5/6-only diversity condition for the conditional follow-up approval.
- The conditional approval for one additional collection was not consumed.
- Do not execute additional protected failure-contrast collection without a fresh reviewed Stage 5/6-only diversity manifest and explicit approval.
- Fresh selector-objective diversity packet: `reports/strategy_arbitration/krk_selector_objective_fresh_diversity_review_packet_v0.json` with status `fresh_stage5_stage6_diversity_collection_review_ready`.
- Fresh selector-objective diversity collection result: `reports/strategy_arbitration/krk_selector_objective_fresh_diversity_collection_v0.json` with status `fresh_stage5_6_selector_objective_collection_complete`.
- The approved collection consumed the fresh Stage 5/6-only packet only; it authorizes no selector training, runtime behavior, Stage 7 promotion, or Stage 8 training.
- Replay-free selector-objective batch gap scan: `reports/strategy_arbitration/krk_selector_objective_batch_gap_scan_v0.json` with status `selector_objective_diversity_improved_replay_free`.
- Selector-objective feature probe v2: `reports/strategy_arbitration/krk_selector_objective_feature_probe_v2.json` with status `selector_objective_feature_probe_v2_review_ready`.
- Selector-objective benchmark v0: `reports/strategy_arbitration/krk_selector_objective_benchmark_v0.json` with status `selector_objective_benchmark_promising_non_causal`.
- Selector-objective benchmark decision v0: `reports/strategy_arbitration/krk_selector_objective_benchmark_decision_v0.json`; implementation remains unauthorized.
- Selector-objective runtime review packet v0: `reports/strategy_arbitration/krk_selector_objective_runtime_review_packet_v0.json` with status `selector_runtime_review_packet_ready`; implementation and runtime sandbox execution remain unauthorized by the packet.

## Verified Invariants

- Selected move/provider deltas, score deltas, and routing deltas remain zero in the previous collection result.
- Runtime behavior changed: false.
- Runtime DTM/tablebase use: false.
- Gameplay-time topology mutation: false.
- Selector training rows, Stage 7 training rows, and runtime authorization rows: zero.
- Stage 7 remains held out/challenge only.
- Stage 7 promotion and Stage 8 training remain blocked.
- M1-M4 semantics remain preserved.
- Capacity labels are not ownership labels.
- Fresh Stage 5/6 selector-objective collection rows: 8 attempted, 8 joined, 76 generated refresh frames, 4 selected-failure visible-positive rows, 4 safe-preservation visible-positive rows.
- Fresh Stage 5/6 selector-objective collection deltas: selected move 0, provider 0, score 0, routing 0, invalid frames 0, baseline refresh frames 0.
- Seed manifest v2 now has 21 non-causal rows after replay-free recovery: Stage 4 rows remain historical evidence; the new fresh contribution is Stage 5/6-only and adds or improves four seed rows.
- Feature probe v2 has one non-causal runtime-visible probe model over review thresholds, but this is a review boundary only. Selector training, runtime selector implementation, routing, scoring, provider selection changes, and provider suppression remain blocked.
- Benchmark v0 compared majority, provider prior, stage/provider-family prior, trace/context rule, proposal-count rule, and combined simple rule. Best non-causal model: `combined_simple_rule` with accuracy 0.952, safe-preservation recall 1.0, switch-contrast recall 0.8, abstain recall 1.0.
- Runtime review packet v0 is review-only: default-off, opt-in, trace-only first, recommendation-only future sandbox envelope; it forbids score/routing/provider/default changes, provider suppression, Stage 7 promotion, Stage 8 training, runtime DTM/tablebase, topology mutation, state-hash exceptions, and treating capacity labels as ownership labels.

## Next Needed Work

- Return to KRK strategy/sequence control-plane work; any future causal selector attempt requires a new architecture review and explicit approval.
- Do not pursue behavior-changing selector variants from the current branch closure.
- Stop at the runtime-review approval boundary; any default-off selector-objective sandbox still requires separate explicit approval before implementation.
- Do not set runtime-ready, selector-ready, Stage 7-ready, or Stage 8-ready from the current evidence.
