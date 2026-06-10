#!/usr/bin/env python3
"""Build non-causal Stage 7 post-box continuation training seeds.

The input is a KRK DTM oracle probe. The output is offline supervision for a
future sandbox overlay. It is not a gameplay policy and must not be loaded by
runtime routing.
"""

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


def _move_record(board: chess.Board, item: dict[str, Any], *, best_dtm: int | None, horizon: int) -> dict[str, Any]:
    move = chess.Move.from_uci(str(item["move"]))
    piece = board.piece_at(move.from_square)
    plies = item.get("plies_to_mate_if_chosen")
    if plies is None and item.get("dtm_after_move") is not None:
        plies = int(item["dtm_after_move"]) + 1
    is_winning = bool(item.get("forces_mate", False))
    is_optimal = bool(isinstance(plies, int) and best_dtm is not None and int(plies) == int(best_dtm))
    return {
        "move": move.uci(),
        "piece": piece.symbol().upper() if piece else None,
        "label": 1 if is_winning and isinstance(plies, int) and int(plies) <= int(horizon) else 0,
        "target_class": (
            "optimal_dtm_move"
            if is_optimal
            else "winning_within_horizon"
            if is_winning and isinstance(plies, int) and int(plies) <= int(horizon)
            else "not_selected_for_seed"
        ),
        "plies_to_mate_if_chosen": plies,
        "is_king_move": bool(piece and piece.piece_type == chess.KING),
        "is_rook_move": bool(piece and piece.piece_type == chess.ROOK),
        "is_check": bool(item.get("is_check", False)),
        "source_terms": [
            "krk_dtm_oracle_offline_label",
            "post_box_unresolved_family",
            "do_not_use_tablebase_at_runtime",
        ],
    }


def build_training_seed(
    *,
    oracle_path: Path,
    horizon: int = 40,
    max_positive_moves_per_state: int = 6,
) -> dict[str, Any]:
    oracle = _load_json(oracle_path)
    examples: list[dict[str, Any]] = []
    for record in oracle.get("records", []) or []:
        if not isinstance(record, dict):
            continue
        fen = str(record.get("fen") or "")
        if not fen:
            continue
        board = chess.Board(fen)
        best = list(record.get("best_winning_moves", []) or [])
        best_plies = [
            int(item["plies_to_mate_if_chosen"])
            for item in best
            if isinstance(item.get("plies_to_mate_if_chosen"), int)
        ]
        best_dtm = min(best_plies) if best_plies else None
        legal = [
            _move_record(board, item, best_dtm=best_dtm, horizon=horizon)
            for item in (record.get("legal_moves", []) or [])
            if isinstance(item, dict) and item.get("move")
        ]
        positives = [
            item
            for item in legal
            if item["label"] == 1 and item["target_class"] == "optimal_dtm_move"
        ]
        if not positives:
            positives = [item for item in legal if item["label"] == 1]
        positives = sorted(
            positives,
            key=lambda item: (
                int(item.get("plies_to_mate_if_chosen") or 10_000),
                item["move"],
            ),
        )[:max_positive_moves_per_state]
        examples.append({
            "schema_version": "stage7_post_box_training_seed_example.v1",
            "causal_status": "non_causal_training_evidence",
            "target_skill": "krk.post_box_shrink_continuation",
            "source_monitor_script": "growth.monitor.stage7_dtm_oracle",
            "fen": fen,
            "state_dtm": record.get("state_dtm"),
            "validation_horizon": int(horizon),
            "positive_moves": positives,
            "legal_move_labels": legal,
            "visible_context_terms": [
                "box_shrink_reward_confirmed",
                "post_box_continuation_needed",
                "rook_safe_after_reply",
                "enemy_king_not_at_edge",
            ],
            "runtime_forbidden_terms": [
                "tablebase_lookup",
                "dtm_oracle_move_selection",
                "state_hash_exception",
            ],
        })
    return {
        "schema_version": "stage7_post_box_training_seed.v1",
        "causal_status": "non_causal_training_evidence",
        "oracle_artifact": str(oracle_path),
        "target_skill": "krk.post_box_shrink_continuation",
        "horizon": int(horizon),
        "example_count": len(examples),
        "positive_move_count": sum(len(item["positive_moves"]) for item in examples),
        "constraints": [
            "offline_training_seed_only",
            "do_not_use_dtm_or_tablebase_at_runtime",
            "do_not_promote_without_guardrails",
        ],
        "examples": examples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage 7 post-box training seed from DTM oracle")
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--jsonl-output", type=Path, default=None)
    parser.add_argument("--horizon", type=int, default=40)
    parser.add_argument("--max-positive-moves-per-state", type=int, default=6)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = build_training_seed(
        oracle_path=args.oracle,
        horizon=args.horizon,
        max_positive_moves_per_state=args.max_positive_moves_per_state,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.jsonl_output:
        args.jsonl_output.parent.mkdir(parents=True, exist_ok=True)
        with args.jsonl_output.open("w", encoding="utf-8") as fh:
            for example in payload["examples"]:
                fh.write(json.dumps(example, sort_keys=True) + "\n")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
