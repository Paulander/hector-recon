#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DEMO_DIR="$ROOT_DIR/demos/experiments/endgame_handover_continuous"
WEIGHTS_DIR="$DEMO_DIR/weights_snapshot"
FEN_FILE="$DEMO_DIR/data/near_promo.fens"

mkdir -p "$DEMO_DIR/outputs"

PACK="$DEMO_DIR/_private/fullgame_router_consol.json"
if [ ! -f "$PACK" ]; then
  echo "Missing router pack: $PACK"
  echo "Run: $DEMO_DIR/run_train_router.sh <num_games>"
  exit 1
fi

if [ ! -f "$FEN_FILE" ]; then
  echo "Missing FEN file: $FEN_FILE"
  exit 1
fi

FEN="$(grep -v '^[[:space:]]*$' "$FEN_FILE" | head -n 1)"
if [ -z "$FEN" ]; then
  echo "No usable FEN found in: $FEN_FILE"
  exit 1
fi

OUT_JSON="$DEMO_DIR/outputs/bridge_demo_export.json"
MOVES="${MOVES:-120}"

set +e
XDG_CACHE_HOME=/tmp UV_CACHE_DIR=/tmp/uv-cache uv run python "$ROOT_DIR/demos/visualization/export_bridge_demo.py" \
  --fen "$FEN" \
  --moves "$MOVES" \
  --weights-dir "$WEIGHTS_DIR" \
  --fullgame-pack "$PACK" \
  --router-mode learned_affordance \
  --router-epsilon 0.05 \
  --output "$OUT_JSON"
STATUS=$?
set -e

if [ $STATUS -ne 0 ] && [ ! -f "$OUT_JSON" ]; then
  echo "Export failed and no output JSON was produced."
  exit $STATUS
fi

if [ $STATUS -ne 0 ]; then
  echo "Export produced JSON but ended with non-zero status (likely draw/no mate)."
fi

echo "Wrote: $OUT_JSON"
echo "Open viewer: $ROOT_DIR/demos/visualization/bridge_demo.html"
