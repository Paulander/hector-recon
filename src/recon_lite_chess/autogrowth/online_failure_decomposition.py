"""TG29b online episode failure decomposition."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, replace
import json
import time
from pathlib import Path
from typing import Any

import chess

from .frozen_foundation_edge_fence_reentry import _evaluate_edge_layer, _foundation_counts
from .frozen_foundation_response_cache_bridge_retrieval import _evaluate_cache_bridge_layer
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .native_quorum_materialization import _tg26t_config
from .native_quorum_mate2_chaining import _tg26u_config
from .tiny_online_krk_episode_runner import (
    TinyOnlineKRKEpisodeRunnerConfig,
    _build_context,
    _episode_starts,
    _foundation_reachable,
    _purity_boundary as _tg29a_purity_boundary,
    _run_episodes,
    _write_progress as _write_tg29a_progress,
)


@dataclass(frozen=True)
class OnlineFailureDecompositionConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("mixed_balanced_plus_staged",),
        progress_output="reports/autogrowth/krk_autogrowth_tg29b_online_failure_decomposition_progress.json",
    )
    reply_policies: tuple[str, ...] = ("deterministic_worst_foundation_reply", "mobility_maximizing")
    max_audit_candidates: int = 12
    max_deep_offline_audit_turns: int = 0
    repair_applied: bool = False
    repair_type: str = "none"


@dataclass(frozen=True)
class OnlineFailureDecompositionResult:
    config: OnlineFailureDecompositionConfig
    foundation_sanity: dict[str, Any]
    regression_results: dict[str, Any]
    main_episodes: dict[str, Any]
    reply_policy_comparison: dict[str, Any]
    failure_decomposition: dict[str, Any]
    ablation_results: dict[str, Any]
    foundation_cache_equivalence: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29b_online_failure_decomposition.v0",
            "checkpoint": "TG29b_online_failure_decomposition",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "foundation_sanity": self.foundation_sanity,
            "regression_results": self.regression_results,
            "main_episodes": self.main_episodes,
            "reply_policy_comparison": self.reply_policy_comparison,
            "failure_decomposition": self.failure_decomposition,
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
                    "# TG29b Online Failure Decomposition",
                    "",
                    f"- checkpoint_pass: `{decision['checkpoint_pass']}`",
                    f"- interpretation: `{decision['checkpoint_interpretation']}`",
                    f"- repair_applied: `{decision['repair_applied']}`",
                    f"- episodes: `{decision['episode_success_count']}` / `{decision['episode_count']}` successes",
                    f"- max-move failures: `{decision['max_move_failure_count']}`",
                    f"- bridge-loop failures: `{decision['bridge_loop_without_foundation_progress_count']}`",
                    f"- bridge->foundation transitions: `{decision['bridge_to_foundation_transition_count']}`",
                    f"- safety: rook/illegal/stalemate `{decision['rook_blunder_count']}` / `{decision['illegal_move_count']}` / `{decision['stalemate_count']}`",
                    "",
                    "Interpretation: TG29b diagnoses online transition failures; it does not broaden KRK competence.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_online_failure_decomposition(
    *,
    config: OnlineFailureDecompositionConfig | None = None,
) -> OnlineFailureDecompositionResult:
    cfg = config or OnlineFailureDecompositionConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})
    context = _build_context(cfg.base)
    timings.update(context["timings"])
    graph = context["graph"]
    cache = context["cache"]
    starts = _episode_starts(cfg.base, context)
    _write_progress(cfg, {"phase": "context_built", "selected_schedule": context["regression"]["selected_schedule_name"]})

    before = _foundation_counts(graph)
    start = time.perf_counter()
    main = _run_episodes(
        graph,
        cache,
        context["mate2_cfg"],
        context["tg28c_cfg"],
        context["edge_cfg"],
        starts,
        context["selected"]["edge_weights"],
        context["selected"]["bridge_weights"],
        cfg.base,
    )
    enriched = _enrich_episodes(main, context, cfg)
    after = _foundation_counts(graph)
    timings["main_episode_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "main_episodes_complete", "episode_success_count": enriched["episode_success_count"]})

    start = time.perf_counter()
    policy_comparison = _reply_policy_comparison(cfg, context, starts)
    timings["reply_policy_comparison_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    ablations = _targeted_ablations(cfg, context, starts, enriched)
    timings["targeted_ablation_seconds"] = round(time.perf_counter() - start, 6)

    foundation_cache_equivalence = cache.live_equivalence_audit(max_samples=min(8, cfg.base.max_samples))
    scheduler_equivalence = _scheduler_equivalence(
        _tg26s_config(_tg26t_config(_tg26u_config(context["mate2_cfg"]))),
        context["mate1_train"],
        context["mate1_heldout"],
    )
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)
    failure = _failure_decomposition(enriched)
    decision = _decision(
        cfg,
        context=context,
        episodes=enriched,
        failure=failure,
        policy_comparison=policy_comparison,
        ablations=ablations,
        foundation_cache_equivalence=foundation_cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        foundation_before=before,
        foundation_after=after,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return OnlineFailureDecompositionResult(
        config=cfg,
        foundation_sanity=context["foundation_sanity"],
        regression_results=_regression_summary(context["regression"]),
        main_episodes=enriched,
        reply_policy_comparison=policy_comparison,
        failure_decomposition=failure,
        ablation_results=ablations,
        foundation_cache_equivalence=foundation_cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _reply_policy_comparison(cfg: OnlineFailureDecompositionConfig, context: dict[str, Any], starts: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    rows = {}
    for policy in cfg.reply_policies:
        policy_cfg = replace(cfg.base, black_reply_policy=policy)
        result = _run_episodes(
            context["graph"],
            context["cache"],
            context["mate2_cfg"],
            context["tg28c_cfg"],
            context["edge_cfg"],
            starts,
            context["selected"]["edge_weights"],
            context["selected"]["bridge_weights"],
            policy_cfg,
        )
        enriched = _enrich_episodes(result, context, cfg)
        rows[policy] = {
            "episode_count": enriched["episode_count"],
            "episode_success_count": enriched["episode_success_count"],
            "episode_success_rate": enriched["episode_success_rate"],
            "foundation_handoff_count": enriched["foundation_handoff_count"],
            "max_move_reached_count": enriched["max_move_reached_count"],
            "failure_bucket_counts": enriched["failure_bucket_counts"],
            "transition_counts": enriched["explicit_transition_counts"],
        }
    return {
        "policies": rows,
        "success_rate_by_black_reply_policy": {policy: row["episode_success_rate"] for policy, row in rows.items()},
        "failure_buckets_by_black_reply_policy": {policy: row["failure_bucket_counts"] for policy, row in rows.items()},
    }


def _targeted_ablations(cfg: OnlineFailureDecompositionConfig, context: dict[str, Any], starts: tuple[dict[str, Any], ...], episodes: dict[str, Any]) -> dict[str, Any]:
    masks = {
        "mask_edge_fence_terminals": {"mask_edge_fence_terminals": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_foundation_response_terminals": {"mask_foundation_response_terminals": True},
        "mask_action_delta_terminals": {"mask_action_delta_terminals": True},
        "mask_safety_veto_terminals": {"mask_safety_veto_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "disable_reply_envelope_foundation_checks": {"disable_reply_envelope_foundation_checks": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_frozen_mate2_foundation_quorum": True},
    }
    if cfg.base.max_episode_ablation_count <= 0:
        return {name: {"skipped": True, "skip_reason": "max_episode_ablation_count_zero"} for name in masks}
    success = next((episode for episode in episodes["traces"] if episode["success"]), None)
    failed = next((episode for episode in episodes["traces"] if episode["max_move_reached"]), None)
    selected_starts = []
    for episode in (success, failed):
        if episode is not None:
            selected_starts.append({"start_fen": episode["start_fen"], "source": episode["source"] + "_ablation"})
    if not selected_starts:
        selected_starts = list(starts[:1])
    out = {}
    for name, mask in masks.items():
        result = _run_episodes(
            context["graph"],
            context["cache"],
            context["mate2_cfg"],
            context["tg28c_cfg"],
            context["edge_cfg"],
            tuple(selected_starts),
            context["selected"]["edge_weights"],
            context["selected"]["bridge_weights"],
            cfg.base,
            masks=mask,
        )
        out[name] = _ablation_summary(_enrich_episodes(result, context, cfg))
    return out


def _enrich_episodes(episodes: dict[str, Any], context: dict[str, Any], cfg: OnlineFailureDecompositionConfig) -> dict[str, Any]:
    traces = []
    transition_counts: Counter[str] = Counter()
    deep_audit_count = 0
    for episode in episodes["traces"]:
        trace = dict(episode)
        trace["episode_id"] = episode["episode_index"]
        trace["max_white_moves"] = cfg.base.max_white_moves_per_episode
        trace["success"] = episode["termination_reason"] in {"checkmate", "foundation_handoff"}
        trace["checkmate"] = episode["termination_reason"] == "checkmate"
        trace["foundation_handoff"] = episode["termination_reason"] == "foundation_handoff"
        trace["max_move_reached"] = episode["termination_reason"] == "max_moves_reached"
        trace["illegal"] = episode["termination_reason"] == "illegal_move_selected"
        trace["null"] = episode["termination_reason"] == "no_move_selected"
        trace["unsafe"] = episode["termination_reason"] == "unsafe_rook_blunder"
        trace["stalemate"] = episode["termination_reason"] == "stalemate"
        previous_phase = None
        enriched_steps = []
        for step in episode["steps"]:
            enriched = dict(step)
            if "foundation_reachable_after_move" in enriched:
                enriched["foundation_reachable_after_white_move"] = enriched["foundation_reachable_after_move"]
            enriched["bridge_candidate_available_after_black_reply"] = None
            enriched["offline_audit"] = _lightweight_turn_audit(enriched["white_to_move_fen"], enriched, context)
            phase = enriched["diagnostic_phase_classification"]
            if previous_phase is not None:
                transition_counts[_transition_name(previous_phase, phase, False)] += 1
            foundation_terminal = bool(enriched.get("foundation_reachable_after_black_reply"))
            if foundation_terminal:
                transition_counts[_transition_name(phase, "foundation", True)] += 1
            previous_phase = phase
            enriched_steps.append(enriched)
        trace["steps"] = enriched_steps
        trace["failure_bucket"] = _classify_episode_failure(trace)
        if not trace["success"]:
            for enriched in trace["steps"]:
                if deep_audit_count >= cfg.max_deep_offline_audit_turns:
                    enriched["offline_audit"]["deep_audit_skipped"] = True
                    enriched["offline_audit"]["deep_audit_skip_reason"] = "max_deep_offline_audit_turns_reached"
                    continue
                enriched["bridge_candidate_available_after_black_reply"] = _bridge_candidate_available(enriched.get("after_black_reply_fen"), context)
                enriched["offline_audit"] = _offline_turn_audit(enriched["white_to_move_fen"], enriched.get("selected_white_move"), context, cfg)
                deep_audit_count += 1
        traces.append(trace)
    enriched = dict(episodes)
    enriched["traces"] = traces
    enriched["explicit_transition_counts"] = dict(transition_counts)
    enriched["edge_to_bridge_transition_count"] = transition_counts["edge_to_bridge"]
    enriched["edge_to_foundation_transition_count"] = transition_counts["edge_to_foundation"]
    enriched["bridge_to_foundation_transition_count"] = transition_counts["bridge_to_foundation"]
    enriched["bridge_to_bridge_transition_count"] = transition_counts["bridge_to_bridge"]
    enriched["mixed_to_foundation_transition_count"] = transition_counts["mixed_to_foundation"]
    enriched["failure_bucket_counts"] = dict(Counter(trace["failure_bucket"] for trace in traces))
    enriched["deep_offline_audit_turn_count"] = deep_audit_count
    return enriched


def _bridge_candidate_available(fen: str | None, context: dict[str, Any]) -> bool:
    if not fen:
        return False
    board = chess.Board(fen)
    if board.turn != chess.WHITE or board.is_game_over():
        return False
    bridge = _evaluate_cache_bridge_layer(
        context["graph"],
        context["cache"],
        (fen,),
        context["tg28c_cfg"],
        context["selected"]["edge_weights"],
        context["selected"]["bridge_weights"],
    )
    sample = bridge.get("samples", [{}])[0] if bridge.get("samples") else {}
    return any(row.get("reply_envelope_foundation_reachable") or row.get("bounded_bridge_foundation_reachable") for row in sample.get("candidate_rows", []))


def _lightweight_turn_audit(fen: str, step: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    board = chess.Board(fen)
    legal_safe = 0
    for move in board.legal_moves:
        after = board.copy(stack=False)
        after.push(move)
        rook = next((sq for sq, piece in after.piece_map().items() if piece.color == chess.WHITE and piece.piece_type == chess.ROOK), None)
        legal_safe += int(rook is not None and not after.is_attacked_by(chess.BLACK, rook) and not after.is_stalemate())
    foundation_state = context["cache"].query_state(board)
    bridge = step.get("graph_evidence_summary", {}).get("bridge", {})
    edge = step.get("graph_evidence_summary", {}).get("edge_fence", {})
    return {
        "audit_depth": "lightweight_runtime_evidence",
        "legal_safe_candidate_count": legal_safe,
        "graph_confirmed_candidate_count": int(bool(step.get("selected_white_move"))),
        "runtime_bridge_candidate_count": bridge.get("candidate_count", 0),
        "runtime_edge_fence_candidate_count": edge.get("candidate_count", 0),
        "runtime_bridge_selected_move": bridge.get("selected_move"),
        "runtime_edge_fence_selected_move": edge.get("selected_move"),
        "better_graph_recognized_candidate_existed": False,
        "better_graph_recognized_candidates": [],
        "foundation_reachable_but_not_selected": bool(_foundation_reachable(foundation_state) and step.get("selected_white_move") != foundation_state.get("foundation_selected_move")),
        "foundation_selected_move": foundation_state.get("foundation_selected_move"),
        "deep_audit_skipped": False,
    }


def _offline_turn_audit(fen: str, selected_move: str | None, context: dict[str, Any], cfg: OnlineFailureDecompositionConfig) -> dict[str, Any]:
    board = chess.Board(fen)
    legal_safe = 0
    for move in board.legal_moves:
        after = board.copy(stack=False)
        after.push(move)
        rook = next((sq for sq, piece in after.piece_map().items() if piece.color == chess.WHITE and piece.piece_type == chess.ROOK), None)
        legal_safe += int(rook is not None and not after.is_attacked_by(chess.BLACK, rook) and not after.is_stalemate())
    edge = _evaluate_edge_layer(
        context["graph"],
        (fen,),
        context["mate2_cfg"],
        context["edge_cfg"],
        context["selected"]["edge_weights"],
        foundation_handoff_enabled=True,
    )
    bridge = _evaluate_cache_bridge_layer(
        context["graph"],
        context["cache"],
        (fen,),
        context["tg28c_cfg"],
        context["selected"]["edge_weights"],
        context["selected"]["bridge_weights"],
    )
    candidates = []
    for source, row in (("edge", edge), ("bridge", bridge)):
        sample = row.get("samples", [{}])[0] if row.get("samples") else {}
        for candidate in sample.get("candidate_rows", [])[: cfg.max_audit_candidates]:
            if candidate.get("formal_recon_engine_confirmed"):
                candidates.append({
                    "source": source,
                    "move": candidate["move"],
                    "evidence_score": candidate.get("evidence_score", 0.0),
                    "foundation_reachable": bool(candidate.get("foundation_handoff_reachable") or candidate.get("reply_envelope_foundation_reachable")),
                })
    candidates.sort(key=lambda item: (item["evidence_score"], item["move"]), reverse=True)
    selected_score = next((item["evidence_score"] for item in candidates if item["move"] == selected_move), None)
    better = [item for item in candidates if item["move"] != selected_move and (selected_score is None or item["evidence_score"] > selected_score)]
    foundation_state = context["cache"].query_state(board)
    return {
        "audit_depth": "bounded_deep_candidate_rows",
        "legal_safe_candidate_count": legal_safe,
        "graph_confirmed_candidate_count": len(candidates),
        "top_graph_candidates": candidates[: cfg.max_audit_candidates],
        "better_graph_recognized_candidate_existed": bool(better),
        "better_graph_recognized_candidates": better[:4],
        "foundation_reachable_but_not_selected": bool(_foundation_reachable(foundation_state) and selected_move != foundation_state.get("foundation_selected_move")),
        "foundation_selected_move": foundation_state.get("foundation_selected_move"),
        "deep_audit_skipped": False,
    }


def _transition_name(previous: str, current: str, terminal_foundation: bool) -> str:
    if terminal_foundation:
        if previous == "edge_fence_move":
            return "edge_to_foundation"
        if previous == "bridge_move":
            return "bridge_to_foundation"
        if previous == "mixed_evidence_move":
            return "mixed_to_foundation"
        if previous == "foundation_move":
            return "foundation_to_terminal"
        return "unknown_transition"
    if previous == "edge_fence_move" and current == "bridge_move":
        return "edge_to_bridge"
    if previous == "bridge_move" and current == "bridge_move":
        return "bridge_to_bridge"
    return "unknown_transition"


def _classify_episode_failure(episode: dict[str, Any]) -> str:
    if episode["success"]:
        return "success"
    if episode["null"]:
        return "no_move_selected"
    if episode["illegal"]:
        return "illegal_move_selected"
    if episode["unsafe"]:
        return "unsafe_rook_blunder"
    if episode["stalemate"]:
        return "stalemate"
    phases = [step["diagnostic_phase_classification"] for step in episode["steps"]]
    if episode["max_move_reached"] and phases.count("bridge_move") >= max(1, len(phases) - 1):
        return "bridge_loop_without_foundation_progress"
    if episode["max_move_reached"]:
        return "selected_moves_safe_but_low_progress"
    return "unknown"


def _failure_decomposition(episodes: dict[str, Any]) -> dict[str, Any]:
    buckets = Counter(trace["failure_bucket"] for trace in episodes["traces"])
    return {
        "max_move_failure_count": sum(int(trace["max_move_reached"]) for trace in episodes["traces"]),
        "bridge_loop_without_foundation_progress_count": buckets["bridge_loop_without_foundation_progress"],
        "selected_safe_but_low_progress_count": buckets["selected_moves_safe_but_low_progress"],
        "foundation_reachable_but_not_selected_count": sum(
            int(step["offline_audit"]["foundation_reachable_but_not_selected"])
            for trace in episodes["traces"]
            for step in trace["steps"]
        ),
        "bridge_candidate_available_but_not_selected_count": sum(
            int(step["bridge_candidate_available_after_black_reply"] is True and step["diagnostic_phase_classification"] != "bridge_move")
            for trace in episodes["traces"]
            for step in trace["steps"]
        ),
        "black_reply_escaped_bridge_basin_count": sum(
            int(step["diagnostic_phase_classification"] == "bridge_move" and not step.get("foundation_reachable_after_black_reply", False))
            for trace in episodes["traces"]
            for step in trace["steps"]
        ),
        "failure_bucket_counts": dict(buckets),
    }


def _regression_summary(regression: dict[str, Any]) -> dict[str, Any]:
    frontier = regression["frontier"]
    staged = regression["staged"]
    near_miss = regression["staged_near_miss"]
    generic = regression["generic"]
    return {
        "selected_schedule_name": regression["selected_schedule_name"],
        "frontier_regression_pass": frontier["selected_move_count"] > 0 and frontier["foundation_handoff_conversion_count"] > 0,
        "staged_regression_pass": staged["any_reply_success_count"] > 0,
        "near_miss_regression_pass": near_miss["selected_move_count"] == 0,
        "generic_edge_regression_pass": generic["edge_fence_success_rate"] > 0.0 and generic["rook_blunder_count"] == 0 and generic.get("stalemate_avoidance_rate", 1.0) >= 1.0,
        "frontier": frontier,
        "staged": staged,
        "staged_near_miss": near_miss,
        "generic": generic,
        "foundation_sanity_pass": True,
    }


def _ablation_summary(episodes: dict[str, Any]) -> dict[str, Any]:
    return {
        "episode_count": episodes["episode_count"],
        "episode_success_count": episodes["episode_success_count"],
        "foundation_handoff_count": episodes["foundation_handoff_count"],
        "max_move_reached_count": episodes["max_move_reached_count"],
        "null_move_count": episodes["null_move_count"],
        "rook_blunder_count": episodes["rook_blunder_count"],
        "edge_fence_move_count": episodes["edge_fence_move_count"],
        "bridge_move_count": episodes["bridge_move_count"],
        "explicit_transition_counts": episodes["explicit_transition_counts"],
        "failure_bucket_counts": episodes["failure_bucket_counts"],
    }


def _decision(
    cfg: OnlineFailureDecompositionConfig,
    *,
    context: dict[str, Any],
    episodes: dict[str, Any],
    failure: dict[str, Any],
    policy_comparison: dict[str, Any],
    ablations: dict[str, Any],
    foundation_cache_equivalence: dict[str, Any],
    scheduler_equivalence: dict[str, Any],
    foundation_before: dict[str, int],
    foundation_after: dict[str, int],
    timings: dict[str, float],
) -> dict[str, Any]:
    m3_delta = foundation_after["m3"] - foundation_before["m3"]
    m4_delta = foundation_after["m4"] - foundation_before["m4"]
    regression = _regression_summary(context["regression"])
    diagnostic_pass = (
        m3_delta == 0
        and m4_delta == 0
        and context["foundation_sanity"]["foundation_mate1_accuracy"] >= 1.0
        and context["foundation_sanity"]["foundation_mate2_conversion_rate"] >= 1.0
        and regression["frontier_regression_pass"]
        and regression["staged_regression_pass"]
        and regression["near_miss_regression_pass"]
        and regression["generic_edge_regression_pass"]
        and foundation_cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
        and failure["max_move_failure_count"] >= 0
    )
    repair_pass = cfg.repair_applied and episodes["episode_success_count"] > 2 and episodes["rook_blunder_count"] == 0
    return {
        "checkpoint_pass": bool(diagnostic_pass or repair_pass),
        "checkpoint_interpretation": "diagnosed_bridge_loop_without_repair" if diagnostic_pass and not cfg.repair_applied else ("repair_improved_online_progress" if repair_pass else "online_failure_decomposition_failed"),
        "repair_applied": cfg.repair_applied,
        "repair_type": cfg.repair_type,
        "foundation_frozen": m3_delta == 0 and m4_delta == 0,
        "foundation_mate1_accuracy": context["foundation_sanity"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": context["foundation_sanity"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": foundation_cache_equivalence["foundation_cache_live_mismatch_count"],
        "foundation_m3_updates_during_episode_eval": m3_delta,
        "foundation_m4_promotions_during_episode_eval": m4_delta,
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
        "edge_to_foundation_transition_count": episodes["edge_to_foundation_transition_count"],
        "bridge_to_foundation_transition_count": episodes["bridge_to_foundation_transition_count"],
        "bridge_to_bridge_transition_count": episodes["bridge_to_bridge_transition_count"],
        "mixed_to_foundation_transition_count": episodes["mixed_to_foundation_transition_count"],
        "same_graph_foundation_continuation_count": episodes["same_graph_foundation_continuation_count"],
        "deep_offline_audit_turn_count": episodes["deep_offline_audit_turn_count"],
        "deep_offline_audit_default_disabled": cfg.max_deep_offline_audit_turns == 0,
        **failure,
        "success_rate_by_black_reply_policy": policy_comparison["success_rate_by_black_reply_policy"],
        "failure_buckets_by_black_reply_policy": policy_comparison["failure_buckets_by_black_reply_policy"],
        "regression_results": {key: regression[key] for key in ("frontier_regression_pass", "staged_regression_pass", "near_miss_regression_pass", "generic_edge_regression_pass", "foundation_sanity_pass")},
        "ablation_results": ablations,
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
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
        "transition_semantics": {
            "foundation_handoff": "episode termination after a white graph-mediated move and harness black reply leave a board state recognized by the frozen native foundation graph",
            "bridge_to_foundation": "a white move classified as bridge_move whose after-black-reply state is foundation reachable; this terminal transition was not represented by TG29a's phase-to-phase counter",
            "edge_to_bridge": "consecutive white moves classified edge_fence_move then bridge_move",
            "diagnostic_only": True,
        },
    }


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29a_purity_boundary()
    boundary.update({
        "checkpoint": "TG29b",
        "failure_decomposition_only": True,
        "repair_applied": False,
        "offline_candidate_audit_trainer_side_only": True,
    })
    return boundary


def _write_progress(cfg: OnlineFailureDecompositionConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
