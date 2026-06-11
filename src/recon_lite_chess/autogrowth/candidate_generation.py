"""M13 risk-aware candidate generation for local ACTION arbitration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

import chess

from .arbitration import LocalArbitrationConfig, LocalArbitrationResult, run_local_arbitration_experiment
from .features import extract_learner_features, validate_learner_record
from .mining import _magnitude_bucket, _signed_bucket
from .positions import KRKPositionSet, generate_position_sets
from .suppressor import _projected_negative_reason


RISK_BEFORE_FEATURES = (
    "black_king_nearest_edge_distance",
    "white_king_to_black_king_distance",
    "white_rook_to_black_king_distance",
    "white_king_to_rook_distance",
    "rook_attacked_by_black",
    "is_check",
)

RISK_DELTA_FEATURES = (
    "black_king_nearest_edge_distance",
    "black_reply_mobility",
    "white_king_to_black_king_distance",
    "white_rook_to_black_king_distance",
    "white_king_to_rook_distance",
    "rook_attacked_by_black",
    "is_check",
    "is_stalemate",
)


@dataclass(frozen=True)
class RiskAwareCandidateConfig:
    seed: int = 20260610
    train_count: int = 200
    heldout_weakness_count: int = 100
    heldout_broader_count: int = 100
    min_support: int = 3
    max_candidates: int = 12
    horizon: int = 40
    min_candidate_credit: float = 0.05
    activation_max_distance: float = 1.5
    suppressor_max_distance: float = 0.75
    eta_m3: float = 0.08


@dataclass(frozen=True)
class RiskAwareCandidateResult:
    config: RiskAwareCandidateConfig
    positions: KRKPositionSet
    candidates: list[dict[str, Any]]
    generation_summary: dict[str, Any]
    arbitration_payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        validate_learner_record(self.candidates)
        return {
            "schema_version": "krk_autogrowth_m13_risk_aware_candidates.v0",
            "config": asdict(self.config),
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "train_count": len(self.positions.train),
                "heldout_count": len(self.positions.heldout),
                "heldout_weakness_count": len(self.positions.heldout_weakness),
                "heldout_broader_count": len(self.positions.heldout_broader),
            },
            "generation_summary": self.generation_summary,
            "candidates": self.candidates,
            "local_arbitration_result": self.arbitration_payload,
            "decision": {
                "status": self.arbitration_payload["decision"]["status"],
                "risk_aware_candidates_generated": len(self.candidates),
                "krk_competence_passed": self.arbitration_payload["decision"]["krk_competence_passed"],
                "safety_checkpoint_passed": self.arbitration_payload["decision"]["safety_checkpoint_passed"],
                "move_choice_mediated_by_local_action_nodes": True,
                "direct_move_override": False,
                "runtime_tablebase_or_dtm_move_source": False,
            },
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_risk_aware_candidate_experiment(
    *,
    config: RiskAwareCandidateConfig,
    positions: KRKPositionSet | None = None,
) -> RiskAwareCandidateResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    candidates, generation_summary = generate_risk_aware_candidates(
        positions.train,
        config=config,
    )
    if candidates:
        arbitration_result = run_local_arbitration_experiment(
            config=LocalArbitrationConfig(
                seed=config.seed,
                train_count=config.train_count,
                heldout_weakness_count=config.heldout_weakness_count,
                heldout_broader_count=config.heldout_broader_count,
                candidate_path="risk_aware_generated_in_memory",
                candidate_count=len(candidates),
                horizon=config.horizon,
                activation_max_distance=config.activation_max_distance,
                suppressor_max_distance=config.suppressor_max_distance,
                eta_m3=config.eta_m3,
            ),
            positions=positions,
            candidates=candidates,
        )
        arbitration_payload = arbitration_result.to_dict()
    else:
        arbitration_payload = _empty_arbitration_payload(config=config, positions=positions)
    return RiskAwareCandidateResult(
        config=config,
        positions=positions,
        candidates=candidates,
        generation_summary=generation_summary,
        arbitration_payload=arbitration_payload,
    )


def generate_risk_aware_candidates(
    train_fens: Iterable[str],
    *,
    config: RiskAwareCandidateConfig,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    total_actions = 0
    rejected_negative = 0
    rejected_low_credit = 0

    for position_index, fen in enumerate(train_fens):
        board = chess.Board(fen)
        if board.turn != chess.WHITE:
            continue
        before_features = extract_learner_features(board)
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            piece = board.piece_at(move.from_square)
            if piece is None or piece.color != chess.WHITE:
                continue
            total_actions += 1
            after = board.copy(stack=False)
            after.push(move)
            if _projected_negative_reason(board, after) is not None:
                rejected_negative += 1
                continue
            credit = _risk_aware_credit(board, after)
            if credit < config.min_candidate_credit:
                rejected_low_credit += 1
                continue
            after_features = extract_learner_features(after)
            progress_deltas = {
                key: after_features[key] - before_features[key]
                for key in before_features
            }
            action_schema = _action_schema(board, move)
            key = _risk_bucket_key(before_features, action_schema)
            buckets.setdefault(key, []).append(
                {
                    "position_index": position_index,
                    "before_features": before_features,
                    "after_features": after_features,
                    "progress_deltas": progress_deltas,
                    "action_schema": action_schema,
                    "credit": credit,
                }
            )

    raw_candidates = [
        _candidate_from_risk_bucket(bucket_key=key, rows=rows)
        for key, rows in buckets.items()
        if len(rows) >= config.min_support
    ]
    raw_candidates.sort(
        key=lambda candidate: (
            candidate["evidence"]["mean_candidate_credit"],
            candidate["evidence"]["support_count"],
            candidate["candidate_key"],
        ),
        reverse=True,
    )
    candidates = raw_candidates[: config.max_candidates]
    for rank, candidate in enumerate(candidates, start=1):
        candidate["rank"] = rank
        candidate["selected_for_m5"] = rank == 1
        validate_learner_record(candidate)

    summary = {
        "total_legal_white_actions_considered": total_actions,
        "rejected_negative_projection_count": rejected_negative,
        "rejected_low_credit_count": rejected_low_credit,
        "bucket_count": len(buckets),
        "candidate_count": len(candidates),
        "behavior_change_applied": False,
        "candidate_active_in_runtime": False,
        "direct_move_override": False,
    }
    return candidates, summary


def _candidate_from_risk_bucket(*, bucket_key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    before = _mean_features(row["before_features"] for row in rows)
    after = _mean_features(row["after_features"] for row in rows)
    deltas = _mean_features(row["progress_deltas"] for row in rows)
    scores = [float(row["credit"]) for row in rows]
    action_schema = rows[0]["action_schema"]
    digest = hashlib.sha256(bucket_key.encode("utf-8")).hexdigest()[:12]
    return {
        "candidate_key": f"m13_risk_action_{digest}",
        "rank": 0,
        "selected_for_m5": False,
        "status": "m13_risk_aware_not_spawned",
        "source_split": "train",
        "behavior_change_applied": False,
        "candidate_active_in_runtime": False,
        "recon_topology_plan": {
            "node_types": ["TERMINAL", "ACTION", "TERMINAL", "SCRIPT"],
            "relation_types": ["SUB", "SUR", "POR", "RET"],
            "spawn_count": 1,
            "spawned_now": False,
            "m3_update_count": 0,
            "m4_event_count": 0,
            "local_parent_id": "m13_risk_aware_parent",
        },
        "before_cluster": {
            "feature_names": list(RISK_BEFORE_FEATURES),
            "prototype": {name: before[name] for name in RISK_BEFORE_FEATURES},
        },
        "action_schema": action_schema,
        "after_delta_cluster": {
            "feature_names": list(RISK_DELTA_FEATURES),
            "prototype": {name: deltas[name] for name in RISK_DELTA_FEATURES},
        },
        "after_cluster": {
            "feature_names": sorted(after),
            "prototype": after,
        },
        "evidence": {
            "support_count": len(rows),
            "position_count": len({int(row["position_index"]) for row in rows}),
            "mean_generic_progress_credit": mean(scores),
            "mean_terminal_reward": 0.0,
            "mean_candidate_credit": mean(scores),
            "positive_credit_count": sum(1 for score in scores if score > 0.0),
            "negative_credit_count": sum(1 for score in scores if score < 0.0),
            "example_trace_keys": [
                f"m13_risk_action_{row['position_index']}"
                for row in rows[:8]
            ],
        },
    }


def _risk_aware_credit(before: chess.Board, after: chess.Board) -> float:
    before_features = extract_learner_features(before)
    after_features = extract_learner_features(after)
    if after.is_checkmate():
        return 2.0
    score = 0.0
    score += -0.35 * (
        after_features["black_king_nearest_edge_distance"]
        - before_features["black_king_nearest_edge_distance"]
    )
    score += -0.08 * (
        after_features["black_reply_mobility"]
        - before_features["black_reply_mobility"]
    )
    score += -0.05 * (
        after_features["white_king_to_black_king_distance"]
        - before_features["white_king_to_black_king_distance"]
    )
    score += -0.03 * (
        after_features["white_rook_to_black_king_distance"]
        - before_features["white_rook_to_black_king_distance"]
    )
    score += 0.15 if after_features["is_check"] > 0.0 else 0.0
    score += -0.50 * after_features["rook_attacked_by_black"]
    return score


def _action_schema(board: chess.Board, move: chess.Move) -> dict[str, int]:
    piece = board.piece_at(move.from_square)
    file_delta = chess.square_file(move.to_square) - chess.square_file(move.from_square)
    rank_delta = chess.square_rank(move.to_square) - chess.square_rank(move.from_square)
    return {
        "piece_type": 0 if piece is None else int(piece.piece_type),
        "file_delta_sign": _signed_bucket(file_delta),
        "rank_delta_sign": _signed_bucket(rank_delta),
        "file_delta_magnitude": _magnitude_bucket(file_delta),
        "rank_delta_magnitude": _magnitude_bucket(rank_delta),
        "gives_check": int(board.gives_check(move)),
        "is_capture": int(board.is_capture(move)),
    }


def _risk_bucket_key(before_features: dict[str, float], action_schema: dict[str, int]) -> str:
    before_bucket = {
        name: int(round(before_features[name]))
        for name in RISK_BEFORE_FEATURES
    }
    return json.dumps(
        {
            "before": before_bucket,
            "action_schema": action_schema,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _mean_features(rows: Iterable[dict[str, float]]) -> dict[str, float]:
    materialized = list(rows)
    if not materialized:
        return {}
    return {
        key: sum(float(row[key]) for row in materialized) / len(materialized)
        for key in materialized[0]
    }


def _empty_arbitration_payload(
    *,
    config: RiskAwareCandidateConfig,
    positions: KRKPositionSet,
) -> dict[str, Any]:
    return {
        "schema_version": "krk_autogrowth_m12_local_arbitration.v0",
        "config": asdict(
            LocalArbitrationConfig(
                seed=config.seed,
                train_count=config.train_count,
                heldout_weakness_count=config.heldout_weakness_count,
                heldout_broader_count=config.heldout_broader_count,
                candidate_count=0,
                horizon=config.horizon,
                activation_max_distance=config.activation_max_distance,
                suppressor_max_distance=config.suppressor_max_distance,
                eta_m3=config.eta_m3,
            )
        ),
        "dataset": {
            "seed": positions.seed,
            "digest": positions.digest(),
            "train_count": len(positions.train),
            "heldout_count": len(positions.heldout),
        },
        "decision": {
            "status": "no_risk_aware_candidates_generated",
            "passed": False,
            "safety_checkpoint_passed": False,
            "krk_competence_passed": False,
            "move_choice_mediated_by_local_action_nodes": True,
            "direct_move_override": False,
            "runtime_tablebase_or_dtm_move_source": False,
        },
    }
