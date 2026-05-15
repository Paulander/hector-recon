#!/usr/bin/env python3
"""Evaluate whether a provider topology can be promoted from diagnostics.

This is an offline gate. It does not affect runtime routing, packets, stats, or
topology. It classifies a candidate as promoted, overlay-only, or quarantine
from already-produced validation artifacts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _playout_rate(metrics: dict[str, Any], key: str) -> float:
    playouts = metrics.get("playouts", {}) or {}
    total = sum(int(value) for value in playouts.values())
    if total <= 0:
        return 0.0
    return float(playouts.get(key, 0) or 0) / float(total)


def _rate(metrics: dict[str, Any], key: str) -> float:
    total = float(metrics.get("total", 0) or 0)
    if total <= 0:
        return 0.0
    return float(metrics.get(key, 0) or 0) / total


def evaluate_artifact(
    path: Path,
    *,
    min_improved_rate: float,
    max_worsened_rate: float,
    min_mate_rate: float,
    max_max_plies_rate: float,
    max_shadow_candidates: int,
) -> dict[str, Any]:
    metrics = _load(path)
    reasons: list[str] = []
    improved_rate = _rate(metrics, "improved")
    worsened_rate = _rate(metrics, "worsened")
    mate_rate = _playout_rate(metrics, "mate")
    max_plies_rate = _playout_rate(metrics, "max_plies")
    shadow_count = int(
        metrics.get("shadow_candidate_count", metrics.get("shadow_candidates_count", 0)) or 0
    )
    if not shadow_count and isinstance(metrics.get("shadow_candidates"), list):
        shadow_count = len(metrics.get("shadow_candidates") or [])

    if improved_rate < min_improved_rate:
        reasons.append(f"improved_rate={improved_rate:.3f} < {min_improved_rate:.3f}")
    if worsened_rate > max_worsened_rate:
        reasons.append(f"worsened_rate={worsened_rate:.3f} > {max_worsened_rate:.3f}")
    if mate_rate < min_mate_rate:
        reasons.append(f"mate_rate={mate_rate:.3f} < {min_mate_rate:.3f}")
    if max_plies_rate > max_max_plies_rate:
        reasons.append(f"max_plies_rate={max_plies_rate:.3f} > {max_max_plies_rate:.3f}")
    if shadow_count > max_shadow_candidates:
        reasons.append(f"shadow_candidates={shadow_count} > {max_shadow_candidates}")

    return {
        "path": str(path),
        "label": metrics.get("label"),
        "total": int(metrics.get("total", 0) or 0),
        "improved_rate": improved_rate,
        "worsened_rate": worsened_rate,
        "mate_rate": mate_rate,
        "max_plies_rate": max_plies_rate,
        "shadow_candidates": shadow_count,
        "passed": not reasons,
        "failure_reasons": reasons,
    }


def evaluate_promotion(
    *,
    stage_artifact: Path,
    guardrail_artifacts: list[Path],
    min_improved_rate: float,
    max_worsened_rate: float,
    min_mate_rate: float,
    max_max_plies_rate: float,
    max_shadow_candidates: int,
) -> dict[str, Any]:
    stage = evaluate_artifact(
        stage_artifact,
        min_improved_rate=min_improved_rate,
        max_worsened_rate=max_worsened_rate,
        min_mate_rate=min_mate_rate,
        max_max_plies_rate=max_max_plies_rate,
        max_shadow_candidates=max_shadow_candidates,
    )
    guardrails = [
        evaluate_artifact(
            path,
            min_improved_rate=min_improved_rate,
            max_worsened_rate=max_worsened_rate,
            min_mate_rate=min_mate_rate,
            max_max_plies_rate=max_max_plies_rate,
            max_shadow_candidates=max_shadow_candidates,
        )
        for path in guardrail_artifacts
    ]
    failures = []
    if not stage["passed"]:
        failures.append({"kind": "stage", **stage})
    failures.extend({"kind": "guardrail", **item} for item in guardrails if not item["passed"])
    if stage["passed"] and not failures:
        status = "promoted"
    elif stage["passed"]:
        status = "overlay_only"
    else:
        status = "quarantine"
    return {
        "schema_version": "provider_promotion_eval.v1",
        "promotion_status": status,
        "stage": stage,
        "guardrails": guardrails,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate provider promotion from diagnostics")
    parser.add_argument("--stage-artifact", type=Path, required=True)
    parser.add_argument("--guardrail-artifact", type=Path, action="append", default=[])
    parser.add_argument("--min-improved-rate", type=float, default=0.70)
    parser.add_argument("--max-worsened-rate", type=float, default=0.20)
    parser.add_argument("--min-mate-rate", type=float, default=0.65)
    parser.add_argument("--max-max-plies-rate", type=float, default=0.25)
    parser.add_argument("--max-shadow-candidates", type=int, default=0)
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args()

    result = evaluate_promotion(
        stage_artifact=args.stage_artifact,
        guardrail_artifacts=list(args.guardrail_artifact),
        min_improved_rate=args.min_improved_rate,
        max_worsened_rate=args.max_worsened_rate,
        min_mate_rate=args.min_mate_rate,
        max_max_plies_rate=args.max_max_plies_rate,
        max_shadow_candidates=args.max_shadow_candidates,
    )
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
