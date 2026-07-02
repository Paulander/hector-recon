# Hector/ReCoN Brief

Mission: merge the Feb baseline learner, native ReCoN runtime, and TG46+ evaluation rigor into one
learner whose frozen graph beats its baseline on heldout KRK behavior with causal ablation evidence.

Current state: Phase 0 is closed.

Headline result: parent baseline 0.156 mean heldout episode success -> M3+M4 0.240 mean across
3/3 seeds.

Ablation result: the trained gain is causal and veto-driven per decomposition; plumbing is verified
by the child-zeroed arm.

Known limitation: positive affordances promote and activate but are behaviorally neutral. This is
deferred to Phase 2 representations.

Current task: Phase 1.1 audit complete; next: 1.2 dieted retrain (feature removal + foundation retrain, atomic).

No-go until Phase 1 starts: new TG names, new report documents, new pool/cache formats, training
logic changes, `docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
