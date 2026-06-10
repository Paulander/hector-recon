# Stage 7 Score Normalization Probe

Schema: `stage7_score_normalization_probe.v1`
Causal status: `non_causal`
Records: `3`

## Candidate Update

- Candidate: `cand.krk.box_shrink.score_normalized_role_arbitration.v1`
- Status: `role_owned_score_normalization_sandbox_candidate`
- Next: `sandbox_role_owned_arbitration_with_guardrails`

## Choice Counts

- `adapter_role_priority:krk.drive_to_edge:mate`: 1
- `adapter_role_priority:krk.stage0_basin:None`: 2
- `bounded_tanh_support:krk.stage0_basin:max_plies`: 3
- `forced_success_oracle:krk.drive_to_edge:mate`: 1
- `forced_success_oracle:krk.stage0_basin:None`: 2
- `provider_local_rank_support:krk.drive_to_edge:mate`: 1
- `provider_local_rank_support:krk.drive_to_edge:max_plies`: 2
- `raw:krk.stage0_basin:None`: 3
- `role_owned_normalized:krk.drive_to_edge:mate`: 1
- `role_owned_normalized:krk.stage0_basin:None`: 2

## Records

### state.069e81a609ed

FEN: `8/8/8/8/7R/2k5/4K3/8 w - - 2 2`

- `raw` -> `krk.stage0_basin` / `e2d1` outcome=`None` raw_score=`13.163832062316127` transformed=`None`
- `bounded_tanh_support` -> `krk.stage0_basin` / `e2d1` outcome=`max_plies` raw_score=`13.163832062316127` transformed=`0.8658816595859435`
- `provider_local_rank_support` -> `krk.drive_to_edge` / `e2e3` outcome=`mate` raw_score=`0.1940721580785863` transformed=`1.05`
- `adapter_role_priority` -> `krk.drive_to_edge` / `e2e3` outcome=`mate` raw_score=`0.1940721580785863` transformed=`None`
- `role_owned_normalized` -> `krk.drive_to_edge` / `e2e3` outcome=`mate` raw_score=`0.1940721580785863` transformed=`None`
- `forced_success_oracle` -> `krk.drive_to_edge` / `e2e3` outcome=`mate` raw_score=`0.1940721580785863` transformed=`None`

### state.2cc0b3e1033a

FEN: `8/8/R7/8/2k5/8/8/3K4 w - - 2 2`

- `raw` -> `krk.stage0_basin` / `a6a8` outcome=`None` raw_score=`1.409134501052089` transformed=`None`
- `bounded_tanh_support` -> `krk.stage0_basin` / `a6a8` outcome=`max_plies` raw_score=`1.409134501052089` transformed=`0.13998811168345318`
- `provider_local_rank_support` -> `krk.drive_to_edge` / `a6a8` outcome=`max_plies` raw_score=`-0.011665899415577205` transformed=`1.0`
- `adapter_role_priority` -> `krk.stage0_basin` / `a6a8` outcome=`None` raw_score=`1.409134501052089` transformed=`None`
- `role_owned_normalized` -> `krk.stage0_basin` / `a6a8` outcome=`None` raw_score=`1.409134501052089` transformed=`None`
- `forced_success_oracle` -> `krk.stage0_basin` / `a6a8` outcome=`None` raw_score=`1.409134501052089` transformed=`None`

### state.bace6f82b671

FEN: `8/8/8/R7/4k3/8/3K4/8 w - - 2 2`

- `raw` -> `krk.stage0_basin` / `a5h5` outcome=`None` raw_score=`13.653305405211634` transformed=`None`
- `bounded_tanh_support` -> `krk.stage0_basin` / `a5h5` outcome=`max_plies` raw_score=`13.653305405211634` transformed=`0.87762364691784`
- `provider_local_rank_support` -> `krk.drive_to_edge` / `d2c3` outcome=`max_plies` raw_score=`0.1418387483566025` transformed=`1.0`
- `adapter_role_priority` -> `krk.stage0_basin` / `a5h5` outcome=`None` raw_score=`13.653305405211634` transformed=`None`
- `role_owned_normalized` -> `krk.stage0_basin` / `a5h5` outcome=`None` raw_score=`13.653305405211634` transformed=`None`
- `forced_success_oracle` -> `krk.stage0_basin` / `a5h5` outcome=`None` raw_score=`13.653305405211634` transformed=`None`

