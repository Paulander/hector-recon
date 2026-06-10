#!/usr/bin/env python3
"""Probe Stage 7 king-support-before-edge-trap handoff candidates.

This is an offline growth-lab diagnostic. It does not alter topology or runtime
defaults. It asks whether a visible king-support move from a Stage 7 failure
state unlocks conversion under the existing handoff-composition profile.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.test_krk_landmark_progress import (  # noqa: E402
    build_graph_from_topology,
    play_to_mate,
    _post_break_followup_move_audit,
)
from recon_lite.engine import ReConEngine  # noqa: E402
from recon_lite_chess.krk_baseline_nodes import _compute_krk_context_terms  # noqa: E402


DEFAULT_HORIZONS = (20, 40, 60)


def _move_support_ready_after(board: chess.Board, move: chess.Move) -> dict[str, Any]:
    post = board.copy(stack=False)
    post.push(move)
    terms = _compute_krk_context_terms(post) if post.turn == chess.BLACK else _compute_krk_context_terms(post)
    return {
        "post_fen": post.fen(),
        "white_king_support_available_after_move": bool(
            terms.get("white_king_support_available", False)
        ),
        "edge_trap_shape_available_after_move": bool(
            terms.get("edge_trap_shape_available", False)
        ),
        "edge_rook_transfer_recovery_available_after_move": bool(
            terms.get("edge_rook_transfer_recovery_available", False)
        ),
        "rook_safe_after_move_context": bool(terms.get("rook_safe", False)),
        "visible_terms_after_move": {
            key: bool(terms.get(key, False))
            for key in (
                "white_king_support_available",
                "white_king_can_improve_support",
                "king_support_improvement_move_exists",
                "edge_trap_shape_available",
                "edge_rook_transfer_recovery_available",
                "rook_safe",
                "fence_exists",
                "fence_stable",
            )
        },
    }


def _probe_move(
    *,
    graph,
    engine,
    start_board: chess.Board,
    move: chess.Move,
    horizons: tuple[int, ...],
    seed: int,
    max_ticks: int,
) -> dict[str, Any]:
    audit = _post_break_followup_move_audit(start_board, move)
    support_after = _move_support_ready_after(start_board, move)
    record: dict[str, Any] = {
        "move": move.uci(),
        "legal": True,
        "candidate_is_king_move": (
            start_board.piece_at(move.from_square) == chess.Piece(chess.KING, chess.WHITE)
        ),
        "move_audit": audit,
        **support_after,
        "outcomes_by_horizon": {},
    }
    for horizon in horizons:
        post = start_board.copy(stack=False)
        post.push(move)
        result = play_to_mate(
            graph,
            engine,
            post,
            random.Random(seed * 1_000_000 + horizon),
            label="box_shrink",
            stage_filter=None,
            max_plies=horizon,
            black_policy="adversarial",
            trace=False,
            max_ticks=max_ticks,
            suggestion_limit=5,
            successor_affordance_layer_enabled=True,
            successor_role_license_enabled=True,
            successor_role_scoped_move_shape_enabled=True,
            successor_role_scoped_move_shape_bonus=0.05,
            stagnation_breaker_enabled=True,
            stagnation_breaker_bonus=0.5,
            post_break_continuation_enabled=True,
            post_break_continuation_bonus=0.25,
            successor_stage0_drift_penalty=6.0,
            early_stop_stable_suggestions=2,
            enable_diagnostic_caches=True,
        )
        first_successor = result.get("first_successor") if isinstance(result, dict) else {}
        engine_details = (
            first_successor.get("engine")
            if isinstance(first_successor, dict) and isinstance(first_successor.get("engine"), dict)
            else {}
        )
        suggestions = engine_details.get("suggestions") if isinstance(engine_details, dict) else []
        first_suggestion = suggestions[0] if isinstance(suggestions, list) and suggestions else {}
        record["outcomes_by_horizon"][str(horizon)] = {
            "result": result.get("result"),
            "plies": result.get("plies"),
            "first_reply": (
                result.get("first_reply", {}).get("move")
                if isinstance(result.get("first_reply"), dict)
                else None
            ),
            "first_successor_move": (
                first_successor.get("move")
                if isinstance(first_successor, dict)
                else None
            ),
            "first_successor_skill": first_suggestion.get("curriculum_label"),
        }
    converts = any(
        outcome.get("result") == "mate"
        for outcome in record["outcomes_by_horizon"].values()
    )
    record["converts_to_mate"] = bool(converts)
    record["classification"] = (
        "converts_to_mate"
        if converts
        else "king_support_move_does_not_convert_under_current_graph"
        if record["candidate_is_king_move"]
        else "non_king_move_reference"
    )
    return record


def probe_king_support_handoff(
    *,
    topology: Path,
    fen: str,
    horizons: tuple[int, ...],
    seed: int,
    max_ticks: int,
) -> dict[str, Any]:
    graph = build_graph_from_topology(topology)
    engine = ReConEngine(graph)
    board = chess.Board(fen)
    if board.turn != chess.WHITE:
        raise ValueError("probe FEN must have White to move")
    current_terms = _compute_krk_context_terms(board)
    legal_king_moves = [
        move for move in board.legal_moves
        if board.piece_at(move.from_square) == chess.Piece(chess.KING, chess.WHITE)
    ]
    records = [
        _probe_move(
            graph=graph,
            engine=engine,
            start_board=board,
            move=move,
            horizons=horizons,
            seed=seed + idx,
            max_ticks=max_ticks,
        )
        for idx, move in enumerate(sorted(legal_king_moves, key=lambda item: item.uci()))
    ]
    converting = [record for record in records if record.get("converts_to_mate")]
    support_ready = [
        record for record in records
        if record.get("white_king_support_available_after_move")
    ]
    candidate_status = (
        "sandbox_ready"
        if converting
        else "needs_more_terms_or_capacity"
        if support_ready
        else "rejected_no_king_support_unlock"
    )
    return {
        "schema_version": "stage7_king_support_handoff_probe.v1",
        "causal_status": "non_causal",
        "candidate_id": "cand.krk.box_shrink.king_support_handoff.v1",
        "source_failure_fen": fen,
        "topology": str(topology),
        "horizons": list(horizons),
        "current_visible_terms": {
            key: bool(current_terms.get(key, False))
            for key in (
                "white_king_support_available",
                "white_king_can_improve_support",
                "king_support_improvement_move_exists",
                "edge_trap_shape_available",
                "edge_rook_transfer_recovery_available",
                "rook_safe",
                "fence_exists",
                "fence_stable",
            )
        },
        "king_move_count": len(records),
        "king_support_ready_after_move_count": len(support_ready),
        "converting_king_move_count": len(converting),
        "converting_king_moves": [record["move"] for record in converting],
        "candidate_status": candidate_status,
        "diagnosis": (
            "king_support_handoff_can_be_sandboxed"
            if converting
            else "king_support_moves_reach_support_terms_but_do_not_convert"
            if support_ready
            else "no_king_move_reaches_support_ready_terms"
        ),
        "records": records,
        "structural_candidate": {
            "schema_version": "structural_candidate.v1",
            "candidate_id": "cand.krk.box_shrink.king_support_handoff.v1",
            "candidate_type": "handoff_role_refinement",
            "source_monitor_script": "growth.monitor.successor_miscalibration",
            "source_terms": [
                "white_king_can_improve_support",
                "white_king_support_available=false",
                "edge_trap_support_blocked",
                "repeated_conversion_failure",
            ],
            "trigger_failure_classes": [
                "selected_successor_miscalibrated",
                "repeated_conversion_failure",
            ],
            "target_skill": "krk.box_shrink",
            "parent_skill": "krk.drive_to_edge",
            "proposed_change": {
                "kind": "king_support_handoff_audit",
                "suggested_terms": [
                    "white_king_support_available_after_move",
                    "white_king_support_improves_after_move",
                    "king_support_improvement_preserves_box",
                    "edge_trap_support_ready_after_king_move",
                ],
            },
            "promotion_status": candidate_status,
            "causal_status": "non_causal",
            "credit": 0.0,
        },
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stage 7 King-Support Handoff Probe",
        "",
        f"- Candidate: `{payload['candidate_id']}`",
        f"- Status: `{payload['candidate_status']}`",
        f"- Diagnosis: `{payload['diagnosis']}`",
        f"- King moves: {payload['king_move_count']}",
        f"- Support-ready king moves: {payload['king_support_ready_after_move_count']}",
        f"- Converting king moves: {payload['converting_king_move_count']}",
        f"- Converting moves: {payload['converting_king_moves']}",
        "",
        "## Move Outcomes",
        "",
    ]
    for record in payload.get("records", []):
        lines.append(
            f"- `{record['move']}` support_after={record.get('white_king_support_available_after_move')} "
            f"class={record.get('classification')} outcomes={record.get('outcomes_by_horizon')}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--fen", required=True)
    parser.add_argument("--horizons", default="20,40,60")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-ticks", type=int, default=40)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()

    horizons = tuple(
        int(item.strip()) for item in args.horizons.split(",") if item.strip()
    ) or DEFAULT_HORIZONS
    payload = probe_king_support_handoff(
        topology=args.topology,
        fen=args.fen,
        horizons=horizons,
        seed=args.seed,
        max_ticks=args.max_ticks,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        _write_markdown(payload, args.markdown_output)
    print(json.dumps({
        "candidate_status": payload["candidate_status"],
        "diagnosis": payload["diagnosis"],
        "king_move_count": payload["king_move_count"],
        "support_ready": payload["king_support_ready_after_move_count"],
        "converting": payload["converting_king_move_count"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
