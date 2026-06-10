#!/usr/bin/env python3
"""Analyze repair-monitor observation-source smoke coverage."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("reports/strategy_arbitration/krk_repair_monitor_observation_source_smoke_v1.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_repair_monitor_observation_source_coverage_v1.json"
)
OUT_MD = Path("reports/strategy_arbitration/krk_repair_monitor_observation_source_coverage_v1.md")


def _load(path: Path = SOURCE) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _repair_frames(payload: dict[str, Any]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for case in payload.get("cases") or []:
        for frame in case.get("enabled_repair_monitor_sample_frames") or []:
            if isinstance(frame, dict):
                frames.append({**frame, "_source_stage": case.get("source_stage")})
    return frames


def build_payload(source: dict[str, Any] | None = None) -> dict[str, Any]:
    source = source or _load()
    frames = _repair_frames(source)
    by_stage = Counter(str(frame.get("_source_stage") or "unknown") for frame in frames)
    risk_terms = Counter()
    invariant_failures = []
    for frame in frames:
        risk_terms.update(str(term) for term in frame.get("risk_terms") or [])
        if (
            frame.get("candidate_source") != "broader_strategy_candidate"
            or frame.get("strategy_family") != "terminal.krk.repair_needed_monitor"
            or frame.get("direct_request") is not False
            or float(frame.get("score_delta", 1.0) or 0.0) != 0.0
            or frame.get("causal_status") != "observation_only"
        ):
            invariant_failures.append(frame)
    status = (
        "repair_monitor_observation_source_coverage_ready_for_guarded_analysis"
        if frames and not invariant_failures
        else "repair_monitor_observation_source_coverage_blocked"
    )
    return {
        "schema_version": "krk_repair_monitor_observation_source_coverage.v1",
        "causal_status": "non_causal_runtime_observation_analysis",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifact": str(SOURCE),
        "summary": {
            "repair_monitor_frame_count": len(frames),
            "frame_count_by_stage": dict(sorted(by_stage.items())),
            "risk_term_counts": dict(sorted(risk_terms.items())),
            "invariant_failure_count": len(invariant_failures),
            "stage7_case_count": (source.get("summary") or {}).get("stage7_case_count"),
            "selected_move_provider_delta_count": (source.get("summary") or {}).get(
                "selected_move_provider_delta_count"
            ),
        },
        "invariant_failures": invariant_failures[:10],
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": "broaden_repair_monitor_observation_sample_non_causal"
            if status == "repair_monitor_observation_source_coverage_ready_for_guarded_analysis"
            else "quarantine_repair_monitor_observation_source",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Repair-Monitor Observation Source Coverage v1",
        "",
        "This analyzes emitted repair-monitor observation frames. It does not authorize selection or guardrails.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- repair_monitor_frame_count: {summary['repair_monitor_frame_count']}",
        f"- frame_count_by_stage: `{summary['frame_count_by_stage']}`",
        f"- risk_term_counts: `{summary['risk_term_counts']}`",
        f"- invariant_failure_count: {summary['invariant_failure_count']}",
        f"- stage7_case_count: {summary['stage7_case_count']}",
        f"- selected_move_provider_delta_count: {summary['selected_move_provider_delta_count']}",
    ]
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
