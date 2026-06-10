#!/usr/bin/env python3
"""Run a small runtime-test smoke for progress-window reconsideration."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

import chess

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from recon_lite.engine import ReConEngine  # noqa: E402
from recon_lite_chess.graph.builder import build_graph_from_topology  # noqa: E402
from scripts.test_krk_landmark_progress import (  # noqa: E402
    COMPOSITION_PROFILE_HANDOFF_V1,
    HANDOFF_COMPOSITION_V1_SETTINGS,
    evaluate_landmark_progress,
    play_to_mate,
)


TOPOLOGY = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json"
)
LABELS = ("edge_trap_wrong_tempo", "fence_established", "drive_to_edge")
INDEPENDENT_LABELS = Path("reports/krk_selected_owner_failure_risk_proxy_independent_labels_v0.json")

OUT_JSON = Path("reports/krk_progress_window_reconsideration_runtime_smoke_v0.json")
OUT_MD = Path("reports/krk_progress_window_reconsideration_runtime_smoke_v0.md")


def _compact_stats(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "total": stats.get("total"),
        "no_move": stats.get("no_move"),
        "playouts": dict(stats.get("playouts", {}) or {}),
        "one_ply_status_counts": dict(stats.get("one_ply_status_counts", {}) or {}),
        "conversion_status_counts": dict(stats.get("conversion_status_counts", {}) or {}),
        "shadow_candidate_count": stats.get("shadow_candidate_count"),
        "krk_progress_window_reconsideration_supported_count": stats.get(
            "krk_progress_window_reconsideration_supported_count"
        ),
        "krk_progress_window_reconsideration_selected_supported_count": stats.get(
            "krk_progress_window_reconsideration_selected_supported_count"
        ),
        "krk_progress_window_reconsideration_supported_provider_by_outcome": dict(
            stats.get("krk_progress_window_reconsideration_supported_provider_by_outcome", {}) or {}
        ),
        "krk_progress_window_reconsideration_selected_by_outcome": dict(
            stats.get("krk_progress_window_reconsideration_selected_by_outcome", {}) or {}
        ),
    }


def _outcome_signature(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "total": row.get("total"),
        "no_move": row.get("no_move"),
        "playouts": row.get("playouts"),
        "one_ply_status_counts": row.get("one_ply_status_counts"),
        "conversion_status_counts": row.get("conversion_status_counts"),
        "shadow_candidate_count": row.get("shadow_candidate_count"),
    }


def _run_eval(label: str, *, enabled: bool, support: float) -> dict[str, Any]:
    return _compact_stats(
        evaluate_landmark_progress(
            ROOT / TOPOLOGY,
            label=label,
            samples=1,
            seed=7,
            playout_max_plies=20,
            composition_profile=COMPOSITION_PROFILE_HANDOFF_V1,
            early_stop_stable_suggestions=2,
            enable_diagnostic_caches=True,
            krk_progress_window_reconsideration_enabled=enabled,
            krk_progress_window_reconsideration_support=support,
            verbose=False,
        )
    )


def _new_graph_engine() -> tuple[Any, ReConEngine]:
    graph = build_graph_from_topology(ROOT / TOPOLOGY)
    return graph, ReConEngine(graph)


def _compact_playout(result: dict[str, Any]) -> dict[str, Any]:
    supported = 0
    selected_supported = 0
    selected_payloads: list[dict[str, Any]] = []
    blocked_reason_counts: dict[str, int] = {}
    monitor_confirmed_events = 0
    candidate_intersection_events = 0
    suggested_loop_breaking_events = 0
    no_supported_examples: list[dict[str, Any]] = []
    for event in result.get("trace", []) or []:
        engine = event.get("engine") if isinstance(event, dict) else {}
        if not isinstance(engine, dict):
            continue
        summary = engine.get("krk_progress_window_reconsideration_summary") or {}
        blocked_reason = str(summary.get("blocked_reason") or "none")
        blocked_reason_counts[blocked_reason] = blocked_reason_counts.get(blocked_reason, 0) + 1
        supported += int(summary.get("supported_count", 0) or 0)
        if summary.get("selected_supported"):
            selected_supported += 1
            selected = engine.get("selected_suggestion") or {}
            payload = (selected.get("krk_progress_window_reconsideration") or {})
            if payload:
                selected_payloads.append(payload)
        ctx = event.get("stagnation_context") if isinstance(event.get("stagnation_context"), dict) else {}
        loop_moves = set(ctx.get("legal_loop_breaking_moves", []) or [])
        suggestion_moves = {
            str(item.get("move"))
            for item in (engine.get("suggestions", []) or [])
            if isinstance(item, dict) and item.get("move")
        }
        selected_move = str(engine.get("move") or "")
        required_monitor_terms = (
            "rook_oscillation_loop",
            "no_box_progress_recently",
            "no_edge_progress_recently",
            "no_mate_progress_recently",
            "safe_loop_breaking_move_available",
        )
        monitor_confirmed = all(bool(ctx.get(term, False)) for term in required_monitor_terms) and (
            bool(ctx.get("repeated_abstract_state", False))
            or int(ctx.get("no_progress_plies", 0) or 0) >= 4
        )
        if monitor_confirmed:
            monitor_confirmed_events += 1
        intersection = sorted(loop_moves & suggestion_moves)
        if intersection:
            candidate_intersection_events += 1
        if selected_move in loop_moves:
            suggested_loop_breaking_events += 1
        if monitor_confirmed and not int(summary.get("supported_count", 0) or 0):
            no_supported_examples.append(
                {
                    "ply": event.get("ply"),
                    "move": event.get("move"),
                    "blocked_reason": blocked_reason,
                    "no_progress_plies": int(ctx.get("no_progress_plies", 0) or 0),
                    "suggestion_moves": sorted(suggestion_moves)[:8],
                    "legal_loop_breaking_moves": sorted(loop_moves)[:8],
                    "intersection": intersection[:8],
                }
            )
    return {
        "result": result.get("result"),
        "plies": result.get("plies"),
        "final_fen": result.get("final_fen"),
        "supported_count": supported,
        "selected_supported_count": selected_supported,
        "selected_payloads": selected_payloads[:3],
        "activation_diagnosis": {
            "blocked_reason_counts": dict(sorted(blocked_reason_counts.items())),
            "monitor_confirmed_events": monitor_confirmed_events,
            "candidate_intersection_events": candidate_intersection_events,
            "suggested_loop_breaking_events": suggested_loop_breaking_events,
            "no_supported_examples": no_supported_examples[:3],
        },
        "stagnation_summary": {
            key: (result.get("stagnation_summary") or {}).get(key)
            for key in (
                "stagnation_loop",
                "rook_oscillation_loop",
                "no_box_progress_recently",
                "no_edge_progress_recently",
                "no_mate_progress_recently",
                "safe_loop_breaking_move_available",
                "no_progress_plies",
            )
        },
    }


def _target_rows() -> list[dict[str, Any]]:
    payload = json.loads((ROOT / INDEPENDENT_LABELS).read_text(encoding="utf-8"))
    labels = list(payload.get("labels") or [])
    true_rows = [row for row in labels if row.get("selected_owner_failure_risk_target") is True]
    safe_rows = [
        row
        for row in labels
        if row.get("selected_owner_failure_risk_target") is not True
        and row.get("safe_preservation_confidence_target") is True
    ][:1]
    return true_rows[:1] + safe_rows


def _run_target(row: dict[str, Any], *, enabled: bool, support: float) -> dict[str, Any]:
    graph, engine = _new_graph_engine()
    board = chess.Board(str(row["fen"]))
    settings = dict(HANDOFF_COMPOSITION_V1_SETTINGS)
    result = play_to_mate(
        graph,
        engine,
        board,
        random.Random(7),
        label=str(row.get("active_landmark_label") or "edge_trap_wrong_tempo"),
        stage_filter=None,
        max_plies=40,
        black_policy="adversarial",
        trace=True,
        max_ticks=200,
        suggestion_limit=10,
        trace_max_plies=80,
        successor_affordance_layer_enabled=bool(settings["successor_affordance_layer_enabled"]),
        successor_role_license_enabled=bool(settings["successor_role_license_enabled"]),
        successor_role_scoped_move_shape_enabled=bool(
            settings["successor_role_scoped_move_shape_enabled"]
        ),
        successor_role_scoped_move_shape_bonus=float(
            settings["successor_role_scoped_move_shape_bonus"]
        ),
        stagnation_breaker_enabled=bool(settings["stagnation_breaker_enabled"]),
        stagnation_breaker_bonus=float(settings["stagnation_breaker_bonus"]),
        post_break_continuation_enabled=bool(settings["post_break_continuation_enabled"]),
        post_break_continuation_bonus=float(settings["post_break_continuation_bonus"]),
        successor_stage0_drift_penalty=float(settings["successor_stage0_drift_penalty"]),
        krk_progress_window_reconsideration_enabled=enabled,
        krk_progress_window_reconsideration_support=support,
        enable_diagnostic_caches=True,
    )
    return _compact_playout(result)


def build_smoke() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for label in LABELS:
        baseline = _run_eval(label, enabled=False, support=0.0)
        flag_off = _run_eval(label, enabled=True, support=0.0)
        enabled = _run_eval(label, enabled=True, support=0.5)
        rows.append(
            {
                "label": label,
                "baseline": baseline,
                "flag_present_default_off": flag_off,
                "enabled_support_0_5": enabled,
                "default_off_equivalence": _outcome_signature(baseline)
                == _outcome_signature(flag_off),
            }
        )
    target_rows = []
    for source in _target_rows():
        baseline = _run_target(source, enabled=False, support=0.0)
        flag_off = _run_target(source, enabled=True, support=0.0)
        enabled = _run_target(source, enabled=True, support=0.5)
        target_rows.append(
            {
                "frame_id": source.get("frame_id"),
                "active_landmark_label": source.get("active_landmark_label"),
                "target_failure_risk": source.get("selected_owner_failure_risk_target") is True,
                "baseline": baseline,
                "flag_present_default_off": flag_off,
                "enabled_support_0_5": enabled,
                "default_off_equivalence": baseline["result"] == flag_off["result"]
                and baseline["plies"] == flag_off["plies"],
            }
        )
    default_off_passed = all(row["default_off_equivalence"] for row in rows + target_rows)
    enabled_supported_total = sum(
        int(row["enabled_support_0_5"].get("krk_progress_window_reconsideration_supported_count", 0) or 0)
        for row in rows
    ) + sum(int(row["enabled_support_0_5"].get("supported_count", 0) or 0) for row in target_rows)
    enabled_selected_supported_total = sum(
        int(row["enabled_support_0_5"].get("krk_progress_window_reconsideration_selected_supported_count", 0) or 0)
        for row in rows
    ) + sum(int(row["enabled_support_0_5"].get("selected_supported_count", 0) or 0) for row in target_rows)
    monitor_confirmed_total = sum(
        int(
            (
                row["enabled_support_0_5"]
                .get("activation_diagnosis", {})
                .get("monitor_confirmed_events", 0)
            )
            or 0
        )
        for row in target_rows
    )
    candidate_intersection_total = sum(
        int(
            (
                row["enabled_support_0_5"]
                .get("activation_diagnosis", {})
                .get("candidate_intersection_events", 0)
            )
            or 0
        )
        for row in target_rows
    )
    target_failure_rows = [row for row in target_rows if row.get("target_failure_risk")]
    improved_target_failure_count = sum(
        1
        for row in target_failure_rows
        if row["baseline"].get("result") != "mate"
        and row["enabled_support_0_5"].get("result") == "mate"
    )
    safe_regression_count = sum(
        1
        for row in target_rows
        if not row.get("target_failure_risk")
        and (
            row["baseline"].get("result") != row["enabled_support_0_5"].get("result")
            or int(row["enabled_support_0_5"].get("plies", 0) or 0)
            > int(row["baseline"].get("plies", 0) or 0)
        )
    )
    if not default_off_passed:
        status = "runtime_smoke_default_off_failed"
        next_step = "stop_and_diagnose_default_off_delta"
    elif enabled_supported_total <= 0:
        status = "runtime_smoke_default_off_passed_no_activation"
        next_step = "diagnose_visible_candidate_coverage_or_monitor_timing"
    elif improved_target_failure_count <= 0:
        status = "runtime_smoke_activation_observed_no_target_improvement"
        next_step = "quarantine_or_refine_reconsideration_policy_before_guardrails"
    elif safe_regression_count > 0:
        status = "runtime_smoke_activation_observed_safe_regression"
        next_step = "stop_and_diagnose_safe_preservation_regression"
    else:
        status = "runtime_smoke_default_off_passed_with_activation"
        next_step = "run_small_guardrails_and_stage7_heldout_challenge"
    payload = {
        "schema_version": "krk_progress_window_reconsideration_runtime_smoke.v0",
        "causal_status": "runtime_test_default_off_sandbox_smoke",
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_review_packet": "reports/krk_state_local_paired_selector_runtime_proxy_review_packet_v1.json",
        "topology": str(TOPOLOGY),
        "profile": COMPOSITION_PROFILE_HANDOFF_V1,
        "protected_control_rows": rows,
        "targeted_progress_window_rows": target_rows,
        "summary": {
            "default_off_equivalence_passed": default_off_passed,
            "protected_label_count": len(rows),
            "targeted_row_count": len(target_rows),
            "enabled_supported_total": enabled_supported_total,
            "enabled_selected_supported_total": enabled_selected_supported_total,
            "targeted_monitor_confirmed_events": monitor_confirmed_total,
            "targeted_candidate_intersection_events": candidate_intersection_total,
            "target_failure_row_count": len(target_failure_rows),
            "improved_target_failure_count": improved_target_failure_count,
            "safe_regression_count": safe_regression_count,
        },
        "decision": {
            "status": status,
            "recommended_next_step": next_step,
        },
    }
    return payload


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Progress-Window Reconsideration Runtime Smoke v0",
        "",
        "This is a default-off runtime-test sandbox smoke. It is not a promotion or default policy change.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Protected Controls", ""])
    for row in payload["protected_control_rows"]:
        lines.append(
            f"- `{row['label']}` default_off=`{row['default_off_equivalence']}` "
            f"baseline=`{row['baseline']['playouts']}` enabled=`{row['enabled_support_0_5']['playouts']}` "
            f"supported=`{row['enabled_support_0_5'].get('krk_progress_window_reconsideration_supported_count')}`"
        )
    lines.extend(["", "## Targeted Progress-Window Rows", ""])
    for row in payload["targeted_progress_window_rows"]:
        diagnosis = row["enabled_support_0_5"].get("activation_diagnosis", {}) or {}
        lines.append(
            f"- `{row['frame_id']}` target_failure=`{row['target_failure_risk']}` "
            f"default_off=`{row['default_off_equivalence']}` "
            f"baseline=`{row['baseline']['result']}/{row['baseline']['plies']}` "
            f"enabled=`{row['enabled_support_0_5']['result']}/{row['enabled_support_0_5']['plies']}` "
            f"selected_supported=`{row['enabled_support_0_5']['selected_supported_count']}` "
            f"monitor_events=`{diagnosis.get('monitor_confirmed_events')}` "
            f"candidate_intersections=`{diagnosis.get('candidate_intersection_events')}`"
        )
        examples = diagnosis.get("no_supported_examples") or []
        if examples:
            example = examples[0]
            lines.append(
                f"  - first no-support example: ply=`{example.get('ply')}` "
                f"blocked=`{example.get('blocked_reason')}` "
                f"intersection=`{example.get('intersection')}`"
            )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- status: `{payload['decision']['status']}`",
            f"- next: `{payload['decision']['recommended_next_step']}`",
            "",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    payload = build_smoke()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
