#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
EXP_DIR="$ROOT_DIR/demos/experiments/kpk_curriculum_benchmark"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%d_%H%M%S)}"
RUN_DIR="$EXP_DIR/_private/recon/$RUN_ID"

TOPOLOGY="${TOPOLOGY:-topologies/kpk_legs_topology.json}"
GAMES_PER_CYCLE="${GAMES_PER_CYCLE:-100}"
CYCLES="${CYCLES:-10}"
WIN_THRESHOLD="${WIN_THRESHOLD:-0.9}"
EXTRA_ARGS="${EXTRA_ARGS:-}"

mkdir -p "$RUN_DIR"

echo "ReCoN curriculum run"
echo "  run_id:          $RUN_ID"
echo "  topology:        $TOPOLOGY"
echo "  games_per_cycle: $GAMES_PER_CYCLE"
echo "  cycles:          $CYCLES"
echo "  win_threshold:   $WIN_THRESHOLD"

XDG_CACHE_HOME=/tmp UV_CACHE_DIR=/tmp/uv-cache uv run python "$ROOT_DIR/scripts/evolution_driver.py" \
  --topology "$TOPOLOGY" \
  --all-stages \
  --games-per-cycle "$GAMES_PER_CYCLE" \
  --cycles "$CYCLES" \
  --win-threshold "$WIN_THRESHOLD" \
  --run-name "$RUN_ID" \
  --output-dir "$RUN_DIR/reports" \
  $EXTRA_ARGS | tee "$RUN_DIR/recon_train.log"

GLOBAL_SNAP="$ROOT_DIR/snapshots/evolution/$RUN_ID"
GLOBAL_TRACE="$ROOT_DIR/traces/evolution/$RUN_ID"

if [ -d "$GLOBAL_SNAP" ]; then
  mkdir -p "$RUN_DIR/snapshots"
  cp -a "$GLOBAL_SNAP"/. "$RUN_DIR/snapshots/"
fi

if [ -d "$GLOBAL_TRACE" ]; then
  mkdir -p "$RUN_DIR/traces"
  cp -a "$GLOBAL_TRACE"/. "$RUN_DIR/traces/"
fi

GIT_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
cat > "$RUN_DIR/run_manifest.json" <<EOF
{
  "run_id": "$RUN_ID",
  "topology": "$TOPOLOGY",
  "games_per_cycle": $GAMES_PER_CYCLE,
  "cycles": $CYCLES,
  "win_threshold": $WIN_THRESHOLD,
  "git_commit": "$GIT_COMMIT"
}
EOF

echo "Wrote $RUN_DIR/run_manifest.json"

echo "ReCoN outputs in: $RUN_DIR"
