#!/usr/bin/env python3
"""Review legal first-move candidates for the isolated Stage 4 caveat state.

This script is deliberately non-causal. It forces one legal first move from the
known Stage 4 caveat FEN, then lets the existing KRK profile continue normally
under a bounded h40 continuation label. The output classifies whether the caveat
looks like a first-move ranking gap, a follow-up/sequence gap, or a known
residual/horizon issue. It does not train, route, score, or mutate topology.
"""

from __future__ import annotations

import importlib.util
import json
import random
import sys
from pathlib import Path
from typing import Any

import chess


ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY = (
    ROOT
    / "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1"
    / "stage6_overlay_composed/topology/krk_entry_topology.json"
)
SOURCE_REVIEW = ROOT / "reports/krk_stage4_caveat_sequence_review_v0.json"
OUTPUT_JSON = ROOT / "reports/krk_stage4_sequence_candidate_review_v0.json"
OUTPUT_MD = ROOT / "reports/krk_stage4_sequence_candidate_review_v0.md"

SCHEMA_VERSION = "krk_stage4_sequence_candidate_review.v0"
TARGET_STATE_ID = "state.44938ccb8ab7"
TARGET_FEN = "1R6/1K6/8/k7/8/8/8/8 w - - 0 1"
TARGET_SELECTED_MOVE = "b8h8"
LABEL = "edge_trap_wrong_tempo"
MAX_TOTAL_PLIES = 40


COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


PLAYOUT_KWARGS = {
    "label": LABEL,
    "stage_filter": None,
    "max_plies": MAX_TOTAL_PLIES - 1,
    "black_policy": "adversarial",
    "trace": True,
    "trace_max_plies": 8,
    "max_ticks": 200,
    "suggestion_limit": 10,
    "successor_affordance_layer_enabled": True,
    "successor_role_license_enabled": True,
    "successor_stage0_drift_penalty": 6.0,
    "successor_role_scoped_move_shape_enabled": True,
    "successor_role_scoped_move_shape_bonus": 0.05,
    "stagnation_breaker_enabled": True,
    "stagnation_breaker_bonus": 0.5,
    "stagnation_breaker_king_support_bonus": 2.0,
    "post_break_continuation_enabled": True,
    "post_break_continuation_bonus": 0.25,
    "early_stop_stable_suggestions": 2,
    "enable_diagnostic_caches": True,
    "initial_white_moves": 1,
}


def _load_landmark_progress_module():
    path = ROOT / "scripts/test_krk_landmark_progress.py"
    spec = importlib.util.spec_from_file_location("krk_landmark_progress_diag", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load diagnostic module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def legal_first_moves(fen: str = TARGET_FEN) -> list[str]:
    board = chess.Board(fen)
    return [move.uci() for move in board.legal_moves]


def _first_successor_skill(result: dict[str, Any]) -> str | None:
    successor = result.get("first_successor")
    if not isinstance(successor, dict):
        return None
    engine = successor.get("engine")
    if not isinstance(engine, dict):
        return None
    move = engine.get("move")
    for suggestion in engine.get("suggestions", []) or []:
        if suggestion.get("move") != move:
            continue
        skill = suggestion.get("skill_id")
        if skill:
            return str(skill)
        source = suggestion.get("source")
        if source:
            return str(source)
    return None


def _compact_result(diag: Any, move_uci: str, result: dict[str, Any]) -> dict[str, Any]:
    compact_trace = diag._compact_playout_trace(result.get("trace", []) or [])
    first_successor_skill = _first_successor_skill(result)
    if first_successor_skill is None:
        first_successor_skill = next(
            (
                str(event.get("selected_skill"))
                for event in compact_trace
                if event.get("turn") == "white" and event.get("selected_skill")
            ),
            None,
        )
    return {
        "first_move": move_uci,
        "post_first_move_fen": result.get("trace", [{}])[0].get("fen")
        if result.get("trace")
        else None,
        "result": result.get("result"),
        "remaining_plies": int(result.get("plies", 0) or 0),
        "total_plies_including_forced_first_move": int(result.get("plies", 0) or 0) + 1,
        "first_reply": result.get("first_reply"),
        "first_successor_skill": first_successor_skill,
        "final_fen": result.get("final_fen"),
        "final_mate_in_one_available": bool(result.get("final_mate_in_one_available", False)),
        "stagnation_summary": result.get("stagnation_summary"),
        "trace": compact_trace,
        "trace_truncated_events": int(result.get("trace_truncated_events", 0) or 0),
    }


def run_candidate(move_uci: str, *, diag: Any) -> dict[str, Any]:
    board = chess.Board(TARGET_FEN)
    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        raise ValueError(f"{move_uci} is not legal in {TARGET_FEN}")
    board.push(move)
    graph = diag.build_graph_from_topology(TOPOLOGY)
    engine = diag.ReConEngine(graph)
    result = diag.play_to_mate(
        graph,
        engine,
        board,
        random.Random(7),
        **PLAYOUT_KWARGS,
    )
    return _compact_result(diag, move_uci, result)


def classify_candidate_results(candidate_results: list[dict[str, Any]]) -> dict[str, Any]:
    selected = next(
        row for row in candidate_results if row["first_move"] == TARGET_SELECTED_MOVE
    )
    converting = [row for row in candidate_results if row["result"] == "mate"]
    selected_converts = selected["result"] == "mate"
    selected_fails = selected["result"] != "mate"
    if selected_fails and converting:
        primary = "stage4_first_move_ranking_gap"
        recommended_next = "non_causal_stage4_first_move_feature_review"
    elif selected_fails and not converting:
        primary = "stage4_sequence_followup_or_horizon_gap"
        recommended_next = "sequence_policy_review_or_keep_stage4_known_residual"
    elif selected_converts:
        primary = "stage4_original_trace_or_horizon_mismatch"
        recommended_next = "harness_consistency_review"
    else:
        primary = "stage4_known_residual_keep_guardrail"
        recommended_next = "keep_stage4_known_residual_guardrail"

    return {
        "primary": primary,
        "recommended_next_step": recommended_next,
        "selected_first_move_result": selected["result"],
        "selected_first_move_total_plies": selected[
            "total_plies_including_forced_first_move"
        ],
        "converting_first_move_count": len(converting),
        "converting_first_moves": [row["first_move"] for row in converting],
        "non_converting_first_move_count": len(candidate_results) - len(converting),
        "support": _classification_support(primary, selected, converting),
    }


def _classification_support(
    primary: str,
    selected: dict[str, Any],
    converting: list[dict[str, Any]],
) -> list[str]:
    if primary == "stage4_first_move_ranking_gap":
        return [
            f"selected first move {TARGET_SELECTED_MOVE} remains {selected['result']}",
            f"{len(converting)} legal first moves convert under the same bounded continuation",
            "the target is a repeated single-state caveat, so this is not enough for a broad selector",
        ]
    if primary == "stage4_sequence_followup_or_horizon_gap":
        return [
            f"selected first move {TARGET_SELECTED_MOVE} remains {selected['result']}",
            "no legal first move converted under the same bounded continuation",
            "the gap is more likely continuation policy, horizon, or broader sequence control",
        ]
    if primary == "stage4_original_trace_or_horizon_mismatch":
        return [
            f"selected first move {TARGET_SELECTED_MOVE} converted in forced-first replay",
            "the prior failure trace should be checked for harness or horizon mismatch",
        ]
    return ["no actionable first-move ranking evidence was found"]


def build_payload() -> dict[str, Any]:
    diag = _load_landmark_progress_module()
    source_review = json.loads(SOURCE_REVIEW.read_text(encoding="utf-8"))
    moves = legal_first_moves()
    candidate_results = [run_candidate(move, diag=diag) for move in moves]
    classification = classify_candidate_results(candidate_results)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_forced_first_move_sequence_review",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            str(SOURCE_REVIEW.relative_to(ROOT)),
            str(TOPOLOGY.relative_to(ROOT)),
        ],
        "target": {
            "state_id": TARGET_STATE_ID,
            "fen": TARGET_FEN,
            "selected_move": TARGET_SELECTED_MOVE,
            "label": LABEL,
            "source_primary_diagnosis": source_review.get("diagnosis", {}).get("primary"),
        },
        "harness": {
            "max_total_plies": MAX_TOTAL_PLIES,
            "remaining_plies_after_forced_first_move": MAX_TOTAL_PLIES - 1,
            "black_policy": PLAYOUT_KWARGS["black_policy"],
            "uses_runtime_dtm_or_tablebase": False,
            "forced_first_move_only": True,
            "selection_policy_changed": False,
            "score_policy_changed": False,
        },
        "summary": {
            "legal_first_move_count": len(moves),
            "candidate_result_counts": _count_by_key(candidate_results, "result"),
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "runtime_behavior_changed": False,
        },
        "classification": classification,
        "candidate_results": candidate_results,
        "decision": {
            "status": classification["primary"],
            "recommended_next_step": classification["recommended_next_step"],
            "runtime_changes_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "explicitly_forbidden": [
            "exact_state_runtime_exception",
            "stage4_runtime_patch_without_review",
            "selector_training_from_forced_first_move_labels",
            "runtime_dtm_or_tablebase_lookup",
            "stage7_promotion",
            "stage8_training",
        ],
    }
    return payload


def _count_by_key(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def write_markdown(payload: dict[str, Any]) -> str:
    target = payload["target"]
    summary = payload["summary"]
    classification = payload["classification"]
    lines = [
        "# KRK Stage 4 Sequence Candidate Review v0",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "- causal_status: `non_causal_forced_first_move_sequence_review`",
        "- runtime_changes_allowed: `false`",
        "- selector_training_allowed: `false`",
        "",
        "## Target",
        "",
        f"- state_id: `{target['state_id']}`",
        f"- fen: `{target['fen']}`",
        f"- selected_move_from_failure: `{target['selected_move']}`",
        f"- source_primary_diagnosis: `{target['source_primary_diagnosis']}`",
        "",
        "## Summary",
        "",
        f"- legal_first_move_count: `{summary['legal_first_move_count']}`",
        f"- candidate_result_counts: `{summary['candidate_result_counts']}`",
        f"- converting_first_move_count: `{classification['converting_first_move_count']}`",
        f"- converting_first_moves: `{classification['converting_first_moves']}`",
        (
            "- selected_first_move_result: "
            f"`{classification['selected_first_move_result']}`"
        ),
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {item}" for item in classification["support"])
    lines.extend([
        "",
        "## Candidate Results",
        "",
        "| first_move | result | total_plies | first_reply | first_successor_skill |",
        "| --- | --- | ---: | --- | --- |",
    ])
    for row in payload["candidate_results"]:
        first_reply = row.get("first_reply") or {}
        lines.append(
            "| "
            f"{row['first_move']} | {row['result']} | "
            f"{row['total_plies_including_forced_first_move']} | "
            f"{first_reply.get('move')} | {row.get('first_successor_skill')} |"
        )
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- These forced-first-move labels are offline diagnostics, not ownership labels.",
        "- No runtime selector, score change, direct routing, topology mutation, Stage 7 promotion, or Stage 8 training is authorized.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "decision": payload["decision"]["status"],
        "legal_first_move_count": payload["summary"]["legal_first_move_count"],
        "candidate_result_counts": payload["summary"]["candidate_result_counts"],
    }, indent=2))


if __name__ == "__main__":
    main()
