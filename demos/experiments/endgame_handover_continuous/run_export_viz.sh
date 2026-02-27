#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DEMO_DIR="$ROOT_DIR/demos/experiments/endgame_handover_continuous"
WEIGHTS_DIR="$DEMO_DIR/weights_snapshot"

mkdir -p "$DEMO_DIR/outputs"

PACK="$DEMO_DIR/_private/fullgame_router_consol.json"
if [ ! -f "$PACK" ]; then
  echo "Missing router pack: $PACK"
  echo "Run: $DEMO_DIR/run_train_router.sh <num_games>"
  exit 1
fi

OUT_JSON="$DEMO_DIR/outputs/bridge_demo_export.json"

XDG_CACHE_HOME=/tmp UV_CACHE_DIR=/tmp/uv-cache uv run python "$ROOT_DIR/demos/visualization/export_bridge_demo.py" \
  --fen-file "$DEMO_DIR/data/near_promo.fens" \
  --weights-dir "$WEIGHTS_DIR" \
  --fullgame-pack "$PACK" \
  --router-mode learned_affordance \
  --router-epsilon 0.05 \
  --out "$OUT_JSON"

echo "Wrote: $OUT_JSON"
echo "Open viewer: $ROOT_DIR/demos/visualization/bridge_demo.html"

