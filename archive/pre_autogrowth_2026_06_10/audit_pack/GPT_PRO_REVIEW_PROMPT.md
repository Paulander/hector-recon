# GPT Pro Review Prompt

Use this prompt with GPT Pro.

```text
You are reviewing a research software branch for Hector/ReCoN.

Branch/head:
- Repository: recon-lite
- Current branch: formalism-fix-and-triplet-cleanup
- HEAD: 2e0a570 (Close selector behavior branch)
- Main question: is the current branch still aligned with the intended Hector/ReCoN research direction, or has it drifted into scaffolding/bloat?

Research direction to evaluate:
- KRK through structural growth
- Fast/slow learning
- Large curriculum/training scaffolding
- Autonomous handover
- Learned structure rather than hardcoded phase logic
- Measurable progress toward KRK competence

Important:
- Do not assume the reports are true.
- Treat reports as claims, evidence records, or intentions that must be checked against code, tests, and experiment outputs.
- Be frank. No hype.
- Cite file paths, report names, section names where useful, and commit hashes.

Read the audit pack in this order:

1. audit_pack/REPORTS_TIMELINE.md
2. audit_pack/INTENT_VS_IMPLEMENTATION.md
3. audit_pack/EXPERIMENT_EVIDENCE.md
4. audit_pack/CURRENT_ARCHITECTURE.md
5. audit_pack/BRANCH_PHASES_FROM_GIT.md
6. audit_pack/DRIFT_AND_TUNNEL_VISION_RISKS.md

Then inspect current code selectively. Prioritize:

- reports/current_agent_brief.md
- reports/recon_long_term_architecture_roadmap.md
- reports/structural_growth_lab_note.md
- reports/architecture_preservation_note.md
- reports/krk_current_control_plane_gate_v0.md
- reports/krk_full_suite_readiness_audit_v0.md
- reports/krk_stage8_training_readiness_review_v0.md
- reports/strategy_arbitration/krk_selector_behavior_branch_closure_v0.md
- reports/strategy_arbitration/krk_selector_behavior_regression_decision_v0.md
- reports/structural_candidates/stage7_curriculum_boundary_decision_v0.json
- reports/structural_candidates/stage7_post_decision_closure.md
- src/recon_lite_chess/triplets.py
- scripts/run_krk_triplet_pipeline.py
- scripts/train_baseline_krk_chain.py
- scripts/baseline_to_recon.py
- scripts/test_krk_landmark_progress.py
- src/recon_lite_chess/krk_baseline_nodes.py
- src/recon_lite_chess/training/krk_landmarks.py
- src/recon_lite_chess/training/adaptive_curriculum.py
- src/recon_lite_hector/plasticity/fast.py
- src/recon_lite_hector/plasticity/consolidate.py
- tests/test_architecture_preservation.py
- tests/test_krk_triplet_pipeline.py
- tests/test_stage7_plan_capsule.py
- tests/test_krk_selector_behavior_regression_audit.py
- tests/test_krk_stage8_training_readiness_review.py

Also use git phase context from these commits:

- feb8560 - First commit ReCoN-lite scaffold
- 06c21f6 - WORKING KRK DEMO
- 3cb1a09 - WORKING MATE
- e6afa62 - M1 continuous activations
- ea99506 - M2 macrograph/endgame expansion
- 1adaec1 - M3 fast plasticity
- 275fa99 - M4 slow consolidation
- a21d4d3 - M5 motifs/discovery/exploration
- a45165d - M6/M7 fan-in/goal hierarchy/full game
- 29e8eba - learned affordance-based endgame router and bridge visualization
- b9641a2 - successful partial triplet curriculum for KRK, change plans past this point
- 81b3e2e - Behavior-Preserving ReCoN Handoff
- 5a6f079 - Stage 7 completed
- 2fcd246 - Stage 8 done
- 8ffae4c - document Stage7 architecture pause
- d0cf9cb - gate KRK self-expansion architecture
- aeb144b - define KRK control plane evidence contract
- 0d676e1 - decide Stage7 curriculum boundary
- c9fdf36 - selector objective benchmark
- 9abda6a - implemented selector behavior sandbox
- 4b54ef5 - audit regression
- 3f958c3 - continuation regression root cause
- 2e0a570 - Close selector behavior branch

Answer these questions:

1. What are the intended Hector/ReCoN mechanisms, and which are actually implemented at HEAD?
2. Which implemented mechanisms are tested as real behavior, and which are mostly report/spec/plumbing?
3. Is the branch conceptually aligned with Hector/ReCoN, or has it drifted?
4. Is the project converging on KRK competence or bloating around blocked Stage7/Stage8 evidence?
5. Which current claim is strongest?
6. Which current claim is weakest or most misleading?
7. Are fast learning, slow consolidation, structural growth, and curriculum scaffolding actually interacting, or are they parallel scaffolds?
8. Is "autonomous handover" real in current KRK evidence, or mostly diagnostic/non-causal?
9. Where does hardcoded phase/stage logic still leak into the supposedly learned structure?
10. What old failed mechanisms still influence current design?
11. What is the smallest next experiment that could prove or falsify the current approach?
12. If the branch appears to be on the wrong track, say so directly. Identify what should be stopped, removed, or refactored, and explain whether that is a conceptual correction, an implementation cleanup, or a full research-direction reset.

For the smallest next experiment, specify:

- exact mechanism under test
- exact baseline/control
- held-out data or FEN-generation rule
- metrics
- pass/fail thresholds
- no-go conditions
- which existing reports/scripts should be reused
- which artifacts must be disabled to avoid leakage or hardcoded phase switching

Constraints for your review:

- Do not hide behind vague "needs refactoring" advice. If a refactor, reset, or deletion is needed, say exactly what should change and why.
- You may recommend a broad refactor or direction change if the evidence says the branch is on the wrong track. Separate that architectural recommendation from the smallest falsification experiment.
- Do not recommend more documentation as the main next step unless the main finding is that the evidence is too disorganized to audit.
- Do not treat runtime DTM/tablebase, direct provider override, gameplay-time topology mutation, Stage7 promotion, or Stage8 training as already allowed. Current reports block those unless a new explicit review and falsification protocol authorizes them.
- Prefer one small experiment that can change the project's belief either way.
```
