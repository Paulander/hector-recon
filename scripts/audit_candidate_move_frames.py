#!/usr/bin/env python3
"""Emit non-causal CandidateMoveFrame records for selected KRK states."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import chess

from recon_lite_chess.krk_baseline_nodes import krk_move_shape_audit
from recon_lite_chess.routing import CandidateMoveFrame


def _frame_for_move(
    board: chess.Board,
    move: chess.Move,
    *,
    include_worst_reply: bool = False,
) -> CandidateMoveFrame:
    audit = krk_move_shape_audit(
        board,
        move,
        {},
        include_worst_reply=include_worst_reply,
    )
    post = board.copy(stack=False)
    post.push(move)
    post_terms = set(audit.get("post_move_terms", []) or [])
    worst_terms = set(audit.get("worst_reply_terms", []) or [])
    safety_terms: list[str] = []
    veto_terms: list[str] = []
    if "rook_safe_after_move" in post_terms:
        safety_terms.append("rook_safe_after_move")
    if "no_draw_after_worst_reply" in worst_terms:
        safety_terms.append("no_draw_after_worst_reply")
    if post.is_stalemate() or post.is_insufficient_material() or post.can_claim_draw():
        veto_terms.append("draw_or_stalemate_risk")
    return CandidateMoveFrame(
        move_uci=move.uci(),
        legal=move in board.legal_moves,
        current_terms=list(audit.get("current_terms", []) or []),
        move_shape_terms=list(audit.get("move_shape_terms", []) or []),
        post_move_terms=list(audit.get("post_move_terms", []) or []),
        worst_reply_terms=list(audit.get("worst_reply_terms", []) or []),
        safety_terms=safety_terms,
        veto_terms=veto_terms,
        source_terms=list(audit.get("current_terms", []) or []),
        source_terminal="terminal.krk.candidate_move_enumerator",
        board_key=f"{board.board_fen()}:{'w' if board.turn == chess.WHITE else 'b'}",
        fen=board.fen(),
        causal_status="non_causal",
    )


def audit_fens(
    fens: list[str],
    *,
    include_worst_reply: bool = False,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    move_shape_counts: Counter[str] = Counter()
    post_move_counts: Counter[str] = Counter()
    current_counts: Counter[str] = Counter()
    for index, fen in enumerate(fens):
        board = chess.Board(fen)
        frames = [
            _frame_for_move(board, move, include_worst_reply=include_worst_reply)
            for move in sorted(board.legal_moves, key=lambda item: item.uci())
        ]
        for frame in frames:
            current_counts.update(frame.current_terms)
            move_shape_counts.update(frame.move_shape_terms)
            post_move_counts.update(frame.post_move_terms)
        records.append(
            {
                "state_index": index,
                "fen": fen,
                "board_key": f"{board.board_fen()}:{'w' if board.turn == chess.WHITE else 'b'}",
                "legal_move_count": len(frames),
                "candidate_move_frames": [frame.to_dict() for frame in frames],
            }
        )
    return {
        "schema_version": "candidate_move_frame_audit.v1",
        "causal_status": "non_causal",
        "source_terminal": "terminal.krk.candidate_move_enumerator",
        "direct_request": False,
        "include_worst_reply": bool(include_worst_reply),
        "state_count": len(records),
        "records": records,
        "term_counts": {
            "current_terms": dict(sorted(current_counts.items())),
            "move_shape_terms": dict(sorted(move_shape_counts.items())),
            "post_move_terms": dict(sorted(post_move_counts.items())),
        },
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# CandidateMoveFrame Audit",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"States: `{payload['state_count']}`",
        "",
        "## States",
        "",
    ]
    for record in payload["records"]:
        lines.append(f"- `{record['fen']}`: {record['legal_move_count']} legal frames")
    lines.extend(["", "## Most Common Move-Shape Terms", ""])
    counts = payload.get("term_counts", {}).get("move_shape_terms", {})
    for term, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:20]:
        lines.append(f"- `{term}`: {count}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fen", action="append", default=[], help="FEN to audit; may repeat")
    parser.add_argument("--fens-file", type=Path, default=None)
    parser.add_argument("--include-worst-reply", action="store_true")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    fens = [str(item) for item in args.fen]
    if args.fens_file is not None:
        fens.extend(
            line.strip()
            for line in args.fens_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    if not fens:
        raise ValueError("at least one --fen or --fens-file entry is required")

    payload = audit_fens(fens, include_worst_reply=args.include_worst_reply)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
