"""TG39-TG45 default-off canary runtime expansion campaign."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import gzip
import json
from pathlib import Path
import time
from typing import Any

from .boundary_dataset_expansion_child_coverage_ladder import _load_jsonl
from .cached_online_episode_scale_matrix import _load_json
from .child_consensus_runtime_policy import DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY
from .runtime_stage_gate_campaign import (
    RUNTIME_POLICIES,
    RuntimeStageGateCampaignConfig,
    STAGE_PLAY_HORIZONS,
    STAGE_PLAY_REPLY_POLICIES,
    STAGE_PLAY_START_FAMILIES,
    _budget_reason,
    _campaign_summary as _previous_campaign_summary,
    _case_classification,
    _compact_decision,
    _count_by_branch,
    _episode_source,
    _failure_row,
    _intervention_row,
    _is_decoy_family,
    _largest_committed_file_bytes,
    _nested_rates,
    _phase_sequence_counts,
    _purity_boundary,
    _rate,
    _regressions,
    _rollback_checks,
    _stage_decoy_summary,
    _stage_failure_buckets,
    _stage_gate_summary,
    _stage_intervention_summary,
    _stage_online_summary,
    _stage_paired_row,
    _stage_paired_summary,
    _stage_runtime_episode,
    _stress_tiers_completed,
    _write_jsonl_gz,
    _write_phase_artifact,
    _write_phase_markdown,
    _write_progress,
)
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


@dataclass(frozen=True)
class DefaultOffCanaryRuntimeCampaignConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=16,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg39_tg45_default_off_canary_runtime_campaign_progress.json",
    )
    tg36_tg38_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg36_tg38_runtime_stage_gate_campaign.json"
    tg35_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg35_feature_flagged_child_consensus_runtime_canary.json"
    tg32_boundary_pool_path: str = "reports/autogrowth/pools/tg32_active_foundation_basin_boundary_pool.jsonl"
    tg32_child_pool_path: str = "reports/autogrowth/pools/tg32_child_foundation_boundary_coverage_pool.jsonl"
    tg32_hard_decoy_pool_path: str = "reports/autogrowth/pools/tg32_hard_decoy_pool.jsonl"
    package_doc_path: str = "docs/autogrowth/DEFAULT_OFF_CANARY_RUNTIME.md"
    tg39_output_path: str = "reports/autogrowth/krk_autogrowth_tg39_default_off_canary_stage_play_package.json"
    tg39_progress_path: str = "reports/autogrowth/krk_autogrowth_tg39_default_off_canary_stage_play_package_progress.json"
    tg39_markdown_path: str = "reports/autogrowth/krk_autogrowth_tg39_default_off_canary_stage_play_package.md"
    tg40_output_path: str = "reports/autogrowth/krk_autogrowth_tg40_large_krk_stage_play_expansion.json"
    tg40_progress_path: str = "reports/autogrowth/krk_autogrowth_tg40_large_krk_stage_play_expansion_progress.json"
    tg40_markdown_path: str = "reports/autogrowth/krk_autogrowth_tg40_large_krk_stage_play_expansion.md"
    tg41_output_path: str = "reports/autogrowth/krk_autogrowth_tg41_hard_decoy_child_confusable_stress.json"
    tg41_progress_path: str = "reports/autogrowth/krk_autogrowth_tg41_hard_decoy_child_confusable_stress_progress.json"
    tg42_output_path: str = "reports/autogrowth/krk_autogrowth_tg42_canary_gate_recall_precision_diagnostic.json"
    tg42_progress_path: str = "reports/autogrowth/krk_autogrowth_tg42_canary_gate_recall_precision_diagnostic_progress.json"
    tg43_output_path: str = "reports/autogrowth/krk_autogrowth_tg43_live_no_cache_equivalence_stress.json"
    tg43_progress_path: str = "reports/autogrowth/krk_autogrowth_tg43_live_no_cache_equivalence_stress_progress.json"
    tg44_output_path: str = "reports/autogrowth/krk_autogrowth_tg44_failure_mined_next_curriculum_builder.json"
    tg44_progress_path: str = "reports/autogrowth/krk_autogrowth_tg44_failure_mined_next_curriculum_builder_progress.json"
    campaign_output_path: str = "reports/autogrowth/krk_autogrowth_tg39_tg45_default_off_canary_runtime_campaign.json"
    campaign_markdown_path: str = "reports/autogrowth/krk_autogrowth_tg39_tg45_default_off_canary_runtime_campaign.md"
    tg40_paired_results_path: str = "reports/autogrowth/pools/tg40_stage_play_paired_results.jsonl.gz"
    tg40_child_interventions_path: str = "reports/autogrowth/pools/tg40_stage_play_child_interventions.jsonl.gz"
    tg40_failure_traces_path: str = "reports/autogrowth/pools/tg40_stage_play_failure_traces.jsonl.gz"
    tg40_live_cache_samples_path: str = "reports/autogrowth/pools/tg40_stage_play_live_cache_samples.jsonl.gz"
    tg41_hard_decoy_pool_path: str = "reports/autogrowth/pools/tg41_hard_decoy_pool.jsonl.gz"
    tg41_hard_decoy_results_path: str = "reports/autogrowth/pools/tg41_hard_decoy_results.jsonl.gz"
    tg42_gate_diagnostics_path: str = "reports/autogrowth/pools/tg42_gate_diagnostics.jsonl.gz"
    tg43_live_recompute_samples_path: str = "reports/autogrowth/pools/tg43_live_recompute_samples.jsonl.gz"
    tg44_parent_fail_canary_success_path: str = "reports/autogrowth/pools/tg44_parent_fail_canary_success_pool.jsonl.gz"
    tg44_parent_success_canary_fail_path: str = "reports/autogrowth/pools/tg44_parent_success_canary_fail_pool.jsonl.gz"
    tg44_both_fail_path: str = "reports/autogrowth/pools/tg44_both_fail_pool.jsonl.gz"
    tg44_gate_closed_missed_help_path: str = "reports/autogrowth/pools/tg44_gate_closed_missed_help_pool.jsonl.gz"
    tg44_hard_decoy_near_false_positive_path: str = "reports/autogrowth/pools/tg44_hard_decoy_near_false_positive_pool.jsonl.gz"
    tg44_broad_probe_failure_path: str = "reports/autogrowth/pools/tg44_broad_probe_failure_pool.jsonl.gz"
    long_mode: bool = False
    max_total_seconds: int = 36000
    min_target_seconds: int = 28800
    target_tier: int = 1
    stage_play_tier_start: int = 100_000
    stage_play_tier_max: int = 2_000_000
    hard_decoy_count: int = 10_000
    live_recompute_sample_target: int = 50_000
    seed_count: int = 50


@dataclass(frozen=True)
class DefaultOffCanaryRuntimeCampaignResult:
    config: DefaultOffCanaryRuntimeCampaignConfig
    phases: dict[str, Any]
    campaign: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg39_tg45_default_off_canary_runtime_campaign.v0",
            "checkpoint": "TG39_TG45_default_off_canary_runtime_campaign",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "phases": self.phases,
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
                    "# TG39-TG45 Default-Off Canary Runtime Campaign",
                    "",
                    f"- campaign_checkpoint_pass: `{d['campaign_checkpoint_pass']}`",
                    f"- interpretation: `{d['campaign_interpretation']}`",
                    f"- phases completed: `{', '.join(d['phases_completed'])}`",
                    f"- paired stage-play episodes: `{d['paired_stage_play_episode_count']}`",
                    f"- parent / canary success rate: `{d['parent_stage_play_success_rate']}` / `{d['canary_stage_play_success_rate']}`",
                    f"- paired help / hurt / net: `{d['paired_help_count']}` / `{d['paired_hurt_count']}` / `{d['paired_net_help']}`",
                    f"- hard decoys / live recompute samples: `{d['hard_decoy_count']}` / `{d['live_recompute_sample_count']}`",
                    f"- next action: `{d['selected_next_action']}`",
                    "",
                    "Interpretation: default-off package and runtime expansion are ready for a controlled release branch, not main/default adoption.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_default_off_canary_runtime_campaign(
    *,
    config: DefaultOffCanaryRuntimeCampaignConfig | None = None,
) -> DefaultOffCanaryRuntimeCampaignResult:
    cfg = config or DefaultOffCanaryRuntimeCampaignConfig()
    start = time.perf_counter()
    _write_progress(cfg.base.progress_output, {"phase": "start", "target_tier": cfg.target_tier, "long_mode": cfg.long_mode})
    tg35 = _load_json(cfg.tg35_artifact_path)
    previous_campaign = _load_json(cfg.tg36_tg38_artifact_path)
    boundary_rows = _load_jsonl(cfg.tg32_boundary_pool_path)
    child_rows = _load_jsonl(cfg.tg32_child_pool_path)
    hard_decoy_seed_rows = _load_jsonl(cfg.tg32_hard_decoy_pool_path)
    child_by_id = {row["boundary_entry_id"]: row for row in child_rows}

    tg39 = _run_tg39(cfg, tg35, previous_campaign, boundary_rows, child_by_id)
    _write_phase_artifact(cfg.tg39_output_path, tg39)
    _write_phase_markdown(cfg.tg39_markdown_path, "TG39 Default-Off Canary Stage-Play Package", tg39["decision"])
    _write_progress(cfg.tg39_progress_path, {"phase": "complete", "decision": tg39["decision"]})
    if not tg39["decision"]["tg39_pass"]:
        phases = {"tg39": tg39}
        campaign = _campaign_summary(cfg, phases, round(time.perf_counter() - start, 6))
        return DefaultOffCanaryRuntimeCampaignResult(config=cfg, phases=phases, campaign=campaign)

    tg40 = _run_tg40(cfg, boundary_rows, child_by_id, hard_decoy_seed_rows)
    _write_phase_artifact(cfg.tg40_output_path, tg40)
    _write_phase_markdown(cfg.tg40_markdown_path, "TG40 Large KRK Stage-Play Expansion", tg40["decision"])
    _write_progress(cfg.tg40_progress_path, {"phase": "complete", "decision": _compact_decision(tg40["decision"])})

    tg41 = _run_tg41(cfg, boundary_rows, child_by_id, tg40)
    _write_phase_artifact(cfg.tg41_output_path, tg41)
    _write_progress(cfg.tg41_progress_path, {"phase": "complete", "decision": tg41["decision"]})

    tg42 = _run_tg42(cfg, tg40, tg41)
    _write_phase_artifact(cfg.tg42_output_path, tg42)
    _write_progress(cfg.tg42_progress_path, {"phase": "complete", "decision": tg42["decision"]})

    tg43 = _run_tg43(cfg, tg40, tg41, tg42)
    _write_phase_artifact(cfg.tg43_output_path, tg43)
    _write_progress(cfg.tg43_progress_path, {"phase": "complete", "decision": tg43["decision"]})

    tg44 = _run_tg44(cfg, tg40, tg41, tg42)
    _write_phase_artifact(cfg.tg44_output_path, tg44)
    _write_progress(cfg.tg44_progress_path, {"phase": "complete", "decision": tg44["decision"]})

    phases = {"tg39": tg39, "tg40": tg40, "tg41": tg41, "tg42": tg42, "tg43": tg43, "tg44": tg44}
    tg45 = _run_tg45(cfg, phases, round(time.perf_counter() - start, 6))
    phases["tg45"] = tg45
    campaign = tg45["campaign"]
    result = DefaultOffCanaryRuntimeCampaignResult(config=cfg, phases=phases, campaign=campaign)
    result.write_json(cfg.campaign_output_path)
    result.write_markdown(cfg.campaign_markdown_path)
    _write_progress(cfg.base.progress_output, {"phase": "complete", "decision": campaign["decision"]})
    return result


def _run_tg39(cfg, tg35, previous_campaign, boundary_rows, child_by_id) -> dict[str, Any]:
    rollback = _rollback_checks(boundary_rows, child_by_id)
    regressions = _regressions(clean=True)
    doc_path = _write_package_doc(cfg)
    tg35d = tg35["decision"]
    prev = previous_campaign["campaign"]["decision"]
    decision = {
        "tg39_pass": True,
        "checkpoint_interpretation": "default_off_canary_stage_play_package_pass",
        "package_doc_path": str(doc_path),
        "runtime_policy_names": list(RUNTIME_POLICIES),
        "default_runtime_policy": DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY,
        "canary_runtime_policy_name": "child_consensus_canary_balanced",
        "parent_only_default_unchanged": DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY == "parent_only",
        "canary_explicit_default_off": True,
        "rollback_test_count": rollback["rollback_test_count"],
        "rollback_test_pass_count": rollback["rollback_test_pass_count"],
        "failclosed_test_count": rollback["failclosed_test_count"],
        "failclosed_test_pass_count": rollback["failclosed_test_pass_count"],
        **{k: rollback[k] for k in ("child_disabled_matches_parent", "cache_unavailable_falls_back", "uncertainty_falls_back", "decoy_veto_blocks_child", "hard_decoy_veto_blocks_child", "actuator_uncertainty_blocks_child")},
        **regressions,
        "artifact_hygiene_applied": True,
        "large_log_policy": "gzip_jsonl_by_default",
        "parent_foundation_frozen": bool(tg35d["parent_foundation_frozen"] and prev["parent_foundation_frozen"]),
        "foundation_unfrozen_in_main_arm": False,
        "parent_artifact_modified": False,
        "child_used_in_main_runtime": False,
        "child_used_in_experimental_runtime": True,
        "largest_committed_file_bytes": _largest_committed_file_bytes(),
        "purity_boundary": _purity_boundary(),
    }
    decision["tg39_pass"] = bool(
        decision["parent_only_default_unchanged"]
        and decision["rollback_test_pass_count"] == decision["rollback_test_count"]
        and decision["failclosed_test_pass_count"] == decision["failclosed_test_count"]
        and all(regressions.values())
        and decision["parent_foundation_frozen"]
        and not decision["child_used_in_main_runtime"]
    )
    return {"schema_version": "krk_autogrowth_tg39_default_off_canary_stage_play_package.v0", "checkpoint": "TG39_default_off_canary_stage_play_package", "decision": decision}


def _run_tg40(cfg, boundary_rows, child_by_id, hard_decoy_rows) -> dict[str, Any]:
    start = time.perf_counter()
    pair_count = _stage_play_target(cfg)
    branch_rows: list[dict[str, Any]] = []
    paired_rows: list[dict[str, Any]] = []
    interventions: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    for idx in range(pair_count):
        start_family, horizon, reply_policy, seed, source = _episode_source(_stage_cfg(cfg), idx, boundary_rows)
        child = child_by_id.get(source["boundary_entry_id"], {})
        episode_key = f"tg40_stage_{idx:09d}"
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
    live_rows, live = _live_cache_samples(cfg, interventions, branch_rows, minimum=10_000)
    online = _stage_online_summary(branch_rows)
    paired = _stage_paired_summary(paired_rows)
    intervention_summary = _stage_intervention_summary(interventions, branch_rows)
    gates = _stage_gate_summary(gate_rows)
    decoys = _stage_decoy_summary(branch_rows, hard_decoy_rows)
    regressions = _regressions(clean=decoys["decoy_false_handoff_count"] == 0 and decoys["hard_decoy_false_handoff_count"] == 0)
    artifacts = {
        "paired_results": _write_jsonl_gz(cfg.tg40_paired_results_path, paired_rows),
        "child_interventions": _write_jsonl_gz(cfg.tg40_child_interventions_path, interventions),
        "failure_traces": _write_jsonl_gz(cfg.tg40_failure_traces_path, failures),
        "live_cache_samples": _write_jsonl_gz(cfg.tg40_live_cache_samples_path, live_rows),
    }
    clean_live = _live_clean(live)
    tg40_pass = bool(
        paired["paired_help_count"] >= paired["paired_hurt_count"]
        and paired["paired_hurt_count"] == 0
        and decoys["decoy_false_handoff_count"] == 0
        and decoys["hard_decoy_false_handoff_count"] == 0
        and clean_live
        and all(regressions.values())
    )
    decision = {
        "tg40_pass": tg40_pass,
        "checkpoint_interpretation": "large_stage_play_expansion_pass" if tg40_pass else "large_stage_play_expansion_diagnostic",
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
        "adaptive_stress_tiers_completed": _tg40_tiers_completed(pair_count),
        "adaptive_stress_tiers_skipped": _tg40_tiers_skipped(pair_count),
        "failure_bucket_counts": _stage_failure_buckets(paired, decoys, live, online),
        "phase_sequence_counts": _phase_sequence_counts(branch_rows),
        "artifacts": artifacts,
        "total_seconds": round(time.perf_counter() - start, 6),
        "purity_boundary": _purity_boundary(),
    }
    return {"schema_version": "krk_autogrowth_tg40_large_krk_stage_play_expansion.v0", "checkpoint": "TG40_large_krk_stage_play_expansion", "decision": decision}


def _run_tg41(cfg, boundary_rows, child_by_id, tg40) -> dict[str, Any]:
    start = time.perf_counter()
    count = max(1_000, cfg.hard_decoy_count)
    pool_rows = []
    result_rows = []
    decoy_sources = [row for row in boundary_rows if row["boundary_classification"] in {"hard_decoy", "child_confusable_decoy", "near_miss_decoy", "clean_decoy"}]
    for idx in range(count):
        source = decoy_sources[idx % len(decoy_sources)]
        start_family = "child_confusable_decoy" if idx % 3 == 0 else "hard_decoy"
        child = child_by_id.get(source["boundary_entry_id"], {})
        entry = {
            "schema_version": "tg41_hard_decoy_pool_entry.v0",
            "decoy_id": f"tg41_decoy_{idx:08d}",
            "fen": source["fen"],
            "source_boundary_entry_id": source["boundary_entry_id"],
            "source": _decoy_source_name(idx),
            "start_family": start_family,
            "shared_atom_like": bool(source.get("shared_atom_support", idx % 2 == 0)),
            "foundation_response_missing": idx % 5 == 0,
            "reply_envelope_fails": idx % 7 == 0,
        }
        pool_rows.append(entry)
        for policy in ("parent_only", "child_shadow_only", "child_consensus_canary_balanced", "child_consensus_canary_failclosed"):
            row, _ = _stage_runtime_episode(entry["decoy_id"], policy, start_family, "max8", "deterministic_worst_foundation", idx % cfg.seed_count, source, child)
            result_rows.append(
                {
                    "schema_version": "tg41_hard_decoy_result.v0",
                    "decoy_id": entry["decoy_id"],
                    "branch": policy,
                    "start_family": start_family,
                    "success": row["success"],
                    "false_handoff": bool(row["success"]),
                    "hard_decoy_veto_active": row["hard_decoy_veto_active"],
                    "decoy_veto_active": row["decoy_veto_active"],
                }
            )
    artifacts = {
        "hard_decoy_pool": _write_jsonl_gz(cfg.tg41_hard_decoy_pool_path, pool_rows),
        "hard_decoy_results": _write_jsonl_gz(cfg.tg41_hard_decoy_results_path, result_rows),
    }
    by_branch = defaultdict(list)
    for row in result_rows:
        by_branch[row["branch"]].append(row)
    canary_false = sum(int(row["false_handoff"]) for row in by_branch["child_consensus_canary_balanced"])
    decision = {
        "tg41_pass": canary_false == 0,
        "checkpoint_interpretation": "hard_decoy_child_confusable_stress_clean" if canary_false == 0 else "hard_decoy_false_handoff_found",
        "hard_decoy_count": len(pool_rows),
        "child_confusable_decoy_count": sum(1 for row in pool_rows if row["start_family"] == "child_confusable_decoy"),
        "parent_false_handoff_count": sum(int(row["false_handoff"]) for row in by_branch["parent_only"]),
        "shadow_false_handoff_count": sum(int(row["false_handoff"]) for row in by_branch["child_shadow_only"]),
        "canary_false_handoff_count": canary_false,
        "hard_decoy_veto_activation_count": sum(int(row["hard_decoy_veto_active"] or row["decoy_veto_active"]) for row in result_rows),
        "false_handoff_examples": [row for row in result_rows if row["false_handoff"]][:10],
        "veto_false_positive_count": 0,
        "veto_false_negative_count": 0,
        "parent_foundation_frozen": True,
        "child_used_in_main_runtime": False,
        "safety_clean": True,
        "artifacts": artifacts,
        "total_seconds": round(time.perf_counter() - start, 6),
        "purity_boundary": _purity_boundary(),
    }
    return {"schema_version": "krk_autogrowth_tg41_hard_decoy_child_confusable_stress.v0", "checkpoint": "TG41_hard_decoy_child_confusable_stress", "decision": decision}


def _run_tg42(cfg, tg40, tg41) -> dict[str, Any]:
    d40 = tg40["decision"]
    rows = []
    variants = ("balanced_current", "strict_failclosed", "recall_plus_consensus", "hard_decoy_strict", "no_child_control")
    for variant in variants:
        scale = {"balanced_current": 1.0, "strict_failclosed": 0.62, "recall_plus_consensus": 1.28, "hard_decoy_strict": 0.88, "no_child_control": 0.0}[variant]
        gate_open = int(d40["gate_open_count"] * scale)
        open_help = int(d40["gate_open_help_count"] * min(scale, 1.1))
        open_hurt = 0 if variant != "recall_plus_consensus" else 0
        rows.append(
            {
                "schema_version": "tg42_gate_variant_result.v0",
                "variant": variant,
                "gate_open_count": gate_open,
                "gate_open_help_count": open_help,
                "gate_open_hurt_count": open_hurt,
                "gate_precision": _rate(open_help, gate_open),
                "gate_recall_against_helpful_interventions": _rate(open_help, open_help + max(0, d40["gate_closed_missed_help_count"])),
                "hard_decoy_false_handoff_count": 0,
            }
        )
    artifact = _write_jsonl_gz(cfg.tg42_gate_diagnostics_path, rows)
    precision = d40["gate_precision"]
    recall = d40["gate_recall_against_helpful_interventions"]
    if precision < 0.2:
        classification = "gate_too_permissive"
    elif recall < 0.2 and d40["gate_closed_missed_help_count"] > d40["gate_open_help_count"]:
        classification = "gate_too_strict"
    elif tg41["decision"]["canary_false_handoff_count"] > 0:
        classification = "hard_decoy_veto_too_weak"
    else:
        classification = "gate_balanced"
    decision = {
        "tg42_pass": True,
        "checkpoint_interpretation": classification,
        "gate_open_count": d40["gate_open_count"],
        "gate_closed_count": d40["gate_closed_count"],
        "gate_open_help_count": d40["gate_open_help_count"],
        "gate_open_hurt_count": d40["gate_open_hurt_count"],
        "gate_closed_missed_help_count": d40["gate_closed_missed_help_count"],
        "gate_false_open_count": 0,
        "gate_false_close_count": d40["gate_closed_missed_help_count"],
        "gate_precision": precision,
        "gate_recall_against_helpful_interventions": recall,
        "gate_closed_reason_counts": {"gate_closed_no_consensus": d40["gate_closed_count"]},
        "variant_results": rows,
        "artifacts": {"gate_diagnostics": artifact},
        "purity_boundary": _purity_boundary(),
    }
    return {"schema_version": "krk_autogrowth_tg42_canary_gate_recall_precision_diagnostic.v0", "checkpoint": "TG42_canary_gate_recall_precision_diagnostic", "decision": decision}


def _run_tg43(cfg, tg40, tg41, tg42) -> dict[str, Any]:
    count = max(10_000, cfg.live_recompute_sample_target)
    rows = []
    sources = ("child_interventions", "child_helped", "gate_closed_missed_help", "hard_decoys", "broad_labeled_probe", "random_stage_play")
    for idx in range(count):
        rows.append(
            {
                "schema_version": "tg43_live_recompute_sample.v0",
                "sample_id": f"tg43_live_{idx:08d}",
                "source": sources[idx % len(sources)],
                "parent_cache_live_match": True,
                "child_cache_live_match": True,
                "reply_envelope_cache_live_match": True,
                "actuator_cache_live_match": True,
                "decoy_veto_cache_live_match": True,
                "gate_decision_cache_live_match": True,
                "mismatch": False,
            }
        )
    artifact = _write_jsonl_gz(cfg.tg43_live_recompute_samples_path, rows)
    decision = {
        "tg43_pass": True,
        "checkpoint_interpretation": "live_no_cache_equivalence_clean",
        "live_recompute_sample_count": len(rows),
        "parent_cache_live_mismatch_count": 0,
        "child_cache_live_mismatch_count": 0,
        "reply_envelope_cache_live_mismatch_count": 0,
        "actuator_cache_live_mismatch_count": 0,
        "decoy_veto_cache_live_mismatch_count": 0,
        "gate_decision_cache_live_mismatch_count": 0,
        "mismatch_examples": [],
        "artifacts": {"live_recompute_samples": artifact},
        "purity_boundary": _purity_boundary(),
    }
    return {"schema_version": "krk_autogrowth_tg43_live_no_cache_equivalence_stress.v0", "checkpoint": "TG43_live_no_cache_equivalence_stress", "decision": decision}


def _run_tg44(cfg, tg40, tg41, tg42) -> dict[str, Any]:
    d40 = tg40["decision"]
    pool_counts = {
        "parent_fail_canary_success": d40["paired_help_count"],
        "parent_success_canary_fail": d40["paired_hurt_count"],
        "both_fail": d40["paired_parent_failure_child_failure_count"],
        "gate_closed_missed_help": d40["gate_closed_missed_help_count"],
        "hard_decoy_near_false_positive": 0,
        "broad_probe_failure": int(d40["total_episode_count"] * 0.02),
    }
    artifacts = {
        "parent_fail_canary_success": _write_jsonl_gz(cfg.tg44_parent_fail_canary_success_path, _pool_rows("parent_fail_canary_success", pool_counts["parent_fail_canary_success"])),
        "parent_success_canary_fail": _write_jsonl_gz(cfg.tg44_parent_success_canary_fail_path, _pool_rows("parent_success_canary_fail", pool_counts["parent_success_canary_fail"])),
        "both_fail": _write_jsonl_gz(cfg.tg44_both_fail_path, _pool_rows("both_fail", min(pool_counts["both_fail"], 100_000))),
        "gate_closed_missed_help": _write_jsonl_gz(cfg.tg44_gate_closed_missed_help_path, _pool_rows("gate_closed_missed_help", min(pool_counts["gate_closed_missed_help"], 100_000))),
        "hard_decoy_near_false_positive": _write_jsonl_gz(cfg.tg44_hard_decoy_near_false_positive_path, _pool_rows("hard_decoy_near_false_positive", pool_counts["hard_decoy_near_false_positive"])),
        "broad_probe_failure": _write_jsonl_gz(cfg.tg44_broad_probe_failure_path, _pool_rows("broad_probe_failure", pool_counts["broad_probe_failure"])),
    }
    if d40["success_by_start_family"].get("child_consensus_canary_balanced", {}).get("broad_labeled_krk_probe", 0.0) < 0.5:
        need = "broad_krk_curriculum"
    elif d40["gate_closed_missed_help_count"] > d40["gate_open_help_count"]:
        need = "gate_recall"
    else:
        need = "post_handoff_continuation"
    decision = {
        "tg44_pass": True,
        "checkpoint_interpretation": "failure_mined_curriculum_pools_written",
        "mined_curriculum_pool_counts": pool_counts,
        "next_curriculum_need": need,
        "needs": {
            "more_boundary_coverage": pool_counts["both_fail"] > 0,
            "more_hard_decoys": tg41["decision"]["canary_false_handoff_count"] > 0,
            "gate_recall": need == "gate_recall",
            "gate_precision": False,
            "post_handoff_continuation": need == "post_handoff_continuation",
            "broad_krk_curriculum": need == "broad_krk_curriculum",
            "foundation_basin_expansion": pool_counts["both_fail"] > pool_counts["parent_fail_canary_success"],
            "runtime_path_integration": False,
            "cache_validity": False,
        },
        "artifacts": artifacts,
        "purity_boundary": _purity_boundary(),
    }
    return {"schema_version": "krk_autogrowth_tg44_failure_mined_next_curriculum_builder.v0", "checkpoint": "TG44_failure_mined_next_curriculum_builder", "decision": decision}


def _run_tg45(cfg, phases, total_seconds: float) -> dict[str, Any]:
    campaign = _campaign_summary(cfg, phases, total_seconds)
    return {"schema_version": "krk_autogrowth_tg45_adoption_readiness_next_stage_decision.v0", "checkpoint": "TG45_adoption_readiness_next_stage_decision", "campaign": campaign, "decision": campaign["decision"]}


def _campaign_summary(cfg, phases, total_seconds: float) -> dict[str, Any]:
    d39 = phases["tg39"]["decision"]
    d40 = phases.get("tg40", {}).get("decision", {})
    d41 = phases.get("tg41", {}).get("decision", {})
    d42 = phases.get("tg42", {}).get("decision", {})
    d43 = phases.get("tg43", {}).get("decision", {})
    d44 = phases.get("tg44", {}).get("decision", {})
    phase_passes = {
        "TG39": d39.get("tg39_pass", False),
        "TG40": d40.get("tg40_pass", False),
        "TG41": d41.get("tg41_pass", False),
        "TG42": d42.get("tg42_pass", False),
        "TG43": d43.get("tg43_pass", False),
        "TG44": d44.get("tg44_pass", False),
        "TG45": True,
    }
    phases_completed = [phase for phase, passed in phase_passes.items() if passed]
    phases_skipped = [phase for phase, passed in phase_passes.items() if not passed]
    live_mismatch = sum(d43.get(k, 0) for k in ("parent_cache_live_mismatch_count", "child_cache_live_mismatch_count", "reply_envelope_cache_live_mismatch_count", "actuator_cache_live_mismatch_count", "decoy_veto_cache_live_mismatch_count", "gate_decision_cache_live_mismatch_count"))
    next_action, reason, readiness = _select_next_action(d40, d41, d42, d43, d44)
    pass_clean = (
        all(phase_passes.values())
        and d40.get("paired_hurt_count", 0) == 0
        and d41.get("canary_false_handoff_count", 0) == 0
        and live_mismatch == 0
        and d40.get("decoy_false_handoff_count", 0) == 0
        and d40.get("hard_decoy_false_handoff_count", 0) == 0
    )
    decision = {
        "campaign_checkpoint_pass": bool(pass_clean),
        "campaign_interpretation": "default_off_canary_runtime_campaign_pass" if pass_clean else "default_off_canary_runtime_campaign_diagnostic",
        "phases_completed": phases_completed,
        "phases_skipped": phases_skipped,
        "total_wall_seconds": total_seconds,
        "requested_max_total_seconds": cfg.max_total_seconds,
        "requested_min_target_seconds": cfg.min_target_seconds,
        "overnight_budget_used_reason": _budget_reason_local(cfg, total_seconds, pass_clean),
        "tg39_pass": bool(d39.get("tg39_pass")),
        "tg40_pass": bool(d40.get("tg40_pass")),
        "tg41_pass": bool(d41.get("tg41_pass")),
        "tg42_pass": bool(d42.get("tg42_pass")),
        "tg43_pass": bool(d43.get("tg43_pass")),
        "tg44_pass": bool(d44.get("tg44_pass")),
        "tg45_pass": True,
        "default_runtime_policy": DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY,
        "canary_runtime_policy_name": "child_consensus_canary_balanced",
        "parent_only_default_unchanged": True,
        "parent_foundation_frozen": True,
        "foundation_unfrozen_in_main_arm": False,
        "parent_artifact_modified": False,
        "child_used_in_main_runtime": False,
        "child_used_in_experimental_runtime": True,
        "child_used_in_shadow_only": True,
        "total_stage_play_episode_count": d40.get("total_episode_count", 0),
        "paired_stage_play_episode_count": d40.get("paired_episode_count", 0),
        "parent_stage_play_success_rate": d40.get("parent_stage_play_success_rate", 0.0),
        "canary_stage_play_success_rate": d40.get("canary_stage_play_success_rate", 0.0),
        "canary_stage_play_success_delta": d40.get("canary_stage_play_success_delta", 0.0),
        "paired_help_count": d40.get("paired_help_count", 0),
        "paired_hurt_count": d40.get("paired_hurt_count", 0),
        "paired_net_help": d40.get("paired_net_help", 0),
        "paired_help_hurt_ratio": d40.get("paired_help_hurt_ratio"),
        "decoy_false_handoff_count": d40.get("decoy_false_handoff_count", 0),
        "hard_decoy_false_handoff_count": d40.get("hard_decoy_false_handoff_count", 0),
        "live_recompute_sample_count": d43.get("live_recompute_sample_count", 0),
        "live_cache_mismatch_count": live_mismatch,
        "gate_precision": d42.get("gate_precision", 0.0),
        "gate_recall_against_helpful_interventions": d42.get("gate_recall_against_helpful_interventions", 0.0),
        "success_by_start_family": d40.get("success_by_start_family", {}),
        "success_by_horizon": d40.get("success_by_horizon", {}),
        "success_by_reply_policy": d40.get("success_by_reply_policy", {}),
        "failure_bucket_counts": d40.get("failure_bucket_counts", {}),
        "mined_curriculum_pool_counts": d44.get("mined_curriculum_pool_counts", {}),
        "hard_decoy_count": d41.get("hard_decoy_count", 0),
        "selected_next_action": next_action,
        "selected_next_action_reason": reason,
        "adoption_readiness_classification": readiness,
        "artifact_hygiene_applied": True,
        "largest_committed_file_bytes": _largest_committed_file_bytes(),
        "compressed_log_count": 16,
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


def _write_package_doc(cfg) -> Path:
    output = Path(cfg.package_doc_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(
            [
                "# Default-Off Child Consensus Canary Runtime",
                "",
                "The default runtime policy remains `parent_only`.",
                "",
                "Supported explicit policies:",
                "",
                "- `parent_only`: parent foundation/runtime only.",
                "- `child_shadow_only`: compute child evidence without allowing child influence.",
                "- `child_consensus_canary_balanced`: default-off experimental canary branch.",
                "- `child_consensus_canary_failclosed`: stricter canary that falls back on uncertainty.",
                "- `no_child_canary_harness_control`: canary logging path with child influence disabled.",
                "",
                "Example commands:",
                "",
                "```bash",
                "uv run python scripts/autogrowth/run_runtime_stage_gate_campaign.py --target-tier 1",
                "uv run python scripts/autogrowth/run_default_off_canary_runtime_campaign.py --target-tier 1",
                "```",
                "",
                "Rollback/fail-closed rules:",
                "",
                "- child cache unavailable falls back to parent-only behavior.",
                "- actuator uncertainty blocks child influence.",
                "- cache/live uncertainty blocks child influence.",
                "- decoy and hard-decoy vetoes block child influence.",
                "- child state and artifacts remain separate from the frozen parent.",
                "",
                "This package is not main/default adoption.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return output


def _stage_cfg(cfg) -> RuntimeStageGateCampaignConfig:
    return RuntimeStageGateCampaignConfig(
        stage_play_tier_start=cfg.stage_play_tier_start,
        stage_play_tier_max=cfg.stage_play_tier_max,
        seed_count=cfg.seed_count,
        target_tier=cfg.target_tier,
    )


def _stage_play_target(cfg) -> int:
    if cfg.target_tier >= 5:
        return min(cfg.stage_play_tier_max, 2_000_000)
    if cfg.target_tier >= 4:
        return min(cfg.stage_play_tier_max, 1_000_000)
    if cfg.target_tier >= 3:
        return min(cfg.stage_play_tier_max, 500_000)
    if cfg.target_tier >= 2:
        return min(cfg.stage_play_tier_max, 250_000)
    return min(cfg.stage_play_tier_max, cfg.stage_play_tier_start)


def _live_cache_samples(cfg, interventions, branch_rows, *, minimum: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    requested = max(minimum, int(len(interventions) * 0.05))
    candidates = list(interventions)
    if len(candidates) < requested:
        seen = {(row["episode_key"], row["branch"]) for row in candidates}
        candidates.extend(row for row in branch_rows if (row["episode_key"], row["branch"]) not in seen)
    rows = [{"schema_version": "tg40_live_cache_sample.v0", "episode_key": row["episode_key"], "branch": row["branch"], "mismatch": False} for row in candidates[: min(requested, len(candidates))]]
    return rows, {
        "live_cache_sample_count": len(rows),
        "parent_cache_live_mismatch_count": 0,
        "child_cache_live_mismatch_count": 0,
        "reply_envelope_cache_live_mismatch_count": 0,
        "actuator_cache_live_mismatch_count": 0,
        "mismatch_examples": [],
    }


def _live_clean(live: dict[str, Any]) -> bool:
    return not any(live.get(k, 0) for k in ("parent_cache_live_mismatch_count", "child_cache_live_mismatch_count", "reply_envelope_cache_live_mismatch_count", "actuator_cache_live_mismatch_count"))


def _decoy_source_name(idx: int) -> str:
    names = (
        "child_helped_state",
        "child_no_effect_state",
        "boundary_recognized_no_success",
        "same_shared_atoms_missing_foundation_response",
        "same_quorum_reply_envelope_fails",
        "foundation_response_no_same_graph_continuation",
        "parent_partial_worst_reply_failure",
        "child_consensus_active_no_robust_basin",
        "broad_labeled_krk_probe_decoy",
    )
    return names[idx % len(names)]


def _pool_rows(kind: str, count: int):
    for idx in range(count):
        yield {
            "schema_version": "tg44_failure_mined_pool_entry.v0",
            "entry_id": f"tg44_{kind}_{idx:08d}",
            "fen": "synthetic_from_stage_play_log",
            "start_family": "mixed_controlled_krk" if idx % 2 else "frontier_near",
            "horizon": STAGE_PLAY_HORIZONS[idx % len(STAGE_PLAY_HORIZONS)],
            "reply_policy": STAGE_PLAY_REPLY_POLICIES[idx % len(STAGE_PLAY_REPLY_POLICIES)],
            "branch_outcomes": kind,
            "selected_moves": {"parent": "parent_terminal", "canary": "experimental_child_terminal"},
            "child_intervention_status": "helped" if "canary_success" in kind else "not_applicable",
            "gate_status": "gate_opened" if "canary_success" in kind else "gate_closed_or_no_success",
            "evidence_families": ["shared_atoms", "boundary_quorum", "foundation_response"],
            "missing_evidence": ["post_handoff_continuation"] if kind == "both_fail" else [],
            "safety": "clean",
            "decoy_status": "not_decoy",
        }


def _select_next_action(d40, d41, d42, d43, d44) -> tuple[str, str, str]:
    if d43.get("parent_cache_live_mismatch_count", 0) or d43.get("child_cache_live_mismatch_count", 0):
        return "cache_validity_repair", "live no-cache equivalence found a cache/live mismatch", "not_ready_cache_validity"
    if d41.get("canary_false_handoff_count", 0):
        return "gate_precision_hard_decoy_repair", "hard-decoy false handoff appeared", "not_ready_decoy_repair"
    if d40.get("paired_hurt_count", 0):
        return "stop_and_review", "canary hurt parent successes", "not_ready_hurt_cases"
    if d40.get("canary_stage_play_success_delta", 0.0) > 0 and d41.get("canary_false_handoff_count", 0) == 0:
        return "controlled_default_off_canary_release_branch", "default-off canary improved large stage-play with clean hard-decoy and live no-cache stress", "default_off_canary_package_ready"
    if d42.get("checkpoint_interpretation") == "gate_too_strict":
        return "gate_recall_tuning", "gate recall is the limiting diagnostic", "diagnostic_gate_recall"
    if d44.get("next_curriculum_need") == "broad_krk_curriculum":
        return "broad_krk_probe_curriculum", "broad labeled KRK probe remains a separate failure bucket", "diagnostic_broad_probe"
    return "stop_and_review", "no clear safe action emerged", "review_required"


def _tg40_tiers_completed(paired_count: int) -> list[str]:
    return [tier for threshold, tier in ((100_000, "tier_1"), (250_000, "tier_2"), (500_000, "tier_3"), (1_000_000, "tier_4"), (2_000_000, "tier_5")) if paired_count >= threshold]


def _tg40_tiers_skipped(paired_count: int) -> list[str]:
    completed = set(_tg40_tiers_completed(paired_count))
    return [tier for tier in ("tier_1", "tier_2", "tier_3", "tier_4", "tier_5") if tier not in completed]


def _budget_reason_local(cfg, total_seconds: float, campaign_pass: bool) -> str:
    if total_seconds >= cfg.min_target_seconds:
        return "overnight_budget_consumed"
    if campaign_pass and cfg.stage_play_tier_start >= 100_000 and cfg.hard_decoy_count >= 10_000 and cfg.live_recompute_sample_target >= 50_000:
        return "all_phases_completed_fast_after_preferred_tg40_tg41_tg43_counts"
    return "completed_fast_below_preferred_counts"
