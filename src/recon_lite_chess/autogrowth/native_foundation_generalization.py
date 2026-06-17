"""TG26r native foundation generalization repair."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

import chess

from .foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _generate_forced_mate_in_two_positions,
    _generate_mate_in_one_positions,
    _mate_moves,
)
from .native_scheduler_replay_audit import _scheduler_equivalence_audit
from .native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
    _evaluate_mate1_stage,
    _evaluate_mate2_stage,
    _train_mate1_stage,
    _train_mate2_stage,
    _TripletNodeIds,
    _triplet_id,
    _triplet_keys,
)


@dataclass(frozen=True)
class NativeFoundationGeneralizationConfig:
    seed: int = 20260618
    mate1_train_count: int = 120
    mate1_heldout_count: int = 40
    mate2_train_count: int = 60
    mate2_heldout_count: int = 20
    max_generation_attempts: int = 500_000
    train_repetitions: int = 2
    continuation_repetitions: int = 1
    max_ticks: int = 80
    max_samples: int = 16
    eta_m3: float = 0.10
    max_abs_local_weight: float = 1.0
    mature_min_abs_weight: float = 0.20
    prototype_distance_threshold: int = 12
    max_prototype_candidates_per_move: int = 3
    max_prototype_scan_triplets: int = 256
    equivalence_mate1_count: int = 3
    equivalence_mate2_count: int = 2


@dataclass(frozen=True)
class NativeFoundationGeneralizationResult:
    config: NativeFoundationGeneralizationConfig
    dataset: dict[str, Any]
    exact_arm: dict[str, Any]
    prototype_arm: dict[str, Any]
    canonical_arm: dict[str, Any]
    exact_vs_prototype_comparison: dict[str, Any]
    raw_vs_canonical_comparison: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    m4_audit: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26r_native_foundation_generalization.v0",
            "checkpoint": "TG26r_native_foundation_generalization_repair",
            "config": asdict(self.config),
            "purity_boundary": {
                "native_recon_graph_execution": True,
                "actuator_affordances_are_NodeType_TERMINAL": True,
                "formal_recon_engine_runtime_choice": True,
                "python_batch_scorer_used_for_runtime_choice": False,
                "action_ranker_used_for_runtime": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "stage_labels_learner_visible": False,
                "edge_fence_touched": False,
                "script_lag_or_ecological_spawning_added": False,
            },
            "dataset": self.dataset,
            "exact_arm": self.exact_arm,
            "prototype_arm": self.prototype_arm,
            "canonical_arm": self.canonical_arm,
            "exact_vs_prototype_comparison": self.exact_vs_prototype_comparison,
            "raw_vs_canonical_comparison": self.raw_vs_canonical_comparison,
            "scheduler_equivalence": self.scheduler_equivalence,
            "m4_audit": self.m4_audit,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_native_foundation_generalization(
    *,
    config: NativeFoundationGeneralizationConfig | None = None,
) -> NativeFoundationGeneralizationResult:
    cfg = config or NativeFoundationGeneralizationConfig()
    mate1_train = tuple(_generate_mate_in_one_positions(
        count=cfg.mate1_train_count,
        seed=cfg.seed,
        max_attempts=cfg.max_generation_attempts,
    ))
    used = set(mate1_train)
    mate1_heldout = tuple(_generate_mate_in_one_positions(
        count=cfg.mate1_heldout_count,
        seed=cfg.seed + 1,
        excluded=used,
        max_attempts=cfg.max_generation_attempts,
    ))
    used.update(mate1_heldout)
    mate2_train = tuple(_generate_forced_mate_in_two_positions(
        count=cfg.mate2_train_count,
        seed=cfg.seed + 2,
        excluded=used,
        max_attempts=cfg.max_generation_attempts,
    ))
    used.update(mate2_train)
    mate2_heldout = tuple(_generate_forced_mate_in_two_positions(
        count=cfg.mate2_heldout_count,
        seed=cfg.seed + 3,
        excluded=used,
        max_attempts=cfg.max_generation_attempts,
    ))

    exact = _run_generated_arm("exact", cfg, mate1_train, mate1_heldout, mate2_train, mate2_heldout)
    prototype = _run_generated_arm("prototype", cfg, mate1_train, mate1_heldout, mate2_train, mate2_heldout)
    canonical = _run_generated_arm("canonical", cfg, mate1_train, mate1_heldout, mate2_train, mate2_heldout)
    scheduler_equivalence = _expanded_scheduler_equivalence(cfg, mate1_train, mate2_train)
    exact_vs_prototype = _arm_comparison(exact, prototype)
    raw_vs_canonical = _arm_comparison(prototype, canonical)
    best_arm = max((exact, prototype, canonical), key=lambda arm: (
        arm["mate2"]["heldout"]["conversion_rate"],
        arm["mate1"]["heldout"]["accuracy"],
    ))
    m4_audit = {
        "m4_requires_heldout_confirmation_under_frozen_m3": True,
        "m4_true_promotion_count": 0,
        "mature_materialized_count": best_arm["graph_diagnostics"]["tier_counts"].get("mature", 0),
        "reason": "TG26r does not promote generated structures because heldout thresholds are not yet met.",
    }
    decision = {
        "checkpoint_pass": (
            best_arm["mate1"]["heldout"]["accuracy"] >= 0.90
            and best_arm["mate2"]["heldout"]["conversion_rate"] >= 0.75
            and best_arm["null_selection_count"] < exact["null_selection_count"]
            and scheduler_equivalence["mismatch_count"] == 0
        ),
        "best_arm": best_arm["key_mode"],
        "generated_mate1_train_count": len(mate1_train),
        "generated_mate1_heldout_accuracy": best_arm["mate1"]["heldout"]["accuracy"],
        "generated_mate2_train_count": len(mate2_train),
        "generated_mate2_heldout_conversion": best_arm["mate2"]["heldout"]["conversion_rate"],
        "null_selection_count": best_arm["null_selection_count"],
        "nearest_triplet_diagnostics": best_arm["nearest_triplet_diagnostics"][: cfg.max_samples],
        "exact_vs_prototype_comparison": exact_vs_prototype,
        "raw_vs_canonical_comparison": raw_vs_canonical,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "m4_true_promotion_count": m4_audit["m4_true_promotion_count"],
        "mature_materialized_count": m4_audit["mature_materialized_count"],
        "next_step": (
            "TG26r passes generated foundation; rerun larger heldout before edge/fence."
            if best_arm["mate1"]["heldout"]["accuracy"] >= 0.90
            and best_arm["mate2"]["heldout"]["conversion_rate"] >= 0.75
            and scheduler_equivalence["mismatch_count"] == 0
            else "Continue native foundation generalization repair; do not return to edge/fence."
        ),
    }
    return NativeFoundationGeneralizationResult(
        config=cfg,
        dataset={
            "source": "generated legal KRK mate-in-1 and forced mate-in-2 positions",
            "mate1_train_count": len(mate1_train),
            "mate1_heldout_count": len(mate1_heldout),
            "mate2_train_count": len(mate2_train),
            "mate2_heldout_count": len(mate2_heldout),
            "curriculum_labels_learner_visible": False,
        },
        exact_arm=exact,
        prototype_arm=prototype,
        canonical_arm=canonical,
        exact_vs_prototype_comparison=exact_vs_prototype,
        raw_vs_canonical_comparison=raw_vs_canonical,
        scheduler_equivalence=scheduler_equivalence,
        m4_audit=m4_audit,
        decision=decision,
    )


def _run_generated_arm(
    key_mode: str,
    cfg: NativeFoundationGeneralizationConfig,
    mate1_train: tuple[str, ...],
    mate1_heldout: tuple[str, ...],
    mate2_train: tuple[str, ...],
    mate2_heldout: tuple[str, ...],
) -> dict[str, Any]:
    native_cfg = NativeSingleGraphConfig(
        train_repetitions=cfg.train_repetitions,
        continuation_repetitions=cfg.continuation_repetitions,
        eta_m3=cfg.eta_m3,
        max_abs_local_weight=cfg.max_abs_local_weight,
        mature_min_abs_weight=cfg.mature_min_abs_weight,
        max_ticks=cfg.max_ticks,
        max_samples=cfg.max_samples,
        indexed_scheduler=True,
        tick_feature_terminals=False,
        key_mode=key_mode,
        prototype_distance_threshold=cfg.prototype_distance_threshold,
        max_prototype_candidates_per_move=cfg.max_prototype_candidates_per_move,
        max_prototype_scan_triplets=cfg.max_prototype_scan_triplets,
    )
    graph = NativeReConKRKGraph(config=native_cfg)
    started = perf_counter()
    mate1_train_metrics = _train_mate1_stage(graph, mate1_train, config=native_cfg)
    mate1_train_metrics["duration_seconds"] = round(perf_counter() - started, 6)
    started = perf_counter()
    mate1_heldout_metrics = _evaluate_mate1_stage(graph, mate1_heldout, config=native_cfg)
    mate1_heldout_metrics["duration_seconds"] = round(perf_counter() - started, 6)
    started = perf_counter()
    mate2_train_metrics = _train_mate2_stage(graph, mate2_train, config=native_cfg)
    mate2_train_metrics["duration_seconds"] = round(perf_counter() - started, 6)
    started = perf_counter()
    mate2_heldout_metrics = _evaluate_mate2_stage(graph, mate2_heldout, config=native_cfg)
    mate2_heldout_metrics["duration_seconds"] = round(perf_counter() - started, 6)
    null_diagnostics = _null_selection_diagnostics(graph, key_mode, mate1_heldout, mate2_heldout, cfg.max_samples)
    graph_diag = graph.graph_diagnostics()
    return {
        "key_mode": key_mode,
        "generated_mate1_train_count": len(mate1_train),
        "generated_mate2_train_count": len(mate2_train),
        "mate1": {"training": mate1_train_metrics, "heldout": mate1_heldout_metrics},
        "mate2": {"training": mate2_train_metrics, "heldout": mate2_heldout_metrics},
        "null_selection_count": null_diagnostics["null_selection_count"],
        "nearest_triplet_diagnostics": null_diagnostics["rows"],
        "graph_diagnostics": graph_diag,
        "runtime": {
            "formal_recon_engine_runtime_choice": True,
            "actuator_affordances_are_terminal_leaves": True,
            "python_batch_scorer_used_for_runtime_choice": False,
        },
    }


def _arm_comparison(baseline: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    return {
        "baseline_key_mode": baseline["key_mode"],
        "variant_key_mode": variant["key_mode"],
        "mate1_accuracy_delta": round(
            float(variant["mate1"]["heldout"]["accuracy"]) - float(baseline["mate1"]["heldout"]["accuracy"]),
            6,
        ),
        "mate2_conversion_delta": round(
            float(variant["mate2"]["heldout"]["conversion_rate"]) - float(baseline["mate2"]["heldout"]["conversion_rate"]),
            6,
        ),
        "null_selection_delta": int(variant["null_selection_count"]) - int(baseline["null_selection_count"]),
        "prototype_distance_evaluation_delta": int(
            variant["graph_diagnostics"]["scheduler_stats"].get("prototype_distance_evaluations", 0)
        )
        - int(baseline["graph_diagnostics"]["scheduler_stats"].get("prototype_distance_evaluations", 0)),
        "interpretation": (
            "variant improves heldout or reduces nulls"
            if (
                float(variant["mate1"]["heldout"]["accuracy"]) > float(baseline["mate1"]["heldout"]["accuracy"])
                or float(variant["mate2"]["heldout"]["conversion_rate"])
                > float(baseline["mate2"]["heldout"]["conversion_rate"])
                or int(variant["null_selection_count"]) < int(baseline["null_selection_count"])
            )
            else "no measured variant improvement"
        ),
    }


def _null_selection_diagnostics(
    graph: NativeReConKRKGraph,
    key_mode: str,
    mate1_fens: Iterable[str],
    mate2_fens: Iterable[str],
    max_samples: int,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for fen in mate1_fens:
        board = chess.Board(fen)
        audit = graph.audit_choice(board)
        if audit.get("selected_move") is not None and len(rows) >= max_samples:
            continue
        mates = _mate_moves(board)
        target = mates[0] if mates else None
        rows.append(_failure_row(graph, key_mode, board, target, "generated_mate1", audit))
    for fen in mate2_fens:
        board = chess.Board(fen)
        audit = graph.audit_choice(board)
        if audit.get("selected_move") is not None and len(rows) >= max_samples:
            continue
        forced = _forced_mate_in_two_first_moves(board)
        target = forced[0] if forced else None
        rows.append(_failure_row(graph, key_mode, board, target, "generated_mate2_first", audit))
    null_count = sum(1 for row in rows if row["selected_move"] is None)
    return {"null_selection_count": null_count, "rows": rows[:max_samples]}


def _failure_row(
    graph: NativeReConKRKGraph,
    key_mode: str,
    board: chess.Board,
    target: chess.Move | None,
    kind: str,
    audit: dict[str, Any],
) -> dict[str, Any]:
    if target is None:
        return {
            "kind": kind,
            "fen": board.fen(),
            "target_move": None,
            "selected_move": audit.get("selected_move"),
            "reason": "no_target_move",
        }
    before, delta, after = _triplet_keys(board, target, key_mode=key_mode)
    triplet_id = _triplet_id(before, delta, after)
    candidate_indexed = triplet_id in graph.triplet_ids
    nearest = _nearest_triplet(graph, before, delta, after)
    return {
        "kind": kind,
        "fen": board.fen(),
        "target_move": target.uci(),
        "selected_move": audit.get("selected_move"),
        "correct_target_candidate_triplet": triplet_id,
        "any_triplet_candidate_indexed": audit.get("candidate_triplet_count", 0) > 0,
        "correct_triplet_indexed": candidate_indexed,
        "before_terminal_matched": candidate_indexed,
        "action_terminal_matched": candidate_indexed and target in board.legal_moves,
        "after_terminal_blocked": not candidate_indexed,
        "scheduler_returned_empty_candidate_set": audit.get("candidate_triplet_count", 0) == 0,
        "scheduler_active_set_excluded_useful_nodes": False if not candidate_indexed else audit.get("confirmed_candidate_count", 0) == 0,
        "failure_bucket": (
            "no_candidate_indexed"
            if audit.get("candidate_triplet_count", 0) == 0
            else "candidate_indexed_but_no_confirmation"
            if audit.get("confirmed_candidate_count", 0) == 0
            else "candidate_confirmed_but_wrong_selection"
        ),
        "nearest_matching_triplet": nearest,
    }


def _nearest_triplet(
    graph: NativeReConKRKGraph,
    before: tuple[str, ...],
    delta: tuple[str, ...],
    after: tuple[str, ...],
) -> dict[str, Any]:
    target = set((*before, *delta, *after))
    best: tuple[int, str, set[str]] | None = None
    for triplet_id in graph.triplet_ids:
        ids = _TripletNodeIds(triplet_id)
        keys = set(graph.graph.nodes[ids.before_terminal].meta.get("pattern_keys", []))
        keys.update(graph.graph.nodes[ids.delta_terminal].meta.get("pattern_keys", []))
        keys.update(graph.graph.nodes[ids.after_terminal].meta.get("pattern_keys", []))
        distance = len(target ^ keys)
        if best is None or distance < best[0]:
            best = (distance, triplet_id, keys)
    if best is None:
        return {"triplet_id": None, "feature_distance": None}
    missing = sorted(target - best[2])
    extra = sorted(best[2] - target)
    absolute_mismatches = [
        key for key in [*missing, *extra]
        if any(part in key for part in ("_file", "_rank", "native_action_exact"))
    ]
    node = graph.graph.nodes[best[1]]
    return {
        "triplet_id": best[1],
        "feature_distance": best[0],
        "tier": node.meta.get("tier", "trial"),
        "missing_feature_keys": missing[:24],
        "extra_feature_keys": extra[:24],
        "absolute_coordinate_mismatch_count": len(absolute_mismatches),
    }


def _expanded_scheduler_equivalence(
    cfg: NativeFoundationGeneralizationConfig,
    mate1_train: tuple[str, ...],
    mate2_train: tuple[str, ...],
) -> dict[str, Any]:
    # Reuse the TG26q equivalence machinery on generated positions. It compares
    # full feature-terminal ticking against the indexed/grouped scheduler.
    from .native_scheduler_replay_audit import NativeSchedulerReplayAuditConfig

    audit_cfg = NativeSchedulerReplayAuditConfig(
        replay_repetitions=1,
        include_symmetries=False,
        max_ticks=cfg.max_ticks,
        generated_mate1_heldout_count=0,
        generated_mate2_heldout_count=0,
        equivalence_mate1_positions=min(cfg.equivalence_mate1_count, len(mate1_train)),
        equivalence_mate2_positions=min(cfg.equivalence_mate2_count, len(mate2_train)),
        max_samples=cfg.max_samples,
    )
    # The reused helper expects curated-shaped tuples; generated positions are
    # acceptable because it only trains/evaluates native graph behavior.
    result = _scheduler_equivalence_audit(audit_cfg, mate1_train, mate2_train)
    result["source"] = "generated_mate1_and_mate2_subset"
    return result
