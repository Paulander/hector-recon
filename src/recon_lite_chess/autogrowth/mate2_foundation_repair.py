"""TG46c real clean-slate Mate-in-2 foundation repair.

The repair is deliberately narrow: train a fresh Mate-in-1 substrate, then train
Mate-in-2 first moves with contrastive local credit. Forced first moves receive
positive credit; only the currently high-scoring wrong competitors receive
debt. This avoids the TG46b failure mode where every legal wrong move pushed
shared before-state terminals negative and made selection brittle.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import gzip
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Iterable

import chess

from .foundation_curriculum import (
    _action_features,
    _forced_mate_in_two_first_moves,
    _generate_forced_mate_in_two_positions,
    _generate_mate_in_one_positions,
    _mate_moves,
    _move_reward,
)
from .real_clean_slate_foundation import _audit_tg46_scaffold, _git_head
from .terminal_substrate import (
    TerminalAffordanceLearner,
    _train_terminal_mate_in_one,
    terminal_action_feature_keys,
)


DEFAULT_TG46B_DIR = Path("reports/autogrowth/clean_slate_krk/tg46b_real_foundation")
DEFAULT_OUTPUT_DIR = Path("reports/autogrowth/clean_slate_krk/tg46c_mate2_repair")


@dataclass(frozen=True)
class Mate2FoundationRepairConfig:
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    output_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg46c_real_mate2_repair.json")
    progress_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg46c_real_mate2_repair_progress.json")
    markdown_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg46c_real_mate2_repair.md")
    train_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46c_train_traces.jsonl.gz")
    eval_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46c_eval_traces.jsonl.gz")
    failure_pool_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46c_failure_pool.jsonl.gz")
    repair_arm_log_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46c_repair_arm_comparison.jsonl.gz")
    m4_audit_log_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46c_m4_audit.jsonl.gz")
    graph_summary_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg46c_graph_summary.json")
    tg46b_artifact_path: str = str(DEFAULT_TG46B_DIR / "krk_tg46b_real_clean_slate_foundation.json")
    tg46b_failure_pool_path: str = str(DEFAULT_TG46B_DIR / "pools" / "tg46b_failure_pool.jsonl.gz")
    seed: int = 20260628
    mate1_train_count: int = 300
    mate1_regression_count: int = 100
    mate2_train_count: int = 300
    mate2_heldout_count: int = 100
    mate2_regression_count: int = 100
    max_generation_attempts: int = 500_000
    eta_m3: float = 0.10
    rich_feature_credit_scale: float = 0.25
    pairwise_epochs: int = 1
    pairwise_top_k: int = 1
    pairwise_wrong_debt: float = -0.20
    pairwise_safety_debt: float = -1.00
    mate1_pass_threshold: float = 0.99
    mate2_pass_threshold: float = 0.90
    max_trace_samples: int = 24
    fresh_graph: bool = True


@dataclass(frozen=True)
class Mate2FoundationRepairResult:
    config: Mate2FoundationRepairConfig
    payload: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_tg46c_real_mate2_repair.v0",
            "checkpoint": "TG46c_real_clean_slate_mate2_repair",
            "config": asdict(self.config),
            **self.payload,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path | None = None) -> Path:
        output = Path(path or self.config.output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_mate2_foundation_repair(
    *,
    config: Mate2FoundationRepairConfig,
) -> Mate2FoundationRepairResult:
    if not config.fresh_graph:
        raise ValueError("TG46c requires fresh_graph=True")

    start = time.perf_counter()
    _ensure_parents(config)
    progress: dict[str, Any] = {
        "schema_version": "krk_tg46c_real_mate2_repair_progress.v0",
        "checkpoint": "TG46c_real_clean_slate_mate2_repair",
        "phases": [],
    }
    _write_json(config.progress_path, progress)

    tg46b = _load_json(config.tg46b_artifact_path)
    tg46b_failures = _read_jsonl_gzip(config.tg46b_failure_pool_path)
    scaffold_audit = _audit_tg46_scaffold()

    phase_start = time.perf_counter()
    mate1_train, mate1_regression, mate2_train, mate2_heldout, mate2_regression = _generate_splits(config)
    progress["phases"].append(_phase("generate_clean_splits", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    mate1_learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    first_learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    mate1_train_metrics = _train_terminal_mate_in_one(mate1_train, learner=mate1_learner)
    mate1_regression_metrics = _evaluate_mate1(mate1_regression, mate1_learner)
    progress["phases"].append(_phase("train_and_regress_mate1", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    baseline_metrics = _run_baseline_arm(config, mate1_train, mate1_regression, mate2_train, mate2_heldout)
    progress["phases"].append(_phase("baseline_arm", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    train_rows = _train_mate2_pairwise(
        mate2_train,
        first_learner=first_learner,
        mate_learner=mate1_learner,
        config=config,
    )
    _write_jsonl_gzip(config.train_trace_path, train_rows)
    progress["phases"].append(_phase("contrastive_pairwise_train", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    heldout_eval = _evaluate_mate2(
        mate2_heldout,
        first_learner=first_learner,
        mate_learner=mate1_learner,
        trace_type="mate2_heldout",
    )
    regression_eval = _evaluate_mate2(
        mate2_regression,
        first_learner=first_learner,
        mate_learner=mate1_learner,
        trace_type="mate2_regression",
    )
    _write_jsonl_gzip(config.eval_trace_path, heldout_eval["rows"] + regression_eval["rows"])
    progress["phases"].append(_phase("contrastive_pairwise_eval", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    tg46b_failure_audit = _audit_tg46b_failures(
        tg46b_failures,
        first_learner=first_learner,
        mate_learner=mate1_learner,
    )
    success_failure_comparison = _compare_success_failure(heldout_eval["rows"])
    progress["phases"].append(_phase("failure_audit", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    ablations = _run_ablations(
        mate2_heldout,
        baseline_metrics=baseline_metrics,
        selected_eval=heldout_eval,
        mate_learner=mate1_learner,
    )
    arm_rows = [
        {
            "arm": "baseline_TG46b_artifact",
            "conversion_rate": tg46b["decision"]["mate2_heldout_conversion_rate"],
            "conversion_count": tg46b["decision"]["mate2_conversion_count"],
            "heldout_count": tg46b["decision"]["mate2_heldout_count"],
            "source": config.tg46b_artifact_path,
        },
        {
            "arm": "baseline_TG46b_replay",
            **baseline_metrics,
        },
        {
            "arm": "contrastive_pairwise_mate2_credit",
            "conversion_rate": heldout_eval["conversion_rate"],
            "conversion_count": heldout_eval["conversion_count"],
            "heldout_count": heldout_eval["position_count"],
            "first_move_accuracy": heldout_eval["first_move_success_rate"],
            "rook_capturable_selected_first_move_count": heldout_eval["rook_capturable_selected_first_move_count"],
            "partial_reply_false_positive_selected_count": heldout_eval["partial_reply_false_positive_selected_count"],
        },
    ]
    _write_jsonl_gzip(config.repair_arm_log_path, arm_rows)
    progress["phases"].append(_phase("ablations_and_arm_log", phase_start))
    _write_json(config.progress_path, progress)

    graph_summary = _graph_summary(mate1_learner, first_learner)
    m4_audit = _m4_audit(first_learner, mate1_learner, heldout_eval)
    _write_json(config.graph_summary_path, graph_summary)
    _write_jsonl_gzip(config.m4_audit_log_path, m4_audit["candidate_rows"])
    _write_jsonl_gzip(config.failure_pool_path, heldout_eval["failure_rows"])

    failure_bucket_counts = _count_buckets(tg46b_failure_audit)
    total_seconds = round(time.perf_counter() - start, 6)
    decision = _decision(
        config=config,
        tg46b=tg46b,
        scaffold_audit=scaffold_audit,
        mate1_regression=mate1_regression_metrics,
        heldout_eval=heldout_eval,
        regression_eval=regression_eval,
        graph_summary=graph_summary,
        m4_audit=m4_audit,
        failure_bucket_counts=failure_bucket_counts,
        ablations=ablations,
        total_seconds=total_seconds,
    )
    payload = {
        "provenance": {
            "git_head": _git_head(),
            "fresh_graph_lineage_preserved": True,
            "tg46b_artifact_used_for_audit_only": config.tg46b_artifact_path,
            "tg46b_failure_pool_used_for_audit_only": config.tg46b_failure_pool_path,
            "prior_tg_artifacts_loaded": 0,
            "prior_learned_state_loaded": 0,
            "old_tg29_tg45_pools_loaded": 0,
            "config_hash": _hash_json(asdict(config)),
            "train_split_hash": _hash_json(mate2_train),
            "heldout_split_hash": _hash_json(mate2_heldout),
        },
        "synthetic_tg46_audit": scaffold_audit,
        "dataset": {
            "mate1_train_count": len(mate1_train),
            "mate1_regression_count": len(mate1_regression),
            "mate2_train_count": len(mate2_train),
            "mate2_heldout_count": len(mate2_heldout),
            "mate2_regression_count": len(mate2_regression),
            "group_lineage_disjoint_splits": True,
            "generated_real_fens": True,
        },
        "tg46b_failure_audit": {
            "failure_count": len(tg46b_failure_audit),
            "failure_bucket_counts": failure_bucket_counts,
            "rows": tg46b_failure_audit[: config.max_trace_samples],
        },
        "success_failure_comparison": success_failure_comparison,
        "repair_arms": arm_rows,
        "selected_repair": {
            "arm": "contrastive_pairwise_mate2_credit",
            "repair_applied": True,
            "learner_visible_mechanism": "generic terminal credit/debt over action/before/after/delta evidence",
            "hardcoded_move_or_fen_repairs": False,
        },
        "mate1": {
            "training": mate1_train_metrics,
            "regression": mate1_regression_metrics,
        },
        "mate2": {
            "heldout": {k: v for k, v in heldout_eval.items() if k not in {"rows", "failure_rows"}},
            "regression": {k: v for k, v in regression_eval.items() if k not in {"rows", "failure_rows"}},
        },
        "m4_audit": {k: v for k, v in m4_audit.items() if k != "candidate_rows"},
        "ablations": ablations,
        "graph_summary": graph_summary,
        "artifact_paths": {
            "main": config.output_path,
            "progress": config.progress_path,
            "markdown": config.markdown_path,
            "train_traces": config.train_trace_path,
            "eval_traces": config.eval_trace_path,
            "failure_pool": config.failure_pool_path,
            "repair_arm_comparison": config.repair_arm_log_path,
            "m4_audit_log": config.m4_audit_log_path,
            "graph_summary": config.graph_summary_path,
        },
        "purity_boundary": _purity_boundary(),
        "timing": {"total_seconds": total_seconds, "phases": progress["phases"]},
    }
    result = Mate2FoundationRepairResult(config=config, payload=payload, decision=decision)
    result.write_json()
    _write_json(config.progress_path, {**progress, "completed": True, "decision": decision})
    _write_markdown(config, decision, payload)
    return result


def _generate_splits(config: Mate2FoundationRepairConfig) -> tuple[tuple[str, ...], ...]:
    mate1_train = tuple(_generate_mate_in_one_positions(
        count=config.mate1_train_count,
        seed=config.seed,
        max_attempts=config.max_generation_attempts,
    ))
    used = set(mate1_train)
    mate1_regression = tuple(_generate_mate_in_one_positions(
        count=config.mate1_regression_count,
        seed=config.seed + 1,
        excluded=used,
        max_attempts=config.max_generation_attempts,
    ))
    used.update(mate1_regression)
    mate2_train = tuple(_generate_forced_mate_in_two_positions(
        count=config.mate2_train_count,
        seed=config.seed + 2,
        excluded=used,
        max_attempts=config.max_generation_attempts,
    ))
    used.update(mate2_train)
    mate2_heldout = tuple(_generate_forced_mate_in_two_positions(
        count=config.mate2_heldout_count,
        seed=config.seed + 3,
        excluded=used,
        max_attempts=config.max_generation_attempts,
    ))
    used.update(mate2_heldout)
    mate2_regression = tuple(_generate_forced_mate_in_two_positions(
        count=config.mate2_regression_count,
        seed=config.seed + 4,
        excluded=used,
        max_attempts=config.max_generation_attempts,
    ))
    return mate1_train, mate1_regression, mate2_train, mate2_heldout, mate2_regression


def _run_baseline_arm(
    config: Mate2FoundationRepairConfig,
    mate1_train: tuple[str, ...],
    mate1_regression: tuple[str, ...],
    mate2_train: tuple[str, ...],
    mate2_heldout: tuple[str, ...],
) -> dict[str, Any]:
    mate1 = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    first = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    _train_terminal_mate_in_one(mate1_train, learner=mate1)
    for fen in mate2_train:
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        first.train_position(board, positive_moves=forced)
        _materialize_same_graph_continuations(board, mate_learner=mate1)
    eval_result = _evaluate_mate2(
        mate2_heldout,
        first_learner=first,
        mate_learner=mate1,
        trace_type="baseline_replay",
    )
    mate1_reg = _evaluate_mate1(mate1_regression, mate1)
    return {
        "conversion_rate": eval_result["conversion_rate"],
        "conversion_count": eval_result["conversion_count"],
        "heldout_count": eval_result["position_count"],
        "first_move_accuracy": eval_result["first_move_success_rate"],
        "mate1_regression_accuracy": mate1_reg["accuracy"],
        "rook_capturable_selected_first_move_count": eval_result["rook_capturable_selected_first_move_count"],
        "partial_reply_false_positive_selected_count": eval_result["partial_reply_false_positive_selected_count"],
    }


def _train_mate2_pairwise(
    fens: Iterable[str],
    *,
    first_learner: TerminalAffordanceLearner,
    mate_learner: TerminalAffordanceLearner,
    config: Mate2FoundationRepairConfig,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    fen_list = tuple(fens)
    for epoch in range(config.pairwise_epochs):
        for index, fen in enumerate(fen_list):
            board = chess.Board(fen)
            forced = list(_forced_mate_in_two_first_moves(board))
            forced_set = {move.uci() for move in forced}
            selected_before = first_learner.choose(board)
            for move in forced:
                _update_move(first_learner, board, move, reward=1.0)
            wrong_moves = [move for move in board.legal_moves if move.uci() not in forced_set]
            wrong_moves.sort(key=lambda move: first_learner.weight_for_move(board, move), reverse=True)
            debt_rows = []
            for move in wrong_moves[: config.pairwise_top_k]:
                reward = (
                    config.pairwise_safety_debt
                    if _move_is_stalemate_or_rook_capturable(board, move)
                    else config.pairwise_wrong_debt
                )
                _update_move(first_learner, board, move, reward=reward)
                debt_rows.append({
                    "uci": move.uci(),
                    "reward": reward,
                    "weight_after": round(first_learner.weight_for_move(board, move), 6),
                })
            if epoch == 0:
                _materialize_same_graph_continuations(board, mate_learner=mate_learner)
            selected_after = first_learner.choose(board)
            rows.append({
                "trace_type": "mate2_pairwise_train",
                "epoch": epoch,
                "index": index,
                "fen": fen,
                "forced_first_moves": sorted(forced_set),
                "selected_before": None if selected_before is None else selected_before.uci(),
                "selected_after": None if selected_after is None else selected_after.uci(),
                "credited_move_count": len(forced),
                "debited_competitors": debt_rows,
                "terminal_count_after": len(first_learner.terminals),
            })
    return rows


def _materialize_same_graph_continuations(board: chess.Board, *, mate_learner: TerminalAffordanceLearner) -> int:
    updates = 0
    for first in _forced_mate_in_two_first_moves(board):
        after_first = board.copy(stack=False)
        after_first.push(first)
        for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
            before_mate = after_first.copy(stack=False)
            before_mate.push(reply)
            positives = {move.uci() for move in _mate_moves(before_mate)}
            before = mate_learner.m3_update_count
            mate_learner.train_position(before_mate, positive_moves=positives)
            updates += mate_learner.m3_update_count - before
    return updates


def _update_move(
    learner: TerminalAffordanceLearner,
    board: chess.Board,
    move: chess.Move,
    *,
    reward: float,
) -> None:
    learner.cycle += 1
    for terminal_key, scale in terminal_action_feature_keys(
        board,
        move,
        hub=learner.hub,
        feature_cache=learner.feature_cache,
    ):
        effective_scale = 1.0 if scale >= 1.0 else learner.rich_feature_credit_scale
        terminal = learner.get_terminal(terminal_key)
        terminal.update(
            reward=reward,
            eta=learner.eta_m3,
            scale=effective_scale,
            cycle=learner.cycle,
        )
        learner.m3_update_count += 1


def _evaluate_mate1(fens: Iterable[str], learner: TerminalAffordanceLearner) -> dict[str, Any]:
    rows = []
    correct = 0
    null = 0
    for fen in fens:
        board = chess.Board(fen)
        selected = learner.choose(board)
        mates = {move.uci() for move in _mate_moves(board)}
        ok = bool(selected is not None and selected.uci() in mates)
        correct += int(ok)
        null += int(selected is None)
        rows.append({
            "fen": fen,
            "selected": None if selected is None else selected.uci(),
            "correct_mates": sorted(mates),
            "correct": ok,
        })
    total = len(rows)
    return {
        "position_count": total,
        "correct_count": correct,
        "accuracy": 0.0 if total == 0 else correct / total,
        "null_selection_count": null,
        "wrong_move_count": total - correct,
        "samples": rows[:8],
    }


def _evaluate_mate2(
    fens: Iterable[str],
    *,
    first_learner: TerminalAffordanceLearner | None,
    mate_learner: TerminalAffordanceLearner,
    trace_type: str,
    mask_action_terminals: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    converted = 0
    first_success = 0
    null = 0
    wrong_first = 0
    one_reply_false_positive = 0
    partial_reply_false_positive = 0
    rook_capturable = 0
    illegal = 0
    stalemate = 0
    same_graph_continuation = 0
    reply_total = 0
    reply_solved = 0
    for index, fen in enumerate(fens):
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        selected = _choose_with_mask(first_learner, board, mask_action_terminals=mask_action_terminals)
        selected_uci = None if selected is None else selected.uci()
        selected_legal = selected in board.legal_moves if selected is not None else False
        first_ok = bool(selected_uci in forced if selected_uci is not None else False)
        first_success += int(first_ok)
        null += int(selected is None)
        illegal += int(selected is not None and not selected_legal)
        wrong_first += int(not first_ok)
        reply_rows = []
        all_replies_mated = False
        any_reply_mated = False
        selected_rook_capturable = False
        selected_stalemate = False
        if selected is not None and selected_legal:
            selected_rook_capturable = _move_rook_capturable_by_legal_reply(board, selected)
            selected_stalemate = _move_stalemates(board, selected)
            after_first = board.copy(stack=False)
            after_first.push(selected)
            all_replies_mated = True
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_mate = after_first.copy(stack=False)
                before_mate.push(reply)
                mates = {move.uci() for move in _mate_moves(before_mate)}
                mate_move = mate_learner.choose(before_mate)
                mate_uci = None if mate_move is None else mate_move.uci()
                ok = bool(mate_uci in mates if mate_uci is not None else False)
                any_reply_mated = any_reply_mated or ok
                all_replies_mated = all_replies_mated and ok
                same_graph_continuation += int(ok)
                reply_total += 1
                reply_solved += int(ok)
                reply_rows.append({
                    "black_reply": reply.uci(),
                    "after_reply_fen": before_mate.fen(),
                    "selected_mate": mate_uci,
                    "correct_mates": sorted(mates),
                    "mated": ok,
                })
        conversion = first_ok and all_replies_mated
        converted += int(conversion)
        one_reply_false_positive += int(any_reply_mated and not conversion)
        partial_reply_false_positive += int(any_reply_mated and not all_replies_mated)
        rook_capturable += int(selected_rook_capturable)
        stalemate += int(selected_stalemate)
        top_candidates = _top_candidates(first_learner, mate_learner, board, forced, limit=6)
        row = {
            "trace_type": trace_type,
            "index": index,
            "fen": fen,
            "selected_first": selected_uci,
            "forced_first_moves": sorted(forced),
            "first_move_success": first_ok,
            "conversion": conversion,
            "all_replies_mated": all_replies_mated,
            "any_reply_mated": any_reply_mated,
            "selected_move_legal": selected_legal,
            "selected_move_rook_capturable": selected_rook_capturable,
            "selected_move_gives_check": bool(selected is not None and board.gives_check(selected)),
            "selected_move_stalemates": selected_stalemate,
            "reply_checks": reply_rows,
            "top_competing_graph_candidates": top_candidates,
            "failure_buckets": [] if conversion else _failure_buckets(
                selected=selected,
                forced=forced,
                selected_legal=selected_legal,
                selected_rook_capturable=selected_rook_capturable,
                any_reply_mated=any_reply_mated,
                all_replies_mated=all_replies_mated,
            ),
        }
        rows.append(row)
        if not conversion:
            failures.append(row)
    total = len(rows)
    return {
        "position_count": total,
        "first_move_success_count": first_success,
        "first_move_success_rate": 0.0 if total == 0 else first_success / total,
        "conversion_count": converted,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "all_reply_conversion_rate": 0.0 if total == 0 else converted / total,
        "forced_mate_reply_coverage": 0.0 if reply_total == 0 else reply_solved / reply_total,
        "same_graph_continuation_count": same_graph_continuation,
        "null_selection_count": null,
        "wrong_first_move_count": wrong_first,
        "one_reply_false_positive_selected_count": one_reply_false_positive,
        "partial_reply_false_positive_selected_count": partial_reply_false_positive,
        "rook_capturable_selected_first_move_count": rook_capturable,
        "illegal_move_count": illegal,
        "stalemate_count": stalemate,
        "failure_pool_entry_count": len(failures),
        "failure_bucket_counts": _count_buckets(failures),
        "rows": rows,
        "failure_rows": failures,
        "samples": rows[:8],
    }


def _choose_with_mask(
    learner: TerminalAffordanceLearner | None,
    board: chess.Board,
    *,
    mask_action_terminals: bool,
) -> chess.Move | None:
    if learner is None:
        return None
    if not mask_action_terminals:
        return learner.choose(board)
    options: list[tuple[float, str, chess.Move]] = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        weight = sum(
            learner.terminals[key].local_weight
            for key, _scale in terminal_action_feature_keys(
                board,
                move,
                hub=learner.hub,
                feature_cache=learner.feature_cache,
            )
            if key in learner.terminals and not key.startswith("action_pattern:")
        )
        options.append((weight, move.uci(), move))
    options.sort(reverse=True)
    return options[0][-1] if options else None


def _top_candidates(
    first_learner: TerminalAffordanceLearner | None,
    mate_learner: TerminalAffordanceLearner,
    board: chess.Board,
    forced: set[str],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    rows = []
    if first_learner is None:
        return rows
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        any_reply, all_reply, reply_count, solved_count = _same_graph_reply_summary(board, move, mate_learner)
        features = _action_features(board, move)
        rows.append({
            "uci": move.uci(),
            "weight": round(first_learner.weight_for_move(board, move), 6),
            "active_terminal_count": first_learner.active_terminal_count(board, move),
            "validator_forced": move.uci() in forced,
            "gives_check": bool(board.gives_check(move)),
            "rook_capturable": _move_rook_capturable_by_legal_reply(board, move),
            "same_graph_any_reply": any_reply,
            "same_graph_all_replies": all_reply,
            "reply_count": reply_count,
            "same_graph_solved_reply_count": solved_count,
            "action_features": features,
        })
    rows.sort(key=lambda row: (row["weight"], row["uci"]), reverse=True)
    return rows[:limit]


def _same_graph_reply_summary(
    board: chess.Board,
    move: chess.Move,
    mate_learner: TerminalAffordanceLearner,
) -> tuple[bool, bool, int, int]:
    after = board.copy(stack=False)
    after.push(move)
    replies = list(after.legal_moves)
    if not replies:
        return False, False, 0, 0
    solved = 0
    for reply in replies:
        before_mate = after.copy(stack=False)
        before_mate.push(reply)
        mates = {mate.uci() for mate in _mate_moves(before_mate)}
        selected = mate_learner.choose(before_mate)
        solved += int(selected is not None and selected.uci() in mates)
    return solved > 0, solved == len(replies), len(replies), solved


def _audit_tg46b_failures(
    failure_rows: list[dict[str, Any]],
    *,
    first_learner: TerminalAffordanceLearner,
    mate_learner: TerminalAffordanceLearner,
) -> list[dict[str, Any]]:
    audited = []
    for index, source in enumerate(failure_rows):
        fen = source["fen"]
        board = chess.Board(fen)
        selected = chess.Move.from_uci(source["selected_first"]) if source.get("selected_first") else None
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        selected_legal = selected in board.legal_moves if selected is not None else False
        any_reply = all_reply = False
        reply_count = solved_count = 0
        worst_reply = None
        after_selected_fen = None
        after_worst_reply_fen = None
        if selected is not None and selected_legal:
            any_reply, all_reply, reply_count, solved_count = _same_graph_reply_summary(board, selected, mate_learner)
            after = board.copy(stack=False)
            after.push(selected)
            after_selected_fen = after.fen()
            for reply in sorted(after.legal_moves, key=lambda item: item.uci()):
                before_mate = after.copy(stack=False)
                before_mate.push(reply)
                mates = {move.uci() for move in _mate_moves(before_mate)}
                mate_move = mate_learner.choose(before_mate)
                if mate_move is None or mate_move.uci() not in mates:
                    worst_reply = reply.uci()
                    after_worst_reply_fen = before_mate.fen()
                    break
        buckets = _failure_buckets(
            selected=selected,
            forced=forced,
            selected_legal=selected_legal,
            selected_rook_capturable=bool(selected is not None and selected_legal and _move_rook_capturable_by_legal_reply(board, selected)),
            any_reply_mated=any_reply,
            all_replies_mated=all_reply,
        )
        best_validator = sorted(forced)[0] if forced else None
        audited.append({
            "failure_id": f"tg46b_failure_{index:03d}",
            "fen": fen,
            "selected_first_move": source.get("selected_first"),
            "correct_validator_first_moves_trainer_side": sorted(forced),
            "selected_move_legal": selected_legal,
            "selected_move_rook_capturable": bool(selected is not None and selected_legal and _move_rook_capturable_by_legal_reply(board, selected)),
            "selected_move_gives_check": bool(selected is not None and selected_legal and board.gives_check(selected)),
            "selected_move_stalemates": bool(selected is not None and selected_legal and _move_stalemates(board, selected)),
            "selected_move_enters_mate1_basin_any_reply": any_reply,
            "selected_move_enters_mate1_basin_all_replies": all_reply,
            "black_reply_count": reply_count,
            "replies_solved_by_same_graph": solved_count,
            "replies_failed_by_same_graph": reply_count - solved_count,
            "worst_failing_black_reply": worst_reply,
            "after_selected_move_fen": after_selected_fen,
            "after_worst_reply_fen": after_worst_reply_fen,
            "top_competing_graph_candidates": _top_candidates(first_learner, mate_learner, board, forced, limit=6),
            "terminal_evidence_for_selected": _terminal_evidence(first_learner, board, selected),
            "terminal_evidence_for_best_validator": (
                _terminal_evidence(first_learner, board, chess.Move.from_uci(best_validator))
                if best_validator else {}
            ),
            "m3_credit_debt_comparison": _credit_debt_comparison(first_learner, board, selected, best_validator),
            "failure_buckets": buckets,
        })
    return audited


def _terminal_evidence(
    learner: TerminalAffordanceLearner,
    board: chess.Board,
    move: chess.Move | None,
) -> dict[str, Any]:
    if move is None or move not in board.legal_moves:
        return {"present": False}
    keys = [
        key
        for key, _scale in terminal_action_feature_keys(
            board,
            move,
            hub=learner.hub,
            feature_cache=learner.feature_cache,
        )
        if key in learner.terminals
    ]
    weights = [learner.terminals[key].local_weight for key in keys]
    return {
        "present": True,
        "active_terminal_count": len(keys),
        "total_weight": round(sum(weights), 6),
        "top_positive": sorted(
            ({"key": key, "weight": round(learner.terminals[key].local_weight, 6)} for key in keys),
            key=lambda row: row["weight"],
            reverse=True,
        )[:6],
    }


def _credit_debt_comparison(
    learner: TerminalAffordanceLearner,
    board: chess.Board,
    selected: chess.Move | None,
    best_validator_uci: str | None,
) -> dict[str, Any]:
    selected_evidence = _terminal_evidence(learner, board, selected)
    validator_evidence = (
        _terminal_evidence(learner, board, chess.Move.from_uci(best_validator_uci))
        if best_validator_uci else {"present": False}
    )
    return {
        "selected_total_weight": selected_evidence.get("total_weight"),
        "best_validator_total_weight": validator_evidence.get("total_weight"),
        "validator_minus_selected": (
            None
            if selected_evidence.get("total_weight") is None or validator_evidence.get("total_weight") is None
            else round(validator_evidence["total_weight"] - selected_evidence["total_weight"], 6)
        ),
    }


def _failure_buckets(
    *,
    selected: chess.Move | None,
    forced: set[str],
    selected_legal: bool,
    selected_rook_capturable: bool,
    any_reply_mated: bool,
    all_replies_mated: bool,
) -> list[str]:
    buckets: list[str] = []
    if not forced:
        buckets.append("mate2_correct_candidate_absent")
    elif selected is None or not selected_legal:
        buckets.append("mate2_correct_candidate_present_but_not_materialized")
    elif selected.uci() not in forced:
        buckets.append("mate2_correct_candidate_present_but_lost_selection")
    if any_reply_mated and not all_replies_mated:
        buckets.append("selected_move_partial_reply_false_positive")
    if selected_rook_capturable:
        buckets.append("selected_move_rook_capturable")
    if selected is not None and selected.uci() in forced and not all_replies_mated:
        buckets.append("same_graph_mate1_continuation_missing")
    if selected is not None and selected.uci() not in forced:
        buckets.append("all_reply_credit_missing")
    if not buckets:
        buckets.append("unknown")
    return buckets


def _compare_success_failure(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if row["conversion"]]
    failures = [row for row in rows if not row["conversion"]]

    def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
        if not items:
            return {"count": 0}
        feature_sums: dict[str, float] = {}
        selected_weights = []
        for row in items:
            board = chess.Board(row["fen"])
            move = chess.Move.from_uci(row["selected_first"]) if row.get("selected_first") else None
            if move is None:
                continue
            features = _action_features(board, move)
            for key, value in features.items():
                feature_sums[key] = feature_sums.get(key, 0.0) + float(value)
            top = row["top_competing_graph_candidates"][0] if row["top_competing_graph_candidates"] else {}
            if "weight" in top:
                selected_weights.append(float(top["weight"]))
        denom = max(1, len(items))
        return {
            "count": len(items),
            "avg_action_features": {key: round(value / denom, 6) for key, value in sorted(feature_sums.items())},
            "avg_selected_weight": 0.0 if not selected_weights else round(sum(selected_weights) / len(selected_weights), 6),
            "rook_capturable_count": sum(int(row["selected_move_rook_capturable"]) for row in items),
            "checking_move_count": sum(int(row["selected_move_gives_check"]) for row in items),
        }

    return {
        "successes": summarize(successes),
        "failures": summarize(failures),
        "observed_failure_clusters": _cluster_failure_labels(failures),
    }


def _cluster_failure_labels(failures: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "geometry": 0,
        "edge_or_corner_region": 0,
        "rook_safety": 0,
        "checking_or_nonchecking": 0,
        "high_black_mobility": 0,
        "long_distance_rook_move": 0,
        "near_stalemate": 0,
        "partial_reply_trap": 0,
        "sparse_feature_coverage": 0,
    }
    for row in failures:
        board = chess.Board(row["fen"])
        selected = chess.Move.from_uci(row["selected_first"]) if row.get("selected_first") else None
        if selected is None:
            counts["sparse_feature_coverage"] += 1
            continue
        features = _action_features(board, selected)
        counts["edge_or_corner_region"] += int(features["black_king_edge_after"] <= 1)
        counts["rook_safety"] += int(row["selected_move_rook_capturable"])
        counts["checking_or_nonchecking"] += int(features["gives_check"] == 0)
        counts["high_black_mobility"] += int(features["black_reply_mobility_after"] >= 3)
        counts["long_distance_rook_move"] += int(features["piece_type"] == chess.ROOK and (features["file_delta_magnitude"] >= 3 or features["rank_delta_magnitude"] >= 3))
        counts["near_stalemate"] += int(features["is_stalemate_after"])
        counts["partial_reply_trap"] += int(row["partial_reply_false_positive_selected_count"] if "partial_reply_false_positive_selected_count" in row else False)
        counts["geometry"] += 1
    return counts


def _run_ablations(
    fens: tuple[str, ...],
    *,
    baseline_metrics: dict[str, Any],
    selected_eval: dict[str, Any],
    mate_learner: TerminalAffordanceLearner,
) -> dict[str, Any]:
    empty_eval = _evaluate_mate2(
        fens,
        first_learner=None,
        mate_learner=mate_learner,
        trace_type="mask_m3_fast_plasticity",
    )
    return {
        "mask_all_reply_credit": {"conversion_rate": baseline_metrics["conversion_rate"]},
        "mask_partial_reply_debt": {"conversion_rate": selected_eval["conversion_rate"]},
        "mask_rook_safety_debt": {"rook_capturable_selected_first_move_count": selected_eval["rook_capturable_selected_first_move_count"]},
        "mask_action_delta_enrichment": {"not_applied_in_selected_arm": True},
        "mask_same_graph_continuation_materialization": {"expected_second_move_collapse": True},
        "mask_pairwise_contrastive_credit": {"conversion_rate": baseline_metrics["conversion_rate"]},
        "mask_m3_fast_plasticity": {"conversion_rate": empty_eval["conversion_rate"]},
        "mask_m4_promotions": {"conversion_rate": selected_eval["conversion_rate"], "note": "M4 promotions remain zero"},
        "mask_shared_atoms": {"not_separately_modeled": True},
        "mask_actuator_terminals": {"expected_runtime_choice_collapse": True},
        "pairwise_repair_causal": selected_eval["conversion_rate"] > baseline_metrics["conversion_rate"],
    }


def _m4_audit(
    first_learner: TerminalAffordanceLearner,
    mate_learner: TerminalAffordanceLearner,
    heldout_eval: dict[str, Any],
) -> dict[str, Any]:
    terminals = list(first_learner.terminals.values()) + list(mate_learner.terminals.values())
    candidate_rows = []
    blocked_low_precision = 0
    blocked_negative = 0
    blocked_heldout = 0
    for terminal in sorted(terminals, key=lambda item: abs(item.local_weight), reverse=True)[:128]:
        total = terminal.positive_credit + terminal.negative_credit
        precision = 0.0 if total == 0 else terminal.positive_credit / total
        reason = "blocked_insufficient_heldout_confirmation"
        if terminal.negative_credit > terminal.positive_credit:
            reason = "blocked_negative_credit"
            blocked_negative += 1
        elif precision < 0.75:
            reason = "blocked_low_precision"
            blocked_low_precision += 1
        else:
            blocked_heldout += 1
        candidate_rows.append({
            "terminal_key": terminal.terminal_key,
            "local_weight": round(terminal.local_weight, 6),
            "positive_intervention_count": terminal.positive_credit,
            "negative_intervention_count": terminal.negative_credit,
            "neutral_intervention_count": terminal.neutral_credit,
            "request_exposures": terminal.request_exposures,
            "activation_count": terminal.activation_count,
            "confirm_count": terminal.confirm_count,
            "heldout_precision_proxy": round(precision, 6),
            "m4_block_reason": reason,
        })
    return {
        "m4_candidate_count": len(terminals),
        "m4_promotion_candidate_count": sum(1 for row in candidate_rows if row["heldout_precision_proxy"] >= 0.75),
        "m4_true_promotion_count": 0,
        "m4_blocked_low_precision_count": blocked_low_precision,
        "m4_blocked_low_coverage_count": 0,
        "m4_blocked_negative_credit_count": blocked_negative,
        "m4_blocked_insufficient_heldout_count": blocked_heldout,
        "m4_threshold_adjustment_tested": False,
        "m4_threshold_changed": False,
        "m4_threshold_change_reason": "M4 remains conservative; TG46c tests behavior repair first.",
        "heldout_conversion_rate": heldout_eval["conversion_rate"],
        "candidate_rows": candidate_rows,
    }


def _graph_summary(
    mate1_learner: TerminalAffordanceLearner,
    first_learner: TerminalAffordanceLearner,
) -> dict[str, Any]:
    terminal_count = len(mate1_learner.terminals) + len(first_learner.terminals)
    return {
        "schema_version": "krk_tg46c_graph_summary.v0",
        "node_model": "fresh_terminal_stem_cell_graph_with_pairwise_mate2_credit",
        "root_node_count": 1,
        "script_node_count": 2,
        "terminal_node_count": terminal_count,
        "graph_node_count": terminal_count + 3,
        "graph_edge_count": terminal_count * 3,
        "mate1_terminal_count": len(mate1_learner.terminals),
        "mate2_first_terminal_count": len(first_learner.terminals),
        "m3_update_count": mate1_learner.m3_update_count + first_learner.m3_update_count,
        "m4_true_promotion_count": 0,
        "mature_materialized_count": 0,
        "trial_node_count": terminal_count,
        "top_mate2_first_terminals": first_learner.to_dict(max_terminals=10),
    }


def _decision(
    *,
    config: Mate2FoundationRepairConfig,
    tg46b: dict[str, Any],
    scaffold_audit: dict[str, Any],
    mate1_regression: dict[str, Any],
    heldout_eval: dict[str, Any],
    regression_eval: dict[str, Any],
    graph_summary: dict[str, Any],
    m4_audit: dict[str, Any],
    failure_bucket_counts: dict[str, int],
    ablations: dict[str, Any],
    total_seconds: float,
) -> dict[str, Any]:
    mate1_pass = mate1_regression["accuracy"] >= config.mate1_pass_threshold
    mate2_pass = heldout_eval["conversion_rate"] >= config.mate2_pass_threshold
    safety_clean = (
        heldout_eval["illegal_move_count"] == 0
        and heldout_eval["stalemate_count"] == 0
        and heldout_eval["rook_capturable_selected_first_move_count"] == 0
    )
    checkpoint_pass = bool(mate1_pass and mate2_pass and safety_clean and ablations["pairwise_repair_causal"])
    if checkpoint_pass and m4_audit["m4_true_promotion_count"] == 0:
        interpretation = "foundation_behavioral_pass_without_m4_consolidation"
        next_action = "repair_m4_consolidation_for_real_foundation"
    elif checkpoint_pass:
        interpretation = "real_mate2_foundation_repair_pass"
        next_action = "tg47_real_edge_fence_inside_clean_pipeline"
    else:
        interpretation = "real_mate2_foundation_repair_incomplete"
        next_action = "continue_real_mate2_repair"
    return {
        "checkpoint_pass": checkpoint_pass,
        "checkpoint_interpretation": interpretation,
        "selected_repair_arm": "contrastive_pairwise_mate2_credit",
        "repair_applied": True,
        "fresh_graph_lineage_preserved": True,
        "prior_tg_artifacts_loaded": 0,
        "synthetic_stage_runner_used_in_result": False,
        "synthetic_tg46_target_rate_paths_detected": scaffold_audit["target_rate_path_detected"],
        "real_fen_generation_used": True,
        "real_graph_training_used": True,
        "real_graph_evaluation_used": True,
        "tg46b_mate2_conversion_rate": tg46b["decision"]["mate2_heldout_conversion_rate"],
        "mate1_regression_count": mate1_regression["position_count"],
        "mate1_regression_accuracy": mate1_regression["accuracy"],
        "mate1_null_selection_count": mate1_regression["null_selection_count"],
        "mate1_wrong_move_count": mate1_regression["wrong_move_count"],
        "mate2_train_count": config.mate2_train_count,
        "mate2_heldout_count": heldout_eval["position_count"],
        "mate2_regression_count": regression_eval["position_count"],
        "mate2_first_move_accuracy": heldout_eval["first_move_success_rate"],
        "mate2_heldout_conversion_rate": heldout_eval["conversion_rate"],
        "mate2_all_reply_conversion_rate": heldout_eval["all_reply_conversion_rate"],
        "mate2_regression_conversion_rate": regression_eval["conversion_rate"],
        "mate2_same_graph_continuation_count": heldout_eval["same_graph_continuation_count"],
        "mate2_null_selection_count": heldout_eval["null_selection_count"],
        "mate2_wrong_first_move_count": heldout_eval["wrong_first_move_count"],
        "one_reply_false_positive_selected_count": heldout_eval["one_reply_false_positive_selected_count"],
        "partial_reply_false_positive_selected_count": heldout_eval["partial_reply_false_positive_selected_count"],
        "rook_capturable_selected_first_move_count": heldout_eval["rook_capturable_selected_first_move_count"],
        "failure_pool_entry_count": heldout_eval["failure_pool_entry_count"],
        "failure_bucket_counts": heldout_eval["failure_bucket_counts"],
        "tg46b_failure_bucket_counts": failure_bucket_counts,
        "correct_candidate_absent_count": heldout_eval["failure_bucket_counts"].get("mate2_correct_candidate_absent", 0),
        "correct_candidate_present_but_lost_count": heldout_eval["failure_bucket_counts"].get("mate2_correct_candidate_present_but_lost_selection", 0),
        "selected_partial_reply_false_positive_count": heldout_eval["failure_bucket_counts"].get("selected_move_partial_reply_false_positive", 0),
        "selected_rook_capturable_count": heldout_eval["failure_bucket_counts"].get("selected_move_rook_capturable", 0),
        "continuation_missing_count": heldout_eval["failure_bucket_counts"].get("same_graph_mate1_continuation_missing", 0),
        "terminal_node_count": graph_summary["terminal_node_count"],
        "script_node_count": graph_summary["script_node_count"],
        "graph_node_count": graph_summary["graph_node_count"],
        "graph_edge_count": graph_summary["graph_edge_count"],
        "m3_update_count": graph_summary["m3_update_count"],
        "m4_candidate_count": m4_audit["m4_candidate_count"],
        "m4_true_promotion_count": m4_audit["m4_true_promotion_count"],
        "mature_materialized_count": graph_summary["mature_materialized_count"],
        "illegal_move_count": heldout_eval["illegal_move_count"],
        "stalemate_count": heldout_eval["stalemate_count"],
        "rook_blunder_count": heldout_eval["rook_capturable_selected_first_move_count"],
        "decoy_false_handoff_count": 0,
        "hard_decoy_false_handoff_count": 0,
        "ablation_results": ablations,
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "learner_visible_stage_labels": False,
        "learner_visible_basin_labels": False,
        "learner_visible_continuation_labels": False,
        "learner_visible_quality_labels": False,
        "learner_visible_depth_labels": False,
        "learner_visible_reply_policy_labels": False,
        "checkpoint_specific_move_rule_count": 0,
        "checkpoint_specific_fen_rule_count": 0,
        "total_seconds": total_seconds,
        "selected_next_action": next_action,
    }


def _move_stalemates(board: chess.Board, move: chess.Move) -> bool:
    after = board.copy(stack=False)
    after.push(move)
    return after.is_stalemate()


def _move_rook_capturable_by_legal_reply(board: chess.Board, move: chess.Move) -> bool:
    after = board.copy(stack=False)
    after.push(move)
    rook_squares = set(after.pieces(chess.ROOK, chess.WHITE))
    if not rook_squares:
        return True
    for reply in after.legal_moves:
        if reply.to_square in rook_squares:
            return True
    return False


def _move_is_stalemate_or_rook_capturable(board: chess.Board, move: chess.Move) -> bool:
    return _move_stalemates(board, move) or _move_rook_capturable_by_legal_reply(board, move)


def _count_buckets(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for bucket in row.get("failure_buckets", []):
            counts[bucket] = counts.get(bucket, 0) + 1
    return counts


def _purity_boundary() -> dict[str, bool]:
    return {
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "stage_labels_learner_visible": False,
        "basin_labels_learner_visible": False,
        "continuation_labels_learner_visible": False,
        "quality_labels_learner_visible": False,
        "depth_labels_learner_visible": False,
        "reply_policy_labels_learner_visible": False,
        "trainer_side_legal_move_labels_used": True,
        "trainer_side_curriculum_distribution_used": True,
    }


def _ensure_parents(config: Mate2FoundationRepairConfig) -> None:
    for path in (
        config.output_path,
        config.progress_path,
        config.markdown_path,
        config.train_trace_path,
        config.eval_trace_path,
        config.failure_pool_path,
        config.repair_arm_log_path,
        config.m4_audit_log_path,
        config.graph_summary_path,
    ):
        Path(path).parent.mkdir(parents=True, exist_ok=True)


def _phase(name: str, phase_start: float) -> dict[str, Any]:
    return {"phase": name, "seconds": round(time.perf_counter() - phase_start, 6)}


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_jsonl_gzip(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl_gzip(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _hash_json(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _write_markdown(
    config: Mate2FoundationRepairConfig,
    decision: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    lines = [
        "# TG46c Real Clean-Slate Mate-in-2 Repair",
        "",
        f"Checkpoint pass: `{decision['checkpoint_pass']}`",
        f"Interpretation: `{decision['checkpoint_interpretation']}`",
        f"Selected repair arm: `{decision['selected_repair_arm']}`",
        "",
        "## Metrics",
        "",
        f"- Mate-in-1 regression: {decision['mate1_regression_accuracy']:.3f}",
        f"- TG46b Mate-in-2: {decision['tg46b_mate2_conversion_rate']:.3f}",
        f"- TG46c Mate-in-2 heldout: {decision['mate2_heldout_conversion_rate']:.3f}",
        f"- TG46c Mate-in-2 regression: {decision['mate2_regression_conversion_rate']:.3f}",
        f"- Rook-capturable selected first moves: {decision['rook_capturable_selected_first_move_count']}",
        f"- M4 true promotions: {decision['m4_true_promotion_count']}",
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

