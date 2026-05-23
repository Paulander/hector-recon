#!/usr/bin/env python3
"""Smoke the default-off repair-monitor observation source."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import chess

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_krk_candidate_generation_observation_sandbox_v0 import (  # noqa: E402
    _compact_decision,
    _new_graph_engine,
    _profile_kwargs,
    _same_decision,
)
from scripts.test_krk_landmark_progress import choose_move_details  # noqa: E402


SOURCE_FRAMES = Path(
    "reports/strategy_arbitration/krk_protected_strategy_monitor_frame_expansion_v1.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_repair_monitor_observation_source_smoke_v1.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_repair_monitor_observation_source_smoke_v1.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _load_cases(stage_cap: int = 1) -> list[dict[str, Any]]:
    payload = _load(SOURCE_FRAMES)
    cases: list[dict[str, Any]] = []
    by_stage: Counter[str] = Counter()
    seen: set[tuple[str, str]] = set()
    for frame in payload.get("frames") or []:
        if frame.get("candidate_strategy_family") != "terminal.krk.repair_needed_monitor":
            continue
        if frame.get("stage7_challenge_row"):
            continue
        stage = str(frame.get("source_stage") or "")
        if by_stage[stage] >= stage_cap:
            continue
        key = (stage, str(frame.get("fen") or ""))
        if key in seen:
            continue
        seen.add(key)
        by_stage[stage] += 1
        cases.append(
            {
                "case_id": f"repair_monitor_{stage}_{by_stage[stage]}",
                "source_stage": stage,
                "fen": frame["fen"],
                "active_landmark_label": frame.get("active_landmark_label"),
                "state_id": frame.get("state_id"),
                "held_out": False,
            }
        )
    return cases


def _run_decision(case: dict[str, Any], *, repair_source_enabled: bool) -> dict[str, Any]:
    graph, engine = _new_graph_engine()
    board = chess.Board(str(case["fen"]))
    details = choose_move_details(
        graph,
        engine,
        board,
        max_ticks=200,
        suggestion_limit=10,
        active_landmark_label=str(case["active_landmark_label"]),
        early_stop_stable_suggestions=2,
        krk_candidate_generation_observability_enabled=True,
        krk_repair_monitor_observation_source_enabled=repair_source_enabled,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    return _compact_decision(details)


def _frames(decision: dict[str, Any]) -> list[dict[str, Any]]:
    observation = decision.get("observation") or {}
    return [frame for frame in observation.get("frames") or [] if isinstance(frame, dict)]


def build_payload() -> dict[str, Any]:
    rows = []
    for case in _load_cases():
        baseline = _run_decision(case, repair_source_enabled=False)
        enabled = _run_decision(case, repair_source_enabled=True)
        baseline_frames = _frames(baseline)
        enabled_frames = _frames(enabled)
        repair_frames = [
            frame
            for frame in enabled_frames
            if frame.get("candidate_source") == "broader_strategy_candidate"
            and frame.get("strategy_family") == "terminal.krk.repair_needed_monitor"
        ]
        rows.append(
            {
                **case,
                "baseline_decision": baseline,
                "enabled_decision": enabled,
                "selected_move_provider_score_equivalent": _same_decision(baseline, enabled),
                "baseline_repair_monitor_frame_count": sum(
                    1
                    for frame in baseline_frames
                    if frame.get("strategy_family") == "terminal.krk.repair_needed_monitor"
                ),
                "enabled_repair_monitor_frame_count": len(repair_frames),
                "enabled_repair_monitor_sample_frames": repair_frames[:3],
            }
        )
    source_counts: Counter[str] = Counter()
    invariant_failures: list[dict[str, Any]] = []
    repair_frame_count = 0
    for row in rows:
        for frame in _frames(row["enabled_decision"]):
            source_counts[str(frame.get("candidate_source") or "unknown")] += 1
            if frame.get("strategy_family") == "terminal.krk.repair_needed_monitor":
                repair_frame_count += 1
                if (
                    frame.get("direct_request") is not False
                    or float(frame.get("score_delta", 1.0) or 0.0) != 0.0
                    or frame.get("causal_status") != "observation_only"
                    or frame.get("protected_status") != "protected_control"
                ):
                    invariant_failures.append(frame)
    selected_delta_count = sum(
        1 for row in rows if not row["selected_move_provider_score_equivalent"]
    )
    baseline_leak_count = sum(
        int(row["baseline_repair_monitor_frame_count"]) for row in rows
    )
    status = (
        "repair_monitor_observation_source_wired_default_off_equivalent"
        if rows
        and repair_frame_count > 0
        and selected_delta_count == 0
        and baseline_leak_count == 0
        and not invariant_failures
        else "repair_monitor_observation_source_smoke_blocked"
    )
    return {
        "schema_version": "krk_repair_monitor_observation_source_smoke.v1",
        "sandbox_id": "sandbox.krk.repair_monitor_observation_source_v1",
        "causal_status": "runtime_observation_only_source_smoke",
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifact": str(SOURCE_FRAMES),
        "summary": {
            "case_count": len(rows),
            "repair_monitor_frame_count": repair_frame_count,
            "candidate_count_by_source": dict(sorted(source_counts.items())),
            "selected_move_provider_delta_count": selected_delta_count,
            "baseline_repair_monitor_frame_count": baseline_leak_count,
            "invariant_failure_count": len(invariant_failures),
            "stage7_case_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        },
        "cases": rows,
        "invariant_failures": invariant_failures[:10],
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": "repair_monitor_observation_source_coverage_analysis"
            if status == "repair_monitor_observation_source_wired_default_off_equivalent"
            else "quarantine_repair_monitor_observation_source",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Repair-Monitor Observation Source Smoke v1",
        "",
        "This smoke tests the default-off observation-only broader-strategy source for `terminal.krk.repair_needed_monitor`.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- case_count: {summary['case_count']}",
        f"- repair_monitor_frame_count: {summary['repair_monitor_frame_count']}",
        f"- candidate_count_by_source: `{summary['candidate_count_by_source']}`",
        f"- selected_move_provider_delta_count: {summary['selected_move_provider_delta_count']}",
        f"- baseline_repair_monitor_frame_count: {summary['baseline_repair_monitor_frame_count']}",
        f"- invariant_failure_count: {summary['invariant_failure_count']}",
        f"- stage7_case_count: {summary['stage7_case_count']}",
        "",
        "## Boundary",
        "",
        "The source emits observation frames only. It does not select, score, route, run guardrails, promote Stage 7, or train Stage 8.",
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
