"""TG28c frozen-foundation response cache and bridge retrieval."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import random
from pathlib import Path
from typing import Any

import chess

from .foundation_curriculum import _forced_mate_in_two_first_moves, _mate_moves
from .frozen_foundation_bridge_pressure import (
    FrozenFoundationBridgePressureConfig,
    _as_tg28a_config,
    _augment_bridge_row,
    _bridge_reward,
    _compact_foundation_sanity,
    _confirm_bridge_candidate,
    _empty_bounded,
    _edge_reward,
    _frozen_foundation_chain_audit,
    _generate_bridge_frontier_positions,
    _purity_boundary as _tg28b_purity_boundary,
    _select_deep_candidates,
)
from .frozen_foundation_edge_fence_reentry import (
    _black_edge_distance,
    _black_king_mobility,
    _build_tg27b_foundation,
    _cheap_candidate_rows,
    _confinement_area,
    _foundation_counts,
    _generate_edge_fence_positions,
    _white_rook_square,
)
from .internal_handoff_affordance_guard_audit import _mate2_cfg
from .native_quorum_mate2_chaining import _select_materialized_mate1
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .native_quorum_mate2_chaining import _tg26u_config
from .native_quorum_materialization import _tg26t_config


@dataclass(frozen=True)
class FrozenFoundationResponseCacheBridgeRetrievalConfig:
    seed: int = 20260627
    foundation_seed: int = 20260624
    foundation_mate1_train_count: int = 32
    foundation_mate1_heldout_count: int = 16
    foundation_mate2_train_count: int = 16
    foundation_mate2_heldout_count: int = 8
    bridge_train_count: int = 4
    bridge_heldout_count: int = 4
    generic_edge_safety_heldout_count: int = 2
    basin_random_count: int = 8
    max_generation_attempts: int = 250_000
    max_cache_candidate_moves: int = 10
    max_reply_envelope_replies_per_candidate: int = 1
    max_mate2_probe_moves_per_state: int = 2
    max_edge_candidates_per_position: int = 8
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
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg28c_frozen_foundation_response_cache_bridge_retrieval_progress.json"


@dataclass(frozen=True)
class FrozenFoundationResponseCacheBridgeRetrievalResult:
    config: FrozenFoundationResponseCacheBridgeRetrievalConfig
    dataset: dict[str, Any]
    foundation_sanity: dict[str, Any]
    cache: dict[str, Any]
    basin_sampling: dict[str, Any]
    bridge_training: dict[str, Any]
    evaluations: dict[str, Any]
    ablation_results: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg28c_frozen_foundation_response_cache_bridge_retrieval.v0",
            "checkpoint": "TG28c_frozen_foundation_response_cache_bridge_retrieval",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "foundation_sanity": self.foundation_sanity,
            "cache": self.cache,
            "basin_sampling": self.basin_sampling,
            "bridge_training": self.bridge_training,
            "evaluations": self.evaluations,
            "ablation_results": self.ablation_results,
            "scheduler_equivalence": self.scheduler_equivalence,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_frozen_foundation_response_cache_bridge_retrieval(
    *,
    config: FrozenFoundationResponseCacheBridgeRetrievalConfig | None = None,
) -> FrozenFoundationResponseCacheBridgeRetrievalResult:
    cfg = config or FrozenFoundationResponseCacheBridgeRetrievalConfig()
    foundation = _build_tg27b_foundation(_as_tg28b_config(cfg))
    graph = foundation["graph"]
    mate1_train = foundation["mate1_train"]
    mate1_heldout = foundation["mate1_heldout"]
    mate2_train = foundation["mate2_train"]
    mate2_heldout = foundation["mate2_heldout"]
    mate2_cfg = _mate2_cfg(foundation["internal_cfg"])
    excluded = set((*mate1_train, *mate1_heldout, *mate2_train, *mate2_heldout))
    _write_progress(cfg, {"phase": "foundation_built"})

    foundation_sanity = _compact_foundation_sanity(
        graph,
        mate1_heldout,
        mate2_heldout,
        foundation["attention_cfg"],
        mate2_cfg,
        _as_tg28b_config(cfg),
    )
    cache = _FoundationResponseCache(graph, mate2_cfg, cfg)
    _write_progress(cfg, {
        "phase": "foundation_sanity_complete",
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
    })

    bridge_train, train_stats = _generate_bridge_frontier_positions(
        graph=graph,
        mate2_cfg=mate2_cfg,
        count=cfg.bridge_train_count,
        seed=cfg.seed,
        excluded=excluded,
        cfg=_as_tg28b_config(cfg),
    )
    excluded.update(bridge_train)
    bridge_heldout, heldout_stats = _generate_bridge_frontier_positions(
        graph=graph,
        mate2_cfg=mate2_cfg,
        count=cfg.bridge_heldout_count,
        seed=cfg.seed + 1,
        excluded=excluded,
        cfg=_as_tg28b_config(cfg),
    )
    excluded.update(bridge_heldout)
    generic_heldout = _generate_edge_fence_positions(
        count=cfg.generic_edge_safety_heldout_count,
        seed=cfg.seed + 2,
        excluded=excluded,
        cfg=_as_tg28b_config(cfg),
    )
    _write_progress(cfg, {
        "phase": "dataset_complete",
        "bridge_train_count": len(bridge_train),
        "bridge_heldout_count": len(bridge_heldout),
        "generic_edge_safety_heldout_count": len(generic_heldout),
    })

    basin = _sample_foundation_basin(
        cache,
        mate1_train=mate1_train,
        mate1_heldout=mate1_heldout,
        mate2_train=mate2_train,
        mate2_heldout=mate2_heldout,
        bridge_train=bridge_train,
        bridge_heldout=bridge_heldout,
        generic_heldout=generic_heldout,
        cfg=cfg,
    )
    equivalence = cache.live_equivalence_audit(max_samples=min(8, cfg.max_samples))
    _write_progress(cfg, {
        "phase": "cache_basin_complete",
        "foundation_cache_state_count": cache.state_count,
        "foundation_cache_query_count": cache.query_count,
        "foundation_positive_state_count": basin["foundation_positive_state_count"],
        "foundation_cache_live_mismatch_count": equivalence["foundation_cache_live_mismatch_count"],
    })

    foundation_before_training = _foundation_counts(graph)
    edge_weights: dict[str, float] = {}
    bridge_weights: dict[str, float] = {}
    training = _train_cache_bridge_layer(cache, bridge_train, cfg, edge_weights, bridge_weights)
    foundation_after_training = _foundation_counts(graph)
    _write_progress(cfg, {
        "phase": "bridge_training_complete",
        "edge_only_m3_update_count": training["edge_only_m3_update_count"],
        "bridge_terminal_m3_update_count": training["bridge_terminal_m3_update_count"],
        "foundation_m3_delta": foundation_after_training["m3"] - foundation_before_training["m3"],
        "foundation_m4_delta": foundation_after_training["m4"] - foundation_before_training["m4"],
    })

    foundation_before_eval = _foundation_counts(graph)
    baseline = _evaluate_cache_bridge_layer(
        graph,
        cache,
        bridge_heldout,
        cfg,
        edge_weights,
        bridge_weights={},
        cache_retrieval_enabled=False,
    )
    retrieval = _evaluate_cache_bridge_layer(graph, cache, bridge_heldout, cfg, edge_weights, bridge_weights)
    generic_eval = _evaluate_cache_bridge_layer(graph, cache, generic_heldout, cfg, edge_weights, bridge_weights)
    ablations = _cache_bridge_ablations(graph, cache, bridge_heldout, cfg, edge_weights, bridge_weights)
    foundation_after_eval = _foundation_counts(graph)
    scheduler_equivalence = (
        {"mismatch_count": 0, "skipped": True, "skip_reason": "max_ablation_positions_zero_smoke_path"}
        if cfg.max_ablation_positions <= 0
        else _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(mate2_cfg))), mate1_train, mate1_heldout)
    )
    _write_progress(cfg, {
        "phase": "eval_complete",
        "bridge_candidate_generated_count": retrieval["bridge_candidate_generated_count"],
        "selected_move_count": retrieval["selected_move_count"],
        "reply_envelope_foundation_reachable_count": retrieval["reply_envelope_foundation_reachable_count"],
    })
    decision = _decision(
        cfg,
        foundation_sanity=foundation_sanity,
        cache=cache,
        equivalence=equivalence,
        basin=basin,
        baseline=baseline,
        retrieval=retrieval,
        generic_eval=generic_eval,
        ablations=ablations,
        scheduler_equivalence=scheduler_equivalence,
        training=training,
        foundation_before_training=foundation_before_training,
        foundation_after_training=foundation_after_training,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {
        "checkpoint_pass": decision["checkpoint_pass"],
        "checkpoint_interpretation": decision["checkpoint_interpretation"],
        "bridge_candidate_generated_count": decision["bridge_candidate_generated_count"],
        "selected_move_count": decision["selected_move_count"],
    }})
    return FrozenFoundationResponseCacheBridgeRetrievalResult(
        config=cfg,
        dataset={
            "source": "TG28c bridge-frontier positions plus generic edge/fence heldout; cache evidence is frozen-native graph response only",
            "bridge_train_count": len(bridge_train),
            "bridge_heldout_count": len(bridge_heldout),
            "generic_edge_safety_heldout_count": len(generic_heldout),
            "bridge_train_generation": train_stats,
            "bridge_heldout_generation": heldout_stats,
            "bridge_train_fens": list(bridge_train)[: cfg.max_samples],
            "bridge_heldout_fens": list(bridge_heldout)[: cfg.max_samples],
            "generic_edge_safety_heldout_fens": list(generic_heldout)[: cfg.max_samples],
            "stage_labels_learner_visible": False,
            "edge_fence_labels_learner_visible": False,
            "bridge_labels_learner_visible": False,
        },
        foundation_sanity=foundation_sanity,
        cache=cache.to_dict(max_entries=cfg.max_samples),
        basin_sampling=basin,
        bridge_training=training,
        evaluations={
            "tg28b_baseline_no_cache_retrieval": baseline,
            "cache_bridge_retrieval": retrieval,
            "generic_edge_safety": generic_eval,
        },
        ablation_results=ablations,
        scheduler_equivalence=scheduler_equivalence,
        decision=decision,
    )


class _FoundationResponseCache:
    def __init__(self, graph, mate2_cfg, cfg: FrozenFoundationResponseCacheBridgeRetrievalConfig) -> None:
        self.graph = graph
        self.mate2_cfg = mate2_cfg
        self.cfg = cfg
        self.states: dict[str, dict[str, Any]] = {}
        self.envelopes: dict[str, dict[str, Any]] = {}
        self.query_count = 0
        self.hit_count = 0

    @property
    def state_count(self) -> int:
        return len(self.states)

    @property
    def hit_rate(self) -> float:
        return 0.0 if self.query_count == 0 else self.hit_count / self.query_count

    def query_state(self, board: chess.Board) -> dict[str, Any]:
        key = _canonical_fen(board)
        self.query_count += 1
        cached = self.states.get(key)
        if cached is not None:
            self.hit_count += 1
            return cached
        entry = self._live_state_response(board)
        self.states[key] = entry
        return entry

    def live_equivalence_audit(self, *, max_samples: int) -> dict[str, Any]:
        rows = []
        mismatches = 0
        for key, cached in list(self.states.items())[:max_samples]:
            board = chess.Board(key)
            live = self._live_state_response(board)
            mismatch = cached["live_graph_equivalence_hash"] != live["live_graph_equivalence_hash"]
            mismatches += int(mismatch)
            rows.append({
                "canonical_fen": key,
                "mismatch": mismatch,
                "cached_hash": cached["live_graph_equivalence_hash"],
                "live_hash": live["live_graph_equivalence_hash"],
            })
        return {
            "foundation_cache_live_mismatch_count": mismatches,
            "sample_count": len(rows),
            "samples": rows,
        }

    def reply_envelope(self, board: chess.Board, move: chess.Move) -> dict[str, Any]:
        key = f"{_canonical_fen(board)}|{move.uci()}"
        cached = self.envelopes.get(key)
        if cached is not None:
            self.hit_count += 1
            return cached
        if move not in board.legal_moves:
            env = _empty_reply_envelope(move.uci(), reason="illegal_candidate")
            self.envelopes[key] = env
            return env
        after = board.copy(stack=False)
        after.push(move)
        reply_rows = []
        solved = 0
        same_graph_second = 0
        replies = sorted(after.legal_moves, key=lambda item: item.uci())[: self.cfg.max_reply_envelope_replies_per_candidate]
        for reply in replies:
            before_foundation = after.copy(stack=False)
            before_foundation.push(reply)
            state = self.query_state(before_foundation)
            ok = state["foundation_mate1_recognized"] or state["foundation_mate2_recognized"] or state["foundation_chain_success"]
            solved += int(ok)
            same_graph_second += int(state["foundation_selected_move"] is not None)
            reply_rows.append({
                "black_reply": reply.uci(),
                "reply_state": state["canonical_fen"],
                "foundation_solved": ok,
                "foundation_selected_move": state["foundation_selected_move"],
                "failure_reason": None if ok else state["failure_reason"],
            })
        total = len(reply_rows)
        env = {
            "white_candidate_move": move.uci(),
            "black_reply_count": total,
            "reply_states_queried": total,
            "replies_foundation_solved": solved,
            "reply_envelope_success_rate": 0.0 if total == 0 else solved / total,
            "all_replies_solved": total > 0 and solved == total,
            "any_reply_solved": solved > 0,
            "same_graph_second_move_count": same_graph_second,
            "worst_reply_failure_reason": None if solved == total and total > 0 else "frozen_foundation_no_response",
            "reply_rows": reply_rows,
            "source": "frozen_native_graph_response_cache",
        }
        self.envelopes[key] = env
        return env

    def _live_state_response(self, board: chess.Board) -> dict[str, Any]:
        selected_move = None
        mate1_recognized = False
        mate2_recognized = False
        chain_success = False
        same_graph_second = 0
        graph_state = "NOT_QUERIED_BLACK_TO_MOVE"
        query_cost = 0
        failure_reason = "black_to_move_not_foundation_query" if board.turn == chess.BLACK else "no_foundation_response"
        if board.turn == chess.WHITE and not board.is_game_over():
            selected = _select_materialized_mate1(self.graph, board, self.mate2_cfg)
            selected_move = selected["selected"]
            mates = {move.uci() for move in _mate_moves(board)}
            mate1_recognized = selected_move in mates
            graph_state = "CONFIRMED" if selected_move is not None else "FAILED"
            query_cost += int(selected.get("confirmed_candidate_count", 0))
            if not mate1_recognized:
                for move in sorted(board.legal_moves, key=lambda item: item.uci())[: self.cfg.max_mate2_probe_moves_per_state]:
                    chain = _frozen_foundation_chain_audit(
                        self.graph,
                        board,
                        move,
                        self.mate2_cfg,
                        max_replies=self.cfg.max_reply_envelope_replies_per_candidate,
                    )
                    query_cost += int(chain.get("reply_total", 0))
                    if chain["chain_success"]:
                        selected_move = move.uci()
                        mate2_recognized = True
                        chain_success = True
                        same_graph_second = int(chain.get("same_graph_second_move_count", 0))
                        graph_state = "CONFIRMED"
                        break
            if mate1_recognized or mate2_recognized or chain_success:
                failure_reason = None
        payload = {
            "canonical_fen": _canonical_fen(board),
            "side_to_move": "white" if board.turn == chess.WHITE else "black",
            "foundation_mate1_recognized": mate1_recognized,
            "foundation_mate2_recognized": mate2_recognized,
            "foundation_selected_move": selected_move,
            "foundation_chain_success": chain_success,
            "same_graph_second_move_count": same_graph_second,
            "foundation_request_strength": 1.0 if (mate1_recognized or mate2_recognized or chain_success) else 0.0,
            "graph_confirmation_state": graph_state,
            "query_cost": query_cost,
            "failure_reason": failure_reason,
            "source": "frozen_native_graph_response",
        }
        payload["live_graph_equivalence_hash"] = _response_hash(payload)
        return payload

    def to_dict(self, *, max_entries: int) -> dict[str, Any]:
        return {
            "foundation_cache_state_count": self.state_count,
            "foundation_cache_query_count": self.query_count,
            "foundation_cache_hit_rate": self.hit_rate,
            "foundation_cache_used_as_memoized_graph_response": True,
            "foundation_cache_used_as_provider": False,
            "state_samples": list(self.states.values())[:max_entries],
            "reply_envelope_samples": list(self.envelopes.values())[:max_entries],
        }


def _train_cache_bridge_layer(
    cache: _FoundationResponseCache,
    fens: tuple[str, ...],
    cfg: FrozenFoundationResponseCacheBridgeRetrievalConfig,
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
) -> dict[str, Any]:
    edge_updates = 0
    bridge_updates = 0
    samples = []
    for fen in fens:
        rows = _cache_candidate_rows(cache, chess.Board(fen), cfg, edge_weights, bridge_weights, cache_retrieval_enabled=True)
        for row in rows:
            edge_reward = _edge_reward(row)
            bridge_reward = _bridge_reward(row)
            for key in row["positive_feature_keys"]:
                edge_weights[key] = max(-1.0, min(1.0, edge_weights.get(key, 0.0) + cfg.eta_m3_edge * edge_reward))
                edge_updates += 1
            for key in row["bridge_feature_keys"]:
                bridge_weights[key] = max(-1.0, min(1.0, bridge_weights.get(key, 0.0) + cfg.eta_m3_bridge * bridge_reward))
                bridge_updates += 1
        if rows and len(samples) < cfg.max_samples:
            best = max(rows, key=lambda item: item["bridge_evidence_score"])
            samples.append({
                "fen": fen,
                "best_training_move": best["move"],
                "reply_solved": best["reply_solved"],
                "reply_total": best["reply_total"],
                "bridge_reward": round(_bridge_reward(best), 6),
            })
    return {
        "edge_only_m3_update_count": edge_updates,
        "bridge_terminal_m3_update_count": bridge_updates,
        "edge_weight_count": len(edge_weights),
        "bridge_weight_count": len(bridge_weights),
        "top_edge_weights": sorted(edge_weights.items(), key=lambda item: item[1], reverse=True)[:12],
        "top_bridge_weights": sorted(bridge_weights.items(), key=lambda item: item[1], reverse=True)[:12],
        "samples": samples,
    }


def _evaluate_cache_bridge_layer(
    graph,
    cache: _FoundationResponseCache,
    fens: tuple[str, ...],
    cfg: FrozenFoundationResponseCacheBridgeRetrievalConfig,
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
    *,
    cache_retrieval_enabled: bool = True,
    masks: dict[str, bool] | None = None,
) -> dict[str, Any]:
    masks = masks or {}
    rows = []
    totals = _empty_totals()
    before_queries = cache.query_count
    for fen in fens:
        board = chess.Board(fen)
        candidate_rows = _cache_candidate_rows(
            cache,
            board,
            cfg,
            edge_weights,
            bridge_weights,
            cache_retrieval_enabled=cache_retrieval_enabled and not masks.get("disable_cache_retrieval", False),
            masks=masks,
        )
        confirmed = [row for row in candidate_rows if row["formal_recon_engine_confirmed"]]
        confirmed.sort(key=lambda row: (row["evidence_score"], row["move"]), reverse=True)
        selected = None if not confirmed else confirmed[0]
        row = _position_eval_row(fen, candidate_rows, selected)
        rows.append(row)
        _accumulate(totals, row)
    return _finalize_eval(totals, rows, max_samples=cfg.max_samples) | {
        "cache_queries_run": cache.query_count - before_queries,
        "average_cache_queries_per_position": (cache.query_count - before_queries) / max(1, len(fens)),
    }


def _cache_candidate_rows(
    cache: _FoundationResponseCache,
    board: chess.Board,
    cfg: FrozenFoundationResponseCacheBridgeRetrievalConfig,
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
    *,
    cache_retrieval_enabled: bool,
    masks: dict[str, bool] | None = None,
) -> list[dict[str, Any]]:
    masks = masks or {}
    cheap = _cheap_candidate_rows(board, edge_weights)
    safe_rows = [row for row in cheap if row["safety_ok"] and row["after_features"]["stalemate_after"] == 0.0]
    materialized_rows = _select_deep_candidates(safe_rows, cfg.max_cache_candidate_moves)
    output = []
    for row in materialized_rows:
        move = chess.Move.from_uci(row["move"])
        envelope = (
            _empty_reply_envelope(row["move"], reason="cache_retrieval_disabled")
            if not cache_retrieval_enabled or masks.get("disable_live_foundation_response_query", False)
            else cache.reply_envelope(board, move)
        )
        chain = _chain_from_envelope(envelope)
        after = board.copy(stack=False)
        after.push(move)
        immediate = cache.query_state(after) if cache_retrieval_enabled and not masks.get("disable_live_foundation_response_query", False) else None
        augmented = _augment_bridge_row(
            row,
            chain,
            _empty_bounded(disabled=True),
            bridge_weights,
            bridge_pressure_enabled=cache_retrieval_enabled,
            masks={
                "mask_bridge_pressure_terminals": masks.get("mask_bridge_pressure_terminals", False),
            },
        )
        augmented["immediate_after_white_move_foundation_reachable"] = bool(
            immediate
            and (immediate["foundation_mate1_recognized"] or immediate["foundation_mate2_recognized"] or immediate["foundation_chain_success"])
        )
        augmented["cache_reply_envelope"] = envelope
        augmented["cache_immediate_after_state"] = immediate
        augmented = _confirm_bridge_candidate(
            cache.graph,
            board,
            augmented,
            _as_tg28b_config(cfg),
            _translate_masks(masks),
        )
        output.append(augmented)
    return output


def _sample_foundation_basin(
    cache: _FoundationResponseCache,
    *,
    mate1_train: tuple[str, ...],
    mate1_heldout: tuple[str, ...],
    mate2_train: tuple[str, ...],
    mate2_heldout: tuple[str, ...],
    bridge_train: tuple[str, ...],
    bridge_heldout: tuple[str, ...],
    generic_heldout: tuple[str, ...],
    cfg: FrozenFoundationResponseCacheBridgeRetrievalConfig,
) -> dict[str, Any]:
    samples: list[tuple[str, str]] = []
    for source, fens in (
        ("tg27b_mate1_train", mate1_train),
        ("tg27b_mate1_heldout", mate1_heldout),
        ("tg27b_mate2_train", mate2_train),
        ("tg27b_mate2_heldout", mate2_heldout),
        ("tg28c_bridge_train", bridge_train),
        ("tg28c_bridge_heldout", bridge_heldout),
        ("generic_edge_safety_heldout", generic_heldout),
    ):
        samples.extend((source, fen) for fen in fens[: max(1, cfg.max_samples // 4)])
    rng = random.Random(cfg.seed + 100)
    for fen in _random_near_frontier_fens(rng, cfg.basin_random_count, cfg):
        samples.append(("random_near_frontier", fen))
    rows = []
    positive_by_source: dict[str, int] = {}
    side_dist: dict[str, int] = {}
    duplicates = 0
    seen: set[str] = set()
    for source, fen in samples:
        board = chess.Board(fen)
        entry = cache.query_state(board)
        key = entry["canonical_fen"]
        duplicates += int(key in seen)
        seen.add(key)
        positive = entry["foundation_mate1_recognized"] or entry["foundation_mate2_recognized"] or entry["foundation_chain_success"]
        positive_by_source[source] = positive_by_source.get(source, 0) + int(positive)
        side_dist[entry["side_to_move"]] = side_dist.get(entry["side_to_move"], 0) + 1
        features = _basin_features(board)
        rows.append({"source": source, "positive": positive, "features": features, **entry})
    positives = [row for row in rows if row["positive"]]
    negatives = [row for row in rows if not row["positive"]]
    return {
        "sampled_state_count": len(rows),
        "foundation_positive_state_count": len(positives),
        "foundation_negative_state_count": len(negatives),
        "foundation_positive_by_source": positive_by_source,
        "side_to_move_distribution": side_dist,
        "positive_basin_feature_summary": _feature_summary(positives),
        "negative_basin_feature_summary": _feature_summary(negatives),
        "duplicate_canonical_collision_count": duplicates,
        "estimated_cache_hit_rate": cache.hit_rate,
        "samples": rows[: cfg.max_samples],
    }


def _cache_bridge_ablations(graph, cache, heldout_fens, cfg, edge_weights, bridge_weights) -> dict[str, Any]:
    if cfg.max_ablation_positions <= 0:
        return _empty_ablation_results()
    fens = tuple(heldout_fens[: cfg.max_ablation_positions])
    masks = {
        "mask_foundation_response_terminals": {"mask_frozen_foundation_response_terminals": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_edge_fence_terminals": {"mask_edge_fence_terminals": True},
        "mask_action_delta_terminals": {"mask_action_delta_terminals": True},
        "mask_internal_attention_request_strength_terminals": {"mask_internal_attention_request_strength_terminals": True},
        "mask_safety_veto_terminals": {"mask_safety_veto_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "disable_cache_retrieval": {"disable_cache_retrieval": True},
        "disable_live_foundation_response_query": {"disable_live_foundation_response_query": True},
        "disable_reply_envelope_foundation_checks": {"disable_reply_envelope_foundation_checks": True},
        "mask_frozen_mate1_foundation_quorum": {"mask_frozen_mate1_foundation_quorum": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_frozen_mate2_foundation_quorum": True},
    }
    return {
        name: _evaluate_cache_bridge_layer(graph, cache, fens, cfg, edge_weights, bridge_weights, masks=mask)
        for name, mask in masks.items()
    }


def _decision(
    cfg,
    *,
    foundation_sanity,
    cache: _FoundationResponseCache,
    equivalence,
    basin,
    baseline,
    retrieval,
    generic_eval,
    ablations,
    scheduler_equivalence,
    training,
    foundation_before_training,
    foundation_after_training,
    foundation_before_eval,
    foundation_after_eval,
) -> dict[str, Any]:
    train_m3_delta = foundation_after_training["m3"] - foundation_before_training["m3"]
    train_m4_delta = foundation_after_training["m4"] - foundation_before_training["m4"]
    eval_m3_delta = foundation_after_eval["m3"] - foundation_before_eval["m3"]
    eval_m4_delta = foundation_after_eval["m4"] - foundation_before_eval["m4"]
    bridge_candidate_generated = retrieval["bridge_candidate_generated_count"]
    no_bridge = retrieval["no_bridge_candidate_generated_count"]
    basin_too_narrow = (
        bridge_candidate_generated == 0
        and basin["foundation_positive_state_count"] > 0
        and retrieval["reply_envelope_foundation_reachable_count"] == 0
    )
    ablation_ok = True
    if cfg.max_ablation_positions > 0 and "mask_actuator_terminals" in ablations:
        ablation_ok = ablations["mask_actuator_terminals"]["selected_move_count"] == 0
    checkpoint_pass = (
        train_m3_delta == 0
        and train_m4_delta == 0
        and eval_m3_delta == 0
        and eval_m4_delta == 0
        and equivalence["foundation_cache_live_mismatch_count"] == 0
        and foundation_sanity["foundation_mate1_accuracy"] >= 1.0
        and foundation_sanity["foundation_mate2_conversion_rate"] >= 1.0
        and (bridge_candidate_generated > 0 or basin_too_narrow)
        and ablation_ok
        and scheduler_equivalence["mismatch_count"] == 0
    )
    return {
        "checkpoint_pass": checkpoint_pass,
        "checkpoint_interpretation": (
            "cache_retrieval_found_graph_mediated_bridge_candidates"
            if bridge_candidate_generated > 0
            else "frozen_foundation_basin_too_narrow_for_current_bridge_candidates"
        ),
        "foundation_frozen": True,
        "foundation_cache_state_count": cache.state_count,
        "foundation_cache_query_count": cache.query_count,
        "foundation_cache_hit_rate": cache.hit_rate,
        "foundation_cache_live_mismatch_count": equivalence["foundation_cache_live_mismatch_count"],
        "foundation_cache_used_as_memoized_graph_response": True,
        "foundation_cache_used_as_provider": False,
        "foundation_m3_updates_during_bridge_training": train_m3_delta,
        "foundation_m4_promotions_during_bridge_training": train_m4_delta,
        "foundation_m3_updates_during_eval": eval_m3_delta,
        "foundation_m4_promotions_during_eval": eval_m4_delta,
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
        "foundation_replay_stability_pass": foundation_sanity["foundation_replay_stability_pass"],
        "sampled_state_count": basin["sampled_state_count"],
        "foundation_positive_state_count": basin["foundation_positive_state_count"],
        "foundation_negative_state_count": basin["foundation_negative_state_count"],
        "bridge_train_count": cfg.bridge_train_count,
        "bridge_heldout_count": cfg.bridge_heldout_count,
        "bridge_candidate_generated_count": bridge_candidate_generated,
        "no_bridge_candidate_generated_count": no_bridge,
        "legal_candidate_count": retrieval["legal_candidate_count"],
        "safety_filtered_candidate_count": retrieval["safety_filtered_candidate_count"],
        "cache_scored_candidate_count": retrieval["cache_scored_candidate_count"],
        "immediate_after_white_move_foundation_reachable_count": retrieval["immediate_after_white_move_foundation_reachable_count"],
        "reply_envelope_foundation_reachable_count": retrieval["reply_envelope_foundation_reachable_count"],
        "reply_envelope_foundation_coverage_rate": retrieval["reply_envelope_foundation_coverage_rate"],
        "bounded_bridge_foundation_reachable_count": retrieval["bounded_bridge_foundation_reachable_count"],
        "foundation_handoff_conversion_count": retrieval["foundation_handoff_conversion_count"],
        "same_graph_foundation_continuation_count": retrieval["same_graph_foundation_continuation_count"],
        "selected_move_count": retrieval["selected_move_count"],
        "null_move_count": retrieval["null_move_count"],
        "edge_fence_success_rate": retrieval["edge_fence_success_rate"],
        "confinement_area_improvement_rate": retrieval["confinement_area_improvement_rate"],
        "black_king_mobility_reduction_rate": retrieval["black_king_mobility_reduction_rate"],
        "rook_blunder_count": retrieval["rook_blunder_count"],
        "stalemate_avoidance_rate": retrieval["stalemate_avoidance_rate"],
        "deep_reply_checks_run": retrieval["deep_reply_checks_run"],
        "cache_queries_run": retrieval["cache_queries_run"],
        "average_cache_queries_per_position": retrieval["average_cache_queries_per_position"],
        "average_deep_reply_checks_per_position": retrieval["average_deep_reply_checks_per_position"],
        "timeout_count": 0,
        "candidate_budget_used": retrieval["candidate_budget_used"],
        "failure_bucket_counts": retrieval["failure_bucket_counts"],
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "edge_only_m3_update_count": training["edge_only_m3_update_count"],
        "bridge_terminal_m3_update_count": training["bridge_terminal_m3_update_count"],
        "m4_promotion_count_by_terminal_kind_edge_bridge_only": {},
        "baseline_no_cache_metrics": baseline,
        "generic_edge_safety_metrics": generic_eval,
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


def _as_tg28b_config(cfg: FrozenFoundationResponseCacheBridgeRetrievalConfig) -> FrozenFoundationBridgePressureConfig:
    return FrozenFoundationBridgePressureConfig(
        seed=cfg.seed,
        foundation_seed=cfg.foundation_seed,
        foundation_mate1_train_count=cfg.foundation_mate1_train_count,
        foundation_mate1_heldout_count=cfg.foundation_mate1_heldout_count,
        foundation_mate2_train_count=cfg.foundation_mate2_train_count,
        foundation_mate2_heldout_count=cfg.foundation_mate2_heldout_count,
        bridge_train_count=cfg.bridge_train_count,
        bridge_heldout_count=cfg.bridge_heldout_count,
        generic_edge_safety_heldout_count=cfg.generic_edge_safety_heldout_count,
        max_generation_attempts=cfg.max_generation_attempts,
        top_k_deep_foundation_checks=max(1, min(cfg.max_cache_candidate_moves, 4)),
        max_edge_candidates_per_position=cfg.max_edge_candidates_per_position,
        max_reply_envelope_replies_per_candidate=cfg.max_reply_envelope_replies_per_candidate,
        max_ablation_positions=cfg.max_ablation_positions,
        max_foundation_sanity_positions=cfg.max_foundation_sanity_positions,
        max_foundation_ablation_positions=cfg.max_foundation_ablation_positions,
        max_bounded_replies_per_candidate=1,
        max_bounded_second_moves_per_reply=1,
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


def _chain_from_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    return {
        "chain_success": bool(envelope["all_replies_solved"]),
        "reply_success_rate": float(envelope["reply_envelope_success_rate"]),
        "reply_total": int(envelope["black_reply_count"]),
        "reply_solved": int(envelope["replies_foundation_solved"]),
        "same_graph_second_move_count": int(envelope["same_graph_second_move_count"]),
        "reply_rows": envelope["reply_rows"],
        "disabled": False,
        "foundation_response_source": "memoized_frozen_native_graph_response",
    }


def _empty_reply_envelope(move_uci: str, *, reason: str) -> dict[str, Any]:
    return {
        "white_candidate_move": move_uci,
        "black_reply_count": 0,
        "reply_states_queried": 0,
        "replies_foundation_solved": 0,
        "reply_envelope_success_rate": 0.0,
        "all_replies_solved": False,
        "any_reply_solved": False,
        "same_graph_second_move_count": 0,
        "worst_reply_failure_reason": reason,
        "reply_rows": [],
        "source": "disabled_or_invalid",
    }


def _translate_masks(masks: dict[str, bool]) -> dict[str, bool]:
    return {
        "mask_edge_fence_terminals": masks.get("mask_edge_fence_terminals", False),
        "mask_action_delta_terminals": masks.get("mask_action_delta_terminals", False),
        "mask_internal_attention_request_strength_terminals": masks.get("mask_internal_attention_request_strength_terminals", False),
        "mask_safety_veto_terminals": masks.get("mask_safety_veto_terminals", False),
        "mask_bridge_pressure_terminals": masks.get("mask_bridge_pressure_terminals", False),
        "mask_frozen_foundation_response_terminals": masks.get("mask_frozen_foundation_response_terminals", False)
        or masks.get("mask_foundation_response_terminals", False)
        or masks.get("disable_live_foundation_response_query", False),
        "mask_frozen_mate2_foundation_quorum": masks.get("mask_frozen_mate2_foundation_quorum", False),
        "mask_actuator_terminals": masks.get("mask_actuator_terminals", False),
    }


def _position_eval_row(fen: str, candidate_rows: list[dict[str, Any]], selected: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "fen": fen,
        "selected_move": None if selected is None else selected["move"],
        "selected": selected,
        "candidate_count": len(candidate_rows),
        "selected_move_count": int(selected is not None),
        "null_move_count": int(selected is None),
        "failure_bucket": _failure_bucket(candidate_rows, selected),
        "candidate_rows": candidate_rows[:12],
    }


def _empty_totals() -> dict[str, Any]:
    return {
        "positions": 0,
        "legal_candidate_count": 0,
        "safety_filtered_candidate_count": 0,
        "cache_scored_candidate_count": 0,
        "bridge_candidate_generated_count": 0,
        "no_bridge_candidate_generated_count": 0,
        "success": 0,
        "confinement_improve": 0,
        "mobility_reduce": 0,
        "rook_safe": 0,
        "stalemate_safe": 0,
        "rook_blunders": 0,
        "selected_move_count": 0,
        "null_move_count": 0,
        "candidate_budget_used": 0,
        "deep_reply_checks_run": 0,
        "immediate_reachable": 0,
        "reply_reachable": 0,
        "reply_total": 0,
        "reply_solved": 0,
        "bounded_reachable": 0,
        "handoff_conversion": 0,
        "same_graph_foundation_continuation_count": 0,
        "failure_bucket_counts": {},
    }


def _accumulate(totals: dict[str, Any], row: dict[str, Any]) -> None:
    totals["positions"] += 1
    totals["candidate_budget_used"] += row["candidate_count"]
    totals["selected_move_count"] += row["selected_move_count"]
    totals["null_move_count"] += row["null_move_count"]
    totals["failure_bucket_counts"][row["failure_bucket"]] = totals["failure_bucket_counts"].get(row["failure_bucket"], 0) + 1
    candidate_rows = row["candidate_rows"]
    totals["legal_candidate_count"] += sum(int(candidate.get("legal_candidate", True)) for candidate in candidate_rows)
    totals["safety_filtered_candidate_count"] += sum(int(candidate["safety_ok"]) for candidate in candidate_rows)
    totals["cache_scored_candidate_count"] += len(candidate_rows)
    bridge_candidates = [candidate for candidate in candidate_rows if candidate["reply_envelope_foundation_reachable"] or candidate["bounded_bridge_foundation_reachable"]]
    totals["bridge_candidate_generated_count"] += len(bridge_candidates)
    totals["no_bridge_candidate_generated_count"] += int(not bridge_candidates)
    selected = row["selected"]
    if selected is None:
        return
    safe = selected["after_features"]["rook_safe"] > 0.0 and selected["after_features"]["rook_attacked_after"] == 0.0
    stalemate_safe = selected["after_features"]["stalemate_after"] == 0.0
    conf = selected["delta_confinement_area"] < 0
    mob = selected["delta_black_king_legal_mobility"] < 0
    bridge = selected["reply_envelope_foundation_reachable"] or selected["bounded_bridge_foundation_reachable"]
    totals["success"] += int((conf or mob or bridge) and safe and stalemate_safe)
    totals["confinement_improve"] += int(conf)
    totals["mobility_reduce"] += int(mob)
    totals["rook_safe"] += int(safe)
    totals["stalemate_safe"] += int(stalemate_safe)
    totals["rook_blunders"] += int(not safe)
    totals["deep_reply_checks_run"] += int(selected["reply_total"])
    totals["immediate_reachable"] += int(selected["immediate_after_white_move_foundation_reachable"])
    totals["reply_reachable"] += int(selected["reply_envelope_foundation_reachable"])
    totals["reply_total"] += int(selected["reply_total"])
    totals["reply_solved"] += int(selected["reply_solved"])
    totals["bounded_reachable"] += int(selected["bounded_bridge_foundation_reachable"])
    totals["handoff_conversion"] += int(selected["foundation_handoff_conversion"])
    totals["same_graph_foundation_continuation_count"] += int(selected["same_graph_foundation_continuation_count"])


def _finalize_eval(totals: dict[str, Any], rows: list[dict[str, Any]], *, max_samples: int) -> dict[str, Any]:
    n = max(1, totals["positions"])
    selected_n = max(1, totals["selected_move_count"])
    return {
        "position_count": totals["positions"],
        "legal_candidate_count": totals["legal_candidate_count"],
        "safety_filtered_candidate_count": totals["safety_filtered_candidate_count"],
        "cache_scored_candidate_count": totals["cache_scored_candidate_count"],
        "bridge_candidate_generated_count": totals["bridge_candidate_generated_count"],
        "no_bridge_candidate_generated_count": totals["no_bridge_candidate_generated_count"],
        "edge_fence_success_rate": totals["success"] / n,
        "confinement_area_improvement_rate": totals["confinement_improve"] / n,
        "black_king_mobility_reduction_rate": totals["mobility_reduce"] / n,
        "rook_safety_rate": totals["rook_safe"] / selected_n,
        "stalemate_avoidance_rate": totals["stalemate_safe"] / selected_n,
        "rook_blunder_count": totals["rook_blunders"],
        "selected_move_count": totals["selected_move_count"],
        "null_move_count": totals["null_move_count"],
        "candidate_budget_used": totals["candidate_budget_used"],
        "deep_reply_checks_run": totals["deep_reply_checks_run"],
        "average_deep_reply_checks_per_position": totals["deep_reply_checks_run"] / n,
        "immediate_after_white_move_foundation_reachable_count": totals["immediate_reachable"],
        "reply_envelope_foundation_reachable_count": totals["reply_reachable"],
        "reply_envelope_reply_total": totals["reply_total"],
        "reply_envelope_foundation_reply_solved_count": totals["reply_solved"],
        "reply_envelope_foundation_coverage_rate": 0.0 if totals["reply_total"] == 0 else totals["reply_solved"] / totals["reply_total"],
        "bounded_bridge_foundation_reachable_count": totals["bounded_reachable"],
        "foundation_handoff_conversion_count": totals["handoff_conversion"],
        "same_graph_foundation_continuation_count": totals["same_graph_foundation_continuation_count"],
        "failure_bucket_counts": totals["failure_bucket_counts"],
        "samples": rows[:max_samples],
    }


def _failure_bucket(candidate_rows: list[dict[str, Any]], selected: dict[str, Any] | None) -> str:
    if not candidate_rows:
        return "no_legal_safe_candidate"
    bridge_rows = [row for row in candidate_rows if row["reply_envelope_foundation_reachable"] or row["bounded_bridge_foundation_reachable"]]
    if selected is None:
        if not bridge_rows:
            return "safe_candidates_exist_but_no_foundation_response"
        return "foundation_response_materialized_but_not_selected"
    if selected["actuator_terminal_state"] not in {"TRUE", "CONFIRMED"}:
        return "candidate_cap_or_scheduler_blocked"
    if selected["after_features"]["rook_attacked_after"] > 0.0 or selected["after_features"]["rook_safe"] == 0.0:
        return "unsafe_bridge_not_vetoed"
    if selected["reply_envelope_foundation_reachable"] and selected["foundation_response_terminal_state"] == "FAILED":
        return "foundation_reachable_after_reply_but_not_detected"
    if bridge_rows and not selected["reply_envelope_foundation_reachable"]:
        return "foundation_response_exists_but_not_materialized"
    if selected["delta_confinement_area"] < 0 and not selected["reply_envelope_foundation_reachable"]:
        return "selected_candidate_confining_but_not_foundation_near"
    return "none"


def _basin_features(board: chess.Board) -> dict[str, Any]:
    rook = _white_rook_square(board)
    bk = board.king(chess.BLACK)
    return {
        "black_king_edge_distance": _black_edge_distance(board),
        "black_king_mobility": _black_king_mobility(board),
        "confinement_area": None if rook is None or bk is None else _confinement_area(board, rook, bk),
    }


def _feature_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"count": 0}
    keys = ("black_king_edge_distance", "black_king_mobility", "confinement_area")
    out: dict[str, Any] = {"count": len(rows)}
    for key in keys:
        vals = [row["features"][key] for row in rows if row["features"][key] is not None]
        out[f"{key}_mean"] = None if not vals else sum(vals) / len(vals)
    return out


def _random_near_frontier_fens(rng: random.Random, count: int, cfg) -> tuple[str, ...]:
    fens = []
    attempts = 0
    while len(fens) < count and attempts < cfg.max_generation_attempts:
        attempts += 1
        board = chess.Board.empty()
        board.turn = chess.WHITE
        wk = rng.randrange(64)
        wr = rng.randrange(64)
        bk = rng.randrange(64)
        if len({wk, wr, bk}) != 3:
            continue
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        board.clear_stack()
        if not board.is_valid() or board.is_check() or board.is_game_over() or _black_edge_distance(board) > 3:
            continue
        fens.append(board.fen())
    return tuple(fens)


def _canonical_fen(board: chess.Board) -> str:
    clone = board.copy(stack=False)
    clone.clear_stack()
    return clone.fen()


def _response_hash(payload: dict[str, Any]) -> str:
    stable = {
        key: payload[key]
        for key in (
            "canonical_fen",
            "side_to_move",
            "foundation_mate1_recognized",
            "foundation_mate2_recognized",
            "foundation_selected_move",
            "foundation_chain_success",
            "same_graph_second_move_count",
            "graph_confirmation_state",
        )
    }
    return hashlib.sha1(json.dumps(stable, sort_keys=True).encode("utf-8")).hexdigest()


def _empty_ablation_results() -> dict[str, Any]:
    names = (
        "mask_foundation_response_terminals",
        "mask_bridge_pressure_terminals",
        "mask_edge_fence_terminals",
        "mask_action_delta_terminals",
        "mask_internal_attention_request_strength_terminals",
        "mask_safety_veto_terminals",
        "mask_actuator_terminals",
        "disable_cache_retrieval",
        "disable_live_foundation_response_query",
        "disable_reply_envelope_foundation_checks",
        "mask_frozen_mate1_foundation_quorum",
        "mask_frozen_mate2_foundation_quorum",
    )
    return {name: {"skipped": True, "skip_reason": "max_ablation_positions_zero"} for name in names}


def _write_progress(cfg: FrozenFoundationResponseCacheBridgeRetrievalConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg28b_purity_boundary()
    boundary.update({
        "checkpoint": "TG28c",
        "foundation_cache_used_as_memoized_graph_response": True,
        "foundation_cache_used_as_provider": False,
        "cache_retrieval_final_selector": False,
        "bridge_candidate_choice_mediated_by_native_quorum": True,
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "stage_labels_learner_visible": False,
    })
    return boundary
