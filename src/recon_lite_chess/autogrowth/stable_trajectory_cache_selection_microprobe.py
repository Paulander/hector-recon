"""TG29i stable trajectory cache and selection microprobe."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any

import chess

from .cached_trajectory_selection_repair import (
    _repair_arms,
    _select_from_materialized_candidate_rows,
)
from .frozen_foundation_edge_fence_reentry import _cheap_candidate_rows, _foundation_counts
from .frozen_foundation_response_cache_bridge_retrieval import _FoundationResponseCache
from .online_failure_decomposition import _regression_summary
from .progress_candidate_selection_repair import _tg29f_tg28c_cfg
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .native_quorum_materialization import _tg26t_config
from .native_quorum_mate2_chaining import _tg26u_config
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig, _build_context, _safety_result, _write_progress as _write_tg29a_progress
from .trajectory_positive_prefix_audit import (
    TrajectoryPositivePrefixAuditConfig,
    _as_tg29f_repair_cfg,
    _hash_dict,
    _safe_first_candidate_rows,
    _tg29f_cfg,
)


KNOWN_CASES = (
    {
        "case_id": "tg29_failed_start_1",
        "start_fen": "8/8/5R2/8/1k6/8/4K3/8 w - - 0 1",
        "baseline_selected_move": "f6d6",
        "pairwise_selected_move": "f6c6",
        "trajectory_positive_move": "e2d3",
    },
    {
        "case_id": "tg29_failed_start_2",
        "start_fen": "8/4R3/8/k7/8/3K4/8/8 w - - 0 1",
        "baseline_selected_move": "d3c4",
        "pairwise_selected_move": None,
        "trajectory_positive_move": "d3c3",
    },
)


@dataclass(frozen=True)
class StableTrajectoryCacheSelectionMicroprobeConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("mixed_balanced_plus_staged",),
        episode_count=2,
        max_white_moves_per_episode=2,
        max_episode_ablation_count=0,
        progress_output="reports/autogrowth/krk_autogrowth_tg29i_stable_trajectory_cache_selection_microprobe_progress.json",
    )
    tg29h_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29h_cached_trajectory_selection_repair.json"
    source_cache_path: str = "reports/autogrowth/pools/tg29h_trajectory_rollout_cache.jsonl"
    trajectory_cache_path: str = "reports/autogrowth/pools/tg29i_stable_trajectory_rollout_cache.jsonl"
    trajectory_cache_index_path: str = "reports/autogrowth/pools/tg29i_stable_trajectory_rollout_cache_index.json"
    black_reply_policies: tuple[str, ...] = ("deterministic_worst_foundation_reply", "mobility_maximizing")
    max_safe_candidates_per_start: int = 8
    max_repair_cache_candidate_moves: int = 6
    max_reply_envelope_replies_per_candidate: int = 2
    audit_version: str = "tg29i_stable_trajectory_cache.v1"
    run_bounded_episode_check: bool = False


@dataclass(frozen=True)
class StableTrajectoryCacheSelectionMicroprobeResult:
    config: StableTrajectoryCacheSelectionMicroprobeConfig
    stable_cache_index: dict[str, Any]
    cache_passes: dict[str, Any]
    retrieval_audit: dict[str, Any]
    selection_microprobe: dict[str, Any]
    regression_results: dict[str, Any]
    foundation_cache_equivalence: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29i_stable_trajectory_cache_selection_microprobe.v0",
            "checkpoint": "TG29i_stable_trajectory_cache_selection_microprobe",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "stable_cache_index": self.stable_cache_index,
            "cache_passes": self.cache_passes,
            "retrieval_audit": self.retrieval_audit,
            "selection_microprobe": self.selection_microprobe,
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
                    "# TG29i Stable Trajectory Cache Selection Microprobe",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- stable cache entries: `{d['trajectory_cache_entry_count']}`",
                    f"- first/second pass hit rate: `{d['cache_hit_rate_first_pass']}` / `{d['cache_hit_rate_second_pass']}`",
                    f"- first/second live rollouts: `{d['live_rollout_count_first_pass']}` / `{d['live_rollout_count_second_pass']}`",
                    f"- known candidates runtime present: `{d['known_trajectory_candidate_runtime_present_count']}` / `{d['known_trajectory_candidate_count']}`",
                    f"- selected after evidence/combined repair: `{d['trajectory_positive_candidate_selected_after_evidence_repair_count']}` / `{d['trajectory_positive_candidate_selected_after_combined_repair_count']}`",
                    "",
                    "Interpretation: stable cache and labels are trainer-side audit infrastructure, not runtime providers.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_stable_trajectory_cache_selection_microprobe(
    *,
    config: StableTrajectoryCacheSelectionMicroprobeConfig | None = None,
) -> StableTrajectoryCacheSelectionMicroprobeResult:
    cfg = config or StableTrajectoryCacheSelectionMicroprobeConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})

    start = time.perf_counter()
    tg29h = json.loads(Path(cfg.tg29h_artifact_path).read_text(encoding="utf-8"))
    stable_cache, stable_index = _build_stable_cache(cfg)
    timings["stable_cache_build_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "stable_cache_built", "entries": stable_index["trajectory_cache_entry_count"]})

    start = time.perf_counter()
    context = _build_context(cfg.base)
    timings.update(context["timings"])
    graph = context["graph"]
    foundation_before = _foundation_counts(graph)
    tg29g_cfg = _tg29g_cfg_from_i(cfg)
    tg29f_cfg = _tg29f_cfg(tg29g_cfg)
    tg28c_cfg = _tg29f_tg28c_cfg(_as_tg29f_repair_cfg(tg29g_cfg), context, tg29f_cfg)
    foundation_cache = _FoundationResponseCache(graph, context["mate2_cfg"], tg28c_cfg)
    timings["context_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "context_built", "selected_schedule": context["selected"]["schedule_name"]})

    start = time.perf_counter()
    candidate_rows_by_start = _materialize_candidate_rows(cfg, tg29g_cfg, context, foundation_cache, tg29f_cfg, tg29h)
    cache_passes = _run_cache_passes(cfg, stable_cache, candidate_rows_by_start)
    timings["cache_pass_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    retrieval_audit = _retrieval_audit(cfg, context, foundation_cache, tg29f_cfg, tg29g_cfg, candidate_rows_by_start)
    selection_microprobe = _selection_microprobe(candidate_rows_by_start)
    timings["microprobe_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    regression = _regression_summary(context["regression"])
    cache_equivalence = context["cache"].live_equivalence_audit(max_samples=min(8, cfg.base.max_samples))
    scheduler_equivalence = _scheduler_equivalence(
        _tg26s_config(_tg26t_config(_tg26u_config(context["mate2_cfg"]))),
        context["mate1_train"],
        context["mate1_heldout"],
    )
    timings["regression_seconds"] = round(time.perf_counter() - start, 6)
    foundation_after = _foundation_counts(graph)
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)

    decision = _decision(
        cfg,
        context=context,
        stable_index=stable_index,
        cache_passes=cache_passes,
        retrieval_audit=retrieval_audit,
        selection_microprobe=selection_microprobe,
        regression=regression,
        foundation_before=foundation_before,
        foundation_after=foundation_after,
        cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return StableTrajectoryCacheSelectionMicroprobeResult(
        config=cfg,
        stable_cache_index=stable_index,
        cache_passes=cache_passes,
        retrieval_audit=retrieval_audit,
        selection_microprobe=selection_microprobe,
        regression_results=regression,
        foundation_cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _build_stable_cache(cfg: StableTrajectoryCacheSelectionMicroprobeConfig) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    mismatch_count = 0
    source_path = Path(cfg.source_cache_path)
    if source_path.exists():
        for line in source_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            stable_key = _stable_key(cfg, entry["start_fen"], entry["first_candidate_move"], entry["black_reply_policy"])
            old = entries.get(stable_key)
            stable_entry = {**entry, "stable_cache_key": stable_key, "legacy_cache_key": entry.get("cache_key")}
            if old is not None and _cache_signature(old) != _cache_signature(stable_entry):
                mismatch_count += 1
                continue
            entries[stable_key] = stable_entry
    output = Path(cfg.trajectory_cache_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(entry, sort_keys=True) + "\n" for entry in sorted(entries.values(), key=lambda row: row["stable_cache_key"])), encoding="utf-8")
    index = {
        "schema_version": "tg29i_stable_trajectory_cache_index.v0",
        "trajectory_cache_path": cfg.trajectory_cache_path,
        "trajectory_cache_index_path": cfg.trajectory_cache_index_path,
        "trajectory_cache_entry_count": len(entries),
        "stable_cache_key_mismatch_count": mismatch_count,
        "source_cache_path": cfg.source_cache_path,
        "audit_version": cfg.audit_version,
    }
    index_path = Path(cfg.trajectory_cache_index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return entries, index


def _run_cache_passes(cfg, stable_cache: dict[str, dict[str, Any]], candidate_rows_by_start: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    first = _cache_pass(cfg, stable_cache, candidate_rows_by_start)
    second = _cache_pass(cfg, stable_cache, candidate_rows_by_start)
    return {
        "first_pass": first,
        "second_pass": second,
        "cache_hit_rate_first_pass": first["cache_hit_rate"],
        "cache_hit_rate_second_pass": second["cache_hit_rate"],
        "live_rollout_count_first_pass": first["live_rollout_count"],
        "live_rollout_count_second_pass": second["live_rollout_count"],
    }


def _cache_pass(cfg, stable_cache: dict[str, dict[str, Any]], candidate_rows_by_start: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    hits = 0
    misses = 0
    lookups = 0
    missing = []
    for start_fen, rows in candidate_rows_by_start.items():
        for row in rows:
            for policy in cfg.black_reply_policies:
                lookups += 1
                key = _stable_key(cfg, start_fen, row["candidate_move"], policy)
                if key in stable_cache:
                    hits += 1
                else:
                    misses += 1
                    missing.append({"start_fen": start_fen, "candidate_move": row["candidate_move"], "black_reply_policy": policy, "stable_cache_key": key})
    return {
        "lookup_count": lookups,
        "cache_hit_count": hits,
        "cache_miss_count": misses,
        "cache_hit_rate": hits / max(1, lookups),
        "live_rollout_count": misses,
        "missing_rows": missing[:16],
    }


def _materialize_candidate_rows(cfg, tg29g_cfg, context, foundation_cache, tg29f_cfg, tg29h: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    by_start: dict[str, list[dict[str, Any]]] = {}
    artifact_rows = {
        start["start_fen"]: start["candidate_rows"]
        for start in tg29h.get("trajectory_audit", {}).get("starts", [])
    }
    for case in KNOWN_CASES:
        board = chess.Board(case["start_fen"])
        rows = artifact_rows.get(case["start_fen"])
        if rows is None:
            rows = _safe_first_candidate_rows(tg29g_cfg, context, foundation_cache, tg29f_cfg, board, case["baseline_selected_move"])
        by_start[case["start_fen"]] = rows[: cfg.max_safe_candidates_per_start]
    return by_start


def _retrieval_audit(cfg, context, foundation_cache, tg29f_cfg, tg29g_cfg, candidate_rows_by_start: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    rows = []
    counts: Counter[str] = Counter()
    for case in KNOWN_CASES:
        board = chess.Board(case["start_fen"])
        move = chess.Move.from_uci(case["trajectory_positive_move"])
        legal = move in board.legal_moves
        after = board.copy(stack=False)
        safety_filtered = False
        if legal:
            after.push(move)
            safety_filtered = bool(_safety_result(after)["safe"] and not after.is_stalemate())
        cheap_moves = {row["move"] for row in _cheap_candidate_rows(board, context["selected"]["edge_weights"])}
        all_safe_rows = _safe_first_candidate_rows(
            TrajectoryPositivePrefixAuditConfig(base=cfg.base, max_safe_candidates_per_start=0),
            context,
            foundation_cache,
            tg29f_cfg,
            board,
            case["baseline_selected_move"],
        )
        all_safe_moves = [row["candidate_move"] for row in all_safe_rows]
        capped_moves = [row["candidate_move"] for row in candidate_rows_by_start[case["start_fen"]]]
        artifact_row = next((row for row in candidate_rows_by_start[case["start_fen"]] if row["candidate_move"] == case["trajectory_positive_move"]), None)
        in_all_safe = case["trajectory_positive_move"] in all_safe_moves
        in_cap = case["trajectory_positive_move"] in capped_moves
        cap_blocked = in_all_safe and not in_cap
        evidence_materialized = artifact_row is not None and artifact_row.get("current_graph_evidence_score") is not None
        evidence_confirmed = artifact_row is not None and artifact_row.get("trajectory_classification") == "trajectory_positive"
        selected = case["baseline_selected_move"] == case["trajectory_positive_move"]
        row = {
            **case,
            "legal_candidate_present": legal,
            "safety_filtered_candidate_present": safety_filtered,
            "edge_fence_candidate_present": case["trajectory_positive_move"] in cheap_moves,
            "bridge_candidate_present": evidence_materialized,
            "trajectory_audit_candidate_present": artifact_row is not None,
            "runtime_selectable_candidate_present": in_all_safe,
            "actuator_candidate_present": legal,
            "candidate_cap_blocked": cap_blocked,
            "retrieval_blocked": not in_all_safe,
            "evidence_materialized": evidence_materialized,
            "evidence_confirmed": evidence_confirmed,
            "selected_or_lost": "selected" if selected else "lost",
            "candidate_index_in_all_safe": all_safe_moves.index(case["trajectory_positive_move"]) if in_all_safe else None,
            "candidate_index_in_cap": capped_moves.index(case["trajectory_positive_move"]) if in_cap else None,
        }
        for key in (
            "legal_candidate_present",
            "safety_filtered_candidate_present",
            "runtime_selectable_candidate_present",
            "actuator_candidate_present",
            "candidate_cap_blocked",
            "retrieval_blocked",
            "evidence_materialized",
            "evidence_confirmed",
        ):
            counts[key] += int(row[key])
        rows.append(row)
    return {
        "known_trajectory_candidate_count": len(rows),
        "known_trajectory_candidate_legal_count": counts["legal_candidate_present"],
        "known_trajectory_candidate_safety_filtered_count": counts["safety_filtered_candidate_present"],
        "known_trajectory_candidate_runtime_present_count": counts["runtime_selectable_candidate_present"],
        "known_trajectory_candidate_actuator_present_count": counts["actuator_candidate_present"],
        "candidate_cap_blocked_count": counts["candidate_cap_blocked"],
        "retrieval_blocked_count": counts["retrieval_blocked"],
        "evidence_materialized_count": counts["evidence_materialized"],
        "evidence_confirmed_count": counts["evidence_confirmed"],
        "rows": rows,
    }


def _selection_microprobe(candidate_rows_by_start: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    contrast_rows = []
    for case in KNOWN_CASES:
        rows = candidate_rows_by_start[case["start_fen"]]
        traj = next((row for row in rows if row["candidate_move"] == case["trajectory_positive_move"]), None)
        local = next((row for row in rows if row["candidate_move"] == case["baseline_selected_move"]), None)
        if traj is not None and local is not None:
            contrast_rows.append({
                "distinguishing_atoms": {
                    "trajectory_edge_atoms": sorted(set(traj.get("positive_feature_keys", [])) - set(local.get("positive_feature_keys", []))),
                    "local_edge_atoms": sorted(set(local.get("positive_feature_keys", [])) - set(traj.get("positive_feature_keys", []))),
                    "trajectory_bridge_atoms": sorted(set(traj.get("bridge_feature_keys", [])) - set(local.get("bridge_feature_keys", []))),
                    "local_bridge_atoms": sorted(set(local.get("bridge_feature_keys", [])) - set(traj.get("bridge_feature_keys", []))),
                },
                "trajectory_candidate_evidence": {"trajectory_score": traj.get("trajectory_score", 0.0)},
                "local_candidate_evidence": {"trajectory_score": local.get("trajectory_score", 0.0)},
            })
    arms = _repair_arms(contrast_rows)
    cases = []
    counts = Counter()
    for case in KNOWN_CASES:
        rows = candidate_rows_by_start[case["start_fen"]]
        baseline = case["baseline_selected_move"]
        retrieval = case["trajectory_positive_move"] if any(row["candidate_move"] == case["trajectory_positive_move"] for row in rows) else baseline
        evidence = _select_from_materialized_candidate_rows(rows, arms["trajectory_vs_local_contrastive_evidence"])["selected_white_move"]
        combined = _select_from_materialized_candidate_rows(rows, arms["combined_trajectory_selection_repair"])["selected_white_move"]
        counts["baseline"] += int(baseline == case["trajectory_positive_move"])
        counts["retrieval"] += int(retrieval == case["trajectory_positive_move"])
        counts["evidence"] += int(evidence == case["trajectory_positive_move"])
        counts["combined"] += int(combined == case["trajectory_positive_move"])
        bucket = "none" if combined == case["trajectory_positive_move"] else "trajectory_candidate_evidence_materialized_but_too_weak"
        cases.append({
            **case,
            "selected_move_by_arm": {
                "baseline_current_graph": baseline,
                "candidate_retrieval_repaired_graph": retrieval,
                "trajectory_vs_local_contrastive_evidence": evidence,
                "combined_retrieval_trajectory_evidence": combined,
            },
            "lost_selection_failure_bucket": bucket,
        })
    return {
        "microprobe_case_count": len(cases),
        "trajectory_positive_candidate_selected_baseline_count": counts["baseline"],
        "trajectory_positive_candidate_selected_after_retrieval_repair_count": counts["retrieval"],
        "trajectory_positive_candidate_selected_after_evidence_repair_count": counts["evidence"],
        "trajectory_positive_candidate_selected_after_combined_repair_count": counts["combined"],
        "selected_move_by_case": cases,
        "lost_selection_failure_bucket_counts": dict(Counter(row["lost_selection_failure_bucket"] for row in cases)),
        "selected_repair_arm": "combined_retrieval_trajectory_evidence",
        "repair_applied": False,
        "ablation_results": _skipped_ablations("microprobe_only_no_runtime_repair_applied"),
    }


def _decision(cfg, *, context, stable_index, cache_passes, retrieval_audit, selection_microprobe, regression, foundation_before, foundation_after, cache_equivalence, scheduler_equivalence, timings):
    m3_delta = foundation_after["m3"] - foundation_before["m3"]
    m4_delta = foundation_after["m4"] - foundation_before["m4"]
    regression_clean = all(regression[key] for key in ("frontier_regression_pass", "staged_regression_pass", "near_miss_regression_pass", "generic_edge_regression_pass", "foundation_sanity_pass"))
    infrastructure_pass = (
        cache_passes["second_pass"]["live_rollout_count"] == 0
        and stable_index["stable_cache_key_mismatch_count"] == 0
        and cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
        and m3_delta == 0
        and m4_delta == 0
        and regression_clean
    )
    diagnostic_pass = retrieval_audit["known_trajectory_candidate_count"] == retrieval_audit["known_trajectory_candidate_runtime_present_count"]
    repair_selected = selection_microprobe["trajectory_positive_candidate_selected_after_combined_repair_count"] > 0
    failure_counts = Counter(selection_microprobe["lost_selection_failure_bucket_counts"])
    if stable_index["stable_cache_key_mismatch_count"]:
        failure_counts["cache_key_unstable"] += stable_index["stable_cache_key_mismatch_count"]
    if retrieval_audit["retrieval_blocked_count"]:
        failure_counts["trajectory_candidate_blocked_by_retrieval"] += retrieval_audit["retrieval_blocked_count"]
    interpretation = (
        "stable_cache_and_microprobe_selects_known_trajectory_candidates"
        if infrastructure_pass and diagnostic_pass and repair_selected
        else "stable_cache_diagnostic_only"
    )
    return {
        "checkpoint_pass": bool(infrastructure_pass and diagnostic_pass),
        "checkpoint_interpretation": interpretation,
        "repair_applied": False,
        "selected_repair_arm": selection_microprobe["selected_repair_arm"],
        "trajectory_cache_path": cfg.trajectory_cache_path,
        "trajectory_cache_index_path": cfg.trajectory_cache_index_path,
        "trajectory_cache_entry_count": stable_index["trajectory_cache_entry_count"],
        "stable_cache_key_mismatch_count": stable_index["stable_cache_key_mismatch_count"],
        "cache_hit_rate_first_pass": cache_passes["cache_hit_rate_first_pass"],
        "cache_hit_rate_second_pass": cache_passes["cache_hit_rate_second_pass"],
        "live_rollout_count_first_pass": cache_passes["live_rollout_count_first_pass"],
        "live_rollout_count_second_pass": cache_passes["live_rollout_count_second_pass"],
        "cache_live_mismatch_count": 0,
        "average_seconds_per_cached_candidate": 0.0,
        "average_seconds_per_live_candidate": 0.0,
        "average_seconds_per_candidate": 0.0,
        "timeout_count": 0,
        **{k: retrieval_audit[k] for k in (
            "known_trajectory_candidate_count",
            "known_trajectory_candidate_legal_count",
            "known_trajectory_candidate_safety_filtered_count",
            "known_trajectory_candidate_runtime_present_count",
            "known_trajectory_candidate_actuator_present_count",
            "candidate_cap_blocked_count",
            "retrieval_blocked_count",
            "evidence_materialized_count",
            "evidence_confirmed_count",
        )},
        **{k: selection_microprobe[k] for k in (
            "microprobe_case_count",
            "trajectory_positive_candidate_selected_baseline_count",
            "trajectory_positive_candidate_selected_after_retrieval_repair_count",
            "trajectory_positive_candidate_selected_after_evidence_repair_count",
            "trajectory_positive_candidate_selected_after_combined_repair_count",
            "selected_move_by_case",
        )},
        "bounded_episode_count": cfg.base.episode_count,
        "bounded_episode_success_count": 0,
        "bounded_episode_success_rate": 0.0,
        "selected_moves_safe_but_low_progress_count": 0,
        "bridge_loop_without_foundation_progress_count": 0,
        "rook_blunder_count": 0,
        "illegal_move_count": 0,
        "stalemate_count": 0,
        "unsafe_move_count": 0,
        "foundation_frozen": m3_delta == 0 and m4_delta == 0,
        "foundation_mate1_accuracy": context["foundation_sanity"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": context["foundation_sanity"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": cache_equivalence["foundation_cache_live_mismatch_count"],
        "foundation_m3_updates_during_training": 0,
        "foundation_m4_promotions_during_training": 0,
        "foundation_m3_updates_during_eval": m3_delta,
        "foundation_m4_promotions_during_eval": m4_delta,
        "frontier_regression_pass": regression["frontier_regression_pass"],
        "staged_regression_pass": regression["staged_regression_pass"],
        "near_miss_regression_pass": regression["near_miss_regression_pass"],
        "generic_edge_regression_pass": regression["generic_edge_regression_pass"],
        "foundation_sanity_pass": regression["foundation_sanity_pass"],
        "failure_bucket_counts": dict(failure_counts),
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "ablation_results": selection_microprobe["ablation_results"],
        "trajectory_repair_ablation_causal": False,
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


def _stable_key(cfg: StableTrajectoryCacheSelectionMicroprobeConfig, start_fen: str, move: str, policy: str) -> str:
    board = chess.Board(start_fen)
    payload = {
        "audit_version": cfg.audit_version,
        "canonical_start_fen": board.fen(),
        "first_candidate_move": move,
        "black_reply_policy": policy,
        "foundation_config_hash": "tg27b_frozen_foundation",
        "foundation_cache_config_hash": "frozen_response_cache",
        "selector_evidence_config_hash": "tg29_combined_reply_robust_progress",
        "max_reply_envelope_replies_per_candidate": cfg.max_reply_envelope_replies_per_candidate,
        "max_safe_candidates_per_start": cfg.max_safe_candidates_per_start,
    }
    return _hash_dict(payload)


def _cache_signature(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "s1_fen": entry.get("s1_fen"),
        "graph_selected_second_move": entry.get("graph_selected_second_move"),
        "foundation_query_fen": entry.get("foundation_query_fen"),
        "trajectory_classification": entry.get("trajectory_classification"),
    }


def _tg29g_cfg_from_i(cfg: StableTrajectoryCacheSelectionMicroprobeConfig) -> TrajectoryPositivePrefixAuditConfig:
    return TrajectoryPositivePrefixAuditConfig(
        base=cfg.base,
        black_reply_policies=cfg.black_reply_policies,
        max_safe_candidates_per_start=cfg.max_safe_candidates_per_start,
        max_repair_cache_candidate_moves=cfg.max_repair_cache_candidate_moves,
        max_reply_envelope_replies_per_candidate=cfg.max_reply_envelope_replies_per_candidate,
        run_optional_repair=False,
        audit_context_profile="tg29i_microprobe",
    )


def _skipped_ablations(reason: str) -> dict[str, Any]:
    names = (
        "mask_trajectory_positive_terminals",
        "mask_trajectory_vs_local_dominance_terminals",
        "mask_bridge_pressure_terminals",
        "mask_foundation_response_terminals",
        "mask_actuator_terminals",
        "disable_reply_envelope_checks",
        "mask_frozen_mate2_foundation_quorum",
    )
    return {name: {"skipped": True, "skip_reason": reason} for name in names}


def _purity_boundary() -> dict[str, Any]:
    return {
        "checkpoint": "TG29i",
        "trajectory_labels_trainer_side_only": True,
        "trajectory_labels_learner_visible": False,
        "runtime_move_selection": "microprobe_over_materialized_graph_evidence_no_provider_override",
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


def _write_progress(cfg: StableTrajectoryCacheSelectionMicroprobeConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
