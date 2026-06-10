# Reports Timeline

Generated for external review of HEAD `2e0a570` (`Close selector behavior branch`) on branch `formalism-fix-and-triplet-cleanup`.

This timeline treats `reports/current_agent_brief.md` as the canonical current brief. The root `current_agent_brief.md` says it is only a pointer. Reports are treated as project self-description and evidence artifacts, not as automatically true experimental proof.

## Primary Sources

- `reports/current_agent_brief.md`, sections `Active KRK Gate`, `Current Decision`, `Verified Invariants`, `Next Needed Work`.
- `reports/Hector_Article_Draft.md`, sections `Abstract`, `III. Hector's Roadmap`, `FeatureHub`, `Inertia pruning`, `Results`, `Limitations`, `Appendix C`.
- `reports/recon_long_term_architecture_roadmap.md`, sections `Purpose`, `Validated stack`, `Stage7 conclusion`, `Gaps`, `Next milestone`, `Runtime sandbox policy`, `M1-M4/M5`, `Avoid next`.
- `reports/architecture_preservation_note.md`.
- `reports/structural_growth_lab_note.md`.
- `reports/krk_self_expansion_architecture_gate_v0.md`.
- `reports/krk_current_control_plane_gate_v0.md`.
- `reports/krk_full_suite_readiness_audit_v0.md`.
- `reports/krk_stage8_training_readiness_review_v0.md`.
- `reports/strategy_arbitration/*.md`.
- `reports/structural_candidates/*.md` and adjacent JSON artifacts.

## Chronological Narrative

### 2025-09: ReCoN-lite and hand-authored KRK scaffold

Representative commits: `feb8560` (`First commit ReCoN-lite scaffold`), `06c21f6` (`WORKING KRK DEMO`), `a9238ba` (demo visually works but board update/move/strategy logic missing), `3cb1a09` (`WORKING MATE`), `656cd12` (subgraphs responsible for patterns/strategies based on terminal node signals).

What the project believed it was doing: proving that a small ReCoN graph could drive KRK-like endgame behavior through terminal nodes, strategy packs, scripts, and visible subgraphs.

Problems discovered: early KRK behavior was not yet a real game loop. Commit `a9238ba` explicitly says the demo worked visually but did not update the board and still needed move, strategy, and game logic.

Fixes attempted: more KRK-specific strategy logic, visual debugging, terminal-signal-driven subgraphs, and mate/stalemate/deadlock handling. This stage established a pattern that persists: chess competence was often advanced by adding explicit domain structure.

What survived into HEAD: the basic graph vocabulary survived, as did the terminal/script/action organization. The specific early KRK demo is no longer the central evidence path.

### 2025-10 to 2025-11: M1/M2, macrograph, TraceDB, and teacher scaffolding

Representative commits: `e6afa62` (`M1 continuous activations`), `ea99506` (`M2 macrograph/endgame expansion`), `6445038` (rook technique subgraph/tests/Stockfish teacher), `50035dd` (`lightweight TraceDB`).

What the project believed it was doing: moving from brittle switches toward continuous activation, macrograph expansion, subgraph delegation, and traceable evaluation. This became the foundation for the later `M1-M4` preservation language.

Mechanisms introduced: continuous activations, macrograph/endgame packs, test scaffolds, teacher/evaluation workflows, and TraceDB.

What survived into HEAD: `libs/recon-lite/src/recon_lite/*` still contains the core engine/graph/macrograph/trace database primitives. `src/recon_lite_hector/*` preserves Hector compatibility wrappers and learning/plasticity modules.

### 2025-12: Fast/slow learning and structural-learning roadmap

Representative commits: `1adaec1` (`M3 fast plasticity`), `275fa99` (`M4 slow consolidation`), `a21d4d3` (`M5 motifs/discovery/exploration`), `a45165d` (`M6/M7 fan-in/goal hierarchy/full game`).

What the project believed it was doing: defining Hector as more than a hand-coded chess controller. `reports/Hector_Article_Draft.md` describes a roadmap in `III. Hector's Roadmap`: `M3` fast plasticity, `M4` slow consolidation, `M5` structural learning, and later full-game/hierarchy stages.

Mechanisms introduced:

- Fast plasticity in `src/recon_lite_hector/plasticity/fast.py`.
- Slow consolidation in `src/recon_lite_hector/plasticity/consolidate.py`.
- Motif/discovery concepts in `src/recon_lite_hector/learning/m5_structure.py` and related modules.
- Trace-backed learning claims and paper-oriented reporting.

Unresolved concern introduced here: the roadmap and paper framing began to run ahead of direct KRK evidence. `reports/Hector_Article_Draft.md`, section `Limitations`, explicitly calls out KRK credit assignment and draw-heavy sample starvation.

### 2025-12 to 2026-02: KPK/KQK handover, structural growth claims, and bridge work

Representative commits: `d938e5d` (`Fixed KRK now 100%`), `da0d103` (`M5 evolution implementation`), `130483a` (`M5plus pattern discovery`), `1a76fad` (`KRK Curriculum 10-stage backward chained`), `fc091f1` (forced AND hoisting/POR chains/bridge), `29e8eba` (learned affordance-based endgame router and bridge visualization).

What the project believed it was doing: demonstrating autonomous strategic handover and structural maturation. `reports/Hector_Article_Draft.md`, sections `Abstract`, `Big Result`, `Results`, and `Appendix C`, frame the core research direction as learned structural subgoals, KPK-to-KQK handover, dynamic stem-cell growth, and improved success/sample efficiency.

Major conceptual pivot: from "make KRK work" to "make ReCoN/Hector discover or mature reusable structure that can hand off between endgame subgraphs." The bridge demo and router artifacts were meant to make this visible.

Mechanisms introduced or emphasized:

- Learned/weighted affordance routing between endgame subgraphs.
- Dynamic Stem Cell Layer language.
- Growth logs and structural maturation metrics.
- FeatureHub and inertia pruning concepts in `reports/Hector_Article_Draft.md`.

Unresolved concern: the report claims are strongest for KPK/KQK-style handover and structural maturation, but they do not by themselves establish robust KRK competence in current HEAD.

### 2026-04 to 2026-05: Triplet formalism, compiled baseline, and behavior-preserving handoff

Representative commits: `502e814` (KRK triplet formalism), `b9641a2` (`successful partial triplet curriculum for KRK, change plans past this point`), `81b3e2e` (`Behavior-Preserving ReCoN Handoff`), `6a5f52d` (`offline shadow stem and handoff`).

What the project believed it was doing: shifting from ad hoc stage patches toward a formal before/actuator/after triplet layer and a behavior-preserving path from learned baseline behavior into ReCoN topology.

Mechanisms introduced:

- `src/recon_lite_chess/triplets.py`: terminal-space triplets, growth profiles, and promotion/pruning thresholds.
- `scripts/run_krk_triplet_pipeline.py`: replayable Stage0/Stage1 triplet-growth pipeline.
- `scripts/baseline_to_recon.py`: compiles learned baseline sensors/actuators into a ReCoN root/hub/leg topology.
- Handoff packets, shadow candidates, provider promotion stats, and skill-contract statistics.

Current interpretation: this was a real implementation pivot, but the formal triplet path still mostly demonstrates scaffolded early-stage competence and topology compilation. It does not prove full KRK strategic competence.

### 2026-05: Stage7/Stage8 optimism, then quarantine

Representative commits: `2f2d907` (`Stage 7 investigation slice`), `04b56ab` (opt-in Stage7 post-king-tempo continuation provider), `5a6f079` (`Stage 7 completed`), `2fcd246` (`Stage 8 done`), followed by report-driven reversals.

What the project believed it was doing initially: adding local Stage7/Stage8 structure to close the KRK curriculum gap.

Problems discovered:

- `reports/structural_candidates/stage7_pause_and_architecture_review.md` says the Stage7 branch produced local evidence but failed reliable conversion and worsened some hard-negative rankings.
- `reports/structural_candidates/stage7_selected_path_architecture_review_v0.md` says Stage7 failures were not homogeneous: some were ownership misselection, others were sequence/capacity/model-expression issues.
- `reports/structural_candidates/stage7_curriculum_boundary_decision_v0.json` reclassifies `box_shrink` as a local evidence handoff trigger instead of a promotable Stage7 skill.
- `reports/structural_candidates/stage7_post_decision_closure.md` closes the Stage7 branch and says Stage7 remains quarantined; Stage8 remains false.

Mechanisms deprecated or replaced:

- Direct Stage7 runtime repair.
- Stage7 promotion.
- Stage8 training based on Stage7.
- Runtime internal-terminal/arbiter intervention.

Current standing: Stage7 is a held-out challenge and boundary signal, not promoted competence.

### 2026-05: Strategy/sequence control plane replaces local Stage7 patching

Representative commits: `8ffae4c` (document Stage7 architecture pause), `d0cf9cb` (gate KRK self-expansion architecture), `aeb144b` (define KRK control-plane evidence contract), `0d676e1` (decide Stage7 curriculum boundary), `8faa9b6` (long-term architecture roadmap), `a770db6` (candidate generation control-plane review).

What the project believed it was doing: stopping local Stage7 micro-patches and reframing the problem as broader KRK strategy/sequence arbitration and candidate generation.

Key report statements:

- `reports/recon_long_term_architecture_roadmap.md`, `Purpose`: the lifecycle evidence -> review -> default-off sandbox -> target smoke -> quarantine worked; the bottleneck is candidate generation/proposal coverage and broader KRK strategy-sequence, not another local Stage7 rule.
- `reports/krk_self_expansion_architecture_gate_v0.md`: selected next architecture goal is a control-plane evidence contract; forbidden next work includes Stage7 runtime repair/promotion, Stage8 training, runtime arbiter/internal terminal, runtime DTM/tablebase, and gameplay-time topology mutation.
- `reports/structural_growth_lab_note.md`: Structural Growth Lab is a compiler/evaluator/safety harness, not the cognitive mechanism; no gameplay-time topology mutation.

Mechanisms introduced:

- Strategy owner and arbiter evidence contracts.
- Candidate generation review packets.
- Plan capsule markers.
- Non-causal selector objective benchmarks.
- Explicit approval gates and default-off sandboxes.

Current standing: this is the active research direction, but it is evidence/control-plane heavy and competence-light.

### 2026-05: Clean retrain, protected stack, and suite gates

Representative commits: `913cd1f` (clean KRK curriculum checkpoint plan), `87756c9` (clean retrain smoke), `8716a3b` (clean retry), `185f3d8` (guardrails), `18e9521` (replacement review), `d33967c` (full suite readiness), `1e683bf` (Stage8 readiness review), `d75d62b` (refresh gates after Stage7 labels).

What the project believed it was doing: establishing a protected stack and guardrail process that could safely replace or quarantine curriculum checkpoints.

Evidence and problems:

- `reports/krk_clean_retrain_smoke_result_v0.md`: plumbing passed, but semantic smoke was too tiny.
- `reports/krk_clean_retrain_run_result_v0.md`: full run incomplete at Stage2A, no promotable checkpoint.
- `reports/krk_clean_retrain_retry1_result_v1.md`: completed through Stage6 overlay and basic checks passed.
- `reports/krk_clean_retrain_retry1_guardrail_result_v1.md`: Stage6 overlay had partial guardrail problems and was quarantined for replacement.
- `reports/krk_clean_stack_post_replacement_validation_v0.md`: clean stack adopted and validated, but Stage7 remained quarantined and Stage8 blocked.
- `reports/krk_stage8_training_readiness_review_v0.md`: Stage8 training remains blocked pending sequence-policy gate.

Current standing: protected Stage5/6 scaffolding is the strongest KRK evidence path. Stage7/8 and runtime selector remain blocked.

### 2026-05 to 2026-06: Selector objective benchmark, behavior sandbox, regression, closure

Representative commits: `78e133a` (fresh Stage5/6 selector diversity collection), `c9fdf36` (selector objective benchmark), `e73efab` (selector runtime review packet), `9abda6a` (implemented selector behavior sandbox), `4b54ef5` (audit regression), `3f958c3` (continuation regression root cause), `2e0a570` (`Close selector behavior branch`).

What the project believed it was doing: evaluating whether a selector/objective layer could safely choose better ownership or continuation behavior.

Evidence:

- `reports/strategy_arbitration/krk_selector_objective_benchmark_review_packet_v2.md`: best non-causal benchmark `combined_simple_rule` reached 0.952 accuracy, safe-preservation recall 1.0, switch-contrast recall 0.8, abstain recall 1.0.
- `reports/strategy_arbitration/krk_selector_objective_runtime_review_packet_v0.md`: runtime review packet only; no behavior changes authorized.
- `reports/strategy_arbitration/krk_selector_behavior_regression_audit_v0.md`: behavior sandbox regressed a safe-control row.
- `reports/strategy_arbitration/krk_selector_behavior_regression_decision_v0.md`: selector behavior quarantined due to safe regression.
- `reports/strategy_arbitration/krk_selector_behavior_continuation_regression_root_cause_v0.md`: root cause was a ply-4 switch that lost continuation.
- `reports/strategy_arbitration/krk_selector_behavior_branch_closure_v0.md`: branch closed; trace-only selector artifacts remain non-causal.

Current stated direction from `reports/current_agent_brief.md`:

- Do not authorize provider, move, score, routing, default, or suppression changes from selector behavior.
- Stop at runtime-review approval boundary.
- Return to broader KRK strategy/sequence control plane work: candidate generation, plan/sequence policy, and state-local paired ownership evidence.
- Do not set runtime-ready, selector-ready, Stage7-ready, or Stage8-ready.

## Major Pivots

- Hand-authored KRK demo -> continuous activation/subgraph/macrograph system.
- Fixed topology learning -> stem-cell/structural-growth aspirations.
- Direct phase-local Stage7 patches -> Stage7 as held-out challenge and handoff/boundary signal.
- Selector recommendation -> selector behavior quarantine; trace-only observability remains.
- Runtime growth/autonomy ambition -> offline, default-off, non-causal, review-gated growth pipeline.
- Full competence claims -> narrower protected Stage5/6 evidence and explicit Stage7/8 blockers.

## Current Stated Direction

The current branch is not claiming runtime selector readiness, Stage7 promotion, Stage8 readiness, or gameplay-time topology mutation. The stated direction is:

- KRK strategy/sequence control plane.
- Better candidate generation and plan/sequence policy.
- State-local paired ownership evidence.
- Offline/reviewed structural growth, not hidden runtime control.
- Preserve M1-M4 semantics and existing protected stack while using Stage7 as held-out challenge evidence.

## Unresolved Concerns

- The project has a large amount of scaffolding, reports, review packets, and approval gates relative to direct KRK competence evidence.
- Stage7 and Stage8 are explicitly blocked in current reports, despite earlier commits claiming completion.
- Structural growth is mostly proposal/compile/evaluate scaffolding at HEAD; accepted evidence that learned structural growth improves arbitrary KRK play is thin.
- Fast/slow learning modules exist, but current KRK evidence does not clearly show M3/M4 learning driving structural improvement.
- Selector/objective artifacts looked promising in non-causal benchmark form but caused a safe-control regression when behavior-changing sandboxing was attempted.
- The article-level claims should be audited against runnable HEAD artifacts before being treated as current branch truth.
