# Endgame Handover (Continuous Router) Demo

Goal: demonstrate KPK -> KQK handover using the *learned/continuous* router in a fixed unified topology.

This folder is intended to be self-contained for running + demoing:
- pre-trained weight packs snapshot (under `weights_snapshot/`)
- a bridge FEN set (under `data/`)
- simple scripts to (optionally) refresh KQK, train router weights, and export a visualization JSON

## What this demo shows

1) **Handover event** (promotion changes the situation so KPK becomes irrelevant and KQK becomes relevant).
2) **Continuous routing**: subgraph choice uses `score = signal * learned_gate_weight` (epsilon-greedy optional).
3) **Inspectability**: exported frames include router signals/weights/scores plus the chessboard.

## Artifacts

- Weight snapshot directory: `demos/experiments/endgame_handover_continuous/weights_snapshot/`
  - Expected files:
    - `fullgame_consol.json`
    - `kpk_consol.json`
    - `kqk_consol.json`
    - `krk_consol.json` (optional; not required for the KPK->KQK bridge)
- Bridge FENs: `demos/experiments/endgame_handover_continuous/data/near_promo.fens`

## Quickstart (recommended)

1) Train router weights on near-promotion positions (writes a private pack):
   - `./demos/experiments/endgame_handover_continuous/run_train_router.sh 500`

2) Export visualization JSON for the bridge demo viewer:
   - `./demos/experiments/endgame_handover_continuous/run_export_viz.sh`
   - Uses the first non-empty FEN from `data/near_promo.fens`
   - Optional move budget override: `MOVES=160 ./demos/experiments/endgame_handover_continuous/run_export_viz.sh`

3) Open the viewer:
   - open `demos/visualization/bridge_demo.html`
   - load `demos/experiments/endgame_handover_continuous/outputs/bridge_demo_export.json`

## Optional: sanity-check the subgraphs

- `./demos/experiments/endgame_handover_continuous/run_eval_subgraphs.sh`

Notes:
- All scripts set `XDG_CACHE_HOME=/tmp` and `UV_CACHE_DIR=/tmp/uv-cache` to avoid uv cache permission issues.
- Outputs are written under `_private/` and `outputs/` and are gitignored.
