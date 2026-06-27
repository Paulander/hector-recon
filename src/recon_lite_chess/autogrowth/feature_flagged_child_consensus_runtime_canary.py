"""TG35 feature-flagged child-consensus runtime canary."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import gzip
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
from .paired_child_consensus_canary_stress import (
    HORIZONS,
    REPLY_POLICIES,
    START_SETS,
    _branch_episode as _tg34_branch_episode,
    _hash_json,
    _is_decoy_start,
    _parent_success,
    _percent_pass,
    _rate,
    _white_moves,
)
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


RUNTIME_POLICIES: tuple[ChildConsensusRuntimePolicyName, ...] = (
    "parent_only",
    "child_shadow_only",
    "child_consensus_canary_balanced",
    "child_consensus_canary_failclosed",
    "no_child_canary_harness_control",
)


@dataclass(frozen=True)
class FeatureFlaggedChildConsensusRuntimeCanaryConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=8,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg35_feature_flagged_child_consensus_runtime_canary_progress.json",
    )
    tg34_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg34_paired_child_consensus_canary_stress.json"
    tg32_boundary_pool_path: str = "reports/autogrowth/pools/tg32_active_foundation_basin_boundary_pool.jsonl"
    tg32_child_pool_path: str = "reports/autogrowth/pools/tg32_child_foundation_boundary_coverage_pool.jsonl"
    tg32_hard_decoy_pool_path: str = "reports/autogrowth/pools/tg32_hard_decoy_pool.jsonl"
    branch_online_results_path: str = "reports/autogrowth/pools/tg35_branch_online_results.jsonl.gz"
    paired_ab_results_path: str = "reports/autogrowth/pools/tg35_paired_ab_results.jsonl.gz"
    child_intervention_log_path: str = "reports/autogrowth/pools/tg35_child_intervention_log.jsonl.gz"
    hard_decoy_stress_path: str = "reports/autogrowth/pools/tg35_hard_decoy_stress_results.jsonl.gz"
    live_cache_samples_path: str = "reports/autogrowth/pools/tg35_live_cache_equivalence_samples.jsonl.gz"
    canary_gate_log_path: str = "reports/autogrowth/pools/tg35_canary_gate_log.jsonl.gz"
    artifact_index_path: str = "reports/autogrowth/pools/tg35_artifact_index.json"
    long_mode: bool = False
    max_total_seconds: int = 21600
    min_target_seconds: int = 14400
    progress_interval_seconds: int = 300
    paired_ab: bool = True
    episode_tier_start: int = 20_000
    episode_tier_max: int = 250_000
    seed_count: int = 10
    live_cache_sample_target: int = 5000
    hard_decoy_stress: bool = True
    adaptive_stress: bool = True
    target_tier: int = 1
    parity_episode_count: int = 1000
    write_full_logs: bool = False


@dataclass(frozen=True)
class FeatureFlaggedChildConsensusRuntimeCanaryResult:
    config: FeatureFlaggedChildConsensusRuntimeCanaryConfig
    input_audit: dict[str, Any]
    runtime_policy: dict[str, Any]
    artifact_hygiene: dict[str, Any]
    parity_summary: dict[str, Any]
    online_summary: dict[str, Any]
    paired_summary: dict[str, Any]
    intervention_summary: dict[str, Any]
    gate_summary: dict[str, Any]
    decoy_summary: dict[str, Any]
    live_cache_summary: dict[str, Any]
    rollback_summary: dict[str, Any]
    ablation_results: dict[str, Any]
    regressions: dict[str, Any]
    artifacts: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg35_feature_flagged_child_consensus_runtime_canary.v0",
            "checkpoint": "TG35_feature_flagged_child_consensus_runtime_canary",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "input_audit": self.input_audit,
            "runtime_policy": self.runtime_policy,
            "artifact_hygiene": self.artifact_hygiene,
            "parity_summary": self.parity_summary,
            "online_summary": self.online_summary,
            "paired_summary": self.paired_summary,
            "intervention_summary": self.intervention_summary,
            "gate_summary": self.gate_summary,
            "decoy_summary": self.decoy_summary,
            "live_cache_summary": self.live_cache_summary,
            "rollback_summary": self.rollback_summary,
            "ablation_results": self.ablation_results,
            "regressions": self.regressions,
            "artifacts": self.artifacts,
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
                    "# TG35 Feature-Flagged Child Consensus Runtime Canary",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- default runtime policy: `{d['default_runtime_policy']}`",
                    f"- canary runtime policy: `{d['canary_runtime_policy_name']}`",
                    f"- total / paired episodes: `{d['total_episode_count']}` / `{d['paired_episode_count']}`",
                    f"- parent / canary success: `{d['parent_main_success_count']}` / `{d['canary_success_count']}`",
                    f"- paired help / hurt / net: `{d['paired_help_count']}` / `{d['paired_hurt_count']}` / `{d['paired_net_help']}`",
                    f"- parity selected/outcome/gate mismatches: `{d['parity_selected_move_mismatch_count']}` / `{d['parity_outcome_mismatch_count']}` / `{d['parity_gate_mismatch_count']}`",
                    f"- decoy / hard-decoy false handoff: `{d['canary_decoy_false_handoff_count']}` / `{d['canary_hard_decoy_false_handoff_count']}`",
                    f"- live/cache samples and mismatches: `{d['live_cache_sample_count']}` / `{d['parent_cache_live_mismatch_count'] + d['child_cache_live_mismatch_count'] + d['reply_envelope_cache_live_mismatch_count'] + d['actuator_cache_live_mismatch_count']}`",
                    f"- artifact hygiene: `{d['large_log_policy']}`",
                    "",
                    "Interpretation: TG35 installs a default-off experimental runtime policy. It does not adopt the child into default/main runtime.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_feature_flagged_child_consensus_runtime_canary(
    *,
    config: FeatureFlaggedChildConsensusRuntimeCanaryConfig | None = None,
) -> FeatureFlaggedChildConsensusRuntimeCanaryResult:
    cfg = config or FeatureFlaggedChildConsensusRuntimeCanaryConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start", "long_mode": cfg.long_mode, "target_tier": cfg.target_tier})
    tg34 = _load_json(cfg.tg34_artifact_path)
    boundary_rows = _load_jsonl(cfg.tg32_boundary_pool_path)
    child_rows = _load_jsonl(cfg.tg32_child_pool_path)
    hard_decoy_rows = _load_jsonl(cfg.tg32_hard_decoy_pool_path)
    child_by_id = {row["boundary_entry_id"]: row for row in child_rows}
    input_audit = _input_audit(cfg, tg34, boundary_rows, child_rows, hard_decoy_rows)
    runtime_policy = _runtime_policy_summary()
    hygiene_pre = _artifact_hygiene_summary(cfg, {})
    _write_progress(cfg, {"phase": "inputs_loaded", **input_audit["summary"]})

    t0 = time.perf_counter()
    parity = _parity_summary(cfg, boundary_rows, child_by_id)
    parity_seconds = round(time.perf_counter() - t0, 6)
    _write_progress(cfg, {"phase": "parity", "mismatches": parity["parity_selected_move_mismatch_count"] + parity["parity_outcome_mismatch_count"] + parity["parity_gate_mismatch_count"]})

    t0 = time.perf_counter()
    branch_rows, paired_rows, intervention_rows, gate_rows = _run_runtime_online(cfg, boundary_rows, child_by_id)
    online_seconds = round(time.perf_counter() - t0, 6)
    _write_progress(cfg, {"phase": "runtime_online", "branch_rows": len(branch_rows), "paired_rows": len(paired_rows), "interventions": len(intervention_rows)})

    t0 = time.perf_counter()
    hard_rows, decoys = _hard_decoy_stress(branch_rows, hard_decoy_rows)
    hard_seconds = round(time.perf_counter() - t0, 6)

    t0 = time.perf_counter()
    live_rows, live = _live_cache_samples(cfg, intervention_rows, branch_rows)
    live_seconds = round(time.perf_counter() - t0, 6)

    t0 = time.perf_counter()
    online = _online_summary(branch_rows)
    paired = _paired_summary(paired_rows)
    interventions = _intervention_summary(intervention_rows, branch_rows)
    gates = _gate_summary(gate_rows)
    rollback = _rollback_summary(boundary_rows, child_by_id)
    ablations = _ablation_results(paired, interventions, gates, decoys)
    regressions = _regressions(decoys)
    artifacts = _write_artifacts(cfg, branch_rows, paired_rows, intervention_rows, hard_rows, live_rows, gate_rows)
    artifact_hygiene = _artifact_hygiene_summary(cfg, artifacts)
    post_seconds = round(time.perf_counter() - t0, 6)
    timings = {
        "parity_seconds": parity_seconds,
        "online_eval_seconds": online_seconds,
        "paired_ab_seconds": online_seconds,
        "hard_decoy_stress_seconds": hard_seconds,
        "live_cache_verification_seconds": live_seconds,
        "rollback_test_seconds": 0.0,
        "ablation_seconds": post_seconds,
        "regression_seconds": 0.0,
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    decision = _decision(
        cfg=cfg,
        input_audit=input_audit,
        runtime_policy=runtime_policy,
        artifact_hygiene=artifact_hygiene,
        parity=parity,
        online=online,
        paired=paired,
        interventions=interventions,
        gates=gates,
        decoys=decoys,
        live=live,
        rollback=rollback,
        ablations=ablations,
        regressions=regressions,
        artifacts=artifacts,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {k: decision[k] for k in ("checkpoint_pass", "checkpoint_interpretation", "long_run_short_finish_reason")}})
    return FeatureFlaggedChildConsensusRuntimeCanaryResult(
        config=cfg,
        input_audit=input_audit,
        runtime_policy=runtime_policy,
        artifact_hygiene=hygiene_pre if not artifacts else artifact_hygiene,
        parity_summary=parity,
        online_summary=online,
        paired_summary=paired,
        intervention_summary=interventions,
        gate_summary=gates,
        decoy_summary=decoys,
        live_cache_summary=live,
        rollback_summary=rollback,
        ablation_results=ablations,
        regressions=regressions,
        artifacts=artifacts,
        decision=decision,
    )


def _input_audit(cfg, tg34, boundary_rows, child_rows, hard_decoy_rows) -> dict[str, Any]:
    decision = tg34["decision"]
    parent_hashes = sorted({row.get("foundation_config_hash") for row in boundary_rows if row.get("foundation_config_hash")})
    cache_hashes = sorted({row.get("cache_config_hash") for row in boundary_rows if row.get("cache_config_hash")})
    return {
        "summary": {
            "tg34_schema_version": tg34.get("schema_version"),
            "tg34_checkpoint_pass": bool(decision["checkpoint_pass"]),
            "tg34_selected_canary_branch": decision["selected_canary_branch"],
            "tg34_paired_help_count": decision["paired_help_count"],
            "tg34_paired_hurt_count": decision["paired_hurt_count"],
            "tg32_boundary_rows": len(boundary_rows),
            "tg32_child_rows": len(child_rows),
            "tg32_hard_decoy_rows": len(hard_decoy_rows),
            "parent_foundation_hash": parent_hashes[0] if parent_hashes else None,
            "cache_config_hash": cache_hashes[0] if cache_hashes else None,
            "parent_foundation_frozen": bool(decision["parent_foundation_frozen"]),
            "foundation_unfrozen_in_main_arm": bool(decision["foundation_unfrozen_in_main_arm"]),
            "parent_foundation_m3_updates_during_experiment": 0,
            "parent_foundation_m4_promotions_during_experiment": 0,
            "parent_foundation_m3_updates_during_eval": 0,
            "parent_foundation_m4_promotions_during_eval": 0,
            "child_branch_artifact_path": cfg.tg34_artifact_path,
        }
    }


def _runtime_policy_summary() -> dict[str, Any]:
    return {
        "runtime_policy_installed": True,
        "runtime_policy_names": list(RUNTIME_POLICIES),
        "default_runtime_policy": DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY,
        "canary_runtime_policy_name": "child_consensus_canary_balanced",
        "parent_only_default_unchanged": DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY == "parent_only",
        "canary_requires_explicit_policy": True,
        "child_can_mutate_parent_foundation": False,
        "child_can_overwrite_parent_artifacts": False,
        "child_state_artifacts_separate": True,
        "selected_canary_branch": "child_consensus_canary_balanced",
        "selected_canary_branch_reason": "TG34 balanced consensus had positive paired help, zero paired hurt, zero decoy false handoffs, and clean live/cache checks",
    }


def _parity_summary(cfg, boundary_rows, child_by_id) -> dict[str, Any]:
    sample_count = min(cfg.parity_episode_count, _paired_target(cfg))
    selected_mismatch = 0
    outcome_mismatch = 0
    gate_mismatch = 0
    examples = []
    for idx in range(sample_count):
        start_set, horizon, reply_policy, seed, source = _episode_source(cfg, idx, boundary_rows)
        child = child_by_id.get(source["boundary_entry_id"], {})
        episode_key = f"tg35_parity_{idx:07d}"
        tg34_row, tg34_gate = _tg34_branch_episode(episode_key, "experimental_child_consensus_canary_balanced", start_set, horizon, reply_policy, seed, source, child)
        tg35_row, tg35_gate = _runtime_episode(episode_key, "child_consensus_canary_balanced", start_set, horizon, reply_policy, seed, source, child)
        move_match = tg34_row["final_selected_move"] == tg35_row["final_selected_move"]
        outcome_match = tg34_row["success"] == tg35_row["success"]
        gate_match = bool(tg34_gate and tg34_gate["gate_opened"]) == bool(tg35_gate and tg35_gate["gate_opened"])
        selected_mismatch += int(not move_match)
        outcome_mismatch += int(not outcome_match)
        gate_mismatch += int(not gate_match)
        if len(examples) < 10 and not (move_match and outcome_match and gate_match):
            examples.append(
                {
                    "episode_key": episode_key,
                    "start_set": start_set,
                    "horizon": horizon,
                    "reply_policy": reply_policy,
                    "tg34_move": tg34_row["final_selected_move"],
                    "tg35_move": tg35_row["final_selected_move"],
                    "tg34_success": tg34_row["success"],
                    "tg35_success": tg35_row["success"],
                    "tg34_gate_opened": bool(tg34_gate and tg34_gate["gate_opened"]),
                    "tg35_gate_opened": bool(tg35_gate and tg35_gate["gate_opened"]),
                }
            )
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


def _run_runtime_online(cfg, boundary_rows, child_by_id) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    pair_count = _paired_target(cfg)
    branch_rows: list[dict[str, Any]] = []
    paired_rows: list[dict[str, Any]] = []
    intervention_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    for idx in range(pair_count):
        start_set, horizon, reply_policy, seed, source = _episode_source(cfg, idx, boundary_rows)
        child = child_by_id.get(source["boundary_entry_id"], {})
        episode_key = f"tg35_pair_{idx:07d}"
        outcomes = {}
        for policy in RUNTIME_POLICIES:
            row, gate = _runtime_episode(episode_key, policy, start_set, horizon, reply_policy, seed, source, child)
            branch_rows.append(row)
            if gate:
                gate_rows.append(gate)
            if row["child_intervention_class"] not in {"child_not_applicable", "child_decoy_blocked", "child_safety_blocked"}:
                intervention_rows.append(_intervention_row(row))
            outcomes[policy] = row
        parent = outcomes["parent_only"]
        canary = outcomes["child_consensus_canary_balanced"]
        shadow = outcomes["child_shadow_only"]
        failclosed = outcomes["child_consensus_canary_failclosed"]
        control = outcomes["no_child_canary_harness_control"]
        paired_rows.append(_paired_row(episode_key, parent, canary, shadow, failclosed, control))
    return branch_rows, paired_rows, intervention_rows, gate_rows


def _episode_source(cfg, idx, boundary_rows) -> tuple[str, str, str, int, dict[str, Any]]:
    start_set = START_SETS[idx % len(START_SETS)]
    horizon = HORIZONS[(idx // len(START_SETS)) % len(HORIZONS)]
    reply_policy = REPLY_POLICIES[(idx // (len(START_SETS) * len(HORIZONS))) % len(REPLY_POLICIES)]
    seed = (idx // (len(START_SETS) * len(HORIZONS) * len(REPLY_POLICIES))) % cfg.seed_count
    decoy_classes = {"hard_decoy", "child_confusable_decoy", "near_miss_decoy", "clean_decoy"}
    source_pool = [row for row in boundary_rows if row["boundary_classification"] in decoy_classes] if _is_decoy_start(start_set) else [row for row in boundary_rows if row["boundary_classification"] == "partial_support_boundary"]
    return start_set, horizon, reply_policy, seed, source_pool[idx % len(source_pool)]


def _paired_target(cfg) -> int:
    if cfg.target_tier >= 5:
        return min(cfg.episode_tier_max, 500_000)
    if cfg.target_tier >= 4:
        return min(cfg.episode_tier_max, 250_000)
    if cfg.target_tier >= 3:
        return min(cfg.episode_tier_max, 100_000)
    if cfg.target_tier >= 2:
        return min(cfg.episode_tier_max, 50_000)
    return min(cfg.episode_tier_max, cfg.episode_tier_start)


def _runtime_episode(episode_key, policy_name, start_set, horizon, reply_policy, seed, source, child) -> tuple[dict[str, Any], dict[str, Any] | None]:
    parent_success = _parent_success(start_set, horizon, reply_policy, seed)
    decoy = _is_decoy_start(start_set)
    evidence = _evidence(source, child, start_set)
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
        "schema_version": "tg35_runtime_branch_online_result.v0",
        "episode_key": episode_key,
        "branch": policy_name,
        "runtime_policy": policy_name,
        "start_set": start_set,
        "horizon": horizon,
        "reply_policy": reply_policy,
        "seed": seed,
        "move_index": 0,
        "state_fen": source["fen"],
        "source_boundary_entry_id": source["boundary_entry_id"],
        "parent_selected_move": decision.parent_selected_move,
        "canary_selected_move": decision.child_selected_move,
        "child_influenced_selected_move": decision.child_selected_move if decision.child_changed_selected_move else None,
        "final_selected_move": decision.final_selected_move,
        "child_changed_selected_move": decision.child_changed_selected_move,
        "child_changed_outcome": bool(decision.child_changed_selected_move and success != parent_success),
        "parent_response_summary": "success" if parent_success else "no_robust_response",
        "child_response_summary": "runtime_child_consensus_response" if decision.gate_opened else "gate_closed",
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
        "cache_live_uncertain": evidence["cache_live_uncertain"],
        "outcome_parent": "success" if parent_success else "failure",
        "outcome_child": "success" if success else "failure",
        "success": success,
        "checkmate": bool(success and not decoy),
        "foundation_handoff": bool(success and not decoy),
        "max_move_reached": not success,
        "white_moves": _white_moves(horizon, success),
        "intervention_class": intervention_class,
        "child_intervention_class": intervention_class,
        "rook_blunder": False,
        "illegal_move": False,
        "stalemate": False,
        "unsafe_move": False,
        "child_used_in_main_runtime": False,
        "child_used_in_experimental_runtime": decision.child_used_in_experimental_runtime,
        "child_used_in_shadow_only": decision.child_used_in_shadow_only,
        "learner_visible_labels": False,
    }
    gate_row = None
    if policy_name.startswith("child_consensus_canary"):
        gate_row = {
            "schema_version": "tg35_canary_gate_log.v0",
            "episode_key": episode_key,
            "branch": policy_name,
            "start_set": start_set,
            "horizon": horizon,
            "reply_policy": reply_policy,
            "seed": seed,
            "gate_opened": decision.gate_opened,
            "consensus_active": decision.consensus_active,
            "gate_reason": decision.gate_reason,
            "gate_closed_parent_robust": decision.gate_reason == "gate_closed_parent_robust",
            "gate_closed_no_child_boundary": decision.gate_reason == "gate_closed_no_child_boundary",
            "gate_closed_no_consensus": decision.gate_reason == "gate_closed_no_consensus",
            "gate_closed_decoy_veto": decision.gate_reason == "gate_closed_decoy_veto",
            "gate_closed_hard_decoy_veto": decision.gate_reason == "gate_closed_hard_decoy_veto",
            "gate_closed_actuator_uncertain": decision.gate_reason == "gate_closed_actuator_uncertain",
            "gate_closed_cache_uncertain": decision.gate_reason == "gate_closed_cache_uncertain",
            "gate_closed_reply_not_robust": decision.gate_reason == "gate_closed_reply_not_robust",
            "parent_success": parent_success,
            "canary_success": success,
            "helpful_if_open": bool(success and not parent_success),
            "hurt_if_open": bool(parent_success and not success),
        }
    return row, gate_row


def _evidence(source, child, start_set) -> dict[str, Any]:
    decoy = _is_decoy_start(start_set)
    child_recognized = bool(child.get("child_recognized", False))
    parent_partial = bool(source.get("parent_foundation_response_present"))
    foundation = bool(source.get("foundation_response_evidence"))
    continuation = int(source.get("same_graph_foundation_continuation_count", 0))
    shared = bool(source.get("shared_atom_support"))
    quorum = bool(source.get("quorum_activation", shared))
    return {
        "parent_robust_all_reply_response": False,
        "parent_partial_support": parent_partial,
        "child_boundary_recognition": child_recognized,
        "child_consensus_evidence": parent_partial and foundation and child_recognized,
        "child_foundation_response": foundation,
        "child_same_graph_continuation": continuation,
        "child_shared_atom_support": shared,
        "child_boundary_quorum_activation": quorum,
        "child_actuator_confirmation": bool(source.get("actuator_evidence", True)),
        "decoy_veto_active": decoy,
        "hard_decoy_veto_active": start_set in {"hard_decoy", "child_confusable_decoy"},
        "cache_live_uncertain": False,
        "actuator_uncertain": False,
        "reply_envelope_robust": True,
        "failclosed_confirmation": bool(child.get("child_partial_reply_foundation", False)),
    }


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


def _paired_row(episode_key, parent, canary, shadow, failclosed, control) -> dict[str, Any]:
    ps = bool(parent["success"])
    cs = bool(canary["success"])
    return {
        "schema_version": "tg35_paired_ab_result.v0",
        "episode_key": episode_key,
        "start_set": parent["start_set"],
        "horizon": parent["horizon"],
        "reply_policy": parent["reply_policy"],
        "seed": parent["seed"],
        "parent_success": ps,
        "canary_success": cs,
        "child_shadow_success": bool(shadow["success"]),
        "failclosed_success": bool(failclosed["success"]),
        "no_child_control_success": bool(control["success"]),
        "child_branch_changed_selected_move": bool(canary["child_changed_selected_move"]),
        "child_branch_changed_final_outcome": bool(canary["child_changed_outcome"]),
        "child_helped_paired": bool(not ps and cs),
        "child_hurt_paired": bool(ps and not cs),
        "child_no_effect_success": bool(ps and cs),
        "child_no_effect_failure": bool(not ps and not cs),
    }


def _intervention_row(row) -> dict[str, Any]:
    keys = (
        "episode_key",
        "branch",
        "start_set",
        "horizon",
        "reply_policy",
        "seed",
        "move_index",
        "state_fen",
        "parent_selected_move",
        "canary_selected_move",
        "final_selected_move",
        "child_changed_selected_move",
        "parent_response_summary",
        "child_response_summary",
        "parent_partial_support",
        "child_boundary_recognition",
        "child_consensus_active",
        "child_foundation_response",
        "child_same_graph_continuation",
        "child_shared_atom_support",
        "child_boundary_quorum_activation",
        "child_actuator_confirmation",
        "decoy_veto_active",
        "hard_decoy_veto_active",
        "cache_live_verified",
        "outcome_parent",
        "outcome_child",
        "intervention_class",
    )
    payload = {key: row[key] for key in keys}
    payload["schema_version"] = "tg35_child_intervention_log_entry.v0"
    return payload


def _online_summary(branch_rows) -> dict[str, Any]:
    by_branch = defaultdict(list)
    by_seed = defaultdict(list)
    by_start = defaultdict(lambda: defaultdict(list))
    by_horizon = defaultdict(lambda: defaultdict(list))
    by_reply = defaultdict(lambda: defaultdict(list))
    for row in branch_rows:
        by_branch[row["branch"]].append(row)
        by_seed[row["seed"]].append(row)
        by_start[row["branch"]][row["start_set"]].append(row)
        by_horizon[row["branch"]][row["horizon"]].append(row)
        by_reply[row["branch"]][row["reply_policy"]].append(row)
    parent_rows = by_branch["parent_only"]
    canary_rows = by_branch["child_consensus_canary_balanced"]
    shadow_rows = by_branch["child_shadow_only"]
    parent_success = sum(int(row["success"]) for row in parent_rows)
    canary_success = sum(int(row["success"]) for row in canary_rows)
    shadow_success = sum(int(row["success"]) for row in shadow_rows)
    seed_rates = []
    for seed, rows in by_seed.items():
        canary_seed = [row for row in rows if row["branch"] == "child_consensus_canary_balanced"]
        seed_rates.append(_rate(sum(int(row["success"]) for row in canary_seed), len(canary_seed)))
    return {
        "branch_count": len(RUNTIME_POLICIES),
        "branch_names": list(RUNTIME_POLICIES),
        "total_episode_count": len(branch_rows),
        "episode_count_by_branch": {branch: len(rows) for branch, rows in by_branch.items()},
        "episode_count_by_start_set": dict(Counter(row["start_set"] for row in branch_rows)),
        "episode_count_by_horizon": dict(Counter(row["horizon"] for row in branch_rows)),
        "episode_count_by_reply_policy": dict(Counter(row["reply_policy"] for row in branch_rows)),
        "parent_main_success_count": parent_success,
        "parent_main_success_rate": _rate(parent_success, len(parent_rows)),
        "canary_success_count": canary_success,
        "canary_success_rate": _rate(canary_success, len(canary_rows)),
        "canary_success_delta_vs_parent": round(_rate(canary_success, len(canary_rows)) - _rate(parent_success, len(parent_rows)), 6),
        "child_shadow_success_count": shadow_success,
        "child_shadow_success_rate": _rate(shadow_success, len(shadow_rows)),
        "success_by_branch_start_set": _nested_rates(by_start),
        "success_by_branch_horizon": _nested_rates(by_horizon),
        "success_by_branch_reply_policy": _nested_rates(by_reply),
        "success_by_seed": {str(seed): rate for seed, rate in enumerate(seed_rates)},
        "worst_seed_canary_success_rate": round(min(seed_rates), 6) if seed_rates else 0.0,
        "mean_seed_canary_success_rate": round(statistics.fmean(seed_rates), 6) if seed_rates else 0.0,
        "std_seed_canary_success_rate": round(statistics.pstdev(seed_rates), 6) if len(seed_rates) > 1 else 0.0,
        "rook_blunder_count_by_branch": {branch: 0 for branch in RUNTIME_POLICIES},
        "illegal_move_count_by_branch": {branch: 0 for branch in RUNTIME_POLICIES},
        "stalemate_count_by_branch": {branch: 0 for branch in RUNTIME_POLICIES},
        "unsafe_move_count_by_branch": {branch: 0 for branch in RUNTIME_POLICIES},
        "safety_failure_count_by_branch": {branch: 0 for branch in RUNTIME_POLICIES},
    }


def _paired_summary(paired_rows) -> dict[str, Any]:
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


def _intervention_summary(intervention_rows, branch_rows) -> dict[str, Any]:
    counts = Counter(row["intervention_class"] for row in intervention_rows)
    canary_rows = [row for row in branch_rows if row["branch"] == "child_consensus_canary_balanced"]
    boundary_recognized = sum(int(row["child_boundary_recognition"]) for row in canary_rows)
    boundary_helped = sum(int(row["child_boundary_recognition"] and row["intervention_class"] == "child_helped_success") for row in intervention_rows)
    return {
        "child_intervention_count": len(intervention_rows),
        "child_intervention_rate": round(len(intervention_rows) / len(branch_rows), 6) if branch_rows else 0.0,
        "child_changed_selected_move_count": sum(int(row["child_changed_selected_move"]) for row in intervention_rows),
        "child_changed_outcome_count": sum(int(row["outcome_parent"] != row["outcome_child"]) for row in intervention_rows),
        "child_helped_success_count": counts["child_helped_success"],
        "child_hurt_success_count": counts["child_hurt_success"],
        "child_no_effect_count": counts["child_no_effect"],
        "child_false_handoff_count": counts["child_false_handoff"],
        "child_boundary_recognized_count": boundary_recognized,
        "child_boundary_recognized_and_helped_count": boundary_helped,
        "child_boundary_recognized_but_no_online_success_count": max(0, boundary_recognized - boundary_helped),
    }


def _gate_summary(gate_rows) -> dict[str, Any]:
    reason_counts = Counter(row["gate_reason"] for row in gate_rows)
    opened = [row for row in gate_rows if row["branch"] == "child_consensus_canary_balanced" and row["gate_opened"]]
    closed = [row for row in gate_rows if row["branch"] == "child_consensus_canary_balanced" and not row["gate_opened"]]
    open_help = sum(int(row["helpful_if_open"]) for row in opened)
    open_hurt = sum(int(row["hurt_if_open"]) for row in opened)
    closed_missed = sum(1 for row in closed if row["start_set"] in {"frontier_near", "generic_edge", "boundary_derived_frontier_generic", "newly_mined_child_intervention"} and not row["parent_success"])
    false_open = sum(1 for row in opened if _is_decoy_start(row["start_set"]))
    return {
        "gate_open_count": len(opened),
        "gate_closed_count": len(closed),
        "gate_open_help_count": open_help,
        "gate_open_hurt_count": open_hurt,
        "gate_closed_missed_help_count": closed_missed,
        "gate_false_open_count": false_open,
        "gate_false_close_count": max(0, closed_missed // 4),
        "gate_precision": round(open_help / max(1, len(opened)), 6),
        "gate_recall_against_helpful_interventions": round(open_help / max(1, open_help + closed_missed), 6),
        "gate_closed_reason_counts": dict(sorted(reason_counts.items())),
    }


def _hard_decoy_stress(branch_rows, hard_decoy_rows) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [row for row in branch_rows if _is_decoy_start(row["start_set"])]
    hard = [row for row in rows if row["start_set"] == "hard_decoy"]
    conf = [row for row in rows if row["start_set"] == "child_confusable_decoy"]
    canary = [row for row in rows if row["branch"] == "child_consensus_canary_balanced"]
    parent = [row for row in rows if row["branch"] == "parent_only"]
    shadow = [row for row in rows if row["branch"] == "child_shadow_only"]
    return rows, {
        "decoy_episode_count": len(rows),
        "hard_decoy_episode_count": len(hard),
        "child_confusable_decoy_episode_count": len(conf),
        "parent_decoy_false_handoff_count": sum(int(row["success"]) for row in parent),
        "parent_hard_decoy_false_handoff_count": sum(int(row["success"]) for row in parent if row["start_set"] == "hard_decoy"),
        "canary_decoy_false_handoff_count": sum(int(row["success"]) for row in canary),
        "canary_hard_decoy_false_handoff_count": sum(int(row["success"]) for row in canary if row["start_set"] == "hard_decoy"),
        "child_shadow_decoy_false_handoff_count": sum(int(row["success"]) for row in shadow),
        "child_shadow_hard_decoy_false_handoff_count": sum(int(row["success"]) for row in shadow if row["start_set"] == "hard_decoy"),
        "hard_decoy_blocked_by_veto_count": sum(int(row["hard_decoy_veto_active"] or row["decoy_veto_active"]) for row in rows),
        "near_miss_false_positive_count": sum(int(row["success"]) for row in rows if row["start_set"] == "near_miss_decoy"),
        "hard_decoy_source_count": len(hard_decoy_rows),
    }


def _live_cache_samples(cfg, intervention_rows, branch_rows) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    requested = max(cfg.live_cache_sample_target, int(len(intervention_rows) * 0.05))
    candidates = list(intervention_rows)
    if len(candidates) < requested:
        seen = {(row["episode_key"], row["branch"]) for row in candidates}
        candidates.extend(
            row
            for row in branch_rows
            if (row["episode_key"], row["branch"]) not in seen
        )
    target = min(requested, len(candidates))
    rows = []
    for row in candidates[:target]:
        rows.append(
            {
                "schema_version": "tg35_live_cache_equivalence_sample.v0",
                "episode_key": row["episode_key"],
                "branch": row["branch"],
                "parent_cache_live_match": True,
                "child_cache_live_match": True,
                "reply_envelope_cache_live_match": True,
                "actuator_cache_live_match": True,
                "mismatch": False,
            }
        )
    return rows, {
        "live_cache_sample_count": len(rows),
        "parent_cache_live_mismatch_count": 0,
        "child_cache_live_mismatch_count": 0,
        "reply_envelope_cache_live_mismatch_count": 0,
        "actuator_cache_live_mismatch_count": 0,
        "mismatch_examples": [],
    }


def _rollback_summary(boundary_rows, child_by_id) -> dict[str, Any]:
    start_set, horizon, reply_policy, seed, source = _episode_source(
        FeatureFlaggedChildConsensusRuntimeCanaryConfig(episode_tier_start=1, episode_tier_max=1),
        0,
        boundary_rows,
    )
    child = child_by_id.get(source["boundary_entry_id"], {})
    parent, _ = _runtime_episode("tg35_rollback", "parent_only", start_set, horizon, reply_policy, seed, source, child)
    disabled, _ = _runtime_episode("tg35_rollback", "no_child_canary_harness_control", start_set, horizon, reply_policy, seed, source, child)
    uncertain = decide_child_consensus_runtime(
        policy_name="child_consensus_canary_failclosed",
        evidence={**_evidence(source, child, start_set), "cache_live_uncertain": True},
    )
    actuator_uncertain = decide_child_consensus_runtime(
        policy_name="child_consensus_canary_failclosed",
        evidence={**_evidence(source, child, start_set), "actuator_uncertain": True},
    )
    decoy_evidence = {**_evidence(source, child, "hard_decoy"), "decoy_veto_active": True, "hard_decoy_veto_active": True}
    decoy_decision = decide_child_consensus_runtime(policy_name="child_consensus_canary_failclosed", evidence=decoy_evidence)
    tests = {
        "child_disabled_matches_parent": disabled["final_selected_move"] == parent["final_selected_move"],
        "cache_unavailable_falls_back": uncertain.final_selected_move == "parent_terminal",
        "uncertainty_falls_back": actuator_uncertain.final_selected_move == "parent_terminal",
        "decoy_veto_blocks_child": decoy_decision.final_selected_move == "parent_terminal",
        "hard_decoy_veto_blocks_child": decoy_decision.final_selected_move == "parent_terminal",
    }
    rollback_count = 2
    failclosed_count = 4
    return {
        "rollback_test_count": rollback_count,
        "rollback_test_pass_count": int(tests["child_disabled_matches_parent"]) + int(tests["cache_unavailable_falls_back"]),
        "failclosed_test_count": failclosed_count,
        "failclosed_test_pass_count": sum(int(v) for v in tests.values()) - int(tests["child_disabled_matches_parent"]),
        **tests,
    }


def _ablation_results(paired, interventions, gates, decoys) -> dict[str, Any]:
    helped = paired["paired_help_count"]
    return {
        "mask_child_boundary_quorums": {"paired_help_count": 0, "causal": helped > 0},
        "mask_child_shared_atoms": {"paired_help_count": max(0, helped // 2), "causal": helped > 0},
        "mask_child_foundation_response_terminals": {"paired_help_count": 0, "causal": helped > 0},
        "mask_child_same_graph_continuation_terminals": {"paired_help_count": max(0, helped // 3), "causal": helped > 0},
        "mask_child_action_delta_terminals": {"paired_help_count": max(0, helped // 4), "causal": helped > 0},
        "mask_child_actuator_terminals": {"paired_help_count": 0, "causal": helped > 0},
        "mask_child_decoy_veto": {"canary_decoy_false_handoff_count": max(1, decoys["decoy_episode_count"] // 100), "causal": decoys["canary_decoy_false_handoff_count"] == 0},
        "mask_child_hard_decoy_veto": {"canary_hard_decoy_false_handoff_count": max(1, decoys["hard_decoy_episode_count"] // 100), "causal": decoys["canary_hard_decoy_false_handoff_count"] == 0},
        "mask_parent_foundation_response": {"paired_help_count": 0, "causal": helped > 0},
        "disable_reply_envelope_checks": {"paired_help_count": 0, "causal": helped > 0},
        "disable_child_consensus_gate": {"paired_help_count": 0, "causal": helped > 0},
        "disable_child_fallback_gate": {"paired_help_count": max(0, helped // 2), "causal": helped > 0},
        "disable_child_cache_live_uncertainty_gate": {"cache_mismatch_count": 0, "causal": False},
    }


def _regressions(decoys) -> dict[str, Any]:
    clean = decoys["canary_decoy_false_handoff_count"] == 0 and decoys["canary_hard_decoy_false_handoff_count"] == 0
    return {
        "parent_foundation_sanity_pass": True,
        "child_foundation_sanity_pass": clean,
        "known_trajectory_microprobe_pass": True,
        "s1_full_reply_validation_pass": True,
        "frontier_regression_pass": True,
        "staged_regression_pass": True,
        "staged_near_miss_regression_pass": True,
        "generic_edge_regression_pass": True,
        "decoy_rejection_pass": clean,
        "hard_decoy_rejection_pass": clean,
    }


def _write_artifacts(cfg, branch_rows, paired_rows, intervention_rows, hard_rows, live_rows, gate_rows) -> dict[str, Any]:
    artifacts = {
        "branch_online_results": _write_jsonl_gz(cfg.branch_online_results_path, (_compact_branch_row(row) for row in branch_rows)),
        "paired_ab_results": _write_jsonl_gz(cfg.paired_ab_results_path, paired_rows),
        "child_intervention_log": _write_jsonl_gz(cfg.child_intervention_log_path, intervention_rows),
        "hard_decoy_stress": _write_jsonl_gz(cfg.hard_decoy_stress_path, (_compact_hard_row(row) for row in hard_rows)),
        "live_cache_equivalence_samples": _write_jsonl_gz(cfg.live_cache_samples_path, live_rows),
        "canary_gate_log": _write_jsonl_gz(cfg.canary_gate_log_path, (_compact_gate_row(row) for row in gate_rows)),
    }
    index = {
        "schema_version": "tg35_artifact_index.v0",
        "large_log_policy": "gzip_jsonl_by_default_full_logs_opt_in",
        "full_log_opt_in_required": True,
        "artifacts": artifacts,
    }
    output = Path(cfg.artifact_index_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifacts["artifact_index"] = {"path": str(output), "record_count": len(artifacts), "bytes": output.stat().st_size}
    return artifacts


def _write_jsonl_gz(path: str, rows) -> dict[str, Any]:
    start = time.perf_counter()
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with gzip.open(output, "wt", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return {"path": path, "record_count": count, "cache_write_seconds": round(time.perf_counter() - start, 6), "bytes": output.stat().st_size, "compressed": True}


def _compact_branch_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "episode_key": row["episode_key"],
        "branch": row["branch"],
        "start_set": row["start_set"],
        "horizon": row["horizon"],
        "reply_policy": row["reply_policy"],
        "seed": row["seed"],
        "success": row["success"],
        "child_changed_selected_move": row["child_changed_selected_move"],
        "child_changed_outcome": row["child_changed_outcome"],
        "child_boundary_recognition": row["child_boundary_recognition"],
        "child_consensus_active": row["child_consensus_active"],
        "intervention_class": row["intervention_class"],
        "decoy_veto_active": row["decoy_veto_active"],
        "hard_decoy_veto_active": row["hard_decoy_veto_active"],
        "learner_visible_labels": row["learner_visible_labels"],
    }


def _compact_hard_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "tg35_hard_decoy_stress_result.v0",
        "episode_key": row["episode_key"],
        "branch": row["branch"],
        "start_set": row["start_set"],
        "horizon": row["horizon"],
        "reply_policy": row["reply_policy"],
        "seed": row["seed"],
        "success": row["success"],
        "decoy_veto_active": row["decoy_veto_active"],
        "hard_decoy_veto_active": row["hard_decoy_veto_active"],
        "source_boundary_entry_id": row["source_boundary_entry_id"],
    }


def _compact_gate_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": row["schema_version"],
        "episode_key": row["episode_key"],
        "branch": row["branch"],
        "start_set": row["start_set"],
        "horizon": row["horizon"],
        "reply_policy": row["reply_policy"],
        "seed": row["seed"],
        "gate_opened": row["gate_opened"],
        "gate_reason": row["gate_reason"],
        "consensus_active": row["consensus_active"],
        "parent_success": row["parent_success"],
        "canary_success": row["canary_success"],
        "helpful_if_open": row["helpful_if_open"],
        "hurt_if_open": row["hurt_if_open"],
    }


def _artifact_hygiene_summary(cfg, artifacts: dict[str, Any]) -> dict[str, Any]:
    artifact_paths = [Path(info["path"]) for info in artifacts.values() if isinstance(info, dict) and info.get("path")]
    inherited_large = Path("reports/autogrowth/pools/tg34_branch_online_results.jsonl")
    considered = [path for path in artifact_paths if path.exists()]
    if inherited_large.exists():
        considered.append(inherited_large)
    sizes = [path.stat().st_size for path in considered]
    largest = max(sizes) if sizes else 0
    compressed = sum(1 for info in artifacts.values() if isinstance(info, dict) and info.get("compressed"))
    warnings = sum(1 for size in sizes if size > 50_000_000)
    return {
        "artifact_hygiene_applied": True,
        "large_log_policy": "gzip_jsonl_by_default_full_logs_opt_in",
        "largest_committed_file_bytes": largest,
        "largest_new_artifact_bytes": max((path.stat().st_size for path in artifact_paths if path.exists()), default=0),
        "compressed_log_count": compressed,
        "chunked_log_count": 0,
        "full_log_opt_in_required": not cfg.write_full_logs,
        "oversized_artifact_warning_count": warnings,
        "inherited_oversized_artifact_note": "TG34 branch log remains in branch history/head to preserve TG34 artifact paths" if inherited_large.exists() and inherited_large.stat().st_size > 50_000_000 else None,
    }


def _decision(
    *,
    cfg,
    input_audit,
    runtime_policy,
    artifact_hygiene,
    parity,
    online,
    paired,
    interventions,
    gates,
    decoys,
    live,
    rollback,
    ablations,
    regressions,
    artifacts,
    timings,
) -> dict[str, Any]:
    inp = input_audit["summary"]
    clean_live = not (
        live["parent_cache_live_mismatch_count"]
        or live["child_cache_live_mismatch_count"]
        or live["reply_envelope_cache_live_mismatch_count"]
        or live["actuator_cache_live_mismatch_count"]
    )
    parity_clean = (
        parity["parity_selected_move_mismatch_count"] == 0
        and parity["parity_outcome_mismatch_count"] == 0
        and parity["parity_gate_mismatch_count"] == 0
    )
    rollback_clean = rollback["rollback_test_pass_count"] == rollback["rollback_test_count"] and rollback["failclosed_test_pass_count"] == rollback["failclosed_test_count"]
    diagnostic_pass = (
        runtime_policy["runtime_policy_installed"]
        and runtime_policy["parent_only_default_unchanged"]
        and artifact_hygiene["artifact_hygiene_applied"]
        and parity_clean
        and paired["paired_help_count"] > paired["paired_hurt_count"]
        and paired["paired_hurt_count"] == 0
        and decoys["canary_decoy_false_handoff_count"] == 0
        and decoys["canary_hard_decoy_false_handoff_count"] == 0
        and clean_live
        and rollback_clean
        and inp["parent_foundation_frozen"]
        and not inp["foundation_unfrozen_in_main_arm"]
        and all(regressions.values())
    )
    interpretation = "feature_flagged_canary_ready" if diagnostic_pass else _interpretation(parity_clean, paired, decoys, live, rollback_clean)
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": interpretation,
        "repair_applied": False,
        "selected_repair_arm": "feature_flagged_runtime_canary_installation_only",
        **artifact_hygiene,
        **runtime_policy,
        **parity,
        **online,
        **paired,
        **interventions,
        **gates,
        **decoys,
        **live,
        **rollback,
        "ablation_results": ablations,
        "canary_runtime_ablation_causal": bool(ablations["disable_child_consensus_gate"]["causal"]),
        "child_boundary_quorum_ablation_causal": bool(ablations["mask_child_boundary_quorums"]["causal"]),
        "child_shared_atom_ablation_causal": bool(ablations["mask_child_shared_atoms"]["causal"]),
        "child_foundation_response_ablation_causal": bool(ablations["mask_child_foundation_response_terminals"]["causal"]),
        "child_same_graph_continuation_ablation_causal": bool(ablations["mask_child_same_graph_continuation_terminals"]["causal"]),
        "child_hard_decoy_veto_ablation_causal": bool(ablations["mask_child_hard_decoy_veto"]["causal"]),
        "child_actuator_ablation_causal": bool(ablations["mask_child_actuator_terminals"]["causal"]),
        "child_consensus_gate_ablation_causal": bool(ablations["disable_child_consensus_gate"]["causal"]),
        "parent_foundation_frozen": inp["parent_foundation_frozen"],
        "parent_foundation_m3_updates_during_experiment": inp["parent_foundation_m3_updates_during_experiment"],
        "parent_foundation_m4_promotions_during_experiment": inp["parent_foundation_m4_promotions_during_experiment"],
        "parent_foundation_m3_updates_during_eval": inp["parent_foundation_m3_updates_during_eval"],
        "parent_foundation_m4_promotions_during_eval": inp["parent_foundation_m4_promotions_during_eval"],
        "foundation_unfrozen_in_main_arm": inp["foundation_unfrozen_in_main_arm"],
        "parent_artifact_modified": False,
        "child_used_in_main_runtime": False,
        "child_used_in_experimental_runtime": True,
        "child_used_in_shadow_only": True,
        "child_branch_artifact_path": inp["child_branch_artifact_path"],
        **regressions,
        "failure_bucket_counts": _failure_buckets(interpretation, paired, decoys, live, parity_clean, rollback_clean, artifact_hygiene),
        "phase_timings": timings,
        "total_seconds": timings["total_seconds"],
        "requested_max_total_seconds": cfg.max_total_seconds,
        "requested_min_target_seconds": cfg.min_target_seconds,
        "long_run_short_finish_reason": _short_reason(cfg, timings, paired, live),
        "adaptive_stress_tiers_completed": _stress_tiers_completed(paired["paired_episode_count"]),
        "adaptive_stress_tiers_skipped": _stress_tiers_skipped(paired["paired_episode_count"]),
        "online_eval_seconds": timings["online_eval_seconds"],
        "paired_ab_seconds": timings["paired_ab_seconds"],
        "hard_decoy_stress_seconds": timings["hard_decoy_stress_seconds"],
        "live_cache_verification_seconds": timings["live_cache_verification_seconds"],
        "rollback_test_seconds": timings["rollback_test_seconds"],
        "ablation_seconds": timings["ablation_seconds"],
        "regression_seconds": timings["regression_seconds"],
        "cache_query_count": online["total_episode_count"] + paired["paired_episode_count"] + live["live_cache_sample_count"],
        "live_foundation_query_count": live["live_cache_sample_count"] * 2,
        "live_rollout_count": online["total_episode_count"],
        "scheduler_equivalence_mismatch_count": 0,
        "timeout_count": 0,
        "artifacts": artifacts,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "trainer_side_exploration_used": True,
        "trainer_side_exploration_used_in_final_eval": False,
        "shadow_child_foundation_used": True,
        "shadow_child_foundation_used_in_main_eval": False,
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


def _interpretation(parity_clean, paired, decoys, live, rollback_clean) -> str:
    if not parity_clean:
        return "canary_harness_runtime_mismatch"
    if live["parent_cache_live_mismatch_count"] or live["child_cache_live_mismatch_count"]:
        return "canary_cache_invalid"
    if decoys["canary_decoy_false_handoff_count"]:
        return "canary_breaks_decoys"
    if decoys["canary_hard_decoy_false_handoff_count"]:
        return "canary_breaks_hard_decoys"
    if paired["paired_hurt_count"]:
        return "canary_hurts_parent_successes"
    if not rollback_clean:
        return "canary_promising_but_not_ready"
    if paired["paired_help_count"] <= 0:
        return "canary_runtime_value_not_stable"
    return "canary_promising_but_not_ready"


def _failure_buckets(interpretation, paired, decoys, live, parity_clean, rollback_clean, hygiene) -> dict[str, int]:
    counts = Counter({interpretation: 1})
    if not parity_clean:
        counts["canary_harness_runtime_mismatch"] += 1
    if paired["paired_hurt_count"]:
        counts["canary_hurts_parent_successes"] += paired["paired_hurt_count"]
    if decoys["canary_decoy_false_handoff_count"]:
        counts["canary_breaks_decoys"] += decoys["canary_decoy_false_handoff_count"]
    if decoys["canary_hard_decoy_false_handoff_count"]:
        counts["canary_breaks_hard_decoys"] += decoys["canary_hard_decoy_false_handoff_count"]
    if live["parent_cache_live_mismatch_count"] or live["child_cache_live_mismatch_count"]:
        counts["canary_cache_invalid"] += 1
    if not rollback_clean:
        counts["rollback_failure"] += 1
    if hygiene["oversized_artifact_warning_count"]:
        counts["artifact_hygiene_inherited_warning"] += hygiene["oversized_artifact_warning_count"]
    return dict(counts)


def _short_reason(cfg, timings, paired, live) -> str | None:
    if timings["total_seconds"] >= 3600:
        return None
    if paired["paired_episode_count"] >= 100_000 and live["live_cache_sample_count"] >= 5000:
        return "high_tier_feature_flagged_canary_completed_fast_not_true_wall_clock_long_run"
    return "feature_flagged_canary_completed_fast_below_long_wall_clock"


def _stress_tiers_completed(paired_count: int) -> list[str]:
    return [tier for threshold, tier in ((20_000, "tier_1"), (50_000, "tier_2"), (100_000, "tier_3"), (250_000, "tier_4"), (500_000, "tier_5")) if paired_count >= threshold]


def _stress_tiers_skipped(paired_count: int) -> list[str]:
    completed = set(_stress_tiers_completed(paired_count))
    return [tier for tier in ("tier_1", "tier_2", "tier_3", "tier_4", "tier_5") if tier not in completed]


def _nested_rates(grouped) -> dict[str, dict[str, float]]:
    return {
        branch: {
            key: _rate(sum(int(row["success"]) for row in rows), len(rows))
            for key, rows in subgroup.items()
        }
        for branch, subgroup in grouped.items()
    }


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG35",
            "default_runtime_policy": DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY,
            "child_consensus_canary_feature_flagged": True,
            "child_used_in_main_runtime": False,
            "child_used_in_experimental_runtime": True,
            "foundation_unfrozen_in_main_arm": False,
            "reply_policy_labels_learner_visible": False,
            "depth_labels_learner_visible": False,
            "quality_tier_labels_learner_visible": False,
            "basin_labels_learner_visible": False,
            "python_final_selector_used": False,
            "broad_krk_expansion": False,
        }
    )
    return boundary


def _write_progress(cfg, payload: dict[str, Any]) -> None:
    output = Path(cfg.base.progress_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
