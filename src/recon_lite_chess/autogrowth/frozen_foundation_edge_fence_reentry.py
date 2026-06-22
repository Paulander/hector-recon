"""TG28a frozen TG27b foundation edge/fence re-entry."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import random
from pathlib import Path
from typing import Any

import chess

from recon_lite import FormalReConEngine, LinkType, Node, NodeState, NodeType
from recon_lite_hector.nodes.stem_cell import StemCellState

from .continuous_handoff_attention import _internal_cfg
from .forced_chain_decomposition import _ablations as _foundation_ablations, _chain_repaired_attention_cfg
from .foundation_curriculum import _forced_mate_in_two_first_moves, _mate_moves
from .internal_handoff_affordance_guard_audit import _mate2_cfg, _train_internal_handoff_gate
from .native_quorum_materialization import _tg26t_config, _train_graph, _trained_graph
from .native_quorum_mate2_chaining import _evaluate_mate1_materialized, _same_graph_chain_audit, _tg26u_config, _train_mate2_chain
from .native_single_graph_curriculum import ROOT_ID, NativeReConKRKGraph
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .single_miss_repair import SingleMissRepairConfig, _attention_cfg as _tg27b_attention_cfg, _datasets_from_internal


@dataclass(frozen=True)
class FrozenFoundationEdgeFenceReentryConfig:
    seed: int = 20260625
    foundation_seed: int = 20260624
    foundation_mate1_train_count: int = 32
    foundation_mate1_heldout_count: int = 16
    foundation_mate2_train_count: int = 16
    foundation_mate2_heldout_count: int = 8
    edge_fence_train_count: int = 16
    edge_fence_heldout_count: int = 8
    max_generation_attempts: int = 250_000
    top_k_deep_foundation_checks: int = 4
    max_edge_candidates_per_position: int = 8
    max_ablation_positions: int = 4
    max_foundation_sanity_positions: int = 2
    max_foundation_ablation_positions: int = 2
    max_ticks: int = 30
    max_samples: int = 16
    repaired_high_recall_threshold: float = 0.018
    eta_m3_edge: float = 0.08
    materialized_quorum_min_evidence: float = -10000.0
    edge_terminal_min_score: float = -0.25
    replay_count: int = 2
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg28a_frozen_foundation_edge_fence_reentry_progress.json"


@dataclass(frozen=True)
class FrozenFoundationEdgeFenceReentryResult:
    config: FrozenFoundationEdgeFenceReentryConfig
    dataset: dict[str, Any]
    foundation_sanity: dict[str, Any]
    edge_training: dict[str, Any]
    evaluations: dict[str, Any]
    ablation_results: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg28a_frozen_foundation_edge_fence_reentry.v0",
            "checkpoint": "TG28a_frozen_foundation_edge_fence_reentry",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "foundation_sanity": self.foundation_sanity,
            "edge_training": self.edge_training,
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


def run_frozen_foundation_edge_fence_reentry(
    *,
    config: FrozenFoundationEdgeFenceReentryConfig | None = None,
) -> FrozenFoundationEdgeFenceReentryResult:
    cfg = config or FrozenFoundationEdgeFenceReentryConfig()
    foundation = _build_tg27b_foundation(cfg)
    graph = foundation["graph"]
    mate1_train = foundation["mate1_train"]
    mate1_heldout = foundation["mate1_heldout"]
    mate2_heldout = foundation["mate2_heldout"]
    foundation_attention = foundation["attention_cfg"]
    mate2_cfg = _mate2_cfg(foundation["internal_cfg"])
    foundation_before_training = _foundation_counts(graph)
    train_fens = _generate_edge_fence_positions(
        count=cfg.edge_fence_train_count,
        seed=cfg.seed,
        excluded=set((*mate1_train, *mate1_heldout, *mate2_heldout)),
        cfg=cfg,
    )
    heldout_fens = _generate_edge_fence_positions(
        count=cfg.edge_fence_heldout_count,
        seed=cfg.seed + 1,
        excluded=set((*mate1_train, *mate1_heldout, *mate2_heldout, *train_fens)),
        cfg=cfg,
    )
    _write_progress(cfg, {
        "phase": "dataset_complete",
        "edge_fence_train_count": len(train_fens),
        "edge_fence_heldout_count": len(heldout_fens),
    })

    edge_weights: dict[str, float] = {}
    training = _train_edge_layer(graph, train_fens, mate2_cfg, cfg, edge_weights)
    foundation_after_training = _foundation_counts(graph)
    _write_progress(cfg, {
        "phase": "edge_training_complete",
        "m3_update_count_edge_fence_only": training["m3_update_count_edge_fence_only"],
        "foundation_m3_delta": foundation_after_training["m3"] - foundation_before_training["m3"],
        "foundation_m4_delta": foundation_after_training["m4"] - foundation_before_training["m4"],
    })

    foundation_before_eval = _foundation_counts(graph)
    foundation_sanity = _foundation_sanity(graph, mate1_heldout, mate2_heldout, foundation_attention, mate2_cfg, cfg)
    _write_progress(cfg, {
        "phase": "foundation_sanity_complete",
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
        "foundation_replay_stability_pass": foundation_sanity["foundation_replay_stability_pass"],
    })
    train_eval = _evaluate_edge_layer(graph, train_fens, mate2_cfg, cfg, edge_weights, foundation_handoff_enabled=True)
    _write_progress(cfg, {
        "phase": "train_eval_complete",
        "edge_fence_success_rate": train_eval["edge_fence_success_rate"],
        "selected_move_count": train_eval["selected_move_count"],
    })
    heldout = _evaluate_edge_layer(graph, heldout_fens, mate2_cfg, cfg, edge_weights, foundation_handoff_enabled=False)
    _write_progress(cfg, {
        "phase": "heldout_no_handoff_eval_complete",
        "edge_fence_success_rate": heldout["edge_fence_success_rate"],
        "selected_move_count": heldout["selected_move_count"],
    })
    heldout_handoff = _evaluate_edge_layer(graph, heldout_fens, mate2_cfg, cfg, edge_weights, foundation_handoff_enabled=True)
    _write_progress(cfg, {
        "phase": "heldout_handoff_eval_complete",
        "edge_fence_success_rate": heldout_handoff["edge_fence_success_rate"],
        "foundation_handoff_conversion_count": heldout_handoff["foundation_handoff_conversion_count"],
    })
    heldout_masked = _evaluate_edge_layer(graph, heldout_fens, mate2_cfg, cfg, edge_weights, foundation_handoff_enabled=False)
    foundation_after_eval = _foundation_counts(graph)
    ablations = _edge_ablations(graph, heldout_fens, mate2_cfg, cfg, edge_weights)
    equivalence = _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(mate2_cfg))), mate1_train, mate1_heldout)
    decision = _decision(
        cfg,
        foundation_sanity=foundation_sanity,
        train_eval=train_eval,
        heldout=heldout_handoff,
        heldout_masked=heldout_masked,
        ablations=ablations,
        equivalence=equivalence,
        training=training,
        foundation_before_training=foundation_before_training,
        foundation_after_training=foundation_after_training,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
    )
    _write_progress(cfg, {
        "phase": "complete",
        "decision": {
            "checkpoint_pass": decision["checkpoint_pass"],
            "edge_fence_success_rate": decision["edge_fence_success_rate"],
            "after_state_foundation_reachable_count": decision["after_state_foundation_reachable_count"],
            "foundation_handoff_conversion_count": decision["foundation_handoff_conversion_count"],
        },
    })
    return FrozenFoundationEdgeFenceReentryResult(
        config=cfg,
        dataset={
            "source": "controlled generated legal KRK edge/fence positions outside immediate Mate_In_1 and strict forced Mate_In_2 where possible",
            "edge_fence_train_count": len(train_fens),
            "edge_fence_heldout_count": len(heldout_fens),
            "train_fens": list(train_fens)[: cfg.max_samples],
            "heldout_fens": list(heldout_fens)[: cfg.max_samples],
            "edge_fence_labels_learner_visible": False,
        },
        foundation_sanity=foundation_sanity,
        edge_training=training,
        evaluations={
            "edge_fence_train": train_eval,
            "edge_fence_heldout": heldout,
            "edge_fence_heldout_with_frozen_foundation_handoff": heldout_handoff,
            "edge_fence_heldout_foundation_handoff_masked": heldout_masked,
        },
        ablation_results=ablations,
        scheduler_equivalence=equivalence,
        decision=decision,
    )


def _build_tg27b_foundation(cfg: FrozenFoundationEdgeFenceReentryConfig) -> dict[str, Any]:
    foundation_cfg = SingleMissRepairConfig(
        seed=cfg.foundation_seed,
        mate1_train_count=cfg.foundation_mate1_train_count,
        mate1_heldout_count=cfg.foundation_mate1_heldout_count,
        mate2_train_count=cfg.foundation_mate2_train_count,
        mate2_heldout_count=cfg.foundation_mate2_heldout_count,
        max_generation_attempts=cfg.max_generation_attempts,
        max_ticks=cfg.max_ticks,
        max_samples=cfg.max_samples,
        repaired_high_recall_threshold=cfg.repaired_high_recall_threshold,
    )
    attention_cfg = _chain_repaired_attention_cfg(_tg27b_attention_cfg(foundation_cfg, cfg.repaired_high_recall_threshold))
    internal_cfg = _internal_cfg(attention_cfg, train_repetitions=foundation_cfg.train_repetitions)
    mate1_train, mate1_heldout, mate2_train, mate2_heldout = _datasets_from_internal(internal_cfg)
    graph = _trained_graph(_tg26u_config(_mate2_cfg(internal_cfg)), score_action_atoms=True)
    _train_graph(graph, mate1_train, _tg26u_config(_mate2_cfg(internal_cfg)))
    _train_mate2_chain(graph, mate2_train, _mate2_cfg(internal_cfg))
    _train_internal_handoff_gate(graph, mate2_train, internal_cfg)
    return {
        "graph": graph,
        "attention_cfg": attention_cfg,
        "internal_cfg": internal_cfg,
        "mate1_train": mate1_train,
        "mate1_heldout": mate1_heldout,
        "mate2_train": mate2_train,
        "mate2_heldout": mate2_heldout,
    }


def _foundation_sanity(
    graph: NativeReConKRKGraph,
    mate1_heldout: tuple[str, ...],
    mate2_heldout: tuple[str, ...],
    attention_cfg,
    mate2_cfg,
    cfg: FrozenFoundationEdgeFenceReentryConfig,
) -> dict[str, Any]:
    from .forced_chain_decomposition import _high_recall

    mate2_sanity = tuple(mate2_heldout[: cfg.max_foundation_sanity_positions])
    mate1 = _evaluate_mate1_materialized(graph, mate1_heldout, mate2_cfg)
    mate2 = _high_recall(graph, mate2_sanity, attention_cfg)
    replay_rates = []
    before = _foundation_counts(graph)
    for _ in range(max(1, cfg.replay_count)):
        replay_rates.append(_high_recall(graph, mate2_sanity, attention_cfg)["conversion_rate"])
    after = _foundation_counts(graph)
    _write_progress(cfg, {
        "phase": "foundation_sanity_replay_complete",
        "foundation_mate1_accuracy": mate1["accuracy"],
        "foundation_mate2_conversion_rate": mate2["conversion_rate"],
        "foundation_replay_rates": replay_rates,
    })
    ablation_fens = tuple(mate2_heldout[: cfg.max_foundation_ablation_positions])
    ablations = _foundation_ablations(graph, ablation_fens, attention_cfg)
    return {
        "foundation_mate1_accuracy": mate1["accuracy"],
        "foundation_mate1_null_count": mate1["null_count"],
        "foundation_mate2_conversion_rate": mate2["conversion_rate"],
        "foundation_replay_rates": replay_rates,
        "foundation_replay_stability_pass": bool(replay_rates) and len(set(replay_rates)) == 1,
        "foundation_replay_m3_delta": after["m3"] - before["m3"],
        "foundation_replay_m4_delta": after["m4"] - before["m4"],
        "foundation_ablation_still_collapses": all(item["conversion_rate"] == 0.0 for item in ablations.values()),
        "foundation_ablation_results": ablations,
    }


def _generate_edge_fence_positions(
    *,
    count: int,
    seed: int,
    excluded: set[str],
    cfg: FrozenFoundationEdgeFenceReentryConfig,
) -> tuple[str, ...]:
    rng = random.Random(seed)
    fens: list[str] = []
    attempts = 0
    while len(fens) < count and attempts < cfg.max_generation_attempts:
        attempts += 1
        wk = rng.randrange(64)
        wr = rng.randrange(64)
        bk = rng.randrange(64)
        if len({wk, wr, bk}) != 3:
            continue
        board = chess.Board.empty()
        board.turn = chess.WHITE
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        board.clear_stack()
        if not board.is_valid() or board.is_check() or board.is_game_over():
            continue
        fen = board.fen()
        if fen in excluded or fen in fens:
            continue
        if _mate_moves(board):
            continue
        if _forced_mate_in_two_first_moves(board):
            continue
        edge = _black_edge_distance(board)
        if edge > 3:
            continue
        if len(list(board.legal_moves)) < 4:
            continue
        fens.append(fen)
    if len(fens) < count:
        raise RuntimeError(f"could only generate {len(fens)} edge/fence positions after {attempts} attempts")
    return tuple(fens)


def _train_edge_layer(
    graph: NativeReConKRKGraph,
    fens: tuple[str, ...],
    mate2_cfg,
    cfg: FrozenFoundationEdgeFenceReentryConfig,
    edge_weights: dict[str, float],
) -> dict[str, Any]:
    updates = 0
    samples = []
    for fen in fens:
        board = chess.Board(fen)
        rows = _cheap_candidate_rows(board, edge_weights)
        for row in rows:
            reward = _edge_reward(row)
            for key in row["positive_feature_keys"]:
                old = edge_weights.get(key, 0.0)
                edge_weights[key] = max(-1.0, min(1.0, old + cfg.eta_m3_edge * reward))
                updates += 1
        if len(samples) < cfg.max_samples:
            samples.append({"fen": fen, "best_training_move": max(rows, key=_edge_reward)["move"], "candidate_count": len(rows)})
        _materialize_edge_candidates(graph, board, rows[: cfg.top_k_deep_foundation_checks], mate2_cfg, cfg, foundation_handoff_enabled=True)
    return {
        "m3_update_count_edge_fence_only": updates,
        "edge_weight_count": len(edge_weights),
        "top_edge_weights": sorted(edge_weights.items(), key=lambda item: item[1], reverse=True)[:12],
        "samples": samples,
    }


def _evaluate_edge_layer(
    graph: NativeReConKRKGraph,
    fens: tuple[str, ...],
    mate2_cfg,
    cfg: FrozenFoundationEdgeFenceReentryConfig,
    edge_weights: dict[str, float],
    *,
    foundation_handoff_enabled: bool,
    masks: dict[str, bool] | None = None,
) -> dict[str, Any]:
    masks = masks or {}
    rows = []
    totals = _empty_totals()
    for fen in fens:
        board = chess.Board(fen)
        cheap = _cheap_candidate_rows(board, edge_weights)
        materialized_rows = _select_deep_candidates(cheap, cfg.max_edge_candidates_per_position)
        selected_for_deep = _select_deep_candidates(materialized_rows, cfg.top_k_deep_foundation_checks)
        candidate_rows = _materialize_edge_candidates(
            graph,
            board,
            materialized_rows,
            mate2_cfg,
            cfg,
            foundation_handoff_enabled=foundation_handoff_enabled,
            deep_move_ucis={row["move"] for row in selected_for_deep},
            masks=masks,
        )
        confirmed = [row for row in candidate_rows if row["formal_recon_engine_confirmed"]]
        confirmed.sort(key=lambda row: (row["evidence_score"], row["move"]), reverse=True)
        selected = None if not confirmed else confirmed[0]
        row = _position_eval_row(fen, candidate_rows, selected)
        _accumulate(totals, row)
        rows.append(row)
    return _finalize_eval(totals, rows, max_samples=cfg.max_samples)


def _cheap_candidate_rows(board: chess.Board, edge_weights: dict[str, float]) -> list[dict[str, Any]]:
    before = _position_features(board)
    rows: list[dict[str, Any]] = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        after = board.copy(stack=False)
        after.push(move)
        after_features = _position_features(after)
        delta_edge = after_features["black_king_edge_distance"] - before["black_king_edge_distance"]
        delta_mobility = after_features["black_king_legal_mobility"] - before["black_king_legal_mobility"]
        delta_area = after_features["confinement_area"] - before["confinement_area"]
        keys = _feature_keys(move, before, after_features, delta_edge, delta_mobility, delta_area)
        safety_ok = after_features["rook_safe"] > 0.0 and after_features["stalemate_after"] == 0.0 and after_features["rook_attacked_after"] == 0.0
        weighted = sum(edge_weights.get(key, 0.0) for key in keys)
        cheap_score = (
            weighted
            + (0.30 if delta_edge < 0 else 0.0)
            + (0.18 if delta_mobility < 0 else 0.0)
            + (0.18 if delta_area < 0 else 0.0)
            + (0.12 if after_features["gives_check"] > 0.0 else 0.0)
            + (0.20 if safety_ok else -1.0)
        )
        rows.append({
            "move": move.uci(),
            "before_features": before,
            "after_features": after_features,
            "delta_black_king_edge_distance": delta_edge,
            "delta_black_king_legal_mobility": delta_mobility,
            "delta_confinement_area": delta_area,
            "positive_feature_keys": keys,
            "safety_ok": safety_ok,
            "cheap_score": round(cheap_score, 6),
        })
    return rows


def _select_deep_candidates(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (row["cheap_score"], row["move"]), reverse=True)[:count]


def _materialize_edge_candidates(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    rows: list[dict[str, Any]],
    mate2_cfg,
    cfg: FrozenFoundationEdgeFenceReentryConfig,
    *,
    foundation_handoff_enabled: bool,
    deep_move_ucis: set[str] | None = None,
    masks: dict[str, bool] | None = None,
) -> list[dict[str, Any]]:
    masks = masks or {}
    deep_move_ucis = {row["move"] for row in rows} if deep_move_ucis is None else deep_move_ucis
    output = []
    for row in rows:
        move = chess.Move.from_uci(row["move"])
        deep = row["move"] in deep_move_ucis and foundation_handoff_enabled and not masks.get("disable_deep_continuation_checks", False)
        if deep:
            chain = _same_graph_chain_audit(
                graph,
                board,
                move,
                mate2_cfg,
                disable_mate1_quorum=masks.get("mask_mate1_foundation_quorum", False),
                disable_same_graph_continuation=masks.get("disable_foundation_handoff_evidence", False),
            )
        else:
            chain = {
                "chain_success": False,
                "reply_success_rate": 0.0,
                "reply_total": 0,
                "reply_solved": 0,
                "same_graph_second_move_count": 0,
                "reply_rows": [],
                "disabled": not foundation_handoff_enabled,
                "deep_reply_check_skipped": True,
            }
        output.append(_confirm_edge_candidate(graph, board, row, chain, cfg, masks))
    return output


def _confirm_edge_candidate(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    row: dict[str, Any],
    chain: dict[str, Any],
    cfg: FrozenFoundationEdgeFenceReentryConfig,
    masks: dict[str, bool],
) -> dict[str, Any]:
    ids = _EdgeIds(board.fen(), row["move"])
    candidate = {
        "move": row["move"],
        "edge_ok": _edge_reward(row) > cfg.edge_terminal_min_score and not masks.get("mask_edge_fence_terminals", False),
        "action_delta_ok": (row["delta_black_king_edge_distance"] <= 0 or row["delta_confinement_area"] <= 0) and not masks.get("mask_action_delta_terminals", False),
        "attention_ok": row["cheap_score"] > cfg.edge_terminal_min_score and not masks.get("mask_internal_attention_terminals", False),
        "safety_ok": bool(row["safety_ok"]) and not masks.get("mask_safety_veto_terminals", False),
        "foundation_ok": bool(chain.get("chain_success", False))
        and not masks.get("disable_foundation_handoff_evidence", False)
        and not masks.get("mask_mate2_foundation_quorum", False),
        "mask_actuator": masks.get("mask_actuator_terminals", False),
        "evidence_score": round(row["cheap_score"] + (0.75 if chain.get("chain_success") else 0.0), 6),
    }
    active_nodes = _materialize_edge_nodes(graph, ids, candidate, row)
    graph._reset_runtime_states(active_nodes)
    env = {
        "board": board,
        "tg28a_edge_candidates": {ids.quorum_script: candidate},
        "materialized_quorum_min_evidence": cfg.materialized_quorum_min_evidence,
    }
    engine = FormalReConEngine(graph.graph, validate_pairs=False, record_trace=False)
    engine.request(ROOT_ID)
    engine.run(
        max_ticks=cfg.max_ticks,
        env=env,
        active_nodes=active_nodes,
        until=lambda _engine: graph.graph.nodes[ids.quorum_script].state in (NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED),
    )
    state = graph.graph.nodes[ids.quorum_script].state
    return {
        **row,
        "quorum_script_id": ids.quorum_script,
        "formal_recon_engine_confirmed": state in (NodeState.TRUE, NodeState.CONFIRMED),
        "graph_confirmation_state": state.name,
        "actuator_terminal_state": graph.graph.nodes[ids.actuator_terminal].state.name,
        "edge_terminal_state": graph.graph.nodes[ids.edge_terminal].state.name,
        "action_delta_terminal_state": graph.graph.nodes[ids.action_delta_terminal].state.name,
        "attention_terminal_state": graph.graph.nodes[ids.attention_terminal].state.name,
        "safety_terminal_state": graph.graph.nodes[ids.safety_terminal].state.name,
        "foundation_terminal_state": graph.graph.nodes[ids.foundation_terminal].state.name,
        "foundation_handoff_reachable": bool(chain.get("chain_success", False)),
        "foundation_handoff_conversion": bool(chain.get("chain_success", False)),
        "reply_total": int(chain.get("reply_total", 0)),
        "reply_solved": int(chain.get("reply_solved", 0)),
        "same_graph_foundation_continuation_count": int(chain.get("same_graph_second_move_count", 0)),
        "evidence_score": candidate["evidence_score"],
        "formal_ticks_run": engine.tick,
    }


def _materialize_edge_nodes(graph: NativeReConKRKGraph, ids: "_EdgeIds", candidate: dict[str, Any], row: dict[str, Any]) -> set[str]:
    nodes = (
        Node(ids.quorum_script, NodeType.SCRIPT, meta={"origin": "tg28a_frozen_foundation_edge_fence", "role": "edge_fence_quorum", "tier": "trial", "stem_cell_state": StemCellState.TRIAL.name, "candidate_move_uci": candidate["move"]}),
        Node(ids.evidence_terminal, NodeType.TERMINAL, predicate=_edge_evidence_predicate(ids.quorum_script), meta={"origin": "tg28a_frozen_foundation_edge_fence", "terminal_kind": "edge_fence_evidence", "candidate_move_uci": candidate["move"], "feature_keys": row["positive_feature_keys"], "tier": "trial"}),
        Node(ids.edge_terminal, NodeType.TERMINAL, predicate=_candidate_bool_predicate(ids.quorum_script, "edge_ok"), meta={"origin": "tg28a_frozen_foundation_edge_fence", "terminal_kind": "edge_fence_feature", "tier": "trial"}),
        Node(ids.action_delta_terminal, NodeType.TERMINAL, predicate=_candidate_bool_predicate(ids.quorum_script, "action_delta_ok"), meta={"origin": "tg28a_frozen_foundation_edge_fence", "terminal_kind": "edge_action_delta", "tier": "trial"}),
        Node(ids.attention_terminal, NodeType.TERMINAL, predicate=_candidate_bool_predicate(ids.quorum_script, "attention_ok"), meta={"origin": "tg28a_frozen_foundation_edge_fence", "terminal_kind": "internal_attention", "tier": "trial"}),
        Node(ids.safety_terminal, NodeType.TERMINAL, predicate=_candidate_bool_predicate(ids.quorum_script, "safety_ok"), meta={"origin": "tg28a_frozen_foundation_edge_fence", "terminal_kind": "veto_or_safety_terminal", "tier": "trial"}),
        Node(ids.foundation_terminal, NodeType.TERMINAL, predicate=_candidate_bool_predicate(ids.quorum_script, "foundation_ok"), meta={"origin": "tg28a_frozen_foundation_edge_fence", "terminal_kind": "frozen_foundation_handoff", "tier": "trial"}),
        Node(ids.actuator_terminal, NodeType.TERMINAL, predicate=_edge_actuator_predicate(candidate["move"]), meta={"origin": "tg28a_frozen_foundation_edge_fence", "terminal_kind": "actuator_terminal", "candidate_move_uci": candidate["move"], "tier": "trial"}),
    )
    for node in nodes:
        if node.nid not in graph.graph.nodes:
            graph.graph.add_node(node)
    for parent, child, weight in (
        (ROOT_ID, ids.quorum_script, candidate["evidence_score"]),
        (ROOT_ID, ids.edge_terminal, 0.0),
        (ROOT_ID, ids.action_delta_terminal, 0.0),
        (ROOT_ID, ids.attention_terminal, 0.0),
        (ROOT_ID, ids.safety_terminal, 0.0),
        (ROOT_ID, ids.foundation_terminal, 0.0),
        (ROOT_ID, ids.actuator_terminal, 0.0),
        (ids.quorum_script, ids.evidence_terminal, candidate["evidence_score"]),
    ):
        _add_pair_once(graph, parent, child, weight)
    return {ROOT_ID, *(node.nid for node in nodes)}


def _edge_evidence_predicate(quorum_script_id: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        graph = env["__graph__"]
        candidate = env["tg28a_edge_candidates"][quorum_script_id]
        edge_terminal = f"{quorum_script_id}_edge_terminal"
        action_delta_terminal = f"{quorum_script_id}_action_delta_terminal"
        attention_terminal = f"{quorum_script_id}_attention_terminal"
        safety_terminal = f"{quorum_script_id}_safety_terminal"
        foundation_terminal = f"{quorum_script_id}_foundation_terminal"
        actuator_terminal = f"{quorum_script_id}_actuator_terminal"
        required = [edge_terminal, action_delta_terminal, attention_terminal, safety_terminal, actuator_terminal]
        states = [graph.nodes[nid].state for nid in required]
        foundation_state = graph.nodes[foundation_terminal].state
        if any(state not in (NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED) for state in states):
            return False, False
        if foundation_state not in (NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED):
            return False, False
        success = (
            all(state in (NodeState.TRUE, NodeState.CONFIRMED) for state in states)
            and not candidate["mask_actuator"]
            and float(candidate["evidence_score"]) >= float(env.get("materialized_quorum_min_evidence", -10000.0))
        )
        node.meta["last_evidence_score"] = candidate["evidence_score"]
        node.meta["foundation_handoff_confirmed"] = foundation_state in (NodeState.TRUE, NodeState.CONFIRMED)
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _candidate_bool_predicate(quorum_script_id: str, key: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        success = bool(env["tg28a_edge_candidates"][quorum_script_id][key])
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _edge_actuator_predicate(move_uci: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        move = chess.Move.from_uci(move_uci)
        success = move in env["board"].legal_moves
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _add_pair_once(graph: NativeReConKRKGraph, parent: str, child: str, weight: float) -> None:
    if graph.graph.get_edge(parent, child, LinkType.SUB) is None:
        graph.graph.add_edge(parent, child, LinkType.SUB)
    if graph.graph.get_edge(child, parent, LinkType.SUR) is None:
        graph.graph.add_edge(child, parent, LinkType.SUR)
    sub = graph.graph.get_edge(parent, child, LinkType.SUB)
    if sub is not None:
        sub.w = float(weight)
        sub.meta.update({"trainable": True, "tier": "trial", "stem_cell_state": StemCellState.TRIAL.name})


def _position_eval_row(fen: str, candidate_rows: list[dict[str, Any]], selected: dict[str, Any] | None) -> dict[str, Any]:
    selected_move = None if selected is None else selected["move"]
    return {
        "fen": fen,
        "selected_move": selected_move,
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
        "success": 0,
        "edge_improve": 0,
        "confinement_improve": 0,
        "mobility_reduce": 0,
        "rook_safe": 0,
        "stalemate_safe": 0,
        "rook_blunders": 0,
        "legal_actuator": 0,
        "foundation_reachable": 0,
        "mate2_reachable": 0,
        "mate1_reachable": 0,
        "handoff_conversion": 0,
        "request_strength_sum": 0.0,
        "selected_move_count": 0,
        "null_move_count": 0,
        "candidate_budget_used": 0,
        "deep_reply_checks_run": 0,
        "same_graph_foundation_continuation_count": 0,
        "failure_bucket_counts": {},
    }


def _accumulate(totals: dict[str, Any], row: dict[str, Any]) -> None:
    totals["positions"] += 1
    selected = row["selected"]
    totals["candidate_budget_used"] += row["candidate_count"]
    totals["selected_move_count"] += row["selected_move_count"]
    totals["null_move_count"] += row["null_move_count"]
    totals["failure_bucket_counts"][row["failure_bucket"]] = totals["failure_bucket_counts"].get(row["failure_bucket"], 0) + 1
    if selected is None:
        return
    edge = selected["delta_black_king_edge_distance"] < 0
    conf = selected["delta_confinement_area"] < 0
    mob = selected["delta_black_king_legal_mobility"] < 0
    safe = selected["after_features"]["rook_safe"] > 0.0 and selected["after_features"]["rook_attacked_after"] == 0.0
    stalemate_safe = selected["after_features"]["stalemate_after"] == 0.0
    totals["success"] += int((edge or conf or mob or selected["foundation_handoff_reachable"]) and safe and stalemate_safe)
    totals["edge_improve"] += int(edge)
    totals["confinement_improve"] += int(conf)
    totals["mobility_reduce"] += int(mob)
    totals["rook_safe"] += int(safe)
    totals["stalemate_safe"] += int(stalemate_safe)
    totals["rook_blunders"] += int(not safe)
    totals["legal_actuator"] += int(selected["actuator_terminal_state"] in {"TRUE", "CONFIRMED"})
    totals["foundation_reachable"] += int(selected["foundation_handoff_reachable"])
    totals["mate2_reachable"] += int(selected["foundation_handoff_reachable"])
    totals["mate1_reachable"] += int(selected["reply_solved"] > 0)
    totals["handoff_conversion"] += int(selected["foundation_handoff_conversion"])
    totals["request_strength_sum"] += max(0.0, min(1.0, selected["cheap_score"]))
    totals["deep_reply_checks_run"] += int(selected["reply_total"])
    totals["same_graph_foundation_continuation_count"] += int(selected["same_graph_foundation_continuation_count"])


def _finalize_eval(totals: dict[str, Any], rows: list[dict[str, Any]], *, max_samples: int) -> dict[str, Any]:
    n = max(1, totals["positions"])
    selected_n = max(1, totals["selected_move_count"])
    return {
        "position_count": totals["positions"],
        "edge_fence_success_rate": totals["success"] / n,
        "edge_distance_improvement_rate": totals["edge_improve"] / n,
        "confinement_area_improvement_rate": totals["confinement_improve"] / n,
        "black_king_mobility_reduction_rate": totals["mobility_reduce"] / n,
        "rook_safety_rate": totals["rook_safe"] / selected_n,
        "stalemate_avoidance_rate": totals["stalemate_safe"] / selected_n,
        "rook_blunder_count": totals["rook_blunders"],
        "legal_actuator_success_rate": totals["legal_actuator"] / selected_n,
        "after_state_foundation_reachable_count": totals["foundation_reachable"],
        "after_state_mate2_foundation_reachable_count": totals["mate2_reachable"],
        "after_state_mate1_foundation_reachable_count": totals["mate1_reachable"],
        "foundation_handoff_conversion_count": totals["handoff_conversion"],
        "average_request_strength_to_foundation": totals["request_strength_sum"] / selected_n,
        "selected_move_count": totals["selected_move_count"],
        "null_move_count": totals["null_move_count"],
        "candidate_budget_used": totals["candidate_budget_used"],
        "deep_reply_checks_run": totals["deep_reply_checks_run"],
        "same_graph_foundation_continuation_count": totals["same_graph_foundation_continuation_count"],
        "failure_bucket_counts": totals["failure_bucket_counts"],
        "samples": rows[:max_samples],
    }


def _edge_ablations(graph, heldout_fens, mate2_cfg, cfg, edge_weights) -> dict[str, Any]:
    masks = {
        "mask_edge_fence_terminals": {"mask_edge_fence_terminals": True},
        "mask_action_delta_terminals": {"mask_action_delta_terminals": True},
        "mask_internal_attention_request_strength_terminals": {"mask_internal_attention_terminals": True},
        "mask_safety_veto_terminals": {"mask_safety_veto_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "mask_frozen_mate1_foundation_quorum": {"mask_mate1_foundation_quorum": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_mate2_foundation_quorum": True},
        "disable_frozen_foundation_handoff_evidence": {"disable_foundation_handoff_evidence": True},
        "disable_deep_continuation_checks": {"disable_deep_continuation_checks": True},
    }
    ablation_fens = tuple(heldout_fens[: cfg.max_ablation_positions])
    return {
        name: _evaluate_edge_layer(graph, ablation_fens, mate2_cfg, cfg, edge_weights, foundation_handoff_enabled=True, masks=mask)
        for name, mask in masks.items()
    }


def _decision(
    cfg,
    *,
    foundation_sanity,
    train_eval,
    heldout,
    heldout_masked,
    ablations,
    equivalence,
    training,
    foundation_before_training,
    foundation_after_training,
    foundation_before_eval,
    foundation_after_eval,
) -> dict[str, Any]:
    foundation_train_m3_delta = foundation_after_training["m3"] - foundation_before_training["m3"]
    foundation_train_m4_delta = foundation_after_training["m4"] - foundation_before_training["m4"]
    foundation_eval_m3_delta = foundation_after_eval["m3"] - foundation_before_eval["m3"]
    foundation_eval_m4_delta = foundation_after_eval["m4"] - foundation_before_eval["m4"]
    edge_ablation_matters = ablations["mask_edge_fence_terminals"]["edge_fence_success_rate"] < heldout["edge_fence_success_rate"]
    actuator_collapses = ablations["mask_actuator_terminals"]["selected_move_count"] == 0
    handoff_matters = (
        ablations["disable_frozen_foundation_handoff_evidence"]["foundation_handoff_conversion_count"]
        < heldout["foundation_handoff_conversion_count"]
        or heldout["foundation_handoff_conversion_count"] == 0
    )
    checkpoint_pass = (
        foundation_train_m3_delta == 0
        and foundation_train_m4_delta == 0
        and foundation_eval_m3_delta == 0
        and foundation_eval_m4_delta == 0
        and foundation_sanity["foundation_mate1_accuracy"] >= 1.0
        and foundation_sanity["foundation_mate2_conversion_rate"] >= 1.0
        and foundation_sanity["foundation_replay_stability_pass"]
        and heldout["edge_fence_success_rate"] > 0.0
        and heldout["selected_move_count"] > 0
        and heldout["rook_blunder_count"] == 0
        and heldout["stalemate_avoidance_rate"] >= 1.0
        and edge_ablation_matters
        and actuator_collapses
        and handoff_matters
        and equivalence["mismatch_count"] == 0
    )
    return {
        "checkpoint_pass": checkpoint_pass,
        "foundation_frozen": True,
        "foundation_m3_updates_during_edge_training": foundation_train_m3_delta,
        "foundation_m4_promotions_during_edge_training": foundation_train_m4_delta,
        "foundation_m3_updates_during_eval": foundation_eval_m3_delta,
        "foundation_m4_promotions_during_eval": foundation_eval_m4_delta,
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
        "foundation_replay_stability_pass": foundation_sanity["foundation_replay_stability_pass"],
        "foundation_ablation_still_collapses": foundation_sanity["foundation_ablation_still_collapses"],
        "edge_fence_train_count": cfg.edge_fence_train_count,
        "edge_fence_heldout_count": cfg.edge_fence_heldout_count,
        "edge_fence_success_rate": heldout["edge_fence_success_rate"],
        "edge_distance_improvement_rate": heldout["edge_distance_improvement_rate"],
        "confinement_area_improvement_rate": heldout["confinement_area_improvement_rate"],
        "black_king_mobility_reduction_rate": heldout["black_king_mobility_reduction_rate"],
        "rook_safety_rate": heldout["rook_safety_rate"],
        "stalemate_avoidance_rate": heldout["stalemate_avoidance_rate"],
        "rook_blunder_count": heldout["rook_blunder_count"],
        "legal_actuator_success_rate": heldout["legal_actuator_success_rate"],
        "after_state_foundation_reachable_count": heldout["after_state_foundation_reachable_count"],
        "after_state_mate2_foundation_reachable_count": heldout["after_state_mate2_foundation_reachable_count"],
        "after_state_mate1_foundation_reachable_count": heldout["after_state_mate1_foundation_reachable_count"],
        "foundation_handoff_conversion_count": heldout["foundation_handoff_conversion_count"],
        "average_request_strength_to_foundation": heldout["average_request_strength_to_foundation"],
        "selected_move_count": heldout["selected_move_count"],
        "null_move_count": heldout["null_move_count"],
        "candidate_budget_used": heldout["candidate_budget_used"],
        "deep_reply_checks_run": heldout["deep_reply_checks_run"],
        "same_graph_foundation_continuation_count": heldout["same_graph_foundation_continuation_count"],
        "failure_bucket_counts": heldout["failure_bucket_counts"],
        "scheduler_equivalence_mismatch_count": equivalence["mismatch_count"],
        "m3_update_count_edge_fence_only": training["m3_update_count_edge_fence_only"],
        "m4_promotion_count_by_terminal_kind_edge_fence_only": {},
        "ablation_results": ablations,
        "masked_handoff_eval": heldout_masked,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _feature_keys(move, before, after, delta_edge, delta_mobility, delta_area) -> list[str]:
    return [
        f"move_piece={move.uci()[0]}",
        f"delta_black_king_edge_distance_sign={_sign(delta_edge)}",
        f"delta_black_king_mobility_sign={_sign(delta_mobility)}",
        f"delta_black_king_mobility_gain_bucket={_gain_bucket(-delta_mobility)}",
        f"delta_confinement_area_sign={_sign(delta_area)}",
        f"delta_confinement_area_gain_bucket={_gain_bucket(-delta_area)}",
        f"combined_progress_gain_bucket={_gain_bucket(max(0.0, -delta_area) + (2.0 * max(0.0, -delta_mobility)) + (2.0 * max(0.0, -delta_edge)))}",
        f"rook_safe_after={int(after['rook_safe'] > 0.0)}",
        f"rook_attacked_after={int(after['rook_attacked_after'] > 0.0)}",
        f"gives_check={int(after['gives_check'] > 0.0)}",
        f"king_support_distance_bucket={min(4, int(after['king_support_distance']))}",
        f"black_king_edge_distance_bucket={int(before['black_king_edge_distance'])}",
    ]


def _edge_reward(row: dict[str, Any]) -> float:
    return (
        (0.35 if row["delta_black_king_edge_distance"] < 0 else -0.05)
        + (0.25 if row["delta_confinement_area"] < 0 else -0.03)
        + (0.20 if row["delta_black_king_legal_mobility"] < 0 else -0.02)
        + (0.15 if row["after_features"]["rook_safe"] > 0.0 else -1.0)
        + (0.10 if row["after_features"]["gives_check"] > 0.0 else 0.0)
        + (-1.0 if row["after_features"]["stalemate_after"] > 0.0 else 0.0)
    )


def _failure_bucket(candidate_rows: list[dict[str, Any]], selected: dict[str, Any] | None) -> str:
    if selected is None:
        if not any(_edge_reward(row) > 0.0 for row in candidate_rows):
            return "no_edge_improving_candidate_found"
        if any(row["cheap_score"] > 0.0 for row in candidate_rows):
            return "edge_candidate_rejected_by_attention"
        return "candidate_cap_or_scheduler_blocked"
    if selected["actuator_terminal_state"] not in {"TRUE", "CONFIRMED"}:
        return "edge_candidate_selected_but_illegal"
    if selected["after_features"]["rook_attacked_after"] > 0.0 or selected["after_features"]["rook_safe"] == 0.0:
        return "rook_blunder_veto_failed"
    if selected["after_features"]["stalemate_after"] > 0.0:
        return "stalemate_veto_failed"
    if selected["delta_confinement_area"] < 0 and not selected["foundation_handoff_reachable"]:
        return "confinement_improved_but_foundation_not_closer"
    if any(row["foundation_handoff_reachable"] for row in candidate_rows) and not selected["foundation_handoff_reachable"]:
        return "foundation_handoff_available_but_not_selected"
    if selected["foundation_handoff_reachable"] and not selected["foundation_handoff_conversion"]:
        return "foundation_handoff_selected_but_chain_failed"
    if selected["cheap_score"] < 0.0:
        return "selection_lost_to_false_positive"
    return "none"


def _position_features(board: chess.Board) -> dict[str, float]:
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    rook = _white_rook_square(board)
    if wk is None or bk is None:
        return {}
    area = _confinement_area(board, rook, bk)
    return {
        "black_king_edge_distance": float(_black_edge_distance(board)),
        "black_king_legal_mobility": float(_black_king_mobility(board)),
        "rook_fence_line": 0.0 if rook is None else float(chess.square_file(rook) == chess.square_file(bk) or chess.square_rank(rook) == chess.square_rank(bk)),
        "rook_fence_distance": 8.0 if rook is None else float(min(abs(chess.square_file(rook) - chess.square_file(bk)), abs(chess.square_rank(rook) - chess.square_rank(bk)))),
        "confinement_area": float(area),
        "kings_distance": float(chess.square_distance(wk, bk)),
        "king_support_distance": 8.0 if rook is None else float(chess.square_distance(wk, rook)),
        "rook_safe": 0.0 if _rook_missing_or_attacked(board) else 1.0,
        "rook_attacked_after": 1.0 if _rook_missing_or_attacked(board) else 0.0,
        "gives_check": 1.0 if board.is_check() else 0.0,
        "stalemate_after": 1.0 if board.is_stalemate() else 0.0,
    }


def _white_rook_square(board: chess.Board) -> int | None:
    rooks = list(board.pieces(chess.ROOK, chess.WHITE))
    return rooks[0] if rooks else None


def _rook_missing_or_attacked(board: chess.Board) -> bool:
    rook = _white_rook_square(board)
    if rook is None:
        return True
    return board.is_attacked_by(chess.BLACK, rook)


def _black_edge_distance(board: chess.Board) -> int:
    bk = board.king(chess.BLACK)
    if bk is None:
        return 8
    f = chess.square_file(bk)
    r = chess.square_rank(bk)
    return min(f, 7 - f, r, 7 - r)


def _black_king_mobility(board: chess.Board) -> int:
    probe = board.copy(stack=False)
    probe.turn = chess.BLACK
    return sum(1 for move in probe.legal_moves if probe.piece_at(move.from_square) and probe.piece_at(move.from_square).piece_type == chess.KING)


def _confinement_area(board: chess.Board, rook: int | None, black_king: int) -> int:
    if rook is None:
        return 64
    rf, rr = chess.square_file(rook), chess.square_rank(rook)
    bf, br = chess.square_file(black_king), chess.square_rank(black_king)
    file_span = 8
    rank_span = 8
    if rf < bf:
        file_span = 7 - rf
    elif rf > bf:
        file_span = rf
    if rr < br:
        rank_span = 7 - rr
    elif rr > br:
        rank_span = rr
    return file_span * rank_span


def _sign(value: float) -> int:
    return -1 if value < 0 else (1 if value > 0 else 0)


def _gain_bucket(value: float) -> int:
    gain = max(0.0, float(value))
    if gain <= 0.0:
        return 0
    if gain <= 2.0:
        return 1
    if gain <= 5.0:
        return 2
    if gain <= 12.0:
        return 3
    return 4


def _foundation_counts(graph: NativeReConKRKGraph) -> dict[str, int]:
    return {"m3": graph.m3_update_count, "m4": graph.m4_event_count}


def _write_progress(cfg: FrozenFoundationEdgeFenceReentryConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class _EdgeIds:
    fen: str
    move_uci: str

    @property
    def digest(self) -> str:
        return hashlib.sha1(f"tg28a|{self.fen}|{self.move_uci}".encode("utf-8")).hexdigest()[:16]

    @property
    def quorum_script(self) -> str:
        return f"tg28a_edge_quorum_{self.digest}"

    @property
    def evidence_terminal(self) -> str:
        return f"{self.quorum_script}_evidence"

    @property
    def edge_terminal(self) -> str:
        return f"{self.quorum_script}_edge_terminal"

    @property
    def action_delta_terminal(self) -> str:
        return f"{self.quorum_script}_action_delta_terminal"

    @property
    def attention_terminal(self) -> str:
        return f"{self.quorum_script}_attention_terminal"

    @property
    def safety_terminal(self) -> str:
        return f"{self.quorum_script}_safety_terminal"

    @property
    def foundation_terminal(self) -> str:
        return f"{self.quorum_script}_foundation_terminal"

    @property
    def actuator_terminal(self) -> str:
        return f"{self.quorum_script}_actuator_terminal"

def _purity_boundary() -> dict[str, Any]:
    return {
        "native_recon_graph_execution": True,
        "foundation_frozen": True,
        "edge_fence_labels_learner_visible": False,
        "stage_labels_learner_visible": False,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "direct_provider_override": False,
        "edge_fence_candidate_choice_mediated_by_native_quorum": True,
    }
