"""TG29f progress candidate selection repair."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
import time
from pathlib import Path
from typing import Any

import chess

from .frozen_foundation_edge_fence_reentry import _foundation_counts
from .frozen_foundation_response_cache_bridge_retrieval import _FoundationResponseCache
from .online_failure_decomposition import OnlineFailureDecompositionConfig, _enrich_episodes, _regression_summary
from .online_low_progress_repair import _progress_summary
from .reply_robust_bridge_pressure import _repair_weight_delta
from .reply_robust_progress_pool import (
    ReplyRobustProgressPoolConfig,
    _candidate_progress_score,
    _candidate_rows_for_pool,
    _compact_candidate_row,
    _merge_weights,
    _purity_boundary as _tg29e_purity_boundary,
    _tg29e_tg28c_cfg,
)
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .native_quorum_materialization import _tg26t_config
from .native_quorum_mate2_chaining import _tg26u_config
from .tiny_online_krk_episode_runner import (
    TinyOnlineKRKEpisodeRunnerConfig,
    _build_context,
    _run_episodes,
    _select_online_move,
    _write_progress as _write_tg29a_progress,
)


@dataclass(frozen=True)
class ProgressCandidateSelectionRepairConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("mixed_balanced_plus_staged",),
        episode_count=2,
        max_white_moves_per_episode=2,
        max_episode_ablation_count=0,
        progress_output="reports/autogrowth/krk_autogrowth_tg29f_progress_candidate_selection_repair_progress.json",
    )
    tg29e_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29e_reply_robust_progress_positive_pool.json"
    max_lost_turns: int = 2
    max_repair_cache_candidate_moves: int = 6
    max_reply_envelope_replies_per_candidate: int = 2
    arm_names: tuple[str, ...] = (
        "combined_reply_robust_baseline",
        "pairwise_contrastive_progress_evidence",
        "progress_dominance_terminal_only",
        "low_progress_hard_negative_veto",
        "spurious_bridge_support_veto",
        "combined_progress_selection_repair",
    )


@dataclass(frozen=True)
class ProgressCandidateSelectionRepairResult:
    config: ProgressCandidateSelectionRepairConfig
    lost_candidate_audit: dict[str, Any]
    pairwise_contrast_rows: list[dict[str, Any]]
    candidate_cap_retrieval_audit: dict[str, Any]
    arm_results: dict[str, Any]
    selected_arm_episodes: dict[str, Any]
    regression_results: dict[str, Any]
    foundation_cache_equivalence: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29f_progress_candidate_selection_repair.v0",
            "checkpoint": "TG29f_progress_candidate_selection_repair",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "lost_candidate_audit": self.lost_candidate_audit,
            "pairwise_contrast_rows": self.pairwise_contrast_rows,
            "candidate_cap_retrieval_audit": self.candidate_cap_retrieval_audit,
            "arm_results": self.arm_results,
            "selected_arm_episodes": self.selected_arm_episodes,
            "regression_results": self.regression_results,
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
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        d = self.decision
        output.write_text(
            "\n".join(
                [
                    "# TG29f Progress Candidate Selection Repair",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- selected_arm: `{d['selected_arm']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- lost turns audited: `{d['lost_turn_count']}`",
                    f"- explained lost turns: `{d['explained_lost_turn_count']}`",
                    f"- better selected after repair: `{d['better_progress_candidate_selected_after_repair_count']}`",
                    f"- episode success: `{d['episode_success_count']}` / `{d['episode_count']}`",
                    f"- low-progress failures: `{d['selected_moves_safe_but_low_progress_count']}`",
                    "",
                    "Interpretation: progress contrast labels are trainer-side. Runtime choice remains graph-mediated through native candidate evidence.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_progress_candidate_selection_repair(
    *,
    config: ProgressCandidateSelectionRepairConfig | None = None,
) -> ProgressCandidateSelectionRepairResult:
    cfg = config or ProgressCandidateSelectionRepairConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})
    context = _build_context(cfg.base)
    timings.update(context["timings"])
    graph = context["graph"]
    foundation_before = _foundation_counts(graph)
    tg29e_cfg = _tg29e_cfg(cfg, context)
    cache = _FoundationResponseCache(graph, context["mate2_cfg"], _tg29f_tg28c_cfg(cfg, context, tg29e_cfg))
    _write_progress(cfg, {"phase": "context_built", "selected_schedule": context["selected"]["schedule_name"]})

    start = time.perf_counter()
    seed_turns = _load_lost_turns(cfg)
    if not seed_turns:
        seed_turns = _fallback_lost_turns(cfg, context, cache, tg29e_cfg)
    lost_audit = _lost_candidate_audit(cfg, context, cache, tg29e_cfg, seed_turns)
    contrast_rows = _pairwise_contrast_rows(lost_audit)
    cap_audit = _candidate_cap_retrieval_audit(lost_audit)
    timings["lost_candidate_audit_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "lost_candidate_audit_complete", "lost_turns": lost_audit["lost_turn_count"]})

    start = time.perf_counter()
    arms = _arm_weight_deltas(contrast_rows)
    starts = tuple({"start_fen": row["start_fen"], "source": "tg29e_lost_low_progress_turn"} for row in lost_audit["turns"])[: cfg.base.episode_count]
    arm_results = _evaluate_arms(cfg, context, tg29e_cfg, starts, arms)
    selected_arm = _select_arm(arm_results)
    timings["arm_eval_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "arms_complete", "selected_arm": selected_arm})

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
        lost_audit=lost_audit,
        arm_results=arm_results,
        selected_arm=selected_arm,
        foundation_before=foundation_before,
        foundation_after=foundation_after,
        cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return ProgressCandidateSelectionRepairResult(
        config=cfg,
        lost_candidate_audit=lost_audit,
        pairwise_contrast_rows=contrast_rows,
        candidate_cap_retrieval_audit=cap_audit,
        arm_results=arm_results,
        selected_arm_episodes=arm_results[selected_arm]["episodes"],
        regression_results=_regression_summary(context["regression"]),
        foundation_cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _tg29e_cfg(cfg: ProgressCandidateSelectionRepairConfig, context: dict[str, Any]) -> ReplyRobustProgressPoolConfig:
    return ReplyRobustProgressPoolConfig(
        base=cfg.base,
        max_repair_cache_candidate_moves=cfg.max_repair_cache_candidate_moves,
        max_reply_envelope_replies_per_candidate=cfg.max_reply_envelope_replies_per_candidate,
    )


def _tg29f_tg28c_cfg(cfg: ProgressCandidateSelectionRepairConfig, context: dict[str, Any], tg29e_cfg: ReplyRobustProgressPoolConfig):
    return type(context["tg28c_cfg"])(
        **{
            **asdict(context["tg28c_cfg"]),
            "max_reply_envelope_replies_per_candidate": cfg.max_reply_envelope_replies_per_candidate,
            "max_cache_candidate_moves": cfg.max_repair_cache_candidate_moves,
        }
    )


def _load_lost_turns(cfg: ProgressCandidateSelectionRepairConfig) -> list[dict[str, Any]]:
    path = Path(cfg.tg29e_artifact_path)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    turns: list[dict[str, Any]] = []
    for episode in payload.get("candidate_audit", {}).get("audited_episodes", []):
        for turn in episode.get("turns", []):
            if turn.get("better_progress_candidate_lost_selection"):
                turns.append({
                    "start_fen": turn["start_fen"],
                    "selected_move": turn.get("selected_move"),
                    "source_episode_id": turn.get("source_episode_id"),
                    "source_turn_index": turn.get("source_turn_index"),
                })
    return turns[: cfg.max_lost_turns]


def _fallback_lost_turns(cfg: ProgressCandidateSelectionRepairConfig, context: dict[str, Any], cache: _FoundationResponseCache, tg29e_cfg: ReplyRobustProgressPoolConfig) -> list[dict[str, Any]]:
    starts = tuple({"start_fen": fen, "source": "fallback_generic_heldout"} for fen in context.get("generic_heldout", ()))[: cfg.base.episode_count]
    episodes = _run_policy(cfg, context, tg29e_cfg, starts, "combined_reply_robust_baseline", {}, {})["episodes"]
    turns = []
    for episode in episodes.get("traces", []):
        for step in episode.get("steps", []):
            if step.get("selected_white_move"):
                turns.append({"start_fen": step["white_to_move_fen"], "selected_move": step["selected_white_move"], "source_episode_id": episode["episode_index"], "source_turn_index": step["move_index"]})
    return turns[: cfg.max_lost_turns]


def _lost_candidate_audit(
    cfg: ProgressCandidateSelectionRepairConfig,
    context: dict[str, Any],
    cache: _FoundationResponseCache,
    tg29e_cfg: ReplyRobustProgressPoolConfig,
    seed_turns: list[dict[str, Any]],
) -> dict[str, Any]:
    turns = []
    totals: Counter[str] = Counter()
    for turn in seed_turns:
        board = chess.Board(turn["start_fen"])
        baseline_selection = _select_with_deltas(cfg, context, cache, tg29e_cfg, board, {}, {})
        selected_move = turn.get("selected_move") or baseline_selection.get("selected_white_move")
        rows = _compact_rows(cfg, context, cache, tg29e_cfg, board, selected_move)
        selected = next((row for row in rows if row["candidate_move"] == selected_move), None)
        better_rows = [row for row in rows if _candidate_progress_score(row) > _candidate_progress_score(selected) and row["classification"] in {"partial_progress", "strong_reply_robust_progress"}]
        best_better = max(better_rows, key=_candidate_progress_score) if better_rows else None
        loss_reason = _loss_reason(selected, best_better)
        totals[loss_reason] += 1
        totals["lost_turn_count"] += 1
        totals["better_available_count"] += int(best_better is not None)
        totals["explained_lost_turn_count"] += int(loss_reason in {"progress_magnitude_not_materialized", "evidence_tie_or_near_tie", "progress_evidence_weights_favor_weaker_candidate"})
        turns.append({
            "start_fen": turn["start_fen"],
            "source_episode_id": turn.get("source_episode_id"),
            "source_turn_index": turn.get("source_turn_index"),
            "selected_move": selected_move,
            "best_better_progress_move": None if best_better is None else best_better["candidate_move"],
            "loss_reason": loss_reason,
            "selected_candidate": _candidate_audit_row(selected),
            "best_better_candidate": _candidate_audit_row(best_better),
            "better_candidate_count": len(better_rows),
            "legal_candidate_count": len(rows),
            "legal_candidate_alternatives": rows[:12],
        })
    return {
        "lost_turn_count": totals["lost_turn_count"],
        "better_available_count": totals["better_available_count"],
        "explained_lost_turn_count": totals["explained_lost_turn_count"],
        "loss_reason_counts": dict(totals),
        "turns": turns,
    }


def _compact_rows(cfg, context, cache, tg29e_cfg, board, selected_move):
    rows = _candidate_rows_for_pool(tg29e_cfg, context, cache, board)
    compact = [_compact_candidate_row(tg29e_cfg, context, cache, board, row, selected_move=selected_move) for row in rows]
    ranked = sorted(compact, key=lambda row: (row.get("evidence_score") or -999.0, row["candidate_move"]), reverse=True)
    for index, row in enumerate(ranked, start=1):
        row["current_graph_evidence_rank"] = index
    progress_ranked = sorted(compact, key=_candidate_progress_score, reverse=True)
    for index, row in enumerate(progress_ranked, start=1):
        row["progress_rank"] = index
    return compact


def _candidate_audit_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    p = row["progress_metrics"]
    return {
        "candidate_move": row["candidate_move"],
        "classification": row["classification"],
        "selected": row["selected"],
        "safe": row["safe"],
        "progress_score": round(_candidate_progress_score(row), 6),
        "evidence_score": row.get("evidence_score"),
        "cheap_score": row.get("cheap_score"),
        "current_graph_evidence_rank": row.get("current_graph_evidence_rank"),
        "progress_rank": row.get("progress_rank"),
        "progress_metrics": p,
        "terminal_support": {
            "edge_fence_evidence": row.get("edge_fence_evidence"),
            "bridge_pressure_evidence": row.get("bridge_pressure_evidence"),
            "foundation_response_evidence": row.get("foundation_response_evidence"),
            "formal_recon_engine_confirmed": row.get("formal_recon_engine_confirmed"),
            "graph_confirmation_state": row.get("graph_confirmation_state"),
        },
        "positive_feature_keys": row.get("positive_feature_keys", []),
        "bridge_feature_keys": row.get("bridge_feature_keys", []),
    }


def _loss_reason(selected: dict[str, Any] | None, better: dict[str, Any] | None) -> str:
    if selected is None:
        return "null_selection"
    if better is None:
        return "no_better_progress_candidate"
    score_gap = float(better.get("evidence_score") or 0.0) - float(selected.get("evidence_score") or 0.0)
    p_sel = selected["progress_metrics"]
    p_better = better["progress_metrics"]
    magnitude_gap = (
        max(0.0, -float(p_better["confinement_area_delta"])) - max(0.0, -float(p_sel["confinement_area_delta"]))
        + max(0.0, -float(p_better["black_king_mobility_delta"])) - max(0.0, -float(p_sel["black_king_mobility_delta"]))
    )
    if abs(score_gap) <= 0.001 and magnitude_gap > 0.0:
        return "progress_magnitude_not_materialized"
    if abs(score_gap) <= 0.05:
        return "evidence_tie_or_near_tie"
    if score_gap < 0.0:
        return "progress_evidence_weights_favor_weaker_candidate"
    return "unexplained_progress_selection_loss"


def _pairwise_contrast_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for turn in audit["turns"]:
        selected = turn["selected_candidate"]
        better = turn["best_better_candidate"]
        if not selected or not better:
            continue
        selected_keys = set(selected["positive_feature_keys"])
        better_keys = set(better["positive_feature_keys"])
        selected_bridge = set(selected["bridge_feature_keys"])
        better_bridge = set(better["bridge_feature_keys"])
        out.append({
            "start_fen": turn["start_fen"],
            "selected_low_progress_candidate": selected["candidate_move"],
            "better_progress_candidate": better["candidate_move"],
            "relation": "better_progress_candidate > selected_low_progress_candidate",
            "positive_edge_feature_keys": sorted(better_keys - selected_keys),
            "negative_edge_feature_keys": sorted(selected_keys - better_keys),
            "positive_bridge_feature_keys": sorted(better_bridge - selected_bridge),
            "negative_bridge_feature_keys": sorted(selected_bridge - better_bridge),
            "selected_progress_score": selected["progress_score"],
            "better_progress_score": better["progress_score"],
            "selected_evidence_score": selected["evidence_score"],
            "better_evidence_score": better["evidence_score"],
            "trainer_side_contrast_label_only": True,
            "learner_visible_stage_labels": False,
        })
    return out


def _candidate_cap_retrieval_audit(audit: dict[str, Any]) -> dict[str, Any]:
    rows = []
    totals: Counter[str] = Counter()
    for turn in audit["turns"]:
        better = turn["best_better_candidate"]
        rows.append({
            "start_fen": turn["start_fen"],
            "selected_move": turn["selected_move"],
            "best_better_progress_move": turn["best_better_progress_move"],
            "candidate_count": turn["legal_candidate_count"],
            "better_candidate_indexed": better is not None,
            "better_candidate_graph_confirmed": bool(better and better["terminal_support"]["formal_recon_engine_confirmed"]),
            "better_candidate_evidence_rank": None if better is None else better["current_graph_evidence_rank"],
            "better_candidate_progress_rank": None if better is None else better["progress_rank"],
        })
        totals["candidate_count"] += turn["legal_candidate_count"]
        totals["better_candidate_indexed_count"] += int(better is not None)
        totals["better_candidate_graph_confirmed_count"] += int(bool(better and better["terminal_support"]["formal_recon_engine_confirmed"]))
    return {
        "turns": rows,
        "average_candidate_count": totals["candidate_count"] / max(1, len(rows)),
        "better_candidate_indexed_count": totals["better_candidate_indexed_count"],
        "better_candidate_graph_confirmed_count": totals["better_candidate_graph_confirmed_count"],
        "candidate_cap_primary_failure": totals["better_candidate_indexed_count"] < len(rows),
    }


def _arm_weight_deltas(contrast_rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, float]]]:
    pairwise_edge: dict[str, float] = {}
    pairwise_bridge: dict[str, float] = {}
    dominance_edge: dict[str, float] = {}
    dominance_bridge: dict[str, float] = {}
    low_veto_edge: dict[str, float] = {}
    low_veto_bridge: dict[str, float] = {}
    spurious_bridge: dict[str, float] = {}
    for row in contrast_rows:
        for key in row["positive_edge_feature_keys"]:
            pairwise_edge[key] = pairwise_edge.get(key, 0.0) + 0.35
            if "gain_bucket=" in key:
                dominance_edge[key] = dominance_edge.get(key, 0.0) + 0.30
        for key in row["negative_edge_feature_keys"]:
            pairwise_edge[key] = pairwise_edge.get(key, 0.0) - 0.20
            if "gain_bucket=0" in key or "gain_bucket=1" in key:
                low_veto_edge[key] = low_veto_edge.get(key, 0.0) - 0.35
        for key in row["positive_bridge_feature_keys"]:
            pairwise_bridge[key] = pairwise_bridge.get(key, 0.0) + 0.25
            if "gain_bucket=" in key:
                dominance_bridge[key] = dominance_bridge.get(key, 0.0) + 0.20
        for key in row["negative_bridge_feature_keys"]:
            pairwise_bridge[key] = pairwise_bridge.get(key, 0.0) - 0.15
            if "gain_bucket=0" in key or "gain_bucket=1" in key:
                low_veto_bridge[key] = low_veto_bridge.get(key, 0.0) - 0.25
        spurious_bridge["reply_envelope_any_foundation=0"] = spurious_bridge.get("reply_envelope_any_foundation=0", 0.0) - 0.20
        spurious_bridge["reply_envelope_rate_bucket=0"] = spurious_bridge.get("reply_envelope_rate_bucket=0", 0.0) - 0.20
    combined_edge = _merge_weights(pairwise_edge, dominance_edge, low_veto_edge)
    combined_bridge = _merge_weights(pairwise_bridge, dominance_bridge, low_veto_bridge, spurious_bridge)
    return {
        "combined_reply_robust_baseline": {"edge": {}, "bridge": _repair_weight_delta("combined_reply_robust")},
        "pairwise_contrastive_progress_evidence": {"edge": pairwise_edge, "bridge": _merge_weights(_repair_weight_delta("combined_reply_robust"), pairwise_bridge)},
        "progress_dominance_terminal_only": {"edge": dominance_edge, "bridge": _merge_weights(_repair_weight_delta("combined_reply_robust"), dominance_bridge)},
        "low_progress_hard_negative_veto": {"edge": low_veto_edge, "bridge": _merge_weights(_repair_weight_delta("combined_reply_robust"), low_veto_bridge)},
        "spurious_bridge_support_veto": {"edge": {}, "bridge": _merge_weights(_repair_weight_delta("combined_reply_robust"), spurious_bridge)},
        "combined_progress_selection_repair": {"edge": combined_edge, "bridge": _merge_weights(_repair_weight_delta("combined_reply_robust"), combined_bridge)},
    }


def _evaluate_arms(cfg, context, tg29e_cfg, starts, arms):
    out = {}
    for arm in cfg.arm_names:
        _write_progress(cfg, {"phase": "arm_start", "arm": arm})
        deltas = arms[arm]
        cache = _FoundationResponseCache(context["graph"], context["mate2_cfg"], _tg29f_tg28c_cfg(cfg, context, tg29e_cfg))
        lost_turns = []
        for start in starts:
            board = chess.Board(start["start_fen"])
            selection = _select_with_deltas(cfg, context, cache, tg29e_cfg, board, deltas["edge"], deltas["bridge"])
            rows = _compact_rows(cfg, context, cache, tg29e_cfg, board, selection.get("selected_white_move"))
            selected = next((row for row in rows if row["candidate_move"] == selection.get("selected_white_move")), None)
            best = max(rows, key=_candidate_progress_score) if rows else None
            lost_turns.append({
                "start_fen": start["start_fen"],
                "selected_move": selection.get("selected_white_move"),
                "best_progress_move": None if best is None else best["candidate_move"],
                "selected_is_best_progress": bool(selected and best and selected["candidate_move"] == best["candidate_move"]),
                "selected_progress_score": None if selected is None else round(_candidate_progress_score(selected), 6),
                "best_progress_score": None if best is None else round(_candidate_progress_score(best), 6),
                "selection": selection,
            })
        policy = _run_policy(cfg, context, tg29e_cfg, starts, arm, deltas["edge"], deltas["bridge"])
        out[arm] = {
            "arm": arm,
            "edge_weight_delta": deltas["edge"],
            "bridge_weight_delta": deltas["bridge"],
            "lost_turn_selection_audit": lost_turns,
            "better_progress_candidate_selected_count": sum(int(row["selected_is_best_progress"]) for row in lost_turns),
            "summary": policy["summary"],
            "progress_summary": policy["progress_summary"],
            "episodes": policy["episodes"],
        }
        _write_progress(cfg, {
            "phase": "arm_complete",
            "arm": arm,
            "better_progress_candidate_selected_count": out[arm]["better_progress_candidate_selected_count"],
            "episode_success_count": policy["progress_summary"]["episode_success_count"],
            "selected_moves_safe_but_low_progress_count": policy["progress_summary"]["selected_moves_safe_but_low_progress_count"],
            "bridge_loop_without_foundation_progress_count": policy["progress_summary"]["bridge_loop_without_foundation_progress_count"],
        })
    return out


def _select_with_deltas(cfg, context, cache, tg29e_cfg, board, edge_delta, bridge_delta):
    edge_weights = _merge_weights(context["selected"]["edge_weights"], edge_delta)
    bridge_weights = _merge_weights(context["selected"]["bridge_weights"], bridge_delta)
    return _select_online_move(
        context["graph"],
        cache,
        context["mate2_cfg"],
        _tg29f_tg28c_cfg(cfg, context, tg29e_cfg),
        context["edge_cfg"],
        board,
        edge_weights,
        bridge_weights,
        masks={},
    )


def _run_policy(cfg, context, tg29e_cfg, starts, arm_name, edge_delta, bridge_delta):
    cache = _FoundationResponseCache(context["graph"], context["mate2_cfg"], _tg29f_tg28c_cfg(cfg, context, tg29e_cfg))
    edge_weights = _merge_weights(context["selected"]["edge_weights"], edge_delta)
    bridge_weights = _merge_weights(context["selected"]["bridge_weights"], bridge_delta)
    episodes = _run_episodes(
        context["graph"],
        cache,
        context["mate2_cfg"],
        _tg29f_tg28c_cfg(cfg, context, tg29e_cfg),
        context["edge_cfg"],
        starts,
        edge_weights,
        bridge_weights,
        cfg.base,
        masks={},
    )
    episodes = _enrich_episodes(episodes, context | {"cache": cache, "tg28c_cfg": _tg29f_tg28c_cfg(cfg, context, tg29e_cfg)}, OnlineFailureDecompositionConfig(base=cfg.base))
    return {"arm_name": arm_name, "episodes": episodes, "summary": _summary(_progress_summary(episodes)), "progress_summary": _progress_summary(episodes)}


def _summary(progress: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "episode_count",
        "episode_success_count",
        "episode_success_rate",
        "checkmate_count",
        "foundation_handoff_count",
        "max_move_reached_count",
        "illegal_move_count",
        "null_move_count",
        "rook_blunder_count",
        "stalemate_count",
        "unsafe_move_count",
        "bridge_loop_without_foundation_progress_count",
        "selected_moves_safe_but_low_progress_count",
    )
    return {key: progress[key] for key in keys}


def _select_arm(arm_results: dict[str, Any]) -> str:
    baseline = arm_results["combined_reply_robust_baseline"]["progress_summary"]
    candidates = []
    for arm, row in arm_results.items():
        p = row["progress_summary"]
        safety_clean = p["rook_blunder_count"] == 0 and p["illegal_move_count"] == 0 and p["stalemate_count"] == 0
        better_delta = row["better_progress_candidate_selected_count"] - arm_results["combined_reply_robust_baseline"]["better_progress_candidate_selected_count"]
        low_delta = baseline["selected_moves_safe_but_low_progress_count"] - p["selected_moves_safe_but_low_progress_count"]
        success_delta = p["episode_success_count"] - baseline["episode_success_count"]
        candidates.append((int(arm != "combined_reply_robust_baseline" and safety_clean and (better_delta > 0 or low_delta > 0 or success_delta > 0)), better_delta, low_delta, success_delta, arm))
    best = max(candidates)
    return best[-1] if best[0] else "combined_reply_robust_baseline"


def _decision(cfg, *, context, lost_audit, arm_results, selected_arm, foundation_before, foundation_after, cache_equivalence, scheduler_equivalence, timings):
    selected = arm_results[selected_arm]
    baseline = arm_results["combined_reply_robust_baseline"]
    selected_progress = selected["progress_summary"]
    baseline_progress = baseline["progress_summary"]
    m3_delta = foundation_after["m3"] - foundation_before["m3"]
    m4_delta = foundation_after["m4"] - foundation_before["m4"]
    regression = _regression_summary(context["regression"])
    regression_clean = all(regression[key] for key in ("frontier_regression_pass", "staged_regression_pass", "near_miss_regression_pass", "generic_edge_regression_pass", "foundation_sanity_pass"))
    safety_clean = selected_progress["rook_blunder_count"] == 0 and selected_progress["illegal_move_count"] == 0 and selected_progress["stalemate_count"] == 0
    better_selected_delta = selected["better_progress_candidate_selected_count"] - baseline["better_progress_candidate_selected_count"]
    low_progress_reduced = selected_progress["selected_moves_safe_but_low_progress_count"] < baseline_progress["selected_moves_safe_but_low_progress_count"]
    success_improved = selected_progress["episode_success_count"] > baseline_progress["episode_success_count"]
    diagnostic_pass = (
        lost_audit["explained_lost_turn_count"] == lost_audit["lost_turn_count"]
        and lost_audit["lost_turn_count"] > 0
        and safety_clean
        and regression_clean
        and m3_delta == 0
        and m4_delta == 0
        and cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
    )
    repair_pass = (
        selected_arm != "combined_reply_robust_baseline"
        and better_selected_delta > 0
        and (low_progress_reduced or success_improved)
        and diagnostic_pass
    )
    return {
        "checkpoint_pass": bool(repair_pass or diagnostic_pass),
        "checkpoint_interpretation": "progress_selection_repaired_graph_mediated" if repair_pass else "lost_candidates_explained_repair_not_yet_episode_improving",
        "selected_arm": selected_arm,
        "repair_applied": bool(repair_pass),
        "foundation_frozen": m3_delta == 0 and m4_delta == 0,
        "foundation_mate1_accuracy": context["foundation_sanity"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": context["foundation_sanity"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": cache_equivalence["foundation_cache_live_mismatch_count"],
        "foundation_m3_updates_during_eval": m3_delta,
        "foundation_m4_promotions_during_eval": m4_delta,
        "lost_turn_count": lost_audit["lost_turn_count"],
        "better_available_count": lost_audit["better_available_count"],
        "explained_lost_turn_count": lost_audit["explained_lost_turn_count"],
        "better_progress_candidate_selected_after_repair_count": selected["better_progress_candidate_selected_count"],
        "better_progress_candidate_selected_baseline_count": baseline["better_progress_candidate_selected_count"],
        **{key: selected_progress[key] for key in (
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
            "bridge_loop_without_foundation_progress_count",
            "selected_moves_safe_but_low_progress_count",
            "meaningful_edge_progress_count",
            "meaningful_bridge_progress_count",
            "meaningful_foundation_progress_count",
        )},
        "baseline_selected_moves_safe_but_low_progress_count": baseline_progress["selected_moves_safe_but_low_progress_count"],
        "baseline_episode_success_count": baseline_progress["episode_success_count"],
        "frontier_regression_pass": regression["frontier_regression_pass"],
        "staged_regression_pass": regression["staged_regression_pass"],
        "near_miss_regression_pass": regression["near_miss_regression_pass"],
        "generic_edge_regression_pass": regression["generic_edge_regression_pass"],
        "foundation_sanity_pass": regression["foundation_sanity_pass"],
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "phase_timings": timings,
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


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29e_purity_boundary()
    boundary.update({
        "checkpoint": "TG29f",
        "progress_contrast_labels_trainer_side_only": True,
        "progress_selection_repair": "graph_mediated_feature_terminal_weight_deltas",
        "direct_provider_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "learner_visible_stage_labels": False,
    })
    return boundary


def _write_progress(cfg: ProgressCandidateSelectionRepairConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
