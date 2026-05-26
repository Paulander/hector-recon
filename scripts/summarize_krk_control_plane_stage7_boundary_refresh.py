#!/usr/bin/env python3
"""Review control-plane artifacts after Stage 7 boundary reclassification."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = Path("reports/structural_candidates/stage7_curriculum_boundary_decision_v0.json")
FILTERED = Path("reports/krk_control_plane_filtered_frames_v0.json")
PROBE = Path("reports/krk_control_plane_strategy_arbitration_probe_v0.json")
BASELINE = Path("reports/krk_control_plane_strategy_arbitration_baseline_v1.json")
OUT_JSON = Path("reports/krk_control_plane_stage7_boundary_refresh_v0.json")
OUT_MD = Path("reports/krk_control_plane_stage7_boundary_refresh_v0.md")


def _load(path: Path) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict:
    boundary = _load(BOUNDARY)
    filtered = _load(FILTERED)
    probe = _load(PROBE)
    baseline = _load(BASELINE)
    boundary_decision = boundary.get("decision") or {}
    summary = filtered.get("summary", {})
    stage_ready = summary.get("strategy_ready_by_stage") or {}
    stage7_ready = int(stage_ready.get("stage7", 0) or 0)
    heldout = int(summary.get("stage7_boundary_heldout_frame_count", 0) or 0)
    status = (
        "control_plane_respects_stage7_boundary"
        if stage7_ready == 0 and heldout > 0
        else "control_plane_stage7_boundary_violation"
    )
    return {
        "schema_version": "krk_control_plane_stage7_boundary_refresh.v0",
        "causal_status": "non_causal_artifact_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(BOUNDARY), str(FILTERED), str(PROBE), str(BASELINE)],
        "boundary_decision_status": boundary_decision.get("status"),
        "boundary_recommended_next_step": boundary_decision.get("recommended_next_step"),
        "boundary_current_evidence_state": boundary.get("current_evidence_state") or {},
        "filtered_frame_summary": {
            "strategy_ready_frame_count": summary.get("strategy_ready_frame_count"),
            "strategy_ready_by_stage": stage_ready,
            "stage7_boundary_heldout_frame_count": heldout,
            "benchmark_role_counts": summary.get("benchmark_role_counts"),
        },
        "strategy_probe_summary": {
            "strategy_benchmark_frame_count": (probe.get("label_coverage") or {}).get(
                "strategy_benchmark_frame_count"
            ),
            "label_status": (probe.get("label_coverage") or {}).get("label_status"),
            "decision_status": (probe.get("decision") or {}).get("selected_status"),
        },
        "baseline_summary": {
            "strategy_benchmark_frame_count": (baseline.get("frame_summary") or {}).get(
                "strategy_benchmark_frame_count"
            ),
            "stage_counts": (baseline.get("frame_summary") or {}).get("stage_counts"),
            "decision_status": (baseline.get("decision") or {}).get("selected_status"),
        },
        "decision": {
            "status": status,
            "recommended_next_step": (
                boundary_decision.get("recommended_next_step")
                or "continue_broader_krk_strategy_sequence_work_with_stage7_heldout"
            ),
            "runtime_work_allowed": False,
        },
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# KRK Control-Plane Stage 7 Boundary Refresh v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "This review verifies that refreshed control-plane artifacts treat Stage 7 as held-out boundary evidence rather than strategy-training evidence.",
        "",
        "## Filtered Frames",
        "",
    ]
    for key, value in payload["filtered_frame_summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Strategy Probe", ""])
    for key, value in payload["strategy_probe_summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Baseline", ""])
    for key, value in payload["baseline_summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Boundary Evidence", ""])
    lines.append(f"- boundary_recommended_next_step: `{payload['boundary_recommended_next_step']}`")
    for key, value in payload["boundary_current_evidence_state"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", f"Recommended next step: `{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
