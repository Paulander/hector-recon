#!/usr/bin/env python3
"""Analyze non-causal Plan Capsule owned-window progress from traced playouts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import chess


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _metrics(fen: str) -> dict[str, int] | None:
    board = chess.Board(fen)
    wk = next(iter(board.pieces(chess.KING, chess.WHITE)), None)
    bk = next(iter(board.pieces(chess.KING, chess.BLACK)), None)
    wr = next(iter(board.pieces(chess.ROOK, chess.WHITE)), None)
    if wk is None or bk is None or wr is None:
        return None
    bk_file, bk_rank = chess.square_file(bk), chess.square_rank(bk)
    wr_file, wr_rank = chess.square_file(wr), chess.square_rank(wr)
    edge = min(bk_file, 7 - bk_file, bk_rank, 7 - bk_rank)
    corner = min(
        max(abs(bk_file - file_), abs(bk_rank - rank_))
        for file_, rank_ in ((0, 0), (0, 7), (7, 0), (7, 7))
    )
    box_width = max(1, wr_file if bk_file < wr_file else 7 - wr_file)
    box_height = max(1, wr_rank if bk_rank < wr_rank else 7 - wr_rank)
    return {
        "box_area": int(box_width * box_height),
        "enemy_edge_distance": int(edge),
        "enemy_corner_distance": int(corner),
        "white_king_enemy_distance": int(chess.square_distance(wk, bk)),
        "white_king_rook_distance": int(chess.square_distance(wk, wr)),
    }


def _first_marker_by_state(diagnostic: dict[str, Any], capsule_id: str) -> dict[str, dict[str, Any]]:
    markers: dict[str, dict[str, Any]] = {}
    for packet in diagnostic.get("handoff_packets") or []:
        if not isinstance(packet, dict):
            continue
        evidence = packet.get("evidence_terms") or {}
        if not isinstance(evidence, dict):
            continue
        marker = (evidence.get("plan_capsule_markers") or {}).get(capsule_id)
        fen = evidence.get("post_reply_fen")
        if isinstance(marker, dict) and fen and fen not in markers:
            markers[fen] = {
                "marker": marker,
                "packet_evidence": evidence,
            }
    return markers


def _white_events_from(trace: list[dict[str, Any]], start_fen: str, ttl: int) -> list[dict[str, Any]]:
    for index, event in enumerate(trace):
        if event.get("turn") == "white" and event.get("fen") == start_fen:
            return [
                item
                for item in trace[index:]
                if isinstance(item, dict) and item.get("turn") == "white"
            ][:ttl]
    return []


def _progress_terms(start: dict[str, int], end: dict[str, int]) -> list[str]:
    terms = []
    if end["box_area"] < start["box_area"]:
        terms.append("box_area_decreased_over_owned_window")
    elif end["box_area"] == start["box_area"]:
        terms.append("box_area_preserved_over_owned_window")
    if end["enemy_edge_distance"] <= start["enemy_edge_distance"]:
        terms.append("enemy_edge_distance_not_worse_over_owned_window")
    if end["enemy_corner_distance"] <= start["enemy_corner_distance"]:
        terms.append("enemy_corner_distance_not_worse_over_owned_window")
    if end["white_king_enemy_distance"] < start["white_king_enemy_distance"]:
        terms.append("white_king_support_improved_over_owned_window")
    if end["white_king_rook_distance"] <= start["white_king_rook_distance"]:
        terms.append("white_king_rook_coordination_not_worse_over_owned_window")
    return terms


def analyze_owned_window(
    diagnostic: dict[str, Any],
    *,
    capsule_id: str,
    ttl_white_moves: int,
) -> dict[str, Any]:
    markers_by_fen = _first_marker_by_state(diagnostic, capsule_id)
    windows = []
    for playout in diagnostic.get("debug_playouts") or []:
        trace = [event for event in playout.get("trace") or [] if isinstance(event, dict)]
        for start_fen, marker_payload in markers_by_fen.items():
            white_events = _white_events_from(trace, start_fen, ttl_white_moves)
            if not white_events:
                continue
            first = white_events[0]
            last = white_events[-1]
            start_metrics = _metrics(first["fen"])
            end_fen = last.get("resulting_fen") or last.get("fen")
            end_metrics = _metrics(end_fen) if end_fen else None
            if not start_metrics or not end_metrics:
                continue
            terms = _progress_terms(start_metrics, end_metrics)
            ttl_failure = len(white_events) >= ttl_white_moves and not any(
                term in terms
                for term in (
                    "box_area_decreased_over_owned_window",
                    "white_king_support_improved_over_owned_window",
                )
            )
            windows.append(
                {
                    "sample": playout.get("sample"),
                    "result": playout.get("result"),
                    "start_fen": start_fen,
                    "moves": [event.get("move") for event in white_events],
                    "owned_white_move_count": len(white_events),
                    "ttl_white_moves": ttl_white_moves,
                    "start_metrics": start_metrics,
                    "end_metrics": end_metrics,
                    "progress_terms": terms,
                    "ttl_failure": ttl_failure,
                    "entry_confirmed": bool(marker_payload["marker"].get("entry_confirmed")),
                    "abort_terms_at_entry": marker_payload["marker"].get("abort_terms_met") or [],
                }
            )
    ttl_failures = sum(1 for item in windows if item["ttl_failure"])
    return {
        "schema_version": "plan_capsule_owned_window_analysis.v1",
        "causal_status": "non_causal",
        "capsule_id": capsule_id,
        "ttl_white_moves": ttl_white_moves,
        "window_count": len(windows),
        "ttl_failure_count": ttl_failures,
        "windows": windows,
        "diagnosis": (
            "owned_window_progress_visible"
            if windows and ttl_failures < len(windows)
            else "owned_window_ttl_failure_or_trace_gap"
        ),
        "next_action": "use_owned_window_monitor_as_non_causal_capsule_validation_signal",
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Plan Capsule Owned-Window Analysis",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Capsule: `{payload['capsule_id']}`",
        f"TTL white moves: `{payload['ttl_white_moves']}`",
        f"Windows: `{payload['window_count']}`",
        f"TTL failures: `{payload['ttl_failure_count']}`",
        "",
        "## Windows",
        "",
    ]
    for item in payload.get("windows") or []:
        lines.append(f"- sample `{item.get('sample')}` result `{item.get('result')}`")
        lines.append(f"  moves: `{', '.join(item.get('moves') or [])}`")
        lines.append(f"  progress: `{', '.join(item.get('progress_terms') or [])}`")
        lines.append(f"  ttl_failure: `{item.get('ttl_failure')}`")
    lines.extend(["", f"Next action: `{payload.get('next_action')}`"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diagnostic", type=Path)
    parser.add_argument("--capsule-id", default="krk.post_box_shrink_continuation")
    parser.add_argument("--ttl-white-moves", type=int, default=3)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()
    payload = analyze_owned_window(
        _load_json(args.diagnostic),
        capsule_id=args.capsule_id,
        ttl_white_moves=args.ttl_white_moves,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
