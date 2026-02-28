#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

from benchmark_common import REPO_ROOT, latest_run_dir, timestamp_utc, write_json


def _load_json(path: Path) -> Dict[str, Any]:
    import json

    return json.loads(path.read_text())


def _find_recon_summary_files(run_dir: Path) -> Dict[int, Path]:
    files: Dict[int, Path] = {}
    for path in run_dir.rglob("evolution_summary.json"):
        # expecting .../stage<idx>/evolution_summary.json
        parent = path.parent.name
        if parent.startswith("stage"):
            try:
                stage = int(parent.replace("stage", ""))
            except ValueError:
                continue
            files[stage] = path
    return files


def _normalize_recon(run_dir: Path) -> Dict[str, Any]:
    by_stage = _find_recon_summary_files(run_dir)
    rows: List[Dict[str, Any]] = []
    for stage in sorted(by_stage.keys()):
        payload = _load_json(by_stage[stage])
        cycles = payload.get("cycles", [])
        final_cycle_win = cycles[-1].get("win_rate", 0.0) if cycles else 0.0
        rows.append(
            {
                "stage": stage,
                "method": "recon",
                "success_rate": float(final_cycle_win),
                "win_rate": float(final_cycle_win),
                "promotion_rate": 0.0,
                "avg_moves": None,
                "source": str(by_stage[stage]),
            }
        )
    return {"method": "recon", "stage_results": rows, "run_dir": str(run_dir)}


def _normalize_direct(payload: Dict[str, Any], method: str, source: Path) -> Dict[str, Any]:
    rows = []
    for row in payload.get("stage_results", []):
        rows.append(
            {
                "stage": int(row["stage"]),
                "method": method,
                "success_rate": float(row.get("success_rate", 0.0)),
                "win_rate": float(row.get("win_rate", 0.0)),
                "promotion_rate": float(row.get("promotion_rate", 0.0)),
                "avg_moves": float(row.get("avg_moves", 0.0)),
                "source": str(source),
            }
        )
    return {"method": method, "stage_results": rows, "run_dir": str(source.parent)}


def _to_markdown(rows: List[Dict[str, Any]]) -> str:
    lines = []
    lines.append("| Method | Stage | Success | Win | Promotion | Avg Moves |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in rows:
        avg_moves = "-" if row["avg_moves"] is None else f"{row['avg_moves']:.1f}"
        lines.append(
            f"| {row['method']} | {row['stage']} | {row['success_rate']:.3f} | "
            f"{row['win_rate']:.3f} | {row['promotion_rate']:.3f} | {avg_moves} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate benchmark results")
    parser.add_argument(
        "--recon-dir",
        type=Path,
        default=None,
        help="ReCoN run directory under _private/recon",
    )
    parser.add_argument(
        "--ppo-results",
        type=Path,
        default=None,
        help="Path to ppo_curriculum_results.json",
    )
    parser.add_argument(
        "--heuristic-results",
        type=Path,
        default=None,
        help="Path to heuristic_results.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("demos/experiments/kpk_curriculum_benchmark/outputs"),
        help="Summary output directory",
    )
    args = parser.parse_args()

    base = REPO_ROOT / "demos/experiments/kpk_curriculum_benchmark/_private"

    recon_dir = args.recon_dir or latest_run_dir(base / "recon")
    if recon_dir is None:
        raise SystemExit("No ReCoN run found. Pass --recon-dir.")

    ppo_results = args.ppo_results
    if ppo_results is None:
        latest_ppo = latest_run_dir(base / "ppo")
        if latest_ppo is None:
            raise SystemExit("No PPO run found. Pass --ppo-results.")
        ppo_results = latest_ppo / "ppo_curriculum_results.json"

    heuristic_results = args.heuristic_results
    if heuristic_results is None:
        latest_heur = latest_run_dir(base / "heuristic")
        if latest_heur is None:
            raise SystemExit("No heuristic run found. Pass --heuristic-results.")
        heuristic_results = latest_heur / "heuristic_results.json"

    if not ppo_results.exists():
        raise SystemExit(f"Missing PPO results file: {ppo_results}")
    if not heuristic_results.exists():
        raise SystemExit(f"Missing heuristic results file: {heuristic_results}")

    recon_norm = _normalize_recon(recon_dir)
    ppo_norm = _normalize_direct(_load_json(ppo_results), "ppo", ppo_results)
    heur_norm = _normalize_direct(_load_json(heuristic_results), "heuristic", heuristic_results)

    all_rows = recon_norm["stage_results"] + ppo_norm["stage_results"] + heur_norm["stage_results"]
    all_rows.sort(key=lambda r: (r["stage"], r["method"]))

    grouped: Dict[str, Dict[str, float]] = {}
    for row in all_rows:
        grouped.setdefault(row["method"], {"sum": 0.0, "n": 0})
        grouped[row["method"]]["sum"] += row["success_rate"]
        grouped[row["method"]]["n"] += 1

    aggregate = {
        method: (data["sum"] / data["n"] if data["n"] else 0.0)
        for method, data in grouped.items()
    }

    payload = {
        "created_utc": timestamp_utc(),
        "sources": {
            "recon_dir": str(recon_dir),
            "ppo_results": str(ppo_results),
            "heuristic_results": str(heuristic_results),
        },
        "aggregate_success_rate_mean": aggregate,
        "rows": all_rows,
    }

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "latest_summary.json", payload)
    (out_dir / "latest_summary.md").write_text(_to_markdown(all_rows))
    print(f"Wrote {out_dir / 'latest_summary.json'}")
    print(f"Wrote {out_dir / 'latest_summary.md'}")


if __name__ == "__main__":
    main()
