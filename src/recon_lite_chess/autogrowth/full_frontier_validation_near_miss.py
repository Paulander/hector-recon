"""TG28g full frontier validation and near-miss audit."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import time
from pathlib import Path
from typing import Any

import chess

from .foundation_backed_bridge_frontier import _as_tg28c_config
from .frozen_foundation_bridge_pressure import _compact_foundation_sanity
from .frozen_foundation_edge_fence_reentry import (
    _black_edge_distance,
    _black_king_mobility,
    _build_tg27b_foundation,
    _confinement_area,
    _foundation_counts,
    _generate_edge_fence_positions,
    _white_rook_square,
)
from .frozen_foundation_response_cache_bridge_retrieval import (
    _FoundationResponseCache,
    _cache_candidate_rows,
    _evaluate_cache_bridge_layer,
    _train_cache_bridge_layer,
)
from .full_foundation_frontier_pool_resume import (
    FullFoundationFrontierPoolResumeConfig,
    _as_tg28e_config,
    _purity_boundary as _tg28f_purity_boundary,
)
from .internal_handoff_affordance_guard_audit import _mate2_cfg
from .native_quorum_mate2_chaining import _tg26u_config
from .native_quorum_materialization import _tg26t_config
from .persisted_foundation_backed_frontier_pool import (
    _as_tg28b_config,
    _as_tg28d_like_config,
    _config_hash,
    _foundation_config_payload,
    _full_tg27b_config_used,
)
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence


@dataclass(frozen=True)
class FullFrontierValidationNearMissConfig:
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
    near_miss_heldout_count: int = 8
    generic_edge_fence_count: int = 8
    full_pool_path: str = "reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl"
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg28g_full_frontier_validation_near_miss_progress.json"


@dataclass(frozen=True)
class FullFrontierValidationNearMissResult:
    config: FullFrontierValidationNearMissConfig
    pool_integrity: dict[str, Any]
    foundation_sanity: dict[str, Any]
    cache: dict[str, Any]
    bridge_training: dict[str, Any]
    evaluations: dict[str, Any]
    residual_dependency_audit: dict[str, Any]
    anchor_disjoint_validation: dict[str, Any]
    near_miss_negatives: dict[str, Any]
    generic_edge_regression: dict[str, Any]
    ablation_results: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    failure_buckets: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg28g_full_frontier_validation_near_miss.v0",
            "checkpoint": "TG28g_full_frontier_validation_near_miss",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "pool_integrity": self.pool_integrity,
            "foundation_sanity": self.foundation_sanity,
            "cache": self.cache,
            "bridge_training": self.bridge_training,
            "evaluations": self.evaluations,
            "residual_dependency_audit": self.residual_dependency_audit,
            "anchor_disjoint_validation": self.anchor_disjoint_validation,
            "near_miss_negatives": self.near_miss_negatives,
            "generic_edge_regression": self.generic_edge_regression,
            "ablation_results": self.ablation_results,
            "scheduler_equivalence": self.scheduler_equivalence,
            "failure_buckets": self.failure_buckets,
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


def run_full_frontier_validation_near_miss(
    *,
    config: FullFrontierValidationNearMissConfig | None = None,
) -> FullFrontierValidationNearMissResult:
    cfg = config or FullFrontierValidationNearMissConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    pool_entries = _load_jsonl(Path(cfg.full_pool_path))
    tg28f_cfg = _as_tg28f_config(cfg)
    tg28c_cfg = _as_tg28c_config(_as_tg28d_like_config(_as_tg28e_config(tg28f_cfg)))
    foundation_hash = _config_hash(_foundation_config_payload(_as_tg28e_config(tg28f_cfg)))
    cache_hash = _config_hash(asdict(tg28c_cfg))
    pool_integrity = _pool_integrity(pool_entries, pool_path=cfg.full_pool_path, foundation_hash=foundation_hash, cache_hash=cache_hash)
    _write_progress(cfg, {"phase": "pool_loaded", **{k: pool_integrity[k] for k in ("full_pool_entry_count", "train_count", "heldout_count", "regression_count")}})

    start = time.perf_counter()
    foundation = _build_tg27b_foundation(_as_tg28b_config(tg28c_cfg))
    timings["foundation_build_seconds"] = round(time.perf_counter() - start, 6)
    graph = foundation["graph"]
    mate1_train = foundation["mate1_train"]
    mate1_heldout = foundation["mate1_heldout"]
    mate2_heldout = foundation["mate2_heldout"]
    mate2_cfg = _mate2_cfg(foundation["internal_cfg"])
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

    train_entries = tuple(entry for entry in pool_entries if entry.get("split") == "train")
    heldout_entries = tuple(entry for entry in pool_entries if entry.get("split") == "heldout")
    regression_entries = tuple(entry for entry in pool_entries if entry.get("split") == "regression")
    train_fens = tuple(entry["position_fen"] for entry in train_entries)
    heldout_fens = tuple(entry["position_fen"] for entry in heldout_entries)
    regression_fens = tuple(entry["position_fen"] for entry in regression_entries)

    foundation_before_training = _foundation_counts(graph)
    edge_weights: dict[str, float] = {}
    bridge_weights: dict[str, float] = {}
    start = time.perf_counter()
    training = _train_cache_bridge_layer(cache, train_fens, tg28c_cfg, edge_weights, bridge_weights)
    timings["bridge_training_seconds"] = round(time.perf_counter() - start, 6)
    foundation_after_training = _foundation_counts(graph)
    _write_progress(cfg, {
        "phase": "bridge_training_complete",
        "edge_only_m3_update_count": training["edge_only_m3_update_count"],
        "bridge_terminal_m3_update_count": training["bridge_terminal_m3_update_count"],
        "foundation_m3_delta": foundation_after_training["m3"] - foundation_before_training["m3"],
        "foundation_m4_delta": foundation_after_training["m4"] - foundation_before_training["m4"],
    })

    start = time.perf_counter()
    foundation_before_eval = _foundation_counts(graph)
    baseline_replay = _evaluate_cache_bridge_layer(graph, cache, heldout_fens, tg28c_cfg, edge_weights, {}, cache_retrieval_enabled=False)
    frontier_eval = _evaluate_cache_bridge_layer(graph, cache, heldout_fens, tg28c_cfg, edge_weights, bridge_weights)
    pool_regression_eval = _evaluate_cache_bridge_layer(graph, cache, regression_fens, tg28c_cfg, edge_weights, bridge_weights)
    residual_eval = _evaluate_cache_bridge_layer(
        graph,
        cache,
        heldout_fens,
        tg28c_cfg,
        edge_weights,
        bridge_weights,
        masks={"disable_reply_envelope_foundation_checks": True},
    )
    residual_audit = _residual_dependency_audit(heldout_entries, residual_eval)
    anchor_disjoint = _anchor_disjoint_validation(train_entries, heldout_entries, graph, cache, tg28c_cfg, edge_weights, bridge_weights)
    near_miss = _near_miss_negative_dataset(pool_entries, graph, cache, tg28c_cfg, edge_weights, bridge_weights, cfg)
    generic = _generic_edge_regression(pool_entries, graph, cache, tg28c_cfg, edge_weights, bridge_weights, cfg)
    ablations = _required_ablations(graph, cache, heldout_fens, tg28c_cfg, edge_weights, bridge_weights)
    equivalence = cache.live_equivalence_audit(max_samples=min(8, cfg.max_samples))
    scheduler_equivalence = (
        {"mismatch_count": 0, "skipped": True, "skip_reason": "max_ablation_positions_zero"}
        if cfg.max_ablation_positions <= 0
        else _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(mate2_cfg))), mate1_train, mate1_heldout)
    )
    foundation_after_eval = _foundation_counts(graph)
    timings["validation_eval_seconds"] = round(time.perf_counter() - start, 6)

    failure_buckets = _failure_buckets(
        pool_integrity=pool_integrity,
        residual_audit=residual_audit,
        near_miss=near_miss,
        generic=generic,
        equivalence=equivalence,
        frontier_eval=frontier_eval,
    )
    timings["artifact_write_seconds"] = 0.0
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)
    decision = _decision(
        cfg,
        pool_integrity=pool_integrity,
        foundation_sanity=foundation_sanity,
        cache=cache,
        equivalence=equivalence,
        frontier_eval=frontier_eval,
        residual_audit=residual_audit,
        anchor_disjoint=anchor_disjoint,
        near_miss=near_miss,
        generic=generic,
        ablations=ablations,
        scheduler_equivalence=scheduler_equivalence,
        training=training,
        foundation_before_training=foundation_before_training,
        foundation_after_training=foundation_after_training,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
        timings=timings,
        failure_buckets=failure_buckets,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {
        "checkpoint_pass": decision["checkpoint_pass"],
        "checkpoint_interpretation": decision["checkpoint_interpretation"],
        "frontier_heldout_selected_count": decision["frontier_heldout_selected_count"],
        "near_miss_false_positive_count": decision["near_miss_false_positive_count"],
    }})
    return FullFrontierValidationNearMissResult(
        config=cfg,
        pool_integrity=pool_integrity,
        foundation_sanity=foundation_sanity,
        cache=cache.to_dict(max_entries=cfg.max_samples),
        bridge_training=training,
        evaluations={
            "tg28f_baseline_replay_no_cache_retrieval": baseline_replay,
            "tg28f_frontier_heldout_replay": frontier_eval,
            "tg28f_pool_regression_replay": pool_regression_eval,
            "disable_reply_envelope_foundation_checks": residual_eval,
        },
        residual_dependency_audit=residual_audit,
        anchor_disjoint_validation=anchor_disjoint,
        near_miss_negatives=near_miss,
        generic_edge_regression=generic,
        ablation_results=ablations,
        scheduler_equivalence=scheduler_equivalence,
        failure_buckets=failure_buckets,
        phase_timings=timings,
        decision=decision,
    )


def _as_tg28f_config(cfg: FullFrontierValidationNearMissConfig) -> FullFoundationFrontierPoolResumeConfig:
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


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _pool_integrity(entries: list[dict[str, Any]], *, pool_path: str, foundation_hash: str, cache_hash: str) -> dict[str, Any]:
    train = [entry for entry in entries if entry.get("split") == "train"]
    heldout = [entry for entry in entries if entry.get("split") == "heldout"]
    regression = [entry for entry in entries if entry.get("split") == "regression"]
    train_anchors = {_anchor_identity(entry) for entry in train}
    heldout_anchors = {_anchor_identity(entry) for entry in heldout}
    train_lineage = {_lineage_identity(entry) for entry in train}
    heldout_lineage = {_lineage_identity(entry) for entry in heldout}
    train_exact = {_canonical_identity(entry) for entry in train}
    heldout_exact = {_canonical_identity(entry) for entry in heldout}
    train_geom = {_geometry_bucket_from_fen(entry["position_fen"]) for entry in train}
    heldout_geom = {_geometry_bucket_from_fen(entry["position_fen"]) for entry in heldout}
    return {
        "full_pool_path": pool_path,
        "full_pool_entry_count": len(entries),
        "train_count": len(train),
        "heldout_count": len(heldout),
        "regression_count": len(regression),
        "foundation_config_hash": foundation_hash,
        "cache_config_hash": cache_hash,
        "entry_foundation_hash_match_count": sum(int(entry.get("foundation_config_hash") == foundation_hash) for entry in entries),
        "entry_cache_hash_match_count": sum(int(entry.get("cache_config_hash") == cache_hash) for entry in entries),
        "anchor_count_train": len(train_anchors),
        "anchor_count_heldout": len(heldout_anchors),
        "anchor_overlap_count": len(train_anchors & heldout_anchors),
        "mutation_lineage_overlap_count": len(train_lineage & heldout_lineage),
        "exact_canonical_overlap_count": len(train_exact & heldout_exact),
        "geometry_bucket_overlap_count": len(train_geom & heldout_geom),
        "anchor_overlap_samples": list(train_anchors & heldout_anchors)[:4],
        "geometry_overlap_samples": [str(item) for item in list(train_geom & heldout_geom)[:4]],
    }


def _anchor_identity(entry: dict[str, Any]) -> str:
    replies = tuple(row.get("reply_fen") for row in entry.get("reply_rows", []))
    continuations = tuple(row.get("foundation_selected_move") for row in entry.get("reply_rows", []))
    return json.dumps({
        "after_candidate_fen": entry.get("after_candidate_fen"),
        "reply_targets": replies,
        "foundation_continuations": continuations,
    }, sort_keys=True)


def _lineage_identity(entry: dict[str, Any]) -> str:
    return str(entry.get("generation_method", "unknown"))


def _canonical_identity(entry: dict[str, Any]) -> str:
    return str(entry.get("canonical_position_key") or chess.Board(entry["position_fen"]).board_fen())


def _geometry_bucket_from_fen(fen: str) -> tuple[Any, ...]:
    board = chess.Board(fen)
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    rook = _white_rook_square(board)
    return (
        None if bk is None else chess.square_file(bk),
        None if bk is None else chess.square_rank(bk),
        None if rook is None else chess.square_file(rook),
        None if rook is None else chess.square_rank(rook),
        None if wk is None or bk is None else chess.square_distance(wk, bk),
        _black_edge_distance(board),
        _black_king_mobility(board),
    )


def _residual_dependency_audit(heldout_entries: tuple[dict[str, Any], ...], residual_eval: dict[str, Any]) -> dict[str, Any]:
    by_fen = {entry["position_fen"]: entry for entry in heldout_entries}
    records = []
    bridge_overreach = 0
    edge_only_false_positive = 0
    for row in residual_eval.get("samples", []):
        selected = row.get("selected")
        if not selected:
            continue
        entry = by_fen.get(row["fen"], {})
        envelope = selected.get("cache_reply_envelope") or {}
        immediate = selected.get("cache_immediate_after_state") or {}
        reply_disabled = envelope.get("source") == "disabled_or_invalid" and envelope.get("worst_reply_failure_reason") == "cache_retrieval_disabled"
        foundation_terminal = selected.get("foundation_response_terminal_state") in {"TRUE", "CONFIRMED"}
        mate2_chain = bool(selected.get("foundation_handoff_conversion") or selected.get("same_graph_foundation_continuation_count", 0) > 0)
        direct_foundation = bool(
            immediate
            and (
                immediate.get("foundation_mate1_recognized")
                or immediate.get("foundation_mate2_recognized")
                or immediate.get("foundation_chain_success")
            )
        )
        edge_only = (
            selected.get("edge_terminal_state") in {"TRUE", "CONFIRMED"}
            and selected.get("bridge_pressure_terminal_state") in {"TRUE", "CONFIRMED"}
            and not foundation_terminal
            and not direct_foundation
            and not mate2_chain
        )
        classification = "instrumentation_artifact"
        acceptable = True
        if foundation_terminal and mate2_chain:
            classification = "acceptable_mate2_chain_path_without_reply_envelope_metric"
        elif foundation_terminal or direct_foundation:
            classification = "acceptable_alternate_foundation_path"
        elif edge_only:
            classification = "edge_only_false_positive"
            acceptable = False
            edge_only_false_positive += 1
        elif not foundation_terminal and not direct_foundation:
            classification = "bridge_overreach_without_foundation_dependency"
            acceptable = False
            bridge_overreach += 1
        records.append({
            "fen": row["fen"],
            "selected_move": row.get("selected_move"),
            "candidate_move": selected.get("move"),
            "split": entry.get("split"),
            "pool_entry_id": entry.get("pool_entry_id"),
            "generation_method": entry.get("generation_method"),
            "reply_envelope_disabled": reply_disabled,
            "foundation_response_terminal_confirmed": foundation_terminal,
            "cached_direct_foundation_response_fired": direct_foundation,
            "mate_in_2_foundation_quorum_confirmed": bool(selected.get("foundation_handoff_reachable") or mate2_chain),
            "chain_confidence_terminal_confirmed": selected.get("bridge_pressure_terminal_state") in {"TRUE", "CONFIRMED"},
            "edge_fence_terminals_confirmed": selected.get("edge_terminal_state") in {"TRUE", "CONFIRMED"},
            "safety_veto_actuator_sufficient": (
                selected.get("safety_terminal_state") in {"TRUE", "CONFIRMED"}
                and selected.get("actuator_terminal_state") in {"TRUE", "CONFIRMED"}
            ),
            "formal_recon_engine_confirmation_path": {
                "quorum_script_id": selected.get("quorum_script_id"),
                "graph_confirmation_state": selected.get("graph_confirmation_state"),
                "formal_ticks_run": selected.get("formal_ticks_run"),
                "terminal_states": {
                    "edge": selected.get("edge_terminal_state"),
                    "action_delta": selected.get("action_delta_terminal_state"),
                    "attention": selected.get("attention_terminal_state"),
                    "safety": selected.get("safety_terminal_state"),
                    "bridge_pressure": selected.get("bridge_pressure_terminal_state"),
                    "foundation_response": selected.get("foundation_response_terminal_state"),
                    "actuator": selected.get("actuator_terminal_state"),
                },
            },
            "classification": classification,
            "acceptable": acceptable,
        })
    classifications = {record["classification"] for record in records}
    return {
        "residual_selection_without_reply_envelope_count": len(records),
        "residual_selection_classification": "none" if not records else ",".join(sorted(classifications)),
        "residual_selection_acceptable": all(record["acceptable"] for record in records),
        "bridge_overreach_count": bridge_overreach,
        "edge_only_false_positive_count": edge_only_false_positive,
        "instrumentation_repair_applied": True,
        "instrumentation_repair": "cache-backed reply-envelope ablation now emits disabled envelope instead of querying reply envelope",
        "records": records,
    }


def _anchor_disjoint_validation(
    train_entries: tuple[dict[str, Any], ...],
    heldout_entries: tuple[dict[str, Any], ...],
    graph,
    cache: _FoundationResponseCache,
    cfg,
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
) -> dict[str, Any]:
    train_anchor = {_anchor_identity(entry) for entry in train_entries}
    train_exact = {_canonical_identity(entry) for entry in train_entries}
    train_geom = {_geometry_bucket_from_fen(entry["position_fen"]) for entry in train_entries}
    train_lineage = {_lineage_identity(entry) for entry in train_entries}
    disjoint = [
        entry for entry in heldout_entries
        if _anchor_identity(entry) not in train_anchor
        and _canonical_identity(entry) not in train_exact
        and _geometry_bucket_from_fen(entry["position_fen"]) not in train_geom
        and _lineage_identity(entry) not in train_lineage
    ]
    fens = tuple(entry["position_fen"] for entry in disjoint)
    eval_result = _evaluate_cache_bridge_layer(graph, cache, fens, cfg, edge_weights, bridge_weights)
    return {
        "anchor_disjoint_heldout_count": len(disjoint),
        "anchor_disjoint_pool_entry_ids": [entry["pool_entry_id"] for entry in disjoint],
        "anchor_disjoint_eval": eval_result,
    }


def _near_miss_negative_dataset(
    pool_entries: list[dict[str, Any]],
    graph,
    cache: _FoundationResponseCache,
    cfg,
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
    audit_cfg: FullFrontierValidationNearMissConfig,
) -> dict[str, Any]:
    excluded = {entry["position_fen"] for entry in pool_entries}
    candidates = _generate_edge_fence_positions(
        count=max(1, audit_cfg.near_miss_heldout_count * 4),
        seed=audit_cfg.seed + 17,
        excluded=excluded,
        cfg=_as_tg28b_config(cfg),
    )
    near_fens = []
    candidate_count = 0
    for fen in candidates:
        board = chess.Board(fen)
        rows = _cache_candidate_rows(cache, board, cfg, edge_weights, bridge_weights, cache_retrieval_enabled=True)
        candidate_count += len(rows)
        has_safe_near = any(row["safety_ok"] and not row["reply_envelope_foundation_reachable"] for row in rows)
        has_foundation = any(row["reply_envelope_foundation_reachable"] or row["bounded_bridge_foundation_reachable"] for row in rows)
        if has_safe_near and not has_foundation:
            near_fens.append(fen)
        if len(near_fens) >= audit_cfg.near_miss_heldout_count:
            break
    eval_result = _evaluate_cache_bridge_layer(graph, cache, tuple(near_fens), cfg, edge_weights, bridge_weights)
    false_positive_count = eval_result["selected_move_count"]
    return {
        "near_miss_fens": near_fens[: audit_cfg.max_samples],
        "near_miss_position_count": len(near_fens),
        "near_miss_candidate_count": candidate_count,
        "near_miss_selected_count": eval_result["selected_move_count"],
        "near_miss_false_positive_count": false_positive_count,
        "near_miss_rejection_rate": 1.0 - (false_positive_count / max(1, len(near_fens))),
        "near_miss_failure_bucket_counts": eval_result["failure_bucket_counts"],
        "evaluation": eval_result,
    }


def _generic_edge_regression(
    pool_entries: list[dict[str, Any]],
    graph,
    cache: _FoundationResponseCache,
    cfg,
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
    audit_cfg: FullFrontierValidationNearMissConfig,
) -> dict[str, Any]:
    excluded = {entry["position_fen"] for entry in pool_entries}
    fens = _generate_edge_fence_positions(
        count=audit_cfg.generic_edge_fence_count,
        seed=audit_cfg.seed + 31,
        excluded=excluded,
        cfg=_as_tg28b_config(cfg),
    )
    evaluation = _evaluate_cache_bridge_layer(graph, cache, fens, cfg, edge_weights, bridge_weights)
    return {
        "generic_edge_fence_fens": list(fens)[: audit_cfg.max_samples],
        "generic_edge_fence_selected_move_count": evaluation["selected_move_count"],
        "generic_edge_fence_null_count": evaluation["null_move_count"],
        "generic_edge_fence_success_rate": evaluation["edge_fence_success_rate"],
        "generic_confinement_area_improvement_rate": evaluation["confinement_area_improvement_rate"],
        "generic_black_king_mobility_reduction_rate": evaluation["black_king_mobility_reduction_rate"],
        "generic_rook_blunder_count": evaluation["rook_blunder_count"],
        "generic_stalemate_avoidance_rate": evaluation["stalemate_avoidance_rate"],
        "generic_foundation_handoff_conversion_count": evaluation["foundation_handoff_conversion_count"],
        "evaluation": evaluation,
    }


def _required_ablations(graph, cache, heldout_fens, cfg, edge_weights, bridge_weights) -> dict[str, Any]:
    masks = {
        "mask_foundation_response_terminals": {"mask_frozen_foundation_response_terminals": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "disable_reply_envelope_foundation_checks": {"disable_reply_envelope_foundation_checks": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_frozen_mate2_foundation_quorum": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
    }
    return {
        name: _evaluate_cache_bridge_layer(graph, cache, tuple(heldout_fens), cfg, edge_weights, bridge_weights, masks=mask)
        for name, mask in masks.items()
    }


def _failure_buckets(*, pool_integrity, residual_audit, near_miss, generic, equivalence, frontier_eval) -> dict[str, Any]:
    buckets = {
        "residual_reply_envelope_dependency_leak": int(
            residual_audit["bridge_overreach_count"] > 0 or residual_audit["edge_only_false_positive_count"] > 0
        ),
        "anchor_overlap_leakage": int(pool_integrity["anchor_overlap_count"] > 0),
        "mutation_lineage_leakage": int(pool_integrity["mutation_lineage_overlap_count"] > 0),
        "near_miss_false_positive": near_miss["near_miss_false_positive_count"],
        "bridge_pressure_overgeneralized": int(near_miss["near_miss_false_positive_count"] > 0),
        "foundation_response_not_materialized": frontier_eval["failure_bucket_counts"].get("foundation_reachable_after_reply_but_not_detected", 0),
        "foundation_response_materialized_but_not_selected": frontier_eval["failure_bucket_counts"].get("foundation_response_materialized_but_not_selected", 0),
        "edge_safety_regression": generic["generic_rook_blunder_count"],
        "actuator_regression": 0,
        "candidate_cap_or_scheduler_blocked": frontier_eval["failure_bucket_counts"].get("candidate_cap_or_scheduler_blocked", 0),
        "cache_live_mismatch": equivalence["foundation_cache_live_mismatch_count"],
        "foundation_basin_too_sparse": frontier_eval["failure_bucket_counts"].get("safe_candidates_exist_but_no_foundation_response", 0),
        "timeout_or_throughput_blocked": 0,
        "unknown": 0,
    }
    return buckets


def _decision(
    cfg: FullFrontierValidationNearMissConfig,
    *,
    pool_integrity,
    foundation_sanity,
    cache: _FoundationResponseCache,
    equivalence,
    frontier_eval,
    residual_audit,
    anchor_disjoint,
    near_miss,
    generic,
    ablations,
    scheduler_equivalence,
    training,
    foundation_before_training,
    foundation_after_training,
    foundation_before_eval,
    foundation_after_eval,
    timings,
    failure_buckets,
) -> dict[str, Any]:
    train_m3_delta = foundation_after_training["m3"] - foundation_before_training["m3"]
    train_m4_delta = foundation_after_training["m4"] - foundation_before_training["m4"]
    eval_m3_delta = foundation_after_eval["m3"] - foundation_before_eval["m3"]
    eval_m4_delta = foundation_after_eval["m4"] - foundation_before_eval["m4"]
    disjoint_eval = anchor_disjoint["anchor_disjoint_eval"]
    ablation_dependency_ok = (
        ablations["mask_foundation_response_terminals"]["selected_move_count"] == 0
        and ablations["mask_bridge_pressure_terminals"]["selected_move_count"] == 0
        and ablations["mask_actuator_terminals"]["selected_move_count"] == 0
        and ablations["disable_reply_envelope_foundation_checks"]["selected_move_count"] == 0
        and ablations["mask_frozen_mate2_foundation_quorum"]["selected_move_count"] == 0
    )
    near_miss_limit = max(1, near_miss["near_miss_position_count"] // 4) if near_miss["near_miss_position_count"] else 0
    checkpoint_pass = (
        _full_tg27b_config_used(_as_tg28e_config(_as_tg28f_config(cfg)))
        and equivalence["foundation_cache_live_mismatch_count"] == 0
        and train_m3_delta == 0
        and train_m4_delta == 0
        and eval_m3_delta == 0
        and eval_m4_delta == 0
        and foundation_sanity["foundation_mate1_accuracy"] >= 1.0
        and foundation_sanity["foundation_mate2_conversion_rate"] >= 1.0
        and residual_audit["residual_selection_acceptable"]
        and residual_audit["bridge_overreach_count"] == 0
        and residual_audit["edge_only_false_positive_count"] == 0
        and disjoint_eval["selected_move_count"] > 0
        and disjoint_eval["reply_envelope_foundation_reachable_count"] > 0
        and disjoint_eval["same_graph_foundation_continuation_count"] > 0
        and near_miss["near_miss_false_positive_count"] <= near_miss_limit
        and generic["generic_rook_blunder_count"] == 0
        and generic["generic_stalemate_avoidance_rate"] >= 1.0
        and ablation_dependency_ok
        and scheduler_equivalence["mismatch_count"] == 0
    )
    return {
        "checkpoint_pass": checkpoint_pass,
        "checkpoint_interpretation": (
            "full_frontier_validated_with_clean_near_miss_and_dependency_audit"
            if checkpoint_pass
            else "full_frontier_validation_needs_repair_or_more_disjoint_data"
        ),
        "foundation_frozen": True,
        "foundation_cache_live_mismatch_count": equivalence["foundation_cache_live_mismatch_count"],
        "foundation_cache_used_as_memoized_graph_response": True,
        "foundation_cache_used_as_provider": False,
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
        "foundation_m3_updates_during_training": train_m3_delta,
        "foundation_m4_promotions_during_training": train_m4_delta,
        "foundation_m3_updates_during_eval": eval_m3_delta,
        "foundation_m4_promotions_during_eval": eval_m4_delta,
        "full_pool_entry_count": pool_integrity["full_pool_entry_count"],
        "train_count": pool_integrity["train_count"],
        "heldout_count": pool_integrity["heldout_count"],
        "regression_count": pool_integrity["regression_count"],
        "anchor_count_train": pool_integrity["anchor_count_train"],
        "anchor_count_heldout": pool_integrity["anchor_count_heldout"],
        "anchor_overlap_count": pool_integrity["anchor_overlap_count"],
        "mutation_lineage_overlap_count": pool_integrity["mutation_lineage_overlap_count"],
        "exact_canonical_overlap_count": pool_integrity["exact_canonical_overlap_count"],
        "geometry_bucket_overlap_count": pool_integrity["geometry_bucket_overlap_count"],
        "frontier_heldout_selected_count": frontier_eval["selected_move_count"],
        "frontier_heldout_count": frontier_eval["position_count"],
        "frontier_selection_rate": frontier_eval["selected_move_count"] / max(1, frontier_eval["position_count"]),
        "reply_envelope_foundation_reachable_count": frontier_eval["reply_envelope_foundation_reachable_count"],
        "reply_envelope_foundation_coverage_rate": frontier_eval["reply_envelope_foundation_coverage_rate"],
        "foundation_handoff_conversion_count": frontier_eval["foundation_handoff_conversion_count"],
        "same_graph_foundation_continuation_count": frontier_eval["same_graph_foundation_continuation_count"],
        "rook_blunder_count": frontier_eval["rook_blunder_count"],
        "stalemate_avoidance_rate": frontier_eval["stalemate_avoidance_rate"],
        "residual_selection_without_reply_envelope_count": residual_audit["residual_selection_without_reply_envelope_count"],
        "residual_selection_classification": residual_audit["residual_selection_classification"],
        "residual_selection_acceptable": residual_audit["residual_selection_acceptable"],
        "bridge_overreach_count": residual_audit["bridge_overreach_count"],
        "edge_only_false_positive_count": residual_audit["edge_only_false_positive_count"],
        "near_miss_candidate_count": near_miss["near_miss_candidate_count"],
        "near_miss_selected_count": near_miss["near_miss_selected_count"],
        "near_miss_false_positive_count": near_miss["near_miss_false_positive_count"],
        "near_miss_rejection_rate": near_miss["near_miss_rejection_rate"],
        "near_miss_failure_bucket_counts": near_miss["near_miss_failure_bucket_counts"],
        "generic_edge_fence_selected_move_count": generic["generic_edge_fence_selected_move_count"],
        "generic_edge_fence_null_count": generic["generic_edge_fence_null_count"],
        "generic_edge_fence_success_rate": generic["generic_edge_fence_success_rate"],
        "generic_confinement_area_improvement_rate": generic["generic_confinement_area_improvement_rate"],
        "generic_black_king_mobility_reduction_rate": generic["generic_black_king_mobility_reduction_rate"],
        "generic_rook_blunder_count": generic["generic_rook_blunder_count"],
        "generic_stalemate_avoidance_rate": generic["generic_stalemate_avoidance_rate"],
        "generic_foundation_handoff_conversion_count": generic["generic_foundation_handoff_conversion_count"],
        "generation_attempts": 0,
        "cache_queries_run": frontier_eval["cache_queries_run"] + disjoint_eval["cache_queries_run"] + near_miss["evaluation"]["cache_queries_run"] + generic["evaluation"]["cache_queries_run"],
        "live_foundation_queries_run": cache.query_count,
        "deep_reply_checks_run": frontier_eval["deep_reply_checks_run"] + disjoint_eval["deep_reply_checks_run"] + near_miss["evaluation"]["deep_reply_checks_run"] + generic["evaluation"]["deep_reply_checks_run"],
        "phase_timings": timings,
        "timeout_count": 0,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "edge_only_m3_update_count": training["edge_only_m3_update_count"],
        "bridge_terminal_m3_update_count": training["bridge_terminal_m3_update_count"],
        "m4_promotion_count_by_terminal_kind_edge_bridge_only": {},
        "ablation_results": ablations,
        "failure_buckets": failure_buckets,
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


def _write_progress(cfg: FullFrontierValidationNearMissConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg28f_purity_boundary()
    boundary.update({
        "checkpoint": "TG28g",
        "full_frontier_validation_only": True,
        "near_miss_dataset_trainer_side_only": True,
        "anchor_disjoint_labels_learner_visible": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "direct_provider_override": False,
    })
    return boundary
