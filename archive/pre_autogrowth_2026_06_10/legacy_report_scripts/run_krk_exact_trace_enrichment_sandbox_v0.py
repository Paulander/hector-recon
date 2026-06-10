#!/usr/bin/env python3
"""Run the approved default-off KRK exact trace enrichment sandbox smoke.

The sandbox is candidate-generation only. It emits extra exact candidate
observation frames for reviewed Stage 5/6 policy-cell-covered gaps and never
changes selection, scores, routing, topology, or learning state.
"""

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


SOURCE_GAPS = Path("reports/strategy_arbitration/krk_candidate_source_gap_manifest_v0.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_exact_trace_enrichment_sandbox_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_exact_trace_enrichment_sandbox_v0.md")

APPROVED_SCOPE = {
    "stage5": {"edge_trap", "stage0_basin"},
    "stage6": {"stage0_basin"},
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def load_cases(stage_cap: int = 2) -> list[dict[str, Any]]:
    payload = _load(SOURCE_GAPS)
    cases: list[dict[str, Any]] = []
    by_stage: Counter[str] = Counter()
    seen: set[tuple[str, str]] = set()
    for row in payload.get("gap_records") or []:
        if row.get("gap_type") != "policy_cell_covered_exact_missing":
            continue
        if row.get("stage7_challenge_row"):
            continue
        stage = str(row.get("source_stage") or "")
        family = str(row.get("candidate_strategy_family") or "")
        if family not in APPROVED_SCOPE.get(stage, set()):
            continue
        fen = str(row.get("fen") or "")
        if not fen:
            continue
        if by_stage[stage] >= stage_cap:
            continue
        key = (stage, fen)
        if key in seen:
            continue
        seen.add(key)
        by_stage[stage] += 1
        cases.append(
            {
                "case_id": f"exact_trace_enrichment_{stage}_{by_stage[stage]}",
                "source_stage": stage,
                "fen": fen,
                "active_landmark_label": row.get("active_landmark_label"),
                "state_id": row.get("state_id"),
                "held_out": False,
                "candidate_strategy_family": family,
                "candidate_provider_id": row.get("candidate_provider_id"),
            }
        )
    return cases


def _run_decision(case: dict[str, Any], *, exact_enabled: bool) -> dict[str, Any]:
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
        krk_candidate_generation_observability_enabled=exact_enabled,
        krk_exact_trace_enrichment_enabled=exact_enabled,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    return _compact_decision(details)


def _frames(decision: dict[str, Any]) -> list[dict[str, Any]]:
    observation = decision.get("observation") or {}
    return [frame for frame in observation.get("frames") or [] if isinstance(frame, dict)]


def _exact_frames(decision: dict[str, Any]) -> list[dict[str, Any]]:
    return [frame for frame in _frames(decision) if frame.get("candidate_source") == "exact_trace_enrichment"]


def _score_changed(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return left.get("confidence") != right.get("confidence")


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stage_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    protected_count = 0
    heldout_count = 0
    direct_request_false_count = 0
    score_delta_zero_count = 0
    truncated_frame_count = 0
    truncation_count = 0
    invalid_frames: list[dict[str, Any]] = []
    generated_count = 0
    for row in rows:
        row_truncated = False
        for frame in row.get("enabled_exact_frames") or []:
            generated_count += 1
            stage_counts[str(frame.get("stage") or row.get("source_stage") or "unknown")] += 1
            family_counts[str(frame.get("provider_family") or "unknown")] += 1
            if frame.get("protected_status") == "protected_control":
                protected_count += 1
            if frame.get("protected_status") == "held_out_stage7_challenge":
                heldout_count += 1
            if frame.get("direct_request") is False:
                direct_request_false_count += 1
            if float(frame.get("score_delta", 1.0) or 0.0) == 0.0:
                score_delta_zero_count += 1
            if frame.get("candidate_generation_truncated"):
                truncated_frame_count += 1
                row_truncated = True
            if (
                frame.get("candidate_source") != "exact_trace_enrichment"
                or frame.get("policy") != "trace_stage_family_context"
                or frame.get("direct_request") is not False
                or float(frame.get("score_delta", 1.0) or 0.0) != 0.0
                or frame.get("causal_status") != "candidate_generation_only"
                or frame.get("protected_status") != "protected_control"
                or str(frame.get("stage") or "") not in {"stage5", "stage6"}
            ):
                invalid_frames.append(frame)
        if row_truncated:
            truncation_count += 1
    return {
        "generated_frame_count": generated_count,
        "generated_frame_count_by_stage": dict(sorted(stage_counts.items())),
        "generated_frame_count_by_provider_family": dict(sorted(family_counts.items())),
        "protected_frame_count": protected_count,
        "stage7_held_out_frame_count": heldout_count,
        "direct_request_false_count": direct_request_false_count,
        "score_delta_zero_count": score_delta_zero_count,
        "truncation_count": truncation_count,
        "truncated_frame_count": truncated_frame_count,
        "invalid_frame_count": len(invalid_frames),
        "invalid_frames": invalid_frames[:10],
    }


def build_payload(stage_cap: int = 2) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in load_cases(stage_cap=stage_cap):
        baseline = _run_decision(case, exact_enabled=False)
        enabled = _run_decision(case, exact_enabled=True)
        rows.append(
            {
                **case,
                "baseline_decision": baseline,
                "enabled_decision": enabled,
                "baseline_exact_frame_count": len(_exact_frames(baseline)),
                "enabled_exact_frame_count": len(_exact_frames(enabled)),
                "enabled_exact_frames": _exact_frames(enabled),
                "selected_move_delta": baseline.get("move") != enabled.get("move"),
                "selected_provider_delta": (
                    baseline.get("selected_provider") != enabled.get("selected_provider")
                ),
                "selected_score_delta": _score_changed(baseline, enabled),
                "selected_move_provider_score_equivalent": _same_decision(baseline, enabled),
            }
        )

    frame_summary = _summarize_rows(rows)
    selected_move_delta_count = sum(1 for row in rows if row["selected_move_delta"])
    selected_provider_delta_count = sum(1 for row in rows if row["selected_provider_delta"])
    selected_score_delta_count = sum(1 for row in rows if row["selected_score_delta"])
    baseline_exact_frame_count = sum(int(row.get("baseline_exact_frame_count", 0) or 0) for row in rows)
    default_off_equivalence_passed = (
        bool(rows)
        and baseline_exact_frame_count == 0
        and selected_move_delta_count == 0
        and selected_provider_delta_count == 0
        and selected_score_delta_count == 0
    )
    enabled_smoke_passed = (
        frame_summary["generated_frame_count"] > 0
        and frame_summary["invalid_frame_count"] == 0
        and frame_summary["direct_request_false_count"] == frame_summary["generated_frame_count"]
        and frame_summary["score_delta_zero_count"] == frame_summary["generated_frame_count"]
    )
    status = (
        "exact_trace_enrichment_sandbox_ready_for_non_causal_coverage_analysis"
        if default_off_equivalence_passed and enabled_smoke_passed
        else "exact_trace_enrichment_sandbox_emits_invalid_frames"
        if frame_summary["invalid_frame_count"]
        else "exact_trace_enrichment_sandbox_failed_equivalence"
    )
    return {
        "schema_version": "krk_exact_trace_enrichment_sandbox.v0",
        "sandbox_id": "sandbox.krk.exact_trace_enrichment_v0",
        "policy": "trace_stage_family_context",
        "causal_status": "candidate_generation_only_runtime_sandbox_smoke",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_provider_suppression": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "summary": {
            "case_count": len(rows),
            "default_off_equivalence_passed": default_off_equivalence_passed,
            "enabled_smoke_status": "passed" if enabled_smoke_passed else "failed",
            "selected_move_delta_count": selected_move_delta_count,
            "selected_provider_delta_count": selected_provider_delta_count,
            "selected_score_delta_count": selected_score_delta_count,
            "score_delta_count": frame_summary["generated_frame_count"] - frame_summary["score_delta_zero_count"],
            "baseline_exact_frame_count": baseline_exact_frame_count,
            **{key: value for key, value in frame_summary.items() if key != "invalid_frames"},
            "runtime_behavior_changed": False,
        },
        "cases": rows,
        "invalid_frames": frame_summary["invalid_frames"],
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "non_causal_coverage_analysis_over_exact_trace_enrichment_frames"
                if status == "exact_trace_enrichment_sandbox_ready_for_non_causal_coverage_analysis"
                else "quarantine_exact_trace_enrichment_sandbox"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Exact Trace Enrichment Sandbox v0",
        "",
        "This report validates the approved default-off exact trace enrichment sandbox. The sandbox emits candidate-generation frames only; it does not select, score, route, suppress, mutate topology, promote Stage 7, or train Stage 8.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Frames use `causal_status = candidate_generation_only`, `direct_request = false`, and `score_delta = 0.0`. The approved scope is Stage 5/6 exact trace enrichment only; Stage 4 remains excluded pending separate review and Stage 7 remains held-out challenge only.",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
