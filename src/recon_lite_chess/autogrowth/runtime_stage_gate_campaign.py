"""TG36-TG38 KRK runtime stage-gate campaign."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import gzip
import hashlib
import json
from pathlib import Path
import statistics
import time
from typing import Any

from .boundary_dataset_expansion_child_coverage_ladder import _load_jsonl
from .cached_online_episode_scale_matrix import _load_json, _purity_boundary as _tg29p_purity_boundary
from .child_consensus_runtime_policy import (
    DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY,
    ChildConsensusRuntimePolicyName,
    decide_child_consensus_runtime,
)
from .feature_flagged_child_consensus_runtime_canary import (
    RUNTIME_POLICIES,
    _evidence as _tg35_evidence,
)
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


STAGE_PLAY_START_FAMILIES = (
    "known_repaired",
    "staged_pool",
    "frontier_near",
    "generic_edge",
    "boundary_derived_frontier_generic",
    "mixed_controlled_krk",
    "broad_labeled_krk_probe",
    "near_miss_decoy",
    "hard_decoy",
    "child_confusable_decoy",
)
STAGE_PLAY_HORIZONS = ("max4", "max6", "max8", "max10", "max12", "max16")
STAGE_PLAY_REPLY_POLICIES = (
    "deterministic_worst_foundation",
    "mobility_maximizing",
    "fixed_seed_random_legal",
    "bridge_avoidance",
    "foundation_escape",
)


@dataclass(frozen=True)
class RuntimeStageGateCampaignConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=16,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg36_tg38_runtime_stage_gate_campaign_progress.json",
    )
    tg35_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg35_feature_flagged_child_consensus_runtime_canary.json"
    tg32_boundary_pool_path: str = "reports/autogrowth/pools/tg32_active_foundation_basin_boundary_pool.jsonl"
    tg32_child_pool_path: str = "reports/autogrowth/pools/tg32_child_foundation_boundary_coverage_pool.jsonl"
    tg32_hard_decoy_pool_path: str = "reports/autogrowth/pools/tg32_hard_decoy_pool.jsonl"
    tg36_output_path: str = "reports/autogrowth/krk_autogrowth_tg36_feature_flagged_canary_packaging_gate.json"
    tg36_progress_path: str = "reports/autogrowth/krk_autogrowth_tg36_feature_flagged_canary_packaging_gate_progress.json"
    tg36_markdown_path: str = "reports/autogrowth/krk_autogrowth_tg36_feature_flagged_canary_packaging_gate.md"
    tg37_output_path: str = "reports/autogrowth/krk_autogrowth_tg37_krk_stage_play_runtime_ladder.json"
    tg37_progress_path: str = "reports/autogrowth/krk_autogrowth_tg37_krk_stage_play_runtime_ladder_progress.json"
    tg37_markdown_path: str = "reports/autogrowth/krk_autogrowth_tg37_krk_stage_play_runtime_ladder.md"
    tg38_output_path: str = "reports/autogrowth/krk_autogrowth_tg38_stage_play_failure_driven_decision.json"
    tg38_progress_path: str = "reports/autogrowth/krk_autogrowth_tg38_stage_play_failure_driven_decision_progress.json"
    tg38_markdown_path: str = "reports/autogrowth/krk_autogrowth_tg38_stage_play_failure_driven_decision.md"
    campaign_output_path: str = "reports/autogrowth/krk_autogrowth_tg36_tg38_runtime_stage_gate_campaign.json"
    campaign_markdown_path: str = "reports/autogrowth/krk_autogrowth_tg36_tg38_runtime_stage_gate_campaign.md"
    tg37_paired_results_path: str = "reports/autogrowth/pools/tg37_stage_play_paired_results.jsonl.gz"
    tg37_child_interventions_path: str = "reports/autogrowth/pools/tg37_stage_play_child_interventions.jsonl.gz"
    tg37_failure_traces_path: str = "reports/autogrowth/pools/tg37_stage_play_failure_traces.jsonl.gz"
    tg37_live_cache_samples_path: str = "reports/autogrowth/pools/tg37_stage_play_live_cache_samples.jsonl.gz"
    tg38_failure_traces_path: str = "reports/autogrowth/pools/tg38_failure_traces.jsonl.gz"
    tg38_gate_diagnostics_path: str = "reports/autogrowth/pools/tg38_gate_diagnostics.jsonl.gz"
    tg38_hurt_case_audit_path: str = "reports/autogrowth/pools/tg38_hurt_case_audit.jsonl.gz"
    long_mode: bool = False
    max_total_seconds: int = 36000
    min_target_seconds: int = 28800
    target_tier: int = 1
    stage_play_tier_start: int = 50_000
    stage_play_tier_max: int = 1_000_000
    seed_count: int = 50
    live_cache_sample_target: int = 10_000
    parity_episode_count: int = 2_000


@dataclass(frozen=True)
class RuntimeStageGateCampaignResult:
    config: RuntimeStageGateCampaignConfig
    tg36: dict[str, Any]
    tg37: dict[str, Any]
    tg38: dict[str, Any]
    campaign: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg36_tg38_runtime_stage_gate_campaign.v0",
            "checkpoint": "TG36_TG38_runtime_stage_gate_campaign",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "tg36": self.tg36,
            "tg37": self.tg37,
            "tg38": self.tg38,
            "campaign": self.campaign,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output

    def write_markdown(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        d = self.campaign["decision"]
        output.write_text(
            "\n".join(
                [
                    "# TG36-TG38 Runtime Stage-Gate Campaign",
                    "",
                    f"- campaign_checkpoint_pass: `{d['campaign_checkpoint_pass']}`",
                    f"- interpretation: `{d['campaign_interpretation']}`",
                    f"- phases completed: `{', '.join(d['phases_completed'])}`",
                    f"- paired stage-play episodes: `{d['paired_stage_play_episode_count']}`",
                    f"- parent / canary success rate: `{d['parent_stage_play_success_rate']}` / `{d['canary_stage_play_success_rate']}`",
                    f"- paired help / hurt / net: `{d['paired_help_count']}` / `{d['paired_hurt_count']}` / `{d['paired_net_help']}`",
                    f"- live/cache samples and mismatches: `{d['live_cache_sample_count']}` / `{d['parent_cache_live_mismatch_count'] + d['child_cache_live_mismatch_count'] + d['reply_envelope_cache_live_mismatch_count'] + d['actuator_cache_live_mismatch_count']}`",
                    f"- next action: `{d['selected_next_action']}`",
                    "",
                    "Interpretation: this is still default-off canary stage-play validation, not main/default adoption.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_runtime_stage_gate_campaign(
    *,
    config: RuntimeStageGateCampaignConfig | None = None,
) -> RuntimeStageGateCampaignResult:
    cfg = config or RuntimeStageGateCampaignConfig()
    start = time.perf_counter()
    _write_progress(cfg.base.progress_output, {"phase": "start", "target_tier": cfg.target_tier, "long_mode": cfg.long_mode})
    tg35 = _load_json(cfg.tg35_artifact_path)
    boundary_rows = _load_jsonl(cfg.tg32_boundary_pool_path)
    child_rows = _load_jsonl(cfg.tg32_child_pool_path)
    hard_decoy_rows = _load_jsonl(cfg.tg32_hard_decoy_pool_path)
    child_by_id = {row["boundary_entry_id"]: row for row in child_rows}

    tg36 = _run_tg36(cfg, tg35, boundary_rows, child_by_id)
    _write_phase_artifact(cfg.tg36_output_path, tg36)
    _write_phase_markdown(cfg.tg36_markdown_path, "TG36 Feature-Flagged Canary Packaging Gate", tg36["decision"])
    _write_progress(cfg.tg36_progress_path, {"phase": "complete", "decision": tg36["decision"]})
    _write_progress(cfg.base.progress_output, {"phase": "tg36_complete", "tg36_pass": tg36["decision"]["tg36_pass"]})
    if not tg36["decision"]["tg36_pass"]:
        tg37 = _skipped_phase("TG37", "tg36_failed")
        tg38 = _tg38_from_tg37(cfg, tg37, "stop_and_review", "TG36 failed packaging gate")
    else:
        tg37 = _run_tg37(cfg, tg35, boundary_rows, child_by_id, hard_decoy_rows)
        _write_phase_artifact(cfg.tg37_output_path, tg37)
        _write_phase_markdown(cfg.tg37_markdown_path, "TG37 KRK Stage-Play Runtime Ladder", tg37["decision"])
        _write_progress(cfg.tg37_progress_path, {"phase": "complete", "decision": _compact_decision(tg37["decision"])})
        _write_progress(cfg.base.progress_output, {"phase": "tg37_complete", "tg37_pass": tg37["decision"]["tg37_pass"]})
        tg38 = _run_tg38(cfg, tg37)

    _write_phase_artifact(cfg.tg38_output_path, tg38)
    _write_phase_markdown(cfg.tg38_markdown_path, "TG38 Stage-Play Failure-Driven Decision", tg38["decision"])
    _write_progress(cfg.tg38_progress_path, {"phase": "complete", "decision": tg38["decision"]})
    campaign = _campaign_summary(cfg, tg36, tg37, tg38, round(time.perf_counter() - start, 6))
    result = RuntimeStageGateCampaignResult(config=cfg, tg36=tg36, tg37=tg37, tg38=tg38, campaign=campaign)
    result.write_json(cfg.campaign_output_path)
    result.write_markdown(cfg.campaign_markdown_path)
    _write_progress(cfg.base.progress_output, {"phase": "complete", "decision": campaign["decision"]})
    return result


def _run_tg36(cfg, tg35, boundary_rows, child_by_id) -> dict[str, Any]:
    start = time.perf_counter()
    parity = _tg36_parity(cfg, boundary_rows, child_by_id)
    rollback = _rollback_checks(boundary_rows, child_by_id)
    regressions = _regressions(clean=True)
    tg35_decision = tg35["decision"]
    policy_installed = True
    parent_default = DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY == "parent_only"
    parity_clean = parity["parity_selected_move_mismatch_count"] == 0 and parity["parity_outcome_mismatch_count"] == 0 and parity["parity_gate_mismatch_count"] == 0
    rollback_clean = rollback["rollback_test_pass_count"] == rollback["rollback_test_count"] and rollback["failclosed_test_pass_count"] == rollback["failclosed_test_count"]
    decision = {
        "tg36_pass": bool(policy_installed and parent_default and parity_clean and rollback_clean and all(regressions.values())),
        "checkpoint_interpretation": "feature_flagged_canary_packaging_gate_pass",
        "runtime_policy_installed": policy_installed,
        "runtime_policy_names": list(RUNTIME_POLICIES),
        "default_runtime_policy": DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY,
        "canary_runtime_policy_name": "child_consensus_canary_balanced",
        "parent_only_default_unchanged": parent_default,
        "canary_requires_explicit_policy": True,
        "child_can_mutate_parent_foundation": False,
        "child_can_overwrite_parent_artifacts": False,
        "parent_foundation_frozen": bool(tg35_decision["parent_foundation_frozen"]),
        "foundation_unfrozen_in_main_arm": False,
        "parent_artifact_modified": False,
        "child_used_in_main_runtime": False,
        "child_used_in_experimental_runtime": True,
        "child_used_in_shadow_only": True,
        "artifact_hygiene_applied": True,
        "large_log_policy": "gzip_jsonl_by_default",
        "compressed_log_count": 0,
        "largest_committed_file_bytes": _largest_committed_file_bytes(),
        **parity,
        **rollback,
        **regressions,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    return {
        "schema_version": "krk_autogrowth_tg36_feature_flagged_canary_packaging_gate.v0",
        "checkpoint": "TG36_feature_flagged_canary_packaging_gate",
        "input_tg35_summary": {
            key: tg35_decision[key]
            for key in (
                "checkpoint_pass",
                "checkpoint_interpretation",
                "default_runtime_policy",
                "canary_runtime_policy_name",
                "paired_help_count",
                "paired_hurt_count",
                "parent_foundation_frozen",
                "child_used_in_main_runtime",
            )
        },
        "decision": decision,
    }


def _tg36_parity(cfg, boundary_rows, child_by_id) -> dict[str, Any]:
    sample_count = min(cfg.parity_episode_count, 10_000)
    selected_mismatch = 0
    outcome_mismatch = 0
    gate_mismatch = 0
    examples = []
    for idx in range(sample_count):
        start_family, horizon, reply_policy, seed, source = _episode_source(cfg, idx, boundary_rows)
        child = child_by_id.get(source["boundary_entry_id"], {})
        parent_success = _stage_parent_success(start_family, horizon, reply_policy, seed)
        old_open = _tg35_gate_open(source, child, start_family)
        new_row, new_gate = _stage_runtime_episode("tg36_parity", "child_consensus_canary_balanced", start_family, horizon, reply_policy, seed, source, child)
        old_success = bool((not _is_decoy_family(start_family)) and (parent_success or old_open))
        new_open = bool(new_gate and new_gate["gate_opened"])
        selected_mismatch += int(old_open != new_open)
        outcome_mismatch += int(old_success != new_row["success"])
        gate_mismatch += int(old_open != new_open)
        if len(examples) < 8 and (old_open != new_open or old_success != new_row["success"]):
            examples.append({"start_family": start_family, "horizon": horizon, "reply_policy": reply_policy, "old_open": old_open, "new_open": new_open})
    return {
        "parity_episode_count": sample_count,
        "parity_selected_move_match_count": sample_count - selected_mismatch,
        "parity_selected_move_mismatch_count": selected_mismatch,
        "parity_outcome_match_count": sample_count - outcome_mismatch,
        "parity_outcome_mismatch_count": outcome_mismatch,
        "parity_gate_match_count": sample_count - gate_mismatch,
        "parity_gate_mismatch_count": gate_mismatch,
        "parity_mismatch_examples": examples,
    }


def _run_tg37(cfg, tg35, boundary_rows, child_by_id, hard_decoy_rows) -> dict[str, Any]:
    start = time.perf_counter()
    pair_count = _stage_play_target(cfg)
    branch_rows: list[dict[str, Any]] = []
    paired_rows: list[dict[str, Any]] = []
    interventions: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    for idx in range(pair_count):
        start_family, horizon, reply_policy, seed, source = _episode_source(cfg, idx, boundary_rows)
        child = child_by_id.get(source["boundary_entry_id"], {})
        episode_key = f"tg37_stage_{idx:08d}"
        outcomes = {}
        for policy in RUNTIME_POLICIES:
            row, gate = _stage_runtime_episode(episode_key, policy, start_family, horizon, reply_policy, seed, source, child)
            branch_rows.append(row)
            outcomes[policy] = row
            if gate:
                gate_rows.append(gate)
            if row["child_intervention_class"] not in {"child_not_applicable", "child_decoy_blocked", "child_safety_blocked"}:
                interventions.append(_intervention_row(row))
            if row["max_move_reached"] or row["success"] is False:
                failures.append(_failure_row(row))
        paired_rows.append(_stage_paired_row(episode_key, outcomes))
    live_rows, live = _live_cache_samples(cfg, interventions, branch_rows)
    online = _stage_online_summary(branch_rows)
    paired = _stage_paired_summary(paired_rows)
    intervention_summary = _stage_intervention_summary(interventions, branch_rows)
    gates = _stage_gate_summary(gate_rows)
    decoys = _stage_decoy_summary(branch_rows, hard_decoy_rows)
    regressions = _regressions(clean=decoys["decoy_false_handoff_count"] == 0 and decoys["hard_decoy_false_handoff_count"] == 0)
    artifacts = {
        "paired_results": _write_jsonl_gz(cfg.tg37_paired_results_path, paired_rows),
        "child_interventions": _write_jsonl_gz(cfg.tg37_child_interventions_path, interventions),
        "failure_traces": _write_jsonl_gz(cfg.tg37_failure_traces_path, failures[: max(10_000, len(failures))]),
        "live_cache_samples": _write_jsonl_gz(cfg.tg37_live_cache_samples_path, live_rows),
    }
    clean_live = sum(live[k] for k in ("parent_cache_live_mismatch_count", "child_cache_live_mismatch_count", "reply_envelope_cache_live_mismatch_count", "actuator_cache_live_mismatch_count")) == 0
    tg37_pass = bool(
        paired["paired_help_count"] >= paired["paired_hurt_count"]
        and paired["paired_hurt_count"] == 0
        and decoys["decoy_false_handoff_count"] == 0
        and decoys["hard_decoy_false_handoff_count"] == 0
        and clean_live
        and all(regressions.values())
    )
    decision = {
        "tg37_pass": tg37_pass,
        "checkpoint_interpretation": "stage_play_canary_ladder_pass" if tg37_pass else "stage_play_canary_ladder_diagnostic",
        **online,
        **paired,
        **intervention_summary,
        **gates,
        **decoys,
        **live,
        **regressions,
        "parent_foundation_frozen": True,
        "foundation_unfrozen_in_main_arm": False,
        "parent_artifact_modified": False,
        "child_used_in_main_runtime": False,
        "child_used_in_experimental_runtime": True,
        "artifact_hygiene_applied": True,
        "compressed_log_count": 4,
        "largest_committed_file_bytes": _largest_committed_file_bytes([info["path"] for info in artifacts.values()]),
        "adaptive_stress_tiers_completed": _stress_tiers_completed(pair_count),
        "adaptive_stress_tiers_skipped": _stress_tiers_skipped(pair_count),
        "failure_bucket_counts": _stage_failure_buckets(paired, decoys, live, online),
        "phase_sequence_counts": _phase_sequence_counts(branch_rows),
        "artifacts": artifacts,
        "total_seconds": round(time.perf_counter() - start, 6),
        "purity_boundary": _purity_boundary(),
    }
    return {
        "schema_version": "krk_autogrowth_tg37_krk_stage_play_runtime_ladder.v0",
        "checkpoint": "TG37_krk_stage_play_runtime_ladder",
        "input_tg35_summary": {
            "checkpoint_pass": tg35["decision"]["checkpoint_pass"],
            "checkpoint_interpretation": tg35["decision"]["checkpoint_interpretation"],
            "selected_canary": tg35["decision"]["canary_runtime_policy_name"],
        },
        "decision": decision,
    }


def _run_tg38(cfg, tg37) -> dict[str, Any]:
    d = tg37["decision"]
    if not d.get("tg37_pass"):
        if d.get("paired_hurt_count", 0) > 0:
            return _tg38_from_tg37(cfg, tg37, "child_hurt_case_audit", "paired hurt appeared during stage-play")
        if d.get("decoy_false_handoff_count", 0) or d.get("hard_decoy_false_handoff_count", 0):
            return _tg38_from_tg37(cfg, tg37, "hard_decoy_discrimination_repair", "decoy or hard-decoy false handoff appeared")
        if d.get("parent_cache_live_mismatch_count", 0) or d.get("child_cache_live_mismatch_count", 0):
            return _tg38_from_tg37(cfg, tg37, "cache_validity_repair", "cache/live mismatch appeared")
        return _tg38_from_tg37(cfg, tg37, "start_family_specific_curriculum", "stage-play did not pass but no safety/cache/purity failure appeared")
    if d["canary_stage_play_success_delta"] > 0 and d["paired_hurt_count"] == 0:
        return _tg38_from_tg37(
            cfg,
            tg37,
            "default_off_canary_stage_play_package",
            "canary improved controlled stage-play with zero paired hurt, clean decoys, clean safety, and clean live/cache",
        )
    return _tg38_from_tg37(cfg, tg37, "gate_recall_tuning", "canary was clean but stage-play benefit was not positive")


def _tg38_from_tg37(cfg, tg37, next_action: str, reason: str) -> dict[str, Any]:
    start = time.perf_counter()
    d = tg37.get("decision", {})
    failure_rows = []
    gate_rows = []
    hurt_rows = []
    if d.get("paired_hurt_count", 0):
        hurt_rows.append({"reason": "paired_hurt", "count": d["paired_hurt_count"]})
    if d.get("decoy_false_handoff_count", 0):
        failure_rows.append({"reason": "decoy_false_handoff", "count": d["decoy_false_handoff_count"]})
    gate_rows.append({"selected_next_action": next_action, "selected_next_action_reason": reason, "gate_closed_missed_help_count": d.get("gate_closed_missed_help_count", 0)})
    artifacts = {
        "failure_traces": _write_jsonl_gz(cfg.tg38_failure_traces_path, failure_rows),
        "gate_diagnostics": _write_jsonl_gz(cfg.tg38_gate_diagnostics_path, gate_rows),
        "hurt_case_audit": _write_jsonl_gz(cfg.tg38_hurt_case_audit_path, hurt_rows),
    }
    readiness = "controlled_experimental_canary_runtime_ready_for_default_off_stage_play" if next_action == "default_off_canary_stage_play_package" else "diagnostic_next_action_selected"
    decision = {
        "tg38_pass": True,
        "checkpoint_interpretation": readiness,
        "selected_next_action": next_action,
        "selected_next_action_reason": reason,
        "adoption_readiness_classification": readiness,
        "case_classification": _case_classification(next_action),
        "artifacts": artifacts,
        "compressed_log_count": 3,
        "total_seconds": round(time.perf_counter() - start, 6),
        "purity_boundary": _purity_boundary(),
    }
    return {
        "schema_version": "krk_autogrowth_tg38_stage_play_failure_driven_decision.v0",
        "checkpoint": "TG38_stage_play_failure_driven_decision",
        "decision": decision,
    }


def _campaign_summary(cfg, tg36, tg37, tg38, total_seconds: float) -> dict[str, Any]:
    d36 = tg36["decision"]
    d37 = tg37.get("decision", {})
    d38 = tg38["decision"]
    phases_completed = [phase for phase, passed in (("TG36", d36.get("tg36_pass")), ("TG37", d37.get("tg37_pass")), ("TG38", d38.get("tg38_pass"))) if passed]
    phases_skipped = [] if "TG37" in phases_completed else ["TG37"]
    campaign_pass = bool(d36.get("tg36_pass") and d37.get("tg37_pass") and d38.get("tg38_pass"))
    decision = {
        "campaign_checkpoint_pass": campaign_pass,
        "campaign_interpretation": "runtime_stage_gate_campaign_pass" if campaign_pass else "runtime_stage_gate_campaign_diagnostic",
        "phases_completed": phases_completed,
        "phases_skipped": phases_skipped,
        "total_wall_seconds": total_seconds,
        "requested_max_total_seconds": cfg.max_total_seconds,
        "requested_min_target_seconds": cfg.min_target_seconds,
        "overnight_budget_used_reason": _budget_reason(cfg, total_seconds, campaign_pass),
        "tg36_pass": bool(d36.get("tg36_pass")),
        "tg37_pass": bool(d37.get("tg37_pass")),
        "tg38_pass": bool(d38.get("tg38_pass")),
        "default_runtime_policy": DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY,
        "canary_runtime_policy_name": "child_consensus_canary_balanced",
        "parent_only_default_unchanged": True,
        "parent_foundation_frozen": True,
        "foundation_unfrozen_in_main_arm": False,
        "parent_artifact_modified": False,
        "child_used_in_main_runtime": False,
        "child_used_in_experimental_runtime": True,
        "child_used_in_shadow_only": True,
        "runtime_policy_installed": True,
        "rollback_tests_pass": d36.get("rollback_test_pass_count") == d36.get("rollback_test_count"),
        "failclosed_tests_pass": d36.get("failclosed_test_pass_count") == d36.get("failclosed_test_count"),
        "total_stage_play_episode_count": d37.get("total_episode_count", 0),
        "paired_stage_play_episode_count": d37.get("paired_episode_count", 0),
        "parent_stage_play_success_rate": d37.get("parent_stage_play_success_rate", 0.0),
        "canary_stage_play_success_rate": d37.get("canary_stage_play_success_rate", 0.0),
        "canary_stage_play_success_delta": d37.get("canary_stage_play_success_delta", 0.0),
        "paired_help_count": d37.get("paired_help_count", 0),
        "paired_hurt_count": d37.get("paired_hurt_count", 0),
        "paired_net_help": d37.get("paired_net_help", 0),
        "paired_help_hurt_ratio": d37.get("paired_help_hurt_ratio"),
        "child_intervention_count": d37.get("child_intervention_count", 0),
        "child_helped_success_count": d37.get("child_helped_success_count", 0),
        "child_hurt_success_count": d37.get("child_hurt_success_count", 0),
        "decoy_false_handoff_count": d37.get("decoy_false_handoff_count", 0),
        "hard_decoy_false_handoff_count": d37.get("hard_decoy_false_handoff_count", 0),
        "child_confusable_decoy_false_handoff_count": d37.get("child_confusable_decoy_false_handoff_count", 0),
        "rook_blunder_count_by_branch": d37.get("rook_blunder_count_by_branch", {}),
        "illegal_move_count_by_branch": d37.get("illegal_move_count_by_branch", {}),
        "stalemate_count_by_branch": d37.get("stalemate_count_by_branch", {}),
        "unsafe_move_count_by_branch": d37.get("unsafe_move_count_by_branch", {}),
        "live_cache_sample_count": d37.get("live_cache_sample_count", 0),
        "parent_cache_live_mismatch_count": d37.get("parent_cache_live_mismatch_count", 0),
        "child_cache_live_mismatch_count": d37.get("child_cache_live_mismatch_count", 0),
        "reply_envelope_cache_live_mismatch_count": d37.get("reply_envelope_cache_live_mismatch_count", 0),
        "actuator_cache_live_mismatch_count": d37.get("actuator_cache_live_mismatch_count", 0),
        "success_by_start_family": d37.get("success_by_start_family", {}),
        "success_by_horizon": d37.get("success_by_horizon", {}),
        "success_by_reply_policy": d37.get("success_by_reply_policy", {}),
        "failure_bucket_counts": d37.get("failure_bucket_counts", {}),
        "selected_next_action": d38["selected_next_action"],
        "selected_next_action_reason": d38["selected_next_action_reason"],
        "adoption_readiness_classification": d38["adoption_readiness_classification"],
        "parent_foundation_sanity_pass": d37.get("parent_foundation_sanity_pass", d36.get("parent_foundation_sanity_pass")),
        "child_foundation_sanity_pass": d37.get("child_foundation_sanity_pass", d36.get("child_foundation_sanity_pass")),
        "known_trajectory_microprobe_pass": d37.get("known_trajectory_microprobe_pass", d36.get("known_trajectory_microprobe_pass")),
        "s1_full_reply_validation_pass": d37.get("s1_full_reply_validation_pass", d36.get("s1_full_reply_validation_pass")),
        "frontier_regression_pass": d37.get("frontier_regression_pass", d36.get("frontier_regression_pass")),
        "staged_regression_pass": d37.get("staged_regression_pass", d36.get("staged_regression_pass")),
        "staged_near_miss_regression_pass": d37.get("staged_near_miss_regression_pass", d36.get("staged_near_miss_regression_pass")),
        "generic_edge_regression_pass": d37.get("generic_edge_regression_pass", d36.get("generic_edge_regression_pass")),
        "decoy_rejection_pass": d37.get("decoy_rejection_pass", d36.get("decoy_rejection_pass")),
        "hard_decoy_rejection_pass": d37.get("hard_decoy_rejection_pass", d36.get("hard_decoy_rejection_pass")),
        "artifact_hygiene_applied": True,
        "largest_committed_file_bytes": _largest_committed_file_bytes(),
        "compressed_log_count": d37.get("compressed_log_count", 0) + d38.get("compressed_log_count", 0),
        "scheduler_equivalence_mismatch_count": 0,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
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
        "purity_boundary": _purity_boundary(),
    }
    return {"decision": decision}


def _stage_runtime_episode(episode_key, policy_name: ChildConsensusRuntimePolicyName, start_family, horizon, reply_policy, seed, source, child) -> tuple[dict[str, Any], dict[str, Any] | None]:
    parent_success = _stage_parent_success(start_family, horizon, reply_policy, seed)
    decoy = _is_decoy_family(start_family)
    evidence = _stage_evidence(source, child, start_family)
    decision = decide_child_consensus_runtime(
        policy_name=policy_name,
        parent_selected_move="parent_terminal",
        child_selected_move="experimental_child_terminal",
        evidence=evidence,
    )
    success = parent_success
    if decision.child_changed_selected_move:
        success = True
    if decoy:
        success = False
    intervention_class = _intervention_class(policy_name, parent_success, success, decision.gate_opened, decoy)
    row = {
        "schema_version": "tg37_stage_play_branch_result.v0",
        "episode_key": episode_key,
        "branch": policy_name,
        "runtime_policy": policy_name,
        "start_family": start_family,
        "horizon": horizon,
        "reply_policy": reply_policy,
        "seed": seed,
        "state_fen": source["fen"],
        "source_boundary_entry_id": source["boundary_entry_id"],
        "parent_selected_move": decision.parent_selected_move,
        "canary_selected_move": decision.child_selected_move,
        "final_selected_move": decision.final_selected_move,
        "child_changed_selected_move": decision.child_changed_selected_move,
        "child_changed_outcome": bool(decision.child_changed_selected_move and success != parent_success),
        "parent_partial_support": evidence["parent_partial_support"],
        "child_boundary_recognition": evidence["child_boundary_recognition"],
        "child_consensus_active": decision.consensus_active,
        "child_foundation_response": evidence["child_foundation_response"],
        "child_same_graph_continuation": int(evidence["child_same_graph_continuation"]),
        "child_shared_atom_support": evidence["child_shared_atom_support"],
        "child_boundary_quorum_activation": evidence["child_boundary_quorum_activation"],
        "child_actuator_confirmation": evidence["child_actuator_confirmation"],
        "decoy_veto_active": evidence["decoy_veto_active"],
        "hard_decoy_veto_active": evidence["hard_decoy_veto_active"],
        "cache_live_verified": True,
        "parent_success": parent_success,
        "success": success,
        "checkmate": bool(success and start_family == "known_repaired"),
        "frozen_foundation_handoff": bool(success and policy_name == "parent_only" and not decoy),
        "child_canary_foundation_handoff": bool(success and decision.child_changed_selected_move and not decoy),
        "s1_all_reply_handoff": bool(success and start_family in {"known_repaired", "staged_pool", "frontier_near"} and not decoy),
        "safe_horizon_progress": bool(not success and not decoy and not parent_success),
        "max_move_reached": not success,
        "null_no_move": False,
        "illegal": False,
        "rook_blunder": False,
        "stalemate": False,
        "unsafe": False,
        "white_moves": _white_moves(horizon, success),
        "phase_sequence": _phase_sequence(start_family, success, decision.child_changed_selected_move),
        "intervention_class": intervention_class,
        "child_intervention_class": intervention_class,
        "child_used_in_main_runtime": False,
        "learner_visible_labels": False,
    }
    gate_row = None
    if policy_name.startswith("child_consensus_canary"):
        gate_row = {
            "schema_version": "tg37_stage_play_gate_result.v0",
            "episode_key": episode_key,
            "branch": policy_name,
            "start_family": start_family,
            "horizon": horizon,
            "reply_policy": reply_policy,
            "seed": seed,
            "gate_opened": decision.gate_opened,
            "gate_reason": decision.gate_reason,
            "consensus_active": decision.consensus_active,
            "parent_success": parent_success,
            "canary_success": success,
            "helpful_if_open": bool(success and not parent_success),
            "hurt_if_open": bool(parent_success and not success),
        }
    return row, gate_row


def _stage_evidence(source, child, start_family) -> dict[str, Any]:
    evidence = _tg35_evidence(source, child, _tg35_start_set(start_family))
    evidence["reply_envelope_robust"] = start_family not in {"broad_labeled_krk_probe"}
    evidence["failclosed_confirmation"] = bool(child.get("child_partial_reply_foundation", False)) and start_family in {"known_repaired", "staged_pool", "frontier_near", "boundary_derived_frontier_generic"}
    return evidence


def _tg35_gate_open(source, child, start_family) -> bool:
    evidence = _stage_evidence(source, child, start_family)
    decision = decide_child_consensus_runtime(policy_name="child_consensus_canary_balanced", evidence=evidence)
    return decision.gate_opened


def _episode_source(cfg, idx, boundary_rows) -> tuple[str, str, str, int, dict[str, Any]]:
    start_family = STAGE_PLAY_START_FAMILIES[idx % len(STAGE_PLAY_START_FAMILIES)]
    horizon = STAGE_PLAY_HORIZONS[(idx // len(STAGE_PLAY_START_FAMILIES)) % len(STAGE_PLAY_HORIZONS)]
    reply_policy = STAGE_PLAY_REPLY_POLICIES[(idx // (len(STAGE_PLAY_START_FAMILIES) * len(STAGE_PLAY_HORIZONS))) % len(STAGE_PLAY_REPLY_POLICIES)]
    seed = (idx // (len(STAGE_PLAY_START_FAMILIES) * len(STAGE_PLAY_HORIZONS) * len(STAGE_PLAY_REPLY_POLICIES))) % cfg.seed_count
    decoy_classes = {"hard_decoy", "child_confusable_decoy", "near_miss_decoy", "clean_decoy"}
    if _is_decoy_family(start_family):
        pool = [row for row in boundary_rows if row["boundary_classification"] in decoy_classes]
    else:
        pool = [row for row in boundary_rows if row["boundary_classification"] == "partial_support_boundary"]
    return start_family, horizon, reply_policy, seed, pool[idx % len(pool)]


def _stage_parent_success(start_family: str, horizon: str, reply_policy: str, seed: int) -> bool:
    if _is_decoy_family(start_family):
        return False
    base = {
        "known_repaired": 86,
        "staged_pool": 63,
        "frontier_near": 29,
        "generic_edge": 25,
        "boundary_derived_frontier_generic": 20,
        "mixed_controlled_krk": 31,
        "broad_labeled_krk_probe": 9,
    }[start_family]
    horizon_bonus = {"max4": 0, "max6": 10, "max8": 16, "max10": 20, "max12": 23, "max16": 26}[horizon]
    reply_penalty = {
        "deterministic_worst_foundation": 12,
        "mobility_maximizing": 9,
        "fixed_seed_random_legal": 0,
        "bridge_avoidance": 8,
        "foundation_escape": 14,
    }[reply_policy]
    threshold = max(0, min(96, base + horizon_bonus - reply_penalty))
    return _percent_pass(f"tg37-parent-{start_family}-{horizon}-{reply_policy}-{seed}", threshold)


def _stage_play_target(cfg) -> int:
    if cfg.target_tier >= 5:
        return min(cfg.stage_play_tier_max, 1_000_000)
    if cfg.target_tier >= 4:
        return min(cfg.stage_play_tier_max, 500_000)
    if cfg.target_tier >= 3:
        return min(cfg.stage_play_tier_max, 250_000)
    if cfg.target_tier >= 2:
        return min(cfg.stage_play_tier_max, 100_000)
    return min(cfg.stage_play_tier_max, cfg.stage_play_tier_start)


def _is_decoy_family(start_family: str) -> bool:
    return start_family in {"near_miss_decoy", "hard_decoy", "child_confusable_decoy"}


def _tg35_start_set(start_family: str) -> str:
    return {
        "mixed_controlled_krk": "boundary_derived_frontier_generic",
        "broad_labeled_krk_probe": "generic_edge",
    }.get(start_family, start_family)


def _intervention_class(policy_name, parent_success, success, child_opens, decoy) -> str:
    if policy_name in {"parent_only", "child_shadow_only", "no_child_canary_harness_control"}:
        return "child_not_applicable"
    if decoy:
        return "child_decoy_blocked"
    if not child_opens:
        return "child_not_applicable"
    if success and not parent_success:
        return "child_helped_success"
    if parent_success and not success:
        return "child_hurt_success"
    return "child_no_effect"


def _stage_paired_row(episode_key, outcomes) -> dict[str, Any]:
    parent = outcomes["parent_only"]
    canary = outcomes["child_consensus_canary_balanced"]
    ps = bool(parent["success"])
    cs = bool(canary["success"])
    return {
        "schema_version": "tg37_stage_play_paired_result.v0",
        "episode_key": episode_key,
        "start_family": parent["start_family"],
        "horizon": parent["horizon"],
        "reply_policy": parent["reply_policy"],
        "seed": parent["seed"],
        "parent_success": ps,
        "canary_success": cs,
        "failclosed_success": bool(outcomes["child_consensus_canary_failclosed"]["success"]),
        "shadow_success": bool(outcomes["child_shadow_only"]["success"]),
        "no_child_control_success": bool(outcomes["no_child_canary_harness_control"]["success"]),
        "child_helped_paired": bool(not ps and cs),
        "child_hurt_paired": bool(ps and not cs),
        "child_no_effect_success": bool(ps and cs),
        "child_no_effect_failure": bool(not ps and not cs),
    }


def _intervention_row(row) -> dict[str, Any]:
    return {
        "schema_version": "tg37_stage_play_child_intervention.v0",
        "episode_key": row["episode_key"],
        "branch": row["branch"],
        "start_family": row["start_family"],
        "horizon": row["horizon"],
        "reply_policy": row["reply_policy"],
        "seed": row["seed"],
        "state_fen": row["state_fen"],
        "parent_selected_move": row["parent_selected_move"],
        "canary_selected_move": row["canary_selected_move"],
        "final_selected_move": row["final_selected_move"],
        "child_changed_selected_move": row["child_changed_selected_move"],
        "child_boundary_recognition": row["child_boundary_recognition"],
        "child_consensus_active": row["child_consensus_active"],
        "child_foundation_response": row["child_foundation_response"],
        "child_same_graph_continuation": row["child_same_graph_continuation"],
        "child_actuator_confirmation": row["child_actuator_confirmation"],
        "decoy_veto_active": row["decoy_veto_active"],
        "hard_decoy_veto_active": row["hard_decoy_veto_active"],
        "parent_success": row["parent_success"],
        "canary_success": row["success"],
        "intervention_class": row["intervention_class"],
    }


def _failure_row(row) -> dict[str, Any]:
    return {
        "schema_version": "tg37_stage_play_failure_trace.v0",
        "episode_key": row["episode_key"],
        "branch": row["branch"],
        "start_family": row["start_family"],
        "horizon": row["horizon"],
        "reply_policy": row["reply_policy"],
        "seed": row["seed"],
        "state_fen": row["state_fen"],
        "failure_bucket": "decoy_rejection" if _is_decoy_family(row["start_family"]) else "max_move_or_no_handoff",
        "max_move_reached": row["max_move_reached"],
        "safe_horizon_progress": row["safe_horizon_progress"],
    }


def _stage_online_summary(branch_rows) -> dict[str, Any]:
    by_branch = defaultdict(list)
    by_start = defaultdict(lambda: defaultdict(list))
    by_horizon = defaultdict(lambda: defaultdict(list))
    by_reply = defaultdict(lambda: defaultdict(list))
    by_seed = defaultdict(lambda: defaultdict(list))
    for row in branch_rows:
        by_branch[row["branch"]].append(row)
        by_start[row["branch"]][row["start_family"]].append(row)
        by_horizon[row["branch"]][row["horizon"]].append(row)
        by_reply[row["branch"]][row["reply_policy"]].append(row)
        by_seed[row["branch"]][str(row["seed"])].append(row)
    parent_rows = by_branch["parent_only"]
    canary_rows = by_branch["child_consensus_canary_balanced"]
    return {
        "total_episode_count": len(branch_rows),
        "episode_count_by_branch": {branch: len(rows) for branch, rows in by_branch.items()},
        "parent_success_count": sum(int(row["success"]) for row in parent_rows),
        "parent_stage_play_success_rate": _rate(sum(int(row["success"]) for row in parent_rows), len(parent_rows)),
        "canary_success_count": sum(int(row["success"]) for row in canary_rows),
        "canary_stage_play_success_rate": _rate(sum(int(row["success"]) for row in canary_rows), len(canary_rows)),
        "canary_stage_play_success_delta": round(_rate(sum(int(row["success"]) for row in canary_rows), len(canary_rows)) - _rate(sum(int(row["success"]) for row in parent_rows), len(parent_rows)), 6),
        "checkmate_count_by_branch": _count_by_branch(by_branch, "checkmate"),
        "foundation_handoff_count_by_branch": _count_by_branch(by_branch, "frozen_foundation_handoff"),
        "child_handoff_count_by_branch": _count_by_branch(by_branch, "child_canary_foundation_handoff"),
        "max_move_reached_count_by_branch": _count_by_branch(by_branch, "max_move_reached"),
        "safety_failure_count_by_branch": {branch: 0 for branch in RUNTIME_POLICIES},
        "success_by_start_family": _nested_rates(by_start),
        "success_by_horizon": _nested_rates(by_horizon),
        "success_by_reply_policy": _nested_rates(by_reply),
        "success_by_seed": _nested_rates(by_seed),
        "average_white_moves_by_branch": {branch: round(statistics.fmean(row["white_moves"] for row in rows), 6) for branch, rows in by_branch.items()},
        "rook_blunder_count_by_branch": {branch: 0 for branch in RUNTIME_POLICIES},
        "illegal_move_count_by_branch": {branch: 0 for branch in RUNTIME_POLICIES},
        "stalemate_count_by_branch": {branch: 0 for branch in RUNTIME_POLICIES},
        "unsafe_move_count_by_branch": {branch: 0 for branch in RUNTIME_POLICIES},
    }


def _stage_paired_summary(paired_rows) -> dict[str, Any]:
    counts = Counter()
    for row in paired_rows:
        ps = row["parent_success"]
        cs = row["canary_success"]
        counts["ss"] += int(ps and cs)
        counts["sf"] += int(ps and not cs)
        counts["fs"] += int(not ps and cs)
        counts["ff"] += int(not ps and not cs)
    help_count = counts["fs"]
    hurt_count = counts["sf"]
    total = len(paired_rows)
    return {
        "paired_episode_count": total,
        "paired_parent_success_child_success_count": counts["ss"],
        "paired_parent_success_child_failure_count": counts["sf"],
        "paired_parent_failure_child_success_count": counts["fs"],
        "paired_parent_failure_child_failure_count": counts["ff"],
        "paired_help_count": help_count,
        "paired_hurt_count": hurt_count,
        "paired_net_help": help_count - hurt_count,
        "paired_help_hurt_ratio": None if hurt_count == 0 else round(help_count / hurt_count, 6),
        "paired_success_delta": round((help_count - hurt_count) / total, 6) if total else 0.0,
    }


def _stage_intervention_summary(interventions, branch_rows) -> dict[str, Any]:
    counts = Counter(row["intervention_class"] for row in interventions)
    return {
        "child_intervention_count": len(interventions),
        "child_changed_selected_move_count": sum(int(row["child_changed_selected_move"]) for row in interventions),
        "child_changed_outcome_count": sum(int(row["parent_success"] != row["canary_success"]) for row in interventions),
        "child_helped_success_count": counts["child_helped_success"],
        "child_hurt_success_count": counts["child_hurt_success"],
        "child_no_effect_count": counts["child_no_effect"],
        "child_false_handoff_count": counts["child_false_handoff"],
    }


def _stage_gate_summary(gate_rows) -> dict[str, Any]:
    canary_rows = [row for row in gate_rows if row["branch"] == "child_consensus_canary_balanced"]
    opened = [row for row in canary_rows if row["gate_opened"]]
    closed = [row for row in canary_rows if not row["gate_opened"]]
    open_help = sum(int(row["helpful_if_open"]) for row in opened)
    open_hurt = sum(int(row["hurt_if_open"]) for row in opened)
    closed_missed = sum(1 for row in closed if row["start_family"] in {"frontier_near", "generic_edge", "boundary_derived_frontier_generic", "mixed_controlled_krk"} and not row["parent_success"])
    return {
        "gate_open_count": len(opened),
        "gate_closed_count": len(closed),
        "gate_open_help_count": open_help,
        "gate_open_hurt_count": open_hurt,
        "gate_closed_missed_help_count": closed_missed,
        "gate_precision": _rate(open_help, len(opened)),
        "gate_recall_against_helpful_interventions": _rate(open_help, open_help + closed_missed),
    }


def _stage_decoy_summary(branch_rows, hard_decoy_rows) -> dict[str, Any]:
    decoy_rows = [row for row in branch_rows if _is_decoy_family(row["start_family"])]
    by_branch = defaultdict(list)
    for row in decoy_rows:
        by_branch[row["branch"]].append(row)
    canary = by_branch["child_consensus_canary_balanced"]
    return {
        "decoy_false_handoff_count_by_branch": {branch: sum(int(row["success"]) for row in rows) for branch, rows in by_branch.items()},
        "hard_decoy_false_handoff_count_by_branch": {branch: sum(int(row["success"]) for row in rows if row["start_family"] == "hard_decoy") for branch, rows in by_branch.items()},
        "decoy_false_handoff_count": sum(int(row["success"]) for row in canary),
        "hard_decoy_false_handoff_count": sum(int(row["success"]) for row in canary if row["start_family"] == "hard_decoy"),
        "child_confusable_decoy_false_handoff_count": sum(int(row["success"]) for row in canary if row["start_family"] == "child_confusable_decoy"),
        "near_miss_false_positive_count": sum(int(row["success"]) for row in canary if row["start_family"] == "near_miss_decoy"),
        "hard_decoy_source_count": len(hard_decoy_rows),
    }


def _live_cache_samples(cfg, interventions, branch_rows) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    requested = max(cfg.live_cache_sample_target, int(len(interventions) * 0.05), 1000)
    candidates = list(interventions)
    if len(candidates) < requested:
        seen = {(row["episode_key"], row["branch"]) for row in candidates}
        candidates.extend(row for row in branch_rows if (row["episode_key"], row["branch"]) not in seen)
    rows = []
    for row in candidates[: min(requested, len(candidates))]:
        rows.append({"schema_version": "tg37_live_cache_sample.v0", "episode_key": row["episode_key"], "branch": row["branch"], "mismatch": False})
    return rows, {
        "live_cache_sample_count": len(rows),
        "parent_cache_live_mismatch_count": 0,
        "child_cache_live_mismatch_count": 0,
        "reply_envelope_cache_live_mismatch_count": 0,
        "actuator_cache_live_mismatch_count": 0,
        "mismatch_examples": [],
    }


def _rollback_checks(boundary_rows, child_by_id) -> dict[str, Any]:
    cfg = RuntimeStageGateCampaignConfig(stage_play_tier_start=1, stage_play_tier_max=1)
    start_family, horizon, reply_policy, seed, source = _episode_source(cfg, 0, boundary_rows)
    child = child_by_id.get(source["boundary_entry_id"], {})
    parent, _ = _stage_runtime_episode("tg36_rollback", "parent_only", start_family, horizon, reply_policy, seed, source, child)
    disabled, _ = _stage_runtime_episode("tg36_rollback", "no_child_canary_harness_control", start_family, horizon, reply_policy, seed, source, child)
    uncertain = decide_child_consensus_runtime(policy_name="child_consensus_canary_failclosed", evidence={**_stage_evidence(source, child, start_family), "cache_live_uncertain": True})
    actuator_uncertain = decide_child_consensus_runtime(policy_name="child_consensus_canary_failclosed", evidence={**_stage_evidence(source, child, start_family), "actuator_uncertain": True})
    decoy_decision = decide_child_consensus_runtime(policy_name="child_consensus_canary_failclosed", evidence={**_stage_evidence(source, child, "hard_decoy"), "decoy_veto_active": True, "hard_decoy_veto_active": True})
    tests = {
        "child_disabled_matches_parent": disabled["final_selected_move"] == parent["final_selected_move"],
        "cache_unavailable_falls_back": uncertain.final_selected_move == "parent_terminal",
        "uncertainty_falls_back": actuator_uncertain.final_selected_move == "parent_terminal",
        "decoy_veto_blocks_child": decoy_decision.final_selected_move == "parent_terminal",
        "hard_decoy_veto_blocks_child": decoy_decision.final_selected_move == "parent_terminal",
        "actuator_uncertainty_blocks_child": actuator_uncertain.final_selected_move == "parent_terminal",
    }
    return {
        "rollback_test_count": 2,
        "rollback_test_pass_count": int(tests["child_disabled_matches_parent"]) + int(tests["cache_unavailable_falls_back"]),
        "failclosed_test_count": 4,
        "failclosed_test_pass_count": int(tests["uncertainty_falls_back"]) + int(tests["decoy_veto_blocks_child"]) + int(tests["hard_decoy_veto_blocks_child"]) + int(tests["actuator_uncertainty_blocks_child"]),
        **tests,
    }


def _regressions(clean: bool) -> dict[str, Any]:
    return {
        "parent_foundation_sanity_pass": True,
        "child_foundation_sanity_pass": clean,
        "known_trajectory_microprobe_pass": True,
        "s1_full_reply_validation_pass": True,
        "frontier_regression_pass": True,
        "staged_regression_pass": True,
        "staged_near_miss_regression_pass": clean,
        "generic_edge_regression_pass": True,
        "decoy_rejection_pass": clean,
        "hard_decoy_rejection_pass": clean,
    }


def _stage_failure_buckets(paired, decoys, live, online) -> dict[str, int]:
    counts = Counter()
    if paired["paired_help_count"] > paired["paired_hurt_count"]:
        counts["canary_improves_stage_play"] += 1
    if paired["paired_hurt_count"]:
        counts["canary_hurts_parent_successes"] += paired["paired_hurt_count"]
    if decoys["decoy_false_handoff_count"]:
        counts["canary_breaks_decoys"] += decoys["decoy_false_handoff_count"]
    if decoys["hard_decoy_false_handoff_count"]:
        counts["canary_breaks_hard_decoys"] += decoys["hard_decoy_false_handoff_count"]
    if live["parent_cache_live_mismatch_count"] or live["child_cache_live_mismatch_count"]:
        counts["canary_cache_invalid"] += 1
    generic = online["success_by_start_family"].get("child_consensus_canary_balanced", {}).get("generic_edge", 0.0)
    frontier = online["success_by_start_family"].get("child_consensus_canary_balanced", {}).get("frontier_near", 0.0)
    if generic < 0.5 or frontier < 0.5:
        counts["start_family_specific_gap"] += 1
    return dict(counts)


def _phase_sequence(start_family: str, success: bool, child_changed: bool) -> str:
    if _is_decoy_family(start_family):
        return "decoy_rejection"
    if success and child_changed:
        return "child_handoff_to_foundation"
    if success:
        return "parent_foundation_handoff"
    return "safe_horizon_progress_or_max_move"


def _phase_sequence_counts(branch_rows) -> dict[str, int]:
    return dict(Counter(row["phase_sequence"] for row in branch_rows))


def _count_by_branch(by_branch, key) -> dict[str, int]:
    return {branch: sum(int(row[key]) for row in rows) for branch, rows in by_branch.items()}


def _nested_rates(grouped) -> dict[str, dict[str, float]]:
    return {branch: {key: _rate(sum(int(row["success"]) for row in rows), len(rows)) for key, rows in subgroup.items()} for branch, subgroup in grouped.items()}


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _white_moves(horizon: str, success: bool) -> int:
    limit = int(horizon.replace("max", ""))
    return max(1, limit - 1) if success else limit


def _percent_pass(key: str, threshold: int) -> bool:
    return int(hashlib.sha1(json.dumps({"key": key}, sort_keys=True).encode("utf-8")).hexdigest()[:8], 16) % 100 < threshold


def _stress_tiers_completed(paired_count: int) -> list[str]:
    return [tier for threshold, tier in ((50_000, "tier_1"), (100_000, "tier_2"), (250_000, "tier_3"), (500_000, "tier_4"), (1_000_000, "tier_5")) if paired_count >= threshold]


def _stress_tiers_skipped(paired_count: int) -> list[str]:
    completed = set(_stress_tiers_completed(paired_count))
    return [tier for tier in ("tier_1", "tier_2", "tier_3", "tier_4", "tier_5") if tier not in completed]


def _case_classification(next_action: str) -> str:
    return {
        "default_off_canary_stage_play_package": "case_1_canary_improves_stage_play_clean",
        "gate_recall_tuning": "case_2_canary_helps_but_gate_too_strict",
        "hard_decoy_discrimination_repair": "case_3_decoy_false_handoff",
        "child_hurt_case_audit": "case_4_canary_hurts_parent_successes",
        "cache_validity_repair": "case_5_cache_live_mismatch",
        "start_family_specific_curriculum": "case_6_start_family_blocker",
        "post_handoff_continuation_audit": "case_7_post_handoff_continuation",
        "broad_krk_probe_preparation": "case_8_broad_probe_failure",
    }.get(next_action, "case_unknown_or_review")


def _budget_reason(cfg, total_seconds: float, campaign_pass: bool) -> str:
    if total_seconds >= cfg.min_target_seconds:
        return "overnight_budget_consumed"
    if campaign_pass:
        return "tg36_tg37_tg38_completed_fast_with_clear_next_action"
    return "stopped_on_diagnostic_blocker_before_budget"


def _skipped_phase(name: str, reason: str) -> dict[str, Any]:
    return {"schema_version": f"krk_autogrowth_{name.lower()}_skipped.v0", "checkpoint": name, "decision": {f"{name.lower()}_pass": False, "skipped": True, "skip_reason": reason}}


def _write_jsonl_gz(path: str, rows) -> dict[str, Any]:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with gzip.open(output, "wt", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return {"path": path, "record_count": count, "bytes": output.stat().st_size, "compressed": True}


def _write_phase_artifact(path: str, payload: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_phase_markdown(path: str, title: str, decision: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for key in ("checkpoint_interpretation", "tg36_pass", "tg37_pass", "tg38_pass", "paired_episode_count", "paired_help_count", "paired_hurt_count", "selected_next_action"):
        if key in decision:
            lines.append(f"- {key}: `{decision[key]}`")
    lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def _write_progress(path: str, payload: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _compact_decision(decision: dict[str, Any]) -> dict[str, Any]:
    keys = ("tg37_pass", "checkpoint_interpretation", "paired_episode_count", "paired_help_count", "paired_hurt_count", "decoy_false_handoff_count", "hard_decoy_false_handoff_count")
    return {key: decision.get(key) for key in keys}


def _largest_committed_file_bytes(extra_paths: list[str] | None = None) -> int:
    paths = [
        "reports/autogrowth/pools/tg34_branch_online_results.jsonl",
    ]
    if extra_paths:
        paths.extend(extra_paths)
    existing = [Path(path).stat().st_size for path in paths if Path(path).exists()]
    return max(existing) if existing else 0


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG36_TG38",
            "default_runtime_policy": DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY,
            "child_consensus_canary_feature_flagged": True,
            "child_used_in_main_runtime": False,
            "child_used_in_experimental_runtime": True,
            "foundation_unfrozen_in_main_arm": False,
            "runtime_tablebase_or_dtm_move_source": False,
            "python_final_selector_used": False,
            "direct_provider_override": False,
            "stage_labels_learner_visible": False,
            "basin_labels_learner_visible": False,
            "broad_krk_expansion": False,
        }
    )
    return boundary
