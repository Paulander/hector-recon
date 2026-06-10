#!/usr/bin/env python3
"""Audit simple KRK geometry features for protected capacity labels."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import chess


ROOT = Path(__file__).resolve().parents[1]
CAPACITY_FRAMES = Path("reports/krk_protected_provider_coverage_frames_v0.json")
NEGATIVE_EVIDENCE = Path("reports/krk_selector_negative_suppression_evidence_v0.json")
OUT_JSON = Path("reports/krk_capacity_geometry_feature_audit_v0.json")
OUT_MD = Path("reports/krk_capacity_geometry_feature_audit_v0.md")


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
    corners = [chess.A1, chess.A8, chess.H1, chess.H8]
    return min(_chebyshev(square, corner) for corner in corners)


def _piece_name(piece: chess.Piece | None) -> str | None:
    if piece is None:
        return None
    if piece.piece_type == chess.KING:
        return "king"
    if piece.piece_type == chess.ROOK:
        return "rook"
    return piece.symbol().lower()


def _features_for_row(row: dict[str, Any]) -> dict[str, Any]:
    board = chess.Board(str(row.get("fen") or ""))
    move = chess.Move.from_uci(str(row.get("forced_first_move") or "0000"))
    white_king_before = board.king(chess.WHITE)
    black_king_before = board.king(chess.BLACK)
    rook_before = next(iter(board.pieces(chess.ROOK, chess.WHITE)), None)
    piece = board.piece_at(move.from_square)
    if white_king_before is None or black_king_before is None or rook_before is None:
        raise ValueError(f"missing KRK pieces in row {row.get('source_label_job_id')}")
    piece_name = _piece_name(piece)
    wk_dist_before = _chebyshev(white_king_before, black_king_before)
    rook_dist_before = _manhattan(rook_before, black_king_before)
    board_after = board.copy(stack=False)
    if move in board_after.legal_moves:
        board_after.push(move)
    else:
        # Forced labels should be legal. Keep the audit explicit if an artifact
        # is malformed rather than silently inventing post-move features.
        raise ValueError(f"illegal forced move {move.uci()} in {row.get('source_label_job_id')}")
    white_king_after = board_after.king(chess.WHITE)
    black_king_after = board_after.king(chess.BLACK)
    rook_after = next(iter(board_after.pieces(chess.ROOK, chess.WHITE)), None)
    assert white_king_after is not None and black_king_after is not None and rook_after is not None
    wk_dist_after = _chebyshev(white_king_after, black_king_after)
    rook_dist_after = _manhattan(rook_after, black_king_after)
    return {
        "black_king_edge_distance": _edge_distance(black_king_before),
        "black_king_corner_distance": _corner_distance(black_king_before),
        "forced_piece_type": piece_name,
        "white_king_distance_to_black_before": wk_dist_before,
        "white_king_distance_to_black_after": wk_dist_after,
        "white_king_distance_delta": wk_dist_after - wk_dist_before,
        "king_moves_toward_black": piece_name == "king" and wk_dist_after < wk_dist_before,
        "king_moves_away_from_black": piece_name == "king" and wk_dist_after > wk_dist_before,
        "rook_distance_to_black_before": rook_dist_before,
        "rook_distance_to_black_after": rook_dist_after,
        "rook_distance_delta": rook_dist_after - rook_dist_before,
        "rook_moves_toward_black": piece_name == "rook" and rook_dist_after < rook_dist_before,
        "rook_moves_away_from_black": piece_name == "rook" and rook_dist_after > rook_dist_before,
        "rook_same_file_as_black_after": chess.square_file(rook_after) == chess.square_file(black_king_after),
        "rook_same_rank_as_black_after": chess.square_rank(rook_after) == chess.square_rank(black_king_after),
        "black_king_legal_reply_count_after": len(list(board_after.legal_moves)),
    }


def build_audit() -> dict[str, Any]:
    capacity = _load(CAPACITY_FRAMES)
    negative_evidence = _load(NEGATIVE_EVIDENCE)
    if capacity.get("causal_status") != "non_causal_capacity_frame_dataset":
        raise ValueError("capacity frames must remain non-causal")
    if negative_evidence.get("causal_status") != "non_causal_evidence_audit":
        raise ValueError("negative suppression evidence must remain non-causal")
    rows = []
    for row in capacity.get("rows") or []:
        features = _features_for_row(row)
        rows.append({
            "schema_version": "krk_capacity_geometry_feature_row.v0",
            "causal_status": "non_causal_feature_evidence",
            "state_id": row.get("state_id"),
            "source_stage": row.get("source_stage"),
            "provider_id": row.get("provider_id"),
            "provider_family": row.get("provider_family"),
            "capacity_label": row.get("capacity_label"),
            "forced_first_move": row.get("forced_first_move"),
            "forced_plies": row.get("forced_plies"),
            **features,
        })
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_label[str(row.get("capacity_label"))].append(row)

    bool_terms = [
        "king_moves_toward_black",
        "king_moves_away_from_black",
        "rook_moves_toward_black",
        "rook_moves_away_from_black",
        "rook_same_file_as_black_after",
        "rook_same_rank_as_black_after",
    ]
    term_summary = {}
    for term in bool_terms:
        term_summary[term] = {
            label: sum(1 for row in label_rows if row.get(term))
            for label, label_rows in by_label.items()
        }
    piece_by_label = {
        label: dict(Counter(str(row.get("forced_piece_type")) for row in label_rows))
        for label, label_rows in by_label.items()
    }
    status = "geometry_terms_partially_informative_not_sufficient"
    recommendation = "add_geometry_terms_to_non_causal_selector_feature_benchmark"
    payload = {
        "schema_version": "krk_capacity_geometry_feature_audit.v0",
        "causal_status": "non_causal_feature_audit",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(CAPACITY_FRAMES), str(NEGATIVE_EVIDENCE)],
        "summary": {
            "row_count": len(rows),
            "capacity_label_counts": dict(Counter(str(row.get("capacity_label")) for row in rows)),
            "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
            "provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in rows)),
            "forced_piece_type_by_label": piece_by_label,
            "term_true_counts_by_label": term_summary,
            "black_king_edge_distance_values_by_label": {
                label: sorted({row.get("black_king_edge_distance") for row in label_rows})
                for label, label_rows in by_label.items()
            },
            "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        },
        "rows": rows,
        "interpretation": {
            "primary": "Simple geometry gives useful diagnostics but does not fully separate positive and negative capacity.",
            "notable_pattern": (
                "Several positive and negative rows share edge-distance and provider-family contexts; selector features need "
                "move/post-move geometry and same-state alternatives, not just provider family or normalized score."
            ),
            "directed_fix_class": "non_causal_geometry_augmented_selector_feature_benchmark",
        },
        "decision": {
            "status": status,
            "recommended_next_step": recommendation,
            "runtime_work_allowed": False,
            "candidate_generator_runtime_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_audit(payload)
    return payload


def validate_audit(payload: dict[str, Any]) -> None:
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
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Capacity Geometry Feature Audit v0",
        "",
        "This replay-free audit computes simple visible geometry terms for protected capacity labels.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Rows", ""])
    for row in payload["rows"]:
        lines.append(
            f"- state=`{row['state_id']}` label=`{row['capacity_label']}` provider=`{row['provider_id']}` "
            f"move=`{row['forced_first_move']}` piece=`{row['forced_piece_type']}` "
            f"king_delta=`{row['white_king_distance_delta']}` rook_delta=`{row['rook_distance_delta']}`"
        )
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_audit()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
