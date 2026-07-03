# Hector/ReCoN Brief

Mission: merge the Feb baseline learner, native ReCoN runtime, and TG46+ evaluation rigor into one
learner whose frozen graph beats its baseline on heldout KRK behavior with causal ablation evidence.

Current state: Phase 2.6 exact fence-establishment skill executes graph-native.

Dieted foundation result: TG46c full-M3 Mate-in-2 heldout all-reply passed 3/3 seeds after the
black-king-neighbor percept revision: 20260701=0.94, 20260702=0.95, 20260703=0.96.

Canonical dieted parent: reports/autogrowth/clean_slate_krk/dieted_foundation_v1/krk_tg46c_real_mate2_repair_seed_20260702_rev1.json

Canonical sha256: ae382d0463e35eff09e9515a715648b5d49b1e0891d127a660e036e378452eb6

Recorded finding: M4 per-key precision promotion loses distributed percept signal (0.94 -> 0.86 on
seed 20260701); promotion redesign deferred to Phase 2 (quorum composition re-compresses
distributed atoms into promotable units).

Current task: 2.5 learned gate is dispatcher-only; exact mate-in-2 remains sole verifier/binder.
Pool: 2000 self-distilled rows (300 exact positives / 1700 negatives), canonical orderer loaded
TG46c full-M3 mate2_first from the dieted parent; 20/657 keys matched because the artifact exports
top 10 positive + top 10 negative terminal rows.

Decision table over heldout, 3 train seeds, vs 2.4 ordered frame reference about 60 mean / 182 max:
threshold | recall | precision | conversion | pos frames mean/max | neg frames mean/max
recall-favor | 1.00/1.00/1.00 | 0.15/0.15/0.15 | 1.00/1.00/1.00 | 2.32/12,2.27/12,2.27/4 | 125.76/185,124.94/182,124.53/185
balanced | 0.96/0.96/0.97 | 1.00/0.95/0.91 | 0.96/0.96/0.97 | 2.21/12,2.19/12,2.21/4 | 0.00/0,0.79/110,1.25/93
precision-favor | 0.87/0.89/0.80 | 1.00/0.99/0.94 | 0.87/0.89/0.80 | 2.00/12,2.03/12,1.79/4 | 0.00/0,0.16/66,0.66/93

Adopted 2.5 operating point: balanced. Verification: seed 20261211's 425 heldout negatives were
genuinely gate-scored; threshold=0.854756, max negative score=0.714112, so 0-frame negatives were
gate declines rather than skipped evaluation.

Current task: 2.6 exact fence-establishment skill, fit-free. `fence_established` is a composed
quorum over nearest-edge branches plus rook safety; `establish_fence_skill` binds legal rook moves
and confirms only if a k=n black-reply quantifier leaves the fence established after every reply.
Fresh seed 20261231: 64/64 trainer-positive edge-rung positions established; 0/64 exact negatives
emitted a move. Frames mean/max overall=46.44/76; positives=28.75/70; negatives=64.12/76.

Next: 2.7 skill chaining: fence -> mate ladder composition.

No-go: new TG names, new report documents, new pool/cache formats, training logic changes,
`docs/autogrowth/ACTIVE_BRIEF.md`, `reports/autogrowth/pools/`, and `archive/`.
