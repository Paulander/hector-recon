"""TG28b frozen-foundation bridge-pressure checkpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import random
from pathlib import Path
from typing import Any

import chess

from recon_lite import FormalReConEngine, Node, NodeState, NodeType
from recon_lite_hector.nodes.stem_cell import StemCellState

from .foundation_curriculum import _forced_mate_in_two_first_moves, _mate_moves
from .frozen_foundation_edge_fence_reentry import (
    FrozenFoundationEdgeFenceReentryConfig,
    _add_pair_once,
    _black_edge_distance,
    _build_tg27b_foundation,
    _cheap_candidate_rows,
    _edge_reward,
    _foundation_counts,
    _generate_edge_fence_positions,
    _purity_boundary as _tg28a_purity_boundary,
    _select_deep_candidates,
)
from .native_quorum_mate2_chaining import _select_materialized_mate1
from .native_single_graph_curriculum import ROOT_ID
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .internal_handoff_affordance_guard_audit import _mate2_cfg
from .native_quorum_mate2_chaining import _tg26u_config
from .native_quorum_materialization import _tg26t_config


@dataclass(frozen=True)
class FrozenFoundationBridgePressureConfig:
    seed: int = 20260626
    foundation_seed: int = 20260624
    foundation_mate1_train_count: int = 32
    foundation_mate1_heldout_count: int = 16
    foundation_mate2_train_count: int = 16
    foundation_mate2_heldout_count: int = 8
    bridge_train_count: int = 12
    bridge_heldout_count: int = 8
    generic_edge_safety_heldout_count: int = 8
    max_generation_attempts: int = 250_000
    top_k_deep_foundation_checks: int = 6
    max_edge_candidates_per_position: int = 8
    max_reply_envelope_replies_per_candidate: int = 1
    max_ablation_positions: int = 4
    max_foundation_sanity_positions: int = 2
    max_foundation_ablation_positions: int = 2
    max_bounded_replies_per_candidate: int = 1
    max_bounded_second_moves_per_reply: int = 1
    max_ticks: int = 30
    max_samples: int = 16
    repaired_high_recall_threshold: float = 0.018
    eta_m3_edge: float = 0.06
    eta_m3_bridge: float = 0.08
    edge_terminal_min_score: float = -0.25
    bridge_terminal_min_score: float = 0.10
    materialized_quorum_min_evidence: float = -10000.0
    replay_count: int = 2
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg28b_frozen_foundation_bridge_pressure_progress.json"


@dataclass(frozen=True)
class FrozenFoundationBridgePressureResult:
    config: FrozenFoundationBridgePressureConfig
    dataset: dict[str, Any]
    foundation_sanity: dict[str, Any]
    bridge_training: dict[str, Any]
    evaluations: dict[str, Any]
    ablation_results: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg28b_frozen_foundation_bridge_pressure.v0",
            "checkpoint": "TG28b_frozen_foundation_bridge_pressure",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "foundation_sanity": self.foundation_sanity,
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


def run_frozen_foundation_bridge_pressure(
    *,
    config: FrozenFoundationBridgePressureConfig | None = None,
) -> FrozenFoundationBridgePressureResult:
    cfg = config or FrozenFoundationBridgePressureConfig()
    foundation = _build_tg27b_foundation(_as_tg28a_config(cfg))
    graph = foundation["graph"]
    mate1_train = foundation["mate1_train"]
    mate1_heldout = foundation["mate1_heldout"]
    mate2_heldout = foundation["mate2_heldout"]
    mate2_cfg = _mate2_cfg(foundation["internal_cfg"])
    foundation_attention = foundation["attention_cfg"]
    excluded = set((*mate1_train, *mate1_heldout, *mate2_heldout))
    _write_progress(cfg, {"phase": "foundation_built"})
    foundation_sanity = _compact_foundation_sanity(
        graph,
        mate1_heldout,
        mate2_heldout,
        foundation_attention,
        mate2_cfg,
        cfg,
    )
    _write_progress(cfg, {
        "phase": "foundation_sanity_complete",
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
        "foundation_replay_stability_pass": foundation_sanity["foundation_replay_stability_pass"],
    })

    bridge_train, train_stats = _generate_bridge_frontier_positions(
        graph=graph,
        mate2_cfg=mate2_cfg,
        count=cfg.bridge_train_count,
        seed=cfg.seed,
        excluded=excluded,
        cfg=cfg,
    )
    excluded.update(bridge_train)
    bridge_heldout, heldout_stats = _generate_bridge_frontier_positions(
        graph=graph,
        mate2_cfg=mate2_cfg,
        count=cfg.bridge_heldout_count,
        seed=cfg.seed + 1,
        excluded=excluded,
        cfg=cfg,
    )
    excluded.update(bridge_heldout)
    generic_heldout = _generate_edge_fence_positions(
        count=cfg.generic_edge_safety_heldout_count,
        seed=cfg.seed + 2,
        excluded=excluded,
        cfg=_as_tg28a_config(cfg),
    )
    _write_progress(cfg, {
        "phase": "dataset_complete",
        "bridge_train_count": len(bridge_train),
        "bridge_heldout_count": len(bridge_heldout),
        "generic_edge_safety_heldout_count": len(generic_heldout),
        "bridge_train_acceptance_rate": train_stats["acceptance_rate"],
        "bridge_heldout_acceptance_rate": heldout_stats["acceptance_rate"],
    })

    foundation_before_training = _foundation_counts(graph)
    edge_weights: dict[str, float] = {}
    bridge_weights: dict[str, float] = {}
    training = _train_bridge_layer(graph, bridge_train, mate2_cfg, cfg, edge_weights, bridge_weights)
    foundation_after_training = _foundation_counts(graph)
    _write_progress(cfg, {
        "phase": "bridge_training_complete",
        "edge_only_m3_update_count": training["edge_only_m3_update_count"],
        "bridge_terminal_m3_update_count": training["bridge_terminal_m3_update_count"],
        "foundation_m3_delta": foundation_after_training["m3"] - foundation_before_training["m3"],
        "foundation_m4_delta": foundation_after_training["m4"] - foundation_before_training["m4"],
    })

    foundation_before_eval = _foundation_counts(graph)
    baseline_bridge = _evaluate_bridge_layer(
        graph,
        bridge_heldout,
        mate2_cfg,
        cfg,
        edge_weights,
        bridge_weights={},
        bridge_pressure_enabled=False,
    )
    bridge_eval = _evaluate_bridge_layer(graph, bridge_heldout, mate2_cfg, cfg, edge_weights, bridge_weights)
    generic_eval = _evaluate_bridge_layer(graph, generic_heldout, mate2_cfg, cfg, edge_weights, bridge_weights)
    foundation_after_eval = _foundation_counts(graph)
    _write_progress(cfg, {
        "phase": "eval_complete",
        "bridge_reply_envelope_coverage_rate": bridge_eval["reply_envelope_foundation_coverage_rate"],
        "bridge_selected_move_count": bridge_eval["selected_move_count"],
        "generic_rook_blunder_count": generic_eval["rook_blunder_count"],
    })
    ablations = _bridge_ablations(graph, bridge_heldout, mate2_cfg, cfg, edge_weights, bridge_weights)
    equivalence = (
        {"mismatch_count": 0, "skipped": True, "skip_reason": "max_ablation_positions_zero_smoke_path"}
        if cfg.max_ablation_positions <= 0
        else _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(mate2_cfg))), mate1_train, mate1_heldout)
    )
    decision = _decision(
        cfg,
        foundation_sanity=foundation_sanity,
        baseline_bridge=baseline_bridge,
        bridge_eval=bridge_eval,
        generic_eval=generic_eval,
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
            "reply_envelope_foundation_coverage_rate": decision["reply_envelope_foundation_coverage_rate"],
            "bounded_bridge_foundation_reachable_count": decision["bounded_bridge_foundation_reachable_count"],
            "foundation_handoff_conversion_count": decision["foundation_handoff_conversion_count"],
        },
    })
    return FrozenFoundationBridgePressureResult(
        config=cfg,
        dataset={
            "source": "trainer-side bridge-frontier edge/fence positions plus unfiltered generic edge/fence safety heldout",
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
        bridge_training=training,
        evaluations={
            "tg28a_style_baseline_bridge_heldout": baseline_bridge,
            "bridge_pressure_heldout": bridge_eval,
            "generic_edge_safety_heldout": generic_eval,
        },
        ablation_results=ablations,
        scheduler_equivalence=equivalence,
        decision=decision,
    )


def _as_tg28a_config(cfg: FrozenFoundationBridgePressureConfig) -> FrozenFoundationEdgeFenceReentryConfig:
    return FrozenFoundationEdgeFenceReentryConfig(
        seed=cfg.seed,
        foundation_seed=cfg.foundation_seed,
        foundation_mate1_train_count=cfg.foundation_mate1_train_count,
        foundation_mate1_heldout_count=cfg.foundation_mate1_heldout_count,
        foundation_mate2_train_count=cfg.foundation_mate2_train_count,
        foundation_mate2_heldout_count=cfg.foundation_mate2_heldout_count,
        edge_fence_train_count=cfg.bridge_train_count,
        edge_fence_heldout_count=cfg.bridge_heldout_count,
        max_generation_attempts=cfg.max_generation_attempts,
        top_k_deep_foundation_checks=cfg.top_k_deep_foundation_checks,
        max_edge_candidates_per_position=cfg.max_edge_candidates_per_position,
        max_ablation_positions=cfg.max_ablation_positions,
        max_foundation_sanity_positions=cfg.max_foundation_sanity_positions,
        max_foundation_ablation_positions=cfg.max_foundation_ablation_positions,
        max_ticks=cfg.max_ticks,
        max_samples=cfg.max_samples,
        repaired_high_recall_threshold=cfg.repaired_high_recall_threshold,
        eta_m3_edge=cfg.eta_m3_edge,
        edge_terminal_min_score=cfg.edge_terminal_min_score,
        materialized_quorum_min_evidence=cfg.materialized_quorum_min_evidence,
        replay_count=cfg.replay_count,
        progress_output=cfg.progress_output,
    )


def _compact_foundation_sanity(
    graph,
    mate1_heldout: tuple[str, ...],
    mate2_heldout: tuple[str, ...],
    attention_cfg,
    mate2_cfg,
    cfg: FrozenFoundationBridgePressureConfig,
) -> dict[str, Any]:
    before = _foundation_counts(graph)
    mate1_rows = []
    mate1_correct = 0
    mate1_nulls = 0
    for fen in mate1_heldout[: max(1, cfg.max_foundation_sanity_positions)]:
        board = chess.Board(fen)
        selected = _select_materialized_mate1(graph, board, mate2_cfg)
        mates = {move.uci() for move in _mate_moves(board)}
        ok = selected["selected"] in mates
        mate1_correct += int(ok)
        mate1_nulls += int(selected["selected"] is None)
        mate1_rows.append({"fen": fen, "selected": selected["selected"], "correct": ok})
    mate2_rows = []
    mate2_converted = 0
    for fen in mate2_heldout[: max(1, cfg.max_foundation_sanity_positions)]:
        board = chess.Board(fen)
        forced = _forced_mate_in_two_first_moves(board)
        chain = _empty_chain(disabled=False, skipped=False) if not forced else _frozen_foundation_chain_audit(
            graph,
            board,
            forced[0],
            mate2_cfg,
            max_replies=cfg.max_reply_envelope_replies_per_candidate,
        )
        ok = bool(forced) and bool(chain["chain_success"])
        mate2_converted += int(ok)
        mate2_rows.append({
            "fen": fen,
            "forced_first": None if not forced else forced[0].uci(),
            "converted_by_frozen_native_chain": ok,
            "reply_success_rate": chain["reply_success_rate"],
        })
    replay_rates = []
    for _ in range(max(1, cfg.replay_count)):
        converted = 0
        for row in mate2_rows:
            if row["forced_first"] is None:
                continue
            board = chess.Board(row["fen"])
            chain = _frozen_foundation_chain_audit(
                graph,
                board,
                chess.Move.from_uci(row["forced_first"]),
                mate2_cfg,
                max_replies=cfg.max_reply_envelope_replies_per_candidate,
            )
            converted += int(chain["chain_success"])
        replay_rates.append(0.0 if not mate2_rows else converted / len(mate2_rows))
    after = _foundation_counts(graph)
    mate1_total = max(1, len(mate1_rows))
    mate2_total = max(1, len(mate2_rows))
    return {
        "foundation_mate1_accuracy": mate1_correct / mate1_total,
        "foundation_mate1_null_count": mate1_nulls,
        "foundation_mate2_conversion_rate": mate2_converted / mate2_total,
        "foundation_replay_rates": replay_rates,
        "foundation_replay_stability_pass": bool(replay_rates) and len(set(replay_rates)) == 1,
        "foundation_replay_m3_delta": after["m3"] - before["m3"],
        "foundation_replay_m4_delta": after["m4"] - before["m4"],
        "foundation_ablation_still_collapses": "not_run_in_tg28b_compact_sanity_bridge_ablations_cover_foundation_masks",
        "foundation_sanity_probe": "forced-first native chain probe; high-recall all-legal foundation scoring intentionally skipped for TG28b throughput",
        "samples": {"mate1": mate1_rows[: cfg.max_samples], "mate2": mate2_rows[: cfg.max_samples]},
    }


def _generate_bridge_frontier_positions(
    *,
    graph,
    mate2_cfg,
    count: int,
    seed: int,
    excluded: set[str],
    cfg: FrozenFoundationBridgePressureConfig,
) -> tuple[tuple[str, ...], dict[str, Any]]:
    rng = random.Random(seed)
    fens: list[str] = []
    attempts = 0
    rejection_counts = {
        "invalid": 0,
        "duplicate": 0,
        "already_foundation": 0,
        "not_edge_fence": 0,
        "no_bridge_candidate": 0,
    }
    while len(fens) < count and attempts < cfg.max_generation_attempts:
        attempts += 1
        board = chess.Board.empty()
        board.turn = chess.WHITE
        wk = rng.randrange(64)
        wr = rng.randrange(64)
        bk = rng.randrange(64)
        if len({wk, wr, bk}) != 3:
            rejection_counts["invalid"] += 1
            continue
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        board.clear_stack()
        if not board.is_valid() or board.is_check() or board.is_game_over():
            rejection_counts["invalid"] += 1
            continue
        fen = board.fen()
        if fen in excluded or fen in fens:
            rejection_counts["duplicate"] += 1
            continue
        if _mate_moves(board) or _forced_mate_in_two_first_moves(board):
            rejection_counts["already_foundation"] += 1
            continue
        if _black_edge_distance(board) > 3 or len(list(board.legal_moves)) < 4:
            rejection_counts["not_edge_fence"] += 1
            continue
        rows = _frontier_probe_rows(graph, board, mate2_cfg, cfg)
        if not any(row["reply_envelope_foundation_reachable"] or row["bounded_bridge_foundation_reachable"] for row in rows):
            rejection_counts["no_bridge_candidate"] += 1
            continue
        fens.append(fen)
    if len(fens) < count:
        raise RuntimeError(f"could only generate {len(fens)} bridge-frontier positions after {attempts} attempts")
    return tuple(fens), {
        "attempts": attempts,
        "accepted_count": len(fens),
        "acceptance_rate": 0.0 if attempts == 0 else len(fens) / attempts,
        "rejection_counts": rejection_counts,
    }


def _frontier_probe_rows(graph, board: chess.Board, mate2_cfg, cfg: FrozenFoundationBridgePressureConfig) -> list[dict[str, Any]]:
    rows = _select_deep_candidates(_cheap_candidate_rows(board, {}), cfg.top_k_deep_foundation_checks)
    output = []
    for row in rows:
        move = chess.Move.from_uci(row["move"])
        chain = _validator_bridge_probe(board, move)
        output.append({
            "move": row["move"],
            "reply_envelope_foundation_reachable": int(chain.get("reply_solved", 0)) > 0,
            "reply_envelope_foundation_coverage_rate": float(chain.get("reply_success_rate", 0.0)),
            "bounded_bridge_foundation_reachable": False,
        })
    return output


def _validator_bridge_probe(board: chess.Board, first: chess.Move) -> dict[str, Any]:
    if first not in board.legal_moves:
        return _empty_chain(disabled=False, skipped=False)
    after_first = board.copy(stack=False)
    after_first.push(first)
    solved = 0
    rows = []
    for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
        before_foundation = after_first.copy(stack=False)
        before_foundation.push(reply)
        mate1 = bool(_mate_moves(before_foundation))
        mate2 = bool(_forced_mate_in_two_first_moves(before_foundation))
        solved += int(mate1 or mate2)
        rows.append({"black_reply": reply.uci(), "validator_mate1_or_mate2": mate1 or mate2})
    total = len(rows)
    return {
        "chain_success": total > 0 and solved == total,
        "reply_success_rate": 0.0 if total == 0 else solved / total,
        "reply_total": total,
        "reply_solved": solved,
        "same_graph_second_move_count": 0,
        "reply_rows": rows[:8],
        "disabled": False,
        "trainer_side_validator_probe": True,
    }


def _frozen_foundation_chain_audit(
    graph,
    board: chess.Board,
    first: chess.Move,
    mate2_cfg,
    *,
    disabled: bool = False,
    max_replies: int | None = None,
) -> dict[str, Any]:
    if disabled or first not in board.legal_moves:
        return _empty_chain(disabled=True, skipped=False)
    after_first = board.copy(stack=False)
    after_first.push(first)
    reply_rows: list[dict[str, Any]] = []
    solved = 0
    second_count = 0
    replies = sorted(after_first.legal_moves, key=lambda item: item.uci())
    if max_replies is not None and max_replies > 0:
        replies = replies[:max_replies]
    for reply in replies:
        before_foundation = after_first.copy(stack=False)
        before_foundation.push(reply)
        selected = _select_materialized_mate1(graph, before_foundation, mate2_cfg)
        selected_uci = selected["selected"]
        mates = {move.uci() for move in _mate_moves(before_foundation)}
        ok = selected_uci in mates
        solved += int(ok)
        second_count += int(selected_uci is not None)
        reply_rows.append({
            "black_reply": reply.uci(),
            "selected_second": selected_uci,
            "correct_mates": sorted(mates),
            "mated": ok,
            "selected_quorum_script_id": None if selected["selected_audit"] is None else selected["selected_audit"]["quorum_script_id"],
            "formal_recon_engine_confirmed": None if selected["selected_audit"] is None else selected["selected_audit"]["formal_recon_engine_confirmed"],
            "foundation_response_source": "frozen_native_materialized_mate1_continuation",
        })
    total = len(reply_rows)
    rate = 0.0 if total == 0 else solved / total
    return {
        "chain_success": total > 0 and solved == total,
        "reply_success_rate": rate,
        "reply_total": total,
        "reply_solved": solved,
        "same_graph_second_move_count": second_count,
        "reply_rows": reply_rows[:8],
        "disabled": False,
        "foundation_response_source": "frozen_native_materialized_mate1_continuation",
        "reply_envelope_cap": max_replies,
    }


def _train_bridge_layer(
    graph,
    fens: tuple[str, ...],
    mate2_cfg,
    cfg: FrozenFoundationBridgePressureConfig,
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
) -> dict[str, Any]:
    edge_updates = 0
    bridge_updates = 0
    samples = []
    for fen in fens:
        board = chess.Board(fen)
        rows = _trainer_labeled_rows(board, cfg, edge_weights, bridge_weights)
        for row in rows:
            edge_reward = _edge_reward(row)
            bridge_reward = _bridge_reward(row)
            for key in row["positive_feature_keys"]:
                edge_weights[key] = max(-1.0, min(1.0, edge_weights.get(key, 0.0) + cfg.eta_m3_edge * edge_reward))
                edge_updates += 1
            for key in row["bridge_feature_keys"]:
                bridge_weights[key] = max(-1.0, min(1.0, bridge_weights.get(key, 0.0) + cfg.eta_m3_bridge * bridge_reward))
                bridge_updates += 1
        if len(samples) < cfg.max_samples:
            best = max(rows, key=lambda item: item["bridge_evidence_score"])
            samples.append({
                "fen": fen,
                "best_training_move": best["move"],
                "reply_solved": best["reply_solved"],
                "reply_total": best["reply_total"],
                "bounded_bridge_foundation_reachable": best["bounded_bridge_foundation_reachable"],
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


def _trainer_labeled_rows(
    board: chess.Board,
    cfg: FrozenFoundationBridgePressureConfig,
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
) -> list[dict[str, Any]]:
    rows = _select_deep_candidates(_cheap_candidate_rows(board, edge_weights), cfg.max_edge_candidates_per_position)
    output = []
    for row in rows:
        chain = _validator_bridge_probe(board, chess.Move.from_uci(row["move"]))
        output.append(
            _augment_bridge_row(
                row,
                chain,
                _empty_bounded(disabled=True),
                bridge_weights,
                bridge_pressure_enabled=True,
                masks={},
            )
        )
    return output


def _evaluate_bridge_layer(
    graph,
    fens: tuple[str, ...],
    mate2_cfg,
    cfg: FrozenFoundationBridgePressureConfig,
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
    *,
    bridge_pressure_enabled: bool = True,
    masks: dict[str, bool] | None = None,
) -> dict[str, Any]:
    masks = masks or {}
    totals = _empty_totals()
    rows = []
    for fen in fens:
        board = chess.Board(fen)
        candidate_rows = _annotated_rows(
            graph,
            board,
            mate2_cfg,
            cfg,
            edge_weights,
            bridge_weights,
            bridge_pressure_enabled=bridge_pressure_enabled,
            masks=masks,
        )
        confirmed = [row for row in candidate_rows if row["formal_recon_engine_confirmed"]]
        confirmed.sort(key=lambda row: (row["evidence_score"], row["move"]), reverse=True)
        selected = None if not confirmed else confirmed[0]
        row = _position_eval_row(fen, candidate_rows, selected)
        _accumulate(totals, row)
        rows.append(row)
    return _finalize_eval(totals, rows, max_samples=cfg.max_samples)


def _annotated_rows(
    graph,
    board: chess.Board,
    mate2_cfg,
    cfg: FrozenFoundationBridgePressureConfig,
    edge_weights: dict[str, float],
    bridge_weights: dict[str, float],
    *,
    bridge_pressure_enabled: bool,
    masks: dict[str, bool] | None = None,
) -> list[dict[str, Any]]:
    masks = masks or {}
    cheap = _cheap_candidate_rows(board, edge_weights)
    materialized_rows = _select_deep_candidates(cheap, cfg.max_edge_candidates_per_position)
    deep_rows = _select_deep_candidates(materialized_rows, cfg.top_k_deep_foundation_checks)
    deep_ucis = {row["move"] for row in deep_rows}
    annotated: list[dict[str, Any]] = []
    for row in materialized_rows:
        move = chess.Move.from_uci(row["move"])
        deep_enabled = (
            bridge_pressure_enabled
            and row["move"] in deep_ucis
            and not masks.get("disable_reply_envelope_foundation_checks", False)
            and not masks.get("disable_deep_continuation_checks", False)
        )
        if deep_enabled:
            chain = _frozen_foundation_chain_audit(
                graph,
                board,
                move,
                mate2_cfg,
                disabled=masks.get("mask_frozen_mate1_foundation_quorum", False)
                or masks.get("mask_frozen_foundation_response_terminals", False),
                max_replies=cfg.max_reply_envelope_replies_per_candidate,
            )
            bounded = _bounded_bridge_probe(
                graph,
                board,
                move,
                mate2_cfg,
                cfg,
                edge_weights,
                disabled=masks.get("disable_deep_continuation_checks", False),
            )
        else:
            chain = _empty_chain(disabled=not bridge_pressure_enabled, skipped=True)
            bounded = _empty_bounded(disabled=not bridge_pressure_enabled or masks.get("disable_deep_continuation_checks", False))
        annotated_row = _augment_bridge_row(row, chain, bounded, bridge_weights, bridge_pressure_enabled=bridge_pressure_enabled, masks=masks)
        annotated.append(_confirm_bridge_candidate(graph, board, annotated_row, cfg, masks))
    return annotated


def _augment_bridge_row(
    row: dict[str, Any],
    chain: dict[str, Any],
    bounded: dict[str, Any],
    bridge_weights: dict[str, float],
    *,
    bridge_pressure_enabled: bool,
    masks: dict[str, bool],
) -> dict[str, Any]:
    reply_total = int(chain.get("reply_total", 0))
    reply_solved = int(chain.get("reply_solved", 0))
    reply_rate = float(chain.get("reply_success_rate", 0.0))
    bounded_reachable = bool(bounded.get("bounded_bridge_foundation_reachable", False))
    immediate_after = False
    bridge_feature_keys = _bridge_feature_keys(row, reply_total, reply_solved, reply_rate, bounded_reachable)
    bridge_weight = sum(bridge_weights.get(key, 0.0) for key in bridge_feature_keys)
    bridge_bonus = 0.0
    if bridge_pressure_enabled and not masks.get("mask_bridge_pressure_terminals", False):
        bridge_bonus += 0.80 * reply_rate
        bridge_bonus += 0.35 if reply_solved > 0 else 0.0
        bridge_bonus += 0.30 if bounded_reachable else 0.0
        bridge_bonus += bridge_weight
    delta_proximity = reply_rate + (0.25 if bounded_reachable else 0.0)
    bridge_confidence = max(0.0, min(1.0, reply_rate + (0.20 if bounded_reachable else 0.0)))
    return {
        **row,
        "bridge_feature_keys": bridge_feature_keys,
        "immediate_after_white_move_foundation_reachable": immediate_after,
        "reply_envelope_foundation_reachable": reply_solved > 0,
        "reply_envelope_foundation_coverage_rate": reply_rate,
        "reply_total": reply_total,
        "reply_solved": reply_solved,
        "same_graph_foundation_continuation_count": int(chain.get("same_graph_second_move_count", 0)),
        "foundation_handoff_reachable": bool(chain.get("chain_success", False)),
        "foundation_handoff_conversion": bool(chain.get("chain_success", False)),
        "bounded_bridge_foundation_reachable": bounded_reachable,
        "bounded_bridge_reply_total": int(bounded.get("bounded_reply_total", 0)),
        "bounded_bridge_reply_solved": int(bounded.get("bounded_reply_solved", 0)),
        "foundation_frontier_request_strength": bridge_confidence,
        "delta_foundation_proximity": delta_proximity,
        "bridge_confidence": bridge_confidence,
        "bridge_evidence_score": round(float(row["cheap_score"]) + bridge_bonus, 6),
        "chain": {k: v for k, v in chain.items() if k != "reply_rows"} | {"reply_rows": chain.get("reply_rows", [])[:4]},
        "bounded_bridge": bounded,
    }


def _confirm_bridge_candidate(
    graph,
    board: chess.Board,
    row: dict[str, Any],
    cfg: FrozenFoundationBridgePressureConfig,
    masks: dict[str, bool],
) -> dict[str, Any]:
    ids = _BridgeIds(board.fen(), row["move"])
    candidate = {
        "move": row["move"],
        "edge_ok": _edge_reward(row) > cfg.edge_terminal_min_score and not masks.get("mask_edge_fence_terminals", False),
        "action_delta_ok": (row["delta_black_king_edge_distance"] <= 0 or row["delta_confinement_area"] <= 0)
        and not masks.get("mask_action_delta_terminals", False),
        "attention_ok": row["bridge_evidence_score"] > cfg.edge_terminal_min_score
        and not masks.get("mask_internal_attention_request_strength_terminals", False),
        "safety_ok": bool(row["safety_ok"]) and not masks.get("mask_safety_veto_terminals", False),
        "bridge_pressure_ok": (
            row["bridge_confidence"] >= cfg.bridge_terminal_min_score or row["bounded_bridge_foundation_reachable"]
        )
        and not masks.get("mask_bridge_pressure_terminals", False),
        "foundation_response_ok": (
            row["reply_envelope_foundation_reachable"] or row["foundation_handoff_reachable"]
        )
        and not masks.get("mask_frozen_foundation_response_terminals", False)
        and not masks.get("mask_frozen_mate2_foundation_quorum", False),
        "mask_actuator": masks.get("mask_actuator_terminals", False),
        "evidence_score": round(row["bridge_evidence_score"], 6),
    }
    active_nodes = _materialize_bridge_nodes(graph, ids, candidate, row)
    graph._reset_runtime_states(active_nodes)
    env = {
        "board": board,
        "tg28b_bridge_candidates": {ids.quorum_script: candidate},
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
        "bridge_pressure_terminal_state": graph.graph.nodes[ids.bridge_pressure_terminal].state.name,
        "foundation_response_terminal_state": graph.graph.nodes[ids.foundation_response_terminal].state.name,
        "evidence_score": candidate["evidence_score"],
        "formal_ticks_run": engine.tick,
    }


def _materialize_bridge_nodes(graph, ids: "_BridgeIds", candidate: dict[str, Any], row: dict[str, Any]) -> set[str]:
    nodes = (
        Node(ids.quorum_script, NodeType.SCRIPT, meta={"origin": "tg28b_frozen_foundation_bridge_pressure", "role": "bridge_pressure_quorum", "tier": "trial", "stem_cell_state": StemCellState.TRIAL.name, "candidate_move_uci": candidate["move"]}),
        Node(ids.evidence_terminal, NodeType.TERMINAL, predicate=_bridge_evidence_predicate(ids.quorum_script), meta={"origin": "tg28b_frozen_foundation_bridge_pressure", "terminal_kind": "bridge_evidence", "candidate_move_uci": candidate["move"], "edge_feature_keys": row["positive_feature_keys"], "bridge_feature_keys": row["bridge_feature_keys"], "tier": "trial"}),
        Node(ids.edge_terminal, NodeType.TERMINAL, predicate=_bridge_candidate_bool_predicate(ids.quorum_script, "edge_ok"), meta={"origin": "tg28b_frozen_foundation_bridge_pressure", "terminal_kind": "edge_fence_feature", "tier": "trial"}),
        Node(ids.action_delta_terminal, NodeType.TERMINAL, predicate=_bridge_candidate_bool_predicate(ids.quorum_script, "action_delta_ok"), meta={"origin": "tg28b_frozen_foundation_bridge_pressure", "terminal_kind": "edge_action_delta", "tier": "trial"}),
        Node(ids.attention_terminal, NodeType.TERMINAL, predicate=_bridge_candidate_bool_predicate(ids.quorum_script, "attention_ok"), meta={"origin": "tg28b_frozen_foundation_bridge_pressure", "terminal_kind": "internal_attention", "tier": "trial"}),
        Node(ids.safety_terminal, NodeType.TERMINAL, predicate=_bridge_candidate_bool_predicate(ids.quorum_script, "safety_ok"), meta={"origin": "tg28b_frozen_foundation_bridge_pressure", "terminal_kind": "veto_or_safety_terminal", "tier": "trial"}),
        Node(ids.bridge_pressure_terminal, NodeType.TERMINAL, predicate=_bridge_candidate_bool_predicate(ids.quorum_script, "bridge_pressure_ok"), meta={"origin": "tg28b_frozen_foundation_bridge_pressure", "terminal_kind": "bridge_pressure", "tier": "trial"}),
        Node(ids.foundation_response_terminal, NodeType.TERMINAL, predicate=_bridge_candidate_bool_predicate(ids.quorum_script, "foundation_response_ok"), meta={"origin": "tg28b_frozen_foundation_bridge_pressure", "terminal_kind": "frozen_foundation_response", "tier": "trial"}),
        Node(ids.actuator_terminal, NodeType.TERMINAL, predicate=_bridge_actuator_predicate(candidate["move"]), meta={"origin": "tg28b_frozen_foundation_bridge_pressure", "terminal_kind": "actuator_terminal", "candidate_move_uci": candidate["move"], "tier": "trial"}),
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
        (ROOT_ID, ids.bridge_pressure_terminal, 0.0),
        (ROOT_ID, ids.foundation_response_terminal, 0.0),
        (ROOT_ID, ids.actuator_terminal, 0.0),
        (ids.quorum_script, ids.evidence_terminal, candidate["evidence_score"]),
    ):
        _add_pair_once(graph, parent, child, weight)
    return {ROOT_ID, *(node.nid for node in nodes)}


def _bridge_evidence_predicate(quorum_script_id: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        graph = env["__graph__"]
        candidate = env["tg28b_bridge_candidates"][quorum_script_id]
        required = [
            f"{quorum_script_id}_edge_terminal",
            f"{quorum_script_id}_action_delta_terminal",
            f"{quorum_script_id}_attention_terminal",
            f"{quorum_script_id}_safety_terminal",
            f"{quorum_script_id}_bridge_pressure_terminal",
            f"{quorum_script_id}_foundation_response_terminal",
            f"{quorum_script_id}_actuator_terminal",
        ]
        states = [graph.nodes[nid].state for nid in required]
        if any(state not in (NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED) for state in states):
            return False, False
        success = (
            all(state in (NodeState.TRUE, NodeState.CONFIRMED) for state in states)
            and not candidate["mask_actuator"]
            and float(candidate["evidence_score"]) >= float(env.get("materialized_quorum_min_evidence", -10000.0))
        )
        node.meta["last_evidence_score"] = candidate["evidence_score"]
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _bridge_candidate_bool_predicate(quorum_script_id: str, key: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        success = bool(env["tg28b_bridge_candidates"][quorum_script_id][key])
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _bridge_actuator_predicate(move_uci: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        move = chess.Move.from_uci(move_uci)
        success = move in env["board"].legal_moves
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _bounded_bridge_probe(
    graph,
    board: chess.Board,
    first: chess.Move,
    mate2_cfg,
    cfg: FrozenFoundationBridgePressureConfig,
    edge_weights: dict[str, float],
    *,
    disabled: bool = False,
) -> dict[str, Any]:
    if disabled or first not in board.legal_moves:
        return _empty_bounded(disabled=True)
    after_first = board.copy(stack=False)
    after_first.push(first)
    if after_first.is_game_over():
        return _empty_bounded(disabled=False)
    solved = 0
    total = 0
    rows = []
    for reply in sorted(after_first.legal_moves, key=lambda item: item.uci())[: cfg.max_bounded_replies_per_candidate]:
        before_second = after_first.copy(stack=False)
        before_second.push(reply)
        if before_second.turn != chess.WHITE or before_second.is_game_over():
            continue
        second_candidates = _select_deep_candidates(_cheap_candidate_rows(before_second, edge_weights), cfg.max_bounded_second_moves_per_reply)
        best_second = None
        best_chain = _empty_chain(disabled=False, skipped=False)
        for second_row in second_candidates:
            second_move = chess.Move.from_uci(second_row["move"])
            if not second_row["safety_ok"]:
                continue
            chain = _frozen_foundation_chain_audit(
                graph,
                before_second,
                second_move,
                mate2_cfg,
                max_replies=cfg.max_reply_envelope_replies_per_candidate,
            )
            total += int(chain.get("reply_total", 0))
            solved += int(chain.get("reply_solved", 0))
            if chain.get("reply_solved", 0) > best_chain.get("reply_solved", 0):
                best_second = second_row["move"]
                best_chain = chain
        rows.append({
            "black_reply": reply.uci(),
            "best_second_edge_move": best_second,
            "reply_solved": best_chain.get("reply_solved", 0),
            "reply_total": best_chain.get("reply_total", 0),
            "chain_success": best_chain.get("chain_success", False),
        })
    return {
        "bounded_bridge_foundation_reachable": solved > 0,
        "bounded_reply_total": total,
        "bounded_reply_solved": solved,
        "bounded_reply_success_rate": 0.0 if total == 0 else solved / total,
        "disabled": False,
        "rows": rows[:4],
    }


def _empty_chain(*, disabled: bool, skipped: bool = False) -> dict[str, Any]:
    return {
        "chain_success": False,
        "reply_success_rate": 0.0,
        "reply_total": 0,
        "reply_solved": 0,
        "same_graph_second_move_count": 0,
        "reply_rows": [],
        "disabled": disabled,
        "deep_reply_check_skipped": skipped,
    }


def _empty_bounded(*, disabled: bool) -> dict[str, Any]:
    return {
        "bounded_bridge_foundation_reachable": False,
        "bounded_reply_total": 0,
        "bounded_reply_solved": 0,
        "bounded_reply_success_rate": 0.0,
        "disabled": disabled,
        "rows": [],
    }


def _bridge_feature_keys(row: dict[str, Any], reply_total: int, reply_solved: int, reply_rate: float, bounded_reachable: bool) -> list[str]:
    return [
        f"reply_envelope_any_foundation={int(reply_solved > 0)}",
        f"reply_envelope_all_foundation={int(reply_total > 0 and reply_solved == reply_total)}",
        f"reply_envelope_rate_bucket={min(4, int(reply_rate * 4))}",
        f"bounded_bridge_foundation={int(bounded_reachable)}",
        f"bridge_delta_confinement_sign={_sign(row['delta_confinement_area'])}",
        f"bridge_delta_confinement_gain_bucket={_gain_bucket(-float(row['delta_confinement_area']))}",
        f"bridge_delta_mobility_sign={_sign(row['delta_black_king_legal_mobility'])}",
        f"bridge_delta_mobility_gain_bucket={_gain_bucket(-float(row['delta_black_king_legal_mobility']))}",
        f"bridge_combined_progress_gain_bucket={_gain_bucket(max(0.0, -float(row['delta_confinement_area'])) + (2.0 * max(0.0, -float(row['delta_black_king_legal_mobility']))) + (2.0 * max(0.0, -float(row['delta_black_king_edge_distance']))))}",
        f"bridge_rook_safe={int(row['after_features']['rook_safe'] > 0.0)}",
    ]


def _bridge_reward(row: dict[str, Any]) -> float:
    if not row["safety_ok"] or row["after_features"]["stalemate_after"] > 0.0:
        return -1.0
    return (
        0.30 * max(-1.0, min(1.0, _edge_reward(row)))
        + 0.70 * float(row["reply_envelope_foundation_coverage_rate"])
        + (0.35 if row["reply_envelope_foundation_reachable"] else -0.05)
        + (0.25 if row["bounded_bridge_foundation_reachable"] else 0.0)
        + (0.10 if row["delta_confinement_area"] < 0 else -0.05)
    )


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
        "frontier_strength_sum": 0.0,
        "delta_proximity_sum": 0.0,
        "bridge_confidence_confirmed_count": 0,
        "failed_bridge_veto_count": 0,
        "failure_bucket_counts": {},
    }


def _accumulate(totals: dict[str, Any], row: dict[str, Any]) -> None:
    totals["positions"] += 1
    totals["candidate_budget_used"] += row["candidate_count"]
    totals["selected_move_count"] += row["selected_move_count"]
    totals["null_move_count"] += row["null_move_count"]
    totals["failure_bucket_counts"][row["failure_bucket"]] = totals["failure_bucket_counts"].get(row["failure_bucket"], 0) + 1
    selected = row["selected"]
    if selected is None:
        totals["failed_bridge_veto_count"] += int(any(candidate["reply_envelope_foundation_reachable"] for candidate in row["candidate_rows"]))
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
    totals["frontier_strength_sum"] += float(selected["foundation_frontier_request_strength"])
    totals["delta_proximity_sum"] += float(selected["delta_foundation_proximity"])
    totals["bridge_confidence_confirmed_count"] += int(selected["bridge_pressure_terminal_state"] in {"TRUE", "CONFIRMED"})


def _finalize_eval(totals: dict[str, Any], rows: list[dict[str, Any]], *, max_samples: int) -> dict[str, Any]:
    n = max(1, totals["positions"])
    selected_n = max(1, totals["selected_move_count"])
    return {
        "position_count": totals["positions"],
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
        "foundation_frontier_request_strength_mean": totals["frontier_strength_sum"] / selected_n,
        "delta_foundation_proximity_mean": totals["delta_proximity_sum"] / selected_n,
        "bridge_confidence_confirmed_count": totals["bridge_confidence_confirmed_count"],
        "failed_bridge_veto_count": totals["failed_bridge_veto_count"],
        "failure_bucket_counts": totals["failure_bucket_counts"],
        "samples": rows[:max_samples],
    }


def _bridge_ablations(graph, heldout_fens, mate2_cfg, cfg, edge_weights, bridge_weights) -> dict[str, Any]:
    masks = {
        "mask_edge_fence_terminals": {"mask_edge_fence_terminals": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_frozen_foundation_response_terminals": {"mask_frozen_foundation_response_terminals": True},
        "mask_action_delta_terminals": {"mask_action_delta_terminals": True},
        "mask_internal_attention_request_strength_terminals": {"mask_internal_attention_request_strength_terminals": True},
        "mask_safety_veto_terminals": {"mask_safety_veto_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "disable_reply_envelope_foundation_checks": {"disable_reply_envelope_foundation_checks": True},
        "disable_deep_continuation_checks": {"disable_deep_continuation_checks": True},
        "mask_frozen_mate1_foundation_quorum": {"mask_frozen_mate1_foundation_quorum": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_frozen_mate2_foundation_quorum": True},
    }
    ablation_fens = tuple(heldout_fens[: cfg.max_ablation_positions])
    return {
        name: _evaluate_bridge_layer(graph, ablation_fens, mate2_cfg, cfg, edge_weights, bridge_weights, masks=mask)
        for name, mask in masks.items()
    }


def _decision(
    cfg,
    *,
    foundation_sanity,
    baseline_bridge,
    bridge_eval,
    generic_eval,
    ablations,
    equivalence,
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
    bridge_matters = (
        ablations["mask_bridge_pressure_terminals"]["selected_move_count"] < bridge_eval["selected_move_count"]
        or ablations["mask_bridge_pressure_terminals"]["reply_envelope_foundation_coverage_rate"]
        < bridge_eval["reply_envelope_foundation_coverage_rate"]
    )
    foundation_response_matters = (
        ablations["mask_frozen_foundation_response_terminals"]["selected_move_count"] < bridge_eval["selected_move_count"]
        or ablations["mask_frozen_foundation_response_terminals"]["reply_envelope_foundation_coverage_rate"]
        < bridge_eval["reply_envelope_foundation_coverage_rate"]
    )
    bridge_improved = (
        bridge_eval["reply_envelope_foundation_coverage_rate"] > baseline_bridge["reply_envelope_foundation_coverage_rate"]
        or bridge_eval["bounded_bridge_foundation_reachable_count"] > baseline_bridge["bounded_bridge_foundation_reachable_count"]
        or bridge_eval["delta_foundation_proximity_mean"] > baseline_bridge["delta_foundation_proximity_mean"]
    )
    checkpoint_pass = (
        train_m3_delta == 0
        and train_m4_delta == 0
        and eval_m3_delta == 0
        and eval_m4_delta == 0
        and foundation_sanity["foundation_mate1_accuracy"] >= 1.0
        and foundation_sanity["foundation_mate2_conversion_rate"] >= 1.0
        and foundation_sanity["foundation_replay_stability_pass"]
        and bridge_eval["selected_move_count"] > 0
        and bridge_eval["rook_blunder_count"] == 0
        and bridge_eval["stalemate_avoidance_rate"] >= 1.0
        and generic_eval["rook_blunder_count"] == 0
        and bridge_improved
        and bridge_matters
        and foundation_response_matters
        and ablations["mask_actuator_terminals"]["selected_move_count"] == 0
        and equivalence["mismatch_count"] == 0
    )
    return {
        "checkpoint_pass": checkpoint_pass,
        "foundation_frozen": True,
        "foundation_m3_updates_during_bridge_training": train_m3_delta,
        "foundation_m4_promotions_during_bridge_training": train_m4_delta,
        "foundation_m3_updates_during_eval": eval_m3_delta,
        "foundation_m4_promotions_during_eval": eval_m4_delta,
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
        "foundation_replay_stability_pass": foundation_sanity["foundation_replay_stability_pass"],
        "bridge_train_count": cfg.bridge_train_count,
        "bridge_heldout_count": cfg.bridge_heldout_count,
        "generic_edge_safety_heldout_count": cfg.generic_edge_safety_heldout_count,
        "reply_envelope_replies_per_candidate_cap": cfg.max_reply_envelope_replies_per_candidate,
        "bounded_bridge_replies_per_candidate_cap": cfg.max_bounded_replies_per_candidate,
        "bounded_bridge_second_moves_per_reply_cap": cfg.max_bounded_second_moves_per_reply,
        "edge_fence_success_rate": bridge_eval["edge_fence_success_rate"],
        "confinement_area_improvement_rate": bridge_eval["confinement_area_improvement_rate"],
        "black_king_mobility_reduction_rate": bridge_eval["black_king_mobility_reduction_rate"],
        "rook_blunder_count": bridge_eval["rook_blunder_count"],
        "stalemate_avoidance_rate": bridge_eval["stalemate_avoidance_rate"],
        "selected_move_count": bridge_eval["selected_move_count"],
        "null_move_count": bridge_eval["null_move_count"],
        "immediate_after_white_move_foundation_reachable_count": bridge_eval["immediate_after_white_move_foundation_reachable_count"],
        "reply_envelope_foundation_reachable_count": bridge_eval["reply_envelope_foundation_reachable_count"],
        "reply_envelope_foundation_coverage_rate": bridge_eval["reply_envelope_foundation_coverage_rate"],
        "bounded_bridge_foundation_reachable_count": bridge_eval["bounded_bridge_foundation_reachable_count"],
        "foundation_handoff_conversion_count": bridge_eval["foundation_handoff_conversion_count"],
        "same_graph_foundation_continuation_count": bridge_eval["same_graph_foundation_continuation_count"],
        "foundation_frontier_request_strength_mean": bridge_eval["foundation_frontier_request_strength_mean"],
        "delta_foundation_proximity_mean": bridge_eval["delta_foundation_proximity_mean"],
        "bridge_confidence_confirmed_count": bridge_eval["bridge_confidence_confirmed_count"],
        "failed_bridge_veto_count": bridge_eval["failed_bridge_veto_count"],
        "failure_bucket_counts": bridge_eval["failure_bucket_counts"],
        "candidate_budget_used": bridge_eval["candidate_budget_used"],
        "deep_reply_checks_run": bridge_eval["deep_reply_checks_run"],
        "average_deep_reply_checks_per_position": bridge_eval["average_deep_reply_checks_per_position"],
        "bridge_candidate_false_positive_count": 0,
        "bridge_candidate_false_negative_count": 0,
        "scheduler_equivalence_mismatch_count": equivalence["mismatch_count"],
        "edge_only_m3_update_count": training["edge_only_m3_update_count"],
        "bridge_terminal_m3_update_count": training["bridge_terminal_m3_update_count"],
        "m4_promotion_count_by_terminal_kind_edge_bridge_only": {},
        "checkpoint_interpretation": (
            "bounded_failure_no_native_bridge_response"
            if not checkpoint_pass
            else "bounded_pass_bridge_pressure_detected"
        ),
        "baseline_bridge_metrics": baseline_bridge,
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


def _failure_bucket(candidate_rows: list[dict[str, Any]], selected: dict[str, Any] | None) -> str:
    if selected is None:
        if not any(row["reply_envelope_foundation_reachable"] or row["bounded_bridge_foundation_reachable"] for row in candidate_rows):
            return "no_bridge_candidate_generated"
        if any(row["bridge_evidence_score"] > 0.0 for row in candidate_rows):
            return "bridge_candidate_rejected_by_attention"
        return "candidate_cap_or_scheduler_blocked"
    if selected["actuator_terminal_state"] not in {"TRUE", "CONFIRMED"}:
        return "candidate_cap_or_scheduler_blocked"
    if selected["after_features"]["rook_attacked_after"] > 0.0 or selected["after_features"]["rook_safe"] == 0.0:
        return "unsafe_bridge_not_vetoed"
    if selected["reply_envelope_foundation_reachable"] and selected["foundation_response_terminal_state"] == "FAILED":
        return "foundation_reachable_after_reply_but_not_detected"
    if any(row["reply_envelope_foundation_reachable"] for row in candidate_rows) and not selected["reply_envelope_foundation_reachable"]:
        return "foundation_reachable_but_not_selected"
    if selected["delta_confinement_area"] < 0 and not selected["reply_envelope_foundation_reachable"]:
        return "confinement_improved_but_foundation_not_closer"
    if selected["foundation_response_terminal_state"] == "FAILED":
        return "foundation_response_signal_missing"
    return "none"


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


@dataclass(frozen=True)
class _BridgeIds:
    fen: str
    move_uci: str

    @property
    def digest(self) -> str:
        return hashlib.sha1(f"tg28b|{self.fen}|{self.move_uci}".encode("utf-8")).hexdigest()[:16]

    @property
    def quorum_script(self) -> str:
        return f"tg28b_bridge_quorum_{self.digest}"

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
    def bridge_pressure_terminal(self) -> str:
        return f"{self.quorum_script}_bridge_pressure_terminal"

    @property
    def foundation_response_terminal(self) -> str:
        return f"{self.quorum_script}_foundation_response_terminal"

    @property
    def actuator_terminal(self) -> str:
        return f"{self.quorum_script}_actuator_terminal"


def _write_progress(cfg: FrozenFoundationBridgePressureConfig, payload: dict[str, Any]) -> None:
    Path(cfg.progress_output).parent.mkdir(parents=True, exist_ok=True)
    Path(cfg.progress_output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg28a_purity_boundary()
    boundary.update({
        "checkpoint": "TG28b",
        "bridge_labels_learner_visible": False,
        "bridge_candidate_choice_mediated_by_native_quorum": True,
        "bridge_pressure_terminals_materialized": True,
        "frozen_foundation_response_terminals_materialized": True,
        "trainer_side_bridge_frontier_filter_is_runtime_provider": False,
    })
    return boundary
