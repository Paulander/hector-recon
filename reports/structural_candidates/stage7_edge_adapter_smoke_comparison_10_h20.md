# Stage 7 Edge Adapter Smoke Comparison

- Candidate: `cand.krk.box_shrink.edge_trap_support_adapter.v1`
- Samples: 10, horizon: 20
- Baseline playouts: {'max_plies': 10}, shadows: 20

## w005
- Support weight: 0.05
- Playouts: {'max_plies': 10}, shadows: 20
- Adapter fires: 12
- Supported providers: {'krk.edge_trap_close:max_plies': 12}

## w010
- Support weight: 0.1
- Playouts: {'max_plies': 10}, shadows: 20
- Adapter fires: 12
- Supported providers: {'krk.edge_trap_close:max_plies': 12}

Result: both support weights are traceable and opt-in but target-neutral on this 10-sample smoke. No guardrails or promotion are justified; candidate remains sandboxed and needs a follow-up diagnosis of the supported `a7d7` edge-trap continuation.
