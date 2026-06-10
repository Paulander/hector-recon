# Stage 7 Edge Adapter Smoke Comparison

- Candidate: `cand.krk.box_shrink.edge_trap_support_adapter.v1`
- Samples: 10, horizon: 20, support: 0.05
- Baseline playouts: {'max_plies': 10}, shadows: 20
- Adapter playouts: {'max_plies': 10}, shadows: 20
- Adapter fires: 12
- Supported providers: {'krk.edge_trap_close:max_plies': 12}

Result: adapter support is traceable and opt-in, but 0.05 support did not improve the 10-sample Stage 7 target. Candidate remains sandboxed; no guardrails or promotion are justified from this smoke.
