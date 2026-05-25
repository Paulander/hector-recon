#!/usr/bin/env python3
"""Bounded symmetry-stratified validation for the Stage 4 ranking-gap motif."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

import chess


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_JSON = ROOT / "reports/krk_stage4_stratified_contrast_validation_v0.json"
OUTPUT_MD = ROOT / "reports/krk_stage4_stratified_contrast_validation_v0.md"

SCHEMA_VERSION = "krk_stage4_stratified_contrast_validation.v0"
TARGET_FEN = "1R6/1K6/8/k7/8/8/8/8 w - - 0 1"
TARGET_SELECTED_MOVE = "b8h8"


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


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _identity(square: chess.Square) -> chess.Square:
    return square


def _mirror_files(square: chess.Square) -> chess.Square:
    return chess.square(7 - chess.square_file(square), chess.square_rank(square))


def _mirror_ranks(square: chess.Square) -> chess.Square:
    return chess.square(chess.square_file(square), 7 - chess.square_rank(square))


def _rotate_180(square: chess.Square) -> chess.Square:
    return chess.square(7 - chess.square_file(square), 7 - chess.square_rank(square))


TRANSFORMS: list[tuple[str, Callable[[chess.Square], chess.Square]]] = [
    ("identity", _identity),
    ("mirror_files", _mirror_files),
    ("mirror_ranks", _mirror_ranks),
    ("rotate_180", _rotate_180),
]


def transform_board_fen(fen: str, transform: Callable[[chess.Square], chess.Square]) -> str:
    board = chess.Board(fen)
    transformed = chess.Board(None)
    for square, piece in board.piece_map().items():
        transformed.set_piece_at(transform(square), piece)
    transformed.turn = board.turn
    transformed.castling_rights = 0
    transformed.ep_square = None
    transformed.halfmove_clock = board.halfmove_clock
    transformed.fullmove_number = board.fullmove_number
    return transformed.fen()


def transform_move_uci(move_uci: str, transform: Callable[[chess.Square], chess.Square]) -> str:
    move = chess.Move.from_uci(move_uci)
    return chess.Move(transform(move.from_square), transform(move.to_square)).uci()


def _feature_terms_for_canonical_move(feature_module: Any, canonical_move: str) -> dict[str, Any]:
    try:
        return feature_module._candidate_terms(TARGET_FEN, canonical_move)
    except Exception as exc:  # pragma: no cover - defensive artifact metadata
        return {"feature_extraction_error": str(exc)}


def _variant_status(rows: list[dict[str, Any]], selected_move: str) -> dict[str, Any]:
    selected = next(row for row in rows if row["first_move"] == selected_move)
    converting = [row for row in rows if row["result"] == "mate"]
    if selected["result"] != "mate" and converting:
        status = "first_move_ranking_gap_reproduced"
    elif selected["result"] == "mate":
        status = "selected_move_converts"
    else:
        status = "no_converting_first_move_found"
    return {
        "status": status,
        "selected_move": selected_move,
        "selected_result": selected["result"],
        "converting_first_move_count": len(converting),
        "converting_first_moves": [row["first_move"] for row in converting],
        "converting_canonical_moves": [row["canonical_move"] for row in converting],
    }


def build_payload() -> dict[str, Any]:
    sequence = _load_module(
        "review_krk_stage4_sequence_candidates_v0",
        "scripts/review_krk_stage4_sequence_candidates_v0.py",
    )
    features = _load_module(
        "review_krk_stage4_first_move_features_v0",
        "scripts/review_krk_stage4_first_move_features_v0.py",
    )
    diag = sequence._load_landmark_progress_module()
    variants = []
    all_rows = []
    for variant_id, transform in TRANSFORMS:
        fen = transform_board_fen(TARGET_FEN, transform)
        selected_move = transform_move_uci(TARGET_SELECTED_MOVE, transform)
        legal_moves = sequence.legal_first_moves(fen)
        rows = []
        for move in legal_moves:
            result = sequence.run_candidate_for_fen(move, fen=fen, diag=diag)
            canonical_move = transform_move_uci(move, transform)
            row = {
                "variant_id": variant_id,
                "fen": fen,
                "first_move": move,
                "canonical_move": canonical_move,
                "selected_analog": move == selected_move,
                "result": result["result"],
                "total_plies_including_forced_first_move": result[
                    "total_plies_including_forced_first_move"
                ],
                "first_reply": result.get("first_reply", {}).get("move")
                if isinstance(result.get("first_reply"), dict)
                else None,
                "first_successor_skill": result.get("first_successor_skill"),
                "canonical_features": _feature_terms_for_canonical_move(
                    features,
                    canonical_move,
                ),
            }
            rows.append(row)
            all_rows.append(row)
        variants.append({
            "variant_id": variant_id,
            "fen": fen,
            "selected_move": selected_move,
            "legal_first_move_count": len(legal_moves),
            "status": _variant_status(rows, selected_move),
            "rows": rows,
        })
    variant_status_counts = _count_by(
        [variant["status"]["status"] for variant in variants]
    )
    gap_variant_count = variant_status_counts.get("first_move_ranking_gap_reproduced", 0)
    if gap_variant_count == len(variants):
        decision = "stage4_stratified_contrast_validation_supports_first_move_ranking_gap"
        recommended_next = "stage4_stratified_first_move_contrast_review_packet"
    elif gap_variant_count:
        decision = "stage4_stratified_contrast_mixed_topology_or_harness_asymmetry"
        recommended_next = "review_asymmetry_before_runtime"
    else:
        decision = "stage4_stratified_contrast_does_not_generalize"
        recommended_next = "keep_stage4_known_residual_guardrail"
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_symmetry_stratified_forced_first_move_validation",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/krk_stage4_sequence_candidate_review_v0.json",
            "reports/krk_stage4_first_move_feature_review_v0.json",
        ],
        "target": {
            "fen": TARGET_FEN,
            "selected_move": TARGET_SELECTED_MOVE,
            "validation_scope": "identity_plus_file_rank_symmetry_variants",
        },
        "summary": {
            "variant_count": len(variants),
            "candidate_row_count": len(all_rows),
            "variant_status_counts": variant_status_counts,
            "gap_variant_count": gap_variant_count,
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "runtime_behavior_changed": False,
        },
        "variants": variants,
        "decision": {
            "status": decision,
            "recommended_next_step": recommended_next,
            "runtime_changes_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "interpretation": {
            "runtime_ready": False,
            "selector_training_supported": False,
            "notes": [
                "This validates geometry-transformed variants only; it is not broad random KRK evidence.",
                "Forced-first-move conversion labels remain capacity/contrast diagnostics, not runtime ownership labels.",
                "A future causal change would still require a review packet, default-off sandbox, and guardrails.",
            ],
        },
    }


def _count_by(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def write_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Stage 4 Stratified Contrast Validation v0",
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
        f"- variant_count: `{payload['summary']['variant_count']}`",
        f"- candidate_row_count: `{payload['summary']['candidate_row_count']}`",
        f"- variant_status_counts: `{payload['summary']['variant_status_counts']}`",
        f"- gap_variant_count: `{payload['summary']['gap_variant_count']}`",
        "",
        "## Variants",
        "",
        "| variant | selected_move | selected_result | converting_count | status |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for variant in payload["variants"]:
        status = variant["status"]
        lines.append(
            "| "
            f"{variant['variant_id']} | {status['selected_move']} | "
            f"{status['selected_result']} | {status['converting_first_move_count']} | "
            f"{status['status']} |"
        )
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- This is non-causal symmetry-stratified validation, not selector training.",
        "- No runtime selector, score change, exact-state patch, Stage 7 promotion, or Stage 8 training is authorized.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "decision": payload["decision"]["status"],
        "variant_status_counts": payload["summary"]["variant_status_counts"],
        "candidate_row_count": payload["summary"]["candidate_row_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
