#!/usr/bin/env python3
"""Audit legal moves against a non-causal MoveShapeRoleSpec."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import chess

from recon_lite_chess.krk_baseline_nodes import krk_move_shape_audit
from recon_lite_chess.routing import MoveShapeRoleSpec, stable_record_id


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _load_role(path: Path) -> MoveShapeRoleSpec:
    payload = _load_json(path)
    role_payload = payload.get("move_shape_role", payload)
    if not isinstance(role_payload, dict):
        raise ValueError(f"expected move_shape_role object in {path}")
    return MoveShapeRoleSpec.from_dict(role_payload)


def _audit_terms(audit: dict[str, Any], key: str) -> set[str]:
    values = audit.get(key)
    if not isinstance(values, list):
        return set()
    return {str(item) for item in values}


def audit_role_for_fen(
    role: MoveShapeRoleSpec,
    *,
    fen: str,
    include_worst_reply: bool = False,
) -> dict[str, Any]:
    board = chess.Board(fen)
    matches: list[dict[str, Any]] = []
    all_moves: list[dict[str, Any]] = []
    required_move = set(role.move_shape_required_terms)
    required_post = set(role.post_move_required_terms)
    veto_terms = set(role.veto_terms)

    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        audit = krk_move_shape_audit(board, move, include_worst_reply=include_worst_reply)
        move_terms = _audit_terms(audit, "move_shape_terms")
        post_terms = _audit_terms(audit, "post_move_terms")
        all_terms = move_terms | post_terms | _audit_terms(audit, "worst_reply_terms")
        missing_move = sorted(required_move - move_terms)
        missing_post = sorted(required_post - post_terms)
        veto_met = sorted(veto_terms & all_terms)
        matched = not missing_move and not missing_post and not veto_met
        row = {
            "move": move.uci(),
            "matched": matched,
            "missing_move_shape_terms": missing_move,
            "missing_post_move_terms": missing_post,
            "veto_terms_met": veto_met,
            "move_shape_terms": sorted(move_terms),
            "post_move_terms": sorted(post_terms),
        }
        all_moves.append(row)
        if matched:
            matches.append(row)

    return {
        "fen": fen,
        "state_signature": stable_record_id("state", board.board_fen(), board.turn),
        "legal_move_count": len(all_moves),
        "matching_move_count": len(matches),
        "matching_moves": matches,
        "all_moves": all_moves,
    }


def build_audit(
    role: MoveShapeRoleSpec,
    *,
    fens: list[str],
    include_worst_reply: bool = False,
) -> dict[str, Any]:
    records = [
        audit_role_for_fen(role, fen=fen, include_worst_reply=include_worst_reply)
        for fen in fens
    ]
    return {
        "schema_version": "move_shape_role_candidate_audit.v1",
        "causal_status": "non_causal",
        "role_id": role.role_id,
        "source_candidate_id": role.source_candidate_id,
        "include_worst_reply": include_worst_reply,
        "record_count": len(records),
        "records": records,
        "summary": {
            "states_with_matches": sum(1 for item in records if item["matching_move_count"] > 0),
            "total_matching_moves": sum(int(item["matching_move_count"]) for item in records),
        },
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Move-Shape Role Candidate Audit",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Role: `{payload['role_id']}`",
        f"Source candidate: `{payload['source_candidate_id']}`",
        f"Records: `{payload['record_count']}`",
        f"States with matches: `{payload['summary']['states_with_matches']}`",
        f"Total matching moves: `{payload['summary']['total_matching_moves']}`",
        "",
        "## Records",
        "",
    ]
    for record in payload.get("records") or []:
        lines.append(f"### {record['state_signature']}")
        lines.append("")
        lines.append(f"- FEN: `{record['fen']}`")
        lines.append(f"- Legal moves: `{record['legal_move_count']}`")
        lines.append(f"- Matching moves: `{record['matching_move_count']}`")
        for move in record.get("matching_moves") or []:
            lines.append(f"- Match: `{move['move']}`")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role_spec", type=Path)
    parser.add_argument("--fen", action="append", default=[], help="FEN to audit; may repeat")
    parser.add_argument("--fens-file", type=Path, default=None, help="JSON list/object containing FENs")
    parser.add_argument("--include-worst-reply", action="store_true")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    fens = list(args.fen or [])
    if args.fens_file:
        payload = json.loads(args.fens_file.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            fens.extend(str(item) for item in payload)
        elif isinstance(payload, dict):
            for item in payload.get("fens", []) or payload.get("records", []) or []:
                if isinstance(item, dict) and item.get("fen"):
                    fens.append(str(item["fen"]))
                elif isinstance(item, str):
                    fens.append(item)
        else:
            raise ValueError("fens-file must contain a JSON list or object")
    if not fens:
        raise ValueError("at least one --fen or --fens-file entry is required")

    payload = build_audit(
        _load_role(args.role_spec),
        fens=fens,
        include_worst_reply=bool(args.include_worst_reply),
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
