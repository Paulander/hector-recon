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

Phase 2.8c diagnostics: paired 200-game fixed-vs-enter-disabled eval found no system effect from
`enter_mate2` on fence/general pools. Fence both 133/200=0.665; general both 144/200=0.720.
Waypoint validation harvested 200 game-log states satisfying `fence_established AND WK Chebyshev<=2
on nearest-edge interior side`; current dispatcher converted 162/200=0.810 in full games, with 38
failures: 27 repetition, 6 rook-loss, 5 fifty-move.

Phase 2.8c middle-rung training: waypoint-to-mate learned policy, no dispatcher integration.
Pool: 400 starts = 200 harvested waypoints + 200 generator-fresh waypoints; split 300 train / 100
heldout. Episode success = exact mate-2 audit confirms within 6 white moves, with direct mate as
terminal success; hard fail on fence break, rook loss, stalemate, or third occurrence. Black is
fixed-seed uniform legal; holding the fence has no reward.

Heldout baselines on identical starts/horizon: current dispatcher 44/100=0.440 Wilson [0.347,
0.538], fallback scorer 28/100=0.280 [0.201, 0.375], random legal 17/100=0.170 [0.109, 0.255].
Learned seeds: 20270211 35/100=0.350, 20270212 36/100=0.360, 20270213 36/100=0.360; spread 0.01.
Paired vs dispatcher: seed 20270211 win/loss 2 and loss/win 11; seeds 20270212/20270213 win/loss
2 and loss/win 10 each. Stable but 0/3 seeds beat dispatcher, so no 2.8d integration.

Discovery instrument: promoted affordance/veto counts were 1560/6973, 1413/7101, 1331/7213.
`king_support_l_shape` and `king_pair_knight_distance_like` each carried about 1.5% of total abs
weight mass; activation was higher in failures (~0.48-0.54) than successes (~0.24-0.28).

Decision: middle-rung learned waypoint policy beats fallback/random but not current dispatcher.
Next: 2.8c middle-rung review; do not integrate.
No-go: new TG names, new report documents, new pool/cache formats, training logic changes, `docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
