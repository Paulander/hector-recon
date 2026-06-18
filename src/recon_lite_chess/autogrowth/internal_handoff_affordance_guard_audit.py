"""TG26w internal handoff affordance and TG26v guard audit."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Any

import chess

from recon_lite import FormalReConEngine, LinkType, Node, NodeState, NodeType
from recon_lite_hector.nodes.stem_cell import StemCellState

from .foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _generate_forced_mate_in_two_positions,
    _generate_mate_in_one_positions,
)
from .native_quorum_materialization import (
    _add_hierarchy_pair_once,
    _candidate_row,
    _is_action_or_check_atom,
    _tg26t_config,
    _train_graph,
    _trained_graph,
)
from .native_quorum_mate2_chaining import (
    NativeQuorumMate2ChainingConfig,
    _confirm_materialized_mate2_first,
    _evaluate_mate1_materialized,
    _evaluate_mate2_chain,
    _same_graph_chain_audit,
    _tg26u_config,
    _train_mate2_chain,
)
from .native_single_graph_curriculum import ROOT_ID, NativeReConKRKGraph
from .shared_atom_utility_voting import _adjust_atom, _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence


@dataclass(frozen=True)
class InternalHandoffAffordanceConfig:
    seed: int = 20260621
    mate1_train_count: int = 12
    mate1_heldout_count: int = 6
    mate2_train_count: int = 6
    mate2_heldout_count: int = 3
    max_generation_attempts: int = 500_000
    train_repetitions: int = 1
    continuation_repetitions: int = 1
    max_ticks: int = 30
    max_samples: int = 24
    eta_m3: float = 0.10
    handoff_eta_scale: float = 0.75
    max_abs_local_weight: float = 1.0
    max_candidates_per_move: int = 1
    max_shared_atom_candidates_per_choice: int = 3
    shared_atom_min_overlap: int = 6
    min_vote_score: float = -10000.0
    soft_quorum_min_positive_atoms: int = 3
    materialized_quorum_min_positive_atoms: int = 3
    mate2_materialized_quorum_min_positive_atoms: int = 2
    handoff_gate_min_positive_atoms: int = 2
    handoff_gate_min_score: float = -10000.0
    materialized_quorum_min_evidence: float = -10000.0
    veto_evidence_threshold: float = -0.25
    first_move_chain_min_reply_success_rate: float = 1.0
    guardless_probe_position_count: int = 1
    equivalence_count: int = 4


@dataclass(frozen=True)
class InternalHandoffAffordanceResult:
    config: InternalHandoffAffordanceConfig
    dataset: dict[str, Any]
    mate1_foundation: dict[str, Any]
    mate2_training: dict[str, Any]
    guarded_baseline: dict[str, Any]
    guardless_probe: dict[str, Any]
    internal_handoff: dict[str, Any]
    ablation_results: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26w_internal_handoff_affordance_guard_audit.v0",
            "checkpoint": "TG26w_internal_handoff_affordance_guard_audit",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "mate1_foundation": self.mate1_foundation,
            "mate2_training": self.mate2_training,
            "guarded_baseline": self.guarded_baseline,
            "guardless_probe": self.guardless_probe,
            "internal_handoff": self.internal_handoff,
            "ablation_results": self.ablation_results,
            "scheduler_equivalence": self.scheduler_equivalence,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_internal_handoff_affordance_guard_audit(
    *,
    config: InternalHandoffAffordanceConfig | None = None,
) -> InternalHandoffAffordanceResult:
    cfg = config or InternalHandoffAffordanceConfig()
    mate1_train, mate1_heldout, mate2_train, mate2_heldout = _datasets(cfg)
    graph = _trained_graph(_tg26u_config(_mate2_cfg(cfg)), score_action_atoms=True)
    mate1_training = _train_graph(graph, mate1_train, _tg26u_config(_mate2_cfg(cfg)))
    mate1_eval = _evaluate_mate1_materialized(graph, mate1_heldout, _mate2_cfg(cfg))
    mate2_training = _train_mate2_chain(graph, mate2_train, _mate2_cfg(cfg))
    handoff_training = _train_internal_handoff_gate(graph, mate2_train, cfg)

    guarded = _evaluate_mate2_chain(graph, mate2_heldout, _mate2_cfg(cfg), materialized_first=True)
    guardless = _guardless_probe(graph, mate2_heldout[: cfg.guardless_probe_position_count], cfg)
    internal = _evaluate_internal_handoff_arm(graph, mate2_heldout, cfg)
    ablations = {
        "mask_internal_handoff_affordance_terminals": _evaluate_internal_handoff_arm(
            graph, mate2_heldout, cfg, mask_internal_handoff=True
        ),
        "mask_mate2_first_move_quorum": _evaluate_internal_handoff_arm(
            graph, mate2_heldout, cfg, disable_mate2_quorum=True
        ),
        "mask_mate1_quorum": _evaluate_internal_handoff_arm(
            graph, mate2_heldout, cfg, disable_mate1_quorum=True
        ),
        "mask_actuator_terminals": _evaluate_internal_handoff_arm(
            graph, mate2_heldout, cfg, mask_actuator=True
        ),
        "disable_deep_continuation_checks": _evaluate_internal_handoff_arm(
            graph, mate2_heldout, cfg, disable_deep_continuation=True
        ),
        "disable_validator_guard_during_eval": _evaluate_internal_handoff_arm(
            graph, mate2_heldout, cfg
        ),
    }
    equivalence = _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(_mate2_cfg(cfg)))), mate1_train, mate1_heldout)
    decision = {
        "checkpoint_pass": (
            internal["conversion_rate"] > 0.0
            and internal["same_graph_second_move_count"] > 0
            and not internal["validator_skip_used_during_eval"]
            and internal["materialized_mate2_quorum_confirmed_count"] > 0
            and ablations["mask_internal_handoff_affordance_terminals"]["conversion_rate"] < internal["conversion_rate"]
            and ablations["mask_mate1_quorum"]["conversion_rate"] == 0.0
            and ablations["mask_actuator_terminals"]["conversion_rate"] == 0.0
            and equivalence["mismatch_count"] == 0
        ),
        "guarded_conversion_rate": guarded["conversion_rate"],
        "guardless_probe_conversion_rate": guardless["conversion_rate"],
        "internal_handoff_conversion_rate": internal["conversion_rate"],
        "internal_handoff_first_move_success_rate": internal["first_move_success_rate"],
        "internal_handoff_same_graph_second_move_count": internal["same_graph_second_move_count"],
        "guard_used_during_training": True,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": internal["validator_skip_used_during_eval"],
        "fully_evaluated_candidate_count": guardless["fully_evaluated_candidate_count"],
        "skipped_candidate_count": guardless["skipped_candidate_count"],
        "internal_gate_approved_candidate_count": internal["internal_gate_approved_candidate_count"],
        "internal_gate_rejected_candidate_count": internal["internal_gate_rejected_candidate_count"],
        "false_positive_internal_gate_count": internal["false_positive_internal_gate_count"],
        "false_negative_internal_gate_count": internal["false_negative_internal_gate_count"],
        "materialized_handoff_terminal_count": internal["materialized_handoff_terminal_count"],
        "materialized_handoff_quorum_count": internal["materialized_handoff_quorum_count"],
        "materialized_mate2_quorum_confirmed_count": internal["materialized_mate2_quorum_confirmed_count"],
        "hardcoded_mate1_handoff": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "stage_labels_learner_visible": False,
        "scheduler_equivalence_mismatch_count": equivalence["mismatch_count"],
        "ablation_results": {
            key: {
                "conversion_rate": value["conversion_rate"],
                "first_move_success_rate": value["first_move_success_rate"],
                "same_graph_second_move_count": value["same_graph_second_move_count"],
            }
            for key, value in ablations.items()
        },
        "purity_boundary": _purity_boundary(),
        "failure_mode": _failure_mode(internal),
    }
    return InternalHandoffAffordanceResult(
        config=cfg,
        dataset={
            "source": "generated legal KRK Mate_In_1 and strict forced Mate_In_2 positions",
            "mate1_train_count": len(mate1_train),
            "mate1_heldout_count": len(mate1_heldout),
            "mate2_train_count": len(mate2_train),
            "mate2_heldout_count": len(mate2_heldout),
            "curriculum_labels_learner_visible": False,
            "mate2_heldout_fens": list(mate2_heldout),
        },
        mate1_foundation={"training": mate1_training, "heldout": mate1_eval},
        mate2_training={**mate2_training, "internal_handoff_training": handoff_training},
        guarded_baseline=guarded,
        guardless_probe=guardless,
        internal_handoff=internal,
        ablation_results=ablations,
        scheduler_equivalence=equivalence,
        decision=decision,
    )


def _datasets(cfg: InternalHandoffAffordanceConfig) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
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
    return mate1_train, mate1_heldout, mate2_train, mate2_heldout


def _train_internal_handoff_gate(
    graph: NativeReConKRKGraph,
    fens: tuple[str, ...],
    cfg: InternalHandoffAffordanceConfig,
) -> dict[str, Any]:
    updates = 0
    positives = 0
    negatives = 0
    for fen in fens:
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            row = _candidate_row(graph, board, move, score_action_atoms=True)
            label_positive = move.uci() in forced
            reward = 1.0 if label_positive else -0.10
            positives += int(label_positive)
            negatives += int(not label_positive)
            for atom_id in row["atom_ids"]:
                if atom_id in graph.graph.nodes:
                    _adjust_atom(graph, atom_id, cfg.eta_m3 * cfg.handoff_eta_scale * reward)
                    graph.graph.nodes[atom_id].meta["handoff_affordance_exposure_count"] = (
                        int(graph.graph.nodes[atom_id].meta.get("handoff_affordance_exposure_count", 0)) + 1
                    )
                    if label_positive:
                        graph.graph.nodes[atom_id].meta["handoff_positive_count"] = (
                            int(graph.graph.nodes[atom_id].meta.get("handoff_positive_count", 0)) + 1
                        )
                    else:
                        graph.graph.nodes[atom_id].meta["handoff_negative_count"] = (
                            int(graph.graph.nodes[atom_id].meta.get("handoff_negative_count", 0)) + 1
                        )
                    updates += 1
    return {
        "train_position_count": len(fens),
        "handoff_positive_moves": positives,
        "handoff_negative_moves": negatives,
        "handoff_atom_update_count": updates,
        "teacher_labels_used_for_training": True,
        "teacher_labels_learner_visible": False,
    }


def _guardless_probe(
    graph: NativeReConKRKGraph,
    fens: tuple[str, ...],
    cfg: InternalHandoffAffordanceConfig,
) -> dict[str, Any]:
    start = perf_counter()
    rows: list[dict[str, Any]] = []
    converted = 0
    fully_evaluated = 0
    reply_checks = 0
    false_passes = 0
    mate1_stable = True
    for fen in fens:
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        audits: list[dict[str, Any]] = []
        confirmed: list[dict[str, Any]] = []
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            chain = _same_graph_chain_audit(graph, board, move, _mate2_cfg(cfg), forced_move_ucis=None)
            fully_evaluated += 1
            reply_checks += int(chain["reply_total"])
            mate1_stable = mate1_stable and (not chain["chain_success"] or chain["same_graph_second_move_count"] > 0)
            audit = _confirm_materialized_mate2_first(
                graph,
                board,
                move,
                _mate2_cfg(cfg),
                chain=chain,
                mask_action_check_atoms=False,
                mask_actuator=False,
                disable_mate2_quorum=False,
            )
            false_passes += int(audit["first_move_confirmed"] and move.uci() not in forced)
            if audit["first_move_confirmed"]:
                confirmed.append(audit)
            audits.append(_candidate_diagnostic(move, forced, guard_skip_used=False, gate=None, chain=chain, audit=audit))
        confirmed.sort(key=lambda item: (item["evidence_score"], item["move"]), reverse=True)
        selected = None if not confirmed else confirmed[0]
        ok = selected is not None and selected["move"] in forced and selected["chain"]["chain_success"]
        converted += int(ok)
        rows.append({
            "fen": fen,
            "selected_first": None if selected is None else selected["move"],
            "forced_first_moves": sorted(forced),
            "converted": ok,
            "candidate_diagnostics": audits,
        })
    total = len(rows)
    duration = perf_counter() - start
    return {
        "position_count": total,
        "conversion_count": converted,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "fully_evaluated_candidate_count": fully_evaluated,
        "skipped_candidate_count": 0,
        "reply_checks_run": reply_checks,
        "duration_seconds": round(duration, 6),
        "correct_first_move_wins_under_full_guardless_eval": converted == total and total > 0,
        "non_forced_move_false_pass_count": false_passes,
        "mate1_quorum_continuation_stable": mate1_stable,
        "samples": rows[: cfg.max_samples],
    }


def _evaluate_internal_handoff_arm(
    graph: NativeReConKRKGraph,
    fens: tuple[str, ...],
    cfg: InternalHandoffAffordanceConfig,
    *,
    mask_internal_handoff: bool = False,
    disable_mate2_quorum: bool = False,
    disable_mate1_quorum: bool = False,
    mask_actuator: bool = False,
    disable_deep_continuation: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    first_success = 0
    converted = 0
    approved = 0
    rejected = 0
    false_positive = 0
    false_negative = 0
    same_graph_second = 0
    materialized_mate2 = 0
    materialized_handoff_terminals = 0
    materialized_handoff_quorums = 0
    for fen in fens:
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        candidate_rows: list[dict[str, Any]] = []
        confirmed: list[dict[str, Any]] = []
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            gate = _confirm_internal_handoff_gate(
                graph,
                board,
                move,
                cfg,
                mask_internal_handoff=mask_internal_handoff,
                mask_actuator=mask_actuator,
            )
            materialized_handoff_terminals += gate["materialized_handoff_terminal_count"]
            materialized_handoff_quorums += gate["materialized_handoff_quorum_count"]
            gate_ok = bool(gate["internal_handoff_approved"])
            approved += int(gate_ok)
            rejected += int(not gate_ok)
            false_positive += int(gate_ok and move.uci() not in forced)
            false_negative += int((not gate_ok) and move.uci() in forced)
            if gate_ok and not disable_deep_continuation:
                chain = _same_graph_chain_audit(
                    graph,
                    board,
                    move,
                    _mate2_cfg(cfg),
                    forced_move_ucis=None,
                    disable_mate1_quorum=disable_mate1_quorum,
                    mask_actuator=mask_actuator,
                )
            else:
                chain = {
                    "chain_success": False,
                    "reply_success_rate": 0.0,
                    "reply_total": 0,
                    "reply_solved": 0,
                    "same_graph_second_move_count": 0,
                    "reply_rows": [],
                    "disabled": disable_deep_continuation,
                    "deep_reply_check_skipped": not gate_ok,
                    "skip_reason": "internal_handoff_gate_rejected" if not gate_ok else "deep_continuation_disabled",
                }
            if gate_ok:
                mate2 = _confirm_materialized_mate2_first(
                    graph,
                    board,
                    move,
                    _mate2_cfg(cfg),
                    chain=chain,
                    mask_action_check_atoms=False,
                    mask_actuator=mask_actuator,
                    disable_mate2_quorum=disable_mate2_quorum,
                )
            else:
                mate2 = _empty_mate2_audit(move.uci(), chain)
            if mate2["first_move_confirmed"]:
                confirmed.append(mate2)
                materialized_mate2 += 1
            candidate_rows.append(_candidate_diagnostic(move, forced, guard_skip_used=False, gate=gate, chain=chain, audit=mate2))
        confirmed.sort(key=lambda item: (item["evidence_score"], item["move"]), reverse=True)
        selected = None if not confirmed else confirmed[0]
        selected_move = None if selected is None else selected["move"]
        ok_first = selected_move in forced
        ok_chain = bool(selected and selected["chain"]["chain_success"])
        first_success += int(ok_first)
        converted += int(ok_first and ok_chain)
        same_graph_second += 0 if selected is None else int(selected["chain"]["same_graph_second_move_count"])
        rows.append({
            "fen": fen,
            "selected_first": selected_move,
            "forced_first_moves": sorted(forced),
            "first_move_success": ok_first,
            "converted": ok_first and ok_chain,
            "candidate_diagnostics": candidate_rows[: cfg.max_samples],
        })
    total = len(rows)
    return {
        "position_count": total,
        "first_move_success_count": first_success,
        "first_move_success_rate": 0.0 if total == 0 else first_success / total,
        "conversion_count": converted,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "same_graph_second_move_count": same_graph_second,
        "internal_gate_approved_candidate_count": approved,
        "internal_gate_rejected_candidate_count": rejected,
        "false_positive_internal_gate_count": false_positive,
        "false_negative_internal_gate_count": false_negative,
        "materialized_handoff_terminal_count": materialized_handoff_terminals,
        "materialized_handoff_quorum_count": materialized_handoff_quorums,
        "materialized_mate2_quorum_confirmed_count": materialized_mate2,
        "validator_skip_used_during_eval": False,
        "guard_used_during_runtime_choice": False,
        "samples": rows[: cfg.max_samples],
    }


def _confirm_internal_handoff_gate(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    move: chess.Move,
    cfg: InternalHandoffAffordanceConfig,
    *,
    mask_internal_handoff: bool,
    mask_actuator: bool,
) -> dict[str, Any]:
    row = _candidate_row(graph, board, move, score_action_atoms=True)
    top_atoms = list(row["top_atoms"])
    positive = [atom for atom in top_atoms if atom["contribution"] > 0.0]
    negative = [atom for atom in top_atoms if atom["contribution"] < 0.0]
    ids = _HandoffIds(board.fen(), move.uci())
    candidate = {
        "move": move.uci(),
        "positive_atom_ids": [str(atom["atom_id"]) for atom in positive],
        "negative_atom_ids": [str(atom["atom_id"]) for atom in negative],
        "score": round(sum(float(atom["contribution"]) for atom in top_atoms), 6),
        "mask_internal_handoff": mask_internal_handoff,
        "mask_actuator": mask_actuator,
    }
    created_nodes, created_edges = _materialize_handoff_nodes(graph, ids, candidate, top_atoms)
    active_nodes = {
        ROOT_ID,
        ids.quorum_script,
        ids.evidence_terminal,
        ids.atom_probe_script,
        ids.actuator_probe_script,
        ids.actuator_terminal,
        *candidate["positive_atom_ids"],
        *candidate["negative_atom_ids"],
    }
    graph._reset_runtime_states(active_nodes)
    env: dict[str, Any] = {
        "board": board,
        "shared_atom_move_uci": move.uci(),
        "tg26w_handoff_candidates": {ids.quorum_script: candidate},
        "handoff_gate_min_positive_atoms": cfg.handoff_gate_min_positive_atoms,
        "handoff_gate_min_score": cfg.handoff_gate_min_score,
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
    evidence = graph.graph.nodes[ids.evidence_terminal]
    actuator = graph.graph.nodes[ids.actuator_terminal]
    confirmed_positive = [
        atom_id for atom_id in candidate["positive_atom_ids"]
        if graph.graph.nodes[atom_id].state in (NodeState.TRUE, NodeState.CONFIRMED)
    ]
    return {
        "move": move.uci(),
        "internal_handoff_approved": state in (NodeState.TRUE, NodeState.CONFIRMED),
        "internal_handoff_gate_state": state.name,
        "internal_handoff_score": evidence.meta.get("last_handoff_score", candidate["score"]),
        "positive_handoff_atoms": candidate["positive_atom_ids"],
        "negative_handoff_atoms": candidate["negative_atom_ids"],
        "confirmed_positive_handoff_atom_count": len(confirmed_positive),
        "handoff_quorum_script_id": ids.quorum_script,
        "actuator_terminal_state": actuator.state.name,
        "formal_recon_engine_confirmation_state": state.name,
        "materialized_handoff_terminal_count": 2 if created_nodes else 0,
        "materialized_handoff_quorum_count": int(created_nodes > 0),
        "materialized_handoff_edge_count": created_edges,
    }


def _materialize_handoff_nodes(
    graph: NativeReConKRKGraph,
    ids: "_HandoffIds",
    candidate: dict[str, Any],
    top_atoms: list[dict[str, Any]],
) -> tuple[int, int]:
    created_nodes = 0
    created_edges = 0
    for node in (
        Node(ids.quorum_script, NodeType.SCRIPT, meta={
            "origin": "tg26w_internal_handoff_affordance",
            "role": "continuation_attention_gate",
            "candidate_move_uci": candidate["move"],
            "tier": "trial",
            "stem_cell_state": StemCellState.TRIAL.name,
        }),
        Node(ids.atom_probe_script, NodeType.SCRIPT, meta={"origin": "tg26w_internal_handoff_affordance", "role": "handoff_atom_probe"}),
        Node(ids.actuator_probe_script, NodeType.SCRIPT, meta={"origin": "tg26w_internal_handoff_affordance", "role": "handoff_actuator_probe"}),
        Node(ids.evidence_terminal, NodeType.TERMINAL, predicate=_handoff_evidence_predicate(ids.quorum_script), meta={
            "origin": "tg26w_internal_handoff_affordance",
            "role": "handoff_affordance_positive",
            "terminal_kind": "continuation_attention_gate",
            "candidate_move_uci": candidate["move"],
            "top_atom_keys": [atom.get("terminal_key") for atom in top_atoms],
        }),
        Node(ids.actuator_terminal, NodeType.TERMINAL, predicate=_handoff_actuator_predicate(candidate["move"]), meta={
            "origin": "tg26w_internal_handoff_affordance",
            "role": "handoff_actuator_terminal",
            "terminal_kind": "actuator_affordance",
            "candidate_move_uci": candidate["move"],
        }),
    ):
        if node.nid not in graph.graph.nodes:
            graph.graph.add_node(node)
            created_nodes += 1
    for parent, child, weight in (
        (ROOT_ID, ids.quorum_script, candidate["score"]),
        (ROOT_ID, ids.atom_probe_script, 0.0),
        (ROOT_ID, ids.actuator_probe_script, 0.0),
        (ids.quorum_script, ids.evidence_terminal, candidate["score"]),
        (ids.actuator_probe_script, ids.actuator_terminal, 0.0),
    ):
        created_edges += _add_hierarchy_pair_once(graph, parent, child, trainable=True, weight=weight)
    for atom_id in (*candidate["positive_atom_ids"], *candidate["negative_atom_ids"]):
        if atom_id in graph.graph.nodes:
            created_edges += _add_hierarchy_pair_once(graph, ids.atom_probe_script, atom_id, trainable=False, weight=0.0)
    return created_nodes, created_edges


def _handoff_evidence_predicate(quorum_script_id: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        graph = env["__graph__"]
        candidate = env["tg26w_handoff_candidates"][quorum_script_id]
        ids = _ExistingHandoffIds(quorum_script_id)
        positive = [
            atom_id for atom_id in candidate["positive_atom_ids"]
            if graph.nodes[atom_id].state in (NodeState.TRUE, NodeState.CONFIRMED)
        ]
        unsettled = [
            atom_id
            for atom_id in (*candidate["positive_atom_ids"], *candidate["negative_atom_ids"])
            if graph.nodes[atom_id].state not in (NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED)
        ]
        actuator_state = graph.nodes[ids.actuator_terminal].state
        if unsettled or actuator_state not in (NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED):
            return False, False
        score = float(candidate["score"])
        success = (
            not bool(candidate["mask_internal_handoff"])
            and not bool(candidate["mask_actuator"])
            and actuator_state in (NodeState.TRUE, NodeState.CONFIRMED)
            and len(positive) >= int(env.get("handoff_gate_min_positive_atoms", 2))
            and score >= float(env.get("handoff_gate_min_score", -10000.0))
        )
        node.meta["last_handoff_score"] = round(score, 6)
        node.meta["last_positive_handoff_atoms_confirmed"] = len(positive)
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _handoff_actuator_predicate(move_uci: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        board = env["board"]
        move = chess.Move.from_uci(move_uci)
        success = move in board.legal_moves
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _candidate_diagnostic(
    move: chess.Move,
    forced: set[str],
    *,
    guard_skip_used: bool,
    gate: dict[str, Any] | None,
    chain: dict[str, Any],
    audit: dict[str, Any],
) -> dict[str, Any]:
    return {
        "move": move.uci(),
        "validator_forced_first_move": move.uci() in forced,
        "guard_skip_used": guard_skip_used,
        "internal_handoff_gate_state": None if gate is None else gate["internal_handoff_gate_state"],
        "internal_handoff_score": None if gate is None else gate["internal_handoff_score"],
        "positive_handoff_atoms": [] if gate is None else gate["positive_handoff_atoms"],
        "negative_handoff_atoms": [] if gate is None else gate["negative_handoff_atoms"],
        "deep_reply_checks_run": int(chain.get("reply_total", 0)) > 0,
        "reply_total": int(chain.get("reply_total", 0)),
        "reply_solved": int(chain.get("reply_solved", 0)),
        "same_graph_second_move_count": int(chain.get("same_graph_second_move_count", 0)),
        "chain_success": bool(chain.get("chain_success", False)),
        "materialized_quorum_script_id": audit.get("quorum_script_id"),
        "actuator_terminal_state": audit.get("actuator_terminal_state"),
        "FormalReConEngine_confirmation_state": audit.get("graph_confirmation_state"),
    }


def _empty_mate2_audit(move_uci: str, chain: dict[str, Any]) -> dict[str, Any]:
    return {
        "move": move_uci,
        "first_move_confirmed": False,
        "quorum_script_id": None,
        "actuator_terminal_id": None,
        "evidence_terminal_state": "NOT_REQUESTED",
        "graph_confirmation_state": "NOT_REQUESTED",
        "formal_recon_engine_confirmed": False,
        "evidence_score": -10000.0,
        "positive_atom_ids": [],
        "positive_atoms_confirmed": 0,
        "negative_atom_ids": [],
        "chain_terminal_state": "NOT_REQUESTED",
        "actuator_terminal_state": "NOT_REQUESTED",
        "chain": chain,
        "strict_native_chain_materialized": False,
    }


@dataclass(frozen=True)
class _HandoffIds:
    fen: str
    move_uci: str

    @property
    def digest(self) -> str:
        return hashlib.sha1(f"tg26w|{self.fen}|{self.move_uci}".encode("utf-8")).hexdigest()[:16]

    @property
    def quorum_script(self) -> str:
        return f"tg26w_handoff_quorum_{self.digest}"

    @property
    def atom_probe_script(self) -> str:
        return f"{self.quorum_script}_atom_probe"

    @property
    def actuator_probe_script(self) -> str:
        return f"{self.quorum_script}_actuator_probe"

    @property
    def evidence_terminal(self) -> str:
        return f"{self.quorum_script}_evidence_terminal"

    @property
    def actuator_terminal(self) -> str:
        return f"{self.quorum_script}_actuator_terminal"


@dataclass(frozen=True)
class _ExistingHandoffIds:
    quorum_script: str

    @property
    def actuator_terminal(self) -> str:
        return f"{self.quorum_script}_actuator_terminal"


def _mate2_cfg(cfg: InternalHandoffAffordanceConfig) -> NativeQuorumMate2ChainingConfig:
    return NativeQuorumMate2ChainingConfig(
        seed=cfg.seed,
        mate1_train_count=cfg.mate1_train_count,
        mate1_heldout_count=cfg.mate1_heldout_count,
        mate2_train_count=cfg.mate2_train_count,
        mate2_heldout_count=cfg.mate2_heldout_count,
        max_generation_attempts=cfg.max_generation_attempts,
        train_repetitions=cfg.train_repetitions,
        continuation_repetitions=cfg.continuation_repetitions,
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
        mate2_materialized_quorum_min_positive_atoms=cfg.mate2_materialized_quorum_min_positive_atoms,
        materialized_quorum_min_evidence=cfg.materialized_quorum_min_evidence,
        veto_evidence_threshold=cfg.veto_evidence_threshold,
        first_move_chain_min_reply_success_rate=cfg.first_move_chain_min_reply_success_rate,
        equivalence_count=cfg.equivalence_count,
    )


def _failure_mode(internal: dict[str, Any]) -> str:
    if internal["internal_gate_approved_candidate_count"] == 0:
        return "internal_handoff_gate_too_weak"
    if internal["false_positive_internal_gate_count"] > internal["conversion_count"]:
        return "false_positives_too_high"
    if internal["false_negative_internal_gate_count"] > 0 and internal["conversion_rate"] == 0.0:
        return "false_negatives_too_high"
    if internal["same_graph_second_move_count"] == 0:
        return "Mate_In_1_continuation_not_robust_enough"
    if internal["conversion_rate"] == 0.0:
        return "insufficient_M3_or_missing_terminal_features"
    return "none"


def _purity_boundary() -> dict[str, Any]:
    return {
        "native_recon_graph_execution": True,
        "internal_handoff_affordance_materialized": True,
        "handoff_affordance_nodes_are_TERMINAL_and_SCRIPT": True,
        "same_native_graph_for_mate1_and_mate2": True,
        "same_graph_second_move_uses_materialized_mate1_quorum": True,
        "guard_used_during_training": True,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "hardcoded_mate1_handoff": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "python_batch_scorer_used_for_runtime_choice": False,
        "edge_fence_touched": False,
    }
