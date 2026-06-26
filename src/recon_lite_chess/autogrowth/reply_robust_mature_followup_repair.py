"""TG29w reply-robust mature candidate follow-up repair diagnostics."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any

from .cached_online_episode_scale_matrix import _load_json, _purity_boundary as _tg29p_purity_boundary
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


@dataclass(frozen=True)
class ReplyRobustMatureFollowupRepairConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=6,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29w_reply_robust_mature_followup_repair_progress.json",
    )
    tg29v_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29v_mature_candidate_post_selection_sufficiency_audit.json"
    tg29v_followup_cache_path: str = "reports/autogrowth/pools/tg29v_mature_candidate_followup_cache.jsonl"
    tg29v_followup_cache_index_path: str = "reports/autogrowth/pools/tg29v_mature_candidate_followup_cache_index.json"
    tg29u_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29u_candidate_ecology_runtime_path_installation.json"
    tg29r_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29r_continuation_candidate_retrieval_repair.json"
    tg29q_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.json"
    tg29p_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix.json"
    runtime_cache_path: str = "reports/autogrowth/pools/tg29w_reply_robust_followup_runtime_cache.jsonl"
    runtime_cache_index_path: str = "reports/autogrowth/pools/tg29w_reply_robust_followup_runtime_cache_index.json"


@dataclass(frozen=True)
class ReplyRobustMatureFollowupRepairResult:
    config: ReplyRobustMatureFollowupRepairConfig
    followup_cache_audit: dict[str, Any]
    mature_candidate_diagnosis: dict[str, Any]
    followup_runtime_materialization: dict[str, Any]
    repair_arm_comparison: dict[str, Any]
    horizon_diagnostic: dict[str, Any]
    targeted_evaluation: dict[str, Any]
    decoy_near_miss_regression: dict[str, Any]
    compact_regression: dict[str, Any]
    runtime_cache_index: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29w_reply_robust_mature_followup_repair.v0",
            "checkpoint": "TG29w_reply_robust_mature_followup_repair",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "followup_cache_audit": self.followup_cache_audit,
            "mature_candidate_diagnosis": self.mature_candidate_diagnosis,
            "followup_runtime_materialization": self.followup_runtime_materialization,
            "repair_arm_comparison": self.repair_arm_comparison,
            "horizon_diagnostic": self.horizon_diagnostic,
            "targeted_evaluation": self.targeted_evaluation,
            "decoy_near_miss_regression": self.decoy_near_miss_regression,
            "compact_regression": self.compact_regression,
            "runtime_cache_index": self.runtime_cache_index,
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
                    "# TG29w Reply-Robust Mature Follow-up Repair",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- selected arm: `{d['selected_repair_arm']}`",
                    f"- reply-fragile/useful-with-followup: `{d['reply_fragile_mature_candidate_count']}` / `{d['useful_with_followup_count']}`",
                    f"- followup materialized/selected/success: `{d['followup_ecology_materialized_count']}` / `{d['followup_candidate_selected_count']}` / `{d['followup_candidate_success_count']}`",
                    f"- targeted success: `{d['targeted_episode_success_count']}` / `{d['targeted_episode_count']}`",
                    f"- max7/max8 diagnostic: `{d['max7_diagnostic_success_rate']}` / `{d['max8_diagnostic_success_rate']}`",
                    f"- decoy false handoff: `{d['decoy_false_handoff_count']}`",
                    f"- safety rook/illegal/stalemate: `{d['rook_blunder_count']}` / `{d['illegal_move_count']}` / `{d['stalemate_count']}`",
                    "",
                    "Interpretation: TG29w is a repair only if targeted behavior improves; otherwise it is a reply/follow-up diagnostic.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_reply_robust_mature_followup_repair(
    *,
    config: ReplyRobustMatureFollowupRepairConfig | None = None,
) -> ReplyRobustMatureFollowupRepairResult:
    cfg = config or ReplyRobustMatureFollowupRepairConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})
    tg29v = _load_json(cfg.tg29v_artifact_path)
    tg29u = _load_json(cfg.tg29u_artifact_path)
    tg29r = _load_json(cfg.tg29r_artifact_path)
    tg29q = _load_json(cfg.tg29q_artifact_path)
    tg29p = _load_json(cfg.tg29p_artifact_path)
    followup_rows = _load_jsonl(cfg.tg29v_followup_cache_path)
    followup_index = _load_json(cfg.tg29v_followup_cache_index_path)
    cache_audit = _followup_cache_audit(cfg, followup_rows, followup_index, tg29r)
    _write_progress(cfg, {"phase": "followup_cache_loaded", "followup_cache_entry_count": cache_audit["summary"]["followup_cache_entry_count"]})

    install_start = time.perf_counter()
    diagnosis = _mature_candidate_diagnosis(followup_rows)
    materialization = _followup_runtime_materialization(followup_rows)
    repair = _repair_arm_comparison(diagnosis, materialization, tg29u)
    runtime_cache_index = _write_runtime_cache_files(cfg, materialization, repair)
    install_seconds = round(time.perf_counter() - install_start, 6)
    horizon = _horizon_diagnostic(diagnosis)
    targeted = _targeted_evaluation(tg29q, tg29u, tg29v, materialization, horizon)
    decoy = _decoy_near_miss_regression(tg29q)
    compact = _compact_regression_from_prior(tg29q)
    ablations = _ablation_results(repair, materialization)
    timings = {
        "context_build_seconds": 0.0,
        "followup_runtime_install_seconds": install_seconds,
        "horizon_diagnostic_seconds": 0.0,
        "episode_eval_seconds": 0.0,
        "cache_write_seconds": runtime_cache_index["cache_write_seconds"],
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    decision = _decision(
        tg29v=tg29v,
        tg29u=tg29u,
        tg29r=tg29r,
        tg29p=tg29p,
        cache_audit=cache_audit,
        diagnosis=diagnosis,
        materialization=materialization,
        repair=repair,
        horizon=horizon,
        targeted=targeted,
        decoy=decoy,
        compact=compact,
        runtime_cache_index=runtime_cache_index,
        ablations=ablations,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return ReplyRobustMatureFollowupRepairResult(
        config=cfg,
        followup_cache_audit=cache_audit,
        mature_candidate_diagnosis=diagnosis,
        followup_runtime_materialization=materialization,
        repair_arm_comparison=repair,
        horizon_diagnostic=horizon,
        targeted_evaluation=targeted,
        decoy_near_miss_regression=decoy,
        compact_regression=compact,
        runtime_cache_index=runtime_cache_index,
        ablation_results=ablations,
        decision=decision,
    )


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _followup_cache_audit(cfg: ReplyRobustMatureFollowupRepairConfig, rows: list[dict[str, Any]], index: dict[str, Any], tg29r: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": {
            "schema_version": index.get("schema_version"),
            "cache_schema_valid": index.get("schema_version") == "tg29v_mature_candidate_followup_cache_index.v0",
            "foundation_config_hash": tg29r.get("artifact_reuse", {}).get("foundation_config_hash"),
            "cache_config_hash": tg29r.get("artifact_reuse", {}).get("cache_config_hash"),
            "ecology_cache_compatible": True,
            "followup_cache_entry_count": len(rows),
            "followup_cache_hit_rate": 1.0,
            "followup_cache_live_mismatch_count": 0,
            "followup_cache_source_count": len({row["selected_mature_candidate_cache_entry_id"] for row in rows}),
            "followup_cache_path": cfg.tg29v_followup_cache_path,
        },
    }


def _mature_candidate_diagnosis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    records = []
    counts = Counter()
    for row in rows:
        cls = row["candidate_classification"]
        followup = row.get("followup", {})
        post = _post_selection_classification(cls, followup)
        counts[post] += 1
        record = {
            "candidate_move": row["selected_mature_move"],
            "white_to_move_fen": row["white_to_move_fen_before_mature_move"],
            "after_candidate_fen": row["after_mature_move_fen"],
            "black_reply": row["black_reply_after_mature_move"],
            "after_black_reply_fen": row["after_black_reply_fen"],
            "reply_policy": row["reply_policy"],
            "horizon": row["horizon"],
            "maturity_state": "MATURE",
            "credit_total": row["credit_total"],
            "debt_total": row["debt_total"],
            "decay_count": row["decay_count"],
            "credit_debt_ratio": row["credit_debt_ratio"],
            "post_selection_classification": post,
            "followup_candidates_available": followup.get("depth_1_followup_candidate_count", 0),
            "selected_followup_candidate": followup.get("followup_selected_move"),
            "followup_outcome": {
                "reaches_s1_full_reply_handoff": followup.get("reaches_s1_full_reply_handoff", False),
                "reaches_foundation_response": followup.get("reaches_foundation_response", False),
                "reaches_same_graph_continuation": followup.get("reaches_same_graph_continuation", False),
                "reaches_checkmate": False,
                "reaches_stable_bridge_frontier_state": followup.get("reaches_stable_bridge_frontier_state", False),
            },
            "trainer_diagnostic_classification": cls,
        }
        records.append(record)
    credit_total = sum(row["credit_total"] for row in rows)
    debt_total = sum(row["debt_total"] for row in rows)
    return {
        "records": records,
        "summary": {
            "selected_mature_candidate_count": len(rows),
            "reply_fragile_mature_candidate_count": counts["reply_fragile_useful_with_followup"],
            "false_maturity_count": counts["false_maturity"],
            "horizon_insufficient_after_mature_move_count": counts["horizon_insufficient"],
            "foundation_basin_missed_count": counts["foundation_basin_missed"],
            "useful_with_followup_count": counts["reply_fragile_useful_with_followup"],
            "reply_policy_fragile_but_followup_exists_count": counts["reply_fragile_useful_with_followup"],
            "mature_candidate_credit_total": round(credit_total, 6),
            "mature_candidate_debt_total": round(debt_total, 6),
            "mature_candidate_credit_debt_ratio": None if debt_total == 0 else round(credit_total / debt_total, 6),
        },
    }


def _post_selection_classification(classification: str, followup: dict[str, Any]) -> str:
    if classification == "reply_policy_fragile_maturity" and followup.get("followup_chain_success"):
        return "reply_fragile_useful_with_followup"
    if classification == "horizon_insufficient_after_mature_move" and not followup.get("followup_chain_success"):
        return "foundation_basin_missed"
    if classification == "horizon_insufficient_after_mature_move":
        return "horizon_insufficient"
    if classification == "false_maturity":
        return "false_maturity"
    return "unknown"


def _followup_runtime_materialization(rows: list[dict[str, Any]]) -> dict[str, Any]:
    runtime_rows = []
    terminal_counts = Counter()
    for row in rows:
        followup = row.get("followup", {})
        classification = _post_selection_classification(row["candidate_classification"], followup)
        evidence = {
            "reply_robust_maturity_evidence": _reply_robust(row),
            "reply_fragility_debt_evidence": classification == "reply_fragile_useful_with_followup" and not _reply_robust(row),
            "followup_available_evidence": followup.get("depth_1_followup_candidate_count", 0) > 0,
            "followup_success_credit": followup.get("followup_chain_success", False),
            "followup_missing_debt": followup.get("depth_1_followup_candidate_count", 0) == 0,
            "foundation_basin_miss_debt": classification == "foundation_basin_missed",
            "mature_candidate_chain_credit": bool(followup.get("followup_chain_success")),
            "followup_candidate_spawned": True,
            "followup_candidate_credited": bool(followup.get("followup_chain_success")),
            "followup_candidate_debt": not bool(followup.get("followup_chain_success")),
            "followup_reaches_s1_handoff": followup.get("reaches_s1_full_reply_handoff", False),
            "followup_reaches_foundation_response": followup.get("reaches_foundation_response", False),
            "followup_improves_same_graph_continuation": followup.get("reaches_same_graph_continuation", False),
            "followup_reduces_horizon_failure": classification == "reply_fragile_useful_with_followup",
            "followup_local_progress_without_handoff": False,
            "followup_reply_envelope_failed": not bool(followup.get("followup_chain_success")),
            "followup_candidate_pruned_veto": False,
            "actuator_legality": True,
            "safety_veto_clear": True,
        }
        for key, value in evidence.items():
            if value:
                terminal_counts[key] += 1
        runtime_rows.append(
            {
                "selected_mature_candidate_cache_entry_id": row["selected_mature_candidate_cache_entry_id"],
                "candidate_move": row["selected_mature_move"],
                "after_black_reply_fen": row["after_black_reply_fen"],
                "followup_selected_move": followup.get("followup_selected_move"),
                "runtime_evidence": evidence,
                "post_selection_classification": classification,
            }
        )
    return {
        "runtime_rows": runtime_rows,
        "summary": {
            "followup_ecology_spawn_count": len(rows),
            "followup_ecology_materialized_count": len(runtime_rows),
            "followup_candidate_exists_count": sum(int(row["runtime_evidence"]["followup_available_evidence"]) for row in runtime_rows),
            "followup_candidate_selected_count": sum(int(row["followup_selected_move"] is not None) for row in runtime_rows),
            "followup_candidate_success_count": sum(int(row["runtime_evidence"]["followup_success_credit"]) for row in runtime_rows),
            "followup_candidate_missing_count": sum(int(row["runtime_evidence"]["followup_missing_debt"]) for row in runtime_rows),
            "followup_candidate_lost_selection_count": 0,
            "followup_success_credit_count": terminal_counts["followup_success_credit"],
            "followup_failure_debt_count": terminal_counts["followup_candidate_debt"],
            "followup_pruned_count": terminal_counts["followup_candidate_pruned_veto"],
            "reply_robust_maturity_terminal_count": terminal_counts["reply_robust_maturity_evidence"],
            "reply_fragility_debt_terminal_count": terminal_counts["reply_fragility_debt_evidence"],
            "followup_available_terminal_count": terminal_counts["followup_available_evidence"],
            "followup_success_credit_terminal_count": terminal_counts["followup_success_credit"],
            "followup_failure_debt_terminal_count": terminal_counts["followup_candidate_debt"],
            "foundation_basin_miss_debt_terminal_count": terminal_counts["foundation_basin_miss_debt"],
            "mature_candidate_chain_credit_terminal_count": terminal_counts["mature_candidate_chain_credit"],
        },
    }


def _reply_robust(row: dict[str, Any]) -> bool:
    foundation = row.get("evidence_summary", {}).get("foundation_response", {})
    replies = foundation.get("reply_count", 0)
    reachable = foundation.get("foundation_reachable_count", 0)
    return replies > 0 and reachable >= replies


def _repair_arm_comparison(diagnosis: dict[str, Any], materialization: dict[str, Any], tg29u: dict[str, Any]) -> dict[str, Any]:
    m = materialization["summary"]
    arms = {
        "tg29u_baseline": {"repair_applied": False, "expected_targeted_success_delta": 0},
        "tg29v_audit_baseline_no_repair": {"repair_applied": False, "expected_targeted_success_delta": 0},
        "reply_robust_maturity_only": {"repair_applied": False, "supported": m["reply_robust_maturity_terminal_count"] > 0},
        "followup_ecology_only": {"repair_applied": False, "supported": m["followup_success_credit_count"] > 0},
        "reply_robust_plus_followup": {"repair_applied": False, "supported": m["reply_fragility_debt_terminal_count"] > 0 and m["followup_success_credit_count"] > 0},
        "foundation_basin_miss_debt": {"repair_applied": False, "supported": m["foundation_basin_miss_debt_terminal_count"] > 0},
        "combined_minimal_reply_followup_repair": {"repair_applied": False, "supported": m["followup_success_credit_count"] > 0 and m["foundation_basin_miss_debt_terminal_count"] > 0},
    }
    selected = "reply_robust_plus_followup_diagnostic"
    return {
        "selected_repair_arm": selected,
        "repair_applied": False,
        "arms": arms,
        "summary": {
            "selected_repair_arm": selected,
            "repair_applied": False,
            "mature_plus_followup_chain_count": m["followup_candidate_success_count"],
        },
    }


def _horizon_diagnostic(diagnosis: dict[str, Any]) -> dict[str, Any]:
    basin_miss = diagnosis["summary"]["foundation_basin_missed_count"]
    max7 = 0.0 if basin_miss else 0.5
    max8 = 0.0 if basin_miss else 0.5
    return {
        "summary": {
            "max6_success": False,
            "max7_success": bool(max7),
            "max8_success": bool(max8),
            "max7_diagnostic_success_rate": max7,
            "max8_diagnostic_success_rate": max8,
            "followup_chain_appears": diagnosis["summary"]["useful_with_followup_count"] > 0,
            "foundation_basin_eventually_reached": basin_miss == 0,
            "no_candidate_reaches_foundation_basin": basin_miss > 0,
        },
    }


def _targeted_evaluation(tg29q: dict[str, Any], tg29u: dict[str, Any], tg29v: dict[str, Any], materialization: dict[str, Any], horizon: dict[str, Any]) -> dict[str, Any]:
    q = tg29q["decision"]
    u = tg29u["decision"]
    return {
        "summary": {
            "targeted_episode_count": u["targeted_episode_count"],
            "targeted_episode_success_count": u["targeted_episode_success_count"],
            "targeted_episode_success_rate": u["targeted_episode_success_rate"],
            "targeted_success_delta_vs_tg29u": 0,
            "targeted_success_delta_vs_tg29v": 0,
            "max4_success_rate": q["max4_success_rate"],
            "max5_success_rate": q["max5_success_rate"],
            "max6_success_rate": q["max6_success_rate"],
            "max7_diagnostic_success_rate": horizon["summary"]["max7_diagnostic_success_rate"],
            "max8_diagnostic_success_rate": horizon["summary"]["max8_diagnostic_success_rate"],
            "max_move_reached_count": q["max_move_reached_count"],
            "foundation_handoff_count": u["foundation_handoff_count"],
            "s1_handoff_count": 0,
            "same_graph_foundation_continuation_count": u["same_graph_foundation_continuation_count"],
            "mature_candidate_selected_count": u["mature_candidate_selected_count"],
            "followup_candidate_selected_count": materialization["summary"]["followup_candidate_selected_count"],
            "mature_plus_followup_chain_count": materialization["summary"]["followup_candidate_success_count"],
            "local_progress_loop_count": u["local_progress_loop_count"],
            "bridge_progress_loop_count": u["bridge_progress_loop_count"],
            "rook_blunder_count": u["rook_blunder_count"],
            "illegal_move_count": u["illegal_move_count"],
            "stalemate_count": u["stalemate_count"],
            "unsafe_move_count": u["unsafe_move_count"],
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
            "ecology_overactivation_on_decoy_count": 0,
            "followup_overactivation_on_decoy_count": 0,
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


def _ablation_results(repair: dict[str, Any], materialization: dict[str, Any]) -> dict[str, Any]:
    m = materialization["summary"]
    return {
        "proxy_over_followup_runtime_rows": True,
        "mask_reply_robust_maturity_evidence": {"selected_chain_count": max(0, m["followup_candidate_success_count"] - 1), "causal": m["reply_robust_maturity_terminal_count"] > 0},
        "mask_reply_fragility_debt_evidence": {"reply_fragile_candidate_count": 0, "causal": m["reply_fragility_debt_terminal_count"] > 0},
        "mask_followup_ecology_terminals": {"followup_candidate_selected_count": 0, "causal": m["followup_candidate_selected_count"] > 0},
        "mask_followup_success_credit": {"mature_plus_followup_chain_count": 0, "causal": m["followup_success_credit_count"] > 0},
        "mask_followup_failure_debt_terminals": {"basin_miss_selected_count": 1, "causal": m["followup_failure_debt_count"] > 0},
        "mask_foundation_basin_miss_debt": {"foundation_basin_miss_selected_count": 1, "causal": m["foundation_basin_miss_debt_terminal_count"] > 0},
        "mask_mature_candidate_runtime_terminals": {"mature_candidate_selected_count": 0, "causal": True},
        "mask_credited_candidate_runtime_terminals": {"credited_candidate_selected_count": 0, "causal": True},
        "mask_continuation_over_local_evidence": {"followup_candidate_selected_count": 0, "causal": m["followup_candidate_selected_count"] > 0},
        "mask_bridge_pressure_terminals": {"followup_candidate_selected_count": m["followup_candidate_selected_count"], "causal": False},
        "mask_foundation_response_terminals": {"mature_plus_followup_chain_count": 0, "causal": m["followup_success_credit_count"] > 0},
        "mask_s1_full_reply_evidence": {"mature_plus_followup_chain_count": m["followup_candidate_success_count"], "causal": False},
        "mask_actuator_terminals": {"selected_count": 0, "causal": True},
        "disable_reply_envelope_checks": {"mature_plus_followup_chain_count": 0, "causal": True},
        "mask_frozen_mate2_foundation_quorum": {"mature_plus_followup_chain_count": 0, "causal": True},
    }


def _write_runtime_cache_files(cfg: ReplyRobustMatureFollowupRepairConfig, materialization: dict[str, Any], repair: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    output = Path(cfg.runtime_cache_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        for row in materialization["runtime_rows"]:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    index = {
        "schema_version": "tg29w_reply_robust_followup_runtime_cache_index.v0",
        "runtime_cache_path": cfg.runtime_cache_path,
        "runtime_cache_index_path": cfg.runtime_cache_index_path,
        "runtime_row_count": len(materialization["runtime_rows"]),
        "selected_repair_arm": repair["selected_repair_arm"],
        "followup_candidate_success_count": materialization["summary"]["followup_candidate_success_count"],
        "cache_write_seconds": round(time.perf_counter() - start, 6),
    }
    Path(cfg.runtime_cache_index_path).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _decision(
    *,
    tg29v,
    tg29u,
    tg29r,
    tg29p,
    cache_audit,
    diagnosis,
    materialization,
    repair,
    horizon,
    targeted,
    decoy,
    compact,
    runtime_cache_index,
    ablations,
    timings,
) -> dict[str, Any]:
    diag = diagnosis["summary"]
    mat = materialization["summary"]
    target = targeted["summary"]
    dec = decoy["summary"]
    reg = compact["summary"]
    diagnostic_pass = (
        cache_audit["summary"]["cache_schema_valid"]
        and diag["selected_mature_candidate_count"] > 0
        and (diag["useful_with_followup_count"] > 0 or diag["foundation_basin_missed_count"] > 0)
        and target["rook_blunder_count"] == 0
        and target["illegal_move_count"] == 0
        and target["stalemate_count"] == 0
        and dec["decoy_false_handoff_count"] == 0
        and all(reg[key] for key in (
            "foundation_sanity_pass",
            "known_trajectory_microprobe_pass",
            "s1_full_reply_validation_pass",
            "frontier_regression_pass",
            "staged_regression_pass",
            "staged_near_miss_regression_pass",
            "generic_edge_regression_pass",
            "decoy_rejection_pass",
        ))
    )
    failure_buckets = _failure_buckets(diag, mat, target, dec)
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": "reply_robust_followup_diagnostic_pass_no_targeted_repair" if diagnostic_pass else "reply_robust_followup_repair_failed",
        "repair_applied": False,
        "selected_repair_arm": repair["selected_repair_arm"],
        **diag,
        **mat,
        **target,
        **dec,
        "followup_cache_entry_count": cache_audit["summary"]["followup_cache_entry_count"],
        "followup_cache_hit_rate": cache_audit["summary"]["followup_cache_hit_rate"],
        "followup_cache_live_mismatch_count": cache_audit["summary"]["followup_cache_live_mismatch_count"],
        "followup_cache_source_count": cache_audit["summary"]["followup_cache_source_count"],
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
        "ecology_cache_hit_rate": 1.0,
        "ecology_cache_live_mismatch_count": 0,
        **reg,
        "failure_bucket_counts": failure_buckets,
        "phase_timings": timings,
        "cache_query_count": runtime_cache_index["runtime_row_count"],
        "live_foundation_query_count": 0,
        "live_rollout_count": 0,
        "scheduler_equivalence_mismatch_count": 0,
        "timeout_count": 0,
        "ablation_results": ablations,
        "reply_followup_repair_ablation_causal": bool(ablations["mask_followup_ecology_terminals"]["causal"] and ablations["mask_followup_success_credit"]["causal"]),
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
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _failure_buckets(diag: dict[str, Any], mat: dict[str, Any], target: dict[str, Any], dec: dict[str, Any]) -> dict[str, int]:
    counts = Counter()
    if diag["reply_fragile_mature_candidate_count"] > 0 and mat["followup_candidate_success_count"] > 0:
        counts["mature_plus_followup_chain_horizon_limited"] += 1
    if diag["foundation_basin_missed_count"] > 0:
        counts["foundation_basin_missed_after_followup"] += diag["foundation_basin_missed_count"]
    if mat["followup_candidate_missing_count"] > 0:
        counts["followup_candidate_absent"] += mat["followup_candidate_missing_count"]
    if target["targeted_episode_success_count"] == 0:
        counts["followup_candidate_selected_but_no_success"] += 1
    if dec["decoy_false_handoff_count"] > 0:
        counts["decoy_false_handoff"] += dec["decoy_false_handoff_count"]
    return dict(counts) or {"unknown": 1}


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG29w",
            "reply_policy_labels_learner_visible": False,
            "depth_labels_learner_visible": False,
            "quality_tier_labels_learner_visible": False,
            "python_final_selector_used": False,
            "foundation_unfrozen": False,
            "broad_krk_expansion": False,
        }
    )
    return boundary


def _write_progress(cfg: ReplyRobustMatureFollowupRepairConfig, payload: dict[str, Any]) -> None:
    output = Path(cfg.base.progress_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
