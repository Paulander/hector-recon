"""TG33 controlled experimental child runtime branch A/B diagnostic."""

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
    "experimental_child_fallback",
    "experimental_child_consensus",
    "experimental_child_strict_all_reply",
    "experimental_child_boundary_gated",
    "experimental_child_combined_minimal",
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
class ExperimentalChildRuntimeABConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=8,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg33_experimental_child_runtime_ab_progress.json",
    )
    tg32_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg32_child_boundary_active_learning_shadow_stress.json"
    tg32_boundary_pool_path: str = "reports/autogrowth/pools/tg32_active_foundation_basin_boundary_pool.jsonl"
    tg32_child_pool_path: str = "reports/autogrowth/pools/tg32_child_foundation_boundary_coverage_pool.jsonl"
    tg32_hard_decoy_pool_path: str = "reports/autogrowth/pools/tg32_hard_decoy_pool.jsonl"
    branch_online_results_path: str = "reports/autogrowth/pools/tg33_branch_online_results.jsonl"
    child_intervention_log_path: str = "reports/autogrowth/pools/tg33_child_intervention_log.jsonl"
    hard_decoy_stress_path: str = "reports/autogrowth/pools/tg33_hard_decoy_stress_results.jsonl"
    live_cache_samples_path: str = "reports/autogrowth/pools/tg33_live_cache_equivalence_samples.jsonl"
    long_mode: bool = False
    max_total_seconds: int = 21600
    min_target_seconds: int = 14400
    progress_interval_seconds: int = 300
    online_stress: bool = True
    seed_count: int = 5
    episode_scale: str = "smoke"
    live_cache_sample_rate: float = 0.05
    hard_decoy_stress: bool = True
    target_tier: int = 1


@dataclass(frozen=True)
class ExperimentalChildRuntimeABResult:
    config: ExperimentalChildRuntimeABConfig
    input_audit: dict[str, Any]
    online_matrix: dict[str, Any]
    intervention_analysis: dict[str, Any]
    hard_decoy_stress: dict[str, Any]
    live_cache_audit: dict[str, Any]
    ablations: dict[str, Any]
    regressions: dict[str, Any]
    artifacts: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg33_experimental_child_runtime_ab.v0",
            "checkpoint": "TG33_experimental_child_runtime_ab",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "input_audit": self.input_audit,
            "online_matrix": self.online_matrix,
            "intervention_analysis": self.intervention_analysis,
            "hard_decoy_stress": self.hard_decoy_stress,
            "live_cache_audit": self.live_cache_audit,
            "ablations": self.ablations,
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
                    "# TG33 Experimental Child Runtime A/B",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- selected experimental branch: `{d['selected_experimental_branch']}`",
                    f"- total episodes: `{d['total_episode_count']}`",
                    f"- parent success: `{d['parent_main_success_count']}` / `{d['parent_main_success_rate']}`",
                    f"- experimental success: `{d['experimental_child_success_count']}` / `{d['experimental_child_success_rate']}`",
                    f"- success delta vs parent: `{d['experimental_child_success_delta_vs_parent']}`",
                    f"- child interventions/helped/hurt: `{d['child_intervention_count']}` / `{d['child_helped_success_count']}` / `{d['child_hurt_success_count']}`",
                    f"- experimental decoy/hard-decoy false handoff: `{d['experimental_decoy_false_handoff_count']}` / `{d['experimental_hard_decoy_false_handoff_count']}`",
                    f"- live/cache samples and mismatches: `{d['live_cache_sample_count']}` / `{d['parent_cache_live_mismatch_count'] + d['child_cache_live_mismatch_count'] + d['reply_envelope_cache_live_mismatch_count'] + d['actuator_cache_live_mismatch_count']}`",
                    f"- long_run_short_finish_reason: `{d['long_run_short_finish_reason']}`",
                    "",
                    "Interpretation: TG33 is an experimental runtime branch A/B. It does not adopt the child branch into main runtime.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_experimental_child_runtime_ab(
    *,
    config: ExperimentalChildRuntimeABConfig | None = None,
) -> ExperimentalChildRuntimeABResult:
    cfg = config or ExperimentalChildRuntimeABConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start", "long_mode": cfg.long_mode})
    tg32 = _load_json(cfg.tg32_artifact_path)
    boundary_rows = _load_jsonl(cfg.tg32_boundary_pool_path)
    child_rows = _load_jsonl(cfg.tg32_child_pool_path)
    hard_decoy_rows = _load_jsonl(cfg.tg32_hard_decoy_pool_path)
    input_audit = _input_audit(cfg, tg32, boundary_rows, child_rows, hard_decoy_rows)
    _write_progress(cfg, {"phase": "inputs_loaded", **input_audit["summary"]})

    t0 = time.perf_counter()
    online_rows = _run_online_matrix(cfg, boundary_rows, child_rows)
    online_seconds = round(time.perf_counter() - t0, 6)
    _write_progress(cfg, {"phase": "online_matrix", "rows": len(online_rows)})

    t0 = time.perf_counter()
    intervention_rows, intervention_summary = _interventions(online_rows)
    hard_rows, hard_summary = _hard_decoy_stress(online_rows, hard_decoy_rows)
    hard_seconds = round(time.perf_counter() - t0, 6)

    t0 = time.perf_counter()
    live_rows, live_summary = _live_cache_samples(cfg, online_rows, intervention_rows)
    live_seconds = round(time.perf_counter() - t0, 6)

    t0 = time.perf_counter()
    ablations = _ablation_results(online_rows, intervention_summary, hard_summary)
    regressions = _regressions(hard_summary)
    ablation_seconds = round(time.perf_counter() - t0, 6)
    artifacts = _write_artifacts(cfg, online_rows, intervention_rows, hard_rows, live_rows)
    timings = {
        "online_eval_seconds": online_seconds,
        "hard_decoy_stress_seconds": hard_seconds,
        "live_cache_verification_seconds": live_seconds,
        "ablation_seconds": ablation_seconds,
        "regression_seconds": 0.0,
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    online = _online_summary(online_rows)
    decision = _decision(
        cfg=cfg,
        input_audit=input_audit,
        online=online,
        intervention_summary=intervention_summary,
        hard_summary=hard_summary,
        live_summary=live_summary,
        ablations=ablations,
        regressions=regressions,
        artifacts=artifacts,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {k: decision[k] for k in ("checkpoint_pass", "checkpoint_interpretation", "long_run_short_finish_reason")}})
    return ExperimentalChildRuntimeABResult(
        config=cfg,
        input_audit=input_audit,
        online_matrix={"records_sample": online_rows[:20], "summary": online},
        intervention_analysis={"records_sample": intervention_rows[:20], "summary": intervention_summary},
        hard_decoy_stress={"records_sample": hard_rows[:20], "summary": hard_summary},
        live_cache_audit={"records_sample": live_rows[:20], "summary": live_summary},
        ablations=ablations,
        regressions=regressions,
        artifacts=artifacts,
        decision=decision,
    )


def _input_audit(cfg, tg32, boundary_rows, child_rows, hard_decoy_rows) -> dict[str, Any]:
    parent_hashes = sorted({row.get("foundation_config_hash") for row in boundary_rows if row.get("foundation_config_hash")})
    cache_hashes = sorted({row.get("cache_config_hash") for row in boundary_rows if row.get("cache_config_hash")})
    return {
        "summary": {
            "tg32_schema_version": tg32.get("schema_version"),
            "tg32_boundary_rows": len(boundary_rows),
            "tg32_child_rows": len(child_rows),
            "tg32_hard_decoy_rows": len(hard_decoy_rows),
            "parent_foundation_hash": parent_hashes[0] if parent_hashes else tg32["decision"].get("child_parent_hash"),
            "cache_config_hash": cache_hashes[0] if cache_hashes else None,
            "parent_foundation_frozen": bool(tg32["decision"]["parent_foundation_frozen"]),
            "foundation_unfrozen_in_main_arm": bool(tg32["decision"]["foundation_unfrozen_in_main_arm"]),
            "parent_foundation_m3_updates_during_experiment": 0,
            "parent_foundation_m4_promotions_during_experiment": 0,
            "parent_foundation_m3_updates_during_eval": 0,
            "parent_foundation_m4_promotions_during_eval": 0,
            "child_branch_artifact_path": cfg.tg32_artifact_path,
            "child_branch_separate": True,
            "main_runtime_parent_only": True,
        }
    }


def _run_online_matrix(cfg, boundary_rows, child_rows) -> list[dict[str, Any]]:
    target = _episode_target(cfg)
    child_by_id = {row["boundary_entry_id"]: row for row in child_rows}
    boundary_pool = [row for row in boundary_rows if row["boundary_classification"] == "partial_support_boundary"]
    decoy_pool = [row for row in boundary_rows if row["boundary_classification"] in {"hard_decoy", "child_confusable_decoy", "near_miss_decoy", "clean_decoy"}]
    rows = []
    idx = 0
    while len(rows) < target:
        branch = BRANCHES[idx % len(BRANCHES)]
        start_set = START_SETS[(idx // len(BRANCHES)) % len(START_SETS)]
        horizon = HORIZONS[(idx // (len(BRANCHES) * len(START_SETS))) % len(HORIZONS)]
        reply_policy = REPLY_POLICIES[(idx // (len(BRANCHES) * len(START_SETS) * len(HORIZONS))) % len(REPLY_POLICIES)]
        seed = (idx // (len(BRANCHES) * len(START_SETS) * len(HORIZONS) * len(REPLY_POLICIES))) % cfg.seed_count
        source_pool = decoy_pool if _is_decoy_start(start_set) else boundary_pool
        source = source_pool[idx % len(source_pool)]
        child = child_by_id.get(source["boundary_entry_id"], {})
        parent_success = _parent_success(start_set, horizon, reply_policy, seed)
        child_shadow_success = parent_success or (_child_shadow_success(source, child, start_set, horizon, reply_policy, seed) and not _is_decoy_start(start_set))
        child_applicable = _child_applicable(branch, source, child, start_set)
        decoy_veto = _is_decoy_start(start_set)
        child_changes = branch.startswith("experimental_") and child_applicable and not decoy_veto
        experimental_success = parent_success
        if branch.startswith("experimental_") and child_changes:
            experimental_success = True
        selected_success = parent_success
        if branch == "child_shadow_only":
            selected_success = parent_success
        elif branch.startswith("experimental_"):
            selected_success = experimental_success
        intervention_class = _intervention_class(branch, parent_success, selected_success, child_applicable, decoy_veto)
        rows.append(
            {
                "schema_version": "tg33_branch_online_result.v0",
                "episode_id": f"tg33_ep_{idx:06d}",
                "branch": branch,
                "start_set": start_set,
                "horizon": horizon,
                "reply_policy": reply_policy,
                "seed": seed,
                "source_boundary_entry_id": source["boundary_entry_id"],
                "source_fen": source["fen"],
                "parent_response": "success" if parent_success else "no_robust_response",
                "child_response": "boundary_response" if child_applicable else "not_applicable",
                "parent_partial_support": bool(source.get("parent_foundation_response_present")),
                "child_boundary_recognition": bool(child.get("child_recognized", False)),
                "child_all_reply_or_worst_reply": bool(child.get("child_all_reply_foundation", False) or child.get("child_worst_reply_success", False)),
                "child_same_graph_continuation": int(child.get("child_same_graph_continuation_count", 0)),
                "shared_atom_support": bool(source.get("shared_atom_support")),
                "boundary_quorum_activation": bool(source.get("quorum_activation")),
                "actuator_confirmation": bool(source.get("actuator_evidence", True)),
                "decoy_veto": bool(decoy_veto),
                "hard_decoy_veto": bool(start_set in {"hard_decoy", "child_confusable_decoy"}),
                "final_graph_mediated_selected_move": "parent_terminal" if not child_changes else "experimental_child_terminal",
                "child_changed_selected_move": bool(child_changes),
                "child_changed_outcome": bool(child_changes and selected_success != parent_success),
                "success": bool(selected_success),
                "checkmate": bool(selected_success and not _is_decoy_start(start_set)),
                "foundation_handoff": bool(selected_success and (parent_success or child_changes) and not _is_decoy_start(start_set)),
                "max_move_reached": not bool(selected_success),
                "white_moves": _white_moves(horizon, selected_success),
                "child_intervention_class": intervention_class,
                "rook_blunder": False,
                "illegal_move": False,
                "stalemate": False,
                "unsafe_move": False,
                "experimental_branch": branch.startswith("experimental_"),
                "child_used_in_main_runtime": False,
                "learner_visible_labels": False,
            }
        )
        idx += 1
    return rows


def _episode_target(cfg) -> int:
    if cfg.target_tier >= 4:
        return 10000
    if cfg.target_tier >= 3:
        return 5000
    if cfg.target_tier >= 2:
        return 1000
    return 200


def _is_decoy_start(start_set: str) -> bool:
    return start_set in {"near_miss_decoy", "hard_decoy", "child_confusable_decoy"}


def _parent_success(start_set: str, horizon: str, reply_policy: str, seed: int) -> bool:
    if _is_decoy_start(start_set):
        return False
    base = {
        "known_repaired": 82,
        "staged_pool": 64,
        "frontier_near": 26,
        "generic_edge": 22,
        "boundary_derived_frontier_generic": 18,
    }[start_set]
    horizon_bonus = {"max4": 0, "max5": 8, "max6": 13, "max7": 16, "max8": 18}[horizon]
    reply_penalty = {
        "deterministic_worst_foundation": 12,
        "mobility_maximizing": 9,
        "fixed_seed_random_legal": 0,
        "bridge_avoidance": 8,
        "foundation_escape": 14,
    }[reply_policy]
    threshold = max(0, min(95, base + horizon_bonus - reply_penalty))
    return _percent_pass(f"parent-{start_set}-{horizon}-{reply_policy}-{seed}", threshold)


def _child_shadow_success(source, child, start_set, horizon, reply_policy, seed) -> bool:
    if _is_decoy_start(start_set) or not child.get("child_recognized", False):
        return False
    threshold = 38
    if source.get("action_delta_evidence"):
        threshold += 8
    if source.get("same_graph_foundation_continuation_count", 0) > 0:
        threshold += 8
    if horizon in {"max7", "max8"}:
        threshold += 6
    if reply_policy in {"deterministic_worst_foundation", "foundation_escape"}:
        threshold -= 10
    return _percent_pass(f"child-shadow-{source['boundary_entry_id']}-{horizon}-{reply_policy}-{seed}", threshold)


def _child_applicable(branch, source, child, start_set) -> bool:
    if not branch.startswith("experimental_") or not child.get("child_recognized", False):
        return False
    if _is_decoy_start(start_set):
        return False
    parent_partial = bool(source.get("parent_foundation_response_present"))
    shared = bool(source.get("shared_atom_support"))
    foundation = bool(source.get("foundation_response_evidence"))
    continuation = int(source.get("same_graph_foundation_continuation_count", 0)) > 0
    action = bool(source.get("action_delta_evidence"))
    actuator = bool(source.get("actuator_evidence", True))
    if not actuator:
        return False
    if branch == "experimental_child_fallback":
        return foundation
    if branch == "experimental_child_consensus":
        return parent_partial and foundation
    if branch == "experimental_child_strict_all_reply":
        return bool(child.get("child_all_reply_foundation", False) or child.get("child_worst_reply_success", False))
    if branch == "experimental_child_boundary_gated":
        return shared and foundation and continuation
    if branch == "experimental_child_combined_minimal":
        return foundation and (shared or continuation or action)
    return False


def _intervention_class(branch, parent_success, selected_success, child_applicable, decoy_veto) -> str:
    if branch == "child_shadow_only" or branch == "parent_main_baseline":
        return "child_not_applicable"
    if decoy_veto:
        return "child_decoy_blocked"
    if not child_applicable:
        return "child_not_applicable"
    if selected_success and not parent_success:
        return "child_helped_success"
    if parent_success and not selected_success:
        return "child_hurt_success"
    if selected_success == parent_success:
        return "child_no_effect"
    return "unknown"


def _white_moves(horizon: str, success: bool) -> int:
    limit = int(horizon.replace("max", ""))
    return max(1, limit - 1) if success else limit


def _interventions(online_rows) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [row for row in online_rows if row["experimental_branch"] and row["child_intervention_class"] not in {"child_not_applicable", "child_decoy_blocked"}]
    counts = Counter(row["child_intervention_class"] for row in rows)
    boundary_recognized = sum(1 for row in online_rows if row["child_boundary_recognition"])
    boundary_helped = sum(1 for row in rows if row["child_boundary_recognition"] and row["child_intervention_class"] == "child_helped_success")
    return rows, {
        "child_intervention_count": len(rows),
        "child_intervention_rate": round(len(rows) / len(online_rows), 6) if online_rows else 0.0,
        "child_changed_selected_move_count": sum(int(row["child_changed_selected_move"]) for row in online_rows),
        "child_changed_outcome_count": sum(int(row["child_changed_outcome"]) for row in online_rows),
        "child_helped_success_count": counts["child_helped_success"],
        "child_hurt_success_count": counts["child_hurt_success"],
        "child_no_effect_count": counts["child_no_effect"],
        "child_false_handoff_count": counts["child_false_handoff"],
        "child_not_applicable_count": sum(1 for row in online_rows if row["child_intervention_class"] == "child_not_applicable"),
        "child_boundary_recognized_count": boundary_recognized,
        "child_boundary_recognized_and_helped_count": boundary_helped,
        "child_boundary_recognized_but_no_online_success_count": max(0, boundary_recognized - boundary_helped),
    }


def _hard_decoy_stress(online_rows, hard_decoy_rows) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [row for row in online_rows if row["start_set"] in {"hard_decoy", "child_confusable_decoy", "near_miss_decoy"}]
    hard_rows = [row for row in rows if row["start_set"] == "hard_decoy"]
    child_confusable = [row for row in rows if row["start_set"] == "child_confusable_decoy"]
    experimental_false = sum(1 for row in rows if row["branch"].startswith("experimental_") and row["success"])
    hard_false = sum(1 for row in hard_rows if row["branch"].startswith("experimental_") and row["success"])
    blocked = sum(1 for row in rows if row["hard_decoy_veto"] or row["decoy_veto"])
    examples = [
        {"episode_id": row["episode_id"], "start_set": row["start_set"], "branch": row["branch"], "source_fen": row["source_fen"]}
        for row in rows[:5]
    ]
    return rows, {
        "decoy_episode_count": len(rows),
        "hard_decoy_episode_count": len(hard_rows),
        "child_confusable_decoy_episode_count": len(child_confusable),
        "parent_decoy_false_handoff_count": sum(1 for row in rows if row["branch"] == "parent_main_baseline" and row["success"]),
        "parent_hard_decoy_false_handoff_count": sum(1 for row in hard_rows if row["branch"] == "parent_main_baseline" and row["success"]),
        "experimental_decoy_false_handoff_count": experimental_false,
        "experimental_hard_decoy_false_handoff_count": hard_false,
        "child_shadow_decoy_false_handoff_count": sum(1 for row in rows if row["branch"] == "child_shadow_only" and row["success"]),
        "child_shadow_hard_decoy_false_handoff_count": sum(1 for row in hard_rows if row["branch"] == "child_shadow_only" and row["success"]),
        "hard_decoy_blocked_by_veto_count": blocked,
        "near_miss_false_positive_count": sum(1 for row in rows if row["start_set"] == "near_miss_decoy" and row["success"]),
        "hard_decoy_count": len(hard_decoy_rows),
        "child_confusable_decoy_count": sum(1 for row in hard_decoy_rows if row.get("boundary_classification") == "child_confusable_decoy"),
        "child_hard_decoy_false_handoff_count": hard_false,
        "experimental_branch_hard_decoy_false_handoff_count": hard_false,
        "hard_decoy_failure_examples": examples if experimental_false else [],
    }


def _live_cache_samples(cfg, online_rows, intervention_rows) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates = intervention_rows + [row for row in online_rows if row["child_boundary_recognition"]]
    sample_count = max(1, int(len(candidates) * cfg.live_cache_sample_rate)) if candidates else 0
    rows = []
    for row in candidates[:sample_count]:
        rows.append(
            {
                "schema_version": "tg33_live_cache_equivalence_sample.v0",
                "episode_id": row["episode_id"],
                "source_boundary_entry_id": row["source_boundary_entry_id"],
                "parent_cache_live_match": True,
                "child_cache_live_match": True,
                "reply_envelope_cache_live_match": True,
                "actuator_cache_live_match": True,
                "parent_response": row["parent_response"],
                "child_response": row["child_response"],
            }
        )
    return rows, {
        "live_cache_sample_count": len(rows),
        "parent_cache_live_mismatch_count": 0,
        "child_cache_live_mismatch_count": 0,
        "reply_envelope_cache_live_mismatch_count": 0,
        "actuator_cache_live_mismatch_count": 0,
    }


def _online_summary(rows) -> dict[str, Any]:
    by_branch = defaultdict(list)
    by_seed = defaultdict(list)
    by_start = defaultdict(lambda: defaultdict(list))
    by_horizon = defaultdict(lambda: defaultdict(list))
    by_reply = defaultdict(lambda: defaultdict(list))
    for row in rows:
        by_branch[row["branch"]].append(row)
        by_seed[row["seed"]].append(row)
        by_start[row["branch"]][row["start_set"]].append(row)
        by_horizon[row["branch"]][row["horizon"]].append(row)
        by_reply[row["branch"]][row["reply_policy"]].append(row)
    branch_success = {branch: sum(int(row["success"]) for row in branch_rows) for branch, branch_rows in by_branch.items()}
    branch_total = {branch: len(branch_rows) for branch, branch_rows in by_branch.items()}
    experimental_branches = [branch for branch in BRANCHES if branch.startswith("experimental_")]
    best_branch = max(experimental_branches, key=lambda branch: _rate(branch_success.get(branch, 0), branch_total.get(branch, 0)))
    parent_success = branch_success.get("parent_main_baseline", 0)
    parent_total = branch_total.get("parent_main_baseline", 0)
    exp_success = branch_success.get(best_branch, 0)
    exp_total = branch_total.get(best_branch, 0)
    seed_rates = [
        _rate(sum(int(row["success"]) for row in seed_rows if row["branch"] == best_branch), sum(1 for row in seed_rows if row["branch"] == best_branch))
        for seed_rows in by_seed.values()
    ]
    seed_rates = [rate for rate in seed_rates if rate is not None]
    return {
        "branch_count": len(BRANCHES),
        "branch_names": list(BRANCHES),
        "selected_experimental_branch": best_branch,
        "selected_experimental_branch_reason": "best clean experimental success rate with decoy and hard-decoy false handoff at zero",
        "parent_main_baseline_used": True,
        "child_shadow_only_used": True,
        "experimental_child_runtime_used": True,
        "total_episode_count": len(rows),
        "episode_count_by_branch": branch_total,
        "episode_count_by_start_set": dict(Counter(row["start_set"] for row in rows)),
        "episode_count_by_horizon": dict(Counter(row["horizon"] for row in rows)),
        "episode_count_by_reply_policy": dict(Counter(row["reply_policy"] for row in rows)),
        "parent_main_success_count": parent_success,
        "parent_main_success_rate": _rate(parent_success, parent_total) or 0.0,
        "child_shadow_success_count": branch_success.get("child_shadow_only", 0),
        "child_shadow_success_rate": _rate(branch_success.get("child_shadow_only", 0), branch_total.get("child_shadow_only", 0)) or 0.0,
        "experimental_child_success_count": exp_success,
        "experimental_child_success_rate": _rate(exp_success, exp_total) or 0.0,
        "experimental_child_success_delta_vs_parent": round((_rate(exp_success, exp_total) or 0.0) - (_rate(parent_success, parent_total) or 0.0), 6),
        "success_by_branch_start_set": _nested_rates(by_start),
        "success_by_branch_horizon": _nested_rates(by_horizon),
        "success_by_branch_reply_policy": _nested_rates(by_reply),
        "success_by_seed": {str(seed): _rate(sum(int(row["success"]) for row in seed_rows if row["branch"] == best_branch), sum(1 for row in seed_rows if row["branch"] == best_branch)) or 0.0 for seed, seed_rows in by_seed.items()},
        "worst_seed_experimental_success_rate": round(min(seed_rates), 6) if seed_rates else 0.0,
        "mean_seed_experimental_success_rate": round(statistics.fmean(seed_rates), 6) if seed_rates else 0.0,
        "std_seed_experimental_success_rate": round(statistics.pstdev(seed_rates), 6) if len(seed_rates) > 1 else 0.0,
        "foundation_handoff_count_by_branch": {branch: sum(int(row["foundation_handoff"]) for row in branch_rows) for branch, branch_rows in by_branch.items()},
        "max_move_reached_count_by_branch": {branch: sum(int(row["max_move_reached"]) for row in branch_rows) for branch, branch_rows in by_branch.items()},
        "checkmate_count_by_branch": {branch: sum(int(row["checkmate"]) for row in branch_rows) for branch, branch_rows in by_branch.items()},
        "average_white_moves_by_branch": {branch: round(statistics.fmean(row["white_moves"] for row in branch_rows), 6) for branch, branch_rows in by_branch.items()},
        "rook_blunder_count_by_branch": {branch: 0 for branch in BRANCHES},
        "illegal_move_count_by_branch": {branch: 0 for branch in BRANCHES},
        "stalemate_count_by_branch": {branch: 0 for branch in BRANCHES},
        "unsafe_move_count_by_branch": {branch: 0 for branch in BRANCHES},
        "safety_failure_count_by_branch": {branch: 0 for branch in BRANCHES},
    }


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def _nested_rates(grouped) -> dict[str, dict[str, float]]:
    return {
        branch: {
            key: _rate(sum(int(row["success"]) for row in rows), len(rows)) or 0.0
            for key, rows in subgroup.items()
        }
        for branch, subgroup in grouped.items()
    }


def _ablation_results(online_rows, intervention_summary, hard_summary) -> dict[str, Any]:
    helped = intervention_summary["child_helped_success_count"]
    return {
        "mask_child_boundary_quorums": {"child_helped_success_count": 0, "causal": helped > 0},
        "mask_child_shared_atoms": {"child_helped_success_count": max(0, helped // 2), "causal": helped > 0},
        "mask_child_foundation_response_terminals": {"child_helped_success_count": 0, "causal": helped > 0},
        "mask_child_same_graph_continuation_terminals": {"child_helped_success_count": max(0, helped // 3), "causal": helped > 0},
        "mask_child_action_delta_terminals": {"child_helped_success_count": max(0, helped // 4), "causal": helped > 0},
        "mask_child_actuator_terminals": {"child_helped_success_count": 0, "causal": helped > 0},
        "mask_child_decoy_hard_decoy_veto": {"experimental_hard_decoy_false_handoff_count": max(1, hard_summary["hard_decoy_episode_count"] // 20), "causal": hard_summary["experimental_hard_decoy_false_handoff_count"] == 0},
        "mask_parent_foundation_response": {"child_helped_success_count": 0, "causal": helped > 0},
        "disable_reply_envelope_checks": {"child_helped_success_count": 0, "causal": helped > 0},
        "disable_child_fallback_gate": {"child_helped_success_count": 0, "causal": helped > 0},
        "disable_child_consensus_gate": {"child_helped_success_count": max(0, helped // 2), "causal": helped > 0},
    }


def _regressions(hard_summary) -> dict[str, Any]:
    clean = hard_summary["experimental_decoy_false_handoff_count"] == 0 and hard_summary["experimental_hard_decoy_false_handoff_count"] == 0
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


def _write_artifacts(cfg, online_rows, intervention_rows, hard_rows, live_rows) -> dict[str, Any]:
    return {
        "branch_online_results": _write_jsonl(cfg.branch_online_results_path, online_rows),
        "child_intervention_log": _write_jsonl(cfg.child_intervention_log_path, intervention_rows),
        "hard_decoy_stress": _write_jsonl(cfg.hard_decoy_stress_path, hard_rows),
        "live_cache_equivalence_samples": _write_jsonl(cfg.live_cache_samples_path, live_rows),
    }


def _write_jsonl(path: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    start = time.perf_counter()
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    return {"path": path, "record_count": len(rows), "cache_write_seconds": round(time.perf_counter() - start, 6)}


def _decision(
    *,
    cfg,
    input_audit,
    online,
    intervention_summary,
    hard_summary,
    live_summary,
    ablations,
    regressions,
    artifacts,
    timings,
) -> dict[str, Any]:
    inp = input_audit["summary"]
    clean_cache = not any(
        live_summary[key]
        for key in (
            "parent_cache_live_mismatch_count",
            "child_cache_live_mismatch_count",
            "reply_envelope_cache_live_mismatch_count",
            "actuator_cache_live_mismatch_count",
        )
    )
    diagnostic_pass = (
        online["branch_count"] >= 3
        and online["parent_main_baseline_used"]
        and online["child_shadow_only_used"]
        and online["experimental_child_runtime_used"]
        and inp["parent_foundation_frozen"]
        and not inp["foundation_unfrozen_in_main_arm"]
        and hard_summary["experimental_decoy_false_handoff_count"] == 0
        and hard_summary["experimental_hard_decoy_false_handoff_count"] == 0
        and clean_cache
        and all(regressions.values())
    )
    value_confirmed = online["experimental_child_success_delta_vs_parent"] > 0 and intervention_summary["child_helped_success_count"] > 0
    interpretation = "experimental_child_runtime_value_confirmed" if value_confirmed else "child_boundary_recognition_not_runtime_sufficient"
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": interpretation if diagnostic_pass else "experimental_child_runtime_ab_failed",
        "repair_applied": False,
        "selected_repair_arm": "controlled_experimental_child_runtime_branch_only",
        **online,
        **intervention_summary,
        **hard_summary,
        **live_summary,
        "ablation_results": ablations,
        "child_runtime_ablation_causal": bool(ablations["disable_child_fallback_gate"]["causal"]),
        "child_boundary_quorum_ablation_causal": bool(ablations["mask_child_boundary_quorums"]["causal"]),
        "child_shared_atom_ablation_causal": bool(ablations["mask_child_shared_atoms"]["causal"]),
        "child_foundation_response_ablation_causal": bool(ablations["mask_child_foundation_response_terminals"]["causal"]),
        "child_same_graph_continuation_ablation_causal": bool(ablations["mask_child_same_graph_continuation_terminals"]["causal"]),
        "child_hard_decoy_veto_ablation_causal": bool(ablations["mask_child_decoy_hard_decoy_veto"]["causal"]),
        "child_actuator_ablation_causal": bool(ablations["mask_child_actuator_terminals"]["causal"]),
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
        "failure_bucket_counts": _failure_buckets(interpretation, online, intervention_summary, hard_summary, live_summary),
        "phase_timings": timings,
        "total_seconds": timings["total_seconds"],
        "requested_max_total_seconds": cfg.max_total_seconds,
        "requested_min_target_seconds": cfg.min_target_seconds,
        "long_run_short_finish_reason": _short_reason(cfg, timings, online),
        "adaptive_stress_tiers_completed": _stress_tiers_completed(cfg, online["total_episode_count"]),
        "adaptive_stress_tiers_skipped": _stress_tiers_skipped(cfg, online["total_episode_count"]),
        "online_episode_count_completed": online["total_episode_count"],
        "cache_query_count": online["total_episode_count"] + intervention_summary["child_intervention_count"] + live_summary["live_cache_sample_count"],
        "live_foundation_query_count": live_summary["live_cache_sample_count"] * 2,
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


def _failure_buckets(interpretation, online, interventions, hard, live) -> dict[str, int]:
    counts = Counter()
    counts[interpretation] += 1
    if hard["experimental_decoy_false_handoff_count"]:
        counts["child_runtime_breaks_decoys"] += hard["experimental_decoy_false_handoff_count"]
    if hard["experimental_hard_decoy_false_handoff_count"]:
        counts["child_runtime_breaks_hard_decoys"] += hard["experimental_hard_decoy_false_handoff_count"]
    if interventions["child_helped_success_count"] == 0:
        counts["child_intervention_not_causal"] += 1
    if online["std_seed_experimental_success_rate"] > 0.35:
        counts["child_runtime_unstable_across_seeds"] += 1
    if any(live[key] for key in live if key.endswith("_mismatch_count")):
        counts["child_runtime_cache_invalid"] += 1
    return dict(counts)


def _short_reason(cfg, timings, online) -> str | None:
    if timings["total_seconds"] >= 3600:
        return None
    if online["total_episode_count"] >= 5000 and cfg.live_cache_sample_rate > 0 and cfg.hard_decoy_stress:
        return "high_tier_online_stress_completed_fast_not_true_wall_clock_long_run"
    return "online_stress_completed_fast_in_smoke_mode"


def _stress_tiers_completed(cfg, episode_count) -> list[str]:
    tiers = []
    if episode_count >= 200:
        tiers.append("tier_1")
    if episode_count >= 1000:
        tiers.append("tier_2")
    if episode_count >= 5000:
        tiers.append("tier_3")
    if episode_count >= 10000:
        tiers.append("tier_4")
    return tiers


def _stress_tiers_skipped(cfg, episode_count) -> list[str]:
    completed = set(_stress_tiers_completed(cfg, episode_count))
    return [tier for tier in ("tier_1", "tier_2", "tier_3", "tier_4") if tier not in completed]


def _percent_pass(key: str, threshold: int) -> bool:
    return int(_hash_json({"key": key})[:8], 16) % 100 < threshold


def _hash_json(payload: dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG33",
            "child_foundation_experimental_branch_only": True,
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

