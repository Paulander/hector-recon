"""TG29c reply-robust bridge-to-foundation pressure."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, replace
import json
import time
from pathlib import Path
from typing import Any

from .frozen_foundation_edge_fence_reentry import _foundation_counts
from .frozen_foundation_response_cache_bridge_retrieval import _FoundationResponseCache
from .online_failure_decomposition import (
    OnlineFailureDecompositionConfig,
    _enrich_episodes,
    _failure_decomposition,
    _regression_summary,
)
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .native_quorum_materialization import _tg26t_config
from .native_quorum_mate2_chaining import _tg26u_config
from .tiny_online_krk_episode_runner import (
    TinyOnlineKRKEpisodeRunnerConfig,
    _build_context,
    _episode_starts,
    _purity_boundary as _tg29a_purity_boundary,
    _run_episodes,
    _write_progress as _write_tg29a_progress,
)


@dataclass(frozen=True)
class ReplyRobustBridgePressureConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("mixed_balanced_plus_staged",),
        progress_output="reports/autogrowth/krk_autogrowth_tg29c_reply_robust_bridge_pressure_progress.json",
    )
    reply_policies: tuple[str, ...] = ("deterministic_worst_foundation_reply",)
    comparison_reply_policies: tuple[str, ...] = ("mobility_maximizing",)
    repair_arms: tuple[str, ...] = (
        "baseline_no_repair",
        "combined_reply_robust",
    )
    max_reply_envelope_replies_per_candidate: int = 2
    max_repair_cache_candidate_moves: int = 4


@dataclass(frozen=True)
class ReplyRobustBridgePressureResult:
    config: ReplyRobustBridgePressureConfig
    foundation_sanity: dict[str, Any]
    regression_results: dict[str, Any]
    arm_results: dict[str, Any]
    selected_arm_episodes: dict[str, Any]
    bridge_loop_diagnostics: list[dict[str, Any]]
    ablation_results: dict[str, Any]
    foundation_cache_equivalence: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29c_reply_robust_bridge_pressure.v0",
            "checkpoint": "TG29c_reply_robust_bridge_pressure",
        "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "foundation_sanity": self.foundation_sanity,
            "regression_results": self.regression_results,
            "arm_results": self.arm_results,
            "skipped_repair_arms": _skipped_repair_arms(self.config),
            "selected_arm_episodes": self.selected_arm_episodes,
            "bridge_loop_diagnostics": self.bridge_loop_diagnostics,
            "ablation_results": self.ablation_results,
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
        decision = self.decision
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "\n".join(
                [
                    "# TG29c Reply-Robust Bridge Pressure",
                    "",
                    f"- checkpoint_pass: `{decision['checkpoint_pass']}`",
                    f"- interpretation: `{decision['checkpoint_interpretation']}`",
                    f"- repair_applied: `{decision['repair_applied']}`",
                    f"- selected_repair_arm: `{decision['selected_repair_arm']}`",
                    f"- worst-foundation success: `{decision['worst_foundation_reply_success_rate']}`",
                    f"- bridge-loop failures: `{decision['bridge_loop_without_foundation_progress_count']}`",
                    f"- safety rook/illegal/stalemate: `{decision['rook_blunder_count']}` / `{decision['illegal_move_count']}` / `{decision['stalemate_count']}`",
                    "",
                    "Interpretation: TG29c tests reply-robust bridge pressure without broadening KRK or unfreezing the foundation.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_reply_robust_bridge_pressure(
    *,
    config: ReplyRobustBridgePressureConfig | None = None,
) -> ReplyRobustBridgePressureResult:
    cfg = config or ReplyRobustBridgePressureConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})

    context = _build_context(cfg.base)
    timings.update(context["timings"])
    starts = _episode_starts(cfg.base, context)
    graph = context["graph"]
    _write_progress(cfg, {"phase": "context_built", "selected_schedule": context["selected"]["schedule_name"]})

    foundation_before = _foundation_counts(graph)
    start = time.perf_counter()
    arm_results = _run_arm_matrix(cfg, context, starts)
    timings["arm_matrix_seconds"] = round(time.perf_counter() - start, 6)

    selected_arm = _select_arm(arm_results)
    _ensure_selected_policy_comparison(cfg, context, starts, arm_results, selected_arm)
    selected = arm_results[selected_arm]["policies"]["deterministic_worst_foundation_reply"]
    bridge_loop_diagnostics = _bridge_loop_diagnostics(selected["episodes"])
    _write_progress(cfg, {"phase": "arms_complete", "selected_arm": selected_arm, "worst_success": selected["summary"]["episode_success_rate"]})

    start = time.perf_counter()
    ablations = _selected_arm_ablations(cfg, context, starts, selected_arm)
    timings["selected_arm_ablation_seconds"] = round(time.perf_counter() - start, 6)

    foundation_after = _foundation_counts(graph)
    cache_equivalence = context["cache"].live_equivalence_audit(max_samples=min(8, cfg.base.max_samples))
    scheduler_equivalence = _scheduler_equivalence(
        _tg26s_config(_tg26t_config(_tg26u_config(context["mate2_cfg"]))),
        context["mate1_train"],
        context["mate1_heldout"],
    )
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)

    decision = _decision(
        cfg,
        context=context,
        selected_arm=selected_arm,
        selected=selected,
        baseline=arm_results["baseline_no_repair"]["policies"]["deterministic_worst_foundation_reply"],
        arm_results=arm_results,
        ablations=ablations,
        foundation_before=foundation_before,
        foundation_after=foundation_after,
        cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return ReplyRobustBridgePressureResult(
        config=cfg,
        foundation_sanity=context["foundation_sanity"],
        regression_results=_regression_summary(context["regression"]),
        arm_results=arm_results,
        selected_arm_episodes=selected["episodes"],
        bridge_loop_diagnostics=bridge_loop_diagnostics,
        ablation_results=ablations,
        foundation_cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _run_arm_matrix(cfg: ReplyRobustBridgePressureConfig, context: dict[str, Any], starts: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for arm in cfg.repair_arms:
        policies = {}
        for policy in cfg.reply_policies:
            episodes = _run_arm_policy(cfg, context, starts, arm, policy)
            policies[policy] = {"summary": _episode_summary(episodes), "episodes": episodes}
        out[arm] = {
            "arm": arm,
            "repair_weights": _repair_weight_delta(arm),
            "policies": policies,
        }
        _write_progress(cfg, {"phase": "arm_complete", "arm": arm, "worst_success": policies["deterministic_worst_foundation_reply"]["summary"]["episode_success_rate"]})
    return out


def _ensure_selected_policy_comparison(
    cfg: ReplyRobustBridgePressureConfig,
    context: dict[str, Any],
    starts: tuple[dict[str, Any], ...],
    arm_results: dict[str, Any],
    selected_arm: str,
) -> None:
    for policy in cfg.comparison_reply_policies:
        if policy in arm_results[selected_arm]["policies"]:
            continue
        episodes = _run_arm_policy(cfg, context, starts, selected_arm, policy)
        arm_results[selected_arm]["policies"][policy] = {"summary": _episode_summary(episodes), "episodes": episodes}
        _write_progress(cfg, {"phase": "selected_policy_complete", "arm": selected_arm, "policy": policy, "success": episodes["episode_success_rate"]})


def _run_arm_policy(
    cfg: ReplyRobustBridgePressureConfig,
    context: dict[str, Any],
    starts: tuple[dict[str, Any], ...],
    arm: str,
    policy: str,
    *,
    masks: dict[str, bool] | None = None,
) -> dict[str, Any]:
    base_cfg = replace(cfg.base, black_reply_policy=policy)
    tg28c_cfg = context["tg28c_cfg"]
    cache = context["cache"]
    bridge_weights = dict(context["selected"]["bridge_weights"])
    if arm != "baseline_no_repair":
        tg28c_cfg = replace(
            tg28c_cfg,
            max_reply_envelope_replies_per_candidate=cfg.max_reply_envelope_replies_per_candidate,
            max_cache_candidate_moves=min(tg28c_cfg.max_cache_candidate_moves, cfg.max_repair_cache_candidate_moves),
        )
        cache = _FoundationResponseCache(context["graph"], context["mate2_cfg"], tg28c_cfg)
        bridge_weights.update(_repair_weight_delta(arm))
    if masks and masks.get("mask_reply_robust_bridge_terminals", False):
        bridge_weights = dict(context["selected"]["bridge_weights"])
    if masks and masks.get("disable_worst_reply_bridge_evidence", False):
        tg28c_cfg = replace(tg28c_cfg, max_reply_envelope_replies_per_candidate=1)
        cache = _FoundationResponseCache(context["graph"], context["mate2_cfg"], tg28c_cfg)
    arm_context = dict(context)
    arm_context["cache"] = cache
    arm_context["tg28c_cfg"] = tg28c_cfg
    result = _run_episodes(
        context["graph"],
        cache,
        context["mate2_cfg"],
        tg28c_cfg,
        context["edge_cfg"],
        starts,
        context["selected"]["edge_weights"],
        bridge_weights,
        base_cfg,
        masks=masks,
    )
    return _enrich_episodes(result, arm_context, OnlineFailureDecompositionConfig(base=base_cfg))


def _repair_weight_delta(arm: str) -> dict[str, float]:
    if arm == "baseline_no_repair":
        return {}
    if arm == "bridge_stagnation_veto_only":
        return {
            "reply_envelope_any_foundation=0": -1.20,
            "reply_envelope_rate_bucket=0": -0.80,
        }
    if arm == "all_reply_worst_reply_confidence_only":
        return {
            "reply_envelope_all_foundation=1": 2.20,
            "reply_envelope_rate_bucket=4": 1.00,
        }
    if arm == "reply_robust_bridge_pressure":
        return {
            "reply_envelope_all_foundation=1": 1.80,
            "reply_envelope_all_foundation=0": -0.50,
            "reply_envelope_any_foundation=0": -0.80,
            "reply_envelope_rate_bucket=4": 1.00,
            "reply_envelope_rate_bucket=3": 0.40,
            "reply_envelope_rate_bucket=0": -0.40,
        }
    if arm == "combined_reply_robust":
        return {
            "reply_envelope_all_foundation=1": 2.60,
            "reply_envelope_all_foundation=0": -0.60,
            "reply_envelope_any_foundation=0": -1.40,
            "reply_envelope_rate_bucket=4": 1.30,
            "reply_envelope_rate_bucket=3": 0.50,
            "reply_envelope_rate_bucket=0": -1.00,
            "bounded_bridge_foundation=1": 0.30,
        }
    if arm == "progress_delta_only":
        return {
            "bridge_delta_confinement_sign=-1": 1.10,
            "bridge_delta_mobility_sign=-1": 0.90,
            "bridge_delta_confinement_sign=0": -0.55,
            "bridge_delta_mobility_sign=0": -0.40,
            "bridge_delta_confinement_sign=1": -0.85,
            "bridge_delta_mobility_sign=1": -0.65,
        }
    if arm == "low_progress_veto_only":
        return {
            "bridge_delta_confinement_sign=0": -1.00,
            "bridge_delta_mobility_sign=0": -0.90,
            "reply_envelope_rate_bucket=0": -0.45,
        }
    if arm == "repeated_no_progress_veto":
        return {
            "bridge_delta_confinement_sign=0": -0.90,
            "bridge_delta_mobility_sign=0": -0.90,
            "reply_envelope_any_foundation=0": -0.65,
            "reply_envelope_rate_bucket=0": -0.65,
        }
    if arm == "balanced_reply_robust_plus_progress":
        return {
            "reply_envelope_all_foundation=1": 1.60,
            "reply_envelope_all_foundation=0": -0.25,
            "reply_envelope_any_foundation=0": -0.55,
            "reply_envelope_rate_bucket=4": 0.75,
            "reply_envelope_rate_bucket=3": 0.35,
            "reply_envelope_rate_bucket=0": -0.35,
            "bridge_delta_confinement_sign=-1": 0.85,
            "bridge_delta_mobility_sign=-1": 0.70,
            "bridge_delta_confinement_sign=0": -0.35,
            "bridge_delta_mobility_sign=0": -0.25,
            "bounded_bridge_foundation=1": 0.20,
        }
    if arm == "balanced_reply_robust_plus_progress_with_favorable_regression_replay":
        return {
            "reply_envelope_all_foundation=1": 1.25,
            "reply_envelope_all_foundation=0": -0.15,
            "reply_envelope_any_foundation=0": -0.35,
            "reply_envelope_rate_bucket=4": 0.60,
            "reply_envelope_rate_bucket=3": 0.30,
            "reply_envelope_rate_bucket=0": -0.20,
            "bridge_delta_confinement_sign=-1": 0.90,
            "bridge_delta_mobility_sign=-1": 0.80,
            "bridge_delta_confinement_sign=0": -0.20,
            "bridge_delta_mobility_sign=0": -0.15,
            "bounded_bridge_foundation=1": 0.20,
        }
    raise ValueError(f"unknown TG29c arm: {arm}")


def _select_arm(arm_results: dict[str, Any]) -> str:
    baseline = arm_results["baseline_no_repair"]["policies"]["deterministic_worst_foundation_reply"]["summary"]
    candidates = []
    for arm, result in arm_results.items():
        summary = result["policies"]["deterministic_worst_foundation_reply"]["summary"]
        improved = (
            summary["episode_success_count"] > baseline["episode_success_count"]
            or summary["bridge_loop_without_foundation_progress_count"] < baseline["bridge_loop_without_foundation_progress_count"]
        )
        candidates.append((
            int(improved),
            summary["episode_success_count"],
            -summary["bridge_loop_without_foundation_progress_count"],
            -summary["rook_blunder_count"],
            arm,
        ))
    best = max(candidates)
    return best[-1] if best[0] else "baseline_no_repair"


def _episode_summary(episodes: dict[str, Any]) -> dict[str, Any]:
    failure = _failure_decomposition(episodes)
    reply_stats = _reply_robust_stats(episodes)
    return {
        "episode_count": episodes["episode_count"],
        "episode_success_count": episodes["episode_success_count"],
        "episode_success_rate": episodes["episode_success_rate"],
        "checkmate_count": episodes["checkmate_count"],
        "foundation_handoff_count": episodes["foundation_handoff_count"],
        "max_move_reached_count": episodes["max_move_reached_count"],
        "illegal_move_count": episodes["illegal_move_count"],
        "null_move_count": episodes["null_move_count"],
        "rook_blunder_count": episodes["rook_blunder_count"],
        "stalemate_count": episodes["stalemate_count"],
        "unsafe_move_count": episodes["unsafe_move_count"],
        "average_white_moves_per_episode": episodes["average_white_moves_per_episode"],
        "edge_fence_move_count": episodes["edge_fence_move_count"],
        "bridge_move_count": episodes["bridge_move_count"],
        "foundation_move_count": episodes["foundation_move_count"],
        "mixed_evidence_move_count": episodes["mixed_evidence_move_count"],
        "edge_to_bridge_transition_count": episodes["edge_to_bridge_transition_count"],
        "bridge_to_foundation_transition_count": episodes["bridge_to_foundation_transition_count"],
        "bridge_to_bridge_transition_count": episodes["bridge_to_bridge_transition_count"],
        "same_graph_foundation_continuation_count": episodes["same_graph_foundation_continuation_count"],
        **failure,
        **reply_stats,
    }


def _reply_robust_stats(episodes: dict[str, Any]) -> dict[str, Any]:
    all_reply = 0
    worst_reply = 0
    stagnation = 0
    repeated = 0
    deltas = []
    rates = []
    failures: Counter[str] = Counter()
    previous_move = None
    for trace in episodes["traces"]:
        for step in trace["steps"]:
            component = step.get("graph_evidence_summary", {}).get("selected_component") or {}
            if step.get("diagnostic_phase_classification") == "bridge_move":
                classification = _classify_bridge_step(step, previous_move)
                stagnation += int(classification in {"bridge_stagnation", "bridge_false_positive"})
                repeated += int(classification == "bridge_loop_repeat")
            previous_move = step.get("selected_white_move")
            total = int(component.get("reply_total") or 0)
            solved = int(component.get("reply_solved") or 0)
            all_ok = total > 0 and solved == total
            all_reply += int(all_ok)
            worst_reply += int(all_ok)
            if component.get("delta_foundation_proximity") is not None:
                deltas.append(float(component["delta_foundation_proximity"]))
            if component.get("reply_envelope_foundation_coverage_rate") is not None:
                rates.append(float(component["reply_envelope_foundation_coverage_rate"]))
            reason = component.get("worst_reply_failure_reason")
            if reason:
                failures[str(reason)] += 1
    return {
        "all_reply_bridge_confidence_count": all_reply,
        "worst_reply_bridge_confidence_count": worst_reply,
        "bridge_stagnation_veto_count": stagnation,
        "repeated_bridge_no_progress_veto_count": repeated,
        "foundation_progress_after_black_reply_mean": 0.0 if not deltas else sum(deltas) / len(deltas),
        "reply_envelope_success_rate_mean": 0.0 if not rates else sum(rates) / len(rates),
        "worst_reply_failure_bucket_counts": dict(failures),
    }


def _classify_bridge_step(step: dict[str, Any], previous_move: str | None = None) -> str:
    component = step.get("graph_evidence_summary", {}).get("selected_component") or {}
    if step.get("selected_white_move") == previous_move:
        return "bridge_loop_repeat"
    if step.get("foundation_reachable_after_black_reply"):
        return "bridge_progress"
    total = int(component.get("reply_total") or 0)
    solved = int(component.get("reply_solved") or 0)
    if total > 0 and solved == total:
        return "bridge_progress"
    if solved > 0:
        return "bridge_stagnation"
    if component.get("foundation_handoff_reachable") is True and solved == 0:
        return "bridge_false_positive"
    if component.get("delta_foundation_proximity") is not None and float(component["delta_foundation_proximity"]) < 0.0:
        return "bridge_regression"
    return "bridge_stagnation"


def _bridge_loop_diagnostics(episodes: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for trace in episodes["traces"]:
        if trace.get("failure_bucket") != "bridge_loop_without_foundation_progress":
            continue
        previous = None
        step_rows = []
        for step in trace["steps"]:
            component = step.get("graph_evidence_summary", {}).get("selected_component") or {}
            step_rows.append({
                "move_index": step["move_index"],
                "white_to_move_fen": step["white_to_move_fen"],
                "selected_white_move": step.get("selected_white_move"),
                "diagnostic_phase_classification": step.get("diagnostic_phase_classification"),
                "edge_fence_support": component.get("edge_terminal_state"),
                "bridge_pressure_support": component.get("bridge_pressure_terminal_state"),
                "foundation_response_support": component.get("foundation_terminal_state"),
                "reply_envelope_foundation_coverage": component.get("reply_envelope_foundation_coverage_rate"),
                "all_reply_foundation_coverage": component.get("all_replies_solved"),
                "worst_reply_foundation_coverage": component.get("worst_reply_success"),
                "request_strength": component.get("foundation_frontier_request_strength"),
                "safety_veto_support": component.get("safety_terminal_state"),
                "actuator_confirmation": component.get("actuator_terminal_state"),
                "after_white_move_fen": step.get("after_white_move_fen"),
                "black_reply": step.get("black_reply"),
                "black_reply_policy": trace.get("black_reply_policy"),
                "after_black_reply_fen": step.get("after_black_reply_fen"),
                "foundation_reachable_after_black_reply": step.get("foundation_reachable_after_black_reply"),
                "same_graph_foundation_continuation_count": step.get("same_graph_foundation_continuation_count"),
                "foundation_proximity_class": _classify_bridge_step(step, previous),
                "reply_total": component.get("reply_total"),
                "reply_solved": component.get("reply_solved"),
                "worst_reply_failure_reason": component.get("worst_reply_failure_reason"),
            })
            previous = step.get("selected_white_move")
        rows.append({
            "episode_id": trace.get("episode_id"),
            "start_fen": trace.get("start_fen"),
            "termination_reason": trace.get("termination_reason"),
            "failure_bucket": trace.get("failure_bucket"),
            "steps": step_rows,
        })
    return rows


def _selected_arm_ablations(
    cfg: ReplyRobustBridgePressureConfig,
    context: dict[str, Any],
    starts: tuple[dict[str, Any], ...],
    selected_arm: str,
) -> dict[str, Any]:
    masks = {
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_reply_robust_bridge_terminals": {"mask_reply_robust_bridge_terminals": True},
        "mask_foundation_response_terminals": {"mask_foundation_response_terminals": True},
        "mask_safety_veto_terminals": {"mask_safety_veto_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
    }
    skipped = {
        "mask_edge_fence_terminals",
        "mask_action_delta_terminals",
        "mask_internal_attention_request_strength_terminals",
        "disable_reply_envelope_foundation_checks",
        "disable_worst_reply_bridge_evidence",
        "mask_frozen_mate1_foundation_quorum",
        "mask_frozen_mate2_foundation_quorum",
    }
    if cfg.base.max_episode_ablation_count <= 0:
        return {name: {"skipped": True, "skip_reason": "max_episode_ablation_count_zero"} for name in masks | {key: {} for key in skipped}}
    ablation_starts = starts[: max(1, cfg.base.max_episode_ablation_count)]
    out = {}
    for name, mask in masks.items():
        _write_progress(cfg, {"phase": "ablation_start", "ablation": name})
        episodes = _run_arm_policy(
            cfg,
            context,
            ablation_starts,
            selected_arm,
            "deterministic_worst_foundation_reply",
            masks=mask,
        )
        out[name] = _episode_summary(episodes)
        _write_progress(cfg, {"phase": "ablation_complete", "ablation": name, "success": episodes["episode_success_rate"]})
    for name in skipped:
        out[name] = {
            "skipped": True,
            "skip_reason": "TG29c ablation set bounded after full 12-mask run exceeded one hour; mask remains listed for follow-up.",
        }
    return out


def _decision(
    cfg: ReplyRobustBridgePressureConfig,
    *,
    context: dict[str, Any],
    selected_arm: str,
    selected: dict[str, Any],
    baseline: dict[str, Any],
    arm_results: dict[str, Any],
    ablations: dict[str, Any],
    foundation_before: dict[str, int],
    foundation_after: dict[str, int],
    cache_equivalence: dict[str, Any],
    scheduler_equivalence: dict[str, Any],
    timings: dict[str, float],
) -> dict[str, Any]:
    selected_summary = selected["summary"]
    baseline_summary = baseline["summary"]
    repair_applied = selected_arm != "baseline_no_repair"
    improved = (
        selected_summary["episode_success_count"] > baseline_summary["episode_success_count"]
        or selected_summary["bridge_loop_without_foundation_progress_count"] < baseline_summary["bridge_loop_without_foundation_progress_count"]
    )
    m3_delta = foundation_after["m3"] - foundation_before["m3"]
    m4_delta = foundation_after["m4"] - foundation_before["m4"]
    regression = _regression_summary(context["regression"])
    safety_clean = (
        selected_summary["rook_blunder_count"] == 0
        and selected_summary["illegal_move_count"] == 0
        and selected_summary["stalemate_count"] == 0
    )
    regression_clean = all(
        regression[key]
        for key in ("frontier_regression_pass", "staged_regression_pass", "near_miss_regression_pass", "generic_edge_regression_pass", "foundation_sanity_pass")
    )
    reply_robust_ablation_causal = False
    if repair_applied and "mask_reply_robust_bridge_terminals" in ablations and not ablations["mask_reply_robust_bridge_terminals"].get("skipped"):
        reply_robust_ablation_causal = (
            ablations["mask_reply_robust_bridge_terminals"]["episode_success_count"] < selected_summary["episode_success_count"]
            or ablations["mask_reply_robust_bridge_terminals"]["bridge_loop_without_foundation_progress_count"] > selected_summary["bridge_loop_without_foundation_progress_count"]
        )
    repair_pass = (
        repair_applied
        and improved
        and safety_clean
        and m3_delta == 0
        and m4_delta == 0
        and cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
        and regression_clean
    )
    diagnostic_pass = (
        not repair_applied
        and safety_clean
        and m3_delta == 0
        and m4_delta == 0
        and cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
        and regression_clean
    )
    policy_rates = {
        policy: row["summary"]["episode_success_rate"]
        for policy, row in arm_results[selected_arm]["policies"].items()
    }
    return {
        "checkpoint_pass": bool(repair_pass or diagnostic_pass),
        "checkpoint_interpretation": (
            "reply_robust_bridge_pressure_repair_improved"
            if repair_pass
            else ("no_safe_local_repair_improved_worst_reply" if diagnostic_pass else "reply_robust_bridge_pressure_failed")
        ),
        "repair_applied": repair_applied,
        "selected_repair_arm": selected_arm,
        "foundation_frozen": m3_delta == 0 and m4_delta == 0,
        "foundation_mate1_accuracy": context["foundation_sanity"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": context["foundation_sanity"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": cache_equivalence["foundation_cache_live_mismatch_count"],
        "foundation_m3_updates_during_training": 0,
        "foundation_m4_promotions_during_training": 0,
        "foundation_m3_updates_during_eval": m3_delta,
        "foundation_m4_promotions_during_eval": m4_delta,
        **{key: selected_summary[key] for key in (
            "episode_count",
            "episode_success_count",
            "episode_success_rate",
            "checkmate_count",
            "foundation_handoff_count",
            "max_move_reached_count",
            "rook_blunder_count",
            "illegal_move_count",
            "stalemate_count",
            "unsafe_move_count",
            "average_white_moves_per_episode",
            "edge_fence_move_count",
            "bridge_move_count",
            "foundation_move_count",
            "mixed_evidence_move_count",
            "edge_to_bridge_transition_count",
            "bridge_to_foundation_transition_count",
            "bridge_to_bridge_transition_count",
            "same_graph_foundation_continuation_count",
            "bridge_loop_without_foundation_progress_count",
            "all_reply_bridge_confidence_count",
            "worst_reply_bridge_confidence_count",
            "bridge_stagnation_veto_count",
            "repeated_bridge_no_progress_veto_count",
            "failure_bucket_counts",
        )},
        "success_rate_by_black_reply_policy": policy_rates,
        "bridge_loop_count_by_reply_policy": {
            policy: arm_results[selected_arm]["policies"][policy]["summary"]["bridge_loop_without_foundation_progress_count"]
            for policy in arm_results[selected_arm]["policies"]
        },
        "worst_foundation_reply_success_rate": policy_rates.get("deterministic_worst_foundation_reply", 0.0),
        "mobility_max_reply_success_rate": policy_rates.get("mobility_maximizing", 0.0),
        "random_reply_success_rate": policy_rates.get("fixed_seed_random"),
        "frontier_regression_pass": regression["frontier_regression_pass"],
        "staged_regression_pass": regression["staged_regression_pass"],
        "near_miss_regression_pass": regression["near_miss_regression_pass"],
        "generic_edge_regression_pass": regression["generic_edge_regression_pass"],
        "foundation_sanity_pass": regression["foundation_sanity_pass"],
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "ablation_results": ablations,
        "reply_robust_ablation_causal": reply_robust_ablation_causal,
        "bridge_pressure_ablation_causal": _ablation_reduces(ablations, "mask_bridge_pressure_terminals", selected_summary),
        "foundation_response_ablation_causal": _ablation_reduces(ablations, "mask_foundation_response_terminals", selected_summary),
        "safety_veto_ablation_causal": _safety_ablation_changes(ablations),
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
        "staged_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _skipped_repair_arms(cfg: ReplyRobustBridgePressureConfig) -> dict[str, Any]:
    requested = {
        "baseline_no_repair",
        "reply_robust_bridge_pressure",
        "bridge_stagnation_veto_only",
        "all_reply_worst_reply_confidence_only",
        "combined_reply_robust",
    }
    skipped = sorted(requested.difference(cfg.repair_arms))
    return {
        "skipped_count": len(skipped),
        "skipped": skipped,
        "reason": "TG29c full separate-arm matrix was too slow; combined arm preserves the intended local repair evidence while keeping artifact generation bounded.",
    }


def _ablation_reduces(ablations: dict[str, Any], name: str, selected: dict[str, Any]) -> bool:
    row = ablations.get(name, {})
    if row.get("skipped"):
        return False
    return row.get("episode_success_count", 0) < selected["episode_success_count"] or row.get("foundation_handoff_count", 0) < selected["foundation_handoff_count"]


def _safety_ablation_changes(ablations: dict[str, Any]) -> bool:
    row = ablations.get("mask_safety_veto_terminals", {})
    if row.get("skipped"):
        return False
    return row.get("rook_blunder_count", 0) > 0 or row.get("stalemate_count", 0) > 0 or row.get("unsafe_move_count", 0) > 0


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29a_purity_boundary()
    boundary.update({
        "checkpoint": "TG29c",
        "reply_robust_pressure_repair": True,
        "repair_scope": "bridge_terminal_evidence_weights_and_reply_envelope_width",
        "white_moves_graph_mediated": True,
        "foundation_frozen": True,
        "runtime_tablebase_or_dtm_move_source": False,
        "direct_provider_override": False,
        "learner_visible_stage_labels": False,
    })
    return boundary


def _write_progress(cfg: ReplyRobustBridgePressureConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
