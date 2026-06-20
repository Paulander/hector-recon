# TG28b Frozen Foundation Bridge Pressure

Result: bounded failure, not advancement.

The TG27b foundation stayed frozen and sane on the bounded probe:

- Mate_In_1 sanity: 1.0
- Mate_In_2 forced-chain sanity: 1.0
- foundation M3/M4 deltas during bridge training/eval: 0/0

Bridge pressure did not appear:

- bridge heldout: 2 positions
- selected moves: 0
- null moves: 2
- reply-envelope foundation reachable count: 0
- bounded bridge foundation reachable count: 0
- failure bucket: `no_bridge_candidate_generated`

Interpretation:

Trainer-side frontier filtering can find positions that are near validator Mate_In_1/Mate_In_2 regions, but the frozen native TG27b foundation does not recognize the evaluated bridge candidates as entering its learned basin under the bounded materialized continuation probe. A top-8 deep probe also timed out, so the next repair should be cached/indexed frozen-foundation response and candidate retrieval, not broader edge/fence scaling.
