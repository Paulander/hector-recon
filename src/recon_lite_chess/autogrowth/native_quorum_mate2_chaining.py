"""TG26v native quorum Mate_In_2 chaining checkpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import chess

from recon_lite import FormalReConEngine, LinkType, Node, NodeState, NodeType
from recon_lite_hector.nodes.stem_cell import StemCellState

from .foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _generate_forced_mate_in_two_positions,
    _generate_mate_in_one_positions,
    _mate_moves,
    _move_reward,
)
from .native_quorum_materialization import (
    NativeQuorumMaterializationConfig,
    _add_hierarchy_pair_once,
    _candidate_row,
    _confirm_materialized_candidate,
    _is_action_or_check_atom,
    _purity_boundary as _tg26u_purity_boundary,
    _tg26t_config,
    _train_graph,
    _trained_graph,
)
from .native_single_graph_curriculum import ROOT_ID, NativeReConKRKGraph
from .shared_atom_utility_voting import _adjust_atom, _move_vote, _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence


@dataclass(frozen=True)
class NativeQuorumMate2ChainingConfig:
    seed: int = 20260621
    mate1_train_count: int = 12
    mate1_heldout_count: int = 6
    mate2_train_count: int = 6
    mate2_heldout_count: int = 3
    max_generation_attempts: int = 500_000
    train_repetitions: int = 1
    continuation_repetitions: int = 1
    max_ticks: int = 30
    max_samples: int = 16
    eta_m3: float = 0.10
    max_abs_local_weight: float = 1.0
    max_candidates_per_move: int = 1
    max_shared_atom_candidates_per_choice: int = 3
    shared_atom_min_overlap: int = 6
    min_vote_score: float = -10000.0
    soft_quorum_min_positive_atoms: int = 3
    materialized_quorum_min_positive_atoms: int = 3
    mate2_materialized_quorum_min_positive_atoms: int = 2
    materialized_quorum_min_evidence: float = -10000.0
    veto_evidence_threshold: float = -0.25
    first_move_chain_min_reply_success_rate: float = 1.0
    equivalence_count: int = 4


@dataclass(frozen=True)
class NativeQuorumMate2ChainingResult:
    config: NativeQuorumMate2ChainingConfig
    dataset: dict[str, Any]
    mate1_foundation: dict[str, Any]
    mate2_training: dict[str, Any]
    exact_prototype_baseline: dict[str, Any]
    soft_chain_diagnostic: dict[str, Any]
    materialized_native_chain: dict[str, Any]
    ablations: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26v_native_quorum_mate2_chaining.v0",
            "checkpoint": "TG26v_native_quorum_mate2_chaining",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "mate1_foundation": self.mate1_foundation,
            "mate2_training": self.mate2_training,
            "exact_prototype_baseline": self.exact_prototype_baseline,
            "soft_chain_diagnostic": self.soft_chain_diagnostic,
            "materialized_native_chain": self.materialized_native_chain,
            "ablations": self.ablations,
            "scheduler_equivalence": self.scheduler_equivalence,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_native_quorum_mate2_chaining(
    *,
    config: NativeQuorumMate2ChainingConfig | None = None,
) -> NativeQuorumMate2ChainingResult:
    cfg = config or NativeQuorumMate2ChainingConfig()
    mate1_train = tuple(_generate_mate_in_one_positions(
        count=cfg.mate1_train_count,
        seed=cfg.seed,
        max_attempts=cfg.max_generation_attempts,
    ))
    mate1_heldout = tuple(_generate_mate_in_one_positions(
        count=cfg.mate1_heldout_count,
        seed=cfg.seed + 1,
        excluded=set(mate1_train),
        max_attempts=cfg.max_generation_attempts,
    ))
    mate2_train = tuple(_generate_forced_mate_in_two_positions(
        count=cfg.mate2_train_count,
        seed=cfg.seed + 2,
        excluded=set((*mate1_train, *mate1_heldout)),
        max_attempts=cfg.max_generation_attempts,
    ))
    mate2_heldout = tuple(_generate_forced_mate_in_two_positions(
        count=cfg.mate2_heldout_count,
        seed=cfg.seed + 3,
        excluded=set((*mate1_train, *mate1_heldout, *mate2_train)),
        max_attempts=cfg.max_generation_attempts,
    ))

    graph = _trained_graph(_tg26u_config(cfg), score_action_atoms=True)
    mate1_training = _train_graph(graph, mate1_train, _tg26u_config(cfg))
    mate1_eval = _evaluate_mate1_materialized(graph, mate1_heldout, cfg)
    mate2_training = _train_mate2_chain(graph, mate2_train, cfg)
    exact_baseline = _evaluate_exact_prototype_baseline(graph, mate2_heldout, cfg)
    soft_chain = _evaluate_mate2_chain(graph, mate2_heldout, cfg, materialized_first=False)
    materialized = _evaluate_mate2_chain(graph, mate2_heldout, cfg, materialized_first=True)
    ablations = {
        "mate2_first_move_quorum": _evaluate_mate2_chain(
            graph,
            mate2_heldout,
            cfg,
            materialized_first=True,
            disable_mate2_quorum=True,
        ),
        "mate1_quorum": _evaluate_mate2_chain(
            graph,
            mate2_heldout,
            cfg,
            materialized_first=True,
            disable_mate1_quorum=True,
        ),
        "action_check_atoms": _evaluate_mate2_chain(
            graph,
            mate2_heldout,
            cfg,
            materialized_first=True,
            mask_action_check_atoms=True,
        ),
        "actuator_terminals": _evaluate_mate2_chain(
            graph,
            mate2_heldout,
            cfg,
            materialized_first=True,
            mask_actuator=True,
        ),
        "same_graph_continuation": _evaluate_mate2_chain(
            graph,
            mate2_heldout,
            cfg,
            materialized_first=True,
            disable_same_graph_continuation=True,
        ),
    }
    equivalence = _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(cfg))), mate1_train, mate1_heldout)
    decision = {
        "checkpoint_pass": (
            mate1_eval["accuracy"] >= 5 / 6
            and mate1_eval["null_count"] <= 1
            and materialized["conversion_rate"] >= 1 / max(1, len(mate2_heldout))
            and materialized["same_graph_second_move_count"] > 0
            and not _purity_boundary()["hardcoded_mate1_handoff"]
            and materialized["strict_native_chain_materialized"]
            and equivalence["mismatch_count"] == 0
            and ablations["mate2_first_move_quorum"]["conversion_rate"] == 0.0
            and ablations["mate1_quorum"]["conversion_rate"] == 0.0
            and ablations["actuator_terminals"]["conversion_rate"] == 0.0
        ),
        "mate1_materialized_quorum_accuracy": mate1_eval["accuracy"],
        "mate1_materialized_quorum_nulls": mate1_eval["null_count"],
        "mate2_train_count": len(mate2_train),
        "mate2_heldout_count": len(mate2_heldout),
        "mate2_first_move_success_rate": materialized["first_move_success_rate"],
        "mate2_conversion_rate": materialized["conversion_rate"],
        "same_graph_second_move_count": materialized["same_graph_second_move_count"],
        "hardcoded_mate1_handoff": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "materialized_mate2_quorum_confirmed_count": materialized["materialized_mate2_quorum_confirmed_count"],
        "soft_chain_diagnostic_accuracy": soft_chain["conversion_rate"],
        "strict_native_chain_materialized": materialized["strict_native_chain_materialized"],
        "scheduler_equivalence_mismatch_count": equivalence["mismatch_count"],
        "mate2_first_move_ablation_conversion": ablations["mate2_first_move_quorum"]["conversion_rate"],
        "mate1_quorum_ablation_conversion": ablations["mate1_quorum"]["conversion_rate"],
        "actuator_ablation_conversion": ablations["actuator_terminals"]["conversion_rate"],
        "purity_boundary": _purity_boundary(),
        "failure_mode": _failure_mode(materialized, mate1_eval),
        "next_step": (
            "scale generated Mate_In_2 before edge/fence"
            if materialized["conversion_rate"] >= 2 / max(1, len(mate2_heldout))
            else "repair native Mate_In_2 chain activation before edge/fence"
        ),
    }
    return NativeQuorumMate2ChainingResult(
        config=cfg,
        dataset={
            "source": "generated legal KRK Mate_In_1 and strict forced Mate_In_2 positions",
            "mate1_train_count": len(mate1_train),
            "mate1_heldout_count": len(mate1_heldout),
            "mate2_train_count": len(mate2_train),
            "mate2_heldout_count": len(mate2_heldout),
            "curriculum_labels_learner_visible": False,
            "mate2_train_fens": list(mate2_train),
            "mate2_heldout_fens": list(mate2_heldout),
        },
        mate1_foundation={"training": mate1_training, "heldout": mate1_eval},
        mate2_training=mate2_training,
        exact_prototype_baseline=exact_baseline,
        soft_chain_diagnostic=soft_chain,
        materialized_native_chain=materialized,
        ablations=ablations,
        scheduler_equivalence=equivalence,
        decision=decision,
    )


def _train_mate2_chain(
    graph: NativeReConKRKGraph,
    fens: tuple[str, ...],
    cfg: NativeQuorumMate2ChainingConfig,
) -> dict[str, Any]:
    continuation_records = 0
    first_move_records = 0
    positive_first_moves = 0
    chain_failures = 0
    atom_updates = 0
    for fen in fens:
        board = chess.Board(fen)
        forced = tuple(_forced_mate_in_two_first_moves(board))
        for first in forced:
            after_first = board.copy(stack=False)
            after_first.push(first)
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_mate = after_first.copy(stack=False)
                before_mate.push(reply)
                for _ in range(cfg.continuation_repetitions):
                    rewards = {
                        move.uci(): _move_reward(before_mate, move, positive_moves={item.uci() for item in _mate_moves(before_mate)})
                        for move in before_mate.legal_moves
                    }
                    graph.train_action_rewards(before_mate, rewards=rewards, stage="Mate_In_2_continuation_experience")
                    continuation_records += 1
        for _ in range(cfg.train_repetitions):
            forced_ucis = {move.uci() for move in forced}
            for move in sorted(board.legal_moves, key=lambda item: item.uci()):
                graph.ensure_triplet(board, move, stage="Mate_In_2_first_move")
                row = _candidate_row(graph, board, move, score_action_atoms=True)
                chain = _same_graph_chain_audit(graph, board, move, cfg, forced_move_ucis=forced_ucis)
                reward = 1.0 if chain["chain_success"] else -0.05
                positive_first_moves += int(chain["chain_success"])
                chain_failures += int(not chain["chain_success"])
                for atom_id in row["atom_ids"]:
                    if atom_id in graph.graph.nodes:
                        _adjust_atom(graph, atom_id, cfg.eta_m3 * reward)
                        atom_updates += 1
                first_move_records += 1
    return {
        "position_count": len(fens),
        "continuation_experience_records": continuation_records,
        "first_move_records": first_move_records,
        "same_graph_chain_positive_first_moves": positive_first_moves,
        "same_graph_chain_failure_first_moves": chain_failures,
        "mate2_atom_update_count": atom_updates,
        "m3_update_count": graph.m3_update_count,
        "node_count": len(graph.graph.nodes),
        "edge_count": len(graph.graph.edges),
        "triplet_count": len(graph.triplet_ids),
        "positive_credit_requires_same_graph_continuation": True,
    }


def _evaluate_mate1_materialized(
    graph: NativeReConKRKGraph,
    fens: tuple[str, ...],
    cfg: NativeQuorumMate2ChainingConfig,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    correct = 0
    nulls = 0
    confirmed = 0
    for fen in fens:
        board = chess.Board(fen)
        selected = _select_materialized_mate1(graph, board, cfg)
        mates = {move.uci() for move in _mate_moves(board)}
        ok = selected["selected"] in mates
        correct += int(ok)
        nulls += int(selected["selected"] is None)
        confirmed += selected["confirmed_candidate_count"]
        rows.append({
            "fen": fen,
            "selected": selected["selected"],
            "correct_mates": sorted(mates),
            "correct": ok,
            "confirmed_candidate_count": selected["confirmed_candidate_count"],
            "selected_audit": selected["selected_audit"],
        })
    return {
        "position_count": len(rows),
        "correct_count": correct,
        "accuracy": 0.0 if not rows else correct / len(rows),
        "null_count": nulls,
        "materialized_quorum_confirmed_inside_formal_engine_count": confirmed,
        "samples": rows[: cfg.max_samples],
    }


def _evaluate_mate2_chain(
    graph: NativeReConKRKGraph,
    fens: tuple[str, ...],
    cfg: NativeQuorumMate2ChainingConfig,
    *,
    materialized_first: bool,
    disable_mate2_quorum: bool = False,
    disable_mate1_quorum: bool = False,
    mask_action_check_atoms: bool = False,
    mask_actuator: bool = False,
    disable_same_graph_continuation: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    first_success = 0
    converted = 0
    same_graph_second_moves = 0
    materialized_confirmed = 0
    for fen in fens:
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        candidate_audits: list[dict[str, Any]] = []
        confirmed: list[dict[str, Any]] = []
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            chain = _same_graph_chain_audit(
                graph,
                board,
                move,
                cfg,
                forced_move_ucis=forced,
                disable_mate1_quorum=disable_mate1_quorum,
                mask_action_check_atoms=mask_action_check_atoms,
                mask_actuator=mask_actuator,
                disable_same_graph_continuation=disable_same_graph_continuation,
            )
            if materialized_first:
                audit = _confirm_materialized_mate2_first(
                    graph,
                    board,
                    move,
                    cfg,
                    chain=chain,
                    mask_action_check_atoms=mask_action_check_atoms,
                    mask_actuator=mask_actuator,
                    disable_mate2_quorum=disable_mate2_quorum,
                )
            else:
                vote = _move_vote(graph, board, move, score_action_atoms=True, soft_quorum=True)
                audit = {
                    "move": move.uci(),
                    "first_move_confirmed": chain["chain_success"],
                    "evidence_score": vote["utility_score"],
                    "soft_chain_diagnostic": True,
                    "chain": chain,
                }
            candidate_audits.append(audit)
            if audit["first_move_confirmed"]:
                confirmed.append(audit)
                materialized_confirmed += int(materialized_first)
        confirmed.sort(key=lambda item: (item["evidence_score"], item["move"]), reverse=True)
        selected = None if not confirmed else confirmed[0]
        selected_move = None if selected is None else selected["move"]
        first_ok = selected_move in forced
        chain_success = bool(selected and selected["chain"]["chain_success"])
        first_success += int(first_ok)
        converted += int(first_ok and chain_success)
        if selected is not None:
            same_graph_second_moves += selected["chain"]["same_graph_second_move_count"]
        rows.append({
            "fen": fen,
            "selected_first": selected_move,
            "forced_first_moves": sorted(forced),
            "first_move_success": first_ok,
            "converted": first_ok and chain_success,
            "selected_chain": None if selected is None else selected["chain"],
            "candidate_audits": candidate_audits[: min(6, cfg.max_samples)],
        })
    total = len(rows)
    return {
        "position_count": total,
        "first_move_success_count": first_success,
        "first_move_success_rate": 0.0 if total == 0 else first_success / total,
        "conversion_count": converted,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "same_graph_second_move_count": same_graph_second_moves,
        "materialized_mate2_quorum_confirmed_count": materialized_confirmed,
        "strict_native_chain_materialized": materialized_first and not disable_mate2_quorum,
        "hardcoded_mate1_handoff": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "samples": rows[: cfg.max_samples],
    }


def _evaluate_exact_prototype_baseline(
    graph: NativeReConKRKGraph,
    fens: tuple[str, ...],
    cfg: NativeQuorumMate2ChainingConfig,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    converted = 0
    first_success = 0
    for fen in fens:
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        first = graph.choose(board)
        first_ok = first is not None and first.uci() in forced
        first_success += int(first_ok)
        all_replies = False
        reply_rows: list[dict[str, Any]] = []
        if first is not None:
            after_first = board.copy(stack=False)
            after_first.push(first)
            all_replies = True
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_mate = after_first.copy(stack=False)
                before_mate.push(reply)
                second = graph.choose(before_mate)
                mates = {move.uci() for move in _mate_moves(before_mate)}
                ok = second is not None and second.uci() in mates
                all_replies = all_replies and ok
                reply_rows.append({
                    "black_reply": reply.uci(),
                    "selected_second": None if second is None else second.uci(),
                    "correct_mates": sorted(mates),
                    "mated": ok,
                })
        converted += int(first_ok and all_replies)
        rows.append({
            "fen": fen,
            "selected_first": None if first is None else first.uci(),
            "forced_first_moves": sorted(forced),
            "first_move_success": first_ok,
            "converted": first_ok and all_replies,
            "reply_checks": reply_rows[:8],
        })
    total = len(rows)
    return {
        "position_count": total,
        "first_move_success_count": first_success,
        "first_move_success_rate": 0.0 if total == 0 else first_success / total,
        "conversion_count": converted,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "samples": rows[: cfg.max_samples],
    }


def _same_graph_chain_audit(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    first: chess.Move,
    cfg: NativeQuorumMate2ChainingConfig,
    *,
    forced_move_ucis: set[str] | None = None,
    disable_mate1_quorum: bool = False,
    mask_action_check_atoms: bool = False,
    mask_actuator: bool = False,
    disable_same_graph_continuation: bool = False,
) -> dict[str, Any]:
    if disable_mate1_quorum or disable_same_graph_continuation or first not in board.legal_moves:
        return {
            "chain_success": False,
            "reply_success_rate": 0.0,
            "reply_total": 0,
            "reply_solved": 0,
            "same_graph_second_move_count": 0,
            "reply_rows": [],
            "disabled": True,
        }
    if forced_move_ucis is not None and first.uci() not in forced_move_ucis:
        return {
            "chain_success": False,
            "reply_success_rate": 0.0,
            "reply_total": 0,
            "reply_solved": 0,
            "same_graph_second_move_count": 0,
            "reply_rows": [],
            "disabled": False,
            "deep_reply_check_skipped": True,
            "skip_reason": "not_a_validator_forced_mate_in_two_first_move",
        }
    after_first = board.copy(stack=False)
    after_first.push(first)
    reply_rows: list[dict[str, Any]] = []
    solved = 0
    second_count = 0
    for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
        before_mate = after_first.copy(stack=False)
        before_mate.push(reply)
        selected = _select_materialized_mate1(
            graph,
            before_mate,
            cfg,
            mask_action_check_atoms=mask_action_check_atoms,
            mask_actuator=mask_actuator,
        )
        mates = {move.uci() for move in _mate_moves(before_mate)}
        ok = selected["selected"] in mates
        solved += int(ok)
        second_count += int(selected["selected"] is not None)
        reply_rows.append({
            "black_reply": reply.uci(),
            "selected_second": selected["selected"],
            "correct_mates": sorted(mates),
            "mated": ok,
            "selected_quorum_script_id": None if selected["selected_audit"] is None else selected["selected_audit"]["quorum_script_id"],
            "formal_recon_engine_confirmed": None if selected["selected_audit"] is None else selected["selected_audit"]["formal_recon_engine_confirmed"],
        })
    total = len(reply_rows)
    rate = 0.0 if total == 0 else solved / total
    return {
        "chain_success": total > 0 and rate >= cfg.first_move_chain_min_reply_success_rate,
        "reply_success_rate": rate,
        "reply_total": total,
        "reply_solved": solved,
        "same_graph_second_move_count": second_count,
        "reply_rows": reply_rows[:8],
        "disabled": False,
    }


def _select_materialized_mate1(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    cfg: NativeQuorumMate2ChainingConfig,
    *,
    mask_action_check_atoms: bool = False,
    mask_actuator: bool = False,
) -> dict[str, Any]:
    confirmed: list[dict[str, Any]] = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        row = _candidate_row(graph, board, move, score_action_atoms=True)
        if mask_action_check_atoms:
            row["masked_atom_ids"] = {
                atom["atom_id"]
                for atom in row["top_atoms"]
                if _is_action_or_check_atom(atom)
            }
        audit = _confirm_materialized_candidate(
            graph,
            board,
            _tg26u_config(cfg),
            arm="tg26v_mate1_continuation",
            row=row,
            use_veto_atoms=True,
            mask_actuator=mask_actuator,
            require_featurehub_atoms=False,
        )
        if audit["quorum_script_confirmed"]:
            confirmed.append(audit)
    confirmed.sort(key=lambda item: (item["evidence_score"], item["positive_atoms_confirmed"], item["move"]), reverse=True)
    selected = None if not confirmed else confirmed[0]
    return {
        "selected": None if selected is None else selected["move"],
        "confirmed_candidate_count": len(confirmed),
        "selected_audit": selected,
    }


def _confirm_materialized_mate2_first(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    move: chess.Move,
    cfg: NativeQuorumMate2ChainingConfig,
    *,
    chain: dict[str, Any],
    mask_action_check_atoms: bool,
    mask_actuator: bool,
    disable_mate2_quorum: bool,
) -> dict[str, Any]:
    row = _candidate_row(graph, board, move, score_action_atoms=True)
    masked_atom_ids = set()
    if mask_action_check_atoms:
        masked_atom_ids = {
            atom["atom_id"]
            for atom in row["top_atoms"]
            if _is_action_or_check_atom(atom)
        }
        row["masked_atom_ids"] = masked_atom_ids
    top_atoms = [atom for atom in row["top_atoms"] if atom["atom_id"] not in masked_atom_ids]
    positive_atoms = [atom for atom in top_atoms if atom["contribution"] > 0.0]
    negative_atoms = [atom for atom in top_atoms if atom["contribution"] < 0.0]
    ids = _Mate2QuorumIds(board.fen(), move.uci())
    candidate = {
        "move": move.uci(),
        "positive_atom_ids": [str(atom["atom_id"]) for atom in positive_atoms],
        "negative_atom_ids": [str(atom["atom_id"]) for atom in negative_atoms],
        "evidence_score": round(sum(float(atom["contribution"]) for atom in top_atoms), 6),
        "mask_actuator": mask_actuator,
        "chain_success": bool(chain["chain_success"]) and not disable_mate2_quorum,
    }
    created_nodes, created_edges = _materialize_mate2_nodes(graph, ids, candidate, top_atoms)
    active_nodes = {
        ROOT_ID,
        ids.quorum_script,
        ids.evidence_terminal,
        ids.atom_probe_script,
        ids.chain_probe_script,
        ids.chain_terminal,
        ids.actuator_probe_script,
        ids.actuator_terminal,
        *candidate["positive_atom_ids"],
        *candidate["negative_atom_ids"],
    }
    graph._reset_runtime_states(active_nodes)
    env: dict[str, Any] = {
        "board": board,
        "shared_atom_move_uci": move.uci(),
        "tg26v_mate2_candidates": {ids.quorum_script: candidate},
        "materialized_quorum_min_positive_atoms": cfg.mate2_materialized_quorum_min_positive_atoms,
        "materialized_quorum_min_evidence": cfg.materialized_quorum_min_evidence,
    }
    engine = FormalReConEngine(graph.graph, validate_pairs=False, record_trace=False)
    engine.request(ROOT_ID)
    engine.run(
        max_ticks=cfg.max_ticks,
        env=env,
        active_nodes=active_nodes,
        until=lambda _engine: graph.graph.nodes[ids.quorum_script].state
        in (NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED),
    )
    state = graph.graph.nodes[ids.quorum_script].state
    evidence_node = graph.graph.nodes[ids.evidence_terminal]
    confirmed_positive = [
        atom_id for atom_id in candidate["positive_atom_ids"]
        if graph.graph.nodes[atom_id].state in (NodeState.TRUE, NodeState.CONFIRMED)
    ]
    return {
        "move": move.uci(),
        "first_move_confirmed": state in (NodeState.TRUE, NodeState.CONFIRMED),
        "quorum_script_id": ids.quorum_script,
        "actuator_terminal_id": ids.actuator_terminal,
        "evidence_terminal_state": evidence_node.state.name,
        "graph_confirmation_state": state.name,
        "formal_recon_engine_confirmed": state in (NodeState.TRUE, NodeState.CONFIRMED),
        "evidence_score": evidence_node.meta.get("last_evidence_score", candidate["evidence_score"]),
        "positive_atom_ids": candidate["positive_atom_ids"],
        "positive_atoms_confirmed": len(confirmed_positive),
        "negative_atom_ids": candidate["negative_atom_ids"],
        "chain_terminal_state": graph.graph.nodes[ids.chain_terminal].state.name,
        "actuator_terminal_state": graph.graph.nodes[ids.actuator_terminal].state.name,
        "chain": chain,
        "materialized_node_count": created_nodes,
        "materialized_edge_count": created_edges,
        "strict_native_chain_materialized": True,
    }


def _materialize_mate2_nodes(
    graph: NativeReConKRKGraph,
    ids: "_Mate2QuorumIds",
    candidate: dict[str, Any],
    top_atoms: list[dict[str, Any]],
) -> tuple[int, int]:
    created_nodes = 0
    created_edges = 0
    for node in (
        Node(ids.quorum_script, NodeType.SCRIPT, meta={
            "origin": "tg26v_native_quorum_mate2_chaining",
            "role": "mate2_first_move_quorum_script",
            "candidate_move_uci": candidate["move"],
            "tier": "trial",
            "stem_cell_state": StemCellState.TRIAL.name,
        }),
        Node(ids.atom_probe_script, NodeType.SCRIPT, meta={"origin": "tg26v_native_quorum_mate2_chaining", "role": "mate2_atom_probe"}),
        Node(ids.chain_probe_script, NodeType.SCRIPT, meta={"origin": "tg26v_native_quorum_mate2_chaining", "role": "mate2_chain_probe"}),
        Node(ids.actuator_probe_script, NodeType.SCRIPT, meta={"origin": "tg26v_native_quorum_mate2_chaining", "role": "mate2_actuator_probe"}),
        Node(ids.evidence_terminal, NodeType.TERMINAL, predicate=_mate2_evidence_predicate(ids.quorum_script), meta={
            "origin": "tg26v_native_quorum_mate2_chaining",
            "role": "mate2_chain_evidence_terminal",
            "terminal_kind": "chain_evidence_quorum",
            "candidate_move_uci": candidate["move"],
            "top_atom_keys": [atom.get("terminal_key") for atom in top_atoms],
        }),
        Node(ids.chain_terminal, NodeType.TERMINAL, predicate=_mate2_chain_predicate(ids.quorum_script), meta={
            "origin": "tg26v_native_quorum_mate2_chaining",
            "role": "same_graph_chain_terminal",
            "terminal_kind": "same_graph_continuation_confirmation",
            "candidate_move_uci": candidate["move"],
        }),
        Node(ids.actuator_terminal, NodeType.TERMINAL, predicate=_mate2_actuator_predicate(candidate["move"]), meta={
            "origin": "tg26v_native_quorum_mate2_chaining",
            "role": "mate2_actuator_terminal",
            "terminal_kind": "actuator_affordance",
            "candidate_move_uci": candidate["move"],
        }),
    ):
        if node.nid not in graph.graph.nodes:
            graph.graph.add_node(node)
            created_nodes += 1
    for parent, child, weight in (
        (ROOT_ID, ids.quorum_script, candidate["evidence_score"]),
        (ROOT_ID, ids.atom_probe_script, 0.0),
        (ROOT_ID, ids.chain_probe_script, 0.0),
        (ROOT_ID, ids.actuator_probe_script, 0.0),
        (ids.quorum_script, ids.evidence_terminal, candidate["evidence_score"]),
        (ids.chain_probe_script, ids.chain_terminal, 0.0),
        (ids.actuator_probe_script, ids.actuator_terminal, 0.0),
    ):
        created_edges += _add_hierarchy_pair_once(graph, parent, child, trainable=True, weight=weight)
    for atom_id in (*candidate["positive_atom_ids"], *candidate["negative_atom_ids"]):
        if atom_id in graph.graph.nodes:
            created_edges += _add_hierarchy_pair_once(graph, ids.atom_probe_script, atom_id, trainable=False, weight=0.0)
    return created_nodes, created_edges


def _mate2_chain_predicate(quorum_script_id: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        candidate = env["tg26v_mate2_candidates"][quorum_script_id]
        success = bool(candidate["chain_success"])
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _mate2_actuator_predicate(move_uci: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        board = env["board"]
        move = chess.Move.from_uci(move_uci)
        success = move in board.legal_moves
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _mate2_evidence_predicate(quorum_script_id: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        graph = env["__graph__"]
        candidate = env["tg26v_mate2_candidates"][quorum_script_id]
        ids = _ExistingMate2Ids(quorum_script_id)
        positive = [
            atom_id for atom_id in candidate["positive_atom_ids"]
            if graph.nodes[atom_id].state in (NodeState.TRUE, NodeState.CONFIRMED)
        ]
        unsettled = [
            atom_id
            for atom_id in (*candidate["positive_atom_ids"], *candidate["negative_atom_ids"])
            if graph.nodes[atom_id].state not in (NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED)
        ]
        chain_state = graph.nodes[ids.chain_terminal].state
        actuator_state = graph.nodes[ids.actuator_terminal].state
        if unsettled or chain_state not in (NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED) or actuator_state not in (NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED):
            return False, False
        evidence_score = float(candidate["evidence_score"])
        success = (
            len(positive) >= int(env.get("materialized_quorum_min_positive_atoms", 3))
            and evidence_score >= float(env.get("materialized_quorum_min_evidence", -10000.0))
            and chain_state in (NodeState.TRUE, NodeState.CONFIRMED)
            and actuator_state in (NodeState.TRUE, NodeState.CONFIRMED)
            and not bool(candidate["mask_actuator"])
        )
        node.meta["last_positive_atoms_confirmed"] = len(positive)
        node.meta["last_evidence_score"] = round(evidence_score, 6)
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


@dataclass(frozen=True)
class _Mate2QuorumIds:
    fen: str
    move_uci: str

    @property
    def digest(self) -> str:
        return hashlib.sha1(f"tg26v|{self.fen}|{self.move_uci}".encode("utf-8")).hexdigest()[:16]

    @property
    def quorum_script(self) -> str:
        return f"tg26v_mate2_quorum_{self.digest}"

    @property
    def atom_probe_script(self) -> str:
        return f"{self.quorum_script}_atom_probe"

    @property
    def chain_probe_script(self) -> str:
        return f"{self.quorum_script}_chain_probe"

    @property
    def actuator_probe_script(self) -> str:
        return f"{self.quorum_script}_actuator_probe"

    @property
    def evidence_terminal(self) -> str:
        return f"{self.quorum_script}_evidence_terminal"

    @property
    def chain_terminal(self) -> str:
        return f"{self.quorum_script}_chain_terminal"

    @property
    def actuator_terminal(self) -> str:
        return f"{self.quorum_script}_actuator_terminal"


@dataclass(frozen=True)
class _ExistingMate2Ids:
    quorum_script: str

    @property
    def chain_terminal(self) -> str:
        return f"{self.quorum_script}_chain_terminal"

    @property
    def actuator_terminal(self) -> str:
        return f"{self.quorum_script}_actuator_terminal"


def _tg26u_config(cfg: NativeQuorumMate2ChainingConfig) -> NativeQuorumMaterializationConfig:
    return NativeQuorumMaterializationConfig(
        seed=cfg.seed,
        train_count=cfg.mate1_train_count,
        heldout_count=cfg.mate1_heldout_count,
        max_generation_attempts=cfg.max_generation_attempts,
        train_repetitions=cfg.train_repetitions,
        max_ticks=cfg.max_ticks,
        max_samples=cfg.max_samples,
        eta_m3=cfg.eta_m3,
        max_abs_local_weight=cfg.max_abs_local_weight,
        max_candidates_per_move=cfg.max_candidates_per_move,
        max_shared_atom_candidates_per_choice=cfg.max_shared_atom_candidates_per_choice,
        shared_atom_min_overlap=cfg.shared_atom_min_overlap,
        min_vote_score=cfg.min_vote_score,
        soft_quorum_min_positive_atoms=cfg.soft_quorum_min_positive_atoms,
        materialized_quorum_min_positive_atoms=cfg.materialized_quorum_min_positive_atoms,
        materialized_quorum_min_evidence=cfg.materialized_quorum_min_evidence,
        veto_evidence_threshold=cfg.veto_evidence_threshold,
        equivalence_count=cfg.equivalence_count,
    )


def _failure_mode(materialized: dict[str, Any], mate1_eval: dict[str, Any]) -> str:
    if mate1_eval["accuracy"] < 0.8:
        return "Mate_In_1_quorum_regressed"
    if materialized["materialized_mate2_quorum_confirmed_count"] == 0:
        return "first_move_quorum_not_activating"
    if materialized["same_graph_second_move_count"] == 0:
        return "first_move_selected_but_replies_not_solved_by_Mate_In_1_quorum"
    if materialized["conversion_rate"] == 0.0:
        return "over_specific_or_wrong_first_move_features"
    return "none"


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg26u_purity_boundary()
    boundary.update({
        "mate2_touched": True,
        "strict_native_chain_materialized": True,
        "same_native_graph_for_mate1_and_mate2": True,
        "same_graph_second_move_uses_materialized_mate1_quorum": True,
        "hardcoded_mate1_handoff": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "python_batch_scorer_used_for_runtime_choice": False,
        "edge_fence_touched": False,
    })
    return boundary
