# Phase 3.20 Conditional-Gate Composites

- Result: conditional gate channel is causal; terminal inertness finding is overturned.
- Correction: 3.19 probation dose tests were confounded because PROBATION composites were requested but not predicate-evaluated; guard now includes PROBATION.
- Gate mechanism: PROBATION/MATURE composites with `action_pattern:*` children stop acting as addends and gate eligible moves; host-best move is chosen inside the gated set.
- Constructed proof passed: row0 host `d5c4` -> gated `d5d4`, candidate count 9, via `action_pattern:file_delta_magnitude=0 AND file_delta_sign=0`.
- Seeds 31-35 confirmed gate cells: `0/3/2/2/5` (12 total).
- Gate validation was non-silent: nonzero discordant dose records `40/60/40/48/48` (236 total).
- Stage B host+confirmed vs host wins: `+0/+8/+3/+12/+6`.
- Controlled heldout ablation no-op passed all seeds.
- Confirmed heldout classes: 9 load-bearing / 2 inert / 1 harmful.
- Cross-rung survivor: seed35 Stage-A-born `black_king_edge_after=0 AND white_rook_to_black_king_after=6`, heldout delta +1 on Stage B.
- Confirmed recurrence: no family reached >=3/5 seeds; best confirmed family recurred 2/5.
- Stop note: seed33 hit `population_unstable_after_stage_b`; no gate regression or audition starvation stop.
- Next: keep gate routing; tighten selectivity/stability so confirmed gates recur and harmful broad gates are filtered.
