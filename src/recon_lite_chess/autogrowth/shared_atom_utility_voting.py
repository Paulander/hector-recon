"""TG26t shared atom utility voting checkpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

import chess

from .foundation_curriculum import _generate_mate_in_one_positions, _mate_moves
from .native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
    _evaluate_mate1_stage,
    _train_mate1_stage,
    _triplet_id,
    _triplet_keys,
)
from .shared_feature_atoms import SharedFeatureAtomConfig, _run_arm as _run_tg26s_arm, _scheduler_equivalence


@dataclass(frozen=True)
class SharedAtomUtilityVotingConfig:
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
    equivalence_count: int = 4


@dataclass(frozen=True)
class SharedAtomUtilityVotingResult:
    config: SharedAtomUtilityVotingConfig
    dataset: dict[str, Any]
    baseline_prototype: dict[str, Any]
    shared_hard_overlap: dict[str, Any]
    shared_weighted_vote: dict[str, Any]
    shared_action_atom_score: dict[str, Any]
    shared_contrastive_credit: dict[str, Any]
    soft_quorum: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26t_shared_atom_utility_voting.v0",
            "checkpoint": "TG26t_shared_atom_utility_voting",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "baseline_prototype": self.baseline_prototype,
            "shared_hard_overlap": self.shared_hard_overlap,
            "shared_weighted_vote": self.shared_weighted_vote,
            "shared_action_atom_score": self.shared_action_atom_score,
            "shared_contrastive_credit": self.shared_contrastive_credit,
            "soft_quorum": self.soft_quorum,
            "scheduler_equivalence": self.scheduler_equivalence,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_shared_atom_utility_voting(
    *,
    config: SharedAtomUtilityVotingConfig | None = None,
) -> SharedAtomUtilityVotingResult:
    cfg = config or SharedAtomUtilityVotingConfig()
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
    tg26s_cfg = _tg26s_config(cfg)
    baseline = _run_tg26s_arm("baseline_prototype", tg26s_cfg, train_fens, heldout_fens)
    hard = _run_tg26s_arm("shared_atom", tg26s_cfg, train_fens, heldout_fens)
    weighted = _run_vote_arm("shared_weighted_vote", cfg, train_fens, heldout_fens)
    action = _run_vote_arm("shared_action_atom_score", cfg, train_fens, heldout_fens, score_action_atoms=True)
    contrastive = _run_vote_arm("shared_contrastive_credit", cfg, train_fens, heldout_fens, contrastive=True, score_action_atoms=True)
    quorum = _run_vote_arm("soft_quorum", cfg, train_fens, heldout_fens, contrastive=True, score_action_atoms=True, soft_quorum=True)
    equivalence = _scheduler_equivalence(tg26s_cfg, train_fens, heldout_fens)
    accuracies = {
        "shared_weighted_vote": weighted["heldout"]["accuracy"],
        "shared_action_atom_score": action["heldout"]["accuracy"],
        "shared_contrastive_credit": contrastive["heldout"]["accuracy"],
        "soft_quorum": quorum["heldout"]["accuracy"],
    }
    null_counts = {
        "baseline_prototype": baseline["null_selection_count"],
        "shared_hard_overlap": hard["null_selection_count"],
        "shared_weighted_vote": weighted["null_selection_count"],
        "shared_action_atom_score": action["null_selection_count"],
        "shared_contrastive_credit": contrastive["null_selection_count"],
        "soft_quorum": quorum["null_selection_count"],
    }
    best_shared = max(accuracies.values())
    decision = {
        "checkpoint_pass": (
            best_shared > hard["heldout"]["accuracy"]
            and min(null_counts[key] for key in null_counts if key != "baseline_prototype") < hard["null_selection_count"]
            and equivalence["mismatch_count"] == 0
        ),
        "baseline_prototype_accuracy": baseline["heldout"]["accuracy"],
        "shared_hard_overlap_accuracy": hard["heldout"]["accuracy"],
        "shared_weighted_vote_accuracy": weighted["heldout"]["accuracy"],
        "shared_action_atom_score_accuracy": action["heldout"]["accuracy"],
        "shared_contrastive_credit_accuracy": contrastive["heldout"]["accuracy"],
        "soft_quorum_accuracy": quorum["heldout"]["accuracy"],
        "null_count_per_arm": null_counts,
        "target_move_candidate_diagnostics": quorum["target_move_candidate_diagnostics"],
        "action_atom_inclusion_exclusion_diagnostics": {
            "action_atoms_excluded_arm": weighted["action_atom_diagnostics"],
            "action_atoms_included_arm": action["action_atom_diagnostics"],
        },
        "active_atom_overlap_distribution": quorum["active_atom_overlap_distribution"],
        "atom_utility_contribution_samples": quorum["atom_utility_contribution_samples"],
        "top_positive_atoms": quorum["graph"]["shared_atom_stats"]["top_positive_atoms"],
        "top_negative_atoms": quorum["graph"]["shared_atom_stats"]["top_negative_atoms"],
        "high_precision_but_unused_atoms": quorum["high_precision_but_unused_atoms"],
        "scheduler_equivalence_mismatches": equivalence["mismatch_count"],
        "strict_native_quorum_materialized": False,
        "soft_quorum_selected_without_full_triplet_confirmation_count": quorum["heldout"][
            "soft_quorum_selected_without_full_triplet_confirmation_count"
        ],
        "purity_boundary": _purity_boundary(),
        "next_step": (
            "continue shared Mate_In_1 repair/scaling before Mate_In_2"
            if best_shared >= baseline["heldout"]["accuracy"]
            else "repair shared atom utility/calibration before Mate_In_2"
        ),
    }
    return SharedAtomUtilityVotingResult(
        config=cfg,
        dataset={
            "source": "generated legal KRK Mate_In_1 positions",
            "train_count": len(train_fens),
            "heldout_count": len(heldout_fens),
            "curriculum_labels_learner_visible": False,
        },
        baseline_prototype=baseline,
        shared_hard_overlap=hard,
        shared_weighted_vote=weighted,
        shared_action_atom_score=action,
        shared_contrastive_credit=contrastive,
        soft_quorum=quorum,
        scheduler_equivalence=equivalence,
        decision=decision,
    )


def _run_vote_arm(
    arm: str,
    cfg: SharedAtomUtilityVotingConfig,
    train_fens: tuple[str, ...],
    heldout_fens: tuple[str, ...],
    *,
    score_action_atoms: bool = False,
    contrastive: bool = False,
    soft_quorum: bool = False,
) -> dict[str, Any]:
    native_cfg = _native_config(cfg, score_action_atoms=score_action_atoms)
    graph = NativeReConKRKGraph(config=native_cfg)
    training = _train_mate1_stage(graph, train_fens, config=native_cfg)
    contrastive_updates = _apply_contrastive_credit(graph, train_fens, cfg) if contrastive else {"updates": 0}
    heldout = _evaluate_voting(graph, heldout_fens, cfg, score_action_atoms=score_action_atoms, soft_quorum=soft_quorum)
    graph_diag = graph.graph_diagnostics()
    return {
        "arm": arm,
        "score_action_atoms": score_action_atoms,
        "contrastive_credit": contrastive,
        "soft_quorum": soft_quorum,
        "soft_quorum_min_positive_atoms": cfg.soft_quorum_min_positive_atoms,
        "training": training,
        "contrastive_updates": contrastive_updates,
        "heldout": heldout,
        "null_selection_count": sum(1 for row in heldout["samples"] if row["selected"] is None),
        "target_move_candidate_diagnostics": heldout["target_move_candidate_diagnostics"],
        "action_atom_diagnostics": heldout["action_atom_diagnostics"],
        "active_atom_overlap_distribution": heldout["active_atom_overlap_distribution"],
        "atom_utility_contribution_samples": heldout["atom_utility_contribution_samples"],
        "high_precision_but_unused_atoms": _high_precision_unused_atoms(graph),
        "graph": graph_diag,
    }


def _evaluate_voting(
    graph: NativeReConKRKGraph,
    fens: tuple[str, ...],
    cfg: SharedAtomUtilityVotingConfig,
    *,
    score_action_atoms: bool,
    soft_quorum: bool,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    contribution_samples: list[dict[str, Any]] = []
    target_diagnostics: list[dict[str, Any]] = []
    overlap_counts: list[int] = []
    action_included = 0
    action_excluded = 0
    correct = 0
    soft_quorum_without_full_confirmation = 0
    for fen in fens:
        board = chess.Board(fen)
        mates = {move.uci() for move in _mate_moves(board)}
        vote_rows = [_move_vote(graph, board, move, score_action_atoms=score_action_atoms, soft_quorum=soft_quorum) for move in board.legal_moves]
        overlap_counts.extend(row["active_atom_count"] for row in vote_rows)
        action_included += sum(row["action_atom_count"] for row in vote_rows)
        action_excluded += sum(row["excluded_action_atom_count"] for row in vote_rows)
        vote_rows.sort(key=lambda item: (item["utility_score"], item["active_atom_count"], item["move"]), reverse=True)
        selected = None
        selected_triplet = None
        confirmed = None
        for row in vote_rows:
            if row["utility_score"] <= cfg.min_vote_score and not soft_quorum:
                continue
            audit = graph.confirm_candidate(board, triplet_id=row["triplet_id"], move_uci=row["move"])
            if audit.get("selected_move") == row["move"]:
                selected = row["move"]
                selected_triplet = row["triplet_id"]
                confirmed = audit
                break
            if (
                soft_quorum
                and row["positive_atom_count"] >= cfg.soft_quorum_min_positive_atoms
                and row["utility_score"] > cfg.min_vote_score
            ):
                selected = row["move"]
                selected_triplet = row["triplet_id"]
                confirmed = {
                    **audit,
                    "soft_quorum_selected_without_full_triplet_confirmation": True,
                    "positive_atom_count": row["positive_atom_count"],
                }
                soft_quorum_without_full_confirmation += 1
                break
        ok = selected in mates
        correct += int(ok)
        target_vote = next((row for row in vote_rows if row["move"] in mates), None)
        target_diagnostics.append({
            "fen": fen,
            "target_moves": sorted(mates),
            "target_found": target_vote is not None,
            "target_utility_score": None if target_vote is None else target_vote["utility_score"],
            "target_active_atom_count": None if target_vote is None else target_vote["active_atom_count"],
            "selected": selected,
            "selected_triplet": selected_triplet,
            "confirmed": confirmed,
        })
        rows.append({
            "fen": fen,
            "selected": selected,
            "correct_mates": sorted(mates),
            "correct": ok,
            "top_votes": vote_rows[: min(8, len(vote_rows))],
        })
        if len(contribution_samples) < cfg.max_samples and vote_rows:
            contribution_samples.append({"fen": fen, "top_move": vote_rows[0]["move"], "top_atoms": vote_rows[0]["top_atoms"]})
    total = len(rows)
    return {
        "position_count": total,
        "correct_count": correct,
        "accuracy": 0.0 if total == 0 else correct / total,
        "samples": rows[: cfg.max_samples],
        "target_move_candidate_diagnostics": target_diagnostics[: cfg.max_samples],
        "action_atom_diagnostics": {
            "score_action_atoms": score_action_atoms,
            "included_action_atom_activations": action_included,
            "excluded_action_atom_activations": action_excluded,
        },
        "active_atom_overlap_distribution": _distribution(overlap_counts),
        "atom_utility_contribution_samples": contribution_samples,
        "soft_quorum_selected_without_full_triplet_confirmation_count": soft_quorum_without_full_confirmation,
    }


def _move_vote(
    graph: NativeReConKRKGraph,
    board: chess.Board,
    move: chess.Move,
    *,
    score_action_atoms: bool,
    soft_quorum: bool,
) -> dict[str, Any]:
    keys = _triplet_keys(board, move, key_mode="prototype")
    atom_ids = graph._shared_atom_ids_for_keys(keys)  # intentional local scheduler diagnostic hook
    triplets = graph._triplets_from_active_shared_atoms(keys)
    triplet_id = _triplet_id(*keys)
    if triplets:
        triplet_id = triplets[0]
    utility = 0.0
    action_atom_count = 0
    excluded_action_atom_count = 0
    top_atoms: list[dict[str, Any]] = []
    for atom_id in atom_ids:
        node = graph.graph.nodes[atom_id]
        terminal_key = str(node.meta.get("terminal_key", ""))
        is_action = terminal_key.startswith("action_pattern:")
        if is_action and not score_action_atoms:
            excluded_action_atom_count += 1
            continue
        if is_action:
            action_atom_count += 1
        weight = float(node.meta.get("local_weight", 0.0))
        precision = float(node.meta.get("context_precision", 0.0))
        positive = float(node.meta.get("positive_correlation", 0.0))
        false_positive = int(node.meta.get("false_positive_count", 0))
        role = str(node.meta.get("role", ""))
        role_weight = 1.0
        if role == "after_feature":
            role_weight = 1.2
        elif role == "delta_feature":
            role_weight = 1.1
        elif role == "projection_feature":
            role_weight = 1.15
        contribution = role_weight * (weight + 0.20 * precision + 0.10 * positive - 0.02 * false_positive)
        utility += contribution
        top_atoms.append({
            "atom_id": atom_id,
            "terminal_key": terminal_key,
            "role": role,
            "contribution": round(contribution, 6),
            "local_weight": round(weight, 6),
            "context_precision": round(precision, 6),
        })
    top_atoms.sort(key=lambda item: item["contribution"], reverse=True)
    positive_atom_count = sum(1 for atom in top_atoms if atom["contribution"] > 0.0)
    if soft_quorum and positive_atom_count >= 3:
        utility += 0.25
    return {
        "move": move.uci(),
        "triplet_id": triplet_id,
        "retrieved_triplet_count": len(triplets),
        "active_atom_count": len(atom_ids),
        "action_atom_count": action_atom_count,
        "excluded_action_atom_count": excluded_action_atom_count,
        "positive_atom_count": positive_atom_count,
        "utility_score": round(utility, 6),
        "top_atoms": top_atoms[:8],
    }


def _apply_contrastive_credit(
    graph: NativeReConKRKGraph,
    train_fens: tuple[str, ...],
    cfg: SharedAtomUtilityVotingConfig,
) -> dict[str, Any]:
    updates = 0
    for fen in train_fens:
        board = chess.Board(fen)
        positive_moves = {move.uci() for move in _mate_moves(board)}
        positive_atoms: set[str] = set()
        move_atoms: dict[str, set[str]] = {}
        for move in board.legal_moves:
            keys = _triplet_keys(board, move, key_mode="prototype")
            atoms = graph._shared_atom_ids_for_keys(keys)
            move_atoms[move.uci()] = atoms
            if move.uci() in positive_moves:
                positive_atoms.update(atoms)
        for move_uci, atoms in move_atoms.items():
            if move_uci in positive_moves:
                for atom_id in atoms:
                    _adjust_atom(graph, atom_id, cfg.eta_m3 * 0.5)
                    updates += 1
            else:
                distinguishing_bad = atoms - positive_atoms
                for atom_id in distinguishing_bad:
                    _adjust_atom(graph, atom_id, -cfg.eta_m3 * 0.25)
                    updates += 1
    return {"updates": updates, "mode": "within_position_contrastive_advantage"}


def _adjust_atom(graph: NativeReConKRKGraph, atom_id: str, delta: float) -> None:
    node = graph.graph.nodes[atom_id]
    node.meta["local_weight"] = max(
        -graph.config.max_abs_local_weight,
        min(graph.config.max_abs_local_weight, float(node.meta.get("local_weight", 0.0)) + delta),
    )
    if delta > 0:
        node.meta["confirm_count"] = int(node.meta.get("confirm_count", 0)) + 1
    elif delta < 0:
        node.meta["false_positive_count"] = int(node.meta.get("false_positive_count", 0)) + 1
        node.meta["negative_confirm_count"] = int(node.meta.get("negative_confirm_count", 0)) + 1
    exposures = max(1, int(node.meta.get("request_exposures", 0)))
    node.meta["positive_correlation"] = int(node.meta.get("confirm_count", 0)) / exposures
    node.meta["negative_correlation"] = int(node.meta.get("negative_confirm_count", 0)) / exposures
    node.meta["context_precision"] = (
        int(node.meta.get("confirm_count", 0))
        / max(1, int(node.meta.get("confirm_count", 0)) + int(node.meta.get("false_positive_count", 0)))
    )


def _high_precision_unused_atoms(graph: NativeReConKRKGraph) -> list[dict[str, Any]]:
    rows = graph.shared_atom_diagnostics(max_atoms=512)["top_positive_atoms"]
    selected = []
    for row in rows:
        key = str(row.get("terminal_key", ""))
        if not key.startswith("action_pattern:"):
            continue
        if row.get("context_precision", 0.0) < 0.5:
            continue
        selected.append(row)
    return selected[:24]


def _tg26s_config(cfg: SharedAtomUtilityVotingConfig) -> SharedFeatureAtomConfig:
    return SharedFeatureAtomConfig(
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
        equivalence_count=cfg.equivalence_count,
    )


def _native_config(cfg: SharedAtomUtilityVotingConfig, *, score_action_atoms: bool) -> NativeSingleGraphConfig:
    return NativeSingleGraphConfig(
        train_repetitions=cfg.train_repetitions,
        eta_m3=cfg.eta_m3,
        max_abs_local_weight=cfg.max_abs_local_weight,
        max_ticks=cfg.max_ticks,
        max_samples=max(cfg.max_samples, cfg.train_count, cfg.heldout_count),
        indexed_scheduler=True,
        tick_feature_terminals=False,
        key_mode="prototype",
        shared_feature_atoms=True,
        shared_projection_atoms=True,
        include_grouped_cache_terminals=False,
        shared_atom_min_overlap=cfg.shared_atom_min_overlap,
        max_prototype_candidates_per_move=cfg.max_candidates_per_move,
        max_shared_atom_candidates_per_choice=cfg.max_shared_atom_candidates_per_choice,
        score_action_pattern_atoms=score_action_atoms,
    )


def _distribution(values: list[int]) -> dict[str, Any]:
    ordered = sorted(values)
    if not ordered:
        return {"count": 0, "min": 0, "p50": 0, "p90": 0, "max": 0}

    def percentile(fraction: float) -> int:
        index = min(len(ordered) - 1, int(round((len(ordered) - 1) * fraction)))
        return ordered[index]

    return {"count": len(ordered), "min": ordered[0], "p50": percentile(0.5), "p90": percentile(0.9), "max": ordered[-1]}


def _purity_boundary() -> dict[str, Any]:
    return {
        "native_recon_graph_execution": True,
        "shared_atoms_are_NodeType_TERMINAL": True,
        "actuator_affordances_are_NodeType_TERMINAL": True,
        "formal_recon_engine_runtime_choice": True,
        "utility_vote_uses_shared_terminal_node_state": True,
        "python_shared_atom_utility_vote_used_for_candidate_ordering": True,
        "soft_quorum_not_yet_materialized_as_recon_script": True,
        "soft_quorum_can_select_without_full_triplet_confirmation": True,
        "python_batch_scorer_used_for_runtime_choice": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "mate2_touched": False,
        "edge_fence_touched": False,
    }
