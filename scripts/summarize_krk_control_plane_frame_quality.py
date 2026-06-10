#!/usr/bin/env python3
"""Assess quality and coverage of KRK control-plane frame export v0."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


FRAMES = Path("reports/krk_control_plane_frames_v0.json")


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    payload = json.loads((root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {relative_path}")
    return payload


def _outcome(frame: dict[str, Any]) -> str:
    result = (frame.get("outcome_labels") or {}).get("result_label") or {}
    if not isinstance(result, dict):
        return "unknown"
    return str(
        result.get("current_graph_h40")
        or result.get("playout_result")
        or result.get("conversion_result")
        or "unknown"
    )


def _count_frames_with(frames: list[dict[str, Any]], field: str) -> dict[str, Any]:
    frames_with = [frame for frame in frames if frame.get(field)]
    return {
        "frames_with": len(frames_with),
        "total_attached_records": sum(len(frame.get(field) or []) for frame in frames),
        "frames_with_by_stage": dict(Counter(frame.get("source_stage") for frame in frames_with)),
    }


def build_quality_report(repo_root: Path) -> dict[str, Any]:
    export = _load_json(repo_root, FRAMES)
    if export.get("causal_status") != "non_causal_frame_export":
        raise ValueError("control-plane frame export must remain non-causal")
    frames = [frame for frame in export.get("frames") or [] if isinstance(frame, dict)]
    monitor_ids = [
        monitor.get("monitor_id")
        for frame in frames
        for monitor in frame.get("internal_monitor_records") or []
        if monitor.get("monitor_id")
    ]
    duplicate_monitor_attachments = len(monitor_ids) - len(set(monitor_ids))
    window_keys = [
        (
            frame.get("state_id"),
            tuple(window.get("progress_terms_confirmed") or []),
            window.get("window_outcome"),
        )
        for frame in frames
        for window in frame.get("plan_capsule_window_records") or []
    ]
    duplicate_window_attachments = len(window_keys) - len(set(window_keys))
    no_proposal_frames = [frame.get("frame_id") for frame in frames if not frame.get("strategy_proposal_frames")]
    sequence_stages = sorted({frame.get("source_stage") for frame in frames if frame.get("sequence_training_examples")})
    plan_window_stages = sorted({frame.get("source_stage") for frame in frames if frame.get("plan_capsule_window_records")})

    report = {
        "schema_version": "krk_control_plane_frame_quality_report.v0",
        "causal_status": "non_causal_quality_report",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "hidden_python_controller": False,
        "gameplay_topology_mutation": False,
        "runtime_arbiter_added": False,
        "runtime_terminals_added": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(FRAMES)],
        "coverage": {
            "frame_count": len(frames),
            "frames_by_stage": dict(Counter(frame.get("source_stage") for frame in frames)),
            "outcome_distribution": dict(Counter(_outcome(frame) for frame in frames)),
            "strategy_proposal_frames": _count_frames_with(frames, "strategy_proposal_frames"),
            "internal_monitor_records": _count_frames_with(frames, "internal_monitor_records"),
            "plan_capsule_window_records": _count_frames_with(frames, "plan_capsule_window_records"),
            "sequence_training_examples": _count_frames_with(frames, "sequence_training_examples"),
        },
        "quality_flags": [
            {
                "flag_id": "some_frames_lack_strategy_proposals",
                "severity": "medium",
                "count": len(no_proposal_frames),
                "examples": no_proposal_frames[:5],
                "interpretation": "These frames can still carry context/monitor evidence but are not usable for provider-ranking benchmarks without additional proposal extraction.",
            },
            {
                "flag_id": "monitor_records_duplicate_across_duplicate_state_frames",
                "severity": "medium",
                "count": duplicate_monitor_attachments,
                "interpretation": "Monitor attachments exceed unique monitor IDs because some state IDs appear in multiple strategy records. Consumers should group by frame_id and dedupe by monitor_id when measuring monitor support.",
            },
            {
                "flag_id": "plan_windows_stage7_only",
                "severity": "high",
                "count": len(plan_window_stages),
                "stages": plan_window_stages,
                "interpretation": "Plan-window evidence is not yet general across protected Stage 4/5/6 contexts.",
            },
            {
                "flag_id": "sequence_examples_stage7_only",
                "severity": "high",
                "count": len(sequence_stages),
                "stages": sequence_stages,
                "interpretation": "Offline sequence examples remain concentrated in Stage 7 residual states; do not train a general KRK sequence policy from this alone.",
            },
            {
                "flag_id": "plan_window_duplicate_attachment",
                "severity": "low",
                "count": duplicate_window_attachments,
                "interpretation": "Several plan-window records share the same state/progress/outcome signature; this is useful evidence but should be deduped for statistical claims.",
            },
        ],
        "readiness": {
            "offline_strategy_arbitration_probe": "ready_with_dedupe_and_missing_proposal_caveat",
            "offline_sequence_policy_benchmark": "not_ready_general_krk_stage7_only",
            "internal_monitor_training_dataset": "ready_for_non_causal_monitor_quality_analysis_only",
            "runtime_sandbox": "blocked",
            "stage8_training": "blocked",
            "stage7_promotion": "blocked",
        },
        "recommended_next_slice": {
            "slice_id": "control_plane_frame_dedupe_and_quality_filters_v0",
            "causal": False,
            "new_playouts_allowed": False,
            "reason": (
                "Before using the frames for offline arbitration or sequence benchmarks, add "
                "dedupe/filter metadata and separate benchmark-ready frames from context-only frames."
            ),
        },
        "blocked_next_steps": [
            "runtime_arbiter",
            "runtime_internal_terminal",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_quality_report(report)
    return report


def validate_quality_report(report: dict[str, Any]) -> None:
    if report.get("causal_status") != "non_causal_quality_report":
        raise ValueError("quality report must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_score_changes",
        "runtime_direct_routing",
        "runtime_dtm_or_tablebase_lookup",
        "hidden_python_controller",
        "gameplay_topology_mutation",
        "runtime_arbiter_added",
        "runtime_terminals_added",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if report.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if report["readiness"]["runtime_sandbox"] != "blocked":
        raise ValueError("runtime sandbox must remain blocked")
    if report["recommended_next_slice"]["causal"]:
        raise ValueError("recommended next slice must remain non-causal")


def render_markdown(report: dict[str, Any]) -> str:
    coverage = report["coverage"]
    lines = [
        "# KRK Control-Plane Frame Quality Report v0",
        "",
        "This is a non-causal quality report for the replay-free frame export. It "
        "does not authorize runtime arbitration, runtime terminals, Stage 7 "
        "promotion, Stage 8 training, or new playouts.",
        "",
        "## Coverage",
        "",
        f"- Frames: `{coverage['frame_count']}`",
        f"- Frames by stage: `{coverage['frames_by_stage']}`",
        f"- Outcome distribution: `{coverage['outcome_distribution']}`",
        f"- Strategy proposal coverage: `{coverage['strategy_proposal_frames']}`",
        f"- Monitor coverage: `{coverage['internal_monitor_records']}`",
        f"- Plan-window coverage: `{coverage['plan_capsule_window_records']}`",
        f"- Sequence-example coverage: `{coverage['sequence_training_examples']}`",
        "",
        "## Quality Flags",
        "",
    ]
    for flag in report["quality_flags"]:
        lines.extend(
            [
                f"### {flag['flag_id']}",
                "",
                f"- Severity: `{flag['severity']}`",
                f"- Count: `{flag['count']}`",
                f"- Interpretation: {flag['interpretation']}",
                "",
            ]
        )
    lines.extend(["## Readiness", ""])
    lines.extend(f"- `{key}`: `{value}`" for key, value in report["readiness"].items())
    rec = report["recommended_next_slice"]
    lines.extend(
        [
            "",
            "## Recommended Next Slice",
            "",
            f"- Slice: `{rec['slice_id']}`",
            f"- Causal: `{rec['causal']}`",
            f"- New playouts allowed: `{rec['new_playouts_allowed']}`",
            f"- Reason: {rec['reason']}",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(report: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_control_plane_frame_quality_report_v0.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_control_plane_frame_quality_report_v0.md").write_text(
        render_markdown(report), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--report-root", type=Path, default=Path("reports"))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report_root = args.report_root
    if not report_root.is_absolute():
        report_root = repo_root / report_root
    report = build_quality_report(repo_root)
    write_outputs(report, report_root)
    print(json.dumps(report["readiness"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
