# Hector/ReCoN Brief

Mission: merge the Feb baseline learner, native ReCoN runtime, and TG46+ evaluation rigor into one
learner whose frozen graph beats its baseline on heldout KRK behavior with causal ablation evidence.

Current task: Phase 0.1 and 0.2 only.

Primary metric: heldout episode success rate versus the repaired parent-only classifier baseline.

Acceptance for this task:

- Parent-only is reported under the repaired classifier and used as the baseline.
- Parent legacy-vs-repaired classifier delta is reported only as a reclassification diagnostic.
- Trained M3/M4/M3+M4 arms are compared with parent under identical repaired classification.
- Reward-channel audit in the run JSON is non-degenerate.
- At least one positive non-veto affordance promotes across the 3-seed check.

Current scope:

- `src/recon_lite_chess/autogrowth/tg48a2_same_side_episode_training.py`
- `docs/BRIEF.md`

No-go this session: other phases, new TG names, new report documents, new pool/cache formats,
`docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
