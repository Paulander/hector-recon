"""TG48a2 focused same-side rook-danger microstage."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
import time
from typing import Any, Mapping

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState

from .clean_edge_fence_stage import (
    DEFAULT_TG46D_DIR,
    _file_sha256,
    _hash_json,
    _load_json,
    _write_json,
    _write_jsonl_gzip,
)
from .edge_killbox_curriculum import (
    EdgeKillboxCurriculumConfig,
    _combine_learners,
    _confinement_area,
    _delta_bucket,
    _failure_buckets,
    _generate_family_split,
    _graded_positive_progress,
    _label_source,
    _move_metrics,
    _parent_snapshot,
    _primary_axis,
    _rate,
    _repair_hard_decoy_pool,
    _rook_capturable_by_reply,
    _score_move,
    _sign,
    classify_edge_killbox_family,
)
from .features import extract_diagnostic_features, validate_learner_record, validate_learner_visible_keys
from .handoff_reachability_audit import (
    _foundation_artifact_sanity,
    _reconstruct_parent_foundation_from_m4_audit,
)
from .real_clean_slate_foundation import _git_head
from .terminal_substrate import TerminalAffordanceLearner


DEFAULT_OUTPUT_DIR = Path("reports/autogrowth/clean_slate_krk/tg48a2_same_side_microstage")
FORBIDDEN_MICROSTAGE_TERMS = (
    "same_side",
    "same-side",
    "opposition",
    "tempo",
    "stage",
    "basin",
    "curriculum",
    "quality",
    "depth",
    "reply_policy",
    "reply-policy",
)


@dataclass(frozen=True)
class TG48a2SameSideMicrostageConfig:
    checkpoint_name: str = "TG48a2_same_side_microstage"
    schema_version: str = "krk_tg48a2_same_side_microstage.v0"
    run_scale_label: str = "smoke"
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    output_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg48a2_same_side_microstage.json")
    markdown_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg48a2_same_side_microstage.md")
    train_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a2_microstage_train_traces.jsonl.gz")
    eval_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a2_microstage_eval_traces.jsonl.gz")
    failure_pool_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a2_microstage_failure_pool.jsonl.gz")
    generator_samples_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a2_microstage_generator_samples.jsonl.gz")
    boundary_positive_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a2_microstage_boundary_positive.jsonl.gz")
    graph_summary_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a2_microstage_graph_summary.json")
    board_sample_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a2_microstage_board_samples.md")
    parent_foundation_artifact_path: str = str(DEFAULT_TG46D_DIR / "promoted_tg46d_foundation.json")
    parent_foundation_m4_audit_path: str = str(DEFAULT_TG46D_DIR / "pools" / "tg46d_m4_audit.jsonl.gz")
    seed: int = 20260701
    train_count: int = 80
    heldout_count: int = 32
    regression_count: int = 32
    decoy_count: int = 32
    hard_decoy_count: int = 32
    max_generation_attempts: int = 250_000
    max_horizon_plies: int = 6
    eta_m3: float = 0.08
    rich_feature_credit_scale: float = 0.25
    m4_affordance_precision_threshold: float = 0.60
    m4_veto_precision_threshold: float = 0.62
    m4_min_positive_support: int = 4
    m4_min_negative_support: int = 4
    m4_max_decoy_false_handoff_activation: int = 0
    m4_max_unsafe_activation: int = 0
    m3_plus_m4_trial_scale: float = 0.25
    sample_boards_per_split: int = 12


@dataclass(frozen=True)
class TG48a2SameSideMicrostageResult:
    config: TG48a2SameSideMicrostageConfig
    payload: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.config.schema_version,
            "checkpoint": self.config.checkpoint_name,
            "config": asdict(self.config),
            **self.payload,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path | None = None) -> Path:
        output = Path(path or self.config.output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_tg48a2_same_side_microstage(
    *,
    config: TG48a2SameSideMicrostageConfig,
) -> TG48a2SameSideMicrostageResult:
    start = time.perf_counter()
    parent_artifact = _load_json(config.parent_foundation_artifact_path)
    parent_hash = _file_sha256(config.parent_foundation_artifact_path)
    parent = _reconstruct_parent_foundation_from_m4_audit(
        parent_artifact=parent_artifact,
        parent_m4_audit_path=config.parent_foundation_m4_audit_path,
    )
    parent_before = _foundation_artifact_sanity(parent_artifact, parent)
    parent_snapshot = _parent_snapshot(parent)
    datasets, hard_decoy_gate = generate_same_side_microstage_datasets(config=config, parent=parent)
    label_source = _label_source()
    _write_jsonl_gzip(config.generator_samples_path, _sample_rows(datasets, limit=config.sample_boards_per_split))
    _write_jsonl_gzip(config.boundary_positive_path, datasets.get("boundary_positive", []))

    learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    train_rows = _train_microstage(
        datasets["train"] + datasets["decoy"] + datasets["hard_decoy"],
        learner=learner,
        parent=parent,
        label_source=label_source,
        config=config,
    )
    _write_jsonl_gzip(config.train_trace_path, train_rows)

    parent_only = _evaluate_rows(datasets["heldout"], parent=parent, learner=None, trace_type="parent_TG46d_only", config=config)
    m3_only = _evaluate_rows(datasets["heldout"], parent=parent, learner=learner, trace_type="TG48a2_M3_trial_only", config=config)
    no_foundation = _evaluate_rows(datasets["heldout"], parent=None, learner=learner, trace_type="TG48a2_no_foundation_control", config=config)
    terminal_audit = _terminal_activation_audit(
        learner,
        datasets["train"] + datasets["heldout"] + datasets["decoy"] + datasets["hard_decoy"],
        parent=parent,
        config=config,
    )
    m4_learner, m4_audit = _promote_m4(learner, terminal_audit=terminal_audit, config=config)
    m4_only = _evaluate_rows(datasets["heldout"], parent=parent, learner=m4_learner, trace_type="TG48a2_M4_consolidated_only", config=config)
    m3_plus_m4 = _evaluate_rows(
        datasets["heldout"],
        parent=parent,
        learner=_combine_learners(m3=learner, m4=m4_learner, trial_scale=config.m3_plus_m4_trial_scale),
        trace_type="TG48a2_true_M3_plus_M4",
        config=config,
    )
    regression_m4 = _evaluate_rows(datasets["regression"], parent=parent, learner=m4_learner, trace_type="TG48a2_regression_M4", config=config)
    decoy_eval = _evaluate_rows(
        datasets["decoy"] + datasets["hard_decoy"],
        parent=parent,
        learner=m4_learner,
        trace_type="TG48a2_decoy_M4",
        config=config,
    )
    oracle = _oracle_summary(datasets["heldout"], parent=parent, config=config)
    eval_rows = (
        parent_only["rows"]
        + m3_only["rows"]
        + no_foundation["rows"]
        + m4_only["rows"]
        + m3_plus_m4["rows"]
        + regression_m4["rows"]
        + decoy_eval["rows"]
    )
    failure_rows = [row for row in eval_rows if row.get("failure_buckets")]
    _write_jsonl_gzip(config.eval_trace_path, eval_rows)
    _write_jsonl_gzip(config.failure_pool_path, failure_rows)
    graph_summary = _graph_summary(learner=learner, m4_learner=m4_learner, m4_audit=m4_audit)
    _write_json(config.graph_summary_path, graph_summary)
    _write_board_samples(config.board_sample_path, eval_rows, m4_audit=m4_audit)

    parent_after = _foundation_artifact_sanity(parent_artifact, parent)
    parent_delta = int(parent_snapshot != _parent_snapshot(parent))
    total_seconds = round(time.perf_counter() - start, 6)
    decision = _decision(
        config=config,
        parent_hash=parent_hash,
        parent_before=parent_before,
        parent_after=parent_after,
        parent_delta=parent_delta,
        datasets=datasets,
        hard_decoy_gate=hard_decoy_gate,
        learner=learner,
        m4_audit=m4_audit,
        parent_only=parent_only,
        m3_only=m3_only,
        m4_only=m4_only,
        m3_plus_m4=m3_plus_m4,
        no_foundation=no_foundation,
        regression_m4=regression_m4,
        decoy_eval=decoy_eval,
        oracle=oracle,
        total_seconds=total_seconds,
    )
    payload = {
        "provenance": {
            "git_head": _git_head(),
            "parent_foundation_artifact": config.parent_foundation_artifact_path,
            "parent_foundation_hash": parent_hash,
            "parent_foundation_m4_audit": config.parent_foundation_m4_audit_path,
            "config_hash": _hash_json(asdict(config)),
            "old_tg_pools_loaded": 0,
            "old_tg_learned_state_loaded_as_training_data": False,
            "runtime_tablebase_or_dtm_move_source": False,
        },
        "parent_foundation": {
            "frozen": True,
            "sanity_before": parent_before,
            "sanity_after": parent_after,
            "m3_delta_during_stage": 0,
            "m4_delta_during_stage": 0,
            "weight_delta_during_stage": parent_delta,
        },
        "datasets": _dataset_summary(datasets),
        "label_source": label_source,
        "evaluation": {
            "parent_TG46d_only": _strip_rows(parent_only),
            "TG48a2_M3_trial_only": _strip_rows(m3_only),
            "TG48a2_M4_consolidated_only": _strip_rows(m4_only),
            "TG48a2_true_M3_plus_M4": _strip_rows(m3_plus_m4),
            "TG48a2_no_foundation_control": _strip_rows(no_foundation),
            "decoy_hard_decoy": _strip_rows(decoy_eval),
            "regression_M4": _strip_rows(regression_m4),
        },
        "oracle": oracle,
        "m4_audit": m4_audit,
        "hard_decoy_gate": hard_decoy_gate,
        "graph_summary": graph_summary,
        "artifact_paths": {
            "main": config.output_path,
            "markdown": config.markdown_path,
            "train_traces": config.train_trace_path,
            "eval_traces": config.eval_trace_path,
            "failure_pool": config.failure_pool_path,
            "generator_samples": config.generator_samples_path,
            "boundary_positive": config.boundary_positive_path,
            "graph_summary": config.graph_summary_path,
            "board_samples": config.board_sample_path,
        },
        "purity_boundary": _purity_boundary(),
        "timing": {"total_seconds": total_seconds},
    }
    result = TG48a2SameSideMicrostageResult(config=config, payload=payload, decision=decision)
    result.write_json()
    _write_markdown(config.markdown_path, result)
    return result


def generate_same_side_microstage_datasets(
    *,
    config: TG48a2SameSideMicrostageConfig,
    parent: dict[str, TerminalAffordanceLearner],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    rng = random.Random(config.seed)
    used: set[str] = set()
    used_lineage: dict[str, str] = {}
    datasets = {
        "train": _generate_same_side_split(
            rng=rng,
            split="train",
            count=config.train_count,
            used=used,
            used_lineage=used_lineage,
            max_attempts=config.max_generation_attempts,
        ),
        "heldout": _generate_same_side_split(
            rng=rng,
            split="heldout",
            count=config.heldout_count,
            used=used,
            used_lineage=used_lineage,
            max_attempts=config.max_generation_attempts,
        ),
        "regression": _generate_same_side_split(
            rng=rng,
            split="regression",
            count=config.regression_count,
            used=used,
            used_lineage=used_lineage,
            max_attempts=config.max_generation_attempts,
        ),
        "decoy": _generate_family_split(
            rng=rng,
            split="decoy",
            family="decoy_edge_killbox",
            count=config.decoy_count,
            used=used,
            used_lineage=used_lineage,
            max_attempts=config.max_generation_attempts,
        ),
        "hard_decoy": _generate_family_split(
            rng=rng,
            split="hard_decoy",
            family="hard_decoy_edge_killbox",
            count=config.hard_decoy_count,
            used=used,
            used_lineage=used_lineage,
            max_attempts=config.max_generation_attempts,
        ),
    }
    repair_config = EdgeKillboxCurriculumConfig(
        hard_decoy_count=config.hard_decoy_count,
        max_generation_attempts=config.max_generation_attempts,
        max_horizon_plies=config.max_horizon_plies,
        seed=config.seed,
    )
    datasets, hard_decoy_gate = _repair_hard_decoy_pool(datasets=datasets, parent=parent, config=repair_config)
    return datasets, hard_decoy_gate


def _generate_same_side_split(
    *,
    rng: random.Random,
    split: str,
    count: int,
    used: set[str],
    used_lineage: dict[str, str],
    max_attempts: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    attempts = 0
    while len(out) < count and attempts < max_attempts:
        attempts += 1
        row = _generate_family_split(
            rng=rng,
            split=split,
            family="edge_killbox_same_side_rook_danger",
            count=1,
            used=set(),
            used_lineage={},
            max_attempts=max(4_000, max_attempts // 20),
        )[0]
        if row["fen"] in used:
            continue
        lineage = row["lineage_key"]
        if lineage in used_lineage and used_lineage[lineage] != split:
            continue
        used.add(row["fen"])
        used_lineage[lineage] = split
        out.append(row)
    if len(out) < count:
        raise RuntimeError(f"generated {len(out)}/{count} TG48a2 same-side {split} positions")
    return out


def _train_microstage(
    rows: list[dict[str, Any]],
    *,
    learner: TerminalAffordanceLearner,
    parent: dict[str, TerminalAffordanceLearner],
    label_source: str,
    config: TG48a2SameSideMicrostageConfig,
) -> list[dict[str, Any]]:
    trace = []
    for index, row in enumerate(rows):
        board = chess.Board(row["fen"])
        rewards = {move.uci(): _reward(board, move, parent=parent, config=config) for move in board.legal_moves}
        is_negative_pool = row["family"] in {"decoy_edge_killbox", "hard_decoy_edge_killbox"}
        if is_negative_pool:
            positive: list[chess.Move] = []
            negative = _negative_pool_debt_moves(board, parent=parent, config=config)
        else:
            positive = [
                move
                for move in sorted(board.legal_moves, key=lambda item: item.uci())
                if rewards[move.uci()] >= 2.0
            ]
            negative = [
                move
                for move in sorted(board.legal_moves, key=lambda item: item.uci())
                if rewards[move.uci()] <= -2.0
            ]
        if not positive and not is_negative_pool and rewards:
            best_reward = max(rewards.values())
            if best_reward > 0.0:
                positive = [
                    move
                    for move in sorted(board.legal_moves, key=lambda item: item.uci())
                    if rewards[move.uci()] == best_reward
                ]
        weak_negative = [
            move
            for move in sorted(board.legal_moves, key=lambda item: item.uci())
            if rewards[move.uci()] < 0.0 and move not in negative
        ][:4]
        before = _choose_move(board, parent=parent, learner=learner)
        updates = {"positive": 0, "negative": 0, "neutral": 0}
        for move in positive:
            _update_move(learner, board, move, reward=max(1.0, rewards[move.uci()]))
            updates["positive"] += 1
        for move in negative:
            _update_move(learner, board, move, reward=min(-1.0, rewards[move.uci()]))
            updates["negative"] += 1
        for move in weak_negative:
            _update_move(learner, board, move, reward=min(-0.5, rewards[move.uci()]))
            updates["negative"] += 1
        after = _choose_move(board, parent=parent, learner=learner)
        trace.append({
            "trace_type": "tg48a2_same_side_microstage_train",
            "index": index,
            "fen": row["fen"],
            "family": row["family"],
            "split": row["split"],
            "label_source": label_source,
            "selected_before": None if before is None else before.uci(),
            "selected_after": None if after is None else after.uci(),
            "max_reward": max(rewards.values()) if rewards else 0.0,
            "positive_reward_count": sum(int(value > 0.0) for value in rewards.values()),
            "credited_move_count": len(positive),
            "negative_debt_move_count": len(negative),
            "weak_debt_move_count": len(weak_negative),
            "negative_pool_training": is_negative_pool,
            "updates": updates,
            "terminal_count_after": len(learner.terminals),
            "learner_visible_labels": False,
        })
    return trace


def _negative_pool_debt_moves(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner],
    config: TG48a2SameSideMicrostageConfig,
) -> list[chess.Move]:
    out = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        diagnostics = _move_diagnostics(board, move, parent=parent, config=config)
        metrics = diagnostics["metrics"]
        if (
            metrics["rook_blunder"]
            or metrics["rook_missing"]
            or metrics["stalemate"]
            or metrics["illegal"]
            or metrics["confinement_regression"]
            or metrics["graph_positive_false_basin"]
            or metrics["partial_only_near_basin"]
            or metrics["validated_entry"]
            or diagnostics["is_lateral_rook_move"]
        ):
            out.append(move)
    return out


def _reward(
    board: chess.Board,
    move: chess.Move,
    *,
    parent: dict[str, TerminalAffordanceLearner],
    config: TG48a2SameSideMicrostageConfig,
) -> float:
    diagnostics = _move_diagnostics(board, move, parent=parent, config=config)
    metrics = diagnostics["metrics"]
    if (
        metrics["illegal"]
        or metrics["rook_blunder"]
        or metrics["rook_missing"]
        or metrics["stalemate"]
    ):
        return -8.0
    if metrics["graph_positive_false_basin"]:
        return -6.0
    if metrics["confinement_regression"]:
        return -4.0
    reward = -0.05
    if metrics["validated_mate1_entry"]:
        reward += 10.0
    elif metrics["validated_mate2_entry"]:
        reward += 8.0
    elif metrics["validated_entry"]:
        reward += 7.0
    if diagnostics["safe_lateral_reposition"]:
        reward += 4.0
    if diagnostics["axis_pattern_improved"]:
        reward += 3.0
    if diagnostics["friendly_geometry"]:
        reward += 2.0
    if metrics["confinement_improved"]:
        reward += 1.0
    if metrics["black_mobility_reduced"]:
        reward += 1.0
    if metrics["graded_positive_progress"] and not metrics["partial_only_near_basin"]:
        reward += 1.0
    if metrics["partial_only_near_basin"]:
        reward -= 1.5
    if diagnostics["rook_danger_after"]:
        reward -= 3.0
    return max(-8.0, min(10.0, reward))


def _evaluate_rows(
    rows: list[dict[str, Any]],
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    learner: TerminalAffordanceLearner | None,
    trace_type: str,
    config: TG48a2SameSideMicrostageConfig,
) -> dict[str, Any]:
    out = []
    for index, row in enumerate(rows):
        board = chess.Board(row["fen"])
        selected = _choose_move(board, parent=parent, learner=learner)
        diagnostics = _move_diagnostics(board, selected, parent=parent, config=config)
        success = _micro_success(diagnostics)
        out.append({
            "trace_type": trace_type,
            "index": index,
            "fen": row["fen"],
            "family": row["family"],
            "substage": row.get("substage"),
            "split": row.get("split"),
            "selected": None if selected is None else selected.uci(),
            "success": success,
            "metrics": diagnostics["metrics"],
            "diagnostics": diagnostics,
            "failure_buckets": [] if success else _failure_buckets(diagnostics["metrics"]),
            "learner_visible_labels": False,
        })
    return _summarize_eval(out)


def _choose_move(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    learner: TerminalAffordanceLearner | None,
) -> chess.Move | None:
    options = [
        (_score_micro_move(board, move, parent=parent, learner=learner), move.uci(), move)
        for move in sorted(board.legal_moves, key=lambda item: item.uci())
    ]
    options.sort(reverse=True)
    return options[0][-1] if options else None


def _score_micro_move(
    board: chess.Board,
    move: chess.Move,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    learner: TerminalAffordanceLearner | None,
) -> float:
    parent_weight = 0.0 if parent is None else _score_move(board, move, parent=parent, learner=None) * 0.20
    child_weight = 0.0 if learner is None else _weight_for_move(learner, board, move)
    return parent_weight + child_weight


def _update_move(learner: TerminalAffordanceLearner, board: chess.Board, move: chess.Move, *, reward: float) -> None:
    learner.cycle += 1
    for key, scale in _micro_terminal_keys(board, move):
        terminal = learner.get_terminal(key)
        terminal.update(
            reward=reward,
            eta=learner.eta_m3,
            scale=scale,
            cycle=learner.cycle,
        )
        learner.m3_update_count += 1


def _weight_for_move(learner: TerminalAffordanceLearner, board: chess.Board, move: chess.Move) -> float:
    return sum(
        learner.terminals[key].local_weight * scale
        for key, scale in _micro_terminal_keys(board, move)
        if key in learner.terminals
    )


def _micro_terminal_keys(board: chess.Board, move: chess.Move) -> tuple[tuple[str, float], ...]:
    after = board.copy(stack=False)
    after.push(move)
    before = extract_diagnostic_features(board)
    after_f = extract_diagnostic_features(after)
    piece = board.piece_at(move.from_square)
    file_delta = chess.square_file(move.to_square) - chess.square_file(move.from_square)
    rank_delta = chess.square_rank(move.to_square) - chess.square_rank(move.from_square)
    before_axis = _axis_pattern(before)
    after_axis = _axis_pattern(after_f)
    confinement_bucket = _delta_bucket(_confinement_area(board) - _confinement_area(after))
    support_bucket = _delta_bucket(before["king_support_manhattan_distance"] - after_f["king_support_manhattan_distance"])
    action_piece = 0 if piece is None else int(piece.piece_type)
    keys = [
        (f"micro_action:piece_type={action_piece}", 1.0),
        (f"micro_action:file_delta_sign={_sign(file_delta)}", 1.0),
        (f"micro_action:rank_delta_sign={_sign(rank_delta)}", 1.0),
        (f"micro_action:file_delta_magnitude={min(3, abs(file_delta))}", 1.0),
        (f"micro_action:rank_delta_magnitude={min(3, abs(rank_delta))}", 1.0),
        (f"micro_before:edge_contact={int(before['black_king_on_edge'])}", 0.5),
        (f"micro_before:support_band={int(_support_band(before))}", 0.5),
        (f"micro_before:axis_pattern={before_axis}", 0.5),
        (f"micro_before:line_distance={min(4, int(before['rook_distance_to_black_king_edge_line']))}", 0.5),
        (f"micro_before:fence_span={min(4, int(before['rook_fence_depth_relative_to_black_king_edge']))}", 0.5),
        (f"micro_after:axis_pattern={after_axis}", 0.5),
        (f"micro_after:support_band={int(_support_band(after_f))}", 0.5),
        (f"micro_after:line_distance={min(4, int(after_f['rook_distance_to_black_king_edge_line']))}", 0.5),
        (f"micro_delta:axis_pattern={_axis_delta_bucket(before_axis, after_axis)}", 1.0),
        (f"micro_delta:confinement_area={confinement_bucket}", 1.0),
        (f"micro_delta:support_distance={support_bucket}", 0.5),
        (
            "micro_compound:"
            f"piece={action_piece}|fd={_sign(file_delta)}|rd={_sign(rank_delta)}|"
            f"b_axis={before_axis}|a_axis={after_axis}|conf={confinement_bucket}",
            1.0,
        ),
        (
            "micro_rook_path:"
            f"piece={action_piece}|fd_mag={min(3, abs(file_delta))}|rd_mag={min(3, abs(rank_delta))}|"
            f"axis_delta={_axis_delta_bucket(before_axis, after_axis)}|conf={confinement_bucket}|"
            f"support={support_bucket}",
            1.0,
        ),
    ]
    validate_learner_visible_keys(
        (key for key, _scale in keys),
        builder="tg48a2_same_side_microstage._micro_terminal_keys",
    )
    _validate_micro_learner_record([key for key, _scale in keys])
    return tuple(keys)


def _move_diagnostics(
    board: chess.Board,
    move: chess.Move | None,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    config: TG48a2SameSideMicrostageConfig,
) -> dict[str, Any]:
    eval_config = EdgeKillboxCurriculumConfig(max_horizon_plies=config.max_horizon_plies)
    metrics = _move_metrics(board, move, parent=parent, config=eval_config)
    if move is None or move not in board.legal_moves:
        return _diagnostics_for_invalid(metrics)
    after = board.copy(stack=False)
    after.push(move)
    before_f = extract_diagnostic_features(board)
    after_f = extract_diagnostic_features(after)
    before_axis = _axis_pattern(before_f)
    after_axis = _axis_pattern(after_f)
    is_lateral = _is_lateral_rook_move(board, move)
    rook_danger_after = bool(metrics["rook_blunder"] or metrics["rook_missing"])
    friendly = _friendly_geometry(after)
    safe_lateral = bool(
        is_lateral
        and not rook_danger_after
        and not metrics["stalemate"]
        and not metrics["confinement_regression"]
        and not metrics["graph_positive_false_basin"]
        and not metrics["partial_only_near_basin"]
    )
    axis_improved = before_axis == 1 and after_axis != 1 and not rook_danger_after
    return {
        "metrics": metrics,
        "is_safe": not (
            metrics["illegal"]
            or metrics["rook_blunder"]
            or metrics["rook_missing"]
            or metrics["stalemate"]
            or metrics["confinement_regression"]
        ),
        "is_lateral_rook_move": is_lateral,
        "preserves_rook_safety": not rook_danger_after,
        "preserves_or_improves_confinement": not metrics["confinement_regression"],
        "axis_pattern_before": before_axis,
        "axis_pattern_after": after_axis,
        "axis_pattern_improved": axis_improved,
        "safe_lateral_reposition": safe_lateral,
        "friendly_geometry": friendly,
        "rook_danger_after": rook_danger_after,
        "bounded_playout_reaches_validated_entry": metrics["validated_entry"] or metrics["mate_conversion_within_horizon"],
        "trainer_side_labels_only": True,
        "learner_visible_labels": False,
    }


def _diagnostics_for_invalid(metrics: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "metrics": dict(metrics),
        "is_safe": False,
        "is_lateral_rook_move": False,
        "preserves_rook_safety": False,
        "preserves_or_improves_confinement": False,
        "axis_pattern_before": 0,
        "axis_pattern_after": 0,
        "axis_pattern_improved": False,
        "safe_lateral_reposition": False,
        "friendly_geometry": False,
        "rook_danger_after": False,
        "bounded_playout_reaches_validated_entry": False,
        "trainer_side_labels_only": True,
        "learner_visible_labels": False,
    }


def _micro_success(diagnostics: Mapping[str, Any]) -> bool:
    metrics = diagnostics["metrics"]
    return bool(
        not metrics["illegal"]
        and not metrics["rook_blunder"]
        and not metrics["rook_missing"]
        and not metrics["stalemate"]
        and not metrics["confinement_regression"]
        and not metrics["graph_positive_false_basin"]
        and not metrics["partial_only_near_basin"]
        and (
            metrics["immediate_checkmate"]
            or metrics["validated_entry"]
            or metrics["mate_conversion_within_horizon"]
            or diagnostics["safe_lateral_reposition"]
            or diagnostics["axis_pattern_improved"]
            or diagnostics["friendly_geometry"]
        )
    )


def _summarize_eval(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_family.setdefault(row["family"], []).append(row)
    selected_lateral = sum(int(row["diagnostics"]["is_lateral_rook_move"]) for row in rows)
    lateral_successes = sum(
        int(row["success"] and row["diagnostics"]["is_lateral_rook_move"])
        for row in rows
    )
    available = sum(int(_safe_lateral_available(chess.Board(row["fen"]))) for row in rows)
    return {
        "position_count": total,
        "success_count": sum(int(row["success"]) for row in rows),
        "success_rate": _rate(sum(int(row["success"]) for row in rows), total),
        "selected_lateral_rook_count": selected_lateral,
        "selected_lateral_rook_rate": _rate(selected_lateral, total),
        "safe_lateral_rook_available_count": available,
        "safe_lateral_rook_available_rate": _rate(available, total),
        "lateral_rook_affordance_precision": _rate(lateral_successes, selected_lateral),
        "lateral_rook_affordance_recall": _rate(lateral_successes, available),
        "validated_entry_count": sum(int(row["metrics"]["validated_entry"]) for row in rows),
        "validated_entry_rate": _rate(sum(int(row["metrics"]["validated_entry"]) for row in rows), total),
        "validated_mate1_entry_rate": _rate(sum(int(row["metrics"]["validated_mate1_entry"]) for row in rows), total),
        "validated_mate2_entry_rate": _rate(sum(int(row["metrics"]["validated_mate2_entry"]) for row in rows), total),
        "mate_conversion_rate_within_horizon": _rate(sum(int(row["metrics"]["mate_conversion_within_horizon"]) for row in rows), total),
        "rook_blunder_count": sum(int(row["metrics"]["rook_blunder"]) for row in rows),
        "rook_missing_count": sum(int(row["metrics"]["rook_missing"]) for row in rows),
        "stalemate_count": sum(int(row["metrics"]["stalemate"]) for row in rows),
        "illegal_move_count": sum(int(row["metrics"]["illegal"]) for row in rows),
        "confinement_regression_count": sum(int(row["metrics"]["confinement_regression"]) for row in rows),
        "graph_positive_false_basin_count": sum(int(row["metrics"]["graph_positive_false_basin"]) for row in rows),
        "partial_only_near_basin_count": sum(int(row["metrics"]["partial_only_near_basin"]) for row in rows),
        "hard_decoy_false_handoff_count": sum(
            int(row["family"] == "hard_decoy_edge_killbox" and row["metrics"]["validated_entry"])
            for row in rows
        ),
        "decoy_false_handoff_count": sum(
            int(row["family"] == "decoy_edge_killbox" and row["metrics"]["validated_entry"])
            for row in rows
        ),
        "family_success_rates": {
            family: _rate(sum(int(row["success"]) for row in items), len(items))
            for family, items in sorted(by_family.items())
        },
        "rows": rows,
    }


def _oracle_summary(
    rows: list[dict[str, Any]],
    *,
    parent: dict[str, TerminalAffordanceLearner],
    config: TG48a2SameSideMicrostageConfig,
) -> dict[str, Any]:
    successes = 0
    validated_successes = 0
    safe_lateral = 0
    samples = []
    for row in rows:
        board = chess.Board(row["fen"])
        best: tuple[float, str, dict[str, Any]] | None = None
        lateral_available = False
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            diagnostics = _move_diagnostics(board, move, parent=parent, config=config)
            reward = _reward(board, move, parent=parent, config=config)
            if diagnostics["safe_lateral_reposition"]:
                lateral_available = True
            if best is None or reward > best[0]:
                best = (reward, move.uci(), diagnostics)
        success = bool(best and _micro_success(best[2]))
        validated = bool(best and best[2]["metrics"]["validated_entry"])
        successes += int(success)
        validated_successes += int(validated)
        safe_lateral += int(lateral_available)
        samples.append({
            "fen": row["fen"],
            "best_move": None if best is None else best[1],
            "best_reward": None if best is None else best[0],
            "best_success": success,
            "best_validated_entry": validated,
            "safe_lateral_rook_available": lateral_available,
            "learner_visible_labels": False,
        })
    return {
        "position_count": len(rows),
        "oracle_success_count": successes,
        "oracle_success_rate": _rate(successes, len(rows)),
        "oracle_validated_success_count": validated_successes,
        "oracle_validated_success_rate": _rate(validated_successes, len(rows)),
        "safe_lateral_rook_available_count": safe_lateral,
        "safe_lateral_rook_available_rate": _rate(safe_lateral, len(rows)),
        "sample_rows": samples[:12],
        "learner_visible_labels": False,
    }


def _terminal_activation_audit(
    learner: TerminalAffordanceLearner,
    rows: list[dict[str, Any]],
    *,
    parent: dict[str, TerminalAffordanceLearner],
    config: TG48a2SameSideMicrostageConfig,
) -> dict[str, dict[str, Any]]:
    audit: dict[str, dict[str, Any]] = {}
    for row in rows:
        board = chess.Board(row["fen"])
        for move in board.legal_moves:
            diagnostics = _move_diagnostics(board, move, parent=parent, config=config)
            metrics = diagnostics["metrics"]
            unsafe = bool(
                metrics["rook_blunder"]
                or metrics["rook_missing"]
                or metrics["stalemate"]
                or metrics["illegal"]
                or metrics["confinement_regression"]
            )
            decoy_false = bool(row["family"] in {"decoy_edge_killbox", "hard_decoy_edge_killbox"} and metrics["validated_entry"])
            positive = _micro_success(diagnostics)
            for key, _scale in _micro_terminal_keys(board, move):
                if key not in learner.terminals:
                    continue
                item = audit.setdefault(
                    key,
                    {
                        "activation_count": 0,
                        "unsafe_activation_count": 0,
                        "decoy_false_handoff_activation_count": 0,
                        "positive_progress_activation_count": 0,
                        "validated_entry_activation_count": 0,
                        "lateral_activation_count": 0,
                        "positive_lateral_activation_count": 0,
                    },
                )
                item["activation_count"] += 1
                item["unsafe_activation_count"] += int(unsafe)
                item["decoy_false_handoff_activation_count"] += int(decoy_false)
                item["positive_progress_activation_count"] += int(positive)
                item["validated_entry_activation_count"] += int(metrics["validated_entry"])
                item["lateral_activation_count"] += int(diagnostics["is_lateral_rook_move"])
                item["positive_lateral_activation_count"] += int(positive and diagnostics["is_lateral_rook_move"])
    return audit


def _promote_m4(
    learner: TerminalAffordanceLearner,
    *,
    terminal_audit: dict[str, dict[str, Any]],
    config: TG48a2SameSideMicrostageConfig,
) -> tuple[TerminalAffordanceLearner, dict[str, Any]]:
    clone = TerminalAffordanceLearner.create(eta_m3=learner.eta_m3, rich_feature_credit_scale=learner.rich_feature_credit_scale)
    rows = []
    promoted = []
    veto_count = 0
    affordance_count = 0
    for key, terminal in learner.terminals.items():
        audit = terminal_audit.get(key, {})
        total = terminal.positive_credit + terminal.negative_credit
        precision = 0.0 if total == 0 else terminal.positive_credit / total
        negative_precision = 0.0 if total == 0 else terminal.negative_credit / total
        promote_affordance = bool(
            terminal.local_weight > 0
            and terminal.positive_credit >= config.m4_min_positive_support
            and precision >= config.m4_affordance_precision_threshold
            and audit.get("unsafe_activation_count", 0) <= config.m4_max_unsafe_activation
            and audit.get("decoy_false_handoff_activation_count", 0) <= config.m4_max_decoy_false_handoff_activation
            and audit.get("positive_lateral_activation_count", 0) > 0
            and not _is_broad_key(key)
        )
        promote_veto = bool(
            terminal.local_weight < 0
            and terminal.negative_credit >= config.m4_min_negative_support
            and negative_precision >= config.m4_veto_precision_threshold
            and _is_veto_key(key)
        )
        promote = promote_affordance or promote_veto
        if promote:
            copied = copy.deepcopy(terminal)
            copied.cell.state = StemCellState.MATURE
            clone.terminals[key] = copied
            promoted.append(key)
            affordance_count += int(promote_affordance)
            veto_count += int(promote_veto)
        rows.append({
            "terminal_key": key,
            "positive_intervention_count": terminal.positive_credit,
            "negative_intervention_count": terminal.negative_credit,
            "neutral_count": terminal.neutral_credit,
            "precision": round(precision, 6),
            "negative_precision": round(negative_precision, 6),
            "local_weight": round(terminal.local_weight, 6),
            "unsafe_activation_count": audit.get("unsafe_activation_count", 0),
            "decoy_false_handoff_activation_count": audit.get("decoy_false_handoff_activation_count", 0),
            "positive_progress_activation_count": audit.get("positive_progress_activation_count", 0),
            "validated_entry_activation_count": audit.get("validated_entry_activation_count", 0),
            "lateral_activation_count": audit.get("lateral_activation_count", 0),
            "positive_lateral_activation_count": audit.get("positive_lateral_activation_count", 0),
            "promoted_as": "affordance" if promote_affordance else "veto" if promote_veto else None,
            "promoted": promote,
        })
    return clone, {
        "M4_candidate_count": len(rows),
        "M4_promoted_terminal_count": len(promoted),
        "M4_promoted_veto_count": veto_count,
        "M4_promoted_affordance_count": affordance_count,
        "candidate_rows": rows,
    }


def _decision(
    *,
    config: TG48a2SameSideMicrostageConfig,
    parent_hash: str,
    parent_before: Mapping[str, Any],
    parent_after: Mapping[str, Any],
    parent_delta: int,
    datasets: dict[str, list[dict[str, Any]]],
    hard_decoy_gate: Mapping[str, Any],
    learner: TerminalAffordanceLearner,
    m4_audit: Mapping[str, Any],
    parent_only: Mapping[str, Any],
    m3_only: Mapping[str, Any],
    m4_only: Mapping[str, Any],
    m3_plus_m4: Mapping[str, Any],
    no_foundation: Mapping[str, Any],
    regression_m4: Mapping[str, Any],
    decoy_eval: Mapping[str, Any],
    oracle: Mapping[str, Any],
    total_seconds: float,
) -> dict[str, Any]:
    _ = (no_foundation, regression_m4)
    safety_clean = bool(
        m4_only["rook_blunder_count"] == 0
        and m4_only["stalemate_count"] == 0
        and m4_only["illegal_move_count"] == 0
        and m4_only["confinement_regression_count"] == 0
    )
    hard_decoy_false = int(decoy_eval["hard_decoy_false_handoff_count"])
    infrastructure_pass = bool(parent_delta == 0 and parent_before["pass"] and parent_after["pass"])
    false_basin_decreased = bool(m4_only["graph_positive_false_basin_count"] < parent_only["graph_positive_false_basin_count"])
    behavioral_candidate = bool(
        infrastructure_pass
        and safety_clean
        and hard_decoy_false == 0
        and m4_only["success_rate"] > parent_only["success_rate"]
        and false_basin_decreased
    )
    if hard_decoy_false > 0:
        interpretation = "same_side_decoy_leak_blocks_training"
        next_action = "repair_same_side_decoys"
    elif oracle["oracle_validated_success_rate"] >= 0.25 and m4_only["success_rate"] < parent_only["success_rate"]:
        interpretation = "same_side_affordance_selection_blocker"
        next_action = "improve_lateral_rook_affordance_precision"
    elif behavioral_candidate:
        interpretation = "same_side_microstage_behavioral_candidate"
        next_action = "integrate_same_side_microstage_into_tg48a"
    else:
        interpretation = "same_side_reward_or_generator_blocker"
        next_action = "inspect_same_side_failure_pool"
    return {
        "checkpoint_pass": infrastructure_pass,
        "checkpoint_interpretation": interpretation,
        "selected_next_action": next_action,
        "behavioral_candidate": behavioral_candidate,
        "run_scale_label": config.run_scale_label,
        "parent_foundation_hash": parent_hash,
        "parent_foundation_frozen": True,
        "parent_foundation_m3_delta_during_stage": 0,
        "parent_foundation_m4_delta_during_stage": 0,
        "parent_foundation_weight_delta_during_stage": parent_delta,
        "same_side_train_count": len(datasets["train"]),
        "same_side_heldout_count": len(datasets["heldout"]),
        "same_side_regression_count": len(datasets["regression"]),
        "decoy_count": len(datasets["decoy"]),
        "hard_decoy_count": len(datasets["hard_decoy"]),
        "boundary_positive_routed_count": len(datasets.get("boundary_positive", [])),
        "hard_decoy_generator_mislabel_count": int(hard_decoy_gate.get("hard_decoy_generator_mislabel_count", 0)),
        "true_hard_decoy_leak_count": int(hard_decoy_gate.get("true_hard_decoy_leak_count", 0)),
        "hard_decoy_false_handoff_count": hard_decoy_false,
        "parent_success_rate": parent_only["success_rate"],
        "M3_success_rate": m3_only["success_rate"],
        "M4_success_rate": m4_only["success_rate"],
        "true_M3_plus_M4_success_rate": m3_plus_m4["success_rate"],
        "oracle_success_rate": oracle["oracle_success_rate"],
        "oracle_validated_success_rate": oracle["oracle_validated_success_rate"],
        "safe_lateral_rook_available_rate": parent_only["safe_lateral_rook_available_rate"],
        "selected_lateral_rook_rate": m4_only["selected_lateral_rook_rate"],
        "lateral_rook_affordance_precision": m4_only["lateral_rook_affordance_precision"],
        "lateral_rook_affordance_recall": m4_only["lateral_rook_affordance_recall"],
        "promoted_affordance_count": m4_audit["M4_promoted_affordance_count"],
        "promoted_veto_count": m4_audit["M4_promoted_veto_count"],
        "M3_update_count": learner.m3_update_count,
        "graph_positive_false_basin_count": m4_only["graph_positive_false_basin_count"],
        "graph_positive_false_basin_parent_count": parent_only["graph_positive_false_basin_count"],
        "graph_positive_false_basin_decreased_vs_parent": false_basin_decreased,
        "rook_blunder_count": m4_only["rook_blunder_count"],
        "stalemate_count": m4_only["stalemate_count"],
        "illegal_move_count": m4_only["illegal_move_count"],
        "confinement_regression_count": m4_only["confinement_regression_count"],
        "partial_only_near_basin_count": m4_only["partial_only_near_basin_count"],
        "runtime_tablebase_or_dtm_move_source": False,
        "stockfish_runtime_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "hardcoded_fen_or_move_repair": False,
        "stage_labels_learner_visible": False,
        "basin_labels_learner_visible": False,
        "curriculum_labels_learner_visible": False,
        "tempo_opposition_labels_learner_visible": False,
        "quality_depth_reply_policy_labels_learner_visible": False,
        "same_side_labels_learner_visible": False,
        "total_seconds": total_seconds,
    }


def _graph_summary(
    *,
    learner: TerminalAffordanceLearner,
    m4_learner: TerminalAffordanceLearner,
    m4_audit: Mapping[str, Any],
) -> dict[str, Any]:
    top = sorted(learner.terminals.items(), key=lambda item: item[1].local_weight, reverse=True)[:20]
    bottom = sorted(learner.terminals.items(), key=lambda item: item[1].local_weight)[:20]
    payload = {
        "trial_terminal_count": len(learner.terminals),
        "mature_terminal_count": len(m4_learner.terminals),
        "m3_update_count": learner.m3_update_count,
        "m4": {key: value for key, value in m4_audit.items() if key != "candidate_rows"},
        "top_positive_terminal_keys": [key for key, _terminal in top],
        "top_negative_terminal_keys": [key for key, _terminal in bottom],
        "learner_visible_labels": False,
    }
    _validate_micro_learner_record(payload["top_positive_terminal_keys"])
    _validate_micro_learner_record(payload["top_negative_terminal_keys"])
    return payload


def _sample_rows(datasets: dict[str, list[dict[str, Any]]], *, limit: int) -> list[dict[str, Any]]:
    out = []
    counts: dict[str, int] = {}
    for split, rows in datasets.items():
        for row in rows:
            count = counts.get(split, 0)
            if count >= limit:
                continue
            counts[split] = count + 1
            out.append(row)
    return out


def _dataset_summary(datasets: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {
        split: {
            "count": len(rows),
            "family_counts": {family: sum(int(row["family"] == family) for row in rows) for family in sorted({row["family"] for row in rows})},
        }
        for split, rows in datasets.items()
    }


def _strip_rows(metrics: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if key != "rows"}


def _friendly_geometry(board: chess.Board) -> bool:
    return classify_edge_killbox_family(board) in {
        "edge_killbox_opposed_side",
        "edge_killbox_same_side_rook_danger",
    }


def _safe_lateral_available(board: chess.Board) -> bool:
    for move in board.legal_moves:
        if not _is_lateral_rook_move(board, move):
            continue
        after = board.copy(stack=False)
        after.push(move)
        if not _rook_capturable_by_reply(after) and not after.is_stalemate() and bool(after.pieces(chess.ROOK, chess.WHITE)):
            return True
    return False


def _is_lateral_rook_move(board: chess.Board, move: chess.Move) -> bool:
    piece = board.piece_at(move.from_square)
    if piece is None or piece.color != chess.WHITE or piece.piece_type != chess.ROOK:
        return False
    bk = board.king(chess.BLACK)
    if bk is None:
        return False
    axis = _primary_axis(bk)
    if axis == "rank":
        return chess.square_file(move.from_square) != chess.square_file(move.to_square)
    return chess.square_rank(move.from_square) != chess.square_rank(move.to_square)


def _axis_pattern(features: Mapping[str, float]) -> int:
    if int(features["rook_black_king_opposite_sides_of_white_king_on_primary_axis"]) == 1:
        return 2
    if int(features["rook_black_king_same_side_of_white_king_on_primary_axis"]) == 1:
        return 1
    return 0


def _axis_delta_bucket(before_axis: int, after_axis: int) -> str:
    if before_axis == after_axis:
        return "same"
    if before_axis == 1 and after_axis != 1:
        return "improved"
    if before_axis != 1 and after_axis == 1:
        return "regressed"
    return "changed"


def _support_band(features: Mapping[str, float]) -> bool:
    return bool(
        int(features["king_support_l_shape"]) == 1
        or (
            int(features["king_support_chebyshev_distance"]) <= 2
            and int(features["king_support_manhattan_distance"]) <= 3
        )
    )


def _is_veto_key(key: str) -> bool:
    return (
        "rook_risk_after=1" in key
        or "stalemate_after=1" in key
        or "confinement_area=regressed" in key
        or "black_mobility=regressed" in key
        or key.startswith("micro_compound:")
        or key.startswith("micro_rook_path:")
    )


def _is_broad_key(key: str) -> bool:
    return key in {"micro_before:edge_contact=1", "micro_after:support_band=1"}


def _purity_boundary() -> dict[str, bool]:
    return {
        "trainer_side_labels_allowed": True,
        "trainer_side_labels_used_as_runtime_provider": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stockfish_runtime_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "hardcoded_fen_or_move_repair": False,
        "stage_labels_learner_visible": False,
        "basin_labels_learner_visible": False,
        "curriculum_labels_learner_visible": False,
        "tempo_opposition_labels_learner_visible": False,
        "quality_depth_reply_policy_labels_learner_visible": False,
        "same_side_labels_learner_visible": False,
    }


def _validate_micro_learner_record(value: Any) -> None:
    validate_learner_record(value)
    encoded = json.dumps(value, sort_keys=True).lower()
    for term in FORBIDDEN_MICROSTAGE_TERMS:
        if term in encoded:
            raise ValueError(f"forbidden TG48a2 microstage learner term leaked: {term}")


def _write_board_samples(path: str | Path, eval_rows: list[dict[str, Any]], *, m4_audit: Mapping[str, Any]) -> None:
    _ = m4_audit
    categories = {
        "M4 failures": [
            row for row in eval_rows if row["trace_type"] == "TG48a2_M4_consolidated_only" and not row["success"]
        ],
        "M4 selected lateral rook": [
            row for row in eval_rows if row["trace_type"] == "TG48a2_M4_consolidated_only" and row["diagnostics"]["is_lateral_rook_move"]
        ],
        "Graph-positive false responses": [
            row for row in eval_rows if row["metrics"].get("graph_positive_false_basin")
        ],
    }
    lines = [
        "# TG48a2 Same-Side Microstage Board Samples",
        "",
        "Human-readable samples. Family and split names are trainer-side diagnostics only.",
        "",
    ]
    for title, rows in categories.items():
        lines.extend([f"## {title}", ""])
        if not rows:
            lines.extend(["No rows in this category.", ""])
            continue
        for row in rows[:8]:
            board = chess.Board(row["fen"])
            lines.extend(
                [
                    f"- Trace: `{row['trace_type']}`, index `{row['index']}`",
                    f"- FEN: `{row['fen']}`",
                    f"- Selected: `{row['selected']}`; success `{row['success']}`; buckets `{', '.join(row['failure_buckets']) if row['failure_buckets'] else 'none'}`",
                    "",
                    "```text",
                    str(board),
                    "```",
                    "",
                ]
            )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _write_markdown(path: str | Path, result: TG48a2SameSideMicrostageResult) -> None:
    d = result.decision
    lines = [
        f"# {result.config.checkpoint_name}",
        "",
        f"- Checkpoint pass: {d['checkpoint_pass']}",
        f"- Interpretation: {d['checkpoint_interpretation']}",
        f"- Selected next action: {d['selected_next_action']}",
        f"- Parent/M3/M4/M3+M4 success: {d['parent_success_rate']:.3f} / {d['M3_success_rate']:.3f} / {d['M4_success_rate']:.3f} / {d['true_M3_plus_M4_success_rate']:.3f}",
        f"- Safe lateral rook availability: {d['safe_lateral_rook_available_rate']:.3f}",
        f"- Selected lateral rook rate: {d['selected_lateral_rook_rate']:.3f}",
        f"- Lateral affordance precision/recall: {d['lateral_rook_affordance_precision']:.3f} / {d['lateral_rook_affordance_recall']:.3f}",
        f"- Promoted affordance/veto: {d['promoted_affordance_count']} / {d['promoted_veto_count']}",
        f"- Graph-positive false responses: {d['graph_positive_false_basin_count']}",
        f"- Hard-decoy false handoff: {d['hard_decoy_false_handoff_count']}",
        f"- Safety rook/stalemate/illegal/confinement: {d['rook_blunder_count']} / {d['stalemate_count']} / {d['illegal_move_count']} / {d['confinement_regression_count']}",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
