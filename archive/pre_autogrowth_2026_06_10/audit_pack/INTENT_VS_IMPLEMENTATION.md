# Intent vs Implementation

Generated for external review of HEAD `2e0a570` (`Close selector behavior branch`).

Statuses used here:

- `implemented and tested`
- `implemented but weakly tested`
- `documented but not implemented`
- `partially implemented / divergent`
- `obsolete / contradicted by current code`

The intent side comes primarily from `reports/current_agent_brief.md` plus related reports. The implementation side comes from current HEAD code, tests, and generated evidence reports.

## Summary Table

| Intended mechanism | Intent source | Current HEAD implementation | Evidence/tests | Status | Audit judgment |
|---|---|---|---|---|---|
| Structural growth | `reports/Hector_Article_Draft.md` sections `M5 structural learning`, `Results`, `Appendix C`; `reports/structural_growth_lab_note.md`; `reports/architecture_preservation_note.md`; `reports/recon_long_term_architecture_roadmap.md` | Triplet primitives in `src/recon_lite_chess/triplets.py`; stem-cell concepts in `src/recon_lite_hector/nodes/stem_cell.py`; structural candidate and Plan Capsule scaffolds in `scripts/test_krk_landmark_progress.py`; offline topology compiler in `scripts/baseline_to_recon.py`; no gameplay-time topology mutation by design | `tests/test_architecture_preservation.py`, `tests/test_stage7_plan_capsule.py`, `tests/test_krk_triplet_pipeline.py`, `reports/structural_growth_lab_note.md`, `reports/structural_candidates/stage7_post_decision_closure.md` | partially implemented / divergent | Real scaffolding exists, but current accepted KRK evidence does not show learned structural growth reliably improving play. The lab is explicitly a compiler/evaluator/safety harness, not the cognitive mechanism. |
| Fast learning | `reports/Hector_Article_Draft.md` section `M3 fast plasticity`; `reports/architecture_preservation_note.md`; `reports/recon_long_term_architecture_roadmap.md` section `M1-M4/M5` | `src/recon_lite_hector/plasticity/fast.py`, `src/recon_lite_hector/plasticity/bandit.py`, edge/provider metadata flags in `scripts/baseline_to_recon.py`; candidate frames generally forbid M3/M4 updates | Core tests pass under `uv run pytest`; architecture tests verify candidate/handoff artifacts do not become hidden M3/M4 runtime changes | implemented but weakly tested | Fast-learning mechanics exist, but current KRK control-plane work deliberately keeps many candidate/selector paths non-causal. There is not strong HEAD evidence that M3 plasticity is the active driver of KRK progress. |
| Slow consolidation | `reports/Hector_Article_Draft.md` section `M4 slow consolidation`; `reports/architecture_preservation_note.md` | `src/recon_lite_hector/plasticity/consolidate.py`, trace-backed consolidation concepts, provider/edge metadata | Core tests pass; architecture preservation tests check that non-causal handoff diagnostics are not silently converted into M4 inputs | implemented but weakly tested | Slow consolidation is implemented as a mechanism, but its contribution to current KRK competence is not convincingly established. |
| Curriculum scaffolding | `reports/Hector_Article_Draft.md` KRK roadmap; `reports/krk_clean_retrain_*`; `reports/krk_full_suite_readiness_audit_v0.md`; `reports/krk_stage8_training_readiness_review_v0.md` | Stage definitions in `src/recon_lite_chess/training/krk_landmarks.py`; pass criteria in `src/recon_lite_chess/training/adaptive_curriculum.py`; pipeline in `scripts/run_krk_triplet_pipeline.py`; baseline training in `scripts/train_baseline_krk_chain.py`; evaluation driver in `scripts/test_krk_landmark_progress.py` | `tests/test_krk_triplet_pipeline.py`, `tests/test_adaptive_curriculum.py`; clean retrain reports; full pytest: 1098 passed in 35.76s | implemented and tested | The curriculum machinery is real and tested as scaffolding. It does not imply all stages are solved: Stage7 is held-out/quarantined and Stage8 is blocked. |
| KRK competence/evaluation | `reports/current_agent_brief.md` `Verified Invariants`; `reports/krk_full_suite_readiness_audit_v0.md`; `reports/structural_candidates/*`; `reports/strategy_arbitration/*` | Evaluation scripts: `scripts/test_krk_entry.py`, `scripts/test_stage1_backchain.py`, `scripts/test_krk_landmark_progress.py`; report-generating scripts under `scripts/`; pytest tests assert report invariants and regressions | Clean stack evidence through Stage6; Stage7 50-h40 analyses show many max_plies; selector sandbox regression; current `uv run pytest` passes | partially implemented / divergent | Measurable progress exists through protected early/mid curriculum stages. Robust KRK competence, especially Stage7/Stage8 and arbitrary conversion, is not demonstrated at HEAD. |
| Autonomous handover | `reports/Hector_Article_Draft.md` sections `Abstract`, `Big Result`, `Results`; `reports/recon_long_term_architecture_roadmap.md` `Validated stack`; `reports/architecture_preservation_note.md` | Handoff packet/contracts in `src/recon_lite_chess/routing/*`; bridge/demo artifacts under `Presentation/AAAI26/Learned affordance bridge/`; diagnostic handoff composition in `scripts/test_krk_landmark_progress.py` | Tests such as `tests/test_handoff_analysis.py` and `tests/test_architecture_preservation.py`; report claims for `handoff_composition_v1` | partially implemented / divergent | Handoff observability and bridge preservation are implemented. Current KRK branch does not prove autonomous handover into solved KRK strategy; reports explicitly keep handoff/candidate artifacts non-causal. |
| Learned structure rather than hardcoded phase logic | `reports/Hector_Article_Draft.md` thesis; `reports/structural_growth_lab_note.md`; `reports/recon_long_term_architecture_roadmap.md`; `reports/current_agent_brief.md` | Code contains explicit stage labels, landmarks, provider names, and opt-in Stage7 terminals in `src/recon_lite_chess/training/krk_landmarks.py`, `src/recon_lite_chess/krk_baseline_nodes.py`, and `scripts/test_krk_landmark_progress.py`; triplets and growth profiles provide a more generic structure | Tests verify guardrails and non-causal boundaries, not label-free discovery | partially implemented / divergent | The direction is learned structure, but current KRK scaffolding still contains substantial hand-authored curriculum and phase/stage vocabulary. Current reports acknowledge this by blocking runtime/Stage8 and asking for broader control-plane evidence. |
| Request/confirmation dynamics | ReCoN core design; `reports/architecture_preservation_note.md`; `reports/recon_long_term_architecture_roadmap.md` M1-M4 preservation | Core ReCoN engine/graph in `libs/recon-lite/src/recon_lite/*`; strict formal pairs in graph compiler; request/confirm/action/script node vocabulary used by chess compiler | Formal and integration tests under `libs/recon-lite/tests` and `tests/test_formal_recon_integration.py`; full pytest passes | implemented and tested | The graph mechanics are real and well covered compared with higher-level competence claims. |
| Sensor/actuator/terminal/script node organization | `reports/structural_growth_lab_note.md`; `reports/recon_long_term_architecture_roadmap.md`; baseline compiler comments | `scripts/baseline_to_recon.py` compiles root -> hub -> actuator legs with terminal/script/action structure; `src/recon_lite_chess/krk_baseline_nodes.py` creates context terminals, successor-affordance scripts, support adapters, Plan Capsule markers, and Stage7 opt-in terminals | `tests/test_krk_triplet_pipeline.py`, `tests/test_stage7_plan_capsule.py`, formal integration tests | implemented and tested | The executable node organization matches the stated architecture. The open issue is whether the organization yields learned competence, not whether it exists. |
| Selector behavior as causal runtime control | `reports/strategy_arbitration/krk_selector_objective_runtime_review_packet_v0.md`; `reports/strategy_arbitration/krk_selector_behavior_branch_closure_v0.md`; `reports/current_agent_brief.md` `Current Decision` | Selector objective benchmark and trace-only recommendation artifacts exist; behavior sandbox path exists but is quarantined after regression; no selector runtime authorization | `tests/test_krk_selector_behavior_regression_audit.py`; `reports/strategy_arbitration/krk_selector_behavior_regression_decision_v0.md`; `reports/strategy_arbitration/krk_selector_behavior_branch_closure_v0.md` | obsolete / contradicted by current code | Causal selector behavior is explicitly closed for now. Only trace-only observability/recommendation remains valid. |
| Stage7 promotion and Stage8 training | Earlier commits `5a6f079` (`Stage 7 completed`) and `2fcd246` (`Stage 8 done`); later reports supersede them | Stage7/Stage8 artifacts and opt-in providers exist, but gates block promotion/training; Stage7 is held-out challenge; Stage8 readiness is false | `reports/structural_candidates/stage7_post_decision_closure.md`, `reports/structural_candidates/stage7_curriculum_boundary_decision_v0.json`, `reports/krk_stage8_training_readiness_review_v0.md`, `tests/test_krk_stage8_training_readiness_review.py` | obsolete / contradicted by current code | Earlier completion language is superseded. Current HEAD says Stage7 is quarantined/held-out and Stage8 is blocked. |

## Mechanism Notes

### Structural Growth

The strongest implementation artifacts are `src/recon_lite_chess/triplets.py`, `scripts/run_krk_triplet_pipeline.py`, `scripts/baseline_to_recon.py`, and the structural candidate sections of `scripts/test_krk_landmark_progress.py`. These establish a real pipeline for representing candidate structure, compiling topology, and validating guardrails.

The divergence is conceptual: `reports/Hector_Article_Draft.md` frames structural growth as autonomous maturation, while `reports/structural_growth_lab_note.md` later narrows the current system to offline proposal/evaluation and explicitly says the lab is not the cognitive mechanism. This is a sane safety position, but it means the current branch is not yet proving the strongest structural-growth claim.

### Fast/Slow Learning

`M3` and `M4` are implemented as code modules and preserved as architectural invariants. The current KRK path, however, often forbids M3/M4 updates inside candidate/selector frames. `reports/current_agent_brief.md` says selector training rows, Stage7 rows, and runtime authorization rows are zero. That makes fast/slow learning more of a preserved substrate than a demonstrated active driver of KRK progress at HEAD.

### Curriculum and KRK Evaluation

The curriculum stack is the most concrete part of the branch. `src/recon_lite_chess/training/krk_landmarks.py` defines stages and features; `src/recon_lite_chess/training/adaptive_curriculum.py` separates one-ply checks from conversion/playout thresholds; `scripts/test_krk_landmark_progress.py` evaluates local and h40-style conversion behavior.

The caveat is that the best current reports stop short of Stage7/Stage8 promotion. `reports/krk_clean_stack_post_replacement_validation_v0.md` says the clean stack was adopted/validated while Stage7 remained quarantined and Stage8 blocked. `reports/krk_stage8_training_readiness_review_v0.md` keeps Stage8 blocked pending sequence-policy evidence.

### Handover and Autonomy

Handoff has real data structures and tests, but current KRK usage is mostly diagnostic/non-causal. `reports/recon_long_term_architecture_roadmap.md` says `handoff_composition_v1` is validated as part of the protected stack, but the same roadmap says Stage7 is not promoted and the bottleneck is broader strategy/sequence control.

The external reviewer should separate two claims:

- There is an implemented handoff observability and bridge system.
- The current branch has not proven autonomous KRK handover into robust competence.

### Learned Structure vs Hardcoded Phase Logic

The project's intention is clearly to avoid hardcoded phase logic. Current code still contains explicit KRK stage names, labels, providers, opt-in terminals, and hand-authored features. This is not automatically disqualifying for research scaffolding, but it is the core conceptual tension of the branch.

The best current interpretation is: the branch is trying to use hand-authored curriculum scaffolding to create evidence for learned structure, while current gates prevent mistaking scaffolding for learned autonomy.

## Bottom Line

The branch is aligned with the stated Hector/ReCoN direction in its caution, vocabulary, and architecture. It is not yet aligned in proof strength. The codebase contains real mechanisms for ReCoN graph execution, triplet/curriculum training, handoff observability, and structural candidate review. The missing piece is accepted evidence that these mechanisms learn structural KRK competence rather than organize increasingly elaborate scaffolding around an unsolved Stage7/Stage8 gap.
