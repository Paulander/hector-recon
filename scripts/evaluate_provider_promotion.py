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
    stage_baseline_artifact: Path | None = None,
    guardrail_artifacts: list[Path],
    guardrail_control_artifacts: list[Path] | None = None,
    min_improved_rate: float,
    max_worsened_rate: float,
    min_mate_rate: float,
    max_max_plies_rate: float,
    max_shadow_candidates: int,
    min_target_mate_delta: float = 0.0,
    max_guardrail_mate_regression: float = 0.02,
    max_guardrail_max_plies_regression: float = 0.02,
    max_guardrail_shadow_regression: int = 0,
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
    stage_baseline = (
        evaluate_artifact(
            stage_baseline_artifact,
            min_improved_rate=min_improved_rate,
            max_worsened_rate=max_worsened_rate,
            min_mate_rate=min_mate_rate,
            max_max_plies_rate=max_max_plies_rate,
            max_shadow_candidates=max_shadow_candidates,
        )
        if stage_baseline_artifact is not None
        else None
    )
    guardrail_controls = [
        evaluate_artifact(
            path,
            min_improved_rate=min_improved_rate,
            max_worsened_rate=max_worsened_rate,
            min_mate_rate=min_mate_rate,
            max_max_plies_rate=max_max_plies_rate,
            max_shadow_candidates=max_shadow_candidates,
        )
        for path in (guardrail_control_artifacts or [])
    ]
    if guardrail_controls and len(guardrail_controls) != len(guardrails):
        raise ValueError("--guardrail-control-artifact count must match --guardrail-artifact count")

    target_delta = None
    target_improved_vs_baseline = None
    if stage_baseline is not None:
        target_delta = _artifact_delta(stage, stage_baseline)
        target_improved_vs_baseline = (
            target_delta["mate_rate_delta"] >= min_target_mate_delta
            and target_delta["max_plies_rate_delta"] <= 0.0
            and target_delta["shadow_candidates_delta"] <= 0
        )
        if not target_improved_vs_baseline:
            stage.setdefault("failure_reasons", []).append(
                "target did not improve versus paired baseline"
            )
            stage["passed"] = False

    guardrail_deltas = []
    guardrail_delta_failures = []
    for index, (guardrail, control) in enumerate(zip(guardrails, guardrail_controls)):
        delta = _artifact_delta(guardrail, control)
        delta["index"] = index
        delta["candidate_path"] = guardrail["path"]
        delta["control_path"] = control["path"]
        regressed = (
            delta["mate_rate_delta"] < -abs(max_guardrail_mate_regression)
            or delta["max_plies_rate_delta"] > abs(max_guardrail_max_plies_regression)
            or delta["shadow_candidates_delta"] > max_guardrail_shadow_regression
        )
        delta["regressed_vs_control"] = bool(regressed)
        guardrail_deltas.append(delta)
        if regressed:
            guardrail_delta_failures.append({"kind": "guardrail_delta", **delta})
    guardrail_control_debt = [
        {"kind": "guardrail_control_debt", **item}
        for item in guardrail_controls
        if not item.get("passed", False)
    ]
    guardrail_semantics = _guardrail_semantics(
        guardrails=guardrails,
        guardrail_controls=guardrail_controls,
        guardrail_deltas=guardrail_deltas,
        guardrail_control_debt=guardrail_control_debt,
    )

    failures = []
    if not stage["passed"]:
        failures.append({"kind": "stage", **stage})
    if guardrail_controls:
        failures.extend(guardrail_delta_failures)
    else:
        failures.extend({"kind": "guardrail", **item} for item in guardrails if not item["passed"])
    if stage["passed"] and not failures and not guardrail_control_debt:
        status = "promoted"
    elif guardrail_delta_failures:
        status = "quarantine"
    elif stage["passed"]:
        status = "overlay_only"
    else:
        status = "quarantine"
    promotion_status_semantics = _promotion_status_semantics(
        status=status,
        stage_passed=bool(stage["passed"]),
        failures=failures,
        guardrail_control_debt=guardrail_control_debt,
    )
    return {
        "schema_version": "provider_promotion_eval.v1",
        "promotion_status": status,
        "promotion_status_semantics": promotion_status_semantics,
        "stage": stage,
        "stage_baseline": stage_baseline,
        "target_delta_vs_baseline": target_delta,
        "target_improved_vs_baseline": target_improved_vs_baseline,
        "guardrails": guardrails,
        "guardrail_controls": guardrail_controls,
        "guardrail_deltas_vs_control": guardrail_deltas,
        "guardrail_control_debt": guardrail_control_debt,
        "guardrail_semantics": guardrail_semantics,
        "failures": failures,
    }


def _artifact_delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "mate_rate_delta": candidate["mate_rate"] - baseline["mate_rate"],
        "max_plies_rate_delta": candidate["max_plies_rate"] - baseline["max_plies_rate"],
        "improved_rate_delta": candidate["improved_rate"] - baseline["improved_rate"],
        "worsened_rate_delta": candidate["worsened_rate"] - baseline["worsened_rate"],
        "shadow_candidates_delta": candidate["shadow_candidates"] - baseline["shadow_candidates"],
    }


def _failure_track(reasons: list[str]) -> str:
    if not reasons:
        return "none"
    local_terms = ("improved_rate", "worsened_rate")
    conversion_terms = ("mate_rate", "max_plies_rate", "shadow_candidates")
    has_local = any(any(term in reason for term in local_terms) for reason in reasons)
    has_conversion = any(any(term in reason for term in conversion_terms) for reason in reasons)
    if has_local and not has_conversion:
        return "local_reward_contract"
    if has_conversion and not has_local:
        return "conversion_or_shadow"
    return "mixed"


def _guardrail_semantics(
    *,
    guardrails: list[dict[str, Any]],
    guardrail_controls: list[dict[str, Any]],
    guardrail_deltas: list[dict[str, Any]],
    guardrail_control_debt: list[dict[str, Any]],
) -> dict[str, Any]:
    conversion_preservation = []
    local_reward_contract_debt = []
    controls_by_path = {item["path"]: item for item in guardrail_controls}
    debt_paths = {item["path"] for item in guardrail_control_debt}

    for index, guardrail in enumerate(guardrails):
        delta = guardrail_deltas[index] if index < len(guardrail_deltas) else None
        control = (
            controls_by_path.get(delta["control_path"])
            if delta is not None and delta.get("control_path")
            else None
        )
        conversion_passed = bool(
            guardrail.get("mate_rate", 0.0) >= 1.0
            and guardrail.get("max_plies_rate", 1.0) <= 0.0
            and guardrail.get("shadow_candidates", 1) == 0
        )
        conversion_preservation.append(
            {
                "index": index,
                "guardrail_path": guardrail.get("path"),
                "control_path": control.get("path") if control else None,
                "track": "conversion_preservation_guardrail",
                "passed": bool(delta is None or not delta.get("regressed_vs_control", False)),
                "candidate_conversion_passed": conversion_passed,
                "regressed_vs_control": bool(delta.get("regressed_vs_control", False))
                if delta is not None
                else None,
                "delta": delta,
            }
        )
        if control and control.get("path") in debt_paths:
            local_reward_contract_debt.append(
                {
                    "index": index,
                    "guardrail_path": guardrail.get("path"),
                    "control_path": control.get("path"),
                    "track": "local_reward_contract_guardrail",
                    "status": "control_debt",
                    "candidate_failure_track": _failure_track(
                        list(guardrail.get("failure_reasons") or [])
                    ),
                    "control_failure_track": _failure_track(
                        list(control.get("failure_reasons") or [])
                    ),
                    "candidate_failure_reasons": list(guardrail.get("failure_reasons") or []),
                    "control_failure_reasons": list(control.get("failure_reasons") or []),
                    "blocks_clean_replacement": True,
                    "blocks_overlay_use": False,
                }
            )

    return {
        "schema_version": "guardrail_semantics_split.v1",
        "split_enabled": bool(guardrail_controls),
        "conversion_preservation": conversion_preservation,
        "local_reward_contract_debt": local_reward_contract_debt,
        "clean_replacement_blocked_by_control_debt": bool(local_reward_contract_debt),
    }


def _promotion_status_semantics(
    *,
    status: str,
    stage_passed: bool,
    failures: list[dict[str, Any]],
    guardrail_control_debt: list[dict[str, Any]],
) -> str:
    if status == "promoted":
        return "promoted_no_guardrail_regression_or_control_debt"
    if status == "overlay_only" and stage_passed and not failures and guardrail_control_debt:
        return "overlay_only_due_to_guardrail_control_debt"
    if status == "overlay_only" and stage_passed:
        return "overlay_only_due_to_guardrail_failure_without_control"
    return "quarantined_due_to_stage_or_guardrail_failure"


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate provider promotion from diagnostics")
    parser.add_argument("--stage-artifact", type=Path, required=True)
    parser.add_argument("--stage-baseline-artifact", type=Path, default=None)
    parser.add_argument("--guardrail-artifact", type=Path, action="append", default=[])
    parser.add_argument("--guardrail-control-artifact", type=Path, action="append", default=[])
    parser.add_argument("--min-improved-rate", type=float, default=0.70)
    parser.add_argument("--max-worsened-rate", type=float, default=0.20)
    parser.add_argument("--min-mate-rate", type=float, default=0.65)
    parser.add_argument("--max-max-plies-rate", type=float, default=0.25)
    parser.add_argument("--max-shadow-candidates", type=int, default=0)
    parser.add_argument("--min-target-mate-delta", type=float, default=0.0)
    parser.add_argument("--max-guardrail-mate-regression", type=float, default=0.02)
    parser.add_argument("--max-guardrail-max-plies-regression", type=float, default=0.02)
    parser.add_argument("--max-guardrail-shadow-regression", type=int, default=0)
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args()

    result = evaluate_promotion(
        stage_artifact=args.stage_artifact,
        stage_baseline_artifact=args.stage_baseline_artifact,
        guardrail_artifacts=list(args.guardrail_artifact),
        guardrail_control_artifacts=list(args.guardrail_control_artifact),
        min_improved_rate=args.min_improved_rate,
        max_worsened_rate=args.max_worsened_rate,
        min_mate_rate=args.min_mate_rate,
        max_max_plies_rate=args.max_max_plies_rate,
        max_shadow_candidates=args.max_shadow_candidates,
        min_target_mate_delta=args.min_target_mate_delta,
        max_guardrail_mate_regression=args.max_guardrail_mate_regression,
        max_guardrail_max_plies_regression=args.max_guardrail_max_plies_regression,
        max_guardrail_shadow_regression=args.max_guardrail_shadow_regression,
    )
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
