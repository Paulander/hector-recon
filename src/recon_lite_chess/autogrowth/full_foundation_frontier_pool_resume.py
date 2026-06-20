"""TG28f full TG27b persisted frontier-pool resume checkpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import random
import time
from pathlib import Path
from typing import Any

import chess

from .foundation_backed_bridge_frontier import (
    _anchor_predecessor_board,
    _as_tg28c_config,
    _foundation_backed_seed_boards,
    _random_edge_board,
)
from .foundation_curriculum import _forced_mate_in_two_first_moves, _mate_moves
from .frozen_foundation_bridge_pressure import _compact_foundation_sanity
from .frozen_foundation_edge_fence_reentry import (
    _black_edge_distance,
    _black_king_mobility,
    _build_tg27b_foundation,
    _cheap_candidate_rows,
    _confinement_area,
    _foundation_counts,
    _white_rook_square,
)
from .frozen_foundation_response_cache_bridge_retrieval import (
    FrozenFoundationResponseCacheBridgeRetrievalConfig,
    _FoundationResponseCache,
    _cache_bridge_ablations,
    _cache_candidate_rows,
    _evaluate_cache_bridge_layer,
    _train_cache_bridge_layer,
)
from .internal_handoff_affordance_guard_audit import _mate2_cfg
from .native_quorum_mate2_chaining import _tg26u_config
from .native_quorum_materialization import _tg26t_config
from .persisted_foundation_backed_frontier_pool import (
    PersistedFoundationBackedFrontierPoolConfig,
    _append_pool_entry,
    _as_tg28b_config,
    _as_tg28d_like_config,
    _config_hash,
    _dedupe_key,
    _entry_id,
    _foundation_config_payload,
    _full_tg27b_config_used,
    _load_pool_entries,
    _pool_entry,
    _purity_boundary as _tg28e_purity_boundary,
    _write_pool_index,
)
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence


@dataclass(frozen=True)
class FullFoundationFrontierPoolResumeConfig:
    seed: int = 20260630
    foundation_seed: int = 20260624
    foundation_mate1_train_count: int = 32
    foundation_mate1_heldout_count: int = 16
    foundation_mate2_train_count: int = 16
    foundation_mate2_heldout_count: int = 8
    bridge_frontier_train_count: int = 8
    bridge_frontier_heldout_count: int = 4
    generic_edge_safety_regression_count: int = 4
    minimum_train_count: int = 6
    minimum_heldout_count: int = 2
    minimum_regression_count: int = 2
    basin_random_count: int = 8
    max_generation_attempts: int = 250_000
    max_pool_generation_seconds: float = 780.0
    max_cache_candidate_moves: int = 12
    max_reply_envelope_replies_per_candidate: int = 1
    max_mate2_probe_moves_per_state: int = 2
    max_edge_candidates_per_position: int = 12
    max_ablation_positions: int = 2
    max_foundation_sanity_positions: int = 2
    max_foundation_ablation_positions: int = 2
    max_ticks: int = 30
    max_samples: int = 16
    repaired_high_recall_threshold: float = 0.018
    eta_m3_edge: float = 0.06
    eta_m3_bridge: float = 0.08
    edge_terminal_min_score: float = -0.25
    bridge_terminal_min_score: float = 0.10
    materialized_quorum_min_evidence: float = -10000.0
    replay_count: int = 2
    compact_pool_path: str = "reports/autogrowth/pools/tg28e_foundation_backed_frontier_pool.jsonl"
    full_pool_path: str = "reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl"
    full_pool_index_path: str = "reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool_index.json"
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg28f_full_foundation_frontier_pool_resume_progress.json"


@dataclass(frozen=True)
class FullFoundationFrontierPoolResumeResult:
    config: FullFoundationFrontierPoolResumeConfig
    anchor_index: dict[str, Any]
    pool: dict[str, Any]
    compact_comparison: dict[str, Any]
    foundation_sanity: dict[str, Any]
    cache: dict[str, Any]
    bridge_training: dict[str, Any]
    evaluations: dict[str, Any]
    ablation_results: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg28f_full_foundation_frontier_pool_resume.v0",
            "checkpoint": "TG28f_full_foundation_frontier_pool_resume",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "anchor_index": self.anchor_index,
            "pool": self.pool,
            "compact_comparison": self.compact_comparison,
            "foundation_sanity": self.foundation_sanity,
            "cache": self.cache,
            "bridge_training": self.bridge_training,
            "evaluations": self.evaluations,
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


def run_full_foundation_frontier_pool_resume(
    *,
    config: FullFoundationFrontierPoolResumeConfig | None = None,
) -> FullFoundationFrontierPoolResumeResult:
    cfg = config or FullFoundationFrontierPoolResumeConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    tg28c_cfg = _as_tg28c_config(_as_tg28d_like_config(_as_tg28e_config(cfg)))
    foundation_hash = _config_hash(_foundation_config_payload(_as_tg28e_config(cfg)))
    cache_hash = _config_hash(asdict(tg28c_cfg))

    start = time.perf_counter()
    foundation = _build_tg27b_foundation(_as_tg28b_config(tg28c_cfg))
    timings["foundation_build_seconds"] = round(time.perf_counter() - start, 6)
    graph = foundation["graph"]
    mate1_train = foundation["mate1_train"]
    mate1_heldout = foundation["mate1_heldout"]
    mate2_train = foundation["mate2_train"]
    mate2_heldout = foundation["mate2_heldout"]
    mate2_cfg = _mate2_cfg(foundation["internal_cfg"])
    _write_progress(cfg, {"phase": "foundation_built", "foundation_config_hash": foundation_hash})

    start = time.perf_counter()
    foundation_sanity = _compact_foundation_sanity(
        graph,
        mate1_heldout,
        mate2_heldout,
        foundation["attention_cfg"],
        mate2_cfg,
        _as_tg28b_config(tg28c_cfg),
    )
    cache = _FoundationResponseCache(graph, mate2_cfg, tg28c_cfg)
    timings["cache_build_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    anchor_index, anchor_boards = _build_anchor_index(
        cache,
        mate1_train=mate1_train,
        mate1_heldout=mate1_heldout,
        mate2_train=mate2_train,
        mate2_heldout=mate2_heldout,
        cfg=cfg,
    )
    timings["anchor_index_build_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {
        "phase": "anchor_index_complete",
        "anchor_count": anchor_index["anchor_count"],
        "positive_anchor_count": anchor_index["positive_anchor_count"],
    })

    before_pool = _foundation_counts(graph)
    excluded = set((*mate1_train, *mate1_heldout, *mate2_train, *mate2_heldout))
    start = time.perf_counter()
    pool_entries, pool_stats = _build_or_resume_full_pool(
        cache,
        anchor_boards=anchor_boards,
        excluded=excluded,
        cfg=cfg,
        tg28c_cfg=tg28c_cfg,
        foundation_hash=foundation_hash,
        cache_hash=cache_hash,
    )
    timings["pool_resume_seconds"] = round(pool_stats["pool_resume_seconds"], 6)
    timings["full_pool_generation_seconds"] = round(time.perf_counter() - start, 6)
    after_pool = _foundation_counts(graph)

    train_fens = tuple(entry["position_fen"] for entry in pool_entries if entry["split"] == "train")
    heldout_fens = tuple(entry["position_fen"] for entry in pool_entries if entry["split"] == "heldout")
    regression_fens = tuple(entry["position_fen"] for entry in pool_entries if entry["split"] == "regression")

    foundation_before_training = _foundation_counts(graph)
    edge_weights: dict[str, float] = {}
    bridge_weights: dict[str, float] = {}
    start = time.perf_counter()
    training = _train_cache_bridge_layer(cache, train_fens, tg28c_cfg, edge_weights, bridge_weights)
    timings["bridge_training_seconds"] = round(time.perf_counter() - start, 6)
    foundation_after_training = _foundation_counts(graph)

    foundation_before_eval = _foundation_counts(graph)
    start = time.perf_counter()
    baseline = _evaluate_cache_bridge_layer(graph, cache, heldout_fens, tg28c_cfg, edge_weights, {}, cache_retrieval_enabled=False)
    frontier_eval = _evaluate_cache_bridge_layer(graph, cache, heldout_fens, tg28c_cfg, edge_weights, bridge_weights)
    generic_eval = _evaluate_cache_bridge_layer(graph, cache, regression_fens, tg28c_cfg, edge_weights, bridge_weights)
    timings["bridge_eval_seconds"] = round(time.perf_counter() - start, 6)
    start = time.perf_counter()
    ablations = _cache_bridge_ablations(graph, cache, heldout_fens, tg28c_cfg, edge_weights, bridge_weights)
    timings["ablation_seconds"] = round(time.perf_counter() - start, 6)
    foundation_after_eval = _foundation_counts(graph)
    equivalence = cache.live_equivalence_audit(max_samples=min(8, cfg.max_samples))
    scheduler_equivalence = (
        {"mismatch_count": 0, "skipped": True, "skip_reason": "max_ablation_positions_zero"}
        if cfg.max_ablation_positions <= 0
        else _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(mate2_cfg))), mate1_train, mate1_heldout)
    )
    compact_comparison = _compact_comparison(cfg)

    timings["artifact_write_seconds"] = 0.0
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)
    decision = _decision(
        cfg,
        foundation_sanity=foundation_sanity,
        cache=cache,
        equivalence=equivalence,
        pool_stats=pool_stats,
        frontier_eval=frontier_eval,
        generic_eval=generic_eval,
        ablations=ablations,
        scheduler_equivalence=scheduler_equivalence,
        training=training,
        foundation_before_pool=before_pool,
        foundation_after_pool=after_pool,
        foundation_before_training=foundation_before_training,
        foundation_after_training=foundation_after_training,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
        timings=timings,
    )
    _write_progress(cfg, {
        "phase": "complete",
        "decision": {
            "checkpoint_pass": decision["checkpoint_pass"],
            "checkpoint_interpretation": decision["checkpoint_interpretation"],
            "full_pool_entry_count": decision["full_pool_entry_count"],
            "selected_move_count": decision["selected_move_count"],
        },
    })
    return FullFoundationFrontierPoolResumeResult(
        config=cfg,
        anchor_index=anchor_index,
        pool={
            "full_pool_path": cfg.full_pool_path,
            "full_pool_index_path": cfg.full_pool_index_path,
            "foundation_config_hash": foundation_hash,
            "cache_config_hash": cache_hash,
            "full_pool_entry_count": len(pool_entries),
            "full_pool_train_count": len(train_fens),
            "full_pool_heldout_count": len(heldout_fens),
            "full_pool_regression_count": len(regression_fens),
            "pool_stats": pool_stats,
            "entry_samples": pool_entries[: cfg.max_samples],
        },
        compact_comparison=compact_comparison,
        foundation_sanity=foundation_sanity,
        cache=cache.to_dict(max_entries=cfg.max_samples),
        bridge_training=training,
        evaluations={
            "baseline_no_cache_from_full_pool_heldout": baseline,
            "foundation_backed_frontier_from_full_pool": frontier_eval,
            "generic_edge_safety_regression_from_full_pool": generic_eval,
        },
        ablation_results=ablations,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _build_anchor_index(
    cache: _FoundationResponseCache,
    *,
    mate1_train: tuple[str, ...],
    mate1_heldout: tuple[str, ...],
    mate2_train: tuple[str, ...],
    mate2_heldout: tuple[str, ...],
    cfg: FullFoundationFrontierPoolResumeConfig,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    candidates: list[tuple[str, str]] = []
    for source, fens in (
        ("tg27b_mate1_train", mate1_train),
        ("tg27b_mate1_heldout", mate1_heldout),
        ("tg27b_mate2_train", mate2_train),
        ("tg27b_mate2_heldout", mate2_heldout),
    ):
        candidates.extend((source, fen) for fen in fens)
    for source, path in (
        ("tg28e_compact_pool_position", cfg.compact_pool_path),
        ("tg28f_full_pool_position", cfg.full_pool_path),
    ):
        for entry in _load_any_pool_entries(Path(path)):
            candidates.append((source, entry["position_fen"]))
            candidates.append((source + "_after_candidate", entry["after_candidate_fen"]))
            for reply in entry.get("reply_rows", []):
                candidates.append((source + "_reply", reply["reply_fen"]))
    rows = []
    positive_rows = []
    seen: set[str] = set()
    for source, fen in candidates:
        try:
            board = chess.Board(fen)
        except ValueError:
            continue
        key = _canonical_position_key(board)
        if key in seen:
            continue
        seen.add(key)
        response = cache.query_state(board)
        positive = response["foundation_mate1_recognized"] or response["foundation_mate2_recognized"] or response["foundation_chain_success"]
        row = {
            "source": source,
            "canonical_fen": response["canonical_fen"],
            "side_to_move": response["side_to_move"],
            "foundation_response_type": _foundation_response_type(response),
            "same_graph_foundation_continuation_count": response["same_graph_second_move_count"],
            "positive": positive,
            "descriptors": _anchor_descriptors(board),
        }
        rows.append(row)
        if positive and board.turn == chess.WHITE:
            positive_rows.append(row)
    return {
        "anchor_count": len(rows),
        "positive_anchor_count": len(positive_rows),
        "sources": _counts(row["source"] for row in rows),
        "positive_sources": _counts(row["source"] for row in positive_rows),
        "samples": rows[: cfg.max_samples],
    }, tuple(row["canonical_fen"] for row in positive_rows)


def _build_or_resume_full_pool(
    cache: _FoundationResponseCache,
    *,
    anchor_boards: tuple[str, ...],
    excluded: set[str],
    cfg: FullFoundationFrontierPoolResumeConfig,
    tg28c_cfg: FrozenFoundationResponseCacheBridgeRetrievalConfig,
    foundation_hash: str,
    cache_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    start_resume = time.perf_counter()
    pool_path = Path(cfg.full_pool_path)
    pool_path.parent.mkdir(parents=True, exist_ok=True)
    entries = _load_pool_entries(pool_path, foundation_hash)
    loaded = len(entries)
    seen = {_dedupe_key(entry) for entry in entries}
    stats = {
        "generation_attempts": 0,
        "accepted_pool_entries": 0,
        "resumed_pool_entries": loaded,
        "loaded_existing_entries": loaded,
        "duplicate_rejections": 0,
        "safety_filter_rejections": 0,
        "no_foundation_response_rejections": 0,
        "rejected_direct_foundation": 0,
        "seed_pool_exhaustion_count": 0,
        "timeout_count": 0,
        "cache_queries_run": 0,
        "live_foundation_queries_run": 0,
        "deep_reply_checks_run": 0,
        "top_rejection_buckets": {},
        "all_reply_bridge_count": 0,
        "partial_reply_bridge_count": 0,
        "any_reply_bridge_count": 0,
        "pool_resume_seconds": time.perf_counter() - start_resume,
    }
    targets = {
        "train": cfg.bridge_frontier_train_count,
        "heldout": cfg.bridge_frontier_heldout_count,
        "regression": cfg.generic_edge_safety_regression_count,
    }
    deadline = time.perf_counter() + cfg.max_pool_generation_seconds
    for split, target in targets.items():
        have = [entry for entry in entries if entry["split"] == split]
        if len(have) >= target:
            continue
        accepted = _generate_full_split_entries(
            cache,
            anchor_boards=anchor_boards,
            excluded=excluded,
            split=split,
            needed=target - len(have),
            seed=cfg.seed + {"train": 0, "heldout": 1, "regression": 2}[split],
            deadline=deadline,
            cfg=cfg,
            tg28c_cfg=tg28c_cfg,
            foundation_hash=foundation_hash,
            cache_hash=cache_hash,
            seen=seen,
            pool_path=pool_path,
            stats=stats,
        )
        entries.extend(accepted)
        excluded.update(entry["position_fen"] for entry in accepted)
        if time.perf_counter() >= deadline:
            break
    selected_entries = []
    for split, target in targets.items():
        selected_entries.extend([entry for entry in entries if entry["split"] == split][:target])
    for entry in selected_entries:
        if entry["foundation_response_summary"]["all_replies_solved"]:
            stats["all_reply_bridge_count"] += 1
        elif entry["foundation_response_summary"]["any_replies_solved"]:
            stats["partial_reply_bridge_count"] += 1
        stats["any_reply_bridge_count"] += int(entry["foundation_response_summary"]["any_replies_solved"])
    stats["full_pool_entry_count"] = len(selected_entries)
    stats["full_pool_train_count"] = sum(1 for entry in selected_entries if entry["split"] == "train")
    stats["full_pool_heldout_count"] = sum(1 for entry in selected_entries if entry["split"] == "heldout")
    stats["full_pool_regression_count"] = sum(1 for entry in selected_entries if entry["split"] == "regression")
    stats["minimum_full_pool_completed"] = (
        stats["full_pool_train_count"] >= cfg.minimum_train_count
        and stats["full_pool_heldout_count"] >= cfg.minimum_heldout_count
        and stats["full_pool_regression_count"] >= cfg.minimum_regression_count
    )
    stats["target_full_pool_completed"] = (
        stats["full_pool_train_count"] >= cfg.bridge_frontier_train_count
        and stats["full_pool_heldout_count"] >= cfg.bridge_frontier_heldout_count
        and stats["full_pool_regression_count"] >= cfg.generic_edge_safety_regression_count
    )
    stats["average_generation_attempts_per_accepted_entry"] = stats["generation_attempts"] / max(1, stats["accepted_pool_entries"])
    stats["acceptance_rate"] = stats["accepted_pool_entries"] / max(1, stats["generation_attempts"])
    _write_full_pool_index(Path(cfg.full_pool_index_path), selected_entries, stats, cfg, foundation_hash, cache_hash)
    return selected_entries, stats


def _generate_full_split_entries(
    cache: _FoundationResponseCache,
    *,
    anchor_boards: tuple[str, ...],
    excluded: set[str],
    split: str,
    needed: int,
    seed: int,
    deadline: float,
    cfg: FullFoundationFrontierPoolResumeConfig,
    tg28c_cfg: FrozenFoundationResponseCacheBridgeRetrievalConfig,
    foundation_hash: str,
    cache_hash: str,
    seen: set[str],
    pool_path: Path,
    stats: dict[str, Any],
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    seed_boards = _foundation_backed_seed_boards(rng, anchor_boards, max_boards=max(8, needed * 4))
    compact_boards = _compact_entry_boards(cfg)
    seed_index = 0
    compact_index = 0
    accepted: list[dict[str, Any]] = []
    attempts = 0
    while len(accepted) < needed and attempts < cfg.max_generation_attempts:
        if time.perf_counter() >= deadline:
            stats["timeout_count"] += 1
            break
        attempts += 1
        stats["generation_attempts"] += 1
        if compact_index < len(compact_boards):
            board = compact_boards[compact_index]
            compact_index += 1
            method = "accepted_entry_mutation"
        elif seed_index < len(seed_boards):
            board = seed_boards[seed_index]
            seed_index += 1
            method = "indexed_anchor_neighborhood"
        else:
            stats["seed_pool_exhaustion_count"] += int(seed_index == len(seed_boards))
            seed_index += 1
            board = _anchor_predecessor_board(rng, anchor_boards)
            method = "rejection_aware_anchor_sampling"
        if board is None:
            board = _random_edge_board(rng)
            method = "geometry_bucket_sampling"
        if board is None:
            _reject(stats, "invalid")
            continue
        fen = board.fen()
        if fen in excluded:
            stats["duplicate_rejections"] += 1
            _reject(stats, "duplicate")
            continue
        if _mate_moves(board) or _forced_mate_in_two_first_moves(board):
            stats["rejected_direct_foundation"] += 1
            _reject(stats, "direct_foundation")
            continue
        cheap_rows = _cheap_candidate_rows(board, {})
        safe_count = sum(1 for row in cheap_rows if row["safety_ok"] and row["after_features"]["stalemate_after"] == 0.0)
        if safe_count <= 0:
            stats["safety_filter_rejections"] += 1
            _reject(stats, "no_legal_safe_candidate")
            continue
        before_queries = cache.query_count
        rows = _cache_candidate_rows(cache, board, tg28c_cfg, {}, {}, cache_retrieval_enabled=True)
        stats["cache_queries_run"] += cache.query_count - before_queries
        stats["live_foundation_queries_run"] = cache.query_count
        stats["deep_reply_checks_run"] += sum(int(row.get("reply_total", 0)) for row in rows)
        bridge_rows = [row for row in rows if row["safety_ok"] and row["reply_envelope_foundation_reachable"]]
        if not bridge_rows:
            stats["no_foundation_response_rejections"] += 1
            _reject(stats, "safe_candidates_exist_but_no_foundation_response")
            continue
        best = max(bridge_rows, key=lambda row: (row["reply_envelope_foundation_coverage_rate"], row["cheap_score"], row["move"]))
        entry = _pool_entry(
            board,
            best,
            split=split,
            seed=seed,
            method=method,
            legal_candidate_count=len(cheap_rows),
            safe_candidate_count=safe_count,
            cfg=_as_tg28e_config(cfg),
            foundation_hash=foundation_hash,
            cache_hash=cache_hash,
        )
        key = _dedupe_key(entry)
        if key in seen:
            stats["duplicate_rejections"] += 1
            _reject(stats, "duplicate")
            continue
        seen.add(key)
        accepted.append(entry)
        excluded.add(fen)
        stats["accepted_pool_entries"] += 1
        _append_pool_entry(pool_path, entry)
        _write_progress(cfg, {
            "phase": "full_pool_generation",
            "split": split,
            "accepted_for_split": len(accepted),
            "needed_for_split": needed,
            "generation_attempts": stats["generation_attempts"],
            "accepted_pool_entries": stats["accepted_pool_entries"],
            "resumed_pool_entries": stats["resumed_pool_entries"],
        })
    return accepted


def _decision(
    cfg: FullFoundationFrontierPoolResumeConfig,
    *,
    foundation_sanity: dict[str, Any],
    cache: _FoundationResponseCache,
    equivalence: dict[str, Any],
    pool_stats: dict[str, Any],
    frontier_eval: dict[str, Any],
    generic_eval: dict[str, Any],
    ablations: dict[str, Any],
    scheduler_equivalence: dict[str, Any],
    training: dict[str, Any],
    foundation_before_pool: dict[str, int],
    foundation_after_pool: dict[str, int],
    foundation_before_training: dict[str, int],
    foundation_after_training: dict[str, int],
    foundation_before_eval: dict[str, int],
    foundation_after_eval: dict[str, int],
    timings: dict[str, float],
) -> dict[str, Any]:
    pool_m3_delta = foundation_after_pool["m3"] - foundation_before_pool["m3"]
    pool_m4_delta = foundation_after_pool["m4"] - foundation_before_pool["m4"]
    train_m3_delta = foundation_after_training["m3"] - foundation_before_training["m3"]
    train_m4_delta = foundation_after_training["m4"] - foundation_before_training["m4"]
    eval_m3_delta = foundation_after_eval["m3"] - foundation_before_eval["m3"]
    eval_m4_delta = foundation_after_eval["m4"] - foundation_before_eval["m4"]
    full_config = _full_tg27b_config_used(_as_tg28e_config(cfg))
    selected_bridge = frontier_eval["selected_move_count"] > 0 and frontier_eval["reply_envelope_foundation_reachable_count"] > 0
    ablation_ok = _ablation_reduces(ablations, "mask_foundation_response_terminals") and _ablation_reduces(ablations, "mask_bridge_pressure_terminals")
    stable = (
        equivalence["foundation_cache_live_mismatch_count"] == 0
        and pool_m3_delta == 0
        and train_m3_delta == 0
        and eval_m3_delta == 0
        and scheduler_equivalence["mismatch_count"] == 0
    )
    full_advancement = (
        full_config
        and stable
        and pool_stats["minimum_full_pool_completed"]
        and selected_bridge
        and frontier_eval["same_graph_foundation_continuation_count"] > 0
        and ablation_ok
        and frontier_eval["rook_blunder_count"] == 0
        and generic_eval["rook_blunder_count"] == 0
    )
    diagnostic_pass = (
        full_config
        and stable
        and pool_stats["full_pool_entry_count"] > pool_stats["resumed_pool_entries"]
        and not full_advancement
    )
    return {
        "checkpoint_pass": full_advancement or diagnostic_pass,
        "checkpoint_interpretation": (
            "full_tg27b_persisted_pool_graph_mediated_bridge_handoff"
            if full_advancement
            else "full_tg27b_pool_resume_indexed_generation_diagnostic_pass"
            if diagnostic_pass
            else "full_tg27b_pool_resume_checkpoint_failed"
        ),
        "foundation_frozen": True,
        "full_tg27b_config_used": full_config,
        "compact_fallback_used": not full_config,
        "resumed_from_existing_full_pool": pool_stats["resumed_pool_entries"] > 0,
        "full_pool_path": cfg.full_pool_path,
        "full_pool_index_path": cfg.full_pool_index_path,
        "full_pool_entry_count": pool_stats["full_pool_entry_count"],
        "full_pool_train_count": pool_stats["full_pool_train_count"],
        "full_pool_heldout_count": pool_stats["full_pool_heldout_count"],
        "full_pool_regression_count": pool_stats["full_pool_regression_count"],
        "minimum_full_pool_completed": pool_stats["minimum_full_pool_completed"],
        "target_full_pool_completed": pool_stats["target_full_pool_completed"],
        "foundation_cache_live_mismatch_count": equivalence["foundation_cache_live_mismatch_count"],
        "foundation_cache_used_as_memoized_graph_response": True,
        "foundation_cache_used_as_provider": False,
        "foundation_m3_updates_during_pool_generation": pool_m3_delta,
        "foundation_m4_promotions_during_pool_generation": pool_m4_delta,
        "foundation_m3_updates_during_bridge_training": train_m3_delta,
        "foundation_m4_promotions_during_bridge_training": train_m4_delta,
        "foundation_m3_updates_during_eval": eval_m3_delta,
        "foundation_m4_promotions_during_eval": eval_m4_delta,
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
        "generation_attempts": pool_stats["generation_attempts"],
        "accepted_pool_entries": pool_stats["accepted_pool_entries"],
        "resumed_pool_entries": pool_stats["resumed_pool_entries"],
        "duplicate_rejections": pool_stats["duplicate_rejections"],
        "safety_filter_rejections": pool_stats["safety_filter_rejections"],
        "no_foundation_response_rejections": pool_stats["no_foundation_response_rejections"],
        "seed_pool_exhaustion_count": pool_stats["seed_pool_exhaustion_count"],
        "timeout_count": pool_stats["timeout_count"],
        "acceptance_rate": pool_stats["acceptance_rate"],
        "average_seconds_per_accepted_entry": timings["full_pool_generation_seconds"] / max(1, pool_stats["accepted_pool_entries"]),
        "average_generation_attempts_per_accepted_entry": pool_stats["average_generation_attempts_per_accepted_entry"],
        "bridge_candidate_generated_count": frontier_eval["bridge_candidate_generated_count"],
        "no_bridge_candidate_generated_count": frontier_eval["no_bridge_candidate_generated_count"],
        "selected_move_count": frontier_eval["selected_move_count"],
        "null_move_count": frontier_eval["null_move_count"],
        "reply_envelope_foundation_reachable_count": frontier_eval["reply_envelope_foundation_reachable_count"],
        "reply_envelope_foundation_coverage_rate": frontier_eval["reply_envelope_foundation_coverage_rate"],
        "foundation_handoff_conversion_count": frontier_eval["foundation_handoff_conversion_count"],
        "same_graph_foundation_continuation_count": frontier_eval["same_graph_foundation_continuation_count"],
        "edge_fence_success_rate": frontier_eval["edge_fence_success_rate"],
        "confinement_area_improvement_rate": frontier_eval["confinement_area_improvement_rate"],
        "black_king_mobility_reduction_rate": frontier_eval["black_king_mobility_reduction_rate"],
        "rook_blunder_count": frontier_eval["rook_blunder_count"],
        "stalemate_avoidance_rate": frontier_eval["stalemate_avoidance_rate"],
        "phase_timings": timings,
        "cache_queries_run": pool_stats["cache_queries_run"] + frontier_eval["cache_queries_run"],
        "live_foundation_queries_run": cache.query_count,
        "deep_reply_checks_run": pool_stats["deep_reply_checks_run"] + frontier_eval["deep_reply_checks_run"],
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "edge_only_m3_update_count": training["edge_only_m3_update_count"],
        "bridge_terminal_m3_update_count": training["bridge_terminal_m3_update_count"],
        "m4_promotion_count_by_terminal_kind_edge_bridge_only": {},
        "ablation_results": ablations,
        "top_rejection_buckets": dict(sorted(pool_stats["top_rejection_buckets"].items(), key=lambda item: item[1], reverse=True)[:8]),
        "compact_comparison_available": Path("reports/autogrowth/krk_autogrowth_tg28e_persisted_foundation_backed_frontier_pool.json").exists(),
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


def _compact_comparison(cfg: FullFoundationFrontierPoolResumeConfig) -> dict[str, Any]:
    path = Path("reports/autogrowth/krk_autogrowth_tg28e_persisted_foundation_backed_frontier_pool.json")
    if not path.exists():
        return {"available": False}
    data = json.loads(path.read_text(encoding="utf-8"))
    decision = data["decision"]
    return {
        "available": True,
        "artifact_path": str(path),
        "pool_entry_count": decision["pool_entry_count"],
        "generation_attempts": decision["generation_attempts"],
        "acceptance_rate": decision["accepted_pool_entries"] / max(1, decision["generation_attempts"]),
        "selected_move_count": decision["selected_move_count"],
        "reply_envelope_foundation_reachable_count": decision["reply_envelope_foundation_reachable_count"],
        "same_graph_foundation_continuation_count": decision["same_graph_foundation_continuation_count"],
        "rook_blunder_count": decision["rook_blunder_count"],
        "stalemate_avoidance_rate": decision["stalemate_avoidance_rate"],
        "ablation_selected_counts": {
            name: result.get("selected_move_count")
            for name, result in decision.get("ablation_results", {}).items()
        },
    }


def _compact_entry_boards(cfg: FullFoundationFrontierPoolResumeConfig) -> list[chess.Board]:
    boards = []
    for entry in _load_any_pool_entries(Path(cfg.compact_pool_path)):
        for key in ("position_fen", "after_candidate_fen"):
            try:
                board = chess.Board(entry[key])
            except (KeyError, ValueError):
                continue
            if board.turn == chess.WHITE and not board.is_game_over():
                boards.append(board)
    return boards


def _write_full_pool_index(
    path: Path,
    entries: list[dict[str, Any]],
    stats: dict[str, Any],
    cfg: FullFoundationFrontierPoolResumeConfig,
    foundation_hash: str,
    cache_hash: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "tg28f_full_foundation_frontier_pool_index.v0",
        "pool_path": cfg.full_pool_path,
        "foundation_config_hash": foundation_hash,
        "cache_config_hash": cache_hash,
        "entry_count": len(entries),
        "split_counts": {
            "train": sum(1 for entry in entries if entry["split"] == "train"),
            "heldout": sum(1 for entry in entries if entry["split"] == "heldout"),
            "regression": sum(1 for entry in entries if entry["split"] == "regression"),
        },
        "entry_ids_by_split": {
            split: [entry["pool_entry_id"] for entry in entries if entry["split"] == split]
            for split in ("train", "heldout", "regression")
        },
        "stats": stats,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _anchor_descriptors(board: chess.Board) -> dict[str, Any]:
    bk = board.king(chess.BLACK)
    wk = board.king(chess.WHITE)
    rook = _white_rook_square(board)
    if bk is None or wk is None:
        return {}
    return {
        "black_king_edge_distance": _black_edge_distance(board),
        "black_king_mobility": _black_king_mobility(board),
        "confinement_area": _confinement_area(board, rook, bk),
        "kings_distance": chess.square_distance(wk, bk),
        "rook_square": None if rook is None else chess.square_name(rook),
        "rook_file": None if rook is None else chess.square_file(rook),
        "rook_rank": None if rook is None else chess.square_rank(rook),
        "rook_safety": None if rook is None else not board.is_attacked_by(chess.BLACK, rook),
    }


def _foundation_response_type(response: dict[str, Any]) -> str:
    if response["foundation_mate1_recognized"]:
        return "Mate_In_1"
    if response["foundation_mate2_recognized"] or response["foundation_chain_success"]:
        return "Mate_In_2"
    return "none"


def _reject(stats: dict[str, Any], bucket: str) -> None:
    stats["top_rejection_buckets"][bucket] = stats["top_rejection_buckets"].get(bucket, 0) + 1


def _counts(values) -> dict[str, int]:
    output: dict[str, int] = {}
    for value in values:
        output[value] = output.get(value, 0) + 1
    return output


def _load_any_pool_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def _canonical_position_key(board: chess.Board) -> str:
    return f"{board.board_fen()} {'w' if board.turn == chess.WHITE else 'b'}"


def _ablation_reduces(ablations: dict[str, Any], name: str) -> bool:
    if name not in ablations:
        return False
    return ablations[name].get("selected_move_count", 0) == 0 or ablations[name].get("reply_envelope_foundation_reachable_count", 0) == 0


def _as_tg28e_config(cfg: FullFoundationFrontierPoolResumeConfig) -> PersistedFoundationBackedFrontierPoolConfig:
    return PersistedFoundationBackedFrontierPoolConfig(
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
        pool_path=cfg.full_pool_path,
        pool_index_path=cfg.full_pool_index_path,
        progress_output=cfg.progress_output,
    )


def _write_progress(cfg: FullFoundationFrontierPoolResumeConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg28e_purity_boundary()
    boundary.update({
        "checkpoint": "TG28f",
        "full_tg27b_foundation_main_arm": True,
        "indexed_anchor_generation_trainer_side_only": True,
        "persisted_full_pool_used_as_provider": False,
    })
    return boundary
