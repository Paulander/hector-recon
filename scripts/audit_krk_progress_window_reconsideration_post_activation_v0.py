#!/usr/bin/env python3
"""Audit why the progress-window reconsideration sandbox activated but failed.

This is a non-causal post-activation audit. It replays the single targeted
progress-window failure row, extracts selected-supported activation decisions,
and runs bounded forced-first-move continuations from those activation states.
It does not change runtime defaults, topology, promotion status, or training.
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import chess

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from recon_lite.engine import ReConEngine  # noqa: E402
from recon_lite_chess.graph.builder import build_graph_from_topology  # noqa: E402
from scripts import test_krk_landmark_progress as diag  # noqa: E402


TOPOLOGY = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json"
)
LABELS = Path("reports/krk_selected_owner_failure_risk_proxy_independent_labels_v0.json")
SMOKE = Path("reports/krk_progress_window_reconsideration_runtime_smoke_v0.json")
OUT_JSON = Path("reports/krk_progress_window_reconsideration_post_activation_audit_v0.json")
OUT_MD = Path("reports/krk_progress_window_reconsideration_post_activation_audit_v0.md")
TARGET_FRAME_ID = "cp.krk.state.ea634c29ece7"


def _settings() -> dict[str, Any]:
    return dict(diag.HANDOFF_COMPOSITION_V1_SETTINGS)


def _new_graph_engine() -> tuple[Any, ReConEngine]:
    graph = build_graph_from_topology(ROOT / TOPOLOGY)
    return graph, ReConEngine(graph)


def _target_row() -> dict[str, Any]:
    payload = json.loads((ROOT / LABELS).read_text(encoding="utf-8"))
    for row in payload.get("labels", []) or []:
        if row.get("frame_id") == TARGET_FRAME_ID:
            return row
    raise ValueError(f"target row not found: {TARGET_FRAME_ID}")


def _skill_id(item: dict[str, Any] | None) -> str | None:
    if not item:
        return None
    return diag._skill_id_for_suggestion(item)


def _selected(move_details: dict[str, Any]) -> dict[str, Any]:
    return diag._selected_engine_suggestion(move_details) or {}


def _suggestion_rows(move_details: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in move_details.get("suggestions", []) or []:
        if not isinstance(item, dict):
            continue
        meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
        payload = meta.get("krk_progress_window_reconsideration")
        rows.append(
            {
                "move": item.get("move"),
                "provider_id": _skill_id(item),
                "score": item.get("score"),
                "supported": isinstance(payload, dict) and bool(payload.get("enabled")),
                "support_payload": payload if isinstance(payload, dict) else {},
            }
        )
    return rows


def _choose_at_state(
    graph: Any,
    engine: ReConEngine,
    *,
    fen: str,
    label: str,
    stagnation_context: dict[str, Any],
    enabled: bool,
    support: float,
) -> dict[str, Any]:
    settings = _settings()
    return diag.choose_move_details(
        graph,
        engine,
        chess.Board(fen),
        max_ticks=200,
        suggestion_limit=10,
        stage_filter=None,
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
        active_landmark_label=label,
        stagnation_context=dict(stagnation_context),
        krk_progress_window_reconsideration_enabled=enabled,
        krk_progress_window_reconsideration_support=support,
        enable_diagnostic_caches=True,
    )


def _run_target_playout(row: dict[str, Any], *, enabled: bool, support: float) -> dict[str, Any]:
    graph, engine = _new_graph_engine()
    settings = _settings()
    return diag.play_to_mate(
        graph,
        engine,
        chess.Board(str(row["fen"])),
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


def _run_forced_first_continuation(
    *,
    graph: Any,
    engine: ReConEngine,
    fen: str,
    move_uci: str,
    label: str,
    cache: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    key = (fen, move_uci)
    if key in cache:
        return dict(cache[key])
    board = chess.Board(fen)
    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        result = {
            "move": move_uci,
            "result": "illegal_move",
            "plies": 0,
            "forced_first_move_legal": False,
        }
        cache[key] = result
        return dict(result)
    board.push(move)
    settings = _settings()
    result = diag.play_to_mate(
        graph,
        engine,
        board,
        random.Random(17),
        label=label,
        stage_filter=None,
        max_plies=39,
        black_policy="adversarial",
        trace=False,
        max_ticks=200,
        suggestion_limit=10,
        trace_max_plies=None,
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
        enable_diagnostic_caches=True,
    )
    summary = result.get("stagnation_summary") or {}
    compact = {
        "move": move_uci,
        "result": result.get("result"),
        "plies_after_forced_move": result.get("plies"),
        "total_plies_including_forced_move": int(result.get("plies", 0) or 0) + 1,
        "forced_first_move_legal": True,
        "final_fen": result.get("final_fen"),
        "stagnation_summary": {
            key: summary.get(key)
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
    cache[key] = compact
    return dict(compact)


def _post_terms_indicate_local_progress(payload: dict[str, Any]) -> bool:
    terms = set(payload.get("post_move_terms", []) or []) | set(
        payload.get("loop_breaking_terms", []) or []
    )
    return bool(
        terms
        & {
            "box_area_not_increased_after_move",
            "box_area_decreases_after_move",
            "enemy_edge_distance_not_increased_after_move",
            "checking_line_created",
            "white_king_distance_to_enemy_decreases",
            "white_king_distance_to_rook_decreases",
        }
    )


def _post_terms_preserve_safety(payload: dict[str, Any]) -> bool:
    terms = set(payload.get("post_move_terms", []) or []) | set(
        payload.get("loop_breaking_terms", []) or []
    )
    return {"rook_safe_after_move", "no_draw_after_move"} <= terms


def _next_white_event(trace: list[dict[str, Any]], index: int) -> dict[str, Any]:
    for event in trace[index + 1 :]:
        if event.get("turn") == "white":
            ctx = event.get("stagnation_context") if isinstance(event.get("stagnation_context"), dict) else {}
            return {
                "ply": event.get("ply"),
                "fen": event.get("fen"),
                "move": event.get("move"),
                "stagnation_context": {
                    key: ctx.get(key)
                    for key in (
                        "stagnation_loop",
                        "rook_oscillation_loop",
                        "repeated_abstract_state_count",
                        "no_progress_plies",
                    )
                },
            }
    return {}


def _activation_records(row: dict[str, Any], result: dict[str, Any]) -> list[dict[str, Any]]:
    label = str(row.get("active_landmark_label") or "edge_trap_wrong_tempo")
    graph, engine = _new_graph_engine()
    continuation_graph, continuation_engine = _new_graph_engine()
    continuation_cache: dict[tuple[str, str], dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    for index, event in enumerate(result.get("trace", []) or []):
        if event.get("turn") != "white":
            continue
        fen = str(event.get("fen") or "")
        event_engine = event.get("engine") if isinstance(event.get("engine"), dict) else {}
        event_selected = event_engine.get("selected_suggestion") or {}
        event_payload = (
            event_selected.get("krk_progress_window_reconsideration")
            if isinstance(event_selected, dict)
            else None
        )
        if not isinstance(event_payload, dict) or not event_payload.get("enabled"):
            continue
        stagnation_context = (
            event.get("stagnation_context") if isinstance(event.get("stagnation_context"), dict) else {}
        )
        baseline_details = _choose_at_state(
            graph,
            engine,
            fen=fen,
            label=label,
            stagnation_context=stagnation_context,
            enabled=False,
            support=0.0,
        )
        enabled_details = _choose_at_state(
            graph,
            engine,
            fen=fen,
            label=label,
            stagnation_context=stagnation_context,
            enabled=True,
            support=0.5,
        )
        baseline_selected = _selected(baseline_details)
        enabled_selected = _selected(enabled_details)
        suggestion_rows = _suggestion_rows(enabled_details)
        supported = [item for item in suggestion_rows if item.get("supported")]
        unsupported_visible = [
            item
            for item in suggestion_rows
            if not item.get("supported") and item.get("move")
        ][:3]

        candidate_moves: dict[str, dict[str, Any]] = {}
        selected_move = str(enabled_selected.get("move") or event.get("move") or "")
        selected_items = [item for item in suggestion_rows if str(item.get("move") or "") == selected_move]
        candidate_source = selected_items[:1] + supported[:4] + unsupported_visible[:2]
        for item in candidate_source:
            move = str(item.get("move") or "")
            if not move or move in candidate_moves:
                continue
            candidate_moves[move] = {
                "move": move,
                "providers": sorted(
                    {
                        str(row.get("provider_id"))
                        for row in suggestion_rows
                        if row.get("move") == move and row.get("provider_id")
                    }
                ),
                "supported": any(
                    bool(row.get("supported"))
                    for row in suggestion_rows
                    if row.get("move") == move
                ),
                "continuation": _run_forced_first_continuation(
                    graph=continuation_graph,
                    engine=continuation_engine,
                    fen=fen,
                    move_uci=move,
                    label=label,
                    cache=continuation_cache,
                ),
            }

        selected_candidate = candidate_moves.get(selected_move) or {
            "move": selected_move,
            "providers": [_skill_id(enabled_selected)] if _skill_id(enabled_selected) else [],
            "supported": True,
            "continuation": _run_forced_first_continuation(
                graph=continuation_graph,
                engine=continuation_engine,
                fen=fen,
                move_uci=selected_move,
                label=label,
                cache=continuation_cache,
            ),
        }
        supported_mates = [
            item for item in candidate_moves.values()
            if item.get("supported") and item.get("continuation", {}).get("result") == "mate"
        ]
        unsupported_mates = [
            item for item in candidate_moves.values()
            if not item.get("supported") and item.get("continuation", {}).get("result") == "mate"
        ]
        records.append(
            {
                "ply": event.get("ply"),
                "fen": fen,
                "current_owner_before_reconsideration": _skill_id(baseline_selected),
                "raw_selected": {
                    "move": baseline_selected.get("move"),
                    "provider_id": _skill_id(baseline_selected),
                    "score": baseline_selected.get("score"),
                },
                "reconsideration_selected": {
                    "move": enabled_selected.get("move"),
                    "provider_id": _skill_id(enabled_selected),
                    "score": enabled_selected.get("score"),
                    "support_payload": (
                        enabled_selected.get("meta", {})
                        if isinstance(enabled_selected.get("meta"), dict)
                        else {}
                    ).get("krk_progress_window_reconsideration", {}),
                },
                "event_selected_payload": event_payload,
                "all_supported_candidates": supported,
                "visible_unsupported_candidates_sample": unsupported_visible,
                "progress_window_terms": {
                    key: stagnation_context.get(key)
                    for key in (
                        "stagnation_loop",
                        "rook_oscillation_loop",
                        "no_box_progress_recently",
                        "no_edge_progress_recently",
                        "no_mate_progress_recently",
                        "safe_loop_breaking_move_available",
                        "no_progress_plies",
                        "legal_loop_breaking_moves",
                    )
                },
                "selected_supported_move_improves_local_progress_terms": (
                    _post_terms_indicate_local_progress(event_payload)
                ),
                "selected_supported_move_preserves_safety": _post_terms_preserve_safety(event_payload),
                "candidate_continuations_h40": list(candidate_moves.values()),
                "selected_supported_continuation_h40": selected_candidate.get("continuation"),
                "supported_candidate_mate_count": len(supported_mates),
                "unsupported_visible_candidate_mate_count": len(unsupported_mates),
                "supported_candidates_that_mate": supported_mates[:5],
                "unsupported_visible_candidates_that_mate": unsupported_mates[:5],
                "first_post_reconsideration_signal": _next_white_event(
                    result.get("trace", []) or [],
                    index,
                ),
            }
        )
    return records


def _classification(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        labels = ["monitor_scope_wrong"]
        return {
            "labels": labels,
            "primary": "monitor_scope_wrong",
            "reason": "No selected-supported activation records were found.",
        }
    supported_mate_count = sum(int(row.get("supported_candidate_mate_count", 0) or 0) for row in records)
    unsupported_mate_count = sum(
        int(row.get("unsupported_visible_candidate_mate_count", 0) or 0) for row in records
    )
    selected_mate_count = sum(
        1
        for row in records
        if (row.get("selected_supported_continuation_h40") or {}).get("result") == "mate"
    )
    locally_safe_progress_count = sum(
        1
        for row in records
        if row.get("selected_supported_move_improves_local_progress_terms")
        and row.get("selected_supported_move_preserves_safety")
    )
    labels: list[str] = []
    if supported_mate_count == 0:
        labels.append("candidate_set_missing_good_alternative")
    if supported_mate_count > 0 and selected_mate_count == 0:
        labels.append("supported_candidate_ranking_wrong")
    if locally_safe_progress_count and selected_mate_count == 0:
        labels.append("visible_support_terms_overbroad")
    if selected_mate_count > 0:
        labels.append("followup_policy_failure")
    if unsupported_mate_count > 0 and supported_mate_count == 0:
        labels.append("candidate_set_missing_good_alternative")
    if not labels:
        labels.append("monitor_scope_wrong")
    priority = [
        "supported_candidate_ranking_wrong",
        "candidate_set_missing_good_alternative",
        "visible_support_terms_overbroad",
        "followup_policy_failure",
        "monitor_scope_wrong",
        "horizon_or_label_issue",
    ]
    primary = next(label for label in priority if label in labels)
    return {
        "labels": sorted(set(labels), key=priority.index),
        "primary": primary,
        "supported_candidate_mate_count": supported_mate_count,
        "unsupported_visible_candidate_mate_count": unsupported_mate_count,
        "selected_supported_mate_count": selected_mate_count,
        "locally_safe_progress_count": locally_safe_progress_count,
    }


def build_audit() -> dict[str, Any]:
    row = _target_row()
    enabled_result = _run_target_playout(row, enabled=True, support=0.5)
    baseline_result = _run_target_playout(row, enabled=False, support=0.0)
    records = _activation_records(row, enabled_result)
    classes = _classification(records)
    provider_counts = Counter(
        str((record.get("reconsideration_selected") or {}).get("provider_id"))
        for record in records
    )
    return {
        "schema_version": "krk_progress_window_reconsideration_post_activation_audit.v0",
        "causal_status": "non_causal_audit",
        "sandbox_id": "sandbox.krk.progress_window_reconsideration_v0",
        "sandbox_status": "wired_but_policy_insufficient",
        "promotion_status": "quarantined_or_analysis_only",
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_smoke": str(SMOKE),
        "target_frame_id": TARGET_FRAME_ID,
        "target_fen": row.get("fen"),
        "active_landmark_label": row.get("active_landmark_label"),
        "baseline_result": {
            "result": baseline_result.get("result"),
            "plies": baseline_result.get("plies"),
            "final_fen": baseline_result.get("final_fen"),
        },
        "enabled_result": {
            "result": enabled_result.get("result"),
            "plies": enabled_result.get("plies"),
            "final_fen": enabled_result.get("final_fen"),
        },
        "activation_count": len(records),
        "selected_supported_provider_counts": dict(sorted(provider_counts.items())),
        "activation_records": records,
        "classification": classes,
        "decision": {
            "status": "post_activation_failure_classified",
            "recommended_next_step": _recommended_next(classes["primary"]),
            "implement_next_fix_now": False,
        },
    }


def _recommended_next(primary: str) -> str:
    return {
        "candidate_set_missing_good_alternative": (
            "return_to_candidate_generation_or_broader_strategy_sequence_track"
        ),
        "supported_candidate_ranking_wrong": (
            "design_narrower_candidate_ranking_policy_still_default_off"
        ),
        "visible_support_terms_overbroad": (
            "refine_support_terms_noncaually_no_runtime_patch"
        ),
        "followup_policy_failure": (
            "return_to_sequence_policy_or_plan_capsule_learning"
        ),
        "monitor_scope_wrong": "quarantine_monitor_for_now",
        "horizon_or_label_issue": "update_labels_or_horizon_classification",
    }.get(primary, "architecture_review")


def write_markdown(payload: dict[str, Any]) -> None:
    classification = payload["classification"]
    lines = [
        "# KRK Progress-Window Reconsideration Post-Activation Audit v0",
        "",
        "This is a non-causal audit of the activated-but-failed runtime-test row.",
        "",
        "## Summary",
        "",
        f"- target: `{payload['target_frame_id']}`",
        f"- sandbox_status: `{payload['sandbox_status']}`",
        f"- promotion_status: `{payload['promotion_status']}`",
        f"- baseline: `{payload['baseline_result']['result']}/{payload['baseline_result']['plies']}`",
        f"- enabled: `{payload['enabled_result']['result']}/{payload['enabled_result']['plies']}`",
        f"- activation_count: `{payload['activation_count']}`",
        f"- selected_supported_provider_counts: `{payload['selected_supported_provider_counts']}`",
        "",
        "## Classification",
        "",
        f"- primary: `{classification['primary']}`",
        f"- labels: `{classification['labels']}`",
        f"- supported_candidate_mate_count: `{classification.get('supported_candidate_mate_count')}`",
        f"- unsupported_visible_candidate_mate_count: `{classification.get('unsupported_visible_candidate_mate_count')}`",
        f"- selected_supported_mate_count: `{classification.get('selected_supported_mate_count')}`",
        f"- locally_safe_progress_count: `{classification.get('locally_safe_progress_count')}`",
        "",
        "## Activation Records",
        "",
    ]
    for record in payload["activation_records"][:12]:
        selected = record.get("reconsideration_selected") or {}
        continuation = record.get("selected_supported_continuation_h40") or {}
        lines.append(
            f"- ply `{record.get('ply')}` selected `{selected.get('provider_id')}` "
            f"`{selected.get('move')}` -> `{continuation.get('result')}`/"
            f"`{continuation.get('total_plies_including_forced_move')}`; "
            f"supported_mates=`{record.get('supported_candidate_mate_count')}` "
            f"unsupported_mates=`{record.get('unsupported_visible_candidate_mate_count')}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- status: `{payload['decision']['status']}`",
            f"- next: `{payload['decision']['recommended_next_step']}`",
            "- implement_next_fix_now: `False`",
            "",
            "Do not enable by default, tune support amount, run guardrails, promote Stage 7, train Stage 8, or turn this into a general pre-decision selector from this audit.",
            "",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    payload = build_audit()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)
    print(json.dumps(payload["classification"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
