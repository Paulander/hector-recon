# TG28d Foundation-Backed Bridge Frontier

Artifact: `reports/autogrowth/krk_autogrowth_tg28d_foundation_backed_bridge_frontier.json`

TG28d proves a very small foundation-backed bridge frontier can be generated and selected through native graph-mediated structure. This is not an edge/fence competence claim and not a broad KRK advancement.

Key result:

- `checkpoint_pass`: true
- foundation frozen: true
- foundation cache/live mismatches: 0
- foundation sanity: Mate_In_1 1.0, Mate_In_2 1.0
- foundation cache states: 118
- foundation-positive states in bounded sample: 6
- generated bridge-frontier positions: 4
- generated all-reply bridge positions: 4
- heldout frontier positions: 2
- bridge candidates on heldout: 1
- selected graph-mediated bridge moves: 1
- reply-envelope foundation-reachable selected moves: 1
- same-graph foundation continuations: 1
- rook blunders: 0
- stalemate avoidance: 1.0
- edge-only M3 updates: 54
- bridge-terminal M3 updates: 42
- scheduler equivalence mismatches: 0

Important bounds:

- Canonical artifact uses a small bounded foundation: 4 Mate_In_1 train, 2 Mate_In_1 heldout, 1 Mate_In_2 train, 1 Mate_In_2 heldout.
- Bridge frontier is 2 train and 2 heldout positions.
- This scale was chosen because larger 16/8/8/4 foundation runs made frontier generation/evaluation too slow for the checkpoint loop.
- Seed-pool generation is now capped and recorded so future runs can distinguish seed-pool exhaustion from cache-response sparsity.

Causal checks on one ablation position:

- Disabling cache retrieval or live foundation-response query collapses bridge candidates to 0 and selection to null.
- Masking bridge-pressure, foundation-response, edge/fence, action-delta, actuator, safety/veto, Mate_In_2 foundation quorum, or internal-attention terminals collapses selection to null.
- Masking Mate_In_1 foundation quorum does not collapse this specific selected bridge, because the selected continuation depends on the Mate_In_2/foundation-chain path in this tiny slice.

Interpretation:

TG28c showed safe bridge candidates were not recognized by the frozen foundation basin. TG28d shows that if the trainer builds positions outward from frozen foundation-positive states, native bridge/foundation-response terminals can select a safe bridge move that hands off to the frozen same-graph foundation. The result is a bounded proof of bridge-frontier viability, not evidence that generic edge/fence now generalizes.

Next decision:

Scale TG28d cautiously by improving persisted/indexed foundation-backed pool generation before returning to edge/fence. Do not broaden KRK, unfreeze TG27b, or claim edge/fence competence from this tiny filtered frontier.
