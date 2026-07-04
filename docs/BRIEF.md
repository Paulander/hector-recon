# Hector/ReCoN Brief

Mission: merge the Feb baseline learner, native ReCoN runtime, and TG46+ evaluation rigor into one
learner whose frozen graph beats its baseline on heldout KRK behavior with causal ablation evidence.
Canonical dieted parent: reports/autogrowth/clean_slate_krk/dieted_foundation_v1/krk_tg46c_real_mate2_repair_seed_20260702_rev1.json
Canonical sha256: ae382d0463e35eff09e9515a715648b5d49b1e0891d127a660e036e378452eb6
Adopted 2.5 gate: balanced seed 20261211 threshold=0.854756; exact mate-in-2 remains verifier.

Standing spec: move loops state polarity explicitly. Learned gates/priors are dispatch-layer only;
labels, strata, success judgments, and reported ground truth use exact ungated audits.
Reclassified call sites: phase2_edge_mate_v1 pool labels, 2.8e true-middle heldout construction, 2.8e policy success judge, and 2.8d-fix chase rung judge.

Phase 2.8b-fix: `enter_mate2_skill` repaired from helpful-opponent existential reply semantics to
universal all-reply semantics. It is exact mate-in-3 restricted to edge/fence distance-1 closure;
the bright line is fixed here: no mate-4 exactification.

Phase 2.8c/2.8d were confounded by mixed strata. Re-stratification found the old waypoint heldout
was 26 mate1-now / 8 mate2-now / 2 distance-1 / 64 true-middle; universal-d1 heldout was
16 mate1-now / 24 distance-1 / 0 true-middle. Full table: reports/autogrowth/clean_slate_krk/phase2_edge_mate_v1/phase2_8e_pool_strata_summary.json.

Phase 2.8e clean true-middle heldout: 100 starts, all from existing true-middle heldout rows; no
fresh rows needed. Evaluation horizon 10, black fixed-seed uniform legal, success = ungated exact
mate2 OR actual mate, hard failures = confinement crossed / rook lost / stalemate / repetition.

True-middle conversion: dispatcher 30/100=0.300 Wilson [0.219, 0.396]; fallback 30/100=0.300
[0.219, 0.396]; best 2.8c learned seed 20270212 25/100=0.250 [0.175, 0.343]; fixed chase
31/100=0.310 [0.228, 0.406]. Chase is not interval-separated from dispatcher.

Paired on true-middle: chase vs dispatcher = 17 win/win, 14 win/loss, 13 loss/win, 56 loss/loss.
Learned vs dispatcher = 23 win/win, 2 win/loss, 7 loss/win, 68 loss/loss. Fallback matched
dispatcher outcomes on this heldout: 30 win/win, 70 loss/loss.

Chase rook-loss audit: all four known losses were black replies capturing the rook after a
chase-bound move, so they are skill bugs, not follow-on fallback behavior. Strata: three
true-middle, one mate1-now. Example FENs: `6k1/4KR2/8/8/8/8/8/8 w - - 0 1` and
`8/8/8/8/8/8/1K3R2/3k4 w - - 0 1`.
Integration no-adopt: Phase 2.8i paired 200 games with-chase 137/200 vs without 134/200 (+0.015), paired 128 win/win, 9 loss/win, 6 win/loss, 57 loss/loss; repetitions 61 vs 56; skill violations 0.
Phase 2.8j forensics replay of 2.8i seeds found no handoff hole: with-chase nonwins 63, ungated exact mate2/mate3 confirmations skipped by dispatcher 0, chase third-occurrence binds 0.
Decision: chase ceiling final at 80/100 corrected standalone; residual gap repetition/not_applicable/tempo is DECLARED the first autonomous-discovery target (2.9); no further hand branches.
No-go: new TG names, new report documents, training logic changes, `docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
