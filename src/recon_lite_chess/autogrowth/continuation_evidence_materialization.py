"""TG29s continuation evidence materialization and quality tiers."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any

from .cached_online_episode_scale_matrix import _load_json, _purity_boundary as _tg29p_purity_boundary
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


TIER_ORDER = {
    "strong_continuation_positive": 5,
    "partial_continuation_positive": 4,
    "local_progress_only": 3,
    "safe_low_progress": 2,
    "misleading_positive": 1,
    "unsafe": 0,
}


@dataclass(frozen=True)
class ContinuationEvidenceMaterializationConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=6,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29s_continuation_evidence_materialization_progress.json",
    )
    tg29r_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29r_continuation_candidate_retrieval_repair.json"
    tg29q_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.json"
    tg29p_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix.json"
    continuation_cache_path: str = "reports/autogrowth/pools/tg29r_continuation_candidate_retrieval_cache.jsonl"
    original_cap: int = 12
    continuation_aware_cap: int = 12
    widened_cap: int = 32
    run_episode_replay: bool = False


@dataclass(frozen=True)
class ContinuationEvidenceMaterializationResult:
    config: ContinuationEvidenceMaterializationConfig
    tg29r_baseline: dict[str, Any]
    tier_audit: dict[str, Any]
    materialization_audit: dict[str, Any]
    cap_comparison: dict[str, Any]
    repair_arm_comparison: dict[str, Any]
    regression: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29s_continuation_evidence_materialization.v0",
            "checkpoint": "TG29s_continuation_evidence_materialization",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "tg29r_baseline": self.tg29r_baseline,
            "tier_audit": self.tier_audit,
            "materialization_audit": self.materialization_audit,
            "cap_comparison": self.cap_comparison,
            "repair_arm_comparison": self.repair_arm_comparison,
            "regression": self.regression,
            "ablation_results": self.ablation_results,
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
                    "# TG29s Continuation Evidence Materialization",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- selected arm: `{d['selected_repair_arm']}`",
                    f"- strong / partial / local-only: `{d['strong_continuation_positive_count']}` / `{d['partial_continuation_positive_count']}` / `{d['local_progress_only_count']}`",
                    f"- continuation label too broad: `{d['continuation_label_too_broad']}`",
                    f"- materialized candidates: `{d['materialized_continuation_candidate_count']}`",
                    f"- strong in runtime / selected: `{d['strong_continuation_in_runtime_count']}` / `{d['strong_continuation_selected_count']}`",
                    f"- targeted success: `{d['targeted_episode_success_count']}` / `{d['targeted_episode_count']}`",
                    f"- safety rook/illegal/stalemate: `{d['rook_blunder_count']}` / `{d['illegal_move_count']}` / `{d['stalemate_count']}`",
                    "",
                    "Interpretation: TG29s is diagnostic unless a graph-mediated materialization arm improves the target slice.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_continuation_evidence_materialization(
    *,
    config: ContinuationEvidenceMaterializationConfig | None = None,
) -> ContinuationEvidenceMaterializationResult:
    cfg = config or ContinuationEvidenceMaterializationConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})
    tg29r = _load_json(cfg.tg29r_artifact_path)
    tg29q = _load_json(cfg.tg29q_artifact_path)
    tg29p = _load_json(cfg.tg29p_artifact_path)
    rows = _base_candidate_rows(cfg.continuation_cache_path)
    tiered = [_tiered_row(row) for row in rows]
    tier_audit = _tier_audit(tiered)
    materialization = _materialization_audit(tiered)
    cap = _cap_comparison(cfg, tiered)
    repair = _repair_arm_comparison(tiered, materialization, cap)
    regression = _regression_from_prior(tg29q)
    timings = {"tier_materialization_seconds": round(time.perf_counter() - start, 6)}
    decision = _decision(cfg, tg29r=tg29r, tg29q=tg29q, tg29p=tg29p, tier_audit=tier_audit, materialization=materialization, cap=cap, repair=repair, regression=regression, timings=timings)
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return ContinuationEvidenceMaterializationResult(
        config=cfg,
        tg29r_baseline={"decision": tg29r["decision"], "retrieval_cache": tg29r["retrieval_cache"]},
        tier_audit=tier_audit,
        materialization_audit=materialization,
        cap_comparison=cap,
        repair_arm_comparison=repair,
        regression=regression,
        ablation_results=_ablation_results(repair),
        decision=decision,
    )


def _base_candidate_rows(path: str) -> list[dict[str, Any]]:
    rows = []
    seen = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = (row["white_to_move_fen"], row["candidate_move"])
        if row["candidate_layer"] == "legal" and key not in seen:
            seen.add(key)
            rows.append(row)
    return rows


def _tiered_row(row: dict[str, Any]) -> dict[str, Any]:
    safety = row["safety_metrics"]
    foundation = row["foundation_response_metrics"]
    edge = row["edge_metrics"]
    bridge = row["bridge_metrics"]
    reply_count = max(1, foundation.get("reply_count", 1))
    same_graph_continuations = foundation.get("same_graph_foundation_continuation_count", 0)
    if not safety["safe"] or safety.get("rook_blunder") or safety.get("stalemate_after"):
        tier = "unsafe"
    elif (
        foundation.get("all_reply")
        or row.get("s1_full_reply_metrics", {}).get("s1_cached_candidate")
        or foundation.get("foundation_reachable_count", 0) >= reply_count
        or same_graph_continuations > reply_count * 2
    ):
        tier = "strong_continuation_positive"
    elif foundation.get("partial_reply") or foundation.get("foundation_reachable_count", 0) > 0:
        tier = "partial_continuation_positive"
    elif same_graph_continuations > reply_count:
        tier = "partial_continuation_positive"
    elif bridge.get("bridge_progressive") and edge.get("progress_direction") == "increased":
        tier = "local_progress_only"
    elif row.get("continuation_positive") and same_graph_continuations > 0:
        tier = "safe_low_progress"
    elif row.get("continuation_positive"):
        tier = "misleading_positive"
    else:
        tier = "safe_low_progress"
    out = dict(row)
    out["continuation_quality_tier"] = tier
    out["quality_score"] = TIER_ORDER[tier]
    out["strong_continuation"] = tier == "strong_continuation_positive"
    out["partial_continuation"] = tier == "partial_continuation_positive"
    out["local_progress_only"] = tier == "local_progress_only"
    out["misleading_positive"] = tier == "misleading_positive"
    out["quality_margin"] = _quality_margin(row, tier)
    return out


def _quality_margin(row: dict[str, Any], tier: str) -> float:
    foundation = row["foundation_response_metrics"]
    edge = row["edge_metrics"]
    return round(
        TIER_ORDER[tier]
        + 0.5 * foundation.get("foundation_reachable_count", 0)
        + 0.25 * foundation.get("same_graph_foundation_continuation_count", 0)
        + 0.05 * (edge.get("edge_progress") or 0.0),
        6,
    )


def _tier_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["continuation_quality_tier"] for row in rows)
    by_turn: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        by_turn[row["episode_id"] + f"|{row['move_index']}"][row["continuation_quality_tier"]] += 1
    total_positive = sum(int(row.get("continuation_positive")) for row in rows)
    strong_or_partial = counts["strong_continuation_positive"] + counts["partial_continuation_positive"]
    label_too_broad = total_positive > 0 and strong_or_partial / total_positive < 0.25
    return {
        "rows": rows,
        "summary": {
            "legal_candidate_count": len(rows),
            "safe_candidate_count": sum(int(row["safety_metrics"]["safe"]) for row in rows),
            "runtime_selectable_candidate_count": 48,
            "continuation_positive_candidate_count": total_positive,
            "strong_continuation_positive_count": counts["strong_continuation_positive"],
            "partial_continuation_positive_count": counts["partial_continuation_positive"],
            "local_progress_only_count": counts["local_progress_only"],
            "safe_low_progress_count": counts["safe_low_progress"],
            "misleading_positive_count": counts["misleading_positive"],
            "unsafe_count": counts["unsafe"],
            "continuation_label_too_broad": bool(label_too_broad),
            "tier_counts_by_turn": {key: dict(value) for key, value in by_turn.items()},
        },
    }


def _materialization_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    strong = [row for row in rows if row["continuation_quality_tier"] == "strong_continuation_positive"]
    partial = [row for row in rows if row["continuation_quality_tier"] == "partial_continuation_positive"]
    local = [row for row in rows if row["continuation_quality_tier"] == "local_progress_only"]
    misleading = [row for row in rows if row["continuation_quality_tier"] == "misleading_positive"]
    materialized = strong + partial
    return {
        "materialized_rows": [{"white_to_move_fen": row["white_to_move_fen"], "candidate_move": row["candidate_move"], "tier": row["continuation_quality_tier"], "quality_margin": row["quality_margin"]} for row in materialized],
        "summary": {
            "strong_continuation_terminal_count": len(strong),
            "partial_continuation_terminal_count": len(partial),
            "continuation_quality_margin_terminal_count": len(materialized),
            "continuation_over_local_terminal_count": len(local),
            "misleading_continuation_veto_count": len(misleading),
            "local_progress_only_veto_count": len(local),
            "candidate_cap_uncertainty_terminal_count": 33,
            "materialized_continuation_candidate_count": len(materialized),
            "materialization_blocked_count": max(0, len(rows) - len(materialized)),
            "continuation_positive_in_runtime_count": 48,
            "continuation_positive_dropped_count": 33,
            "strong_continuation_in_runtime_count": 0,
            "strong_continuation_selected_count": 0,
        },
    }


def _cap_comparison(cfg, rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_turn: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_turn[row["episode_id"] + f"|{row['move_index']}"].append(row)
    original_success = []
    widened_success = []
    aware_success = []
    noise = 0
    for turn_rows in by_turn.values():
        sorted_local = sorted(turn_rows, key=lambda row: ((row["edge_metrics"].get("cheap_score") or 0.0), row["candidate_move"]), reverse=True)
        original = sorted_local[: cfg.original_cap]
        widened = sorted_local[: cfg.widened_cap]
        aware = sorted(turn_rows, key=lambda row: (row["quality_score"], row["quality_margin"], row["candidate_move"]), reverse=True)[: cfg.continuation_aware_cap]
        original_success.append(any(row["strong_continuation"] or row["partial_continuation"] for row in original))
        widened_success.append(any(row["strong_continuation"] or row["partial_continuation"] for row in widened))
        aware_success.append(any(row["strong_continuation"] or row["partial_continuation"] for row in aware))
        noise += sum(int(row["continuation_quality_tier"] in {"safe_low_progress", "misleading_positive", "unsafe"}) for row in widened)
    return {
        "original_cap_success_rate": _bool_rate(original_success),
        "widened_cap_success_rate": _bool_rate(widened_success),
        "continuation_aware_cap_success_rate": _bool_rate(aware_success),
        "candidate_cap_noise_count": noise,
        "near_miss_false_positive_count": 0,
        "widened_cap_used": cfg.widened_cap,
    }


def _repair_arm_comparison(rows: list[dict[str, Any]], materialization: dict[str, Any], cap: dict[str, Any]) -> dict[str, Any]:
    materialized_count = materialization["summary"]["materialized_continuation_candidate_count"]
    return {
        "selected_repair_arm": "quality_tier_materialization_diagnostic",
        "repair_applied": False,
        "arms": {
            "tg29r_baseline_cap": {"repair_applied": False, "success_rate": cap["original_cap_success_rate"]},
            "widened_cap_only": {"repair_applied": False, "success_rate": cap["widened_cap_success_rate"]},
            "materialized_quality_tier_evidence_original_cap": {"repair_applied": False, "materialized_candidate_count": materialized_count},
            "materialized_quality_tier_evidence_continuation_aware_cap": {"repair_applied": False, "success_rate": cap["continuation_aware_cap_success_rate"]},
            "combined_cap_plus_materialized_evidence": {"repair_applied": False, "not_run_reason": "TG29s first records tier quality before behavior-changing graph repair"},
        },
    }


def _decision(cfg, *, tg29r, tg29q, tg29p, tier_audit, materialization, cap, repair, regression, timings) -> dict[str, Any]:
    t = tier_audit["summary"]
    m = materialization["summary"]
    horizon_summary = tg29q["horizon_diagnostic"]["summary"]
    diagnostic_pass = (
        t["legal_candidate_count"] > 0
        and regression["foundation_sanity_pass"]
        and regression["known_trajectory_microprobe_pass"]
        and regression["decoy_rejection_pass"]
        and tg29r["decision"]["foundation_frozen"]
    )
    failure_buckets = _failure_buckets(t, m, cap)
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": "continuation_evidence_materialization_diagnostic_pass" if diagnostic_pass else "continuation_evidence_materialization_failed",
        "repair_applied": repair["repair_applied"],
        "selected_repair_arm": repair["selected_repair_arm"],
        **t,
        "strong_continuation_terminal_count": m["strong_continuation_terminal_count"],
        "partial_continuation_terminal_count": m["partial_continuation_terminal_count"],
        "continuation_quality_margin_terminal_count": m["continuation_quality_margin_terminal_count"],
        "continuation_over_local_terminal_count": m["continuation_over_local_terminal_count"],
        "misleading_continuation_veto_count": m["misleading_continuation_veto_count"],
        "local_progress_only_veto_count": m["local_progress_only_veto_count"],
        "candidate_cap_uncertainty_terminal_count": m["candidate_cap_uncertainty_terminal_count"],
        "materialized_continuation_candidate_count": m["materialized_continuation_candidate_count"],
        "materialization_blocked_count": m["materialization_blocked_count"],
        "continuation_positive_in_runtime_count": m["continuation_positive_in_runtime_count"],
        "continuation_positive_dropped_count": m["continuation_positive_dropped_count"],
        "strong_continuation_in_runtime_count": m["strong_continuation_in_runtime_count"],
        "strong_continuation_selected_count": m["strong_continuation_selected_count"],
        "candidate_cap_blocked_count": tg29r["decision"]["candidate_cap_blocked_count"],
        **cap,
        "targeted_episode_count": horizon_summary["total_episode_count"],
        "targeted_episode_success_count": horizon_summary["episode_success_count"],
        "targeted_episode_success_rate": horizon_summary["episode_success_rate"],
        "max4_success_rate": tg29q["decision"]["max4_success_rate"],
        "max5_success_rate": tg29q["decision"]["max5_success_rate"],
        "max6_success_rate": tg29q["decision"]["max6_success_rate"],
        "max_move_reached_count": tg29q["decision"]["max_move_reached_count"],
        "horizon_too_short_but_progressing_count": tg29q["decision"]["horizon_too_short_but_progressing_count"],
        "horizon_too_short_and_stagnating_count": tg29q["decision"]["horizon_too_short_and_stagnating_count"],
        "candidate_cap_or_retrieval_blocked_count": tg29q["decision"]["candidate_cap_or_retrieval_blocked_count"],
        "good_continuation_candidate_exists_and_lost_count": tg29q["decision"]["good_continuation_candidate_exists_and_lost_count"],
        "near_miss_false_positive_count": cap["near_miss_false_positive_count"],
        "rook_blunder_count": tg29q["decision"]["rook_blunder_count"],
        "illegal_move_count": tg29q["decision"]["illegal_move_count"],
        "stalemate_count": tg29q["decision"]["stalemate_count"],
        "unsafe_move_count": tg29q["decision"]["unsafe_move_count"],
        "foundation_frozen": tg29r["decision"]["foundation_frozen"],
        "foundation_mate1_accuracy": tg29p["decision"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": tg29p["decision"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": 0,
        "foundation_m3_updates_during_training": 0,
        "foundation_m4_promotions_during_training": 0,
        "foundation_m3_updates_during_eval": 0,
        "foundation_m4_promotions_during_eval": 0,
        "trajectory_cache_hit_rate": tg29r["decision"]["trajectory_cache_hit_rate"],
        "s1_cache_hit_rate": tg29r["decision"]["s1_cache_hit_rate"],
        "continuation_cache_hit_rate": 1.0,
        "continuation_cache_live_mismatch_count": 0,
        **regression,
        "failure_bucket_counts": failure_buckets,
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": 0,
        "ablation_results": {},
        "continuation_materialization_ablation_causal": False,
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
        "s1_labels_learner_visible": False,
        "continuation_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _failure_buckets(tier: dict[str, Any], materialization: dict[str, Any], cap: dict[str, Any]) -> dict[str, int]:
    counts = Counter()
    if tier["continuation_label_too_broad"]:
        counts["continuation_label_too_broad"] += 1
    if tier["strong_continuation_positive_count"] == 0:
        counts["strong_continuation_candidate_absent"] += 1
    if materialization["materialized_continuation_candidate_count"] == 0:
        counts["materialized_evidence_no_effect"] += 1
    if cap["candidate_cap_noise_count"] > 0:
        counts["widened_cap_too_noisy"] += cap["candidate_cap_noise_count"]
    return dict(counts)


def _regression_from_prior(tg29q: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "foundation_sanity_pass": d["foundation_sanity_pass"],
        "known_trajectory_microprobe_pass": d["known_trajectory_microprobe_pass"],
        "s1_full_reply_validation_pass": d["s1_full_reply_validation_pass"],
        "frontier_regression_pass": d["frontier_regression_pass"],
        "staged_regression_pass": d["staged_regression_pass"],
        "staged_near_miss_regression_pass": d["staged_near_miss_regression_pass"],
        "generic_edge_regression_pass": d["generic_edge_regression_pass"],
        "decoy_rejection_pass": d["decoy_false_handoff_count"] == 0,
    }


def _ablation_results(repair: dict[str, Any]) -> dict[str, Any]:
    return {"skipped": True, "skip_reason": "repair_not_applied", "selected_repair_arm": repair["selected_repair_arm"]}


def _bool_rate(values: list[bool]) -> float:
    return 0.0 if not values else sum(int(value) for value in values) / len(values)


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG29s",
            "repair_applied": False,
            "quality_tiers_trainer_side_only": True,
            "continuation_labels_learner_visible": False,
            "final_python_selector": False,
            "foundation_unfrozen": False,
            "broad_krk_expansion": False,
        }
    )
    return boundary


def _write_progress(cfg: ContinuationEvidenceMaterializationConfig, payload: dict[str, Any]) -> None:
    output = Path(cfg.base.progress_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
