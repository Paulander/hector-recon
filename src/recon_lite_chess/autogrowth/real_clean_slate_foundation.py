"""TG46b real clean-slate KRK foundation runner.

This checkpoint replaces the TG46 synthetic clean-slate scaffold with a real
Mate-in-1 / Mate-in-2 foundation run over generated KRK FENs. It still uses the
terminal substrate rather than the full historical tick engine, but all
behavior-changing training and evaluation is mediated by terminal/stem-cell
weights created in this fresh run.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any, Iterable

import chess

from .foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _generate_forced_mate_in_two_positions,
    _generate_mate_in_one_positions,
    _mate_moves,
)
from .terminal_substrate import (
    TerminalAffordanceLearner,
    terminal_action_feature_keys,
)


DEFAULT_OUTPUT_DIR = Path("reports/autogrowth/clean_slate_krk/tg46b_real_foundation")


@dataclass(frozen=True)
class RealCleanSlateFoundationConfig:
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    output_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg46b_real_clean_slate_foundation.json")
    progress_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg46b_real_clean_slate_foundation_progress.json")
    markdown_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg46b_real_clean_slate_foundation.md")
    mate1_train_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46b_mate1_train_traces.jsonl.gz")
    mate1_eval_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46b_mate1_eval_traces.jsonl.gz")
    mate2_train_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46b_mate2_train_traces.jsonl.gz")
    mate2_eval_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46b_mate2_eval_traces.jsonl.gz")
    failure_pool_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46b_failure_pool.jsonl.gz")
    graph_summary_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46b_graph_summary.json")
    seed: int = 20260628
    mate1_train_count: int = 300
    mate1_heldout_count: int = 100
    mate2_train_count: int = 300
    mate2_heldout_count: int = 100
    max_generation_attempts: int = 500_000
    eta_m3: float = 0.10
    rich_feature_credit_scale: float = 0.25
    mate1_pass_threshold: float = 0.99
    mate2_pass_threshold: float = 0.90
    max_trace_samples: int = 16
    fresh_graph: bool = True


@dataclass(frozen=True)
class RealCleanSlateFoundationResult:
    config: RealCleanSlateFoundationConfig
    payload: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_tg46b_real_clean_slate_foundation.v0",
            "checkpoint": "TG46b_real_clean_slate_krk_foundation",
            "config": asdict(self.config),
            **self.payload,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path | None = None) -> Path:
        output = Path(path or self.config.output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_real_clean_slate_krk_foundation(
    *,
    config: RealCleanSlateFoundationConfig,
) -> RealCleanSlateFoundationResult:
    if not config.fresh_graph:
        raise ValueError("TG46b requires fresh_graph=True")

    start = time.perf_counter()
    for path in (
        config.mate1_train_trace_path,
        config.mate1_eval_trace_path,
        config.mate2_train_trace_path,
        config.mate2_eval_trace_path,
        config.failure_pool_path,
        config.graph_summary_path,
        config.output_path,
        config.progress_path,
        config.markdown_path,
    ):
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    scaffold_audit = _audit_tg46_scaffold()
    progress: dict[str, Any] = {
        "schema_version": "krk_tg46b_real_clean_slate_foundation_progress.v0",
        "checkpoint": "TG46b_real_clean_slate_krk_foundation",
        "started_at_monotonic": start,
        "phases": [],
    }
    _write_json(config.progress_path, progress)

    mate1_learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    mate2_first_learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    failure_rows: list[dict[str, Any]] = []

    phase_start = time.perf_counter()
    mate1_train_fens = tuple(_generate_mate_in_one_positions(
        count=config.mate1_train_count,
        seed=config.seed,
        max_attempts=config.max_generation_attempts,
    ))
    mate1_heldout_fens = tuple(_generate_mate_in_one_positions(
        count=config.mate1_heldout_count,
        seed=config.seed + 1,
        excluded=set(mate1_train_fens),
        max_attempts=config.max_generation_attempts,
    ))
    progress["phases"].append(_phase("generate_mate1", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    mate1_training = _train_mate_in_one_real(
        mate1_train_fens,
        learner=mate1_learner,
        trace_path=Path(config.mate1_train_trace_path),
        max_trace_samples=config.max_trace_samples,
    )
    progress["phases"].append(_phase("train_mate1", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    mate1_heldout = _evaluate_mate_in_one_real(
        mate1_heldout_fens,
        learner=mate1_learner,
        trace_path=Path(config.mate1_eval_trace_path),
        failure_rows=failure_rows,
        max_trace_samples=config.max_trace_samples,
    )
    progress["phases"].append(_phase("evaluate_mate1", phase_start))
    _write_json(config.progress_path, progress)

    mate1_pass = mate1_heldout["accuracy"] >= config.mate1_pass_threshold
    mate2_training: dict[str, Any] = {"skipped": True, "reason": "mate1_failed"}
    mate2_heldout: dict[str, Any] = {"skipped": True, "reason": "mate1_failed"}
    mate2_train_fens: tuple[str, ...] = ()
    mate2_heldout_fens: tuple[str, ...] = ()

    if mate1_pass:
        phase_start = time.perf_counter()
        used = set(mate1_train_fens) | set(mate1_heldout_fens)
        mate2_train_fens = tuple(_generate_forced_mate_in_two_positions(
            count=config.mate2_train_count,
            seed=config.seed + 2,
            excluded=used,
            max_attempts=config.max_generation_attempts,
        ))
        mate2_heldout_fens = tuple(_generate_forced_mate_in_two_positions(
            count=config.mate2_heldout_count,
            seed=config.seed + 3,
            excluded=used | set(mate2_train_fens),
            max_attempts=config.max_generation_attempts,
        ))
        progress["phases"].append(_phase("generate_mate2", phase_start))
        _write_json(config.progress_path, progress)

        phase_start = time.perf_counter()
        mate2_training = _train_mate_in_two_real(
            mate2_train_fens,
            first_learner=mate2_first_learner,
            mate_learner=mate1_learner,
            trace_path=Path(config.mate2_train_trace_path),
            max_trace_samples=config.max_trace_samples,
        )
        progress["phases"].append(_phase("train_mate2", phase_start))
        _write_json(config.progress_path, progress)

        phase_start = time.perf_counter()
        mate2_heldout = _evaluate_mate_in_two_real(
            mate2_heldout_fens,
            first_learner=mate2_first_learner,
            mate_learner=mate1_learner,
            trace_path=Path(config.mate2_eval_trace_path),
            failure_rows=failure_rows,
            max_trace_samples=config.max_trace_samples,
        )
        progress["phases"].append(_phase("evaluate_mate2", phase_start))
        _write_json(config.progress_path, progress)

    graph_summary = _graph_summary(
        mate1_learner=mate1_learner,
        mate2_first_learner=mate2_first_learner,
        mate1_training=mate1_training,
        mate2_training=mate2_training,
    )
    _write_json(config.graph_summary_path, graph_summary)
    _write_jsonl_gzip(Path(config.failure_pool_path), failure_rows)

    mate2_pass = (
        not mate2_heldout.get("skipped", False)
        and mate2_heldout["conversion_rate"] >= config.mate2_pass_threshold
    )
    train_manifest = {
        "mate1_train_count": len(mate1_train_fens),
        "mate1_heldout_count": len(mate1_heldout_fens),
        "mate2_train_count": len(mate2_train_fens),
        "mate2_heldout_count": len(mate2_heldout_fens),
        "mate1_train_hash": _hash_json(mate1_train_fens),
        "mate1_heldout_hash": _hash_json(mate1_heldout_fens),
        "mate2_train_hash": _hash_json(mate2_train_fens),
        "mate2_heldout_hash": _hash_json(mate2_heldout_fens),
    }
    graph_hash = _hash_json(graph_summary)
    artifact_hashes = {
        "graph_summary_hash": graph_hash,
        "failure_pool_hash": _file_sha256(config.failure_pool_path),
        "mate1_train_trace_hash": _file_sha256(config.mate1_train_trace_path),
        "mate1_eval_trace_hash": _file_sha256(config.mate1_eval_trace_path),
        "mate2_train_trace_hash": _file_sha256(config.mate2_train_trace_path),
        "mate2_eval_trace_hash": _file_sha256(config.mate2_eval_trace_path),
    }

    total_seconds = round(time.perf_counter() - start, 6)
    decision = _decision(
        config=config,
        scaffold_audit=scaffold_audit,
        mate1_heldout=mate1_heldout,
        mate2_heldout=mate2_heldout,
        mate1_pass=mate1_pass,
        mate2_pass=mate2_pass,
        graph_summary=graph_summary,
        failure_count=len(failure_rows),
        total_seconds=total_seconds,
    )
    payload = {
        "provenance": {
            "git_head": _git_head(),
            "fresh_graph": True,
            "loaded_prior_tg_artifact_count": 0,
            "loaded_prior_learned_node_count": 0,
            "loaded_prior_m3_weight_count": 0,
            "loaded_prior_m4_promotion_count": 0,
            "parent_graph_hash": None,
            "config_hash": _hash_json(asdict(config)),
            "train_manifest_hash": _hash_json(train_manifest),
            "feature_schema_hash": _hash_json(_feature_schema_sample(mate1_train_fens[0])),
            "evaluator_version_hash": _hash_json({
                "mate1": "legal_move_after_is_checkmate",
                "mate2": "all_black_replies_have_mate_in_one",
            }),
        },
        "synthetic_tg46_audit": scaffold_audit,
        "training_runway": {
            "generated_krk_fens_used": True,
            "real_mate1_positions_used": True,
            "real_mate2_positions_used": True,
            "real_legal_move_evaluation_used": True,
            "curriculum_labels_trainer_side_only": True,
            "learner_visible_stage_labels": False,
            "learner_visible_basin_labels": False,
        },
        "runtime_structure": {
            "real_graph_training_used": True,
            "real_graph_evaluation_used": True,
            "terminal_stem_cell_nodes_used": True,
            "m3_updates_modify_terminal_weights": True,
            "same_fresh_graph_used_for_mate1_then_mate2": True,
            "same_graph_continuation_used_for_mate2_second_moves": True,
            "runtime_choice": "terminal_weighted_legal_affordance_selection",
            "remaining_caveat": (
                "legal move affordances are enumerated by the environment and scored by "
                "terminal activation weights; this is not the synthetic TG46 target-rate scaffold"
            ),
        },
        "dataset": train_manifest,
        "mate1": {
            "training": mate1_training,
            "heldout": mate1_heldout,
        },
        "mate2": {
            "training": mate2_training,
            "heldout": mate2_heldout,
        },
        "graph_summary": graph_summary,
        "artifact_paths": {
            "main": config.output_path,
            "progress": config.progress_path,
            "markdown": config.markdown_path,
            "mate1_train_trace": config.mate1_train_trace_path,
            "mate1_eval_trace": config.mate1_eval_trace_path,
            "mate2_train_trace": config.mate2_train_trace_path,
            "mate2_eval_trace": config.mate2_eval_trace_path,
            "failure_pool": config.failure_pool_path,
            "graph_summary": config.graph_summary_path,
        },
        "artifact_hashes": artifact_hashes,
        "timing": {
            "total_seconds": total_seconds,
            "phases": progress["phases"],
        },
        "purity_boundary": _purity_boundary(),
    }
    result = RealCleanSlateFoundationResult(config=config, payload=payload, decision=decision)
    result.write_json()
    _write_json(config.progress_path, {**progress, "completed": True, "decision": decision})
    _write_markdown(config, decision, payload)
    return result


def _train_mate_in_one_real(
    fens: Iterable[str],
    *,
    learner: TerminalAffordanceLearner,
    trace_path: Path,
    max_trace_samples: int,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    totals = {"positive": 0, "negative": 0, "neutral": 0}
    before_updates = learner.m3_update_count
    for index, fen in enumerate(fens):
        board = chess.Board(fen)
        positives = {move.uci() for move in _mate_moves(board)}
        selected_before = learner.choose(board)
        updates = learner.train_position(board, positive_moves=positives)
        selected_after = learner.choose(board)
        for key in totals:
            totals[key] += updates[key]
        rows.append({
            "trace_type": "mate1_train",
            "index": index,
            "fen": fen,
            "positive_mating_moves": sorted(positives),
            "legal_move_count": board.legal_moves.count(),
            "selected_before": None if selected_before is None else selected_before.uci(),
            "selected_after": None if selected_after is None else selected_after.uci(),
            "updates": updates,
            "terminal_count_after": len(learner.terminals),
        })
    _write_jsonl_gzip(trace_path, rows)
    return {
        "position_count": len(rows),
        "positive_updates": totals["positive"],
        "negative_updates": totals["negative"],
        "neutral_updates": totals["neutral"],
        "m3_update_count_delta": learner.m3_update_count - before_updates,
        "m3_update_count_total": learner.m3_update_count,
        "terminal_count": len(learner.terminals),
        "samples": rows[:max_trace_samples],
    }


def _evaluate_mate_in_one_real(
    fens: Iterable[str],
    *,
    learner: TerminalAffordanceLearner,
    trace_path: Path,
    failure_rows: list[dict[str, Any]],
    max_trace_samples: int,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    correct = 0
    null = 0
    rook_blunder = 0
    stalemate = 0
    illegal = 0
    for index, fen in enumerate(fens):
        board = chess.Board(fen)
        positives = {move.uci() for move in _mate_moves(board)}
        selected = learner.choose(board)
        selected_uci = None if selected is None else selected.uci()
        is_legal = selected in board.legal_moves if selected is not None else False
        is_correct = selected_uci in positives if selected_uci is not None else False
        flags = _outcome_flags(board, selected)
        correct += int(is_correct)
        null += int(selected is None)
        illegal += int(selected is not None and not is_legal)
        rook_blunder += int(flags["rook_missing_or_capturable"])
        stalemate += int(flags["stalemate"])
        row = {
            "trace_type": "mate1_eval",
            "index": index,
            "fen": fen,
            "positive_mating_moves": sorted(positives),
            "selected": selected_uci,
            "correct": is_correct,
            "legal": is_legal,
            "active_terminal_count": 0 if selected is None else learner.active_terminal_count(board, selected),
            "selected_weight": None if selected is None else round(learner.weight_for_move(board, selected), 6),
            "outcome_flags": flags,
        }
        rows.append(row)
        if not is_correct:
            failure_rows.append({**row, "failure_stage": "mate1_heldout"})
    _write_jsonl_gzip(trace_path, rows)
    total = len(rows)
    return {
        "position_count": total,
        "correct_count": correct,
        "accuracy": 0.0 if total == 0 else correct / total,
        "wrong_action_count": total - correct,
        "null_selection_count": null,
        "illegal_move_count": illegal,
        "rook_blunder_count": rook_blunder,
        "stalemate_count": stalemate,
        "samples": rows[:max_trace_samples],
    }


def _train_mate_in_two_real(
    fens: Iterable[str],
    *,
    first_learner: TerminalAffordanceLearner,
    mate_learner: TerminalAffordanceLearner,
    trace_path: Path,
    max_trace_samples: int,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    first_totals = {"positive": 0, "negative": 0, "neutral": 0}
    before_first = first_learner.m3_update_count
    before_mate = mate_learner.m3_update_count
    reply_training_positions = 0
    for index, fen in enumerate(fens):
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        selected_before = first_learner.choose(board)
        updates = first_learner.train_position(board, positive_moves=forced)
        selected_after = first_learner.choose(board)
        for key in first_totals:
            first_totals[key] += updates[key]
        reply_rows = []
        for first in _forced_mate_in_two_first_moves(board):
            after_first = board.copy(stack=False)
            after_first.push(first)
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_reply_mate = after_first.copy(stack=False)
                before_reply_mate.push(reply)
                positives = {move.uci() for move in _mate_moves(before_reply_mate)}
                if not positives:
                    continue
                mate_learner.train_position(before_reply_mate, positive_moves=positives)
                reply_training_positions += 1
                if len(reply_rows) < 8:
                    reply_rows.append({
                        "forced_first": first.uci(),
                        "black_reply": reply.uci(),
                        "mate_moves": sorted(positives),
                    })
        rows.append({
            "trace_type": "mate2_train",
            "index": index,
            "fen": fen,
            "forced_first_moves": sorted(forced),
            "legal_move_count": board.legal_moves.count(),
            "selected_before": None if selected_before is None else selected_before.uci(),
            "selected_after": None if selected_after is None else selected_after.uci(),
            "first_updates": updates,
            "reply_training_sample": reply_rows,
            "first_terminal_count_after": len(first_learner.terminals),
            "mate_terminal_count_after": len(mate_learner.terminals),
        })
    _write_jsonl_gzip(trace_path, rows)
    return {
        "position_count": len(rows),
        "first_move_positive_updates": first_totals["positive"],
        "first_move_negative_updates": first_totals["negative"],
        "first_move_neutral_updates": first_totals["neutral"],
        "first_learner_m3_update_count_delta": first_learner.m3_update_count - before_first,
        "mate_learner_extra_m3_update_count_delta": mate_learner.m3_update_count - before_mate,
        "reply_training_position_count": reply_training_positions,
        "first_terminal_count": len(first_learner.terminals),
        "mate_terminal_count": len(mate_learner.terminals),
        "samples": rows[:max_trace_samples],
    }


def _evaluate_mate_in_two_real(
    fens: Iterable[str],
    *,
    first_learner: TerminalAffordanceLearner,
    mate_learner: TerminalAffordanceLearner,
    trace_path: Path,
    failure_rows: list[dict[str, Any]],
    max_trace_samples: int,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    first_success = 0
    converted = 0
    replied_total = 0
    replied_mated = 0
    one_reply_false_positive = 0
    null = 0
    rook_blunder = 0
    stalemate = 0
    illegal = 0
    same_graph_continuation_count = 0
    for index, fen in enumerate(fens):
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        selected = first_learner.choose(board)
        selected_uci = None if selected is None else selected.uci()
        first_ok = selected_uci in forced if selected_uci is not None else False
        flags = _outcome_flags(board, selected)
        null += int(selected is None)
        illegal += int(selected is not None and selected not in board.legal_moves)
        rook_blunder += int(flags["rook_missing_or_capturable"])
        stalemate += int(flags["stalemate"])
        first_success += int(first_ok)
        all_replies_mated = False
        any_reply_mated = False
        reply_rows = []
        if selected is not None and selected in board.legal_moves:
            after_first = board.copy(stack=False)
            after_first.push(selected)
            all_replies_mated = True
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_mate = after_first.copy(stack=False)
                before_mate.push(reply)
                mates = {move.uci() for move in _mate_moves(before_mate)}
                mate_move = mate_learner.choose(before_mate)
                mate_uci = None if mate_move is None else mate_move.uci()
                ok = mate_uci in mates if mate_uci is not None else False
                replied_total += 1
                replied_mated += int(ok)
                same_graph_continuation_count += int(ok)
                any_reply_mated = any_reply_mated or ok
                all_replies_mated = all_replies_mated and ok
                reply_rows.append({
                    "black_reply": reply.uci(),
                    "selected_mate": mate_uci,
                    "correct_mates": sorted(mates),
                    "mated": ok,
                })
        conversion = first_ok and all_replies_mated
        converted += int(conversion)
        one_reply_false_positive += int(any_reply_mated and not conversion)
        row = {
            "trace_type": "mate2_eval",
            "index": index,
            "fen": fen,
            "forced_first_moves": sorted(forced),
            "selected_first": selected_uci,
            "first_move_success": first_ok,
            "all_replies_mated": all_replies_mated,
            "conversion": conversion,
            "any_reply_mated": any_reply_mated,
            "selected_first_active_terminal_count": (
                0 if selected is None else first_learner.active_terminal_count(board, selected)
            ),
            "selected_first_weight": None if selected is None else round(first_learner.weight_for_move(board, selected), 6),
            "reply_checks": reply_rows,
            "outcome_flags": flags,
        }
        rows.append(row)
        if not conversion:
            failure_rows.append({**row, "failure_stage": "mate2_heldout"})
    _write_jsonl_gzip(trace_path, rows)
    total = len(rows)
    return {
        "position_count": total,
        "first_move_success_count": first_success,
        "first_move_success_rate": 0.0 if total == 0 else first_success / total,
        "conversion_count": converted,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "forced_mate_reply_coverage": 0.0 if replied_total == 0 else replied_mated / replied_total,
        "reply_evaluation_count": replied_total,
        "same_graph_continuation_count": same_graph_continuation_count,
        "one_reply_false_positive_selected_count": one_reply_false_positive,
        "wrong_first_move_count": total - first_success,
        "null_selection_count": null,
        "illegal_move_count": illegal,
        "rook_blunder_count": rook_blunder,
        "stalemate_count": stalemate,
        "samples": rows[:max_trace_samples],
    }


def _outcome_flags(board: chess.Board, move: chess.Move | None) -> dict[str, bool]:
    if move is None or move not in board.legal_moves:
        return {"stalemate": False, "checkmate": False, "rook_missing_or_capturable": False}
    after = board.copy(stack=False)
    after.push(move)
    rook = next((sq for sq, piece in after.piece_map().items() if piece.symbol() == "R"), None)
    rook_bad = rook is None or after.is_attacked_by(chess.BLACK, rook)
    return {
        "stalemate": after.is_stalemate(),
        "checkmate": after.is_checkmate(),
        "rook_missing_or_capturable": rook_bad,
    }


def _graph_summary(
    *,
    mate1_learner: TerminalAffordanceLearner,
    mate2_first_learner: TerminalAffordanceLearner,
    mate1_training: dict[str, Any],
    mate2_training: dict[str, Any],
) -> dict[str, Any]:
    terminal_state_counts: dict[str, int] = {}
    for learner in (mate1_learner, mate2_first_learner):
        for terminal in learner.terminals.values():
            name = terminal.cell.state.name
            terminal_state_counts[name] = terminal_state_counts.get(name, 0) + 1
    mate1_terminal_count = len(mate1_learner.terminals)
    mate2_terminal_count = len(mate2_first_learner.terminals)
    return {
        "schema_version": "krk_tg46b_graph_summary.v0",
        "node_model": "fresh_terminal_stem_cell_graph",
        "root_node_count": 1,
        "script_node_count": 2,
        "terminal_node_count": mate1_terminal_count + mate2_terminal_count,
        "mate1_terminal_count": mate1_terminal_count,
        "mate2_first_terminal_count": mate2_terminal_count,
        "edge_count_estimate": 3 * (mate1_terminal_count + mate2_terminal_count),
        "terminal_state_counts": terminal_state_counts,
        "mature_materialized_count": terminal_state_counts.get("MATURE", 0),
        "trial_node_count": terminal_state_counts.get("TRIAL", 0),
        "dead_or_pruned_node_count": terminal_state_counts.get("PRUNED", 0),
        "m3_update_count": mate1_learner.m3_update_count + mate2_first_learner.m3_update_count,
        "m3_update_count_by_subgraph": {
            "mate1_and_continuation": mate1_learner.m3_update_count,
            "mate2_first_move": mate2_first_learner.m3_update_count,
        },
        "m4_true_promotion_count": 0,
        "m4_note": "TG46b proves fresh foundation training/evaluation; M4 promotion remains conservative.",
        "top_mate1_terminals": mate1_learner.to_dict(max_terminals=8),
        "top_mate2_first_terminals": mate2_first_learner.to_dict(max_terminals=8),
        "training_update_summary": {
            "mate1": mate1_training,
            "mate2": mate2_training,
        },
    }


def _decision(
    *,
    config: RealCleanSlateFoundationConfig,
    scaffold_audit: dict[str, Any],
    mate1_heldout: dict[str, Any],
    mate2_heldout: dict[str, Any],
    mate1_pass: bool,
    mate2_pass: bool,
    graph_summary: dict[str, Any],
    failure_count: int,
    total_seconds: float,
) -> dict[str, Any]:
    checkpoint_pass = mate1_pass and mate2_pass
    if not mate1_pass:
        interpretation = "real_clean_slate_foundation_failed_at_mate1"
        next_action = "repair_real_mate1_foundation"
    elif not mate2_pass:
        interpretation = "real_clean_slate_foundation_failed_at_mate2"
        next_action = "repair_real_mate2_foundation"
    else:
        interpretation = "real_clean_slate_foundation_pass_mate1_mate2_only"
        next_action = "tg47_real_edge_fence_inside_clean_pipeline"
    return {
        "checkpoint_pass": checkpoint_pass,
        "checkpoint_interpretation": interpretation,
        "synthetic_tg46_target_rate_paths_detected": scaffold_audit["target_rate_path_detected"],
        "synthetic_tg46_success_counts_detected": scaffold_audit["synthetic_success_count_detected"],
        "synthetic_tg46_placeholder_fens_detected": scaffold_audit["placeholder_fen_detected"],
        "synthetic_tg46_graph_growth_detected": scaffold_audit["synthetic_graph_growth_detected"],
        "synthetic_tg46_ablations_detected": scaffold_audit["synthetic_ablation_detected"],
        "synthetic_stage_runner_used_in_result": False,
        "fresh_graph": True,
        "generated_krk_fens_used": True,
        "placeholder_fens_used": False,
        "real_legal_move_evaluation_used": True,
        "real_graph_training_used": True,
        "real_graph_evaluation_used": True,
        "real_graph_artifact_written": True,
        "real_failure_pool_used": True,
        "loaded_prior_tg_artifact_count": 0,
        "loaded_prior_learned_node_count": 0,
        "loaded_prior_m3_weight_count": 0,
        "loaded_prior_m4_promotion_count": 0,
        "mate1_train_count": config.mate1_train_count,
        "mate1_heldout_count": mate1_heldout["position_count"],
        "mate1_heldout_accuracy": mate1_heldout["accuracy"],
        "mate1_correct_count": mate1_heldout["correct_count"],
        "mate1_null_selection_count": mate1_heldout["null_selection_count"],
        "mate2_train_count": config.mate2_train_count,
        "mate2_heldout_count": mate2_heldout.get("position_count", 0),
        "mate2_heldout_conversion_rate": mate2_heldout.get("conversion_rate", 0.0),
        "mate2_conversion_count": mate2_heldout.get("conversion_count", 0),
        "mate2_first_move_success_rate": mate2_heldout.get("first_move_success_rate", 0.0),
        "mate2_forced_reply_coverage": mate2_heldout.get("forced_mate_reply_coverage", 0.0),
        "same_graph_continuation_count": mate2_heldout.get("same_graph_continuation_count", 0),
        "one_reply_false_positive_selected_count": mate2_heldout.get("one_reply_false_positive_selected_count", 0),
        "failure_pool_entry_count": failure_count,
        "m3_update_count": graph_summary["m3_update_count"],
        "m4_true_promotion_count": graph_summary["m4_true_promotion_count"],
        "mature_materialized_count": graph_summary["mature_materialized_count"],
        "trial_node_count": graph_summary["trial_node_count"],
        "terminal_node_count": graph_summary["terminal_node_count"],
        "rook_blunder_count": mate1_heldout["rook_blunder_count"] + mate2_heldout.get("rook_blunder_count", 0),
        "illegal_move_count": mate1_heldout["illegal_move_count"] + mate2_heldout.get("illegal_move_count", 0),
        "stalemate_count": mate1_heldout["stalemate_count"] + mate2_heldout.get("stalemate_count", 0),
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "learner_visible_stage_labels": False,
        "learner_visible_basin_labels": False,
        "learner_visible_continuation_labels": False,
        "curriculum_labels_trainer_side_only": True,
        "total_seconds": total_seconds,
        "selected_next_action": next_action,
        "selected_next_action_reason": (
            "Mate-in-1 and Mate-in-2 passed real generated clean-slate foundation thresholds"
            if checkpoint_pass else interpretation
        ),
        "purity_boundary": _purity_boundary(),
    }


def _audit_tg46_scaffold() -> dict[str, Any]:
    path = Path("src/recon_lite_chess/autogrowth/clean_slate_full_curriculum.py")
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return {
        "audited_path": str(path),
        "target_rate_path_detected": "target_rate" in text,
        "synthetic_success_count_detected": "heldout_success_count" in text or "success_count" in text,
        "placeholder_fen_detected": "generated_clean_slate" in text or "failure_fen" in text,
        "synthetic_graph_growth_detected": "node_growth" in text or "edge_growth" in text,
        "synthetic_ablation_detected": "_stage_ablations" in text or "ablation" in text,
        "used_in_tg46b_result": False,
    }


def _purity_boundary() -> dict[str, bool]:
    return {
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "stage_labels_learner_visible": False,
        "basin_labels_learner_visible": False,
        "trajectory_labels_learner_visible": False,
        "quality_tier_labels_learner_visible": False,
        "depth_labels_learner_visible": False,
        "reply_policy_labels_learner_visible": False,
        "trainer_side_legal_move_labels_used": True,
        "trainer_side_curriculum_distribution_used": True,
    }


def _feature_schema_sample(fen: str) -> tuple[str, ...]:
    board = chess.Board(fen)
    first_move = next(iter(sorted(board.legal_moves, key=lambda item: item.uci())))
    return tuple(key.split("=", 1)[0] for key, _scale in terminal_action_feature_keys(board, first_move))


def _phase(name: str, phase_start: float) -> dict[str, Any]:
    return {"phase": name, "seconds": round(time.perf_counter() - phase_start, 6)}


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl_gzip(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _hash_json(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()
    except Exception:
        return None


def _write_markdown(
    config: RealCleanSlateFoundationConfig,
    decision: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    lines = [
        "# TG46b Real Clean-Slate KRK Foundation",
        "",
        f"Checkpoint pass: `{decision['checkpoint_pass']}`",
        f"Interpretation: `{decision['checkpoint_interpretation']}`",
        "",
        "TG46b audits the earlier TG46 synthetic scaffold and does not use it for the result.",
        "The run uses generated KRK Mate-in-1 and forced Mate-in-2 FENs, legal move labels,",
        "fresh terminal/stem-cell graph weights, and real heldout failures.",
        "",
        "## Metrics",
        "",
        f"- Mate-in-1 heldout: {decision['mate1_correct_count']}/{decision['mate1_heldout_count']} "
        f"({decision['mate1_heldout_accuracy']:.3f})",
        f"- Mate-in-2 heldout conversion: {decision['mate2_conversion_count']}/{decision['mate2_heldout_count']} "
        f"({decision['mate2_heldout_conversion_rate']:.3f})",
        f"- Same-graph continuation count: {decision['same_graph_continuation_count']}",
        f"- Failure pool entries: {decision['failure_pool_entry_count']}",
        f"- Terminal nodes: {decision['terminal_node_count']}",
        f"- M3 updates: {decision['m3_update_count']}",
        "",
        "## Next",
        "",
        f"`{decision['selected_next_action']}`",
        "",
        "## Artifacts",
        "",
    ]
    for name, path in payload["artifact_paths"].items():
        lines.append(f"- {name}: `{path}`")
    Path(config.markdown_path).write_text("\n".join(lines) + "\n", encoding="utf-8")

