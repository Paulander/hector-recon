# Hector/ReCoN Brief

Mission: merge the Feb baseline learner, native ReCoN runtime, and TG46+ evaluation rigor into one
learner whose frozen graph beats its baseline on heldout KRK behavior with causal ablation evidence.
Canonical dieted parent: reports/autogrowth/clean_slate_krk/dieted_foundation_v1/krk_tg46c_real_mate2_repair_seed_20260702_rev1.json
Canonical sha256: ae382d0463e35eff09e9515a715648b5d49b1e0891d127a660e036e378452eb6
Adopted 2.5 gate: balanced seed 20261211 threshold=0.854756; exact mate-in-2 remains verifier.

Standing spec checklist: every loop over moves in any skill must state quantifier polarity
explicitly: existential over our candidate moves, universal over opponent replies.

Phase 2.8b-fix: `enter_mate2_skill` repaired from helpful-opponent existential reply semantics to
universal all-reply semantics. It is exact mate-in-3 restricted to edge/fence distance-1 closure;
the bright line is fixed here: no mate-4 exactification.

Phase 2.8c: waypoint validation (`fence_established AND WK Chebyshev<=2 on nearest-edge interior
side`) converted 162/200=0.810 in full games, but horizon-6 middle-rung learning on 300/100
waypoint starts did not beat dispatcher. Heldout baselines: dispatcher 44/100=0.440, fallback
28/100=0.280, random 17/100=0.170. Learned seeds: 35/100, 36/100, 36/100; stable but 0/3 beat
dispatcher. Discovery: `king_support_l_shape` and `king_pair_knight_distance_like` carried ~1.5%
abs weight mass and activated more in failures than successes.

Phase 2.8d: added `chase_to_mate_skill`, a fit-free hand-authored ceiling gated on the waypoint
manifold. Branch order: gated mate-2 defer, rook escape slide, king approach, rook waiting tempo.
Per-move verification is one-ply own-move only: legal, fence intact, rook safe, no stalemate, no
third occurrence. It is not learned and is not evidence for autogrowth.

2.8d rung eval on the same 100 heldout starts, horizon 6, fixed-seed uniform black: chase
20/100=0.200, Wilson [0.133, 0.289], no own-move skill violations. Dispatcher remained
44/100=0.440; reproduced best learned seed 20270212 at 36/100=0.360. Paired chase vs dispatcher:
15 win/win, 5 win/loss, 29 loss/win, 51 loss/loss. Chase vs best learned: 11 win/win, 9 win/loss,
25 loss/win, 55 loss/loss.

Failure structure: 37 fence breaks, 16 horizons, 20 outside-domain skill fails, 6 repetitions, 1
rook-escape fail. Locally safe but not reply-robust: below the 0.60 integration threshold, so
`krk_policy` was not changed and no 200-game integration eval was run.

Decision: Phase 2.8d stops before integration. Next: 2.8d/Phase 2 review of reply-robust middle
rung design; do not claim learned discovery for this ceiling.
No-go: new TG names, new report documents, new pool/cache formats, training logic changes, `docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
