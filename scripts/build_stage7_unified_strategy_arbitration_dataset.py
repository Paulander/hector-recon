#!/usr/bin/env python3
"""Build a non-causal Stage 7 unified KRK strategy arbitration dataset.

This script probes decision states offline. It records suggestions from
independently learned KRK providers, visible board/move terms, provider-local
rank/normalization, and bounded playout labels for provider-best suggestions.

It does not change runtime behavior, does not mutate topology, and does not use
DTM/tablebase values at runtime.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import chess

import test_krk_landmark_progress as diag
from recon_lite_chess.krk_baseline_nodes import (
    _compute_krk_context_terms,
    _krk_geometry_metrics,
    krk_move_shape_audit,
)


DEFAULT_PROVIDERS = [
    "krk.stage0_basin",
    "krk.edge_trap_close",
    "krk.edge_trap_enemy_between",
    "krk.edge_trap_wrong_tempo",
    "krk.fence_established",
    "krk.drive_to_edge",
    "krk.box_shrink",
    "krk.post_box_shrink_continuation",
]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _move_uci(value: Any) -> str:
    return value.uci() if hasattr(value, "uci") else str(value or "")


def _skill_id(suggestion: dict[str, Any]) -> str:
    return str(
        suggestion.get("skill_id")
        or suggestion.get("provider_skill_id")
        or suggestion.get("curriculum_label")
        or ""
    )


def _normalize_skill_id(value: str) -> str:
    if value.startswith("krk."):
        return value
    mapping = {
        "stage0_basin": "krk.stage0_basin",
        "edge_trap_close": "krk.edge_trap_close",
        "edge_trap_enemy_between": "krk.edge_trap_enemy_between",
        "edge_trap_wrong_tempo": "krk.edge_trap_wrong_tempo",
        "fence_established": "krk.fence_established",
        "drive_to_edge": "krk.drive_to_edge",
        "box_shrink": "krk.box_shrink",
        "post_box_shrink_continuation": "krk.post_box_shrink_continuation",
    }
    return mapping.get(value, value)


def _state_id(fen: str) -> str:
    import hashlib

    return "state." + hashlib.sha1(fen.encode("utf-8")).hexdigest()[:12]


def _collect_seed_fens(seed: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for trajectory_index, trajectory in enumerate(seed.get("trajectories") or []):
        if not isinstance(trajectory, dict):
            continue
        steps = [step for step in trajectory.get("white_training_steps") or [] if isinstance(step, dict)]
        if not steps or not steps[0].get("fen"):
            continue
        step = steps[0]
        fen = str(step["fen"])
        if fen in seen:
            continue
        seen.add(fen)
        rows.append({
            "fen": fen,
            "source": "trajectory_seed_start",
            "trajectory_index": trajectory_index,
            "step_index": 0,
            "teacher_move": step.get("move"),
        })
    return rows


def _collect_replay_fens(payloads: list[dict[str, Any]], seen: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_index, payload in enumerate(payloads):
        source = str(payload.get("topology") or payload.get("schema_version") or source_index)
        for record_index, record in enumerate(payload.get("records") or []):
            if not isinstance(record, dict):
                continue
            if record.get("start_fen") and str(record["start_fen"]) not in seen:
                fen = str(record["start_fen"])
                seen.add(fen)
                rows.append({
                    "fen": fen,
                    "source": "closed_loop_replay_start",
                    "replay_source": source,
                    "record_index": record_index,
                    "source_result": record.get("result"),
                })
            for event in record.get("trace") or []:
                if not isinstance(event, dict) or event.get("turn") != "white" or not event.get("fen"):
                    continue
                fen = str(event["fen"])
                if fen in seen:
                    continue
                seen.add(fen)
                rows.append({
                    "fen": fen,
                    "source": "closed_loop_replay_trace",
                    "replay_source": source,
                    "record_index": record_index,
                    "source_ply": event.get("ply"),
                    "source_move": event.get("move"),
                    "source_result": record.get("result"),
                })
    return rows


def _box_area_relevance(metrics: dict[str, Any] | None) -> str:
    if not metrics:
        return "unknown"
    edge_value = metrics.get("enemy_edge_distance")
    box_value = metrics.get("box_area")
    edge = int(edge_value) if edge_value is not None else 99
    box = int(box_value) if box_value is not None else 0
    if edge <= 0:
        return "low"
    if edge == 1:
        return "medium" if box >= 8 else "low"
    return "high" if box >= 12 else "medium"


def _board_features(board: chess.Board) -> dict[str, Any]:
    terms = _compute_krk_context_terms(board)
    metrics = _krk_geometry_metrics(board) or {}
    return {
        "fen": board.fen(),
        "terminal_terms": terms,
        "active_terminal_terms": sorted(key for key, value in terms.items() if value),
        "metrics": metrics,
        "box_area_relevance": _box_area_relevance(metrics),
        "black_king_edge_distance": metrics.get("enemy_edge_distance"),
        "box_area": metrics.get("box_area"),
        "black_king_mobility": metrics.get("black_king_escape_count"),
        "rook_safe": bool(terms.get("rook_safe", False)),
        "fence_exists": bool(terms.get("fence_exists", False)),
        "fence_stable": bool(terms.get("fence_stable", False)),
        "king_support": bool(terms.get("white_king_support_available", False)),
        "mate_in_one": bool(terms.get("mate_in_one_available", False)),
        "edge_or_corner_pressure": bool(
            terms.get("edge_rook_transfer_recovery_available", False)
            or terms.get("corner_net_pressure_available", False)
            or terms.get("enemy_king_near_edge", False)
        ),
    }


def _provider_ranked_suggestions(
    suggestions: list[dict[str, Any]],
    providers: set[str],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for suggestion in suggestions:
        skill = _normalize_skill_id(_skill_id(suggestion))
        if skill not in providers:
            continue
        grouped[skill].append(suggestion)

    rows: list[dict[str, Any]] = []
    for provider, items in grouped.items():
        items.sort(key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)
        scores = [float(item.get("score", 0.0) or 0.0) for item in items]
        min_score = min(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0
        denom = max_score - min_score
        for idx, item in enumerate(items, start=1):
            score = float(item.get("score", 0.0) or 0.0)
            normalized = 1.0 if denom == 0.0 and idx == 1 else (score - min_score) / denom if denom else 0.0
            rows.append({
                "provider_id": provider,
                "move": _move_uci(item.get("move")),
                "raw_score": score,
                "provider_local_rank": idx,
                "provider_local_normalized_score": normalized,
                "provider_local_rank_score": 1.0 / float(idx),
                "actuator": item.get("actuator"),
                "curriculum_label": item.get("curriculum_label"),
                "meta": item.get("meta") if isinstance(item.get("meta"), dict) else {},
            })
    rows.sort(key=lambda item: float(item["raw_score"]), reverse=True)
    return rows


def _suggestion_features(board: chess.Board, suggestion: dict[str, Any]) -> dict[str, Any]:
    move_uci = str(suggestion.get("move") or "")
    audit: dict[str, Any] = {}
    try:
        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            audit = krk_move_shape_audit(board, move, {}, include_worst_reply=False)
    except Exception:
        audit = {}
    current_box = audit.get("current_box_area")
    post_box = audit.get("post_box_area")
    return {
        "move_shape_terms": list(audit.get("move_shape_terms") or []),
        "post_move_terms": list(audit.get("post_move_terms") or []),
        "safety_terms": [
            term
            for term in (
                "rook_safe_after_move",
                "no_draw_after_move",
                "no_stalemate_after_move",
            )
            if term in set(audit.get("post_move_terms") or []) or term in set(audit.get("source_terms") or [])
        ],
        "veto_terms": list(audit.get("veto_terms") or []),
        "box_area_delta": (
            int(post_box) - int(current_box)
            if post_box is not None and current_box is not None
            else None
        ),
        "visible_move_shape_audit": audit,
    }


def _label_candidate(
    *,
    graph: Any,
    engine: Any,
    board: chess.Board,
    move_uci: str,
    rng: random.Random,
    horizon: int,
    max_ticks: int,
    trace_mode: str,
) -> dict[str, Any]:
    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        return {"result": "illegal_move", "plies": 0}
    b = board.copy(stack=False)
    b.push(move)
    trace_enabled = trace_mode == "all"
    result = diag.play_to_mate(
        graph,
        engine,
        b,
        rng,
        label="box_shrink",
        stage_filter=None,
        max_plies=max(0, horizon - 1),
        black_policy="adversarial",
        trace=trace_enabled,
        trace_max_plies=horizon,
        max_ticks=max_ticks,
        suggestion_limit=5,
        early_stop_stable_suggestions=2,
        enable_diagnostic_caches=True,
        initial_white_moves=1,
    )
    if trace_mode == "failures" and result.get("result") != "mate":
        # Optional failure trace rerun for inspection. The default probe keeps
        # this off because h40 labels are the expensive part of the dataset.
        traced = diag.play_to_mate(
            graph,
            engine,
            b,
            rng,
            label="box_shrink",
            stage_filter=None,
            max_plies=max(0, horizon - 1),
            black_policy="adversarial",
            trace=True,
            trace_max_plies=horizon,
            max_ticks=max_ticks,
            suggestion_limit=5,
            early_stop_stable_suggestions=2,
            enable_diagnostic_caches=True,
            initial_white_moves=1,
        )
        result = traced
    stagnation = result.get("stagnation_summary") if isinstance(result.get("stagnation_summary"), dict) else {}
    first_successor = result.get("first_successor") if isinstance(result.get("first_successor"), dict) else {}
    engine_payload = first_successor.get("engine") if isinstance(first_successor.get("engine"), dict) else {}
    selected = engine_payload.get("selected_suggestion") if isinstance(engine_payload.get("selected_suggestion"), dict) else {}
    return {
        "result": result.get("result"),
        "plies": result.get("plies"),
        "stagnation": bool(stagnation.get("stagnation_loop") or stagnation.get("rook_oscillation_loop")),
        "shadow_candidate": False,
        "successful_handoff": bool(result.get("result") == "mate"),
        "first_successor_skill": selected.get("skill_id"),
        "first_successor_move": selected.get("move"),
    }


def build_dataset(
    *,
    topology_path: Path,
    trajectory_seed_path: Path,
    replay_paths: list[Path],
    providers: list[str],
    max_states: int,
    max_labels_per_state: int,
    horizon: int,
    max_ticks: int,
    label_trace_mode: str,
    seed: int,
) -> dict[str, Any]:
    trajectory_seed = _load_json(trajectory_seed_path)
    replay_payloads = [_load_json(path) for path in replay_paths if path.exists()]
    state_rows = _collect_seed_fens(trajectory_seed)
    seen = {row["fen"] for row in state_rows}
    state_rows.extend(_collect_replay_fens(replay_payloads, seen))
    state_rows = state_rows[:max_states]

    graph = diag.build_graph_from_topology(topology_path)
    engine = diag.ReConEngine(graph)
    label_engine = diag.ReConEngine(graph)
    rng = random.Random(seed)
    provider_set = {_normalize_skill_id(provider) for provider in providers}
    records: list[dict[str, Any]] = []

    for row in state_rows:
        board = chess.Board(row["fen"])
        board_features = _board_features(board)
        details = diag.choose_move_details(
            graph,
            engine,
            board,
            max_ticks=max_ticks,
            stage_filter=None,
            suggestion_limit=1000,
            active_landmark_label="box_shrink",
            stage7_post_box_post_reply_context=True,
            candidate_move_layer_enabled=True,
            early_stop_stable_suggestions=2,
            enable_diagnostic_caches=True,
        )
        suggestions = _provider_ranked_suggestions(list(details.get("suggestions") or []), provider_set)
        provider_best = {
            item["provider_id"]: item
            for item in suggestions
            if int(item.get("provider_local_rank", 0) or 0) == 1
        }
        labels_by_key: dict[str, dict[str, Any]] = {}
        label_candidates = sorted(
            provider_best.values(),
            key=lambda item: (
                0 if item["provider_id"] in {"krk.stage0_basin", "krk.box_shrink"} else 1,
                -float(item.get("raw_score", 0.0) or 0.0),
            ),
            reverse=True,
        )[:max_labels_per_state]
        for item in label_candidates:
            key = f"{item['provider_id']}:{item['move']}"
            labels_by_key[key] = _label_candidate(
                graph=graph,
                engine=label_engine,
                board=board,
                move_uci=str(item["move"]),
                rng=rng,
                horizon=horizon,
                max_ticks=max_ticks,
                trace_mode=label_trace_mode,
            )
        enriched = []
        used_label_keys: set[str] = set()
        for item in suggestions:
            features = _suggestion_features(board, item)
            label_key = f"{item['provider_id']}:{item['move']}"
            label = labels_by_key.get(label_key) if label_key not in used_label_keys else None
            if label is not None:
                used_label_keys.add(label_key)
            enriched.append({
                **item,
                **features,
                "playout_label": label,
                "label_scope": "provider_best_h40" if label else "unlabeled_non_best_suggestion",
            })
        records.append({
            "state_id": _state_id(row["fen"]),
            "fen": row["fen"],
            "source": row,
            "board_features": board_features,
            "role_capsule_context": {
                "active_landmark_label": "box_shrink",
                "stage7_post_box_post_reply_context": True,
                "plan_capsule_runtime_enabled": False,
                "causal_status": "non_causal_dataset",
            },
            "selected_runtime_move": details.get("move"),
            "selected_runtime_provider": (details.get("selected_suggestion") or {}).get("skill_id"),
            "suggestions": enriched,
        })
    return {
        "schema_version": "stage7_unified_strategy_arbitration_dataset.v1",
        "causal_status": "non_causal",
        "runtime_behavior_changed": False,
        "runtime_tablebase_lookup": False,
        "topology": str(topology_path),
        "trajectory_seed": str(trajectory_seed_path),
        "replay_sources": [str(path) for path in replay_paths],
        "providers": sorted(provider_set),
        "horizon": int(horizon),
        "label_scope": "provider_best_suggestions_only",
        "max_labels_per_state": int(max_labels_per_state),
        "label_trace_mode": str(label_trace_mode),
        "state_count": len(records),
        "records": records,
        "hard_constraints": [
            "do_not_train_stage8",
            "do_not_promote_stage7",
            "do_not_make_arbitration_causal",
            "do_not_use_dtm_or_tablebase_at_runtime",
            "do_not_mutate_topology_during_gameplay",
        ],
    }


def _mate_label(item: dict[str, Any]) -> bool:
    label = item.get("playout_label") if isinstance(item.get("playout_label"), dict) else {}
    return label.get("result") == "mate"


def run_probe(dataset: dict[str, Any]) -> dict[str, Any]:
    state_summaries = []
    raw_top_success = 0
    normalized_shortlist_success = 0
    labeled_state_count = 0
    provider_outcomes: Counter[str] = Counter()
    relevance_outcomes: Counter[str] = Counter()
    selected_failures: Counter[str] = Counter()
    feature_groups: dict[tuple[str, Any], Counter[str]] = defaultdict(Counter)

    for record in dataset.get("records") or []:
        suggestions = [item for item in record.get("suggestions") or [] if item.get("playout_label")]
        if not suggestions:
            continue
        labeled_state_count += 1
        raw_top = max(suggestions, key=lambda item: float(item.get("raw_score", 0.0) or 0.0))
        provider_best = [item for item in suggestions if int(item.get("provider_local_rank", 0) or 0) == 1]
        converting = [item for item in suggestions if _mate_label(item)]
        if _mate_label(raw_top):
            raw_top_success += 1
        if any(_mate_label(item) for item in provider_best):
            normalized_shortlist_success += 1
        relevance = str((record.get("board_features") or {}).get("box_area_relevance", "unknown"))
        relevance_outcomes[f"{relevance}:any_mate={bool(converting)}"] += 1
        for item in suggestions:
            label = item.get("playout_label") or {}
            provider_outcomes[f"{item['provider_id']}:{label.get('result')}"] += 1
            if label.get("result") != "mate" and item["provider_id"] in {
                "krk.box_shrink",
                "krk.stage0_basin",
            }:
                selected_failures[f"{item['provider_id']}:{relevance}"] += 1
        features = record.get("board_features") or {}
        for key in ("box_area_relevance", "black_king_edge_distance", "fence_exists", "king_support"):
            feature_groups[(key, features.get(key))].update(
                item["provider_id"] for item in converting
            )
        state_summaries.append({
            "state_id": record.get("state_id"),
            "box_area_relevance": relevance,
            "raw_top_provider": raw_top.get("provider_id"),
            "raw_top_move": raw_top.get("move"),
            "raw_top_result": (raw_top.get("playout_label") or {}).get("result"),
            "converting_providers": sorted({item["provider_id"] for item in converting}),
            "provider_local_rank1_contains_converting": any(_mate_label(item) for item in provider_best),
        })

    best_feature_rules = []
    for (key, value), counts in feature_groups.items():
        if not counts:
            continue
        provider, support = counts.most_common(1)[0]
        best_feature_rules.append({
            "feature": key,
            "value": value,
            "predicted_converting_provider": provider,
            "support": support,
            "provider_counts": dict(counts),
        })
    best_feature_rules.sort(key=lambda item: int(item["support"]), reverse=True)
    return {
        "schema_version": "stage7_unified_strategy_arbitration_probe.v1",
        "causal_status": "non_causal",
        "dataset_state_count": int(dataset.get("state_count", 0) or 0),
        "labeled_state_count": labeled_state_count,
        "raw_global_top_conversion_rate": raw_top_success / labeled_state_count if labeled_state_count else 0.0,
        "provider_local_rank1_oracle_coverage": (
            normalized_shortlist_success / labeled_state_count if labeled_state_count else 0.0
        ),
        "provider_outcome_counts": dict(provider_outcomes),
        "box_area_relevance_outcome_counts": dict(relevance_outcomes),
        "box_or_stage0_failure_counts_by_relevance": dict(selected_failures),
        "best_visible_feature_rules": best_feature_rules[:12],
        "state_summaries": state_summaries,
        "answers": {
            "provider_selection_model_predicts_converting_provider": bool(best_feature_rules),
            "provider_local_normalization_outperforms_raw_global_score": (
                normalized_shortlist_success > raw_top_success
            ),
            "box_area_relevance_explains_some_failures": any(
                key.endswith(":low") or key.endswith(":medium")
                for key in selected_failures
            ),
            "failures_suggest_box_or_stage0_over_ownership": bool(selected_failures),
        },
        "recommended_next_action": (
            "derive unified strategy arbitration candidates from visible feature rules"
            if normalized_shortlist_success > raw_top_success
            else "collect broader arbitration dataset before causal arbitration"
        ),
    }


def _write_markdown(probe: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stage 7 Unified Strategy Arbitration Probe",
        "",
        "This is non-causal analysis. It does not alter runtime routing.",
        "",
        "## Summary",
        "",
        f"- dataset states: `{probe['dataset_state_count']}`",
        f"- labeled states: `{probe['labeled_state_count']}`",
        f"- raw global top conversion rate: `{probe['raw_global_top_conversion_rate']:.3f}`",
        f"- provider-local rank1 oracle coverage: `{probe['provider_local_rank1_oracle_coverage']:.3f}`",
        f"- provider-local normalization beats raw: `{probe['answers']['provider_local_normalization_outperforms_raw_global_score']}`",
        f"- box relevance explains some failures: `{probe['answers']['box_area_relevance_explains_some_failures']}`",
        f"- next action: `{probe['recommended_next_action']}`",
        "",
        "## Provider Outcomes",
        "",
    ]
    for key, value in sorted(probe["provider_outcome_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Visible Feature Rules", ""])
    for item in probe["best_visible_feature_rules"][:8]:
        lines.append(
            f"- `{item['feature']}={item['value']}` -> `{item['predicted_converting_provider']}` "
            f"(support `{item['support']}`)"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build non-causal Stage 7 unified strategy arbitration dataset")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--trajectory-seed", type=Path, required=True)
    parser.add_argument("--closed-loop-replay", type=Path, action="append", default=[])
    parser.add_argument("--providers", default=",".join(DEFAULT_PROVIDERS))
    parser.add_argument("--max-states", type=int, default=8)
    parser.add_argument("--max-labels-per-state", type=int, default=4)
    parser.add_argument("--horizon", type=int, default=40)
    parser.add_argument("--max-ticks", type=int, default=40)
    parser.add_argument("--label-trace-mode", choices=["none", "failures", "all"], default="none")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--dataset-output", type=Path, required=True)
    parser.add_argument("--probe-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    providers = [item.strip() for item in args.providers.split(",") if item.strip()]
    dataset = build_dataset(
        topology_path=args.topology,
        trajectory_seed_path=args.trajectory_seed,
        replay_paths=list(args.closed_loop_replay),
        providers=providers,
        max_states=args.max_states,
        max_labels_per_state=args.max_labels_per_state,
        horizon=args.horizon,
        max_ticks=args.max_ticks,
        label_trace_mode=args.label_trace_mode,
        seed=args.seed,
    )
    probe = run_probe(dataset)
    args.dataset_output.parent.mkdir(parents=True, exist_ok=True)
    args.dataset_output.write_text(json.dumps(dataset, indent=2) + "\n", encoding="utf-8")
    args.probe_output.write_text(json.dumps(probe, indent=2) + "\n", encoding="utf-8")
    _write_markdown(probe, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(probe, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
