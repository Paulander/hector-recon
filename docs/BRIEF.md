# Hector/ReCoN Brief

Mission: merge the Feb baseline learner, native ReCoN runtime, and TG46+ evaluation rigor into one
learner whose frozen graph beats its baseline on heldout KRK behavior with causal ablation evidence.
Current state: Phase 2.7b repaired dispatcher: mate-in-1 first, mate-in-2 immediate-mate cash-in,
fallback-only threefold repetition guard; no training and no new skills.
Canonical dieted parent: reports/autogrowth/clean_slate_krk/dieted_foundation_v1/krk_tg46c_real_mate2_repair_seed_20260702_rev1.json
Canonical sha256: ae382d0463e35eff09e9515a715648b5d49b1e0891d127a660e036e378452eb6
Adopted 2.5 gate: balanced seed 20261211 threshold=0.854756; exact mate-in-2 remains verifier.

Phase 2.7b full-game eval: same 50 games/pool seeds 20270101-20270104, black=fixed-seed uniform
legal as in 2.7. Stop-rule violations: 0 skill illegal moves, 0 skill rook losses, 0 skill
stalemates; fallback rook loss: 1 fence-game draw.

Before -> after:
pool | win rate | repetition draws | other draws | frames mean/max | fallback share
mate-in-<=2 | 0.72 -> 1.00 | 14 -> 0 | none -> none | 13.23/64 -> 0.72/4 | 0.00 -> 0.00
fence-rung | 0.44 -> 0.70 | 27 -> 11 | fifty 1 -> fifty 3, rook 1 | 41.48/161 -> 47.30/161 | 0.65 -> 0.72
general KRK | 0.54 -> 0.72 | 22 -> 13 | fifty 1 -> fifty 1 | 57.11/152 -> 59.30/152 | 0.75 -> 0.79

After branch counts: mate-in-<=2 mate1=50 mate2=25 fallback=0; fence fallback=532 fence=143
mate1=35 mate2=26; general fallback=636 fence=110 mate1=36 mate2=24.
Pool (a) per-game branches: mate1 moves {1:50}; mate2 moves {0:25, 1:25}.
Fallback repetition guard activations/masked/lifted: mate-in-<=2 0/0/0; fence 19/19/0; general
20/21/0.

Fence-to-mate gap after: fence gaps=26, mean/median/max=19.38/15/52 plies, unresolved=18,
fallback share inside gap=0.857; general gaps=21, mean/median/max=25.05/20/58, unresolved=20,
fallback share inside gap=0.821.
Fence durability after: fallback broke established fences 32 times in fence games and 25 times in
general; establish_fence fired more than once in 33 fence games and 23 general games.
Deferral recovery after: 5 gate-declined trainer-verified mate-in-2 positions; 5/5 games won,
mean extra plies=0.00.

Next: 2.8 edge-mate rung (learned policy, mate-2 gate as goal manifold) - designed against the
measured gap.
No-go: new TG names, new report documents, new pool/cache formats, training logic changes,
`docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
