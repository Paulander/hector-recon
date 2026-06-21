"""TG28i short staged edge/fence -> bridge -> frozen foundation rollout."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import time
from pathlib import Path
from typing import Any

import chess

from .controlled_mixed_frontier_edge_curriculum import (
    ControlledMixedFrontierEdgeCurriculumConfig,
    _action_delta_update_estimate,
    _as_tg28f_config,
    _near_miss_fens,
    _purity_boundary as _tg28h_purity_boundary,
    _schedule_public as _tg28h_schedule_public,
    _train_generic_edge_weights,
    _train_near_miss_negative,
)
from .foundation_backed_bridge_frontier import _as_tg28c_config
from .frozen_foundation_bridge_pressure import _bridge_reward, _compact_foundation_sanity
from .frozen_foundation_edge_fence_reentry import (
    _build_tg27b_foundation,
    _edge_reward,
    _evaluate_edge_layer,
    _foundation_counts,
    _generate_edge_fence_positions,
    _cheap_candidate_rows,
)
from .frozen_foundation_response_cache_bridge_retrieval import (
    _FoundationResponseCache,
    _cache_candidate_rows,
    _evaluate_cache_bridge_layer,
    _train_cache_bridge_layer,
)
from .full_frontier_validation_near_miss import _load_jsonl
from .internal_handoff_affordance_guard_audit import _mate2_cfg
from .native_quorum_mate2_chaining import _tg26u_config
from .native_quorum_materialization import _tg26t_config
from .persisted_foundation_backed_frontier_pool import _as_tg28b_config, _as_tg28d_like_config
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence


@dataclass(frozen=True)
class StagedEdgeBridgeFoundationRolloutConfig:
    seed: int = 20260701
    foundation_seed: int = 20260624
    foundation_mate1_train_count: int = 32
    foundation_mate1_heldout_count: int = 16
    foundation_mate2_train_count: int = 16
    foundation_mate2_heldout_count: int = 8
    bridge_frontier_train_count: int = 8
    bridge_frontier_heldout_count: int = 4
    generic_edge_safety_regression_count: int = 8
    basin_random_count: int = 8
    max_generation_attempts: int = 250_000
    max_cache_candidate_moves: int = 6
    max_reply_envelope_replies_per_candidate: int = 1
    max_mate2_probe_moves_per_state: int = 2
    max_edge_candidates_per_position: int = 12
    max_ablation_positions: int = 1
    max_foundation_sanity_positions: int = 1
    max_foundation_ablation_positions: int = 1
    max_ticks: int = 30
    max_samples: int = 16
    repaired_high_recall_threshold: float = 0.018
    eta_m3_edge: float = 0.06
    eta_m3_bridge: float = 0.08
    edge_terminal_min_score: float = -0.25
    bridge_terminal_min_score: float = 0.10
    materialized_quorum_min_evidence: float = -10000.0
    replay_count: int = 1
    generic_edge_train_count: int = 16
    generic_edge_heldout_count: int = 8
    near_miss_train_count: int = 8
    near_miss_heldout_count: int = 8
    staged_train_count: int = 4
    staged_heldout_count: int = 4
    staged_generation_multiplier: int = 30
    max_staged_source_positions: int = 120
    max_staged_first_move_candidates: int = 4
    max_staged_black_replies_after_edge: int = 2
    max_staged_black_replies_after_bridge: int = 1
    schedule_names: tuple[str, ...] = (
        "tg28h_mixed_balanced_baseline",
        "mixed_balanced_plus_staged",
        "staged_first_then_mixed_replay",
        "mixed_first_then_staged",
        "mixed_staged_near_miss_replay",
    )
    full_pool_path: str = "reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl"
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg28i_staged_edge_bridge_foundation_rollout_progress.json"


@dataclass(frozen=True)
class StagedEdgeBridgeFoundationRolloutResult:
    config: StagedEdgeBridgeFoundationRolloutConfig
    dataset: dict[str, Any]
    foundation_sanity: dict[str, Any]
    generation: dict[str, Any]
    schedule_comparison: dict[str, Any]
    selected_schedule: dict[str, Any]
    ablation_results: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg28i_staged_edge_bridge_foundation_rollout.v0",
            "checkpoint": "TG28i_staged_edge_bridge_foundation_rollout",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "foundation_sanity": self.foundation_sanity,
            "generation": self.generation,
            "schedule_comparison": self.schedule_comparison,
            "selected_schedule": self.selected_schedule,
            "ablation_results": self.ablation_results,
            "scheduler_equivalence": self.scheduler_equivalence,
            "phase_timings": self.phase_timings,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        start = time.perf_counter()
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        self.phase_timings["artifact_write_seconds"] = round(time.perf_counter() - start, 6)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_staged_edge_bridge_foundation_rollout(
    *,
    config: StagedEdgeBridgeFoundationRolloutConfig | None = None,
) -> StagedEdgeBridgeFoundationRolloutResult:
    cfg = config or StagedEdgeBridgeFoundationRolloutConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    tg28c_cfg = _as_tg28c_config(_as_tg28d_like_config(_as_tg28f_config(_as_tg28h_config(cfg))))
    edge_cfg = _as_tg28b_config(tg28c_cfg)
    pool_entries = _load_jsonl(Path(cfg.full_pool_path))
    frontier_train = tuple(entry["position_fen"] for entry in pool_entries if entry.get("split") == "train")[: cfg.bridge_frontier_train_count]
    frontier_heldout = tuple(entry["position_fen"] for entry in pool_entries if entry.get("split") == "heldout")[: cfg.bridge_frontier_heldout_count]
    excluded = set(frontier_train + frontier_heldout)
    _write_progress(cfg, {"phase": "pool_loaded", "frontier_train_count": len(frontier_train), "frontier_heldout_count": len(frontier_heldout)})

    start = time.perf_counter()
    foundation = _build_tg27b_foundation(edge_cfg)
    timings["foundation_build_seconds"] = round(time.perf_counter() - start, 6)
    graph = foundation["graph"]
    mate1_train = foundation["mate1_train"]
    mate1_heldout = foundation["mate1_heldout"]
    mate2_heldout = foundation["mate2_heldout"]
    mate2_cfg = _mate2_cfg(foundation["internal_cfg"])
    start = time.perf_counter()
    foundation_sanity = _compact_foundation_sanity(graph, mate1_heldout, mate2_heldout, foundation["attention_cfg"], mate2_cfg, edge_cfg)
    cache = _FoundationResponseCache(graph, mate2_cfg, tg28c_cfg)
    timings["foundation_sanity_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {
        "phase": "foundation_sanity_complete",
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
    })

    start = time.perf_counter()
    generic_train = _generate_edge_fence_positions(count=cfg.generic_edge_train_count, seed=cfg.seed + 41, excluded=excluded, cfg=edge_cfg)
    excluded.update(generic_train)
    generic_heldout = _generate_edge_fence_positions(count=cfg.generic_edge_heldout_count, seed=cfg.seed + 42, excluded=excluded, cfg=edge_cfg)
    excluded.update(generic_heldout)
    seed_edge_weights: dict[str, float] = {}
    seed_bridge_weights: dict[str, float] = {}
    _train_cache_bridge_layer(cache, frontier_train, tg28c_cfg, seed_edge_weights, seed_bridge_weights)
    _write_progress(cfg, {"phase": "seed_frontier_training_complete", "frontier_train_count": len(frontier_train)})
    _train_generic_edge_weights(generic_train, edge_cfg, seed_edge_weights)
    _write_progress(cfg, {"phase": "seed_generic_training_complete", "generic_train_count": len(generic_train)})
    near_miss_train = (
        tuple()
        if cfg.near_miss_train_count <= 0
        else _near_miss_fens(cache, tg28c_cfg, seed_edge_weights, seed_bridge_weights, cfg.near_miss_train_count, cfg.seed + 43, excluded)
    )
    excluded.update(near_miss_train)
    near_miss_heldout = (
        tuple()
        if cfg.near_miss_heldout_count <= 0
        else _near_miss_fens(cache, tg28c_cfg, seed_edge_weights, seed_bridge_weights, cfg.near_miss_heldout_count, cfg.seed + 44, excluded)
    )
    excluded.update(near_miss_heldout)
    staged, generation = _generate_staged_examples(
        cache,
        tg28c_cfg,
        edge_cfg,
        seed_edge_weights,
        seed_bridge_weights,
        count=cfg.staged_train_count + cfg.staged_heldout_count,
        seed=cfg.seed + 50,
        excluded=excluded,
        cfg=cfg,
    )
    staged_train = tuple(staged[: cfg.staged_train_count])
    staged_heldout = tuple(staged[cfg.staged_train_count : cfg.staged_train_count + cfg.staged_heldout_count])
    timings["dataset_generation_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {
        "phase": "datasets_complete",
        "generic_train_count": len(generic_train),
        "generic_heldout_count": len(generic_heldout),
        "near_miss_train_count": len(near_miss_train),
        "near_miss_heldout_count": len(near_miss_heldout),
        "staged_train_count": len(staged_train),
        "staged_heldout_count": len(staged_heldout),
        "staged_generation_attempts": generation["generation_attempts"],
    })

    foundation_before_training = _foundation_counts(graph)
    start = time.perf_counter()
    schedules = _run_schedule_comparison(
        graph,
        cache,
        mate2_cfg,
        tg28c_cfg,
        edge_cfg,
        frontier_train=frontier_train,
        frontier_heldout=frontier_heldout,
        generic_train=generic_train,
        generic_heldout=generic_heldout,
        near_miss_train=near_miss_train,
        near_miss_heldout=near_miss_heldout,
        staged_train=staged_train,
        staged_heldout=staged_heldout,
        cfg=cfg,
    )
    timings["schedule_comparison_seconds"] = round(time.perf_counter() - start, 6)
    foundation_after_training = _foundation_counts(graph)
    selected = _select_schedule(schedules)
    _write_progress(cfg, {
        "phase": "schedule_comparison_complete",
        "selected_training_schedule": selected["schedule_name"],
        "frontier_selected_count": selected["frontier_selected_count"],
        "near_miss_false_positive_count": selected["near_miss_false_positive_count"],
        "generic_edge_fence_success_rate": selected["generic_edge_fence_success_rate"],
        "staged_any_reply_success_count": selected["staged_any_reply_success_count"],
    })

    foundation_before_eval = _foundation_counts(graph)
    start = time.perf_counter()
    ablations = _required_ablations(
        graph,
        cache,
        mate2_cfg,
        tg28c_cfg,
        edge_cfg,
        frontier_heldout,
        generic_heldout,
        staged_heldout,
        selected["edge_weights"],
        selected["bridge_weights"],
        cfg,
    )
    equivalence = cache.live_equivalence_audit(max_samples=min(8, cfg.max_samples))
    scheduler_equivalence = (
        {"mismatch_count": 0, "skipped": True, "skip_reason": "max_ablation_positions_zero"}
        if cfg.max_ablation_positions <= 0
        else _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(mate2_cfg))), mate1_train, mate1_heldout)
    )
    foundation_after_eval = _foundation_counts(graph)
    timings["ablation_eval_seconds"] = round(time.perf_counter() - start, 6)
    timings["artifact_write_seconds"] = 0.0
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)

    decision = _decision(
        cfg,
        foundation_sanity=foundation_sanity,
        selected=selected,
        schedules=schedules,
        equivalence=equivalence,
        ablations=ablations,
        scheduler_equivalence=scheduler_equivalence,
        foundation_before_training=foundation_before_training,
        foundation_after_training=foundation_after_training,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {
        "checkpoint_pass": decision["checkpoint_pass"],
        "checkpoint_interpretation": decision["checkpoint_interpretation"],
        "selected_training_schedule": decision["selected_training_schedule"],
        "staged_any_reply_success_count": decision["staged_any_reply_success_count"],
    }})
    return StagedEdgeBridgeFoundationRolloutResult(
        config=cfg,
        dataset={
            "frontier_train_count": len(frontier_train),
            "frontier_heldout_count": len(frontier_heldout),
            "generic_train_count": len(generic_train),
            "generic_heldout_count": len(generic_heldout),
            "near_miss_train_count": len(near_miss_train),
            "near_miss_heldout_count": len(near_miss_heldout),
            "staged_train_count": len(staged_train),
            "staged_heldout_count": len(staged_heldout),
            "frontier_heldout_fens": list(frontier_heldout)[: cfg.max_samples],
            "generic_heldout_fens": list(generic_heldout)[: cfg.max_samples],
            "near_miss_heldout_fens": list(near_miss_heldout)[: cfg.max_samples],
            "staged_train_examples": [example["summary"] for example in staged_train[: cfg.max_samples]],
            "staged_heldout_examples": [example["summary"] for example in staged_heldout[: cfg.max_samples]],
            "stream_labels_learner_visible": False,
        },
        foundation_sanity=foundation_sanity,
        generation=generation,
        schedule_comparison={name: _schedule_public(row, cfg.max_samples) for name, row in schedules.items()},
        selected_schedule=_schedule_public(selected, cfg.max_samples),
        ablation_results=ablations,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _as_tg28h_config(cfg: StagedEdgeBridgeFoundationRolloutConfig) -> ControlledMixedFrontierEdgeCurriculumConfig:
    return ControlledMixedFrontierEdgeCurriculumConfig(
        seed=cfg.seed,
        foundation_seed=cfg.foundation_seed,
        foundation_mate1_train_count=cfg.foundation_mate1_train_count,
        foundation_mate1_heldout_count=cfg.foundation_mate1_heldout_count,
        foundation_mate2_train_count=cfg.foundation_mate2_train_count,
        foundation_mate2_heldout_count=cfg.foundation_mate2_heldout_count,
        bridge_frontier_train_count=cfg.bridge_frontier_train_count,
        bridge_frontier_heldout_count=cfg.bridge_frontier_heldout_count,
        generic_edge_safety_regression_count=cfg.generic_edge_safety_regression_count,
        basin_random_count=cfg.basin_random_count,
        max_generation_attempts=cfg.max_generation_attempts,
        max_cache_candidate_moves=cfg.max_cache_candidate_moves,
        max_reply_envelope_replies_per_candidate=cfg.max_reply_envelope_replies_per_candidate,
        max_mate2_probe_moves_per_state=cfg.max_mate2_probe_moves_per_state,
        max_edge_candidates_per_position=cfg.max_edge_candidates_per_position,
        max_ablation_positions=cfg.max_ablation_positions,
        max_foundation_sanity_positions=cfg.max_foundation_sanity_positions,
        max_foundation_ablation_positions=cfg.max_foundation_ablation_positions,
        max_ticks=cfg.max_ticks,
        max_samples=cfg.max_samples,
        repaired_high_recall_threshold=cfg.repaired_high_recall_threshold,
        eta_m3_edge=cfg.eta_m3_edge,
        eta_m3_bridge=cfg.eta_m3_bridge,
        edge_terminal_min_score=cfg.edge_terminal_min_score,
        bridge_terminal_min_score=cfg.bridge_terminal_min_score,
        materialized_quorum_min_evidence=cfg.materialized_quorum_min_evidence,
        replay_count=cfg.replay_count,
        generic_edge_train_count=cfg.generic_edge_train_count,
        generic_edge_heldout_count=cfg.generic_edge_heldout_count,
        near_miss_train_count=cfg.near_miss_train_count,
        near_miss_heldout_count=cfg.near_miss_heldout_count,
        full_pool_path=cfg.full_pool_path,
        progress_output=cfg.progress_output,
    )


def _generate_staged_examples(
    cache: _FoundationResponseCache,
    tg28c_cfg,
    edge_cfg,
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
    *,
    count: int,
    seed: int,
    excluded: set[str],
    cfg: StagedEdgeBridgeFoundationRolloutConfig,
) -> tuple[tuple[dict[str, Any], ...], dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    attempts = 0
    rejected: dict[str, int] = {}
    if count <= 0:
        return tuple(), {
            "generation_method": "forward_filter_generic_edge_to_cache_bridge_frontier",
            "generation_attempts": 0,
            "requested_count": count,
            "accepted_count": 0,
            "rejection_counts": {},
            "acceptance_rate": 0.0,
            "cache_queries_run_total": cache.query_count,
            "max_staged_black_replies_after_edge": cfg.max_staged_black_replies_after_edge,
            "max_staged_black_replies_after_bridge": cfg.max_staged_black_replies_after_bridge,
            "samples": [],
        }
    source_count = min(cfg.max_staged_source_positions, max(count * cfg.staged_generation_multiplier, count))
    candidate_fens = _generate_edge_fence_positions(count=source_count, seed=seed, excluded=excluded, cfg=edge_cfg)
    for fen in candidate_fens:
        attempts += 1
        board = chess.Board(fen)
        if _foundation_positive(cache.query_state(board)):
            rejected["already_in_foundation_basin"] = rejected.get("already_in_foundation_basin", 0) + 1
            continue
        rows = sorted(
            [row for row in _cheap_candidate_rows(board, edge_weights) if row["safety_ok"] and _edge_reward(row) > 0.0],
            key=lambda row: (row["cheap_score"] + _edge_reward(row), row["move"]),
            reverse=True,
        )[: cfg.max_staged_first_move_candidates]
        if not rows:
            rejected["no_safe_edge_candidate"] = rejected.get("no_safe_edge_candidate", 0) + 1
            continue
        accepted = None
        for edge_row in rows:
            reply_rows = _stage_reply_rows(cache, tg28c_cfg, board, edge_row["move"], edge_weights, bridge_weights, cfg)
            bridge_reply_count = sum(int(row["bridge_opportunity"]) for row in reply_rows)
            if bridge_reply_count <= 0:
                continue
            accepted = {
                "fen": fen,
                "trainer_edge_move": edge_row["move"],
                "edge_reward": round(_edge_reward(edge_row), 6),
                "reply_rows": reply_rows,
                "summary": {
                    "fen": fen,
                    "trainer_edge_move": edge_row["move"],
                    "sampled_black_reply_count": len(reply_rows),
                    "bridge_opportunity_reply_count": bridge_reply_count,
                    "all_reply_stage_success": len(reply_rows) > 0 and bridge_reply_count == len(reply_rows),
                    "partial_reply_stage_success": 0 < bridge_reply_count < len(reply_rows),
                    "any_reply_stage_success": bridge_reply_count > 0,
                },
            }
            break
        if accepted is None:
            rejected["no_black_reply_bridge_opportunity"] = rejected.get("no_black_reply_bridge_opportunity", 0) + 1
            continue
        examples.append(accepted)
        excluded.add(fen)
        if len(examples) >= count:
            break
    return tuple(examples), {
        "generation_method": "forward_filter_generic_edge_to_cache_bridge_frontier",
        "generation_attempts": attempts,
        "requested_count": count,
        "accepted_count": len(examples),
        "rejection_counts": rejected,
        "acceptance_rate": len(examples) / max(1, attempts),
        "cache_queries_run_total": cache.query_count,
        "max_staged_black_replies_after_edge": cfg.max_staged_black_replies_after_edge,
        "max_staged_black_replies_after_bridge": cfg.max_staged_black_replies_after_bridge,
        "samples": [example["summary"] for example in examples[: cfg.max_samples]],
    }


def _stage_reply_rows(cache, tg28c_cfg, board: chess.Board, edge_move_uci: str, edge_weights, bridge_weights, cfg) -> list[dict[str, Any]]:
    move = chess.Move.from_uci(edge_move_uci)
    if move not in board.legal_moves:
        return []
    after_edge = board.copy(stack=False)
    after_edge.push(move)
    rows = []
    for black_reply in sorted(after_edge.legal_moves, key=lambda item: item.uci())[: cfg.max_staged_black_replies_after_edge]:
        s1 = after_edge.copy(stack=False)
        s1.push(black_reply)
        if s1.turn != chess.WHITE or s1.is_game_over():
            rows.append({
                "black_reply": black_reply.uci(),
                "s1_fen": s1.fen(),
                "bridge_opportunity": False,
                "failure_bucket": "black_reply_terminal_or_wrong_turn",
            })
            continue
        candidates = _cache_candidate_rows(cache, s1, tg28c_cfg, edge_weights, bridge_weights, cache_retrieval_enabled=True)
        confirmed = [row for row in candidates if row["formal_recon_engine_confirmed"]]
        confirmed.sort(key=lambda row: (row["evidence_score"], row["move"]), reverse=True)
        selected = None if not confirmed else confirmed[0]
        bridge_rows = [row for row in candidates if row["reply_envelope_foundation_reachable"] or row["bounded_bridge_foundation_reachable"]]
        rows.append({
            "black_reply": black_reply.uci(),
            "s1_fen": s1.fen(),
            "bridge_candidate_count": len(bridge_rows),
            "bridge_opportunity": len(bridge_rows) > 0,
            "bridge_selected_move": None if selected is None else selected["move"],
            "bridge_selected_foundation_reachable": bool(selected and selected["reply_envelope_foundation_reachable"]),
            "same_graph_foundation_continuation_count": 0 if selected is None else selected["same_graph_foundation_continuation_count"],
            "foundation_handoff_conversion": bool(selected and selected["foundation_handoff_conversion"]),
            "failure_bucket": "none" if bridge_rows else "black_reply_leaves_no_bridge_candidate",
        })
    return rows


def _run_schedule_comparison(
    graph,
    cache: _FoundationResponseCache,
    mate2_cfg,
    tg28c_cfg,
    edge_cfg,
    *,
    frontier_train: tuple[str, ...],
    frontier_heldout: tuple[str, ...],
    generic_train: tuple[str, ...],
    generic_heldout: tuple[str, ...],
    near_miss_train: tuple[str, ...],
    near_miss_heldout: tuple[str, ...],
    staged_train: tuple[dict[str, Any], ...],
    staged_heldout: tuple[dict[str, Any], ...],
    cfg: StagedEdgeBridgeFoundationRolloutConfig,
) -> dict[str, dict[str, Any]]:
    specs = {
        "tg28h_mixed_balanced_baseline": ("frontier", "generic", "near_miss"),
        "mixed_balanced_plus_staged": ("frontier", "generic", "near_miss", "staged"),
        "staged_first_then_mixed_replay": ("staged", "frontier", "generic", "near_miss"),
        "mixed_first_then_staged": ("frontier", "generic", "near_miss", "staged"),
        "mixed_staged_near_miss_replay": ("frontier", "generic", "near_miss", "staged", "near_miss"),
    }
    rows = {}
    for name, steps in specs.items():
        if name not in cfg.schedule_names:
            continue
        edge_weights: dict[str, float] = {}
        bridge_weights: dict[str, float] = {}
        updates = {"edge_terminal_m3_update_count": 0, "bridge_terminal_m3_update_count": 0, "shared_action_delta_update_count": 0, "actuator_update_count": 0}
        samples = []
        for step in steps:
            if step == "frontier":
                result = _train_cache_bridge_layer(cache, frontier_train, tg28c_cfg, edge_weights, bridge_weights)
                updates["edge_terminal_m3_update_count"] += result["edge_only_m3_update_count"]
                updates["bridge_terminal_m3_update_count"] += result["bridge_terminal_m3_update_count"]
                updates["shared_action_delta_update_count"] += _action_delta_update_estimate(result)
                samples.extend(result.get("samples", [])[:2])
            elif step == "generic":
                result = _train_generic_edge_weights(generic_train, edge_cfg, edge_weights)
                updates["edge_terminal_m3_update_count"] += result["edge_terminal_m3_update_count"]
                updates["shared_action_delta_update_count"] += _action_delta_update_estimate(result)
                samples.extend(result.get("samples", [])[:2])
            elif step == "near_miss":
                result = _train_near_miss_negative(cache, near_miss_train, tg28c_cfg, edge_weights, bridge_weights)
                updates["bridge_terminal_m3_update_count"] += result["bridge_terminal_m3_update_count"]
                updates["shared_action_delta_update_count"] += result["shared_action_delta_update_count"]
                samples.extend(result.get("samples", [])[:2])
            elif step == "staged":
                result = _train_staged_examples(cache, staged_train, tg28c_cfg, edge_cfg, edge_weights, bridge_weights, cfg)
                updates["edge_terminal_m3_update_count"] += result["edge_terminal_m3_update_count"]
                updates["bridge_terminal_m3_update_count"] += result["bridge_terminal_m3_update_count"]
                updates["shared_action_delta_update_count"] += result["shared_action_delta_update_count"]
                samples.extend(result.get("samples", [])[:2])
        rows[name] = _evaluate_schedule(
            name,
            graph,
            cache,
            mate2_cfg,
            tg28c_cfg,
            edge_cfg,
            frontier_heldout,
            generic_heldout,
            near_miss_heldout,
            staged_heldout,
            edge_weights,
            bridge_weights,
            updates,
            samples,
            cfg,
        )
        _write_progress(cfg, {
            "phase": "schedule_arm_complete",
            "schedule_name": name,
            "frontier_selected_count": rows[name]["frontier_selected_count"],
            "near_miss_false_positive_count": rows[name]["near_miss_false_positive_count"],
            "generic_edge_fence_success_rate": rows[name]["generic_edge_fence_success_rate"],
            "staged_any_reply_success_count": rows[name]["staged_any_reply_success_count"],
        })
    return rows


def _train_staged_examples(cache, staged_examples, tg28c_cfg, edge_cfg, edge_weights, bridge_weights, cfg) -> dict[str, Any]:
    edge_updates = 0
    bridge_updates = 0
    action_delta_updates = 0
    samples = []
    for example in staged_examples:
        board = chess.Board(example["fen"])
        rows = _cheap_candidate_rows(board, edge_weights)
        for row in rows:
            reward = _edge_reward(row) + (0.35 if row["move"] == example["trainer_edge_move"] else 0.0)
            for key in row["positive_feature_keys"]:
                edge_weights[key] = max(-1.0, min(1.0, edge_weights.get(key, 0.0) + edge_cfg.eta_m3_edge * reward))
                edge_updates += 1
                action_delta_updates += int("delta_" in key)
        s1_fens = tuple(row["s1_fen"] for row in example["reply_rows"] if row.get("bridge_opportunity"))
        result = _train_cache_bridge_layer(cache, s1_fens, tg28c_cfg, edge_weights, bridge_weights)
        edge_updates += result["edge_only_m3_update_count"]
        bridge_updates += result["bridge_terminal_m3_update_count"]
        action_delta_updates += _action_delta_update_estimate(result)
        if len(samples) < cfg.max_samples:
            samples.append({
                "fen": example["fen"],
                "trainer_edge_move": example["trainer_edge_move"],
                "stage_bridge_reply_count": len(s1_fens),
                "bridge_updates": result["bridge_terminal_m3_update_count"],
            })
    return {
        "edge_terminal_m3_update_count": edge_updates,
        "bridge_terminal_m3_update_count": bridge_updates,
        "shared_action_delta_update_count": action_delta_updates,
        "samples": samples,
    }


def _evaluate_schedule(
    name,
    graph,
    cache,
    mate2_cfg,
    tg28c_cfg,
    edge_cfg,
    frontier_heldout,
    generic_heldout,
    near_miss_heldout,
    staged_heldout,
    edge_weights,
    bridge_weights,
    updates,
    samples,
    cfg,
) -> dict[str, Any]:
    frontier = _evaluate_cache_bridge_layer(graph, cache, frontier_heldout, tg28c_cfg, edge_weights, bridge_weights)
    near_miss = _evaluate_cache_bridge_layer(graph, cache, near_miss_heldout, tg28c_cfg, edge_weights, bridge_weights)
    generic = _evaluate_edge_layer(graph, generic_heldout, mate2_cfg, edge_cfg, edge_weights, foundation_handoff_enabled=True)
    staged = _evaluate_staged_rollout(graph, cache, mate2_cfg, tg28c_cfg, edge_cfg, staged_heldout, edge_weights, bridge_weights, cfg)
    return {
        "schedule_name": name,
        "frontier": frontier,
        "near_miss": near_miss,
        "generic": generic,
        "staged": staged,
        "frontier_selected_count": frontier["selected_move_count"],
        "frontier_heldout_count": frontier["position_count"],
        "frontier_selection_rate": frontier["selected_move_count"] / max(1, frontier["position_count"]),
        "frontier_reply_envelope_foundation_reachable_count": frontier["reply_envelope_foundation_reachable_count"],
        "frontier_foundation_handoff_conversion_count": frontier["foundation_handoff_conversion_count"],
        "frontier_same_graph_continuation_count": frontier["same_graph_foundation_continuation_count"],
        "frontier_rook_blunder_count": frontier["rook_blunder_count"],
        "frontier_stalemate_avoidance_rate": frontier["stalemate_avoidance_rate"],
        "near_miss_candidate_count": near_miss["cache_scored_candidate_count"],
        "near_miss_selected_count": near_miss["selected_move_count"],
        "near_miss_false_positive_count": near_miss["selected_move_count"],
        "near_miss_rejection_rate": 1.0 - near_miss["selected_move_count"] / max(1, near_miss["position_count"]),
        "near_miss_failure_bucket_counts": near_miss["failure_bucket_counts"],
        "generic_selected_count": generic["selected_move_count"],
        "generic_heldout_count": generic["position_count"],
        "generic_selection_rate": generic["selected_move_count"] / max(1, generic["position_count"]),
        "generic_edge_fence_success_rate": generic["edge_fence_success_rate"],
        "generic_confinement_area_improvement_rate": generic["confinement_area_improvement_rate"],
        "generic_black_king_mobility_reduction_rate": generic["black_king_mobility_reduction_rate"],
        "generic_edge_distance_improvement_rate": generic["edge_distance_improvement_rate"],
        "generic_foundation_handoff_conversion_count": generic["foundation_handoff_conversion_count"],
        "generic_rook_blunder_count": generic["rook_blunder_count"],
        "generic_stalemate_avoidance_rate": generic["stalemate_avoidance_rate"],
        "generic_null_count": generic["null_move_count"],
        "staged_train_count": cfg.staged_train_count,
        "staged_heldout_count": staged["position_count"],
        "staged_selected_first_move_count": staged["selected_first_move_count"],
        "staged_first_move_edge_success_count": staged["first_move_edge_success_count"],
        "staged_first_move_safety_success_count": staged["first_move_safety_success_count"],
        "staged_black_reply_count_total": staged["black_reply_count_total"],
        "staged_s1_bridge_candidate_count": staged["s1_bridge_candidate_count"],
        "staged_s1_bridge_selected_count": staged["s1_bridge_selected_count"],
        "staged_s1_bridge_foundation_reachable_count": staged["s1_bridge_foundation_reachable_count"],
        "staged_same_graph_foundation_continuation_count": staged["same_graph_foundation_continuation_count"],
        "staged_foundation_handoff_conversion_count": staged["foundation_handoff_conversion_count"],
        "staged_all_reply_success_count": staged["all_reply_success_count"],
        "staged_partial_reply_success_count": staged["partial_reply_success_count"],
        "staged_any_reply_success_count": staged["any_reply_success_count"],
        "staged_null_count": staged["null_count"],
        "staged_rook_blunder_count": staged["rook_blunder_count"],
        "staged_stalemate_failure_count": staged["stalemate_failure_count"],
        "failure_bucket_counts": {
            "frontier": frontier["failure_bucket_counts"],
            "near_miss": near_miss["failure_bucket_counts"],
            "generic_edge_fence": generic["failure_bucket_counts"],
            "staged": staged["failure_bucket_counts"],
        },
        "edge_weights": dict(edge_weights),
        "bridge_weights": dict(bridge_weights),
        "training_samples": samples[:8],
        **updates,
        "m4_promotion_count_by_terminal_kind_edge_bridge_staged_only": {},
    }


def _evaluate_staged_rollout(
    graph,
    cache,
    mate2_cfg,
    tg28c_cfg,
    edge_cfg,
    staged_examples,
    edge_weights,
    bridge_weights,
    cfg,
    *,
    edge_masks: dict[str, bool] | None = None,
    bridge_masks: dict[str, bool] | None = None,
) -> dict[str, Any]:
    edge_masks = edge_masks or {}
    bridge_masks = bridge_masks or {}
    rows = []
    totals = _empty_staged_totals()
    before_cache_queries = cache.query_count
    for example in staged_examples:
        fen = example["fen"]
        edge_eval = _evaluate_edge_layer(graph, (fen,), mate2_cfg, edge_cfg, edge_weights, foundation_handoff_enabled=True, masks=edge_masks)
        edge_row = edge_eval["samples"][0] if edge_eval["samples"] else {"selected": None, "failure_bucket": "unknown"}
        selected_edge = edge_row["selected"]
        row = {
            "fen": fen,
            "trainer_edge_move": example.get("trainer_edge_move"),
            "selected_edge_move": None if selected_edge is None else selected_edge["move"],
            "edge_eval": edge_row,
            "reply_rows": [],
            "failure_bucket": "none",
        }
        totals["positions"] += 1
        if selected_edge is None:
            totals["null_count"] += 1
            totals["failure_bucket_counts"]["edge_candidate_rejected_by_attention"] = totals["failure_bucket_counts"].get("edge_candidate_rejected_by_attention", 0) + 1
            row["failure_bucket"] = edge_row.get("failure_bucket", "edge_candidate_rejected_by_attention")
            rows.append(row)
            continue
        totals["selected_first_move_count"] += 1
        edge_success = (
            selected_edge["delta_black_king_edge_distance"] < 0
            or selected_edge["delta_confinement_area"] < 0
            or selected_edge["delta_black_king_legal_mobility"] < 0
        )
        edge_safe = selected_edge["after_features"]["rook_safe"] > 0.0 and selected_edge["after_features"]["rook_attacked_after"] == 0.0
        stalemate_safe = selected_edge["after_features"]["stalemate_after"] == 0.0
        totals["first_move_edge_success_count"] += int(edge_success)
        totals["first_move_safety_success_count"] += int(edge_safe and stalemate_safe)
        totals["rook_blunder_count"] += int(not edge_safe)
        totals["stalemate_failure_count"] += int(not stalemate_safe)
        if not edge_safe:
            row["failure_bucket"] = "selected_first_move_blunders_rook"
        elif not stalemate_safe:
            row["failure_bucket"] = "selected_first_move_stalemates"
        board = chess.Board(fen)
        move = chess.Move.from_uci(selected_edge["move"])
        if move not in board.legal_moves:
            totals["failure_bucket_counts"]["selected_first_move_illegal"] = totals["failure_bucket_counts"].get("selected_first_move_illegal", 0) + 1
            row["failure_bucket"] = "selected_first_move_illegal"
            rows.append(row)
            continue
        after_edge = board.copy(stack=False)
        after_edge.push(move)
        reply_successes = 0
        reply_count = 0
        for black_reply in sorted(after_edge.legal_moves, key=lambda item: item.uci())[: cfg.max_staged_black_replies_after_edge]:
            reply_count += 1
            totals["black_reply_count_total"] += 1
            s1 = after_edge.copy(stack=False)
            s1.push(black_reply)
            bridge_eval = _evaluate_cache_bridge_layer(graph, cache, (s1.fen(),), tg28c_cfg, edge_weights, bridge_weights, masks=bridge_masks)
            bridge_row = bridge_eval["samples"][0] if bridge_eval["samples"] else {"selected": None, "candidate_rows": [], "failure_bucket": "unknown"}
            selected_bridge = bridge_row["selected"]
            bridge_candidates = [
                candidate
                for candidate in bridge_row.get("candidate_rows", [])
                if candidate["reply_envelope_foundation_reachable"] or candidate["bounded_bridge_foundation_reachable"]
            ]
            totals["s1_bridge_candidate_count"] += len(bridge_candidates)
            reply_payload = {
                "black_reply": black_reply.uci(),
                "s1_fen": s1.fen(),
                "bridge_selected_move": None if selected_bridge is None else selected_bridge["move"],
                "bridge_candidate_count": len(bridge_candidates),
                "bridge_failure_bucket": bridge_row.get("failure_bucket"),
                "foundation_reply_rows": [],
            }
            if selected_bridge is None:
                totals["failure_bucket_counts"]["bridge_candidate_not_generated"] = totals["failure_bucket_counts"].get("bridge_candidate_not_generated", 0) + 1
                row["reply_rows"].append(reply_payload)
                continue
            totals["s1_bridge_selected_count"] += 1
            bridge_reachable = bool(selected_bridge["reply_envelope_foundation_reachable"] or selected_bridge["bounded_bridge_foundation_reachable"])
            totals["s1_bridge_foundation_reachable_count"] += int(bridge_reachable)
            totals["same_graph_foundation_continuation_count"] += int(selected_bridge["same_graph_foundation_continuation_count"])
            totals["foundation_handoff_conversion_count"] += int(selected_bridge["foundation_handoff_conversion"])
            envelope = selected_bridge.get("cache_reply_envelope", {})
            foundation_rows = envelope.get("reply_rows", [])[: cfg.max_staged_black_replies_after_bridge]
            reply_payload["foundation_reply_rows"] = foundation_rows
            foundation_ok = bool(foundation_rows) and all(item.get("foundation_solved") for item in foundation_rows)
            reply_payload["foundation_continuation_success"] = foundation_ok
            reply_successes += int(bridge_reachable and foundation_ok)
            row["reply_rows"].append(reply_payload)
        all_success = reply_count > 0 and reply_successes == reply_count
        any_success = reply_successes > 0
        partial_success = 0 < reply_successes < reply_count
        totals["all_reply_success_count"] += int(all_success)
        totals["partial_reply_success_count"] += int(partial_success)
        totals["any_reply_success_count"] += int(any_success)
        if not any_success and row["failure_bucket"] == "none":
            row["failure_bucket"] = "black_reply_leaves_no_bridge_candidate"
        totals["failure_bucket_counts"][row["failure_bucket"]] = totals["failure_bucket_counts"].get(row["failure_bucket"], 0) + 1
        rows.append(row)
    return {
        "position_count": totals["positions"],
        "selected_first_move_count": totals["selected_first_move_count"],
        "first_move_edge_success_count": totals["first_move_edge_success_count"],
        "first_move_safety_success_count": totals["first_move_safety_success_count"],
        "black_reply_count_total": totals["black_reply_count_total"],
        "s1_bridge_candidate_count": totals["s1_bridge_candidate_count"],
        "s1_bridge_selected_count": totals["s1_bridge_selected_count"],
        "s1_bridge_foundation_reachable_count": totals["s1_bridge_foundation_reachable_count"],
        "same_graph_foundation_continuation_count": totals["same_graph_foundation_continuation_count"],
        "foundation_handoff_conversion_count": totals["foundation_handoff_conversion_count"],
        "all_reply_success_count": totals["all_reply_success_count"],
        "partial_reply_success_count": totals["partial_reply_success_count"],
        "any_reply_success_count": totals["any_reply_success_count"],
        "null_count": totals["null_count"],
        "rook_blunder_count": totals["rook_blunder_count"],
        "stalemate_failure_count": totals["stalemate_failure_count"],
        "cache_queries_run": cache.query_count - before_cache_queries,
        "failure_bucket_counts": totals["failure_bucket_counts"],
        "samples": rows[: cfg.max_samples],
    }


def _empty_staged_totals() -> dict[str, Any]:
    return {
        "positions": 0,
        "selected_first_move_count": 0,
        "first_move_edge_success_count": 0,
        "first_move_safety_success_count": 0,
        "black_reply_count_total": 0,
        "s1_bridge_candidate_count": 0,
        "s1_bridge_selected_count": 0,
        "s1_bridge_foundation_reachable_count": 0,
        "same_graph_foundation_continuation_count": 0,
        "foundation_handoff_conversion_count": 0,
        "all_reply_success_count": 0,
        "partial_reply_success_count": 0,
        "any_reply_success_count": 0,
        "null_count": 0,
        "rook_blunder_count": 0,
        "stalemate_failure_count": 0,
        "failure_bucket_counts": {},
    }


def _select_schedule(schedules: dict[str, dict[str, Any]]) -> dict[str, Any]:
    candidates = list(schedules.values())
    return max(
        candidates,
        key=lambda row: (
            row["staged_any_reply_success_count"],
            row["frontier_reply_envelope_foundation_reachable_count"],
            -row["near_miss_false_positive_count"],
            row["generic_edge_fence_success_rate"],
            row["staged_s1_bridge_foundation_reachable_count"],
        ),
    )


def _required_ablations(graph, cache, mate2_cfg, tg28c_cfg, edge_cfg, frontier_heldout, generic_heldout, staged_heldout, edge_weights, bridge_weights, cfg):
    names = (
        "mask_edge_fence_terminals",
        "mask_bridge_pressure_terminals",
        "mask_foundation_response_terminals",
        "mask_action_delta_terminals",
        "mask_internal_attention_request_strength_terminals",
        "mask_safety_veto_terminals",
        "mask_actuator_terminals",
        "disable_reply_envelope_foundation_checks",
        "mask_frozen_mate1_foundation_quorum",
        "mask_frozen_mate2_foundation_quorum",
    )
    if cfg.max_ablation_positions <= 0:
        return {name: {"skipped": True, "skip_reason": "max_ablation_positions_zero"} for name in names}
    frontier_fens = tuple(frontier_heldout[: cfg.max_ablation_positions])
    generic_fens = tuple(generic_heldout[: cfg.max_ablation_positions])
    staged_examples = tuple(staged_heldout[: cfg.max_ablation_positions])
    bridge_masks = {
        "mask_edge_fence_terminals": {"mask_edge_fence_terminals": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_foundation_response_terminals": {"mask_frozen_foundation_response_terminals": True},
        "mask_action_delta_terminals": {"mask_action_delta_terminals": True},
        "mask_internal_attention_request_strength_terminals": {"mask_internal_attention_request_strength_terminals": True},
        "mask_safety_veto_terminals": {"mask_safety_veto_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "disable_reply_envelope_foundation_checks": {"disable_reply_envelope_foundation_checks": True},
        "mask_frozen_mate1_foundation_quorum": {"mask_frozen_mate1_foundation_quorum": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_frozen_mate2_foundation_quorum": True},
    }
    edge_masks = {
        "mask_edge_fence_terminals": {"mask_edge_fence_terminals": True},
        "mask_action_delta_terminals": {"mask_action_delta_terminals": True},
        "mask_internal_attention_request_strength_terminals": {"mask_internal_attention_terminals": True},
        "mask_safety_veto_terminals": {"mask_safety_veto_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "mask_frozen_mate1_foundation_quorum": {"mask_mate1_foundation_quorum": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_mate2_foundation_quorum": True},
    }
    return {
        name: {
            "frontier": _evaluate_cache_bridge_layer(graph, cache, frontier_fens, tg28c_cfg, edge_weights, bridge_weights, masks=bridge_mask),
            "generic": _evaluate_edge_layer(graph, generic_fens, mate2_cfg, edge_cfg, edge_weights, foundation_handoff_enabled=True, masks=edge_masks.get(name, {})),
            "staged": _evaluate_staged_rollout(
                graph,
                cache,
                mate2_cfg,
                tg28c_cfg,
                edge_cfg,
                staged_examples,
                edge_weights,
                bridge_weights,
                cfg,
                edge_masks=edge_masks.get(name, {}),
                bridge_masks=bridge_mask,
            ),
        }
        for name, bridge_mask in bridge_masks.items()
    }


def _decision(
    cfg,
    *,
    foundation_sanity,
    selected,
    schedules,
    equivalence,
    ablations,
    scheduler_equivalence,
    foundation_before_training,
    foundation_after_training,
    foundation_before_eval,
    foundation_after_eval,
    timings,
) -> dict[str, Any]:
    train_m3_delta = foundation_after_training["m3"] - foundation_before_training["m3"]
    train_m4_delta = foundation_after_training["m4"] - foundation_before_training["m4"]
    eval_m3_delta = foundation_after_eval["m3"] - foundation_before_eval["m3"]
    eval_m4_delta = foundation_after_eval["m4"] - foundation_before_eval["m4"]
    baseline = schedules.get("tg28h_mixed_balanced_baseline", selected)
    frontier_drop = 4 - selected["frontier_selected_count"]
    near_fp_increase = selected["near_miss_false_positive_count"]
    generic_drop = 1.0 - selected["generic_edge_fence_success_rate"]
    staged_gain = selected["staged_any_reply_success_count"] - baseline["staged_any_reply_success_count"]
    ablation_ok = True if cfg.max_ablation_positions <= 0 else (
        ablations["mask_actuator_terminals"]["staged"]["selected_first_move_count"] == 0
        and ablations["mask_edge_fence_terminals"]["generic"]["edge_fence_success_rate"] < selected["generic_edge_fence_success_rate"]
        and ablations["mask_bridge_pressure_terminals"]["frontier"]["selected_move_count"] < selected["frontier_selected_count"]
        and ablations["disable_reply_envelope_foundation_checks"]["frontier"]["selected_move_count"] < selected["frontier_selected_count"]
    )
    checkpoint_pass = (
        train_m3_delta == 0
        and train_m4_delta == 0
        and eval_m3_delta == 0
        and eval_m4_delta == 0
        and foundation_sanity["foundation_mate1_accuracy"] >= 1.0
        and foundation_sanity["foundation_mate2_conversion_rate"] >= 1.0
        and equivalence["foundation_cache_live_mismatch_count"] == 0
        and selected["frontier_selected_count"] > 0
        and selected["frontier_reply_envelope_foundation_reachable_count"] > 0
        and selected["near_miss_false_positive_count"] <= 1
        and selected["generic_edge_fence_success_rate"] >= 0.75
        and selected["generic_rook_blunder_count"] == 0
        and selected["generic_stalemate_avoidance_rate"] >= 1.0
        and selected["staged_any_reply_success_count"] > 0
        and selected["staged_rook_blunder_count"] == 0
        and selected["staged_stalemate_failure_count"] == 0
        and ablation_ok
        and scheduler_equivalence["mismatch_count"] == 0
    )
    return {
        "checkpoint_pass": checkpoint_pass,
        "checkpoint_interpretation": "short_staged_components_composed" if checkpoint_pass else _failed_interpretation(selected),
        "selected_training_schedule": selected["schedule_name"],
        "foundation_frozen": True,
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": equivalence["foundation_cache_live_mismatch_count"],
        "foundation_m3_updates_during_training": train_m3_delta,
        "foundation_m4_promotions_during_training": train_m4_delta,
        "foundation_m3_updates_during_eval": eval_m3_delta,
        "foundation_m4_promotions_during_eval": eval_m4_delta,
        "frontier_selected_count": selected["frontier_selected_count"],
        "frontier_heldout_count": selected["frontier_heldout_count"],
        "frontier_foundation_handoff_conversion_count": selected["frontier_foundation_handoff_conversion_count"],
        "frontier_same_graph_continuation_count": selected["frontier_same_graph_continuation_count"],
        "near_miss_selected_count": selected["near_miss_selected_count"],
        "near_miss_false_positive_count": selected["near_miss_false_positive_count"],
        "generic_selected_count": selected["generic_selected_count"],
        "generic_heldout_count": selected["generic_heldout_count"],
        "generic_edge_fence_success_rate": selected["generic_edge_fence_success_rate"],
        "generic_confinement_area_improvement_rate": selected["generic_confinement_area_improvement_rate"],
        "generic_black_king_mobility_reduction_rate": selected["generic_black_king_mobility_reduction_rate"],
        "generic_rook_blunder_count": selected["generic_rook_blunder_count"],
        "generic_stalemate_avoidance_rate": selected["generic_stalemate_avoidance_rate"],
        "staged_train_count": cfg.staged_train_count,
        "staged_heldout_count": selected["staged_heldout_count"],
        "staged_selected_first_move_count": selected["staged_selected_first_move_count"],
        "staged_first_move_edge_success_count": selected["staged_first_move_edge_success_count"],
        "staged_s1_bridge_selected_count": selected["staged_s1_bridge_selected_count"],
        "staged_s1_bridge_foundation_reachable_count": selected["staged_s1_bridge_foundation_reachable_count"],
        "staged_same_graph_foundation_continuation_count": selected["staged_same_graph_foundation_continuation_count"],
        "staged_foundation_handoff_conversion_count": selected["staged_foundation_handoff_conversion_count"],
        "staged_all_reply_success_count": selected["staged_all_reply_success_count"],
        "staged_partial_reply_success_count": selected["staged_partial_reply_success_count"],
        "staged_any_reply_success_count": selected["staged_any_reply_success_count"],
        "staged_null_count": selected["staged_null_count"],
        "staged_rook_blunder_count": selected["staged_rook_blunder_count"],
        "staged_stalemate_failure_count": selected["staged_stalemate_failure_count"],
        "frontier_drop_vs_TG28h": frontier_drop,
        "near_miss_false_positive_increase_vs_TG28h": near_fp_increase,
        "generic_edge_drop_vs_TG28h": generic_drop,
        "staged_rollout_success_vs_baseline": staged_gain,
        "failure_bucket_counts": selected["failure_bucket_counts"],
        "phase_timings": timings,
        "timeout_count": 0,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "edge_terminal_m3_update_count": selected["edge_terminal_m3_update_count"],
        "bridge_terminal_m3_update_count": selected["bridge_terminal_m3_update_count"],
        "shared_action_delta_update_count": selected["shared_action_delta_update_count"],
        "actuator_update_count": selected["actuator_update_count"],
        "m4_promotion_count_by_terminal_kind_edge_bridge_staged_only": {},
        "ablation_results": ablations,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _schedule_public(row, max_samples: int) -> dict[str, Any]:
    public = _tg28h_schedule_public(row, max_samples)
    public["staged"]["samples"] = public["staged"].get("samples", [])[:max_samples]
    return public


def _foundation_positive(entry: dict[str, Any]) -> bool:
    return bool(entry["foundation_mate1_recognized"] or entry["foundation_mate2_recognized"] or entry["foundation_chain_success"])


def _failed_interpretation(selected: dict[str, Any]) -> str:
    if selected["staged_heldout_count"] == 0:
        return "staged_examples_not_generated"
    if selected["staged_selected_first_move_count"] == 0:
        return "first_edge_move_not_selected"
    if selected["staged_s1_bridge_selected_count"] == 0:
        return "edge_moves_do_not_reach_graph_selected_bridge"
    if selected["staged_s1_bridge_foundation_reachable_count"] == 0:
        return "bridge_selected_without_frozen_foundation_reachability"
    if selected["near_miss_false_positive_count"] > 1:
        return "near_miss_false_positives_reintroduced"
    return "short_staged_rollout_failed_or_needs_more_pool_support"


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg28h_purity_boundary()
    boundary.update({
        "checkpoint": "TG28i",
        "short_staged_rollout": True,
        "foundation_frozen": True,
        "staged_generation_trainer_side_only": True,
        "final_runtime_choice_graph_mediated": True,
        "cache_used_as_memoized_frozen_graph_response": True,
        "cache_used_as_provider": False,
    })
    return boundary


def _write_progress(cfg: StagedEdgeBridgeFoundationRolloutConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
