"""Stockfish cross-checks for curated KRK mate-in-two curriculum claims."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import shutil
from typing import Any

import chess
import chess.engine

from .curated_terminal_curriculum import CuratedStageEntry, curated_stage_entries
from .foundation_curriculum import _forced_mate_in_two_first_moves, _mate_moves


@dataclass(frozen=True)
class CuratedStockfishValidationConfig:
    stockfish_path: str
    depth: int = 16
    include_symmetries: bool = True
    threads: int = 1
    hash_mb: int = 32


@dataclass(frozen=True)
class CuratedStockfishValidationResult:
    config: CuratedStockfishValidationConfig
    engine: dict[str, Any]
    summary: dict[str, Any]
    rows: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26j_stockfish_mate2_validation.v0",
            "config": asdict(self.config),
            "scope": {
                "source": "src/recon_lite_chess/training/krk_curriculum.py::KRK_STAGES",
                "included_entries": [
                    "stage_name == Mate_In_2",
                    "optimal_moves == 2",
                ],
                "include_symmetries": self.config.include_symmetries,
                "note": (
                    "Stockfish is a cross-check. Exact KRK forced-mate-in-two status is also "
                    "computed by enumerating all legal first moves, black replies, and mate moves."
                ),
            },
            "engine": self.engine,
            "summary": self.summary,
            "rows": list(self.rows),
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def default_stockfish_path() -> str | None:
    return (
        os.environ.get("STOCKFISH_PATH")
        or shutil.which("stockfish")
        or ("/usr/games/stockfish" if Path("/usr/games/stockfish").exists() else None)
    )


def run_curated_stockfish_validation(
    *,
    config: CuratedStockfishValidationConfig,
) -> CuratedStockfishValidationResult:
    claims = _mate_two_claim_entries(include_symmetries=config.include_symmetries)
    with chess.engine.SimpleEngine.popen_uci(config.stockfish_path) as engine:
        _configure_engine(engine, config)
        rows = tuple(_validate_entry(engine=engine, entry=entry, depth=config.depth) for entry in claims)
        engine_id = dict(engine.id)
    return CuratedStockfishValidationResult(
        config=config,
        engine=engine_id,
        summary=_summarize(rows),
        rows=rows,
    )


def _mate_two_claim_entries(*, include_symmetries: bool) -> tuple[CuratedStageEntry, ...]:
    entries = curated_stage_entries(include_symmetries=include_symmetries)
    return tuple(
        entry
        for entry in entries
        if entry.stage_name == "Mate_In_2" or entry.optimal_moves == 2
    )


def _configure_engine(
    engine: chess.engine.SimpleEngine,
    config: CuratedStockfishValidationConfig,
) -> None:
    options: dict[str, Any] = {}
    if "Threads" in engine.options:
        options["Threads"] = config.threads
    if "Hash" in engine.options:
        options["Hash"] = config.hash_mb
    if options:
        engine.configure(options)


def _validate_entry(
    *,
    engine: chess.engine.SimpleEngine,
    entry: CuratedStageEntry,
    depth: int,
) -> dict[str, Any]:
    board = chess.Board(entry.fen)
    exact = _exact_classification(board)
    stockfish: dict[str, Any]
    if not entry.valid:
        stockfish = {
            "classification": "invalid_fen",
            "mate_score": None,
            "centipawn_score": None,
            "bestmove": None,
            "pv": [],
        }
    else:
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        score = info["score"].pov(board.turn)
        pv = [move.uci() for move in info.get("pv", [])]
        mate_score = score.mate()
        stockfish = {
            "classification": _stockfish_classification(mate_score),
            "mate_score": mate_score,
            "centipawn_score": score.score(mate_score=100000),
            "bestmove": pv[0] if pv else None,
            "pv": pv,
            "depth": info.get("depth"),
            "seldepth": info.get("seldepth"),
            "nodes": info.get("nodes"),
        }
    return {
        "stage_index": entry.stage_index,
        "stage_id": entry.stage_id,
        "stage_name": entry.stage_name,
        "position_index": entry.position_index,
        "symmetry": entry.symmetry,
        "fen": entry.fen,
        "optimal_moves": entry.optimal_moves,
        "description": entry.description,
        "claim_types": _claim_types(entry),
        "python_chess_valid": entry.valid,
        "exact": exact,
        "stockfish": stockfish,
        "agrees_strict_mate_in_two": (
            exact["classification"] == "strict_forced_mate_in_two"
            and stockfish["classification"] == "stockfish_mate_in_2"
        ),
    }


def _claim_types(entry: CuratedStageEntry) -> tuple[str, ...]:
    claims: list[str] = []
    if entry.stage_name == "Mate_In_2":
        claims.append("stage_name_mate_in_2")
    if entry.optimal_moves == 2:
        claims.append("optimal_moves_2")
    return tuple(claims)


def _exact_classification(board: chess.Board) -> dict[str, Any]:
    if not (
        board.turn == chess.WHITE
        and board.is_valid()
        and not board.is_game_over(claim_draw=False)
    ):
        return {
            "classification": "invalid_or_terminal",
            "mate_in_one_moves": [],
            "forced_mate_in_two_first_moves": [],
        }
    mate1 = tuple(move.uci() for move in _mate_moves(board))
    forced2 = tuple(move.uci() for move in _forced_mate_in_two_first_moves(board))
    if mate1:
        classification = "mate_in_one"
    elif forced2:
        classification = "strict_forced_mate_in_two"
    else:
        classification = "not_strict_forced_mate_in_two"
    return {
        "classification": classification,
        "mate_in_one_moves": mate1,
        "forced_mate_in_two_first_moves": forced2,
    }


def _stockfish_classification(mate_score: int | None) -> str:
    if mate_score == 1:
        return "stockfish_mate_in_1"
    if mate_score == 2:
        return "stockfish_mate_in_2"
    if mate_score is not None and mate_score > 2:
        return "stockfish_mate_longer"
    if mate_score is not None and mate_score <= 0:
        return "stockfish_mated_or_drawish"
    return "stockfish_no_forced_mate_at_depth"


def _summarize(rows: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    by_stockfish: dict[str, int] = {}
    by_exact: dict[str, int] = {}
    by_stage: dict[str, dict[str, int]] = {}
    disagreements: list[dict[str, Any]] = []
    for row in rows:
        stockfish_class = row["stockfish"]["classification"]
        exact_class = row["exact"]["classification"]
        by_stockfish[stockfish_class] = by_stockfish.get(stockfish_class, 0) + 1
        by_exact[exact_class] = by_exact.get(exact_class, 0) + 1
        stage = by_stage.setdefault(row["stage_name"], {"total": 0, "stockfish_mate_in_2": 0, "strict_exact_mate_in_2": 0})
        stage["total"] += 1
        stage["stockfish_mate_in_2"] += int(stockfish_class == "stockfish_mate_in_2")
        stage["strict_exact_mate_in_2"] += int(exact_class == "strict_forced_mate_in_two")
        if not row["agrees_strict_mate_in_two"]:
            disagreements.append({
                "stage_name": row["stage_name"],
                "position_index": row["position_index"],
                "symmetry": row["symmetry"],
                "fen": row["fen"],
                "description": row["description"],
                "exact": exact_class,
                "stockfish": stockfish_class,
                "mate_score": row["stockfish"]["mate_score"],
                "bestmove": row["stockfish"]["bestmove"],
            })
    return {
        "total_claim_entries": len(rows),
        "stockfish_classification_counts": dict(sorted(by_stockfish.items())),
        "exact_classification_counts": dict(sorted(by_exact.items())),
        "by_stage": dict(sorted(by_stage.items())),
        "strict_stockfish_and_exact_mate_in_2_count": sum(
            int(row["agrees_strict_mate_in_two"]) for row in rows
        ),
        "non_strict_or_disagreeing_count": len(disagreements),
        "non_strict_or_disagreeing_examples": disagreements[:40],
    }
