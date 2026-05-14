#!/usr/bin/env python3
"""Audit KRK continuation after a visible stagnation-breaker license fires.

This is a non-causal diagnostic. It reads a saved target-failure trace, finds
the first White decision with ``visible_stagnation_breaker_license``, enumerates
all legal moves satisfying the same visible loop-breaker terms, then manually
applies each candidate and releases control back to the normal ReCoN topology
for several playout horizons.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import chess

from recon_lite.engine import ReConEngine

from test_krk_landmark_progress import (
    _compact_playout_trace,
    _krk_box_area_and_edge,
    _loop_breaking_move_audit,
    _mate_in_one_available,
    _playout_stagnation_summary,
    build_graph_from_topology,
    play_to_mate,
)


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def _load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [
            payload
            for line in text.splitlines()
            if line.strip()
            for payload in [json.loads(line)]
            if isinstance(payload, dict)
        ]
    payload = json.loads(text)
    if isinstance(payload, dict) and isinstance(payload.get("target_failure_traces"), list):
        return [item for item in payload["target_failure_traces"] if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _find_first_stagnation_breaker_event(records: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    for record in records:
        trace = list(record.get("trace") or record.get("trace_summary") or [])
        for idx, event in enumerate(trace):
            if not isinstance(event, dict):
                continue
            if event.get("visible_stagnation_breaker_license"):
                return record, event, trace[: idx + 1]
    raise ValueError("No visible_stagnation_breaker_license event found in trace input")


def _classify_candidate_outcome(
    *,
    outcome: str,
    pre_break_summary: dict[str, Any],
    post_break_summary: dict[str, Any],
) -> str:
    if outcome == "mate":
        return "converts_to_mate"
    if outcome in {"draw", "stalemate"}:
        return "draw_or_stalemate"
    if outcome in {"rook_loss", "illegal_move", "no_move", "no_black_reply"}:
        return "rook_loss_or_safety_failure"
    if bool(post_break_summary.get("stagnation_loop")):
        before_pairs = {
            str(item.get("moves"))
            for item in pre_break_summary.get("rook_oscillation_pairs", []) or []
            if isinstance(item, dict)
        }
        after_pairs = {
            str(item.get("moves"))
            for item in post_break_summary.get("rook_oscillation_pairs", []) or []
            if isinstance(item, dict)
        }
        if before_pairs and after_pairs and not after_pairs.issubset(before_pairs):
            return "changes_loop_family"
        return "breaks_loop_but_reenters_stagnation"
    if int(post_break_summary.get("no_progress_plies", 0) or 0) >= 8:
        return "preserves_safety_but_no_progress"
    return "preserves_safety_but_no_progress"


def _mate_in_one_after_plies(trace: list[dict[str, Any]]) -> int | None:
    for event in trace:
        fen = event.get("fen") if isinstance(event, dict) else None
        if not isinstance(fen, str):
            continue
        try:
            board = chess.Board(fen)
        except Exception:
            continue
        if board.turn == chess.WHITE and _mate_in_one_available(board):
            ply = event.get("ply")
            return int(ply) if isinstance(ply, int) else None
    return None


def _selected_successors(trace: list[dict[str, Any]], *, limit: int = 8) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in trace:
        if not isinstance(event, dict) or event.get("turn") != "white":
            continue
        engine = event.get("engine") if isinstance(event.get("engine"), dict) else {}
        selected_skill = event.get("selected_skill")
        if not selected_skill and isinstance(engine, dict):
            suggestions = list(engine.get("suggestions") or [])
            selected_move = engine.get("move")
            selected = next(
                (item for item in suggestions if item.get("move") == selected_move),
                suggestions[0] if suggestions else {},
            )
            meta = selected.get("meta") if isinstance(selected.get("meta"), dict) else {}
            label = meta.get("curriculum_label") or selected.get("curriculum_label")
            selected_skill = f"krk.{str(label).lower()}" if label else None
        rows.append({
            "ply": event.get("ply"),
            "move": event.get("move"),
            "selected_skill": selected_skill,
        })
        if len(rows) >= limit:
            break
    return rows


def _post_break_progress(
    *,
    first_board: chess.Board,
    after_move_board: chess.Board,
    continuation: dict[str, Any],
    pre_break_summary: dict[str, Any],
) -> dict[str, Any]:
    before_box, before_edge = _krk_box_area_and_edge(first_board)
    after_box, after_edge = _krk_box_area_and_edge(after_move_board)
    post_summary = dict(continuation.get("stagnation_summary") or {})
    trace = list(continuation.get("trace") or [])
    final_box = None
    final_edge = None
    final_fen = continuation.get("final_fen")
    if isinstance(final_fen, str):
        try:
            final_box, final_edge = _krk_box_area_and_edge(chess.Board(final_fen))
        except Exception:
            final_box, final_edge = None, None
    return {
        "box_area_delta": (
            after_box - before_box
            if before_box is not None and after_box is not None
            else None
        ),
        "enemy_king_edge_distance_delta": (
            after_edge - before_edge
            if before_edge is not None and after_edge is not None
            else None
        ),
        "final_box_area_delta_from_break": (
            final_box - after_box
            if final_box is not None and after_box is not None
            else None
        ),
        "final_enemy_edge_distance_delta_from_break": (
            final_edge - after_edge
            if final_edge is not None and after_edge is not None
            else None
        ),
        "mate_in_one_appears_after_n_plies": _mate_in_one_after_plies(trace),
        "repeated_abstract_state_count_after_break": int(
            post_summary.get("repeated_abstract_state_count", 0) or 0
        ),
        "rook_oscillation_count_after_break": int(
            post_summary.get("rook_reversal_count", 0) or 0
        ),
        "selected_successors_after_break": _selected_successors(trace),
        "pre_break_repeated_abstract_state_count": int(
            pre_break_summary.get("repeated_abstract_state_count", 0) or 0
        ),
        "pre_break_rook_oscillation_count": int(
            pre_break_summary.get("rook_reversal_count", 0) or 0
        ),
    }


def _candidate_loop_breaking_audits(
    *,
    event: dict[str, Any],
    trace_prefix: list[dict[str, Any]],
) -> tuple[chess.Board, dict[str, Any], list[dict[str, Any]]]:
    fen = event.get("fen")
    if not isinstance(fen, str):
        raise ValueError("Stagnation-breaker event has no FEN")
    board = chess.Board(fen)
    pre_break_summary = _playout_stagnation_summary(trace_prefix, current_board=board)
    context_moves = set(
        str(item)
        for item in (event.get("stagnation_context") or {}).get("legal_loop_breaking_moves", [])
    )
    audits = list(pre_break_summary.get("legal_loop_breaking_move_audits") or [])
    if context_moves:
        audits_by_move = {str(item.get("move")): item for item in audits}
        missing = sorted(context_moves.difference(audits_by_move))
        for move_uci in missing:
            try:
                move = chess.Move.from_uci(move_uci)
            except ValueError:
                continue
            audits.append(
                _loop_breaking_move_audit(
                    board,
                    move,
                    oscillation_squares=set(),
                    last_rook_move=None,
                )
            )
    audits = [item for item in audits if item.get("loop_breaking")]
    audits.sort(key=lambda item: str(item.get("move")))
    return board, pre_break_summary, audits


def _run_candidate(
    graph,
    engine: ReConEngine,
    *,
    board: chess.Board,
    move_uci: str,
    horizon: int,
    rng: random.Random,
    label: str,
    black_policy: str,
    max_ticks: int,
    suggestion_limit: int,
    early_stop_stable_suggestions: int,
    successor_affordance_layer_enabled: bool,
    successor_role_license_enabled: bool,
    successor_role_scoped_move_shape_enabled: bool,
    successor_role_scoped_move_shape_bonus: float,
    stagnation_breaker_enabled: bool,
    stagnation_breaker_bonus: float,
    trace_max_plies: int,
) -> dict[str, Any]:
    move = chess.Move.from_uci(move_uci)
    after = board.copy()
    if move not in after.legal_moves:
        return {"result": "illegal_move", "plies": 0}
    after.push(move)
    if after.is_checkmate():
        return {
            "result": "mate",
            "plies": 1,
            "final_fen": after.fen(),
            "trace": [],
            "stagnation_summary": {},
        }
    continuation = play_to_mate(
        graph,
        engine,
        after,
        random.Random(rng.randrange(2**32)),
        label,
        None,
        max(0, horizon - 1),
        black_policy,
        trace=True,
        max_ticks=max_ticks,
        suggestion_limit=suggestion_limit,
        trace_max_plies=trace_max_plies,
        successor_affordance_layer_enabled=successor_affordance_layer_enabled,
        successor_contract_gate_enabled=False,
        successor_role_license_enabled=successor_role_license_enabled,
        successor_role_scoped_move_shape_enabled=successor_role_scoped_move_shape_enabled,
        successor_role_scoped_move_shape_bonus=successor_role_scoped_move_shape_bonus,
        stagnation_breaker_enabled=stagnation_breaker_enabled,
        stagnation_breaker_bonus=stagnation_breaker_bonus,
        early_stop_stable_suggestions=early_stop_stable_suggestions,
    )
    continuation["plies"] = int(continuation.get("plies", 0) or 0) + 1
    return continuation


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit post-stagnation-break KRK continuation")
    parser.add_argument("--trace", type=Path, required=True,
                        help="Target failure trace JSON/JSONL containing visible_stagnation_breaker_license")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--label", default="fence_established")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--horizons", default="21,30,40",
                        help="Comma-separated playout horizons after the loop-break candidate")
    parser.add_argument("--include-horizon-60", action="store_true")
    parser.add_argument("--black-policy", choices=["random", "adversarial"], default="adversarial")
    parser.add_argument("--max-ticks", type=int, default=40)
    parser.add_argument("--suggestion-limit", type=int, default=5)
    parser.add_argument("--early-stop-stable-suggestions", type=int, default=2)
    parser.add_argument("--trace-max-plies", type=int, default=80)
    parser.add_argument("--max-candidates", type=int, default=0,
                        help="If >0, audit only the first N visible loop-breaking moves")
    parser.add_argument("--enable-successor-affordance-layer", action="store_true")
    parser.add_argument("--enable-successor-role-licenses", action="store_true")
    parser.add_argument("--enable-role-scoped-move-shapes", action="store_true")
    parser.add_argument("--role-scoped-move-shape-bonus", type=float, default=0.0)
    parser.add_argument("--enable-stagnation-breaker", action="store_true")
    parser.add_argument("--stagnation-breaker-bonus", type=float, default=0.0)
    parser.add_argument("--steps-output", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args()

    horizons = [int(item) for item in args.horizons.split(",") if item.strip()]
    if args.include_horizon_60 and 60 not in horizons:
        horizons.append(60)
    horizons = sorted(set(horizons))

    records = _load_records(args.trace)
    source_record, event, trace_prefix = _find_first_stagnation_breaker_event(records)
    board, pre_break_summary, candidate_audits = _candidate_loop_breaking_audits(
        event=event,
        trace_prefix=trace_prefix,
    )
    selected_break_move = str(event.get("move") or "")
    if selected_break_move:
        candidate_audits.sort(
            key=lambda item: (
                str(item.get("move")) != selected_break_move,
                str(item.get("move")),
            )
        )
    if args.max_candidates > 0:
        candidate_audits = candidate_audits[: args.max_candidates]
    graph = build_graph_from_topology(args.topology)
    engine = ReConEngine(graph)
    rng = random.Random(args.seed)

    candidates: list[dict[str, Any]] = []
    loop_breaking_moves_that_convert: list[str] = []
    for candidate_index, audit in enumerate(candidate_audits, start=1):
        move_uci = str(audit.get("move"))
        print(
            f"{candidate_index:3d}/{len(candidate_audits)} move={move_uci}",
            flush=True,
        )
        outcomes_by_horizon: dict[str, str] = {}
        details_by_horizon: dict[str, Any] = {}
        after = board.copy()
        after.push(chess.Move.from_uci(move_uci))
        for horizon in horizons:
            print(f"      horizon={horizon}", flush=True)
            continuation = _run_candidate(
                graph,
                engine,
                board=board,
                move_uci=move_uci,
                horizon=horizon,
                rng=rng,
                label=args.label,
                black_policy=args.black_policy,
                max_ticks=args.max_ticks,
                suggestion_limit=args.suggestion_limit,
                early_stop_stable_suggestions=args.early_stop_stable_suggestions,
                successor_affordance_layer_enabled=args.enable_successor_affordance_layer,
                successor_role_license_enabled=args.enable_successor_role_licenses,
                successor_role_scoped_move_shape_enabled=args.enable_role_scoped_move_shapes,
                successor_role_scoped_move_shape_bonus=args.role_scoped_move_shape_bonus,
                stagnation_breaker_enabled=args.enable_stagnation_breaker,
                stagnation_breaker_bonus=args.stagnation_breaker_bonus,
                trace_max_plies=args.trace_max_plies,
            )
            outcome = str(continuation.get("result") or "unknown")
            outcomes_by_horizon[str(horizon)] = outcome
            progress = _post_break_progress(
                first_board=board,
                after_move_board=after,
                continuation=continuation,
                pre_break_summary=pre_break_summary,
            )
            post_summary = dict(continuation.get("stagnation_summary") or {})
            classification = _classify_candidate_outcome(
                outcome=outcome,
                pre_break_summary=pre_break_summary,
                post_break_summary=post_summary,
            )
            details = {
                "result": outcome,
                "plies": int(continuation.get("plies", 0) or 0),
                "classification": classification,
                "post_break_progress": progress,
                "final_fen": continuation.get("final_fen"),
                "trace": _compact_playout_trace(list(continuation.get("trace") or [])),
                "trace_truncated_events": continuation.get("trace_truncated_events", 0),
            }
            details_by_horizon[str(horizon)] = details
            if args.steps_output is not None:
                _append_jsonl(
                    args.steps_output,
                    {
                        "source_trace": str(args.trace),
                        "first_stagnation_breaker_fen": board.fen(),
                        "move": move_uci,
                        "horizon": horizon,
                        **details,
                    },
                )
        if any(outcome == "mate" for outcome in outcomes_by_horizon.values()):
            loop_breaking_moves_that_convert.append(move_uci)
        candidates.append({
            "move": move_uci,
            "source_terms": list(audit.get("source_terms") or []),
            "outcomes_by_horizon": outcomes_by_horizon,
            "details_by_horizon": details_by_horizon,
        })

    output = {
        "schema_version": "krk_post_break_continuation_audit.v1",
        "source_trace": str(args.trace),
        "topology": str(args.topology),
        "source_state_signature": source_record.get("state_signature"),
        "first_stagnation_breaker_state": board.fen(),
        "first_stagnation_breaker_event": event,
        "visible_terms": {
            "rook_oscillation_loop": bool(pre_break_summary.get("rook_oscillation_loop")),
            "no_box_progress_recently": bool(pre_break_summary.get("no_box_progress_recently")),
            "no_edge_progress_recently": bool(pre_break_summary.get("no_edge_progress_recently")),
            "no_mate_progress_recently": bool(pre_break_summary.get("no_mate_progress_recently")),
            "safe_loop_breaking_move_available": bool(
                pre_break_summary.get("safe_loop_breaking_move_available")
            ),
        },
        "pre_break_stagnation_summary": pre_break_summary,
        "horizons": horizons,
        "licensed_loop_breaking_moves": candidates,
        "loop_breaking_moves_that_convert": sorted(loop_breaking_moves_that_convert),
        "outcome_counts_by_horizon": {
            str(horizon): {
                outcome: sum(
                    1
                    for candidate in candidates
                    if candidate["outcomes_by_horizon"].get(str(horizon)) == outcome
                )
                for outcome in sorted({
                    candidate["outcomes_by_horizon"].get(str(horizon))
                    for candidate in candidates
                })
            }
            for horizon in horizons
        },
    }
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "first_stagnation_breaker_state": output["first_stagnation_breaker_state"],
        "candidate_count": len(candidates),
        "loop_breaking_moves_that_convert": output["loop_breaking_moves_that_convert"],
        "outcome_counts_by_horizon": output["outcome_counts_by_horizon"],
    }, indent=2))


if __name__ == "__main__":
    main()
