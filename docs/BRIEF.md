# Hector/ReCoN Brief

Mission: merge the Feb baseline learner, native ReCoN runtime, and TG46+ evaluation rigor into one
learner whose frozen graph beats its baseline on heldout KRK behavior with causal ablation evidence.

Current state: Phase 2.1c basin recognizer refined and measured.

Dieted foundation result: TG46c full-M3 Mate-in-2 heldout all-reply passed 3/3 seeds after the
black-king-neighbor percept revision: 20260701=0.94, 20260702=0.95, 20260703=0.96.

Canonical dieted parent: reports/autogrowth/clean_slate_krk/dieted_foundation_v1/krk_tg46c_real_mate2_repair_seed_20260702_rev1.json

Canonical sha256: ae382d0463e35eff09e9515a715648b5d49b1e0891d127a660e036e378452eb6

Recorded finding: M4 per-key precision promotion loses distributed percept signal (0.94 -> 0.86 on
seed 20260701); promotion redesign deferred to Phase 2 (quorum composition re-compresses
distributed atoms into promotable units).

Current task: 2.1c basin recognizer at P=1.00/R=1.00 on fresh heldout (64+64,
seed 20260901) via composed edge-relative opposition OR corner branch; next: 2.2 bind
recognizer to mate-in-1 actuator candidates.

No-go: new TG names, new report documents, new pool/cache formats, training logic changes,
`docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
