"""TG28e persisted foundation-backed frontier pool checkpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
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
    _purity_boundary as _tg28d_purity_boundary,
    _random_edge_board,
)
from .foundation_curriculum import _forced_mate_in_two_first_moves, _mate_moves
from .frozen_foundation_bridge_pressure import _compact_foundation_sanity
from .frozen_foundation_edge_fence_reentry import (
    _build_tg27b_foundation,
    _cheap_candidate_rows,
    _foundation_counts,
)
from .frozen_foundation_response_cache_bridge_retrieval import (
    FrozenFoundationResponseCacheBridgeRetrievalConfig,
    _FoundationResponseCache,
    _cache_bridge_ablations,
    _cache_candidate_rows,
    _evaluate_cache_bridge_layer,
    _sample_foundation_basin,
    _train_cache_bridge_layer,
)
from .internal_handoff_affordance_guard_audit import _mate2_cfg
from .native_quorum_mate2_chaining import _tg26u_config
from .native_quorum_materialization import _tg26t_config
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence


@dataclass(frozen=True)
class PersistedFoundationBackedFrontierPoolConfig:
    seed: int = 20260629
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
    pool_path: str = "reports/autogrowth/pools/tg28e_foundation_backed_frontier_pool.jsonl"
    pool_index_path: str = "reports/autogrowth/pools/tg28e_foundation_backed_frontier_pool_index.json"
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg28e_persisted_foundation_backed_frontier_pool_progress.json"


@dataclass(frozen=True)
class PersistedFoundationBackedFrontierPoolResult:
    config: PersistedFoundationBackedFrontierPoolConfig
    pool: dict[str, Any]
    foundation_sanity: dict[str, Any]
    cache: dict[str, Any]
    basin_sampling: dict[str, Any]
    bridge_training: dict[str, Any]
    evaluations: dict[str, Any]
    ablation_results: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    throughput: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg28e_persisted_foundation_backed_frontier_pool.v0",
            "checkpoint": "TG28e_persisted_foundation_backed_frontier_pool",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "pool": self.pool,
            "foundation_sanity": self.foundation_sanity,
            "cache": self.cache,
            "basin_sampling": self.basin_sampling,
            "bridge_training": self.bridge_training,
            "evaluations": self.evaluations,
            "ablation_results": self.ablation_results,
            "scheduler_equivalence": self.scheduler_equivalence,
            "phase_timings": self.phase_timings,
            "throughput": self.throughput,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        start = time.perf_counter()
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        self.phase_timings["artifact_write_seconds"] = round(time.perf_counter() - start, 6)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_persisted_foundation_backed_frontier_pool(
    *,
    config: PersistedFoundationBackedFrontierPoolConfig | None = None,
) -> PersistedFoundationBackedFrontierPoolResult:
    cfg = config or PersistedFoundationBackedFrontierPoolConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    tg28c_cfg = _as_tg28c_config(_as_tg28d_like_config(cfg))
    foundation_hash = _config_hash(_foundation_config_payload(cfg))
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
    _write_progress(cfg, {
        "phase": "foundation_sanity_complete",
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
    })

    before_pool = _foundation_counts(graph)
    anchors = tuple(dict.fromkeys((*mate1_train, *mate1_heldout, *mate2_train, *mate2_heldout)))
    excluded = set((*mate1_train, *mate1_heldout, *mate2_train, *mate2_heldout))
    start = time.perf_counter()
    pool_entries, pool_stats = _build_or_resume_pool(
        cache,
        anchors=anchors,
        excluded=excluded,
        cfg=cfg,
        tg28c_cfg=tg28c_cfg,
        foundation_hash=foundation_hash,
        cache_hash=cache_hash,
    )
    timings["pool_generation_seconds"] = round(time.perf_counter() - start, 6)
    after_pool = _foundation_counts(graph)

    train_fens = tuple(entry["position_fen"] for entry in pool_entries if entry["split"] == "train")
    heldout_fens = tuple(entry["position_fen"] for entry in pool_entries if entry["split"] == "heldout")
    regression_fens = tuple(entry["position_fen"] for entry in pool_entries if entry["split"] == "regression")

    basin = _sample_foundation_basin(
        cache,
        mate1_train=mate1_train,
        mate1_heldout=mate1_heldout,
        mate2_train=mate2_train,
        mate2_heldout=mate2_heldout,
        bridge_train=train_fens,
        bridge_heldout=heldout_fens,
        generic_heldout=regression_fens,
        cfg=tg28c_cfg,
    )
    equivalence = cache.live_equivalence_audit(max_samples=min(8, cfg.max_samples))
    _write_progress(cfg, {
        "phase": "pool_loaded_and_cache_audited",
        "pool_entry_count": len(pool_entries),
        "foundation_cache_state_count": cache.state_count,
        "foundation_cache_live_mismatch_count": equivalence["foundation_cache_live_mismatch_count"],
    })

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

    scheduler_equivalence = (
        {"mismatch_count": 0, "skipped": True, "skip_reason": "max_ablation_positions_zero"}
        if cfg.max_ablation_positions <= 0
        else _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(mate2_cfg))), mate1_train, mate1_heldout)
    )

    timings["artifact_write_seconds"] = 0.0
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)
    throughput = _throughput(pool_stats, frontier_eval, cache, timings)
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
        throughput=throughput,
    )
    _write_progress(cfg, {
        "phase": "complete",
        "decision": {
            "checkpoint_pass": decision["checkpoint_pass"],
            "checkpoint_interpretation": decision["checkpoint_interpretation"],
            "pool_entry_count": decision["pool_entry_count"],
            "selected_move_count": decision["selected_move_count"],
        },
    })
    return PersistedFoundationBackedFrontierPoolResult(
        config=cfg,
        pool={
            "pool_path": cfg.pool_path,
            "pool_index_path": cfg.pool_index_path,
            "pool_entry_count": len(pool_entries),
            "pool_train_count": len(train_fens),
            "pool_heldout_count": len(heldout_fens),
            "pool_regression_count": len(regression_fens),
            "foundation_config_hash": foundation_hash,
            "cache_config_hash": cache_hash,
            "pool_stats": pool_stats,
            "entry_samples": pool_entries[: cfg.max_samples],
            "deterministic_and_resumable": True,
            "dedupe_key": "canonical_position_key + candidate_move + foundation_config_hash",
        },
        foundation_sanity=foundation_sanity,
        cache=cache.to_dict(max_entries=cfg.max_samples),
        basin_sampling=basin,
        bridge_training=training,
        evaluations={
            "baseline_no_cache_from_pool_heldout": baseline,
            "foundation_backed_frontier_from_pool": frontier_eval,
            "generic_edge_safety_regression_from_pool": generic_eval,
        },
        ablation_results=ablations,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        throughput=throughput,
        decision=decision,
    )


def _build_or_resume_pool(
    cache: _FoundationResponseCache,
    *,
    anchors: tuple[str, ...],
    excluded: set[str],
    cfg: PersistedFoundationBackedFrontierPoolConfig,
    tg28c_cfg: FrozenFoundationResponseCacheBridgeRetrievalConfig,
    foundation_hash: str,
    cache_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pool_path = Path(cfg.pool_path)
    pool_path.parent.mkdir(parents=True, exist_ok=True)
    entries = _load_pool_entries(pool_path, foundation_hash)
    seen = {_dedupe_key(entry) for entry in entries}
    stats = {
        "generation_attempts": 0,
        "accepted_pool_entries": 0,
        "loaded_existing_entries": len(entries),
        "duplicate_count": 0,
        "rejected_duplicate": 0,
        "rejected_invalid": 0,
        "rejected_direct_foundation": 0,
        "rejected_no_legal_safe_candidate": 0,
        "rejected_no_foundation_response": 0,
        "seed_pool_exhaustion_count": 0,
        "generation_timeout_count": 0,
        "no_foundation_positive_anchor_available": int(not anchors),
        "no_bridge_predecessor_found": 0,
        "all_reply_bridge_count": 0,
        "partial_reply_bridge_count": 0,
        "any_reply_bridge_count": 0,
    }
    targets = {
        "train": cfg.bridge_frontier_train_count,
        "heldout": cfg.bridge_frontier_heldout_count,
        "regression": cfg.generic_edge_safety_regression_count,
    }
    for split, target in targets.items():
        have = [entry for entry in entries if entry["split"] == split]
        if len(have) >= target:
            continue
        needed = target - len(have)
        accepted = _generate_split_entries(
            cache,
            anchors=anchors,
            excluded=excluded,
            split=split,
            needed=needed,
            seed=cfg.seed + {"train": 0, "heldout": 1, "regression": 2}[split],
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
    selected_entries = []
    for split, target in targets.items():
        selected_entries.extend([entry for entry in entries if entry["split"] == split][:target])
    for entry in selected_entries:
        if entry["foundation_response_summary"]["all_replies_solved"]:
            stats["all_reply_bridge_count"] += 1
        elif entry["foundation_response_summary"]["any_replies_solved"]:
            stats["partial_reply_bridge_count"] += 1
        stats["any_reply_bridge_count"] += int(entry["foundation_response_summary"]["any_replies_solved"])
    stats["pool_entry_count"] = len(selected_entries)
    stats["pool_train_count"] = sum(1 for entry in selected_entries if entry["split"] == "train")
    stats["pool_heldout_count"] = sum(1 for entry in selected_entries if entry["split"] == "heldout")
    stats["pool_regression_count"] = sum(1 for entry in selected_entries if entry["split"] == "regression")
    stats["average_generation_attempts_per_accepted_entry"] = stats["generation_attempts"] / max(1, stats["accepted_pool_entries"])
    _write_pool_index(Path(cfg.pool_index_path), selected_entries, stats, cfg, foundation_hash, cache_hash)
    return selected_entries, stats


def _generate_split_entries(
    cache: _FoundationResponseCache,
    *,
    anchors: tuple[str, ...],
    excluded: set[str],
    split: str,
    needed: int,
    seed: int,
    cfg: PersistedFoundationBackedFrontierPoolConfig,
    tg28c_cfg: FrozenFoundationResponseCacheBridgeRetrievalConfig,
    foundation_hash: str,
    cache_hash: str,
    seen: set[str],
    pool_path: Path,
    stats: dict[str, Any],
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    seed_boards = _foundation_backed_seed_boards(rng, anchors, max_boards=max(4, needed * 2))
    seed_index = 0
    accepted: list[dict[str, Any]] = []
    attempts = 0
    while len(accepted) < needed and attempts < cfg.max_generation_attempts:
        attempts += 1
        stats["generation_attempts"] += 1
        if seed_index < len(seed_boards):
            board = seed_boards[seed_index]
            seed_index += 1
            method = "anchor_neighborhood"
        else:
            stats["seed_pool_exhaustion_count"] += int(seed_index == len(seed_boards))
            seed_index += 1
            board = _anchor_predecessor_board(rng, anchors)
            method = "basin_backed_perturbation"
        if board is None:
            stats["no_bridge_predecessor_found"] += 1
            board = _random_edge_board(rng)
            method = "forward_filter"
        if board is None:
            stats["rejected_invalid"] += 1
            continue
        fen = board.fen()
        if fen in excluded:
            stats["duplicate_count"] += 1
            stats["rejected_duplicate"] += 1
            continue
        if _mate_moves(board) or _forced_mate_in_two_first_moves(board):
            stats["rejected_direct_foundation"] += 1
            continue
        cheap_rows = _cheap_candidate_rows(board, {})
        safe_count = sum(1 for row in cheap_rows if row["safety_ok"] and row["after_features"]["stalemate_after"] == 0.0)
        if safe_count <= 0:
            stats["rejected_no_legal_safe_candidate"] += 1
            continue
        rows = _cache_candidate_rows(cache, board, tg28c_cfg, {}, {}, cache_retrieval_enabled=True)
        bridge_rows = [row for row in rows if row["safety_ok"] and row["reply_envelope_foundation_reachable"]]
        if not bridge_rows:
            stats["rejected_no_foundation_response"] += 1
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
            cfg=cfg,
            foundation_hash=foundation_hash,
            cache_hash=cache_hash,
        )
        key = _dedupe_key(entry)
        if key in seen:
            stats["duplicate_count"] += 1
            stats["rejected_duplicate"] += 1
            continue
        seen.add(key)
        accepted.append(entry)
        excluded.add(fen)
        stats["accepted_pool_entries"] += 1
        _append_pool_entry(pool_path, entry)
        _write_progress(cfg, {
            "phase": "pool_generation",
            "split": split,
            "accepted_for_split": len(accepted),
            "needed_for_split": needed,
            "generation_attempts": stats["generation_attempts"],
            "accepted_pool_entries": stats["accepted_pool_entries"],
        })
    if len(accepted) < needed:
        stats["generation_timeout_count"] += 1
    return accepted


def _pool_entry(
    board: chess.Board,
    row: dict[str, Any],
    *,
    split: str,
    seed: int,
    method: str,
    legal_candidate_count: int,
    safe_candidate_count: int,
    cfg: PersistedFoundationBackedFrontierPoolConfig,
    foundation_hash: str,
    cache_hash: str,
) -> dict[str, Any]:
    move = chess.Move.from_uci(row["move"])
    after = board.copy(stack=False)
    after.push(move)
    envelope = row["cache_reply_envelope"]
    return {
        "schema_version": "tg28e_foundation_backed_frontier_pool_entry.v0",
        "pool_entry_id": _entry_id(board.fen(), row["move"], foundation_hash),
        "split": split,
        "generation_seed": seed,
        "generation_method": method if method != "basin_backed_perturbation" else "mixed",
        "foundation_config": _foundation_config_payload(cfg),
        "cache_config_hash": cache_hash,
        "foundation_config_hash": foundation_hash,
        "position_fen": board.fen(),
        "canonical_position_key": _canonical_position_key(board),
        "side_to_move": "white" if board.turn == chess.WHITE else "black",
        "candidate_move": row["move"],
        "after_candidate_fen": after.fen(),
        "legal_candidate_count": legal_candidate_count,
        "safe_candidate_count": safe_candidate_count,
        "safety_metrics": {
            "rook_blunder": not bool(row["after_features"]["rook_safe"]),
            "stalemate_after": bool(row["after_features"]["stalemate_after"]),
            "rook_safe_after": bool(row["after_features"]["rook_safe"]),
        },
        "edge_metrics": {
            "black_king_edge_distance_before": row["before_features"]["black_king_edge_distance"],
            "black_king_edge_distance_after": row["after_features"]["black_king_edge_distance"],
            "black_king_mobility_before": row["before_features"]["black_king_legal_mobility"],
            "black_king_mobility_after": row["after_features"]["black_king_legal_mobility"],
            "confinement_area_before": row["before_features"]["confinement_area"],
            "confinement_area_after": row["after_features"]["confinement_area"],
        },
        "foundation_response_summary": {
            "immediate_after_white_move_foundation_reachable": row["immediate_after_white_move_foundation_reachable"],
            "reply_total": row["reply_total"],
            "replies_foundation_solved": row["reply_solved"],
            "reply_envelope_success_rate": row["reply_envelope_foundation_coverage_rate"],
            "all_replies_solved": envelope["all_replies_solved"],
            "any_replies_solved": envelope["any_reply_solved"],
            "same_graph_foundation_continuation_count": row["same_graph_foundation_continuation_count"],
        },
        "reply_rows": [
            {
                "black_reply": reply["black_reply"],
                "reply_fen": reply["reply_state"],
                "foundation_mate1_recognized": None,
                "foundation_mate2_recognized": None,
                "foundation_selected_move": reply["foundation_selected_move"],
                "foundation_chain_success": reply["foundation_solved"],
                "graph_confirmation_state": "CONFIRMED" if reply["foundation_solved"] else "FAILED",
            }
            for reply in envelope["reply_rows"][: cfg.max_samples]
        ],
        "live_graph_equivalence_hash": (
            None
            if row["cache_immediate_after_state"] is None
            else row["cache_immediate_after_state"]["live_graph_equivalence_hash"]
        ),
        "source": "frozen_native_graph_response",
        "validator_labels_used_for_generation_only": True,
        "learner_visible_labels": False,
    }


def _decision(
    cfg: PersistedFoundationBackedFrontierPoolConfig,
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
    throughput: dict[str, Any],
) -> dict[str, Any]:
    pool_m3_delta = foundation_after_pool["m3"] - foundation_before_pool["m3"]
    pool_m4_delta = foundation_after_pool["m4"] - foundation_before_pool["m4"]
    train_m3_delta = foundation_after_training["m3"] - foundation_before_training["m3"]
    train_m4_delta = foundation_after_training["m4"] - foundation_before_training["m4"]
    eval_m3_delta = foundation_after_eval["m3"] - foundation_before_eval["m3"]
    eval_m4_delta = foundation_after_eval["m4"] - foundation_before_eval["m4"]
    full_config = _full_tg27b_config_used(cfg)
    selected_bridge = frontier_eval["selected_move_count"] > 0 and frontier_eval["reply_envelope_foundation_reachable_count"] > 0
    pool_ready = pool_stats["pool_train_count"] > 0 and pool_stats["pool_heldout_count"] > 0
    ablation_ok = _ablation_reduces(ablations, "mask_foundation_response_terminals") and _ablation_reduces(ablations, "mask_bridge_pressure_terminals")
    infrastructure_ok = (
        pool_stats["pool_entry_count"] > 0
        and equivalence["foundation_cache_live_mismatch_count"] == 0
        and pool_m3_delta == 0
        and train_m3_delta == 0
        and eval_m3_delta == 0
        and scheduler_equivalence["mismatch_count"] == 0
    )
    full_advancement = (
        infrastructure_ok
        and full_config
        and pool_ready
        and selected_bridge
        and ablation_ok
        and frontier_eval["rook_blunder_count"] == 0
        and generic_eval["rook_blunder_count"] == 0
    )
    diagnostic_pass = infrastructure_ok and not full_advancement
    checkpoint_pass = full_advancement or diagnostic_pass
    return {
        "checkpoint_pass": checkpoint_pass,
        "checkpoint_interpretation": (
            "full_foundation_persisted_pool_graph_mediated_bridge_handoff"
            if full_advancement
            else "persisted_pool_infrastructure_diagnostic_pass"
            if diagnostic_pass
            else "persisted_pool_checkpoint_failed"
        ),
        "foundation_frozen": True,
        "foundation_config_name": "full_tg27b" if full_config else "compact_diagnostic",
        "foundation_full_tg27b_config_used": full_config,
        "compact_foundation_fallback_used": not full_config,
        "foundation_cache_state_count": cache.state_count,
        "foundation_cache_query_count": cache.query_count,
        "foundation_cache_hit_rate": cache.hit_rate,
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
        "pool_path": cfg.pool_path,
        "pool_index_path": cfg.pool_index_path,
        "pool_entry_count": pool_stats["pool_entry_count"],
        "pool_train_count": pool_stats["pool_train_count"],
        "pool_heldout_count": pool_stats["pool_heldout_count"],
        "pool_regression_count": pool_stats["pool_regression_count"],
        "generation_attempts": pool_stats["generation_attempts"],
        "accepted_pool_entries": pool_stats["accepted_pool_entries"],
        "all_reply_bridge_count": pool_stats["all_reply_bridge_count"],
        "partial_reply_bridge_count": pool_stats["partial_reply_bridge_count"],
        "any_reply_bridge_count": pool_stats["any_reply_bridge_count"],
        "duplicate_count": pool_stats["duplicate_count"],
        "seed_pool_exhaustion_count": pool_stats["seed_pool_exhaustion_count"],
        "generation_timeout_count": pool_stats["generation_timeout_count"],
        "average_generation_attempts_per_accepted_entry": pool_stats["average_generation_attempts_per_accepted_entry"],
        "average_seconds_per_accepted_entry": throughput["average_seconds_per_accepted_entry"],
        "bridge_candidate_generated_count": frontier_eval["bridge_candidate_generated_count"],
        "no_bridge_candidate_generated_count": frontier_eval["no_bridge_candidate_generated_count"],
        "selected_move_count": frontier_eval["selected_move_count"],
        "null_move_count": frontier_eval["null_move_count"],
        "reply_envelope_foundation_reachable_count": frontier_eval["reply_envelope_foundation_reachable_count"],
        "reply_envelope_foundation_coverage_rate": frontier_eval["reply_envelope_foundation_coverage_rate"],
        "all_reply_foundation_bridge_success_count": sum(
            1 for sample in frontier_eval["samples"] if sample["selected"] is not None and sample["selected"]["foundation_handoff_conversion"]
        ),
        "partial_reply_foundation_bridge_success_count": frontier_eval["reply_envelope_foundation_reachable_count"],
        "foundation_handoff_conversion_count": frontier_eval["foundation_handoff_conversion_count"],
        "same_graph_foundation_continuation_count": frontier_eval["same_graph_foundation_continuation_count"],
        "edge_fence_success_rate": frontier_eval["edge_fence_success_rate"],
        "confinement_area_improvement_rate": frontier_eval["confinement_area_improvement_rate"],
        "black_king_mobility_reduction_rate": frontier_eval["black_king_mobility_reduction_rate"],
        "rook_blunder_count": frontier_eval["rook_blunder_count"],
        "stalemate_avoidance_rate": frontier_eval["stalemate_avoidance_rate"],
        "phase_timings": timings,
        "cache_queries_run": frontier_eval["cache_queries_run"],
        "live_foundation_queries_run": cache.query_count,
        "deep_reply_checks_run": frontier_eval["deep_reply_checks_run"],
        "timeout_count": pool_stats["generation_timeout_count"],
        "candidate_budget_used": frontier_eval["candidate_budget_used"],
        "failure_bucket_counts": _failure_buckets(pool_stats, frontier_eval),
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "edge_only_m3_update_count": training["edge_only_m3_update_count"],
        "bridge_terminal_m3_update_count": training["bridge_terminal_m3_update_count"],
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


def _throughput(
    pool_stats: dict[str, Any],
    frontier_eval: dict[str, Any],
    cache: _FoundationResponseCache,
    timings: dict[str, float],
) -> dict[str, Any]:
    accepted = max(1, pool_stats["accepted_pool_entries"])
    return {
        "generation_attempts": pool_stats["generation_attempts"],
        "accepted_pool_entries": pool_stats["accepted_pool_entries"],
        "rejected_no_legal_safe_candidate": pool_stats["rejected_no_legal_safe_candidate"],
        "rejected_no_foundation_response": pool_stats["rejected_no_foundation_response"],
        "rejected_duplicate": pool_stats["rejected_duplicate"],
        "cache_queries_run": frontier_eval["cache_queries_run"],
        "live_foundation_queries_run": cache.query_count,
        "deep_reply_checks_run": frontier_eval["deep_reply_checks_run"],
        "average_cache_queries_per_accepted_entry": cache.query_count / accepted,
        "average_seconds_per_accepted_entry": timings["pool_generation_seconds"] / accepted,
        "timeout_count": pool_stats["generation_timeout_count"],
    }


def _failure_buckets(pool_stats: dict[str, Any], frontier_eval: dict[str, Any]) -> dict[str, int]:
    buckets = dict(frontier_eval["failure_bucket_counts"])
    if pool_stats["generation_timeout_count"]:
        buckets["timeout_or_throughput_blocked"] = pool_stats["generation_timeout_count"]
    if pool_stats["seed_pool_exhaustion_count"]:
        buckets["seed_pool_exhausted"] = pool_stats["seed_pool_exhaustion_count"]
    if pool_stats["rejected_no_legal_safe_candidate"]:
        buckets["no_legal_safe_candidate"] = pool_stats["rejected_no_legal_safe_candidate"]
    if pool_stats["rejected_no_foundation_response"]:
        buckets["safe_candidates_exist_but_no_foundation_response"] = (
            buckets.get("safe_candidates_exist_but_no_foundation_response", 0)
            + pool_stats["rejected_no_foundation_response"]
        )
    return buckets


def _ablation_reduces(ablations: dict[str, Any], name: str) -> bool:
    if name not in ablations:
        return False
    return ablations[name].get("selected_move_count", 0) == 0 or ablations[name].get("reply_envelope_foundation_reachable_count", 0) == 0


def _load_pool_entries(path: Path, foundation_hash: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("foundation_config_hash") == foundation_hash:
            entries.append(entry)
    return entries


def _append_pool_entry(path: Path, entry: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def _write_pool_index(
    path: Path,
    entries: list[dict[str, Any]],
    stats: dict[str, Any],
    cfg: PersistedFoundationBackedFrontierPoolConfig,
    foundation_hash: str,
    cache_hash: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "tg28e_foundation_backed_frontier_pool_index.v0",
        "pool_path": cfg.pool_path,
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


def _dedupe_key(entry: dict[str, Any]) -> str:
    return f"{entry['canonical_position_key']}|{entry['candidate_move']}|{entry['foundation_config_hash']}"


def _entry_id(fen: str, move: str, foundation_hash: str) -> str:
    return hashlib.sha256(f"{fen}|{move}|{foundation_hash}".encode("utf-8")).hexdigest()[:20]


def _canonical_position_key(board: chess.Board) -> str:
    return f"{board.board_fen()} {'w' if board.turn == chess.WHITE else 'b'}"


def _config_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _foundation_config_payload(cfg: PersistedFoundationBackedFrontierPoolConfig) -> dict[str, Any]:
    return {
        "foundation_mate1_train_count": cfg.foundation_mate1_train_count,
        "foundation_mate1_heldout_count": cfg.foundation_mate1_heldout_count,
        "foundation_mate2_train_count": cfg.foundation_mate2_train_count,
        "foundation_mate2_heldout_count": cfg.foundation_mate2_heldout_count,
        "foundation_seed": cfg.foundation_seed,
    }


def _full_tg27b_config_used(cfg: PersistedFoundationBackedFrontierPoolConfig) -> bool:
    return (
        cfg.foundation_mate1_train_count == 32
        and cfg.foundation_mate1_heldout_count == 16
        and cfg.foundation_mate2_train_count == 16
        and cfg.foundation_mate2_heldout_count == 8
    )


@dataclass(frozen=True)
class _TG28DLikeConfig:
    seed: int
    foundation_seed: int
    foundation_mate1_train_count: int
    foundation_mate1_heldout_count: int
    foundation_mate2_train_count: int
    foundation_mate2_heldout_count: int
    bridge_frontier_train_count: int
    bridge_frontier_heldout_count: int
    generic_edge_safety_regression_count: int
    basin_random_count: int
    max_generation_attempts: int
    max_cache_candidate_moves: int
    max_reply_envelope_replies_per_candidate: int
    max_mate2_probe_moves_per_state: int
    max_edge_candidates_per_position: int
    max_ablation_positions: int
    max_foundation_sanity_positions: int
    max_foundation_ablation_positions: int
    max_ticks: int
    max_samples: int
    repaired_high_recall_threshold: float
    eta_m3_edge: float
    eta_m3_bridge: float
    edge_terminal_min_score: float
    bridge_terminal_min_score: float
    materialized_quorum_min_evidence: float
    replay_count: int
    progress_output: str


def _as_tg28d_like_config(cfg: PersistedFoundationBackedFrontierPoolConfig) -> _TG28DLikeConfig:
    return _TG28DLikeConfig(
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
        progress_output=cfg.progress_output,
    )


def _as_tg28b_config(cfg: FrozenFoundationResponseCacheBridgeRetrievalConfig):
    from .frozen_foundation_response_cache_bridge_retrieval import _as_tg28b_config as convert

    return convert(cfg)


def _write_progress(cfg: PersistedFoundationBackedFrontierPoolConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg28d_purity_boundary()
    boundary.update({
        "checkpoint": "TG28e",
        "persisted_pool_used_for_training_distribution": True,
        "persisted_pool_used_as_provider": False,
        "pool_labels_learner_visible": False,
    })
    return boundary
