# Stage 7 Edge Adapter Smoke Comparison

- Candidate: `cand.krk.box_shrink.edge_trap_support_adapter.v1`
- Samples: 10, horizon: 20
- Baseline playouts: {'max_plies': 10}, shadows: 20

## w005
- Support weight: 0.05
- Playouts: {'max_plies': 10}, shadows: 20
- Adapter fires: 0
- Supported providers: {}

## w010
- Support weight: 0.1
- Playouts: {'max_plies': 10}, shadows: 20
- Adapter fires: 0
- Supported providers: {}

Result: the original edge-trap support hypothesis was overbroad. The supported `a7d7` move does not convert under current continuation, so the adapter now requires actual `white_king_support_available`; that blocks this repeated unsupported state. The candidate remains sandboxed and should not be guardrailed or promoted.
