"""TG26s shared feature atom substrate checkpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from time import perf_counter
from typing import Any

import chess

from .foundation_curriculum import _generate_mate_in_one_positions
from .native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
    _evaluate_mate1_stage,
    _train_mate1_stage,
)


@dataclass(frozen=True)
class SharedFeatureAtomConfig:
    seed: int = 20260619
    train_count: int = 40
    heldout_count: int = 20
    max_generation_attempts: int = 500_000
    train_repetitions: int = 1
    max_ticks: int = 30
    max_samples: int = 16
    eta_m3: float = 0.10
    max_abs_local_weight: float = 1.0
    prototype_distance_threshold: int = 12
    max_candidates_per_move: int = 1
    max_shared_atom_candidates_per_choice: int = 6
    shared_atom_min_overlap: int = 6
    equivalence_count: int = 4


@dataclass(frozen=True)
class SharedFeatureAtomResult:
    config: SharedFeatureAtomConfig
    dataset: dict[str, Any]
    baseline_prototype: dict[str, Any]
    shared_atom: dict[str, Any]
    shared_projection: dict[str, Any]
    shared_projection_pruned: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26s_shared_feature_atoms.v0",
            "checkpoint": "TG26s_shared_feature_atom_substrate",
            "config": asdict(self.config),
            "runtime_purity_boundary": {
                "native_recon_graph_execution": True,
                "shared_atoms_are_NodeType_TERMINAL": True,
                "actuator_affordances_are_NodeType_TERMINAL": True,
                "formal_recon_engine_runtime_choice": True,
                "scheduler_indexing_is_optimization_only": True,
                "python_batch_scorer_used_for_runtime_choice": False,
                "action_ranker_used_for_runtime": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "stage_labels_learner_visible": False,
                "mate2_touched": False,
                "edge_fence_touched": False,
                "script_lag_or_ecological_spawning_added": False,
            },
            "dataset": self.dataset,
            "baseline_prototype": self.baseline_prototype,
            "shared_atom": self.shared_atom,
            "shared_projection": self.shared_projection,
            "shared_projection_pruned": self.shared_projection_pruned,
            "scheduler_equivalence": self.scheduler_equivalence,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_shared_feature_atom_experiment(
    *,
    config: SharedFeatureAtomConfig | None = None,
) -> SharedFeatureAtomResult:
    cfg = config or SharedFeatureAtomConfig()
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

    baseline = _run_arm("baseline_prototype", cfg, train_fens, heldout_fens)
    shared = _run_arm("shared_atom", cfg, train_fens, heldout_fens)
    projection = _run_arm("shared_projection", cfg, train_fens, heldout_fens)
    pruned = _run_arm("shared_projection_pruned", cfg, train_fens, heldout_fens)
    equivalence = _scheduler_equivalence(cfg, train_fens, heldout_fens)

    best_shared_accuracy = max(
        shared["heldout"]["accuracy"],
        projection["heldout"]["accuracy"],
        pruned["heldout"]["accuracy"],
    )
    baseline_nulls = baseline["null_selection_count"]
    best_shared_nulls = min(
        shared["null_selection_count"],
        projection["null_selection_count"],
        pruned["null_selection_count"],
    )
    checkpoint_pass = (
        shared["graph"]["shared_atom_count"] > 0
        and shared["graph"]["reused_atom_count"] > 0
        and best_shared_accuracy > baseline["heldout"]["accuracy"]
        and best_shared_nulls < baseline_nulls
        and equivalence["mismatch_count"] == 0
    )
    decision = {
        "checkpoint_pass": checkpoint_pass,
        "train_count": len(train_fens),
        "heldout_count": len(heldout_fens),
        "baseline_prototype_accuracy": baseline["heldout"]["accuracy"],
        "shared_atom_accuracy": shared["heldout"]["accuracy"],
        "shared_projection_accuracy": projection["heldout"]["accuracy"],
        "post_prune_accuracy": pruned["heldout"]["accuracy"],
        "null_selection_count_by_arm": {
            "baseline_prototype": baseline["null_selection_count"],
            "shared_atom": shared["null_selection_count"],
            "shared_projection": projection["null_selection_count"],
            "shared_projection_pruned": pruned["null_selection_count"],
        },
        "shared_atom_count": pruned["graph"]["shared_atom_count"],
        "triplet_local_feature_terminal_count": pruned["graph"]["triplet_local_feature_terminal_count"],
        "grouped_cache_terminal_count": pruned["graph"]["grouped_cache_terminal_count"],
        "reused_atom_count": pruned["graph"]["reused_atom_count"],
        "atom_activation_distribution": pruned["graph"]["shared_atom_stats"]["atom_activation_distribution"],
        "atom_confirmation_distribution": pruned["graph"]["shared_atom_stats"]["atom_confirmation_distribution"],
        "atom_false_positive_distribution": pruned["graph"]["shared_atom_stats"]["atom_false_positive_distribution"],
        "top_positive_atoms": pruned["graph"]["shared_atom_stats"]["top_positive_atoms"],
        "top_negative_atoms": pruned["graph"]["shared_atom_stats"]["top_negative_atoms"],
        "top_reused_atoms": pruned["graph"]["shared_atom_stats"]["top_reused_atoms"],
        "pruned_exact_terminal_count": pruned["graph"]["pruned_exact_terminal_count"],
        "pruned_triplet_count": pruned["graph"]["pruned_triplet_count"],
        "ablation_results": pruned["ablation_results"],
        "scheduler_equivalence_mismatch_count": equivalence["mismatch_count"],
        "runtime_purity_boundary": "clean",
        "next_step": (
            "continue shared-terminal generated Mate_In_1 scaling"
            if checkpoint_pass
            else "repair shared-terminal retrieval/credit before Mate_In_2"
        ),
    }
    return SharedFeatureAtomResult(
        config=cfg,
        dataset={
            "source": "generated legal KRK Mate_In_1 positions",
            "train_count": len(train_fens),
            "heldout_count": len(heldout_fens),
            "curriculum_labels_learner_visible": False,
        },
        baseline_prototype=baseline,
        shared_atom=shared,
        shared_projection=projection,
        shared_projection_pruned=pruned,
        scheduler_equivalence=equivalence,
        decision=decision,
    )


def _run_arm(
    arm: str,
    cfg: SharedFeatureAtomConfig,
    train_fens: tuple[str, ...],
    heldout_fens: tuple[str, ...],
) -> dict[str, Any]:
    shared = arm in {"shared_atom", "shared_projection", "shared_projection_pruned"}
    projections = arm in {"shared_projection", "shared_projection_pruned"}
    native_cfg = NativeSingleGraphConfig(
        train_repetitions=cfg.train_repetitions,
        eta_m3=cfg.eta_m3,
        max_abs_local_weight=cfg.max_abs_local_weight,
        max_ticks=cfg.max_ticks,
        max_samples=max(cfg.max_samples, len(train_fens), len(heldout_fens)),
        indexed_scheduler=True,
        tick_feature_terminals=False,
        key_mode="prototype",
        prototype_distance_threshold=cfg.prototype_distance_threshold,
        max_prototype_candidates_per_move=cfg.max_candidates_per_move,
        max_shared_atom_candidates_per_choice=cfg.max_shared_atom_candidates_per_choice,
        shared_feature_atoms=shared,
        shared_projection_atoms=projections,
        include_grouped_cache_terminals=not shared,
        shared_atom_min_overlap=cfg.shared_atom_min_overlap,
    )
    graph = NativeReConKRKGraph(config=native_cfg)
    started = perf_counter()
    training = _train_mate1_stage(graph, train_fens, config=native_cfg)
    training["duration_seconds"] = round(perf_counter() - started, 6)
    before_prune = _evaluate_mate1_stage(graph, train_fens, config=native_cfg)
    prune_result = None
    if arm == "shared_projection_pruned":
        prune_result = graph.apply_shared_atom_pruning()
    started = perf_counter()
    heldout = _evaluate_mate1_stage(graph, heldout_fens, config=native_cfg)
    heldout["duration_seconds"] = round(perf_counter() - started, 6)
    graph_diag = graph.graph_diagnostics()
    return {
        "arm": arm,
        "shared_feature_atoms": shared,
        "shared_projection_atoms": projections,
        "grouped_cache_terminals_enabled": not shared,
        "training": training,
        "train_replay_before_prune": before_prune,
        "prune_result": prune_result,
        "heldout": heldout,
        "null_selection_count": _null_count(heldout),
        "graph": graph_diag,
        "ablation_results": {
            "train_replay_accuracy_before_prune": before_prune["accuracy"],
            "pruning_applied": prune_result is not None,
            "pruned_shared_atom_count": 0 if prune_result is None else prune_result["pruned_shared_atom_count"],
            "pruned_exact_terminal_count": 0 if prune_result is None else prune_result["pruned_exact_terminal_count"],
            "pruned_triplet_count": 0 if prune_result is None else prune_result["pruned_triplet_count"],
            "heldout_accuracy_after_prune": heldout["accuracy"],
        },
    }


def _null_count(metrics: dict[str, Any]) -> int:
    return sum(1 for row in metrics.get("samples", []) if row.get("selected") is None)


def _scheduler_equivalence(
    cfg: SharedFeatureAtomConfig,
    train_fens: tuple[str, ...],
    heldout_fens: tuple[str, ...],
) -> dict[str, Any]:
    base_cfg = NativeSingleGraphConfig(
        train_repetitions=cfg.train_repetitions,
        eta_m3=cfg.eta_m3,
        max_abs_local_weight=cfg.max_abs_local_weight,
        max_ticks=cfg.max_ticks,
        max_samples=max(cfg.max_samples, len(train_fens), len(heldout_fens)),
        indexed_scheduler=True,
        tick_feature_terminals=False,
        key_mode="prototype",
        shared_feature_atoms=True,
        shared_projection_atoms=True,
        include_grouped_cache_terminals=False,
        shared_atom_min_overlap=cfg.shared_atom_min_overlap,
        max_prototype_candidates_per_move=cfg.max_candidates_per_move,
        max_shared_atom_candidates_per_choice=cfg.max_shared_atom_candidates_per_choice,
    )
    full_cfg = NativeSingleGraphConfig(
        **{**asdict(base_cfg), "tick_feature_terminals": True}
    )
    grouped = NativeReConKRKGraph(config=base_cfg)
    full = NativeReConKRKGraph(config=full_cfg)
    _train_mate1_stage(grouped, train_fens, config=base_cfg)
    _train_mate1_stage(full, train_fens, config=full_cfg)
    rows: list[dict[str, Any]] = []
    for fen in heldout_fens[: cfg.equivalence_count]:
        board = chess.Board(fen)
        grouped_audit = grouped.audit_choice(board)
        full_audit = full.audit_choice(board)
        rows.append({
            "fen": fen,
            "grouped_selected": grouped_audit.get("selected_move"),
            "full_selected": full_audit.get("selected_move"),
            "selected_match": grouped_audit.get("selected_move") == full_audit.get("selected_move"),
            "grouped_confirmed_count": grouped_audit.get("confirmed_candidate_count", 0),
            "full_confirmed_count": full_audit.get("confirmed_candidate_count", 0),
        })
    return {
        "source": "shared_atom_tick_feature_terminal_false_vs_true",
        "mismatch_count": sum(1 for row in rows if not row["selected_match"]),
        "samples": rows,
    }
