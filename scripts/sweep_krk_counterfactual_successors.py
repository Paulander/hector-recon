#!/usr/bin/env python3
"""Replay failed KRK handoff states with forced successor skills.

This is an offline audit tool. It reads diagnostic JSON emitted by
``test_krk_landmark_progress.py`` and replays only failed post-reply states,
forcing one candidate successor skill for the first White continuation move.
It does not change topology or runtime routing.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import chess

from recon_lite.engine import ReConEngine
from recon_lite_chess.krk_baseline_nodes import krk_move_shape_audit

from test_krk_landmark_progress import (
    build_graph_from_topology,
    choose_move_details,
    play_to_mate,
    run_counterfactual_successor_sweep,
    stable_record_id,
    summarize_counterfactual_successor_sweeps,
)


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def _route_scores(evidence: dict[str, Any]) -> dict[str, float]:
    skills = evidence.get("successor_skills")
    if not isinstance(skills, dict):
        return {}
    scores: dict[str, float] = {}
    for skill_id, payload in skills.items():
        if isinstance(payload, dict):
            scores[str(skill_id)] = float(payload.get("score", 0.0) or 0.0)
    return scores


def canonical_skill_id(label: str) -> str:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in label.lower()).strip("_")
    return f"krk.{normalized or 'unknown'}"


def _skill_id_for_suggestion(item: dict[str, Any]) -> str:
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    label = meta.get("curriculum_label") or item.get("curriculum_label")
    if label:
        raw = str(label)
        return raw if raw.startswith("krk.") else canonical_skill_id(raw)
    stage = item.get("stage") or meta.get("stage")
    return f"krk.stage_{stage}" if stage is not None else "krk.unknown"


def failed_post_reply_states(
    diagnostic: dict[str, Any],
    *,
    dedupe_state_signatures: bool = True,
) -> list[dict[str, Any]]:
    """Extract failed post-opponent-reply states from a diagnostic payload."""
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for packet in diagnostic.get("handoff_packets") or []:
        if not isinstance(packet, dict):
            continue
        if packet.get("phase") != "post_opponent_reply":
            continue
        evidence = packet.get("evidence_terms")
        if not isinstance(evidence, dict):
            continue
        result = str(evidence.get("playout_result") or packet.get("observed_outcome") or "unknown")
        if result == "mate":
            continue
        post_reply_fen = evidence.get("post_reply_fen")
        if not post_reply_fen:
            continue
        try:
            state_signature = stable_record_id("state", chess.Board(post_reply_fen).board_fen(), chess.WHITE)
        except Exception:
            state_signature = "state.invalid"
        if dedupe_state_signatures and state_signature in seen:
            continue
        seen.add(state_signature)
        records.append({
            "packet_id": packet.get("packet_id"),
            "state_signature": state_signature,
            "start_fen": evidence.get("fen"),
            "post_reply_fen": post_reply_fen,
            "actual_selected_successor": evidence.get("successor_selected_skill"),
            "actual_result": result,
            "actual_route_scores": _route_scores(evidence),
            "failure_classes": list(evidence.get("failure_classes") or []),
        })
    return records


def run_legal_first_move_sweep(
    graph,
    engine: ReConEngine,
    *,
    post_reply_fen: str,
    rng: random.Random,
    label: str,
    max_plies: int,
    black_policy: str,
    max_ticks: int,
    suggestion_limit: int,
    successor_affordance_layer_enabled: bool,
    successor_contract_gate_enabled: bool,
    successor_role_license_enabled: bool,
    successor_role_veto_penalty: float = 0.0,
    successor_stage0_drift_penalty: float = 0.0,
    successor_role_scoped_move_shape_enabled: bool = False,
    successor_role_scoped_move_shape_bonus: float = 0.0,
    successor_role_scoped_move_shape_require_worst_reply: bool = False,
    stagnation_breaker_enabled: bool = False,
    stagnation_breaker_bonus: float = 0.0,
    early_stop_stable_suggestions: int = 0,
    require_any_terms: tuple[str, ...] = (),
    require_all_terms: tuple[str, ...] = (),
    max_moves: int = 0,
    audit_worst_reply: bool = True,
    step_output: Path | None = None,
    step_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Try every legal first White move, then release to normal topology.

    This is diagnostic-only. It answers whether a failed post-reply state has
    any converting first move under the current continuation policy, independent
    of whether an existing successor provider selected that move.
    """
    board = chess.Board(post_reply_fen)
    results: dict[str, Any] = {}
    candidates: list[tuple[chess.Move, dict[str, Any]]] = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        audit = krk_move_shape_audit(board, move, include_worst_reply=audit_worst_reply)
        term_set = _audit_term_set(audit)
        if require_any_terms and not term_set.intersection(require_any_terms):
            continue
        if require_all_terms and not set(require_all_terms).issubset(term_set):
            continue
        candidates.append((move, audit))
    if max_moves > 0:
        candidates = candidates[:max_moves]

    for move, audit in candidates:
        b = board.copy()
        b.push(move)
        if b.is_checkmate():
            result = {"result": "mate", "plies": 1}
        else:
            local_rng = random.Random(rng.randrange(2**32))
            continuation = play_to_mate(
                graph,
                engine,
                b,
                local_rng,
                label,
                None,
                max(0, max_plies - 1),
                black_policy,
                trace=False,
                max_ticks=max_ticks,
                suggestion_limit=suggestion_limit,
                successor_affordance_layer_enabled=successor_affordance_layer_enabled,
                successor_contract_gate_enabled=successor_contract_gate_enabled,
                successor_role_license_enabled=successor_role_license_enabled,
                successor_role_veto_penalty=successor_role_veto_penalty,
                successor_stage0_drift_penalty=successor_stage0_drift_penalty,
                successor_role_scoped_move_shape_enabled=successor_role_scoped_move_shape_enabled,
                successor_role_scoped_move_shape_bonus=successor_role_scoped_move_shape_bonus,
                successor_role_scoped_move_shape_require_worst_reply=(
                    successor_role_scoped_move_shape_require_worst_reply
                ),
                stagnation_breaker_enabled=stagnation_breaker_enabled,
                stagnation_breaker_bonus=stagnation_breaker_bonus,
                early_stop_stable_suggestions=early_stop_stable_suggestions,
            )
            result = {
                "result": continuation.get("result"),
                "plies": int(continuation.get("plies", 0) or 0) + 1,
            }
        result["move_shape_audit"] = audit
        results[move.uci()] = result
        if step_output is not None:
            _append_jsonl(
                step_output,
                {
                    **(step_context or {}),
                    "legal_first_move": move.uci(),
                    "legal_first_move_result": result,
                },
            )
    return results


def _audit_term_set(audit: dict[str, Any]) -> set[str]:
    terms: set[str] = set()
    for key in ("current_terms", "move_shape_terms", "post_move_terms", "worst_reply_terms"):
        values = audit.get(key)
        if isinstance(values, list):
            terms.update(str(item) for item in values)
    return terms


def _parse_terms(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def run_provider_suggestion_audit(
    graph,
    engine: ReConEngine,
    *,
    post_reply_fen: str,
    legal_first_results: dict[str, Any],
    max_ticks: int,
    suggestion_limit: int,
    successor_affordance_layer_enabled: bool,
    successor_contract_gate_enabled: bool,
    successor_role_license_enabled: bool,
    successor_role_veto_penalty: float = 0.0,
    successor_stage0_drift_penalty: float = 0.0,
    successor_role_scoped_move_shape_enabled: bool = False,
    successor_role_scoped_move_shape_bonus: float = 0.0,
    successor_role_scoped_move_shape_require_worst_reply: bool = False,
    stagnation_breaker_enabled: bool = False,
    stagnation_breaker_bonus: float = 0.0,
    early_stop_stable_suggestions: int = 0,
) -> dict[str, Any]:
    """Compare converting legal-first moves against runtime provider suggestions."""
    board = chess.Board(post_reply_fen)
    move_details = choose_move_details(
        graph,
        engine,
        board,
        max_ticks=max_ticks,
        suggestion_limit=suggestion_limit,
        successor_affordance_layer_enabled=successor_affordance_layer_enabled,
        successor_contract_gate_enabled=successor_contract_gate_enabled,
        successor_role_license_enabled=successor_role_license_enabled,
        successor_role_veto_penalty=successor_role_veto_penalty,
        successor_stage0_drift_penalty=successor_stage0_drift_penalty,
        successor_role_scoped_move_shape_enabled=successor_role_scoped_move_shape_enabled,
        successor_role_scoped_move_shape_bonus=successor_role_scoped_move_shape_bonus,
        successor_role_scoped_move_shape_require_worst_reply=(
            successor_role_scoped_move_shape_require_worst_reply
        ),
        stagnation_breaker_enabled=stagnation_breaker_enabled,
        stagnation_breaker_bonus=stagnation_breaker_bonus,
        early_stop_stable_suggestions=early_stop_stable_suggestions,
    )
    suggestions = list(move_details.get("suggestions", []) or [])
    suggested_moves = {str(item.get("move")) for item in suggestions if item.get("move")}
    suggested_by_move: dict[str, list[dict[str, Any]]] = {}
    for item in suggestions:
        move = item.get("move")
        if not move:
            continue
        suggested_by_move.setdefault(str(move), []).append({
            "skill_id": _skill_id_for_suggestion(item),
            "score": float(item.get("score", 0.0) or 0.0),
            "actuator": item.get("actuator"),
            "meta": item.get("meta") if isinstance(item.get("meta"), dict) else {},
        })

    converting_moves = {
        move: result
        for move, result in legal_first_results.items()
        if isinstance(result, dict) and str(result.get("result")) == "mate"
    }
    converting_suggested = sorted(move for move in converting_moves if move in suggested_moves)
    converting_not_proposed = sorted(move for move in converting_moves if move not in suggested_moves)
    selected_move = move_details.get("move")
    selected_converts = bool(selected_move in converting_moves)
    if not converting_moves:
        failure_class = "no_converting_legal_first_in_filter"
    elif selected_converts:
        failure_class = "selected_converting_move"
    elif converting_suggested:
        failure_class = "converting_move_proposed_not_selected"
    else:
        failure_class = "converting_move_not_proposed"

    return {
        "move": selected_move,
        "ticks": move_details.get("ticks"),
        "early_stopped": bool(move_details.get("early_stopped", False)),
        "suggestion_count": len(suggestions),
        "suggested_moves": sorted(suggested_moves),
        "suggested_by_move": suggested_by_move,
        "converting_moves": sorted(converting_moves),
        "converting_suggested": converting_suggested,
        "converting_not_proposed": converting_not_proposed,
        "selected_converts": selected_converts,
        "failure_class": failure_class,
    }


def run_continuation_trace_audit(
    graph,
    engine: ReConEngine,
    *,
    post_reply_fen: str,
    first_move: str,
    rng: random.Random,
    label: str,
    max_plies: int,
    black_policy: str,
    max_ticks: int,
    suggestion_limit: int,
    successor_affordance_layer_enabled: bool,
    successor_contract_gate_enabled: bool,
    successor_role_license_enabled: bool,
    successor_role_veto_penalty: float = 0.0,
    successor_stage0_drift_penalty: float = 0.0,
    successor_role_scoped_move_shape_enabled: bool = False,
    successor_role_scoped_move_shape_bonus: float = 0.0,
    successor_role_scoped_move_shape_require_worst_reply: bool = False,
    stagnation_breaker_enabled: bool = False,
    stagnation_breaker_bonus: float = 0.0,
    early_stop_stable_suggestions: int = 0,
    trace_max_plies: int = 24,
) -> dict[str, Any]:
    """Apply a first move, then trace downstream ReCoN continuation."""
    board = chess.Board(post_reply_fen)
    try:
        move = chess.Move.from_uci(first_move)
    except ValueError:
        return {"first_move": first_move, "result": "invalid_first_move"}
    if move not in board.legal_moves:
        return {"first_move": first_move, "result": "illegal_first_move"}

    first_audit = krk_move_shape_audit(board, move, include_worst_reply=False)
    board.push(move)
    if board.is_checkmate():
        return {
            "first_move": first_move,
            "first_move_audit": first_audit,
            "result": "mate",
            "plies": 1,
            "trace_summary": [],
        }

    continuation = play_to_mate(
        graph,
        engine,
        board,
        rng,
        label,
        None,
        max(0, max_plies - 1),
        black_policy,
        trace=True,
        max_ticks=max_ticks,
        suggestion_limit=suggestion_limit,
        trace_max_plies=trace_max_plies,
        successor_affordance_layer_enabled=successor_affordance_layer_enabled,
        successor_contract_gate_enabled=successor_contract_gate_enabled,
        successor_role_license_enabled=successor_role_license_enabled,
        successor_role_veto_penalty=successor_role_veto_penalty,
        successor_stage0_drift_penalty=successor_stage0_drift_penalty,
        successor_role_scoped_move_shape_enabled=successor_role_scoped_move_shape_enabled,
        successor_role_scoped_move_shape_bonus=successor_role_scoped_move_shape_bonus,
        successor_role_scoped_move_shape_require_worst_reply=(
            successor_role_scoped_move_shape_require_worst_reply
        ),
        stagnation_breaker_enabled=stagnation_breaker_enabled,
        stagnation_breaker_bonus=stagnation_breaker_bonus,
        early_stop_stable_suggestions=early_stop_stable_suggestions,
    )
    trace = list(continuation.get("trace", []) or [])
    return {
        "first_move": first_move,
        "first_move_audit": first_audit,
        "result": continuation.get("result"),
        "plies": int(continuation.get("plies", 0) or 0) + 1,
        "final_fen": continuation.get("final_fen"),
        "engine_decision_count": continuation.get("engine_decision_count"),
        "engine_ticks_total": continuation.get("engine_ticks_total"),
        "stagnation_summary": continuation.get("stagnation_summary"),
        "trace_truncated_events": continuation.get("trace_truncated_events", 0),
        "trace_summary": _summarize_continuation_trace(trace),
    }


def _summarize_continuation_trace(trace: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for event in trace:
        if not isinstance(event, dict):
            continue
        item: dict[str, Any] = {
            "ply": event.get("ply"),
            "turn": event.get("turn"),
            "fen": event.get("fen"),
            "move": event.get("move"),
            "resulting_fen": event.get("resulting_fen"),
            "is_checkmate": bool(event.get("is_checkmate", False)),
            "is_stalemate": bool(event.get("is_stalemate", False)),
        }
        if isinstance(event.get("stagnation_context"), dict):
            ctx = event["stagnation_context"]
            item["stagnation_context"] = {
                "stagnation_loop": bool(ctx.get("stagnation_loop", False)),
                "rook_oscillation_loop": bool(ctx.get("rook_oscillation_loop", False)),
                "repeated_abstract_state_count": int(ctx.get("repeated_abstract_state_count", 0) or 0),
                "no_progress_plies": int(ctx.get("no_progress_plies", 0) or 0),
                "safe_loop_breaking_move_available": bool(ctx.get("safe_loop_breaking_move_available", False)),
                "legal_loop_breaking_moves": list(ctx.get("legal_loop_breaking_moves", []) or []),
            }
        engine_details = event.get("engine") if isinstance(event.get("engine"), dict) else None
        if engine_details:
            suggestions = list(engine_details.get("suggestions", []) or [])
            selected_move = engine_details.get("move")
            selected = next(
                (suggestion for suggestion in suggestions if suggestion.get("move") == selected_move),
                suggestions[0] if suggestions else {},
            )
            item.update({
                "selected_skill": _skill_id_for_suggestion(selected) if selected else None,
                "confidence": engine_details.get("confidence"),
                "ticks": engine_details.get("ticks"),
                "early_stopped": bool(engine_details.get("early_stopped", False)),
                "top_suggestions": [
                    {
                        "move": suggestion.get("move"),
                        "skill_id": _skill_id_for_suggestion(suggestion),
                        "score": suggestion.get("score"),
                    }
                    for suggestion in suggestions[:5]
                ],
            })
            meta = selected.get("meta") if isinstance(selected, dict) and isinstance(selected.get("meta"), dict) else {}
            if meta.get("visible_stagnation_breaker_license"):
                item["visible_stagnation_breaker_license"] = meta.get(
                    "visible_stagnation_breaker_license"
                )
                item["visible_stagnation_breaker_bonus"] = meta.get(
                    "visible_stagnation_breaker_bonus"
                )
        summary.append(item)
    return summary


def summarize_legal_first_move_sweeps(sweeps: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total_sweeps": len(sweeps),
        "sweeps_with_any_mate": 0,
        "sweeps_without_any_mate": 0,
        "legal_first_move_outcome_counts": {},
        "best_mating_first_move_counts": {},
    }
    for sweep in sweeps:
        results = sweep.get("legal_first_move_results")
        if not isinstance(results, dict):
            continue
        mating_moves = []
        for move, result in results.items():
            if not isinstance(result, dict):
                continue
            outcome = str(result.get("result") or "unknown")
            key = f"{move}:{outcome}"
            summary["legal_first_move_outcome_counts"][key] = (
                summary["legal_first_move_outcome_counts"].get(key, 0) + 1
            )
            if outcome == "mate":
                mating_moves.append((move, int(result.get("plies", 0) or 0)))
        if mating_moves:
            summary["sweeps_with_any_mate"] += 1
            best_plies = min(plies for _, plies in mating_moves)
            for move, plies in mating_moves:
                if plies == best_plies:
                    summary["best_mating_first_move_counts"][move] = (
                        summary["best_mating_first_move_counts"].get(move, 0) + 1
                    )
        else:
            summary["sweeps_without_any_mate"] += 1
    return summary


def summarize_provider_suggestion_audits(sweeps: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total_audits": 0,
        "failure_class_counts": {},
        "converting_not_proposed_count": 0,
        "converting_proposed_not_selected_count": 0,
        "selected_converting_count": 0,
    }
    for sweep in sweeps:
        audit = sweep.get("provider_suggestion_audit")
        if not isinstance(audit, dict):
            continue
        summary["total_audits"] += 1
        failure_class = str(audit.get("failure_class") or "unknown")
        summary["failure_class_counts"][failure_class] = (
            summary["failure_class_counts"].get(failure_class, 0) + 1
        )
        summary["converting_not_proposed_count"] += len(
            audit.get("converting_not_proposed") or []
        )
        summary["converting_proposed_not_selected_count"] += len(
            audit.get("converting_suggested") or []
        )
        if bool(audit.get("selected_converts", False)):
            summary["selected_converting_count"] += 1
    return summary


def summarize_continuation_trace_audits(sweeps: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total_audits": 0,
        "result_counts": {},
        "first_move_counts": {},
    }
    for sweep in sweeps:
        audit = sweep.get("continuation_trace_audit")
        if not isinstance(audit, dict):
            continue
        summary["total_audits"] += 1
        result = str(audit.get("result") or "unknown")
        first_move = str(audit.get("first_move") or "unknown")
        summary["result_counts"][result] = summary["result_counts"].get(result, 0) + 1
        summary["first_move_counts"][first_move] = (
            summary["first_move_counts"].get(first_move, 0) + 1
        )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay failed KRK handoff states with forced successors")
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--successors", type=str, required=True,
                        help="Comma-separated canonical successor skill IDs")
    parser.add_argument("--label", default="fence_established")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-states", type=int, default=0,
                        help="If >0, limit replay to this many failed post-reply states")
    parser.add_argument("--include-duplicate-states", action="store_true",
                        help="Replay duplicate failed post-reply state signatures instead of one representative each")
    parser.add_argument("--playout-max-plies", type=int, default=80)
    parser.add_argument("--black-policy", choices=["random", "adversarial"], default="adversarial")
    parser.add_argument("--max-ticks", type=int, default=200)
    parser.add_argument("--suggestion-limit", type=int, default=5)
    parser.add_argument("--early-stop-stable-suggestions", type=int, default=0,
                        help="Diagnostic speedup: stop each ReCoN move loop after the top suggestion is stable for this many ticks")
    parser.add_argument("--enable-successor-affordance-layer", action="store_true")
    parser.add_argument("--enable-successor-contract-gate", action="store_true")
    parser.add_argument("--enable-successor-role-licenses", action="store_true")
    parser.add_argument("--successor-role-veto-penalty", type=float, default=0.0,
                        help="Opt-in diagnostic visible role-veto penalty")
    parser.add_argument("--successor-stage0-drift-penalty", type=float, default=0.0,
                        help="Opt-in penalty for visibly unproductive stage0 king drift")
    parser.add_argument("--enable-role-scoped-move-shapes", action="store_true",
                        help="Enable role-scoped visible move-shape support")
    parser.add_argument("--role-scoped-move-shape-bonus", type=float, default=0.0)
    parser.add_argument("--require-role-scoped-move-shape-worst-reply", action="store_true",
                        help="Require worst-reply survival terms for role-scoped move-shape support")
    parser.add_argument("--enable-stagnation-breaker", action="store_true",
                        help="Enable opt-in visible stagnation-breaker move license bonus")
    parser.add_argument("--stagnation-breaker-bonus", type=float, default=0.0,
                        help="Small bonus for moves licensed by visible stagnation-breaker terms")
    parser.add_argument("--skip-forced-successor-sweep", action="store_true",
                        help="Run only legal-first replay diagnostics, without forced-successor sweeps")
    parser.add_argument("--steps-output", type=Path, default=None,
                        help="Optional JSONL path for per-forced-successor records")
    parser.add_argument("--sweeps-output", type=Path, default=None,
                        help="Optional JSONL path for per-state sweep records")
    parser.add_argument("--legal-first-move-sweep", action="store_true",
                        help="Also try every legal first White move from each failed post-reply state")
    parser.add_argument("--legal-first-require-any-terms", default="",
                        help="Comma-separated audit terms; only replay moves matching at least one")
    parser.add_argument("--legal-first-require-all-terms", default="",
                        help="Comma-separated audit terms; only replay moves matching all")
    parser.add_argument("--legal-first-max-moves", type=int, default=0,
                        help="If >0, cap tested legal-first moves after term filtering")
    parser.add_argument("--legal-first-audit-no-worst-reply", action="store_true",
                        help="Skip worst-reply terms in legal-first move-shape audits for speed")
    parser.add_argument("--provider-suggestion-audit", action="store_true",
                        help="Compare legal-first converting moves against runtime provider suggestions")
    parser.add_argument("--continuation-trace-audit", action="store_true",
                        help="Trace downstream continuation after the runtime-selected first move")
    parser.add_argument("--continuation-trace-only-selected-converting", action="store_true",
                        help="Only trace when provider audit says the selected first move converted in legal-first replay")
    parser.add_argument("--continuation-trace-max-plies", type=int, default=24,
                        help="Maximum trace events retained for continuation trace audits")
    parser.add_argument("--legal-steps-output", type=Path, default=None,
                        help="Optional JSONL path for per-legal-first-move records")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args()

    diagnostic = json.loads(args.diagnostic.read_text(encoding="utf-8"))
    all_states = failed_post_reply_states(diagnostic, dedupe_state_signatures=False)
    states = failed_post_reply_states(
        diagnostic,
        dedupe_state_signatures=not args.include_duplicate_states,
    )
    if args.max_states > 0:
        states = states[:args.max_states]
    successors = tuple(item.strip() for item in args.successors.split(",") if item.strip())

    graph = build_graph_from_topology(args.topology)
    engine = ReConEngine(graph)
    rng = random.Random(args.seed)

    sweeps: list[dict[str, Any]] = []
    for index, state in enumerate(states, start=1):
        print(
            f"{index:4d}/{len(states)} state={state['state_signature']} "
            f"actual={state.get('actual_selected_successor')} result={state.get('actual_result')}",
            flush=True,
        )
        step_context = {
            "source_diagnostic": str(args.diagnostic),
            "state_index": index - 1,
            **state,
        }
        if args.skip_forced_successor_sweep:
            results = {}
        else:
            results = run_counterfactual_successor_sweep(
                graph,
                engine,
                post_reply_fen=str(state["post_reply_fen"]),
                successors=successors,
                rng=rng,
                label=args.label,
                max_plies=args.playout_max_plies,
                black_policy=args.black_policy,
                max_ticks=args.max_ticks,
                suggestion_limit=args.suggestion_limit,
                successor_affordance_layer_enabled=args.enable_successor_affordance_layer,
                successor_contract_gate_enabled=args.enable_successor_contract_gate,
                successor_role_license_enabled=args.enable_successor_role_licenses,
                successor_role_veto_penalty=args.successor_role_veto_penalty,
                successor_stage0_drift_penalty=args.successor_stage0_drift_penalty,
                successor_role_scoped_move_shape_enabled=args.enable_role_scoped_move_shapes,
                successor_role_scoped_move_shape_bonus=args.role_scoped_move_shape_bonus,
                successor_role_scoped_move_shape_require_worst_reply=(
                    args.require_role_scoped_move_shape_worst_reply
                ),
                stagnation_breaker_enabled=args.enable_stagnation_breaker,
                stagnation_breaker_bonus=args.stagnation_breaker_bonus,
                early_stop_stable_suggestions=args.early_stop_stable_suggestions,
                step_output=args.steps_output,
                step_context=step_context,
            )
        sweep = {
            **state,
            "counterfactual_results": results,
        }
        if args.legal_first_move_sweep:
            legal_results = run_legal_first_move_sweep(
                graph,
                engine,
                post_reply_fen=str(state["post_reply_fen"]),
                rng=rng,
                label=args.label,
                max_plies=args.playout_max_plies,
                black_policy=args.black_policy,
                max_ticks=args.max_ticks,
                suggestion_limit=args.suggestion_limit,
                successor_affordance_layer_enabled=args.enable_successor_affordance_layer,
                successor_contract_gate_enabled=args.enable_successor_contract_gate,
                successor_role_license_enabled=args.enable_successor_role_licenses,
                successor_role_veto_penalty=args.successor_role_veto_penalty,
                successor_stage0_drift_penalty=args.successor_stage0_drift_penalty,
                successor_role_scoped_move_shape_enabled=args.enable_role_scoped_move_shapes,
                successor_role_scoped_move_shape_bonus=args.role_scoped_move_shape_bonus,
                successor_role_scoped_move_shape_require_worst_reply=(
                    args.require_role_scoped_move_shape_worst_reply
                ),
                stagnation_breaker_enabled=args.enable_stagnation_breaker,
                stagnation_breaker_bonus=args.stagnation_breaker_bonus,
                early_stop_stable_suggestions=args.early_stop_stable_suggestions,
                require_any_terms=_parse_terms(args.legal_first_require_any_terms),
                require_all_terms=_parse_terms(args.legal_first_require_all_terms),
                max_moves=args.legal_first_max_moves,
                audit_worst_reply=not args.legal_first_audit_no_worst_reply,
                step_output=args.legal_steps_output,
                step_context=step_context,
            )
            sweep["legal_first_move_results"] = legal_results
            if args.provider_suggestion_audit:
                sweep["provider_suggestion_audit"] = run_provider_suggestion_audit(
                    graph,
                    engine,
                    post_reply_fen=str(state["post_reply_fen"]),
                    legal_first_results=legal_results,
                    max_ticks=args.max_ticks,
                    suggestion_limit=args.suggestion_limit,
                    successor_affordance_layer_enabled=args.enable_successor_affordance_layer,
                    successor_contract_gate_enabled=args.enable_successor_contract_gate,
                    successor_role_license_enabled=args.enable_successor_role_licenses,
                    successor_role_veto_penalty=args.successor_role_veto_penalty,
                    successor_stage0_drift_penalty=args.successor_stage0_drift_penalty,
                    successor_role_scoped_move_shape_enabled=args.enable_role_scoped_move_shapes,
                    successor_role_scoped_move_shape_bonus=args.role_scoped_move_shape_bonus,
                    successor_role_scoped_move_shape_require_worst_reply=(
                        args.require_role_scoped_move_shape_worst_reply
                    ),
                    stagnation_breaker_enabled=args.enable_stagnation_breaker,
                    stagnation_breaker_bonus=args.stagnation_breaker_bonus,
                    early_stop_stable_suggestions=args.early_stop_stable_suggestions,
                )
            if args.continuation_trace_audit:
                provider_audit = sweep.get("provider_suggestion_audit")
                selected_move = (
                    provider_audit.get("move")
                    if isinstance(provider_audit, dict)
                    else None
                )
                selected_converts = (
                    bool(provider_audit.get("selected_converts", False))
                    if isinstance(provider_audit, dict)
                    else False
                )
                if selected_move and (
                    selected_converts
                    or not args.continuation_trace_only_selected_converting
                ):
                    sweep["continuation_trace_audit"] = run_continuation_trace_audit(
                        graph,
                        engine,
                        post_reply_fen=str(state["post_reply_fen"]),
                        first_move=str(selected_move),
                        rng=random.Random(rng.randrange(2**32)),
                        label=args.label,
                        max_plies=args.playout_max_plies,
                        black_policy=args.black_policy,
                        max_ticks=args.max_ticks,
                        suggestion_limit=args.suggestion_limit,
                        successor_affordance_layer_enabled=args.enable_successor_affordance_layer,
                        successor_contract_gate_enabled=args.enable_successor_contract_gate,
                        successor_role_license_enabled=args.enable_successor_role_licenses,
                        successor_role_veto_penalty=args.successor_role_veto_penalty,
                        successor_stage0_drift_penalty=args.successor_stage0_drift_penalty,
                        successor_role_scoped_move_shape_enabled=args.enable_role_scoped_move_shapes,
                        successor_role_scoped_move_shape_bonus=args.role_scoped_move_shape_bonus,
                        successor_role_scoped_move_shape_require_worst_reply=(
                            args.require_role_scoped_move_shape_worst_reply
                        ),
                        stagnation_breaker_enabled=args.enable_stagnation_breaker,
                        stagnation_breaker_bonus=args.stagnation_breaker_bonus,
                        early_stop_stable_suggestions=args.early_stop_stable_suggestions,
                        trace_max_plies=args.continuation_trace_max_plies,
                    )
        sweeps.append(sweep)
        if args.sweeps_output is not None:
            _append_jsonl(args.sweeps_output, sweep)

    summary = {
        "schema_version": "krk_counterfactual_successor_sweep.v1",
        "source_diagnostic": str(args.diagnostic),
        "topology": str(args.topology),
        "successors": list(successors),
        "source_failed_state_count": len(all_states),
        "failed_state_count": len(states),
        "dedupe_state_signatures": not args.include_duplicate_states,
        "counterfactual_successor_sweeps": sweeps,
        "counterfactual_successor_summary": summarize_counterfactual_successor_sweeps(sweeps),
    }
    if args.legal_first_move_sweep:
        summary["legal_first_move_summary"] = summarize_legal_first_move_sweeps(sweeps)
    if args.provider_suggestion_audit:
        summary["provider_suggestion_audit_summary"] = summarize_provider_suggestion_audits(
            sweeps
        )
    if args.continuation_trace_audit:
        summary["continuation_trace_audit_summary"] = summarize_continuation_trace_audits(
            sweeps
        )
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["counterfactual_successor_summary"], indent=2))
    if args.legal_first_move_sweep:
        print(json.dumps(summary["legal_first_move_summary"], indent=2))
    if args.provider_suggestion_audit:
        print(json.dumps(summary["provider_suggestion_audit_summary"], indent=2))
    if args.continuation_trace_audit:
        print(json.dumps(summary["continuation_trace_audit_summary"], indent=2))


if __name__ == "__main__":
    main()
