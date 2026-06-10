from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


def find_repo_root(start: Path) -> Path:
    for parent in [start] + list(start.parents):
        if (parent / "pyproject.toml").exists() and (parent / "src").exists():
            return parent
    return start.parents[4]


THIS_FILE = Path(__file__).resolve()
REPO_ROOT = find_repo_root(THIS_FILE.parent)

SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from recon_lite_chess.training.generators import KPK_STAGES, generate_kpk_curriculum_position


DEFAULT_STAGES = list(range(8))


def timestamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def parse_stage_list(raw: str) -> List[int]:
    stages = [int(part.strip()) for part in raw.split(",") if part.strip()]
    if not stages:
        raise ValueError("Stage list cannot be empty")
    max_idx = len(KPK_STAGES) - 1
    for stage in stages:
        if stage < 0 or stage > max_idx:
            raise ValueError(f"Invalid stage {stage}. Valid range is 0..{max_idx}")
    return stages


def parse_int_list(raw: str) -> List[int]:
    values = [int(part.strip()) for part in raw.split(",") if part.strip()]
    if not values:
        raise ValueError("Value list cannot be empty")
    return values


def expand_per_stage(values: List[int], stage_count: int) -> List[int]:
    if len(values) == 1:
        return values * stage_count
    if len(values) != stage_count:
        raise ValueError(
            f"Expected either 1 value or {stage_count} values, got {len(values)}"
        )
    return values


def ensure_eval_fens(
    eval_dir: Path,
    stages: List[int],
    per_stage: int,
    seed: int,
    force: bool = False,
) -> Dict[int, Path]:
    eval_dir.mkdir(parents=True, exist_ok=True)
    out: Dict[int, Path] = {}
    for stage in stages:
        path = eval_dir / f"stage_{stage:02d}.fens"
        if path.exists() and not force:
            lines = [ln.strip() for ln in path.read_text().splitlines() if ln.strip()]
            if len(lines) >= per_stage:
                out[stage] = path
                continue

        # Deterministic generation per stage.
        random.seed(seed + stage * 100003)
        lines = []
        for _ in range(per_stage):
            board = generate_kpk_curriculum_position(KPK_STAGES[stage])
            lines.append(board.fen())
        path.write_text("\n".join(lines) + "\n")
        out[stage] = path
    return out


def load_fens(path: Path) -> List[str]:
    return [ln.strip() for ln in path.read_text().splitlines() if ln.strip() and not ln.startswith("#")]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def latest_run_dir(base_dir: Path) -> Path | None:
    if not base_dir.exists():
        return None
    dirs = [p for p in base_dir.iterdir() if p.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda p: p.stat().st_mtime)
