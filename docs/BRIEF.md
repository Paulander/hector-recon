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

Phase 2.8c diagnostics: fresh 200-game fence/general pools, black=fixed-seed uniform legal, paired
fixed dispatcher vs identical dispatcher with `enter_mate2` disabled. Fence fixed and disabled both
won 133/200=0.665, Wilson 95% [0.597, 0.727], paired table 133 win/win and 67 loss/loss. General
fixed and disabled both won 144/200=0.720, Wilson [0.654, 0.778], paired table 144 win/win and
56 loss/loss. Therefore `enter_mate2` has no measured system-level effect on these pools.

Draw/loss structure: fence fixed nonwins 67; only 1 had `enter_mate2` fire, once; shuffle declines
0. General fixed nonwins 56; `enter_mate2` fired in 0; shuffle declines 0. Draws were repetition
dominant: fence 54 repetitions, 7 fifty-move, 6 rook-loss; general 50 repetitions, 6 fifty-move.
Repetition-guard activations: fence 48, general 68. Only multi-enter game: general index 10
(`8/8/2K5/6k1/8/R7/8/8 w - - 0 1`) with two firings.

Waypoint validation: `king_support_waypoint = fence_established AND white king Chebyshev<=2 from
black king on nearest-edge interior side`. Harvested 200/200 from game logs. Current dispatcher
converted 162/200=0.810, Wilson [0.750, 0.858]; failures 38 = 27 repetition, 6 rook-loss, 5
fifty-move. This waypoint is not a solved middle manifold.

Decision: no code fix, no training, no threshold move. Next: 2.8c middle-rung design
(fence-maintenance + king-approach) against waypoint data.

No-go: new TG names, new report documents, new pool/cache formats, training logic changes,
`docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
