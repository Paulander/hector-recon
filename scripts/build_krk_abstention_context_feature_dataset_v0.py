#!/usr/bin/env python3
"""Join abstention labels with replay-free control-plane context features."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ABSTENTION_DATASET = Path("reports/krk_abstention_training_dataset_v1.json")
CONTROL_FRAMES = Path("reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json")
OUT_JSON = Path("reports/krk_abstention_context_feature_dataset_v0.json")
OUT_MD = Path("reports/krk_abstention_context_feature_dataset_v0.md")


def _load_json(root: Path, path: Path) -> dict[str, Any]:
    payload = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _piece_square(board_part: str, piece: str) -> tuple[int, int] | None:
    ranks = board_part.split("/")
    for fen_rank_index, rank_text in enumerate(ranks):
        rank = 7 - fen_rank_index
        file = 0
        for char in rank_text:
            if char.isdigit():
                file += int(char)
                continue
            if char == piece:
                return file, rank
            file += 1
    return None


def _chebyshev(a: tuple[int, int] | None, b: tuple[int, int] | None) -> int | None:
    if a is None or b is None:
        return None
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _terminal_context_from_fen(fen: str | None) -> dict[str, Any]:
    if not fen:
        return {"feature_source_status": "missing_fen"}
    board = fen.split()[0]
    white_king = _piece_square(board, "K")
    white_rook = _piece_square(board, "R")
    black_king = _piece_square(board, "k")
    if white_king is None or white_rook is None or black_king is None:
        return {"feature_source_status": "missing_krk_piece"}

    bk_file, bk_rank = black_king
    edge_distance = min(bk_file, bk_rank, 7 - bk_file, 7 - bk_rank)
    if edge_distance == 0:
        edge_bucket = "edge"
        box_area_relevance = "low"
    elif edge_distance == 1:
        edge_bucket = "near_edge"
        box_area_relevance = "medium"
    else:
        edge_bucket = "interior"
        box_area_relevance = "high"

    king_distance = _chebyshev(white_king, black_king)
    rook_distance = _chebyshev(white_rook, black_king)
    king_to_rook_distance = _chebyshev(white_king, white_rook)
    rook_safe_proxy = bool(rook_distance is not None and (rook_distance > 1 or (king_to_rook_distance or 9) <= 1))
    support_bucket = "unknown"
    if king_distance is not None:
        support_bucket = "close" if king_distance <= 2 else "medium" if king_distance <= 3 else "far"

    file_span = abs(white_rook[0] - black_king[0]) + 1
    rank_span = abs(white_rook[1] - black_king[1]) + 1
    box_area_proxy = file_span * rank_span
    enemy_mobility_proxy = max(0, (2 * edge_distance + 3))
    return {
        "feature_source_status": "fen_proxy",
        "black_king_edge_distance": edge_distance,
        "black_king_edge_bucket": edge_bucket,
        "box_area_proxy": box_area_proxy,
        "box_area_relevance": box_area_relevance,
        "rook_safe_proxy": rook_safe_proxy,
        "white_king_black_king_distance": king_distance,
        "white_king_support_bucket": support_bucket,
        "white_king_rook_distance": king_to_rook_distance,
        "enemy_king_mobility_proxy": enemy_mobility_proxy,
    }


def _provider_family(provider_id: str | None) -> str:
    text = str(provider_id or "")
    if text == "krk.stage0_basin":
        return "stage0_basin"
    if text == "krk.drive_to_edge":
        return "drive_to_edge"
    if text == "krk.fence_established":
        return "fence_established"
    if text.startswith("krk.edge_trap"):
        return "edge_trap"
    if text.startswith("krk.box_shrink"):
        return "box_shrink"
    return "other"


def _monitor_features(frame: dict[str, Any]) -> dict[str, Any]:
    monitors = frame.get("internal_monitor_records") or []
    monitor_types = sorted({str(item.get("monitor_type")) for item in monitors if item.get("monitor_type")})
    terminal_ids = sorted({str(item.get("terminal_id")) for item in monitors if item.get("terminal_id")})
    source_terms = sorted({
        str(term)
        for item in monitors
        for term in (item.get("source_terms_met") or item.get("source_terms") or [])
    })
    confidence_values = [
        float(item["confidence"])
        for item in monitors
        if isinstance(item.get("confidence"), int | float)
    ]
    return {
        "monitor_count": len(monitors),
        "monitor_types_present": monitor_types,
        "monitor_terminal_ids": terminal_ids,
        "monitor_source_terms": source_terms,
        "has_phase_boundary_monitor": "PhaseBoundaryMonitor" in monitor_types,
        "has_owner_exit_monitor": "OwnerExitMonitor" in monitor_types,
        "has_repair_needed_monitor": "RepairNeededMonitor" in monitor_types,
        "has_plan_selection_monitor": "PlanSelectionNeededMonitor" in monitor_types,
        "monitor_confidence_max": max(confidence_values) if confidence_values else None,
        "monitor_signature": "+".join(monitor_types) if monitor_types else "none",
    }


def _proposal_features(frame: dict[str, Any], provider_id: str, move_uci: str | None) -> dict[str, Any]:
    proposals = frame.get("strategy_proposal_frames") or []
    scored = [
        proposal
        for proposal in proposals
        if isinstance(proposal.get("raw_score"), int | float)
    ]
    ranked = sorted(scored, key=lambda proposal: float(proposal.get("raw_score")), reverse=True)
    top_raw = float(ranked[0]["raw_score"]) if ranked else None
    provider_matches = [
        proposal for proposal in proposals if str(proposal.get("provider_id")) == str(provider_id)
    ]
    exact_matches = [
        proposal
        for proposal in provider_matches
        if move_uci and str(proposal.get("move_uci")) == str(move_uci)
    ]
    match = (exact_matches or provider_matches or [None])[0]
    if match is None:
        return {
            "proposal_count": len(proposals),
            "matched_proposal": False,
            "proposal_match_kind": "missing_provider_proposal",
            "proposal_raw_score": None,
            "proposal_normalized_score": None,
            "proposal_provider_local_rank": None,
            "proposal_global_raw_rank": None,
            "proposal_raw_score_gap_to_top": None,
            "top_provider_id": ranked[0].get("provider_id") if ranked else None,
            "top_provider_family": _provider_family(ranked[0].get("provider_id")) if ranked else None,
        }
    global_rank = None
    for index, proposal in enumerate(ranked, start=1):
        if proposal is match:
            global_rank = index
            break
    raw_score = match.get("raw_score")
    return {
        "proposal_count": len(proposals),
        "matched_proposal": True,
        "proposal_match_kind": "provider_and_move" if exact_matches else "provider_only",
        "proposal_raw_score": raw_score,
        "proposal_normalized_score": match.get("normalized_score"),
        "proposal_provider_local_rank": match.get("provider_local_rank"),
        "proposal_global_raw_rank": global_rank,
        "proposal_raw_score_gap_to_top": (top_raw - float(raw_score)) if top_raw is not None and isinstance(raw_score, int | float) else None,
        "top_provider_id": ranked[0].get("provider_id") if ranked else None,
        "top_provider_family": _provider_family(ranked[0].get("provider_id")) if ranked else None,
    }


def _build_row(row: dict[str, Any], frame: dict[str, Any]) -> dict[str, Any]:
    terminal_context = _terminal_context_from_fen(frame.get("fen"))
    monitor_context = _monitor_features(frame)
    proposal_context = _proposal_features(
        frame,
        str(row.get("provider_id") or ""),
        row.get("forced_first_move"),
    )
    label_source_kind = "selected_playout_success" if row.get("target_kind") == "selected_playout_success" else "forced_provider_conversion"
    return {
        "schema_version": "krk_abstention_context_feature_row.v0",
        "causal_status": "non_causal_context_feature_example",
        "state_id": row.get("state_id"),
        "frame_id": row.get("frame_id") or frame.get("frame_id"),
        "fen": frame.get("fen"),
        "source_stage": row.get("source_stage"),
        "active_landmark_label": row.get("active_landmark_label") or frame.get("active_landmark_label"),
        "provider_id": row.get("provider_id"),
        "provider_family": row.get("provider_family") or _provider_family(row.get("provider_id")),
        "provider_maturity": row.get("provider_maturity"),
        "provider_version": row.get("provider_version"),
        "move_uci": row.get("forced_first_move"),
        "label": row.get("abstention_label"),
        "label_unsafe": row.get("abstention_label") == "unsafe_owner",
        "label_source_artifact": row.get("label_source_artifact"),
        "label_source_kind": label_source_kind,
        "forced_result": row.get("forced_result"),
        "forced_plies": row.get("forced_plies"),
        "terminal_space_context": terminal_context,
        "proposal_context": proposal_context,
        "monitor_context": monitor_context,
        "frame_outcome": frame.get("outcome"),
        "frame_filter_metadata": frame.get("filter_metadata") or {},
        "usable_for_training": row.get("usable_for_training") is True and row.get("source_stage") != "stage7",
    }


def validate_dataset(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_training_rows"] != 0:
        raise ValueError("Stage7 rows must remain excluded from abstention-context training")
    for row in payload.get("rows") or []:
        if row.get("causal_status") != "non_causal_context_feature_example":
            raise ValueError("all context rows must remain non-causal")


def build_dataset(root: Path = ROOT) -> dict[str, Any]:
    abstention = _load_json(root, ABSTENTION_DATASET)
    frames_payload = _load_json(root, CONTROL_FRAMES)
    if abstention.get("causal_status") != "non_causal_abstention_dataset":
        raise ValueError("abstention dataset must remain non-causal")
    if not str(frames_payload.get("causal_status") or "").startswith("non_causal"):
        raise ValueError("control-plane frames must remain non-causal")
    frames = {str(frame.get("state_id")): frame for frame in frames_payload.get("frames") or []}
    rows = []
    missing_frame_count = 0
    for row in abstention.get("rows") or []:
        frame = frames.get(str(row.get("state_id")))
        if frame is None:
            missing_frame_count += 1
            continue
        rows.append(_build_row(row, frame))

    label_counts = Counter(str(row["label"]) for row in rows)
    stage_counts = Counter(str(row["source_stage"]) for row in rows)
    source_kind_counts = Counter(str(row["label_source_kind"]) for row in rows)
    matched_proposal_count = sum(1 for row in rows if row["proposal_context"]["matched_proposal"])
    exact_feature_count = sum(
        1 for row in rows if row["terminal_space_context"].get("feature_source_status") == "fen_proxy"
    )
    summary = {
        "row_count": len(rows),
        "state_count": len({row["state_id"] for row in rows}),
        "label_counts": dict(label_counts),
        "stage_counts": dict(stage_counts),
        "source_kind_counts": dict(source_kind_counts),
        "missing_frame_count": missing_frame_count,
        "matched_proposal_count": matched_proposal_count,
        "terminal_context_proxy_count": exact_feature_count,
        "stage7_training_rows": sum(1 for row in rows if row["source_stage"] == "stage7" and row["usable_for_training"]),
    }
    payload = {
        "schema_version": "krk_abstention_context_feature_dataset.v0",
        "causal_status": "non_causal_context_feature_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(ABSTENTION_DATASET), str(CONTROL_FRAMES)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "abstention_context_feature_dataset_ready_for_non_causal_probe",
            "recommended_next_step": "probe_abstention_context_features_non_causal",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_dataset(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Abstention Context Feature Dataset v0",
        "",
        "This replay-free dataset joins abstention labels to existing control-plane evidence. It derives terminal-space context from FEN proxies and monitor/proposal metadata only; it does not run playouts or change runtime behavior.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend([
        "",
        "## Feature Groups",
        "",
        "- `terminal_space_context`: FEN-derived KRK geometry proxies.",
        "- `proposal_context`: matched provider proposal score/rank metadata when available.",
        "- `monitor_context`: non-causal monitor evidence already present on the control-plane frame.",
        "",
        "## Decision",
        "",
        f"- Status: `{payload['decision']['status']}`",
        f"- Recommended next step: `{payload['decision']['recommended_next_step']}`",
        f"- Runtime test allowed next: `{payload['decision']['runtime_test_allowed_next']}`",
        f"- Stage 7 promotion allowed: `{payload['decision']['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{payload['decision']['stage8_training_allowed']}`",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    payload = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
