#!/usr/bin/env python3
"""Run the approved default-off KRK candidate-generation refresh sandbox smoke.

The sandbox is candidate-generation only. It emits trace frames for the reviewed
Stage 5/6 trace-stage-family cells and never changes selection, scores, routing,
topology, or learning state.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_krk_candidate_generation_observation_sandbox_v0 import (  # noqa: E402
    _same_decision,
)
from scripts.run_krk_stage5_6_candidate_generation_refresh_smoke_v0 import (  # noqa: E402
    _refresh_frames,
    _run_decision,
    load_cases,
)


OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_refresh_sandbox_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_candidate_generation_refresh_sandbox_v0.md"
)


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
        for frame in row.get("enabled_refresh_frames") or []:
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
                frame.get("candidate_source") != "stage_conditioned_candidate_generation_refresh"
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
        baseline = _run_decision(case, refresh_enabled=False)
        enabled = _run_decision(case, refresh_enabled=True)
        rows.append(
            {
                **case,
                "baseline_decision": baseline,
                "enabled_decision": enabled,
                "baseline_refresh_frame_count": len(_refresh_frames(baseline)),
                "enabled_refresh_frame_count": len(_refresh_frames(enabled)),
                "enabled_refresh_frames": _refresh_frames(enabled),
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
    baseline_refresh_frame_count = sum(
        int(row.get("baseline_refresh_frame_count", 0) or 0) for row in rows
    )
    default_off_equivalence_passed = (
        bool(rows)
        and baseline_refresh_frame_count == 0
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
        "candidate_generation_refresh_sandbox_ready_for_non_causal_coverage_analysis"
        if default_off_equivalence_passed and enabled_smoke_passed
        else "candidate_generation_refresh_sandbox_emits_invalid_frames"
        if frame_summary["invalid_frame_count"]
        else "candidate_generation_refresh_sandbox_failed_equivalence"
    )
    return {
        "schema_version": "krk_candidate_generation_refresh_sandbox.v0",
        "sandbox_id": "sandbox.krk.candidate_generation_refresh_v0",
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
            "score_delta_count": (
                frame_summary["generated_frame_count"]
                - frame_summary["score_delta_zero_count"]
            ),
            "baseline_refresh_frame_count": baseline_refresh_frame_count,
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
                "non_causal_coverage_analysis_over_emitted_candidate_generation_frames"
                if status
                == "candidate_generation_refresh_sandbox_ready_for_non_causal_coverage_analysis"
                else "quarantine_candidate_generation_refresh_sandbox"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate-Generation Refresh Sandbox v0",
        "",
        "This report validates the approved default-off candidate-generation refresh sandbox. The sandbox emits candidate-generation frames only; it does not select, score, route, suppress, mutate topology, promote Stage 7, or train Stage 8.",
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
            "Frames use `causal_status = candidate_generation_only`, `direct_request = false`, and `score_delta = 0.0`. The approved scope is Stage 5/6 only; Stage 4 remains excluded pending separate review and Stage 7 remains held-out challenge only.",
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
