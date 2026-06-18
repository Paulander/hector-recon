"""TG26u native materialization of the TG26t soft quorum.

TG26t showed that shared TERMINAL atom evidence can select Mate_In_1 moves
when a soft quorum is allowed to bypass full triplet confirmation.  This module
keeps that soft quorum as a diagnostic baseline and materializes the quorum as
first-class ReCoN graph structure:

ROOT SCRIPT -> quorum SCRIPT -> quorum evidence TERMINAL
ROOT SCRIPT -> atom/action probe SCRIPTs -> shared atom/actuator TERMINALs

The evidence terminal confirms only from graph-local TERMINAL states.  It does
not choose a move directly; runtime selection is restricted to quorum SCRIPTs
that were confirmed by ``FormalReConEngine``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import chess

from recon_lite import FormalReConEngine, LinkType, Node, NodeState, NodeType
from recon_lite_hector.nodes.stem_cell import StemCellState

from .foundation_curriculum import _generate_mate_in_one_positions, _mate_moves
from .native_single_graph_curriculum import (
    ROOT_ID,
    NativeReConKRKGraph,
    _triplet_keys,
)
from .shared_atom_utility_voting import (
    SharedAtomUtilityVotingConfig,
    _apply_contrastive_credit,
    _move_vote,
    _native_config,
    _purity_boundary as _tg26t_purity_boundary,
    _run_vote_arm,
    _tg26s_config,
)
from .shared_feature_atoms import _run_arm as _run_tg26s_arm, _scheduler_equivalence


@dataclass(frozen=True)
class NativeQuorumMaterializationConfig:
    seed: int = 20260620
    train_count: int = 12
    heldout_count: int = 6
    max_generation_attempts: int = 500_000
    train_repetitions: int = 1
    max_ticks: int = 30
    max_samples: int = 24
    eta_m3: float = 0.10
    max_abs_local_weight: float = 1.0
    max_candidates_per_move: int = 1
    max_shared_atom_candidates_per_choice: int = 3
    shared_atom_min_overlap: int = 6
    min_vote_score: float = -10000.0
    soft_quorum_min_positive_atoms: int = 3
    materialized_quorum_min_positive_atoms: int = 3
    materialized_quorum_min_evidence: float = -10000.0
    veto_evidence_threshold: float = -0.25
    top_atom_ablation_count: int = 2
    equivalence_count: int = 4


@dataclass(frozen=True)
class NativeQuorumMaterializationResult:
    config: NativeQuorumMaterializationConfig
    dataset: dict[str, Any]
    baseline_prototype: dict[str, Any]
    soft_quorum_diagnostic: dict[str, Any]
    materialized_quorum: dict[str, Any]
    materialized_quorum_action_atoms: dict[str, Any]
    materialized_quorum_veto_atoms: dict[str, Any]
    featurehub_backed_materialized_quorum: dict[str, Any]
    ablations: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26u_native_quorum_materialization.v0",
            "checkpoint": "TG26u_native_quorum_materialization",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "baseline_prototype": self.baseline_prototype,
            "soft_quorum_diagnostic": self.soft_quorum_diagnostic,
            "materialized_quorum": self.materialized_quorum,
            "materialized_quorum_action_atoms": self.materialized_quorum_action_atoms,
            "materialized_quorum_veto_atoms": self.materialized_quorum_veto_atoms,
            "featurehub_backed_materialized_quorum": self.featurehub_backed_materialized_quorum,
            "ablations": self.ablations,
            "scheduler_equivalence": self.scheduler_equivalence,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_native_quorum_materialization(
    *,
    config: NativeQuorumMaterializationConfig | None = None,
) -> NativeQuorumMaterializationResult:
    cfg = config or NativeQuorumMaterializationConfig()
    train_fens = tuple(_generate_mate_in_one_positions(
        count=cfg.train_count,
        seed=cfg.seed,
        max_attempts=cfg.max_generation_attempts,
    ))
    heldout_fens = tuple(_generate_mate_in_one_positions(
        count=cfg.heldout_count,
        seed=cfg.seed + 1,
        excluded=set(train_fens),
        max_attempts=cfg.max_generation_attempts,
    ))
    tg26t_cfg = _tg26t_config(cfg)
    tg26s_cfg = _tg26s_config(tg26t_cfg)
    baseline = _run_tg26s_arm("baseline_prototype", tg26s_cfg, train_fens, heldout_fens)
    soft = _run_vote_arm(
        "soft_quorum_diagnostic",
        tg26t_cfg,
        train_fens,
        heldout_fens,
        contrastive=True,
        score_action_atoms=True,
        soft_quorum=True,
    )

    materialized = _run_materialized_arm(
        "materialized_quorum",
        cfg,
        train_fens,
        heldout_fens,
        score_action_atoms=False,
        use_veto_atoms=False,
    )
    action_atoms = _run_materialized_arm(
        "materialized_quorum_action_atoms",
        cfg,
        train_fens,
        heldout_fens,
        score_action_atoms=True,
        use_veto_atoms=False,
    )
    veto_atoms = _run_materialized_arm(
        "materialized_quorum_veto_atoms",
        cfg,
        train_fens,
        heldout_fens,
        score_action_atoms=True,
        use_veto_atoms=True,
    )
    featurehub = _run_materialized_arm(
        "featurehub_backed_materialized_quorum",
        cfg,
        train_fens,
        heldout_fens,
        score_action_atoms=True,
        use_veto_atoms=True,
        require_featurehub_atoms=True,
    )

    ablation_graph = _trained_graph(cfg, score_action_atoms=True)
    _train_graph(ablation_graph, train_fens, cfg)
    ablations = {
        "top_positive_atoms": _evaluate_materialized_quorum(
            ablation_graph,
            heldout_fens,
            cfg,
            arm="top_positive_atom_ablation",
            score_action_atoms=True,
            use_veto_atoms=True,
            mask_top_positive_atoms=True,
        ),
        "action_check_atoms": _evaluate_materialized_quorum(
            ablation_graph,
            heldout_fens,
            cfg,
            arm="action_check_atom_ablation",
            score_action_atoms=True,
            use_veto_atoms=True,
            mask_action_check_atoms=True,
        ),
        "after_check_atoms": _evaluate_materialized_quorum(
            ablation_graph,
            heldout_fens,
            cfg,
            arm="after_check_atom_ablation",
            score_action_atoms=True,
            use_veto_atoms=True,
            mask_after_check_atoms=True,
        ),
        "actuator_terminal": _evaluate_materialized_quorum(
            ablation_graph,
            heldout_fens,
            cfg,
            arm="actuator_ablation",
            score_action_atoms=True,
            use_veto_atoms=True,
            mask_actuator=True,
        ),
        "remove_materialized_quorum_keep_shared_atoms": _evaluate_without_materialized_quorum(
            ablation_graph,
            heldout_fens,
            cfg,
            score_action_atoms=True,
        ),
        "disable_featurehub_backed_atoms": _evaluate_materialized_quorum(
            ablation_graph,
            heldout_fens,
            cfg,
            arm="disable_featurehub_backed_atoms",
            score_action_atoms=True,
            use_veto_atoms=True,
            disable_featurehub_atoms=True,
        ),
    }
    equivalence = _scheduler_equivalence(tg26s_cfg, train_fens, heldout_fens)

    selected_materialized = featurehub if featurehub["heldout"]["accuracy"] >= veto_atoms["heldout"]["accuracy"] else veto_atoms
    selected_accuracy = selected_materialized["heldout"]["accuracy"]
    materialized_nulls = selected_materialized["null_selection_count"]
    formal_confirm_count = selected_materialized["heldout"]["materialized_quorum_confirmed_inside_formal_engine_count"]
    top_atom_accuracy = ablations["top_positive_atoms"]["accuracy"]
    action_atom_accuracy = ablations["action_check_atoms"]["accuracy"]
    actuator_accuracy = ablations["actuator_terminal"]["accuracy"]
    decision = {
        "checkpoint_pass": (
            selected_accuracy >= 5 / 6
            and materialized_nulls <= 1
            and formal_confirm_count >= max(1, selected_materialized["heldout"]["position_count"] - materialized_nulls)
            and actuator_accuracy == 0.0
            and equivalence["mismatch_count"] == 0
        ),
        "baseline_prototype_accuracy": baseline["heldout"]["accuracy"],
        "soft_quorum_accuracy": soft["heldout"]["accuracy"],
        "materialized_quorum_accuracy": selected_accuracy,
        "materialized_quorum_nulls": materialized_nulls,
        "strict_native_quorum_materialized": True,
        "soft_quorum_selected_without_full_triplet_confirmation_count": soft["heldout"][
            "soft_quorum_selected_without_full_triplet_confirmation_count"
        ],
        "materialized_quorum_confirmed_inside_formal_engine_count": formal_confirm_count,
        "featurehub_backed_atoms_used": featurehub["featurehub_backed_atoms_used"],
        "scheduler_equivalence_mismatch_count": equivalence["mismatch_count"],
        "top_atom_ablation_accuracy": top_atom_accuracy,
        "action_atom_ablation_accuracy": action_atom_accuracy,
        "actuator_ablation_accuracy": actuator_accuracy,
        "shared_atom_dependency_demonstrated": top_atom_accuracy < selected_accuracy or action_atom_accuracy < selected_accuracy,
        "purity_boundary": _purity_boundary(),
        "next_step": (
            "if accepted, repeat native materialized quorum on generated Mate_In_2 without hardcoded handoff"
            if selected_accuracy >= 5 / 6
            else "repair native quorum evidence before Mate_In_2"
        ),
    }
    return NativeQuorumMaterializationResult(
        config=cfg,
        dataset={
            "source": "generated legal KRK Mate_In_1 positions",
            "train_count": len(train_fens),
            "heldout_count": len(heldout_fens),
            "curriculum_labels_learner_visible": False,
            "mate2_touched": False,
            "edge_fence_touched": False,
        },
        baseline_prototype=baseline,
        soft_quorum_diagnostic=soft,
        materialized_quorum=materialized,
        materialized_quorum_action_atoms=action_atoms,
        materialized_quorum_veto_atoms=veto_atoms,
        featurehub_backed_materialized_quorum=featurehub,
        ablations=ablations,
        scheduler_equivalence=equivalence,
        decision=decision,
    )


def _run_materialized_arm(
    arm: str,
    cfg: NativeQuorumMaterializationConfig,
    train_fens: tuple[str, ...],
    heldout_fens: tuple[str, ...],
    *,
    score_action_atoms: bool,
    use_veto_atoms: bool,
    require_featurehub_atoms: bool = False,
) -> dict[str, Any]:
    graph = _trained_graph(cfg, score_action_atoms=score_action_atoms)
    training = _train_graph(graph, train_fens, cfg)
    heldout = _evaluate_materialized_quorum(
        graph,
        heldout_fens,
        cfg,
        arm=arm,
        score_action_atoms=score_action_atoms,
        use_veto_atoms=use_veto_atoms,
        require_featurehub_atoms=require_featurehub_atoms,
    )
    return {
        "arm": arm,
        "score_action_atoms": score_action_atoms,
        "use_veto_atoms": use_veto_atoms,
        "featurehub_backed_atoms_used": heldout["featurehub_backed_atoms_used"],
        "training": training,
        "heldout": heldout,
        "null_selection_count": sum(1 for row in heldout["samples"] if row["selected"] is None),
        "graph": graph.graph_diagnostics(),
    }


def _trained_graph(cfg: NativeQuorumMaterializationConfig, *, score_action_atoms: bool) -> NativeReConKRKGraph:
    return NativeReConKRKGraph(config=_native_config(_tg26t_config(cfg), score_action_atoms=score_action_atoms))


def _train_graph(
    graph: NativeReConKRKGraph,
    train_fens: tuple[str, ...],
    cfg: NativeQuorumMaterializationConfig,
) -> dict[str, Any]:
    # Reuse the TG26t substrate training.  It grows real shared atom terminals
    # and applies contrastive M3 credit; TG26u only changes runtime materialization.
    from .native_single_graph_curriculum import _train_mate1_stage

    training = _train_mate1_stage(graph, train_fens, config=graph.config)
    contrastive = _apply_contrastive_credit(graph, train_fens, _tg26t_config(cfg))
    return {"mate1_training": training, "contrastive_updates": contrastive}


def _evaluate_materialized_quorum(
    graph: NativeReConKRKGraph,
    fens: tuple[str, ...],
    cfg: NativeQuorumMaterializationConfig,
    *,
    arm: str,
    score_action_atoms: bool,
    use_veto_atoms: bool,
    mask_top_positive_atoms: bool = False,
    mask_action_check_atoms: bool = False,
    mask_after_check_atoms: bool = False,
    mask_actuator: bool = False,
    disable_featurehub_atoms: bool = False,
    require_featurehub_atoms: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    correct = 0
    formal_confirmed = 0
    materialized_nodes = 0
    materialized_edges = 0
    featurehub_atoms_used = False
    for fen in fens:
        board = chess.Board(fen)
        mates = {move.uci() for move in _mate_moves(board)}
        candidate_rows = [
            _candidate_row(graph, board, move, score_action_atoms=score_action_atoms)
            for move in sorted(board.legal_moves, key=lambda item: item.uci())
        ]
        for row in candidate_rows:
            if mask_top_positive_atoms:
                row["masked_atom_ids"] = {
                    atom["atom_id"]
                    for atom in row["top_atoms"][: cfg.top_atom_ablation_count]
                    if atom["contribution"] > 0.0
                }
            elif mask_action_check_atoms:
                row["masked_atom_ids"] = {
                    atom["atom_id"]
                    for atom in row["top_atoms"]
                    if _is_action_or_check_atom(atom)
                }
            elif mask_after_check_atoms:
                row["masked_atom_ids"] = {
                    atom["atom_id"]
                    for atom in row["top_atoms"]
                    if atom.get("role") == "after_feature" and _is_check_like_key(str(atom.get("terminal_key", "")))
                }
            elif disable_featurehub_atoms:
                row["masked_atom_ids"] = {
                    atom["atom_id"]
                    for atom in row["top_atoms"]
                    if "feature_hub_" in str(atom.get("terminal_key", ""))
                }
            else:
                row["masked_atom_ids"] = set()
        confirmed: list[dict[str, Any]] = []
        audits: list[dict[str, Any]] = []
        for row in candidate_rows:
            audit = _confirm_materialized_candidate(
                graph,
                board,
                cfg,
                arm=arm,
                row=row,
                use_veto_atoms=use_veto_atoms,
                mask_actuator=mask_actuator,
                require_featurehub_atoms=require_featurehub_atoms,
            )
            materialized_nodes += audit["materialized_node_count"]
            materialized_edges += audit["materialized_edge_count"]
            audits.append(audit)
            featurehub_atoms_used = featurehub_atoms_used or bool(audit["featurehub_atom_count"])
            if audit["quorum_script_confirmed"]:
                formal_confirmed += 1
                confirmed.append(audit)
        confirmed.sort(key=lambda item: (item["evidence_score"], item["positive_atoms_confirmed"], item["move"]), reverse=True)
        selected = None if not confirmed else confirmed[0]["move"]
        ok = selected in mates
        correct += int(ok)
        rows.append({
            "fen": fen,
            "selected": selected,
            "correct_mates": sorted(mates),
            "correct": ok,
            "selected_quorum_script_id": None if not confirmed else confirmed[0]["quorum_script_id"],
            "selected_actuator_terminal_id": None if not confirmed else confirmed[0]["actuator_terminal_id"],
            "top_confirmed_candidates": confirmed[:8],
            "candidate_audits": audits[:8],
        })
    return {
        "arm": arm,
        "position_count": len(rows),
        "correct_count": correct,
        "accuracy": 0.0 if not rows else correct / len(rows),
        "samples": rows[: cfg.max_samples],
        "materialized_node_count": materialized_nodes,
        "materialized_edge_count": materialized_edges,
        "materialized_quorum_confirmed_inside_formal_engine_count": formal_confirmed,
        "featurehub_backed_atoms_used": featurehub_atoms_used,
        "strict_native_quorum_materialized": True,
        "runtime_selection_from_confirmed_quorum_scripts_only": True,
    }


def _evaluate_without_materialized_quorum(
    graph: NativeReConKRKGraph,
    fens: tuple[str, ...],
    cfg: NativeQuorumMaterializationConfig,
    *,
    score_action_atoms: bool,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for fen in fens:
        board = chess.Board(fen)
        rows.append({
            "fen": fen,
            "selected": None,
            "correct_mates": sorted(move.uci() for move in _mate_moves(board)),
            "shared_atom_count": sum(
                len(_candidate_row(graph, board, move, score_action_atoms=score_action_atoms)["atom_ids"])
                for move in board.legal_moves
            ),
            "reason": "materialized quorum SCRIPT removed; shared atoms remain but no actuator quorum can confirm",
        })
    return {
        "position_count": len(rows),
        "correct_count": 0,
        "accuracy": 0.0,
        "samples": rows[: cfg.max_samples],
        "strict_native_quorum_materialized": False,
    }


def _candidate_row(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    move: chess.Move,
    *,
    score_action_atoms: bool,
) -> dict[str, Any]:
    row = _move_vote(graph, board, move, score_action_atoms=score_action_atoms, soft_quorum=True)
    keys = _triplet_keys(board, move, key_mode="prototype")
    atom_ids = graph._shared_atom_ids_for_keys(keys)  # graph-local shared atom retrieval
    return {**row, "atom_ids": sorted(atom_ids), "keys": keys}


def _confirm_materialized_candidate(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    cfg: NativeQuorumMaterializationConfig,
    *,
    arm: str,
    row: dict[str, Any],
    use_veto_atoms: bool,
    mask_actuator: bool,
    require_featurehub_atoms: bool,
) -> dict[str, Any]:
    move_uci = str(row["move"])
    ids = _QuorumIds(arm=arm, fen=board.fen(), move_uci=move_uci)
    masked_atom_ids = set(row.get("masked_atom_ids", set()))
    top_atoms = [
        atom
        for atom in row["top_atoms"]
        if atom["atom_id"] not in masked_atom_ids
    ]
    positive_atoms = [atom for atom in top_atoms if atom["contribution"] > 0.0]
    negative_atoms = [atom for atom in top_atoms if atom["contribution"] < 0.0]
    positive_atom_ids = [str(atom["atom_id"]) for atom in positive_atoms]
    negative_atom_ids = [str(atom["atom_id"]) for atom in negative_atoms]
    featurehub_atom_count = sum(1 for atom in top_atoms if "feature_hub_" in str(atom.get("terminal_key", "")))
    evidence_score = round(sum(float(atom["contribution"]) for atom in positive_atoms + (negative_atoms if use_veto_atoms else [])), 6)
    candidate = {
        "move": move_uci,
        "positive_atom_ids": positive_atom_ids,
        "negative_atom_ids": negative_atom_ids,
        "evidence_score": evidence_score,
        "use_veto_atoms": use_veto_atoms,
        "mask_actuator": mask_actuator,
        "require_featurehub_atoms": require_featurehub_atoms,
        "featurehub_atom_count": featurehub_atom_count,
    }
    created_nodes, created_edges = _materialize_quorum_nodes(graph, ids, candidate, top_atoms)
    active_nodes = {
        ROOT_ID,
        ids.quorum_script,
        ids.evidence_terminal,
        ids.atom_probe_script,
        ids.actuator_probe_script,
        ids.actuator_terminal,
        *positive_atom_ids,
        *negative_atom_ids,
    }
    graph._reset_runtime_states(active_nodes)
    env: dict[str, Any] = {
        "board": board,
        "shared_atom_move_uci": move_uci,
        "tg26u_quorum_candidates": {ids.quorum_script: candidate},
        "materialized_quorum_min_positive_atoms": cfg.materialized_quorum_min_positive_atoms,
        "materialized_quorum_min_evidence": cfg.materialized_quorum_min_evidence,
        "veto_evidence_threshold": cfg.veto_evidence_threshold,
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
    quorum_state = graph.graph.nodes[ids.quorum_script].state
    evidence_node = graph.graph.nodes[ids.evidence_terminal]
    actuator_state = graph.graph.nodes[ids.actuator_terminal].state
    confirmed_positive_ids = [
        atom_id
        for atom_id in positive_atom_ids
        if graph.graph.nodes[atom_id].state in (NodeState.TRUE, NodeState.CONFIRMED)
    ]
    confirmed_negative_ids = [
        atom_id
        for atom_id in negative_atom_ids
        if graph.graph.nodes[atom_id].state in (NodeState.TRUE, NodeState.CONFIRMED)
    ]
    return {
        "move": move_uci,
        "quorum_script_id": ids.quorum_script,
        "selected_quorum_script_id": ids.quorum_script,
        "actuator_terminal_id": ids.actuator_terminal,
        "selected_actuator_terminal_id": ids.actuator_terminal,
        "positive_atom_ids": positive_atom_ids,
        "positive_atoms_confirmed": len(confirmed_positive_ids),
        "confirmed_positive_atom_ids": confirmed_positive_ids,
        "negative_atom_ids": negative_atom_ids,
        "negative_veto_atom_ids": negative_atom_ids if use_veto_atoms else [],
        "negative_atoms_confirmed": len(confirmed_negative_ids),
        "evidence_score": evidence_node.meta.get("last_evidence_score", evidence_score),
        "graph_confirmation_state": quorum_state.name,
        "formal_recon_engine_confirmed": quorum_state in (NodeState.TRUE, NodeState.CONFIRMED),
        "quorum_script_confirmed": quorum_state in (NodeState.TRUE, NodeState.CONFIRMED),
        "evidence_terminal_state": evidence_node.state.name,
        "actuator_terminal_state": actuator_state.name,
        "formal_ticks_run": engine.tick,
        "diagnostic_soft_quorum_same_move": True,
        "dependency_on_shared_atoms": bool(positive_atom_ids),
        "featurehub_atom_count": featurehub_atom_count,
        "materialized_node_count": created_nodes,
        "materialized_edge_count": created_edges,
        "masked_atom_count": len(masked_atom_ids),
        "purity_boundary": {
            "confirmed_by_formal_recon_engine": quorum_state in (NodeState.TRUE, NodeState.CONFIRMED),
            "evidence_terminal_reads_graph_node_states": True,
            "actuator_legality_checked_by_terminal": True,
            "python_batch_final_move_scorer": False,
        },
    }


def _materialize_quorum_nodes(
    graph: NativeReConKRKGraph,
    ids: "_QuorumIds",
    candidate: dict[str, Any],
    top_atoms: list[dict[str, Any]],
) -> tuple[int, int]:
    created_nodes = 0
    created_edges = 0
    for node in (
        Node(ids.quorum_script, NodeType.SCRIPT, meta={
            "origin": "tg26u_native_quorum_materialization",
            "role": "quorum_script",
            "candidate_move_uci": candidate["move"],
            "tier": "trial",
            "stem_cell_state": StemCellState.TRIAL.name,
            "evidence_score": candidate["evidence_score"],
        }),
        Node(ids.atom_probe_script, NodeType.SCRIPT, meta={
            "origin": "tg26u_native_quorum_materialization",
            "role": "quorum_atom_probe_script",
            "candidate_move_uci": candidate["move"],
            "tier": "trial",
        }),
        Node(ids.actuator_probe_script, NodeType.SCRIPT, meta={
            "origin": "tg26u_native_quorum_materialization",
            "role": "quorum_actuator_probe_script",
            "candidate_move_uci": candidate["move"],
            "tier": "trial",
        }),
        Node(ids.evidence_terminal, NodeType.TERMINAL, predicate=_quorum_evidence_predicate(ids.quorum_script), meta={
            "origin": "tg26u_native_quorum_materialization",
            "role": "quorum_evidence_terminal",
            "terminal_kind": "evidence_quorum",
            "candidate_move_uci": candidate["move"],
            "positive_atom_ids": list(candidate["positive_atom_ids"]),
            "negative_atom_ids": list(candidate["negative_atom_ids"]),
            "top_atom_keys": [atom.get("terminal_key") for atom in top_atoms],
            "tier": "trial",
        }),
        Node(ids.actuator_terminal, NodeType.TERMINAL, predicate=_materialized_actuator_predicate(candidate["move"]), meta={
            "origin": "tg26u_native_quorum_materialization",
            "role": "actuator_terminal",
            "terminal_kind": "actuator_affordance",
            "candidate_move_uci": candidate["move"],
            "tier": "trial",
        }),
    ):
        if node.nid not in graph.graph.nodes:
            graph.graph.add_node(node)
            created_nodes += 1
    for parent, child, weight in (
        (ROOT_ID, ids.quorum_script, candidate["evidence_score"]),
        (ROOT_ID, ids.atom_probe_script, 0.0),
        (ROOT_ID, ids.actuator_probe_script, 0.0),
        (ids.quorum_script, ids.evidence_terminal, candidate["evidence_score"]),
        (ids.actuator_probe_script, ids.actuator_terminal, 0.0),
    ):
        created_edges += _add_hierarchy_pair_once(graph, parent, child, trainable=True, weight=weight)
    for atom_id in (*candidate["positive_atom_ids"], *candidate["negative_atom_ids"]):
        if atom_id in graph.graph.nodes:
            created_edges += _add_hierarchy_pair_once(graph, ids.atom_probe_script, atom_id, trainable=False, weight=0.0)
    return created_nodes, created_edges


def _quorum_evidence_predicate(quorum_script_id: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        graph = env["__graph__"]
        candidate = env["tg26u_quorum_candidates"][quorum_script_id]
        positive_atom_ids = list(candidate["positive_atom_ids"])
        negative_atom_ids = list(candidate["negative_atom_ids"])
        positive_confirmed = [
            atom_id
            for atom_id in positive_atom_ids
            if graph.nodes[atom_id].state in (NodeState.TRUE, NodeState.CONFIRMED)
        ]
        negative_confirmed = [
            atom_id
            for atom_id in negative_atom_ids
            if graph.nodes[atom_id].state in (NodeState.TRUE, NodeState.CONFIRMED)
        ]
        unsettled = [
            atom_id
            for atom_id in (*positive_atom_ids, *negative_atom_ids)
            if graph.nodes[atom_id].state not in (NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED)
        ]
        actuator_id = _QuorumIds.from_script_id(quorum_script_id).actuator_terminal
        actuator_state = graph.nodes[actuator_id].state
        if unsettled or actuator_state not in (NodeState.TRUE, NodeState.CONFIRMED, NodeState.FAILED):
            return False, False
        evidence_score = float(candidate["evidence_score"])
        veto_score = 0.0
        if candidate["use_veto_atoms"]:
            for atom_id in negative_confirmed:
                atom = graph.nodes[atom_id]
                veto_score += min(0.0, float(atom.meta.get("local_weight", 0.0)))
        success = (
            len(positive_confirmed) >= int(env.get("materialized_quorum_min_positive_atoms", 3))
            and evidence_score >= float(env.get("materialized_quorum_min_evidence", -10000.0))
            and actuator_state in (NodeState.TRUE, NodeState.CONFIRMED)
            and not bool(candidate["mask_actuator"])
            and (not candidate["require_featurehub_atoms"] or int(candidate["featurehub_atom_count"]) > 0)
            and veto_score > float(env.get("veto_evidence_threshold", -0.25))
        )
        node.meta["last_positive_atoms_confirmed"] = len(positive_confirmed)
        node.meta["last_negative_atoms_confirmed"] = len(negative_confirmed)
        node.meta["last_evidence_score"] = round(evidence_score, 6)
        node.meta["last_veto_score"] = round(veto_score, 6)
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _materialized_actuator_predicate(move_uci: str):
    def predicate(node: Node, env: dict[str, Any]) -> tuple[bool, bool]:
        board = env["board"]
        move = chess.Move.from_uci(move_uci)
        success = move in board.legal_moves
        node.activation.value = 1.0 if success else 0.0
        return True, success

    return predicate


def _add_hierarchy_pair_once(
    graph: NativeReConKRKGraph,
    parent: str,
    child: str,
    *,
    trainable: bool,
    weight: float,
) -> int:
    created = 0
    if graph.graph.get_edge(parent, child, LinkType.SUB) is None:
        graph.graph.add_edge(parent, child, LinkType.SUB)
        created += 1
    if graph.graph.get_edge(child, parent, LinkType.SUR) is None:
        graph.graph.add_edge(child, parent, LinkType.SUR)
        created += 1
    sub = graph.graph.get_edge(parent, child, LinkType.SUB)
    sur = graph.graph.get_edge(child, parent, LinkType.SUR)
    if sub is not None:
        sub.w = float(weight)
        sub.meta.update({"trainable": trainable, "tier": "trial", "stem_cell_state": StemCellState.TRIAL.name})
    if sur is not None:
        sur.meta.update({"structural_fixed": True})
    return created


@dataclass(frozen=True)
class _QuorumIds:
    arm: str
    fen: str
    move_uci: str

    @property
    def digest(self) -> str:
        payload = f"{self.arm}|{self.fen}|{self.move_uci}".encode("utf-8")
        return hashlib.sha1(payload).hexdigest()[:16]

    @property
    def quorum_script(self) -> str:
        return f"tg26u_quorum_{self.digest}"

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

    @classmethod
    def from_script_id(cls, script_id: str) -> "_ExistingQuorumIds":
        return _ExistingQuorumIds(script_id)


@dataclass(frozen=True)
class _ExistingQuorumIds:
    quorum_script: str

    @property
    def actuator_terminal(self) -> str:
        return f"{self.quorum_script}_actuator_terminal"


def _is_action_or_check_atom(atom: dict[str, Any]) -> bool:
    key = str(atom.get("terminal_key", ""))
    return key.startswith("action_pattern:") or _is_check_like_key(key)


def _is_check_like_key(key: str) -> bool:
    return any(token in key for token in ("check", "mate", "legal_gives_check"))


def _tg26t_config(cfg: NativeQuorumMaterializationConfig) -> SharedAtomUtilityVotingConfig:
    return SharedAtomUtilityVotingConfig(
        seed=cfg.seed,
        train_count=cfg.train_count,
        heldout_count=cfg.heldout_count,
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
        equivalence_count=cfg.equivalence_count,
    )


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg26t_purity_boundary()
    boundary.update({
        "strict_native_quorum_materialized": True,
        "soft_quorum_not_yet_materialized_as_recon_script": False,
        "soft_quorum_diagnostic_only": True,
        "soft_quorum_can_select_without_full_triplet_confirmation": False,
        "materialized_quorum_is_SCRIPT": True,
        "materialized_quorum_evidence_is_TERMINAL": True,
        "materialized_actuator_is_TERMINAL": True,
        "shared_atoms_participate_as_NodeType_TERMINAL": True,
        "formal_recon_engine_confirms_selected_quorum": True,
        "python_shared_atom_utility_vote_used_for_candidate_ordering": False,
        "python_batch_scorer_used_for_runtime_choice": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "mate2_touched": False,
        "edge_fence_touched": False,
    })
    return boundary
