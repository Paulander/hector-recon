# Hector/ReCoN Brief

Mission: merge the Feb baseline learner, native ReCoN runtime, and TG46+ evaluation rigor into one
learner whose frozen graph beats its baseline on heldout KRK behavior with causal ablation evidence.
Canonical dieted parent: reports/autogrowth/clean_slate_krk/dieted_foundation_v1/krk_tg46c_real_mate2_repair_seed_20260702_rev1.json
Canonical sha256: ae382d0463e35eff09e9515a715648b5d49b1e0891d127a660e036e378452eb6
Adopted 2.5 gate: balanced seed 20261211 threshold=0.854756; exact mate-in-2 remains verifier.

Standing spec checklist: every loop over moves in any skill must state quantifier polarity
explicitly: existential over our candidate moves, universal over opponent replies.

Phase 2.8b-fix: `enter_mate2_skill` repaired from helpful-opponent existential reply semantics to
universal all-reply semantics. It is now exact mate-in-3 restricted to edge/fence distance-1
closure; the bright line is fixed here: no mate-4 exactification.

Relabel result: old 2.8a distance-1 train survived 134/300=0.447 and heldout survived
40/96=0.417, so the omitted reply quantifier inflated the heldout pool by 56/96 positions.
Corrected distance-1 closure on relabeled heldout is 40/40=1.000; frames mean/max 6.35/46.

Full-game eval, same 50-game pools/seeds, black=fixed-seed uniform legal:
pool | 2.7b | broken 2.8b | fixed 2.8b
mate-in-<=2 | 50/50 | 50/50 | 50/50
fence | 35/50 | 31/50 | 30/50
general | 36/50 | 28/50 | 29/50
Fixed run had zero skill-branch illegal moves, rook losses, or stalemates.

Fixed gap/fallback: fence fallback share 0.748, gap mean/median/max 15.72/8/56 with 21 unresolved;
general fallback share 0.763, gap 14.47/6/48 with 21 unresolved. Fence breaks under fallback
remain dominant: 111 in fence/general combined during fixed eval.

Corrected distance-2 stratum, baselines only: source d2 107 -> certified 105; split 41 train /
64 heldout. Heldout entry rates: fallback 56/64=0.875, random 10/64=0.156, dispatcher
56/64=0.875. Because fallback remains >=0.85, the stratum needs redefinition before training.

Decision: no training this session and no Phase 2.8c advance. Next: 2.8b review of stratum
definition and fence-maintenance gap under explicit quantifier polarity.

No-go: new TG names, new report documents, new pool/cache formats, training logic changes,
`docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
