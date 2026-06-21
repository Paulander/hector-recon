"""TG28j persisted staged-predecessor pool."""

from __future__ import annotations

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
    _foundation_counts,
    _generate_edge_fence_positions,
    _cheap_candidate_rows,
)
from .frozen_foundation_response_cache_bridge_retrieval import (
    _FoundationResponseCache,
    _cache_candidate_rows,
    _train_cache_bridge_layer,
)
from .full_frontier_validation_near_miss import _load_jsonl
from .internal_handoff_affordance_guard_audit import _mate2_cfg
from .native_quorum_mate2_chaining import _tg26u_config
from .native_quorum_materialization import _tg26t_config
from .persisted_foundation_backed_frontier_pool import _as_tg28b_config, _as_tg28d_like_config
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .staged_edge_bridge_foundation_rollout import (
    StagedEdgeBridgeFoundationRolloutConfig,
    _as_tg28h_config,
    _as_tg28f_config,
    _evaluate_staged_rollout,
    _generate_staged_examples,
    _purity_boundary as _tg28i_purity_boundary,
    _required_ablations,
    _run_schedule_comparison,
    _schedule_public,
    _select_schedule,
    _stage_reply_rows,
    _train_generic_edge_weights,
)


@dataclass(frozen=True)
class PersistedStagedPredecessorPoolConfig:
    seed: int = 20260702
    foundation_seed: int = 20260624
    foundation_mate1_train_count: int = 32
    foundation_mate1_heldout_count: int = 16
    foundation_mate2_train_count: int = 16
    foundation_mate2_heldout_count: int = 8
    bridge_frontier_train_count: int = 2
    bridge_frontier_heldout_count: int = 1
    generic_edge_train_count: int = 4
    generic_edge_heldout_count: int = 2
    near_miss_train_count: int = 0
    near_miss_heldout_count: int = 0
    staged_train_count: int = 4
    staged_heldout_count: int = 2
    staged_regression_count: int = 2
    staged_near_miss_count: int = 0
    max_generation_attempts: int = 250_000
    max_cache_candidate_moves: int = 3
    max_reply_envelope_replies_per_candidate: int = 1
    max_mate2_probe_moves_per_state: int = 2
    max_edge_candidates_per_position: int = 12
    max_ablation_positions: int = 0
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
    staged_generation_multiplier: int = 30
    max_staged_source_positions: int = 32
    max_staged_first_move_candidates: int = 2
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
    staged_pool_path: str = "reports/autogrowth/pools/tg28j_staged_predecessor_pool.jsonl"
    staged_pool_index_path: str = "reports/autogrowth/pools/tg28j_staged_predecessor_pool_index.json"
    tg28i_bootstrap_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg28i_staged_edge_bridge_foundation_rollout.json"
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg28j_persisted_staged_predecessor_pool_progress.json"


@dataclass(frozen=True)
class PersistedStagedPredecessorPoolResult:
    config: PersistedStagedPredecessorPoolConfig
    foundation_sanity: dict[str, Any]
    pool: dict[str, Any]
    schedule_comparison: dict[str, Any]
    selected_schedule: dict[str, Any]
    ablation_results: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg28j_persisted_staged_predecessor_pool.v0",
            "checkpoint": "TG28j_persisted_staged_predecessor_pool",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "foundation_sanity": self.foundation_sanity,
            "pool": self.pool,
            "schedule_comparison": self.schedule_comparison,
            "selected_schedule": self.selected_schedule,
            "ablation_results": self.ablation_results,
            "scheduler_equivalence": self.scheduler_equivalence,
            "phase_timings": self.phase_timings,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_persisted_staged_predecessor_pool(
    *,
    config: PersistedStagedPredecessorPoolConfig | None = None,
) -> PersistedStagedPredecessorPoolResult:
    cfg = config or PersistedStagedPredecessorPoolConfig()
    timings: dict[str, float] = {"artifact_write_seconds": 0.0}
    total_start = time.perf_counter()
    tg28i_cfg = _as_tg28i_config(cfg)
    tg28c_cfg = _as_tg28c_config(_as_tg28d_like_config(_as_tg28f_config(_as_tg28h_config(tg28i_cfg))))
    edge_cfg = _as_tg28b_config(tg28c_cfg)

    pool_entries = _load_jsonl(Path(cfg.full_pool_path))
    frontier_train = tuple(entry["position_fen"] for entry in pool_entries if entry.get("split") == "train")[: cfg.bridge_frontier_train_count]
    frontier_heldout = tuple(entry["position_fen"] for entry in pool_entries if entry.get("split") == "heldout")[: cfg.bridge_frontier_heldout_count]
    excluded = set(frontier_train + frontier_heldout)
    _write_progress(cfg, {"phase": "frontier_pool_loaded", "frontier_train_count": len(frontier_train), "frontier_heldout_count": len(frontier_heldout)})

    start = time.perf_counter()
    foundation = _build_tg27b_foundation(edge_cfg)
    timings["foundation_build_seconds"] = round(time.perf_counter() - start, 6)
    graph = foundation["graph"]
    mate1_train = foundation["mate1_train"]
    mate1_heldout = foundation["mate1_heldout"]
    mate2_heldout = foundation["mate2_heldout"]
    mate2_cfg = _mate2_cfg(foundation["internal_cfg"])
    foundation_hash = _stable_hash({
        "foundation_seed": cfg.foundation_seed,
        "mate1_train": cfg.foundation_mate1_train_count,
        "mate1_heldout": cfg.foundation_mate1_heldout_count,
        "mate2_train": cfg.foundation_mate2_train_count,
        "mate2_heldout": cfg.foundation_mate2_heldout_count,
        "repaired_high_recall_threshold": cfg.repaired_high_recall_threshold,
    })
    cache_hash = _stable_hash(asdict(tg28c_cfg))

    start = time.perf_counter()
    foundation_sanity = _compact_foundation_sanity(graph, mate1_heldout, mate2_heldout, foundation["attention_cfg"], mate2_cfg, edge_cfg)
    cache = _FoundationResponseCache(graph, mate2_cfg, tg28c_cfg)
    timings["foundation_sanity_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "foundation_sanity_complete", "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"], "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"]})

    start = time.perf_counter()
    generic_train = _generate_edge_fence_positions(count=cfg.generic_edge_train_count, seed=cfg.seed + 41, excluded=excluded, cfg=edge_cfg)
    excluded.update(generic_train)
    generic_heldout = _generate_edge_fence_positions(count=cfg.generic_edge_heldout_count, seed=cfg.seed + 42, excluded=excluded, cfg=edge_cfg)
    excluded.update(generic_heldout)
    edge_weights: dict[str, float] = {}
    bridge_weights: dict[str, float] = {}
    _train_cache_bridge_layer(cache, frontier_train, tg28c_cfg, edge_weights, bridge_weights)
    _train_generic_edge_weights(generic_train, edge_cfg, edge_weights)
    timings["seed_training_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "seed_training_complete", "generic_train_count": len(generic_train)})

    start = time.perf_counter()
    existing_entries = _load_pool_entries(Path(cfg.staged_pool_path))
    persisted = _ensure_pool_entries(
        cfg,
        cache,
        tg28c_cfg,
        edge_cfg,
        edge_weights,
        bridge_weights,
        foundation_hash=foundation_hash,
        cache_hash=cache_hash,
        existing_entries=existing_entries,
        excluded=excluded,
    )
    timings["pool_generation_seconds"] = round(time.perf_counter() - start, 6)

    pool_by_split = _entries_by_split(persisted["entries"])
    staged_train = _examples_from_entries(pool_by_split["train"])
    staged_heldout = _examples_from_entries(pool_by_split["heldout"])
    near_miss_heldout = tuple(entry["start_fen"] for entry in pool_by_split["near_miss"][: cfg.near_miss_heldout_count])
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
        near_miss_train=tuple(),
        near_miss_heldout=near_miss_heldout,
        staged_train=staged_train,
        staged_heldout=staged_heldout,
        cfg=tg28i_cfg,
    )
    timings["schedule_comparison_seconds"] = round(time.perf_counter() - start, 6)
    foundation_after_training = _foundation_counts(graph)
    selected = _select_schedule(schedules)
    _write_progress(cfg, {"phase": "schedule_comparison_complete", "selected_training_schedule": selected["schedule_name"], "staged_any_reply_success_count": selected["staged_any_reply_success_count"]})

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
        tg28i_cfg,
    )
    equivalence = cache.live_equivalence_audit(max_samples=min(8, cfg.max_samples))
    scheduler_equivalence = (
        {"mismatch_count": 0, "skipped": True, "skip_reason": "max_ablation_positions_zero"}
        if cfg.max_ablation_positions <= 0
        else _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(mate2_cfg))), mate1_train, mate1_heldout)
    )
    foundation_after_eval = _foundation_counts(graph)
    timings["ablation_eval_seconds"] = round(time.perf_counter() - start, 6)
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)

    pool_summary = _pool_summary(cfg, persisted, timings)
    decision = _decision(
        cfg,
        pool_summary=pool_summary,
        foundation_sanity=foundation_sanity,
        selected=selected,
        schedules=schedules,
        equivalence=equivalence,
        scheduler_equivalence=scheduler_equivalence,
        foundation_before_training=foundation_before_training,
        foundation_after_training=foundation_after_training,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
        timings=timings,
        ablations=ablations,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})

    return PersistedStagedPredecessorPoolResult(
        config=cfg,
        foundation_sanity=foundation_sanity,
        pool=pool_summary,
        schedule_comparison={name: _schedule_public(row, cfg.max_samples) for name, row in schedules.items()},
        selected_schedule=_schedule_public(selected, cfg.max_samples),
        ablation_results=ablations,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _as_tg28i_config(cfg: PersistedStagedPredecessorPoolConfig) -> StagedEdgeBridgeFoundationRolloutConfig:
    return StagedEdgeBridgeFoundationRolloutConfig(
        seed=cfg.seed,
        foundation_seed=cfg.foundation_seed,
        foundation_mate1_train_count=cfg.foundation_mate1_train_count,
        foundation_mate1_heldout_count=cfg.foundation_mate1_heldout_count,
        foundation_mate2_train_count=cfg.foundation_mate2_train_count,
        foundation_mate2_heldout_count=cfg.foundation_mate2_heldout_count,
        bridge_frontier_train_count=cfg.bridge_frontier_train_count,
        bridge_frontier_heldout_count=cfg.bridge_frontier_heldout_count,
        generic_edge_safety_regression_count=cfg.generic_edge_heldout_count,
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
        staged_train_count=cfg.staged_train_count,
        staged_heldout_count=cfg.staged_heldout_count,
        staged_generation_multiplier=cfg.staged_generation_multiplier,
        max_staged_source_positions=cfg.max_staged_source_positions,
        max_staged_first_move_candidates=cfg.max_staged_first_move_candidates,
        max_staged_black_replies_after_edge=cfg.max_staged_black_replies_after_edge,
        max_staged_black_replies_after_bridge=cfg.max_staged_black_replies_after_bridge,
        schedule_names=cfg.schedule_names,
        full_pool_path=cfg.full_pool_path,
        progress_output=cfg.progress_output,
    )


def _ensure_pool_entries(
    cfg: PersistedStagedPredecessorPoolConfig,
    cache: _FoundationResponseCache,
    tg28c_cfg,
    edge_cfg,
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
    *,
    foundation_hash: str,
    cache_hash: str,
    existing_entries: list[dict[str, Any]],
    excluded: set[str],
) -> dict[str, Any]:
    path = Path(cfg.staged_pool_path)
    index_path = Path(cfg.staged_pool_index_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = list(existing_entries)
    dedupe = {_dedupe_key(entry) for entry in entries}
    generation_attempts = 0
    accepted = 0
    duplicates = 0
    rejection_counts: dict[str, int] = {}
    targets = {
        "train": cfg.staged_train_count,
        "heldout": cfg.staged_heldout_count,
        "regression": cfg.staged_regression_count,
        "near_miss": cfg.staged_near_miss_count,
    }
    bootstrap_examples = _bootstrap_examples_from_tg28i(Path(cfg.tg28i_bootstrap_artifact_path))
    for split, target in targets.items():
        while split != "near_miss" and bootstrap_examples and sum(1 for entry in entries if entry["split"] == split) < target:
            example = bootstrap_examples.pop(0)
            entry = _pool_entry_from_example(example, split, cfg.seed, foundation_hash, cache_hash, cache, tg28c_cfg, edge_weights, bridge_weights)
            entry["generation_method"] = "accepted_entry_mutation"
            key = _dedupe_key(entry)
            if key in dedupe:
                duplicates += 1
                continue
            entries.append(entry)
            dedupe.add(key)
            accepted += 1
            _append_jsonl(path, entry)
            _write_index(index_path, entries, generation_attempts, duplicates, rejection_counts)
            _write_progress(cfg, {"phase": "pool_entry_accepted", "split": split, "pool_entry_id": entry["pool_entry_id"], "pool_entry_count": len(entries), "generation_method": "accepted_entry_mutation"})
        while sum(1 for entry in entries if entry["split"] == split) < target:
            needed = target - sum(1 for entry in entries if entry["split"] == split)
            if split == "near_miss":
                new_entries, stats = _generate_negative_entries(cfg, cache, tg28c_cfg, edge_cfg, edge_weights, bridge_weights, split, foundation_hash, cache_hash, excluded, needed)
            else:
                staged, stats = _generate_staged_examples(
                    cache,
                    tg28c_cfg,
                    edge_cfg,
                    edge_weights,
                    bridge_weights,
                    count=needed,
                    seed=cfg.seed + len(entries) + len(split),
                    excluded=excluded,
                    cfg=_as_tg28i_config(cfg),
                )
                new_entries = [
                    _pool_entry_from_example(example, split, cfg.seed, foundation_hash, cache_hash, cache, tg28c_cfg, edge_weights, bridge_weights)
                    for example in staged
                ]
            generation_attempts += stats.get("generation_attempts", 0)
            for key, value in stats.get("rejection_counts", {}).items():
                rejection_counts[key] = rejection_counts.get(key, 0) + value
            if not new_entries:
                rejection_counts["generation_timeout"] = rejection_counts.get("generation_timeout", 0) + 1
                break
            for entry in new_entries:
                key = _dedupe_key(entry)
                if key in dedupe:
                    duplicates += 1
                    continue
                entries.append(entry)
                dedupe.add(key)
                accepted += 1
                _append_jsonl(path, entry)
                _write_index(index_path, entries, generation_attempts, duplicates, rejection_counts)
                _write_progress(cfg, {"phase": "pool_entry_accepted", "split": split, "pool_entry_id": entry["pool_entry_id"], "pool_entry_count": len(entries)})
    _write_index(index_path, entries, generation_attempts, duplicates, rejection_counts)
    return {
        "entries": entries,
        "generation_attempts": generation_attempts,
        "accepted_staged_entries": accepted,
        "duplicate_rejections": duplicates,
        "rejection_counts": rejection_counts,
    }


def _pool_entry_from_example(example, split, seed, foundation_hash, cache_hash, cache, tg28c_cfg, edge_weights, bridge_weights) -> dict[str, Any]:
    start = chess.Board(example["fen"])
    first = chess.Move.from_uci(example["trainer_edge_move"])
    after_first = start.copy(stack=False)
    after_first.push(first)
    reply = next((row for row in example["reply_rows"] if row.get("bridge_opportunity")), example["reply_rows"][0])
    black_reply = chess.Move.from_uci(reply["black_reply"])
    s1 = after_first.copy(stack=False)
    s1.push(black_reply)
    bridge_move_uci = reply.get("bridge_selected_move")
    if bridge_move_uci is None:
        rows = _cache_candidate_rows(cache, s1, tg28c_cfg, edge_weights, bridge_weights, cache_retrieval_enabled=True)
        confirmed = [row for row in rows if row["formal_recon_engine_confirmed"]]
        confirmed.sort(key=lambda row: (row["evidence_score"], row["move"]), reverse=True)
        bridge_move_uci = None if not confirmed else confirmed[0]["move"]
    bridge_move = chess.Move.from_uci(bridge_move_uci) if bridge_move_uci else None
    after_bridge = s1.copy(stack=False)
    if bridge_move in after_bridge.legal_moves:
        after_bridge.push(bridge_move)
    foundation_query = after_bridge.copy(stack=False)
    black_reply_after_bridge = None
    if not foundation_query.is_game_over() and foundation_query.turn == chess.BLACK:
        replies = sorted(foundation_query.legal_moves, key=lambda item: item.uci())
        if replies:
            black_reply_after_bridge = replies[0].uci()
            foundation_query.push(replies[0])
    foundation_state = cache.query_state(foundation_query)
    before_metrics = _board_metrics(start)
    after_first_metrics = _board_metrics(after_first)
    after_bridge_metrics = _board_metrics(after_bridge)
    staged_type = _staged_success_type(example)
    payload = {
        "schema_version": "tg28j_staged_predecessor_pool_entry.v0",
        "split": split,
        "generation_seed": seed,
        "generation_method": "forward_filter",
        "foundation_config_hash": foundation_hash,
        "cache_config_hash": cache_hash,
        "bridge_frontier_pool_entry_id": None,
        "anchor_bridge_fen": None,
        "start_fen": start.fen(),
        "first_edge_move": first.uci(),
        "after_first_edge_fen": after_first.fen(),
        "black_reply_after_edge": reply["black_reply"],
        "s1_fen": s1.fen(),
        "bridge_move": bridge_move_uci,
        "after_bridge_fen": after_bridge.fen(),
        "black_reply_after_bridge": black_reply_after_bridge,
        "foundation_query_fen": foundation_query.fen(),
        "foundation_selected_move": foundation_state["foundation_selected_move"],
        "final_graph_confirmation_state": foundation_state["graph_confirmation_state"],
        "staged_success_type": staged_type,
        "rook_blunder": not after_first_metrics["rook_safe"] or not after_bridge_metrics["rook_safe"],
        "stalemate_after_first": after_first.is_stalemate(),
        "stalemate_after_bridge": after_bridge.is_stalemate(),
        "rook_safe_after_first": after_first_metrics["rook_safe"],
        "rook_safe_after_bridge": after_bridge_metrics["rook_safe"],
        "edge_distance_before": before_metrics["edge_distance"],
        "edge_distance_after_first": after_first_metrics["edge_distance"],
        "black_king_mobility_before": before_metrics["black_king_mobility"],
        "black_king_mobility_after_first": after_first_metrics["black_king_mobility"],
        "confinement_area_before": before_metrics["confinement_area"],
        "confinement_area_after_first": after_first_metrics["confinement_area"],
        "bridge_reply_total": len(example["reply_rows"]),
        "bridge_replies_foundation_solved": sum(int(row.get("foundation_handoff_conversion", False) or row.get("bridge_selected_foundation_reachable", False)) for row in example["reply_rows"]),
        "bridge_reply_envelope_success_rate": sum(int(row.get("bridge_opportunity", False)) for row in example["reply_rows"]) / max(1, len(example["reply_rows"])),
        "same_graph_foundation_continuation_count": int(reply.get("same_graph_foundation_continuation_count", 0)),
        "live_graph_equivalence_hash": foundation_state["live_graph_equivalence_hash"],
        "source": foundation_state["source"],
        "validator_labels_used_for_generation_only": True,
        "learner_visible_labels": False,
    }
    payload["pool_entry_id"] = hashlib.sha1(_dedupe_key(payload).encode("utf-8")).hexdigest()[:20]
    return payload


def _generate_negative_entries(cfg, cache, tg28c_cfg, edge_cfg, edge_weights, bridge_weights, split, foundation_hash, cache_hash, excluded, count):
    entries = []
    attempts = 0
    rejected: dict[str, int] = {}
    source_count = min(cfg.max_staged_source_positions, max(1, count * cfg.staged_generation_multiplier))
    for fen in _generate_edge_fence_positions(count=source_count, seed=cfg.seed + 900 + count, excluded=excluded, cfg=edge_cfg):
        attempts += 1
        board = chess.Board(fen)
        rows = [row for row in _cheap_candidate_rows(board, edge_weights) if row["safety_ok"]]
        if not rows:
            rejected["no_edge_predecessor_found"] = rejected.get("no_edge_predecessor_found", 0) + 1
            continue
        edge_row = sorted(rows, key=lambda row: (row["cheap_score"], row["move"]), reverse=True)[0]
        reply_rows = _stage_reply_rows(cache, tg28c_cfg, board, edge_row["move"], edge_weights, bridge_weights, _as_tg28i_config(cfg))
        if any(row.get("bridge_opportunity") for row in reply_rows):
            rejected["bridge_s1_found"] = rejected.get("bridge_s1_found", 0) + 1
            continue
        example = {"fen": fen, "trainer_edge_move": edge_row["move"], "reply_rows": reply_rows or [], "summary": {"any_reply_stage_success": False}}
        if not example["reply_rows"]:
            rejected["edge_predecessor_found_but_no_bridge_s1"] = rejected.get("edge_predecessor_found_but_no_bridge_s1", 0) + 1
            continue
        entry = _pool_entry_from_example(example, split, cfg.seed, foundation_hash, cache_hash, cache, tg28c_cfg, edge_weights, bridge_weights)
        entry["staged_success_type"] = "negative_near_miss"
        entries.append(entry)
        if len(entries) >= count:
            break
    return entries, {"generation_attempts": attempts, "rejection_counts": rejected}


def _bootstrap_examples_from_tg28i(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    samples = payload.get("selected_schedule", {}).get("staged", {}).get("samples", [])
    examples = []
    for sample in samples:
        for row in sample.get("reply_rows", []):
            reply_rows = [{
                "black_reply": row["black_reply"],
                "s1_fen": row["s1_fen"],
                "bridge_candidate_count": row.get("bridge_candidate_count", 0),
                "bridge_opportunity": bool(row.get("foundation_continuation_success")) or row.get("bridge_candidate_count", 0) > 0,
                "bridge_selected_move": row.get("bridge_selected_move"),
                "bridge_selected_foundation_reachable": bool(row.get("foundation_continuation_success")),
                "same_graph_foundation_continuation_count": sum(int(item.get("foundation_solved", False)) for item in row.get("foundation_reply_rows", [])),
                "foundation_handoff_conversion": bool(row.get("foundation_continuation_success")),
                "failure_bucket": row.get("bridge_failure_bucket", "none"),
            }]
            examples.append({
                "fen": sample["fen"],
                "trainer_edge_move": sample.get("selected_edge_move") or sample.get("trainer_edge_move"),
                "reply_rows": reply_rows,
                "summary": {"fen": sample["fen"], "trainer_edge_move": sample.get("selected_edge_move") or sample.get("trainer_edge_move")},
            })
    return examples


def _examples_from_entries(entries: list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for entry in entries:
        if entry["staged_success_type"] == "negative_near_miss":
            continue
        grouped.setdefault((entry["start_fen"], entry["first_edge_move"]), []).append(entry)
    out = []
    for (fen, move), rows in grouped.items():
        reply_rows = [
            {
                "black_reply": entry["black_reply_after_edge"],
                "s1_fen": entry["s1_fen"],
                "bridge_candidate_count": int(entry["bridge_move"] is not None),
                "bridge_opportunity": entry["staged_success_type"] != "negative_near_miss",
                "bridge_selected_move": entry["bridge_move"],
                "bridge_selected_foundation_reachable": entry["bridge_replies_foundation_solved"] > 0,
                "same_graph_foundation_continuation_count": entry["same_graph_foundation_continuation_count"],
                "foundation_handoff_conversion": entry["foundation_selected_move"] is not None,
                "failure_bucket": "none",
            }
            for entry in rows
        ]
        out.append({"fen": fen, "trainer_edge_move": move, "reply_rows": reply_rows, "summary": {"fen": fen, "trainer_edge_move": move}})
    return tuple(out)


def _pool_summary(cfg, persisted, timings) -> dict[str, Any]:
    entries = persisted["entries"]
    by_split = _entries_by_split(entries)
    return {
        "staged_pool_path": cfg.staged_pool_path,
        "staged_pool_index_path": cfg.staged_pool_index_path,
        "staged_pool_entry_count": len(entries),
        "staged_train_count": len(by_split["train"]),
        "staged_heldout_count": len(by_split["heldout"]),
        "staged_regression_count": len(by_split["regression"]),
        "staged_near_miss_count": len(by_split["near_miss"]),
        "all_reply_staged_count": sum(1 for entry in entries if entry["staged_success_type"] == "all_reply_success"),
        "partial_reply_staged_count": sum(1 for entry in entries if entry["staged_success_type"] == "partial_reply_success"),
        "any_reply_staged_count": sum(1 for entry in entries if entry["staged_success_type"] == "any_reply_success"),
        "negative_near_miss_count": sum(1 for entry in entries if entry["staged_success_type"] == "negative_near_miss"),
        "generation_attempts": persisted["generation_attempts"],
        "accepted_staged_entries": persisted["accepted_staged_entries"],
        "duplicate_rejections": persisted["duplicate_rejections"],
        "rejection_counts": persisted["rejection_counts"],
        "timeout_count": persisted["rejection_counts"].get("generation_timeout", 0),
        "average_seconds_per_accepted_entry": timings.get("pool_generation_seconds", 0.0) / max(1, persisted["accepted_staged_entries"]),
        "samples": entries[: cfg.max_samples],
    }


def _decision(cfg, *, pool_summary, foundation_sanity, selected, schedules, equivalence, scheduler_equivalence, foundation_before_training, foundation_after_training, foundation_before_eval, foundation_after_eval, timings, ablations) -> dict[str, Any]:
    train_m3_delta = foundation_after_training["m3"] - foundation_before_training["m3"]
    train_m4_delta = foundation_after_training["m4"] - foundation_before_training["m4"]
    eval_m3_delta = foundation_after_eval["m3"] - foundation_before_eval["m3"]
    eval_m4_delta = foundation_after_eval["m4"] - foundation_before_eval["m4"]
    baseline = schedules.get("tg28h_mixed_balanced_baseline", selected)
    infrastructure_pass = (
        pool_summary["staged_train_count"] > 0
        and pool_summary["staged_heldout_count"] > 0
        and foundation_sanity["foundation_mate1_accuracy"] >= 1.0
        and foundation_sanity["foundation_mate2_conversion_rate"] >= 1.0
        and train_m3_delta == 0
        and train_m4_delta == 0
        and eval_m3_delta == 0
        and eval_m4_delta == 0
        and equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
    )
    staged_advancement = infrastructure_pass and selected["staged_any_reply_success_count"] > 0 and selected["staged_s1_bridge_foundation_reachable_count"] > 0
    return {
        "checkpoint_pass": infrastructure_pass,
        "checkpoint_interpretation": "persisted_pool_and_staged_advancement" if staged_advancement else ("persisted_pool_infrastructure_pass" if infrastructure_pass else "persisted_pool_infrastructure_failed"),
        "selected_training_schedule": selected["schedule_name"],
        "foundation_frozen": True,
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": equivalence["foundation_cache_live_mismatch_count"],
        "foundation_m3_updates_during_training": train_m3_delta,
        "foundation_m4_promotions_during_training": train_m4_delta,
        "foundation_m3_updates_during_eval": eval_m3_delta,
        "foundation_m4_promotions_during_eval": eval_m4_delta,
        **{key: pool_summary[key] for key in (
            "staged_pool_path", "staged_pool_index_path", "staged_pool_entry_count", "staged_train_count", "staged_heldout_count",
            "staged_regression_count", "staged_near_miss_count", "all_reply_staged_count", "partial_reply_staged_count",
            "any_reply_staged_count", "negative_near_miss_count", "generation_attempts", "accepted_staged_entries", "timeout_count",
        )},
        "staged_selected_first_move_count": selected["staged_selected_first_move_count"],
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
        "frontier_selected_count": selected["frontier_selected_count"],
        "frontier_foundation_handoff_conversion_count": selected["frontier_foundation_handoff_conversion_count"],
        "frontier_same_graph_continuation_count": selected["frontier_same_graph_continuation_count"],
        "near_miss_selected_count": selected["near_miss_selected_count"],
        "near_miss_false_positive_count": selected["near_miss_false_positive_count"],
        "generic_edge_fence_success_rate": selected["generic_edge_fence_success_rate"],
        "generic_rook_blunder_count": selected["generic_rook_blunder_count"],
        "generic_stalemate_avoidance_rate": selected["generic_stalemate_avoidance_rate"],
        "frontier_drop_vs_TG28h": 4 - selected["frontier_selected_count"],
        "near_miss_false_positive_increase_vs_TG28h": selected["near_miss_false_positive_count"],
        "generic_edge_drop_vs_TG28h": 1.0 - selected["generic_edge_fence_success_rate"],
        "staged_rollout_success_vs_TG28i": selected["staged_any_reply_success_count"] - 1,
        "failure_bucket_counts": selected["failure_bucket_counts"] | {"pool_generation": pool_summary["rejection_counts"]},
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "ablation_results": ablations,
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


def _load_pool_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append_jsonl(path: Path, entry: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def _write_index(path: Path, entries: list[dict[str, Any]], attempts: int, duplicates: int, rejection_counts: dict[str, int]) -> None:
    by_split = _entries_by_split(entries)
    payload = {
        "schema_version": "tg28j_staged_predecessor_pool_index.v0",
        "entry_count": len(entries),
        "counts_by_split": {key: len(value) for key, value in by_split.items()},
        "generation_attempts": attempts,
        "duplicate_rejections": duplicates,
        "rejection_counts": rejection_counts,
        "entry_ids": [entry["pool_entry_id"] for entry in entries],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _entries_by_split(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {split: [entry for entry in entries if entry["split"] == split] for split in ("train", "heldout", "regression", "near_miss")}


def _dedupe_key(entry: dict[str, Any]) -> str:
    return "|".join(str(entry.get(key)) for key in ("start_fen", "first_edge_move", "black_reply_after_edge", "bridge_move", "foundation_config_hash"))


def _staged_success_type(example: dict[str, Any]) -> str:
    rows = example["reply_rows"]
    hits = sum(int(row.get("bridge_opportunity", False)) for row in rows)
    if rows and hits == len(rows):
        return "all_reply_success"
    if hits > 0:
        return "partial_reply_success" if hits < len(rows) else "any_reply_success"
    return "negative_near_miss"


def _board_metrics(board: chess.Board) -> dict[str, Any]:
    bk = board.king(chess.BLACK)
    rook = next((sq for sq, piece in board.piece_map().items() if piece.color == chess.WHITE and piece.piece_type == chess.ROOK), None)
    if bk is None:
        edge = 0
        mobility = 0
    else:
        file = chess.square_file(bk)
        rank = chess.square_rank(bk)
        edge = min(file, rank, 7 - file, 7 - rank)
        turn = board.turn
        board.turn = chess.BLACK
        mobility = len(list(board.legal_moves))
        board.turn = turn
    rook_safe = rook is not None and not board.is_attacked_by(chess.BLACK, rook)
    return {
        "edge_distance": edge,
        "black_king_mobility": mobility,
        "confinement_area": None if rook is None or bk is None else abs(chess.square_file(rook) - chess.square_file(bk)) + abs(chess.square_rank(rook) - chess.square_rank(bk)),
        "rook_safe": rook_safe,
    }


def _stable_hash(payload: Any) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg28i_purity_boundary()
    boundary.update({
        "checkpoint": "TG28j",
        "persisted_staged_pool": True,
        "pool_labels_learner_visible": False,
        "pool_used_as_provider": False,
    })
    return boundary


def _write_progress(cfg: PersistedStagedPredecessorPoolConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
