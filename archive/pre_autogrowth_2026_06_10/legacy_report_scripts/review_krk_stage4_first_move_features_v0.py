#!/usr/bin/env python3
"""Non-causal feature review for the isolated Stage 4 first-move ranking gap."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import chess


ROOT = Path(__file__).resolve().parents[1]
INPUT_JSON = ROOT / "reports/krk_stage4_sequence_candidate_review_v0.json"
OUTPUT_JSON = ROOT / "reports/krk_stage4_first_move_feature_review_v0.json"
OUTPUT_MD = ROOT / "reports/krk_stage4_first_move_feature_review_v0.md"

SCHEMA_VERSION = "krk_stage4_first_move_feature_review.v0"


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


def _square_features(square: chess.Square) -> dict[str, Any]:
    return {
        "file": chess.square_file(square),
        "rank": chess.square_rank(square),
        "square": chess.square_name(square),
    }


def _chebyshev(a: chess.Square, b: chess.Square) -> int:
    return max(
        abs(chess.square_file(a) - chess.square_file(b)),
        abs(chess.square_rank(a) - chess.square_rank(b)),
    )


def _candidate_terms(fen: str, move_uci: str) -> dict[str, Any]:
    board = chess.Board(fen)
    move = chess.Move.from_uci(move_uci)
    piece = board.piece_at(move.from_square)
    if piece is None:
        raise ValueError(f"no piece at {move.from_square} for {move_uci}")
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    rook_square = next(
        (sq for sq, p in board.piece_map().items() if p.symbol() == "R"),
        None,
    )
    assert white_king is not None
    assert black_king is not None
    assert rook_square is not None
    from_feat = _square_features(move.from_square)
    to_feat = _square_features(move.to_square)
    terms = {
        "piece": "rook" if piece.piece_type == chess.ROOK else "king",
        "from_square": from_feat["square"],
        "to_square": to_feat["square"],
        "to_file": to_feat["file"],
        "to_rank": to_feat["rank"],
        "dx": to_feat["file"] - from_feat["file"],
        "dy": to_feat["rank"] - from_feat["rank"],
        "move_distance": _chebyshev(move.from_square, move.to_square),
        "target_distance_to_white_king": _chebyshev(move.to_square, white_king),
        "target_distance_to_black_king": _chebyshev(move.to_square, black_king),
        "target_edge_distance": min(
            to_feat["file"],
            7 - to_feat["file"],
            to_feat["rank"],
            7 - to_feat["rank"],
        ),
    }
    if piece.piece_type == chess.ROOK:
        terms.update({
            "rook_rank8_destination": to_feat["rank"] == 7,
            "rook_mid_rank8_cut_candidate": to_feat["rank"] == 7 and to_feat["file"] in {2, 3, 4},
            "rook_far_rank8_drift_candidate": to_feat["rank"] == 7 and to_feat["file"] in {0, 5, 6, 7},
            "rook_destination_file_distance_from_black_king_file": abs(
                to_feat["file"] - chess.square_file(black_king)
            ),
            "rook_destination_file_distance_from_white_king_file": abs(
                to_feat["file"] - chess.square_file(white_king)
            ),
        })
    else:
        terms.update({
            "king_move": True,
            "king_destination_a7": to_feat["square"] == "a7",
            "king_destination_rank7_or_8": to_feat["rank"] >= 6,
            "king_destination_c_file": to_feat["file"] == 2,
        })
    return terms


def _row_with_features(candidate_row: dict[str, Any], fen: str) -> dict[str, Any]:
    terms = _candidate_terms(fen, candidate_row["first_move"])
    return {
        "first_move": candidate_row["first_move"],
        "result": candidate_row["result"],
        "outcome_bucket": "converts" if candidate_row["result"] == "mate" else "fails_h40",
        "total_plies_including_forced_first_move": candidate_row[
            "total_plies_including_forced_first_move"
        ],
        "first_reply": (candidate_row.get("first_reply") or {}).get("move"),
        "first_successor_skill": candidate_row.get("first_successor_skill"),
        "features": terms,
    }


def _boolean_feature_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = sorted(
        {
            key
            for row in rows
            for key, value in row["features"].items()
            if isinstance(value, bool)
        }
    )
    summary = []
    for key in keys:
        yes_rows = [row for row in rows if row["features"].get(key) is True]
        no_rows = [row for row in rows if row["features"].get(key) is not True]
        if not yes_rows:
            continue
        yes_success = sum(1 for row in yes_rows if row["outcome_bucket"] == "converts")
        no_success = sum(1 for row in no_rows if row["outcome_bucket"] == "converts")
        summary.append({
            "feature": key,
            "true_count": len(yes_rows),
            "true_success_count": yes_success,
            "true_failure_count": len(yes_rows) - yes_success,
            "true_success_precision": yes_success / len(yes_rows),
            "false_count": len(no_rows),
            "false_success_count": no_success,
            "false_failure_count": len(no_rows) - no_success,
            "single_state_only": True,
        })
    return sorted(
        summary,
        key=lambda item: (
            -abs(item["true_success_precision"] - 0.5),
            item["feature"],
        ),
    )


def _categorical_feature_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = ["piece", "first_reply", "first_successor_skill"]
    summary = []
    for key in keys:
        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            value = row.get(key)
            if value is None:
                value = row["features"].get(key)
            buckets[str(value)].append(row)
        summary.append({
            "feature": key,
            "buckets": {
                value: {
                    "count": len(bucket_rows),
                    "success_count": sum(
                        1 for row in bucket_rows if row["outcome_bucket"] == "converts"
                    ),
                    "failure_count": sum(
                        1 for row in bucket_rows if row["outcome_bucket"] != "converts"
                    ),
                }
                for value, bucket_rows in sorted(buckets.items())
            },
            "single_state_only": True,
        })
    return summary


def _interpretation(boolean_summary: list[dict[str, Any]]) -> dict[str, Any]:
    exact_success = [
        row
        for row in boolean_summary
        if row["true_success_count"] > 0 and row["true_failure_count"] == 0
    ]
    exact_failure = [
        row
        for row in boolean_summary
        if row["true_failure_count"] > 0 and row["true_success_count"] == 0
    ]
    return {
        "primary": "single_state_visible_first_move_contrast_found",
        "support": [
            "The selected failed move is separable from several converting first moves by simple visible move-shape terms.",
            "The evidence is one repeated state only, so these terms are not runtime-ready and should not be treated as general selector labels.",
            "The safest next step is synthetic/stratified contrast validation or a sequence-policy review, not an exact-state patch.",
        ],
        "candidate_positive_terms": [row["feature"] for row in exact_success],
        "candidate_failure_terms": [row["feature"] for row in exact_failure],
        "runtime_ready": False,
    }


def build_payload(candidate_review: dict[str, Any] | None = None) -> dict[str, Any]:
    candidate_review = candidate_review or json.loads(INPUT_JSON.read_text(encoding="utf-8"))
    fen = candidate_review["target"]["fen"]
    rows = [
        _row_with_features(row, fen)
        for row in candidate_review.get("candidate_results", [])
    ]
    boolean_summary = _boolean_feature_summary(rows)
    categorical_summary = _categorical_feature_summary(rows)
    interpretation = _interpretation(boolean_summary)
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_single_state_feature_review",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": ["reports/krk_stage4_sequence_candidate_review_v0.json"],
        "target": dict(candidate_review["target"]),
        "summary": {
            "row_count": len(rows),
            "success_count": sum(1 for row in rows if row["outcome_bucket"] == "converts"),
            "failure_count": sum(1 for row in rows if row["outcome_bucket"] != "converts"),
            "single_state_only": True,
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "runtime_behavior_changed": False,
        },
        "candidate_feature_rows": rows,
        "boolean_feature_summary": boolean_summary,
        "categorical_feature_summary": categorical_summary,
        "interpretation": interpretation,
        "decision": {
            "status": "stage4_first_move_feature_contrast_found_single_state",
            "recommended_next_step": "synthetic_or_stratified_stage4_contrast_validation",
            "runtime_changes_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "explicitly_forbidden": [
            "exact_state_runtime_patch",
            "selector_training_from_single_state_terms",
            "broad_stage0_penalty",
            "runtime_score_change",
            "stage7_promotion",
            "stage8_training",
        ],
    }


def write_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Stage 4 First-Move Feature Review v0",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "- runtime_changes_allowed: `false`",
        "- selector_training_allowed: `false`",
        "",
        "## Summary",
        "",
        f"- row_count: `{payload['summary']['row_count']}`",
        f"- success_count: `{payload['summary']['success_count']}`",
        f"- failure_count: `{payload['summary']['failure_count']}`",
        "- single_state_only: `true`",
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["interpretation"]["support"])
    lines.extend([
        "",
        "## Candidate Terms",
        "",
        f"- candidate_positive_terms: `{payload['interpretation']['candidate_positive_terms']}`",
        f"- candidate_failure_terms: `{payload['interpretation']['candidate_failure_terms']}`",
        "",
        "## Boolean Feature Summary",
        "",
        "| feature | true_count | true_success | true_failure | true_success_precision |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for row in payload["boolean_feature_summary"]:
        lines.append(
            "| "
            f"{row['feature']} | {row['true_count']} | "
            f"{row['true_success_count']} | {row['true_failure_count']} | "
            f"{row['true_success_precision']:.3f} |"
        )
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- These are single-state visible contrast terms, not runtime terminals or selector labels.",
        "- No exact-state patch, selector training, score change, Stage 7 promotion, or Stage 8 training is authorized.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "decision": payload["decision"]["status"],
        "row_count": payload["summary"]["row_count"],
        "success_count": payload["summary"]["success_count"],
        "failure_count": payload["summary"]["failure_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
