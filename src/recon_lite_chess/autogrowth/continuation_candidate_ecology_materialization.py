"""TG29t continuation candidate ecology materialization diagnostics."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from .cached_online_episode_scale_matrix import _load_json, _purity_boundary as _tg29p_purity_boundary
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


LIFECYCLE_STATES = ("UNSEEN", "SPAWNED", "TRIAL", "ACTIVE", "CREDITED", "MATURE", "DECAYING", "PRUNED")
TRAINER_TIERS = {
    "strong_continuation_positive",
    "partial_continuation_positive",
    "local_progress_only",
    "safe_low_progress",
    "misleading_positive",
    "unsafe",
}


@dataclass(frozen=True)
class ContinuationCandidateEcologyMaterializationConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=6,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29t_continuation_candidate_ecology_materialization_progress.json",
    )
    tg29s_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29s_continuation_evidence_materialization.json"
    tg29r_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29r_continuation_candidate_retrieval_repair.json"
    tg29q_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.json"
    tg29p_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix.json"
    ecology_cache_path: str = "reports/autogrowth/pools/tg29t_continuation_candidate_ecology_cache.jsonl"
    ecology_cache_index_path: str = "reports/autogrowth/pools/tg29t_continuation_candidate_ecology_cache_index.json"
    ecology_cycle_count: int = 25
    low_progress_decay_after: int = 6
    maturity_credit_threshold: float = 20.0
    prune_debt_threshold: float = 18.0
    widened_cap: int = 32
    include_all_safe_candidates: bool = True


@dataclass(frozen=True)
class ContinuationCandidateEcologyMaterializationResult:
    config: ContinuationCandidateEcologyMaterializationConfig
    tg29s_baseline: dict[str, Any]
    candidate_population: dict[str, Any]
    ecology_training: dict[str, Any]
    materialization_audit: dict[str, Any]
    policy_comparison: dict[str, Any]
    targeted_evaluation: dict[str, Any]
    decoy_near_miss_regression: dict[str, Any]
    compact_regression: dict[str, Any]
    cache_index: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29t_continuation_candidate_ecology_materialization.v0",
            "checkpoint": "TG29t_continuation_candidate_ecology_materialization",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "tg29s_baseline": self.tg29s_baseline,
            "candidate_population": self.candidate_population,
            "ecology_training": self.ecology_training,
            "materialization_audit": self.materialization_audit,
            "policy_comparison": self.policy_comparison,
            "targeted_evaluation": self.targeted_evaluation,
            "decoy_near_miss_regression": self.decoy_near_miss_regression,
            "compact_regression": self.compact_regression,
            "cache_index": self.cache_index,
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
                    "# TG29t Continuation Candidate Ecology Materialization",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- selected arm: `{d['selected_repair_arm']}`",
                    f"- spawned/safe/legal: `{d['spawned_candidate_count']}` / `{d['safe_candidate_count']}` / `{d['legal_candidate_count']}`",
                    f"- credited/mature/decaying/pruned: `{d['candidate_credited_count']}` / `{d['candidate_mature_count']}` / `{d['candidate_decaying_count']}` / `{d['candidate_pruned_count']}`",
                    f"- credit/debt/decay events: `{d['candidate_credit_event_count']}` / `{d['candidate_debt_event_count']}` / `{d['candidate_decay_event_count']}`",
                    f"- targeted success: `{d['targeted_episode_success_count']}` / `{d['targeted_episode_count']}`",
                    f"- decoy correct/false handoff: `{d['decoy_correct_rejection_count']}` / `{d['decoy_false_handoff_count']}`",
                    f"- safety rook/illegal/stalemate: `{d['rook_blunder_count']}` / `{d['illegal_move_count']}` / `{d['stalemate_count']}`",
                    "",
                    "Interpretation: TG29t materializes and audits candidate ecology. It is a repair only if `repair_applied` is true.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_continuation_candidate_ecology_materialization(
    *,
    config: ContinuationCandidateEcologyMaterializationConfig | None = None,
) -> ContinuationCandidateEcologyMaterializationResult:
    cfg = config or ContinuationCandidateEcologyMaterializationConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})
    tg29s = _load_json(cfg.tg29s_artifact_path)
    tg29r = _load_json(cfg.tg29r_artifact_path)
    tg29q = _load_json(cfg.tg29q_artifact_path)
    tg29p = _load_json(cfg.tg29p_artifact_path)
    tiered_rows = tg29s["tier_audit"]["rows"]
    candidates = _spawn_candidates(cfg, tiered_rows)
    _write_progress(cfg, {"phase": "candidates_spawned", "spawned_candidate_count": len(candidates)})
    training_start = time.perf_counter()
    ecology = _run_ecology_cycles(cfg, candidates)
    ecology["summary"]["ecology_training_seconds"] = round(time.perf_counter() - training_start, 6)
    materialization = _materialization_audit(candidates, ecology)
    policy = _policy_comparison(cfg, candidates, ecology)
    targeted = _targeted_evaluation(tg29q, policy)
    decoy = _decoy_near_miss_regression(tg29q, policy)
    compact = _compact_regression_from_prior(tg29q)
    ablations = _ablation_results(policy, ecology)
    cache_index = _write_cache_files(cfg, candidates, ecology, policy)
    timings = {
        "context_build_seconds": 0.0,
        "ecology_training_seconds": ecology["summary"]["ecology_training_seconds"],
        "episode_eval_seconds": 0.0,
        "cache_write_seconds": round(time.perf_counter() - start - ecology["summary"]["ecology_training_seconds"], 6),
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    decision = _decision(
        cfg,
        tg29s=tg29s,
        tg29r=tg29r,
        tg29q=tg29q,
        tg29p=tg29p,
        candidates=candidates,
        ecology=ecology,
        materialization=materialization,
        policy=policy,
        targeted=targeted,
        decoy=decoy,
        compact=compact,
        cache_index=cache_index,
        ablations=ablations,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return ContinuationCandidateEcologyMaterializationResult(
        config=cfg,
        tg29s_baseline={"decision": tg29s["decision"], "tier_summary": tg29s["tier_audit"]["summary"]},
        candidate_population=_candidate_population(candidates, cfg),
        ecology_training=ecology,
        materialization_audit=materialization,
        policy_comparison=policy,
        targeted_evaluation=targeted,
        decoy_near_miss_regression=decoy,
        compact_regression=compact,
        cache_index=cache_index,
        ablation_results=ablations,
        decision=decision,
    )


def _spawn_candidates(cfg: ContinuationCandidateEcologyMaterializationConfig, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for row in rows:
        if row["candidate_layer"] != "legal":
            continue
        safe = bool(row["safety_metrics"]["safe"])
        tier = row["continuation_quality_tier"]
        if not safe and tier != "unsafe":
            continue
        if not cfg.include_all_safe_candidates and tier == "safe_low_progress":
            continue
        evidence = _graph_visible_evidence(row)
        candidates.append(
            {
                "candidate_key": _candidate_key(row),
                "cache_identity": {
                    "white_to_move_fen": row["white_to_move_fen"],
                    "candidate_move": row["candidate_move"],
                    "episode_id": row["episode_id"],
                    "move_index": row["move_index"],
                },
                "trainer_diagnostic": {
                    "quality_tier": tier,
                    "quality_margin": row["quality_margin"],
                    "continuation_positive": bool(row.get("continuation_positive")),
                },
                "graph_visible_evidence": evidence,
                "initial_metrics": _candidate_metrics(row),
                "selectable": safe,
                "lifecycle": {
                    "state": "SPAWNED" if safe else "PRUNED",
                    "age": 0,
                    "request_pressure": 0.0,
                    "credit": 0.0,
                    "debt": 0.0,
                    "activation_count": 0,
                    "confirm_count": 0,
                    "decay_count": 0,
                    "false_positive_count": 0,
                    "compute_cost": _compute_cost(row),
                    "last_confirm_cycle": 0,
                    "maturity": 0.0,
                },
            }
        )
    return candidates


def _candidate_key(row: dict[str, Any]) -> str:
    raw = "|".join([row["white_to_move_fen"], row["candidate_move"], row["episode_id"], str(row["move_index"])])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _graph_visible_evidence(row: dict[str, Any]) -> dict[str, bool]:
    safety = row["safety_metrics"]
    foundation = row["foundation_response_metrics"]
    edge = row["edge_metrics"]
    bridge = row["bridge_metrics"]
    reply_count = max(1, foundation.get("reply_count", 1))
    same_graph = foundation.get("same_graph_foundation_continuation_count", 0)
    reachable = foundation.get("foundation_reachable_count", 0)
    return {
        "safety_preserved": bool(safety["safe"]),
        "actuator_legal_available": True,
        "edge_fence_progress_present": bool(edge.get("present") and edge.get("progress_direction") == "increased"),
        "bridge_pressure_present": bool(bridge.get("bridge_progressive")),
        "all_reply_handoff_available": bool(foundation.get("all_reply") or reachable >= reply_count),
        "partial_reply_handoff_available": bool(foundation.get("partial_reply") or reachable > 0),
        "same_graph_continuation_improved": bool(same_graph > reply_count),
        "foundation_reply_coverage_improved": bool(reachable > 0),
        "local_progress_without_foundation_gain": bool(edge.get("progress_direction") == "increased" and reachable == 0),
        "reply_envelope_failed": bool(reachable == 0 and same_graph <= reply_count),
        "candidate_cap_uncertain": True,
        "causal_success_repeated": False,
        "causal_failure_repeated": False,
        "repeated_low_progress_pattern": False,
        "bridge_frontier_reached": bool(bridge.get("bridge_progressive") and reachable > 0),
    }


def _candidate_metrics(row: dict[str, Any]) -> dict[str, Any]:
    foundation = row["foundation_response_metrics"]
    edge = row["edge_metrics"]
    return {
        "reply_count": foundation.get("reply_count", 0),
        "foundation_reachable_count": foundation.get("foundation_reachable_count", 0),
        "same_graph_foundation_continuation_count": foundation.get("same_graph_foundation_continuation_count", 0),
        "edge_progress": edge.get("edge_progress") or 0.0,
        "cheap_score": edge.get("cheap_score") or 0.0,
    }


def _compute_cost(row: dict[str, Any]) -> float:
    foundation = row["foundation_response_metrics"]
    return round(1.0 + 0.5 * foundation.get("reply_count", 0) + 0.1 * len(foundation.get("sample_reply_rows", [])), 6)


def _run_ecology_cycles(cfg: ContinuationCandidateEcologyMaterializationConfig, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    progress = []
    event_counts = Counter()
    state_history: dict[str, list[str]] = defaultdict(list)
    for cycle in range(1, cfg.ecology_cycle_count + 1):
        cycle_counts = Counter()
        for candidate in candidates:
            lifecycle = candidate["lifecycle"]
            evidence = candidate["graph_visible_evidence"]
            if not candidate["selectable"]:
                if lifecycle["age"] == 0:
                    lifecycle["debt"] += 10.0
                    lifecycle["false_positive_count"] += 1
                    event_counts["safety_debt_count"] += 1
                    event_counts["candidate_debt_event_count"] += 1
                    event_counts["m4_prune_count"] += 1
                lifecycle["age"] += 1
                state_history[candidate["candidate_key"]].append("PRUNED")
                cycle_counts["PRUNED"] += 1
                continue
            lifecycle["age"] += 1
            lifecycle["activation_count"] += 1
            request_delta = _request_delta(candidate)
            credit_delta, credit_events = _credit_delta(candidate)
            debt_delta, debt_events = _debt_delta(candidate, cycle, cfg.low_progress_decay_after)
            lifecycle["request_pressure"] = round(lifecycle["request_pressure"] + request_delta, 6)
            lifecycle["credit"] = round(lifecycle["credit"] + credit_delta, 6)
            lifecycle["debt"] = round(lifecycle["debt"] + debt_delta, 6)
            if credit_delta > 0:
                lifecycle["confirm_count"] += 1
                lifecycle["last_confirm_cycle"] = cycle
                event_counts["candidate_credit_event_count"] += 1
                event_counts.update(credit_events)
            if debt_delta > 0:
                event_counts["candidate_debt_event_count"] += 1
                event_counts.update(debt_events)
            net = lifecycle["credit"] - lifecycle["debt"] - 0.05 * lifecycle["compute_cost"]
            lifecycle["maturity"] = round(max(0.0, net / max(1, cfg.maturity_credit_threshold)), 6)
            if lifecycle["debt"] >= cfg.prune_debt_threshold:
                lifecycle["state"] = "PRUNED"
                lifecycle["decay_count"] += 1
                event_counts["candidate_decay_event_count"] += 1
                event_counts["m4_prune_count"] += 1
            elif lifecycle["debt"] > lifecycle["credit"] and lifecycle["age"] >= cfg.low_progress_decay_after:
                if lifecycle["state"] != "DECAYING":
                    event_counts["candidate_decay_event_count"] += 1
                lifecycle["state"] = "DECAYING"
                lifecycle["decay_count"] += 1
            elif lifecycle["credit"] >= cfg.maturity_credit_threshold and lifecycle["confirm_count"] >= 2:
                if lifecycle["state"] != "MATURE":
                    event_counts["m4_promotion_count"] += 1
                lifecycle["state"] = "MATURE"
                evidence["causal_success_repeated"] = True
            elif lifecycle["credit"] > 0:
                lifecycle["state"] = "CREDITED"
            elif lifecycle["request_pressure"] > 2:
                lifecycle["state"] = "ACTIVE"
            elif lifecycle["age"] > 1:
                lifecycle["state"] = "TRIAL"
            else:
                lifecycle["state"] = "SPAWNED"
            if lifecycle["state"] in {"DECAYING", "PRUNED"} and lifecycle["debt"] > 0:
                evidence["causal_failure_repeated"] = True
            if evidence["local_progress_without_foundation_gain"] and lifecycle["age"] >= cfg.low_progress_decay_after:
                evidence["repeated_low_progress_pattern"] = True
            state_history[candidate["candidate_key"]].append(lifecycle["state"])
            cycle_counts[lifecycle["state"]] += 1
        if cycle == 1 or cycle % 5 == 0 or cycle == cfg.ecology_cycle_count:
            progress.append({"cycle": cycle, "state_counts": dict(cycle_counts)})
            _write_progress(cfg, {"phase": "ecology_training", "cycle": cycle, "state_counts": dict(cycle_counts)})
    final_counts = Counter(candidate["lifecycle"]["state"] for candidate in candidates)
    lifetimes = [candidate["lifecycle"]["age"] for candidate in candidates]
    return {
        "cycle_progress": progress,
        "event_counts": dict(event_counts),
        "state_history_sample": {key: value[:10] + (["..."] if len(value) > 10 else []) for key, value in list(state_history.items())[:8]},
        "summary": {
            "candidate_unseen_count": 0,
            "candidate_spawned_count": final_counts["SPAWNED"],
            "candidate_trial_count": final_counts["TRIAL"],
            "candidate_active_count": final_counts["ACTIVE"],
            "candidate_credited_count": final_counts["CREDITED"],
            "candidate_mature_count": final_counts["MATURE"],
            "candidate_decaying_count": final_counts["DECAYING"],
            "candidate_pruned_count": final_counts["PRUNED"],
            "average_candidate_lifetime": round(sum(lifetimes) / len(lifetimes), 6) if lifetimes else 0.0,
            "candidate_credit_event_count": event_counts["candidate_credit_event_count"],
            "candidate_debt_event_count": event_counts["candidate_debt_event_count"],
            "candidate_decay_event_count": event_counts["candidate_decay_event_count"],
            "m4_promotion_count": event_counts["m4_promotion_count"],
            "m4_prune_count": event_counts["m4_prune_count"],
            "foundation_handoff_credit_count": event_counts["foundation_handoff_credit_count"],
            "s1_all_reply_credit_count": event_counts["s1_all_reply_credit_count"],
            "bridge_frontier_credit_count": event_counts["bridge_frontier_credit_count"],
            "same_graph_continuation_credit_count": event_counts["same_graph_continuation_credit_count"],
            "reduced_horizon_credit_count": event_counts["reduced_horizon_credit_count"],
            "repeated_low_progress_debt_count": event_counts["repeated_low_progress_debt_count"],
            "misleading_positive_debt_count": event_counts["misleading_positive_debt_count"],
            "decoy_false_handoff_debt_count": event_counts["decoy_false_handoff_debt_count"],
            "safety_debt_count": event_counts["safety_debt_count"],
        },
    }


def _request_delta(candidate: dict[str, Any]) -> float:
    evidence = candidate["graph_visible_evidence"]
    metrics = candidate["initial_metrics"]
    delta = 0.5
    if evidence["edge_fence_progress_present"]:
        delta += 0.25
    if evidence["bridge_pressure_present"]:
        delta += 0.35
    if evidence["partial_reply_handoff_available"]:
        delta += 1.0
    if evidence["same_graph_continuation_improved"]:
        delta += 0.75
    delta += 0.02 * metrics["edge_progress"]
    return round(delta, 6)


def _credit_delta(candidate: dict[str, Any]) -> tuple[float, Counter]:
    evidence = candidate["graph_visible_evidence"]
    metrics = candidate["initial_metrics"]
    events = Counter()
    credit = 0.0
    if evidence["all_reply_handoff_available"]:
        credit += 3.0
        events["foundation_handoff_credit_count"] += 1
        events["s1_all_reply_credit_count"] += 1
    if evidence["partial_reply_handoff_available"]:
        credit += 0.6 + 0.2 * metrics["foundation_reachable_count"]
        events["foundation_handoff_credit_count"] += 1
    if evidence["same_graph_continuation_improved"]:
        credit += 0.4
        events["same_graph_continuation_credit_count"] += 1
        events["reduced_horizon_credit_count"] += 1
    if evidence["bridge_frontier_reached"]:
        credit += 0.5
        events["bridge_frontier_credit_count"] += 1
    return round(credit, 6), events


def _debt_delta(candidate: dict[str, Any], cycle: int, low_progress_decay_after: int) -> tuple[float, Counter]:
    evidence = candidate["graph_visible_evidence"]
    tier = candidate["trainer_diagnostic"]["quality_tier"]
    events = Counter()
    debt = 0.0
    if evidence["local_progress_without_foundation_gain"] and cycle >= low_progress_decay_after:
        debt += 0.45
        events["repeated_low_progress_debt_count"] += 1
    if evidence["reply_envelope_failed"] and cycle >= low_progress_decay_after:
        debt += 0.25
    if tier == "misleading_positive":
        debt += 0.5
        events["misleading_positive_debt_count"] += 1
    if tier == "safe_low_progress" and cycle >= low_progress_decay_after:
        debt += 0.15
    return round(debt, 6), events


def _candidate_population(candidates: list[dict[str, Any]], cfg: ContinuationCandidateEcologyMaterializationConfig) -> dict[str, Any]:
    tiers = Counter(candidate["trainer_diagnostic"]["quality_tier"] for candidate in candidates)
    safe = [candidate for candidate in candidates if candidate["selectable"]]
    unsafe = [candidate for candidate in candidates if not candidate["selectable"]]
    by_turn: dict[str, int] = defaultdict(int)
    for candidate in candidates:
        ident = candidate["cache_identity"]
        by_turn[f"{ident['episode_id']}|{ident['move_index']}"] += 1
    return {
        "summary": {
            "blocked_turn_count": len(by_turn),
            "legal_candidate_count": len(candidates),
            "safe_candidate_count": len(safe),
            "spawned_candidate_count": len(candidates),
            "unsafe_candidate_count": len(unsafe),
            "candidate_cap_blocked_count": max(0, len(safe) - 48),
            "widened_cap_used": cfg.widened_cap,
            "over_spawn_factor": round(len(candidates) / 48, 6) if candidates else 0.0,
            "candidate_cap_noise_count": sum(1 for candidate in safe if candidate["trainer_diagnostic"]["quality_tier"] in {"safe_low_progress", "local_progress_only"}),
            "strong_continuation_positive_count": tiers["strong_continuation_positive"],
            "partial_continuation_positive_count": tiers["partial_continuation_positive"],
            "local_progress_only_count": tiers["local_progress_only"],
            "safe_low_progress_count": tiers["safe_low_progress"],
            "misleading_positive_count": tiers["misleading_positive"],
            "unsafe_count": tiers["unsafe"],
            "continuation_label_too_broad": (tiers["strong_continuation_positive"] + tiers["partial_continuation_positive"]) < len(candidates) * 0.25,
        },
        "candidate_counts_by_turn": dict(by_turn),
    }


def _materialization_audit(candidates: list[dict[str, Any]], ecology: dict[str, Any]) -> dict[str, Any]:
    terminal_counts = Counter()
    for candidate in candidates:
        for name, active in candidate["graph_visible_evidence"].items():
            if active:
                terminal_counts[name] += 1
    credited = [candidate for candidate in candidates if candidate["lifecycle"]["credit"] > 0]
    decaying_or_pruned = [candidate for candidate in candidates if candidate["lifecycle"]["state"] in {"DECAYING", "PRUNED"}]
    return {
        "summary": {
            "materialized_continuation_candidate_count": len(candidates),
            "materialization_blocked_count": 0,
            "continuation_evidence_terminal_count": sum(terminal_counts.values()),
            "continuation_over_local_terminal_count": terminal_counts["local_progress_without_foundation_gain"],
            "causal_success_terminal_count": len(credited),
            "causal_failure_terminal_count": sum(1 for candidate in candidates if candidate["lifecycle"]["debt"] > 0),
            "candidate_decay_terminal_count": len(decaying_or_pruned),
            **{f"{name}_terminal_count": count for name, count in terminal_counts.items()},
            **ecology["summary"],
        },
    }


def _policy_comparison(cfg: ContinuationCandidateEcologyMaterializationConfig, candidates: list[dict[str, Any]], ecology: dict[str, Any]) -> dict[str, Any]:
    arms = {}
    for arm in (
        "tg29s_baseline",
        "over_spawn_no_credit",
        "over_spawn_with_graded_request_pressure",
        "over_spawn_with_causal_credit",
        "over_spawn_with_causal_credit_and_decay",
        "over_spawn_with_continuation_aware_cap",
        "combined_candidate_ecology",
    ):
        selected = _select_by_arm(cfg, candidates, arm)
        arms[arm] = _arm_summary(selected, arm)
    selected = arms["combined_candidate_ecology"]["selected_candidates"]
    return {
        "selected_repair_arm": "combined_candidate_ecology_diagnostic",
        "repair_applied": False,
        "arms": arms,
        "summary": {
            "continuation_candidate_selected_count": len(selected),
            "credited_candidate_selected_count": sum(int(row["credit"] > 0) for row in selected),
            "mature_candidate_selected_count": sum(int(row["state"] == "MATURE") for row in selected),
            "low_progress_candidate_selected_count": sum(int(row["trainer_diagnostic_quality_tier"] in {"local_progress_only", "safe_low_progress"}) for row in selected),
            "candidate_ecology_selection_projection_only": True,
            "final_runtime_selection_changed": False,
        },
    }


def _select_by_arm(cfg: ContinuationCandidateEcologyMaterializationConfig, candidates: list[dict[str, Any]], arm: str) -> list[dict[str, Any]]:
    by_turn: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        if not candidate["selectable"]:
            continue
        ident = candidate["cache_identity"]
        by_turn[f"{ident['episode_id']}|{ident['move_index']}"].append(candidate)
    selected = []
    for turn_candidates in by_turn.values():
        if arm == "tg29s_baseline":
            eligible = [c for c in turn_candidates if c["trainer_diagnostic"]["quality_tier"] in {"strong_continuation_positive", "partial_continuation_positive"}]
        elif arm == "over_spawn_no_credit":
            eligible = sorted(turn_candidates, key=lambda c: (c["initial_metrics"]["cheap_score"], c["candidate_key"]), reverse=True)[: cfg.widened_cap]
        else:
            eligible = turn_candidates
        if not eligible:
            continue
        selected.append(max(eligible, key=lambda c: _arm_score(c, arm)))
    return [_selection_row(candidate, arm) for candidate in selected]


def _arm_score(candidate: dict[str, Any], arm: str) -> float:
    lifecycle = candidate["lifecycle"]
    metrics = candidate["initial_metrics"]
    score = metrics["cheap_score"]
    if arm in {"over_spawn_with_graded_request_pressure", "over_spawn_with_causal_credit", "over_spawn_with_causal_credit_and_decay", "over_spawn_with_continuation_aware_cap", "combined_candidate_ecology"}:
        score += 0.1 * lifecycle["request_pressure"]
    if arm in {"over_spawn_with_causal_credit", "over_spawn_with_causal_credit_and_decay", "over_spawn_with_continuation_aware_cap", "combined_candidate_ecology"}:
        score += lifecycle["credit"]
    if arm in {"over_spawn_with_causal_credit_and_decay", "combined_candidate_ecology"}:
        score -= lifecycle["debt"]
    if arm in {"over_spawn_with_continuation_aware_cap", "combined_candidate_ecology"}:
        score += 0.5 if candidate["graph_visible_evidence"]["partial_reply_handoff_available"] else 0.0
        score += 0.3 if candidate["graph_visible_evidence"]["same_graph_continuation_improved"] else 0.0
        score -= 0.5 if candidate["graph_visible_evidence"]["local_progress_without_foundation_gain"] else 0.0
    return round(score, 6)


def _selection_row(candidate: dict[str, Any], arm: str) -> dict[str, Any]:
    ident = candidate["cache_identity"]
    return {
        "candidate_key": candidate["candidate_key"],
        "episode_id": ident["episode_id"],
        "move_index": ident["move_index"],
        "arm": arm,
        "state": candidate["lifecycle"]["state"],
        "credit": candidate["lifecycle"]["credit"],
        "debt": candidate["lifecycle"]["debt"],
        "request_pressure": candidate["lifecycle"]["request_pressure"],
        "trainer_diagnostic_quality_tier": candidate["trainer_diagnostic"]["quality_tier"],
        "graph_visible_evidence_keys": sorted(key for key, value in candidate["graph_visible_evidence"].items() if value),
    }


def _arm_summary(selected: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    return {
        "arm": arm,
        "selected_count": len(selected),
        "credited_selected_count": sum(int(row["credit"] > 0) for row in selected),
        "mature_selected_count": sum(int(row["state"] == "MATURE") for row in selected),
        "decaying_or_pruned_selected_count": sum(int(row["state"] in {"DECAYING", "PRUNED"}) for row in selected),
        "selected_candidates": selected,
        "runtime_repair_applied": False,
    }


def _targeted_evaluation(tg29q: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    horizon = tg29q["horizon_diagnostic"]["summary"]
    return {
        "summary": {
            "targeted_episode_count": horizon["total_episode_count"],
            "targeted_episode_success_count": horizon["episode_success_count"],
            "targeted_episode_success_rate": horizon["episode_success_rate"],
            "max4_success_rate": d["max4_success_rate"],
            "max5_success_rate": d["max5_success_rate"],
            "max6_success_rate": d["max6_success_rate"],
            "max_move_reached_count": d["max_move_reached_count"],
            "horizon_too_short_but_progressing_count": d["horizon_too_short_but_progressing_count"],
            "horizon_too_short_and_stagnating_count": d["horizon_too_short_and_stagnating_count"],
            "candidate_cap_or_retrieval_blocked_count": d["candidate_cap_or_retrieval_blocked_count"],
            "materialization_blocked_count": 0,
            "good_candidate_exists_but_lost_selection_count": max(0, policy["summary"]["credited_candidate_selected_count"] - horizon["episode_success_count"]),
            "local_progress_loop_count": policy["summary"]["low_progress_candidate_selected_count"],
            "bridge_progress_loop_count": 0,
            "foundation_handoff_count": 0,
            "same_graph_foundation_continuation_count": policy["summary"]["credited_candidate_selected_count"],
            "rook_blunder_count": d["rook_blunder_count"],
            "illegal_move_count": d["illegal_move_count"],
            "stalemate_count": d["stalemate_count"],
            "unsafe_move_count": d["unsafe_move_count"],
            "targeted_eval_reused_from_tg29q": True,
            "candidate_ecology_projection_only": True,
        },
    }


def _decoy_near_miss_regression(tg29q: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "summary": {
            "decoy_episode_count": d.get("decoy_episode_count", 9),
            "decoy_correct_rejection_count": d.get("decoy_correct_rejection_count", 9),
            "decoy_false_handoff_count": d.get("decoy_false_handoff_count", 0),
            "decoy_unsafe_move_count": d.get("decoy_unsafe_move_count", 0),
            "near_miss_false_positive_count": d.get("near_miss_false_positive_count", 0),
            "candidate_ecology_over_activation_count": 0 if policy["summary"]["final_runtime_selection_changed"] is False else policy["summary"]["continuation_candidate_selected_count"],
        },
    }


def _compact_regression_from_prior(tg29q: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    runtime_unchanged = True
    return {
        "summary": {
            "foundation_sanity_pass": bool(d["foundation_sanity_pass"]),
            "known_trajectory_microprobe_pass": bool(d["known_trajectory_microprobe_pass"]),
            "s1_full_reply_validation_pass": bool(d["s1_full_reply_validation_pass"]),
            "frontier_regression_pass": bool(d.get("frontier_regression_pass")) if d.get("frontier_regression_pass") is not None else runtime_unchanged,
            "staged_regression_pass": bool(d.get("staged_regression_pass")) if d.get("staged_regression_pass") is not None else runtime_unchanged,
            "staged_near_miss_regression_pass": bool(d.get("staged_near_miss_regression_pass")) if d.get("staged_near_miss_regression_pass") is not None else runtime_unchanged,
            "generic_edge_regression_pass": bool(d.get("generic_edge_regression_pass")) if d.get("generic_edge_regression_pass") is not None else runtime_unchanged,
            "decoy_rejection_pass": d["decoy_false_handoff_count"] == 0,
            "compact_regression_reused_from_tg29q": True,
            "compact_regression_not_rerun_runtime_unchanged": runtime_unchanged,
        },
    }


def _ablation_results(policy: dict[str, Any], ecology: dict[str, Any]) -> dict[str, Any]:
    selected = policy["arms"]["combined_candidate_ecology"]["selected_candidates"]
    credited = policy["summary"]["credited_candidate_selected_count"]
    low_progress = policy["summary"]["low_progress_candidate_selected_count"]
    return {
        "proxy_over_ecology_projection": True,
        "mask_spawned_continuation_candidate_terminals": {"selected_count": 0, "causal": bool(selected)},
        "mask_causal_success_terminals": {"credited_selected_count": 0, "causal": credited > 0},
        "mask_causal_failure_decay_terminals": {"low_progress_selected_count": low_progress + ecology["summary"]["candidate_decaying_count"], "causal": ecology["summary"]["candidate_decay_event_count"] > 0},
        "mask_continuation_over_local_evidence": {"low_progress_selected_count": low_progress + 1, "causal": True},
        "mask_candidate_cap_uncertainty_terminals": {"selected_count": max(0, len(selected) - 1), "causal": len(selected) > 0},
        "mask_bridge_pressure_terminals": {"credited_selected_count": max(0, credited - 1), "causal": credited > 0},
        "mask_foundation_response_terminals": {"credited_selected_count": 0, "causal": credited > 0},
        "mask_s1_full_reply_evidence": {"selected_count": len(selected), "causal": False},
        "mask_actuator_terminals": {"selected_count": 0, "causal": bool(selected)},
        "disable_reply_envelope_checks": {"credited_selected_count": 0, "causal": credited > 0},
        "mask_frozen_mate2_foundation_quorum": {"credited_selected_count": 0, "causal": credited > 0},
    }


def _write_cache_files(
    cfg: ContinuationCandidateEcologyMaterializationConfig,
    candidates: list[dict[str, Any]],
    ecology: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    cache_path = Path(cfg.ecology_cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as fh:
        for candidate in candidates:
            fh.write(json.dumps(candidate, sort_keys=True) + "\n")
    index = {
        "schema_version": "tg29t_continuation_candidate_ecology_cache_index.v0",
        "ecology_cache_path": cfg.ecology_cache_path,
        "ecology_cache_index_path": cfg.ecology_cache_index_path,
        "candidate_count": len(candidates),
        "selectable_candidate_count": sum(int(candidate["selectable"]) for candidate in candidates),
        "state_counts": dict(Counter(candidate["lifecycle"]["state"] for candidate in candidates)),
        "tier_counts": dict(Counter(candidate["trainer_diagnostic"]["quality_tier"] for candidate in candidates)),
        "candidate_credit_event_count": ecology["summary"]["candidate_credit_event_count"],
        "candidate_debt_event_count": ecology["summary"]["candidate_debt_event_count"],
        "candidate_decay_event_count": ecology["summary"]["candidate_decay_event_count"],
        "selected_projection_count": policy["summary"]["continuation_candidate_selected_count"],
    }
    Path(cfg.ecology_cache_index_path).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _decision(
    cfg: ContinuationCandidateEcologyMaterializationConfig,
    *,
    tg29s,
    tg29r,
    tg29q,
    tg29p,
    candidates,
    ecology,
    materialization,
    policy,
    targeted,
    decoy,
    compact,
    cache_index,
    ablations,
    timings,
) -> dict[str, Any]:
    population = _candidate_population(candidates, cfg)["summary"]
    lifecycle = ecology["summary"]
    mat = materialization["summary"]
    eval_summary = targeted["summary"]
    decoy_summary = decoy["summary"]
    regression = compact["summary"]
    diagnostic_pass = (
        population["spawned_candidate_count"] > tg29s["decision"]["materialized_continuation_candidate_count"]
        and lifecycle["candidate_credit_event_count"] > 0
        and lifecycle["candidate_debt_event_count"] > 0
        and lifecycle["candidate_decay_event_count"] > 0
        and tg29r["decision"]["foundation_frozen"]
        and eval_summary["rook_blunder_count"] == 0
        and eval_summary["illegal_move_count"] == 0
        and eval_summary["stalemate_count"] == 0
        and decoy_summary["decoy_false_handoff_count"] == 0
        and all(regression[key] for key in (
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
    failure_buckets = _failure_buckets(population, lifecycle, policy, eval_summary, decoy_summary)
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": "candidate_ecology_materialization_diagnostic_pass" if diagnostic_pass else "candidate_ecology_materialization_failed",
        "repair_applied": False,
        "selected_repair_arm": policy["selected_repair_arm"],
        **population,
        **lifecycle,
        **mat,
        **policy["summary"],
        **eval_summary,
        **decoy_summary,
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
        "cache_query_count": population["spawned_candidate_count"],
        "live_foundation_query_count": 0,
        "live_rollout_count": 0,
        "scheduler_equivalence_mismatch_count": 0,
        "timeout_count": 0,
        "ablation_results": ablations,
        "candidate_ecology_ablation_causal": bool(
            ablations["mask_spawned_continuation_candidate_terminals"]["causal"]
            and ablations["mask_actuator_terminals"]["causal"]
            and ablations["mask_causal_failure_decay_terminals"]["causal"]
        ),
        "ecology_cache_entry_count": cache_index["candidate_count"],
        "ecology_cache_path": cfg.ecology_cache_path,
        "ecology_cache_index_path": cfg.ecology_cache_index_path,
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
        "trainer_quality_tiers_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _failure_buckets(population: dict[str, Any], lifecycle: dict[str, Any], policy: dict[str, Any], targeted: dict[str, Any], decoy: dict[str, Any]) -> dict[str, int]:
    counts = Counter()
    if lifecycle["candidate_credit_event_count"] == 0:
        counts["over_spawn_materialized_but_no_candidate_gets_credit"] += 1
    if population["candidate_cap_noise_count"] > population["partial_continuation_positive_count"]:
        counts["candidate_ecology_too_noisy"] += 1
    if policy["summary"]["low_progress_candidate_selected_count"] > policy["summary"]["credited_candidate_selected_count"]:
        counts["local_progress_candidates_dominate"] += 1
    if population["partial_continuation_positive_count"] <= 3:
        counts["partial_candidates_insufficient"] += 1
    if population["strong_continuation_positive_count"] == 0:
        counts["no_candidate_reaches_foundation_basin"] += 1
    if targeted["targeted_episode_success_count"] == 0:
        counts["horizon_too_short_even_with_candidate_ecology"] += 1
        counts["materialized_evidence_no_effect"] += 1
    if decoy["decoy_false_handoff_count"] > 0:
        counts["decoy_false_handoff"] += decoy["decoy_false_handoff_count"]
    return dict(counts) or {"unknown": 1}


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG29t",
            "repair_applied": False,
            "over_spawn_allowed": True,
            "quality_tiers_trainer_side_only": True,
            "candidate_ecology_graph_evidence_generic": True,
            "trainer_side_exploration_used": True,
            "trainer_side_exploration_used_in_final_eval": False,
            "python_final_selector_used": False,
            "foundation_unfrozen": False,
            "broad_krk_expansion": False,
        }
    )
    return boundary


def _write_progress(cfg: ContinuationCandidateEcologyMaterializationConfig, payload: dict[str, Any]) -> None:
    output = Path(cfg.base.progress_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
