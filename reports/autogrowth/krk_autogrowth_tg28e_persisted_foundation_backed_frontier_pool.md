# TG28e Persisted Foundation-Backed Frontier Pool

Artifact: `reports/autogrowth/krk_autogrowth_tg28e_persisted_foundation_backed_frontier_pool.json`

TG28e separates foundation-backed frontier generation from bridge training/evaluation by writing a resumable JSONL pool plus index. This is an infrastructure checkpoint, not edge/fence competence.

Result:

- `checkpoint_pass`: true
- `checkpoint_interpretation`: `persisted_pool_infrastructure_diagnostic_pass`
- full TG27b foundation config used: false
- compact fallback used: true
- foundation cache/live mismatches: 0
- foundation sanity: Mate_In_1 1.0, Mate_In_2 1.0
- pool entries: 8
- pool split: 4 train / 2 heldout / 2 regression
- generation attempts: 93
- all-reply bridge entries: 8
- heldout selected moves from persisted pool: 2/2
- reply-envelope foundation-reachable selected moves: 2/2
- foundation handoff conversions: 2
- same-graph foundation continuations: 2
- rook blunders: 0
- stalemate avoidance: 1.0
- scheduler equivalence mismatches: 0
- edge-only M3 updates: 108
- bridge-terminal M3 updates: 84

Throughput:

- pool generation: 272.76 seconds
- bridge training: 1.44 seconds
- bridge eval: 8.39 seconds
- ablations: 0.17 seconds
- total run: 380.40 seconds
- average seconds per accepted pool entry: 34.09
- rejected safe candidates with no foundation response: 34
- seed-pool exhaustion count: 3

Full-config probe:

The first full TG27b attempt used 32/16 Mate_In_1 and 16/8 Mate_In_2 foundation counts. It reached clean foundation sanity and persisted 6 train entries, but hit the 15-minute cap before completing the requested 8/4/4 pool. That confirms the TG28d diagnosis: full-foundation frontier pool generation is feasible but still too slow for the current checkpoint loop.

Causal checks:

- Disabling cache retrieval or live foundation response query collapses selection to 0.
- Masking foundation-response, bridge-pressure, edge/fence, action-delta, actuator, safety/veto, Mate_In_2 foundation quorum, or internal-attention terminals collapses selected moves to 0 on the ablation slice.
- Masking Mate_In_1 foundation quorum does not collapse this compact slice because the selected continuation flows through the Mate_In_2/foundation-chain path.

Interpretation:

TG28e passes diagnostically: the persisted pool format, resume/dedup path, pool index, timing counters, and graph-mediated bridge evaluation from persisted entries work. It does not pass as a full advancement because the canonical completed artifact uses the compact foundation fallback.

Next decision:

Optimize persisted pool generation before returning to generic edge/fence. The likely next checkpoint should resume full TG27b pool generation with better indexed anchor expansion and periodic complete artifacts, not change the learning architecture.
