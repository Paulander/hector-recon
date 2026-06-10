"""M4 trace collection for KRK autogrowth.

Trace collection observes the existing playout policy. It does not select,
rerank, override, or otherwise alter moves.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

import chess

from .evaluate import (
    choose_black_reply,
    choose_white_baseline_move,
    classify_terminal_outcome,
    _position_repetition_key,
)
from .features import make_trace_record, validate_learner_record
from .positions import KRKPositionSet, generate_position_sets


@dataclass(frozen=True)
class TraceCollectionConfig:
    seed: int = 20260610
    train_count: int = 200
    horizon: int = 40


@dataclass(frozen=True)
class TraceCollectionResult:
    config: TraceCollectionConfig
    positions: KRKPositionSet
    records: list[dict[str, Any]]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        validate_learner_record(self.records)
        return {
            "schema_version": "krk_autogrowth_m4_traces.v0",
            "config": asdict(self.config),
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "source_split": "train",
                "train_count": len(self.positions.train),
                "train": list(self.positions.train),
                "heldout_used_for_trace": False,
            },
            "summary": self.summary,
            "records": self.records,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def _empty_positions(seed: int, train_count: int) -> KRKPositionSet:
    return generate_position_sets(
        seed=seed,
        train_count=train_count,
        heldout_weakness_count=0,
        heldout_broader_count=0,
    )


def _finish_position_records(
    *,
    records: list[dict[str, Any]],
    indices: list[int],
    terminal_outcome: str,
    terminal_plies: int,
) -> None:
    terminal_reward = 1.0 if terminal_outcome == "mate" else 0.0
    for index in indices:
        records[index]["terminal_outcome"] = terminal_outcome
        records[index]["terminal_plies"] = int(terminal_plies)
        records[index]["rollout_credit"] = {
            "terminal_reward": terminal_reward,
            "credit_origin": "rollout_terminal",
            "runtime_move_source": False,
        }
        records[index]["outcome"] = terminal_outcome
        validate_learner_record(records[index])


def collect_trace_records(
    *,
    config: TraceCollectionConfig,
    positions: KRKPositionSet | None = None,
) -> TraceCollectionResult:
    """Collect train-only before/action/after records for later graph mining."""

    positions = positions or _empty_positions(seed=config.seed, train_count=config.train_count)
    records: list[dict[str, Any]] = []
    outcome_counts: dict[str, int] = {}
    total_repetition_events = 0
    total_repeated_white_action_events = 0
    total_white_action_count = 0
    total_white_unique_action_count = 0

    for position_index, fen in enumerate(positions.train):
        board = chess.Board(fen)
        position_counts = {_position_repetition_key(board): 1}
        white_action_counts: dict[str, int] = {}
        position_record_indices: list[int] = []
        terminal_outcome = "horizon_no_mate"
        terminal_plies = int(config.horizon)
        repetition_events = 0
        repeated_white_action_events = 0
        white_action_index = 0

        for ply in range(int(config.horizon)):
            terminal = classify_terminal_outcome(board)
            if terminal is not None:
                terminal_outcome = terminal
                terminal_plies = ply
                break

            move = choose_white_baseline_move(board) if board.turn == chess.WHITE else choose_black_reply(board)
            before = board.copy(stack=False)
            if move is None or move not in board.legal_moves:
                terminal_outcome = "illegal_move"
                terminal_plies = ply
                break

            action_seen_before = white_action_counts.get(move.uci(), 0) if before.turn == chess.WHITE else 0
            if before.turn == chess.WHITE and action_seen_before > 0:
                repeated_white_action_events += 1

            board.push(move)
            position_key = _position_repetition_key(board)
            position_seen_before = position_counts.get(position_key, 0)
            if position_seen_before > 0:
                repetition_events += 1
            position_counts[position_key] = position_seen_before + 1

            if before.turn == chess.WHITE:
                white_action_counts[move.uci()] = action_seen_before + 1
                record = make_trace_record(
                    board=before,
                    move=move,
                    after_board=board,
                    outcome="pending",
                    ply=ply,
                )
                record.update(
                    {
                        "trace_key": f"train_{position_index:04d}_white_{white_action_index:03d}",
                        "source_split": "train",
                        "position_index": position_index,
                        "initial_fen": fen,
                        "white_action_index": white_action_index,
                        "repetition_context": {
                            "position_seen_before": int(position_seen_before),
                            "white_action_seen_before": int(action_seen_before),
                        },
                        "candidate_mining_input": {
                            "terminal_action_terminal": True,
                            "relation_types": ["SUB", "SUR", "POR", "RET"],
                            "runtime_behavior_change": False,
                            "external_action_ranking": False,
                        },
                    }
                )
                validate_learner_record(record)
                records.append(record)
                position_record_indices.append(len(records) - 1)
                white_action_index += 1

            terminal = classify_terminal_outcome(board)
            if terminal is not None:
                terminal_outcome = terminal
                terminal_plies = ply + 1
                break

        total_repetition_events += repetition_events
        total_repeated_white_action_events += repeated_white_action_events
        total_white_action_count += sum(white_action_counts.values())
        total_white_unique_action_count += len(white_action_counts)
        outcome_counts[terminal_outcome] = outcome_counts.get(terminal_outcome, 0) + 1
        _finish_position_records(
            records=records,
            indices=position_record_indices,
            terminal_outcome=terminal_outcome,
            terminal_plies=terminal_plies,
        )

    action_vitality_rate = (
        0.0 if total_white_action_count == 0 else total_white_unique_action_count / total_white_action_count
    )
    summary = {
        "trace_record_count": len(records),
        "train_position_count": len(positions.train),
        "horizon": int(config.horizon),
        "terminal_outcomes": dict(sorted(outcome_counts.items())),
        "repetition_events": total_repetition_events,
        "repeated_white_action_events": total_repeated_white_action_events,
        "white_action_count": total_white_action_count,
        "white_unique_action_total": total_white_unique_action_count,
        "action_vitality_rate": action_vitality_rate,
        "behavior_change_applied": False,
        "candidate_behavior_enabled": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "heldout_used_for_trace": False,
    }
    return TraceCollectionResult(
        config=config,
        positions=positions,
        records=records,
        summary=summary,
    )
