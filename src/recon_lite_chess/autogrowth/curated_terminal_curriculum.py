"""TG26j curated KRK curriculum runway for terminal-native learning.

The old KRK curriculum is useful training distribution, not learner-visible
strategy. This module adapts curated stage FENs into terminal-native
Mate_In_1/Mate_In_2 training and reports which later stages need graded rollout
instead of forcing everything through the mate-in-two classifier.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable

import chess

from recon_lite_chess.training.krk_curriculum import KRKStage, KRK_STAGES

from .features import validate_learner_record
from .foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _mate_moves,
)
from .terminal_substrate import (
    TerminalAffordanceLearner,
    _evaluate_terminal_mate_in_one,
    _evaluate_terminal_mate_in_two,
    _train_terminal_mate_in_one,
    _train_terminal_mate_in_two,
)


@dataclass(frozen=True)
class CuratedTerminalCurriculumConfig:
    train_repetitions: int = 3
    eta_m3: float = 0.10
    rich_feature_credit_scale: float = 0.25
    max_samples: int = 24


@dataclass(frozen=True)
class CuratedStageEntry:
    stage_index: int
    stage_id: int
    stage_name: str
    position_index: int
    symmetry: str
    fen: str
    optimal_moves: int
    description: str
    valid: bool
    mate_in_one_moves: tuple[str, ...]
    forced_mate_in_two_first_moves: tuple[str, ...]

    @property
    def training_role(self) -> str:
        if self.mate_in_one_moves:
            return "mate_in_one"
        if self.forced_mate_in_two_first_moves:
            return "forced_mate_in_two"
        if self.valid:
            return "later_graded_rollout"
        return "invalid"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["training_role"] = self.training_role
        return data


@dataclass(frozen=True)
class CuratedTerminalCurriculumResult:
    config: CuratedTerminalCurriculumConfig
    stage_inventory: dict[str, Any]
    original_position_run: dict[str, Any]
    symmetry_expanded_run: dict[str, Any]
    interpretation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26j_curated_terminal_curriculum.v0",
            "config": asdict(self.config),
            "purity_boundary": {
                "curriculum_labels_are_schedule_and_diagnostics_only": True,
                "stage_labels_learner_visible": False,
                "strategic_descriptions_learner_visible": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "direct_provider_override": False,
                "behavior_mediated_by_terminal_weights": True,
            },
            "stage_inventory": self.stage_inventory,
            "original_position_run": self.original_position_run,
            "symmetry_expanded_run": self.symmetry_expanded_run,
            "interpretation": self.interpretation,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_curated_terminal_curriculum(
    *,
    config: CuratedTerminalCurriculumConfig | None = None,
) -> CuratedTerminalCurriculumResult:
    cfg = config or CuratedTerminalCurriculumConfig()
    original_entries = curated_stage_entries(include_symmetries=False)
    symmetry_entries = curated_stage_entries(include_symmetries=True)
    inventory = stage_inventory(symmetry_entries)
    original_run = _run_curated_foundation(entries=original_entries, config=cfg)
    symmetry_run = _run_curated_foundation(entries=symmetry_entries, config=cfg)
    return CuratedTerminalCurriculumResult(
        config=cfg,
        stage_inventory=inventory,
        original_position_run=original_run,
        symmetry_expanded_run=symmetry_run,
        interpretation=_interpret(original_run=original_run, symmetry_run=symmetry_run, inventory=inventory),
    )


def curated_stage_entries(*, include_symmetries: bool) -> tuple[CuratedStageEntry, ...]:
    entries: list[CuratedStageEntry] = []
    for stage_index, stage in enumerate(KRK_STAGES):
        for position_index, position in enumerate(stage.positions):
            boards = _symmetry_boards(position.fen) if include_symmetries else (("identity", chess.Board(position.fen)),)
            seen: set[str] = set()
            for symmetry, board in boards:
                normalized = _normalize_board(board)
                fen = normalized.fen()
                if fen in seen:
                    continue
                seen.add(fen)
                valid = _valid_krk_board(normalized)
                mate1: tuple[str, ...] = ()
                mate2: tuple[str, ...] = ()
                if valid:
                    mate1 = tuple(move.uci() for move in _mate_moves(normalized))
                    mate2 = tuple(move.uci() for move in _forced_mate_in_two_first_moves(normalized))
                entries.append(
                    CuratedStageEntry(
                        stage_index=stage_index,
                        stage_id=stage.stage_id,
                        stage_name=stage.name,
                        position_index=position_index,
                        symmetry=symmetry,
                        fen=fen,
                        optimal_moves=position.optimal_moves,
                        description=position.description,
                        valid=valid,
                        mate_in_one_moves=mate1,
                        forced_mate_in_two_first_moves=mate2,
                    )
                )
    return tuple(entries)


def stage_inventory(entries: Iterable[CuratedStageEntry]) -> dict[str, Any]:
    by_stage: dict[str, dict[str, Any]] = {}
    examples: dict[str, list[dict[str, Any]]] = {
        "mate_in_one": [],
        "forced_mate_in_two": [],
        "later_graded_rollout": [],
        "invalid": [],
    }
    for entry in entries:
        stage = by_stage.setdefault(
            entry.stage_name,
            {
                "stage_index": entry.stage_index,
                "stage_id": entry.stage_id,
                "position_count": 0,
                "mate_in_one_count": 0,
                "forced_mate_in_two_count": 0,
                "later_graded_rollout_count": 0,
                "invalid_count": 0,
            },
        )
        stage["position_count"] += 1
        stage[f"{entry.training_role}_count"] += 1
        if len(examples[entry.training_role]) < 12:
            examples[entry.training_role].append(entry.to_dict())
    validate_learner_record([
        {
            "stage": stage,
            "counts": {
                "mate_in_one": data["mate_in_one_count"],
                "forced_mate_in_two": data["forced_mate_in_two_count"],
                "later": data["later_graded_rollout_count"],
            },
        }
        for stage, data in sorted(by_stage.items())
    ])
    return {
        "source": "src/recon_lite_chess/training/krk_curriculum.py::KRK_STAGES",
        "stage_count": len(by_stage),
        "entry_count": sum(data["position_count"] for data in by_stage.values()),
        "by_stage": dict(sorted(by_stage.items(), key=lambda item: item[1]["stage_index"])),
        "examples": examples,
    }


def _run_curated_foundation(
    *,
    entries: tuple[CuratedStageEntry, ...],
    config: CuratedTerminalCurriculumConfig,
) -> dict[str, Any]:
    mate1_fens = _unique(entry.fen for entry in entries if entry.stage_name == "Mate_In_1" and entry.mate_in_one_moves)
    mate2_fens = _unique(
        entry.fen
        for entry in entries
        if entry.stage_name == "Mate_In_2" and entry.forced_mate_in_two_first_moves
    )
    mate1_learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    mate1_train = tuple(fen for fen in mate1_fens for _ in range(config.train_repetitions))
    mate1_training = _train_terminal_mate_in_one(mate1_train, learner=mate1_learner)
    mate1_eval = _evaluate_terminal_mate_in_one(mate1_fens, learner=mate1_learner, max_samples=config.max_samples)
    mate2_learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    mate2_train = tuple(fen for fen in mate2_fens for _ in range(config.train_repetitions))
    mate2_training = _train_terminal_mate_in_two(
        mate2_train,
        first_learner=mate2_learner,
        mate_learner=mate1_learner,
    )
    mate2_eval = _evaluate_terminal_mate_in_two(
        mate2_fens,
        first_learner=mate2_learner,
        mate_learner=mate1_learner,
        max_samples=config.max_samples,
    )
    return {
        "dataset": {
            "mate1_unique_positions": len(mate1_fens),
            "mate1_train_records": len(mate1_train),
            "mate2_unique_positions": len(mate2_fens),
            "mate2_train_records": len(mate2_train),
            "source_labels_learner_visible": False,
        },
        "mate1": {
            "training": mate1_training,
            "evaluation": mate1_eval,
            "m4_consolidation_event_count": int(mate1_eval["accuracy"] >= 0.95 and mate1_learner.m3_update_count > 0),
        },
        "mate2": {
            "training": mate2_training,
            "evaluation": mate2_eval,
            "m4_consolidation_event_count": int(
                mate2_eval["conversion_rate"] >= 0.95 and mate2_learner.m3_update_count > 0
            ),
        },
        "terminal_counts": {
            "mate1": len(mate1_learner.terminals),
            "mate2_first": len(mate2_learner.terminals),
        },
    }


def _interpret(
    *,
    original_run: dict[str, Any],
    symmetry_run: dict[str, Any],
    inventory: dict[str, Any],
) -> dict[str, Any]:
    original_mate2 = original_run["mate2"]["evaluation"]["conversion_rate"]
    symmetry_mate2 = symmetry_run["mate2"]["evaluation"]["conversion_rate"]
    return {
        "old_curriculum_reuse_status": "active_curated_terminal_runway_added",
        "foundation_decision": (
            "use curated Mate_In_1 and Mate_In_2 as the primary near-term runway; "
            "keep random forced Mate_In_2 as generalization audit"
        ),
        "symmetry_interference_flag": symmetry_mate2 < original_mate2,
        "stage2_decision": (
            "old edge/fence stages are inventoried, but positions that are not immediate mate-in-one "
            "or forced mate-in-two remain later graded-rollout curriculum rather than classifier data"
        ),
        "m4_policy": "consolidate only per bucket after heldout/symmetry confirmation, not from labels alone",
        "inventory_entry_count": inventory["entry_count"],
    }


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _valid_krk_board(board: chess.Board) -> bool:
    return (
        board.turn == chess.WHITE
        and board.is_valid()
        and board.king(chess.WHITE) is not None
        and board.king(chess.BLACK) is not None
        and any(
            piece.piece_type == chess.ROOK and piece.color == chess.WHITE
            for piece in board.piece_map().values()
        )
        and not board.is_game_over(claim_draw=False)
    )


def _symmetry_boards(fen: str) -> tuple[tuple[str, chess.Board], ...]:
    board = chess.Board(fen)
    transforms = (
        ("identity", lambda item: item.copy(stack=False)),
        ("flip_horizontal", lambda item: item.transform(chess.flip_horizontal)),
        ("flip_vertical", lambda item: item.transform(chess.flip_vertical)),
        ("flip_diagonal", lambda item: item.transform(chess.flip_diagonal)),
        ("flip_anti_diagonal", lambda item: item.transform(chess.flip_anti_diagonal)),
    )
    return tuple((name, fn(board)) for name, fn in transforms)


def _normalize_board(board: chess.Board) -> chess.Board:
    normalized = board.copy(stack=False)
    normalized.turn = chess.WHITE
    normalized.castling_rights = 0
    normalized.ep_square = None
    normalized.halfmove_clock = 0
    normalized.fullmove_number = 1
    return normalized
