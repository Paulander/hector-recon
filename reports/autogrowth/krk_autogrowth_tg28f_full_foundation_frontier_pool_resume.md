# TG28f Full Foundation Frontier Pool Resume

TG28f completed the full TG27b persisted frontier-pool target.

- Artifact: `reports/autogrowth/krk_autogrowth_tg28f_full_foundation_frontier_pool_resume.json`
- Pool: `reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl`
- Index: `reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool_index.json`
- Checkpoint pass: `true`
- Interpretation: `full_tg27b_persisted_pool_graph_mediated_bridge_handoff`

## Result

The full TG27b foundation configuration was used: 32 Mate_In_1 train, 16 Mate_In_1 heldout, 16 Mate_In_2 train, and 8 Mate_In_2 heldout. No compact fallback was used.

The persisted pool reached the requested 8/4/4 target:

- train: 8
- heldout: 4
- regression: 4
- generation attempts: 103
- accepted entries: 16
- acceptance rate: 0.1553
- timeout count: 0
- safety-filter rejections: 0
- direct-foundation rejections: 62
- no-foundation-response rejections: 9

Heldout bridge evaluation selected graph-mediated bridge moves for all 4 heldout positions:

- selected moves: 4/4
- reply-envelope foundation reachable: 4/4
- foundation handoff conversions: 4
- same-graph foundation continuations: 4
- rook blunders: 0
- stalemate avoidance: 1.0
- scheduler equivalence mismatches: 0

Foundation remained frozen:

- foundation Mate_In_1 accuracy: 1.0
- foundation Mate_In_2 conversion rate: 1.0
- cache/live mismatches: 0
- foundation M3 deltas during pool generation, bridge training, and eval: 0
- foundation M4 deltas during pool generation, bridge training, and eval: 0

Bridge-layer updates were local:

- edge-only M3 updates: 432
- bridge-terminal M3 updates: 336
- M4 promotion count for edge/bridge terminal kinds: 0

## Causal Checks

Ablations collapse the selected bridge behavior when cache retrieval, bridge pressure, foundation-response terminals, edge/fence terminals, action-delta terminals, actuator terminals, safety/veto terminals, internal-attention terminals, or Mate_In_2 foundation quorum are masked.

Two caveats remain:

- `disable_reply_envelope_foundation_checks` still selects 1/4, so the bridge layer has one position where other graph evidence can still drive a selected move without the reply-envelope check.
- `mask_frozen_mate1_foundation_quorum` still selects 1/4, so the heldout slice is not solely dependent on Mate_In_1 quorum; Mate_In_2 foundation quorum remains decisive in this run.

## Interpretation

This is a full-config frontier-pool advancement over TG28e. It fixes the compact-fallback limitation and shows that persisted/indexed foundation-backed frontier generation can produce a complete 8/4/4 pool under the full TG27b foundation.

It is not yet broad edge/fence competence. The training distribution is still foundation-backed bridge-frontier positions selected by trainer-side scheduling. The result proves the bridge-frontier runway can be scaled to the full foundation configuration while preserving the purity boundary.

Next decision should be either external audit or a cautious scale-up of this same full-config frontier pool, with filtered frontier success kept separate from unfiltered edge/fence generalization.
