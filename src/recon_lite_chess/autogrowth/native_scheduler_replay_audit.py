"""TG26q replay, heldout, equivalence, and ablation audit for TG26p."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

import chess

from .curated_replay_curriculum import _mate2_buckets
from .curated_terminal_curriculum import curated_stage_entries
from .foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _generate_forced_mate_in_two_positions,
    _generate_mate_in_one_positions,
    _mate_moves,
    _move_reward,
)
from .native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
    _evaluate_mate1_stage,
    _evaluate_mate2_stage,
    _train_mate1_stage,
    _train_mate2_stage,
    _unique,
)


@dataclass(frozen=True)
class NativeSchedulerReplayAuditConfig:
    seed: int = 20260617
    replay_repetitions: int = 50
    include_symmetries: bool = True
    max_ticks: int = 80
    eta_m3: float = 0.10
    max_abs_local_weight: float = 1.0
    mature_min_abs_weight: float = 0.20
    generated_mate1_heldout_count: int = 12
    generated_mate2_heldout_count: int = 6
    max_generation_attempts: int = 500_000
    equivalence_mate1_positions: int = 1
    equivalence_mate2_positions: int = 1
    max_samples: int = 16
    prune_weight_threshold: float = -0.20


@dataclass(frozen=True)
class NativeSchedulerReplayAuditResult:
    config: NativeSchedulerReplayAuditConfig
    dataset: dict[str, Any]
    replay: dict[str, Any]
    generated_heldout: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    ablations: dict[str, Any]
    graph_diagnostics: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26q_native_scheduler_replay_audit.v0",
            "checkpoint": "TG26q_native_scheduler_replay_heldout_equivalence_audit",
            "config": asdict(self.config),
            "purity_boundary": {
                "native_recon_graph_execution": True,
                "same_persistent_graph_replayed": True,
                "actuator_affordances_are_NodeType_TERMINAL": True,
                "stage_labels_learner_visible": False,
                "direct_provider_override": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "scheduler_equivalence_mismatches_reported": True,
                "ablations_are_audit_interventions_only": True,
                "edge_fence_structures_m4_consolidated": False,
            },
            "dataset": self.dataset,
            "replay": self.replay,
            "generated_heldout": self.generated_heldout,
            "scheduler_equivalence": self.scheduler_equivalence,
            "ablations": self.ablations,
            "graph_diagnostics": self.graph_diagnostics,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_native_scheduler_replay_audit(
    *,
    config: NativeSchedulerReplayAuditConfig | None = None,
) -> NativeSchedulerReplayAuditResult:
    cfg = config or NativeSchedulerReplayAuditConfig()
    native_cfg = NativeSingleGraphConfig(
        include_symmetries=cfg.include_symmetries,
        train_repetitions=1,
        continuation_repetitions=1,
        eta_m3=cfg.eta_m3,
        max_abs_local_weight=cfg.max_abs_local_weight,
        mature_min_abs_weight=cfg.mature_min_abs_weight,
        max_ticks=cfg.max_ticks,
        max_samples=cfg.max_samples,
        indexed_scheduler=True,
        tick_feature_terminals=False,
    )
    mate1_fens, mate2_fens = _curated_foundation_fens(include_symmetries=cfg.include_symmetries)
    graph = NativeReConKRKGraph(config=native_cfg)

    replay_started = perf_counter()
    replay_rows: list[dict[str, Any]] = []
    for repetition in range(1, cfg.replay_repetitions + 1):
        before_m3 = graph.m3_update_count
        before_m4 = graph.m4_event_count
        _train_mate1_stage(graph, mate1_fens, config=native_cfg)
        mate1_eval = _evaluate_mate1_stage(graph, mate1_fens, config=native_cfg)
        maturation = graph.mature_existing_graph()
        _train_mate2_stage(graph, mate2_fens, config=native_cfg)
        mate2_eval = _evaluate_mate2_stage(graph, mate2_fens, config=native_cfg)
        if mate2_eval["conversion_rate"] >= native_cfg.mate2_threshold:
            graph.m4_event_count += 1
        diagnostics = graph.graph_diagnostics(prune_weight_threshold=cfg.prune_weight_threshold)
        replay_rows.append({
            "repetition": repetition,
            "mate1_correct": mate1_eval["correct_count"],
            "mate1_total": mate1_eval["position_count"],
            "mate1_accuracy": mate1_eval["accuracy"],
            "mate2_conversions": mate2_eval["conversion_count"],
            "mate2_total": mate2_eval["position_count"],
            "mate2_conversion_rate": mate2_eval["conversion_rate"],
            "same_graph_second_move_count": mate2_eval["same_graph_second_move_count"],
            "m3_update_delta": graph.m3_update_count - before_m3,
            "m3_update_total": graph.m3_update_count,
            "m4_event_delta": graph.m4_event_count - before_m4,
            "m4_event_total": graph.m4_event_count,
            "node_count": len(graph.graph.nodes),
            "edge_count": len(graph.graph.edges),
            "triplet_count": len(graph.triplet_ids),
            "mature_node_count": diagnostics["tier_counts"].get("mature", 0),
            "trial_node_count": diagnostics["tier_counts"].get("trial", 0),
            "dead_node_count": diagnostics["dead_node_count"],
            "weight_saturation": diagnostics["weight_saturation"],
            "collapse_indicators": diagnostics["collapse_indicators"],
        })
    replay = {
        "duration_seconds": round(perf_counter() - replay_started, 6),
        "repetition_count": len(replay_rows),
        "rows": replay_rows,
        "final": replay_rows[-1] if replay_rows else {},
        "all_mate1_passed": all(row["mate1_correct"] == row["mate1_total"] for row in replay_rows),
        "all_mate2_passed": all(row["mate2_conversions"] == row["mate2_total"] for row in replay_rows),
    }

    generated_heldout = _generated_heldout_eval(graph, cfg, native_cfg, excluded=set((*mate1_fens, *mate2_fens)))
    scheduler_equivalence = _scheduler_equivalence_audit(cfg, mate1_fens, mate2_fens)
    ablations = _ablation_audit(graph, mate1_fens, mate2_fens, native_cfg, cfg)
    graph_diagnostics = graph.graph_diagnostics(prune_weight_threshold=cfg.prune_weight_threshold)
    post_prune = _post_prune_eval(graph, graph_diagnostics["prune_candidate_triplets"], mate1_fens, mate2_fens, native_cfg)
    graph_diagnostics["post_prune_replay_accuracy"] = post_prune

    checkpoint_pass = (
        replay["all_mate1_passed"]
        and replay["all_mate2_passed"]
        and generated_heldout["mate1"]["accuracy"] >= 0.95
        and generated_heldout["mate2"]["conversion_rate"] >= 0.90
        and scheduler_equivalence["mismatch_count"] == 0
        and ablations["mate_terminal_mask"]["mate2_second_moves_collapsed"]
        and ablations["mate2_first_move_mask"]["first_moves_collapsed"]
    )
    decision = {
        "checkpoint_pass": checkpoint_pass,
        "replay_all_mate1_passed": replay["all_mate1_passed"],
        "replay_all_mate2_passed": replay["all_mate2_passed"],
        "generated_mate1_accuracy": generated_heldout["mate1"]["accuracy"],
        "generated_mate2_conversion_rate": generated_heldout["mate2"]["conversion_rate"],
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "mate_terminal_mask_collapsed_second_moves": ablations["mate_terminal_mask"]["mate2_second_moves_collapsed"],
        "mate2_first_move_mask_collapsed_first_moves": ablations["mate2_first_move_mask"]["first_moves_collapsed"],
        "next_step": (
            "TG26q passes; consider carefully scoped edge/fence only after reviewing scheduler shortcut."
            if checkpoint_pass
            else "Repair native foundation stability/equivalence/heldout before edge/fence."
        ),
    }

    return NativeSchedulerReplayAuditResult(
        config=cfg,
        dataset={
            "curated_source": "src/recon_lite_chess/training/krk_curriculum.py::KRK_STAGES",
            "include_symmetries": cfg.include_symmetries,
            "curated_mate1_count": len(mate1_fens),
            "curated_mate2_count": len(mate2_fens),
            "generated_source": "src/recon_lite_chess/autogrowth/foundation_curriculum.py random legal KRK generators",
        },
        replay=replay,
        generated_heldout=generated_heldout,
        scheduler_equivalence=scheduler_equivalence,
        ablations=ablations,
        graph_diagnostics=graph_diagnostics,
        decision=decision,
    )


def _curated_foundation_fens(*, include_symmetries: bool) -> tuple[tuple[str, ...], tuple[str, ...]]:
    entries = curated_stage_entries(include_symmetries=include_symmetries)
    mate1_fens = _unique(
        entry.fen
        for entry in entries
        if entry.stage_name == "Mate_In_1" and entry.mate_in_one_moves
    )
    buckets = _mate2_buckets(entries)
    mate2_fens = _unique(fen for bucket in buckets for fen in bucket["fens"])
    return mate1_fens, mate2_fens


def _generated_heldout_eval(
    graph: NativeReConKRKGraph,
    cfg: NativeSchedulerReplayAuditConfig,
    native_cfg: NativeSingleGraphConfig,
    *,
    excluded: set[str],
) -> dict[str, Any]:
    mate1 = tuple(_generate_mate_in_one_positions(
        count=cfg.generated_mate1_heldout_count,
        seed=cfg.seed + 101,
        excluded=excluded,
        max_attempts=cfg.max_generation_attempts,
    ))
    used = set((*excluded, *mate1))
    mate2 = tuple(_generate_forced_mate_in_two_positions(
        count=cfg.generated_mate2_heldout_count,
        seed=cfg.seed + 202,
        excluded=used,
        max_attempts=cfg.max_generation_attempts,
    ))
    started = perf_counter()
    mate1_eval = _evaluate_mate1_stage(graph, mate1, config=native_cfg)
    mate1_eval["duration_seconds"] = round(perf_counter() - started, 6)
    started = perf_counter()
    mate2_eval = _evaluate_mate2_stage(graph, mate2, config=native_cfg)
    mate2_eval["duration_seconds"] = round(perf_counter() - started, 6)
    return {
        "stage_labels_learner_visible": False,
        "mate1_fens": mate1,
        "mate2_fens": mate2,
        "mate1": mate1_eval,
        "mate2": mate2_eval,
    }


def _scheduler_equivalence_audit(
    cfg: NativeSchedulerReplayAuditConfig,
    mate1_fens: tuple[str, ...],
    mate2_fens: tuple[str, ...],
) -> dict[str, Any]:
    subset_mate1 = mate1_fens[: cfg.equivalence_mate1_positions]
    subset_mate2 = mate2_fens[: cfg.equivalence_mate2_positions]
    rows: list[dict[str, Any]] = []
    grouped_cfg = NativeSingleGraphConfig(
        include_symmetries=False,
        train_repetitions=1,
        continuation_repetitions=1,
        max_ticks=cfg.max_ticks,
        max_samples=cfg.max_samples,
        indexed_scheduler=True,
        tick_feature_terminals=False,
    )
    full_cfg = NativeSingleGraphConfig(
        include_symmetries=False,
        train_repetitions=1,
        continuation_repetitions=1,
        max_ticks=cfg.max_ticks,
        max_samples=cfg.max_samples,
        indexed_scheduler=True,
        tick_feature_terminals=True,
    )
    grouped = NativeReConKRKGraph(config=grouped_cfg)
    full = NativeReConKRKGraph(config=full_cfg)
    for graph in (grouped, full):
        for _ in range(2):
            _train_mate1_stage(graph, subset_mate1, config=grouped_cfg)
        graph.mature_existing_graph()
        for _ in range(2):
            _train_mate2_stage(graph, subset_mate2, config=grouped_cfg)
    boards = [chess.Board(fen) for fen in subset_mate1]
    for fen in subset_mate2:
        board = chess.Board(fen)
        boards.append(board)
        forced = _forced_mate_in_two_first_moves(board)
        if forced:
            after_first = board.copy(stack=False)
            after_first.push(forced[0])
            reply = next(iter(sorted(after_first.legal_moves, key=lambda item: item.uci())), None)
            if reply is not None:
                after_reply = after_first.copy(stack=False)
                after_reply.push(reply)
                boards.append(after_reply)
    for board in boards:
        grouped_audit = grouped.audit_choice(board)
        full_audit = full.audit_choice(board)
        grouped_confirmed = [(row["move"], row["triplet_id"]) for row in grouped_audit["confirmed_candidates"]]
        full_confirmed = [(row["move"], row["triplet_id"]) for row in full_audit["confirmed_candidates"]]
        rows.append({
            "fen": board.fen(),
            "grouped_selected": grouped_audit.get("selected_move"),
            "full_feature_selected": full_audit.get("selected_move"),
            "selected_match": grouped_audit.get("selected_move") == full_audit.get("selected_move"),
            "grouped_confirmed_count": grouped_audit.get("confirmed_candidate_count"),
            "full_feature_confirmed_count": full_audit.get("confirmed_candidate_count"),
            "confirmed_candidates_match": grouped_confirmed == full_confirmed,
            "grouped_confirmed": grouped_confirmed[:8],
            "full_feature_confirmed": full_confirmed[:8],
        })
    mismatches = [
        row for row in rows if not row["selected_match"] or not row["confirmed_candidates_match"]
    ]
    return {
        "tiny_subset_only": True,
        "full_feature_terminal_ticking": True,
        "grouped_scheduler_ticks_feature_terminals": False,
        "position_count": len(rows),
        "mismatch_count": len(mismatches),
        "rows": rows,
        "mismatches": mismatches,
    }


def _ablation_audit(
    graph: NativeReConKRKGraph,
    mate1_fens: tuple[str, ...],
    mate2_fens: tuple[str, ...],
    native_cfg: NativeSingleGraphConfig,
    cfg: NativeSchedulerReplayAuditConfig,
) -> dict[str, Any]:
    baseline_mate2 = _evaluate_mate2_stage(graph, mate2_fens, config=native_cfg)
    mate1_original = graph.triplets_by_stage(lambda stage: stage == "Mate_In_1")
    mate_terminal = graph.triplets_by_stage(lambda stage: stage in {"Mate_In_1", "Mate_In_2_continuation_experience"})
    mate2_first = graph.triplets_by_stage(lambda stage: stage == "Mate_In_2_first_move")
    mate1_original_eval = _evaluate_mate2_with_mask(graph, mate2_fens, mate1_original, max_samples=cfg.max_samples)
    mate_terminal_eval = _evaluate_mate2_with_mask(graph, mate2_fens, mate_terminal, max_samples=cfg.max_samples)
    mate2_first_eval = _evaluate_mate2_with_mask(graph, mate2_fens, mate2_first, max_samples=cfg.max_samples)
    return {
        "baseline": {
            "mate2_conversion_count": baseline_mate2["conversion_count"],
            "mate2_total": baseline_mate2["position_count"],
            "same_graph_second_move_count": baseline_mate2["same_graph_second_move_count"],
        },
        "mate1_original_only_mask": {
            "masked_triplet_count": len(mate1_original),
            **mate1_original_eval,
            "interpretation": "If this does not collapse second moves, continuation-experience mate structures are carrying the mate-after-reply behavior.",
        },
        "mate_terminal_mask": {
            "masked_triplet_count": len(mate_terminal),
            **mate_terminal_eval,
            "mate2_second_moves_collapsed": mate_terminal_eval["same_graph_second_move_count"] < baseline_mate2["same_graph_second_move_count"],
        },
        "mate2_first_move_mask": {
            "masked_triplet_count": len(mate2_first),
            **mate2_first_eval,
            "first_moves_collapsed": mate2_first_eval["first_move_success_count"] < baseline_mate2["first_move_success_count"],
        },
    }


def _evaluate_mate2_with_mask(
    graph: NativeReConKRKGraph,
    fens: Iterable[str],
    masked_triplets: set[str],
    *,
    max_samples: int,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    first_success = 0
    converted = 0
    same_graph_second_move_count = 0
    for fen in tuple(fens):
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        first = graph.choose(board, masked_triplets=masked_triplets)
        first_ok = first is not None and first.uci() in forced
        first_success += int(first_ok)
        all_replies_mated = False
        if first is not None:
            after_first = board.copy(stack=False)
            after_first.push(first)
            all_replies_mated = True
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_mate = after_first.copy(stack=False)
                before_mate.push(reply)
                second = graph.choose(before_mate, masked_triplets=masked_triplets)
                mates = {move.uci() for move in _mate_moves(before_mate)}
                ok = second is not None and second.uci() in mates
                same_graph_second_move_count += int(second is not None)
                all_replies_mated = all_replies_mated and ok
        converted += int(first_ok and all_replies_mated)
        rows.append({
            "fen": fen,
            "selected_first": None if first is None else first.uci(),
            "first_move_success": first_ok,
            "all_replies_mated": all_replies_mated,
        })
    total = len(rows)
    return {
        "first_move_success_count": first_success,
        "conversion_count": converted,
        "position_count": total,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "same_graph_second_move_count": same_graph_second_move_count,
        "samples": rows[:max_samples],
    }


def _post_prune_eval(
    graph: NativeReConKRKGraph,
    prune_triplets: Iterable[str],
    mate1_fens: tuple[str, ...],
    mate2_fens: tuple[str, ...],
    native_cfg: NativeSingleGraphConfig,
) -> dict[str, Any]:
    masked = set(prune_triplets)
    mate1_correct = 0
    for fen in mate1_fens:
        board = chess.Board(fen)
        move = graph.choose(board, masked_triplets=masked)
        mates = {item.uci() for item in _mate_moves(board)}
        mate1_correct += int(move is not None and move.uci() in mates)
    mate2 = _evaluate_mate2_with_mask(graph, mate2_fens, masked, max_samples=native_cfg.max_samples)
    return {
        "masked_prune_candidate_count": len(masked),
        "mate1_correct": mate1_correct,
        "mate1_total": len(mate1_fens),
        "mate1_accuracy": 0.0 if not mate1_fens else mate1_correct / len(mate1_fens),
        "mate2_conversion_count": mate2["conversion_count"],
        "mate2_total": mate2["position_count"],
        "mate2_conversion_rate": mate2["conversion_rate"],
    }
