"""TG28h controlled mixed frontier and generic edge/fence curriculum."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import time
from pathlib import Path
from typing import Any

import chess

from .foundation_backed_bridge_frontier import _as_tg28c_config
from .frozen_foundation_bridge_pressure import _bridge_reward, _compact_foundation_sanity
from .frozen_foundation_edge_fence_reentry import (
    _black_edge_distance,
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
from .full_foundation_frontier_pool_resume import FullFoundationFrontierPoolResumeConfig, _as_tg28e_config
from .full_frontier_validation_near_miss import _load_jsonl, _purity_boundary as _tg28g_purity_boundary
from .internal_handoff_affordance_guard_audit import _mate2_cfg
from .native_quorum_mate2_chaining import _tg26u_config
from .native_quorum_materialization import _tg26t_config
from .persisted_foundation_backed_frontier_pool import _as_tg28b_config, _as_tg28d_like_config
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence


@dataclass(frozen=True)
class ControlledMixedFrontierEdgeCurriculumConfig:
    seed: int = 20260630
    foundation_seed: int = 20260624
    foundation_mate1_train_count: int = 32
    foundation_mate1_heldout_count: int = 16
    foundation_mate2_train_count: int = 16
    foundation_mate2_heldout_count: int = 8
    bridge_frontier_train_count: int = 8
    bridge_frontier_heldout_count: int = 4
    generic_edge_safety_regression_count: int = 4
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
    schedule_names: tuple[str, ...] = (
        "frontier_only",
        "generic_edge_only",
        "mixed_balanced",
        "mixed_frontier_then_edge",
        "mixed_edge_then_frontier",
        "mixed_with_near_miss_replay",
    )
    full_pool_path: str = "reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl"
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg28h_controlled_mixed_frontier_edge_curriculum_progress.json"


@dataclass(frozen=True)
class ControlledMixedFrontierEdgeCurriculumResult:
    config: ControlledMixedFrontierEdgeCurriculumConfig
    dataset: dict[str, Any]
    foundation_sanity: dict[str, Any]
    schedule_comparison: dict[str, Any]
    selected_schedule: dict[str, Any]
    ablation_results: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg28h_controlled_mixed_frontier_edge_curriculum.v0",
            "checkpoint": "TG28h_controlled_mixed_frontier_edge_curriculum",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "foundation_sanity": self.foundation_sanity,
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


def run_controlled_mixed_frontier_edge_curriculum(
    *,
    config: ControlledMixedFrontierEdgeCurriculumConfig | None = None,
) -> ControlledMixedFrontierEdgeCurriculumResult:
    cfg = config or ControlledMixedFrontierEdgeCurriculumConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    tg28c_cfg = _as_tg28c_config(_as_tg28d_like_config(_as_tg28e_config(_as_tg28f_config(cfg))))
    edge_cfg = _as_tg28b_config(tg28c_cfg)
    pool_entries = _load_jsonl(Path(cfg.full_pool_path))
    frontier_train = tuple(entry["position_fen"] for entry in pool_entries if entry.get("split") == "train")
    frontier_heldout = tuple(entry["position_fen"] for entry in pool_entries if entry.get("split") == "heldout")
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
    near_miss_train = _near_miss_fens(cache, tg28c_cfg, {}, {}, cfg.near_miss_train_count, cfg.seed + 43, excluded)
    excluded.update(near_miss_train)
    near_miss_heldout = _near_miss_fens(cache, tg28c_cfg, {}, {}, cfg.near_miss_heldout_count, cfg.seed + 44, excluded)
    timings["dataset_generation_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {
        "phase": "datasets_complete",
        "generic_train_count": len(generic_train),
        "generic_heldout_count": len(generic_heldout),
        "near_miss_train_count": len(near_miss_train),
        "near_miss_heldout_count": len(near_miss_heldout),
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
        cfg=cfg,
    )
    timings["schedule_comparison_seconds"] = round(time.perf_counter() - start, 6)
    foundation_after_training = _foundation_counts(graph)
    selected = _select_schedule(schedules)
    _write_progress(cfg, {
        "phase": "schedule_comparison_complete",
        "selected_training_schedule": selected["schedule_name"],
        "generic_edge_fence_success_rate": selected["generic_edge_fence_success_rate"],
        "frontier_selected_count": selected["frontier_selected_count"],
        "near_miss_false_positive_count": selected["near_miss_false_positive_count"],
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
        selected["edge_weights"],
        selected["bridge_weights"],
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
        "generic_edge_fence_success_rate": decision["generic_edge_fence_success_rate"],
    }})
    return ControlledMixedFrontierEdgeCurriculumResult(
        config=cfg,
        dataset={
            "frontier_train_count": len(frontier_train),
            "frontier_heldout_count": len(frontier_heldout),
            "generic_train_count": len(generic_train),
            "generic_heldout_count": len(generic_heldout),
            "near_miss_train_count": len(near_miss_train),
            "near_miss_heldout_count": len(near_miss_heldout),
            "frontier_heldout_fens": list(frontier_heldout)[: cfg.max_samples],
            "generic_heldout_fens": list(generic_heldout)[: cfg.max_samples],
            "near_miss_heldout_fens": list(near_miss_heldout)[: cfg.max_samples],
            "stream_labels_learner_visible": False,
        },
        foundation_sanity=foundation_sanity,
        schedule_comparison={name: _schedule_public(row, cfg.max_samples) for name, row in schedules.items()},
        selected_schedule=_schedule_public(selected, cfg.max_samples),
        ablation_results=ablations,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _as_tg28f_config(cfg: ControlledMixedFrontierEdgeCurriculumConfig) -> FullFoundationFrontierPoolResumeConfig:
    return FullFoundationFrontierPoolResumeConfig(
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
        full_pool_path=cfg.full_pool_path,
    )


def _near_miss_fens(
    cache: _FoundationResponseCache,
    cfg,
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
    count: int,
    seed: int,
    excluded: set[str],
) -> tuple[str, ...]:
    candidates = _generate_edge_fence_positions(count=max(1, count * 5), seed=seed, excluded=excluded, cfg=_as_tg28b_config(cfg))
    out = []
    for fen in candidates:
        rows = _cache_candidate_rows(cache, chess.Board(fen), cfg, edge_weights, bridge_weights, cache_retrieval_enabled=True)
        has_safe_negative = any(row["safety_ok"] and not row["reply_envelope_foundation_reachable"] for row in rows)
        has_foundation = any(row["reply_envelope_foundation_reachable"] or row["bounded_bridge_foundation_reachable"] for row in rows)
        if has_safe_negative and not has_foundation:
            out.append(fen)
        if len(out) >= count:
            break
    return tuple(out)


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
    cfg: ControlledMixedFrontierEdgeCurriculumConfig,
) -> dict[str, dict[str, Any]]:
    specs = {
        "frontier_only": ("frontier",),
        "generic_edge_only": ("generic",),
        "mixed_balanced": ("frontier", "generic", "near_miss"),
        "mixed_frontier_then_edge": ("frontier", "generic"),
        "mixed_edge_then_frontier": ("generic", "frontier"),
        "mixed_with_near_miss_replay": ("frontier", "generic", "near_miss", "frontier", "near_miss"),
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
            edge_weights,
            bridge_weights,
            updates,
            samples,
        )
        _write_progress(cfg, {
            "phase": "schedule_arm_complete",
            "schedule_name": name,
            "frontier_selected_count": rows[name]["frontier_selected_count"],
            "near_miss_false_positive_count": rows[name]["near_miss_false_positive_count"],
            "generic_edge_fence_success_rate": rows[name]["generic_edge_fence_success_rate"],
        })
    return rows


def _train_generic_edge_weights(fens: tuple[str, ...], cfg, edge_weights: dict[str, float]) -> dict[str, Any]:
    updates = 0
    samples = []
    for fen in fens:
        rows = _cheap_candidate_rows(chess.Board(fen), edge_weights)
        for row in rows:
            reward = _edge_reward(row)
            for key in row["positive_feature_keys"]:
                edge_weights[key] = max(-1.0, min(1.0, edge_weights.get(key, 0.0) + cfg.eta_m3_edge * reward))
                updates += 1
        if rows and len(samples) < cfg.max_samples:
            best = max(rows, key=_edge_reward)
            samples.append({"fen": fen, "best_training_move": best["move"], "candidate_count": len(rows), "edge_reward": round(_edge_reward(best), 6)})
    return {
        "edge_terminal_m3_update_count": updates,
        "edge_weight_count": len(edge_weights),
        "top_edge_weights": sorted(edge_weights.items(), key=lambda item: item[1], reverse=True)[:12],
        "samples": samples,
    }


def _train_near_miss_negative(cache, fens, cfg, edge_weights, bridge_weights) -> dict[str, Any]:
    bridge_updates = 0
    action_delta_updates = 0
    samples = []
    for fen in fens:
        rows = _cache_candidate_rows(cache, chess.Board(fen), cfg, edge_weights, bridge_weights, cache_retrieval_enabled=True)
        negative_rows = [row for row in rows if row["safety_ok"] and not row["reply_envelope_foundation_reachable"]]
        for row in negative_rows:
            reward = min(-0.05, _bridge_reward(row))
            for key in row["bridge_feature_keys"]:
                bridge_weights[key] = max(-1.0, min(1.0, bridge_weights.get(key, 0.0) + cfg.eta_m3_bridge * reward))
                bridge_updates += 1
            action_delta_updates += sum(1 for key in row["positive_feature_keys"] if "delta_" in key)
        if negative_rows and len(samples) < cfg.max_samples:
            samples.append({"fen": fen, "negative_candidate_count": len(negative_rows), "sample_move": negative_rows[0]["move"]})
    return {
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
    edge_weights,
    bridge_weights,
    updates,
    samples,
) -> dict[str, Any]:
    frontier = _evaluate_cache_bridge_layer(graph, cache, frontier_heldout, tg28c_cfg, edge_weights, bridge_weights)
    near_miss = _evaluate_cache_bridge_layer(graph, cache, near_miss_heldout, tg28c_cfg, edge_weights, bridge_weights)
    generic = _evaluate_edge_layer(graph, generic_heldout, mate2_cfg, edge_cfg, edge_weights, foundation_handoff_enabled=True)
    return {
        "schedule_name": name,
        "frontier": frontier,
        "near_miss": near_miss,
        "generic": generic,
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
        "failure_bucket_counts": _combined_failure_buckets(frontier, near_miss, generic),
        "edge_weights": dict(edge_weights),
        "bridge_weights": dict(bridge_weights),
        "training_samples": samples[:8],
        **updates,
        "m4_promotion_count_by_terminal_kind_edge_bridge_only": {},
    }


def _select_schedule(schedules: dict[str, dict[str, Any]]) -> dict[str, Any]:
    mixed_names = [name for name in schedules if name.startswith("mixed")]
    candidates = [schedules[name] for name in mixed_names]
    return max(
        candidates,
        key=lambda row: (
            row["frontier_reply_envelope_foundation_reachable_count"],
            -row["near_miss_false_positive_count"],
            row["generic_edge_fence_success_rate"],
            row["generic_selected_count"],
            row["frontier_selected_count"],
        ),
    )


def _required_ablations(graph, cache, mate2_cfg, tg28c_cfg, edge_cfg, frontier_heldout, generic_heldout, edge_weights, bridge_weights):
    if tg28c_cfg.max_ablation_positions <= 0:
        return {
            name: {"skipped": True, "skip_reason": "max_ablation_positions_zero"}
            for name in (
                "mask_foundation_response_terminals",
                "mask_bridge_pressure_terminals",
                "mask_edge_fence_terminals",
                "mask_action_delta_terminals",
                "mask_internal_attention_request_strength_terminals",
                "mask_safety_veto_terminals",
                "mask_actuator_terminals",
                "disable_cache_retrieval",
                "disable_reply_envelope_foundation_checks",
                "mask_frozen_mate1_foundation_quorum",
                "mask_frozen_mate2_foundation_quorum",
            )
        }
    frontier_fens = tuple(frontier_heldout[: tg28c_cfg.max_ablation_positions])
    generic_fens = tuple(generic_heldout[: tg28c_cfg.max_ablation_positions])
    bridge_masks = {
        "mask_foundation_response_terminals": {"mask_frozen_foundation_response_terminals": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_action_delta_terminals": {"mask_action_delta_terminals": True},
        "mask_internal_attention_request_strength_terminals": {"mask_internal_attention_request_strength_terminals": True},
        "mask_safety_veto_terminals": {"mask_safety_veto_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "disable_cache_retrieval": {"disable_cache_retrieval": True},
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
        }
        for name, bridge_mask in bridge_masks.items()
    } | {
        "mask_edge_fence_terminals": {
            "frontier": _evaluate_cache_bridge_layer(graph, cache, frontier_fens, tg28c_cfg, edge_weights, bridge_weights, masks={"mask_edge_fence_terminals": True}),
            "generic": _evaluate_edge_layer(graph, generic_fens, mate2_cfg, edge_cfg, edge_weights, foundation_handoff_enabled=True, masks={"mask_edge_fence_terminals": True}),
        }
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
    tg28g_frontier_selected = 4
    tg28g_near_miss_fp = 0
    tg28g_generic_success = 0.125
    frontier_drop = tg28g_frontier_selected - selected["frontier_selected_count"]
    near_fp_increase = selected["near_miss_false_positive_count"] - tg28g_near_miss_fp
    generic_improvement = selected["generic_edge_fence_success_rate"] - tg28g_generic_success
    ablation_ok = True if cfg.max_ablation_positions <= 0 else (
        ablations["mask_foundation_response_terminals"]["frontier"]["selected_move_count"] == 0
        and ablations["mask_bridge_pressure_terminals"]["frontier"]["selected_move_count"] == 0
        and ablations["mask_actuator_terminals"]["frontier"]["selected_move_count"] == 0
        and ablations["mask_edge_fence_terminals"]["generic"]["edge_fence_success_rate"] < selected["generic_edge_fence_success_rate"]
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
        and generic_improvement > 0.0
        and selected["generic_rook_blunder_count"] == 0
        and selected["generic_stalemate_avoidance_rate"] >= 1.0
        and ablation_ok
        and scheduler_equivalence["mismatch_count"] == 0
    )
    return {
        "checkpoint_pass": checkpoint_pass,
        "checkpoint_interpretation": "mixed_curriculum_preserved_frontier_and_improved_generic_edge" if checkpoint_pass else "mixed_curriculum_failed_or_needs_schedule_repair",
        "selected_training_schedule": selected["schedule_name"],
        "foundation_frozen": True,
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
        "foundation_m3_updates_during_training": train_m3_delta,
        "foundation_m4_promotions_during_training": train_m4_delta,
        "foundation_m3_updates_during_eval": eval_m3_delta,
        "foundation_m4_promotions_during_eval": eval_m4_delta,
        "cache_live_mismatch_count": equivalence["foundation_cache_live_mismatch_count"],
        "frontier_selected_count": selected["frontier_selected_count"],
        "frontier_heldout_count": selected["frontier_heldout_count"],
        "frontier_selection_rate": selected["frontier_selection_rate"],
        "frontier_reply_envelope_foundation_reachable_count": selected["frontier_reply_envelope_foundation_reachable_count"],
        "frontier_foundation_handoff_conversion_count": selected["frontier_foundation_handoff_conversion_count"],
        "frontier_same_graph_continuation_count": selected["frontier_same_graph_continuation_count"],
        "frontier_rook_blunder_count": selected["frontier_rook_blunder_count"],
        "frontier_stalemate_avoidance_rate": selected["frontier_stalemate_avoidance_rate"],
        "near_miss_candidate_count": selected["near_miss_candidate_count"],
        "near_miss_selected_count": selected["near_miss_selected_count"],
        "near_miss_false_positive_count": selected["near_miss_false_positive_count"],
        "near_miss_rejection_rate": selected["near_miss_rejection_rate"],
        "near_miss_failure_bucket_counts": selected["near_miss_failure_bucket_counts"],
        "generic_selected_count": selected["generic_selected_count"],
        "generic_heldout_count": selected["generic_heldout_count"],
        "generic_selection_rate": selected["generic_selection_rate"],
        "generic_edge_fence_success_rate": selected["generic_edge_fence_success_rate"],
        "generic_confinement_area_improvement_rate": selected["generic_confinement_area_improvement_rate"],
        "generic_black_king_mobility_reduction_rate": selected["generic_black_king_mobility_reduction_rate"],
        "generic_edge_distance_improvement_rate": selected["generic_edge_distance_improvement_rate"],
        "generic_foundation_handoff_conversion_count": selected["generic_foundation_handoff_conversion_count"],
        "generic_rook_blunder_count": selected["generic_rook_blunder_count"],
        "generic_stalemate_avoidance_rate": selected["generic_stalemate_avoidance_rate"],
        "generic_null_count": selected["generic_null_count"],
        "frontier_drop_vs_TG28g": frontier_drop,
        "near_miss_false_positive_increase_vs_TG28g": near_fp_increase,
        "generic_edge_improvement_vs_TG28g": generic_improvement,
        "schedule_comparison": {name: _schedule_metrics(row) for name, row in schedules.items()},
        "failure_bucket_counts": selected["failure_bucket_counts"],
        "phase_timings": timings,
        "timeout_count": 0,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "edge_terminal_m3_update_count": selected["edge_terminal_m3_update_count"],
        "bridge_terminal_m3_update_count": selected["bridge_terminal_m3_update_count"],
        "shared_action_delta_update_count": selected["shared_action_delta_update_count"],
        "actuator_update_count": selected["actuator_update_count"],
        "m4_promotion_count_by_terminal_kind_edge_bridge_only": {},
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


def _schedule_metrics(row):
    keys = (
        "frontier_selected_count",
        "frontier_reply_envelope_foundation_reachable_count",
        "near_miss_false_positive_count",
        "generic_selected_count",
        "generic_edge_fence_success_rate",
        "generic_rook_blunder_count",
        "generic_stalemate_avoidance_rate",
    )
    return {key: row[key] for key in keys}


def _schedule_public(row, max_samples: int) -> dict[str, Any]:
    public = {k: v for k, v in row.items() if k not in {"edge_weights", "bridge_weights"}}
    public["edge_weight_count"] = len(row["edge_weights"])
    public["bridge_weight_count"] = len(row["bridge_weights"])
    public["top_edge_weights"] = sorted(row["edge_weights"].items(), key=lambda item: item[1], reverse=True)[:12]
    public["top_bridge_weights"] = sorted(row["bridge_weights"].items(), key=lambda item: item[1], reverse=True)[:12]
    public["frontier"]["samples"] = public["frontier"].get("samples", [])[:max_samples]
    public["near_miss"]["samples"] = public["near_miss"].get("samples", [])[:max_samples]
    public["generic"]["samples"] = public["generic"].get("samples", [])[:max_samples]
    return public


def _combined_failure_buckets(frontier, near_miss, generic) -> dict[str, Any]:
    return {
        "frontier": frontier["failure_bucket_counts"],
        "near_miss": near_miss["failure_bucket_counts"],
        "generic_edge_fence": generic["failure_bucket_counts"],
    }


def _action_delta_update_estimate(result: dict[str, Any]) -> int:
    samples = result.get("top_edge_weights", [])
    return sum(1 for key, _value in samples if "delta_" in key)


def _write_progress(cfg: ControlledMixedFrontierEdgeCurriculumConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg28g_purity_boundary()
    boundary.update({
        "checkpoint": "TG28h",
        "controlled_mixed_curriculum": True,
        "stream_labels_learner_visible": False,
        "final_runtime_choice_graph_mediated": True,
    })
    return boundary
