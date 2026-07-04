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
side`) converted 162/200=0.810 in full games, but horizon-6 learning on 300/100 starts did not beat
dispatcher. Baselines: dispatcher 44/100=0.440, fallback 28/100=0.280, random 17/100=0.170.
Learned seeds: 35/100, 36/100, 36/100; stable but 0/3 beat dispatcher.

Phase 2.8d: added `chase_to_mate_skill`, a fit-free hand-authored ceiling gated on the waypoint
manifold. Branch order: gated mate-2 defer, rook escape slide, king approach, rook waiting tempo.
It is not learned and is not evidence for autogrowth.
Initial 2.8d rung eval on the same 100 heldout starts, horizon 6, fixed-seed uniform black: chase
20/100=0.200, no own-move skill violations. It was below the 0.60 integration threshold, so
`krk_policy` was not changed and no 200-game integration eval was run.

Phase 2.8d-fix: judge repaired to trainer-side ungated exact mate-2 audit OR actual mate; learned
gate is not ground-truth. Hard failures are confinement crossed, rook lost, stalemate, or third
occurrence; attacked rook is recoverable. Gate audit found no current positive-label judge leak.

Fixed standalone rung eval, same 100 starts, horizon 10: chase 33/100=0.330, Wilson [0.246, 0.427].
Branch counts: king approach 74, rook escape 32, tempo 228, not-applicable 29; tempo moved from old
h6 186 fires/start=1.86 to fixed h10 228 fires/start=2.28.

Stop condition: 4 skill-branch rook-loss hard failures occurred after black replies, so paired
200-game integration was not run. Rook-loss FENs include `6k1/4KR2/8/8/8/8/8/8 w - - 0 1` and
`8/8/8/8/8/8/1K3R2/3k4 w - - 0 1`. `krk_policy` has an opt-in chase flag only; default unchanged.
Decision: Phase 2.8d-fix stops before integration; repair chase rook-safety/tempo before closure.
No-go: new TG names, new report documents, new pool/cache formats, training logic changes, `docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
