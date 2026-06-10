#!/usr/bin/env python3
"""Summarize non-causal KRK DTM probes into Stage 7 growth candidates.

This script deliberately does not produce a move policy. It converts oracle
evidence into StructuralCandidate-style records so the growth lab can decide
whether to sandbox/train a narrow post-box continuation provider.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import chess


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _state_suffix(fen: str) -> str:
    board = chess.Board(fen)
    key = f"{board.board_fen()} {'w' if board.turn == chess.WHITE else 'b'}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def _best_move_terms(record: dict[str, Any]) -> dict[str, Any]:
    best = list(record.get("best_winning_moves", []) or [])
    if not best:
        return {
            "best_dtm_plies": None,
            "best_moves": [],
            "best_move_piece_types": [],
        }
    fen = str(record.get("fen") or "")
    board = chess.Board(fen)
    move_terms: list[dict[str, Any]] = []
    for item in best[:10]:
        move = chess.Move.from_uci(str(item["move"]))
        piece = board.piece_at(move.from_square)
        move_terms.append({
            "move": move.uci(),
            "plies_to_mate_if_chosen": item.get("plies_to_mate_if_chosen"),
            "piece": piece.symbol().upper() if piece else None,
            "is_king_move": bool(piece and piece.piece_type == chess.KING),
            "is_rook_move": bool(piece and piece.piece_type == chess.ROOK),
            "is_check": bool(item.get("is_check", False)),
        })
    return {
        "best_dtm_plies": best[0].get("plies_to_mate_if_chosen"),
        "best_moves": move_terms,
        "best_move_piece_types": sorted(
            {
                str(item.get("piece"))
                for item in move_terms
                if item.get("piece") is not None
            }
        ),
    }


def _candidate_for_record(
    record: dict[str, Any],
    *,
    source_artifacts: list[str],
    validation_horizon: int,
) -> dict[str, Any]:
    fen = str(record.get("fen") or "")
    suffix = _state_suffix(fen)
    best_terms = _best_move_terms(record)
    state_dtm = record.get("state_dtm")
    winning_move_count = int(record.get("winning_move_count", 0) or 0)
    legal_move_count = int(record.get("legal_move_count", 0) or 0)
    within_horizon = (
        isinstance(state_dtm, int)
        and state_dtm >= 0
        and int(state_dtm) <= int(validation_horizon)
    )
    if winning_move_count > 0 and within_horizon:
        diagnosis = "dtm_won_within_validation_horizon_but_current_continuation_failed"
        candidate_type = "post_box_continuation_overlay_probe"
        governor_status = "growth_allowed"
        diagnostic_labels = [
            "provider_capacity_missing",
            "expressive_but_untrained",
            "current_provider_policy_gap",
        ]
        proposed_change = {
            "kind": "sandbox_narrow_post_box_shrink_continuation_overlay",
            "scope": "stage7_post_box_unresolved_dtm_won_family",
            "training_target": (
                "preserve KRK safety and reduce DTM/progress proxy after visible "
                "box-shrink/post-reply contexts"
            ),
            "do_not_use_tablebase_at_runtime": True,
            "suggested_visible_terms": [
                "box_shrink_reward_confirmed",
                "visible_box_area_decreased_or_preserved",
                "rook_safe_after_reply",
                "enemy_king_not_at_edge",
                "safe_followup_available",
                "king_support_or_rook_cut_followup_available",
            ],
        }
    else:
        diagnosis = "dtm_not_winning_within_validation_horizon_or_not_indexed"
        candidate_type = "horizon_or_oracle_followup_probe"
        governor_status = "needs_more_weight_training"
        diagnostic_labels = ["horizon_limited"]
        proposed_change = {
            "kind": "longer_horizon_or_oracle_validation_followup",
            "max_validation_horizon": int(validation_horizon),
        }
    return {
        "schema_version": "structural_candidate.v1",
        "candidate_id": (
            f"cand.krk.box_shrink.family_{suffix}.{candidate_type}.v1"
        ),
        "candidate_type": candidate_type,
        "source_monitor_script": "growth.monitor.stage7_dtm_oracle",
        "source_terms": [
            "current_graph_legal_first_failed",
            "forced_existing_providers_failed",
            "krk_dtm_oracle_winning_position" if winning_move_count else "krk_dtm_no_winning_move",
            "dtm_within_validation_horizon" if within_horizon else "dtm_outside_validation_horizon",
        ],
        "trigger_failure_classes": [
            "selected_successor_miscalibrated",
            "no_legal_first_conversion_under_current_graph",
            "unresolved_by_existing_forced_providers",
        ],
        "target_skill": "krk.box_shrink",
        "parent_skill": "krk.drive_to_edge",
        "state_id": f"state.{suffix}",
        "post_reply_fen": fen,
        "diagnosis": diagnosis,
        "dtm": {
            "state_dtm": state_dtm,
            "winning_move_count": winning_move_count,
            "legal_move_count": legal_move_count,
            **best_terms,
        },
        "proposed_change": proposed_change,
        "evidence_artifacts": list(source_artifacts),
        "governor_status": governor_status,
        "governor_metadata": {
            "validation_horizon": int(validation_horizon),
            "growth_monitor": "stage7_dtm_oracle",
            "growth_blocked_by_runtime_causality": True,
        },
        "topology_weight_diagnosis": {
            "frozen_weight_probe_result": "current_graph_legal_first_failed",
            "forced_oracle_probe_result": "dtm_winning_within_horizon" if within_horizon else "not_winning_within_horizon",
            "bounded_m3_warmup_result": "not_run",
            "bounded_m4_consolidation_result": "not_run",
            "candidate_locality": "stage7_post_box_shrink",
            "candidate_complexity": "narrow_overlay_probe",
        },
        "candidate_diagnostic_labels": diagnostic_labels,
        "promotion_status": "proposed",
        "causal_status": "non_causal",
        "credit": 0.0,
    }


def summarize_dtm_oracle(
    *,
    oracle_path: Path,
    validation_horizon: int = 40,
    evidence_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    payload = _load_json(oracle_path)
    records = list(payload.get("records", []) or [])
    artifacts = [str(oracle_path)] + list(evidence_artifacts or [])
    candidates = [
        _candidate_for_record(
            record,
            source_artifacts=artifacts,
            validation_horizon=validation_horizon,
        )
        for record in records
        if isinstance(record, dict)
    ]
    return {
        "schema_version": "stage7_dtm_oracle_candidate_summary.v1",
        "causal_status": "non_causal",
        "oracle_artifact": str(oracle_path),
        "validation_horizon": int(validation_horizon),
        "record_count": len(records),
        "candidate_count": len(candidates),
        "diagnosis_counts": dict(Counter(item["diagnosis"] for item in candidates)),
        "candidate_status_counts": dict(Counter(item["promotion_status"] for item in candidates)),
        "governor_status_counts": dict(Counter(item["governor_status"] for item in candidates)),
        "candidates": candidates,
    }


def _to_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 DTM Oracle Candidate Summary",
        "",
        f"- Causal status: `{payload.get('causal_status')}`",
        f"- Oracle artifact: `{payload.get('oracle_artifact')}`",
        f"- Validation horizon: {payload.get('validation_horizon')}",
        f"- Candidates: {payload.get('candidate_count')}",
        "",
        "## Diagnoses",
        "",
    ]
    for key, count in (payload.get("diagnosis_counts") or {}).items():
        lines.append(f"- `{key}`: {count}")
    lines.extend(["", "## Candidates", ""])
    for candidate in payload.get("candidates", []) or []:
        dtm = candidate.get("dtm", {}) or {}
        lines.append(f"### {candidate.get('candidate_id')}")
        lines.append(f"- Diagnosis: `{candidate.get('diagnosis')}`")
        lines.append(f"- Governor: `{candidate.get('governor_status')}`")
        lines.append(f"- FEN: `{candidate.get('post_reply_fen')}`")
        lines.append(f"- State DTM: {dtm.get('state_dtm')}")
        lines.append(f"- Best plies: {dtm.get('best_dtm_plies')}")
        moves = ", ".join(
            f"`{item.get('move')}`"
            for item in (dtm.get("best_moves") or [])[:5]
        )
        lines.append(f"- Best winning moves: {moves or 'none'}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize Stage 7 KRK DTM oracle candidates")
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--validation-horizon", type=int, default=40)
    parser.add_argument("--evidence-artifact", action="append", default=[])
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = summarize_dtm_oracle(
        oracle_path=args.oracle,
        validation_horizon=args.validation_horizon,
        evidence_artifacts=list(args.evidence_artifact or []),
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(_to_markdown(payload), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
