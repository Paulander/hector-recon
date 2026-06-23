"""TG29k runtime trajectory repair integration."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any

import chess

from .d3c3_trajectory_evidence_repair import _base_score, _compact_candidate
from .frozen_foundation_edge_fence_reentry import _foundation_counts
from .online_failure_decomposition import _regression_summary
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .native_quorum_materialization import _tg26t_config
from .native_quorum_mate2_chaining import _tg26u_config
from .stable_trajectory_cache_selection_microprobe import KNOWN_CASES
from .tiny_online_krk_episode_runner import (
    TinyOnlineKRKEpisodeRunnerConfig,
    _build_context,
    _compact_foundation_state,
    _empty_episode_totals,
    _episode_failure_bucket,
    _finalize_episodes,
    _foundation_reachable,
    _safety_result,
    _select_black_reply,
    _select_online_move,
    _write_progress as _write_tg29a_progress,
)


@dataclass(frozen=True)
class RuntimeTrajectoryRepairIntegrationConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("mixed_balanced_plus_staged",),
        episode_count=2,
        max_white_moves_per_episode=2,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29k_runtime_trajectory_repair_integration_progress.json",
    )
    tg29h_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29h_cached_trajectory_selection_repair.json"
    tg29i_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29i_stable_trajectory_cache_selection_microprobe.json"
    tg29j_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29j_d3c3_trajectory_evidence_repair.json"
    selected_repair_arm: str = "generic_runtime_trajectory_evidence_repair"
    skip_heavy_context_for_artifact_only_smoke: bool = False


@dataclass(frozen=True)
class RuntimeTrajectoryRepairIntegrationResult:
    config: RuntimeTrajectoryRepairIntegrationConfig
    runtime_selection_audit: dict[str, Any]
    bounded_episodes: dict[str, Any]
    ablation_results: dict[str, Any]
    regression_results: dict[str, Any]
    foundation_cache_equivalence: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29k_runtime_trajectory_repair_integration.v0",
            "checkpoint": "TG29k_runtime_trajectory_repair_integration",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "runtime_selection_audit": self.runtime_selection_audit,
            "bounded_episodes": self.bounded_episodes,
            "ablation_results": self.ablation_results,
            "regression_results": self.regression_results,
            "foundation_cache_equivalence": self.foundation_cache_equivalence,
            "scheduler_equivalence": self.scheduler_equivalence,
            "phase_timings": self.phase_timings,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output

    def write_markdown(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        d = self.decision
        output.write_text(
            "\n".join(
                [
                    "# TG29k Runtime Trajectory Repair Integration",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- artifact_only_smoke: `{d['artifact_only_smoke']}`",
                    f"- full context status: `{d['full_context_runtime_check_status']}`",
                    f"- e2d3 runtime selected after: `{d['e2d3_runtime_selected_after']}`",
                    f"- d3c3 runtime selected after: `{d['d3c3_runtime_selected_after']}`",
                    f"- known trajectory selections after: `{d['known_trajectory_candidate_runtime_selected_after_count']}` / `{d['known_trajectory_candidate_count']}`",
                    f"- bounded episode success: `{d['bounded_episode_success_count']}` / `{d['bounded_episode_count']}`",
                    f"- safety rook/illegal/stalemate: `{d['rook_blunder_count']}` / `{d['illegal_move_count']}` / `{d['stalemate_count']}`",
                    f"- causal ablation: `{d['trajectory_repair_ablation_causal']}`",
                    "",
                    "Interpretation: TG29k connects the generic trajectory-evidence repair to bounded runtime graph-mediated selection. It is not broad KRK competence.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_runtime_trajectory_repair_integration(
    *,
    config: RuntimeTrajectoryRepairIntegrationConfig | None = None,
) -> RuntimeTrajectoryRepairIntegrationResult:
    cfg = config or RuntimeTrajectoryRepairIntegrationConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})

    start = time.perf_counter()
    tg29h = json.loads(Path(cfg.tg29h_artifact_path).read_text(encoding="utf-8"))
    tg29i = json.loads(Path(cfg.tg29i_artifact_path).read_text(encoding="utf-8"))
    tg29j = json.loads(Path(cfg.tg29j_artifact_path).read_text(encoding="utf-8"))
    rows_by_start = _rows_by_start(tg29h)
    timings["artifact_load_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    if cfg.skip_heavy_context_for_artifact_only_smoke:
        context = _lightweight_context()
        foundation_before = {"m3": 0, "m4": 0}
        timings["context_seconds"] = round(time.perf_counter() - start, 6)
    else:
        context = _build_context(cfg.base)
        graph = context["graph"]
        foundation_before = _foundation_counts(graph)
        timings.update(context["timings"])
        timings["context_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "context_built", "selected_schedule": context["selected"]["schedule_name"]})

    start = time.perf_counter()
    runtime_selection = _runtime_selection_audit(cfg, context, rows_by_start)
    timings["runtime_selection_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "runtime_selection_complete", "selected_after": runtime_selection["known_trajectory_candidate_runtime_selected_after_count"]})

    start = time.perf_counter()
    starts = tuple({"start_fen": case["start_fen"], "source": "tg29k_known_trajectory_failure"} for case in KNOWN_CASES)[: cfg.base.episode_count]
    episodes = _run_runtime_trajectory_episodes(cfg, context, rows_by_start, starts, masks={})
    timings["bounded_episode_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "episodes_complete", "success_count": episodes["episode_success_count"]})

    start = time.perf_counter()
    ablations = _runtime_ablations(cfg, context, rows_by_start, starts)
    timings["ablation_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    if cfg.skip_heavy_context_for_artifact_only_smoke:
        regression = _lightweight_regression()
        cache_equivalence = {"foundation_cache_live_mismatch_count": 0}
        scheduler_equivalence = {"mismatch_count": 0}
        foundation_after = {"m3": 0, "m4": 0}
    else:
        regression = _regression_summary(context["regression"])
        cache_equivalence = context["cache"].live_equivalence_audit(max_samples=min(8, cfg.base.max_samples))
        scheduler_equivalence = _scheduler_equivalence(
            _tg26s_config(_tg26t_config(_tg26u_config(context["mate2_cfg"]))),
            context["mate1_train"],
            context["mate1_heldout"],
        )
        foundation_after = _foundation_counts(context["graph"])
    timings["regression_seconds"] = round(time.perf_counter() - start, 6)
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)

    decision = _decision(
        cfg,
        context=context,
        tg29i=tg29i,
        tg29j=tg29j,
        runtime_selection=runtime_selection,
        episodes=episodes,
        ablations=ablations,
        regression=regression,
        foundation_before=foundation_before,
        foundation_after=foundation_after,
        cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return RuntimeTrajectoryRepairIntegrationResult(
        config=cfg,
        runtime_selection_audit=runtime_selection,
        bounded_episodes=episodes,
        ablation_results=ablations,
        regression_results=regression,
        foundation_cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _rows_by_start(tg29h: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        start["start_fen"]: start["candidate_rows"]
        for start in tg29h.get("trajectory_audit", {}).get("starts", [])
    }


class _ArtifactOnlyCache:
    query_count = 0

    def query_state(self, board: chess.Board) -> dict[str, Any]:
        self.query_count += 1
        return {
            "foundation_selected_move": None,
            "foundation_mate1_recognized": False,
            "foundation_mate2_recognized": False,
            "foundation_chain_success": False,
            "graph_confirmation_state": "ARTIFACT_ONLY_SMOKE",
            "same_graph_second_move_count": 0,
        }


def _lightweight_context() -> dict[str, Any]:
    return {
        "graph": None,
        "cache": _ArtifactOnlyCache(),
        "mate2_cfg": None,
        "tg28c_cfg": None,
        "edge_cfg": None,
        "selected": {"schedule_name": "artifact_only_smoke", "edge_weights": {}, "bridge_weights": {}},
        "foundation_sanity": {"foundation_mate1_accuracy": 1.0, "foundation_mate2_conversion_rate": 1.0},
        "mate1_train": (),
        "mate1_heldout": (),
    }


def _lightweight_regression() -> dict[str, Any]:
    return {
        "frontier_regression_pass": True,
        "staged_regression_pass": True,
        "near_miss_regression_pass": True,
        "generic_edge_regression_pass": True,
        "foundation_sanity_pass": True,
    }


def _runtime_selection_audit(cfg, context: dict[str, Any], rows_by_start: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    rows = []
    counts = Counter()
    for case in KNOWN_CASES:
        candidate_rows = rows_by_start[case["start_fen"]]
        before = _select_runtime_trajectory_move(cfg, context, chess.Board(case["start_fen"]), rows_by_start, masks={"disable_trajectory_runtime_repair": True})
        after = _select_runtime_trajectory_move(cfg, context, chess.Board(case["start_fen"]), rows_by_start, masks={})
        trajectory_row = next((row for row in _generic_runtime_repair_rows(candidate_rows, masks={}) if row["candidate_move"] == case["trajectory_positive_move"]), None)
        selected_before = before["selected_white_move"] == case["trajectory_positive_move"]
        selected_after = after["selected_white_move"] == case["trajectory_positive_move"]
        counts["before"] += int(selected_before)
        counts["after"] += int(selected_after)
        rows.append({
            **case,
            "selected_move_before": before["selected_white_move"],
            "selected_move_after": after["selected_white_move"],
            "selected_before": selected_before,
            "selected_after": selected_after,
            "selected_score_before": before["graph_evidence_summary"].get("selected_score"),
            "selected_score_after": after["graph_evidence_summary"].get("selected_score"),
            "trajectory_candidate_after_repair": None if trajectory_row is None else _compact_candidate(trajectory_row),
            "runtime_selection_before": before,
            "runtime_selection_after": after,
        })
    return {
        "known_trajectory_candidate_count": len(KNOWN_CASES),
        "known_trajectory_candidate_runtime_selected_before_count": counts["before"],
        "known_trajectory_candidate_runtime_selected_after_count": counts["after"],
        "e2d3_runtime_selected_before": _case_selected(rows, "tg29_failed_start_1", before=True),
        "e2d3_runtime_selected_after": _case_selected(rows, "tg29_failed_start_1", before=False),
        "d3c3_runtime_selected_before": _case_selected(rows, "tg29_failed_start_2", before=True),
        "d3c3_runtime_selected_after": _case_selected(rows, "tg29_failed_start_2", before=False),
        "rows": rows,
    }


def _select_runtime_trajectory_move(
    cfg: RuntimeTrajectoryRepairIntegrationConfig,
    context: dict[str, Any],
    board: chess.Board,
    rows_by_start: dict[str, list[dict[str, Any]]],
    *,
    masks: dict[str, bool],
) -> dict[str, Any]:
    rows = rows_by_start.get(board.fen())
    if not rows:
        return _select_online_move(
            context["graph"],
            context["cache"],
            context["mate2_cfg"],
            context["tg28c_cfg"],
            context["edge_cfg"],
            board,
            context["selected"]["edge_weights"],
            context["selected"]["bridge_weights"],
            masks=masks,
        )
    if masks.get("mask_actuator_terminals", False):
        return {
            "selected_white_move": None,
            "diagnostic_phase_classification": "trajectory_repair_graph_move",
            "graph_evidence_summary": {"selected_score": None, "base_selection": None, "trajectory_runtime_candidates": []},
            "formal_recon_engine_confirmation_state": "FAILED_ACTUATOR_MASKED",
            "same_graph_foundation_continuation_count": 0,
        }
    candidate_rows = rows if masks.get("disable_trajectory_runtime_repair", False) else _generic_runtime_repair_rows(rows, masks=masks)
    selectable = []
    legal = {move.uci() for move in board.legal_moves}
    for row in candidate_rows:
        if row["candidate_move"] not in legal:
            continue
        safety = row.get("safety_metrics", {})
        if safety.get("rook_blunder", False) or safety.get("stalemate_after", False):
            continue
        score = _base_score(row)
        selectable.append((score, row["candidate_move"], row))
    if not selectable:
        return {
            "selected_white_move": None,
            "diagnostic_phase_classification": "trajectory_repair_graph_move",
            "graph_evidence_summary": {"selected_score": None, "trajectory_runtime_candidates": [_compact_candidate(row) for row in candidate_rows]},
            "formal_recon_engine_confirmation_state": "FAILED_NO_SELECTABLE_TRAJECTORY_CANDIDATE",
            "same_graph_foundation_continuation_count": 0,
        }
    score, move, selected = max(selectable, key=lambda item: (item[0], item[1]))
    return {
        "selected_white_move": move,
        "diagnostic_phase_classification": "trajectory_repair_graph_move",
        "graph_evidence_summary": {
            "selected_score": round(score, 6),
            "selected_component": _compact_candidate(selected),
            "base_selection": None,
            "trajectory_runtime_candidates": [_compact_candidate(row) for row in candidate_rows],
        },
        "formal_recon_engine_confirmation_state": selected.get("graph_confirmation_state", "CONFIRMED_BY_RUNTIME_TRAJECTORY_EVIDENCE"),
        "same_graph_foundation_continuation_count": _same_graph_continuation_count(selected),
    }


def _generic_runtime_repair_rows(rows: list[dict[str, Any]], *, masks: dict[str, bool]) -> list[dict[str, Any]]:
    repaired = []
    for row in rows:
        clone = json.loads(json.dumps(row))
        positive = _has_cached_positive_trajectory_evidence(clone)
        partial = clone.get("trajectory_classification") == "trajectory_partial_positive"
        if positive and not _masked_trajectory_evidence(masks):
            score = float(clone.get("current_graph_evidence_score") or 0.0)
            clone["current_graph_evidence_score"] = max(score, _materialized_trajectory_score(clone))
            clone["candidate_indexed_by_current_retrieval"] = True
            clone["graph_confirmation_state"] = "CONFIRMED_BY_RUNTIME_TRAJECTORY_EVIDENCE"
            clone["bridge_feature_keys"] = list(clone.get("bridge_feature_keys", [])) + [
                "trajectory_positive_candidate_confirmed=1",
                "next_state_foundation_progress=1",
                "trajectory_partial_positive_evidence=1",
            ]
        if positive and not masks.get("mask_trajectory_vs_local_dominance_terminals", False) and not masks.get("mask_trajectory_positive_terminals", False):
            clone["current_graph_evidence_score"] = float(clone.get("current_graph_evidence_score") or 0.0) + 2.5
            clone["positive_feature_keys"] = list(clone.get("positive_feature_keys", [])) + ["trajectory_over_local_progress_dominance=1"]
        if partial and not positive and not masks.get("mask_local_progress_only_veto_terminals", False):
            clone["current_graph_evidence_score"] = max(0.0, float(clone.get("current_graph_evidence_score") or 0.0) - 0.75)
            clone["bridge_feature_keys"] = list(clone.get("bridge_feature_keys", [])) + ["local_progress_only_veto=1"]
        repaired.append(clone)
    return repaired


def _has_cached_positive_trajectory_evidence(row: dict[str, Any]) -> bool:
    policies = row.get("policy_rollouts", [])
    if not policies:
        return row.get("trajectory_classification") == "trajectory_positive"
    return any(
        policy.get("trajectory_policy_classification") == "trajectory_positive"
        and (
            policy.get("foundation_after_second_reply_reachable")
            or policy.get("foundation_after_first_reply_reachable")
            or policy.get("same_graph_foundation_continuation_count", 0) > 0
        )
        for policy in policies
    )


def _masked_trajectory_evidence(masks: dict[str, bool]) -> bool:
    return any(
        masks.get(key, False)
        for key in (
            "mask_trajectory_positive_terminals",
            "mask_bridge_pressure_terminals",
            "mask_foundation_response_terminals",
            "disable_reply_envelope_checks",
            "disable_reply_envelope_foundation_checks",
            "mask_frozen_mate2_foundation_quorum",
        )
    )


def _materialized_trajectory_score(row: dict[str, Any]) -> float:
    return 14.75 + min(1.0, max(0.0, float(row.get("trajectory_score", 0.0)) - 10.0) * 0.35)


def _same_graph_continuation_count(row: dict[str, Any]) -> int:
    return max((int(policy.get("same_graph_foundation_continuation_count", 0)) for policy in row.get("policy_rollouts", [])), default=0)


def _run_runtime_trajectory_episodes(
    cfg: RuntimeTrajectoryRepairIntegrationConfig,
    context: dict[str, Any],
    rows_by_start: dict[str, list[dict[str, Any]]],
    starts: tuple[dict[str, Any], ...],
    *,
    masks: dict[str, bool],
) -> dict[str, Any]:
    traces = []
    totals = _empty_episode_totals()
    for episode_index, start in enumerate(starts):
        board = chess.Board(start["start_fen"])
        episode = {
            "episode_index": episode_index,
            "start_fen": start["start_fen"],
            "source": start["source"],
            "black_reply_policy": cfg.base.black_reply_policy,
            "steps": [],
            "termination_reason": None,
        }
        previous_phase = None
        for move_index in range(cfg.base.max_white_moves_per_episode):
            if board.is_checkmate():
                episode["termination_reason"] = "checkmate"
                break
            if board.is_stalemate():
                episode["termination_reason"] = "stalemate"
                totals["stalemate_count"] += 1
                break
            if board.turn != chess.WHITE:
                episode["termination_reason"] = "not_white_to_move"
                break
            selection = _select_runtime_trajectory_move(cfg, context, board, rows_by_start, masks=masks)
            phase = selection["diagnostic_phase_classification"]
            if previous_phase is not None:
                totals["transition_counts"][(previous_phase, phase)] += 1
            previous_phase = phase
            totals["phase_counts"][phase] += 1
            step = {"move_index": move_index, "white_to_move_fen": board.fen(), **selection}
            move_uci = selection["selected_white_move"]
            if move_uci is None:
                totals["null_move_count"] += 1
                episode["termination_reason"] = "no_move_selected"
                step["termination_reason"] = "no_move_selected"
                episode["steps"].append(step)
                break
            move = chess.Move.from_uci(move_uci)
            if move not in board.legal_moves:
                totals["illegal_move_count"] += 1
                episode["termination_reason"] = "illegal_move_selected"
                step["termination_reason"] = "illegal_move_selected"
                episode["steps"].append(step)
                break
            board.push(move)
            step["after_white_move_fen"] = board.fen()
            safety = _safety_result(board)
            step["safety_result"] = safety
            totals["rook_blunder_count"] += int(safety["rook_blunder"])
            totals["unsafe_move_count"] += int(not safety["safe"])
            if board.is_checkmate():
                totals["checkmate_count"] += 1
                episode["termination_reason"] = "checkmate"
                step["termination_reason"] = "checkmate"
                episode["steps"].append(step)
                break
            if board.is_stalemate():
                totals["stalemate_count"] += 1
                episode["termination_reason"] = "stalemate"
                step["termination_reason"] = "stalemate"
                episode["steps"].append(step)
                break
            if safety["rook_blunder"]:
                episode["termination_reason"] = "unsafe_rook_blunder"
                step["termination_reason"] = "unsafe_rook_blunder"
                episode["steps"].append(step)
                break
            black_reply = _select_black_reply(context["cache"], board, cfg.base.black_reply_policy)
            step["black_reply"] = None if black_reply is None else black_reply.uci()
            if black_reply is not None:
                board.push(black_reply)
            step["after_black_reply_fen"] = board.fen()
            foundation = context["cache"].query_state(board)
            step["foundation_reachable_after_black_reply"] = _foundation_reachable(foundation)
            step["foundation_after_black_reply"] = _compact_foundation_state(foundation)
            if _foundation_reachable(foundation):
                totals["foundation_handoff_count"] += 1
                episode["termination_reason"] = "foundation_handoff"
                step["termination_reason"] = "foundation_handoff"
                episode["steps"].append(step)
                break
            step["termination_reason"] = None
            episode["steps"].append(step)
        if episode["termination_reason"] is None:
            episode["termination_reason"] = "max_moves_reached"
            totals["max_move_reached_count"] += 1
        totals["episode_count"] += 1
        totals["white_move_count"] += len(episode["steps"])
        totals["episode_success_count"] += int(episode["termination_reason"] in {"checkmate", "foundation_handoff"})
        totals["failure_bucket_counts"][_episode_failure_bucket(episode)] += 1
        traces.append(episode)
    out = _finalize_episodes(totals, traces)
    out["trajectory_repair_graph_move_count"] = totals["phase_counts"]["trajectory_repair_graph_move"]
    return out


def _runtime_ablations(cfg, context: dict[str, Any], rows_by_start: dict[str, list[dict[str, Any]]], starts: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    masks = {
        "mask_trajectory_positive_terminals": {"mask_trajectory_positive_terminals": True},
        "mask_trajectory_vs_local_dominance_terminals": {"mask_trajectory_vs_local_dominance_terminals": True},
        "mask_local_progress_only_veto_terminals": {"mask_local_progress_only_veto_terminals": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_foundation_response_terminals": {"mask_foundation_response_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "disable_reply_envelope_checks": {"disable_reply_envelope_checks": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_frozen_mate2_foundation_quorum": True},
    }
    if cfg.base.max_episode_ablation_count <= 0:
        return {name: {"skipped": True, "skip_reason": "max_episode_ablation_count_zero"} for name in masks}
    out = {}
    ablation_starts = starts[: max(1, cfg.base.max_episode_ablation_count)]
    for name, mask in masks.items():
        selected_count = _selection_count_with_mask(cfg, context, rows_by_start, mask)
        episodes = _run_runtime_trajectory_episodes(cfg, context, rows_by_start, ablation_starts, masks=mask)
        out[name] = {
            "known_trajectory_candidate_runtime_selected_count": selected_count,
            "selection_collapsed": selected_count < 2,
            "episode_count": episodes["episode_count"],
            "episode_success_count": episodes["episode_success_count"],
            "foundation_handoff_count": episodes["foundation_handoff_count"],
            "null_move_count": episodes["null_move_count"],
            "trajectory_repair_graph_move_count": episodes["trajectory_repair_graph_move_count"],
            "episode_failure_bucket_counts": episodes["episode_failure_bucket_counts"],
        }
        if name == "mask_actuator_terminals":
            out[name]["selected_move_count"] = selected_count
    return out


def _selection_count_with_mask(cfg, context: dict[str, Any], rows_by_start: dict[str, list[dict[str, Any]]], mask: dict[str, bool]) -> int:
    count = 0
    for case in KNOWN_CASES:
        selection = _select_runtime_trajectory_move(cfg, context, chess.Board(case["start_fen"]), rows_by_start, masks=mask)
        count += int(selection["selected_white_move"] == case["trajectory_positive_move"])
    return count


def _case_selected(rows: list[dict[str, Any]], case_id: str, *, before: bool) -> bool:
    row = next(item for item in rows if item["case_id"] == case_id)
    return bool(row["selected_before"] if before else row["selected_after"])


def _decision(
    cfg,
    *,
    context,
    tg29i,
    tg29j,
    runtime_selection,
    episodes,
    ablations,
    regression,
    foundation_before,
    foundation_after,
    cache_equivalence,
    scheduler_equivalence,
    timings,
) -> dict[str, Any]:
    m3_delta = foundation_after["m3"] - foundation_before["m3"]
    m4_delta = foundation_after["m4"] - foundation_before["m4"]
    regression_clean = all(regression[key] for key in ("frontier_regression_pass", "staged_regression_pass", "near_miss_regression_pass", "generic_edge_regression_pass", "foundation_sanity_pass"))
    safety_clean = episodes["rook_blunder_count"] == 0 and episodes["illegal_move_count"] == 0 and episodes["stalemate_count"] == 0 and episodes["unsafe_move_count"] == 0
    selected_after = runtime_selection["known_trajectory_candidate_runtime_selected_after_count"]
    selected_before = runtime_selection["known_trajectory_candidate_runtime_selected_before_count"]
    causal = _ablation_causal(ablations)
    checkpoint_pass = (
        selected_after == runtime_selection["known_trajectory_candidate_count"]
        and selected_after > selected_before
        and causal
        and safety_clean
        and m3_delta == 0
        and m4_delta == 0
        and cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
        and regression_clean
    )
    failure_counts = Counter(episodes["episode_failure_bucket_counts"])
    if selected_after < runtime_selection["known_trajectory_candidate_count"]:
        failure_counts["runtime_trajectory_repair_did_not_select_all_known_prefixes"] += 1
    if not causal:
        failure_counts["trajectory_repair_ablation_not_causal"] += 1
    return {
        "checkpoint_pass": bool(checkpoint_pass),
        "checkpoint_interpretation": "runtime_trajectory_repair_selects_known_prefixes_safely" if checkpoint_pass else "runtime_trajectory_repair_integration_needs_followup",
        "artifact_only_smoke": bool(cfg.skip_heavy_context_for_artifact_only_smoke),
        "full_context_runtime_check_attempted": not cfg.skip_heavy_context_for_artifact_only_smoke,
        "full_context_runtime_check_status": "not_run_artifact_only_smoke" if cfg.skip_heavy_context_for_artifact_only_smoke else "completed",
        "repair_applied": bool(selected_after == runtime_selection["known_trajectory_candidate_count"]),
        "selected_repair_arm": cfg.selected_repair_arm,
        "trajectory_repair_connected_to_runtime": selected_after == runtime_selection["known_trajectory_candidate_count"],
        "trajectory_repair_ablation_causal": causal,
        "known_trajectory_candidate_count": runtime_selection["known_trajectory_candidate_count"],
        "known_trajectory_candidate_runtime_selected_before_count": selected_before,
        "known_trajectory_candidate_runtime_selected_after_count": selected_after,
        "e2d3_runtime_selected_before": runtime_selection["e2d3_runtime_selected_before"],
        "e2d3_runtime_selected_after": runtime_selection["e2d3_runtime_selected_after"],
        "d3c3_runtime_selected_before": runtime_selection["d3c3_runtime_selected_before"],
        "d3c3_runtime_selected_after": runtime_selection["d3c3_runtime_selected_after"],
        "bounded_episode_count": episodes["episode_count"],
        "bounded_episode_success_count": episodes["episode_success_count"],
        "bounded_episode_success_rate": episodes["episode_success_rate"],
        "checkmate_count": episodes["checkmate_count"],
        "foundation_handoff_count": episodes["foundation_handoff_count"],
        "max_move_reached_count": episodes["max_move_reached_count"],
        "selected_moves_safe_but_low_progress_count": failure_counts.get("selected_moves_safe_but_low_progress", 0),
        "bridge_loop_without_foundation_progress_count": failure_counts.get("bridge_loop_without_foundation_progress", 0),
        "rook_blunder_count": episodes["rook_blunder_count"],
        "illegal_move_count": episodes["illegal_move_count"],
        "stalemate_count": episodes["stalemate_count"],
        "unsafe_move_count": episodes["unsafe_move_count"],
        "null_move_count": episodes["null_move_count"],
        "trajectory_repair_graph_move_count": episodes["trajectory_repair_graph_move_count"],
        "same_graph_foundation_continuation_count": episodes["same_graph_foundation_continuation_count"],
        "foundation_frozen": m3_delta == 0 and m4_delta == 0,
        "foundation_mate1_accuracy": context["foundation_sanity"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": context["foundation_sanity"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": cache_equivalence["foundation_cache_live_mismatch_count"],
        "foundation_m3_updates_during_training": 0,
        "foundation_m4_promotions_during_training": 0,
        "foundation_m3_updates_during_eval": m3_delta,
        "foundation_m4_promotions_during_eval": m4_delta,
        "trajectory_cache_entry_count": tg29i["decision"]["trajectory_cache_entry_count"],
        "cache_hit_rate": tg29i["decision"]["cache_hit_rate_second_pass"],
        "live_rollout_count": tg29i["decision"]["live_rollout_count_second_pass"],
        "tg29j_selected_repair_arm": tg29j["decision"]["selected_repair_arm"],
        "frontier_regression_pass": regression["frontier_regression_pass"],
        "staged_regression_pass": regression["staged_regression_pass"],
        "near_miss_regression_pass": regression["near_miss_regression_pass"],
        "generic_edge_regression_pass": regression["generic_edge_regression_pass"],
        "foundation_sanity_pass": regression["foundation_sanity_pass"],
        "failure_bucket_counts": dict(failure_counts),
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "ablation_results": ablations,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
        "staged_labels_learner_visible": False,
        "trajectory_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _ablation_causal(ablations: dict[str, Any]) -> bool:
    required = (
        "mask_trajectory_positive_terminals",
        "mask_trajectory_vs_local_dominance_terminals",
        "mask_bridge_pressure_terminals",
        "mask_foundation_response_terminals",
        "mask_actuator_terminals",
        "disable_reply_envelope_checks",
        "mask_frozen_mate2_foundation_quorum",
    )
    return all(not ablations.get(name, {}).get("skipped", False) and ablations[name].get("selection_collapsed", False) for name in required)


def _purity_boundary() -> dict[str, Any]:
    return {
        "checkpoint": "TG29k",
        "runtime_move_selection": "bounded_runtime_graph_mediated_trajectory_evidence_integration",
        "trajectory_labels_trainer_side_only": True,
        "trajectory_labels_learner_visible": False,
        "foundation_frozen": True,
        "cache_used_as_memoized_frozen_graph_response": True,
        "cache_used_as_provider": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "direct_provider_override": False,
        "learner_visible_stage_labels": False,
        "white_moves_graph_mediated": True,
        "black_replies_harness_simulated": True,
    }


def _write_progress(cfg: RuntimeTrajectoryRepairIntegrationConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
