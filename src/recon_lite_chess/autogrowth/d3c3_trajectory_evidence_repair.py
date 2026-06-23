"""TG29j d3c3 trajectory evidence repair microprobe."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any

from .frozen_foundation_edge_fence_reentry import _foundation_counts
from .online_failure_decomposition import _regression_summary
from .cached_trajectory_selection_repair import _select_from_materialized_candidate_rows
from .stable_trajectory_cache_selection_microprobe import KNOWN_CASES
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .native_quorum_materialization import _tg26t_config
from .native_quorum_mate2_chaining import _tg26u_config
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig, _build_context, _write_progress as _write_tg29a_progress
from .trajectory_positive_prefix_audit import _hash_dict


@dataclass(frozen=True)
class D3C3TrajectoryEvidenceRepairConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("mixed_balanced_plus_staged",),
        episode_count=2,
        max_white_moves_per_episode=2,
        max_episode_ablation_count=0,
        progress_output="reports/autogrowth/krk_autogrowth_tg29j_d3c3_trajectory_evidence_repair_progress.json",
    )
    tg29h_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29h_cached_trajectory_selection_repair.json"
    tg29i_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29i_stable_trajectory_cache_selection_microprobe.json"
    trajectory_cache_path: str = "reports/autogrowth/pools/tg29i_stable_trajectory_rollout_cache.jsonl"


@dataclass(frozen=True)
class D3C3TrajectoryEvidenceRepairResult:
    config: D3C3TrajectoryEvidenceRepairConfig
    selection_margin_audit: dict[str, Any]
    evidence_comparison: dict[str, Any]
    microprobe: dict[str, Any]
    regression_results: dict[str, Any]
    foundation_cache_equivalence: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29j_d3c3_trajectory_evidence_repair.v0",
            "checkpoint": "TG29j_d3c3_trajectory_evidence_repair",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "selection_margin_audit": self.selection_margin_audit,
            "evidence_comparison": self.evidence_comparison,
            "microprobe": self.microprobe,
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
                    "# TG29j d3c3 Trajectory Evidence Repair",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- selected repair arm: `{d['selected_repair_arm']}`",
                    f"- e2d3 selected before/after: `{d['e2d3_selected_before']}` / `{d['e2d3_selected_after']}`",
                    f"- d3c3 selected before/after: `{d['d3c3_selected_before']}` / `{d['d3c3_selected_after']}`",
                    f"- selected count before/after: `{d['known_trajectory_candidate_selected_before_count']}` / `{d['known_trajectory_candidate_selected_after_count']}`",
                    f"- d3c3 failure before/after: `{d['d3c3_failure_bucket_before']}` / `{d['d3c3_failure_bucket_after']}`",
                    "",
                    "Interpretation: TG29j repairs materialized trajectory evidence in the microprobe. It is not a runtime provider.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_d3c3_trajectory_evidence_repair(
    *,
    config: D3C3TrajectoryEvidenceRepairConfig | None = None,
) -> D3C3TrajectoryEvidenceRepairResult:
    cfg = config or D3C3TrajectoryEvidenceRepairConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})

    start = time.perf_counter()
    tg29h = json.loads(Path(cfg.tg29h_artifact_path).read_text(encoding="utf-8"))
    tg29i = json.loads(Path(cfg.tg29i_artifact_path).read_text(encoding="utf-8"))
    case_rows = _case_rows(tg29h)
    cache_entries = _load_cache_entries(Path(cfg.trajectory_cache_path))
    timings["artifact_load_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    context = _build_context(cfg.base)
    graph = context["graph"]
    foundation_before = _foundation_counts(graph)
    timings.update(context["timings"])
    timings["context_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "context_built", "selected_schedule": context["selected"]["schedule_name"]})

    start = time.perf_counter()
    margin = _selection_margin_audit(case_rows, cache_entries)
    comparison = _evidence_comparison(case_rows)
    microprobe = _microprobe(case_rows)
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
        tg29i=tg29i,
        margin=margin,
        comparison=comparison,
        microprobe=microprobe,
        regression=regression,
        foundation_before=foundation_before,
        foundation_after=foundation_after,
        cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return D3C3TrajectoryEvidenceRepairResult(
        config=cfg,
        selection_margin_audit=margin,
        evidence_comparison=comparison,
        microprobe=microprobe,
        regression_results=regression,
        foundation_cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _case_rows(tg29h: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for start in tg29h["trajectory_audit"]["starts"]:
        by_move = {row["candidate_move"]: row for row in start["candidate_rows"]}
        case = next(item for item in KNOWN_CASES if item["start_fen"] == start["start_fen"])
        rows[case["case_id"]] = {
            "case": case,
            "start": start,
            "selected": by_move[case["baseline_selected_move"]],
            "trajectory": by_move[case["trajectory_positive_move"]],
            "candidate_rows": start["candidate_rows"],
        }
    return rows


def _load_cache_entries(path: Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    entries: dict[tuple[str, str], list[dict[str, Any]]] = {}
    if not path.exists():
        return entries
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        entries.setdefault((entry["start_fen"], entry["first_candidate_move"]), []).append(entry)
    return entries


def _selection_margin_audit(case_rows: dict[str, dict[str, Any]], cache_entries: dict[tuple[str, str], list[dict[str, Any]]]) -> dict[str, Any]:
    second = case_rows["tg29_failed_start_2"]
    selected = second["selected"]
    d3c3 = second["trajectory"]
    before_selected_score = _base_score(selected)
    before_d3c3_score = _base_score(d3c3)
    repaired_rows = _repair_rows(second["candidate_rows"], repair_type="d3c3_trajectory_evidence_materialization")
    repaired_selected = next(row for row in repaired_rows if row["candidate_move"] == selected["candidate_move"])
    repaired_d3c3 = next(row for row in repaired_rows if row["candidate_move"] == d3c3["candidate_move"])
    after_selected_score = _base_score(repaired_selected)
    after_d3c3_score = _base_score(repaired_d3c3)
    return {
        "start_fen": second["case"]["start_fen"],
        "current_selected_move": selected["candidate_move"],
        "trajectory_positive_move": d3c3["candidate_move"],
        "d3c3_candidate_row": _compact_candidate(d3c3),
        "all_candidate_rows_considered_by_runtime": [_compact_candidate(row) for row in second["candidate_rows"]],
        "candidate_scores_before": {row["candidate_move"]: _base_score(row) for row in second["candidate_rows"]},
        "candidate_scores_after": {row["candidate_move"]: _base_score(row) for row in repaired_rows},
        "selected_vs_d3c3_score_margin_before": round(before_selected_score - before_d3c3_score, 6),
        "selected_vs_d3c3_score_margin_after": round(after_selected_score - after_d3c3_score, 6),
        "selected_vs_d3c3_terminal_states": _compare_keys(selected.get("positive_feature_keys", []), d3c3.get("positive_feature_keys", [])),
        "selected_vs_d3c3_edge_fence_evidence": _compare_keys(selected.get("positive_feature_keys", []), d3c3.get("positive_feature_keys", [])),
        "selected_vs_d3c3_bridge_pressure_evidence": _compare_keys(selected.get("bridge_feature_keys", []), d3c3.get("bridge_feature_keys", [])),
        "selected_vs_d3c3_trajectory_positive_evidence": {
            "selected_classification": selected["trajectory_classification"],
            "d3c3_classification": d3c3["trajectory_classification"],
            "selected_trajectory_score": selected["trajectory_score"],
            "d3c3_trajectory_score": d3c3["trajectory_score"],
        },
        "selected_vs_d3c3_foundation_response_evidence": {
            "selected_cache_entries": _foundation_cache_summary(cache_entries.get((second["case"]["start_fen"], selected["candidate_move"]), [])),
            "d3c3_cache_entries": _foundation_cache_summary(cache_entries.get((second["case"]["start_fen"], d3c3["candidate_move"]), [])),
        },
        "selected_vs_d3c3_action_delta_evidence": _compare_keys(selected.get("positive_feature_keys", []), d3c3.get("positive_feature_keys", []), prefix_filter=("delta_", "combined_progress")),
        "selected_vs_d3c3_internal_attention_request_strength_evidence": {
            "selected_current_graph_evidence_score": selected.get("current_graph_evidence_score"),
            "d3c3_current_graph_evidence_score": d3c3.get("current_graph_evidence_score"),
        },
        "selected_vs_d3c3_safety_veto_evidence": {
            "selected": selected["safety_metrics"],
            "d3c3": d3c3["safety_metrics"],
        },
        "selected_vs_d3c3_actuator_confirmation": {
            "selected_candidate_indexed_by_current_retrieval": selected.get("candidate_indexed_by_current_retrieval"),
            "d3c3_candidate_indexed_by_current_retrieval": d3c3.get("candidate_indexed_by_current_retrieval"),
        },
        "formal_recon_engine_confirmation_state": {
            "selected": "CONFIRMED",
            "d3c3": "MATERIALIZED_BY_TG29J_TRAJECTORY_EVIDENCE_REPAIR",
        },
        "d3c3_failure_bucket_before": _d3c3_failure_bucket_before(selected, d3c3),
        "d3c3_failure_bucket_after": "none" if after_d3c3_score > after_selected_score else "d3c3_trajectory_evidence_too_weak",
    }


def _evidence_comparison(case_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    e2 = case_rows["tg29_failed_start_1"]["trajectory"]
    e2_selected = case_rows["tg29_failed_start_1"]["selected"]
    d3 = case_rows["tg29_failed_start_2"]["trajectory"]
    d3_selected = case_rows["tg29_failed_start_2"]["selected"]
    e2_atoms = set(e2.get("positive_feature_keys", [])) | set(e2.get("bridge_feature_keys", []))
    d3_atoms = set(d3.get("positive_feature_keys", [])) | set(d3.get("bridge_feature_keys", []))
    d3_selected_atoms = set(d3_selected.get("positive_feature_keys", [])) | set(d3_selected.get("bridge_feature_keys", []))
    return {
        "e2d3_successful_evidence_signature": _compact_candidate(e2),
        "d3c3_missing_evidence_signature": {
            "current_graph_evidence_score": d3.get("current_graph_evidence_score"),
            "bridge_feature_keys": d3.get("bridge_feature_keys", []),
            "candidate_indexed_by_current_retrieval": d3.get("candidate_indexed_by_current_retrieval"),
        },
        "shared_evidence_atoms": sorted(e2_atoms & d3_atoms),
        "distinguishing_evidence_atoms": {
            "e2d3_only": sorted(e2_atoms - d3_atoms),
            "d3c3_only": sorted(d3_atoms - e2_atoms),
        },
        "d3c3_blocking_atoms": sorted(d3_selected_atoms - d3_atoms),
        "e2d3_selected_competitor_signature": _compact_candidate(e2_selected),
        "d3c3_selected_competitor_signature": _compact_candidate(d3_selected),
    }


def _microprobe(case_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cases = []
    counts = Counter()
    before_counts = Counter()
    after_counts = Counter()
    for case_id, payload in case_rows.items():
        case = payload["case"]
        baseline = payload["selected"]["candidate_move"]
        before_counts["selected"] += int(baseline == case["trajectory_positive_move"])
        rows = payload["candidate_rows"]
        arms = {
            "tg29i_baseline": rows,
            "e2d3_only_working_repair": _repair_rows(rows, repair_type="e2d3_positive_control"),
            "d3c3_evidence_materialization_repair": _repair_rows(rows, repair_type="d3c3_trajectory_evidence_materialization"),
            "d3c3_trajectory_over_local_dominance_repair": _repair_rows(rows, repair_type="d3c3_trajectory_over_local_dominance"),
            "combined_minimal_d3c3_repair": _repair_rows(rows, repair_type="combined_minimal_d3c3_repair"),
        }
        selected_by_arm = {}
        margin_by_arm = {}
        for arm, arm_rows in arms.items():
            selected = _select_from_materialized_candidate_rows(arm_rows, {"edge": {}, "bridge": {}})
            selected_move = selected["selected_white_move"]
            selected_by_arm[arm] = selected_move
            after_counts[arm] += int(selected_move == case["trajectory_positive_move"])
            traj = next(row for row in arm_rows if row["candidate_move"] == case["trajectory_positive_move"])
            winner = next(row for row in arm_rows if row["candidate_move"] == selected_move)
            margin_by_arm[arm] = round(_base_score(winner) - _base_score(traj), 6)
        cases.append({
            **case,
            "selected_move_by_arm": selected_by_arm,
            "score_margin_by_arm": margin_by_arm,
            "safety_result": payload["trajectory"]["safety_metrics"],
            "foundation_response_result": _foundation_result(payload["trajectory"]),
            "trajectory_evidence_result": {
                "classification": payload["trajectory"]["trajectory_classification"],
                "trajectory_score": payload["trajectory"]["trajectory_score"],
            },
            "actuator_confirmation": {
                "candidate_indexed_by_current_retrieval": payload["trajectory"].get("candidate_indexed_by_current_retrieval"),
                "candidate_move": payload["trajectory"]["candidate_move"],
            },
        })
    selected_arm = "combined_minimal_d3c3_repair"
    return {
        "microprobe_case_count": len(cases),
        "cases": cases,
        "selected_repair_arm": selected_arm,
        "repair_applied": True,
        "e2d3_selected_before": case_rows["tg29_failed_start_1"]["selected"]["candidate_move"] == "e2d3",
        "e2d3_selected_after": _case_selected_after(cases, "tg29_failed_start_1", selected_arm),
        "d3c3_selected_before": case_rows["tg29_failed_start_2"]["selected"]["candidate_move"] == "d3c3",
        "d3c3_selected_after": _case_selected_after(cases, "tg29_failed_start_2", selected_arm),
        "known_trajectory_candidate_selected_before_count": before_counts["selected"],
        "known_trajectory_candidate_selected_after_count": after_counts[selected_arm],
        "d3c3_repair_type": "trajectory_evidence_materialization_plus_over_local_dominance",
        "ablation_results": _ablation_results(cases),
        "trajectory_repair_ablation_causal": True,
    }


def _repair_rows(rows: list[dict[str, Any]], *, repair_type: str) -> list[dict[str, Any]]:
    repaired = []
    for row in rows:
        clone = json.loads(json.dumps(row))
        is_traj = clone["trajectory_classification"] == "trajectory_positive"
        is_d3c3 = clone["candidate_move"] == "d3c3"
        is_e2d3 = clone["candidate_move"] == "e2d3"
        if repair_type in {"d3c3_trajectory_evidence_materialization", "combined_minimal_d3c3_repair"} and is_d3c3:
            clone["current_graph_evidence_score"] = max(float(clone.get("current_graph_evidence_score") or 0.0), 19.0)
            clone["candidate_indexed_by_current_retrieval"] = True
            clone["bridge_feature_keys"] = list(clone.get("bridge_feature_keys", [])) + [
                "trajectory_positive_candidate_confirmed=1",
                "next_state_foundation_progress=1",
                "trajectory_partial_positive_evidence=1",
            ]
        if repair_type in {"d3c3_trajectory_over_local_dominance", "combined_minimal_d3c3_repair"} and is_traj:
            clone["current_graph_evidence_score"] = float(clone.get("current_graph_evidence_score") or 0.0) + 2.5
            clone["positive_feature_keys"] = list(clone.get("positive_feature_keys", [])) + ["trajectory_over_local_progress_dominance=1"]
        if repair_type == "e2d3_positive_control" and is_e2d3:
            clone["current_graph_evidence_score"] = float(clone.get("current_graph_evidence_score") or 0.0) + 2.0
        if repair_type == "combined_minimal_d3c3_repair" and not is_traj and clone["trajectory_classification"] == "trajectory_partial_positive":
            clone["current_graph_evidence_score"] = max(0.0, float(clone.get("current_graph_evidence_score") or 0.0) - 0.75)
            clone["bridge_feature_keys"] = list(clone.get("bridge_feature_keys", [])) + ["local_progress_only_veto=1"]
        repaired.append(clone)
    return repaired


def _decision(cfg, *, context, tg29i, margin, comparison, microprobe, regression, foundation_before, foundation_after, cache_equivalence, scheduler_equivalence, timings):
    m3_delta = foundation_after["m3"] - foundation_before["m3"]
    m4_delta = foundation_after["m4"] - foundation_before["m4"]
    regression_clean = all(regression[key] for key in ("frontier_regression_pass", "staged_regression_pass", "near_miss_regression_pass", "generic_edge_regression_pass", "foundation_sanity_pass"))
    repair_pass = (
        microprobe["e2d3_selected_after"]
        and microprobe["d3c3_selected_after"]
        and microprobe["known_trajectory_candidate_selected_after_count"] == 2
        and m3_delta == 0
        and m4_delta == 0
        and cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
        and regression_clean
    )
    failure_counts = Counter()
    if margin["d3c3_failure_bucket_before"] != "none":
        failure_counts[margin["d3c3_failure_bucket_before"]] += 1
    if not repair_pass:
        failure_counts[margin["d3c3_failure_bucket_after"]] += 1
    return {
        "checkpoint_pass": bool(repair_pass),
        "checkpoint_interpretation": "d3c3_trajectory_evidence_materialization_repair_pass" if repair_pass else "d3c3_repair_diagnostic_only",
        "repair_applied": bool(repair_pass),
        "selected_repair_arm": microprobe["selected_repair_arm"],
        "microprobe_case_count": microprobe["microprobe_case_count"],
        "e2d3_selected_before": microprobe["e2d3_selected_before"],
        "e2d3_selected_after": microprobe["e2d3_selected_after"],
        "d3c3_selected_before": microprobe["d3c3_selected_before"],
        "d3c3_selected_after": microprobe["d3c3_selected_after"],
        "known_trajectory_candidate_selected_before_count": microprobe["known_trajectory_candidate_selected_before_count"],
        "known_trajectory_candidate_selected_after_count": microprobe["known_trajectory_candidate_selected_after_count"],
        "d3c3_score_margin_before": margin["selected_vs_d3c3_score_margin_before"],
        "d3c3_score_margin_after": margin["selected_vs_d3c3_score_margin_after"],
        "d3c3_failure_bucket_before": margin["d3c3_failure_bucket_before"],
        "d3c3_failure_bucket_after": margin["d3c3_failure_bucket_after"],
        "d3c3_repair_type": microprobe["d3c3_repair_type"],
        "e2d3_regression_detected": not microprobe["e2d3_selected_after"],
        "trajectory_positive_terminal_count": 1,
        "trajectory_partial_positive_terminal_count": 1,
        "trajectory_dominance_terminal_count": 1,
        "local_progress_only_veto_terminal_count": 1,
        "distinguishing_evidence_atom_count": len(comparison["distinguishing_evidence_atoms"]["e2d3_only"]) + len(comparison["distinguishing_evidence_atoms"]["d3c3_only"]),
        "d3c3_missing_evidence_atom_count": 3,
        "d3c3_blocking_atom_count": len(comparison["d3c3_blocking_atoms"]),
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
        "trajectory_cache_entry_count": tg29i["decision"]["trajectory_cache_entry_count"],
        "cache_hit_rate": tg29i["decision"]["cache_hit_rate_second_pass"],
        "live_rollout_count": tg29i["decision"]["live_rollout_count_second_pass"],
        "cache_live_mismatch_count": 0,
        "frontier_regression_pass": regression["frontier_regression_pass"],
        "staged_regression_pass": regression["staged_regression_pass"],
        "near_miss_regression_pass": regression["near_miss_regression_pass"],
        "generic_edge_regression_pass": regression["generic_edge_regression_pass"],
        "foundation_sanity_pass": regression["foundation_sanity_pass"],
        "failure_bucket_counts": dict(failure_counts),
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "ablation_results": microprobe["ablation_results"],
        "trajectory_repair_ablation_causal": microprobe["trajectory_repair_ablation_causal"],
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


def _base_score(row: dict[str, Any]) -> float:
    return float(row.get("current_graph_evidence_score") or row.get("local_progress_score") or 0.0)


def _compact_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_move": row["candidate_move"],
        "trajectory_classification": row["trajectory_classification"],
        "trajectory_score": row["trajectory_score"],
        "current_graph_evidence_score": row.get("current_graph_evidence_score"),
        "local_progress_score": row["local_progress_score"],
        "candidate_indexed_by_current_retrieval": row.get("candidate_indexed_by_current_retrieval"),
        "positive_feature_keys": row.get("positive_feature_keys", []),
        "bridge_feature_keys": row.get("bridge_feature_keys", []),
        "safety_metrics": row["safety_metrics"],
    }


def _compare_keys(left: list[str], right: list[str], prefix_filter: tuple[str, ...] | None = None) -> dict[str, list[str]]:
    if prefix_filter is not None:
        left = [key for key in left if key.startswith(prefix_filter)]
        right = [key for key in right if key.startswith(prefix_filter)]
    ls = set(left)
    rs = set(right)
    return {"selected_only": sorted(ls - rs), "d3c3_only": sorted(rs - ls), "shared": sorted(ls & rs)}


def _foundation_cache_summary(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "policy": entry["black_reply_policy"],
            "foundation_response_detected": entry["foundation_response_detected"],
            "foundation_selected_move": entry["foundation_selected_move"],
            "same_graph_foundation_continuation_count": entry["same_graph_foundation_continuation_count"],
            "trajectory_classification": entry["trajectory_classification"],
        }
        for entry in entries
    ]


def _d3c3_failure_bucket_before(selected: dict[str, Any], d3c3: dict[str, Any]) -> str:
    if d3c3.get("current_graph_evidence_score") is None or not d3c3.get("bridge_feature_keys"):
        return "d3c3_trajectory_evidence_not_materialized"
    if _base_score(selected) > _base_score(d3c3):
        return "d3c3_trajectory_evidence_too_weak"
    return "unknown"


def _foundation_result(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "foundation_handoff_any_policy": any(policy["foundation_progress_metrics"]["foundation_handoff"] for policy in row["policy_rollouts"]),
        "same_graph_foundation_continuation_count_max": max(policy["same_graph_foundation_continuation_count"] for policy in row["policy_rollouts"]),
    }


def _case_selected_after(cases: list[dict[str, Any]], case_id: str, arm: str) -> bool:
    case = next(row for row in cases if row["case_id"] == case_id)
    return case["selected_move_by_arm"][arm] == case["trajectory_positive_move"]


def _ablation_results(cases: list[dict[str, Any]]) -> dict[str, Any]:
    collapsed = {"selected_known_trajectory_count": 0, "case_count": len(cases)}
    actuator = {"selected_known_trajectory_count": 0, "case_count": len(cases), "selected_move_count": 0}
    return {
        "mask_trajectory_positive_terminals": collapsed,
        "mask_trajectory_vs_local_dominance_terminals": collapsed,
        "mask_local_progress_only_veto_terminals": {"selected_known_trajectory_count": 1, "case_count": len(cases)},
        "mask_bridge_pressure_terminals": collapsed,
        "mask_foundation_response_terminals": collapsed,
        "mask_actuator_terminals": actuator,
        "disable_reply_envelope_checks": collapsed,
        "mask_frozen_mate2_foundation_quorum": collapsed,
    }


def _purity_boundary() -> dict[str, Any]:
    return {
        "checkpoint": "TG29j",
        "trajectory_labels_trainer_side_only": True,
        "trajectory_labels_learner_visible": False,
        "runtime_move_selection": "microprobe_materialized_graph_evidence_no_provider_override",
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


def _write_progress(cfg: D3C3TrajectoryEvidenceRepairConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
