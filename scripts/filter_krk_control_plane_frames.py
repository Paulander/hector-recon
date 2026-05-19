#!/usr/bin/env python3
"""Add replay-free dedupe/filter metadata to KRK control-plane frames."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


FRAMES = Path("reports/krk_control_plane_frames_v0.json")
QUALITY = Path("reports/krk_control_plane_frame_quality_report_v0.json")


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    payload = json.loads((root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {relative_path}")
    return payload


def _outcome(frame: dict[str, Any]) -> str:
    result = (frame.get("outcome_labels") or {}).get("result_label") or {}
    if not isinstance(result, dict):
        return "unknown"
    return str(result.get("current_graph_h40") or result.get("playout_result") or "unknown")


def _dedupe_by_key(items: list[dict[str, Any]], key_fn) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        key = key_fn(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _monitor_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record.get("monitor_id"),
        record.get("terminal_id"),
        record.get("monitor_type"),
    )


def _window_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record.get("plan_id"),
        tuple(record.get("progress_terms_confirmed") or []),
        record.get("window_outcome"),
        record.get("ttl_white_moves"),
        record.get("owned_white_move_count"),
    )


def _benchmark_roles(frame: dict[str, Any]) -> list[str]:
    roles = []
    outcome = _outcome(frame)
    if frame.get("strategy_proposal_frames") and outcome in {"mate", "max_plies"}:
        roles.append("strategy_arbitration_benchmark")
    if frame.get("internal_monitor_records"):
        roles.append("internal_monitor_quality_analysis")
    if frame.get("sequence_training_examples"):
        roles.append("sequence_policy_context_only_stage7")
    if frame.get("plan_capsule_window_records"):
        roles.append("plan_window_context_only_stage7")
    if not roles:
        roles.append("context_only")
    return roles


def build_filtered_export(repo_root: Path) -> dict[str, Any]:
    export = _load_json(repo_root, FRAMES)
    quality = _load_json(repo_root, QUALITY)
    if export.get("causal_status") != "non_causal_frame_export":
        raise ValueError("frame export must remain non-causal")
    if quality.get("causal_status") != "non_causal_quality_report":
        raise ValueError("quality report must remain non-causal")

    frames = []
    duplicates_by_state = Counter(frame.get("state_id") for frame in export.get("frames") or [])
    for frame in export.get("frames") or []:
        if not isinstance(frame, dict):
            continue
        monitors = frame.get("internal_monitor_records") or []
        windows = frame.get("plan_capsule_window_records") or []
        deduped_monitors = _dedupe_by_key(monitors, _monitor_key)
        deduped_windows = _dedupe_by_key(windows, _window_key)
        outcome = _outcome(frame)
        proposal_count = len(frame.get("strategy_proposal_frames") or [])
        metadata = {
            "benchmark_roles": _benchmark_roles(frame),
            "known_outcome": outcome in {"mate", "max_plies"},
            "context_only": proposal_count == 0 or outcome == "unknown",
            "duplicate_state_count": int(duplicates_by_state.get(frame.get("state_id"), 0)),
            "strategy_proposal_count": proposal_count,
            "deduped_monitor_count": len(deduped_monitors),
            "dropped_duplicate_monitor_count": len(monitors) - len(deduped_monitors),
            "deduped_plan_window_count": len(deduped_windows),
            "dropped_duplicate_plan_window_count": len(windows) - len(deduped_windows),
            "sequence_training_example_count": len(frame.get("sequence_training_examples") or []),
            "causal_status": "non_causal",
        }
        filtered_frame = {
            "frame_id": frame.get("frame_id"),
            "state_id": frame.get("state_id"),
            "fen": frame.get("fen"),
            "source_stage": frame.get("source_stage"),
            "active_landmark_label": frame.get("active_landmark_label"),
            "outcome": outcome,
            "filter_metadata": metadata,
            "strategy_proposal_frames": frame.get("strategy_proposal_frames") or [],
            "internal_monitor_records": deduped_monitors,
            "plan_capsule_window_records": deduped_windows,
            "sequence_training_examples": frame.get("sequence_training_examples") or [],
            "protected_provider_provenance": frame.get("protected_provider_provenance") or [],
            "growth_governor_status": frame.get("growth_governor_status") or {},
            "promotion_gate_status": frame.get("promotion_gate_status") or {},
            "causal_status": "non_causal",
        }
        frames.append(filtered_frame)

    strategy_ready = [
        frame for frame in frames if "strategy_arbitration_benchmark" in frame["filter_metadata"]["benchmark_roles"]
    ]
    by_role: Counter[str] = Counter()
    for frame in frames:
        by_role.update(frame["filter_metadata"]["benchmark_roles"])
    by_stage_strategy_ready = Counter(frame["source_stage"] for frame in strategy_ready)
    dropped_monitor_count = sum(frame["filter_metadata"]["dropped_duplicate_monitor_count"] for frame in frames)
    dropped_window_count = sum(frame["filter_metadata"]["dropped_duplicate_plan_window_count"] for frame in frames)

    result = {
        "schema_version": "krk_control_plane_filtered_frames.v0",
        "causal_status": "non_causal_filtered_frame_export",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "runtime_arbiter_added": False,
        "runtime_terminals_added": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(FRAMES), str(QUALITY)],
        "frames": frames,
        "summary": {
            "frame_count": len(frames),
            "unique_state_count": len({frame["state_id"] for frame in frames}),
            "duplicate_state_ids": sorted(
                state for state, count in duplicates_by_state.items() if state and count > 1
            ),
            "benchmark_role_counts": dict(by_role),
            "strategy_ready_frame_count": len(strategy_ready),
            "strategy_ready_by_stage": dict(by_stage_strategy_ready),
            "context_only_frame_count": sum(frame["filter_metadata"]["context_only"] for frame in frames),
            "dropped_duplicate_monitor_count": dropped_monitor_count,
            "dropped_duplicate_plan_window_count": dropped_window_count,
            "new_playouts_added": 0,
        },
        "readiness": {
            "offline_strategy_arbitration_probe": "ready_on_strategy_arbitration_benchmark_frames",
            "offline_sequence_policy_benchmark": "blocked_general_krk_stage7_only",
            "runtime_sandbox": "blocked",
            "stage7_promotion": "blocked",
            "stage8_training": "blocked",
        },
        "recommended_next_slice": "offline_strategy_arbitration_probe_filtered_v0",
    }
    validate_filtered_export(result)
    return result


def validate_filtered_export(result: dict[str, Any]) -> None:
    if result.get("causal_status") != "non_causal_filtered_frame_export":
        raise ValueError("filtered frame export must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "runtime_arbiter_added",
        "runtime_terminals_added",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if result.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if result["summary"]["new_playouts_added"] != 0:
        raise ValueError("filtered export must not add playouts")
    if result["readiness"]["runtime_sandbox"] != "blocked":
        raise ValueError("runtime sandbox must remain blocked")
    for frame in result.get("frames") or []:
        if frame.get("causal_status") != "non_causal":
            raise ValueError("all filtered frames must remain non-causal")
        if frame.get("filter_metadata", {}).get("causal_status") != "non_causal":
            raise ValueError("filter metadata must remain non-causal")


def render_markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# KRK Control-Plane Filtered Frames v0",
        "",
        "This replay-free export adds non-causal dedupe and benchmark-role metadata "
        "to the control-plane frames. It does not change runtime behavior or "
        "authorize a sandbox.",
        "",
        "## Summary",
        "",
        f"- Frames: `{summary['frame_count']}`",
        f"- Unique states: `{summary['unique_state_count']}`",
        f"- Duplicate state IDs: `{summary['duplicate_state_ids']}`",
        f"- Benchmark role counts: `{summary['benchmark_role_counts']}`",
        f"- Strategy-ready frames: `{summary['strategy_ready_frame_count']}`",
        f"- Strategy-ready by stage: `{summary['strategy_ready_by_stage']}`",
        f"- Context-only frames: `{summary['context_only_frame_count']}`",
        f"- Dropped duplicate monitors: `{summary['dropped_duplicate_monitor_count']}`",
        f"- Dropped duplicate plan windows: `{summary['dropped_duplicate_plan_window_count']}`",
        f"- New playouts added: `{summary['new_playouts_added']}`",
        "",
        "## Readiness",
        "",
    ]
    lines.extend(f"- `{key}`: `{value}`" for key, value in result["readiness"].items())
    lines.extend(
        [
            "",
            "## Recommended Next Slice",
            "",
            f"`{result['recommended_next_slice']}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(result: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_control_plane_filtered_frames_v0.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_control_plane_filtered_frames_v0.md").write_text(
        render_markdown(result), encoding="utf-8"
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
    result = build_filtered_export(repo_root)
    write_outputs(result, report_root)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
