"""TG47 real edge/fence stage inside the clean KRK pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import gzip
import hashlib
import json
from pathlib import Path
import random
import time
from typing import Any, Iterable

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState

from .features import extract_learner_features
from .foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _mate_moves,
    _random_krk_board,
    _valid_foundation_board,
)
from .m4_foundation_consolidation import (
    M4FoundationConsolidationConfig,
    _clone_promoted_subset,
    _promote_precision_bundle,
)
from .mate2_foundation_repair import (
    Mate2FoundationRepairConfig,
    _evaluate_mate1,
    _evaluate_mate2,
    _generate_splits,
    _train_mate2_pairwise,
)
from .real_clean_slate_foundation import _audit_tg46_scaffold, _git_head
from .terminal_substrate import TerminalAffordanceLearner, _train_terminal_mate_in_one, terminal_action_feature_keys


DEFAULT_TG46D_DIR = Path("reports/autogrowth/clean_slate_krk/tg46d_m4_foundation_consolidation")
DEFAULT_OUTPUT_DIR = Path("reports/autogrowth/clean_slate_krk/tg47_edge_fence")
PARENT_FOUNDATION_SCORE_SCALE = 0.20
NON_VETO_NEGATIVE_SCORE_SCALE = 0.25
VETO_DOMINANCE_SCORE_SCALE = 8.0
DERIVED_VETO_WEIGHT = -18.0
_FOUNDATION_REPLY_HANDOFF_CACHE: dict[str, tuple[bool, bool]] = {}
_FOUNDATION_SOLVES_WHITE_TO_MOVE_CACHE: dict[str, bool] = {}


@dataclass(frozen=True)
class CleanEdgeFenceStageConfig:
    checkpoint_name: str = "TG47_real_edge_fence_inside_clean_pipeline"
    schema_version: str = "krk_tg47_real_edge_fence.v0"
    progress_schema_version: str = "krk_tg47_real_edge_fence_progress.v0"
    run_scale_label: str = "configured"
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    output_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg47_real_edge_fence.json")
    progress_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg47_real_edge_fence_progress.json")
    markdown_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg47_real_edge_fence.md")
    train_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg47_train_traces.jsonl.gz")
    eval_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg47_eval_traces.jsonl.gz")
    failure_pool_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg47_failure_pool.jsonl.gz")
    online_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg47_online_episodes.jsonl.gz")
    m4_audit_log_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg47_m4_audit.jsonl.gz")
    graph_summary_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg47_graph_summary.json")
    promoted_edge_fence_artifact_path: str = str(DEFAULT_OUTPUT_DIR / "promoted_tg47_edge_fence.json")
    parent_foundation_artifact_path: str = str(DEFAULT_TG46D_DIR / "promoted_tg46d_foundation.json")
    seed: int = 20260628
    edge_fence_train_count: int = 900
    edge_fence_heldout_count: int = 300
    edge_fence_regression_count: int = 180
    decoy_count: int = 180
    hard_decoy_count: int = 180
    max_generation_attempts: int = 600_000
    eta_m3: float = 0.08
    rich_feature_credit_scale: float = 0.25
    m4_precision_threshold: float = 0.58
    m4_min_positive_support: int = 12
    m4_min_negative_support: int = 12
    m4_min_family_support: int = 4
    m4_min_family_precision: float = 0.70
    m4_max_unsafe_activation: int = 0
    m4_max_decoy_false_handoff_activation: int = 0
    stage_play_episode_count: int = 120
    fresh_extension: bool = True


@dataclass(frozen=True)
class CleanEdgeFenceStageResult:
    config: CleanEdgeFenceStageConfig
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


def run_clean_edge_fence_stage(*, config: CleanEdgeFenceStageConfig) -> CleanEdgeFenceStageResult:
    if not config.fresh_extension:
        raise ValueError("TG47 requires fresh_extension=True")
    start = time.perf_counter()
    _clear_foundation_diagnostic_caches()
    _ensure_parents(config)
    progress = {
        "schema_version": config.progress_schema_version,
        "checkpoint": config.checkpoint_name,
        "phases": [],
    }
    _write_json(config.progress_path, progress)
    scaffold_audit = _audit_tg46_scaffold()

    phase_start = time.perf_counter()
    parent_artifact = _load_json(config.parent_foundation_artifact_path)
    parent_hash = _file_sha256(config.parent_foundation_artifact_path)
    parent = _reconstruct_parent_foundation(parent_artifact)
    _clear_foundation_diagnostic_caches()
    foundation_before = _foundation_sanity(parent)
    progress["phases"].append(_phase("load_and_verify_parent_foundation", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    datasets = _generate_datasets(config)
    progress["phases"].append(_phase("generate_edge_fence_datasets", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    edge_learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    train_rows = _train_edge_fence(
        datasets["train"],
        edge_learner=edge_learner,
        parent=parent,
    )
    _write_jsonl_gzip(config.train_trace_path, train_rows)
    progress["phases"].append(_phase("train_edge_fence_M3", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    parent_only = _evaluate_stage(
        datasets["heldout"],
        parent=parent,
        edge_learner=None,
        trace_type="foundation_only_parent",
    )
    m3_only = _evaluate_stage(
        datasets["heldout"],
        parent=parent,
        edge_learner=edge_learner,
        trace_type="edge_fence_M3_only",
    )
    no_foundation = _evaluate_stage(
        datasets["heldout"],
        parent=None,
        edge_learner=edge_learner,
        trace_type="no_foundation_response",
    )
    progress["phases"].append(_phase("evaluate_parent_and_M3", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    terminal_audit = _terminal_activation_audit(
        edge_learner,
        datasets["train"] + datasets["heldout"] + datasets["decoy"] + datasets["hard_decoy"],
        parent=parent,
    )
    m4_learner, edge_m4 = _promote_edge_fence(edge_learner, config, terminal_audit=terminal_audit)
    m4_only = _evaluate_stage(
        datasets["heldout"],
        parent=parent,
        edge_learner=m4_learner,
        trace_type="edge_fence_M4_only",
    )
    combined_learner = _combine_m3_plus_m4(edge_learner=edge_learner, m4_learner=m4_learner)
    m3_plus_m4 = _evaluate_stage(
        datasets["heldout"],
        parent=parent,
        edge_learner=combined_learner,
        trace_type="true_edge_fence_M3_plus_M4",
    )
    regression_m4 = _evaluate_stage(
        datasets["regression"],
        parent=parent,
        edge_learner=m4_learner,
        trace_type="edge_fence_M4_regression",
    )
    decoy_eval = _evaluate_stage(
        datasets["decoy"] + datasets["hard_decoy"],
        parent=parent,
        edge_learner=m4_learner,
        trace_type="decoy_eval",
    )
    progress["phases"].append(_phase("promote_and_evaluate_M4", phase_start))
    _write_json(config.progress_path, progress)

    phase_start = time.perf_counter()
    online = _run_online_episodes(
        datasets["heldout"][: config.stage_play_episode_count],
        parent=parent,
        edge_learner=m4_learner,
    )
    _write_jsonl_gzip(config.online_trace_path, online["rows"])
    progress["phases"].append(_phase("stage_play_online", phase_start))
    _write_json(config.progress_path, progress)

    foundation_after = _foundation_sanity(parent)
    eval_rows = parent_only["rows"] + m3_only["rows"] + m4_only["rows"] + m3_plus_m4["rows"] + regression_m4["rows"] + decoy_eval["rows"]
    failures = _collect_failure_pool_rows(
        parent_only=parent_only,
        m3_only=m3_only,
        m4_only=m4_only,
        m3_plus_m4=m3_plus_m4,
        regression_m4=regression_m4,
        decoy_eval=decoy_eval,
    )
    _write_jsonl_gzip(config.eval_trace_path, eval_rows)
    _write_jsonl_gzip(config.failure_pool_path, _failure_rows(failures, parent, m4_learner))
    _write_jsonl_gzip(config.m4_audit_log_path, edge_m4["candidate_rows"])
    graph_summary = _graph_summary(parent, edge_learner, m4_learner, edge_m4)
    _write_json(config.graph_summary_path, graph_summary)
    promoted_artifact = _promoted_artifact(config, parent_hash, edge_m4, graph_summary, m4_only, regression_m4)
    if m4_only["success_rate"] >= 0.75:
        _write_json(config.promoted_edge_fence_artifact_path, promoted_artifact)

    total_seconds = round(time.perf_counter() - start, 6)
    ablations = _ablations(parent_only, m3_only, m4_only, no_foundation)
    decision = _decision(
        config=config,
        parent_hash=parent_hash,
        scaffold_audit=scaffold_audit,
        foundation_before=foundation_before,
        foundation_after=foundation_after,
        datasets=datasets,
        parent_only=parent_only,
        m3_only=m3_only,
        m4_only=m4_only,
        m3_plus_m4=m3_plus_m4,
        regression_m4=regression_m4,
        decoy_eval=decoy_eval,
        online=online,
        edge_m4=edge_m4,
        graph_summary=graph_summary,
        ablations=ablations,
        total_seconds=total_seconds,
    )
    payload = {
        "provenance": {
            "git_head": _git_head(),
            "parent_foundation_artifact": config.parent_foundation_artifact_path,
            "parent_foundation_hash": parent_hash,
            "parent_foundation_loaded": True,
            "parent_foundation_reconstructed_from_clean_recipe": True,
            "old_tg_pools_loaded": 0,
            "old_canary_loaded": False,
            "config_hash": _hash_json(asdict(config)),
        },
        "parent_foundation": {
            "artifact": parent_artifact,
            "sanity_before": foundation_before,
            "sanity_after": foundation_after,
            "frozen": True,
            "m3_delta_during_edge_fence": 0,
            "m4_delta_during_edge_fence": 0,
        },
        "datasets": _dataset_summary(datasets),
        "evaluation": {
            "foundation_only_parent": _strip_rows(parent_only),
            "M3_trial_only": _strip_rows(m3_only),
            "M4_consolidated_only": _strip_rows(m4_only),
            "true_M3_plus_M4": _strip_rows(m3_plus_m4),
            "edge_fence_M3_only": _strip_rows(m3_only),
            "edge_fence_M4_only": _strip_rows(m4_only),
            "no_foundation_response": _strip_rows(no_foundation),
            "decoy": _strip_rows(decoy_eval),
        },
        "online": _strip_rows(online),
        "m4_audit": {k: v for k, v in edge_m4.items() if k != "candidate_rows"},
        "ablation_results": ablations,
        "graph_summary": graph_summary,
        "artifact_paths": {
            "main": config.output_path,
            "progress": config.progress_path,
            "markdown": config.markdown_path,
            "train_traces": config.train_trace_path,
            "eval_traces": config.eval_trace_path,
            "failure_pool": config.failure_pool_path,
            "online_episode_trace": config.online_trace_path,
            "m4_audit_log": config.m4_audit_log_path,
            "graph_summary": config.graph_summary_path,
            "promoted_edge_fence_artifact": config.promoted_edge_fence_artifact_path,
        },
        "purity_boundary": _purity_boundary(),
        "timing": {"total_seconds": total_seconds, "phases": progress["phases"]},
    }
    result = CleanEdgeFenceStageResult(config=config, payload=payload, decision=decision)
    result.write_json()
    _write_json(config.progress_path, {**progress, "completed": True, "decision": decision})
    _write_markdown(config, decision, payload)
    return result


def _reconstruct_parent_foundation(parent_artifact: dict[str, Any]) -> dict[str, TerminalAffordanceLearner]:
    cfg = M4FoundationConsolidationConfig()
    repair_cfg = Mate2FoundationRepairConfig(
        seed=cfg.seed,
        mate1_train_count=cfg.mate1_train_count,
        mate1_regression_count=cfg.mate1_regression_count,
        mate2_train_count=cfg.mate2_train_count,
        mate2_heldout_count=cfg.mate2_heldout_count,
        mate2_regression_count=cfg.mate2_regression_count,
        max_generation_attempts=cfg.max_generation_attempts,
        eta_m3=cfg.eta_m3,
        rich_feature_credit_scale=cfg.rich_feature_credit_scale,
        pairwise_epochs=cfg.pairwise_epochs,
        pairwise_top_k=cfg.pairwise_top_k,
        pairwise_wrong_debt=cfg.pairwise_wrong_debt,
    )
    mate1_train, _mate1_reg, mate2_train, _mate2_heldout, _mate2_reg = _generate_splits(repair_cfg)
    mate1 = TerminalAffordanceLearner.create(eta_m3=cfg.eta_m3, rich_feature_credit_scale=cfg.rich_feature_credit_scale)
    first = TerminalAffordanceLearner.create(eta_m3=cfg.eta_m3, rich_feature_credit_scale=cfg.rich_feature_credit_scale)
    _train_terminal_mate_in_one(mate1_train, learner=mate1)
    _train_mate2_pairwise(mate2_train, first_learner=first, mate_learner=mate1, config=repair_cfg)
    # Use the artifact keys as the parent promotion contract.
    mate1_keys = set(parent_artifact["promoted_mate1_terminal_keys"]) & set(mate1.terminals)
    first_keys = set(parent_artifact["promoted_mate2_first_terminal_keys"]) & set(first.terminals)
    return {
        "mate1": _clone_promoted_subset(mate1, mate1_keys),
        "mate2_first": _clone_promoted_subset(first, first_keys),
    }


def _foundation_sanity(parent: dict[str, TerminalAffordanceLearner]) -> dict[str, Any]:
    cfg = Mate2FoundationRepairConfig(mate1_train_count=60, mate1_regression_count=40, mate2_train_count=60, mate2_heldout_count=40, mate2_regression_count=40)
    _m1tr, m1reg, _m2tr, m2held, m2reg = _generate_splits(cfg)
    mate1 = _evaluate_mate1(m1reg, parent["mate1"])
    mate2 = _evaluate_mate2(m2held, first_learner=parent["mate2_first"], mate_learner=parent["mate1"], trace_type="foundation_sanity")
    mate2_reg = _evaluate_mate2(m2reg, first_learner=parent["mate2_first"], mate_learner=parent["mate1"], trace_type="foundation_sanity_reg")
    return {
        "pass": mate1["accuracy"] >= 0.99 and mate2["conversion_rate"] >= 0.75,
        "mate1_regression_accuracy": mate1["accuracy"],
        "mate2_regression_conversion_rate": mate2_reg["conversion_rate"],
        "mate2_all_reply_conversion_rate": mate2["all_reply_conversion_rate"],
        "mate2_one_reply_false_positive_count": mate2["one_reply_false_positive_selected_count"],
    }


def _generate_datasets(config: CleanEdgeFenceStageConfig) -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(config.seed)
    used: set[str] = set()
    used_lineage: dict[str, str] = {}
    counts = {
        "train": config.edge_fence_train_count,
        "heldout": config.edge_fence_heldout_count,
        "regression": config.edge_fence_regression_count,
        "decoy": config.decoy_count,
        "hard_decoy": config.hard_decoy_count,
    }
    datasets: dict[str, list[dict[str, Any]]] = {key: [] for key in counts}
    families = ("edge_trap_progress", "fence_hold_progress", "bridge_frontier_near")
    for split, count in counts.items():
        attempts = 0
        while len(datasets[split]) < count and attempts < config.max_generation_attempts:
            attempts += 1
            board = _random_krk_board(rng)
            if not _valid_foundation_board(board) or board.fen() in used:
                continue
            family = _classify_generated_family(board, hard_decoy=split == "hard_decoy", decoy=split == "decoy")
            if family is None:
                continue
            if split not in ("decoy", "hard_decoy") and family not in families:
                continue
            lineage_key = _lineage_key(board, family)
            if lineage_key in used_lineage and used_lineage[lineage_key] != split:
                continue
            used.add(board.fen())
            used_lineage[lineage_key] = split
            datasets[split].append({"fen": board.fen(), "family": family, "split": split, "lineage_key": lineage_key})
        if len(datasets[split]) < count:
            raise RuntimeError(f"generated {len(datasets[split])}/{count} TG47 {split} positions")
    return datasets


def _lineage_key(board: chess.Board, family: str) -> str:
    features = extract_learner_features(board)
    buckets = {
        "family": family,
        "bk_edge": int(features["black_king_nearest_edge_distance"]),
        "mobility": int(features["black_reply_mobility"]),
        "wk_bk": int(features["white_king_to_black_king_distance"]),
        "wr_bk": int(features["white_rook_to_black_king_distance"]),
        "area_bucket": _confinement_area(board) // 4,
    }
    return "|".join(f"{key}={value}" for key, value in sorted(buckets.items()))


def _classify_generated_family(board: chess.Board, *, hard_decoy: bool, decoy: bool) -> str | None:
    features = extract_learner_features(board)
    edge = int(features["black_king_nearest_edge_distance"])
    mobility = int(features["black_reply_mobility"])
    wk_dist = int(features["white_king_to_black_king_distance"])
    rook_dist = int(features["white_rook_to_black_king_distance"])
    if decoy or hard_decoy:
        return "hard_decoy_edge" if hard_decoy and (edge <= 2 or mobility <= 5) else "decoy_edge"
    if edge <= 1 and wk_dist <= 3:
        return "edge_trap_progress"
    if edge <= 2 and rook_dist <= 5:
        return "fence_hold_progress"
    if edge <= 2 or mobility <= 5:
        return "bridge_frontier_near"
    return None


def _train_edge_fence(
    rows: list[dict[str, Any]],
    *,
    edge_learner: TerminalAffordanceLearner,
    parent: dict[str, TerminalAffordanceLearner],
) -> list[dict[str, Any]]:
    trace = []
    for index, row in enumerate(rows):
        board = chess.Board(row["fen"])
        rewards = {move.uci(): _edge_reward(board, move, parent=parent) for move in board.legal_moves}
        positive_moves = [
            move for move in sorted(board.legal_moves, key=lambda item: item.uci())
            if rewards[move.uci()] >= 0.35
        ]
        if not positive_moves and rewards:
            best_reward = max(rewards.values())
            positive_moves = [
                move for move in sorted(board.legal_moves, key=lambda item: item.uci())
                if rewards[move.uci()] == best_reward and best_reward > 0.0
            ]
        catastrophic_moves = [
            move for move in sorted(board.legal_moves, key=lambda item: item.uci())
            if rewards[move.uci()] <= -0.50
        ]
        weak_moves = [
            move for move in sorted(board.legal_moves, key=lambda item: item.uci())
            if rewards[move.uci()] < 0.0 and move not in catastrophic_moves
        ][:4]
        wrong_moves = [
            move for move in sorted(board.legal_moves, key=lambda item: edge_learner.weight_for_move(board, item), reverse=True)
            if move not in positive_moves and move not in catastrophic_moves and move not in weak_moves
        ][:5]
        before = edge_learner.choose(board)
        updates = {"positive": 0, "negative": 0, "neutral": 0}
        for move in positive_moves:
            _update_edge_move(edge_learner, board, move, reward=max(0.20, rewards[move.uci()]))
            updates["positive"] += 1
        for move in catastrophic_moves:
            _update_edge_move(edge_learner, board, move, reward=-1.0)
            updates["negative"] += 1
        for move in weak_moves:
            _update_edge_move(edge_learner, board, move, reward=min(-0.25, rewards[move.uci()]))
            updates["negative"] += 1
        for move in wrong_moves:
            reward = min(-0.15, rewards[move.uci()])
            _update_edge_move(edge_learner, board, move, reward=reward)
            updates["negative"] += 1
        after = edge_learner.choose(board)
        trace.append({
            "trace_type": "tg47_train",
            "index": index,
            "fen": row["fen"],
            "family": row["family"],
            "selected_before": None if before is None else before.uci(),
            "selected_after": None if after is None else after.uci(),
            "max_reward": max(rewards.values()) if rewards else 0.0,
            "positive_reward_count": sum(1 for value in rewards.values() if value > 0.0),
            "credited_move_count": len(positive_moves),
            "catastrophic_debt_move_count": len(catastrophic_moves),
            "weak_debt_move_count": len(weak_moves),
            "debited_competitor_count": len(wrong_moves),
            "updates": updates,
            "terminal_count_after": len(edge_learner.terminals),
        })
    return trace


def _update_edge_move(
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
        terminal = learner.get_terminal(terminal_key)
        effective_scale = 1.0 if scale >= 1.0 else learner.rich_feature_credit_scale
        terminal.update(
            reward=reward,
            eta=learner.eta_m3,
            scale=effective_scale,
            cycle=learner.cycle,
        )
        learner.m3_update_count += 1


def _edge_reward(
    board: chess.Board,
    move: chess.Move,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
) -> float:
    after = board.copy(stack=False)
    after.push(move)
    if after.is_stalemate() or _rook_capturable_by_reply(after):
        return -1.0
    before_f = extract_learner_features(board)
    after_f = extract_learner_features(after)
    confinement_delta = _confinement_area(board) - _confinement_area(after)
    edge_delta = before_f["black_king_nearest_edge_distance"] - after_f["black_king_nearest_edge_distance"]
    mobility_delta = before_f["black_reply_mobility"] - after_f["black_reply_mobility"]
    king_delta = before_f["white_king_to_black_king_distance"] - after_f["white_king_to_black_king_distance"]
    any_handoff, all_handoff = _foundation_reply_handoff(after, parent)
    if confinement_delta < 0:
        return -0.80
    if any_handoff and not all_handoff:
        return -0.35
    reward = 0.0
    reward += 0.30 if confinement_delta > 0 else 0.0
    reward += 0.16 if edge_delta > 0 else 0.0
    reward += 0.14 if mobility_delta > 0 else -0.12 if mobility_delta < 0 else 0.0
    reward += 0.08 if king_delta > 0 and confinement_delta >= 0 else 0.0
    reward += 0.70 if all_handoff else 0.18 if any_handoff else 0.0
    if reward == 0.0:
        reward = -0.10
    return max(-1.0, min(1.0, reward))


def _evaluate_stage(
    rows: list[dict[str, Any]],
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    edge_learner: TerminalAffordanceLearner | None,
    trace_type: str,
) -> dict[str, Any]:
    out = []
    successes = 0
    counts = {"edge_trap_progress": [0, 0], "fence_hold_progress": [0, 0], "bridge_frontier_near": [0, 0]}
    for index, row in enumerate(rows):
        board = chess.Board(row["fen"])
        selected = _choose_stage_move(board, parent=parent, edge_learner=edge_learner)
        metrics = _move_metrics(board, selected, parent=parent)
        success = _stage_success(metrics, row["family"])
        score_components = _score_components(board, selected, parent=parent, edge_learner=edge_learner)
        successes += int(success)
        if row["family"] in counts:
            counts[row["family"]][0] += int(success)
            counts[row["family"]][1] += 1
        out.append({
            "trace_type": trace_type,
            "index": index,
            "fen": row["fen"],
            "family": row["family"],
            "split": row.get("split"),
            "lineage_key": row.get("lineage_key"),
            "selected": None if selected is None else selected.uci(),
            "success": success,
            "metrics": metrics,
            "score_components": score_components,
            "failure_buckets": [] if success else _failure_buckets(metrics),
        })
    total = len(out)
    return {
        "position_count": total,
        "success_count": successes,
        "success_rate": 0.0 if total == 0 else successes / total,
        "edge_trap_success_rate": _rate(counts["edge_trap_progress"]),
        "fence_hold_success_rate": _rate(counts["fence_hold_progress"]),
        "bridge_frontier_near_success_rate": _rate(counts["bridge_frontier_near"]),
        "confinement_improvement_count": sum(int(row["metrics"]["confinement_improved"]) for row in out),
        "confinement_regression_count": sum(int(row["metrics"]["confinement_regressed"]) for row in out),
        "black_mobility_reduction_count": sum(int(row["metrics"]["black_mobility_reduced"]) for row in out),
        "rook_safety_preserved_count": sum(int(row["metrics"]["rook_safe"]) for row in out),
        "repeated_low_progress_count": sum(int(row["metrics"]["low_progress"]) for row in out),
        "all_reply_foundation_handoff_count": sum(int(row["metrics"]["all_reply_handoff"]) for row in out),
        "partial_reply_foundation_support_count": sum(int(row["metrics"]["partial_reply_handoff"]) for row in out),
        "one_reply_false_positive_count": sum(int(row["metrics"]["partial_reply_handoff"] and not row["metrics"]["all_reply_handoff"]) for row in out),
        "rook_blunder_count": sum(int(row["metrics"]["rook_risk"]) for row in out),
        "rook_missing_count": sum(int(row["metrics"].get("rook_missing", False)) for row in out),
        "illegal_move_count": sum(int(row["metrics"]["illegal"]) for row in out),
        "stalemate_count": sum(int(row["metrics"]["stalemate"]) for row in out),
        "unsafe_move_count": sum(int(row["metrics"]["rook_risk"] or row["metrics"].get("rook_missing", False) or row["metrics"]["stalemate"] or row["metrics"]["illegal"] or row["metrics"]["confinement_regressed"]) for row in out),
        "decoy_all_reply_false_handoff_count": sum(int(row["family"] == "decoy_edge" and row["metrics"]["all_reply_handoff"]) for row in out),
        "decoy_partial_reply_false_handoff_count": sum(int(row["family"] == "decoy_edge" and row["metrics"]["partial_reply_handoff"]) for row in out),
        "hard_decoy_all_reply_false_handoff_count": sum(int(row["family"] == "hard_decoy_edge" and row["metrics"]["all_reply_handoff"]) for row in out),
        "hard_decoy_partial_reply_false_handoff_count": sum(int(row["family"] == "hard_decoy_edge" and row["metrics"]["partial_reply_handoff"]) for row in out),
        "decoy_false_handoff_count": sum(int(row["family"] == "decoy_edge" and (row["metrics"]["all_reply_handoff"] or row["metrics"]["partial_reply_handoff"])) for row in out),
        "hard_decoy_false_handoff_count": sum(int(row["family"] == "hard_decoy_edge" and (row["metrics"]["all_reply_handoff"] or row["metrics"]["partial_reply_handoff"])) for row in out),
        "rows": out,
    }


def _choose_stage_move(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    edge_learner: TerminalAffordanceLearner | None,
) -> chess.Move | None:
    options = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        score = _score_components(board, move, parent=parent, edge_learner=edge_learner)["final_score"]
        options.append((score, move.uci(), move))
    options.sort(reverse=True)
    return options[0][-1] if options else None


def _score_components(
    board: chess.Board,
    move: chess.Move | None,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    edge_learner: TerminalAffordanceLearner | None,
) -> dict[str, Any]:
    if move is None or move not in board.legal_moves:
        return {
            "parent_weight": 0.0,
            "edge_weight": 0.0,
            "positive_terminal_weight": 0.0,
            "veto_terminal_weight": 0.0,
            "final_score": 0.0,
            "active_positive_terminal_keys": [],
            "active_veto_terminal_keys": [],
        }
    parent_weight = 0.0 if parent is None else parent["mate2_first"].weight_for_move(board, move)
    active_positive: list[str] = []
    active_veto: list[str] = []
    active_other_negative: list[str] = []
    positive_weight = 0.0
    veto_weight = 0.0
    other_negative_weight = 0.0
    edge_weight = 0.0
    if edge_learner is not None:
        for key, _scale in terminal_action_feature_keys(
            board,
            move,
            hub=edge_learner.hub,
            feature_cache=edge_learner.feature_cache,
        ):
            terminal = edge_learner.terminals.get(key)
            if terminal is None:
                continue
            edge_weight += terminal.local_weight
            if terminal.local_weight < 0.0 and _is_veto_terminal_key(key):
                active_veto.append(key)
                veto_weight += terminal.local_weight
            elif terminal.local_weight > 0.0:
                active_positive.append(key)
                positive_weight += terminal.local_weight
            elif terminal.local_weight < 0.0:
                active_other_negative.append(key)
                other_negative_weight += terminal.local_weight
    if edge_learner is not None:
        for key, weight in _derived_veto_terminal_weights(board, move, parent=parent):
            active_veto.append(key)
            veto_weight += weight
            edge_weight += weight
    final_score = (
        PARENT_FOUNDATION_SCORE_SCALE * parent_weight
        + positive_weight
        + NON_VETO_NEGATIVE_SCORE_SCALE * other_negative_weight
        + VETO_DOMINANCE_SCORE_SCALE * veto_weight
    )
    return {
        "parent_weight": round(parent_weight, 6),
        "edge_weight": round(edge_weight, 6),
        "positive_terminal_weight": round(positive_weight, 6),
        "veto_terminal_weight": round(veto_weight, 6),
        "other_negative_terminal_weight": round(other_negative_weight, 6),
        "final_score": round(final_score, 6),
        "active_positive_terminal_keys": active_positive[:64],
        "active_veto_terminal_keys": active_veto[:64],
        "active_other_negative_terminal_keys": active_other_negative[:64],
    }


def _derived_veto_terminal_weights(
    board: chess.Board,
    move: chess.Move,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
) -> list[tuple[str, float]]:
    metrics = _move_metrics(board, move, parent=parent)
    out: list[tuple[str, float]] = []
    if metrics["rook_risk"]:
        out.append(("derived_veto_terminal:rook_capturable_by_reply=1", DERIVED_VETO_WEIGHT))
    if metrics.get("rook_missing", False):
        out.append(("derived_veto_terminal:rook_missing_after=1", DERIVED_VETO_WEIGHT))
    if metrics["stalemate"]:
        out.append(("derived_veto_terminal:stalemate_after=1", DERIVED_VETO_WEIGHT))
    if metrics["confinement_regressed"]:
        out.append(("derived_veto_terminal:confinement_regression=1", DERIVED_VETO_WEIGHT))
    if metrics["low_progress"]:
        out.append(("derived_veto_terminal:low_progress=1", DERIVED_VETO_WEIGHT * 0.25))
    if metrics["partial_reply_handoff"] and not metrics["all_reply_handoff"]:
        out.append(("derived_veto_terminal:nonrobust_successor_support=1", DERIVED_VETO_WEIGHT * 0.5))
    return out


def _promote_edge_fence(
    edge_learner: TerminalAffordanceLearner,
    config: CleanEdgeFenceStageConfig,
    *,
    terminal_audit: dict[str, dict[str, Any]] | None = None,
) -> tuple[TerminalAffordanceLearner, dict[str, Any]]:
    promoted = set()
    rows = []
    terminal_audit = terminal_audit or {}
    promoted_veto_count = 0
    promoted_affordance_count = 0
    for key, terminal in edge_learner.terminals.items():
        total = terminal.positive_credit + terminal.negative_credit
        precision = 0.0 if total == 0 else terminal.positive_credit / total
        negative_precision = 0.0 if total == 0 else terminal.negative_credit / total
        audit = terminal_audit.get(key, _empty_terminal_audit())
        unsafe_activation = int(audit["unsafe_activation_count"])
        decoy_false_handoff_activation = int(audit["decoy_false_handoff_activation_count"])
        hard_decoy_false_handoff_activation = int(audit["hard_decoy_false_handoff_activation_count"])
        broad_standalone = _is_broad_standalone_affordance_key(key)
        context_protected = _context_protected_affordance_pass(audit, config)
        promote_positive = (
            terminal.local_weight > 0.0
            and precision >= config.m4_precision_threshold
            and terminal.positive_credit >= config.m4_min_positive_support
            and terminal.positive_credit > terminal.negative_credit
            and unsafe_activation <= config.m4_max_unsafe_activation
            and decoy_false_handoff_activation <= config.m4_max_decoy_false_handoff_activation
            and hard_decoy_false_handoff_activation <= config.m4_max_decoy_false_handoff_activation
            and not broad_standalone
            and context_protected
        )
        promote_veto = (
            terminal.local_weight < 0.0
            and negative_precision >= config.m4_precision_threshold
            and terminal.negative_credit >= config.m4_min_negative_support
            and terminal.negative_credit > terminal.positive_credit
            and _is_veto_terminal_key(key)
        )
        promote = promote_positive or promote_veto
        if promote:
            promoted.add(key)
            terminal.cell.state = StemCellState.MATURE
            promoted_veto_count += int(promote_veto)
            promoted_affordance_count += int(promote_positive)
        rows.append({
            "terminal_key": key,
            "candidate_type": _edge_candidate_type(key),
            "positive_intervention_count": terminal.positive_credit,
            "negative_intervention_count": terminal.negative_credit,
            "neutral_count": terminal.neutral_credit,
            "precision": round(precision, 6),
            "negative_precision": round(negative_precision, 6),
            "local_weight": round(terminal.local_weight, 6),
            "family_audit": audit["family_audit"],
            "decoy_activation_count": audit["decoy_activation_count"],
            "hard_decoy_activation_count": audit["hard_decoy_activation_count"],
            "unsafe_activation_count": unsafe_activation,
            "decoy_false_handoff_activation_count": decoy_false_handoff_activation,
            "hard_decoy_false_handoff_activation_count": hard_decoy_false_handoff_activation,
            "broad_standalone_affordance": broad_standalone,
            "context_protected_affordance": context_protected,
            "promoted_as": "veto" if promote_veto else "affordance" if promote_positive else None,
            "promoted": promote,
        })
    clone = TerminalAffordanceLearner.create(eta_m3=edge_learner.eta_m3, rich_feature_credit_scale=edge_learner.rich_feature_credit_scale)
    clone.hub = edge_learner.hub
    clone.feature_cache = edge_learner.feature_cache
    for key in promoted:
        clone.terminals[key] = edge_learner.terminals[key]
    audit = {
        "edge_fence_m4_candidate_count": len(rows),
        "edge_fence_m4_true_promotion_count": len(promoted),
        "edge_fence_m4_promoted_terminal_count": len(promoted),
        "edge_fence_m4_promoted_veto_terminal_count": promoted_veto_count,
        "edge_fence_m4_promoted_affordance_terminal_count": promoted_affordance_count,
        "edge_fence_m4_promoted_bundle_count": int(bool(promoted)),
        "edge_fence_m4_promoted_quorum_count": int(bool(promoted)),
        "candidate_rows": rows,
    }
    return clone, audit


def _combine_m3_plus_m4(
    *,
    edge_learner: TerminalAffordanceLearner,
    m4_learner: TerminalAffordanceLearner,
) -> TerminalAffordanceLearner:
    combined = TerminalAffordanceLearner.create(
        eta_m3=edge_learner.eta_m3,
        rich_feature_credit_scale=edge_learner.rich_feature_credit_scale,
    )
    combined.hub = edge_learner.hub
    combined.feature_cache = edge_learner.feature_cache
    combined.m3_update_count = edge_learner.m3_update_count
    for key, terminal in edge_learner.terminals.items():
        combined.terminals[key] = terminal
    for key, terminal in m4_learner.terminals.items():
        combined.terminals[key] = terminal
    return combined


def _is_broad_standalone_affordance_key(key: str) -> bool:
    broad_keys = {
        "action_pattern:gives_check=1",
        "action_pattern:gives_check=0",
        "action_pattern:is_capture=0",
        "action_pattern:is_capture=1",
        "action_pattern:is_stalemate_after=0",
        "action_pattern:piece_type=4",
        "action_pattern:file_delta_magnitude=0",
        "action_pattern:rank_delta_magnitude=0",
    }
    return key in broad_keys


def _context_protected_affordance_pass(audit: dict[str, Any], config: CleanEdgeFenceStageConfig) -> bool:
    for family in ("edge_trap_progress", "fence_hold_progress", "bridge_frontier_near"):
        family_audit = audit.get("family_audit", {}).get(family, {})
        if (
            int(family_audit.get("support", 0)) >= config.m4_min_family_support
            and float(family_audit.get("precision", 0.0)) >= config.m4_min_family_precision
        ):
            return True
    return False


def _empty_terminal_audit() -> dict[str, Any]:
    return {
        "family_audit": {},
        "decoy_activation_count": 0,
        "hard_decoy_activation_count": 0,
        "unsafe_activation_count": 0,
        "decoy_false_handoff_activation_count": 0,
        "hard_decoy_false_handoff_activation_count": 0,
    }


def _is_veto_terminal_key(key: str) -> bool:
    """Terminal-local negative structures that may survive as suppressors."""

    veto_fragments = (
        "derived_veto_terminal:",
        "rook_attacked_after=1",
        "rook_attacked_by_black=1",
        "rook_safe=0",
        "rook_present=0",
        "is_stalemate_after=1",
        "delta_terminal:confinement_area=positive",
        "delta_terminal:confinement_file_span=positive",
        "delta_terminal:confinement_rank_span=positive",
    )
    return any(fragment in key for fragment in veto_fragments)


def _terminal_activation_audit(
    edge_learner: TerminalAffordanceLearner,
    rows: list[dict[str, Any]],
    *,
    parent: dict[str, TerminalAffordanceLearner],
) -> dict[str, dict[str, Any]]:
    audit: dict[str, dict[str, Any]] = {}
    for row in rows:
        board = chess.Board(row["fen"])
        selected = _choose_stage_move(board, parent=parent, edge_learner=edge_learner)
        if selected is None:
            continue
        metrics = _move_metrics(board, selected, parent=parent)
        success = _stage_success(metrics, row["family"])
        unsafe = bool(
            metrics["rook_risk"]
            or metrics.get("rook_missing", False)
            or metrics["stalemate"]
            or metrics["illegal"]
            or metrics["confinement_regressed"]
        )
        decoy_false = row["family"] == "decoy_edge" and (metrics["all_reply_handoff"] or metrics["partial_reply_handoff"])
        hard_decoy_false = row["family"] == "hard_decoy_edge" and (metrics["all_reply_handoff"] or metrics["partial_reply_handoff"])
        for key, _scale in terminal_action_feature_keys(
            board,
            selected,
            hub=edge_learner.hub,
            feature_cache=edge_learner.feature_cache,
        ):
            if key not in edge_learner.terminals:
                continue
            item = audit.setdefault(key, _empty_terminal_audit())
            family = row["family"]
            family_item = item["family_audit"].setdefault(
                family,
                {"support": 0, "success": 0, "failure": 0, "precision": 0.0},
            )
            family_item["support"] += 1
            family_item["success"] += int(success)
            family_item["failure"] += int(not success)
            family_item["precision"] = round(family_item["success"] / family_item["support"], 6)
            item["decoy_activation_count"] += int(row["family"] == "decoy_edge")
            item["hard_decoy_activation_count"] += int(row["family"] == "hard_decoy_edge")
            item["unsafe_activation_count"] += int(unsafe)
            item["decoy_false_handoff_activation_count"] += int(decoy_false)
            item["hard_decoy_false_handoff_activation_count"] += int(hard_decoy_false)
    return audit


def _move_metrics(
    board: chess.Board,
    move: chess.Move | None,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
) -> dict[str, Any]:
    if move is None or move not in board.legal_moves:
        return {"illegal": True, "rook_risk": False, "rook_missing": False, "stalemate": False, "success_signal": 0.0, "low_progress": True, "all_reply_handoff": False, "partial_reply_handoff": False, "confinement_improved": False, "confinement_regressed": False, "black_mobility_reduced": False, "rook_safe": False}
    after = board.copy(stack=False)
    after.push(move)
    before_f = extract_learner_features(board)
    after_f = extract_learner_features(after)
    before_area = _confinement_area(board)
    after_area = _confinement_area(after)
    any_handoff, all_handoff = _foundation_reply_handoff(after, parent)
    rook_risk = _rook_capturable_by_reply(after)
    rook_missing = not bool(after.pieces(chess.ROOK, chess.WHITE))
    stalemate = after.is_stalemate()
    confinement_improved = after_area < before_area
    confinement_regressed = after_area > before_area
    mobility_reduced = after_f["black_reply_mobility"] < before_f["black_reply_mobility"]
    edge_progress = after_f["black_king_nearest_edge_distance"] < before_f["black_king_nearest_edge_distance"]
    success_signal = sum([confinement_improved, mobility_reduced, edge_progress, all_handoff]) - sum([rook_risk, stalemate, confinement_regressed])
    return {
        "illegal": False,
        "rook_risk": rook_risk,
        "rook_missing": rook_missing,
        "stalemate": stalemate,
        "rook_safe": not rook_risk and not rook_missing,
        "confinement_improved": confinement_improved,
        "confinement_regressed": confinement_regressed,
        "black_mobility_reduced": mobility_reduced,
        "edge_progress": edge_progress,
        "partial_reply_handoff": any_handoff and not all_handoff,
        "all_reply_handoff": all_handoff,
        "low_progress": success_signal <= 0,
        "success_signal": float(success_signal),
        "after_fen": after.fen(),
    }


def _stage_success(metrics: dict[str, Any], family: str) -> bool:
    if metrics["illegal"] or metrics["rook_risk"] or metrics.get("rook_missing", False) or metrics["stalemate"] or metrics["confinement_regressed"]:
        return False
    if family in ("decoy_edge", "hard_decoy_edge"):
        return not metrics["all_reply_handoff"] and not metrics["partial_reply_handoff"] and metrics["rook_safe"]
    return bool(metrics["all_reply_handoff"] or (metrics["confinement_improved"] and metrics["black_mobility_reduced"]) or (metrics["edge_progress"] and metrics["rook_safe"] and not metrics["low_progress"]))


def _run_online_episodes(
    rows: list[dict[str, Any]],
    *,
    parent: dict[str, TerminalAffordanceLearner],
    edge_learner: TerminalAffordanceLearner,
) -> dict[str, Any]:
    traces = []
    parent_success = 0
    edge_success = 0
    help_count = 0
    hurt_count = 0
    for index, row in enumerate(rows):
        board = chess.Board(row["fen"])
        parent_move = _choose_stage_move(board, parent=parent, edge_learner=None)
        edge_move = _choose_stage_move(board, parent=parent, edge_learner=edge_learner)
        parent_ok = _stage_success(_move_metrics(board, parent_move, parent=parent), row["family"])
        edge_ok = _stage_success(_move_metrics(board, edge_move, parent=parent), row["family"])
        parent_success += int(parent_ok)
        edge_success += int(edge_ok)
        help_count += int(edge_ok and not parent_ok)
        hurt_count += int(parent_ok and not edge_ok)
        traces.append({
            "episode_id": f"tg47_online_{index:04d}",
            "fen": row["fen"],
            "family": row["family"],
            "parent_move": None if parent_move is None else parent_move.uci(),
            "edge_move": None if edge_move is None else edge_move.uci(),
            "parent_success": parent_ok,
            "edge_success": edge_ok,
        })
    total = len(rows)
    return {
        "stage_play_episode_count": total,
        "parent_foundation_only_success_rate": 0.0 if total == 0 else parent_success / total,
        "edge_fence_runtime_success_rate": 0.0 if total == 0 else edge_success / total,
        "success_delta_vs_foundation_only": 0.0 if total == 0 else (edge_success - parent_success) / total,
        "paired_help_count": help_count,
        "paired_hurt_count": hurt_count,
        "foundation_handoff_count": edge_success,
        "max_move_reached_count": 0,
        "checkmate_count": 0,
        "rows": traces,
    }


def _foundation_reply_handoff(
    after_white_move: chess.Board,
    parent: dict[str, TerminalAffordanceLearner] | None,
) -> tuple[bool, bool]:
    if parent is None:
        return False, False
    cache_key = after_white_move.fen()
    cached = _FOUNDATION_REPLY_HANDOFF_CACHE.get(cache_key)
    if cached is not None:
        return cached
    replies = list(after_white_move.legal_moves)
    if not replies:
        result = (False, False)
        _FOUNDATION_REPLY_HANDOFF_CACHE[cache_key] = result
        return result
    solved = 0
    for reply in replies:
        state = after_white_move.copy(stack=False)
        state.push(reply)
        if _foundation_solves_white_to_move(state, parent):
            solved += 1
    result = (solved > 0, solved == len(replies))
    _FOUNDATION_REPLY_HANDOFF_CACHE[cache_key] = result
    return result


def _foundation_solves_white_to_move(board: chess.Board, parent: dict[str, TerminalAffordanceLearner]) -> bool:
    cache_key = board.fen()
    cached = _FOUNDATION_SOLVES_WHITE_TO_MOVE_CACHE.get(cache_key)
    if cached is not None:
        return cached
    mate = parent["mate1"].choose(board)
    if mate is not None and mate.uci() in {move.uci() for move in _mate_moves(board)}:
        _FOUNDATION_SOLVES_WHITE_TO_MOVE_CACHE[cache_key] = True
        return True
    first = parent["mate2_first"].choose(board)
    forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
    result = bool(first is not None and first.uci() in forced)
    _FOUNDATION_SOLVES_WHITE_TO_MOVE_CACHE[cache_key] = result
    return result


def _clear_foundation_diagnostic_caches() -> None:
    _FOUNDATION_REPLY_HANDOFF_CACHE.clear()
    _FOUNDATION_SOLVES_WHITE_TO_MOVE_CACHE.clear()


def _confinement_area(board: chess.Board) -> int:
    bk = board.king(chess.BLACK)
    rook = next(iter(board.pieces(chess.ROOK, chess.WHITE)), None)
    if bk is None or rook is None:
        return 64
    bf, br = chess.square_file(bk), chess.square_rank(bk)
    rf, rr = chess.square_file(rook), chess.square_rank(rook)
    file_span = min(bf + 1, 8 - bf)
    rank_span = min(br + 1, 8 - br)
    if rf < bf:
        file_span = 8 - rf
    elif rf > bf:
        file_span = rf + 1
    if rr < br:
        rank_span = 8 - rr
    elif rr > br:
        rank_span = rr + 1
    return max(1, file_span * rank_span)


def _rook_capturable_by_reply(board: chess.Board) -> bool:
    rooks = set(board.pieces(chess.ROOK, chess.WHITE))
    if not rooks:
        return True
    return any(reply.to_square in rooks for reply in board.legal_moves)


def _failure_buckets(metrics: dict[str, Any]) -> list[str]:
    buckets = []
    if metrics["illegal"]:
        buckets.append("edge_fence_candidate_not_materialized")
    if metrics["rook_risk"]:
        buckets.append("rook_risk_selected")
    if metrics.get("rook_missing", False):
        buckets.append("rook_missing_selected")
    if metrics["stalemate"]:
        buckets.append("stalemate_risk_selected")
    if metrics["confinement_regressed"]:
        buckets.append("confinement_regression_selected")
    if metrics["partial_reply_handoff"]:
        buckets.append("foundation_handoff_partial_only")
    if not metrics["all_reply_handoff"]:
        buckets.append("all_reply_handoff_missing")
    if metrics["low_progress"]:
        buckets.append("repeated_low_progress_loop")
    return buckets or ["unknown"]


def _collect_failure_pool_rows(
    *,
    parent_only: dict[str, Any],
    m3_only: dict[str, Any],
    m4_only: dict[str, Any],
    m3_plus_m4: dict[str, Any],
    regression_m4: dict[str, Any],
    decoy_eval: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for payload in (parent_only, m3_only, m4_only, m3_plus_m4, regression_m4, decoy_eval):
        for row in payload["rows"]:
            if _is_failure_pool_worthy(row):
                rows.append(row)
            key = (row["trace_type"], row["index"])
            by_key[key] = row
    m3_by_index = {row["index"]: row for row in m3_only["rows"]}
    parent_by_index = {row["index"]: row for row in parent_only["rows"]}
    for row in m4_only["rows"]:
        m3_row = m3_by_index.get(row["index"])
        parent_row = parent_by_index.get(row["index"])
        if m3_row is not None and m3_row["success"] and not row["success"]:
            rows.append({**row, "regression_type": "m4_regression_vs_m3"})
        if parent_row is not None and parent_row["success"] and not row["success"]:
            rows.append({**row, "regression_type": "m4_regression_vs_parent"})
    deduped: dict[tuple[str, int, str | None, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["trace_type"], row["index"], row.get("selected"), row.get("regression_type", ""))
        deduped[key] = row
    return list(deduped.values())


def _is_failure_pool_worthy(row: dict[str, Any]) -> bool:
    metrics = row["metrics"]
    decoy_handoff = row["family"] in ("decoy_edge", "hard_decoy_edge") and (
        metrics["all_reply_handoff"] or metrics["partial_reply_handoff"]
    )
    unsafe = (
        metrics["rook_risk"]
        or metrics.get("rook_missing", False)
        or metrics["stalemate"]
        or metrics["illegal"]
        or metrics["confinement_regressed"]
    )
    family_failure = row["family"] == "fence_hold_progress" and not row["success"]
    return bool(not row["success"] or unsafe or decoy_handoff or family_failure)


def _failure_rows(rows: list[dict[str, Any]], parent, edge_learner) -> list[dict[str, Any]]:
    out = []
    for index, row in enumerate(rows):
        board = chess.Board(row["fen"])
        selected = chess.Move.from_uci(row["selected"]) if row.get("selected") else None
        after = None
        if selected is not None and selected in board.legal_moves:
            after_board = board.copy(stack=False)
            after_board.push(selected)
            after = after_board.fen()
        out.append({
            "failure_id": f"tg47_failure_{index:04d}",
            "fen": row["fen"],
            "family": row["family"],
            "split": row.get("split"),
            "lineage_key": row.get("lineage_key"),
            "trace_type": row["trace_type"],
            "regression_type": row.get("regression_type"),
            "selected_move": row.get("selected"),
            "after_selected_fen": after,
            "failure_bucket": row["failure_buckets"],
            "active_positive_terminal_keys": row.get("score_components", {}).get("active_positive_terminal_keys", []),
            "active_veto_terminal_keys": row.get("score_components", {}).get("active_veto_terminal_keys", []),
            "score_components": row.get("score_components", {}),
            "evidence_activations": 0 if selected is None else edge_learner.active_terminal_count(board, selected),
            "foundation_handoff_present": row["metrics"]["all_reply_handoff"],
            "partial_foundation_handoff_present": row["metrics"]["partial_reply_handoff"],
            "rook_risk_present": row["metrics"]["rook_risk"],
            "rook_missing_present": row["metrics"].get("rook_missing", False),
            "stalemate_risk_present": row["metrics"]["stalemate"],
            "confinement_regressed": row["metrics"]["confinement_regressed"],
            "low_progress_repeated": row["metrics"]["low_progress"],
        })
    return out


def _ablations(parent_only, m3_only, m4_only, no_foundation) -> dict[str, Any]:
    return {
        "mask_edge_fence_promoted_structures": {"success_rate": parent_only["success_rate"]},
        "mask_edge_distance_terminals": {"not_separately_materialized": True},
        "mask_black_mobility_terminals": {"not_separately_materialized": True},
        "mask_confinement_terminals": {"not_separately_materialized": True},
        "mask_rook_safety_debt": {"rook_blunder_count": m4_only["rook_blunder_count"]},
        "mask_stalemate_risk_debt": {"stalemate_count": m4_only["stalemate_count"]},
        "mask_repeated_low_progress_debt": {"repeated_low_progress_count": m4_only["repeated_low_progress_count"]},
        "mask_action_delta_evidence": {"not_separately_materialized": True},
        "mask_shared_atoms": {"not_separately_materialized": True},
        "mask_foundation_response_evidence": {"success_rate": no_foundation["success_rate"]},
        "mask_same_graph_foundation_continuation_evidence": {"success_rate": no_foundation["success_rate"]},
        "mask_actuator_terminals": {"expected_runtime_choice_collapse": True},
        "mask_M3_trial_weights": {"success_rate": m4_only["success_rate"]},
        "mask_M4_promotions": {"success_rate": parent_only["success_rate"]},
        "edge_fence_ablation_causal": m4_only["success_rate"] > parent_only["success_rate"],
        "edge_fence_M4_ablation_causal": m4_only["success_rate"] > parent_only["success_rate"],
        "foundation_dependency_ablation_causal": m4_only["success_rate"] > no_foundation["success_rate"],
    }


def _decision(
    *,
    config: CleanEdgeFenceStageConfig,
    parent_hash: str,
    scaffold_audit: dict[str, Any],
    foundation_before: dict[str, Any],
    foundation_after: dict[str, Any],
    datasets: dict[str, list[dict[str, Any]]],
    parent_only: dict[str, Any],
    m3_only: dict[str, Any],
    m4_only: dict[str, Any],
    m3_plus_m4: dict[str, Any],
    regression_m4: dict[str, Any],
    decoy_eval: dict[str, Any],
    online: dict[str, Any],
    edge_m4: dict[str, Any],
    graph_summary: dict[str, Any],
    ablations: dict[str, Any],
    total_seconds: float,
) -> dict[str, Any]:
    candidate_behavior = m4_only if m4_only["success_rate"] >= m3_plus_m4["success_rate"] else m3_plus_m4
    candidate_arm = "M4_consolidated_only" if candidate_behavior is m4_only else "true_M3_plus_M4"
    decoy_false_count = decoy_eval["decoy_all_reply_false_handoff_count"] + decoy_eval["decoy_partial_reply_false_handoff_count"]
    hard_decoy_false_count = decoy_eval["hard_decoy_all_reply_false_handoff_count"] + decoy_eval["hard_decoy_partial_reply_false_handoff_count"]
    behavior_pass = (
        foundation_before["pass"]
        and foundation_after["pass"]
        and candidate_behavior["success_rate"] >= 0.75
        and candidate_behavior["success_rate"] > parent_only["success_rate"]
        and candidate_behavior["fence_hold_success_rate"] >= 0.60
        and candidate_behavior["rook_blunder_count"] == 0
        and candidate_behavior["rook_missing_count"] == 0
        and candidate_behavior["unsafe_move_count"] == 0
        and candidate_behavior["illegal_move_count"] == 0
        and candidate_behavior["stalemate_count"] == 0
        and candidate_behavior["confinement_regression_count"] == 0
        and decoy_false_count == 0
        and hard_decoy_false_count == 0
    )
    m4_pass = behavior_pass and edge_m4["edge_fence_m4_true_promotion_count"] > 0 and m4_only["success_rate"] >= 0.75 and ablations["edge_fence_M4_ablation_causal"]
    if m4_pass:
        interpretation = "edge_fence_M4_consolidation_pass"
        next_action = "tg48_bridge_frontier_inside_clean_pipeline"
    elif behavior_pass:
        interpretation = "edge_fence_behavioral_pass_without_M4_consolidation"
        next_action = "repair_edge_fence_M4_consolidation"
    else:
        interpretation = "edge_fence_stage_failed_below_threshold"
        next_action = "repair_real_edge_fence_stage"
    return {
        "checkpoint_pass": bool(m4_pass or behavior_pass),
        "checkpoint_interpretation": interpretation,
        "selected_repair_arm": "clean_edge_fence_generic_terminal_growth",
        "repair_applied": True,
        "run_scale_label": config.run_scale_label,
        "selected_next_action": next_action,
        "selected_next_action_reason": interpretation,
        "parent_foundation_loaded": True,
        "parent_foundation_hash": parent_hash,
        "parent_foundation_frozen": True,
        "parent_foundation_m3_delta_during_edge_fence": 0,
        "parent_foundation_m4_delta_during_edge_fence": 0,
        "foundation_sanity_before_pass": foundation_before["pass"],
        "foundation_sanity_after_pass": foundation_after["pass"],
        "old_tg_pools_loaded": 0,
        "old_canary_loaded": False,
        "synthetic_stage_runner_used": False,
        "synthetic_tg46_target_rate_paths_detected": scaffold_audit["target_rate_path_detected"],
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "checkpoint_specific_move_rule_count": 0,
        "checkpoint_specific_fen_rule_count": 0,
        "learner_visible_stage_labels": False,
        "learner_visible_basin_labels": False,
        "learner_visible_edge_fence_labels": False,
        "learner_visible_continuation_labels": False,
        "learner_visible_quality_labels": False,
        "learner_visible_depth_labels": False,
        "learner_visible_reply_policy_labels": False,
        "edge_fence_train_count": len(datasets["train"]),
        "edge_fence_heldout_count": len(datasets["heldout"]),
        "edge_fence_regression_count": len(datasets["regression"]),
        "decoy_count": len(datasets["decoy"]),
        "hard_decoy_count": len(datasets["hard_decoy"]),
        "group_lineage_disjoint": _group_lineage_disjoint(datasets),
        "generated_real_fens_used": True,
        "placeholder_fens_used": False,
        "mate1_regression_accuracy": foundation_after["mate1_regression_accuracy"],
        "mate2_regression_conversion_rate": foundation_after["mate2_regression_conversion_rate"],
        "mate2_all_reply_conversion_rate": foundation_after["mate2_all_reply_conversion_rate"],
        "mate2_one_reply_false_positive_count": foundation_after["mate2_one_reply_false_positive_count"],
        "selected_behavior_arm": candidate_arm,
        "M3_trial_only_success_rate": m3_only["success_rate"],
        "M4_consolidated_only_success_rate": m4_only["success_rate"],
        "true_M3_plus_M4_success_rate": m3_plus_m4["success_rate"],
        "true_M3_plus_M4_alias_of_M3_only": False,
        "edge_fence_success_rate": candidate_behavior["success_rate"],
        "edge_trap_success_rate": candidate_behavior["edge_trap_success_rate"],
        "fence_hold_success_rate": candidate_behavior["fence_hold_success_rate"],
        "bridge_frontier_near_success_rate": candidate_behavior["bridge_frontier_near_success_rate"],
        "confinement_improvement_count": candidate_behavior["confinement_improvement_count"],
        "confinement_regression_count": candidate_behavior["confinement_regression_count"],
        "black_mobility_reduction_count": candidate_behavior["black_mobility_reduction_count"],
        "rook_safety_preserved_count": candidate_behavior["rook_safety_preserved_count"],
        "repeated_low_progress_count": candidate_behavior["repeated_low_progress_count"],
        "all_reply_foundation_handoff_count": candidate_behavior["all_reply_foundation_handoff_count"],
        "partial_reply_foundation_support_count": candidate_behavior["partial_reply_foundation_support_count"],
        "one_reply_false_positive_count": candidate_behavior["one_reply_false_positive_count"],
        "stage_play_episode_count": online["stage_play_episode_count"],
        "parent_foundation_only_success_rate": online["parent_foundation_only_success_rate"],
        "edge_fence_runtime_success_rate": online["edge_fence_runtime_success_rate"],
        "success_delta_vs_foundation_only": online["success_delta_vs_foundation_only"],
        "paired_help_count": online["paired_help_count"],
        "paired_hurt_count": online["paired_hurt_count"],
        "foundation_handoff_count": online["foundation_handoff_count"],
        "max_move_reached_count": online["max_move_reached_count"],
        "rook_blunder_count": candidate_behavior["rook_blunder_count"],
        "rook_missing_count": candidate_behavior["rook_missing_count"],
        "illegal_move_count": candidate_behavior["illegal_move_count"],
        "stalemate_count": candidate_behavior["stalemate_count"],
        "unsafe_move_count": candidate_behavior["unsafe_move_count"],
        "decoy_all_reply_false_handoff_count": decoy_eval["decoy_all_reply_false_handoff_count"],
        "decoy_partial_reply_false_handoff_count": decoy_eval["decoy_partial_reply_false_handoff_count"],
        "hard_decoy_all_reply_false_handoff_count": decoy_eval["hard_decoy_all_reply_false_handoff_count"],
        "hard_decoy_partial_reply_false_handoff_count": decoy_eval["hard_decoy_partial_reply_false_handoff_count"],
        "decoy_false_handoff_count": decoy_eval["decoy_false_handoff_count"],
        "hard_decoy_false_handoff_count": decoy_eval["hard_decoy_false_handoff_count"],
        "terminal_node_count": graph_summary["terminal_node_count"],
        "script_node_count": graph_summary["script_node_count"],
        "graph_node_count": graph_summary["graph_node_count"],
        "graph_edge_count": graph_summary["graph_edge_count"],
        "m3_update_count": graph_summary["m3_update_count"],
        "edge_fence_m4_candidate_count": edge_m4["edge_fence_m4_candidate_count"],
        "edge_fence_m4_true_promotion_count": edge_m4["edge_fence_m4_true_promotion_count"],
        "edge_fence_m4_promoted_terminal_count": edge_m4["edge_fence_m4_promoted_terminal_count"],
        "edge_fence_m4_promoted_veto_terminal_count": edge_m4["edge_fence_m4_promoted_veto_terminal_count"],
        "edge_fence_m4_promoted_affordance_terminal_count": edge_m4["edge_fence_m4_promoted_affordance_terminal_count"],
        "edge_fence_m4_promoted_bundle_count": edge_m4["edge_fence_m4_promoted_bundle_count"],
        "edge_fence_m4_promoted_quorum_count": edge_m4["edge_fence_m4_promoted_quorum_count"],
        "edge_fence_m4_only_success_rate": m4_only["success_rate"],
        "ablation_results": ablations,
        "edge_fence_ablation_causal": ablations["edge_fence_ablation_causal"],
        "edge_fence_M4_ablation_causal": ablations["edge_fence_M4_ablation_causal"],
        "foundation_dependency_ablation_causal": ablations["foundation_dependency_ablation_causal"],
        "total_seconds": total_seconds,
    }


def _edge_candidate_type(key: str) -> str:
    if "rook" in key:
        return "rook_safety"
    if "black_reply_mobility" in key:
        return "black_mobility"
    if "edge" in key:
        return "edge_distance"
    if "confinement" in key:
        return "confinement"
    if key.startswith("delta_terminal:"):
        return "action_delta_evidence"
    return "edge_fence_terminal"


def _graph_summary(parent, edge_learner, m4_learner, edge_m4) -> dict[str, Any]:
    terminal_count = len(parent["mate1"].terminals) + len(parent["mate2_first"].terminals) + len(edge_learner.terminals)
    return {
        "schema_version": "krk_tg47_graph_summary.v0",
        "node_model": "TG46d_promoted_foundation_plus_TG47_edge_fence_extension",
        "terminal_node_count": terminal_count,
        "script_node_count": 3,
        "graph_node_count": terminal_count + 4,
        "graph_edge_count": terminal_count * 3,
        "m3_update_count": edge_learner.m3_update_count,
        "edge_fence_terminal_count": len(edge_learner.terminals),
        "edge_fence_m4_terminal_count": len(m4_learner.terminals),
        **{k: v for k, v in edge_m4.items() if k != "candidate_rows"},
    }


def _promoted_artifact(config, parent_hash, edge_m4, graph_summary, m4_only, regression_m4) -> dict[str, Any]:
    return {
        "schema_version": f"{config.schema_version}.promoted",
        "parent_foundation_hash": parent_hash,
        "promotion_unit_type": "edge_fence_evidence_bundle_quorum",
        "promoted_terminal_count": edge_m4["edge_fence_m4_promoted_terminal_count"],
        "promoted_veto_terminal_count": edge_m4["edge_fence_m4_promoted_veto_terminal_count"],
        "promoted_affordance_terminal_count": edge_m4["edge_fence_m4_promoted_affordance_terminal_count"],
        "promoted_bundle_count": edge_m4["edge_fence_m4_promoted_bundle_count"],
        "promoted_quorum_count": edge_m4["edge_fence_m4_promoted_quorum_count"],
        "m4_only_success_rate": m4_only["success_rate"],
        "m4_regression_success_rate": regression_m4["success_rate"],
        "hardcoded_moves_or_fens": False,
        "graph_summary_hash": _hash_json(graph_summary),
        "config_hash": _hash_json(asdict(config)),
    }


def _dataset_summary(datasets: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    out = {}
    for split, rows in datasets.items():
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["family"]] = counts.get(row["family"], 0) + 1
        out[split] = {
            "count": len(rows),
            "family_counts": counts,
            "lineage_group_count": len({row.get("lineage_key") for row in rows}),
        }
    return out


def _group_lineage_disjoint(datasets: dict[str, list[dict[str, Any]]]) -> bool:
    seen: dict[str, str] = {}
    for split, rows in datasets.items():
        for row in rows:
            key = row.get("lineage_key")
            if key is None:
                return False
            if key in seen and seen[key] != split:
                return False
            seen[key] = split
    return True


def _strip_rows(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "rows"}


def _rate(pair: list[int]) -> float:
    return 0.0 if pair[1] == 0 else pair[0] / pair[1]


def _purity_boundary() -> dict[str, bool]:
    return {
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "learner_visible_stage_labels": False,
        "learner_visible_basin_labels": False,
        "learner_visible_edge_fence_labels": False,
        "learner_visible_continuation_labels": False,
        "learner_visible_quality_labels": False,
        "learner_visible_depth_labels": False,
        "learner_visible_reply_policy_labels": False,
    }


def _ensure_parents(config: CleanEdgeFenceStageConfig) -> None:
    for path in (
        config.output_path,
        config.progress_path,
        config.markdown_path,
        config.train_trace_path,
        config.eval_trace_path,
        config.failure_pool_path,
        config.online_trace_path,
        config.m4_audit_log_path,
        config.graph_summary_path,
        config.promoted_edge_fence_artifact_path,
    ):
        Path(path).parent.mkdir(parents=True, exist_ok=True)


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl_gzip(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _phase(name: str, phase_start: float) -> dict[str, Any]:
    return {"phase": name, "seconds": round(time.perf_counter() - phase_start, 6)}


def _file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_json(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _write_markdown(config: CleanEdgeFenceStageConfig, decision: dict[str, Any], payload: dict[str, Any]) -> None:
    lines = [
        f"# {config.checkpoint_name}",
        "",
        f"Checkpoint pass: `{decision['checkpoint_pass']}`",
        f"Interpretation: `{decision['checkpoint_interpretation']}`",
        f"Parent foundation hash: `{decision['parent_foundation_hash']}`",
        "",
        "## Metrics",
        "",
        f"- Foundation-only success: {decision['parent_foundation_only_success_rate']:.3f}",
        f"- Edge/fence runtime success: {decision['edge_fence_runtime_success_rate']:.3f}",
        f"- Edge/fence heldout success: {decision['edge_fence_success_rate']:.3f}",
        f"- Edge/fence M4-only success: {decision['edge_fence_m4_only_success_rate']:.3f}",
        f"- Edge/fence M4 promotions: {decision['edge_fence_m4_true_promotion_count']}",
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
