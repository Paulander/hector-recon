"""TG48a2 same-side rook-danger episode training."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import gzip
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
    _failure_buckets,
    _foundation_response as _edge_foundation_response,
    _label_source,
    _move_metrics,
    _parent_snapshot,
    _rate,
    _rook_capturable_by_reply,
)
from .features import extract_learner_features, validate_learner_record
from .handoff_reachability_audit import (
    _foundation_artifact_sanity,
    _reconstruct_parent_foundation_from_m4_audit,
)
from .real_clean_slate_foundation import _git_head
from .terminal_substrate import TerminalAffordanceLearner
from .tg48a2_same_side_microstage import (
    FORBIDDEN_MICROSTAGE_TERMS,
    TG48a2SameSideMicrostageConfig,
    _axis_delta_bucket,
    _axis_pattern,
    _is_lateral_rook_move,
    _micro_terminal_keys,
    _score_micro_move,
    _support_band,
    _validate_micro_learner_record,
    generate_same_side_microstage_datasets,
)


DEFAULT_OUTPUT_DIR = Path("reports/autogrowth/clean_slate_krk/tg48a2_same_side_episode_training")


@dataclass(frozen=True)
class TG48a2SameSideEpisodeTrainingConfig:
    checkpoint_name: str = "TG48a2_same_side_episode_training"
    schema_version: str = "krk_tg48a2_same_side_episode_training.v0"
    run_scale_label: str = "smoke"
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    output_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg48a2_same_side_episode_training.json")
    markdown_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg48a2_same_side_episode_training.md")
    train_episode_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "train_episode_traces.jsonl.gz")
    eval_episode_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "eval_episode_traces.jsonl.gz")
    failure_episode_pool_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "failure_episode_pool.jsonl.gz")
    promoted_terminal_audit_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "promoted_terminal_audit.jsonl.gz")
    reward_channel_audit_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "reward_channel_audit.jsonl.gz")
    board_sample_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "board_samples.md")
    parent_foundation_artifact_path: str = str(DEFAULT_TG46D_DIR / "promoted_tg46d_foundation.json")
    parent_foundation_m4_audit_path: str = str(DEFAULT_TG46D_DIR / "pools" / "tg46d_m4_audit.jsonl.gz")
    seed: int = 20260701
    train_count: int = 80
    heldout_count: int = 32
    regression_count: int = 32
    decoy_count: int = 32
    hard_decoy_count: int = 32
    max_generation_attempts: int = 250_000
    max_white_moves: int = 3
    max_total_plies: int = 6
    gamma: float = 0.75
    eta_m3: float = 0.08
    rich_feature_credit_scale: float = 0.25
    exploration_rate: float = 0.65
    m4_affordance_precision_threshold: float = 0.58
    m4_veto_precision_threshold: float = 0.62
    m4_min_positive_support: int = 3
    m4_min_negative_support: int = 3
    m3_plus_m4_trial_scale: float = 0.25


@dataclass(frozen=True)
class TG48a2SameSideEpisodeTrainingResult:
    config: TG48a2SameSideEpisodeTrainingConfig
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


def run_tg48a2_same_side_episode_training(
    *,
    config: TG48a2SameSideEpisodeTrainingConfig,
) -> TG48a2SameSideEpisodeTrainingResult:
    start = time.perf_counter()
    parent_artifact = _load_json(config.parent_foundation_artifact_path)
    parent_hash = _file_sha256(config.parent_foundation_artifact_path)
    parent = _reconstruct_parent_foundation_from_m4_audit(
        parent_artifact=parent_artifact,
        parent_m4_audit_path=config.parent_foundation_m4_audit_path,
    )
    parent_before = _foundation_artifact_sanity(parent_artifact, parent)
    parent_snapshot = _parent_snapshot(parent)
    dataset_config = TG48a2SameSideMicrostageConfig(
        seed=config.seed,
        train_count=config.train_count,
        heldout_count=config.heldout_count,
        regression_count=config.regression_count,
        decoy_count=config.decoy_count,
        hard_decoy_count=config.hard_decoy_count,
        max_generation_attempts=config.max_generation_attempts,
        max_horizon_plies=config.max_total_plies,
    )
    datasets, hard_decoy_gate = generate_same_side_microstage_datasets(config=dataset_config, parent=parent)
    label_source = _label_source()
    learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    train_traces = _train_episode_rows(
        datasets["train"] + datasets["decoy"] + datasets["hard_decoy"],
        learner=learner,
        parent=parent,
        config=config,
        label_source=label_source,
    )
    _write_jsonl_gzip(config.train_episode_trace_path, train_traces)

    terminal_audit = _terminal_episode_audit(learner, train_traces)
    m4_learner, m4_audit = _promote_m4(learner, terminal_audit=terminal_audit, config=config)
    parent_legacy_eval = _evaluate_episode_rows(
        datasets["heldout"],
        parent=parent,
        learner=None,
        trace_type="parent_TG46d_episode_legacy_availability_classifier",
        config=config,
        classifier_mode="legacy_availability_diagnostic",
    )
    parent_eval = _evaluate_episode_rows(
        datasets["heldout"],
        parent=parent,
        learner=None,
        trace_type="parent_TG46d_episode",
        config=config,
    )
    child_weights_zeroed_eval = _evaluate_episode_rows(
        datasets["heldout"],
        parent=parent,
        learner=_zero_child_weights(learner),
        trace_type="TG48a2_episode_child_weights_zeroed",
        config=config,
    )
    m3_eval = _evaluate_episode_rows(datasets["heldout"], parent=parent, learner=learner, trace_type="TG48a2_episode_M3", config=config)
    m4_eval = _evaluate_episode_rows(datasets["heldout"], parent=parent, learner=m4_learner, trace_type="TG48a2_episode_M4", config=config)
    m3_plus_m4_eval = _evaluate_episode_rows(
        datasets["heldout"],
        parent=parent,
        learner=_combine_learners(m3=learner, m4=m4_learner, trial_scale=config.m3_plus_m4_trial_scale),
        trace_type="TG48a2_episode_M3_plus_M4",
        config=config,
    )
    ablated_affordances_eval = _evaluate_episode_rows(
        datasets["heldout"],
        parent=parent,
        learner=_ablate_promoted_positive_affordances(
            _combine_learners(m3=learner, m4=m4_learner, trial_scale=config.m3_plus_m4_trial_scale),
            m4_audit=m4_audit,
        ),
        trace_type="TG48a2_episode_M3_plus_M4_ablated_affordances",
        config=config,
    )
    no_foundation_eval = _evaluate_episode_rows(datasets["heldout"], parent=None, learner=learner, trace_type="TG48a2_episode_no_foundation", config=config)
    regression_eval = _evaluate_episode_rows(datasets["regression"], parent=parent, learner=m4_learner, trace_type="TG48a2_episode_regression_M4", config=config)
    decoy_eval = _evaluate_episode_rows(
        datasets["decoy"] + datasets["hard_decoy"],
        parent=parent,
        learner=m4_learner,
        trace_type="TG48a2_episode_decoy_M4",
        config=config,
    )
    eval_traces = (
        parent_legacy_eval["traces"]
        + parent_eval["traces"]
        + child_weights_zeroed_eval["traces"]
        + m3_eval["traces"]
        + m4_eval["traces"]
        + m3_plus_m4_eval["traces"]
        + ablated_affordances_eval["traces"]
        + no_foundation_eval["traces"]
        + regression_eval["traces"]
        + decoy_eval["traces"]
    )
    failure_traces = [trace for trace in eval_traces if not trace["episode_success"] or trace["rook_blunder"] or trace["graph_positive_false_basin"]]
    _write_jsonl_gzip(config.eval_episode_trace_path, eval_traces)
    _write_jsonl_gzip(config.failure_episode_pool_path, failure_traces)
    _write_jsonl_gzip(config.promoted_terminal_audit_path, m4_audit["candidate_rows"])
    _write_jsonl_gzip(config.reward_channel_audit_path, _reward_channel_rows(train_traces))
    _write_board_samples(config.board_sample_path, eval_traces)

    parent_after = _foundation_artifact_sanity(parent_artifact, parent)
    parent_delta = int(parent_snapshot != _parent_snapshot(parent))
    total_seconds = round(time.perf_counter() - start, 6)
    decision = _decision(
        config=config,
        parent_hash=parent_hash,
        parent_before=parent_before,
        parent_after=parent_after,
        parent_delta=parent_delta,
        hard_decoy_gate=hard_decoy_gate,
        learner=learner,
        m4_audit=m4_audit,
        parent_legacy_eval=parent_legacy_eval,
        parent_eval=parent_eval,
        child_weights_zeroed_eval=child_weights_zeroed_eval,
        m3_eval=m3_eval,
        m4_eval=m4_eval,
        m3_plus_m4_eval=m3_plus_m4_eval,
        ablated_affordances_eval=ablated_affordances_eval,
        no_foundation_eval=no_foundation_eval,
        regression_eval=regression_eval,
        decoy_eval=decoy_eval,
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
            "primary_training_unit": "episode_trajectory",
            "move_local_reward_primary": False,
        },
        "training_strategy": {
            "strategy_note": "docs/autogrowth/TRAINING_STRATEGY_NOTE.md",
            "episode_first_after_mate2": True,
            "move_local_scoring_diagnostic_only": True,
            "eligibility_trace_discount": config.gamma,
            "trainer_side_playout_not_runtime_selector": True,
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
        "hard_decoy_gate": hard_decoy_gate,
        "evaluation": {
            "parent_legacy_availability_classifier": _strip_traces(parent_legacy_eval),
            "parent": _strip_traces(parent_eval),
            "child_weights_zeroed": _strip_traces(child_weights_zeroed_eval),
            "M3": _strip_traces(m3_eval),
            "M4": _strip_traces(m4_eval),
            "M3_plus_M4": _strip_traces(m3_plus_m4_eval),
            "M3_plus_M4_ablated_affordances": _strip_traces(ablated_affordances_eval),
            "no_foundation": _strip_traces(no_foundation_eval),
            "regression_M4": _strip_traces(regression_eval),
            "decoy_M4": _strip_traces(decoy_eval),
        },
        "reward_channel_audit": _reward_channel_summary(train_traces),
        "m4_audit": m4_audit,
        "artifact_paths": {
            "main": config.output_path,
            "markdown": config.markdown_path,
            "train_episode_traces": config.train_episode_trace_path,
            "eval_episode_traces": config.eval_episode_trace_path,
            "failure_episode_pool": config.failure_episode_pool_path,
            "promoted_terminal_audit": config.promoted_terminal_audit_path,
            "reward_channel_audit": config.reward_channel_audit_path,
            "board_samples": config.board_sample_path,
        },
        "purity_boundary": _purity_boundary(),
        "timing": {"total_seconds": total_seconds},
    }
    result = TG48a2SameSideEpisodeTrainingResult(config=config, payload=payload, decision=decision)
    result.write_json()
    _write_markdown(config.markdown_path, result)
    return result


def _train_episode_rows(
    rows: list[dict[str, Any]],
    *,
    learner: TerminalAffordanceLearner,
    parent: dict[str, TerminalAffordanceLearner],
    config: TG48a2SameSideEpisodeTrainingConfig,
    label_source: str,
) -> list[dict[str, Any]]:
    traces = []
    for index, row in enumerate(rows):
        rng = random.Random(config.seed + 4821 + index)
        trace = _play_episode(
            row=row,
            episode_id=f"train_{index:05d}",
            parent=parent,
            learner=learner,
            config=config,
            behavior_policy="graph_with_trainer_side_exploration",
            rng=rng,
            training=True,
        )
        contrastive_trace = _contrastive_episode_trace(
            row=row,
            selected_trace=trace,
            episode_id=f"train_{index:05d}_contrastive",
            parent=parent,
            learner=learner,
            config=config,
            rng=random.Random(config.seed + 94821 + index),
        )
        _attach_contrastive_credit(trace, contrastive_trace=contrastive_trace, config=config)
        trace["label_source"] = label_source
        _apply_episode_credit(learner, trace=trace, config=config)
        traces.append(trace)
    return traces


def _evaluate_episode_rows(
    rows: list[dict[str, Any]],
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    learner: TerminalAffordanceLearner | None,
    trace_type: str,
    config: TG48a2SameSideEpisodeTrainingConfig,
    classifier_mode: str = "repaired",
) -> dict[str, Any]:
    traces = [
        _play_episode(
            row=row,
            episode_id=f"{trace_type}_{index:05d}",
            parent=parent,
            learner=learner,
            config=config,
            behavior_policy="graph_runtime_no_exploration",
            rng=random.Random(config.seed + index),
            training=False,
            classifier_mode=classifier_mode,
        )
        for index, row in enumerate(rows)
    ]
    return _summarize_episodes(traces)


def _zero_child_weights(learner: TerminalAffordanceLearner) -> TerminalAffordanceLearner:
    clone = copy.deepcopy(learner)
    for terminal in clone.terminals.values():
        terminal.local_weight = 0.0
    return clone


_POSITIVE_AFFORDANCE_PROMOTIONS = {
    "lateral_escape_affordance",
    "geometry_transition_affordance",
    "foundation_handoff_affordance",
}


def _ablate_promoted_positive_affordances(
    learner: TerminalAffordanceLearner,
    *,
    m4_audit: Mapping[str, Any],
) -> TerminalAffordanceLearner:
    clone = copy.deepcopy(learner)
    for row in m4_audit["candidate_rows"]:
        if row.get("promoted_as") not in _POSITIVE_AFFORDANCE_PROMOTIONS:
            continue
        terminal = clone.terminals.get(row["terminal_key"])
        if terminal is not None:
            terminal.local_weight = 0.0
    return clone


def _play_episode(
    *,
    row: Mapping[str, Any],
    episode_id: str,
    parent: dict[str, TerminalAffordanceLearner] | None,
    learner: TerminalAffordanceLearner | None,
    config: TG48a2SameSideEpisodeTrainingConfig,
    behavior_policy: str,
    rng: random.Random,
    training: bool,
    classifier_mode: str = "repaired",
    forced_first_move_uci: str | None = None,
) -> dict[str, Any]:
    board = chess.Board(str(row["fen"]))
    positions = [board.fen()]
    white_moves: list[str] = []
    black_replies: list[str] = []
    selected_moves_by_white_ply: list[str | None] = []
    terminal_activations_by_white_ply: list[list[str]] = []
    legal_reply_coverage: list[dict[str, Any]] = []
    endpoint_type = "no_progress"
    endpoint_diagnostics: dict[str, Any] = {}
    episode_diagnostics: dict[str, bool] = {
        "partial_only_near_basin_seen": False,
        "handoff_available_seen": False,
        "legacy_availability_partial_only_near_basin_seen": False,
        "legacy_availability_graph_positive_false_basin_seen": False,
    }
    max_white = config.max_white_moves
    max_plies = config.max_total_plies
    total_plies = 0
    for white_ply in range(max_white):
        if board.turn != chess.WHITE or total_plies >= max_plies:
            break
        if white_ply == 0 and forced_first_move_uci is not None:
            move = chess.Move.from_uci(forced_first_move_uci)
            if move not in board.legal_moves:
                move = None
        else:
            move = _select_white_move(
                board,
                parent=parent,
                learner=learner,
                config=config,
                rng=rng,
                training=training,
            )
        selected_moves_by_white_ply.append(None if move is None else move.uci())
        if move is None or move not in board.legal_moves:
            endpoint_type = "illegal"
            endpoint_diagnostics = _endpoint_diagnostics(board, None, parent=parent, config=config)
            _accumulate_episode_diagnostics(episode_diagnostics, endpoint_diagnostics)
            break
        terminal_keys = [key for key, _scale in _micro_terminal_keys(board, move)]
        terminal_activations_by_white_ply.append(terminal_keys)
        white_moves.append(move.uci())
        board.push(move)
        total_plies += 1
        positions.append(board.fen())
        endpoint_type, endpoint_diagnostics = _classify_endpoint(
            board,
            parent=parent,
            config=config,
            classifier_mode=classifier_mode,
        )
        _accumulate_episode_diagnostics(episode_diagnostics, endpoint_diagnostics)
        if endpoint_type in _STOP_ENDPOINTS:
            break
        if board.turn != chess.BLACK or total_plies >= max_plies:
            endpoint_type = "horizon_reached_safe" if _safe_board(board) else "no_progress"
            break
        replies = sorted(board.legal_moves, key=lambda item: item.uci())
        legal_reply_coverage.append({
            "white_ply": white_ply,
            "reply_total": len(replies),
            "all_legal_replies_enumerated": True,
            "learner_visible_labels": False,
        })
        reply = _select_black_reply(board, replies)
        if reply is None:
            endpoint_type = "horizon_reached_safe" if _safe_board(board) else "stalemate"
            break
        black_replies.append(reply.uci())
        board.push(reply)
        total_plies += 1
        positions.append(board.fen())
        endpoint_type, endpoint_diagnostics = _classify_endpoint(
            board,
            parent=parent,
            config=config,
            classifier_mode=classifier_mode,
        )
        _accumulate_episode_diagnostics(episode_diagnostics, endpoint_diagnostics)
        if endpoint_type in _STOP_ENDPOINTS:
            break
    else:
        endpoint_type = "horizon_reached_safe" if _safe_board(board) else "no_progress"
        endpoint_diagnostics = _endpoint_board_diagnostics(board, parent=parent, config=config)
        _accumulate_episode_diagnostics(episode_diagnostics, endpoint_diagnostics)
    if not endpoint_diagnostics:
        endpoint_diagnostics = _endpoint_board_diagnostics(board, parent=parent, config=config)
        _accumulate_episode_diagnostics(episode_diagnostics, endpoint_diagnostics)
    endpoint_diagnostics = {**endpoint_diagnostics, **episode_diagnostics}
    reward_channels, trajectory_reward = _trajectory_reward(endpoint_type, endpoint_diagnostics)
    credit_assignments = _credit_assignments(
        terminal_activations_by_white_ply=terminal_activations_by_white_ply,
        reward_channels=reward_channels,
        trajectory_reward=trajectory_reward,
        gamma=config.gamma,
    )
    trace = {
        "schema_version": "tg48a2_episode_trace.v0",
        "start_fen": row["fen"],
        "split": row.get("split"),
        "family": row.get("family"),
        "episode_id": episode_id,
        "behavior_policy": behavior_policy,
        "classifier_mode": classifier_mode,
        "max_white_moves": config.max_white_moves,
        "max_total_plies": config.max_total_plies,
        "white_moves": white_moves,
        "black_replies": black_replies,
        "positions": positions,
        "terminal_activations_by_white_ply": terminal_activations_by_white_ply,
        "selected_moves_by_white_ply": selected_moves_by_white_ply,
        "legal_reply_coverage": legal_reply_coverage,
        "endpoint_type": endpoint_type,
        "endpoint_fen": board.fen(),
        "endpoint_validated_entry": bool(endpoint_diagnostics.get("validated_entry", False)),
        "endpoint_validated_mate1": bool(endpoint_diagnostics.get("validated_mate1_entry", False)),
        "endpoint_validated_mate2": bool(endpoint_diagnostics.get("validated_mate2_entry", False)),
        "endpoint_killbox_friendly": bool(endpoint_diagnostics.get("killbox_friendly", False)),
        "endpoint_opposed_side_or_safer_geometry": bool(endpoint_diagnostics.get("geometry_transition", False)),
        "rook_blunder": bool(endpoint_diagnostics.get("rook_blunder", False)),
        "stalemate": bool(endpoint_diagnostics.get("stalemate", False)),
        "illegal": endpoint_type == "illegal",
        "confinement_regression": bool(endpoint_diagnostics.get("confinement_regression", False)),
        "graph_positive_false_basin": bool(endpoint_diagnostics.get("graph_positive_false_basin", False)),
        "partial_only_near_basin": bool(endpoint_diagnostics.get("partial_only_near_basin", False)),
        "partial_only_near_basin_seen": bool(endpoint_diagnostics.get("partial_only_near_basin_seen", False)),
        "handoff_available": bool(endpoint_diagnostics.get("handoff_available", False)),
        "handoff_available_seen": bool(endpoint_diagnostics.get("handoff_available_seen", False)),
        "legacy_availability_endpoint_type": _classify_legacy_availability_endpoint(endpoint_diagnostics),
        "trajectory_reward": trajectory_reward,
        "reward_channels": reward_channels,
        "credit_assignments": credit_assignments,
        "episode_success": _episode_success(endpoint_type),
        "same_side_subskill_success": endpoint_type == "safer_opposed_or_killbox_geometry",
        "lateral_escape_success": bool(
            endpoint_diagnostics.get("lateral_escape_survived_reply", False)
            and not endpoint_diagnostics.get("rook_blunder", False)
        ),
        "trainer_side_playout_used_for_reward": True,
        "trainer_side_playout_used_for_runtime_selection": False,
        "learner_visible_labels": False,
    }
    _validate_episode_trace_learner_visible(trace)
    return trace


def _contrastive_episode_trace(
    *,
    row: Mapping[str, Any],
    selected_trace: Mapping[str, Any],
    episode_id: str,
    parent: dict[str, TerminalAffordanceLearner],
    learner: TerminalAffordanceLearner,
    config: TG48a2SameSideEpisodeTrainingConfig,
    rng: random.Random,
) -> dict[str, Any] | None:
    board = chess.Board(str(row["fen"]))
    selected_uci = selected_trace["selected_moves_by_white_ply"][0] if selected_trace["selected_moves_by_white_ply"] else None
    move = _select_contrastive_first_move(
        board,
        selected_uci=selected_uci,
        parent=parent,
        learner=learner,
        config=config,
    )
    if move is None:
        return None
    return _play_episode(
        row=row,
        episode_id=episode_id,
        parent=parent,
        learner=learner,
        config=config,
        behavior_policy="trainer_side_contrastive_alternative",
        rng=rng,
        training=False,
        forced_first_move_uci=move.uci(),
    )


def _select_contrastive_first_move(
    board: chess.Board,
    *,
    selected_uci: str | None,
    parent: dict[str, TerminalAffordanceLearner],
    learner: TerminalAffordanceLearner,
    config: TG48a2SameSideEpisodeTrainingConfig,
) -> chess.Move | None:
    candidates = [move for move in sorted(board.legal_moves, key=lambda item: item.uci()) if move.uci() != selected_uci]
    if not candidates:
        return None
    ranked = sorted(
        (
            (
                _trainer_exploration_score(board, move, parent=parent, config=config),
                _score_micro_move(board, move, parent=parent, learner=learner),
                move.uci(),
                move,
            )
            for move in candidates
        ),
        reverse=True,
    )
    return ranked[0][-1]


def _attach_contrastive_credit(
    trace: dict[str, Any],
    *,
    contrastive_trace: Mapping[str, Any] | None,
    config: TG48a2SameSideEpisodeTrainingConfig,
) -> None:
    if contrastive_trace is None:
        trace["credit_assignment_mode"] = "selected_trajectory_no_available_pair"
        trace["contrastive_episode"] = {"available": False, "learner_visible_labels": False}
        return
    trace["credit_assignment_mode"] = "contrastive_terminal_activation_difference"
    trace["contrastive_episode"] = _contrastive_summary(contrastive_trace)
    trace["credit_assignments"] = _credit_assignments(
        terminal_activations_by_white_ply=trace["terminal_activations_by_white_ply"],
        reward_channels=trace["reward_channels"],
        trajectory_reward=float(trace["trajectory_reward"]),
        gamma=config.gamma,
        contrastive_terminal_activations_by_white_ply=contrastive_trace["terminal_activations_by_white_ply"],
        contrastive_reward_channels=contrastive_trace["reward_channels"],
        contrastive_trajectory_reward=float(contrastive_trace["trajectory_reward"]),
    )


def _contrastive_summary(trace: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "available": True,
        "episode_id": trace["episode_id"],
        "behavior_policy": trace["behavior_policy"],
        "endpoint_type": trace["endpoint_type"],
        "episode_success": trace["episode_success"],
        "same_side_subskill_success": trace["same_side_subskill_success"],
        "lateral_escape_success": trace["lateral_escape_success"],
        "endpoint_validated_entry": trace["endpoint_validated_entry"],
        "endpoint_opposed_side_or_safer_geometry": trace["endpoint_opposed_side_or_safer_geometry"],
        "rook_blunder": trace["rook_blunder"],
        "stalemate": trace["stalemate"],
        "illegal": trace["illegal"],
        "confinement_regression": trace["confinement_regression"],
        "graph_positive_false_basin": trace["graph_positive_false_basin"],
        "partial_only_near_basin": trace["partial_only_near_basin"],
        "partial_only_near_basin_seen": trace["partial_only_near_basin_seen"],
        "handoff_available_seen": trace["handoff_available_seen"],
        "trajectory_reward": trace["trajectory_reward"],
        "reward_channels": trace["reward_channels"],
        "terminal_activations_by_white_ply": trace["terminal_activations_by_white_ply"],
        "selected_moves_by_white_ply": trace["selected_moves_by_white_ply"],
        "learner_visible_labels": False,
    }


def _accumulate_episode_diagnostics(flags: dict[str, bool], diag: Mapping[str, Any]) -> None:
    flags["partial_only_near_basin_seen"] = flags["partial_only_near_basin_seen"] or bool(diag.get("partial_only_near_basin"))
    flags["handoff_available_seen"] = flags["handoff_available_seen"] or bool(diag.get("handoff_available"))
    flags["legacy_availability_partial_only_near_basin_seen"] = flags[
        "legacy_availability_partial_only_near_basin_seen"
    ] or bool(diag.get("legacy_availability_partial_only_near_basin"))
    flags["legacy_availability_graph_positive_false_basin_seen"] = flags[
        "legacy_availability_graph_positive_false_basin_seen"
    ] or bool(diag.get("legacy_availability_graph_positive_false_basin"))


_STOP_ENDPOINTS = {
    "validated_mate1_entry",
    "validated_mate2_entry",
    "validated_foundation_entry",
    "safer_opposed_or_killbox_geometry",
    "rook_blunder",
    "stalemate",
    "illegal",
    "confinement_regression",
    "graph_positive_false_basin",
}


def _select_white_move(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    learner: TerminalAffordanceLearner | None,
    config: TG48a2SameSideEpisodeTrainingConfig,
    rng: random.Random,
    training: bool,
) -> chess.Move | None:
    moves = sorted(board.legal_moves, key=lambda item: item.uci())
    if not moves:
        return None
    if training and rng.random() < config.exploration_rate:
        ranked = sorted(
            ((_trainer_exploration_score(board, move, parent=parent, config=config), move.uci(), move) for move in moves),
            reverse=True,
        )
        return ranked[0][-1]
    ranked = sorted(
        ((_score_micro_move(board, move, parent=parent, learner=learner), move.uci(), move) for move in moves),
        reverse=True,
    )
    return ranked[0][-1]


def _trainer_exploration_score(
    board: chess.Board,
    move: chess.Move,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    config: TG48a2SameSideEpisodeTrainingConfig,
) -> float:
    after = board.copy(stack=False)
    after.push(move)
    endpoint, diag = _classify_endpoint(after, parent=parent, config=config)
    score = 0.0
    score += 10.0 if endpoint in {"validated_mate1_entry", "validated_mate2_entry", "validated_foundation_entry"} else 0.0
    score += 5.0 if endpoint == "safer_opposed_or_killbox_geometry" else 0.0
    score += 3.0 if _is_lateral_rook_move(board, move) and _safe_board(after) else 0.0
    score += 1.0 if diag.get("geometry_transition") else 0.0
    score += 0.5 if diag.get("partial_only_near_basin") else 0.0
    score -= 8.0 if diag.get("rook_blunder") or diag.get("stalemate") else 0.0
    score -= 5.0 if diag.get("graph_positive_false_basin") else 0.0
    return score


def _select_black_reply(board: chess.Board, replies: list[chess.Move]) -> chess.Move | None:
    if not replies:
        return None
    return sorted(((_black_reply_risk(board, reply), reply.uci(), reply) for reply in replies), reverse=True)[0][-1]


def _black_reply_risk(board: chess.Board, reply: chess.Move) -> float:
    after = board.copy(stack=False)
    after.push(reply)
    risk = 0.0
    rook_squares = set(board.pieces(chess.ROOK, chess.WHITE))
    risk += 100.0 if reply.to_square in rook_squares else 0.0
    risk += 10.0 if _rook_capturable_by_reply(after) else 0.0
    risk += float(_confinement_area(after) - _confinement_area(board)) * 0.1
    risk += float(_black_mobility(after)) * 0.05
    return risk


def _classify_endpoint(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    config: TG48a2SameSideEpisodeTrainingConfig,
    classifier_mode: str = "repaired",
) -> tuple[str, dict[str, Any]]:
    diag = _endpoint_board_diagnostics(board, parent=parent, config=config)
    if classifier_mode == "legacy_availability_diagnostic":
        return _classify_legacy_availability_endpoint(diag), diag
    if diag["rook_blunder"] or diag["rook_missing"]:
        return "rook_blunder", diag
    if diag["stalemate"]:
        return "stalemate", diag
    if diag["confinement_regression"]:
        return "confinement_regression", diag
    if diag["validated_mate1_entry"]:
        return "validated_mate1_entry", diag
    if diag["validated_mate2_entry"]:
        return "validated_mate2_entry", diag
    if diag["validated_entry"]:
        return "validated_foundation_entry", diag
    if diag["graph_positive_false_basin"]:
        return "graph_positive_false_basin", diag
    if diag["geometry_transition"] and diag["killbox_friendly"] and not diag["rook_blunder"]:
        return "safer_opposed_or_killbox_geometry", diag
    return "no_progress", diag


def _classify_legacy_availability_endpoint(diag: Mapping[str, Any]) -> str:
    if diag["rook_blunder"] or diag["rook_missing"]:
        return "rook_blunder"
    if diag["stalemate"]:
        return "stalemate"
    if diag["confinement_regression"]:
        return "confinement_regression"
    if diag["legacy_availability_graph_positive_false_basin"]:
        return "graph_positive_false_basin"
    if diag["legacy_availability_partial_only_near_basin"]:
        return "partial_only_near_basin"
    if diag["legacy_availability_validated_mate1_entry"]:
        return "validated_mate1_entry"
    if diag["legacy_availability_validated_mate2_entry"]:
        return "validated_mate2_entry"
    if diag["legacy_availability_validated_entry"]:
        return "validated_foundation_entry"
    if diag["geometry_transition"] and diag["killbox_friendly"] and not diag["rook_blunder"]:
        return "safer_opposed_or_killbox_geometry"
    return "no_progress"


def _endpoint_diagnostics(
    board: chess.Board,
    move: chess.Move | None,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    config: TG48a2SameSideEpisodeTrainingConfig,
) -> dict[str, Any]:
    if move is None or move not in board.legal_moves:
        diag = _endpoint_board_diagnostics(board, parent=parent, config=config)
        diag["illegal"] = True
        return diag
    after = board.copy(stack=False)
    after.push(move)
    return _endpoint_board_diagnostics(after, parent=parent, config=config)


def _endpoint_board_diagnostics(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    config: TG48a2SameSideEpisodeTrainingConfig,
) -> dict[str, Any]:
    eval_config = EdgeKillboxCurriculumConfig(max_horizon_plies=config.max_total_plies)
    metrics = _move_metrics(_null_white_board(board), None, parent=parent, config=eval_config)
    # `_move_metrics` is move-based; direct endpoint fields below are authoritative.
    f = extract_learner_features(_white_turn_copy(board))
    axis = _axis_pattern(f)
    response = _foundation_response_for_board(board, parent=parent, config=config)
    diag = {
        "validated_entry": response["validated_entry"],
        "validated_mate1_entry": response["validated_mate1_entry"],
        "validated_mate2_entry": response["validated_mate2_entry"],
        "graph_positive_false_basin": response["graph_positive_false_basin"],
        "partial_only_near_basin": response["partial_only_near_basin"],
        "handoff_available": response["handoff_available"],
        "handoff_available_mate1_entry": response["handoff_available_mate1_entry"],
        "handoff_available_mate2_entry": response["handoff_available_mate2_entry"],
        "handoff_available_partial_only_near_basin": response["handoff_available_partial_only_near_basin"],
        "handoff_available_graph_positive_false_basin": response["handoff_available_graph_positive_false_basin"],
        "legacy_availability_validated_entry": response["legacy_availability_validated_entry"],
        "legacy_availability_validated_mate1_entry": response["legacy_availability_validated_mate1_entry"],
        "legacy_availability_validated_mate2_entry": response["legacy_availability_validated_mate2_entry"],
        "legacy_availability_graph_positive_false_basin": response["legacy_availability_graph_positive_false_basin"],
        "legacy_availability_partial_only_near_basin": response["legacy_availability_partial_only_near_basin"],
        "rook_blunder": _rook_capturable_by_reply(_white_turn_copy(board)),
        "rook_missing": not bool(board.pieces(chess.ROOK, chess.WHITE)),
        "stalemate": board.is_stalemate(),
        "confinement_regression": False,
        "killbox_friendly": bool(int(f["black_king_on_edge"]) == 1 and _support_band(f)),
        "geometry_transition": axis != 1 and int(f["black_king_on_edge"]) == 1 and _support_band(f),
        "lateral_escape_survived_reply": axis != 1 and not _rook_capturable_by_reply(_white_turn_copy(board)),
        "illegal": False,
        "metrics_note": metrics["illegal"],
    }
    return diag


def _foundation_response_for_board(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    config: TG48a2SameSideEpisodeTrainingConfig,
) -> dict[str, bool]:
    if parent is None:
        return _empty_foundation_response_flags()
    direct = _direct_foundation_response_for_board(board, parent=parent)
    availability = _foundation_availability_for_board(board, parent=parent, config=config, force_white_turn=False)
    legacy = _foundation_availability_for_board(board, parent=parent, config=config, force_white_turn=True)
    return {
        **direct,
        "handoff_available": availability["validated_entry"],
        "handoff_available_mate1_entry": availability["validated_mate1_entry"],
        "handoff_available_mate2_entry": availability["validated_mate2_entry"],
        "handoff_available_graph_positive_false_basin": availability["graph_positive_false_basin"],
        "handoff_available_partial_only_near_basin": availability["partial_only_near_basin"],
        "legacy_availability_validated_entry": legacy["validated_entry"],
        "legacy_availability_validated_mate1_entry": legacy["validated_mate1_entry"],
        "legacy_availability_validated_mate2_entry": legacy["validated_mate2_entry"],
        "legacy_availability_graph_positive_false_basin": legacy["graph_positive_false_basin"],
        "legacy_availability_partial_only_near_basin": legacy["partial_only_near_basin"],
    }


def _empty_foundation_response_flags() -> dict[str, bool]:
    return {
        "validated_entry": False,
        "validated_mate1_entry": False,
        "validated_mate2_entry": False,
        "graph_positive_false_basin": False,
        "partial_only_near_basin": False,
        "handoff_available": False,
        "handoff_available_mate1_entry": False,
        "handoff_available_mate2_entry": False,
        "handoff_available_graph_positive_false_basin": False,
        "handoff_available_partial_only_near_basin": False,
        "legacy_availability_validated_entry": False,
        "legacy_availability_validated_mate1_entry": False,
        "legacy_availability_validated_mate2_entry": False,
        "legacy_availability_graph_positive_false_basin": False,
        "legacy_availability_partial_only_near_basin": False,
    }


def _direct_foundation_response_for_board(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner],
) -> dict[str, bool]:
    if board.turn != chess.BLACK:
        return {
            "validated_entry": False,
            "validated_mate1_entry": False,
            "validated_mate2_entry": False,
            "graph_positive_false_basin": False,
            "partial_only_near_basin": False,
        }
    response = _edge_foundation_response(board, parent)
    validated_entry = bool(response["validated_all_reply_handoff"])
    partial_only = bool(response["validated_partial_only"] and not validated_entry)
    return {
        "validated_entry": validated_entry,
        "validated_mate1_entry": bool(response["validated_mate1_entry"]),
        "validated_mate2_entry": bool(response["validated_mate2_entry"]),
        "graph_positive_false_basin": bool(response["graph_positive_false_basin"] and not partial_only),
        "partial_only_near_basin": partial_only,
    }


def _foundation_availability_for_board(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner],
    config: TG48a2SameSideEpisodeTrainingConfig,
    force_white_turn: bool,
) -> dict[str, bool]:
    if not force_white_turn and board.turn != chess.WHITE:
        return {
            "validated_entry": False,
            "validated_mate1_entry": False,
            "validated_mate2_entry": False,
            "graph_positive_false_basin": False,
            "partial_only_near_basin": False,
        }
    white_board = _white_turn_copy(board) if force_white_turn else board.copy(stack=False)
    legal = list(white_board.legal_moves)
    best = {
        "validated_entry": False,
        "validated_mate1_entry": False,
        "validated_mate2_entry": False,
        "graph_positive_false_basin": False,
        "partial_only_near_basin": False,
    }
    eval_config = EdgeKillboxCurriculumConfig(max_horizon_plies=config.max_total_plies)
    for move in legal:
        metrics = _move_metrics(white_board, move, parent=parent, config=eval_config)
        best["validated_entry"] = best["validated_entry"] or bool(metrics["validated_entry"])
        best["validated_mate1_entry"] = best["validated_mate1_entry"] or bool(metrics["validated_mate1_entry"])
        best["validated_mate2_entry"] = best["validated_mate2_entry"] or bool(metrics["validated_mate2_entry"])
        best["graph_positive_false_basin"] = best["graph_positive_false_basin"] or bool(
            metrics["graph_positive_false_basin"] and not metrics["partial_only_near_basin"]
        )
        best["partial_only_near_basin"] = best["partial_only_near_basin"] or bool(metrics["partial_only_near_basin"])
    return best


def _null_white_board(board: chess.Board) -> chess.Board:
    white = _white_turn_copy(board)
    return white


def _white_turn_copy(board: chess.Board) -> chess.Board:
    copy_board = board.copy(stack=False)
    copy_board.turn = chess.WHITE
    return copy_board


def _safe_board(board: chess.Board) -> bool:
    white = _white_turn_copy(board)
    return bool(white.pieces(chess.ROOK, chess.WHITE)) and not _rook_capturable_by_reply(white) and not white.is_stalemate()


def _black_mobility(board: chess.Board) -> int:
    black = board.copy(stack=False)
    black.turn = chess.BLACK
    return black.legal_moves.count()


def _trajectory_reward(endpoint_type: str, diag: Mapping[str, Any]) -> tuple[dict[str, float], float]:
    channels = {
        "foundation_entry_achieved": 0.0,
        "foundation_handoff_available": 0.0,
        "near_basin_shaping": 0.0,
        "lateral_escape": 0.0,
        "geometry_transition": 0.0,
        "safety": 0.0,
        "false_basin": 0.0,
        "terminal_failure": 0.0,
    }
    if endpoint_type == "validated_mate1_entry":
        channels["foundation_entry_achieved"] = 10.0
    elif endpoint_type in {"validated_mate2_entry", "validated_foundation_entry"}:
        channels["foundation_entry_achieved"] = 8.0
    if (
        channels["foundation_entry_achieved"] == 0.0
        and (diag.get("handoff_available") or diag.get("handoff_available_seen"))
    ):
        channels["foundation_handoff_available"] = 1.0
    if (
        endpoint_type == "partial_only_near_basin"
        or diag.get("partial_only_near_basin")
        or diag.get("partial_only_near_basin_seen")
    ) and not diag.get("graph_positive_false_basin"):
        channels["near_basin_shaping"] = 0.5
    if endpoint_type == "safer_opposed_or_killbox_geometry":
        channels["geometry_transition"] = 5.0
    if diag.get("lateral_escape_survived_reply"):
        channels["lateral_escape"] = 3.0
    if diag.get("killbox_friendly") and not diag.get("rook_blunder"):
        channels["safety"] += 1.0
    if endpoint_type == "graph_positive_false_basin":
        channels["false_basin"] = -5.0
    if endpoint_type == "confinement_regression":
        channels["terminal_failure"] = -6.0
    if endpoint_type in {"rook_blunder", "stalemate", "illegal"}:
        channels["terminal_failure"] = -8.0
    reward = round(sum(channels.values()), 6)
    return channels, reward


def _credit_assignments(
    *,
    terminal_activations_by_white_ply: list[list[str]],
    reward_channels: Mapping[str, float],
    trajectory_reward: float,
    gamma: float,
    contrastive_terminal_activations_by_white_ply: list[list[str]] | None = None,
    contrastive_reward_channels: Mapping[str, float] | None = None,
    contrastive_trajectory_reward: float = 0.0,
) -> list[dict[str, Any]]:
    assignments = []
    contrastive_activations = contrastive_terminal_activations_by_white_ply or []
    total = max(len(terminal_activations_by_white_ply), len(contrastive_activations))
    channel_keys = set(reward_channels)
    if contrastive_reward_channels is not None:
        channel_keys.update(contrastive_reward_channels)
    reward_delta = round(trajectory_reward - contrastive_trajectory_reward, 6)
    for index in range(total):
        keys = terminal_activations_by_white_ply[index] if index < len(terminal_activations_by_white_ply) else []
        contrastive_keys = contrastive_activations[index] if index < len(contrastive_activations) else []
        selected_set = set(keys)
        contrastive_set = set(contrastive_keys)
        selected_only = sorted(selected_set - contrastive_set)
        contrastive_only = sorted(contrastive_set - selected_set)
        shared = selected_set & contrastive_set
        discount = gamma ** max(0, total - index - 1)
        discounted_reward = round(reward_delta * discount, 6)
        channel_credit = {
            key: round((float(reward_channels.get(key, 0.0)) - float((contrastive_reward_channels or {}).get(key, 0.0))) * discount, 6)
            for key in sorted(channel_keys)
        }
        terminal_credit = {key: discounted_reward for key in selected_only}
        terminal_credit.update({key: round(-discounted_reward, 6) for key in contrastive_only})
        terminal_sources = {key: "selected_only" for key in selected_only}
        terminal_sources.update({key: "alternative_only" for key in contrastive_only})
        assignments.append({
            "white_ply": index,
            "terminal_count": len(terminal_credit),
            "selected_terminal_count": len(keys),
            "contrastive_terminal_count": len(contrastive_keys),
            "shared_terminal_count": len(shared),
            "discount": round(discount, 6),
            "discounted_reward": discounted_reward,
            "reward_delta": reward_delta,
            "reward_channels": channel_credit,
            "terminal_credit": terminal_credit,
            "terminal_sources": terminal_sources,
            "learner_visible_labels": False,
        })
    return assignments


def _apply_episode_credit(
    learner: TerminalAffordanceLearner,
    *,
    trace: Mapping[str, Any],
    config: TG48a2SameSideEpisodeTrainingConfig,
) -> None:
    activations = trace["terminal_activations_by_white_ply"]
    assignments = trace["credit_assignments"]
    for index, assignment in enumerate(assignments):
        terminal_credit = assignment.get("terminal_credit")
        if terminal_credit is None:
            keys = activations[index] if index < len(activations) else []
            terminal_credit = {key: float(assignment["discounted_reward"]) for key in keys}
        for key, reward_value in terminal_credit.items():
            reward = float(reward_value)
            terminal = learner.get_terminal(key)
            terminal.update(
                reward=reward,
                eta=config.eta_m3,
                scale=1.0,
                cycle=learner.cycle,
            )
            learner.m3_update_count += 1
        learner.cycle += 1


def _terminal_episode_audit(
    learner: TerminalAffordanceLearner,
    traces: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    audit: dict[str, dict[str, Any]] = {}
    for trace in traces:
        episode_credit: dict[tuple[str, str], float] = {}
        for assignment in trace["credit_assignments"]:
            terminal_credit = assignment.get("terminal_credit")
            terminal_sources = assignment.get("terminal_sources", {})
            if terminal_credit is None:
                terminal_credit = {
                    key: float(assignment["discounted_reward"])
                    for key in trace["terminal_activations_by_white_ply"][assignment["white_ply"]]
                }
                terminal_sources = {key: "selected_only" for key in terminal_credit}
            for key, value in terminal_credit.items():
                source = str(terminal_sources.get(key, "selected_only"))
                episode_credit[(key, source)] = episode_credit.get((key, source), 0.0) + float(value)
        for (key, source), signed_credit in episode_credit.items():
            outcome = _audit_outcome_for_source(trace, source)
            positive = signed_credit > 0.0
            negative = signed_credit < 0.0
            item = audit.setdefault(
                key,
                {
                    "activation_count": 0,
                    "positive_episode_activation_count": 0,
                    "negative_episode_activation_count": 0,
                    "lateral_escape_episode_activation_count": 0,
                    "geometry_transition_episode_activation_count": 0,
                    "validated_entry_episode_activation_count": 0,
                    "false_basin_episode_activation_count": 0,
                    "unsafe_episode_activation_count": 0,
                    "decoy_false_handoff_activation_count": 0,
                    "discounted_credit_sum": 0.0,
                    "discounted_debt_sum": 0.0,
                },
            )
            item["activation_count"] += 1
            item["positive_episode_activation_count"] += int(positive)
            item["negative_episode_activation_count"] += int(negative)
            item["lateral_escape_episode_activation_count"] += int(outcome["lateral_escape_success"])
            item["geometry_transition_episode_activation_count"] += int(outcome["endpoint_opposed_side_or_safer_geometry"])
            item["validated_entry_episode_activation_count"] += int(outcome["endpoint_validated_entry"])
            item["false_basin_episode_activation_count"] += int(
                outcome["graph_positive_false_basin"] or outcome["partial_only_near_basin"]
            )
            item["unsafe_episode_activation_count"] += int(
                outcome["rook_blunder"] or outcome["stalemate"] or outcome["illegal"] or outcome["confinement_regression"]
            )
            item["decoy_false_handoff_activation_count"] += int(
                trace["family"] in {"decoy_edge_killbox", "hard_decoy_edge_killbox"} and outcome["endpoint_validated_entry"]
            )
            if signed_credit > 0:
                item["discounted_credit_sum"] += signed_credit
            elif signed_credit < 0:
                item["discounted_debt_sum"] += abs(signed_credit)
    return audit


def _audit_outcome_for_source(trace: Mapping[str, Any], source: str) -> Mapping[str, Any]:
    if source == "alternative_only":
        contrastive = trace.get("contrastive_episode", {})
        if contrastive.get("available"):
            return contrastive
    return trace


def _promote_m4(
    learner: TerminalAffordanceLearner,
    *,
    terminal_audit: Mapping[str, Mapping[str, Any]],
    config: TG48a2SameSideEpisodeTrainingConfig,
) -> tuple[TerminalAffordanceLearner, dict[str, Any]]:
    clone = TerminalAffordanceLearner.create(eta_m3=learner.eta_m3, rich_feature_credit_scale=learner.rich_feature_credit_scale)
    rows = []
    counts = {
        "lateral_escape_affordance": 0,
        "geometry_transition_affordance": 0,
        "foundation_handoff_affordance": 0,
        "safety_veto": 0,
    }
    for key, terminal in learner.terminals.items():
        audit = dict(terminal_audit.get(key, {}))
        credit = float(audit.get("discounted_credit_sum", 0.0))
        debt = float(audit.get("discounted_debt_sum", 0.0))
        total = credit + debt
        precision = 0.0 if total <= 0 else credit / total
        negative_precision = 0.0 if total <= 0 else debt / total
        promoted_as = None
        if (
            terminal.local_weight > 0
            and terminal.positive_credit >= config.m4_min_positive_support
            and precision >= config.m4_affordance_precision_threshold
            and audit.get("unsafe_episode_activation_count", 0) == 0
            and audit.get("decoy_false_handoff_activation_count", 0) == 0
        ):
            if audit.get("validated_entry_episode_activation_count", 0) > 0:
                promoted_as = "foundation_handoff_affordance"
            elif audit.get("geometry_transition_episode_activation_count", 0) > 0:
                promoted_as = "geometry_transition_affordance"
            elif audit.get("lateral_escape_episode_activation_count", 0) > 0:
                promoted_as = "lateral_escape_affordance"
        if (
            promoted_as is None
            and terminal.local_weight < 0
            and terminal.negative_credit >= config.m4_min_negative_support
            and negative_precision >= config.m4_veto_precision_threshold
            and (
                audit.get("unsafe_episode_activation_count", 0) > 0
                or audit.get("false_basin_episode_activation_count", 0) > 0
            )
        ):
            promoted_as = "safety_veto"
        if promoted_as:
            copied = copy.deepcopy(terminal)
            copied.cell.state = StemCellState.MATURE
            clone.terminals[key] = copied
            counts[promoted_as] += 1
        row = {
            "terminal_key": key,
            "positive_intervention_count": terminal.positive_credit,
            "negative_intervention_count": terminal.negative_credit,
            "neutral_count": terminal.neutral_credit,
            "local_weight": round(terminal.local_weight, 6),
            "precision": round(precision, 6),
            "negative_precision": round(negative_precision, 6),
            **audit,
            "discounted_credit_sum": round(credit, 6),
            "discounted_debt_sum": round(debt, 6),
            "promoted_as": promoted_as,
            "promoted": bool(promoted_as),
        }
        _validate_micro_learner_record({"terminal_key": key})
        rows.append(row)
    return clone, {
        "M4_candidate_count": len(rows),
        "M4_promoted_terminal_count": sum(counts.values()),
        "promoted_lateral_escape_affordance_count": counts["lateral_escape_affordance"],
        "promoted_geometry_transition_affordance_count": counts["geometry_transition_affordance"],
        "promoted_foundation_handoff_affordance_count": counts["foundation_handoff_affordance"],
        "promoted_veto_count": counts["safety_veto"],
        "candidate_rows": rows,
    }


def _summarize_episodes(traces: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(traces)
    return {
        "episode_count": total,
        "episode_success_count": sum(int(trace["episode_success"]) for trace in traces),
        "episode_success_rate": _rate(sum(int(trace["episode_success"]) for trace in traces), total),
        "same_side_subskill_success_rate": _rate(sum(int(trace["same_side_subskill_success"]) for trace in traces), total),
        "lateral_escape_success_rate": _rate(sum(int(trace["lateral_escape_success"]) for trace in traces), total),
        "selected_lateral_rook_rate": _rate(
            sum(int(any(_move_is_lateral_from_trace(trace, ply) for ply in range(len(trace["white_moves"])))) for trace in traces),
            total,
        ),
        "safe_lateral_rook_available_rate": _rate(sum(int(_safe_lateral_available(chess.Board(trace["start_fen"]))) for trace in traces), total),
        "transition_to_opposed_or_killbox_rate": _rate(sum(int(trace["endpoint_opposed_side_or_safer_geometry"]) for trace in traces), total),
        "validated_entry_rate": _rate(sum(int(trace["endpoint_validated_entry"]) for trace in traces), total),
        "validated_mate1_entry_rate": _rate(sum(int(trace["endpoint_validated_mate1"]) for trace in traces), total),
        "validated_mate2_entry_rate": _rate(sum(int(trace["endpoint_validated_mate2"]) for trace in traces), total),
        "graph_positive_false_basin_count": sum(int(trace["graph_positive_false_basin"]) for trace in traces),
        "partial_only_near_basin_count": sum(int(trace["partial_only_near_basin"]) for trace in traces),
        "partial_only_near_basin_seen_count": sum(int(trace.get("partial_only_near_basin_seen", False)) for trace in traces),
        "handoff_available_seen_count": sum(int(trace.get("handoff_available_seen", False)) for trace in traces),
        "rook_blunder_count": sum(int(trace["rook_blunder"]) for trace in traces),
        "stalemate_count": sum(int(trace["stalemate"]) for trace in traces),
        "illegal_move_count": sum(int(trace["illegal"]) for trace in traces),
        "confinement_regression_count": sum(int(trace["confinement_regression"]) for trace in traces),
        "hard_decoy_false_handoff_count": sum(
            int(trace["family"] == "hard_decoy_edge_killbox" and trace["endpoint_validated_entry"])
            for trace in traces
        ),
        "traces": traces,
    }


def _move_is_lateral_from_trace(trace: Mapping[str, Any], ply: int) -> bool:
    if ply >= len(trace["white_moves"]):
        return False
    board = chess.Board(trace["positions"][ply * 2])
    return _is_lateral_rook_move(board, chess.Move.from_uci(trace["white_moves"][ply]))


def _safe_lateral_available(board: chess.Board) -> bool:
    for move in board.legal_moves:
        if not _is_lateral_rook_move(board, move):
            continue
        after = board.copy(stack=False)
        after.push(move)
        if _safe_board(after):
            return True
    return False


def _episode_success(endpoint_type: str) -> bool:
    return endpoint_type in {
        "validated_mate1_entry",
        "validated_mate2_entry",
        "validated_foundation_entry",
        "safer_opposed_or_killbox_geometry",
        "horizon_reached_safe",
    }


def _strip_traces(metrics: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if key != "traces"}


def _episode_summary_matches(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _strip_traces(left) == _strip_traces(right)


def _dataset_summary(datasets: Mapping[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {
        split: {
            "count": len(rows),
            "family_counts": {family: sum(int(row["family"] == family) for row in rows) for family in sorted({row["family"] for row in rows})},
        }
        for split, rows in datasets.items()
    }


def _reward_channel_rows(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for trace in traces:
        contrastive = trace.get("contrastive_episode", {})
        contrastive_reward = contrastive.get("trajectory_reward")
        rows.append({
            "episode_id": trace["episode_id"],
            "endpoint_type": trace["endpoint_type"],
            "trajectory_reward": trace["trajectory_reward"],
            "contrastive_endpoint_type": contrastive.get("endpoint_type"),
            "contrastive_trajectory_reward": contrastive_reward,
            "contrastive_reward_delta": (
                None
                if contrastive_reward is None
                else round(float(trace["trajectory_reward"]) - float(contrastive_reward), 6)
            ),
            "reward_channels": trace["reward_channels"],
            "credit_assignment_mode": trace.get("credit_assignment_mode", "selected_trajectory"),
            "credit_assignment_count": len(trace["credit_assignments"]),
            "learner_visible_labels": False,
        })
    return rows


def _reward_channel_summary(traces: list[dict[str, Any]]) -> dict[str, Any]:
    channel_sums: dict[str, float] = {}
    channel_nonzero_counts: dict[str, int] = {}
    endpoint_counts: dict[str, int] = {}
    delta_rewards = []
    for trace in traces:
        endpoint = str(trace["endpoint_type"])
        endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
        for key, value in trace["reward_channels"].items():
            channel_sums[key] = channel_sums.get(key, 0.0) + float(value)
            channel_nonzero_counts[key] = channel_nonzero_counts.get(key, 0) + int(abs(float(value)) > 1e-12)
        contrastive = trace.get("contrastive_episode", {})
        if contrastive.get("available"):
            delta_rewards.append(round(float(trace["trajectory_reward"]) - float(contrastive["trajectory_reward"]), 6))
    rewards = [float(trace["trajectory_reward"]) for trace in traces]
    return {
        "episode_count": len(traces),
        "positive_reward_count": sum(int(value > 0.0) for value in rewards),
        "negative_reward_count": sum(int(value < 0.0) for value in rewards),
        "zero_reward_count": sum(int(value == 0.0) for value in rewards),
        "positive_contrastive_delta_count": sum(int(value > 0.0) for value in delta_rewards),
        "negative_contrastive_delta_count": sum(int(value < 0.0) for value in delta_rewards),
        "zero_contrastive_delta_count": sum(int(value == 0.0) for value in delta_rewards),
        "contrastive_pair_count": len(delta_rewards),
        "endpoint_counts": endpoint_counts,
        "channel_sums": {key: round(value, 6) for key, value in sorted(channel_sums.items())},
        "channel_nonzero_counts": dict(sorted(channel_nonzero_counts.items())),
        "nondegenerate_reward_distribution": bool(
            len({round(value, 6) for value in rewards}) > 1
            or (any(value > 0.0 for value in delta_rewards) and any(value < 0.0 for value in delta_rewards))
        ),
    }


def _decision(
    *,
    config: TG48a2SameSideEpisodeTrainingConfig,
    parent_hash: str,
    parent_before: Mapping[str, Any],
    parent_after: Mapping[str, Any],
    parent_delta: int,
    hard_decoy_gate: Mapping[str, Any],
    learner: TerminalAffordanceLearner,
    m4_audit: Mapping[str, Any],
    parent_legacy_eval: Mapping[str, Any],
    parent_eval: Mapping[str, Any],
    child_weights_zeroed_eval: Mapping[str, Any],
    m3_eval: Mapping[str, Any],
    m4_eval: Mapping[str, Any],
    m3_plus_m4_eval: Mapping[str, Any],
    ablated_affordances_eval: Mapping[str, Any],
    no_foundation_eval: Mapping[str, Any],
    regression_eval: Mapping[str, Any],
    decoy_eval: Mapping[str, Any],
    total_seconds: float,
) -> dict[str, Any]:
    _ = (no_foundation_eval, regression_eval)
    infrastructure_pass = bool(parent_delta == 0 and parent_before["pass"] and parent_after["pass"])
    safety_clean = bool(
        m4_eval["rook_blunder_count"] == 0
        and m4_eval["stalemate_count"] == 0
        and m4_eval["illegal_move_count"] == 0
        and m4_eval["confinement_regression_count"] == 0
    )
    any_affordance = bool(
        m4_audit["promoted_lateral_escape_affordance_count"]
        or m4_audit["promoted_geometry_transition_affordance_count"]
        or m4_audit["promoted_foundation_handoff_affordance_count"]
    )
    m3_delta_vs_parent = m3_eval["episode_success_rate"] - parent_eval["episode_success_rate"]
    m4_delta_vs_parent = m4_eval["episode_success_rate"] - parent_eval["episode_success_rate"]
    m3_plus_m4_delta_vs_parent = m3_plus_m4_eval["episode_success_rate"] - parent_eval["episode_success_rate"]
    ablated_affordances_delta_vs_parent = ablated_affordances_eval["episode_success_rate"] - parent_eval["episode_success_rate"]
    zeroed_child_delta_vs_parent = child_weights_zeroed_eval["episode_success_rate"] - parent_eval["episode_success_rate"]
    zeroed_child_matches_parent = _episode_summary_matches(parent_eval, child_weights_zeroed_eval)
    trained_arm_beats_parent = bool(
        m3_delta_vs_parent > 0.0
        or m4_delta_vs_parent > 0.0
        or m3_plus_m4_delta_vs_parent > 0.0
    )
    m4_subskill_improves = m4_eval["same_side_subskill_success_rate"] > parent_eval["same_side_subskill_success_rate"]
    false_basin_decreases = m4_eval["graph_positive_false_basin_count"] < parent_eval["graph_positive_false_basin_count"]
    if not infrastructure_pass:
        interpretation = "episode_training_infrastructure_failed"
        next_action = "repair_episode_training_infrastructure"
    elif not any_affordance:
        interpretation = "trajectory_affordance_not_forming"
        next_action = "inspect_episode_reward_channels_and_terminal_keys"
    elif m4_subskill_improves and m4_eval["validated_entry_rate"] <= parent_eval["validated_entry_rate"]:
        interpretation = "same_side_subskill_learned_foundation_handoff_still_sparse"
        next_action = "inspect_repaired_parent_vs_trained_arm_main_json_metrics"
    elif m4_subskill_improves and safety_clean and false_basin_decreases:
        interpretation = "same_side_episode_behavioral_candidate"
        next_action = "record_phase0_metric_result_before_any_next_phase"
    else:
        interpretation = "same_side_episode_reward_or_generator_blocker"
        next_action = "inspect_main_json_reward_channel_audit_and_terminal_credit"
    return {
        "checkpoint_pass": infrastructure_pass,
        "checkpoint_interpretation": interpretation,
        "selected_next_action": next_action,
        "run_scale_label": config.run_scale_label,
        "parent_foundation_hash": parent_hash,
        "episode_train_count": config.train_count,
        "episode_heldout_count": parent_eval["episode_count"],
        "primary_metric": "heldout_episode_success_rate_vs_repaired_parent",
        "parent_legacy_availability_classifier_episode_success_rate": parent_legacy_eval["episode_success_rate"],
        "parent_episode_success_rate": parent_eval["episode_success_rate"],
        "parent_reclassification_episode_success_delta": round(
            parent_eval["episode_success_rate"] - parent_legacy_eval["episode_success_rate"],
            6,
        ),
        "child_weights_zeroed_episode_success_rate": child_weights_zeroed_eval["episode_success_rate"],
        "child_weights_zeroed_delta_vs_repaired_parent_episode_success_rate": round(zeroed_child_delta_vs_parent, 6),
        "child_weights_zeroed_matches_repaired_parent": zeroed_child_matches_parent,
        "M3_episode_success_rate": m3_eval["episode_success_rate"],
        "M4_episode_success_rate": m4_eval["episode_success_rate"],
        "true_M3_plus_M4_episode_success_rate": m3_plus_m4_eval["episode_success_rate"],
        "M3_plus_M4_ablated_affordances_episode_success_rate": ablated_affordances_eval["episode_success_rate"],
        "M3_delta_vs_repaired_parent_episode_success_rate": round(m3_delta_vs_parent, 6),
        "M4_delta_vs_repaired_parent_episode_success_rate": round(m4_delta_vs_parent, 6),
        "M3_plus_M4_delta_vs_repaired_parent_episode_success_rate": round(m3_plus_m4_delta_vs_parent, 6),
        "M3_plus_M4_ablated_affordances_delta_vs_repaired_parent_episode_success_rate": round(
            ablated_affordances_delta_vs_parent,
            6,
        ),
        "trained_arm_beats_repaired_parent": trained_arm_beats_parent,
        "primary_metric_acceptance_pass": trained_arm_beats_parent,
        "same_side_subskill_success_rate": m4_eval["same_side_subskill_success_rate"],
        "lateral_escape_success_rate": m4_eval["lateral_escape_success_rate"],
        "selected_lateral_rook_rate": m4_eval["selected_lateral_rook_rate"],
        "safe_lateral_rook_available_rate": m4_eval["safe_lateral_rook_available_rate"],
        "transition_to_opposed_or_killbox_rate": m4_eval["transition_to_opposed_or_killbox_rate"],
        "validated_entry_rate": m4_eval["validated_entry_rate"],
        "validated_mate1_entry_rate": m4_eval["validated_mate1_entry_rate"],
        "validated_mate2_entry_rate": m4_eval["validated_mate2_entry_rate"],
        "graph_positive_false_basin_count": m4_eval["graph_positive_false_basin_count"],
        "partial_only_near_basin_count": m4_eval["partial_only_near_basin_count"],
        "rook_blunder_count": m4_eval["rook_blunder_count"],
        "stalemate_count": m4_eval["stalemate_count"],
        "illegal_move_count": m4_eval["illegal_move_count"],
        "confinement_regression_count": m4_eval["confinement_regression_count"],
        "hard_decoy_false_handoff_count": decoy_eval["hard_decoy_false_handoff_count"],
        "promoted_lateral_escape_affordance_count": m4_audit["promoted_lateral_escape_affordance_count"],
        "promoted_geometry_transition_affordance_count": m4_audit["promoted_geometry_transition_affordance_count"],
        "promoted_foundation_handoff_affordance_count": m4_audit["promoted_foundation_handoff_affordance_count"],
        "promoted_veto_count": m4_audit["promoted_veto_count"],
        "M3_update_count": learner.m3_update_count,
        "hard_decoy_generator_mislabel_count": int(hard_decoy_gate.get("hard_decoy_generator_mislabel_count", 0)),
        "parent_foundation_frozen": True,
        "parent_foundation_m3_delta_during_stage": 0,
        "parent_foundation_m4_delta_during_stage": 0,
        "parent_foundation_weight_delta_during_stage": parent_delta,
        "primary_training_unit": "episode_trajectory",
        "move_local_reward_primary": False,
        **_purity_boundary(),
        "total_seconds": total_seconds,
    }


def _purity_boundary() -> dict[str, bool]:
    return {
        "trainer_side_playout_used_for_reward": True,
        "trainer_side_playout_used_for_runtime_selection": False,
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


def _validate_episode_trace_learner_visible(trace: Mapping[str, Any]) -> None:
    learner_visible = {
        "terminal_activations_by_white_ply": trace["terminal_activations_by_white_ply"],
        "selected_moves_by_white_ply": trace["selected_moves_by_white_ply"],
    }
    validate_learner_record(learner_visible)
    encoded = json.dumps(learner_visible, sort_keys=True).lower()
    for term in FORBIDDEN_MICROSTAGE_TERMS:
        if term in encoded:
            raise ValueError(f"forbidden TG48a2 episode learner term leaked: {term}")


def _write_board_samples(path: str | Path, traces: list[dict[str, Any]]) -> None:
    samples = [trace for trace in traces if not trace["episode_success"] or trace["rook_blunder"] or trace["graph_positive_false_basin"]][:20]
    lines = [
        "# TG48a2 Same-Side Episode Board Samples",
        "",
        "Human-readable samples. Family/split/endpoint names are trainer-side diagnostics only.",
        "",
    ]
    for trace in samples:
        lines.extend([
            f"## {trace['episode_id']}",
            "",
            f"- Start FEN: `{trace['start_fen']}`",
            f"- Endpoint: `{trace['endpoint_type']}`",
            f"- White moves: `{', '.join(trace['white_moves']) if trace['white_moves'] else 'none'}`",
            f"- Black replies: `{', '.join(trace['black_replies']) if trace['black_replies'] else 'none'}`",
            f"- Reward: `{trace['trajectory_reward']}`",
            "",
            "```text",
            str(chess.Board(trace["start_fen"])),
            "```",
            "",
        ])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _write_markdown(path: str | Path, result: TG48a2SameSideEpisodeTrainingResult) -> None:
    d = result.decision
    lines = [
        f"# {result.config.checkpoint_name}",
        "",
        f"- Checkpoint pass: {d['checkpoint_pass']}",
        f"- Interpretation: {d['checkpoint_interpretation']}",
        f"- Selected next action: {d['selected_next_action']}",
        f"- Primary metric: {d['primary_metric']}",
        f"- Parent legacy/repaired/reclassification delta: {d['parent_legacy_availability_classifier_episode_success_rate']:.3f} / {d['parent_episode_success_rate']:.3f} / {d['parent_reclassification_episode_success_delta']:.3f}",
        f"- Child weights zeroed rate/delta/matches parent: {d['child_weights_zeroed_episode_success_rate']:.3f} / {d['child_weights_zeroed_delta_vs_repaired_parent_episode_success_rate']:.3f} / {d['child_weights_zeroed_matches_repaired_parent']}",
        f"- Episode success parent/M3/M4/M3+M4: {d['parent_episode_success_rate']:.3f} / {d['M3_episode_success_rate']:.3f} / {d['M4_episode_success_rate']:.3f} / {d['true_M3_plus_M4_episode_success_rate']:.3f}",
        f"- Ablated affordances rate/delta vs repaired parent: {d['M3_plus_M4_ablated_affordances_episode_success_rate']:.3f} / {d['M3_plus_M4_ablated_affordances_delta_vs_repaired_parent_episode_success_rate']:.3f}",
        f"- Episode success deltas vs repaired parent M3/M4/M3+M4: {d['M3_delta_vs_repaired_parent_episode_success_rate']:.3f} / {d['M4_delta_vs_repaired_parent_episode_success_rate']:.3f} / {d['M3_plus_M4_delta_vs_repaired_parent_episode_success_rate']:.3f}",
        f"- Same-side subskill success: {d['same_side_subskill_success_rate']:.3f}",
        f"- Lateral escape success: {d['lateral_escape_success_rate']:.3f}",
        f"- Validated entry rate: {d['validated_entry_rate']:.3f}",
        f"- Promoted lateral/geometry/foundation/veto: {d['promoted_lateral_escape_affordance_count']} / {d['promoted_geometry_transition_affordance_count']} / {d['promoted_foundation_handoff_affordance_count']} / {d['promoted_veto_count']}",
        f"- Graph-positive false basin count: {d['graph_positive_false_basin_count']}",
        f"- Safety rook/stalemate/illegal/confinement: {d['rook_blunder_count']} / {d['stalemate_count']} / {d['illegal_move_count']} / {d['confinement_regression_count']}",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
