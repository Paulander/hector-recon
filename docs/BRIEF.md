# Hector/ReCoN Brief

Mission: merge the Feb baseline learner, native ReCoN runtime, and TG46+ evaluation rigor into one
learner whose frozen graph beats its baseline on heldout KRK behavior with causal ablation evidence.
Current state: Phase 2.8a edge-mate rung v1 trained in the flat episode substrate; graph-native
learned dispatch migration is explicitly deferred.
Canonical dieted parent: reports/autogrowth/clean_slate_krk/dieted_foundation_v1/krk_tg46c_real_mate2_repair_seed_20260702_rev1.json
Canonical sha256: ae382d0463e35eff09e9515a715648b5d49b1e0891d127a660e036e378452eb6
Adopted 2.5 gate: balanced seed 20261211 threshold=0.854756; exact mate-in-2 remains verifier.

Phase 2.7b dispatcher baseline: mate-in-1 first, mate-in-2 cash-in, fallback-only threefold guard.
Full-game win rates: mate-in-<=2 50/50, fence-rung 35/50, general KRK 36/50; gap remains dominated
by fallback between established fence and mate-2 gate.

Phase 2.8a pools: reports/autogrowth/clean_slate_krk/phase2_edge_mate_v1/pools/. Banked 300
distance-1 train, 96 fresh distance-1 heldout, 300 distance-2-to-5 selfplay starts. Deeper
distribution: d2=107, d3=80, d4=63, d5=50. Distance labels used exact mate-2 confirmation after a
fast KRK validator prefilter; graph/quantifier label frames total/mean/max=5150/13.01/48.

Training: distance-1 only, contrastive terminal episode credit, black=fixed-seed uniform legal
(v1 limitation), success=exact mate-2 manifold entered within 2 white moves; failure=fence break,
rook loss, stalemate, illegal, or horizon.

Heldout manifold-entry rate:
arm | rate | endpoints
fallback scorer | 47/96=0.490 | mate2 47, horizon 39, fence-broken 10
random legal | 18/96=0.188 | mate2/mate 18, horizon 32, fence-broken 42, rook 3, stalemate 1
learned seed 20270211 | 43/96=0.448 | mate2 43, horizon 34, fence-broken 10, rook 2, stalemate 7
learned seed 20270212 | 50/96=0.521 | mate2/mate 50, horizon 24, fence-broken 15, stalemate 7
learned seed 20270213 | 42/96=0.438 | mate2/mate 42, horizon 35, fence-broken 13, rook 1, stalemate 5

Learned structure summary (affordance/veto promoted counts): 20270211=92/580, 20270212=119/552,
20270213=84/587. Finding: dense near-goal training adds more positive affordances than Phase 0, but
the substrate still learns vetoes more readily.

Decision: stop rule did not fire because one seed beat fallback, but the effect is unstable
(1/3 seeds above fallback). Next: 2.8b distance expansion + dispatcher integration, with seed
stability as the first acceptance check.
No-go: new TG names, new report documents, new pool/cache formats, training logic changes,
`docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
