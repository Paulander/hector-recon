#!/usr/bin/env python3
"""Run Stage 7 2cc protocol Phase 0/1 checks.

Phase 0 is static sanity: verify sources are non-causal, runtime-forbidden
terms are present, and the protocol remains sandbox-only.

Phase 1 is a frozen-weight probe: score the 2cc CandidateMoveFrames with the
existing non-promoted visible-term model, without training or changing runtime.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import chess


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _move_features(fen: str, frame: dict[str, Any]) -> set[str]:
    move_uci = str(frame.get("move_uci") or "")
    board = chess.Board(fen)
    move = chess.Move.from_uci(move_uci)
    piece = board.piece_at(move.from_square)
    feats: set[str] = set()
    if piece:
        feats.add(f"piece:{piece.symbol().upper()}")
        if piece.piece_type == chess.KING:
            feats.add("piece_type:king")
        if piece.piece_type == chess.ROOK:
            feats.add("piece_type:rook")
    from_file = chess.square_file(move.from_square)
    from_rank = chess.square_rank(move.from_square)
    to_file = chess.square_file(move.to_square)
    to_rank = chess.square_rank(move.to_square)
    df = to_file - from_file
    dr = to_rank - from_rank
    for term in (
        f"piece.{piece.symbol().upper() if piece else 'unknown'}",
        f"from_file.{from_file}",
        f"from_rank.{from_rank}",
        f"to_file.{to_file}",
        f"to_rank.{to_rank}",
        f"delta_file_sign.{0 if df == 0 else 1 if df > 0 else -1}",
        f"delta_rank_sign.{0 if dr == 0 else 1 if dr > 0 else -1}",
        f"delta_file_abs.{abs(df)}",
        f"delta_rank_abs.{abs(dr)}",
    ):
        feats.add(f"coord:{term}")
    for term in frame.get("move_shape_terms") or []:
        feats.add(f"move_shape:{term}")
    for term in frame.get("post_move_terms") or []:
        feats.add(f"post_move:{term}")
    return feats


def _dtm_by_move(alignment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = {}
    for item in alignment.get("labeled_candidate_frames") or []:
        if isinstance(item, dict) and item.get("move"):
            rows[str(item["move"])] = {
                "child_dtm": item.get("child_dtm"),
                "forces_mate": bool(item.get("forces_mate", False)),
                "optimal_dtm_move": bool(item.get("optimal_dtm_move", False)),
            }
    return rows


def evaluate_phase01(
    *,
    protocol_path: Path,
    alignment_path: Path,
    candidate_frames_path: Path,
    model_path: Path,
) -> dict[str, Any]:
    protocol = _load_json(protocol_path)
    alignment = _load_json(alignment_path)
    frames_payload = _load_json(candidate_frames_path)
    model = _load_json(model_path)

    candidate = dict(protocol.get("structural_candidate", {}) or {})
    proposed = dict(candidate.get("proposed_change", {}) or {})
    forbidden = set(proposed.get("runtime_forbidden_terms") or [])
    model_forbidden = set(model.get("runtime_forbidden_terms") or [])
    phase0_checks = {
        "protocol_non_causal": protocol.get("causal_status") == "non_causal",
        "candidate_non_causal": candidate.get("causal_status") == "non_causal",
        "candidate_not_promoted": candidate.get("promotion_status") != "promoted",
        "tablebase_forbidden": "tablebase_lookup" in forbidden | model_forbidden,
        "dtm_runtime_forbidden": "dtm_oracle_move_selection" in forbidden | model_forbidden,
        "state_hash_forbidden": "state_hash_exception" in forbidden | model_forbidden,
        "model_non_promoted": model.get("causal_status") == "sandbox_model_non_promoted",
        "model_default_off": "do_not_enable_by_default" in set(model.get("constraints") or []),
    }

    records = [
        record
        for record in frames_payload.get("records") or []
        if isinstance(record, dict)
    ]
    if not records:
        raise ValueError("candidate frame audit contains no records")
    record = records[0]
    fen = str(record.get("fen") or alignment.get("target_fen") or "")
    weights = {str(k): float(v) for k, v in (model.get("weights") or {}).items()}
    bias = float(model.get("bias", 0.0) or 0.0)
    dtm_rows = _dtm_by_move(alignment)
    scored = []
    for frame in record.get("candidate_move_frames") or []:
        if not isinstance(frame, dict):
            continue
        move = str(frame.get("move_uci") or "")
        feats = _move_features(fen, frame)
        score = bias + sum(weights.get(term, 0.0) for term in feats)
        score = max(-80.0, min(80.0, score))
        probability = 1.0 / (1.0 + math.exp(-score))
        scored.append(
            {
                "move": move,
                "score": score,
                "probability": probability,
                "feature_count": len(feats),
                "matched_weighted_terms": sorted(term for term in feats if term in weights),
                **dtm_rows.get(move, {}),
            }
        )
    scored.sort(key=lambda item: (item["score"], item["move"]), reverse=True)
    selected = scored[0] if scored else {}
    optimal_moves = sorted(
        item["move"]
        for item in scored
        if item.get("optimal_dtm_move")
    )
    selected_is_winning = bool(selected.get("forces_mate", False))
    selected_is_optimal = bool(selected.get("optimal_dtm_move", False))
    phase1_status = (
        "frozen_model_selects_optimal_dtm_move"
        if selected_is_optimal
        else "frozen_model_selects_winning_nonoptimal_move"
        if selected_is_winning
        else "frozen_model_selects_nonwinning_or_unlabeled_move"
    )
    return {
        "schema_version": "stage7_2cc_protocol_phase01_eval.v1",
        "causal_status": "non_causal",
        "runtime_behavior_changed": False,
        "sources": {
            "protocol": str(protocol_path),
            "alignment": str(alignment_path),
            "candidate_frames": str(candidate_frames_path),
            "model": str(model_path),
        },
        "phase0_static_sanity": {
            "checks": phase0_checks,
            "passed": all(phase0_checks.values()),
        },
        "phase1_frozen_weight_probe": {
            "model_schema": model.get("schema_version"),
            "provider_skill_id": model.get("provider_skill_id"),
            "selected_move": selected.get("move"),
            "selected_score": selected.get("score"),
            "selected_forces_mate": selected_is_winning,
            "selected_optimal_dtm_move": selected_is_optimal,
            "selected_child_dtm": selected.get("child_dtm"),
            "optimal_dtm_moves": optimal_moves,
            "status": phase1_status,
            "top_scored_moves": scored[:10],
        },
        "candidate_status_update": {
            "candidate_id": candidate.get("candidate_id"),
            "phase0_status": "passed" if all(phase0_checks.values()) else "failed",
            "phase1_status": phase1_status,
            "diagnosis": (
                "frozen_visible_term_model_has_expressive_first_step"
                if selected_is_winning
                else "frozen_visible_term_model_needs_candidate_local_calibration"
            ),
            "next_action": (
                "run default-off sandbox candidate-local probe"
                if selected_is_winning
                else "adjust bounded plasticity protocol before sandbox runtime"
            ),
            "causal_status": "non_causal",
            "promotion_status": "sandbox_protocol_phase01_complete",
        },
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    phase0 = payload["phase0_static_sanity"]
    phase1 = payload["phase1_frozen_weight_probe"]
    update = payload["candidate_status_update"]
    lines = [
        "# Stage 7 2cc Protocol Phase 0/1",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Runtime behavior changed: `{payload['runtime_behavior_changed']}`",
        "",
        "## Phase 0",
        "",
        f"Passed: `{phase0['passed']}`",
        "",
        "## Phase 1",
        "",
        f"Model: `{phase1['model_schema']}`",
        f"Selected move: `{phase1['selected_move']}`",
        f"Selected child DTM: `{phase1['selected_child_dtm']}`",
        f"Selected winning: `{phase1['selected_forces_mate']}`",
        f"Selected optimal: `{phase1['selected_optimal_dtm_move']}`",
        f"Status: `{phase1['status']}`",
        "",
        "## Candidate Update",
        "",
        f"Candidate: `{update['candidate_id']}`",
        f"Diagnosis: `{update['diagnosis']}`",
        f"Next action: `{update['next_action']}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--alignment", type=Path, required=True)
    parser.add_argument("--candidate-frames", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = evaluate_phase01(
        protocol_path=args.protocol,
        alignment_path=args.alignment,
        candidate_frames_path=args.candidate_frames,
        model_path=args.model,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
