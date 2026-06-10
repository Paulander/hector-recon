#!/usr/bin/env python3
"""Add replay-free geometry context to ownership-selection labels."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import chess


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_krk_abstention_context_feature_dataset_v0 import _terminal_context_from_fen  # noqa: E402


OWNERSHIP = Path("reports/krk_ownership_selection_label_dataset_v2.json")
LABEL_SOURCES = [
    Path("reports/krk_strategy_arbiter_out_of_sample_control_labels_v0.json"),
    Path("reports/krk_selected_provider_diversity_ownership_labels_v0.json"),
    Path("reports/krk_selected_provider_diversity_ownership_labels_v1.json"),
]
FRAME_SOURCES = [
    Path("reports/krk_control_plane_frames_v0.json"),
    Path("reports/krk_control_plane_filtered_frames_v0.json"),
    Path("reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json"),
    Path("reports/krk_strategy_arbiter_observation_frames_v0.json"),
    Path("reports/krk_ranked_strategy_proposal_frames_v1.json"),
]
OUT_JSON = Path("reports/krk_ownership_selection_context_dataset_v0.json")
OUT_MD = Path("reports/krk_ownership_selection_context_dataset_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _label_positive(row: dict[str, Any]) -> bool:
    return row.get("target_label") == "selected_owner_converted" or row.get("owner_positive") is True


def _fen_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for path in LABEL_SOURCES:
        payload = _load(path)
        if not str(payload.get("causal_status") or "").startswith("non_causal"):
            raise ValueError(f"source must remain non-causal: {path}")
        for label in payload.get("labels") or []:
            state_id = str(label.get("state_id") or "")
            fen = label.get("fen")
            if state_id and fen:
                index.setdefault(state_id, str(fen))
    for path in FRAME_SOURCES:
        payload = _load(path)
        if not str(payload.get("causal_status") or "").startswith("non_causal"):
            raise ValueError(f"source must remain non-causal: {path}")
        for frame in (payload.get("frames") or payload.get("records") or payload.get("rows") or []):
            state_id = str(frame.get("state_id") or "")
            fen = frame.get("fen")
            if state_id and fen:
                index.setdefault(state_id, str(fen))
    return index


def _piece_at_move(board: chess.Board, move_uci: str | None) -> str:
    if not move_uci:
        return "unknown"
    try:
        move = chess.Move.from_uci(move_uci)
    except ValueError:
        return "invalid"
    piece = board.piece_at(move.from_square)
    if piece is None:
        return "missing"
    if piece.piece_type == chess.KING:
        return "king"
    if piece.piece_type == chess.ROOK:
        return "rook"
    return "other"


def _numeric(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _delta_bucket(delta: float | None) -> str:
    if delta is None:
        return "missing"
    if delta < 0:
        return "improves"
    if delta > 0:
        return "worsens"
    return "same"


def _post_move_context(fen: str | None, move_uci: str | None) -> dict[str, Any]:
    if not fen or not move_uci:
        return {"move_context_status": "missing"}
    try:
        board = chess.Board(fen)
        move = chess.Move.from_uci(move_uci)
    except ValueError:
        return {"move_context_status": "invalid"}
    if move not in board.legal_moves:
        return {
            "move_context_status": "illegal",
            "selected_piece": _piece_at_move(board, move_uci),
        }
    before = _terminal_context_from_fen(fen)
    selected_piece = _piece_at_move(board, move_uci)
    board.push(move)
    after = _terminal_context_from_fen(board.fen())
    king_distance_delta = (
        _numeric(after.get("white_king_black_king_distance"))
        - _numeric(before.get("white_king_black_king_distance"))
        if _numeric(after.get("white_king_black_king_distance")) is not None
        and _numeric(before.get("white_king_black_king_distance")) is not None
        else None
    )
    rook_distance_delta = (
        _numeric(after.get("white_king_rook_distance"))
        - _numeric(before.get("white_king_rook_distance"))
        if _numeric(after.get("white_king_rook_distance")) is not None
        and _numeric(before.get("white_king_rook_distance")) is not None
        else None
    )
    box_area_delta = (
        _numeric(after.get("box_area_proxy")) - _numeric(before.get("box_area_proxy"))
        if _numeric(after.get("box_area_proxy")) is not None and _numeric(before.get("box_area_proxy")) is not None
        else None
    )
    return {
        "move_context_status": "exact_from_fen",
        "selected_piece": selected_piece,
        "post_terminal_context": after,
        "king_distance_delta": king_distance_delta,
        "king_distance_delta_bucket": _delta_bucket(king_distance_delta),
        "rook_distance_delta": rook_distance_delta,
        "rook_distance_delta_bucket": _delta_bucket(rook_distance_delta),
        "box_area_delta": box_area_delta,
        "box_area_delta_bucket": _delta_bucket(box_area_delta),
        "rook_safe_after_proxy": after.get("rook_safe_proxy"),
    }


def _context_terms(row: dict[str, Any]) -> list[str]:
    terminal = row.get("terminal_space_context") or {}
    move = row.get("selected_move_context") or {}
    terms = [
        f"edge_bucket:{terminal.get('black_king_edge_bucket')}",
        f"box_area_relevance:{terminal.get('box_area_relevance')}",
        f"support_bucket:{terminal.get('white_king_support_bucket')}",
        f"rook_safe_proxy:{terminal.get('rook_safe_proxy')}",
        f"selected_piece:{move.get('selected_piece')}",
        f"king_distance_delta:{move.get('king_distance_delta_bucket')}",
        f"rook_distance_delta:{move.get('rook_distance_delta_bucket')}",
        f"box_area_delta:{move.get('box_area_delta_bucket')}",
        f"rook_safe_after_proxy:{move.get('rook_safe_after_proxy')}",
    ]
    return [term for term in terms if not term.endswith(":None")]


def build_dataset() -> dict[str, Any]:
    ownership = _load(OWNERSHIP)
    if ownership.get("causal_status") != "non_causal_ownership_label_dataset":
        raise ValueError("ownership labels must remain non-causal")
    fens = _fen_index()
    rows = []
    for row in ownership.get("rows") or []:
        if row.get("source_stage") == "stage7":
            continue
        fen = fens.get(str(row.get("state_id") or ""))
        terminal = _terminal_context_from_fen(fen)
        move_context = _post_move_context(fen, row.get("move_uci"))
        enriched = {
            **row,
            "schema_version": "krk_ownership_selection_context_row.v0",
            "causal_status": "non_causal_context_label",
            "fen": fen,
            "terminal_space_context": terminal,
            "selected_move_context": move_context,
            "context_terms": [],
            "usable_for_selector_training": False,
        }
        enriched["context_terms"] = _context_terms(enriched)
        rows.append(enriched)

    summary = {
        "row_count": len(rows),
        "state_count": len({row.get("state_id") for row in rows}),
        "label_counts": dict(Counter(str(row.get("target_label")) for row in rows)),
        "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
        "provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in rows)),
        "fen_join_count": sum(1 for row in rows if row.get("fen")),
        "missing_fen_count": sum(1 for row in rows if not row.get("fen")),
        "exact_move_context_count": sum(
            1 for row in rows if (row.get("selected_move_context") or {}).get("move_context_status") == "exact_from_fen"
        ),
        "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        "selector_training_row_count": sum(1 for row in rows if row.get("usable_for_selector_training")),
    }
    payload = {
        "schema_version": "krk_ownership_selection_context_dataset.v0",
        "causal_status": "non_causal_context_feature_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OWNERSHIP), *map(str, LABEL_SOURCES), *map(str, FRAME_SOURCES)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "ownership_selection_context_dataset_ready_for_non_causal_probe",
            "recommended_next_step": "probe_context_enriched_ownership_selection_features",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_dataset(payload)
    return payload


def validate_dataset(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_candidate_generator_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_row_count"] != 0:
        raise ValueError("Stage 7 rows must remain excluded")
    if payload["summary"]["selector_training_row_count"] != 0:
        raise ValueError("selector training remains blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Ownership Selection Context Dataset v0",
        "",
        "Replay-free enrichment of normal-routing ownership labels with FEN-derived terminal-space and selected-move geometry context. This is offline evidence only.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
