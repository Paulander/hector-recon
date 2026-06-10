#!/usr/bin/env python3
"""Run a broader protected-only repair-monitor observation-source sample."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_krk_repair_monitor_observation_source_smoke_v1 import (
    _frames,
    _load_cases,
    _run_decision,
)
from scripts.run_krk_candidate_generation_observation_sandbox_v0 import _same_decision


OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_repair_monitor_observation_source_broadened_v1.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_repair_monitor_observation_source_broadened_v1.md"
)


def _repair_monitor_frames(decision: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        frame
        for frame in _frames(decision)
        if frame.get("candidate_source") == "broader_strategy_candidate"
        and frame.get("strategy_family") == "terminal.krk.repair_needed_monitor"
    ]


def _invariant_failures(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for row in rows:
        for frame in row.get("enabled_repair_monitor_sample_frames") or []:
            if (
                frame.get("direct_request") is not False
                or float(frame.get("score_delta", 1.0) or 0.0) != 0.0
                or frame.get("causal_status") != "observation_only"
                or frame.get("protected_status") != "protected_control"
            ):
                failures.append(
                    {
                        "case_id": row.get("case_id"),
                        "source_stage": row.get("source_stage"),
                        "frame": frame,
                    }
                )
    return failures


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    risk_terms: Counter[str] = Counter()
    selected_providers: Counter[str] = Counter()
    repair_frame_count = 0
    baseline_leak_count = 0
    selected_delta_count = 0
    for row in rows:
        stage_counts[str(row.get("source_stage") or "unknown")] += 1
        if not row.get("selected_move_provider_score_equivalent"):
            selected_delta_count += 1
        baseline_leak_count += int(row.get("baseline_repair_monitor_frame_count") or 0)
        selected_providers[str(row.get("selected_provider") or "unknown")] += 1
        for frame in _frames(row["enabled_decision"]):
            source_counts[str(frame.get("candidate_source") or "unknown")] += 1
        for frame in row.get("enabled_repair_monitor_sample_frames") or []:
            repair_frame_count += 1
            risk_terms.update(str(term) for term in frame.get("risk_terms") or [])
    invariant_failures = _invariant_failures(rows)
    return {
        "case_count": len(rows),
        "case_count_by_stage": dict(sorted(stage_counts.items())),
        "repair_monitor_frame_count": repair_frame_count,
        "candidate_count_by_source": dict(sorted(source_counts.items())),
        "risk_term_counts": dict(sorted(risk_terms.items())),
        "selected_provider_counts": dict(sorted(selected_providers.items())),
        "selected_move_provider_delta_count": selected_delta_count,
        "baseline_repair_monitor_frame_count": baseline_leak_count,
        "invariant_failure_count": len(invariant_failures),
        "stage7_case_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
    }


def _decision(summary: dict[str, Any]) -> dict[str, Any]:
    passed = (
        summary["case_count"] > 3
        and summary["repair_monitor_frame_count"] > 0
        and summary["selected_move_provider_delta_count"] == 0
        and summary["baseline_repair_monitor_frame_count"] == 0
        and summary["invariant_failure_count"] == 0
        and summary["stage7_case_count"] == 0
    )
    return {
        "status": (
            "repair_monitor_observation_source_broadened_default_off_equivalent"
            if passed
            else "repair_monitor_observation_source_broadened_blocked"
        ),
        "selector_allowed": False,
        "guardrails_allowed": False,
        "promotion_allowed": False,
        "recommended_next_step": (
            "repair_monitor_observation_source_non_causal_quality_review"
            if passed
            else "quarantine_repair_monitor_observation_source"
        ),
    }


def build_payload(*, stage_cap: int = 4) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in _load_cases(stage_cap=stage_cap):
        baseline = _run_decision(case, repair_source_enabled=False)
        enabled = _run_decision(case, repair_source_enabled=True)
        baseline_repair_frames = _repair_monitor_frames(baseline)
        enabled_repair_frames = _repair_monitor_frames(enabled)
        rows.append(
            {
                **case,
                "selected_provider": enabled.get("selected_provider"),
                "baseline_decision": baseline,
                "enabled_decision": enabled,
                "selected_move_provider_score_equivalent": _same_decision(
                    baseline,
                    enabled,
                ),
                "baseline_repair_monitor_frame_count": len(baseline_repair_frames),
                "enabled_repair_monitor_frame_count": len(enabled_repair_frames),
                "enabled_repair_monitor_sample_frames": enabled_repair_frames[:3],
            }
        )
    summary = _summary(rows)
    invariant_failures = _invariant_failures(rows)
    return {
        "schema_version": "krk_repair_monitor_observation_source_broadened.v1",
        "sandbox_id": "sandbox.krk.repair_monitor_observation_source_v1",
        "causal_status": "runtime_observation_only_source_broadened_sample",
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "summary": summary,
        "cases": rows,
        "invariant_failures": invariant_failures[:10],
        "decision": _decision(summary),
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Repair-Monitor Observation Source Broadened Sample v1",
        "",
        "This is a protected-only broader sample for the default-off repair-monitor observation source. It is not selector or guardrail evidence.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- guardrails_allowed: `{payload['decision']['guardrails_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- case_count: {summary['case_count']}",
        f"- case_count_by_stage: `{summary['case_count_by_stage']}`",
        f"- repair_monitor_frame_count: {summary['repair_monitor_frame_count']}",
        f"- candidate_count_by_source: `{summary['candidate_count_by_source']}`",
        f"- risk_term_counts: `{summary['risk_term_counts']}`",
        f"- selected_provider_counts: `{summary['selected_provider_counts']}`",
        f"- selected_move_provider_delta_count: {summary['selected_move_provider_delta_count']}",
        f"- baseline_repair_monitor_frame_count: {summary['baseline_repair_monitor_frame_count']}",
        f"- invariant_failure_count: {summary['invariant_failure_count']}",
        f"- stage7_case_count: {summary['stage7_case_count']}",
        "",
        "## Boundary",
        "",
        "The broadened sample only checks observability and invariants. It does not authorize selector behavior, score changes, routing, guardrails, Stage 7 promotion, or Stage 8 training.",
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
