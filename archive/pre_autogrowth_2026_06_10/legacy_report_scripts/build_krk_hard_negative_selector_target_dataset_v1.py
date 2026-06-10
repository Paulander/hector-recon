#!/usr/bin/env python3
"""Build expanded non-causal hard-negative selector targets."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import chess


ROOT = Path(__file__).resolve().parents[1]
TARGETS_V0 = Path("reports/krk_hard_negative_selector_target_dataset_v0.json")
BALANCED_LABELS = Path("reports/krk_balanced_hard_negative_labels_v0.json")
SEMANTICS = Path("reports/krk_hard_negative_selector_target_training_semantics_review_v0.json")
OUT_JSON = Path("reports/krk_hard_negative_selector_target_dataset_v1.json")
OUT_MD = Path("reports/krk_hard_negative_selector_target_dataset_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _coord(square: int) -> tuple[int, int]:
    return chess.square_file(square), chess.square_rank(square)


def _chebyshev(a: int, b: int) -> int:
    af, ar = _coord(a)
    bf, br = _coord(b)
    return max(abs(af - bf), abs(ar - br))


def _manhattan(a: int, b: int) -> int:
    af, ar = _coord(a)
    bf, br = _coord(b)
    return abs(af - bf) + abs(ar - br)


def _edge_distance(square: int) -> int:
    file, rank = _coord(square)
    return min(file, 7 - file, rank, 7 - rank)


def _corner_distance(square: int) -> int:
    return min(_chebyshev(square, corner) for corner in (chess.A1, chess.A8, chess.H1, chess.H8))


def _piece_name(piece: chess.Piece | None) -> str | None:
    if piece is None:
        return None
    if piece.piece_type == chess.KING:
        return "king"
    if piece.piece_type == chess.ROOK:
        return "rook"
    return piece.symbol().lower()


def _provider_family(provider_id: str) -> str:
    if "stage0_basin" in provider_id:
        return "stage0_basin"
    if "drive_to_edge" in provider_id:
        return "drive_to_edge"
    if "fence_established" in provider_id:
        return "fence_established"
    if "edge_trap" in provider_id:
        return "edge_trap"
    return provider_id.rsplit(".", 1)[-1]


def _target_kind(result: Any) -> str | None:
    if result == "mate":
        return "positive_capacity_context"
    if result == "max_plies":
        return "hard_negative_capacity"
    return None


def _features(fen: str, move_uci: str) -> dict[str, Any]:
    board = chess.Board(fen)
    move = chess.Move.from_uci(move_uci)
    white_king_before = board.king(chess.WHITE)
    black_king_before = board.king(chess.BLACK)
    rook_before = next(iter(board.pieces(chess.ROOK, chess.WHITE)), None)
    if white_king_before is None or black_king_before is None or rook_before is None:
        raise ValueError(f"missing KRK pieces in {fen}")
    piece = board.piece_at(move.from_square)
    piece_name = _piece_name(piece)
    wk_before = _chebyshev(white_king_before, black_king_before)
    rook_before_dist = _manhattan(rook_before, black_king_before)
    after = board.copy(stack=False)
    if move not in after.legal_moves:
        raise ValueError(f"illegal forced move {move_uci} in {fen}")
    after.push(move)
    white_king_after = after.king(chess.WHITE)
    black_king_after = after.king(chess.BLACK)
    rook_after = next(iter(after.pieces(chess.ROOK, chess.WHITE)), None)
    assert white_king_after is not None and black_king_after is not None and rook_after is not None
    wk_after = _chebyshev(white_king_after, black_king_after)
    rook_after_dist = _manhattan(rook_after, black_king_after)
    return {
        "black_king_edge_distance": _edge_distance(black_king_before),
        "black_king_corner_distance": _corner_distance(black_king_before),
        "forced_piece_type": piece_name,
        "white_king_distance_to_black_before": wk_before,
        "white_king_distance_to_black_after": wk_after,
        "white_king_distance_delta": wk_after - wk_before,
        "king_moves_toward_black": piece_name == "king" and wk_after < wk_before,
        "king_moves_away_from_black": piece_name == "king" and wk_after > wk_before,
        "rook_distance_to_black_before": rook_before_dist,
        "rook_distance_to_black_after": rook_after_dist,
        "rook_distance_delta": rook_after_dist - rook_before_dist,
        "rook_moves_toward_black": piece_name == "rook" and rook_after_dist < rook_before_dist,
        "rook_moves_away_from_black": piece_name == "rook" and rook_after_dist > rook_before_dist,
        "rook_same_file_as_black_after": chess.square_file(rook_after) == chess.square_file(black_king_after),
        "rook_same_rank_as_black_after": chess.square_rank(rook_after) == chess.square_rank(black_king_after),
        "black_king_legal_reply_count_after": len(list(after.legal_moves)),
    }


def _row_from_label(label: dict[str, Any]) -> dict[str, Any] | None:
    target = _target_kind(label.get("result"))
    if target is None:
        return None
    move = str(label.get("forced_first_move") or "")
    fen = str(label.get("fen") or "")
    if not move or not fen:
        return None
    provider_id = str(label.get("provider_id") or "")
    return {
        "schema_version": "krk_hard_negative_selector_target_candidate.v1",
        "causal_status": "non_causal_target_candidate",
        "target_kind": target,
        "label_semantics": "forced_provider_capacity_label_not_runtime_ownership",
        "source_artifact_channel": "balanced_protected_hard_negative_capacity",
        "state_id": label.get("state_id"),
        "frame_id": label.get("frame_id"),
        "source_stage": label.get("source_stage"),
        "active_landmark_label": label.get("source_active_landmark_label") or label.get("active_landmark_label"),
        "provider_id": provider_id,
        "provider_family": label.get("provider_family") or _provider_family(provider_id),
        "capacity_label": label.get("capacity_label"),
        "forced_first_move": move,
        "forced_plies": label.get("plies"),
        "forced_successor_available": label.get("forced_successor_available"),
        "provider_version": label.get("provider_version"),
        **_features(fen, move),
        "usable_for_training": False,
        "training_block_reason": "selector training remains blocked; offline benchmark evidence only",
        "stage7_challenge_row": False,
    }


def build_dataset() -> dict[str, Any]:
    v0 = _load(TARGETS_V0)
    labels = _load(BALANCED_LABELS)
    semantics = _load(SEMANTICS)
    if v0.get("causal_status") != "non_causal_target_dataset":
        raise ValueError("v0 targets must remain non-causal")
    if labels.get("causal_status") != "non_causal_label_run":
        raise ValueError("balanced labels must remain non-causal")
    if semantics.get("causal_status") != "non_causal_semantics_review":
        raise ValueError("semantics review must remain non-causal")
    rows = []
    seen: set[tuple[str, str, str]] = set()
    for row in v0.get("rows") or []:
        copied = dict(row)
        copied["schema_version"] = "krk_hard_negative_selector_target_candidate.v1"
        copied.setdefault("source_artifact_channel", "protected_provider_capacity_v0")
        key = (str(copied.get("state_id")), str(copied.get("provider_id")), str(copied.get("forced_first_move")))
        rows.append(copied)
        seen.add(key)
    for label in labels.get("labels") or []:
        row = _row_from_label(label)
        if row is None:
            continue
        key = (str(row.get("state_id")), str(row.get("provider_id")), str(row.get("forced_first_move")))
        if key in seen:
            continue
        rows.append(row)
        seen.add(key)
    summary = {
        "row_count": len(rows),
        "target_kind_counts": dict(Counter(str(row.get("target_kind")) for row in rows)),
        "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
        "provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in rows)),
        "source_artifact_channel_counts": dict(Counter(str(row.get("source_artifact_channel")) for row in rows)),
        "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        "training_row_count": sum(1 for row in rows if row.get("usable_for_training")),
        "state_count": len({row.get("state_id") for row in rows}),
        "hard_negative_state_count": len({row.get("state_id") for row in rows if row.get("target_kind") == "hard_negative_capacity"}),
    }
    payload = {
        "schema_version": "krk_hard_negative_selector_target_dataset.v1",
        "causal_status": "non_causal_target_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(TARGETS_V0), str(BALANCED_LABELS), str(SEMANTICS)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "hard_negative_selector_target_dataset_expanded",
            "recommended_next_step": "run_hard_negative_selector_feature_ablation_v1",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "offline_benchmark_allowed": True,
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
    if payload["summary"]["training_row_count"] != 0:
        raise ValueError("target candidates are not training rows")
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")
    for row in payload.get("rows") or []:
        if row.get("causal_status") != "non_causal_target_candidate":
            raise ValueError("target rows must remain non-causal")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Hard-Negative Selector Target Dataset v1",
        "",
        "Expanded non-causal selector target candidates after the balanced protected label run.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Rows", ""])
    for row in payload["rows"]:
        lines.append(
            f"- state=`{row['state_id']}` stage=`{row['source_stage']}` target=`{row['target_kind']}` "
            f"provider=`{row['provider_id']}` move=`{row['forced_first_move']}` "
            f"piece=`{row['forced_piece_type']}` king_delta=`{row['white_king_distance_delta']}` "
            f"rook_delta=`{row['rook_distance_delta']}`"
        )
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
