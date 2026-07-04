# Hector/ReCoN Brief

Mission: merge the Feb baseline learner, native ReCoN runtime, and TG46+ evaluation rigor into one
learner whose frozen graph beats its baseline on heldout KRK behavior with causal ablation evidence.
Canonical dieted parent: reports/autogrowth/clean_slate_krk/dieted_foundation_v1/krk_tg46c_real_mate2_repair_seed_20260702_rev1.json
Canonical sha256: ae382d0463e35eff09e9515a715648b5d49b1e0891d127a660e036e378452eb6
Adopted 2.5 gate: balanced seed 20261211 threshold=0.854756; exact mate-in-2 remains verifier.

Phase 2.8a finding: distance-1 learning was unstable and roughly fallback-level (best seed
50/96=0.521 vs fallback 47/96=0.490), so distance-1 is now treated as exact-reachable and the
learning frontier moved to distance-2.

Phase 2.8b exact closure: `enter_mate2_skill` enters the certified mate-in-2 manifold on the
2.8a distance-1 heldout at 96/96=1.000; frames mean/max 3.54/16. The lower-than-expected frame
mean versus the old 13.01 label audit is from lazy k=1 OR exit on first confirming candidate.

Phase 2.8b dispatcher eval, same 50-game pools/seeds as 2.7b, black=fixed-seed uniform legal:
mate-in-<=2 stayed 50/50 with fallback share 0.000; fence fell 35/50 -> 31/50; general fell
36/50 -> 28/50. No skill-branch illegal moves, rook losses, or stalemates after fixing an eval
SquareSet/a1 false-positive. Fallback share stayed high: fence 0.719, general 0.727.

Gap measurement after `enter_mate2`: fence gap mean/median/max 18.83/8/68 with 21 unresolved and
0.787 fallback share inside; general gap 15.00/6/48 with 22 unresolved and 0.711 fallback share.
Fence durability remains the hole: fence broken while fallback played 110 times in fence pool and
85 times in general.

Phase 2.8b distance-2 training: source d2 rows 107 -> 73 certified; split 9 train / 64 heldout.
Baselines on heldout: fallback 58/64=0.906, random 7/64=0.109, integrated dispatcher 59/64=0.922.
Learned entry rates by seed: 20270211 44/64=0.688, 20270212 60/64=0.938, 20270213 58/64=0.906.
Promoted affordance/veto counts: 134/1127, 122/147, 212/330.

Decision: stop condition is seed instability (spread 0.25) and only 1/3 seeds beat dispatcher.
No tuning, no Phase 2.8c advance. Next: 2.8b review of distance-2 data volume/credit and the
fence-maintenance gap before any distance-3+ expansion.

No-go: new TG names, new report documents, new pool/cache formats, training logic changes,
`docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
