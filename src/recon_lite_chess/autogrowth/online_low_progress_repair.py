"""TG29d online low-progress repair and reply-policy balance."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
import time
from pathlib import Path
from typing import Any

from .frozen_foundation_edge_fence_reentry import _foundation_counts
from .online_failure_decomposition import _regression_summary
from .reply_robust_bridge_pressure import (
    ReplyRobustBridgePressureConfig,
    _ensure_selected_policy_comparison,
    _purity_boundary as _tg29c_purity_boundary,
    _repair_weight_delta,
    _run_arm_matrix,
    _run_arm_policy,
    _selected_arm_ablations,
)
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .native_quorum_materialization import _tg26t_config
from .native_quorum_mate2_chaining import _tg26u_config
from .tiny_online_krk_episode_runner import (
    TinyOnlineKRKEpisodeRunnerConfig,
    _build_context,
    _episode_starts,
    _write_progress as _write_tg29a_progress,
)


@dataclass(frozen=True)
class OnlineLowProgressRepairConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("mixed_balanced_plus_staged",),
        progress_output="reports/autogrowth/krk_autogrowth_tg29d_online_low_progress_repair_progress.json",
    )
    reply_policies: tuple[str, ...] = ("deterministic_worst_foundation_reply",)
    comparison_reply_policies: tuple[str, ...] = ("mobility_maximizing",)
    repair_arms: tuple[str, ...] = (
        "baseline_no_repair",
        "combined_reply_robust",
        "balanced_reply_robust_plus_progress",
        "balanced_reply_robust_plus_progress_with_favorable_regression_replay",
    )
    max_reply_envelope_replies_per_candidate: int = 2
    max_repair_cache_candidate_moves: int = 4


@dataclass(frozen=True)
class OnlineLowProgressRepairResult:
    config: OnlineLowProgressRepairConfig
    foundation_sanity: dict[str, Any]
    regression_results: dict[str, Any]
    arm_results: dict[str, Any]
    selected_arm_episodes: dict[str, Any]
    low_progress_diagnostics: list[dict[str, Any]]
    ablation_results: dict[str, Any]
    foundation_cache_equivalence: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29d_online_low_progress_repair.v0",
            "checkpoint": "TG29d_online_low_progress_repair",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "foundation_sanity": self.foundation_sanity,
            "regression_results": self.regression_results,
            "arm_results": self.arm_results,
            "skipped_repair_arms": _skipped_repair_arms(self.config),
            "selected_arm_episodes": self.selected_arm_episodes,
            "low_progress_diagnostics": self.low_progress_diagnostics,
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
                    "# TG29d Online Low-Progress Repair",
                    "",
                    f"- checkpoint_pass: `{decision['checkpoint_pass']}`",
                    f"- interpretation: `{decision['checkpoint_interpretation']}`",
                    f"- repair_applied: `{decision['repair_applied']}`",
                    f"- selected_repair_arm: `{decision['selected_repair_arm']}`",
                    f"- worst-foundation success: `{decision['worst_foundation_reply_success_rate']}`",
                    f"- mobility-max success: `{decision['mobility_max_reply_success_rate']}`",
                    f"- low-progress failures: `{decision['selected_moves_safe_but_low_progress_count']}`",
                    f"- bridge-loop failures: `{decision['bridge_loop_without_foundation_progress_count']}`",
                    f"- safety rook/illegal/stalemate: `{decision['rook_blunder_count']}` / `{decision['illegal_move_count']}` / `{decision['stalemate_count']}`",
                    "",
                    "Interpretation: TG29d tests progress pressure on the same frozen-foundation online runway.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_online_low_progress_repair(
    *,
    config: OnlineLowProgressRepairConfig | None = None,
) -> OnlineLowProgressRepairResult:
    cfg = config or OnlineLowProgressRepairConfig()
    bridge_cfg = _as_tg29c_cfg(cfg)
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
    arm_results = _run_arm_matrix(bridge_cfg, context, starts)
    timings["arm_matrix_seconds"] = round(time.perf_counter() - start, 6)
    selected_arm = _select_progress_arm(arm_results)
    _ensure_selected_policy_comparison(bridge_cfg, context, starts, arm_results, selected_arm)
    selected = arm_results[selected_arm]["policies"]["deterministic_worst_foundation_reply"]
    _write_progress(cfg, {"phase": "arms_complete", "selected_arm": selected_arm, "worst_success": selected["summary"]["episode_success_rate"]})

    start = time.perf_counter()
    ablations = _selected_arm_ablations(bridge_cfg, context, starts, selected_arm)
    ablations = {name: _normalize_ablation_progress(row) for name, row in ablations.items()}
    timings["selected_arm_ablation_seconds"] = round(time.perf_counter() - start, 6)

    foundation_after = _foundation_counts(graph)
    cache_equivalence = context["cache"].live_equivalence_audit(max_samples=min(8, cfg.base.max_samples))
    scheduler_equivalence = _scheduler_equivalence(
        _tg26s_config(_tg26t_config(_tg26u_config(context["mate2_cfg"]))),
        context["mate1_train"],
        context["mate1_heldout"],
    )
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)
    selected_summary = _progress_summary(selected["episodes"])
    baseline_summary = _progress_summary(arm_results["combined_reply_robust"]["policies"]["deterministic_worst_foundation_reply"]["episodes"])
    decision = _decision(
        cfg,
        context=context,
        selected_arm=selected_arm,
        selected_summary=selected_summary,
        tg29c_summary=baseline_summary,
        arm_results=arm_results,
        ablations=ablations,
        foundation_before=foundation_before,
        foundation_after=foundation_after,
        cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return OnlineLowProgressRepairResult(
        config=cfg,
        foundation_sanity=context["foundation_sanity"],
        regression_results=_regression_summary(context["regression"]),
        arm_results={arm: _arm_with_progress(result) for arm, result in arm_results.items()},
        selected_arm_episodes=selected["episodes"],
        low_progress_diagnostics=_low_progress_diagnostics(selected["episodes"]),
        ablation_results=ablations,
        foundation_cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _as_tg29c_cfg(cfg: OnlineLowProgressRepairConfig) -> ReplyRobustBridgePressureConfig:
    return ReplyRobustBridgePressureConfig(
        base=cfg.base,
        reply_policies=cfg.reply_policies,
        comparison_reply_policies=cfg.comparison_reply_policies,
        repair_arms=cfg.repair_arms,
        max_reply_envelope_replies_per_candidate=cfg.max_reply_envelope_replies_per_candidate,
        max_repair_cache_candidate_moves=cfg.max_repair_cache_candidate_moves,
    )


def _select_progress_arm(arm_results: dict[str, Any]) -> str:
    tg29c = _progress_summary(arm_results["combined_reply_robust"]["policies"]["deterministic_worst_foundation_reply"]["episodes"])
    candidates = []
    for arm, result in arm_results.items():
        summary = _progress_summary(result["policies"]["deterministic_worst_foundation_reply"]["episodes"])
        mobility = result["policies"].get("mobility_maximizing", {}).get("summary", {}).get("episode_success_count", 0)
        low_delta = tg29c["selected_moves_safe_but_low_progress_count"] - summary["selected_moves_safe_but_low_progress_count"]
        loop_ok = summary["bridge_loop_without_foundation_progress_count"] <= tg29c["bridge_loop_without_foundation_progress_count"]
        safety_ok = summary["rook_blunder_count"] == 0 and summary["illegal_move_count"] == 0 and summary["stalemate_count"] == 0
        candidates.append((
            int(low_delta > 0 and loop_ok and safety_ok),
            low_delta,
            summary["episode_success_count"],
            -summary["bridge_loop_without_foundation_progress_count"],
            mobility,
            arm,
        ))
    best = max(candidates)
    return best[-1] if best[0] else "combined_reply_robust"


def _arm_with_progress(result: dict[str, Any]) -> dict[str, Any]:
    out = dict(result)
    out["policies"] = {
        policy: row | {"progress_summary": _progress_summary(row["episodes"])}
        for policy, row in result["policies"].items()
    }
    return out


def _progress_summary(episodes: dict[str, Any]) -> dict[str, Any]:
    base = {
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
        "failure_bucket_counts": episodes["failure_bucket_counts"],
        "bridge_loop_without_foundation_progress_count": episodes["failure_bucket_counts"].get("bridge_loop_without_foundation_progress", 0),
        "selected_moves_safe_but_low_progress_count": episodes["failure_bucket_counts"].get("selected_moves_safe_but_low_progress", 0),
    }
    progress = _progress_counts(episodes)
    return base | progress


def _progress_counts(episodes: dict[str, Any]) -> dict[str, Any]:
    repeated_safe = 0
    repeated_bridge = 0
    meaningful_edge = 0
    meaningful_bridge = 0
    meaningful_foundation = 0
    edge_deltas = []
    mobility_deltas = []
    conf_deltas = []
    foundation_deltas = []
    rate_deltas = []
    worst_deltas = []
    last_geometry = None
    last_phase = None
    for trace in episodes["traces"]:
        previous_rate = 0.0
        previous_foundation = 0.0
        for step in trace["steps"]:
            component = step.get("graph_evidence_summary", {}).get("selected_component") or {}
            edge = _num(component.get("delta_black_king_edge_distance"))
            mobility = _num(component.get("delta_black_king_legal_mobility"))
            conf = _num(component.get("delta_confinement_area"))
            rate = _num(component.get("reply_envelope_foundation_coverage_rate"))
            foundation = 1.0 if step.get("foundation_reachable_after_black_reply") else 0.0
            edge_deltas.append(edge)
            mobility_deltas.append(mobility)
            conf_deltas.append(conf)
            foundation_deltas.append(foundation - previous_foundation)
            rate_deltas.append(rate - previous_rate)
            worst_deltas.append((1.0 if component.get("worst_reply_success") else 0.0) - previous_foundation)
            phase = step.get("diagnostic_phase_classification")
            geometry = (edge, mobility, conf, phase)
            repeated = geometry == last_geometry or phase == last_phase
            repeated_safe += int(repeated)
            repeated_bridge += int(repeated and phase == "bridge_move")
            meaningful_edge += int(edge < 0 or conf < 0)
            meaningful_bridge += int(rate > previous_rate or mobility < 0)
            meaningful_foundation += int(foundation > previous_foundation or rate > 0.0)
            previous_rate = rate
            previous_foundation = foundation
            last_geometry = geometry
            last_phase = phase
    return {
        "repeated_safe_no_progress_count": repeated_safe,
        "repeated_bridge_no_progress_count": repeated_bridge,
        "meaningful_edge_progress_count": meaningful_edge,
        "meaningful_bridge_progress_count": meaningful_bridge,
        "meaningful_foundation_progress_count": meaningful_foundation,
        "average_edge_distance_delta": _avg(edge_deltas),
        "average_black_king_mobility_delta": _avg(mobility_deltas),
        "average_confinement_area_delta": _avg(conf_deltas),
        "average_foundation_reachability_delta": _avg(foundation_deltas),
        "average_reply_envelope_success_rate_delta": _avg(rate_deltas),
        "average_worst_reply_foundation_score_delta": _avg(worst_deltas),
    }


def _low_progress_diagnostics(episodes: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for trace in episodes["traces"]:
        if trace.get("failure_bucket") != "selected_moves_safe_but_low_progress":
            continue
        rows.append({
            "episode_id": trace.get("episode_id"),
            "start_fen": trace.get("start_fen"),
            "termination_reason": trace.get("termination_reason"),
            "steps": [_diagnostic_step(step) for step in trace["steps"]],
        })
    return rows


def _diagnostic_step(step: dict[str, Any]) -> dict[str, Any]:
    component = step.get("graph_evidence_summary", {}).get("selected_component") or {}
    edge = _num(component.get("delta_black_king_edge_distance"))
    mobility = _num(component.get("delta_black_king_legal_mobility"))
    conf = _num(component.get("delta_confinement_area"))
    rate = _num(component.get("reply_envelope_foundation_coverage_rate"))
    classification = "neutral_safe_move"
    if step.get("foundation_reachable_after_black_reply") or rate > 0:
        classification = "meaningful_foundation_progress"
    elif mobility < 0:
        classification = "meaningful_bridge_progress"
    elif edge < 0 or conf < 0:
        classification = "meaningful_edge_progress"
    elif edge > 0 or conf > 0 or mobility > 0:
        classification = "regress_without_blunder"
    return {
        "move_index": step["move_index"],
        "white_to_move_fen": step["white_to_move_fen"],
        "selected_white_move": step.get("selected_white_move"),
        "diagnostic_phase": step.get("diagnostic_phase_classification"),
        "edge_fence_evidence": component.get("edge_terminal_state"),
        "bridge_pressure_evidence": component.get("bridge_pressure_terminal_state"),
        "reply_robust_evidence": component.get("worst_reply_success"),
        "foundation_response_evidence": component.get("foundation_terminal_state"),
        "safety_veto_evidence": component.get("safety_terminal_state"),
        "actuator_confirmation": component.get("actuator_terminal_state"),
        "after_white_move_fen": step.get("after_white_move_fen"),
        "black_reply": step.get("black_reply"),
        "after_black_reply_fen": step.get("after_black_reply_fen"),
        "black_king_edge_distance_delta": edge,
        "black_king_mobility_delta": mobility,
        "confinement_area_delta": conf,
        "foundation_reachability_delta": 1.0 if step.get("foundation_reachable_after_black_reply") else 0.0,
        "reply_envelope_success_rate_delta": rate,
        "worst_reply_foundation_score_delta": 1.0 if component.get("worst_reply_success") else 0.0,
        "same_graph_foundation_continuation_delta": step.get("same_graph_foundation_continuation_count", 0),
        "safe_move_classification": classification,
    }


def _decision(
    cfg: OnlineLowProgressRepairConfig,
    *,
    context: dict[str, Any],
    selected_arm: str,
    selected_summary: dict[str, Any],
    tg29c_summary: dict[str, Any],
    arm_results: dict[str, Any],
    ablations: dict[str, Any],
    foundation_before: dict[str, int],
    foundation_after: dict[str, int],
    cache_equivalence: dict[str, Any],
    scheduler_equivalence: dict[str, Any],
    timings: dict[str, float],
) -> dict[str, Any]:
    m3_delta = foundation_after["m3"] - foundation_before["m3"]
    m4_delta = foundation_after["m4"] - foundation_before["m4"]
    regression = _regression_summary(context["regression"])
    policy_rates = {
        policy: row["summary"]["episode_success_rate"]
        for policy, row in arm_results[selected_arm]["policies"].items()
    }
    low_progress_improved = selected_summary["selected_moves_safe_but_low_progress_count"] < tg29c_summary["selected_moves_safe_but_low_progress_count"]
    safety_clean = selected_summary["rook_blunder_count"] == 0 and selected_summary["illegal_move_count"] == 0 and selected_summary["stalemate_count"] == 0
    regression_clean = all(regression[key] for key in ("frontier_regression_pass", "staged_regression_pass", "near_miss_regression_pass", "generic_edge_regression_pass", "foundation_sanity_pass"))
    mobility_ok = policy_rates.get("mobility_maximizing", 0.0) >= 0.5
    progress_causal = _ablation_progress_causal(ablations, selected_summary)
    repair_pass = (
        selected_arm != "combined_reply_robust"
        and low_progress_improved
        and selected_summary["bridge_loop_without_foundation_progress_count"] <= tg29c_summary["bridge_loop_without_foundation_progress_count"]
        and safety_clean
        and m3_delta == 0
        and m4_delta == 0
        and cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
        and regression_clean
        and mobility_ok
    )
    diagnostic_pass = (
        not repair_pass
        and safety_clean
        and m3_delta == 0
        and m4_delta == 0
        and cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
        and regression_clean
    )
    return {
        "checkpoint_pass": bool(repair_pass or diagnostic_pass),
        "checkpoint_interpretation": "online_low_progress_repair_improved" if repair_pass else "low_progress_explained_no_safe_local_repair",
        "repair_applied": selected_arm != "combined_reply_robust",
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
            "episode_count", "episode_success_count", "episode_success_rate", "checkmate_count", "foundation_handoff_count",
            "max_move_reached_count", "rook_blunder_count", "illegal_move_count", "stalemate_count", "unsafe_move_count",
            "average_white_moves_per_episode", "edge_fence_move_count", "bridge_move_count", "foundation_move_count",
            "mixed_evidence_move_count", "edge_to_bridge_transition_count", "bridge_to_foundation_transition_count",
            "bridge_to_bridge_transition_count", "same_graph_foundation_continuation_count",
            "bridge_loop_without_foundation_progress_count", "selected_moves_safe_but_low_progress_count",
            "repeated_safe_no_progress_count", "repeated_bridge_no_progress_count", "meaningful_edge_progress_count",
            "meaningful_bridge_progress_count", "meaningful_foundation_progress_count", "failure_bucket_counts",
        )},
        "success_rate_by_black_reply_policy": policy_rates,
        "worst_foundation_reply_success_rate": policy_rates.get("deterministic_worst_foundation_reply", 0.0),
        "mobility_max_reply_success_rate": policy_rates.get("mobility_maximizing", 0.0),
        "random_reply_success_rate": policy_rates.get("fixed_seed_random"),
        "low_progress_count_by_reply_policy": {
            policy: row["progress_summary"]["selected_moves_safe_but_low_progress_count"]
            for policy, row in _arm_with_progress(arm_results[selected_arm])["policies"].items()
        },
        "bridge_loop_count_by_reply_policy": {
            policy: row["progress_summary"]["bridge_loop_without_foundation_progress_count"]
            for policy, row in _arm_with_progress(arm_results[selected_arm])["policies"].items()
        },
        "frontier_regression_pass": regression["frontier_regression_pass"],
        "staged_regression_pass": regression["staged_regression_pass"],
        "near_miss_regression_pass": regression["near_miss_regression_pass"],
        "generic_edge_regression_pass": regression["generic_edge_regression_pass"],
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "ablation_results": ablations,
        "progress_repair_ablation_causal": progress_causal,
        "reply_robust_ablation_causal": _ablation_reduces(ablations, "mask_reply_robust_bridge_terminals", selected_summary),
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
    } | {key: selected_summary[key] for key in (
        "average_edge_distance_delta", "average_black_king_mobility_delta", "average_confinement_area_delta",
        "average_foundation_reachability_delta", "average_reply_envelope_success_rate_delta", "average_worst_reply_foundation_score_delta",
    )}


def _ablation_progress_causal(ablations: dict[str, Any], selected: dict[str, Any]) -> bool:
    row = ablations.get("mask_reply_robust_bridge_terminals", {})
    return not row.get("skipped", False) and row.get("selected_moves_safe_but_low_progress_count", 0) > selected["selected_moves_safe_but_low_progress_count"]


def _ablation_reduces(ablations: dict[str, Any], name: str, selected: dict[str, Any]) -> bool:
    row = ablations.get(name, {})
    return not row.get("skipped", False) and row.get("episode_success_count", 0) < selected["episode_success_count"]


def _normalize_ablation_progress(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("skipped", False):
        return dict(row)
    buckets = row.get("failure_bucket_counts", {})
    return {
        **row,
        "selected_moves_safe_but_low_progress_count": buckets.get("selected_moves_safe_but_low_progress", 0),
        "bridge_loop_without_foundation_progress_count": buckets.get("bridge_loop_without_foundation_progress", 0),
    }


def _skipped_repair_arms(cfg: OnlineLowProgressRepairConfig) -> dict[str, Any]:
    requested = {
        "baseline_no_repair",
        "combined_reply_robust",
        "progress_delta_only",
        "low_progress_veto_only",
        "repeated_no_progress_veto",
        "balanced_reply_robust_plus_progress",
        "balanced_reply_robust_plus_progress_with_favorable_regression_replay",
    }
    skipped = sorted(requested.difference(cfg.repair_arms))
    return {
        "skipped_count": len(skipped),
        "skipped": skipped,
        "reason": "TG29d keeps the matrix bounded after TG29c showed full arm/policy/ablation expansion is CPU-bound.",
    }


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29c_purity_boundary()
    boundary.update({
        "checkpoint": "TG29d",
        "online_low_progress_repair": True,
        "repair_scope": "existing_bridge_progress_delta_weights",
        "direct_provider_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "learner_visible_stage_labels": False,
    })
    return boundary


def _write_progress(cfg: OnlineLowProgressRepairConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _avg(values: list[float]) -> float:
    return 0.0 if not values else sum(values) / len(values)
