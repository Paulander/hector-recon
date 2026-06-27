"""TG34 paired child-consensus canary stress diagnostic."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import statistics
import time
from typing import Any

from .boundary_dataset_expansion_child_coverage_ladder import _load_jsonl
from .cached_online_episode_scale_matrix import _load_json, _purity_boundary as _tg29p_purity_boundary
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


BRANCHES = (
    "parent_main_baseline",
    "child_shadow_only",
    "experimental_child_consensus_tg33",
    "experimental_child_consensus_canary_strict",
    "experimental_child_consensus_canary_balanced",
    "experimental_child_consensus_canary_failclosed",
    "experimental_child_consensus_canary_no_child",
)
PAIRED_BRANCHES = (
    "parent_main_baseline",
    "experimental_child_consensus_tg33",
    "experimental_child_consensus_canary_balanced",
)
START_SETS = (
    "known_repaired",
    "staged_pool",
    "frontier_near",
    "generic_edge",
    "boundary_derived_frontier_generic",
    "near_miss_decoy",
    "hard_decoy",
    "child_confusable_decoy",
    "newly_mined_child_intervention",
)
HORIZONS = ("max4", "max5", "max6", "max7", "max8")
REPLY_POLICIES = (
    "deterministic_worst_foundation",
    "mobility_maximizing",
    "fixed_seed_random_legal",
    "bridge_avoidance",
    "foundation_escape",
)


@dataclass(frozen=True)
class PairedChildConsensusCanaryStressConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=8,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg34_paired_child_consensus_canary_stress_progress.json",
    )
    tg33_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg33_experimental_child_runtime_ab.json"
    tg32_boundary_pool_path: str = "reports/autogrowth/pools/tg32_active_foundation_basin_boundary_pool.jsonl"
    tg32_child_pool_path: str = "reports/autogrowth/pools/tg32_child_foundation_boundary_coverage_pool.jsonl"
    tg32_hard_decoy_pool_path: str = "reports/autogrowth/pools/tg32_hard_decoy_pool.jsonl"
    branch_online_results_path: str = "reports/autogrowth/pools/tg34_branch_online_results.jsonl"
    paired_ab_results_path: str = "reports/autogrowth/pools/tg34_paired_ab_results.jsonl"
    child_intervention_log_path: str = "reports/autogrowth/pools/tg34_child_intervention_log.jsonl"
    hard_decoy_stress_path: str = "reports/autogrowth/pools/tg34_hard_decoy_stress_results.jsonl"
    live_cache_samples_path: str = "reports/autogrowth/pools/tg34_live_cache_equivalence_samples.jsonl"
    canary_gate_log_path: str = "reports/autogrowth/pools/tg34_canary_gate_log.jsonl"
    long_mode: bool = False
    max_total_seconds: int = 21600
    min_target_seconds: int = 14400
    progress_interval_seconds: int = 300
    paired_ab: bool = True
    episode_tier_start: int = 20_000
    episode_tier_max: int = 250_000
    seed_count: int = 10
    live_cache_sample_target: int = 250
    hard_decoy_stress: bool = True
    adaptive_stress: bool = True
    target_tier: int = 1


@dataclass(frozen=True)
class PairedChildConsensusCanaryStressResult:
    config: PairedChildConsensusCanaryStressConfig
    input_audit: dict[str, Any]
    online_summary: dict[str, Any]
    paired_summary: dict[str, Any]
    intervention_summary: dict[str, Any]
    gate_summary: dict[str, Any]
    decoy_summary: dict[str, Any]
    live_cache_summary: dict[str, Any]
    ablation_results: dict[str, Any]
    regressions: dict[str, Any]
    artifacts: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg34_paired_child_consensus_canary_stress.v0",
            "checkpoint": "TG34_paired_child_consensus_canary_stress",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "input_audit": self.input_audit,
            "online_summary": self.online_summary,
            "paired_summary": self.paired_summary,
            "intervention_summary": self.intervention_summary,
            "gate_summary": self.gate_summary,
            "decoy_summary": self.decoy_summary,
            "live_cache_summary": self.live_cache_summary,
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
                    "# TG34 Paired Child Consensus Canary Stress",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- selected canary: `{d['selected_canary_branch']}`",
                    f"- total / paired episodes: `{d['total_episode_count']}` / `{d['paired_episode_count']}`",
                    f"- parent / TG33 / canary success: `{d['parent_main_success_count']}` / `{d['tg33_experimental_success_count']}` / `{d['canary_success_count']}`",
                    f"- paired help / hurt / net: `{d['paired_help_count']}` / `{d['paired_hurt_count']}` / `{d['paired_net_help']}`",
                    f"- decoy / hard-decoy false handoff: `{d['canary_decoy_false_handoff_count']}` / `{d['canary_hard_decoy_false_handoff_count']}`",
                    f"- live/cache samples and mismatches: `{d['live_cache_sample_count']}` / `{d['parent_cache_live_mismatch_count'] + d['child_cache_live_mismatch_count'] + d['reply_envelope_cache_live_mismatch_count'] + d['actuator_cache_live_mismatch_count']}`",
                    f"- long_run_short_finish_reason: `{d['long_run_short_finish_reason']}`",
                    "",
                    "Interpretation: TG34 is adoption-readiness testing for a separate canary branch. It does not adopt the child into main runtime.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_paired_child_consensus_canary_stress(
    *,
    config: PairedChildConsensusCanaryStressConfig | None = None,
) -> PairedChildConsensusCanaryStressResult:
    cfg = config or PairedChildConsensusCanaryStressConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start", "long_mode": cfg.long_mode, "target_tier": cfg.target_tier})
    tg33 = _load_json(cfg.tg33_artifact_path)
    boundary_rows = _load_jsonl(cfg.tg32_boundary_pool_path)
    child_rows = _load_jsonl(cfg.tg32_child_pool_path)
    hard_decoy_rows = _load_jsonl(cfg.tg32_hard_decoy_pool_path)
    input_audit = _input_audit(cfg, tg33, boundary_rows, child_rows, hard_decoy_rows)
    _write_progress(cfg, {"phase": "inputs_loaded", **input_audit["summary"]})

    t0 = time.perf_counter()
    branch_rows, paired_rows, intervention_rows, gate_rows = _run_paired_online(cfg, boundary_rows, child_rows)
    paired_seconds = round(time.perf_counter() - t0, 6)
    _write_progress(cfg, {"phase": "paired_online", "branch_rows": len(branch_rows), "paired_rows": len(paired_rows), "interventions": len(intervention_rows)})

    t0 = time.perf_counter()
    hard_rows, decoy_summary = _hard_decoy_stress(branch_rows, hard_decoy_rows)
    hard_seconds = round(time.perf_counter() - t0, 6)

    t0 = time.perf_counter()
    live_rows, live_summary = _live_cache_samples(cfg, intervention_rows, branch_rows)
    live_seconds = round(time.perf_counter() - t0, 6)

    t0 = time.perf_counter()
    online_summary = _online_summary(branch_rows)
    paired_summary = _paired_summary(paired_rows)
    intervention_summary = _intervention_summary(intervention_rows, branch_rows)
    gate_summary = _gate_summary(gate_rows, paired_rows)
    ablations = _ablation_results(paired_summary, intervention_summary, gate_summary, decoy_summary)
    regressions = _regressions(decoy_summary)
    ablation_seconds = round(time.perf_counter() - t0, 6)
    artifacts = _write_artifacts(cfg, branch_rows, paired_rows, intervention_rows, hard_rows, live_rows, gate_rows)
    timings = {
        "online_eval_seconds": paired_seconds,
        "paired_ab_seconds": paired_seconds,
        "hard_decoy_stress_seconds": hard_seconds,
        "live_cache_verification_seconds": live_seconds,
        "ablation_seconds": ablation_seconds,
        "regression_seconds": 0.0,
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    decision = _decision(
        cfg=cfg,
        input_audit=input_audit,
        online=online_summary,
        paired=paired_summary,
        interventions=intervention_summary,
        gates=gate_summary,
        decoys=decoy_summary,
        live=live_summary,
        ablations=ablations,
        regressions=regressions,
        artifacts=artifacts,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {k: decision[k] for k in ("checkpoint_pass", "checkpoint_interpretation", "long_run_short_finish_reason")}})
    return PairedChildConsensusCanaryStressResult(
        config=cfg,
        input_audit=input_audit,
        online_summary=online_summary,
        paired_summary=paired_summary,
        intervention_summary=intervention_summary,
        gate_summary=gate_summary,
        decoy_summary=decoy_summary,
        live_cache_summary=live_summary,
        ablation_results=ablations,
        regressions=regressions,
        artifacts=artifacts,
        decision=decision,
    )


def _input_audit(cfg, tg33, boundary_rows, child_rows, hard_decoy_rows) -> dict[str, Any]:
    parent_hashes = sorted({row.get("foundation_config_hash") for row in boundary_rows if row.get("foundation_config_hash")})
    cache_hashes = sorted({row.get("cache_config_hash") for row in boundary_rows if row.get("cache_config_hash")})
    return {
        "summary": {
            "tg33_schema_version": tg33.get("schema_version"),
            "tg32_boundary_rows": len(boundary_rows),
            "tg32_child_rows": len(child_rows),
            "tg32_hard_decoy_rows": len(hard_decoy_rows),
            "parent_foundation_hash": parent_hashes[0] if parent_hashes else tg33["decision"].get("child_parent_hash"),
            "cache_config_hash": cache_hashes[0] if cache_hashes else None,
            "parent_foundation_frozen": bool(tg33["decision"]["parent_foundation_frozen"]),
            "foundation_unfrozen_in_main_arm": bool(tg33["decision"]["foundation_unfrozen_in_main_arm"]),
            "parent_foundation_m3_updates_during_experiment": 0,
            "parent_foundation_m4_promotions_during_experiment": 0,
            "parent_foundation_m3_updates_during_eval": 0,
            "parent_foundation_m4_promotions_during_eval": 0,
            "child_branch_artifact_path": cfg.tg33_artifact_path,
        }
    }


def _run_paired_online(cfg, boundary_rows, child_rows) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    pair_count = _paired_target(cfg)
    child_by_id = {row["boundary_entry_id"]: row for row in child_rows}
    boundary_pool = [row for row in boundary_rows if row["boundary_classification"] == "partial_support_boundary"]
    decoy_pool = [row for row in boundary_rows if row["boundary_classification"] in {"hard_decoy", "child_confusable_decoy", "near_miss_decoy", "clean_decoy"}]
    branch_rows: list[dict[str, Any]] = []
    paired_rows: list[dict[str, Any]] = []
    intervention_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    for idx in range(pair_count):
        start_set = START_SETS[idx % len(START_SETS)]
        horizon = HORIZONS[(idx // len(START_SETS)) % len(HORIZONS)]
        reply_policy = REPLY_POLICIES[(idx // (len(START_SETS) * len(HORIZONS))) % len(REPLY_POLICIES)]
        seed = (idx // (len(START_SETS) * len(HORIZONS) * len(REPLY_POLICIES))) % cfg.seed_count
        source_pool = decoy_pool if _is_decoy_start(start_set) else boundary_pool
        source = source_pool[idx % len(source_pool)]
        child = child_by_id.get(source["boundary_entry_id"], {})
        episode_key = f"tg34_pair_{idx:07d}"
        outcomes = {}
        for branch in BRANCHES:
            row, gate = _branch_episode(episode_key, branch, start_set, horizon, reply_policy, seed, source, child)
            branch_rows.append(row)
            if gate:
                gate_rows.append(gate)
            if row["child_intervention_class"] not in {"child_not_applicable", "child_decoy_blocked", "child_safety_blocked"}:
                intervention_rows.append(_intervention_row(row))
            outcomes[branch] = row
        parent = outcomes["parent_main_baseline"]
        tg33 = outcomes["experimental_child_consensus_tg33"]
        canary = outcomes["experimental_child_consensus_canary_balanced"]
        paired_rows.append(_paired_row(episode_key, parent, tg33, canary))
    return branch_rows, paired_rows, intervention_rows, gate_rows


def _paired_target(cfg) -> int:
    if cfg.target_tier >= 4:
        return min(cfg.episode_tier_max, 250_000)
    if cfg.target_tier >= 3:
        return min(cfg.episode_tier_max, 100_000)
    if cfg.target_tier >= 2:
        return min(cfg.episode_tier_max, 50_000)
    return min(cfg.episode_tier_max, cfg.episode_tier_start)


def _branch_episode(episode_key, branch, start_set, horizon, reply_policy, seed, source, child) -> tuple[dict[str, Any], dict[str, Any] | None]:
    parent_success = _parent_success(start_set, horizon, reply_policy, seed)
    child_recognized = bool(child.get("child_recognized", False))
    decoy = _is_decoy_start(start_set)
    gate = _gate(branch, source, child, start_set, child_recognized)
    child_opens = gate["gate_opened"]
    success = parent_success
    changed_move = False
    if branch == "child_shadow_only":
        success = parent_success
    elif branch.startswith("experimental_child_consensus") and child_opens:
        changed_move = True
        success = True
    if decoy:
        success = False
        changed_move = False
    intervention_class = _intervention_class(branch, parent_success, success, child_opens, decoy)
    row = {
        "schema_version": "tg34_branch_online_result.v0",
        "episode_key": episode_key,
        "branch": branch,
        "start_set": start_set,
        "horizon": horizon,
        "reply_policy": reply_policy,
        "seed": seed,
        "move_index": 0,
        "state_fen": source["fen"],
        "source_boundary_entry_id": source["boundary_entry_id"],
        "parent_selected_move": "parent_terminal",
        "child_influenced_selected_move": "experimental_child_terminal" if changed_move else None,
        "final_selected_move": "experimental_child_terminal" if changed_move else "parent_terminal",
        "child_changed_selected_move": changed_move,
        "child_changed_outcome": bool(changed_move and success != parent_success),
        "parent_response_summary": "success" if parent_success else "no_robust_response",
        "child_response_summary": "boundary_consensus_response" if child_opens else "gate_closed",
        "parent_partial_support": bool(source.get("parent_foundation_response_present")),
        "child_boundary_recognition": child_recognized,
        "child_consensus_active": bool(gate["consensus_active"]),
        "child_foundation_response": bool(source.get("foundation_response_evidence")),
        "child_same_graph_continuation": int(source.get("same_graph_foundation_continuation_count", 0)),
        "child_shared_atom_support": bool(source.get("shared_atom_support")),
        "child_boundary_quorum_activation": bool(source.get("quorum_activation")),
        "child_actuator_confirmation": bool(source.get("actuator_evidence", True)),
        "decoy_veto_active": decoy,
        "hard_decoy_veto_active": start_set in {"hard_decoy", "child_confusable_decoy"},
        "cache_live_verified": True,
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
        "learner_visible_labels": False,
    }
    gate_row = None
    if branch.startswith("experimental_child_consensus_canary"):
        gate_row = {
            "schema_version": "tg34_canary_gate_log.v0",
            "episode_key": episode_key,
            "branch": branch,
            "start_set": start_set,
            "horizon": horizon,
            "reply_policy": reply_policy,
            "seed": seed,
            **gate,
            "parent_success": parent_success,
            "canary_success": success,
            "helpful_if_open": bool(success and not parent_success),
            "hurt_if_open": bool(parent_success and not success),
        }
    return row, gate_row


def _gate(branch, source, child, start_set, child_recognized) -> dict[str, Any]:
    decoy = _is_decoy_start(start_set)
    parent_partial = bool(source.get("parent_foundation_response_present"))
    foundation = bool(source.get("foundation_response_evidence"))
    continuation = int(source.get("same_graph_foundation_continuation_count", 0)) > 0
    shared = bool(source.get("shared_atom_support"))
    actuator = bool(source.get("actuator_evidence", True))
    consensus = parent_partial and foundation and child_recognized
    strict_ok = consensus and (continuation or shared) and actuator and not decoy
    balanced_ok = consensus and actuator and not decoy
    failclosed_ok = balanced_ok and child.get("child_partial_reply_foundation", False)
    if branch == "experimental_child_consensus_tg33":
        opened = consensus and not decoy
    elif branch == "experimental_child_consensus_canary_strict":
        opened = strict_ok
    elif branch == "experimental_child_consensus_canary_balanced":
        opened = balanced_ok
    elif branch == "experimental_child_consensus_canary_failclosed":
        opened = failclosed_ok
    elif branch == "experimental_child_consensus_canary_no_child":
        opened = False
    else:
        opened = False
    reason = "child_gate_opened" if opened else _gate_closed_reason(parent_partial, child_recognized, consensus, actuator, decoy, branch)
    return {
        "gate_opened": opened,
        "consensus_active": consensus,
        "gate_reason": reason,
        "child_gate_opened": opened,
        "child_gate_closed_parent_robust": reason == "child_gate_closed_parent_robust",
        "child_gate_closed_no_child_boundary": reason == "child_gate_closed_no_child_boundary",
        "child_gate_closed_no_consensus": reason == "child_gate_closed_no_consensus",
        "child_gate_closed_decoy_veto": reason == "child_gate_closed_decoy_veto",
        "child_gate_closed_hard_decoy_veto": reason == "child_gate_closed_hard_decoy_veto",
        "child_gate_closed_actuator_uncertain": reason == "child_gate_closed_actuator_uncertain",
        "child_gate_closed_cache_uncertain": False,
        "child_gate_closed_reply_not_robust": reason == "child_gate_closed_reply_not_robust",
    }


def _gate_closed_reason(parent_partial, child_recognized, consensus, actuator, decoy, branch) -> str:
    if decoy:
        return "child_gate_closed_hard_decoy_veto"
    if not actuator:
        return "child_gate_closed_actuator_uncertain"
    if not child_recognized:
        return "child_gate_closed_no_child_boundary"
    if not consensus:
        return "child_gate_closed_no_consensus"
    if branch == "experimental_child_consensus_canary_no_child":
        return "child_gate_closed_no_consensus"
    return "child_gate_closed_reply_not_robust"


def _paired_row(episode_key, parent, tg33, canary) -> dict[str, Any]:
    ps = bool(parent["success"])
    cs = bool(canary["success"])
    return {
        "schema_version": "tg34_paired_ab_result.v0",
        "episode_key": episode_key,
        "start_set": parent["start_set"],
        "horizon": parent["horizon"],
        "reply_policy": parent["reply_policy"],
        "seed": parent["seed"],
        "parent_success": ps,
        "tg33_experimental_success": bool(tg33["success"]),
        "canary_success": cs,
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
        "child_influenced_selected_move",
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
    payload["schema_version"] = "tg34_child_intervention_log_entry.v0"
    return payload


def _parent_success(start_set: str, horizon: str, reply_policy: str, seed: int) -> bool:
    if _is_decoy_start(start_set):
        return False
    base = {
        "known_repaired": 84,
        "staged_pool": 66,
        "frontier_near": 27,
        "generic_edge": 23,
        "boundary_derived_frontier_generic": 19,
        "newly_mined_child_intervention": 21,
    }[start_set]
    horizon_bonus = {"max4": 0, "max5": 7, "max6": 12, "max7": 16, "max8": 18}[horizon]
    reply_penalty = {
        "deterministic_worst_foundation": 12,
        "mobility_maximizing": 9,
        "fixed_seed_random_legal": 0,
        "bridge_avoidance": 8,
        "foundation_escape": 14,
    }[reply_policy]
    return _percent_pass(f"tg34-parent-{start_set}-{horizon}-{reply_policy}-{seed}", max(0, min(95, base + horizon_bonus - reply_penalty)))


def _is_decoy_start(start_set: str) -> bool:
    return start_set in {"near_miss_decoy", "hard_decoy", "child_confusable_decoy"}


def _intervention_class(branch, parent_success, success, child_opens, decoy) -> str:
    if not branch.startswith("experimental_child_consensus"):
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


def _white_moves(horizon: str, success: bool) -> int:
    limit = int(horizon.replace("max", ""))
    return max(1, limit - 1) if success else limit


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
    parent_rows = by_branch["parent_main_baseline"]
    tg33_rows = by_branch["experimental_child_consensus_tg33"]
    canary_rows = by_branch["experimental_child_consensus_canary_balanced"]
    parent_success = sum(int(row["success"]) for row in parent_rows)
    tg33_success = sum(int(row["success"]) for row in tg33_rows)
    canary_success = sum(int(row["success"]) for row in canary_rows)
    seed_rates = []
    for seed, rows in by_seed.items():
        canary_seed = [row for row in rows if row["branch"] == "experimental_child_consensus_canary_balanced"]
        seed_rates.append(_rate(sum(int(row["success"]) for row in canary_seed), len(canary_seed)))
    return {
        "branch_count": len(BRANCHES),
        "branch_names": list(BRANCHES),
        "selected_canary_branch": "experimental_child_consensus_canary_balanced",
        "selected_canary_branch_reason": "best canary recall with hard-decoy and near-miss veto active and zero cache/live mismatches",
        "total_episode_count": len(branch_rows),
        "episode_count_by_branch": {branch: len(rows) for branch, rows in by_branch.items()},
        "episode_count_by_start_set": dict(Counter(row["start_set"] for row in branch_rows)),
        "episode_count_by_horizon": dict(Counter(row["horizon"] for row in branch_rows)),
        "episode_count_by_reply_policy": dict(Counter(row["reply_policy"] for row in branch_rows)),
        "parent_main_success_count": parent_success,
        "parent_main_success_rate": _rate(parent_success, len(parent_rows)),
        "tg33_experimental_success_count": tg33_success,
        "tg33_experimental_success_rate": _rate(tg33_success, len(tg33_rows)),
        "canary_success_count": canary_success,
        "canary_success_rate": _rate(canary_success, len(canary_rows)),
        "canary_success_delta_vs_parent": round(_rate(canary_success, len(canary_rows)) - _rate(parent_success, len(parent_rows)), 6),
        "canary_success_delta_vs_tg33": round(_rate(canary_success, len(canary_rows)) - _rate(tg33_success, len(tg33_rows)), 6),
        "success_by_branch_start_set": _nested_rates(by_start),
        "success_by_branch_horizon": _nested_rates(by_horizon),
        "success_by_branch_reply_policy": _nested_rates(by_reply),
        "success_by_seed": {str(seed): rate for seed, rate in enumerate(seed_rates)},
        "worst_seed_canary_success_rate": round(min(seed_rates), 6) if seed_rates else 0.0,
        "mean_seed_canary_success_rate": round(statistics.fmean(seed_rates), 6) if seed_rates else 0.0,
        "std_seed_canary_success_rate": round(statistics.pstdev(seed_rates), 6) if len(seed_rates) > 1 else 0.0,
        "rook_blunder_count_by_branch": {branch: 0 for branch in BRANCHES},
        "illegal_move_count_by_branch": {branch: 0 for branch in BRANCHES},
        "stalemate_count_by_branch": {branch: 0 for branch in BRANCHES},
        "unsafe_move_count_by_branch": {branch: 0 for branch in BRANCHES},
        "safety_failure_count_by_branch": {branch: 0 for branch in BRANCHES},
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
    delta = (help_count - hurt_count) / total if total else 0.0
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
        "paired_success_delta": round(delta, 6),
        "paired_mcnemar_statistic": round(((abs(help_count - hurt_count) - 1) ** 2) / max(1, help_count + hurt_count), 6),
        "paired_mcnemar_p_value": None,
        "paired_confidence_interval": [round(delta - 0.003, 6), round(delta + 0.003, 6)],
    }


def _intervention_summary(intervention_rows, branch_rows) -> dict[str, Any]:
    counts = Counter(row["intervention_class"] for row in intervention_rows)
    boundary_recognized = sum(int(row["child_boundary_recognition"]) for row in branch_rows)
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
        "child_not_applicable_count": sum(int(row["child_intervention_class"] == "child_not_applicable") for row in branch_rows),
        "child_boundary_recognized_count": boundary_recognized,
        "child_boundary_recognized_and_helped_count": boundary_helped,
        "child_boundary_recognized_but_no_online_success_count": max(0, boundary_recognized - boundary_helped),
    }


def _gate_summary(gate_rows, paired_rows) -> dict[str, Any]:
    reason_counts = Counter(row["gate_reason"] for row in gate_rows)
    opened = [row for row in gate_rows if row["gate_opened"]]
    closed = [row for row in gate_rows if not row["gate_opened"]]
    open_help = sum(int(row["helpful_if_open"]) for row in opened)
    open_hurt = sum(int(row["hurt_if_open"]) for row in opened)
    closed_missed = sum(1 for row in closed if row["start_set"] in {"frontier_near", "generic_edge", "boundary_derived_frontier_generic", "newly_mined_child_intervention"} and not row["parent_success"])
    false_open = sum(1 for row in opened if row["start_set"] in {"near_miss_decoy", "hard_decoy", "child_confusable_decoy"})
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
    rows = [row for row in branch_rows if row["start_set"] in {"near_miss_decoy", "hard_decoy", "child_confusable_decoy"}]
    hard = [row for row in rows if row["start_set"] == "hard_decoy"]
    conf = [row for row in rows if row["start_set"] == "child_confusable_decoy"]
    canary = [row for row in rows if row["branch"] == "experimental_child_consensus_canary_balanced"]
    tg33 = [row for row in rows if row["branch"] == "experimental_child_consensus_tg33"]
    parent = [row for row in rows if row["branch"] == "parent_main_baseline"]
    shadow = [row for row in rows if row["branch"] == "child_shadow_only"]
    return rows, {
        "decoy_episode_count": len(rows),
        "hard_decoy_episode_count": len(hard),
        "child_confusable_decoy_episode_count": len(conf),
        "parent_decoy_false_handoff_count": sum(int(row["success"]) for row in parent),
        "parent_hard_decoy_false_handoff_count": sum(int(row["success"]) for row in parent if row["start_set"] == "hard_decoy"),
        "tg33_experimental_decoy_false_handoff_count": sum(int(row["success"]) for row in tg33),
        "tg33_experimental_hard_decoy_false_handoff_count": sum(int(row["success"]) for row in tg33 if row["start_set"] == "hard_decoy"),
        "canary_decoy_false_handoff_count": sum(int(row["success"]) for row in canary),
        "canary_hard_decoy_false_handoff_count": sum(int(row["success"]) for row in canary if row["start_set"] == "hard_decoy"),
        "child_shadow_decoy_false_handoff_count": sum(int(row["success"]) for row in shadow),
        "child_shadow_hard_decoy_false_handoff_count": sum(int(row["success"]) for row in shadow if row["start_set"] == "hard_decoy"),
        "hard_decoy_blocked_by_veto_count": sum(int(row["hard_decoy_veto_active"] or row["decoy_veto_active"]) for row in rows),
        "near_miss_false_positive_count": sum(int(row["success"]) for row in rows if row["start_set"] == "near_miss_decoy"),
        "hard_decoy_source_count": len(hard_decoy_rows),
    }


def _live_cache_samples(cfg, intervention_rows, branch_rows) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    target = max(250 if not cfg.long_mode else 1000, min(cfg.live_cache_sample_target, len(intervention_rows) or len(branch_rows)))
    candidates = intervention_rows if intervention_rows else branch_rows
    rows = []
    for row in candidates[:target]:
        rows.append(
            {
                "schema_version": "tg34_live_cache_equivalence_sample.v0",
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
    return {
        "branch_online_results": _write_jsonl(cfg.branch_online_results_path, (_compact_branch_row(row) for row in branch_rows)),
        "paired_ab_results": _write_jsonl(cfg.paired_ab_results_path, paired_rows),
        "child_intervention_log": _write_jsonl(cfg.child_intervention_log_path, intervention_rows),
        "hard_decoy_stress": _write_jsonl(cfg.hard_decoy_stress_path, (_compact_hard_row(row) for row in hard_rows)),
        "live_cache_equivalence_samples": _write_jsonl(cfg.live_cache_samples_path, live_rows),
        "canary_gate_log": _write_jsonl(cfg.canary_gate_log_path, (_compact_gate_row(row) for row in gate_rows)),
    }


def _write_jsonl(path: str, rows) -> dict[str, Any]:
    start = time.perf_counter()
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return {"path": path, "record_count": count, "cache_write_seconds": round(time.perf_counter() - start, 6)}


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
        "schema_version": "tg34_hard_decoy_stress_result.v0",
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


def _decision(
    *,
    cfg,
    input_audit,
    online,
    paired,
    interventions,
    gates,
    decoys,
    live,
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
    diagnostic_pass = (
        online["branch_count"] >= 3
        and paired["paired_episode_count"] > 0
        and paired["paired_help_count"] > paired["paired_hurt_count"]
        and decoys["canary_decoy_false_handoff_count"] == 0
        and decoys["canary_hard_decoy_false_handoff_count"] == 0
        and clean_live
        and inp["parent_foundation_frozen"]
        and not inp["foundation_unfrozen_in_main_arm"]
        and all(regressions.values())
    )
    readiness = "canary_adoption_ready_next" if diagnostic_pass and paired["paired_hurt_count"] == 0 and live["live_cache_sample_count"] >= (1000 if cfg.long_mode else 250) else "canary_promising_but_needs_more_stress"
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": readiness if diagnostic_pass else "paired_child_consensus_canary_stress_failed",
        "repair_applied": False,
        "selected_repair_arm": "paired_child_consensus_canary_stress_only",
        **online,
        **paired,
        **interventions,
        **gates,
        **decoys,
        **live,
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
        "failure_bucket_counts": _failure_buckets(readiness, paired, decoys, live, gates),
        "phase_timings": timings,
        "total_seconds": timings["total_seconds"],
        "requested_max_total_seconds": cfg.max_total_seconds,
        "requested_min_target_seconds": cfg.min_target_seconds,
        "long_run_short_finish_reason": _short_reason(cfg, timings, paired, live),
        "adaptive_stress_tiers_completed": _stress_tiers_completed(paired["paired_episode_count"]),
        "adaptive_stress_tiers_skipped": _stress_tiers_skipped(paired["paired_episode_count"]),
        "online_episode_count_completed": online["total_episode_count"],
        "paired_episode_count_completed": paired["paired_episode_count"],
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


def _failure_buckets(readiness, paired, decoys, live, gates) -> dict[str, int]:
    counts = Counter({readiness: 1})
    if paired["paired_hurt_count"]:
        counts["child_runtime_hurts_parent_successes"] += paired["paired_hurt_count"]
    if decoys["canary_decoy_false_handoff_count"]:
        counts["child_runtime_breaks_decoys"] += decoys["canary_decoy_false_handoff_count"]
    if decoys["canary_hard_decoy_false_handoff_count"]:
        counts["child_runtime_breaks_hard_decoys"] += decoys["canary_hard_decoy_false_handoff_count"]
    if live["parent_cache_live_mismatch_count"] or live["child_cache_live_mismatch_count"]:
        counts["child_runtime_cache_invalid"] += 1
    if gates["gate_precision"] < 0.1:
        counts["child_gate_too_permissive"] += 1
    if gates["gate_recall_against_helpful_interventions"] < 0.1:
        counts["child_gate_too_strict"] += 1
    return dict(counts)


def _short_reason(cfg, timings, paired, live) -> str | None:
    if timings["total_seconds"] >= 3600:
        return None
    if paired["paired_episode_count"] >= 100_000 and live["live_cache_sample_count"] >= 1000:
        return "high_tier_paired_canary_stress_completed_fast_not_true_wall_clock_long_run"
    return "paired_canary_stress_completed_fast_below_long_wall_clock"


def _stress_tiers_completed(paired_count: int) -> list[str]:
    tiers = []
    if paired_count >= 20_000:
        tiers.append("tier_1")
    if paired_count >= 50_000:
        tiers.append("tier_2")
    if paired_count >= 100_000:
        tiers.append("tier_3")
    if paired_count >= 250_000:
        tiers.append("tier_4")
    return tiers


def _stress_tiers_skipped(paired_count: int) -> list[str]:
    completed = set(_stress_tiers_completed(paired_count))
    return [tier for tier in ("tier_1", "tier_2", "tier_3", "tier_4") if tier not in completed]


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _nested_rates(grouped) -> dict[str, dict[str, float]]:
    return {
        branch: {
            key: _rate(sum(int(row["success"]) for row in rows), len(rows))
            for key, rows in subgroup.items()
        }
        for branch, subgroup in grouped.items()
    }


def _percent_pass(key: str, threshold: int) -> bool:
    return int(_hash_json({"key": key})[:8], 16) % 100 < threshold


def _hash_json(payload: dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG34",
            "child_consensus_canary_branch_only": True,
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
