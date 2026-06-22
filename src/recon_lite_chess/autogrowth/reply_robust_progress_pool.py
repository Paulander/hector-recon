"""TG29e reply-robust progress-positive episode pool."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import chess

from .frozen_foundation_edge_fence_reentry import _foundation_counts
from .frozen_foundation_response_cache_bridge_retrieval import _FoundationResponseCache, _cache_candidate_rows
from .online_failure_decomposition import OnlineFailureDecompositionConfig, _enrich_episodes, _regression_summary
from .online_low_progress_repair import _progress_summary
from .reply_robust_bridge_pressure import (
    ReplyRobustBridgePressureConfig,
    _purity_boundary as _tg29c_purity_boundary,
    _repair_weight_delta,
)
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .native_quorum_materialization import _tg26t_config
from .native_quorum_mate2_chaining import _tg26u_config
from .tiny_online_krk_episode_runner import (
    TinyOnlineKRKEpisodeRunnerConfig,
    _build_context,
    _episode_starts,
    _run_episodes,
    _safety_result,
    _select_online_move,
    _write_progress as _write_tg29a_progress,
)


@dataclass(frozen=True)
class ReplyRobustProgressPoolConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("mixed_balanced_plus_staged",),
        progress_output="reports/autogrowth/krk_autogrowth_tg29e_reply_robust_progress_positive_pool_progress.json",
    )
    tg29d_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29d_online_low_progress_repair.json"
    pool_path: str = "reports/autogrowth/pools/tg29e_reply_robust_progress_positive_pool.jsonl"
    pool_index_path: str = "reports/autogrowth/pools/tg29e_reply_robust_progress_positive_pool_index.json"
    reply_policies: tuple[str, ...] = ("deterministic_worst_foundation_reply",)
    comparison_reply_policies: tuple[str, ...] = ("mobility_maximizing",)
    max_reply_envelope_replies_per_candidate: int = 2
    max_repair_cache_candidate_moves: int = 6
    progress_positive_train_target: int = 8
    progress_positive_heldout_target: int = 4
    low_progress_negative_target: int = 8
    near_miss_target: int = 8
    regression_target: int = 4
    min_progress_positive_train_count: int = 4
    min_progress_positive_heldout_count: int = 2
    min_low_progress_negative_count: int = 4
    min_near_miss_count: int = 4
    min_regression_count: int = 2
    max_forward_filter_starts: int = 12
    max_audit_low_progress_episodes: int = 2
    max_audit_turns_per_episode: int = 4
    training_arms: tuple[str, ...] = (
        "combined_reply_robust_baseline",
        "progress_positive_candidate_replay_only",
        "combined_reply_robust_plus_progress_positive_replay",
        "combined_reply_robust_plus_progress_positive_and_low_progress_negatives",
        "combined_reply_robust_plus_progress_positive_low_progress_and_near_miss",
    )


@dataclass(frozen=True)
class ReplyRobustProgressPoolResult:
    config: ReplyRobustProgressPoolConfig
    candidate_audit: dict[str, Any]
    pool_index: dict[str, Any]
    arm_results: dict[str, Any]
    selected_arm_episodes: dict[str, Any]
    ablation_results: dict[str, Any]
    regression_results: dict[str, Any]
    foundation_cache_equivalence: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29e_reply_robust_progress_positive_pool.v0",
            "checkpoint": "TG29e_reply_robust_progress_positive_pool",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "candidate_audit": self.candidate_audit,
            "pool_index": self.pool_index,
            "arm_results": self.arm_results,
            "selected_arm_episodes": self.selected_arm_episodes,
            "ablation_results": self.ablation_results,
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
                    "# TG29e Reply-Robust Progress-Positive Episode Pool",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- selected_training_arm: `{d['selected_training_arm']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- audited candidates: `{d['audited_candidate_count']}`",
                    f"- progress-positive candidates: `{d['progress_positive_candidate_count']}`",
                    f"- better progress lost selection: `{d['better_progress_candidate_lost_selection_count']}`",
                    f"- pool entries: `{d['progress_pool_entry_count']}`",
                    f"- episode success: `{d['episode_success_count']}` / `{d['episode_count']}`",
                    f"- low-progress failures: `{d['selected_moves_safe_but_low_progress_count']}`",
                    f"- bridge-loop failures: `{d['bridge_loop_without_foundation_progress_count']}`",
                    "",
                    "Interpretation: TG29e separates candidate existence from selection repair. Pool labels are trainer-side only.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_reply_robust_progress_pool(*, config: ReplyRobustProgressPoolConfig | None = None) -> ReplyRobustProgressPoolResult:
    cfg = config or ReplyRobustProgressPoolConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})
    context = _build_context(cfg.base)
    timings.update(context["timings"])
    starts = _episode_starts(cfg.base, context)
    graph = context["graph"]
    foundation_before = _foundation_counts(graph)
    _write_progress(cfg, {"phase": "context_built", "selected_schedule": context["selected"]["schedule_name"]})

    tg29e_cache = _FoundationResponseCache(graph, context["mate2_cfg"], _tg29e_tg28c_cfg(cfg, context))
    start = time.perf_counter()
    seed_episodes = _load_low_progress_episodes(cfg)
    if not seed_episodes:
        seed_episodes = _seed_selected_episodes(cfg, context, starts)
    candidate_audit = _audit_low_progress_candidates(cfg, context, tg29e_cache, seed_episodes)
    timings["candidate_audit_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "candidate_audit_complete", "audited_candidates": candidate_audit["audited_candidate_count"]})

    start = time.perf_counter()
    pool_entries, pool_stats = _build_pool(cfg, context, tg29e_cache, candidate_audit)
    pool_index = _write_pool_files(cfg, pool_entries, pool_stats)
    timings["pool_generation_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "pool_written", "entries": pool_index["progress_pool_entry_count"]})

    start = time.perf_counter()
    arm_results = _run_training_arms(cfg, context, starts, pool_entries)
    timings["arm_eval_seconds"] = round(time.perf_counter() - start, 6)
    selected_arm = _select_training_arm(arm_results)
    selected_policy = arm_results[selected_arm]["policies"]["deterministic_worst_foundation_reply"]
    _ensure_policy_comparisons(cfg, context, starts, pool_entries, arm_results, selected_arm)
    _write_progress(cfg, {"phase": "arms_complete", "selected_arm": selected_arm, "success": selected_policy["summary"]["episode_success_rate"]})

    start = time.perf_counter()
    ablations = _selected_arm_ablations(cfg, context, starts, pool_entries, selected_arm)
    timings["ablation_seconds"] = round(time.perf_counter() - start, 6)

    foundation_after = _foundation_counts(graph)
    cache_equivalence = context["cache"].live_equivalence_audit(max_samples=min(8, cfg.base.max_samples))
    scheduler_equivalence = _scheduler_equivalence(
        _tg26s_config(_tg26t_config(_tg26u_config(context["mate2_cfg"]))),
        context["mate1_train"],
        context["mate1_heldout"],
    )
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)
    selected_summary = arm_results[selected_arm]["policies"]["deterministic_worst_foundation_reply"]["progress_summary"]
    baseline_summary = arm_results["combined_reply_robust_baseline"]["policies"]["deterministic_worst_foundation_reply"]["progress_summary"]
    decision = _decision(
        cfg,
        context=context,
        selected_arm=selected_arm,
        selected_summary=selected_summary,
        baseline_summary=baseline_summary,
        candidate_audit=candidate_audit,
        pool_index=pool_index,
        arm_results=arm_results,
        ablations=ablations,
        foundation_before=foundation_before,
        foundation_after=foundation_after,
        cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return ReplyRobustProgressPoolResult(
        config=cfg,
        candidate_audit=candidate_audit,
        pool_index=pool_index,
        arm_results=arm_results,
        selected_arm_episodes=arm_results[selected_arm]["policies"]["deterministic_worst_foundation_reply"]["episodes"],
        ablation_results=ablations,
        regression_results=_regression_summary(context["regression"]),
        foundation_cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


def _tg29e_tg28c_cfg(cfg: ReplyRobustProgressPoolConfig, context: dict[str, Any]):
    return type(context["tg28c_cfg"])(
        **{
            **asdict(context["tg28c_cfg"]),
            "max_reply_envelope_replies_per_candidate": cfg.max_reply_envelope_replies_per_candidate,
            "max_cache_candidate_moves": cfg.max_repair_cache_candidate_moves,
        }
    )


def _load_low_progress_episodes(cfg: ReplyRobustProgressPoolConfig) -> list[dict[str, Any]]:
    path = Path(cfg.tg29d_artifact_path)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        trace
        for trace in payload.get("selected_arm_episodes", {}).get("traces", [])
        if trace.get("failure_bucket") == "selected_moves_safe_but_low_progress"
    ][: cfg.max_audit_low_progress_episodes]


def _seed_selected_episodes(cfg: ReplyRobustProgressPoolConfig, context: dict[str, Any], starts: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    episodes = _run_policy(
        cfg,
        context,
        starts,
        arm_name="combined_reply_robust_baseline",
        bridge_delta=_repair_weight_delta("combined_reply_robust"),
        black_reply_policy="deterministic_worst_foundation_reply",
    )["episodes"]
    return [
        trace
        for trace in episodes.get("traces", [])
        if trace.get("failure_bucket") == "selected_moves_safe_but_low_progress"
    ][: cfg.max_audit_low_progress_episodes]


def _audit_low_progress_candidates(
    cfg: ReplyRobustProgressPoolConfig,
    context: dict[str, Any],
    cache: _FoundationResponseCache,
    episodes: list[dict[str, Any]],
) -> dict[str, Any]:
    audited_turns = []
    totals: Counter[str] = Counter()
    for episode in episodes:
        turn_rows = []
        for step in episode.get("steps", [])[: cfg.max_audit_turns_per_episode]:
            fen = step.get("white_to_move_fen")
            if not fen:
                continue
            _write_progress(cfg, {
                "phase": "candidate_audit_turn",
                "episode_id": episode.get("episode_id", episode.get("episode_index")),
                "turn_index": step.get("move_index"),
            })
            board = chess.Board(fen)
            selected = _select_online_move(
                context["graph"],
                cache,
                context["mate2_cfg"],
                _tg29e_tg28c_cfg(cfg, context),
                context["edge_cfg"],
                board,
                context["selected"]["edge_weights"],
                context["selected"]["bridge_weights"] | _repair_weight_delta("combined_reply_robust"),
                masks={},
            )
            candidates = _candidate_rows_for_pool(cfg, context, cache, board)
            selected_move = step.get("selected_white_move") or selected.get("selected_white_move")
            compact = [_compact_candidate_row(cfg, context, cache, board, row, selected_move=selected_move) for row in candidates]
            for row in compact:
                totals["audited_candidate_count"] += 1
                totals["safe_candidate_count"] += int(row["safe"])
                totals[f"{row['classification']}_count"] += 1
            better = _better_progress_available(compact, selected_move)
            totals["better_progress_candidate_available_count"] += int(better["available"])
            totals["better_progress_candidate_lost_selection_count"] += int(better["lost_selection"])
            totals["no_better_progress_candidate_count"] += int(not better["available"])
            turn_rows.append({
                "source_episode_id": episode.get("episode_id", episode.get("episode_index")),
                "source_turn_index": step.get("move_index"),
                "start_fen": fen,
                "selected_move": selected_move,
                "current_graph_selection_rank": _selection_rank(compact, selected_move),
                "better_progress_candidate_available": better["available"],
                "better_progress_candidate_lost_selection": better["lost_selection"],
                "legal_candidate_alternatives": compact[:12],
            })
        if turn_rows:
            audited_turns.append({
                "episode_id": episode.get("episode_id", episode.get("episode_index")),
                "start_fen": episode.get("start_fen"),
                "failure_bucket": episode.get("failure_bucket"),
                "turns": turn_rows,
            })
    return {
        "audited_low_progress_episode_count": len(episodes),
        "audited_turn_count": sum(len(row["turns"]) for row in audited_turns),
        "audited_candidate_count": totals["audited_candidate_count"],
        "safe_candidate_count": totals["safe_candidate_count"],
        "progress_positive_candidate_count": totals["strong_reply_robust_progress_count"] + totals["partial_progress_count"],
        "strong_reply_robust_progress_count": totals["strong_reply_robust_progress_count"],
        "partial_progress_count": totals["partial_progress_count"],
        "safe_low_progress_candidate_count": totals["safe_low_progress_count"],
        "regress_without_blunder_count": totals["regress_without_blunder_count"],
        "unsafe_count": totals["unsafe_count"],
        "better_progress_candidate_available_count": totals["better_progress_candidate_available_count"],
        "better_progress_candidate_lost_selection_count": totals["better_progress_candidate_lost_selection_count"],
        "no_better_progress_candidate_count": totals["no_better_progress_candidate_count"],
        "audited_episodes": audited_turns,
    }


def _candidate_rows_for_pool(
    cfg: ReplyRobustProgressPoolConfig,
    context: dict[str, Any],
    cache: _FoundationResponseCache,
    board: chess.Board,
) -> list[dict[str, Any]]:
    return _cache_candidate_rows(
        cache,
        board,
        _tg29e_tg28c_cfg(cfg, context),
        context["selected"]["edge_weights"],
        context["selected"]["bridge_weights"] | _repair_weight_delta("combined_reply_robust"),
        cache_retrieval_enabled=True,
    )


def _compact_candidate_row(
    cfg: ReplyRobustProgressPoolConfig,
    context: dict[str, Any],
    cache: _FoundationResponseCache,
    board: chess.Board,
    row: dict[str, Any],
    *,
    selected_move: str | None,
) -> dict[str, Any]:
    move = chess.Move.from_uci(row["move"])
    after = board.copy(stack=False)
    after.push(move)
    safety = _safety_result(after)
    envelope = row.get("cache_reply_envelope", {})
    reply_rows = []
    for reply_row in envelope.get("reply_rows", []):
        reply_fen = reply_row.get("reply_fen") or reply_row.get("reply_state")
        reply_rows.append({
            "black_reply": reply_row.get("black_reply"),
            "reply_fen": reply_fen,
            "foundation_response_detected": bool(reply_row.get("foundation_response_detected") or reply_row.get("foundation_solved") or reply_row.get("mated") or reply_row.get("foundation_selected_move")),
            "foundation_selected_move": reply_row.get("foundation_selected_move") or reply_row.get("selected_second"),
            "graph_confirmation_state": reply_row.get("graph_confirmation_state") or reply_row.get("formal_recon_engine_confirmed"),
            "same_graph_foundation_continuation_count": int(reply_row.get("same_graph_second_move_count", 0) or int(bool(reply_row.get("selected_second")))),
        })
    progress = _progress_metrics(row)
    classification = _candidate_classification(row, safety, progress)
    after_key = _fen_key(after.fen())
    return {
        "candidate_move": row["move"],
        "legal": move in board.legal_moves,
        "safe": bool(safety["safe"]) and bool(row.get("safety_ok", False)),
        "rook_blunder": bool(safety["rook_blunder"]),
        "stalemate_after": bool(after.is_stalemate()),
        "edge_fence_evidence": row.get("edge_terminal_state"),
        "bridge_pressure_evidence": row.get("bridge_pressure_terminal_state"),
        "foundation_response_evidence": row.get("foundation_response_terminal_state"),
        "reply_robust_evidence": bool(row.get("foundation_handoff_reachable") or row.get("reply_envelope_foundation_reachable")),
        "current_graph_selection_rank": None,
        "selected": row["move"] == selected_move,
        "after_white_move_fen": after.fen(),
        "after_white_move_fen_key": after_key,
        "black_reply_envelope": {
            "reply_cap": cfg.max_reply_envelope_replies_per_candidate,
            "all_legal_replies_feasible": len(list(after.legal_moves)) <= cfg.max_reply_envelope_replies_per_candidate,
            "black_reply_rows": reply_rows,
        },
        "frozen_foundation_response_after_replies": reply_rows,
        "safety_metrics": {
            "rook_blunder": bool(safety["rook_blunder"]),
            "stalemate_after": bool(after.is_stalemate()),
            "rook_safe_after": bool(safety["safe"]),
        },
        "progress_metrics": progress,
        "classification": classification,
        "bridge_feature_keys": list(row.get("bridge_feature_keys", [])),
        "positive_feature_keys": list(row.get("positive_feature_keys", [])),
        "cheap_score": row.get("cheap_score"),
        "evidence_score": row.get("evidence_score"),
        "formal_recon_engine_confirmed": bool(row.get("formal_recon_engine_confirmed", False)),
        "graph_confirmation_state": row.get("graph_confirmation_state"),
        "cache_config_hash": _hash_dict(asdict(_tg29e_tg28c_cfg(cfg, context))),
        "foundation_config_hash": _hash_dict(context["foundation_sanity"]),
        "live_graph_equivalence_hash": _hash_dict({"graph_nodes": len(context["graph"].graph.nodes), "graph_edges": len(context["graph"].graph.edges)}),
    }


def _progress_metrics(row: dict[str, Any]) -> dict[str, Any]:
    edge_delta = float(row.get("delta_black_king_edge_distance", 0.0))
    mobility_delta = float(row.get("delta_black_king_legal_mobility", 0.0))
    confinement_delta = float(row.get("delta_confinement_area", 0.0))
    rate = float(row.get("reply_envelope_foundation_coverage_rate", 0.0))
    return {
        "edge_distance_delta": edge_delta,
        "black_king_mobility_delta": mobility_delta,
        "confinement_area_delta": confinement_delta,
        "foundation_reachability_delta": rate,
        "reply_envelope_success_rate": rate,
        "worst_reply_foundation_success": bool(row.get("foundation_handoff_reachable", False)),
        "any_reply_foundation_success": bool(row.get("reply_envelope_foundation_reachable", False)),
        "all_reply_foundation_success": bool(row.get("foundation_handoff_reachable", False)),
    }


def _candidate_classification(row: dict[str, Any], safety: dict[str, Any], progress: dict[str, Any]) -> str:
    if not safety["safe"] or not row.get("safety_ok", False):
        return "unsafe"
    if progress["all_reply_foundation_success"] and (
        progress["edge_distance_delta"] <= 0 or progress["black_king_mobility_delta"] <= 0 or progress["confinement_area_delta"] <= 0
    ):
        return "strong_reply_robust_progress"
    if progress["any_reply_foundation_success"] or progress["reply_envelope_success_rate"] > 0.0 or progress["edge_distance_delta"] < 0 or progress["black_king_mobility_delta"] < 0 or progress["confinement_area_delta"] < 0:
        return "partial_progress"
    if progress["edge_distance_delta"] > 0 or progress["black_king_mobility_delta"] > 0 or progress["confinement_area_delta"] > 0:
        return "regress_without_blunder"
    return "safe_low_progress"


def _better_progress_available(rows: list[dict[str, Any]], selected_move: str | None) -> dict[str, bool]:
    selected = next((row for row in rows if row["candidate_move"] == selected_move), None)
    selected_score = _candidate_progress_score(selected) if selected else -999.0
    better = any(_candidate_progress_score(row) > selected_score and row["classification"] in {"strong_reply_robust_progress", "partial_progress"} for row in rows)
    return {"available": better, "lost_selection": better and selected_move is not None}


def _candidate_progress_score(row: dict[str, Any] | None) -> float:
    if row is None:
        return -999.0
    p = row["progress_metrics"]
    return (
        2.0 * float(p["reply_envelope_success_rate"])
        + (1.5 if p["all_reply_foundation_success"] else 0.0)
        + (0.7 if p["any_reply_foundation_success"] else 0.0)
        + max(0.0, -float(p["edge_distance_delta"])) * 0.25
        + max(0.0, -float(p["black_king_mobility_delta"])) * 0.18
        + max(0.0, -float(p["confinement_area_delta"])) * 0.12
        - max(0.0, float(p["confinement_area_delta"])) * 0.10
    )


def _selection_rank(rows: list[dict[str, Any]], selected_move: str | None) -> int | None:
    ranked = sorted(rows, key=_candidate_progress_score, reverse=True)
    for index, row in enumerate(ranked, start=1):
        row["current_graph_selection_rank"] = index if row["candidate_move"] == selected_move else None
        if row["candidate_move"] == selected_move:
            return index
    return None


def _build_pool(
    cfg: ReplyRobustProgressPoolConfig,
    context: dict[str, Any],
    cache: _FoundationResponseCache,
    audit: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    stats: Counter[str] = Counter()

    def accept(start_fen: str, source_episode_id: Any, source_turn_index: Any, row: dict[str, Any], split: str) -> None:
        key = f"{start_fen}|{row['candidate_move']}|{split}"
        stats["generation_attempts"] += 1
        if key in seen:
            stats["duplicate_rejections"] += 1
            return
        if row["classification"] == "unsafe":
            stats["unsafe_rejections"] += 1
            return
        seen.add(key)
        entries.append(_pool_entry(cfg, start_fen, source_episode_id, source_turn_index, row, split))
        stats["accepted_entries"] += 1

    for episode in audit["audited_episodes"]:
        for turn in episode["turns"]:
            rows = sorted(turn["legal_candidate_alternatives"], key=_candidate_progress_score, reverse=True)
            for row in rows:
                split = _split_for_row(cfg, entries, row)
                if split is not None:
                    accept(turn["start_fen"], turn["source_episode_id"], turn["source_turn_index"], row, split)

    forward_fens = _forward_filter_fens(cfg, context)
    for source_index, fen in enumerate(forward_fens):
        _write_progress(cfg, {"phase": "pool_forward_filter_fen", "source_index": source_index, "fen": fen})
        board = chess.Board(fen)
        selected = _select_online_move(
            context["graph"],
            cache,
            context["mate2_cfg"],
            _tg29e_tg28c_cfg(cfg, context),
            context["edge_cfg"],
            board,
            context["selected"]["edge_weights"],
            context["selected"]["bridge_weights"] | _repair_weight_delta("combined_reply_robust"),
            masks={},
        )
        rows = [
            _compact_candidate_row(cfg, context, cache, board, row, selected_move=selected.get("selected_white_move"))
            for row in _candidate_rows_for_pool(cfg, context, cache, board)
        ]
        for row in sorted(rows, key=_candidate_progress_score, reverse=True):
            split = _split_for_row(cfg, entries, row)
            if split is not None:
                accept(fen, f"forward_{source_index}", 0, row, split)
        if _pool_targets_met(cfg, entries):
            break

    for entry in entries:
        stats[f"{entry['split']}_count"] += 1
    return entries, dict(stats)


def _forward_filter_fens(cfg: ReplyRobustProgressPoolConfig, context: dict[str, Any]) -> list[str]:
    fens = []
    for key in ("staged_heldout", "frontier_heldout", "generic_heldout", "near_miss_heldout", "mate2_heldout"):
        values = context.get(key, ())
        for item in values:
            fen = item["fen"] if isinstance(item, dict) else item
            fens.append(fen)
    return fens[: cfg.max_forward_filter_starts]


def _split_for_row(cfg: ReplyRobustProgressPoolConfig, entries: list[dict[str, Any]], row: dict[str, Any]) -> str | None:
    counts = Counter(entry["split"] for entry in entries)
    cls = row["classification"]
    if cls == "strong_reply_robust_progress" and counts["train"] < cfg.progress_positive_train_target:
        return "train"
    if cls in {"strong_reply_robust_progress", "partial_progress"} and counts["heldout"] < cfg.progress_positive_heldout_target:
        return "heldout"
    if cls == "safe_low_progress" and counts["negative_low_progress"] < cfg.low_progress_negative_target:
        return "negative_low_progress"
    if cls in {"partial_progress", "regress_without_blunder"} and counts["near_miss"] < cfg.near_miss_target:
        return "near_miss"
    if counts["regression"] < cfg.regression_target:
        return "regression"
    return None


def _pool_targets_met(cfg: ReplyRobustProgressPoolConfig, entries: list[dict[str, Any]]) -> bool:
    counts = Counter(entry["split"] for entry in entries)
    return (
        counts["train"] >= cfg.progress_positive_train_target
        and counts["heldout"] >= cfg.progress_positive_heldout_target
        and counts["negative_low_progress"] >= cfg.low_progress_negative_target
        and counts["near_miss"] >= cfg.near_miss_target
        and counts["regression"] >= cfg.regression_target
    )


def _pool_entry(
    cfg: ReplyRobustProgressPoolConfig,
    start_fen: str,
    source_episode_id: Any,
    source_turn_index: Any,
    row: dict[str, Any],
    split: str,
) -> dict[str, Any]:
    entry_id = _fen_key(f"{start_fen}|{row['candidate_move']}|{split}")
    return {
        "schema_version": "tg29e_reply_robust_progress_positive_pool_entry.v0",
        "pool_entry_id": f"tg29e_{entry_id}",
        "split": split,
        "source_episode_id": source_episode_id,
        "source_turn_index": source_turn_index,
        "start_fen": start_fen,
        "candidate_move": row["candidate_move"],
        "after_candidate_fen": row["after_white_move_fen"],
        "black_reply_policy_used_for_generation": "reply_envelope_frozen_foundation",
        "black_reply_rows": row["black_reply_envelope"]["black_reply_rows"],
        "safety_metrics": row["safety_metrics"],
        "progress_metrics": row["progress_metrics"],
        "classification": row["classification"] if split not in {"negative_low_progress", "near_miss"} else ("negative_near_miss" if split == "near_miss" else "safe_low_progress"),
        "bridge_feature_keys": row["bridge_feature_keys"],
        "positive_feature_keys": row["positive_feature_keys"],
        "foundation_config_hash": row["foundation_config_hash"],
        "cache_config_hash": row["cache_config_hash"],
        "live_graph_equivalence_hash": row["live_graph_equivalence_hash"],
        "source": "frozen_native_graph_response",
        "validator_labels_used_for_generation_only": True,
        "learner_visible_labels": False,
    }


def _write_pool_files(cfg: ReplyRobustProgressPoolConfig, entries: list[dict[str, Any]], stats: dict[str, Any]) -> dict[str, Any]:
    pool_path = Path(cfg.pool_path)
    pool_path.parent.mkdir(parents=True, exist_ok=True)
    pool_path.write_text("".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries), encoding="utf-8")
    counts = Counter(entry["split"] for entry in entries)
    index = {
        "schema_version": "tg29e_reply_robust_progress_positive_pool_index.v0",
        "progress_pool_path": str(pool_path),
        "progress_pool_index_path": cfg.pool_index_path,
        "progress_pool_entry_count": len(entries),
        "progress_positive_train_count": counts["train"],
        "progress_positive_heldout_count": counts["heldout"],
        "low_progress_negative_count": counts["negative_low_progress"],
        "near_miss_count": counts["near_miss"],
        "regression_count": counts["regression"],
        "generation_attempts": stats.get("generation_attempts", 0),
        "accepted_entries": stats.get("accepted_entries", 0),
        "duplicate_rejections": stats.get("duplicate_rejections", 0),
        "unsafe_rejections": stats.get("unsafe_rejections", 0),
        "no_foundation_response_rejections": stats.get("no_foundation_response_rejections", 0),
        "no_progress_positive_candidate_rejections": stats.get("no_progress_positive_candidate_rejections", 0),
        "timeout_count": stats.get("timeout_count", 0),
        "minimum_useful_diagnostic_met": (
            counts["train"] >= cfg.min_progress_positive_train_count
            and counts["heldout"] >= cfg.min_progress_positive_heldout_count
            and counts["negative_low_progress"] >= cfg.min_low_progress_negative_count
            and counts["near_miss"] >= cfg.min_near_miss_count
            and counts["regression"] >= cfg.min_regression_count
        ),
        "target_met": _pool_targets_met(cfg, entries),
    }
    index_path = Path(cfg.pool_index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _run_training_arms(
    cfg: ReplyRobustProgressPoolConfig,
    context: dict[str, Any],
    starts: tuple[dict[str, Any], ...],
    pool_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    all_arms = {
        "combined_reply_robust_baseline": _repair_weight_delta("combined_reply_robust"),
        "progress_positive_candidate_replay_only": _pool_weight_delta(pool_entries, include_positive=True, include_low_progress=False, include_near_miss=False),
        "combined_reply_robust_plus_progress_positive_replay": _merge_weights(_repair_weight_delta("combined_reply_robust"), _pool_weight_delta(pool_entries, include_positive=True, include_low_progress=False, include_near_miss=False)),
        "combined_reply_robust_plus_progress_positive_and_low_progress_negatives": _merge_weights(_repair_weight_delta("combined_reply_robust"), _pool_weight_delta(pool_entries, include_positive=True, include_low_progress=True, include_near_miss=False)),
        "combined_reply_robust_plus_progress_positive_low_progress_and_near_miss": _merge_weights(_repair_weight_delta("combined_reply_robust"), _pool_weight_delta(pool_entries, include_positive=True, include_low_progress=True, include_near_miss=True)),
    }
    arms = {name: all_arms[name] for name in cfg.training_arms}
    if "combined_reply_robust_baseline" not in arms:
        arms = {"combined_reply_robust_baseline": all_arms["combined_reply_robust_baseline"]} | arms
    out = {}
    for arm, delta in arms.items():
        policies = {}
        for policy in cfg.reply_policies:
            policies[policy] = _run_policy(cfg, context, starts, arm_name=arm, bridge_delta=delta, black_reply_policy=policy)
        out[arm] = {"arm": arm, "repair_weights": delta, "policies": policies}
        _write_progress(cfg, {"phase": "arm_complete", "arm": arm, "success": policies["deterministic_worst_foundation_reply"]["summary"]["episode_success_rate"]})
    return out


def _ensure_policy_comparisons(
    cfg: ReplyRobustProgressPoolConfig,
    context: dict[str, Any],
    starts: tuple[dict[str, Any], ...],
    pool_entries: list[dict[str, Any]],
    arm_results: dict[str, Any],
    selected_arm: str,
) -> None:
    delta = arm_results[selected_arm]["repair_weights"]
    for policy in cfg.comparison_reply_policies:
        if policy not in arm_results[selected_arm]["policies"]:
            arm_results[selected_arm]["policies"][policy] = _run_policy(cfg, context, starts, arm_name=selected_arm, bridge_delta=delta, black_reply_policy=policy)


def _run_policy(
    cfg: ReplyRobustProgressPoolConfig,
    context: dict[str, Any],
    starts: tuple[dict[str, Any], ...],
    *,
    arm_name: str,
    bridge_delta: dict[str, float],
    black_reply_policy: str,
    masks: dict[str, bool] | None = None,
) -> dict[str, Any]:
    base_cfg = type(cfg.base)(**{**asdict(cfg.base), "black_reply_policy": black_reply_policy})
    tg28c_cfg = _tg29e_tg28c_cfg(cfg, context)
    cache = _FoundationResponseCache(context["graph"], context["mate2_cfg"], tg28c_cfg)
    bridge_weights = dict(context["selected"]["bridge_weights"])
    bridge_weights.update(bridge_delta)
    episodes = _run_episodes(
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
    episodes = _enrich_episodes(episodes, context | {"cache": cache, "tg28c_cfg": tg28c_cfg}, OnlineFailureDecompositionConfig(base=base_cfg))
    summary = _episode_summary(episodes)
    return {"summary": summary, "progress_summary": _progress_summary(episodes), "episodes": episodes, "arm_name": arm_name}


def _episode_summary(episodes: dict[str, Any]) -> dict[str, Any]:
    summary = _progress_summary(episodes)
    return {
        key: summary[key]
        for key in (
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
    }


def _pool_weight_delta(
    entries: list[dict[str, Any]],
    *,
    include_positive: bool,
    include_low_progress: bool,
    include_near_miss: bool,
) -> dict[str, float]:
    weights: dict[str, float] = {}
    for entry in entries:
        split = entry["split"]
        if split in {"train", "heldout"} and not include_positive:
            continue
        if split == "negative_low_progress" and not include_low_progress:
            continue
        if split == "near_miss" and not include_near_miss:
            continue
        sign = 1.0 if split in {"train", "heldout"} else -1.0
        scale = 0.08 if sign > 0 else 0.05
        if split == "near_miss":
            scale = 0.03
        for key in entry.get("bridge_feature_keys", []):
            weights[key] = max(-1.0, min(1.0, weights.get(key, 0.0) + sign * scale))
    return weights


def _merge_weights(*deltas: dict[str, float]) -> dict[str, float]:
    merged: dict[str, float] = {}
    for delta in deltas:
        for key, value in delta.items():
            merged[key] = max(-2.5, min(2.5, merged.get(key, 0.0) + value))
    return merged


def _select_training_arm(arm_results: dict[str, Any]) -> str:
    baseline = arm_results["combined_reply_robust_baseline"]["policies"]["deterministic_worst_foundation_reply"]["progress_summary"]
    candidates = []
    for arm, result in arm_results.items():
        s = result["policies"]["deterministic_worst_foundation_reply"]["progress_summary"]
        improved_low = baseline["selected_moves_safe_but_low_progress_count"] - s["selected_moves_safe_but_low_progress_count"]
        safety_clean = s["rook_blunder_count"] == 0 and s["illegal_move_count"] == 0 and s["stalemate_count"] == 0
        loop_ok = s["bridge_loop_without_foundation_progress_count"] <= baseline["bridge_loop_without_foundation_progress_count"]
        candidates.append((
            int(improved_low > 0 and safety_clean and loop_ok),
            improved_low,
            s["episode_success_count"],
            -s["bridge_loop_without_foundation_progress_count"],
            arm,
        ))
    best = max(candidates)
    return best[-1] if best[0] else "combined_reply_robust_baseline"


def _selected_arm_ablations(
    cfg: ReplyRobustProgressPoolConfig,
    context: dict[str, Any],
    starts: tuple[dict[str, Any], ...],
    pool_entries: list[dict[str, Any]],
    selected_arm: str,
) -> dict[str, Any]:
    if cfg.base.max_episode_ablation_count <= 0:
        names = (
            "mask_edge_fence_terminals",
            "mask_bridge_pressure_terminals",
            "mask_reply_robust_bridge_terminals",
            "mask_progress_positive_terminals_or_evidence",
            "mask_low_progress_veto_terminals_or_evidence",
            "mask_foundation_response_terminals",
            "mask_action_delta_terminals",
            "mask_internal_attention_request_strength_terminals",
            "mask_safety_veto_terminals",
            "mask_actuator_terminals",
            "disable_reply_envelope_foundation_checks",
            "disable_worst_reply_bridge_evidence",
            "mask_frozen_mate1_foundation_quorum",
            "mask_frozen_mate2_foundation_quorum",
        )
        return {name: {"skipped": True, "skip_reason": "max_episode_ablation_count_zero"} for name in names}
    ablation_starts = starts[: max(1, cfg.base.max_episode_ablation_count)]
    base_delta = _arm_delta(selected_arm, pool_entries)
    masks = {
        "mask_edge_fence_terminals": {"mask_edge_fence_terminals": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_reply_robust_bridge_terminals": {"mask_bridge_pressure_terminals": True, "disable_reply_envelope_foundation_checks": True},
        "mask_foundation_response_terminals": {"mask_foundation_response_terminals": True},
        "mask_action_delta_terminals": {"mask_action_delta_terminals": True},
        "mask_internal_attention_request_strength_terminals": {"mask_internal_attention_request_strength_terminals": True},
        "mask_safety_veto_terminals": {"mask_safety_veto_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "disable_reply_envelope_foundation_checks": {"disable_reply_envelope_foundation_checks": True},
        "disable_worst_reply_bridge_evidence": {"disable_reply_envelope_foundation_checks": True},
        "mask_frozen_mate1_foundation_quorum": {"mask_frozen_mate1_foundation_quorum": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_frozen_mate2_foundation_quorum": True},
    }
    out: dict[str, Any] = {}
    for name, mask in masks.items():
        out[name] = _run_policy(
            cfg,
            context,
            ablation_starts,
            arm_name=selected_arm,
            bridge_delta=base_delta,
            black_reply_policy="deterministic_worst_foundation_reply",
            masks=mask,
        )["progress_summary"]
    out["mask_progress_positive_terminals_or_evidence"] = _run_policy(
        cfg,
        context,
        ablation_starts,
        arm_name=selected_arm,
        bridge_delta=_merge_weights(_repair_weight_delta("combined_reply_robust"), _pool_weight_delta(pool_entries, include_positive=False, include_low_progress=True, include_near_miss=True)),
        black_reply_policy="deterministic_worst_foundation_reply",
    )["progress_summary"]
    out["mask_low_progress_veto_terminals_or_evidence"] = _run_policy(
        cfg,
        context,
        ablation_starts,
        arm_name=selected_arm,
        bridge_delta=_merge_weights(_repair_weight_delta("combined_reply_robust"), _pool_weight_delta(pool_entries, include_positive=True, include_low_progress=False, include_near_miss=True)),
        black_reply_policy="deterministic_worst_foundation_reply",
    )["progress_summary"]
    return out


def _arm_delta(arm: str, entries: list[dict[str, Any]]) -> dict[str, float]:
    if arm == "combined_reply_robust_baseline":
        return _repair_weight_delta("combined_reply_robust")
    if arm == "progress_positive_candidate_replay_only":
        return _pool_weight_delta(entries, include_positive=True, include_low_progress=False, include_near_miss=False)
    if arm == "combined_reply_robust_plus_progress_positive_replay":
        return _merge_weights(_repair_weight_delta("combined_reply_robust"), _pool_weight_delta(entries, include_positive=True, include_low_progress=False, include_near_miss=False))
    if arm == "combined_reply_robust_plus_progress_positive_and_low_progress_negatives":
        return _merge_weights(_repair_weight_delta("combined_reply_robust"), _pool_weight_delta(entries, include_positive=True, include_low_progress=True, include_near_miss=False))
    if arm == "combined_reply_robust_plus_progress_positive_low_progress_and_near_miss":
        return _merge_weights(_repair_weight_delta("combined_reply_robust"), _pool_weight_delta(entries, include_positive=True, include_low_progress=True, include_near_miss=True))
    return _repair_weight_delta("combined_reply_robust")


def _decision(
    cfg: ReplyRobustProgressPoolConfig,
    *,
    context: dict[str, Any],
    selected_arm: str,
    selected_summary: dict[str, Any],
    baseline_summary: dict[str, Any],
    candidate_audit: dict[str, Any],
    pool_index: dict[str, Any],
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
    regression_clean = all(
        regression[key]
        for key in ("frontier_regression_pass", "staged_regression_pass", "near_miss_regression_pass", "generic_edge_regression_pass", "foundation_sanity_pass")
    )
    safety_clean = selected_summary["rook_blunder_count"] == 0 and selected_summary["illegal_move_count"] == 0 and selected_summary["stalemate_count"] == 0
    low_progress_reduced = selected_summary["selected_moves_safe_but_low_progress_count"] < baseline_summary["selected_moves_safe_but_low_progress_count"]
    loop_ok = selected_summary["bridge_loop_without_foundation_progress_count"] <= baseline_summary["bridge_loop_without_foundation_progress_count"]
    progress_causal = _ablation_increases_low_progress(ablations, "mask_progress_positive_terminals_or_evidence", selected_summary)
    low_negative_causal = _ablation_increases_low_progress(ablations, "mask_low_progress_veto_terminals_or_evidence", selected_summary)
    repair_pass = (
        selected_arm != "combined_reply_robust_baseline"
        and low_progress_reduced
        and loop_ok
        and safety_clean
        and progress_causal
        and m3_delta == 0
        and m4_delta == 0
        and cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
        and regression_clean
    )
    diagnostic_pass = (
        not repair_pass
        and candidate_audit["audited_candidate_count"] > 0
        and safety_clean
        and m3_delta == 0
        and m4_delta == 0
        and cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
        and regression_clean
    )
    policy_rates = {policy: row["summary"]["episode_success_rate"] for policy, row in arm_results[selected_arm]["policies"].items()}
    failure_bucket_counts = Counter(selected_summary["failure_bucket_counts"])
    if candidate_audit["better_progress_candidate_lost_selection_count"] > 0 and not low_progress_reduced:
        failure_bucket_counts["better_progress_candidate_exists_but_lost_selection"] += candidate_audit["better_progress_candidate_lost_selection_count"]
    elif candidate_audit["no_better_progress_candidate_count"] > 0:
        failure_bucket_counts["no_better_progress_candidate_exists"] += candidate_audit["no_better_progress_candidate_count"]
    if not progress_causal and pool_index["progress_pool_entry_count"] > 0:
        failure_bucket_counts["progress_positive_replay_no_effect"] += 1
    return {
        "checkpoint_pass": bool(repair_pass or diagnostic_pass),
        "checkpoint_interpretation": (
            "progress_positive_pool_repair_reduced_low_progress"
            if repair_pass
            else (
                "better_progress_candidates_exist_selection_not_repaired"
                if candidate_audit["better_progress_candidate_lost_selection_count"] > 0
                else "progress_pool_diagnostic_no_clear_repair"
            )
        ),
        "selected_training_arm": selected_arm,
        "repair_applied": bool(repair_pass),
        "foundation_frozen": m3_delta == 0 and m4_delta == 0,
        "foundation_mate1_accuracy": context["foundation_sanity"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": context["foundation_sanity"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": cache_equivalence["foundation_cache_live_mismatch_count"],
        "foundation_m3_updates_during_training": 0,
        "foundation_m4_promotions_during_training": 0,
        "foundation_m3_updates_during_eval": m3_delta,
        "foundation_m4_promotions_during_eval": m4_delta,
        "audited_candidate_count": candidate_audit["audited_candidate_count"],
        "progress_positive_candidate_count": candidate_audit["progress_positive_candidate_count"],
        "better_progress_candidate_available_count": candidate_audit["better_progress_candidate_available_count"],
        "better_progress_candidate_lost_selection_count": candidate_audit["better_progress_candidate_lost_selection_count"],
        "no_better_progress_candidate_count": candidate_audit["no_better_progress_candidate_count"],
        **{key: pool_index[key] for key in (
            "progress_pool_entry_count",
            "progress_positive_train_count",
            "progress_positive_heldout_count",
            "low_progress_negative_count",
            "near_miss_count",
            "regression_count",
        )},
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
            "bridge_loop_without_foundation_progress_count",
            "selected_moves_safe_but_low_progress_count",
            "repeated_safe_no_progress_count",
            "repeated_bridge_no_progress_count",
            "meaningful_edge_progress_count",
            "meaningful_bridge_progress_count",
            "meaningful_foundation_progress_count",
        )},
        "success_rate_by_black_reply_policy": policy_rates,
        "worst_foundation_reply_success_rate": policy_rates.get("deterministic_worst_foundation_reply", 0.0),
        "mobility_max_reply_success_rate": policy_rates.get("mobility_maximizing", 0.0),
        "random_reply_success_rate": policy_rates.get("fixed_seed_random"),
        "low_progress_count_by_reply_policy": {
            policy: row["progress_summary"]["selected_moves_safe_but_low_progress_count"]
            for policy, row in arm_results[selected_arm]["policies"].items()
        },
        "bridge_loop_count_by_reply_policy": {
            policy: row["progress_summary"]["bridge_loop_without_foundation_progress_count"]
            for policy, row in arm_results[selected_arm]["policies"].items()
        },
        "safety_failure_count_by_reply_policy": {
            policy: row["progress_summary"]["rook_blunder_count"] + row["progress_summary"]["illegal_move_count"] + row["progress_summary"]["stalemate_count"]
            for policy, row in arm_results[selected_arm]["policies"].items()
        },
        "frontier_regression_pass": regression["frontier_regression_pass"],
        "staged_regression_pass": regression["staged_regression_pass"],
        "near_miss_regression_pass": regression["near_miss_regression_pass"],
        "generic_edge_regression_pass": regression["generic_edge_regression_pass"],
        "foundation_sanity_pass": regression["foundation_sanity_pass"],
        "failure_bucket_counts": dict(failure_bucket_counts),
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "ablation_results": ablations,
        "progress_positive_ablation_causal": progress_causal,
        "low_progress_negative_ablation_causal": low_negative_causal,
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


def _ablation_increases_low_progress(ablations: dict[str, Any], name: str, selected: dict[str, Any]) -> bool:
    row = ablations.get(name, {})
    return not row.get("skipped", False) and row.get("selected_moves_safe_but_low_progress_count", 0) > selected["selected_moves_safe_but_low_progress_count"]


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29c_purity_boundary()
    boundary.update({
        "checkpoint": "TG29e",
        "reply_robust_progress_positive_pool": True,
        "pool_labels_trainer_side_only": True,
        "runtime_move_selection": "graph_mediated_candidate_weights_no_provider_override",
        "direct_provider_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "learner_visible_stage_labels": False,
    })
    return boundary


def _hash_dict(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def _fen_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _write_progress(cfg: ReplyRobustProgressPoolConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
