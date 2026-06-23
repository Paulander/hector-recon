"""TG29g trajectory-positive prefix audit."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import chess

from .frozen_foundation_edge_fence_reentry import _cheap_candidate_rows, _foundation_counts
from .frozen_foundation_response_cache_bridge_retrieval import _FoundationResponseCache
from .online_failure_decomposition import OnlineFailureDecompositionConfig, _enrich_episodes, _regression_summary
from .online_low_progress_repair import _progress_summary
from .progress_candidate_selection_repair import (
    ProgressCandidateSelectionRepairConfig,
    _select_with_deltas,
    _tg29f_tg28c_cfg,
)
from .reply_robust_bridge_pressure import _repair_weight_delta
from .reply_robust_progress_pool import (
    ReplyRobustProgressPoolConfig,
    _candidate_rows_for_pool,
    _compact_candidate_row,
    _merge_weights,
)
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .native_quorum_materialization import _tg26t_config
from .native_quorum_mate2_chaining import _tg26u_config
from .tiny_online_krk_episode_runner import (
    TinyOnlineKRKEpisodeRunnerConfig,
    _build_context,
    _foundation_reachable,
    _run_episodes,
    _safety_result,
    _select_black_reply,
    _select_online_move,
    _write_progress as _write_tg29a_progress,
)


@dataclass(frozen=True)
class TrajectoryPositivePrefixAuditConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("mixed_balanced_plus_staged",),
        episode_count=2,
        max_white_moves_per_episode=2,
        max_episode_ablation_count=0,
        progress_output="reports/autogrowth/krk_autogrowth_tg29g_trajectory_positive_prefix_audit_progress.json",
    )
    tg29f_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29f_progress_candidate_selection_repair.json"
    pool_path: str = "reports/autogrowth/pools/tg29g_trajectory_positive_prefix_pool.jsonl"
    pool_index_path: str = "reports/autogrowth/pools/tg29g_trajectory_positive_prefix_pool_index.json"
    black_reply_policies: tuple[str, ...] = ("deterministic_worst_foundation_reply", "mobility_maximizing")
    max_failure_starts: int = 2
    max_safe_candidates_per_start: int = 0
    max_repair_cache_candidate_moves: int = 6
    max_reply_envelope_replies_per_candidate: int = 2
    run_optional_repair: bool = True
    audit_context_profile: str = "full"
    throughput_note: str = ""


@dataclass(frozen=True)
class TrajectoryPositivePrefixAuditResult:
    config: TrajectoryPositivePrefixAuditConfig
    trajectory_audit: dict[str, Any]
    comparison: dict[str, Any]
    pool_index: dict[str, Any]
    optional_repair: dict[str, Any]
    regression_results: dict[str, Any]
    foundation_cache_equivalence: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29g_trajectory_positive_prefix_audit.v0",
            "checkpoint": "TG29g_trajectory_positive_prefix_audit",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "trajectory_audit": self.trajectory_audit,
            "comparison": self.comparison,
            "pool_index": self.pool_index,
            "optional_repair": self.optional_repair,
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
                    "# TG29g Trajectory-Positive Prefix Audit",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- trajectory-positive candidates: `{d['trajectory_positive_candidate_count']}`",
                    f"- trajectory-positive lost selections: `{d['trajectory_positive_candidate_lost_selection_count']}`",
                    f"- pool entries: `{d['trajectory_pool_entry_count']}`",
                    f"- audited candidates / rollouts: `{d['audited_candidate_count']}` / `{d['trajectory_rollout_count']}`",
                    f"- average seconds per candidate: `{d['average_seconds_per_candidate']}`",
                    f"- bounded episode success: `{d['bounded_episode_success_count']}` / `{d['bounded_episode_count']}`",
                    f"- low-progress / bridge-loop failures: `{d['selected_moves_safe_but_low_progress_count']}` / `{d['bridge_loop_without_foundation_progress_count']}`",
                    "",
                    "Interpretation: trajectory labels are trainer-side audit labels. Runtime choices remain graph-mediated.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_trajectory_positive_prefix_audit(
    *,
    config: TrajectoryPositivePrefixAuditConfig | None = None,
) -> TrajectoryPositivePrefixAuditResult:
    cfg = config or TrajectoryPositivePrefixAuditConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})

    context = _build_context(cfg.base)
    timings.update(context["timings"])
    graph = context["graph"]
    foundation_before = _foundation_counts(graph)
    tg29f_cfg = _tg29f_cfg(cfg)
    tg28c_cfg = _tg29f_tg28c_cfg(_as_tg29f_repair_cfg(cfg), context, tg29f_cfg)
    cache = _FoundationResponseCache(graph, context["mate2_cfg"], tg28c_cfg)
    _write_progress(cfg, {"phase": "context_built", "selected_schedule": context["selected"]["schedule_name"]})

    start = time.perf_counter()
    failure_starts = _failure_starts(cfg)
    timings["candidate_audit_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    trajectory_audit = _trajectory_audit(cfg, context, cache, tg29f_cfg, failure_starts)
    timings["trajectory_rollout_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {
        "phase": "trajectory_audit_complete",
        "audited_candidate_count": trajectory_audit["audited_candidate_count"],
        "trajectory_positive_candidate_count": trajectory_audit["trajectory_positive_candidate_count"],
    })

    start = time.perf_counter()
    comparison = _comparison(trajectory_audit)
    pool_entries, pool_index = _write_pool(cfg, context, trajectory_audit)
    timings["artifact_write_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "pool_written", "entries": pool_index["trajectory_pool_entry_count"]})

    start = time.perf_counter()
    optional_repair = _optional_repair(cfg, context, tg29f_cfg, trajectory_audit, comparison)
    timings["optional_repair_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    regression = _regression_summary(context["regression"])
    cache_equivalence = context["cache"].live_equivalence_audit(max_samples=min(8, cfg.base.max_samples))
    scheduler_equivalence = _scheduler_equivalence(
        _tg26s_config(_tg26t_config(_tg26u_config(context["mate2_cfg"]))),
        context["mate1_train"],
        context["mate1_heldout"],
    )
    timings["regression_seconds"] = round(time.perf_counter() - start, 6)

    foundation_after = _foundation_counts(graph)
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)
    decision = _decision(
        cfg,
        context=context,
        trajectory_audit=trajectory_audit,
        comparison=comparison,
        pool_index=pool_index,
        optional_repair=optional_repair,
        regression=regression,
        foundation_before=foundation_before,
        foundation_after=foundation_after,
        cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return TrajectoryPositivePrefixAuditResult(
        config=cfg,
        trajectory_audit=trajectory_audit,
        comparison=comparison,
        pool_index=pool_index,
        optional_repair=optional_repair,
        regression_results=regression,
        foundation_cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _as_tg29f_repair_cfg(cfg: TrajectoryPositivePrefixAuditConfig) -> ProgressCandidateSelectionRepairConfig:
    return ProgressCandidateSelectionRepairConfig(
        base=cfg.base,
        max_repair_cache_candidate_moves=cfg.max_repair_cache_candidate_moves,
        max_reply_envelope_replies_per_candidate=cfg.max_reply_envelope_replies_per_candidate,
    )


def _tg29f_cfg(cfg: TrajectoryPositivePrefixAuditConfig) -> ReplyRobustProgressPoolConfig:
    return ReplyRobustProgressPoolConfig(
        base=cfg.base,
        max_repair_cache_candidate_moves=cfg.max_repair_cache_candidate_moves,
        max_reply_envelope_replies_per_candidate=cfg.max_reply_envelope_replies_per_candidate,
    )


def _failure_starts(cfg: TrajectoryPositivePrefixAuditConfig) -> list[dict[str, Any]]:
    path = Path(cfg.tg29f_artifact_path)
    if not path.exists():
        return [
            {"start_fen": "8/8/5R2/8/1k6/8/4K3/8 w - - 0 1", "source": "tg29f_known_failure_fallback"},
            {"start_fen": "8/4R3/8/k7/8/3K4/8/8 w - - 0 1", "source": "tg29f_known_failure_fallback"},
        ][: cfg.max_failure_starts]
    payload = json.loads(path.read_text(encoding="utf-8"))
    traces = payload.get("selected_arm_episodes", {}).get("traces", [])
    starts = []
    for trace in traces:
        if trace.get("failure_bucket") in {"selected_moves_safe_but_low_progress", "bridge_loop_without_foundation_progress"} or trace.get("episode_success_count") == 0:
            starts.append({
                "start_fen": trace["start_fen"],
                "source": "tg29f_selected_arm_failure",
                "failure_bucket": trace.get("failure_bucket"),
                "tg29f_first_move": (trace.get("steps") or [{}])[0].get("selected_white_move"),
            })
    if not starts:
        for trace in traces:
            starts.append({"start_fen": trace["start_fen"], "source": "tg29f_selected_arm_trace"})
    return starts[: cfg.max_failure_starts]


def _trajectory_audit(
    cfg: TrajectoryPositivePrefixAuditConfig,
    context: dict[str, Any],
    cache: _FoundationResponseCache,
    tg29f_cfg: ReplyRobustProgressPoolConfig,
    starts: list[dict[str, Any]],
) -> dict[str, Any]:
    totals: Counter[str] = Counter()
    start_rows = []
    cache_before = cache.query_count
    for start_index, start in enumerate(starts):
        board = chess.Board(start["start_fen"])
        baseline_selection = _select_with_deltas(_as_tg29f_repair_cfg(cfg), context, cache, tg29f_cfg, board, {}, _repair_weight_delta("combined_reply_robust"))
        pairwise_selection = {"selected_white_move": start.get("tg29f_first_move")}
        rows = _safe_first_candidate_rows(cfg, context, cache, tg29f_cfg, board, baseline_selection.get("selected_white_move"))
        candidate_rows = []
        for candidate_index, row in enumerate(rows):
            _write_progress(cfg, {"phase": "trajectory_candidate", "start_index": start_index, "candidate_index": candidate_index, "move": row["candidate_move"]})
            policy_rows = [
                _trajectory_for_policy(cfg, context, cache, tg29f_cfg, board, row, policy)
                for policy in cfg.black_reply_policies
            ]
            classification = _aggregate_classification(policy_rows, row)
            trajectory_score = _trajectory_score(classification, policy_rows)
            totals[classification + "_candidate_count"] += 1
            totals["audited_candidate_count"] += 1
            totals["trajectory_rollout_count"] += len(policy_rows)
            totals["deep_reply_checks_run"] += sum(item["deep_reply_checks_run"] for item in policy_rows)
            candidate_rows.append({
                **row,
                "trajectory_classification": classification,
                "trajectory_score": trajectory_score,
                "policy_rollouts": policy_rows,
            })
        current = baseline_selection.get("selected_white_move")
        pairwise = pairwise_selection.get("selected_white_move")
        best_local = _best(candidate_rows, key=lambda row: row["local_progress_score"])
        best_traj = _best(candidate_rows, key=lambda row: row["trajectory_score"])
        trajectory_exists = any(row["trajectory_classification"] == "trajectory_positive" for row in candidate_rows)
        trajectory_lost = bool(trajectory_exists and current != (best_traj or {}).get("candidate_move"))
        totals["trajectory_positive_candidate_exists_count"] += int(trajectory_exists)
        totals["trajectory_positive_candidate_lost_selection_count"] += int(trajectory_lost)
        totals["local_progress_beats_trajectory_progress_count"] += int(best_local and best_traj and best_local["candidate_move"] != best_traj["candidate_move"])
        totals["no_trajectory_positive_candidate_exists_count"] += int(not trajectory_exists)
        start_rows.append({
            **start,
            "current_graph_selected_move": current,
            "tg29f_pairwise_selected_move": pairwise,
            "best_local_progress_move": None if best_local is None else best_local["candidate_move"],
            "best_trajectory_positive_move": None if best_traj is None else best_traj["candidate_move"],
            "trajectory_positive_candidate_exists": trajectory_exists,
            "trajectory_positive_candidate_lost_selection": trajectory_lost,
            "local_progress_winner_differs_from_trajectory_winner": bool(best_local and best_traj and best_local["candidate_move"] != best_traj["candidate_move"]),
            "failure_bucket": _failure_bucket(current, pairwise, best_local, best_traj, trajectory_exists),
            "candidate_rows": candidate_rows,
        })
    return {
        "audited_failure_start_count": len(start_rows),
        "audited_candidate_count": totals["audited_candidate_count"],
        "trajectory_rollout_count": totals["trajectory_rollout_count"],
        "trajectory_positive_candidate_count": totals["trajectory_positive_candidate_count"],
        "trajectory_partial_positive_candidate_count": totals["trajectory_partial_positive_candidate_count"],
        "local_progress_only_candidate_count": totals["local_progress_only_candidate_count"],
        "safe_low_progress_candidate_count": totals["safe_low_progress_candidate_count"],
        "bridge_loop_inducing_candidate_count": totals["bridge_loop_inducing_candidate_count"],
        "unsafe_candidate_count": totals["unsafe_candidate_count"],
        "unknown_candidate_count": totals["unknown_candidate_count"],
        "trajectory_positive_candidate_exists_count": totals["trajectory_positive_candidate_exists_count"],
        "trajectory_positive_candidate_lost_selection_count": totals["trajectory_positive_candidate_lost_selection_count"],
        "local_progress_beats_trajectory_progress_count": totals["local_progress_beats_trajectory_progress_count"],
        "no_trajectory_positive_candidate_exists_count": totals["no_trajectory_positive_candidate_exists_count"],
        "cache_queries_run": cache.query_count - cache_before,
        "live_foundation_queries_run": cache.query_count - cache_before,
        "deep_reply_checks_run": totals["deep_reply_checks_run"],
        "skipped_deep_audit_count": 0,
        "skipped_reason_counts": {},
        "starts": start_rows,
    }


def _safe_first_candidate_rows(cfg, context, cache, tg29f_cfg, board, selected_move):
    cheap = _cheap_candidate_rows(board, context["selected"]["edge_weights"])
    compact_by_move = {
        row["candidate_move"]: row
        for row in (_compact_candidate_row(tg29f_cfg, context, cache, board, candidate, selected_move=selected_move) for candidate in _candidate_rows_for_pool(tg29f_cfg, context, cache, board))
    }
    rows = []
    for row in cheap:
        move = chess.Move.from_uci(row["move"])
        after = board.copy(stack=False)
        after.push(move)
        safety = _safety_result(after)
        if not row["safety_ok"] or not safety["safe"] or after.is_stalemate():
            continue
        compact = compact_by_move.get(row["move"])
        progress = _local_progress_metrics(row)
        keys = list(row.get("positive_feature_keys", []))
        rows.append({
            "candidate_move": row["move"],
            "after_first_candidate_fen": after.fen(),
            "selected_by_current_graph": row["move"] == selected_move,
            "local_progress_metrics": progress,
            "local_progress_score": _local_progress_score(progress),
            "safety_metrics": {"rook_blunder": bool(safety["rook_blunder"]), "rook_safe_after": bool(safety["safe"]), "stalemate_after": bool(after.is_stalemate())},
            "positive_feature_keys": keys,
            "bridge_feature_keys": [] if compact is None else list(compact.get("bridge_feature_keys", [])),
            "current_graph_evidence_score": None if compact is None else compact.get("evidence_score"),
            "candidate_indexed_by_current_retrieval": compact is not None,
            "foundation_config_hash": _hash_dict(context["foundation_sanity"]),
            "cache_config_hash": _hash_dict(asdict(_tg29f_tg28c_cfg(_as_tg29f_repair_cfg(cfg), context, tg29f_cfg))),
            "live_graph_equivalence_hash": _hash_dict({"graph_nodes": len(context["graph"].graph.nodes), "graph_edges": len(context["graph"].graph.edges)}),
        })
    rows = sorted(rows, key=lambda item: (item["local_progress_score"], item["candidate_move"]), reverse=True)
    if cfg.max_safe_candidates_per_start > 0:
        rows = rows[: cfg.max_safe_candidates_per_start]
    return rows


def _trajectory_for_policy(cfg, context, cache, tg29f_cfg, board, row, policy: str) -> dict[str, Any]:
    first = chess.Move.from_uci(row["candidate_move"])
    after_first = board.copy(stack=False)
    after_first.push(first)
    black_reply = _select_black_reply(cache, after_first, policy)
    if black_reply is not None:
        after_first.push(black_reply)
    s1_fen = after_first.fen()
    foundation_after_reply = cache.query_state(after_first)
    next_selection = None
    after_second_fen = None
    second_black_reply = None
    foundation_query_fen = s1_fen
    foundation_after_second_reply = foundation_after_reply
    deep_reply_checks = 1
    if after_first.turn == chess.WHITE and not after_first.is_game_over():
        next_selection = _select_online_move(
            context["graph"],
            cache,
            context["mate2_cfg"],
            _tg29f_tg28c_cfg(_as_tg29f_repair_cfg(cfg), context, tg29f_cfg),
            context["edge_cfg"],
            after_first,
            context["selected"]["edge_weights"],
            _merge_weights(context["selected"]["bridge_weights"], _repair_weight_delta("combined_reply_robust")),
            masks={},
        )
        move_uci = next_selection.get("selected_white_move")
        if move_uci is not None:
            second = chess.Move.from_uci(move_uci)
            if second in after_first.legal_moves:
                after_first.push(second)
                after_second_fen = after_first.fen()
                if after_first.turn == chess.BLACK and not after_first.is_game_over():
                    reply = _select_black_reply(cache, after_first, policy)
                    second_black_reply = None if reply is None else reply.uci()
                    if reply is not None:
                        after_first.push(reply)
                foundation_query_fen = after_first.fen()
                foundation_after_second_reply = cache.query_state(after_first)
                deep_reply_checks += 1
    next_phase = None if next_selection is None else next_selection.get("diagnostic_phase_classification")
    foundation_after_reply_reachable = _foundation_reachable(foundation_after_reply)
    foundation_after_second_reachable = _foundation_reachable(foundation_after_second_reply)
    same_graph_count = 0 if next_selection is None else int(next_selection.get("same_graph_foundation_continuation_count", 0))
    classification = _policy_classification(
        foundation_after_reply_reachable=foundation_after_reply_reachable,
        foundation_after_second_reachable=foundation_after_second_reachable,
        next_phase=next_phase,
        same_graph_count=same_graph_count,
    )
    return {
        "black_reply_policy": policy,
        "black_reply": None if black_reply is None else black_reply.uci(),
        "s1_fen": s1_fen,
        "graph_selected_second_move": None if next_selection is None else next_selection.get("selected_white_move"),
        "after_second_move_fen": after_second_fen,
        "second_black_reply": second_black_reply,
        "foundation_query_fen": foundation_query_fen,
        "foundation_selected_move": foundation_after_second_reply.get("foundation_selected_move"),
        "same_graph_foundation_continuation_count": same_graph_count,
        "next_phase": next_phase,
        "foundation_after_first_reply_reachable": foundation_after_reply_reachable,
        "foundation_after_second_reply_reachable": foundation_after_second_reachable,
        "trajectory_policy_classification": classification,
        "bridge_progress_metrics": {
            "bridge_selected_next": next_phase == "bridge_move",
            "mixed_evidence_next": next_phase == "mixed_evidence_move",
        },
        "foundation_progress_metrics": {
            "foundation_reachable_after_first_reply": foundation_after_reply_reachable,
            "foundation_reachable_after_second_reply": foundation_after_second_reachable,
            "foundation_handoff": foundation_after_reply_reachable or foundation_after_second_reachable,
            "same_graph_foundation_continuation_count": same_graph_count,
        },
        "deep_reply_checks_run": deep_reply_checks,
    }


def _policy_classification(*, foundation_after_reply_reachable: bool, foundation_after_second_reachable: bool, next_phase: str | None, same_graph_count: int) -> str:
    if foundation_after_reply_reachable or foundation_after_second_reachable:
        return "trajectory_positive"
    if next_phase in {"foundation_move", "mixed_evidence_move"} or same_graph_count > 0:
        return "trajectory_partial_positive"
    if next_phase == "bridge_move":
        return "bridge_loop_inducing"
    if next_phase == "edge_fence_move":
        return "local_progress_only"
    if next_phase is None:
        return "safe_low_progress"
    return "unknown"


def _aggregate_classification(policy_rows: list[dict[str, Any]], row: dict[str, Any]) -> str:
    classes = {item["trajectory_policy_classification"] for item in policy_rows}
    if "trajectory_positive" in classes:
        return "trajectory_positive"
    if "trajectory_partial_positive" in classes:
        return "trajectory_partial_positive"
    if classes == {"bridge_loop_inducing"} or "bridge_loop_inducing" in classes:
        return "bridge_loop_inducing"
    if row["local_progress_score"] > 0:
        return "local_progress_only"
    if "safe_low_progress" in classes:
        return "safe_low_progress"
    return "unknown"


def _trajectory_score(classification: str, policy_rows: list[dict[str, Any]]) -> float:
    class_bonus = {
        "trajectory_positive": 10.0,
        "trajectory_partial_positive": 6.0,
        "local_progress_only": 2.0,
        "safe_low_progress": 1.0,
        "bridge_loop_inducing": 0.5,
        "unknown": 0.0,
    }.get(classification, 0.0)
    foundation = sum(1.0 for row in policy_rows if row["foundation_progress_metrics"]["foundation_handoff"])
    same_graph = sum(float(row["same_graph_foundation_continuation_count"]) for row in policy_rows)
    bridge = sum(1.0 for row in policy_rows if row["bridge_progress_metrics"]["bridge_selected_next"])
    return class_bonus + foundation + (0.1 * same_graph) + (0.05 * bridge)


def _comparison(audit: dict[str, Any]) -> dict[str, Any]:
    rows = []
    counts: Counter[str] = Counter()
    for start in audit["starts"]:
        current = start["current_graph_selected_move"]
        pairwise = start["tg29f_pairwise_selected_move"]
        best_local = start["best_local_progress_move"]
        best_traj = start["best_trajectory_positive_move"]
        exists = bool(start["trajectory_positive_candidate_exists"])
        lost = bool(exists and current != best_traj)
        bucket = start["failure_bucket"]
        counts[bucket] += 1
        rows.append({
            "start_fen": start["start_fen"],
            "selected_move": current,
            "tg29f_pairwise_selected_move": pairwise,
            "best_local_progress_candidate": best_local,
            "best_trajectory_positive_candidate": best_traj,
            "trajectory_positive_candidate_exists": exists,
            "current_graph_selected_trajectory_candidate": current == best_traj and best_traj is not None,
            "tg29f_pairwise_selected_trajectory_candidate": pairwise == best_traj and best_traj is not None,
            "local_progress_winner_differs_from_trajectory_winner": start["local_progress_winner_differs_from_trajectory_winner"],
            "why_trajectory_positive_candidate_lost": bucket,
        })
    return {"rows": rows, "failure_bucket_counts": dict(counts)}


def _write_pool(cfg, context, audit):
    entries = []
    counts: Counter[str] = Counter()
    for start in audit["starts"]:
        for row in start["candidate_rows"]:
            split = _pool_split(row, counts)
            if split is None:
                continue
            for policy_row in row["policy_rollouts"]:
                entry = {
                    "schema_version": "tg29g_trajectory_positive_prefix_pool_entry.v0",
                    "pool_entry_id": "tg29g_" + _hash_dict({"fen": start["start_fen"], "move": row["candidate_move"], "policy": policy_row["black_reply_policy"], "split": split}),
                    "split": split,
                    "start_fen": start["start_fen"],
                    "first_candidate_move": row["candidate_move"],
                    "after_first_candidate_fen": row["after_first_candidate_fen"],
                    "black_reply_policy": policy_row["black_reply_policy"],
                    "black_reply": policy_row["black_reply"],
                    "s1_fen": policy_row["s1_fen"],
                    "graph_selected_second_move": policy_row["graph_selected_second_move"],
                    "after_second_move_fen": policy_row["after_second_move_fen"],
                    "second_black_reply": policy_row["second_black_reply"],
                    "foundation_query_fen": policy_row["foundation_query_fen"],
                    "foundation_selected_move": policy_row["foundation_selected_move"],
                    "same_graph_foundation_continuation_count": policy_row["same_graph_foundation_continuation_count"],
                    "trajectory_classification": row["trajectory_classification"],
                    "local_progress_metrics": row["local_progress_metrics"],
                    "bridge_progress_metrics": policy_row["bridge_progress_metrics"],
                    "foundation_progress_metrics": policy_row["foundation_progress_metrics"],
                    "safety_metrics": row["safety_metrics"],
                    "positive_feature_keys": row["positive_feature_keys"],
                    "bridge_feature_keys": row["bridge_feature_keys"],
                    "foundation_config_hash": row["foundation_config_hash"],
                    "cache_config_hash": row["cache_config_hash"],
                    "live_graph_equivalence_hash": row["live_graph_equivalence_hash"],
                    "source": "frozen_native_graph_response",
                    "validator_labels_used_for_generation_only": True,
                    "learner_visible_labels": False,
                }
                entries.append(entry)
                counts[split] += 1
                break
    pool_path = Path(cfg.pool_path)
    pool_path.parent.mkdir(parents=True, exist_ok=True)
    pool_path.write_text("".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries), encoding="utf-8")
    index = {
        "schema_version": "tg29g_trajectory_positive_prefix_pool_index.v0",
        "trajectory_pool_path": cfg.pool_path,
        "trajectory_pool_index_path": cfg.pool_index_path,
        "trajectory_pool_entry_count": len(entries),
        "trajectory_positive_count": counts["trajectory_positive"],
        "local_progress_negative_count": counts["local_progress_negative"],
        "near_miss_or_low_progress_negative_count": counts["near_miss_or_low_progress_negative"],
        "minimum_useful_pool": counts["trajectory_positive"] >= 1 and counts["local_progress_negative"] >= 1 and counts["near_miss_or_low_progress_negative"] >= 2,
    }
    index_path = Path(cfg.pool_index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return entries, index


def _pool_split(row: dict[str, Any], counts: Counter[str]) -> str | None:
    cls = row["trajectory_classification"]
    if cls == "trajectory_positive" and counts["trajectory_positive"] < 8:
        return "trajectory_positive"
    if cls == "local_progress_only" and counts["local_progress_negative"] < 8:
        return "local_progress_negative"
    if cls in {"safe_low_progress", "bridge_loop_inducing", "trajectory_partial_positive"} and counts["near_miss_or_low_progress_negative"] < 8:
        return "near_miss_or_low_progress_negative"
    return None


def _optional_repair(cfg, context, tg29f_cfg, audit, comparison):
    if not cfg.run_optional_repair or audit["trajectory_positive_candidate_count"] <= 0 or audit["trajectory_positive_candidate_lost_selection_count"] <= 0:
        return {"repair_applied": False, "skip_reason": "no_lost_trajectory_positive_candidate_or_disabled", "ablation_results": {}}
    edge_delta, bridge_delta = _trajectory_contrast_deltas(audit)
    if not edge_delta and not bridge_delta:
        return {"repair_applied": False, "skip_reason": "trajectory_positive_candidates_found_but_no_distinguishing_feature_keys", "ablation_results": {}}
    starts = tuple({"start_fen": row["start_fen"], "source": "tg29g_failure_start"} for row in audit["starts"])[: cfg.base.episode_count]
    episodes = _run_repair_policy(cfg, context, tg29f_cfg, starts, edge_delta, bridge_delta, masks={})
    progress = _progress_summary(episodes)
    selection_rows = []
    cache = _FoundationResponseCache(context["graph"], context["mate2_cfg"], _tg29f_tg28c_cfg(_as_tg29f_repair_cfg(cfg), context, tg29f_cfg))
    for start in audit["starts"]:
        selection = _select_with_deltas(_as_tg29f_repair_cfg(cfg), context, cache, tg29f_cfg, chess.Board(start["start_fen"]), edge_delta, bridge_delta)
        best_traj = start["best_trajectory_positive_move"]
        selection_rows.append({"start_fen": start["start_fen"], "selected_move": selection.get("selected_white_move"), "best_trajectory_positive_move": best_traj, "selected_trajectory_positive": selection.get("selected_white_move") == best_traj and best_traj is not None})
    ablations = _repair_ablations(cfg, context, tg29f_cfg, starts, edge_delta, bridge_delta)
    return {
        "repair_applied": True,
        "selected_repair_arm": "trajectory_positive_contrastive_evidence",
        "edge_weight_delta": edge_delta,
        "bridge_weight_delta": bridge_delta,
        "selection_rows": selection_rows,
        "better_trajectory_candidate_selected_after_repair_count": sum(int(row["selected_trajectory_positive"]) for row in selection_rows),
        "episodes": episodes,
        "progress_summary": progress,
        "ablation_results": ablations,
    }


def _trajectory_contrast_deltas(audit: dict[str, Any]) -> tuple[dict[str, float], dict[str, float]]:
    edge: dict[str, float] = {}
    bridge: dict[str, float] = {}
    for start in audit["starts"]:
        positives = [row for row in start["candidate_rows"] if row["trajectory_classification"] == "trajectory_positive"]
        negatives = [row for row in start["candidate_rows"] if row["trajectory_classification"] in {"local_progress_only", "bridge_loop_inducing", "safe_low_progress"}]
        if not positives or not negatives:
            continue
        positive_keys = set().union(*(set(row["positive_feature_keys"]) for row in positives))
        negative_keys = set().union(*(set(row["positive_feature_keys"]) for row in negatives))
        positive_bridge = set().union(*(set(row["bridge_feature_keys"]) for row in positives))
        negative_bridge = set().union(*(set(row["bridge_feature_keys"]) for row in negatives))
        for key in positive_keys - negative_keys:
            edge[key] = edge.get(key, 0.0) + 0.35
        for key in negative_keys - positive_keys:
            edge[key] = edge.get(key, 0.0) - 0.20
        for key in positive_bridge - negative_bridge:
            bridge[key] = bridge.get(key, 0.0) + 0.25
        for key in negative_bridge - positive_bridge:
            bridge[key] = bridge.get(key, 0.0) - 0.15
    return edge, _merge_weights(_repair_weight_delta("combined_reply_robust"), bridge)


def _run_repair_policy(cfg, context, tg29f_cfg, starts, edge_delta, bridge_delta, *, masks: dict[str, bool]):
    cache = _FoundationResponseCache(context["graph"], context["mate2_cfg"], _tg29f_tg28c_cfg(_as_tg29f_repair_cfg(cfg), context, tg29f_cfg))
    episodes = _run_episodes(
        context["graph"],
        cache,
        context["mate2_cfg"],
        _tg29f_tg28c_cfg(_as_tg29f_repair_cfg(cfg), context, tg29f_cfg),
        context["edge_cfg"],
        starts,
        _merge_weights(context["selected"]["edge_weights"], edge_delta),
        _merge_weights(context["selected"]["bridge_weights"], bridge_delta),
        cfg.base,
        masks=masks,
    )
    return _enrich_episodes(episodes, context | {"cache": cache, "tg28c_cfg": _tg29f_tg28c_cfg(_as_tg29f_repair_cfg(cfg), context, tg29f_cfg)}, OnlineFailureDecompositionConfig(base=cfg.base))


def _repair_ablations(cfg, context, tg29f_cfg, starts, edge_delta, bridge_delta):
    masks = {
        "mask_trajectory_positive_terminals": {"mask_edge_fence_terminals": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_foundation_response_terminals": {"mask_foundation_response_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "disable_reply_envelope_checks": {"disable_reply_envelope_foundation_checks": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_frozen_mate2_foundation_quorum": True},
    }
    if cfg.base.max_episode_ablation_count <= 0:
        return {name: {"skipped": True, "skip_reason": "max_episode_ablation_count_zero"} for name in masks}
    ablation_starts = starts[: max(1, cfg.base.max_episode_ablation_count)]
    return {name: _progress_summary(_run_repair_policy(cfg, context, tg29f_cfg, ablation_starts, edge_delta, bridge_delta, masks=mask)) for name, mask in masks.items()}


def _decision(cfg, *, context, trajectory_audit, comparison, pool_index, optional_repair, regression, foundation_before, foundation_after, cache_equivalence, scheduler_equivalence, timings):
    m3_delta = foundation_after["m3"] - foundation_before["m3"]
    m4_delta = foundation_after["m4"] - foundation_before["m4"]
    regression_clean = all(regression[key] for key in ("frontier_regression_pass", "staged_regression_pass", "near_miss_regression_pass", "generic_edge_regression_pass", "foundation_sanity_pass"))
    repair_progress = optional_repair.get("progress_summary", {})
    repair_applied = bool(optional_repair.get("repair_applied", False))
    repair_success = bool(
        repair_applied
        and optional_repair.get("better_trajectory_candidate_selected_after_repair_count", 0) > 0
        and (repair_progress.get("episode_success_count", 0) > 0 or repair_progress.get("selected_moves_safe_but_low_progress_count", 99) < 2)
        and repair_progress.get("rook_blunder_count", 0) == 0
        and repair_progress.get("illegal_move_count", 0) == 0
        and repair_progress.get("stalemate_count", 0) == 0
    )
    diagnostic_pass = (
        trajectory_audit["audited_failure_start_count"] > 0
        and trajectory_audit["audited_candidate_count"] > 0
        and m3_delta == 0
        and m4_delta == 0
        and cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
        and regression_clean
    )
    bounded = repair_progress if repair_applied else {"episode_success_count": 0, "episode_count": cfg.base.episode_count, "selected_moves_safe_but_low_progress_count": 0, "bridge_loop_without_foundation_progress_count": 0, "rook_blunder_count": 0, "illegal_move_count": 0, "stalemate_count": 0}
    average_seconds_per_candidate = 0.0
    if trajectory_audit["audited_candidate_count"] > 0:
        average_seconds_per_candidate = round(
            timings.get("trajectory_rollout_seconds", 0.0) / trajectory_audit["audited_candidate_count"],
            6,
        )
    interpretation = (
        "trajectory_positive_repair_improved_bounded_slice"
        if repair_success
        else (
            "trajectory_positive_candidates_exist_selection_or_basin_needs_repair"
            if trajectory_audit["trajectory_positive_candidate_count"] > 0
            else "no_trajectory_positive_candidate_found_expand_basin_not_selection"
        )
    )
    return {
        "checkpoint_pass": bool(repair_success or diagnostic_pass),
        "checkpoint_interpretation": interpretation,
        "repair_applied": repair_applied and repair_success,
        "selected_repair_arm": optional_repair.get("selected_repair_arm"),
        "audit_context_profile": cfg.audit_context_profile,
        "throughput_note": cfg.throughput_note,
        "bounded_safe_candidates_per_start": cfg.max_safe_candidates_per_start,
        "optional_repair_requested": cfg.run_optional_repair,
        "foundation_frozen": m3_delta == 0 and m4_delta == 0,
        "foundation_mate1_accuracy": context["foundation_sanity"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": context["foundation_sanity"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": cache_equivalence["foundation_cache_live_mismatch_count"],
        "foundation_m3_updates_during_training": 0,
        "foundation_m4_promotions_during_training": 0,
        "foundation_m3_updates_during_eval": m3_delta,
        "foundation_m4_promotions_during_eval": m4_delta,
        "audited_failure_start_count": trajectory_audit["audited_failure_start_count"],
        "audited_candidate_count": trajectory_audit["audited_candidate_count"],
        "trajectory_rollout_count": trajectory_audit["trajectory_rollout_count"],
        "cache_queries_run": trajectory_audit["cache_queries_run"],
        "live_foundation_queries_run": trajectory_audit["live_foundation_queries_run"],
        "deep_reply_checks_run": trajectory_audit["deep_reply_checks_run"],
        "average_seconds_per_candidate": average_seconds_per_candidate,
        "skipped_deep_audit_count": trajectory_audit["skipped_deep_audit_count"],
        "skipped_reason_counts": trajectory_audit["skipped_reason_counts"],
        "trajectory_positive_candidate_count": trajectory_audit["trajectory_positive_candidate_count"],
        "trajectory_partial_positive_candidate_count": trajectory_audit["trajectory_partial_positive_candidate_count"],
        "local_progress_only_candidate_count": trajectory_audit["local_progress_only_candidate_count"],
        "safe_low_progress_candidate_count": trajectory_audit["safe_low_progress_candidate_count"],
        "bridge_loop_inducing_candidate_count": trajectory_audit["bridge_loop_inducing_candidate_count"],
        "trajectory_positive_candidate_exists_count": trajectory_audit["trajectory_positive_candidate_exists_count"],
        "trajectory_positive_candidate_lost_selection_count": trajectory_audit["trajectory_positive_candidate_lost_selection_count"],
        "local_progress_beats_trajectory_progress_count": trajectory_audit["local_progress_beats_trajectory_progress_count"],
        "no_trajectory_positive_candidate_exists_count": trajectory_audit["no_trajectory_positive_candidate_exists_count"],
        "trajectory_pool_path": pool_index["trajectory_pool_path"],
        "trajectory_pool_entry_count": pool_index["trajectory_pool_entry_count"],
        "optional_repair_applied": bool(optional_repair.get("repair_applied", False)),
        "better_trajectory_candidate_selected_after_repair_count": optional_repair.get("better_trajectory_candidate_selected_after_repair_count", 0),
        "bounded_episode_success_count": bounded.get("episode_success_count", 0),
        "bounded_episode_count": bounded.get("episode_count", cfg.base.episode_count),
        "selected_moves_safe_but_low_progress_count": bounded.get("selected_moves_safe_but_low_progress_count", 0),
        "bridge_loop_without_foundation_progress_count": bounded.get("bridge_loop_without_foundation_progress_count", 0),
        "rook_blunder_count": bounded.get("rook_blunder_count", 0),
        "illegal_move_count": bounded.get("illegal_move_count", 0),
        "stalemate_count": bounded.get("stalemate_count", 0),
        "regression_results": regression,
        "failure_bucket_counts": comparison["failure_bucket_counts"],
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "ablation_results": optional_repair.get("ablation_results", {}),
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


def _failure_bucket(current, pairwise, best_local, best_traj, exists: bool) -> str:
    if not exists:
        return "no_trajectory_positive_candidate_exists"
    best_traj_move = None if best_traj is None else best_traj["candidate_move"]
    best_local_move = None if best_local is None else best_local["candidate_move"]
    if current != best_traj_move:
        if best_local_move != best_traj_move:
            return "local_progress_beats_trajectory_progress"
        return "trajectory_positive_candidate_exists_but_lost_selection"
    if pairwise != best_traj_move:
        return "trajectory_positive_evidence_too_weak"
    return "none"


def _best(rows: list[dict[str, Any]], *, key):
    return max(rows, key=key) if rows else None


def _local_progress_metrics(row: dict[str, Any]) -> dict[str, float]:
    return {
        "edge_distance_delta": float(row.get("delta_black_king_edge_distance", 0.0)),
        "black_king_mobility_delta": float(row.get("delta_black_king_legal_mobility", 0.0)),
        "confinement_area_delta": float(row.get("delta_confinement_area", 0.0)),
    }


def _local_progress_score(metrics: dict[str, float]) -> float:
    return (
        max(0.0, -metrics["edge_distance_delta"]) * 0.25
        + max(0.0, -metrics["black_king_mobility_delta"]) * 0.18
        + max(0.0, -metrics["confinement_area_delta"]) * 0.12
        - max(0.0, metrics["confinement_area_delta"]) * 0.10
    )


def _hash_dict(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def _purity_boundary() -> dict[str, Any]:
    return {
        "checkpoint": "TG29g",
        "trajectory_labels_trainer_side_only": True,
        "runtime_move_selection": "graph_mediated_candidate_weights_no_provider_override",
        "foundation_frozen": True,
        "cache_used_as_memoized_frozen_graph_response": True,
        "cache_used_as_provider": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "direct_provider_override": False,
        "learner_visible_stage_labels": False,
        "white_moves_graph_mediated": True,
        "black_replies_harness_simulated": True,
    }


def _write_progress(cfg: TrajectoryPositivePrefixAuditConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
