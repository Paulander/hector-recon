# Hector/ReCoN Brief

Mission: merge the Feb baseline learner, native ReCoN runtime, and TG46+ evaluation rigor into one
learner whose frozen graph beats its baseline on heldout KRK behavior with causal ablation evidence.
Current state: Phase 2.7 priority dispatcher composes the learned mate-in-2 gate, exact mate-in-2
skill, mate-in-1 basin/skill, exact fence-establishment skill, and canonical dieted fallback scorer.
Canonical dieted parent: reports/autogrowth/clean_slate_krk/dieted_foundation_v1/krk_tg46c_real_mate2_repair_seed_20260702_rev1.json
Canonical sha256: ae382d0463e35eff09e9515a715648b5d49b1e0891d127a660e036e378452eb6
Adopted 2.5 operating point: balanced gate, seed 20261211, threshold=0.854756; exact mate-in-2
skill remains the sole verifier/binder when the gate fires.
Phase 2.6 fence-establishment ceiling: seed 20261231, 64/64 positives established, 0/64 negatives
emitted, frames mean/max=46.44/76.
Phase 2.7 full-game eval: 50 games per pool, fresh seeds 20270101-20270104, black=fixed-seed
uniform legal because the old deterministic-worst-foundation reply path depends on historical cache
construction. Stop-rule violations: 0 skill illegal moves, 0 skill rook losses, 0 skill stalemates.
pool | win rate | draws | mean mate plies | frames mean/max | fallback share | branch counts
mate-in-<=2 | 36/50=0.72 | repetition 14 | 2.78 | 13.23/64 | 0.00 | mate2 145, mate1 8
fence-rung | 22/50=0.44 | repetition 27, fifty 1 | 24.45 | 41.48/161 | 0.65 | fallback 456, fence 126, mate2 100, mate1 17
general KRK | 27/50=0.54 | repetition 22, fifty 1 | 26.33 | 57.11/152 | 0.75 | fallback 592, fence 108, mate2 66, mate1 20
Deferral recovery: gate-declined trainer-verified mate-in-2 positions=5 across fence/general games;
3/5 such games still won, mean extra plies among recovered wins=1.33.
Fence-to-mate gap: fence pool observed 25 gaps, mean/median/max=18.56/14/50 plies, unresolved=19,
fallback share inside gap=0.85; general observed 19 gaps, mean/median/max=22.11/16/58, unresolved=22,
fallback share inside gap=0.81.
Fence durability finding: fallback broke established fences 32 times in fence games and 25 times in
general games; establish_fence fired more than once in 32 fence games and 22 general games.
Recorded finding: mate2-first dispatch can preempt immediate mate, causing 14 repetitions even in
mate-in-<=2 starts with fallback share 0.00.
Next: 2.8 — fence-to-mate bridge closes fallback wandering in the established-fence to mate-2 gap.
No-go: new TG names, new report documents, new pool/cache formats, training logic changes,
`docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
