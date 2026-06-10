#!/usr/bin/env python3
"""Audit Stage 7 king-tempo move-shape boundaries from existing artifacts.

This is a non-causal Growth Lab diagnostic. It compares converting king-tempo
moves from the targeted probe with moves selected by the failed sandbox smoke,
then emits visible terms that distinguish the two families.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from recon_lite_chess.krk_baseline_nodes import (  # noqa: E402
    _compute_krk_context_terms,
    _stage7_king_tempo_move_audit,
    krk_move_shape_audit,
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _active_terms(payload: dict[str, Any]) -> set[str]:
    return {str(key) for key, value in payload.items() if bool(value)}


def _chebyshev(a: int, b: int) -> int:
    return chess.square_distance(a, b)


def _square_name(square: int | None) -> str | None:
    return chess.square_name(square) if square is not None else None


def _piece_square(board: chess.Board, piece_type: chess.PieceType, color: chess.Color) -> int | None:
    squares = list(board.pieces(piece_type, color))
    return squares[0] if squares else None


def _geometry_features(board: chess.Board, move: chess.Move) -> dict[str, Any]:
    wk = _piece_square(board, chess.KING, chess.WHITE)
    bk = _piece_square(board, chess.KING, chess.BLACK)
    wr = _piece_square(board, chess.ROOK, chess.WHITE)
    if wk is None or bk is None or wr is None:
        return {}
    post = board.copy(stack=False)
    post.push(move)
    post_wk = _piece_square(post, chess.KING, chess.WHITE)
    current_box = krk_move_shape_audit(board, move, {}, include_worst_reply=False).get("current_metrics", {})
    post_metrics = krk_move_shape_audit(board, move, {}, include_worst_reply=False).get("post_move_metrics", {})
    from_file, from_rank = chess.square_file(move.from_square), chess.square_rank(move.from_square)
    to_file, to_rank = chess.square_file(move.to_square), chess.square_rank(move.to_square)
    bk_file, bk_rank = chess.square_file(bk), chess.square_rank(bk)
    wr_file, wr_rank = chess.square_file(wr), chess.square_rank(wr)
    king_rook_before = _chebyshev(wk, wr)
    king_rook_after = _chebyshev(post_wk, wr) if post_wk is not None else None
    king_enemy_before = _chebyshev(wk, bk)
    king_enemy_after = _chebyshev(post_wk, bk) if post_wk is not None else None
    return {
        "wk": _square_name(wk),
        "bk": _square_name(bk),
        "wr": _square_name(wr),
        "move_file_delta": int(to_file - from_file),
        "move_rank_delta": int(to_rank - from_rank),
        "king_enemy_file_distance_delta": int(abs(to_file - bk_file) - abs(from_file - bk_file)),
        "king_enemy_rank_distance_delta": int(abs(to_rank - bk_rank) - abs(from_rank - bk_rank)),
        "king_enemy_chebyshev_delta": (
            int(king_enemy_after - king_enemy_before)
            if king_enemy_after is not None
            else None
        ),
        "king_rook_file_distance_delta": int(abs(to_file - wr_file) - abs(from_file - wr_file)),
        "king_rook_rank_distance_delta": int(abs(to_rank - wr_rank) - abs(from_rank - wr_rank)),
        "king_rook_chebyshev_delta": (
            int(king_rook_after - king_rook_before)
            if king_rook_after is not None
            else None
        ),
        "current_box_area": current_box.get("box_area"),
        "post_box_area": post_metrics.get("box_area"),
        "current_enemy_edge_distance": current_box.get("enemy_edge_distance"),
        "post_enemy_edge_distance": post_metrics.get("enemy_edge_distance"),
        "king_moves_toward_rook_support": bool(
            king_rook_after is not None and king_rook_after < king_rook_before
        ),
        "king_moves_toward_enemy": bool(
            king_enemy_after is not None and king_enemy_after < king_enemy_before
        ),
        "compact_box_area_before_move": bool(
            current_box.get("box_area") is not None and int(current_box["box_area"]) <= 8
        ),
        "box_area_large_before_move": bool(
            current_box.get("box_area") is not None and int(current_box["box_area"]) >= 16
        ),
    }


def _record_for_move(*, fen: str, move_uci: str, source: str, outcome: str) -> dict[str, Any]:
    board = chess.Board(fen)
    move = chess.Move.from_uci(move_uci)
    shape = krk_move_shape_audit(board, move, {}, include_worst_reply=True)
    tempo = _stage7_king_tempo_move_audit(board, move)
    context = _compute_krk_context_terms(board)
    geom = _geometry_features(board, move)
    active = (
        _active_terms(context)
        | set(shape.get("current_terms", []) or [])
        | set(shape.get("move_shape_terms", []) or [])
        | set(shape.get("post_move_terms", []) or [])
        | set(shape.get("worst_reply_terms", []) or [])
        | {key for key, value in geom.items() if isinstance(value, bool) and value}
    )
    return {
        "source": source,
        "fen": fen,
        "move": move_uci,
        "outcome": outcome,
        "active_terms": sorted(active),
        "context_terms": {key: bool(value) for key, value in context.items()},
        "move_shape_terms": list(shape.get("move_shape_terms", []) or []),
        "post_move_terms": list(shape.get("post_move_terms", []) or []),
        "worst_reply_terms": list(shape.get("worst_reply_terms", []) or []),
        "stage7_king_tempo_audit": tempo,
        "geometry": geom,
    }


def _extract_probe_records(probe: dict[str, Any]) -> list[dict[str, Any]]:
    fen = str(probe.get("source_failure_fen") or "")
    records: list[dict[str, Any]] = []
    for record in probe.get("records") or []:
        if not isinstance(record, dict):
            continue
        move = record.get("move")
        if not fen or not move:
            continue
        outcome = "converts_to_mate" if record.get("converts_to_mate") else "probe_nonconverter"
        records.append(_record_for_move(fen=fen, move_uci=str(move), source="targeted_probe", outcome=outcome))
    return records


def _extract_failed_sandbox_records(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    records: dict[tuple[str, str], dict[str, Any]] = {}
    for packet in diagnostic.get("handoff_packets") or []:
        if not isinstance(packet, dict) or packet.get("phase") != "post_opponent_reply":
            continue
        evidence = packet.get("evidence_terms") or {}
        if not isinstance(evidence, dict):
            continue
        license_payload = evidence.get("visible_stage7_king_tempo_license")
        if not isinstance(license_payload, dict) or not license_payload:
            continue
        fen = evidence.get("post_reply_fen")
        move = license_payload.get("move")
        if not fen or not move:
            continue
        key = (str(fen), str(move))
        if key in records:
            continue
        records[key] = _record_for_move(
            fen=str(fen),
            move_uci=str(move),
            source="failed_sandbox_selection",
            outcome=str(evidence.get("playout_result") or "unknown"),
        )
    return list(records.values())


def _common_terms(records: Iterable[dict[str, Any]]) -> set[str]:
    items = list(records)
    if not items:
        return set()
    common = set(items[0].get("active_terms", []) or [])
    for item in items[1:]:
        common &= set(item.get("active_terms", []) or [])
    return common


def _term_counts(records: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        for term in set(record.get("active_terms", []) or []):
            counts[term] = counts.get(term, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def audit_king_tempo_move_shapes(*, probe_path: Path, diagnostic_path: Path) -> dict[str, Any]:
    probe = _load_json(probe_path)
    diagnostic = _load_json(diagnostic_path)
    probe_records = _extract_probe_records(probe)
    failed_records = _extract_failed_sandbox_records(diagnostic)
    converting = [record for record in probe_records if record.get("outcome") == "converts_to_mate"]
    probe_nonconverting = [record for record in probe_records if record.get("outcome") != "converts_to_mate"]
    failed_selected = [record for record in failed_records if record.get("outcome") != "mate"]

    converting_common = _common_terms(converting)
    failed_common = _common_terms(failed_selected)
    converting_only_common = sorted(converting_common - failed_common)
    failed_only_common = sorted(failed_common - converting_common)

    compact_converters = sum(
        1 for record in converting
        if record.get("geometry", {}).get("compact_box_area_before_move")
    )
    large_failed = sum(
        1 for record in failed_selected
        if record.get("geometry", {}).get("box_area_large_before_move")
    )
    fence_survives_converters = sum(
        1 for record in converting
        if "fence_survives_worst_reply" in set(record.get("worst_reply_terms", []) or [])
    )
    fence_survives_failed = sum(
        1 for record in failed_selected
        if "fence_survives_worst_reply" in set(record.get("worst_reply_terms", []) or [])
    )
    toward_rook_failed = sum(
        1 for record in failed_selected
        if record.get("geometry", {}).get("king_moves_toward_rook_support")
    )
    toward_rook_converting = sum(
        1 for record in converting
        if record.get("geometry", {}).get("king_moves_toward_rook_support")
    )

    suggested_terms = []
    veto_terms = []
    if compact_converters == len(converting) and large_failed:
        suggested_terms.append("compact_box_area_before_move")
        veto_terms.append("box_area_large_before_move")
    if fence_survives_converters == len(converting) and fence_survives_failed == 0:
        suggested_terms.append("fence_survives_worst_reply")
    if toward_rook_failed == len(failed_selected) and toward_rook_converting == 0:
        veto_terms.append("king_moves_toward_rook_support")

    return {
        "schema_version": "stage7_king_tempo_move_shape_audit.v1",
        "causal_status": "non_causal",
        "candidate_id": "cand.krk.box_shrink.king_tempo_handoff.v1",
        "probe_artifact": str(probe_path),
        "failed_sandbox_artifact": str(diagnostic_path),
        "counts": {
            "probe_records": len(probe_records),
            "probe_converting": len(converting),
            "probe_nonconverting": len(probe_nonconverting),
            "failed_sandbox_unique_moves": len(failed_selected),
        },
        "term_counts": {
            "converting": _term_counts(converting),
            "probe_nonconverting": _term_counts(probe_nonconverting),
            "failed_sandbox_selected": _term_counts(failed_selected),
        },
        "separating_terms": {
            "converting_common_not_failed_common": converting_only_common,
            "failed_common_not_converting_common": failed_only_common,
            "suggested_required_terms": suggested_terms,
            "suggested_veto_terms": veto_terms,
        },
        "diagnosis": (
            "king_tempo_contract_too_broad"
            if failed_selected and suggested_terms
            else "needs_more_evidence"
        ),
        "candidate_update": {
            "schema_version": "structural_candidate_update.v1",
            "candidate_id": "cand.krk.box_shrink.king_tempo_handoff.v1",
            "candidate_status": "needs_contract_refinement",
            "diagnostic_labels": [
                "parameter_or_ontology_miscalibrated",
                "selected_successor_miscalibrated",
            ],
            "proposed_change": {
                "kind": "visible_move_shape_contract_refinement",
                "required_terms": suggested_terms,
                "veto_terms": veto_terms,
                "notes": (
                    "The failed sandbox selected quiet king moves in large-box states. "
                    "The targeted converters share compact box/worst-reply survival terms."
                ),
            },
            "promotion_status": "sandboxed",
            "causal_status": "non_causal",
            "credit": 0.0,
        },
        "records": {
            "converting": converting,
            "probe_nonconverting": probe_nonconverting,
            "failed_sandbox_selected": failed_selected,
        },
    }


def _write_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 King-Tempo Move-Shape Audit",
        "",
        f"- Candidate: `{payload['candidate_id']}`",
        f"- Causal status: `{payload['causal_status']}`",
        f"- Diagnosis: `{payload['diagnosis']}`",
        f"- Counts: {payload['counts']}",
        "",
        "## Separating Terms",
        "",
        f"- Suggested required terms: {payload['separating_terms']['suggested_required_terms']}",
        f"- Suggested veto terms: {payload['separating_terms']['suggested_veto_terms']}",
        f"- Converting common not failed common: {payload['separating_terms']['converting_common_not_failed_common']}",
        f"- Failed common not converting common: {payload['separating_terms']['failed_common_not_converting_common']}",
        "",
        "## Interpretation",
        "",
        (
            "The failed sandbox did not prove the king-tempo idea wrong. It showed "
            "that the current contract is too broad: it fires in large-box states "
            "where the quiet king move does not produce conversion. The targeted "
            "converters are compact-box moves with worst-reply fence survival."
        ),
        "",
        "## Candidate Update",
        "",
        "```json",
        json.dumps(payload["candidate_update"], indent=2),
        "```",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = audit_king_tempo_move_shapes(
        probe_path=args.probe,
        diagnostic_path=args.diagnostic,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(_write_markdown(payload), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps({
            "candidate_id": payload["candidate_id"],
            "diagnosis": payload["diagnosis"],
            "suggested_required_terms": payload["separating_terms"]["suggested_required_terms"],
            "suggested_veto_terms": payload["separating_terms"]["suggested_veto_terms"],
        }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
