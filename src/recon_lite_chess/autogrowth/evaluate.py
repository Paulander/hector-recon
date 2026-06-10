"""Baseline and sham-growth KRK evaluation for autogrowth M1-M3."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any, Iterable, Literal

import chess

from .features import extract_learner_features, make_trace_record, validate_learner_record
from .positions import KRKPositionSet, generate_position_sets


ArmName = Literal["baseline", "sham_growth"]


@dataclass(frozen=True)
class EvaluationConfig:
    seed: int = 20260610
    train_count: int = 200
    heldout_weakness_count: int = 100
    heldout_broader_count: int = 100
    horizons: tuple[int, ...] = (40, 80)


@dataclass(frozen=True)
class ArmMetrics:
    arm: str
    horizon: int
    total: int
    mates: int
    max_plies: int
    horizon_no_mate: int
    stalemates: int
    rook_losses: int
    draws: int
    draw_reasons: dict[str, int]
    illegal_moves: int
    other_failures: int
    repetition_events: int
    repeated_white_action_events: int
    white_action_count: int
    white_unique_action_total: int
    action_vitality_rate: float

    @property
    def conversion_rate(self) -> float:
        return 0.0 if self.total == 0 else self.mates / self.total

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["conversion_rate"] = self.conversion_rate
        return payload


@dataclass(frozen=True)
class EvaluationResult:
    config: EvaluationConfig
    positions: KRKPositionSet
    metrics: dict[str, dict[str, ArmMetrics]]
    paired_deltas: dict[str, dict[str, int]]
    learning_counters: dict[str, int | float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_m1_m3_baseline.v0",
            "config": {
                **asdict(self.config),
                "horizons": list(self.config.horizons),
            },
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "train_count": len(self.positions.train),
                "heldout_weakness_count": len(self.positions.heldout_weakness),
                "heldout_broader_count": len(self.positions.heldout_broader),
                "heldout_count": len(self.positions.heldout),
                "train": list(self.positions.train),
                "heldout_weakness": list(self.positions.heldout_weakness),
                "heldout_broader": list(self.positions.heldout_broader),
            },
            "arms": {
                arm: {horizon: metrics.to_dict() for horizon, metrics in by_horizon.items()}
                for arm, by_horizon in self.metrics.items()
            },
            "paired_deltas": self.paired_deltas,
            "learning_counters": self.learning_counters,
            "decision": {
                "status": "baseline_and_sham_ready",
                "autogrowth_candidate_enabled": False,
                "selector_behavior_enabled": False,
                "runtime_tablebase_or_dtm_provider": False,
                "stage_label_learner_features": False,
            },
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def _white_rook_square(board: chess.Board) -> int | None:
    rooks = sorted(board.pieces(chess.ROOK, chess.WHITE))
    return rooks[0] if rooks else None


def _chebyshev(a: int | None, b: int | None) -> int:
    if a is None or b is None:
        return 8
    return max(
        abs(chess.square_file(a) - chess.square_file(b)),
        abs(chess.square_rank(a) - chess.square_rank(b)),
    )


def _edge_distance(square: int | None) -> int:
    if square is None:
        return 4
    file_idx = chess.square_file(square)
    rank_idx = chess.square_rank(square)
    return min(file_idx, 7 - file_idx, rank_idx, 7 - rank_idx)


def _move_checkmates(board: chess.Board, move: chess.Move) -> bool:
    if move not in board.legal_moves:
        return False
    after = board.copy(stack=False)
    after.push(move)
    return after.is_checkmate()


def _position_repetition_key(board: chess.Board) -> str:
    return " ".join(
        [
            board.board_fen(),
            "w" if board.turn == chess.WHITE else "b",
            board.castling_xfen(),
            chess.square_name(board.ep_square) if board.ep_square is not None else "-",
        ]
    )


def classify_terminal_outcome(board: chess.Board) -> str | None:
    """Return a concrete terminal reason when python-chess exposes one."""

    if board.is_checkmate():
        return "mate"
    if board.is_stalemate():
        return "stalemate"
    if _white_rook_square(board) is None:
        return "rook_loss"
    outcome = board.outcome(claim_draw=False)
    if outcome is None:
        return None
    reason = outcome.termination.name.lower()
    if outcome.winner is None:
        return f"draw_{reason}"
    return f"terminal_{reason}"


def _rook_safe_after_white_move(board: chess.Board, move: chess.Move) -> bool:
    after = board.copy(stack=False)
    after.push(move)
    rook = _white_rook_square(after)
    white_king = after.king(chess.WHITE)
    black_king = after.king(chess.BLACK)
    if rook is None or black_king is None:
        return False
    capture = chess.Move(black_king, rook)
    if capture not in after.legal_moves:
        return True
    return _chebyshev(white_king, rook) <= 1


def _score_white_post_move(board: chess.Board, move: chess.Move) -> tuple[float, str]:
    after = board.copy(stack=False)
    after.push(move)
    if after.is_checkmate():
        return (10_000.0, "mate")
    if after.is_stalemate():
        return (-10_000.0, "stalemate")
    black_king = after.king(chess.BLACK)
    white_king = after.king(chess.WHITE)
    rook = _white_rook_square(after)
    score = 0.0
    score -= 12.0 * _edge_distance(black_king)
    score -= 1.5 * _chebyshev(white_king, black_king)
    score -= 0.5 * _chebyshev(rook, black_king)
    score -= 0.25 * after.legal_moves.count()
    score += 8.0 if after.is_check() else 0.0
    score += 4.0 if _rook_safe_after_white_move(board, move) else -20.0
    return (score, "heuristic")


def choose_white_baseline_move(board: chess.Board) -> chess.Move | None:
    if board.turn != chess.WHITE or board.is_game_over(claim_draw=False):
        return None
    legal_moves = sorted(board.legal_moves, key=lambda item: item.uci())
    if not legal_moves:
        return None
    mates = [move for move in legal_moves if _move_checkmates(board, move)]
    if mates:
        return mates[0]
    scored = [(_score_white_post_move(board, move), move.uci(), move) for move in legal_moves]
    scored.sort(key=lambda item: (item[0][0], item[1]), reverse=True)
    return scored[0][2]


def _score_black_post_move(board: chess.Board, move: chess.Move) -> tuple[float, str]:
    after = board.copy(stack=False)
    after.push(move)
    if after.is_checkmate():
        return (-10_000.0, "self_mate")
    black_king = after.king(chess.BLACK)
    white_king = after.king(chess.WHITE)
    rook = _white_rook_square(after)
    score = 0.0
    score += 12.0 * _edge_distance(black_king)
    score += 1.0 * _chebyshev(white_king, black_king)
    score += 0.25 * after.legal_moves.count()
    if rook is None:
        score += 500.0
    else:
        score += 0.25 * _chebyshev(rook, black_king)
    return (score, "heuristic")


def choose_black_reply(board: chess.Board) -> chess.Move | None:
    if board.turn != chess.BLACK or board.is_game_over(claim_draw=False):
        return None
    legal_moves = sorted(board.legal_moves, key=lambda item: item.uci())
    if not legal_moves:
        return None
    scored = [(_score_black_post_move(board, move), move.uci(), move) for move in legal_moves]
    scored.sort(key=lambda item: (item[0][0], item[1]), reverse=True)
    return scored[0][2]


def _playout(fen: str, *, arm: ArmName, horizon: int, keep_trace: bool = False) -> dict[str, Any]:
    board = chess.Board(fen)
    trace: list[dict[str, Any]] = []
    illegal_moves = 0
    position_counts = {_position_repetition_key(board): 1}
    white_action_counts: dict[str, int] = {}
    repetition_events = 0
    repeated_white_action_events = 0
    white_action_count = 0

    for ply in range(int(horizon)):
        terminal_outcome = classify_terminal_outcome(board)
        if terminal_outcome is not None:
            return {
                "outcome": terminal_outcome,
                "plies": ply,
                "illegal_moves": illegal_moves,
                "trace": trace,
                "repetition_events": repetition_events,
                "repeated_white_action_events": repeated_white_action_events,
                "white_action_count": white_action_count,
                "white_unique_action_total": len(white_action_counts),
            }

        move = choose_white_baseline_move(board) if board.turn == chess.WHITE else choose_black_reply(board)
        before = board.copy(stack=False)
        if move is None or move not in board.legal_moves:
            illegal_moves += 1
            return {
                "outcome": "illegal_move",
                "plies": ply,
                "illegal_moves": illegal_moves,
                "trace": trace,
                "repetition_events": repetition_events,
                "repeated_white_action_events": repeated_white_action_events,
                "white_action_count": white_action_count,
                "white_unique_action_total": len(white_action_counts),
            }

        if before.turn == chess.WHITE:
            white_action_count += 1
            action_key = move.uci()
            if white_action_counts.get(action_key, 0) > 0:
                repeated_white_action_events += 1
            white_action_counts[action_key] = white_action_counts.get(action_key, 0) + 1

        board.push(move)
        position_key = _position_repetition_key(board)
        if position_counts.get(position_key, 0) > 0:
            repetition_events += 1
        position_counts[position_key] = position_counts.get(position_key, 0) + 1

        if keep_trace and before.turn == chess.WHITE:
            trace.append(
                make_trace_record(
                    board=before,
                    move=move,
                    after_board=board,
                    outcome="pending",
                    ply=ply,
                )
            )
        terminal_outcome = classify_terminal_outcome(board)
        if terminal_outcome is not None:
            if trace and keep_trace:
                trace[-1]["outcome"] = terminal_outcome
                validate_learner_record(trace)
            return {
                "outcome": terminal_outcome,
                "plies": ply + 1,
                "illegal_moves": illegal_moves,
                "trace": trace,
                "repetition_events": repetition_events,
                "repeated_white_action_events": repeated_white_action_events,
                "white_action_count": white_action_count,
                "white_unique_action_total": len(white_action_counts),
            }

    outcome = "mate" if board.is_checkmate() else "horizon_no_mate"
    if trace and keep_trace:
        trace[-1]["outcome"] = outcome
        validate_learner_record(trace)
    return {
        "outcome": outcome,
        "plies": int(horizon),
        "illegal_moves": illegal_moves,
        "trace": trace,
        "repetition_events": repetition_events,
        "repeated_white_action_events": repeated_white_action_events,
        "white_action_count": white_action_count,
        "white_unique_action_total": len(white_action_counts),
    }


def evaluate_arm(fens: Iterable[str], *, arm: ArmName, horizon: int) -> tuple[ArmMetrics, list[dict[str, Any]]]:
    outcomes: list[dict[str, Any]] = []
    counts = {
        "mate": 0,
        "horizon_no_mate": 0,
        "stalemate": 0,
        "rook_loss": 0,
        "illegal_move": 0,
        "other_failure": 0,
    }
    draw_reasons: dict[str, int] = {}
    repetition_events = 0
    repeated_white_action_events = 0
    white_action_count = 0
    white_unique_action_total = 0
    for fen in fens:
        result = _playout(fen, arm=arm, horizon=horizon)
        outcome = str(result["outcome"])
        if outcome.startswith("draw_"):
            draw_reasons[outcome] = draw_reasons.get(outcome, 0) + 1
        else:
            counts[outcome] = counts.get(outcome, 0) + 1
        repetition_events += int(result["repetition_events"])
        repeated_white_action_events += int(result["repeated_white_action_events"])
        white_action_count += int(result["white_action_count"])
        white_unique_action_total += int(result["white_unique_action_total"])
        outcomes.append({"fen": fen, **{key: value for key, value in result.items() if key != "trace"}})
    draws = sum(draw_reasons.values())
    action_vitality_rate = 0.0 if white_action_count == 0 else white_unique_action_total / white_action_count

    return (
        ArmMetrics(
            arm=arm,
            horizon=int(horizon),
            total=len(outcomes),
            mates=counts["mate"],
            max_plies=counts["horizon_no_mate"],
            horizon_no_mate=counts["horizon_no_mate"],
            stalemates=counts["stalemate"],
            rook_losses=counts["rook_loss"],
            draws=draws,
            draw_reasons=dict(sorted(draw_reasons.items())),
            illegal_moves=counts["illegal_move"],
            other_failures=counts["other_failure"],
            repetition_events=repetition_events,
            repeated_white_action_events=repeated_white_action_events,
            white_action_count=white_action_count,
            white_unique_action_total=white_unique_action_total,
            action_vitality_rate=action_vitality_rate,
        ),
        outcomes,
    )


def _paired_delta(
    baseline_outcomes: list[dict[str, Any]],
    sham_outcomes: list[dict[str, Any]],
) -> dict[str, int]:
    baseline_by_fen = {row["fen"]: row for row in baseline_outcomes}
    sham_by_fen = {row["fen"]: row for row in sham_outcomes}
    candidate_succeeds_baseline_fails = 0
    candidate_fails_baseline_succeeds = 0
    changed = 0
    for fen, baseline in baseline_by_fen.items():
        sham = sham_by_fen[fen]
        baseline_success = baseline["outcome"] == "mate"
        sham_success = sham["outcome"] == "mate"
        if sham["outcome"] != baseline["outcome"]:
            changed += 1
        if sham_success and not baseline_success:
            candidate_succeeds_baseline_fails += 1
        if baseline_success and not sham_success:
            candidate_fails_baseline_succeeds += 1
    return {
        "candidate_succeeds_where_baseline_fails": candidate_succeeds_baseline_fails,
        "candidate_fails_where_baseline_succeeds": candidate_fails_baseline_succeeds,
        "outcome_changed_count": changed,
    }


def evaluate_baseline_and_sham(
    *,
    config: EvaluationConfig,
    positions: KRKPositionSet | None = None,
) -> EvaluationResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    metrics: dict[str, dict[str, ArmMetrics]] = {"baseline": {}, "sham_growth": {}}
    paired_deltas: dict[str, dict[str, int]] = {}

    for horizon in config.horizons:
        baseline_metrics, baseline_outcomes = evaluate_arm(positions.heldout, arm="baseline", horizon=horizon)
        sham_metrics, sham_outcomes = evaluate_arm(positions.heldout, arm="sham_growth", horizon=horizon)
        metrics["baseline"][str(horizon)] = baseline_metrics
        metrics["sham_growth"][str(horizon)] = sham_metrics
        paired_deltas[str(horizon)] = _paired_delta(baseline_outcomes, sham_outcomes)

    return EvaluationResult(
        config=config,
        positions=positions,
        metrics=metrics,
        paired_deltas=paired_deltas,
        learning_counters={
            "candidate_nodes_spawned": 0,
            "candidate_nodes_promoted": 0,
            "candidate_activation_rate": 0.0,
            "positive_credit_count": 0,
            "negative_credit_count": 0,
            "m3_update_count": 0,
            "m4_consolidation_event_count": 0,
            "deleted_candidate_count": 0,
        },
    )
