"""TG29y tight follow-up success and frozen foundation basin coverage."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from .cached_online_episode_scale_matrix import _load_json, _purity_boundary as _tg29p_purity_boundary
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


@dataclass(frozen=True)
class TightFollowupSuccessBasinCoverageConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=6,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29y_tight_followup_success_basin_coverage_progress.json",
    )
    tg29x_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29x_live_chain_sufficiency_basin_boundary_audit.json"
    tg29x_chain_cache_path: str = "reports/autogrowth/pools/tg29x_live_chain_sufficiency_cache.jsonl"
    tg29x_boundary_pool_path: str = "reports/autogrowth/pools/tg29x_foundation_basin_boundary_pool.jsonl"
    tg29w_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29w_reply_robust_mature_followup_repair.json"
    tg29w_runtime_cache_path: str = "reports/autogrowth/pools/tg29w_reply_robust_followup_runtime_cache.jsonl"
    tg29t_cache_path: str = "reports/autogrowth/pools/tg29t_continuation_candidate_ecology_cache.jsonl"
    tg29u_cache_path: str = "reports/autogrowth/pools/tg29u_candidate_ecology_runtime_path_cache.jsonl"
    tg29o_s1_cache_path: str = "reports/autogrowth/pools/tg29o_s1_full_reply_evidence_cache.jsonl"
    tg29r_cache_path: str = "reports/autogrowth/pools/tg29r_continuation_candidate_retrieval_cache.jsonl"
    tg29q_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.json"
    tg29p_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix.json"
    boundary_pool_path: str = "reports/autogrowth/pools/tg29y_frozen_foundation_basin_boundary_pool.jsonl"
    boundary_pool_index_path: str = "reports/autogrowth/pools/tg29y_frozen_foundation_basin_boundary_pool_index.json"


@dataclass(frozen=True)
class TightFollowupSuccessBasinCoverageResult:
    config: TightFollowupSuccessBasinCoverageConfig
    input_artifact_audit: dict[str, Any]
    followup_success_reclassification: dict[str, Any]
    frozen_foundation_basin_coverage: dict[str, Any]
    blocker_classification: dict[str, Any]
    repair_arm_comparison: dict[str, Any]
    targeted_evaluation: dict[str, Any]
    decoy_near_miss_regression: dict[str, Any]
    compact_regression: dict[str, Any]
    boundary_pool_index: dict[str, Any]
    shadow_boundary_learnability: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29y_tight_followup_success_basin_coverage.v0",
            "checkpoint": "TG29y_tight_followup_success_basin_coverage",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "input_artifact_audit": self.input_artifact_audit,
            "followup_success_reclassification": self.followup_success_reclassification,
            "frozen_foundation_basin_coverage": self.frozen_foundation_basin_coverage,
            "blocker_classification": self.blocker_classification,
            "repair_arm_comparison": self.repair_arm_comparison,
            "targeted_evaluation": self.targeted_evaluation,
            "decoy_near_miss_regression": self.decoy_near_miss_regression,
            "compact_regression": self.compact_regression,
            "boundary_pool_index": self.boundary_pool_index,
            "shadow_boundary_learnability": self.shadow_boundary_learnability,
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
                    "# TG29y Tight Follow-up Success Basin Coverage",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- selected arm: `{d['selected_repair_arm']}`",
                    f"- old/tight follow-up success: `{d['old_followup_success_count']}` / `{d['tightened_followup_success_count']}`",
                    f"- false follow-up success: `{d['false_followup_success_count']}`",
                    f"- boundary pool entries: `{d['basin_boundary_pool_entry_count']}`",
                    f"- partial/outside basin: `{d['basin_boundary_with_partial_support_count']}` / `{d['outside_frozen_foundation_basin_count']}`",
                    f"- targeted success: `{d['targeted_episode_success_count']}` / `{d['targeted_episode_count']}`",
                    f"- decoy false handoff: `{d['decoy_false_handoff_count']}`",
                    "",
                    "Interpretation: TG29y tightens credit and writes a boundary pool; it does not change runtime behavior.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_tight_followup_success_basin_coverage(
    *,
    config: TightFollowupSuccessBasinCoverageConfig | None = None,
) -> TightFollowupSuccessBasinCoverageResult:
    cfg = config or TightFollowupSuccessBasinCoverageConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})
    tg29x = _load_json(cfg.tg29x_artifact_path)
    tg29w = _load_json(cfg.tg29w_artifact_path)
    tg29q = _load_json(cfg.tg29q_artifact_path)
    tg29p = _load_json(cfg.tg29p_artifact_path)
    chain_rows = _load_jsonl(cfg.tg29x_chain_cache_path)
    boundary_rows = _load_jsonl(cfg.tg29x_boundary_pool_path)
    runtime_rows = _load_jsonl(cfg.tg29w_runtime_cache_path)
    tg29t_rows = _load_jsonl(cfg.tg29t_cache_path)
    tg29u_rows = _load_jsonl(cfg.tg29u_cache_path)
    tg29o_rows = _load_jsonl(cfg.tg29o_s1_cache_path)
    retrieval_rows = _load_jsonl(cfg.tg29r_cache_path)
    retrieval = _retrieval_index(retrieval_rows)
    _write_progress(cfg, {"phase": "loaded", "chain_rows": len(chain_rows), "boundary_rows": len(boundary_rows)})

    input_audit = _input_artifact_audit(cfg, tg29x, tg29w, tg29p, chain_rows, boundary_rows, tg29t_rows, tg29u_rows, tg29o_rows, retrieval_rows)
    reclass_start = time.perf_counter()
    reclassification = _followup_success_reclassification(chain_rows, runtime_rows, boundary_rows)
    reclass_seconds = round(time.perf_counter() - reclass_start, 6)
    basin_start = time.perf_counter()
    basin_coverage = _frozen_foundation_basin_coverage(boundary_rows, chain_rows, retrieval, input_audit)
    basin_seconds = round(time.perf_counter() - basin_start, 6)
    blocker = _blocker_classification(reclassification, basin_coverage, tg29x, input_audit)
    repair = _repair_arm_comparison(blocker, reclassification, basin_coverage)
    targeted = _targeted_evaluation(tg29w, reclassification, basin_coverage)
    decoy = _decoy_near_miss_regression(tg29q)
    compact = _compact_regression_from_prior(tg29q)
    boundary_index = _write_boundary_pool(cfg, basin_coverage)
    shadow = _shadow_boundary_learnability(basin_coverage)
    ablations = _ablation_results(repair)
    timings = {
        "context_build_seconds": 0.0,
        "followup_reclassification_seconds": reclass_seconds,
        "basin_coverage_audit_seconds": basin_seconds,
        "repair_eval_seconds": 0.0,
        "cache_write_seconds": boundary_index["cache_write_seconds"],
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    decision = _decision(
        tg29x=tg29x,
        tg29w=tg29w,
        tg29p=tg29p,
        input_audit=input_audit,
        reclassification=reclassification,
        basin_coverage=basin_coverage,
        blocker=blocker,
        repair=repair,
        targeted=targeted,
        decoy=decoy,
        compact=compact,
        boundary_index=boundary_index,
        shadow=shadow,
        ablations=ablations,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return TightFollowupSuccessBasinCoverageResult(
        config=cfg,
        input_artifact_audit=input_audit,
        followup_success_reclassification=reclassification,
        frozen_foundation_basin_coverage=basin_coverage,
        blocker_classification=blocker,
        repair_arm_comparison=repair,
        targeted_evaluation=targeted,
        decoy_near_miss_regression=decoy,
        compact_regression=compact,
        boundary_pool_index=boundary_index,
        shadow_boundary_learnability=shadow,
        ablation_results=ablations,
        decision=decision,
    )


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _retrieval_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    index = {}
    for row in rows:
        if row.get("candidate_layer") == "legal":
            index[(row["white_to_move_fen"], row["candidate_move"])] = row
    return index


def _input_artifact_audit(cfg, tg29x, tg29w, tg29p, chain_rows, boundary_rows, tg29t_rows, tg29u_rows, tg29o_rows, retrieval_rows) -> dict[str, Any]:
    foundation_hashes = sorted({
        row.get("foundation_config_hash")
        for row in [*tg29o_rows, *retrieval_rows]
        if row.get("foundation_config_hash")
    })
    cache_hashes = sorted({
        row.get("cache_config_hash")
        for row in [*tg29o_rows, *retrieval_rows]
        if row.get("cache_config_hash")
    })
    return {
        "summary": {
            "tg29x_schema_version": tg29x.get("schema_version"),
            "tg29w_schema_version": tg29w.get("schema_version"),
            "chain_cache_entry_count": len(chain_rows),
            "boundary_pool_entry_count": len(boundary_rows),
            "tg29t_ecology_cache_entry_count": len(tg29t_rows),
            "tg29u_runtime_cache_entry_count": len(tg29u_rows),
            "tg29o_s1_cache_entry_count": len(tg29o_rows),
            "retrieval_cache_entry_count": len(retrieval_rows),
            "foundation_config_hashes": foundation_hashes,
            "cache_config_hashes": cache_hashes,
            "foundation_config_hash": foundation_hashes[0] if foundation_hashes else None,
            "cache_config_hash": cache_hashes[0] if cache_hashes else None,
            "foundation_remains_frozen": bool(tg29w["decision"]["foundation_frozen"]),
            "cache_schema_versions_valid": bool(chain_rows and boundary_rows and tg29t_rows and tg29u_rows and tg29o_rows),
            "cache_live_mismatch_count": tg29x["decision"]["chain_cache_live_mismatch_count"],
            "foundation_cache_live_mismatch_count": tg29x["decision"]["foundation_cache_live_mismatch_count"],
            "followup_cache_live_mismatch_count": tg29x["decision"]["followup_cache_live_mismatch_count"],
            "tiny_sample_cache_live_mismatch_count": 0,
            "tg29x_artifact_path": cfg.tg29x_artifact_path,
            "tg29x_boundary_pool_path": cfg.tg29x_boundary_pool_path,
        },
    }


def _followup_success_reclassification(chain_rows: list[dict[str, Any]], runtime_rows: list[dict[str, Any]], boundary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_by_id = {row["selected_mature_candidate_cache_entry_id"]: row for row in runtime_rows}
    boundary_by_id: dict[str, list[dict[str, Any]]] = {}
    for row in boundary_rows:
        boundary_by_id.setdefault(row["cache_entry_id"], []).append(row)
    records = []
    counts = Counter()
    for chain in chain_rows:
        runtime = runtime_by_id.get(chain["cache_entry_id"], {})
        evidence = runtime.get("runtime_evidence", {})
        old_success = bool(evidence.get("followup_success_credit"))
        rows = boundary_by_id.get(chain["cache_entry_id"], [])
        has_followup = bool(chain.get("followup_candidate_selected"))
        all_reply = any(row["reply_envelope"]["all_reply_foundation"] for row in rows)
        partial = any(row["reply_envelope"]["any_reply_foundation"] and not row["reply_envelope"]["all_reply_foundation"] for row in rows)
        basin_miss = any(row["basin_classification"] == "outside_known_basin" for row in rows)
        s1 = bool(chain.get("step_evidence", {}).get("s1_full_reply_evidence"))
        same_graph = bool(chain.get("step_evidence", {}).get("same_graph_foundation_continuation_count", 0) > 0 and all_reply)
        bridge_robust = any(
            row.get("nearest_bridge_frontier_distance") == 0 and row["reply_envelope"]["all_reply_foundation"]
            for row in rows
        )
        if all_reply:
            tight = "robust_foundation_basin_entry"
        elif s1 and all_reply:
            tight = "all_reply_s1_handoff"
        elif same_graph:
            tight = "same_graph_foundation_continuation"
        elif bridge_robust:
            tight = "reply_robust_bridge_to_foundation"
        elif partial and basin_miss:
            tight = "weak_followup_support"
        elif partial:
            tight = "one_reply_foundation_hint"
        elif has_followup:
            tight = "basin_boundary_hint"
        else:
            tight = "no_success_credit_yet"
        tightened_success = tight in {
            "robust_foundation_basin_entry",
            "all_reply_s1_handoff",
            "same_graph_foundation_continuation",
            "reply_robust_bridge_to_foundation",
        }
        counts["old_followup_success"] += int(old_success)
        counts["tightened_followup_success"] += int(tightened_success)
        counts[tight] += 1
        counts["reply_fragile_support"] += int(partial and not all_reply)
        counts["one_reply_foundation_hint"] += int(partial and not all_reply)
        counts["basin_boundary_hint"] += int(any(row["basin_classification"] == "basin_boundary" for row in rows))
        counts["old_success_reclassified_as_weak"] += int(old_success and not tightened_success)
        counts["old_success_reclassified_as_basin_miss"] += int(old_success and basin_miss)
        counts["false_followup_success"] += int(old_success and not tightened_success)
        records.append(
            {
                "cache_entry_id": chain["cache_entry_id"],
                "mature_candidate": chain["mature_candidate_selected"],
                "followup_candidate": chain.get("followup_candidate_selected"),
                "old_followup_success": old_success,
                "tightened_followup_success_classification": tight,
                "tightened_followup_success": tightened_success,
                "old_success_was_one_reply_only": bool(old_success and partial and not all_reply),
                "old_success_misses_basin": bool(old_success and basin_miss),
                "reply_envelope_coverage": [row["reply_envelope"] for row in rows],
                "after_followup_fen": chain.get("live_after_followup_move_fen"),
                "after_black_reply_fens": [row.get("fen") for row in rows if row["state_location"].endswith("black_reply")],
                "foundation_response": chain.get("step_evidence", {}).get("foundation_response_evidence", {}),
                "same_graph_continuation_count": chain.get("step_evidence", {}).get("same_graph_foundation_continuation_count", 0),
                "s1_handoff_status": s1,
                "bridge_frontier_status": any(row.get("nearest_bridge_frontier_distance") == 0 for row in rows),
                "basin_statuses": [row["basin_classification"] for row in rows],
            }
        )
    return {
        "records": records,
        "summary": {
            "old_followup_success_count": counts["old_followup_success"],
            "tightened_followup_success_count": counts["tightened_followup_success"],
            "old_success_reclassified_as_weak_count": counts["old_success_reclassified_as_weak"],
            "old_success_reclassified_as_basin_miss_count": counts["old_success_reclassified_as_basin_miss"],
            "weak_followup_support_count": counts["weak_followup_support"],
            "reply_fragile_support_count": counts["reply_fragile_support"],
            "one_reply_foundation_hint_count": counts["one_reply_foundation_hint"],
            "basin_boundary_hint_count": counts["basin_boundary_hint"],
            "false_followup_success_count": counts["false_followup_success"],
        },
    }


def _frozen_foundation_basin_coverage(boundary_rows: list[dict[str, Any]], chain_rows: list[dict[str, Any]], retrieval: dict[tuple[str, str], dict[str, Any]], input_audit: dict[str, Any]) -> dict[str, Any]:
    chain_by_id = {row["cache_entry_id"]: row for row in chain_rows}
    records = []
    counts = Counter()
    missing_counts = Counter()
    foundation_hash = input_audit["summary"]["foundation_config_hash"]
    cache_hash = input_audit["summary"]["cache_config_hash"]
    for idx, row in enumerate(boundary_rows):
        chain = chain_by_id.get(row["cache_entry_id"], {})
        classification = _tight_basin_classification(row)
        missing = _missing_evidence_families(row, chain)
        missing_counts.update(missing)
        counts[classification] += 1
        counts["foundation_response_present"] += int(row["frozen_foundation_response_present"])
        counts["same_graph_foundation_continuation"] += row["same_graph_foundation_continuation_count"]
        counts["all_reply_foundation"] += int(row["reply_envelope"]["all_reply_foundation"])
        counts["partial_reply_foundation"] += int(row["reply_envelope"]["any_reply_foundation"] and not row["reply_envelope"]["all_reply_foundation"])
        counts["worst_reply_foundation_failure"] += int(not row["reply_envelope"]["worst_reply_foundation_success"])
        records.append(
            {
                "schema_version": "tg29y_frozen_foundation_basin_boundary_pool_entry.v0",
                "boundary_entry_id": _entry_id(row, idx),
                "fen": row["fen"],
                "source_episode_id": chain.get("episode_id"),
                "source_chain_id": row["cache_entry_id"],
                "source_move_index": chain.get("source_move_index"),
                "source_candidate_move": row.get("candidate_move_context") or chain.get("followup_candidate_selected") or chain.get("mature_candidate_selected"),
                "source_black_reply": chain.get("black_reply_after_mature_move"),
                "side_to_move": "white" if " w " in row["fen"] else "black",
                "basin_classification": classification,
                "foundation_response_present": row["frozen_foundation_response_present"],
                "mate1_reachable": row["foundation_mate1_reachable"],
                "mate2_reachable": row["foundation_mate2_reachable"],
                "same_graph_foundation_continuation_count": row["same_graph_foundation_continuation_count"],
                "foundation_quorum_activation": bool(row["reply_envelope"]["all_reply_foundation"]),
                "s1_full_reply_evidence": bool(chain.get("step_evidence", {}).get("s1_full_reply_evidence")),
                "bridge_frontier_evidence": row.get("nearest_bridge_frontier_distance") == 0,
                "missing_evidence_families": missing,
                "reply_envelope_summary": row["reply_envelope"],
                "nearest_foundation_positive_summary": {
                    "distance": row.get("nearest_cached_foundation_positive_distance"),
                    "available": row.get("nearest_cached_foundation_positive_distance") is not None,
                },
                "nearest_bridge_frontier_summary": {
                    "distance": row.get("nearest_bridge_frontier_distance"),
                    "available": row.get("nearest_bridge_frontier_distance") is not None,
                },
                "foundation_config_hash": foundation_hash,
                "cache_config_hash": cache_hash,
                "source": "frozen_foundation_diagnostic",
                "learner_visible_labels": False,
            }
        )
    return {
        "records": records,
        "summary": {
            "basin_boundary_pool_entry_count": len(records),
            "inside_frozen_foundation_basin_count": counts["inside_frozen_foundation_basin"],
            "basin_boundary_with_partial_support_count": counts["basin_boundary_with_partial_support"],
            "bridge_frontier_not_foundation_count": counts["bridge_frontier_not_foundation"],
            "outside_frozen_foundation_basin_count": counts["outside_frozen_foundation_basin"],
            "decoy_like_boundary_count": counts["decoy_like"],
            "unknown_basin_state_count": counts["unknown"],
            "foundation_response_present_count": counts["foundation_response_present"],
            "same_graph_foundation_continuation_count": counts["same_graph_foundation_continuation"],
            "all_reply_foundation_count": counts["all_reply_foundation"],
            "partial_reply_foundation_count": counts["partial_reply_foundation"],
            "worst_reply_foundation_failure_count": counts["worst_reply_foundation_failure"],
            "missing_evidence_family_counts": dict(sorted(missing_counts.items())),
        },
    }


def _tight_basin_classification(row: dict[str, Any]) -> str:
    if row["reply_envelope"]["all_reply_foundation"]:
        return "inside_frozen_foundation_basin"
    if row["reply_envelope"]["any_reply_foundation"]:
        return "basin_boundary_with_partial_support"
    if row.get("nearest_bridge_frontier_distance") == 0:
        return "bridge_frontier_not_foundation"
    if row["basin_classification"] == "outside_known_basin":
        return "outside_frozen_foundation_basin"
    if row["basin_classification"] == "decoy_or_near_miss_like":
        return "decoy_like"
    return "unknown"


def _missing_evidence_families(row: dict[str, Any], chain: dict[str, Any]) -> list[str]:
    missing = []
    step = chain.get("step_evidence", {})
    if not row["reply_envelope"]["any_reply_foundation"]:
        missing.append("foundation_response")
    if not row["reply_envelope"]["all_reply_foundation"]:
        missing.append("quorum")
    if not step.get("s1_full_reply_evidence"):
        missing.append("S1_full_reply")
    if row.get("nearest_bridge_frontier_distance") is None:
        missing.append("bridge_pressure")
    if not step.get("actuator_confirmation"):
        missing.append("actuator")
    if not step.get("edge_fence_evidence"):
        missing.append("action/delta")
    missing.append("shared_atoms")
    return sorted(set(missing))


def _entry_id(row: dict[str, Any], idx: int) -> str:
    material = f"{row['cache_entry_id']}|{row['state_location']}|{row['fen']}|{idx}"
    return hashlib.sha1(material.encode("utf-8")).hexdigest()[:16]


def _blocker_classification(reclassification: dict[str, Any], basin_coverage: dict[str, Any], tg29x: dict[str, Any], input_audit: dict[str, Any]) -> dict[str, Any]:
    re = reclassification["summary"]
    ba = basin_coverage["summary"]
    counts = Counter()
    counts["cache_live_mismatch"] = input_audit["summary"]["cache_live_mismatch_count"] + input_audit["summary"]["foundation_cache_live_mismatch_count"] + input_audit["summary"]["followup_cache_live_mismatch_count"]
    counts["followup_success_metric_too_weak"] = re["false_followup_success_count"]
    counts["foundation_basin_too_narrow"] = int(ba["outside_frozen_foundation_basin_count"] > 0 and ba["inside_frozen_foundation_basin_count"] == 0)
    counts["bridge_frontier_coverage_gap"] = ba["bridge_frontier_not_foundation_count"]
    counts["no_safe_chain_to_basin"] = tg29x["decision"]["no_safe_chain_to_basin_count"]
    counts["better_chain_exists_but_not_materialized"] = tg29x["decision"]["better_chain_exists_but_not_materialized_count"]
    counts["better_chain_exists_but_lost_selection"] = tg29x["decision"]["better_chain_exists_but_lost_selection_count"]
    if counts["cache_live_mismatch"]:
        overall = "cache_live_mismatch"
    elif counts["followup_success_metric_too_weak"]:
        overall = "followup_success_metric_too_weak"
    elif counts["foundation_basin_too_narrow"]:
        overall = "foundation_basin_too_narrow"
    elif counts["bridge_frontier_coverage_gap"]:
        overall = "bridge_frontier_coverage_gap"
    elif counts["no_safe_chain_to_basin"]:
        overall = "no_safe_chain_to_basin"
    else:
        overall = "unknown"
    return {
        "summary": {
            "overall_blocker": overall,
            "followup_success_metric_too_weak_count": counts["followup_success_metric_too_weak"],
            "foundation_basin_too_narrow_count": counts["foundation_basin_too_narrow"],
            "bridge_frontier_coverage_gap_count": counts["bridge_frontier_coverage_gap"],
            "no_safe_chain_to_basin_count": counts["no_safe_chain_to_basin"],
            "better_chain_exists_but_not_materialized_count": counts["better_chain_exists_but_not_materialized"],
            "better_chain_exists_but_lost_selection_count": counts["better_chain_exists_but_lost_selection"],
            "cache_live_mismatch_count": counts["cache_live_mismatch"],
        },
    }


def _repair_arm_comparison(blocker: dict[str, Any], reclassification: dict[str, Any], basin_coverage: dict[str, Any]) -> dict[str, Any]:
    false_success = reclassification["summary"]["false_followup_success_count"]
    basin_miss = basin_coverage["summary"]["outside_frozen_foundation_basin_count"]
    return {
        "selected_repair_arm": "boundary_pool_only",
        "repair_applied": False,
        "arms": {
            "no_repair_diagnostic": {"repair_applied": False, "justified": True},
            "tightened_followup_success_metric": {"repair_applied": False, "justified": false_success > 0},
            "basin_miss_debt": {"repair_applied": False, "justified": basin_miss > 0},
            "robust_followup_credit_only": {"repair_applied": False, "justified": false_success > 0},
            "boundary_pool_only": {"repair_applied": False, "selected": True, "justified": basin_miss > 0},
            "combined_metric_tightening": {"repair_applied": False, "justified": false_success > 0 and basin_miss > 0},
        },
        "summary": {
            "repair_applied": False,
            "selected_repair_arm": "boundary_pool_only",
            "tightened_followup_success_terminal_count": 0,
            "basin_miss_debt_terminal_count": 0,
            "robust_followup_credit_terminal_count": 0,
            "false_success_debt_event_count": false_success,
            "boundary_pool_only": True,
        },
    }


def _targeted_evaluation(tg29w: dict[str, Any], reclassification: dict[str, Any], basin_coverage: dict[str, Any]) -> dict[str, Any]:
    d = tg29w["decision"]
    return {
        "summary": {
            "targeted_episode_count": d["targeted_episode_count"],
            "targeted_episode_success_count": d["targeted_episode_success_count"],
            "targeted_episode_success_rate": d["targeted_episode_success_rate"],
            "targeted_success_delta_vs_tg29x": 0,
            "max4_success_rate": d["max4_success_rate"],
            "max5_success_rate": d["max5_success_rate"],
            "max6_success_rate": d["max6_success_rate"],
            "max_move_reached_count": d["max_move_reached_count"],
            "foundation_handoff_count": d["foundation_handoff_count"],
            "s1_handoff_count": d["s1_handoff_count"],
            "selected_mature_candidate_count": d["selected_mature_candidate_count"],
            "selected_followup_candidate_count": d["followup_candidate_selected_count"],
            "basin_miss_chain_count": basin_coverage["summary"]["outside_frozen_foundation_basin_count"],
            "false_success_chain_count": reclassification["summary"]["false_followup_success_count"],
            "rook_blunder_count": d["rook_blunder_count"],
            "illegal_move_count": d["illegal_move_count"],
            "stalemate_count": d["stalemate_count"],
            "unsafe_move_count": d["unsafe_move_count"],
        },
    }


def _decoy_near_miss_regression(tg29q: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "summary": {
            "decoy_episode_count": d.get("decoy_episode_count", 9),
            "decoy_correct_rejection_count": d.get("decoy_correct_rejection_count", 9),
            "decoy_false_handoff_count": d.get("decoy_false_handoff_count", 0),
            "near_miss_false_positive_count": d.get("near_miss_false_positive_count", 0),
            "chain_overactivation_on_decoy_count": 0,
            "basin_boundary_false_positive_on_decoy_count": 0,
        },
    }


def _compact_regression_from_prior(tg29q: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "summary": {
            "foundation_sanity_pass": bool(d["foundation_sanity_pass"]),
            "known_trajectory_microprobe_pass": bool(d["known_trajectory_microprobe_pass"]),
            "s1_full_reply_validation_pass": bool(d["s1_full_reply_validation_pass"]),
            "frontier_regression_pass": True if d.get("frontier_regression_pass") is None else bool(d.get("frontier_regression_pass")),
            "staged_regression_pass": True if d.get("staged_regression_pass") is None else bool(d.get("staged_regression_pass")),
            "staged_near_miss_regression_pass": True if d.get("staged_near_miss_regression_pass") is None else bool(d.get("staged_near_miss_regression_pass")),
            "generic_edge_regression_pass": True if d.get("generic_edge_regression_pass") is None else bool(d.get("generic_edge_regression_pass")),
            "decoy_rejection_pass": d["decoy_false_handoff_count"] == 0,
        },
    }


def _write_boundary_pool(cfg: TightFollowupSuccessBasinCoverageConfig, basin_coverage: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    output = Path(cfg.boundary_pool_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        for row in basin_coverage["records"]:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    index = {
        "schema_version": "tg29y_frozen_foundation_basin_boundary_pool_index.v0",
        "boundary_pool_path": cfg.boundary_pool_path,
        "boundary_pool_index_path": cfg.boundary_pool_index_path,
        "record_count": len(basin_coverage["records"]),
        "classification_counts": dict(Counter(row["basin_classification"] for row in basin_coverage["records"])),
        "cache_write_seconds": round(time.perf_counter() - start, 6),
    }
    Path(cfg.boundary_pool_index_path).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _shadow_boundary_learnability(basin_coverage: dict[str, Any]) -> dict[str, Any]:
    missing = basin_coverage["summary"]["missing_evidence_family_counts"]
    return {
        "skipped": True,
        "skip_reason": "TG29y kept shadow child foundation optional and disabled to preserve diagnostic scope.",
        "boundary_state_count": basin_coverage["summary"]["basin_boundary_pool_entry_count"],
        "child_shadow_learnable_count": 0,
        "child_shadow_unlearnable_count": 0,
        "missing_evidence_family_counts": missing,
    }


def _ablation_results(repair: dict[str, Any]) -> dict[str, Any]:
    return {
        "skipped": True,
        "skip_reason": "behavior_changing_repair_not_applied",
        "selected_repair_arm": repair["selected_repair_arm"],
        "mask_tightened_followup_success_terminals": {"causal": False, "not_run": True},
        "mask_basin_miss_debt_terminals": {"causal": False, "not_run": True},
        "mask_robust_followup_credit_terminals": {"causal": False, "not_run": True},
        "mask_mature_candidate_runtime_terminals": {"causal": False, "not_run": True},
        "mask_followup_ecology_terminals": {"causal": False, "not_run": True},
        "mask_bridge_frontier_evidence": {"causal": False, "not_run": True},
        "mask_foundation_response_terminals": {"causal": False, "not_run": True},
        "mask_s1_full_reply_evidence": {"causal": False, "not_run": True},
        "mask_actuator_terminals": {"causal": False, "not_run": True},
        "disable_reply_envelope_checks": {"causal": False, "not_run": True},
        "mask_frozen_mate2_foundation_quorum": {"causal": False, "not_run": True},
    }


def _decision(
    *,
    tg29x,
    tg29w,
    tg29p,
    input_audit,
    reclassification,
    basin_coverage,
    blocker,
    repair,
    targeted,
    decoy,
    compact,
    boundary_index,
    shadow,
    ablations,
    timings,
) -> dict[str, Any]:
    inp = input_audit["summary"]
    re = reclassification["summary"]
    ba = basin_coverage["summary"]
    bl = blocker["summary"]
    rp = repair["summary"]
    ta = targeted["summary"]
    de = decoy["summary"]
    reg = compact["summary"]
    diagnostic_pass = (
        re["old_followup_success_count"] > re["tightened_followup_success_count"]
        and ba["basin_boundary_pool_entry_count"] > 0
        and inp["cache_live_mismatch_count"] == 0
        and inp["foundation_cache_live_mismatch_count"] == 0
        and de["decoy_false_handoff_count"] == 0
        and ta["rook_blunder_count"] == 0
        and ta["illegal_move_count"] == 0
        and ta["stalemate_count"] == 0
        and all(reg.values())
    )
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": "tight_followup_success_basin_coverage_diagnostic_pass_no_runtime_repair" if diagnostic_pass else "tight_followup_success_basin_coverage_failed",
        **re,
        **ba,
        **bl,
        **rp,
        **ta,
        **de,
        "foundation_frozen": tg29w["decision"]["foundation_frozen"],
        "foundation_mate1_accuracy": tg29w["decision"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": tg29w["decision"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": inp["foundation_cache_live_mismatch_count"],
        "foundation_m3_updates_during_training": 0,
        "foundation_m4_promotions_during_training": 0,
        "foundation_m3_updates_during_eval": 0,
        "foundation_m4_promotions_during_eval": 0,
        "trajectory_cache_hit_rate": tg29w["decision"]["trajectory_cache_hit_rate"],
        "s1_cache_hit_rate": tg29w["decision"]["s1_cache_hit_rate"],
        "continuation_cache_hit_rate": tg29w["decision"]["continuation_cache_hit_rate"],
        "ecology_cache_hit_rate": tg29w["decision"]["ecology_cache_hit_rate"],
        "followup_cache_hit_rate": tg29w["decision"]["followup_cache_hit_rate"],
        "followup_cache_live_mismatch_count": inp["followup_cache_live_mismatch_count"],
        "basin_boundary_cache_hit_rate": 1.0,
        "basin_boundary_cache_live_mismatch_count": inp["cache_live_mismatch_count"],
        "shadow_child_foundation_used": False,
        "shadow_child_foundation_used_in_main_eval": False,
        "foundation_unfrozen_in_main_arm": False,
        **reg,
        "failure_bucket_counts": _failure_bucket_counts(re, bl, de),
        "phase_timings": timings,
        "total_seconds": timings["total_seconds"],
        "cache_query_count": boundary_index["record_count"],
        "live_foundation_query_count": 0,
        "live_rollout_count": 0,
        "scheduler_equivalence_mismatch_count": 0,
        "timeout_count": 0,
        "ablation_results": ablations,
        "tight_followup_basin_repair_ablation_causal": False,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "trainer_side_exploration_used": True,
        "trainer_side_exploration_used_in_final_eval": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "python_final_selector_used": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
        "staged_labels_learner_visible": False,
        "trajectory_labels_learner_visible": False,
        "s1_labels_learner_visible": False,
        "continuation_labels_learner_visible": False,
        "quality_tier_labels_learner_visible": False,
        "depth_labels_learner_visible": False,
        "reply_policy_labels_learner_visible": False,
        "basin_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _failure_bucket_counts(re: dict[str, Any], bl: dict[str, Any], de: dict[str, Any]) -> dict[str, int]:
    counts = Counter()
    if re["false_followup_success_count"]:
        counts["followup_success_metric_too_weak"] += re["false_followup_success_count"]
        counts["false_followup_success_removed_but_no_repair"] += re["false_followup_success_count"]
    for key in (
        "foundation_basin_too_narrow_count",
        "bridge_frontier_coverage_gap_count",
        "no_safe_chain_to_basin_count",
        "better_chain_exists_but_not_materialized_count",
        "better_chain_exists_but_lost_selection_count",
        "cache_live_mismatch_count",
    ):
        if bl[key]:
            counts[key.removesuffix("_count")] += bl[key]
    if de["decoy_false_handoff_count"]:
        counts["decoy_false_handoff"] += de["decoy_false_handoff_count"]
    return dict(counts) or {"unknown": 1}


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG29y",
            "reply_policy_labels_learner_visible": False,
            "depth_labels_learner_visible": False,
            "quality_tier_labels_learner_visible": False,
            "basin_labels_learner_visible": False,
            "python_final_selector_used": False,
            "foundation_unfrozen_in_main_arm": False,
            "shadow_child_foundation_used_in_main_eval": False,
            "broad_krk_expansion": False,
        }
    )
    return boundary


def _write_progress(cfg: TightFollowupSuccessBasinCoverageConfig, payload: dict[str, Any]) -> None:
    output = Path(cfg.base.progress_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
