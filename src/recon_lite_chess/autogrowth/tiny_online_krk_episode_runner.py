"""TG29a tiny online KRK episode runner."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import chess

from .foundation_backed_bridge_frontier import _as_tg28c_config
from .frozen_foundation_bridge_pressure import _compact_foundation_sanity
from .frozen_foundation_edge_fence_reentry import (
    _build_tg27b_foundation,
    _evaluate_edge_layer,
    _foundation_counts,
    _generate_edge_fence_positions,
)
from .frozen_foundation_response_cache_bridge_retrieval import (
    _FoundationResponseCache,
    _evaluate_cache_bridge_layer,
    _train_cache_bridge_layer,
)
from .full_frontier_validation_near_miss import _load_jsonl
from .internal_handoff_affordance_guard_audit import _mate2_cfg
from .native_quorum_mate2_chaining import _tg26u_config
from .native_quorum_materialization import _tg26t_config
from .persisted_foundation_backed_frontier_pool import _as_tg28b_config, _as_tg28d_like_config
from .persisted_staged_predecessor_pool import (
    PersistedStagedPredecessorPoolConfig,
    _as_tg28i_config,
    _entries_by_split,
    _examples_from_entries,
    _load_pool_entries,
)
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .staged_edge_bridge_foundation_rollout import (
    _as_tg28f_config,
    _as_tg28h_config,
    _evaluate_staged_rollout,
    _required_ablations,
    _run_schedule_comparison,
    _select_schedule,
    _train_generic_edge_weights,
)


@dataclass(frozen=True)
class TinyOnlineKRKEpisodeRunnerConfig:
    seed: int = 20260703
    episode_count: int = 4
    max_white_moves_per_episode: int = 4
    black_reply_policy: str = "deterministic_worst_foundation_reply"
    foundation_seed: int = 20260624
    foundation_mate1_train_count: int = 32
    foundation_mate1_heldout_count: int = 16
    foundation_mate2_train_count: int = 16
    foundation_mate2_heldout_count: int = 8
    bridge_frontier_train_count: int = 2
    bridge_frontier_heldout_count: int = 1
    generic_edge_train_count: int = 4
    generic_edge_heldout_count: int = 2
    staged_train_count: int = 8
    staged_heldout_count: int = 4
    staged_regression_count: int = 4
    staged_near_miss_count: int = 8
    near_miss_heldout_count: int = 8
    max_ablation_positions: int = 1
    max_foundation_sanity_positions: int = 1
    max_foundation_ablation_positions: int = 1
    max_samples: int = 16
    max_episode_ablation_count: int = 1
    schedule_names: tuple[str, ...] = (
        "tg28h_mixed_balanced_baseline",
        "mixed_balanced_plus_staged",
        "staged_first_then_mixed_replay",
        "mixed_first_then_staged",
        "mixed_staged_near_miss_replay",
    )
    repaired_high_recall_threshold: float = 0.018
    full_pool_path: str = "reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl"
    staged_pool_path: str = "reports/autogrowth/pools/tg28l_staged_predecessor_pool.jsonl"
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg29a_tiny_online_krk_episode_runner_progress.json"


@dataclass(frozen=True)
class TinyOnlineKRKEpisodeRunnerResult:
    config: TinyOnlineKRKEpisodeRunnerConfig
    foundation_sanity: dict[str, Any]
    regression_slices: dict[str, Any]
    episodes: dict[str, Any]
    ablation_results: dict[str, Any]
    foundation_cache_equivalence: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29a_tiny_online_krk_episode_runner.v0",
            "checkpoint": "TG29a_tiny_online_krk_episode_runner",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "foundation_sanity": self.foundation_sanity,
            "regression_slices": self.regression_slices,
            "episodes": self.episodes,
            "ablation_results": self.ablation_results,
            "foundation_cache_equivalence": self.foundation_cache_equivalence,
            "scheduler_equivalence": self.scheduler_equivalence,
            "phase_timings": self.phase_timings,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output

    def write_markdown(self, path: str | Path) -> Path:
        decision = self.decision
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "\n".join(
                [
                    "# TG29a Tiny Online KRK Episode Runner",
                    "",
                    f"- checkpoint_pass: `{decision['checkpoint_pass']}`",
                    f"- interpretation: `{decision['checkpoint_interpretation']}`",
                    f"- episodes: `{decision['episode_count']}`",
                    f"- episode success: `{decision['episode_success_count']}` / `{decision['episode_count']}`",
                    f"- foundation handoffs: `{decision['foundation_handoff_count']}`",
                    f"- rook blunders / illegal / stalemate: `{decision['rook_blunder_count']}` / `{decision['illegal_move_count']}` / `{decision['stalemate_count']}`",
                    f"- edge->bridge transitions: `{decision['transition_edge_to_bridge_count']}`",
                    f"- bridge->foundation transitions: `{decision['transition_bridge_to_foundation_count']}`",
                    f"- selected schedule: `{self.regression_slices['selected_schedule_name']}`",
                    "",
                    "Interpretation: TG29a is an online integration test over existing graph-mediated components, not broad KRK competence.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_tiny_online_krk_episode_runner(
    *,
    config: TinyOnlineKRKEpisodeRunnerConfig | None = None,
) -> TinyOnlineKRKEpisodeRunnerResult:
    cfg = config or TinyOnlineKRKEpisodeRunnerConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})
    context = _build_context(cfg)
    timings.update(context["timings"])
    _write_progress(cfg, {"phase": "context_built", "selected_schedule": context["selected"]["schedule_name"]})

    graph = context["graph"]
    cache = context["cache"]
    foundation_before_episode = _foundation_counts(graph)
    start = time.perf_counter()
    episode_starts = _episode_starts(cfg, context)
    episodes = _run_episodes(
        graph,
        cache,
        context["mate2_cfg"],
        context["tg28c_cfg"],
        context["edge_cfg"],
        episode_starts,
        context["selected"]["edge_weights"],
        context["selected"]["bridge_weights"],
        cfg,
    )
    foundation_after_episode = _foundation_counts(graph)
    timings["episode_eval_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "episodes_complete", "episode_success_count": episodes["episode_success_count"]})

    start = time.perf_counter()
    ablations = _episode_ablations(
        graph,
        cache,
        context,
        episode_starts[: max(1, cfg.max_episode_ablation_count)],
        cfg,
    )
    timings["episode_ablation_seconds"] = round(time.perf_counter() - start, 6)
    foundation_cache_equivalence = cache.live_equivalence_audit(max_samples=min(8, cfg.max_samples))
    scheduler_equivalence = _scheduler_equivalence(
        _tg26s_config(_tg26t_config(_tg26u_config(context["mate2_cfg"]))),
        context["mate1_train"],
        context["mate1_heldout"],
    )
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)

    decision = _decision(
        cfg,
        foundation_sanity=context["foundation_sanity"],
        regression=context["regression"],
        episodes=episodes,
        ablations=ablations,
        foundation_cache_equivalence=foundation_cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        foundation_before_episode=foundation_before_episode,
        foundation_after_episode=foundation_after_episode,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return TinyOnlineKRKEpisodeRunnerResult(
        config=cfg,
        foundation_sanity=context["foundation_sanity"],
        regression_slices=context["regression"],
        episodes=episodes,
        ablation_results=ablations,
        foundation_cache_equivalence=foundation_cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _build_context(cfg: TinyOnlineKRKEpisodeRunnerConfig) -> dict[str, Any]:
    timings: dict[str, float] = {}
    pool_cfg = _pool_cfg(cfg)
    tg28i_cfg = _as_tg28i_config(pool_cfg)
    tg28c_cfg = _as_tg28c_config(_as_tg28d_like_config(_as_tg28f_config(_as_tg28h_config(tg28i_cfg))))
    edge_cfg = _as_tg28b_config(tg28c_cfg)

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

    full_pool = _load_jsonl(Path(cfg.full_pool_path))
    frontier_train = tuple(entry["position_fen"] for entry in full_pool if entry.get("split") == "train")[: cfg.bridge_frontier_train_count]
    frontier_heldout = tuple(entry["position_fen"] for entry in full_pool if entry.get("split") == "heldout")[: cfg.bridge_frontier_heldout_count]
    excluded = set(frontier_train + frontier_heldout)
    generic_train = _generate_edge_fence_positions(count=cfg.generic_edge_train_count, seed=cfg.seed + 41, excluded=excluded, cfg=edge_cfg)
    excluded.update(generic_train)
    generic_heldout = _generate_edge_fence_positions(count=cfg.generic_edge_heldout_count, seed=cfg.seed + 42, excluded=excluded, cfg=edge_cfg)

    start = time.perf_counter()
    seed_edge_weights: dict[str, float] = {}
    seed_bridge_weights: dict[str, float] = {}
    _train_cache_bridge_layer(cache, frontier_train, tg28c_cfg, seed_edge_weights, seed_bridge_weights)
    _train_generic_edge_weights(generic_train, edge_cfg, seed_edge_weights)
    staged_entries = _load_pool_entries(Path(cfg.staged_pool_path))
    by_split = _entries_by_split(staged_entries)
    staged_train = _examples_from_entries(by_split["train"])
    staged_heldout = _examples_from_entries(by_split["heldout"])
    near_miss_heldout = tuple(entry["s1_fen"] for entry in by_split["near_miss"][: cfg.near_miss_heldout_count])
    timings["dataset_seconds"] = round(time.perf_counter() - start, 6)

    before_training = _foundation_counts(graph)
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
        near_miss_train=tuple(),
        near_miss_heldout=near_miss_heldout,
        staged_train=staged_train,
        staged_heldout=staged_heldout,
        cfg=tg28i_cfg,
    )
    selected = _select_schedule(schedules)
    after_training = _foundation_counts(graph)
    timings["schedule_comparison_seconds"] = round(time.perf_counter() - start, 6)
    start = time.perf_counter()
    regression = {
        "selected_schedule_name": selected["schedule_name"],
        "frontier": selected["frontier"],
        "staged": selected["staged"],
        "staged_near_miss": selected["near_miss"],
        "generic": selected["generic"],
        "foundation_training_deltas": {
            "m3": after_training["m3"] - before_training["m3"],
            "m4": after_training["m4"] - before_training["m4"],
        },
    }
    regression["ablations"] = _required_ablations(
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
        tg28i_cfg,
    )
    timings["regression_ablation_seconds"] = round(time.perf_counter() - start, 6)
    return {
        "graph": graph,
        "cache": cache,
        "mate2_cfg": mate2_cfg,
        "tg28c_cfg": tg28c_cfg,
        "edge_cfg": edge_cfg,
        "foundation_sanity": foundation_sanity,
        "regression": regression,
        "selected": selected,
        "frontier_heldout": frontier_heldout,
        "generic_heldout": generic_heldout,
        "staged_heldout": staged_heldout,
        "near_miss_heldout": near_miss_heldout,
        "mate1_train": mate1_train,
        "mate1_heldout": mate1_heldout,
        "mate2_heldout": mate2_heldout,
        "timings": timings,
    }


def _pool_cfg(cfg: TinyOnlineKRKEpisodeRunnerConfig) -> PersistedStagedPredecessorPoolConfig:
    return PersistedStagedPredecessorPoolConfig(
        seed=cfg.seed,
        foundation_seed=cfg.foundation_seed,
        foundation_mate1_train_count=cfg.foundation_mate1_train_count,
        foundation_mate1_heldout_count=cfg.foundation_mate1_heldout_count,
        foundation_mate2_train_count=cfg.foundation_mate2_train_count,
        foundation_mate2_heldout_count=cfg.foundation_mate2_heldout_count,
        bridge_frontier_train_count=cfg.bridge_frontier_train_count,
        bridge_frontier_heldout_count=cfg.bridge_frontier_heldout_count,
        generic_edge_train_count=cfg.generic_edge_train_count,
        generic_edge_heldout_count=cfg.generic_edge_heldout_count,
        staged_train_count=cfg.staged_train_count,
        staged_heldout_count=cfg.staged_heldout_count,
        staged_regression_count=cfg.staged_regression_count,
        staged_near_miss_count=cfg.staged_near_miss_count,
        near_miss_heldout_count=cfg.near_miss_heldout_count,
        max_ablation_positions=cfg.max_ablation_positions,
        max_foundation_sanity_positions=cfg.max_foundation_sanity_positions,
        max_foundation_ablation_positions=cfg.max_foundation_ablation_positions,
        max_samples=cfg.max_samples,
        repaired_high_recall_threshold=cfg.repaired_high_recall_threshold,
        schedule_names=cfg.schedule_names,
        full_pool_path=cfg.full_pool_path,
        staged_pool_path=cfg.staged_pool_path,
        progress_output=cfg.progress_output,
    )


def _episode_starts(cfg: TinyOnlineKRKEpisodeRunnerConfig, context: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    starts: list[dict[str, Any]] = []
    for example in context["staged_heldout"][:2]:
        starts.append({"start_fen": example["fen"], "source": "tg28l_staged_heldout"})
    for fen in context["frontier_heldout"][:1]:
        starts.append({"start_fen": fen, "source": "tg28f_frontier_heldout"})
    for fen in context["mate2_heldout"][:1]:
        starts.append({"start_fen": fen, "source": "tg27b_foundation_heldout"})
    return tuple(starts[: cfg.episode_count])


def _run_episodes(
    graph,
    cache: _FoundationResponseCache,
    mate2_cfg,
    tg28c_cfg,
    edge_cfg,
    starts: tuple[dict[str, Any], ...],
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
    cfg: TinyOnlineKRKEpisodeRunnerConfig,
    *,
    masks: dict[str, bool] | None = None,
) -> dict[str, Any]:
    masks = masks or {}
    traces = []
    totals = _empty_episode_totals()
    for episode_index, start in enumerate(starts):
        board = chess.Board(start["start_fen"])
        episode = {
            "episode_index": episode_index,
            "start_fen": start["start_fen"],
            "source": start["source"],
            "black_reply_policy": cfg.black_reply_policy,
            "steps": [],
            "termination_reason": None,
        }
        previous_phase = None
        for move_index in range(cfg.max_white_moves_per_episode):
            if board.is_checkmate():
                episode["termination_reason"] = "checkmate"
                break
            if board.is_stalemate():
                episode["termination_reason"] = "stalemate"
                totals["stalemate_count"] += 1
                break
            if board.turn != chess.WHITE:
                episode["termination_reason"] = "not_white_to_move"
                break
            selection = _select_online_move(graph, cache, mate2_cfg, tg28c_cfg, edge_cfg, board, edge_weights, bridge_weights, masks=masks)
            phase = selection["diagnostic_phase_classification"]
            if previous_phase is not None:
                totals["transition_counts"][(previous_phase, phase)] += 1
            previous_phase = phase
            totals["phase_counts"][phase] += 1
            step = {
                "move_index": move_index,
                "white_to_move_fen": board.fen(),
                **selection,
            }
            move_uci = selection["selected_white_move"]
            if move_uci is None:
                totals["null_move_count"] += 1
                episode["termination_reason"] = "no_move_selected"
                step["termination_reason"] = "no_move_selected"
                episode["steps"].append(step)
                break
            move = chess.Move.from_uci(move_uci)
            if move not in board.legal_moves:
                totals["illegal_move_count"] += 1
                episode["termination_reason"] = "illegal_move_selected"
                step["termination_reason"] = "illegal_move_selected"
                episode["steps"].append(step)
                break
            board.push(move)
            step["after_white_move_fen"] = board.fen()
            safety = _safety_result(board)
            step["safety_result"] = safety
            totals["rook_blunder_count"] += int(safety["rook_blunder"])
            totals["unsafe_move_count"] += int(not safety["safe"])
            if board.is_checkmate():
                totals["checkmate_count"] += 1
                episode["termination_reason"] = "checkmate"
                step["termination_reason"] = "checkmate"
                episode["steps"].append(step)
                break
            if board.is_stalemate():
                totals["stalemate_count"] += 1
                episode["termination_reason"] = "stalemate"
                step["termination_reason"] = "stalemate"
                episode["steps"].append(step)
                break
            if safety["rook_blunder"]:
                episode["termination_reason"] = "unsafe_rook_blunder"
                step["termination_reason"] = "unsafe_rook_blunder"
                episode["steps"].append(step)
                break
            after_white_foundation = cache.query_state(board) if board.turn == chess.WHITE else {"foundation_selected_move": None, "foundation_mate1_recognized": False, "foundation_mate2_recognized": False, "foundation_chain_success": False}
            step["foundation_reachable_after_move"] = _foundation_reachable(after_white_foundation)
            black_reply = _select_black_reply(cache, board, cfg.black_reply_policy)
            step["black_reply"] = None if black_reply is None else black_reply.uci()
            if black_reply is not None:
                board.push(black_reply)
            step["after_black_reply_fen"] = board.fen()
            after_black_foundation = cache.query_state(board)
            step["foundation_reachable_after_black_reply"] = _foundation_reachable(after_black_foundation)
            step["foundation_after_black_reply"] = _compact_foundation_state(after_black_foundation)
            if _foundation_reachable(after_black_foundation):
                totals["foundation_handoff_count"] += 1
                episode["termination_reason"] = "foundation_handoff"
                step["termination_reason"] = "foundation_handoff"
                episode["steps"].append(step)
                break
            step["termination_reason"] = None
            episode["steps"].append(step)
        if episode["termination_reason"] is None:
            episode["termination_reason"] = "max_moves_reached"
            totals["max_move_reached_count"] += 1
        totals["episode_count"] += 1
        totals["white_move_count"] += len(episode["steps"])
        success = episode["termination_reason"] in {"checkmate", "foundation_handoff"}
        totals["episode_success_count"] += int(success)
        totals["failure_bucket_counts"][_episode_failure_bucket(episode)] += 1
        traces.append(episode)
    return _finalize_episodes(totals, traces)


def _select_online_move(graph, cache, mate2_cfg, tg28c_cfg, edge_cfg, board, edge_weights, bridge_weights, *, masks: dict[str, bool]) -> dict[str, Any]:
    foundation = cache.query_state(board)
    foundation_reachable = _foundation_reachable(foundation) and not masks.get("mask_frozen_mate2_foundation_quorum", False)
    bridge_eval = _evaluate_cache_bridge_layer(graph, cache, (board.fen(),), tg28c_cfg, edge_weights, bridge_weights, masks=_bridge_masks(masks))
    edge_eval = _evaluate_edge_layer(graph, (board.fen(),), mate2_cfg, edge_cfg, edge_weights, foundation_handoff_enabled=True, masks=_edge_masks(masks))
    bridge_selected = bridge_eval["samples"][0].get("selected") if bridge_eval.get("samples") else None
    edge_selected = edge_eval["samples"][0].get("selected") if edge_eval.get("samples") else None
    candidates = []
    if foundation_reachable and foundation.get("foundation_selected_move") in {move.uci() for move in board.legal_moves}:
        candidates.append(("foundation_move", foundation["foundation_selected_move"], 2.0, foundation))
    if bridge_selected is not None:
        candidates.append(("bridge_move", bridge_selected["move"], 1.0 + float(bridge_selected.get("evidence_score", 0.0)), bridge_selected))
    if edge_selected is not None:
        candidates.append(("edge_fence_move", edge_selected["move"], float(edge_selected.get("evidence_score", 0.0)), edge_selected))
    if not candidates:
        return {
            "selected_white_move": None,
            "diagnostic_phase_classification": "unsafe_or_unknown",
            "graph_evidence_summary": {
                "foundation": _compact_foundation_state(foundation),
                "bridge": _compact_eval(bridge_eval),
                "edge_fence": _compact_eval(edge_eval),
            },
            "formal_recon_engine_confirmation_state": "FAILED",
        }
    phase, move, score, selected = max(candidates, key=lambda item: (item[2], item[1]))
    if phase != "foundation_move" and foundation_reachable:
        phase = "mixed_evidence_move"
    return {
        "selected_white_move": move,
        "diagnostic_phase_classification": phase,
        "graph_evidence_summary": {
            "selected_score": round(score, 6),
            "foundation": _compact_foundation_state(foundation),
            "bridge": _compact_eval(bridge_eval),
            "edge_fence": _compact_eval(edge_eval),
            "selected_component": _compact_component(selected),
        },
        "formal_recon_engine_confirmation_state": selected.get("graph_confirmation_state", "CONFIRMED") if isinstance(selected, dict) else "CONFIRMED",
        "same_graph_foundation_continuation_count": int(selected.get("same_graph_foundation_continuation_count", foundation.get("same_graph_second_move_count", 0))) if isinstance(selected, dict) else 0,
    }


def _bridge_masks(masks: dict[str, bool]) -> dict[str, bool]:
    return {
        "mask_bridge_pressure_terminals": masks.get("mask_bridge_pressure_terminals", False),
        "mask_frozen_foundation_response_terminals": masks.get("mask_foundation_response_terminals", False),
        "mask_internal_attention_request_strength_terminals": masks.get("mask_internal_attention_request_strength_terminals", False),
        "disable_reply_envelope_foundation_checks": masks.get("disable_reply_envelope_foundation_checks", False),
        "mask_frozen_mate1_foundation_quorum": masks.get("mask_frozen_mate1_foundation_quorum", False),
        "mask_frozen_mate2_foundation_quorum": masks.get("mask_frozen_mate2_foundation_quorum", False),
        "mask_actuator_terminals": masks.get("mask_actuator_terminals", False),
    }


def _edge_masks(masks: dict[str, bool]) -> dict[str, bool]:
    return {
        "mask_edge_fence_terminals": masks.get("mask_edge_fence_terminals", False),
        "mask_action_delta_terminals": masks.get("mask_action_delta_terminals", False),
        "mask_internal_attention_terminals": masks.get("mask_internal_attention_request_strength_terminals", False),
        "mask_safety_veto_terminals": masks.get("mask_safety_veto_terminals", False),
        "mask_actuator_terminals": masks.get("mask_actuator_terminals", False),
        "mask_mate2_foundation_quorum": masks.get("mask_frozen_mate2_foundation_quorum", False),
    }


def _select_black_reply(cache: _FoundationResponseCache, board: chess.Board, policy: str) -> chess.Move | None:
    if board.turn != chess.BLACK or board.is_game_over():
        return None
    replies = sorted(board.legal_moves, key=lambda item: item.uci())
    if not replies:
        return None
    if policy == "mobility_maximizing":
        ranked = []
        for reply in replies:
            after = board.copy(stack=False)
            after.push(reply)
            mobility = len(list(after.legal_moves)) if after.turn == chess.WHITE else 0
            ranked.append((mobility, reply.uci(), reply))
        return sorted(ranked, key=lambda item: (item[0], item[1]), reverse=True)[0][2]
    if policy == "fixed_seed_random":
        key = hashlib.sha256(board.fen().encode("utf-8")).hexdigest()
        return replies[int(key[:8], 16) % len(replies)]
    if policy != "deterministic_worst_foundation_reply":
        return replies[0]
    ranked = []
    for reply in replies:
        after = board.copy(stack=False)
        after.push(reply)
        state = cache.query_state(after)
        ranked.append((int(_foundation_reachable(state)), reply.uci(), reply))
    return sorted(ranked, key=lambda item: (item[0], item[1]))[0][2]


def _episode_ablations(graph, cache, context, starts, cfg) -> dict[str, Any]:
    masks = {
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "mask_edge_fence_terminals": {"mask_edge_fence_terminals": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_foundation_response_terminals": {"mask_foundation_response_terminals": True},
        "disable_reply_envelope_foundation_checks": {"disable_reply_envelope_foundation_checks": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_frozen_mate2_foundation_quorum": True},
    }
    if cfg.max_episode_ablation_count <= 0:
        return {name: {"skipped": True, "skip_reason": "max_episode_ablation_count_zero"} for name in masks}
    out = {}
    for name, mask in masks.items():
        out[name] = _run_episodes(
            graph,
            cache,
            context["mate2_cfg"],
            context["tg28c_cfg"],
            context["edge_cfg"],
            starts,
            context["selected"]["edge_weights"],
            context["selected"]["bridge_weights"],
            cfg,
            masks=mask,
        )
    return out


def _empty_episode_totals() -> dict[str, Any]:
    return {
        "episode_count": 0,
        "episode_success_count": 0,
        "checkmate_count": 0,
        "foundation_handoff_count": 0,
        "max_move_reached_count": 0,
        "illegal_move_count": 0,
        "null_move_count": 0,
        "rook_blunder_count": 0,
        "stalemate_count": 0,
        "unsafe_move_count": 0,
        "white_move_count": 0,
        "phase_counts": Counter(),
        "transition_counts": Counter(),
        "failure_bucket_counts": Counter(),
    }


def _finalize_episodes(totals: dict[str, Any], traces: list[dict[str, Any]]) -> dict[str, Any]:
    n = max(1, totals["episode_count"])
    phase_sequences = Counter(tuple(step["diagnostic_phase_classification"] for step in episode["steps"]) for episode in traces)
    same_graph = sum(int(step.get("same_graph_foundation_continuation_count", 0)) for episode in traces for step in episode["steps"])
    return {
        "episode_count": totals["episode_count"],
        "episode_success_count": totals["episode_success_count"],
        "episode_success_rate": totals["episode_success_count"] / n,
        "checkmate_count": totals["checkmate_count"],
        "foundation_handoff_count": totals["foundation_handoff_count"],
        "max_move_reached_count": totals["max_move_reached_count"],
        "illegal_move_count": totals["illegal_move_count"],
        "null_move_count": totals["null_move_count"],
        "rook_blunder_count": totals["rook_blunder_count"],
        "stalemate_count": totals["stalemate_count"],
        "unsafe_move_count": totals["unsafe_move_count"],
        "average_white_moves_per_episode": totals["white_move_count"] / n,
        "edge_fence_move_count": totals["phase_counts"]["edge_fence_move"],
        "bridge_move_count": totals["phase_counts"]["bridge_move"],
        "foundation_move_count": totals["phase_counts"]["foundation_move"],
        "mixed_evidence_move_count": totals["phase_counts"]["mixed_evidence_move"],
        "same_graph_foundation_continuation_count": same_graph,
        "transition_edge_to_bridge_count": totals["transition_counts"][("edge_fence_move", "bridge_move")],
        "transition_bridge_to_foundation_count": totals["transition_counts"][("bridge_move", "foundation_move")],
        "transition_edge_to_foundation_count": totals["transition_counts"][("edge_fence_move", "foundation_move")],
        "phase_sequence_counts": {" -> ".join(key): value for key, value in phase_sequences.items()},
        "episode_failure_bucket_counts": dict(totals["failure_bucket_counts"]),
        "traces": traces,
    }


def _decision(cfg, *, foundation_sanity, regression, episodes, ablations, foundation_cache_equivalence, scheduler_equivalence, foundation_before_episode, foundation_after_episode, timings) -> dict[str, Any]:
    m3_delta = foundation_after_episode["m3"] - foundation_before_episode["m3"]
    m4_delta = foundation_after_episode["m4"] - foundation_before_episode["m4"]
    frontier = regression["frontier"]
    staged = regression["staged"]
    near_miss = regression["staged_near_miss"]
    generic = regression["generic"]
    frontier_pass = frontier["selected_move_count"] > 0 and frontier["foundation_handoff_conversion_count"] > 0
    staged_pass = staged["any_reply_success_count"] > 0
    near_miss_pass = near_miss["selected_move_count"] == 0
    generic_pass = generic["edge_fence_success_rate"] > 0.0 and generic["rook_blunder_count"] == 0 and generic["stalemate_avoidance_rate"] >= 1.0
    composition = (
        episodes["transition_edge_to_bridge_count"] > 0
        or episodes["transition_bridge_to_foundation_count"] > 0
        or episodes["transition_edge_to_foundation_count"] > 0
        or episodes["foundation_handoff_count"] > 0
    )
    safety_clean = episodes["rook_blunder_count"] == 0 and episodes["illegal_move_count"] == 0 and episodes["stalemate_count"] == 0
    checkpoint_pass = (
        m3_delta == 0
        and m4_delta == 0
        and foundation_sanity["foundation_mate1_accuracy"] >= 1.0
        and foundation_sanity["foundation_mate2_conversion_rate"] >= 1.0
        and foundation_cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
        and composition
        and safety_clean
        and frontier_pass
        and staged_pass
        and near_miss_pass
        and generic_pass
    )
    return {
        "checkpoint_pass": checkpoint_pass,
        "checkpoint_interpretation": "tiny_online_components_compose_safely" if checkpoint_pass else "tiny_online_episode_needs_transition_or_safety_repair",
        "foundation_frozen": m3_delta == 0 and m4_delta == 0,
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": foundation_cache_equivalence["foundation_cache_live_mismatch_count"],
        "foundation_m3_updates_during_episode_eval": m3_delta,
        "foundation_m4_promotions_during_episode_eval": m4_delta,
        **{key: episodes[key] for key in (
            "episode_count", "episode_success_count", "episode_success_rate", "checkmate_count", "foundation_handoff_count",
            "max_move_reached_count", "illegal_move_count", "null_move_count", "rook_blunder_count", "stalemate_count",
            "unsafe_move_count", "average_white_moves_per_episode", "edge_fence_move_count", "bridge_move_count",
            "foundation_move_count", "mixed_evidence_move_count", "transition_edge_to_bridge_count", "transition_bridge_to_foundation_count",
            "transition_edge_to_foundation_count", "same_graph_foundation_continuation_count", "episode_failure_bucket_counts", "phase_sequence_counts",
        )},
        "frontier_regression_pass": frontier_pass,
        "staged_regression_pass": staged_pass,
        "near_miss_regression_pass": near_miss_pass,
        "generic_edge_regression_pass": generic_pass,
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "ablation_results": {name: _ablation_summary(row) for name, row in ablations.items()},
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
        "staged_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _ablation_summary(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("skipped", False):
        return dict(row)
    return {key: row[key] for key in (
        "episode_count",
        "episode_success_count",
        "foundation_handoff_count",
        "null_move_count",
        "edge_fence_move_count",
        "bridge_move_count",
        "foundation_move_count",
        "transition_edge_to_bridge_count",
        "transition_bridge_to_foundation_count",
        "episode_failure_bucket_counts",
    )}


def _foundation_reachable(state: dict[str, Any]) -> bool:
    return bool(state.get("foundation_mate1_recognized") or state.get("foundation_mate2_recognized") or state.get("foundation_chain_success"))


def _compact_foundation_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "recognized": _foundation_reachable(state),
        "selected_move": state.get("foundation_selected_move"),
        "mate1": state.get("foundation_mate1_recognized"),
        "mate2": state.get("foundation_mate2_recognized"),
        "chain": state.get("foundation_chain_success"),
        "confirmation_state": state.get("graph_confirmation_state"),
        "same_graph_second_move_count": state.get("same_graph_second_move_count", 0),
    }


def _compact_eval(eval_row: dict[str, Any]) -> dict[str, Any]:
    sample = eval_row.get("samples", [{}])[0] if eval_row.get("samples") else {}
    selected = sample.get("selected")
    return {
        "selected_move_count": eval_row.get("selected_move_count", 0),
        "selected_move": sample.get("selected_move"),
        "candidate_count": sample.get("candidate_count", 0),
        "failure_bucket": sample.get("failure_bucket"),
        "selected": _compact_component(selected) if selected is not None else None,
    }


def _compact_component(component: dict[str, Any] | None) -> dict[str, Any] | None:
    if component is None:
        return None
    reply_total = int(component.get("reply_total") or 0)
    reply_solved = int(component.get("reply_solved") or 0)
    return {
        "move": component.get("move"),
        "evidence_score": component.get("evidence_score"),
        "formal_recon_engine_confirmed": component.get("formal_recon_engine_confirmed"),
        "graph_confirmation_state": component.get("graph_confirmation_state"),
        "edge_terminal_state": component.get("edge_terminal_state"),
        "bridge_pressure_terminal_state": component.get("bridge_pressure_terminal_state"),
        "foundation_terminal_state": component.get("foundation_terminal_state"),
        "action_delta_terminal_state": component.get("action_delta_terminal_state"),
        "attention_terminal_state": component.get("attention_terminal_state"),
        "safety_terminal_state": component.get("safety_terminal_state"),
        "actuator_terminal_state": component.get("actuator_terminal_state"),
        "foundation_handoff_reachable": component.get("foundation_handoff_reachable") or component.get("reply_envelope_foundation_reachable"),
        "foundation_handoff_conversion": component.get("foundation_handoff_conversion"),
        "same_graph_foundation_continuation_count": component.get("same_graph_foundation_continuation_count", 0),
        "reply_total": reply_total,
        "reply_solved": reply_solved,
        "reply_envelope_foundation_coverage_rate": component.get("reply_envelope_foundation_coverage_rate"),
        "all_replies_solved": reply_total > 0 and reply_solved == reply_total,
        "worst_reply_success": reply_total > 0 and reply_solved == reply_total,
        "foundation_frontier_request_strength": component.get("foundation_frontier_request_strength"),
        "delta_foundation_proximity": component.get("delta_foundation_proximity"),
        "bridge_confidence": component.get("bridge_confidence"),
        "worst_reply_failure_reason": component.get("cache_reply_envelope", {}).get("worst_reply_failure_reason") if isinstance(component.get("cache_reply_envelope"), dict) else component.get("chain", {}).get("worst_reply_failure_reason"),
        "delta_black_king_edge_distance": component.get("delta_black_king_edge_distance"),
        "delta_black_king_legal_mobility": component.get("delta_black_king_legal_mobility"),
        "delta_confinement_area": component.get("delta_confinement_area"),
    }


def _safety_result(board: chess.Board) -> dict[str, Any]:
    rook = next((sq for sq, piece in board.piece_map().items() if piece.color == chess.WHITE and piece.piece_type == chess.ROOK), None)
    rook_blunder = rook is None or board.is_attacked_by(chess.BLACK, rook)
    return {"rook_blunder": rook_blunder, "safe": not rook_blunder}


def _episode_failure_bucket(episode: dict[str, Any]) -> str:
    reason = episode["termination_reason"]
    if reason in {"checkmate", "foundation_handoff"}:
        return "success"
    return {
        "no_move_selected": "no_move_selected",
        "illegal_move_selected": "illegal_move_selected",
        "unsafe_rook_blunder": "unsafe_rook_blunder",
        "stalemate": "stalemate",
        "max_moves_reached": "max_moves_reached",
    }.get(reason, "unknown")


def _purity_boundary() -> dict[str, Any]:
    return {
        "checkpoint": "TG29a",
        "online_episode_runner": True,
        "foundation_frozen": True,
        "white_moves_graph_mediated": True,
        "black_replies_harness_simulated": True,
        "cache_used_as_memoized_frozen_graph_response": True,
        "cache_used_as_provider": False,
        "action_ranker_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "learner_visible_stage_labels": False,
        "direct_provider_override": False,
    }


def _write_progress(cfg: TinyOnlineKRKEpisodeRunnerConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
