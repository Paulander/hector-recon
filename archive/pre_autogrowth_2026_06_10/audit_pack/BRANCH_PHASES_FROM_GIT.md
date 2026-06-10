# Branch Phases From Git

Generated for external review of HEAD `2e0a570` (`Close selector behavior branch`).

This is a conceptual grouping of 970 commits. It deliberately does not list every commit.

## Phase 1: ReCoN-lite scaffold and hand-authored KRK demo

- Commit range: `feb8560` through `656cd12`.
- Dates: 2025-09-12 to 2025-09-23.
- Rough purpose: establish ReCoN-lite, a KRK demo, mate behavior, board visualization, and terminal/subgraph-driven strategy structure.
- Major files touched: early core ReCoN code, KRK demo scripts, visualization files, chess strategy/subgraph code.
- Relation to reports/current brief: predates current report vocabulary but seeds the later KRK and terminal/subgraph architecture.
- What survived into HEAD: graph/node vocabulary, terminal-script-action organization, KRK domain focus.
- What was superseded: early hand-authored demo behavior is no longer the main evidence path.

Representative commits:

- `feb8560` - First commit ReCoN-lite scaffold.
- `06c21f6` - WORKING KRK DEMO.
- `a9238ba` - notes visual demo works but board update/move/strategy/game logic still missing.
- `3cb1a09` - WORKING MATE.
- `656cd12` - subgraphs responsible for patterns/strategies based on terminal node signals.

## Phase 2: Continuous activation, macrograph, teacher, and TraceDB

- Commit range: `e6afa62` through `50035dd`.
- Dates: 2025-10 to 2025-11.
- Rough purpose: move from brittle switches into continuous activations, macrograph expansion, teacher/eval scaffolding, and trace capture.
- Major files touched: `libs/recon-lite/src/recon_lite/*`, Hector graph/engine modules, KRK subgraph/evaluation/test code.
- Relation to reports/current brief: later reports call this part of the preserved M1/M2/M4 substrate.
- What survived into HEAD: core engine, macrograph concepts, TraceDB, and continuous/weighted graph semantics.
- What was superseded: narrow teacher/eval loops became part of broader training/evaluation scaffolding.

Representative commits:

- `e6afa62` - M1 continuous activations.
- `ea99506` - M2 macrograph/endgame expansion.
- `6445038` - rook technique subgraph/tests/Stockfish teacher.
- `50035dd` - lightweight TraceDB.

## Phase 3: M3/M4/M5-M7 learning roadmap

- Commit range: `1adaec1` through `a45165d`.
- Dates: 2025-12-01 to 2025-12-03.
- Rough purpose: implement fast plasticity, slow consolidation, motif discovery, exploration, fan-in, goal hierarchy, and full-game roadmap pieces.
- Major files touched: `src/recon_lite_hector/plasticity/*`, `src/recon_lite_hector/learning/*`, motif/trust/dynamics modules, tests.
- Relation to reports/current brief: `reports/Hector_Article_Draft.md` frames these as the Hector roadmap; current reports preserve M1-M4 semantics and keep M5-style topology changes review-gated.
- What survived into HEAD: fast/slow learning modules and architecture preservation language.
- What was superseded: the roadmap-level claims are now gated by stricter KRK evidence requirements.

Representative commits:

- `1adaec1` - M3 fast plasticity.
- `275fa99` - M4 slow consolidation.
- `a21d4d3` - M5 motifs/discovery/exploration.
- `a45165d` - M6/M7 fan-in/goal hierarchy/full game.

## Phase 4: KPK/KQK handover and bridge architecture

- Commit range: `d938e5d` through `3313c0e`.
- Dates: 2025-12-22 to 2026-02-28.
- Rough purpose: expand from KRK demos into multi-endgame handover, learned affordance routing, bridge visualization, and structural maturation claims.
- Major files touched: chess endgame modules, routing/bridge assets, report/article artifacts, presentation/demo files.
- Relation to reports/current brief: `reports/Hector_Article_Draft.md` presents this as a core success story; current KRK brief treats handoff structures as non-causal unless explicitly promoted.
- What survived into HEAD: routing/handoff vocabulary, bridge artifacts, protected handoff-composition concepts.
- What was superseded: broad paper claims must now be checked against stricter current gates and KRK-specific evidence.

Representative commits:

- `d938e5d` - Fixed KRK now 100%.
- `3e50cb8` - 70 percent winrate with learned gating.
- `29e8eba` - learned affordance-based endgame router plus bridge visualization.
- `3313c0e` - 98 percent winrate stem cell curriculum in new demo.

## Phase 5: Stem cells, KRK curriculum, and compiled baseline

- Commit range: `da0d103` through `a8ea24a`. This is a conceptual subphase inside the broader Phase 4 date span, because the branch mixed bridge demos, paper work, stem-cell experiments, and KRK curriculum commits during January/February.
- Dates: 2026-01-02 to 2026-02-05.
- Rough purpose: create structural growth/stem-cell concepts, a KRK backward-chained curriculum, and a path from baseline learning into ReCoN topology.
- Major files touched: `src/recon_lite_hector/nodes/stem_cell.py`, `src/recon_lite_chess/training/*`, `scripts/train_baseline_krk_chain.py`, `scripts/baseline_to_recon.py`, tests.
- Relation to reports/current brief: directly related to the user's target criteria: KRK through structural growth, curriculum scaffolding, and learned structure rather than hardcoded phase logic.
- What survived into HEAD: explicit KRK landmark curriculum, adaptive criteria, topology compiler, triplet pipeline foundation.
- What was superseded: some early "completed" language was later replaced by Stage7/Stage8 gates and quarantines.

Representative commits:

- `da0d103` - M5 evolution implementation.
- `130483a` - M5plus pattern discovery.
- `1a76fad` - KRK Curriculum 10-stage backward chained.
- `fc091f1` - forced AND hoisting/POR chains/bridge.
- `57b8fd6` - new baseline architecture.
- `4b04fa2` - baseline integration report: graph compilation, runtime execution, spawn points, full integration.
- `a8ea24a` - retrained Stage0 and Stage1, now 100 percent but slower due to larger network.

## Phase 6: Triplet formalism and behavior-preserving handoff

- Commit range: `502e814` through `6a5f52d`.
- Dates: 2026-04 to 2026-05-11.
- Rough purpose: formalize terminal-space triplets, partial KRK curriculum growth, and behavior-preserving handoff into ReCoN structure.
- Major files touched: `src/recon_lite_chess/triplets.py`, `scripts/run_krk_triplet_pipeline.py`, `scripts/baseline_to_recon.py`, `scripts/train_baseline_krk_chain.py`, tests and snapshots.
- Relation to reports/current brief: becomes the concrete infrastructure beneath later protected stack and growth-lab discussions.
- What survived into HEAD: triplet primitives, pipeline tests, handoff/shadow-stem observability.
- What was superseded: partial curriculum success became insufficient once Stage7/Stage8 and sequence-policy gaps were discovered.

Representative commits:

- `502e814` - KRK triplet formalism.
- `b9641a2` - successful partial triplet curriculum for KRK, change plans past this point.
- `81b3e2e` - Behavior-Preserving ReCoN Handoff.
- `6a5f52d` - offline shadow stem and handoff.

## Phase 7: Stage7/Stage8 local repair, then architecture pause

- Commit range: `2f2d907` through `8ffae4c`.
- Dates: 2026-05-16 to 2026-05-19.
- Rough purpose: investigate Stage7, add opt-in continuation/provider mechanisms, initially claim Stage7/Stage8 completion, then pause and reclassify after evidence did not support promotion.
- Major files touched: `src/recon_lite_chess/krk_baseline_nodes.py`, `scripts/test_krk_landmark_progress.py`, `reports/structural_candidates/*`, tests.
- Relation to reports/current brief: current brief and Stage7 reports supersede early completion commits. Stage7 is held-out/quarantined; Stage8 is blocked.
- What survived into HEAD: diagnostic Stage7 artifacts, opt-in providers/terminals, Plan Capsule markers, structural candidate reports.
- What was superseded: direct Stage7 promotion and Stage8 training.

Representative commits:

- `2f2d907` - Stage 7 investigation slice.
- `04b56ab` - opt-in Stage7 post-king-tempo continuation provider.
- `5a6f079` - Stage 7 completed.
- `2fcd246` - Stage 8 done.
- `8ffae4c` - document Stage7 architecture pause.

## Phase 8: KRK self-expansion and strategy/control-plane evidence

- Commit range: `d0cf9cb` through `a770db6`.
- Dates: 2026-05-19 to 2026-05-23.
- Rough purpose: replace local Stage7 patching with broader KRK self-expansion, strategy arbitration, candidate generation, control-plane evidence, and review gates.
- Major files touched: `reports/krk_self_expansion_architecture_gate_v0.md`, `reports/recon_long_term_architecture_roadmap.md`, `reports/strategy_arbitration/*`, `scripts/test_krk_landmark_progress.py`, tests.
- Relation to reports/current brief: this is the direct ancestor of the current stated direction: strategy/sequence control plane, candidate generation, plan policy, and state-local ownership evidence.
- What survived into HEAD: control-plane vocabulary, non-causal candidate/selector/Plan Capsule artifacts, approval gates.
- What was superseded: direct runtime Stage7/arbiter/terminal interventions.

Representative commits:

- `d0cf9cb` - gate KRK self-expansion architecture.
- `aeb144b` - define KRK control plane evidence contract.
- `0d676e1` - decide Stage7 curriculum boundary.
- `8faa9b6` - add ReCoN long-term architecture roadmap.
- `a770db6` - candidate generation control plane review.

## Phase 9: Clean retrain, protected stack, and passive gate hardening

- Commit range: `913cd1f` through `946c707`.
- Dates: 2026-05-24 to 2026-05-27.
- Rough purpose: run clean curriculum retries, validate/replace protected stack artifacts, harden guardrails, produce readiness/gate reports, and block unsafe next actions.
- Major files touched: `reports/krk_clean_retrain_*`, `reports/krk_full_suite_readiness_audit_v0.md`, `reports/krk_stage8_training_readiness_review_v0.md`, `reports/krk_current_control_plane_gate_v0.md`, `tests/*`, `scripts/*`.
- Relation to reports/current brief: current brief inherits these invariants: protected stack valid, Stage7/8 blocked, runtime authorization rows zero, approval boundaries explicit.
- What survived into HEAD: protected stack/gate framework, report-backed blocked state, test assertions around readiness and safety.
- What was superseded: any unreviewed clean retrain checkpoint that failed guardrails or did not satisfy Stage7/8 readiness.

Representative commits:

- `913cd1f` - clean KRK curriculum checkpoint plan.
- `87756c9` - clean retrain smoke.
- `8716a3b` - clean retry.
- `185f3d8` - guardrails.
- `18e9521` - replacement review.
- `d33967c` - full suite readiness.
- `1e683bf` - Stage8 readiness review.
- `d75d62b` - refresh gates after Stage7 labels.
- `946c707` - diverse contrast v1 lineage.

## Phase 10: Selector objective, behavior sandbox, regression, and closure

- Commit range: `50830c4` through `2e0a570`.
- Dates: 2026-05-29 to 2026-06-03.
- Rough purpose: evaluate selector objective diversity, prepare runtime review packet, implement bounded behavior sandbox, discover safe-control regression, diagnose root cause, and close the behavior branch.
- Major files touched: `reports/strategy_arbitration/*`, `scripts/test_krk_landmark_progress.py`, selector/regression tests, `reports/current_agent_brief.md`.
- Relation to reports/current brief: this is the current active brief state. Selector behavior is quarantined; trace-only artifacts remain; next work returns to KRK strategy/sequence control plane.
- What survived into HEAD: non-causal selector benchmark/recommendation artifacts and regression tests.
- What was superseded: behavior-changing selector sandbox as a candidate runtime path.

Representative commits:

- `50830c4` - ownership label v3/v4 lineage.
- `78e133a` - fresh Stage5/6 selector diversity collection.
- `c9fdf36` - selector objective benchmark.
- `e73efab` - selector runtime review packet.
- `9abda6a` - implemented selector behavior sandbox.
- `4b54ef5` - audit regression.
- `3f958c3` - continuation regression root cause.
- `2e0a570` - Close selector behavior branch.

## Git-History Bottom Line

The branch has not moved linearly from idea to proof. It has repeatedly advanced a mechanism, found a boundary condition or regression, then wrapped it in a more explicit review/gate process. That is a healthy safety pattern, but it also means many artifacts in HEAD are fossils of failed or quarantined paths. The current branch phase is not "selector solved KRK"; it is "selector behavior failed a safe-control test, so the project returned to control-plane evidence and candidate generation."
