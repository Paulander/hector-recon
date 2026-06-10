# Current Architecture

Generated for external review of HEAD `2e0a570` (`Close selector behavior branch`).

This document distinguishes executable behavior from documentation/spec artifacts. Reports are useful evidence and intent sources, but most reports are not runtime mechanisms.

## Main Modules and Directories

- `libs/recon-lite/src/recon_lite/`: core ReCoN engine, graph primitives, formal engine, macrograph support, logging, and TraceDB.
- `src/recon_lite_hector/`: Hector compatibility namespace with engine/graph wrappers, dynamics, learning, motifs, trust, visualization, fast plasticity, slow consolidation, and stem-cell concepts.
- `src/recon_lite_chess/`: chess domain code: baseline nodes, chess graph construction, triplets, features, sensors, affordance support, endgame scripts, routing/handoff, training, and KRK/KPK/KQK utilities.
- `scripts/`: executable training, compilation, evaluation, audit, report-generation, and visualization scripts.
- `tests/`: main project tests for KRK pipelines, architecture preservation, selector regressions, report invariants, and integration behavior.
- `libs/recon-lite/tests/`: core ReCoN library tests.
- `reports/`: current brief, paper draft, architecture notes, readiness/gate reports, strategy arbitration packets, structural candidate reports, and experiment summaries.
- `snapshots/`: generated model/topology/checkpoint outputs referenced by scripts and reports.

## Executable vs Documentation/Spec

Executable or directly tested:

- Python packages under `libs/recon-lite/src`, `src/recon_lite_hector`, and `src/recon_lite_chess`.
- Training/evaluation scripts under `scripts/`.
- Pytest suites under `tests/` and `libs/recon-lite/tests/`.
- JSON topology/checkpoint/manifest files consumed by scripts.

Documentation/spec/evidence artifacts:

- `reports/current_agent_brief.md`.
- `reports/Hector_Article_Draft.md`.
- `reports/recon_long_term_architecture_roadmap.md`.
- Most `reports/strategy_arbitration/*.md` and `reports/structural_candidates/*.md`.
- Review packets and gate reports. Some tests assert their invariants, but the reports themselves are not runtime controllers.

## Training Flow

The current KRK training flow is scaffolded around explicit landmarks and triplet/formal graph compilation.

1. `scripts/train_baseline_krk_chain.py` trains baseline KRK goal memories. Its header describes Stage0 mate-in-1 and Stage1 backchaining using goal memories.
2. `src/recon_lite_chess/training/krk_landmarks.py` defines KRK stages and labels such as `edge_trap`, `fence_established`, `drive_to_edge`, `box_shrink`, `opposition_tempo`, and `full_krk`.
3. `src/recon_lite_chess/training/adaptive_curriculum.py` defines stage pass criteria and separates local one-ply checks from conversion/playout thresholds.
4. `scripts/baseline_to_recon.py` compiles learned baseline sensors and actuators into a ReCoN topology: root -> hub -> actuator legs, with terminal/script/action organization and provider metadata.
5. `scripts/run_krk_triplet_pipeline.py` orchestrates a replayable Stage0/Stage1 pipeline: train baseline, compile to ReCoN topology, validate formal pairs, evaluate KRK entry and Stage1 backchain, and write a manifest.

The training stack is real. The current reports do not claim full Stage7/Stage8 completion at HEAD.

## Evaluation Flow

Main evaluation surfaces:

- `scripts/test_krk_entry.py`: entry/mate-style evaluation.
- `scripts/test_stage1_backchain.py`: Stage1 backchain checks.
- `scripts/test_krk_landmark_progress.py`: large KRK landmark/progress harness with one-ply checks, h40 conversion/playout checks, candidate frames, selector observations, Plan Capsule markers, and optional sandboxes.
- Report-generation scripts under `scripts/` that produce `reports/strategy_arbitration/*` and `reports/structural_candidates/*`.
- Pytest tests that validate report invariants and known regressions.

Important distinction: many tests validate that unsafe changes are blocked, reports are internally consistent, or scaffolding behaves as expected. Passing pytest is not the same as proving arbitrary KRK competence.

Current fresh test result:

```text
uv run pytest
1098 passed in 35.76s
```

## Curriculum Flow

The curriculum is explicit and staged.

- `src/recon_lite_chess/training/krk_landmarks.py` defines Stage2 through Stage9-style landmark structure, including `box_shrink` and `opposition_tempo`.
- `src/recon_lite_chess/training/adaptive_curriculum.py` computes pass/fail outcomes with thresholds for local, conversion, and playout behavior.
- `reports/krk_clean_retrain_*` documents clean retrain attempts and guardrail decisions.
- `reports/structural_candidates/stage7_curriculum_boundary_decision_v0.json` reclassifies `box_shrink` as a local evidence handoff trigger instead of a promotable Stage7 skill.
- `reports/krk_stage8_training_readiness_review_v0.md` keeps Stage8 training blocked pending sequence-policy evidence.

Current state: protected early/mid curriculum stack is accepted through Stage5/6-style evidence. Stage7 is held out/quarantined; Stage8 is blocked.

## Structural Growth Flow

Structural growth is currently offline, review-gated, and non-causal unless explicitly promoted by a reviewed path.

Key code:

- `src/recon_lite_chess/triplets.py`: reusable before/actuator/after triplet primitives, growth profiles, candidate lifetime, stagnation, promotion, and pruning thresholds.
- `src/recon_lite_hector/nodes/stem_cell.py`: stem-cell node concepts.
- `scripts/test_krk_landmark_progress.py`: emits candidate-generation frames, Plan Capsule markers, strategy-owner signals, selector observations, and sandbox traces.
- `scripts/baseline_to_recon.py`: compiles selected learned baseline structure into topology.

Key reports:

- `reports/structural_growth_lab_note.md`: Structural Growth Lab is a compiler/evaluator/safety harness, not a hidden runtime controller. No gameplay-time topology mutation.
- `reports/architecture_preservation_note.md`: handoff, role, and stagnation observability are trace/candidate evidence, not hidden M4 inputs or runtime topology changes.
- `reports/recon_long_term_architecture_roadmap.md`: M5-style topology changes are offline, reviewed, guardrail-aware, and default-off.

Current state: structural growth exists as candidate/evidence/proposal machinery. It is not currently an online topology-mutating KRK learner.

## Runtime Decision Flow

At runtime/evaluation time, the ReCoN topology is compiled and executed over a chess board state.

1. A compiled topology is loaded from a snapshot or generated by `scripts/baseline_to_recon.py`.
2. `src/recon_lite_chess/krk_baseline_nodes.py` creates graph nodes for KRK root initialization, context terminals, successor-affordance scripts, support adapters, Plan Capsule markers, and optional Stage7 terminals.
3. The engine executes graph ticks, populating a blackboard with visible features, suggestions, provider evidence, and scores.
4. The evaluator materializes candidate moves and evaluates one-ply or playout/conversion outcomes.
5. Optional candidate-generation, selector, arbiter, or Plan Capsule modes can emit trace/recommendation artifacts.
6. The behavior-changing selector sandbox exists in code but is quarantined by `reports/strategy_arbitration/krk_selector_behavior_regression_decision_v0.md` and closed by `reports/strategy_arbitration/krk_selector_behavior_branch_closure_v0.md`.

Forbidden/currently blocked by reports:

- Runtime DTM/tablebase control.
- Gameplay-time topology mutation.
- Selector-driven provider/move/score/routing/default/suppression changes.
- Stage7 promotion.
- Stage8 training.

## State, Config, and Spec JSON Layers

Important artifact layers:

- Topology JSON: compiled graph structures generated by `scripts/baseline_to_recon.py` and stored in `snapshots/`.
- Learner/checkpoint files: baseline/triplet/curriculum learner outputs stored in `snapshots/`.
- Pipeline manifests: generated by `scripts/run_krk_triplet_pipeline.py`.
- Report JSON/MD: gate decisions, review packets, benchmark summaries, and structural candidate analyses under `reports/`.
- Strategy/candidate traces: generated by `scripts/test_krk_landmark_progress.py` and strategy arbitration scripts.

The branch uses JSON heavily as an audit/control-plane layer. Some JSON files are inputs to tests or scripts; others are evidence records.

## Tests and Scripts

Representative tests:

- `tests/test_krk_triplet_pipeline.py`: pipeline command plans, manifest behavior, load/resume, and readiness checks.
- `tests/test_architecture_preservation.py`: no hidden tablebase/controller imports in runtime source; handoff diagnostics and shadow candidates remain non-causal.
- `tests/test_stage7_plan_capsule.py`: Plan Capsule artifacts are default-off/non-causal.
- `tests/test_krk_selector_behavior_regression_audit.py`: validates selector behavior regression evidence and quarantine.
- `tests/test_krk_stage8_training_readiness_review.py`: validates Stage8 blocked state and no runtime/selector/tablebase/topology authorization.
- Core formal/graph tests under `libs/recon-lite/tests`.

Representative scripts:

- `scripts/train_baseline_krk_chain.py`
- `scripts/baseline_to_recon.py`
- `scripts/run_krk_triplet_pipeline.py`
- `scripts/test_krk_entry.py`
- `scripts/test_stage1_backchain.py`
- `scripts/test_krk_landmark_progress.py`

## Architectural Bottom Line

The current architecture is a large, safety-gated KRK research scaffold. The executable core is real: graph execution, triplets, curriculum, topology compilation, and evaluation harnesses all exist and test cleanly. The current competence claim is narrower: protected Stage5/6-style evidence and blocked Stage7/Stage8, with the next intended work centered on KRK strategy/sequence control-plane evidence rather than another direct Stage7 patch.
