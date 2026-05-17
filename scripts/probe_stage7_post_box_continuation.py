#!/usr/bin/env python3
"""Bounded Stage 7 post-box-shrink continuation probe.

This is a non-causal topology-vs-weight diagnostic. It consumes the replay-free
Stage 7 post-box diagnosis and checks whether existing continuation providers
can at least propose first moves from the unique failed post-reply states.

Optional short forced playouts can be enabled explicitly. The default mode is
cheap: forced-provider first-move/suggestion audit only.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import chess

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recon_lite.engine import ReConEngine
from recon_lite_chess.krk_baseline_nodes import krk_move_shape_audit

from test_krk_landmark_progress import (
    build_graph_from_topology,
    choose_move_details,
    play_to_mate,
    stable_record_id,
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def _skill_id_for_suggestion(item: dict[str, Any]) -> str:
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    label = meta.get("curriculum_label") or item.get("curriculum_label")
    if label:
        raw = str(label)
        if raw.startswith("krk."):
            return raw
        normalized = "".join(ch if ch.isalnum() else "_" for ch in raw.lower()).strip("_")
        return f"krk.{normalized or 'unknown'}"
    stage = item.get("stage") or meta.get("stage")
    return f"krk.stage_{stage}" if stage is not None else "krk.unknown"


def _parse_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _parse_horizons(value: str) -> tuple[int, ...]:
    horizons = tuple(int(item) for item in _parse_csv(value))
    if not horizons:
        raise ValueError("at least one horizon is required")
    if any(item <= 0 for item in horizons):
        raise ValueError("horizons must be positive")
    return horizons


def failed_post_box_states(
    diagnosis: dict[str, Any],
    *,
    max_states: int = 0,
    state_ids: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    seen: set[str] = set()
    allowed = set(state_ids)
    source_records = list(diagnosis.get("unique_failed_post_reply_states") or [])
    if not source_records:
        source_records = list(diagnosis.get("families") or [])
    for record in source_records:
        if not isinstance(record, dict):
            continue
        fen = record.get("post_reply_fen")
        if not fen:
            continue
        try:
            board = chess.Board(str(fen))
            state_id = stable_record_id("state", board.board_fen(), chess.WHITE)
        except Exception:
            continue
        if allowed and state_id not in allowed:
            continue
        if state_id in seen:
            continue
        seen.add(state_id)
        states.append({
            "state_id": state_id,
            "post_reply_fen": str(fen),
            "selected_successor": record.get("selected_successor"),
            "selected_move": record.get("selected_move"),
            "conversion_result": record.get("conversion_result"),
            "failure_classes": list(record.get("failure_classes") or []),
            "source_sample_index": record.get("sample_index"),
            "family_id": record.get("family_id"),
            "diagnosis": record.get("diagnosis"),
            "source_record": record,
        })
        if max_states > 0 and len(states) >= max_states:
            break
    return states


def _compact_suggestion(item: dict[str, Any]) -> dict[str, Any]:
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    compact = {
        "move": item.get("move"),
        "skill_id": _skill_id_for_suggestion(item),
        "score": item.get("score"),
        "actuator": item.get("actuator"),
        "curriculum_label": meta.get("curriculum_label") or item.get("curriculum_label"),
        "stage": meta.get("stage") or item.get("stage"),
    }
    if isinstance(meta.get("visible_role_provider_support_adapter"), dict):
        compact["visible_role_provider_support_adapter"] = dict(
            meta["visible_role_provider_support_adapter"]
        )
    if "explicit_role_provider_move_shape_support_bonus" in meta:
        compact["explicit_role_provider_move_shape_support_bonus"] = meta.get(
            "explicit_role_provider_move_shape_support_bonus"
        )
    if isinstance(meta.get("visible_move_shape_audit"), dict):
        audit = meta["visible_move_shape_audit"]
        compact["visible_move_shape_audit"] = {
            "move_shape_terms": list(audit.get("move_shape_terms", []) or []),
            "post_move_terms": list(audit.get("post_move_terms", []) or []),
        }
    return compact


def forced_provider_first_move_probe(
    graph,
    engine: ReConEngine,
    *,
    post_reply_fen: str,
    provider: str,
    max_ticks: int,
    suggestion_limit: int,
    early_stop_stable_suggestions: int,
    enable_successor_affordance_layer: bool,
    enable_successor_role_licenses: bool,
    enable_role_scoped_move_shapes: bool,
    explicit_role_provider_support_enabled: bool,
    enable_diagnostic_caches: bool,
) -> dict[str, Any]:
    board = chess.Board(post_reply_fen)
    details = choose_move_details(
        graph,
        engine,
        board,
        max_ticks=max_ticks,
        suggestion_limit=suggestion_limit,
        successor_affordance_layer_enabled=enable_successor_affordance_layer,
        successor_role_license_enabled=enable_successor_role_licenses,
        successor_role_scoped_move_shape_enabled=enable_role_scoped_move_shapes,
        explicit_role_provider_support_enabled=explicit_role_provider_support_enabled,
        forced_successor_skill=provider,
        early_stop_stable_suggestions=early_stop_stable_suggestions,
        enable_diagnostic_caches=enable_diagnostic_caches,
    )
    move_uci = details.get("move")
    audit = None
    legal = False
    if move_uci:
        try:
            move = chess.Move.from_uci(str(move_uci))
            legal = move in board.legal_moves
            if legal:
                audit = krk_move_shape_audit(board, move, include_worst_reply=False)
        except Exception:
            legal = False
    suggestions = list(details.get("suggestions") or [])
    return {
        "provider": provider,
        "forced_successor_available": bool(details.get("forced_successor_available")),
        "move": move_uci,
        "legal": legal,
        "confidence": details.get("confidence"),
        "ticks": details.get("ticks"),
        "early_stopped": bool(details.get("early_stopped", False)),
        "suggestion_count": len(suggestions),
        "top_suggestions": [_compact_suggestion(item) for item in suggestions[:suggestion_limit]],
        "move_shape_audit": audit,
    }


def forced_provider_playout_probe(
    graph,
    engine: ReConEngine,
    *,
    post_reply_fen: str,
    provider: str,
    rng: random.Random,
    label: str,
    horizon: int,
    black_policy: str,
    max_ticks: int,
    suggestion_limit: int,
    early_stop_stable_suggestions: int,
    enable_successor_affordance_layer: bool,
    enable_successor_role_licenses: bool,
    enable_role_scoped_move_shapes: bool,
    explicit_role_provider_support_enabled: bool,
    enable_diagnostic_caches: bool,
) -> dict[str, Any]:
    board = chess.Board(post_reply_fen)
    result = play_to_mate(
        graph,
        engine,
        board,
        rng,
        label,
        None,
        horizon,
        black_policy,
        trace=False,
        max_ticks=max_ticks,
        suggestion_limit=suggestion_limit,
        successor_affordance_layer_enabled=enable_successor_affordance_layer,
        successor_role_license_enabled=enable_successor_role_licenses,
        successor_role_scoped_move_shape_enabled=enable_role_scoped_move_shapes,
        explicit_role_provider_support_enabled=explicit_role_provider_support_enabled,
        early_stop_stable_suggestions=early_stop_stable_suggestions,
        forced_successor_skill=provider,
        enable_diagnostic_caches=enable_diagnostic_caches,
    )
    first = result.get("first_successor") if isinstance(result.get("first_successor"), dict) else {}
    engine_details = first.get("engine") if isinstance(first.get("engine"), dict) else {}
    return {
        "provider": provider,
        "horizon": horizon,
        "result": result.get("result"),
        "plies": result.get("plies"),
        "first_move": first.get("move"),
        "forced_successor_available": engine_details.get("forced_successor_available"),
        "engine_decision_count": result.get("engine_decision_count"),
        "engine_ticks_total": result.get("engine_ticks_total"),
        "engine_early_stop_count": result.get("engine_early_stop_count"),
    }


def _audit_term_set(audit: dict[str, Any]) -> set[str]:
    terms: set[str] = set()
    for key in ("current_terms", "move_shape_terms", "post_move_terms", "worst_reply_terms"):
        values = audit.get(key)
        if isinstance(values, list):
            terms.update(str(item) for item in values)
    return terms


def legal_first_move_probe(
    graph,
    engine: ReConEngine,
    *,
    post_reply_fen: str,
    rng: random.Random,
    label: str,
    horizon: int,
    black_policy: str,
    max_ticks: int,
    suggestion_limit: int,
    early_stop_stable_suggestions: int,
    enable_successor_affordance_layer: bool,
    enable_successor_role_licenses: bool,
    enable_role_scoped_move_shapes: bool,
    explicit_role_provider_support_enabled: bool,
    enable_diagnostic_caches: bool,
    require_any_terms: tuple[str, ...],
    require_all_terms: tuple[str, ...],
    max_moves: int,
    audit_worst_reply: bool,
) -> list[dict[str, Any]]:
    board = chess.Board(post_reply_fen)
    candidates: list[tuple[chess.Move, dict[str, Any]]] = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        audit = krk_move_shape_audit(board, move, include_worst_reply=audit_worst_reply)
        terms = _audit_term_set(audit)
        if require_any_terms and not terms.intersection(require_any_terms):
            continue
        if require_all_terms and not set(require_all_terms).issubset(terms):
            continue
        candidates.append((move, audit))
    if max_moves > 0:
        candidates = candidates[:max_moves]

    results: list[dict[str, Any]] = []
    for move, audit in candidates:
        b = board.copy(stack=False)
        b.push(move)
        if b.is_checkmate():
            payload = {
                "move": move.uci(),
                "horizon": horizon,
                "result": "mate",
                "plies": 1,
                "move_shape_audit": audit,
            }
        else:
            continuation = play_to_mate(
                graph,
                engine,
                b,
                random.Random(rng.randrange(2**32)),
                label,
                None,
                max(0, horizon - 1),
                black_policy,
                trace=False,
                max_ticks=max_ticks,
                suggestion_limit=suggestion_limit,
                successor_affordance_layer_enabled=enable_successor_affordance_layer,
                successor_role_license_enabled=enable_successor_role_licenses,
                successor_role_scoped_move_shape_enabled=enable_role_scoped_move_shapes,
                explicit_role_provider_support_enabled=explicit_role_provider_support_enabled,
                early_stop_stable_suggestions=early_stop_stable_suggestions,
                enable_diagnostic_caches=enable_diagnostic_caches,
            )
            payload = {
                "move": move.uci(),
                "horizon": horizon,
                "result": continuation.get("result"),
                "plies": int(continuation.get("plies", 0) or 0) + 1,
                "first_successor": continuation.get("first_successor"),
                "engine_decision_count": continuation.get("engine_decision_count"),
                "engine_ticks_total": continuation.get("engine_ticks_total"),
                "move_shape_audit": audit,
            }
        results.append(payload)
    return results


def summarize_probe(records: list[dict[str, Any]]) -> dict[str, Any]:
    first_move_counts = Counter()
    first_move_available = Counter()
    playout_counts = Counter()
    mate_by_provider = Counter()
    legal_first_counts = Counter()
    legal_first_mate_by_move = Counter()
    state_with_any_available: set[str] = set()
    state_with_any_mate: set[str] = set()
    state_with_any_legal_first_mate: set[str] = set()
    for record in records:
        state_id = str(record.get("state_id") or "unknown")
        for probe in record.get("first_move_probes") or []:
            provider = str(probe.get("provider") or "unknown")
            available = bool(probe.get("forced_successor_available")) and bool(probe.get("legal"))
            first_move_available[f"{provider}:{'available' if available else 'unavailable'}"] += 1
            if available:
                state_with_any_available.add(state_id)
            move = str(probe.get("move") or "none")
            first_move_counts[f"{provider}:{move}"] += 1
        for probe in record.get("playout_probes") or []:
            provider = str(probe.get("provider") or "unknown")
            result = str(probe.get("result") or "unknown")
            horizon = str(probe.get("horizon") or "unknown")
            playout_counts[f"{provider}:h{horizon}:{result}"] += 1
            if result == "mate":
                mate_by_provider[provider] += 1
                state_with_any_mate.add(state_id)
        for probe in record.get("legal_first_probes") or []:
            result = str(probe.get("result") or "unknown")
            move = str(probe.get("move") or "unknown")
            horizon = str(probe.get("horizon") or "unknown")
            legal_first_counts[f"h{horizon}:{result}"] += 1
            if result == "mate":
                legal_first_mate_by_move[move] += 1
                state_with_any_legal_first_mate.add(state_id)
    diagnosis = "needs_forced_playout_probe"
    if playout_counts:
        if state_with_any_mate:
            diagnosis = "topology_present_untrained_or_miscalibrated"
        else:
            diagnosis = "provider_capacity_missing_or_horizon_limited"
    elif state_with_any_available:
        diagnosis = "existing_provider_first_moves_available_playout_pending"
    return {
        "state_count": len(records),
        "states_with_any_available_provider": len(state_with_any_available),
        "states_with_any_mating_forced_playout": len(state_with_any_mate),
        "first_move_available_counts": dict(first_move_available),
        "first_move_counts": dict(first_move_counts),
        "forced_playout_outcome_counts": dict(playout_counts),
        "forced_playout_mate_by_provider": dict(mate_by_provider),
        "states_with_any_legal_first_mate": len(state_with_any_legal_first_mate),
        "legal_first_outcome_counts": dict(legal_first_counts),
        "legal_first_mate_by_move": dict(legal_first_mate_by_move),
        "topology_weight_diagnosis": diagnosis,
    }


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    start = time.perf_counter()
    diagnosis = _load_json(args.diagnosis)
    providers = _parse_csv(args.providers)
    horizons = _parse_horizons(args.horizons)
    states = failed_post_box_states(
        diagnosis,
        max_states=args.max_states,
        state_ids=_parse_csv(args.state_ids),
    )
    graph = build_graph_from_topology(args.topology)
    engine = ReConEngine(graph)
    rng = random.Random(args.seed)
    records: list[dict[str, Any]] = []
    for state_index, state in enumerate(states, start=1):
        print(f"{state_index:3d}/{len(states)} state={state['state_id']}", flush=True)
        record = {
            **state,
            "first_move_probes": [],
            "playout_probes": [],
            "legal_first_probes": [],
        }
        for provider in providers:
            first_probe = forced_provider_first_move_probe(
                graph,
                engine,
                post_reply_fen=str(state["post_reply_fen"]),
                provider=provider,
                max_ticks=args.max_ticks,
                suggestion_limit=args.suggestion_limit,
                early_stop_stable_suggestions=args.early_stop_stable_suggestions,
                enable_successor_affordance_layer=args.enable_successor_affordance_layer,
                enable_successor_role_licenses=args.enable_successor_role_licenses,
                enable_role_scoped_move_shapes=args.enable_role_scoped_move_shapes,
                explicit_role_provider_support_enabled=args.enable_explicit_role_provider_support,
                enable_diagnostic_caches=args.enable_diagnostic_caches,
            )
            record["first_move_probes"].append(first_probe)
            if args.steps_output:
                _append_jsonl(args.steps_output, {
                    "probe_kind": "forced_provider_first_move",
                    "state_id": state["state_id"],
                    **first_probe,
                })
            if not args.run_forced_playouts:
                continue
            if args.playouts_only_if_provider_available and not (
                first_probe.get("forced_successor_available") and first_probe.get("legal")
            ):
                continue
            for horizon in horizons:
                playout_probe = forced_provider_playout_probe(
                    graph,
                    engine,
                    post_reply_fen=str(state["post_reply_fen"]),
                    provider=provider,
                    rng=random.Random(rng.randrange(2**32)),
                    label=args.label,
                    horizon=horizon,
                    black_policy=args.black_policy,
                    max_ticks=args.max_ticks,
                    suggestion_limit=args.suggestion_limit,
                    early_stop_stable_suggestions=args.early_stop_stable_suggestions,
                    enable_successor_affordance_layer=args.enable_successor_affordance_layer,
                    enable_successor_role_licenses=args.enable_successor_role_licenses,
                    enable_role_scoped_move_shapes=args.enable_role_scoped_move_shapes,
                    explicit_role_provider_support_enabled=args.enable_explicit_role_provider_support,
                    enable_diagnostic_caches=args.enable_diagnostic_caches,
                )
                record["playout_probes"].append(playout_probe)
                if args.steps_output:
                    _append_jsonl(args.steps_output, {
                        "probe_kind": "forced_provider_playout",
                        "state_id": state["state_id"],
                        **playout_probe,
                    })
        if args.run_legal_first_sweep:
            for horizon in horizons:
                legal_results = legal_first_move_probe(
                    graph,
                    engine,
                    post_reply_fen=str(state["post_reply_fen"]),
                    rng=random.Random(rng.randrange(2**32)),
                    label=args.label,
                    horizon=horizon,
                    black_policy=args.black_policy,
                    max_ticks=args.max_ticks,
                    suggestion_limit=args.suggestion_limit,
                    early_stop_stable_suggestions=args.early_stop_stable_suggestions,
                    enable_successor_affordance_layer=args.enable_successor_affordance_layer,
                    enable_successor_role_licenses=args.enable_successor_role_licenses,
                    enable_role_scoped_move_shapes=args.enable_role_scoped_move_shapes,
                    explicit_role_provider_support_enabled=args.enable_explicit_role_provider_support,
                    enable_diagnostic_caches=args.enable_diagnostic_caches,
                    require_any_terms=_parse_csv(args.legal_first_require_any_terms),
                    require_all_terms=_parse_csv(args.legal_first_require_all_terms),
                    max_moves=args.legal_first_max_moves,
                    audit_worst_reply=not args.legal_first_audit_no_worst_reply,
                )
                record["legal_first_probes"].extend(legal_results)
                if args.steps_output:
                    for legal_probe in legal_results:
                        _append_jsonl(args.steps_output, {
                            "probe_kind": "legal_first_move",
                            "state_id": state["state_id"],
                            **legal_probe,
                        })
        records.append(record)
    summary = summarize_probe(records)
    return {
        "schema_version": "stage7_post_box_forced_provider_probe.v1",
        "causal_status": "non_causal",
        "source_diagnosis": str(args.diagnosis),
        "topology": str(args.topology),
        "providers": list(providers),
        "horizons": list(horizons),
        "run_forced_playouts": bool(args.run_forced_playouts),
        "config": {
            "max_ticks": args.max_ticks,
            "suggestion_limit": args.suggestion_limit,
            "early_stop_stable_suggestions": args.early_stop_stable_suggestions,
            "black_policy": args.black_policy,
            "successor_affordance_layer_enabled": args.enable_successor_affordance_layer,
            "successor_role_licenses_enabled": args.enable_successor_role_licenses,
            "role_scoped_move_shapes_enabled": args.enable_role_scoped_move_shapes,
            "explicit_role_provider_support_enabled": args.enable_explicit_role_provider_support,
            "diagnostic_caches_enabled": args.enable_diagnostic_caches,
            "run_legal_first_sweep": args.run_legal_first_sweep,
            "legal_first_require_any_terms": args.legal_first_require_any_terms,
            "legal_first_require_all_terms": args.legal_first_require_all_terms,
            "legal_first_max_moves": args.legal_first_max_moves,
        },
        "summary": summary,
        "candidate_update": {
            "candidate_id": "cand.krk.box_shrink.handoff_role_refinement.v1",
            "status": (
                "needs_bounded_m3_or_role_calibration_probe"
                if summary["topology_weight_diagnosis"] == "topology_present_untrained_or_miscalibrated"
                else "needs_forced_playout_probe"
                if summary["topology_weight_diagnosis"] == "existing_provider_first_moves_available_playout_pending"
                else "possible_provider_capacity_gap"
            ),
            "topology_weight_diagnosis": summary["topology_weight_diagnosis"],
            "causal_status": "non_causal",
            "promotion_status": "proposed",
        },
        "records": records,
        "wall_time_seconds": round(time.perf_counter() - start, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded Stage 7 post-box continuation probe")
    parser.add_argument("--diagnosis", type=Path, required=True)
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--providers", type=str, required=True)
    parser.add_argument("--horizons", type=str, default="20,40")
    parser.add_argument("--label", default="box_shrink")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-states", type=int, default=0)
    parser.add_argument("--state-ids", default="", help="Comma-separated state IDs to include")
    parser.add_argument("--max-ticks", type=int, default=20)
    parser.add_argument("--suggestion-limit", type=int, default=5)
    parser.add_argument("--early-stop-stable-suggestions", type=int, default=2)
    parser.add_argument("--black-policy", choices=["random", "adversarial"], default="adversarial")
    parser.add_argument("--enable-successor-affordance-layer", action="store_true")
    parser.add_argument("--enable-successor-role-licenses", action="store_true")
    parser.add_argument("--enable-role-scoped-move-shapes", action="store_true")
    parser.add_argument("--enable-explicit-role-provider-support", action="store_true")
    parser.add_argument("--enable-diagnostic-caches", action="store_true")
    parser.add_argument("--run-forced-playouts", action="store_true")
    parser.add_argument("--playouts-only-if-provider-available", action="store_true")
    parser.add_argument("--run-legal-first-sweep", action="store_true")
    parser.add_argument("--legal-first-require-any-terms", default="")
    parser.add_argument("--legal-first-require-all-terms", default="")
    parser.add_argument("--legal-first-max-moves", type=int, default=0)
    parser.add_argument("--legal-first-audit-no-worst-reply", action="store_true")
    parser.add_argument("--steps-output", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = run_probe(args)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
