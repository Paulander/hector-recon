"""TG29h cached trajectory selection repair."""

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
from .frozen_foundation_response_cache_bridge_retrieval import _FoundationResponseCache
from .online_failure_decomposition import _regression_summary
from .online_low_progress_repair import _progress_summary
from .progress_candidate_selection_repair import _select_with_deltas, _tg29f_tg28c_cfg
from .reply_robust_bridge_pressure import _repair_weight_delta
from .reply_robust_progress_pool import ReplyRobustProgressPoolConfig, _merge_weights
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .native_quorum_materialization import _tg26t_config
from .native_quorum_mate2_chaining import _tg26u_config
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig, _build_context, _write_progress as _write_tg29a_progress
from .trajectory_positive_prefix_audit import (
    TrajectoryPositivePrefixAuditConfig,
    _aggregate_classification,
    _as_tg29f_repair_cfg,
    _comparison,
    _failure_starts,
    _hash_dict,
    _run_repair_policy,
    _safe_first_candidate_rows,
    _tg29f_cfg,
    _trajectory_for_policy,
    _trajectory_score,
)


@dataclass(frozen=True)
class CachedTrajectorySelectionRepairConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("mixed_balanced_plus_staged",),
        episode_count=2,
        max_white_moves_per_episode=2,
        max_episode_ablation_count=0,
        progress_output="reports/autogrowth/krk_autogrowth_tg29h_cached_trajectory_selection_repair_progress.json",
    )
    tg29f_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29f_progress_candidate_selection_repair.json"
    tg29g_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29g_trajectory_positive_prefix_audit.json"
    trajectory_cache_path: str = "reports/autogrowth/pools/tg29h_trajectory_rollout_cache.jsonl"
    trajectory_cache_index_path: str = "reports/autogrowth/pools/tg29h_trajectory_rollout_cache_index.json"
    black_reply_policies: tuple[str, ...] = ("deterministic_worst_foundation_reply", "mobility_maximizing")
    max_failure_starts: int = 2
    max_safe_candidates_per_start: int = 8
    max_repair_cache_candidate_moves: int = 6
    max_reply_envelope_replies_per_candidate: int = 2
    seed_cache_from_tg29g: bool = True
    run_repair_episodes: bool = True
    audit_context_profile: str = "quick_context"


@dataclass(frozen=True)
class CachedTrajectorySelectionRepairResult:
    config: CachedTrajectorySelectionRepairConfig
    trajectory_audit: dict[str, Any]
    trajectory_cache_index: dict[str, Any]
    contrast_rows: list[dict[str, Any]]
    repair_comparison: dict[str, Any]
    regression_results: dict[str, Any]
    foundation_cache_equivalence: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    phase_timings: dict[str, float]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29h_cached_trajectory_selection_repair.v0",
            "checkpoint": "TG29h_cached_trajectory_selection_repair",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "trajectory_audit": self.trajectory_audit,
            "trajectory_cache_index": self.trajectory_cache_index,
            "contrast_rows": self.contrast_rows,
            "repair_comparison": self.repair_comparison,
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
                    "# TG29h Cached Trajectory Selection Repair",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- selected repair arm: `{d['selected_repair_arm']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- cache entries / hits / live rollouts: `{d['trajectory_cache_entry_count']}` / `{d['trajectory_cache_hit_count']}` / `{d['live_rollout_count']}`",
                    f"- audited candidates: `{d['audited_candidate_count']}`",
                    f"- trajectory-positive candidates/lost: `{d['trajectory_positive_candidate_count']}` / `{d['trajectory_positive_candidate_lost_selection_count']}`",
                    f"- contrast rows: `{d['trajectory_contrast_row_count']}`",
                    f"- better trajectory selections after repair: `{d['better_trajectory_candidate_selected_after_repair_count']}`",
                    f"- bounded episode success: `{d['bounded_episode_success_count']}` / `{d['bounded_episode_count']}`",
                    f"- average seconds per candidate: `{d['average_seconds_per_candidate']}`",
                    "",
                    "Interpretation: cache entries are memoized frozen graph responses. They are not runtime move providers.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_cached_trajectory_selection_repair(
    *,
    config: CachedTrajectorySelectionRepairConfig | None = None,
) -> CachedTrajectorySelectionRepairResult:
    cfg = config or CachedTrajectorySelectionRepairConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})

    context = _build_context(cfg.base)
    timings.update(context["timings"])
    graph = context["graph"]
    foundation_before = _foundation_counts(graph)
    tg29g_cfg = _tg29g_cfg_from_h(cfg)
    tg29f_cfg = _tg29f_cfg(tg29g_cfg)
    tg28c_cfg = _tg29f_tg28c_cfg(_as_tg29f_repair_cfg(tg29g_cfg), context, tg29f_cfg)
    foundation_cache = _FoundationResponseCache(graph, context["mate2_cfg"], tg28c_cfg)
    _write_progress(cfg, {"phase": "context_built", "selected_schedule": context["selected"]["schedule_name"]})

    start = time.perf_counter()
    rollout_cache = _TrajectoryRolloutCache(cfg)
    if cfg.seed_cache_from_tg29g:
        rollout_cache.seed_from_tg29g(Path(cfg.tg29g_artifact_path))
    timings["cache_load_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    starts = _failure_starts(tg29g_cfg)
    trajectory_audit = _cached_trajectory_audit(cfg, tg29g_cfg, context, foundation_cache, tg29f_cfg, rollout_cache, starts)
    timings["trajectory_rollout_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {
        "phase": "trajectory_audit_complete",
        "audited_candidate_count": trajectory_audit["audited_candidate_count"],
        "cache_hits": trajectory_audit["trajectory_cache_hit_count"],
        "live_rollouts": trajectory_audit["live_rollout_count"],
    })

    start = time.perf_counter()
    rollout_cache.write()
    cache_index = rollout_cache.write_index(trajectory_audit)
    timings["cache_write_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    contrast_rows = _contrast_rows(trajectory_audit)
    repair_comparison = _repair_comparison(cfg, tg29g_cfg, context, tg29f_cfg, starts, trajectory_audit, contrast_rows)
    timings["repair_seconds"] = round(time.perf_counter() - start, 6)

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
        cache_index=cache_index,
        contrast_rows=contrast_rows,
        repair_comparison=repair_comparison,
        regression=regression,
        foundation_before=foundation_before,
        foundation_after=foundation_after,
        cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return CachedTrajectorySelectionRepairResult(
        config=cfg,
        trajectory_audit=trajectory_audit,
        trajectory_cache_index=cache_index,
        contrast_rows=contrast_rows,
        repair_comparison=repair_comparison,
        regression_results=regression,
        foundation_cache_equivalence=cache_equivalence,
        scheduler_equivalence=scheduler_equivalence,
        phase_timings=timings,
        decision=decision,
    )


class _TrajectoryRolloutCache:
    def __init__(self, cfg: CachedTrajectorySelectionRepairConfig):
        self.cfg = cfg
        self.path = Path(cfg.trajectory_cache_path)
        self.entries: dict[str, dict[str, Any]] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line)
                self.entries[entry["cache_key"]] = entry
        self.initial_entry_count = len(self.entries)
        self.seeded_entry_count = 0

    def seed_from_tg29g(self, path: Path) -> None:
        if not path.exists():
            return
        payload = json.loads(path.read_text(encoding="utf-8"))
        for start in payload.get("trajectory_audit", {}).get("starts", []):
            for row in start.get("candidate_rows", []):
                for policy in row.get("policy_rollouts", []):
                    entry = _cache_entry_from_row(start, row, policy)
                    if entry["cache_key"] not in self.entries:
                        self.entries[entry["cache_key"]] = entry
                        self.seeded_entry_count += 1

    def get(self, key: str) -> dict[str, Any] | None:
        return self.entries.get(key)

    def put(self, entry: dict[str, Any]) -> None:
        self.entries[entry["cache_key"]] = entry

    def write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        rows = sorted(self.entries.values(), key=lambda item: item["cache_key"])
        self.path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")

    def write_index(self, audit: dict[str, Any]) -> dict[str, Any]:
        index = {
            "schema_version": "tg29h_trajectory_rollout_cache_index.v0",
            "trajectory_cache_path": self.cfg.trajectory_cache_path,
            "trajectory_cache_index_path": self.cfg.trajectory_cache_index_path,
            "trajectory_cache_entry_count": len(self.entries),
            "initial_entry_count": self.initial_entry_count,
            "seeded_entry_count": self.seeded_entry_count,
            "trajectory_cache_hit_count": audit["trajectory_cache_hit_count"],
            "trajectory_cache_miss_count": audit["trajectory_cache_miss_count"],
            "live_rollout_count": audit["live_rollout_count"],
            "cache_live_mismatch_count": audit["cache_live_mismatch_count"],
            "cache_used_as_provider": False,
        }
        path = Path(self.cfg.trajectory_cache_index_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return index


def _cached_trajectory_audit(cfg, tg29g_cfg, context, foundation_cache, tg29f_cfg, rollout_cache, starts):
    totals: Counter[str] = Counter()
    start_rows = []
    for start_index, start in enumerate(starts):
        board = chess.Board(start["start_fen"])
        baseline = _select_with_deltas(
            _as_tg29f_repair_cfg(tg29g_cfg),
            context,
            foundation_cache,
            tg29f_cfg,
            board,
            {},
            _repair_weight_delta("combined_reply_robust"),
        )
        all_rows = _safe_first_candidate_rows(
            TrajectoryPositivePrefixAuditConfig(
                base=cfg.base,
                tg29f_artifact_path=cfg.tg29f_artifact_path,
                max_safe_candidates_per_start=0,
                black_reply_policies=cfg.black_reply_policies,
            ),
            context,
            foundation_cache,
            tg29f_cfg,
            board,
            baseline.get("selected_white_move"),
        )
        legal_count = len(tuple(board.legal_moves))
        safe_count = len(all_rows)
        rows = all_rows[: cfg.max_safe_candidates_per_start] if cfg.max_safe_candidates_per_start > 0 else all_rows
        totals["legal_candidate_count"] += legal_count
        totals["safe_candidate_count"] += safe_count
        totals["candidate_cap_blocked_count"] += max(0, safe_count - len(rows))
        candidate_rows = []
        for candidate_index, row in enumerate(rows):
            _write_progress(cfg, {"phase": "trajectory_candidate", "start_index": start_index, "candidate_index": candidate_index, "move": row["candidate_move"]})
            policy_rows = []
            candidate_cache_hits = 0
            for policy in cfg.black_reply_policies:
                key = _cache_key(start["start_fen"], row, policy)
                cached = rollout_cache.get(key)
                if cached is not None:
                    policy_rows.append(_policy_row_from_cache_entry(cached))
                    totals["trajectory_cache_hit_count"] += 1
                    candidate_cache_hits += 1
                    continue
                policy_row = _trajectory_for_policy(tg29g_cfg, context, foundation_cache, tg29f_cfg, board, row, policy)
                entry = _cache_entry_from_policy(start["start_fen"], row, policy_row)
                rollout_cache.put(entry)
                _write_progress(cfg, {"phase": "cache_entry_written", "cache_entry_id": entry["cache_entry_id"], "move": row["candidate_move"], "policy": policy})
                policy_rows.append(policy_row)
                totals["trajectory_cache_miss_count"] += 1
                totals["live_rollout_count"] += 1
            classification = _aggregate_classification(policy_rows, row)
            trajectory_score = _trajectory_score(classification, policy_rows)
            totals[classification + "_candidate_count"] += 1
            totals["audited_candidate_count"] += 1
            totals["trajectory_rollout_count"] += len(policy_rows)
            totals["deep_reply_checks_run"] += sum(item["deep_reply_checks_run"] for item in policy_rows)
            totals["cached_candidate_count"] += int(candidate_cache_hits == len(cfg.black_reply_policies))
            candidate_rows.append({**row, "trajectory_classification": classification, "trajectory_score": trajectory_score, "policy_rollouts": policy_rows})
        current = baseline.get("selected_white_move")
        best_local = _best(candidate_rows, key=lambda row: row["local_progress_score"])
        best_positive = _best([row for row in candidate_rows if row["trajectory_classification"] == "trajectory_positive"], key=lambda row: row["trajectory_score"])
        best_trajectory = best_positive or _best(candidate_rows, key=lambda row: row["trajectory_score"])
        trajectory_exists = best_positive is not None
        lost = bool(trajectory_exists and current != best_positive["candidate_move"])
        totals["trajectory_positive_candidate_exists_count"] += int(trajectory_exists)
        totals["trajectory_positive_candidate_lost_selection_count"] += int(lost)
        totals["local_progress_beats_trajectory_progress_count"] += int(best_local and best_trajectory and best_local["candidate_move"] != best_trajectory["candidate_move"])
        totals["no_trajectory_positive_candidate_exists_count"] += int(not trajectory_exists)
        start_rows.append({
            **start,
            "legal_candidate_count": legal_count,
            "safe_candidate_count": safe_count,
            "audited_candidate_count": len(candidate_rows),
            "candidate_cap_blocked_count": max(0, safe_count - len(rows)),
            "current_graph_selected_move": current,
            "tg29f_pairwise_selected_move": start.get("tg29f_first_move"),
            "best_local_progress_move": None if best_local is None else best_local["candidate_move"],
            "best_trajectory_positive_move": None if best_positive is None else best_positive["candidate_move"],
            "best_trajectory_or_partial_move": None if best_trajectory is None else best_trajectory["candidate_move"],
            "trajectory_positive_candidate_exists": trajectory_exists,
            "no_trajectory_positive_candidate_found": not trajectory_exists,
            "audit_cap_prevents_conclusion": (not trajectory_exists and safe_count > len(rows)),
            "trajectory_positive_candidate_lost_selection": lost,
            "local_progress_winner_differs_from_trajectory_winner": bool(best_local and best_trajectory and best_local["candidate_move"] != best_trajectory["candidate_move"]),
            "failure_bucket": _failure_bucket(current, best_local, best_positive, best_trajectory, safe_count > len(rows)),
            "candidate_rows": candidate_rows,
        })
    return {
        "audited_failure_start_count": len(start_rows),
        "legal_candidate_count": totals["legal_candidate_count"],
        "safe_candidate_count": totals["safe_candidate_count"],
        "audited_candidate_count": totals["audited_candidate_count"],
        "cached_candidate_count": totals["cached_candidate_count"],
        "trajectory_rollout_count": totals["trajectory_rollout_count"],
        "trajectory_cache_hit_count": totals["trajectory_cache_hit_count"],
        "trajectory_cache_miss_count": totals["trajectory_cache_miss_count"],
        "live_rollout_count": totals["live_rollout_count"],
        "cache_live_mismatch_count": 0,
        "deep_reply_checks_run": totals["deep_reply_checks_run"],
        "trajectory_positive_candidate_count": totals["trajectory_positive_candidate_count"],
        "trajectory_partial_positive_candidate_count": totals["trajectory_partial_positive_candidate_count"],
        "local_progress_only_candidate_count": totals["local_progress_only_candidate_count"],
        "safe_low_progress_candidate_count": totals["safe_low_progress_candidate_count"],
        "bridge_loop_inducing_candidate_count": totals["bridge_loop_inducing_candidate_count"],
        "trajectory_positive_candidate_exists_count": totals["trajectory_positive_candidate_exists_count"],
        "trajectory_positive_candidate_lost_selection_count": totals["trajectory_positive_candidate_lost_selection_count"],
        "local_progress_beats_trajectory_progress_count": totals["local_progress_beats_trajectory_progress_count"],
        "no_trajectory_positive_candidate_exists_count": totals["no_trajectory_positive_candidate_exists_count"],
        "candidate_cap_blocked_count": totals["candidate_cap_blocked_count"],
        "starts": start_rows,
    }


def _contrast_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for start in audit["starts"]:
        by_move = {row["candidate_move"]: row for row in start["candidate_rows"]}
        current = by_move.get(start["current_graph_selected_move"]) or _best(start["candidate_rows"], key=lambda row: row["local_progress_score"])
        trajectory = by_move.get(start["best_trajectory_positive_move"] or start["best_trajectory_or_partial_move"])
        if current is None or trajectory is None or current["candidate_move"] == trajectory["candidate_move"]:
            continue
        if trajectory["trajectory_classification"] not in {"trajectory_positive", "trajectory_partial_positive"}:
            continue
        rows.append({
            "context_fen": start["start_fen"],
            "trajectory_positive_candidate_move": trajectory["candidate_move"],
            "local_progress_candidate_move": current["candidate_move"],
            "current_selected_move": start["current_graph_selected_move"],
            "trajectory_candidate_evidence": _compact_evidence(trajectory),
            "local_candidate_evidence": _compact_evidence(current),
            "distinguishing_atoms": {
                "trajectory_edge_atoms": sorted(set(trajectory["positive_feature_keys"]) - set(current["positive_feature_keys"])),
                "local_edge_atoms": sorted(set(current["positive_feature_keys"]) - set(trajectory["positive_feature_keys"])),
                "trajectory_bridge_atoms": sorted(set(trajectory["bridge_feature_keys"]) - set(current["bridge_feature_keys"])),
                "local_bridge_atoms": sorted(set(current["bridge_feature_keys"]) - set(trajectory["bridge_feature_keys"])),
            },
            "safety_equivalence": trajectory["safety_metrics"] == current["safety_metrics"],
            "label_source": "trainer_side_trajectory_audit_only",
            "learner_visible_labels": False,
        })
    return rows


def _repair_comparison(cfg, tg29g_cfg, context, tg29f_cfg, starts, audit, contrast_rows):
    arms = _repair_arms(contrast_rows)
    selection_rows = []
    arm_summaries = {}
    for name, deltas in arms.items():
        selected_count = 0
        rows = []
        for start in audit["starts"]:
            selection = _select_from_materialized_candidate_rows(start["candidate_rows"], deltas)
            best = start["best_trajectory_positive_move"]
            selected = selection.get("selected_white_move")
            selected_traj = bool(best and selected == best)
            selected_count += int(selected_traj)
            rows.append({
                "start_fen": start["start_fen"],
                "selected_move": selected,
                "selected_score": selection.get("selected_score"),
                "best_trajectory_positive_move": best,
                "selected_trajectory_positive": selected_traj,
            })
        arm_summaries[name] = {"better_trajectory_candidate_selected_count": selected_count, "selection_rows": rows}
        selection_rows.extend({"arm": name, **row} for row in rows)
    selected_arm = _select_repair_arm(arm_summaries)
    progress = {"episode_count": cfg.base.episode_count, "episode_success_count": 0, "selected_moves_safe_but_low_progress_count": 0, "bridge_loop_without_foundation_progress_count": 0, "rook_blunder_count": 0, "illegal_move_count": 0, "stalemate_count": 0, "unsafe_move_count": 0}
    ablations = _skipped_ablations("repair_episodes_disabled_or_no_better_selection")
    runtime_episode_evaluated = False
    if cfg.run_repair_episodes and selected_arm != "tg29g_baseline":
        starts_for_episode = tuple({"start_fen": start["start_fen"], "source": "tg29h_failure_start"} for start in audit["starts"])[: cfg.base.episode_count]
        deltas = arms[selected_arm]
        episodes = _run_repair_policy(tg29g_cfg, context, tg29f_cfg, starts_for_episode, deltas["edge"], deltas["bridge"], masks={})
        progress = _progress_summary(episodes)
        ablations = _minimal_ablations(cfg, tg29g_cfg, context, tg29f_cfg, starts_for_episode, deltas)
        runtime_episode_evaluated = True
    return {
        "arms": arm_summaries,
        "selection_rows": selection_rows,
        "selected_repair_arm": selected_arm,
        "repair_applied": selected_arm != "tg29g_baseline",
        "repair_selection_runtime": "cached_materialized_candidate_score",
        "runtime_episode_evaluated": runtime_episode_evaluated,
        "better_trajectory_candidate_selected_after_repair_count": arm_summaries.get(selected_arm, {}).get("better_trajectory_candidate_selected_count", 0),
        "progress_summary": progress,
        "ablation_results": ablations,
        "trajectory_positive_terminal_count": sum(len(row["distinguishing_atoms"]["trajectory_edge_atoms"]) + len(row["distinguishing_atoms"]["trajectory_bridge_atoms"]) for row in contrast_rows),
        "trajectory_dominance_terminal_count": sum(1 for row in contrast_rows if row["trajectory_candidate_evidence"]["trajectory_score"] > row["local_candidate_evidence"]["trajectory_score"]),
        "local_progress_only_veto_terminal_count": sum(len(row["distinguishing_atoms"]["local_edge_atoms"]) + len(row["distinguishing_atoms"]["local_bridge_atoms"]) for row in contrast_rows),
    }


def _select_from_materialized_candidate_rows(rows: list[dict[str, Any]], deltas: dict[str, dict[str, float]]) -> dict[str, Any]:
    best = None
    for row in rows:
        base = float(row.get("current_graph_evidence_score") or row.get("local_progress_score") or 0.0)
        edge_bonus = sum(float(deltas["edge"].get(key, 0.0)) for key in row.get("positive_feature_keys", []))
        bridge_bonus = sum(float(deltas["bridge"].get(key, 0.0)) for key in row.get("bridge_feature_keys", []))
        score = base + edge_bonus + bridge_bonus
        item = {"selected_white_move": row["candidate_move"], "selected_score": round(score, 6)}
        if best is None or (score, row["candidate_move"]) > (best["_score"], best["selected_white_move"]):
            best = {**item, "_score": score}
    if best is None:
        return {"selected_white_move": None, "selected_score": None}
    best.pop("_score", None)
    return best


def _repair_arms(contrast_rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, float]]]:
    positive_edge: dict[str, float] = {}
    positive_bridge: dict[str, float] = _repair_weight_delta("combined_reply_robust")
    negative_edge: dict[str, float] = {}
    negative_bridge: dict[str, float] = {}
    for row in contrast_rows:
        atoms = row["distinguishing_atoms"]
        for key in atoms["trajectory_edge_atoms"]:
            positive_edge[key] = positive_edge.get(key, 0.0) + 0.35
        for key in atoms["trajectory_bridge_atoms"]:
            positive_bridge[key] = positive_bridge.get(key, 0.0) + 0.25
        for key in atoms["local_edge_atoms"]:
            negative_edge[key] = negative_edge.get(key, 0.0) - 0.25
        for key in atoms["local_bridge_atoms"]:
            negative_bridge[key] = negative_bridge.get(key, 0.0) - 0.20
    return {
        "tg29g_baseline": {"edge": {}, "bridge": _repair_weight_delta("combined_reply_robust")},
        "trajectory_vs_local_contrastive_evidence": {"edge": _merge_weights(positive_edge, negative_edge), "bridge": _merge_weights(positive_bridge, negative_bridge)},
        "trajectory_positive_dominance_terminal": {"edge": positive_edge, "bridge": positive_bridge},
        "local_progress_only_veto": {"edge": negative_edge, "bridge": _merge_weights(_repair_weight_delta("combined_reply_robust"), negative_bridge)},
        "combined_trajectory_selection_repair": {"edge": _merge_weights(positive_edge, negative_edge), "bridge": _merge_weights(positive_bridge, negative_bridge)},
        "retrieval_only_wider_candidate_cap": {"edge": {}, "bridge": _repair_weight_delta("combined_reply_robust")},
    }


def _select_repair_arm(arms: dict[str, Any]) -> str:
    order = (
        "combined_trajectory_selection_repair",
        "trajectory_vs_local_contrastive_evidence",
        "trajectory_positive_dominance_terminal",
        "local_progress_only_veto",
    )
    for name in order:
        if arms.get(name, {}).get("better_trajectory_candidate_selected_count", 0) > 0:
            return name
    return "tg29g_baseline"


def _minimal_ablations(cfg, tg29g_cfg, context, tg29f_cfg, starts, deltas):
    if cfg.base.max_episode_ablation_count <= 0:
        return _skipped_ablations("max_episode_ablation_count_zero")
    masks = {
        "mask_trajectory_positive_terminals": {"mask_edge_fence_terminals": True},
        "mask_trajectory_vs_local_dominance_terminals": {"mask_edge_fence_terminals": True},
        "mask_local_progress_only_veto_terminals": {"mask_edge_fence_terminals": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_foundation_response_terminals": {"mask_foundation_response_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "disable_reply_envelope_checks": {"disable_reply_envelope_foundation_checks": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_frozen_mate2_foundation_quorum": True},
    }
    return {
        name: _progress_summary(_run_repair_policy(tg29g_cfg, context, tg29f_cfg, starts[: max(1, cfg.base.max_episode_ablation_count)], deltas["edge"], deltas["bridge"], masks=mask))
        for name, mask in masks.items()
    }


def _decision(cfg, *, context, trajectory_audit, cache_index, contrast_rows, repair_comparison, regression, foundation_before, foundation_after, cache_equivalence, scheduler_equivalence, timings):
    m3_delta = foundation_after["m3"] - foundation_before["m3"]
    m4_delta = foundation_after["m4"] - foundation_before["m4"]
    progress = repair_comparison["progress_summary"]
    regression_clean = all(regression[key] for key in ("frontier_regression_pass", "staged_regression_pass", "near_miss_regression_pass", "generic_edge_regression_pass", "foundation_sanity_pass"))
    selected_count = repair_comparison["better_trajectory_candidate_selected_after_repair_count"]
    repair_success = bool(
        repair_comparison["repair_applied"]
        and repair_comparison.get("runtime_episode_evaluated", False)
        and selected_count > 0
        and progress.get("rook_blunder_count", 0) == 0
        and progress.get("illegal_move_count", 0) == 0
        and progress.get("stalemate_count", 0) == 0
    )
    diagnostic_pass = bool(
        trajectory_audit["audited_failure_start_count"] > 0
        and trajectory_audit["audited_candidate_count"] > 0
        and cache_index["trajectory_cache_entry_count"] > 0
        and m3_delta == 0
        and m4_delta == 0
        and cache_equivalence["foundation_cache_live_mismatch_count"] == 0
        and scheduler_equivalence["mismatch_count"] == 0
        and regression_clean
    )
    avg_live = 0.0
    if trajectory_audit["live_rollout_count"] > 0:
        avg_live = round(timings.get("trajectory_rollout_seconds", 0.0) / trajectory_audit["live_rollout_count"], 6)
    avg_candidate = 0.0
    if trajectory_audit["audited_candidate_count"] > 0:
        avg_candidate = round(timings.get("trajectory_rollout_seconds", 0.0) / trajectory_audit["audited_candidate_count"], 6)
    interpretation = (
        "trajectory_selection_repair_selected_lost_candidate"
        if repair_success
        else (
            "cached_wider_audit_found_trajectory_candidate_but_repair_not_causal"
            if trajectory_audit["trajectory_positive_candidate_count"] > 0
            else "cached_wider_audit_no_trajectory_candidate_or_cap_limited"
        )
    )
    failure_counts = Counter(start["failure_bucket"] for start in trajectory_audit["starts"])
    return {
        "checkpoint_pass": bool(repair_success or diagnostic_pass),
        "checkpoint_interpretation": interpretation,
        "repair_applied": bool(repair_success),
        "selected_repair_arm": repair_comparison["selected_repair_arm"],
        "repair_selection_runtime": repair_comparison["repair_selection_runtime"],
        "runtime_episode_evaluated": repair_comparison["runtime_episode_evaluated"],
        "trajectory_cache_path": cfg.trajectory_cache_path,
        "trajectory_cache_index_path": cfg.trajectory_cache_index_path,
        "trajectory_cache_entry_count": cache_index["trajectory_cache_entry_count"],
        "trajectory_cache_hit_count": trajectory_audit["trajectory_cache_hit_count"],
        "trajectory_cache_miss_count": trajectory_audit["trajectory_cache_miss_count"],
        "live_rollout_count": trajectory_audit["live_rollout_count"],
        "cache_live_mismatch_count": trajectory_audit["cache_live_mismatch_count"],
        "average_seconds_per_cached_candidate": 0.0,
        "average_seconds_per_live_candidate": avg_live,
        "average_seconds_per_candidate": avg_candidate,
        "timeout_count": 0,
        "audited_failure_start_count": trajectory_audit["audited_failure_start_count"],
        "legal_candidate_count": trajectory_audit["legal_candidate_count"],
        "safe_candidate_count": trajectory_audit["safe_candidate_count"],
        "audited_candidate_count": trajectory_audit["audited_candidate_count"],
        "cached_candidate_count": trajectory_audit["cached_candidate_count"],
        "trajectory_positive_candidate_count": trajectory_audit["trajectory_positive_candidate_count"],
        "trajectory_partial_positive_candidate_count": trajectory_audit["trajectory_partial_positive_candidate_count"],
        "local_progress_only_candidate_count": trajectory_audit["local_progress_only_candidate_count"],
        "safe_low_progress_candidate_count": trajectory_audit["safe_low_progress_candidate_count"],
        "bridge_loop_inducing_candidate_count": trajectory_audit["bridge_loop_inducing_candidate_count"],
        "trajectory_positive_candidate_exists_count": trajectory_audit["trajectory_positive_candidate_exists_count"],
        "trajectory_positive_candidate_lost_selection_count": trajectory_audit["trajectory_positive_candidate_lost_selection_count"],
        "no_trajectory_positive_candidate_exists_count": trajectory_audit["no_trajectory_positive_candidate_exists_count"],
        "candidate_cap_blocked_count": trajectory_audit["candidate_cap_blocked_count"],
        "trajectory_contrast_row_count": len(contrast_rows),
        "trajectory_positive_terminal_count": repair_comparison["trajectory_positive_terminal_count"],
        "trajectory_dominance_terminal_count": repair_comparison["trajectory_dominance_terminal_count"],
        "local_progress_only_veto_terminal_count": repair_comparison["local_progress_only_veto_terminal_count"],
        "better_trajectory_candidate_selected_after_repair_count": selected_count,
        "bounded_episode_count": progress.get("episode_count", cfg.base.episode_count),
        "bounded_episode_success_count": progress.get("episode_success_count", 0),
        "bounded_episode_success_rate": progress.get("episode_success_count", 0) / max(1, progress.get("episode_count", cfg.base.episode_count)),
        "worst_foundation_reply_success_rate": progress.get("episode_success_count", 0) / max(1, progress.get("episode_count", cfg.base.episode_count)),
        "mobility_max_reply_success_rate": 0.0,
        "selected_moves_safe_but_low_progress_count": progress.get("selected_moves_safe_but_low_progress_count", 0),
        "bridge_loop_without_foundation_progress_count": progress.get("bridge_loop_without_foundation_progress_count", 0),
        "rook_blunder_count": progress.get("rook_blunder_count", 0),
        "illegal_move_count": progress.get("illegal_move_count", 0),
        "stalemate_count": progress.get("stalemate_count", 0),
        "unsafe_move_count": progress.get("unsafe_move_count", 0),
        "foundation_frozen": m3_delta == 0 and m4_delta == 0,
        "foundation_mate1_accuracy": context["foundation_sanity"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": context["foundation_sanity"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": cache_equivalence["foundation_cache_live_mismatch_count"],
        "foundation_m3_updates_during_training": 0,
        "foundation_m4_promotions_during_training": 0,
        "foundation_m3_updates_during_eval": m3_delta,
        "foundation_m4_promotions_during_eval": m4_delta,
        "frontier_regression_pass": regression["frontier_regression_pass"],
        "staged_regression_pass": regression["staged_regression_pass"],
        "near_miss_regression_pass": regression["near_miss_regression_pass"],
        "generic_edge_regression_pass": regression["generic_edge_regression_pass"],
        "foundation_sanity_pass": regression["foundation_sanity_pass"],
        "failure_bucket_counts": dict(failure_counts),
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": scheduler_equivalence["mismatch_count"],
        "ablation_results": repair_comparison["ablation_results"],
        "trajectory_repair_ablation_causal": False,
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
        "staged_labels_learner_visible": False,
        "trajectory_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _tg29g_cfg_from_h(cfg: CachedTrajectorySelectionRepairConfig) -> TrajectoryPositivePrefixAuditConfig:
    return TrajectoryPositivePrefixAuditConfig(
        base=cfg.base,
        tg29f_artifact_path=cfg.tg29f_artifact_path,
        black_reply_policies=cfg.black_reply_policies,
        max_failure_starts=cfg.max_failure_starts,
        max_safe_candidates_per_start=cfg.max_safe_candidates_per_start,
        max_repair_cache_candidate_moves=cfg.max_repair_cache_candidate_moves,
        max_reply_envelope_replies_per_candidate=cfg.max_reply_envelope_replies_per_candidate,
        run_optional_repair=False,
        audit_context_profile=cfg.audit_context_profile,
    )


def _cache_key(start_fen: str, row: dict[str, Any], policy: str) -> str:
    payload = {
        "start_fen": start_fen,
        "first_candidate_move": row["candidate_move"],
        "black_reply_policy": policy,
        "foundation_config_hash": row["foundation_config_hash"],
        "cache_config_hash": row["cache_config_hash"],
        "live_graph_equivalence_hash": row["live_graph_equivalence_hash"],
    }
    return _hash_dict(payload)


def _cache_entry_from_row(start: dict[str, Any], row: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    return _cache_entry_from_policy(start["start_fen"], row, policy)


def _cache_entry_from_policy(start_fen: str, row: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    entry = {
        "schema_version": "tg29h_trajectory_rollout_cache_entry.v0",
        "cache_key": _cache_key(start_fen, row, policy["black_reply_policy"]),
        "start_fen": start_fen,
        "first_candidate_move": row["candidate_move"],
        "after_first_candidate_fen": row["after_first_candidate_fen"],
        "black_reply_policy": policy["black_reply_policy"],
        "black_reply_after_first": policy["black_reply"],
        "s1_fen": policy["s1_fen"],
        "graph_selected_second_move": policy["graph_selected_second_move"],
        "after_second_move_fen": policy["after_second_move_fen"],
        "second_black_reply_policy": policy["black_reply_policy"],
        "second_black_reply": policy["second_black_reply"],
        "foundation_query_fen": policy["foundation_query_fen"],
        "foundation_response_detected": bool(policy["foundation_progress_metrics"]["foundation_handoff"]),
        "foundation_selected_move": policy["foundation_selected_move"],
        "same_graph_foundation_continuation_count": policy["same_graph_foundation_continuation_count"],
        "trajectory_classification": policy["trajectory_policy_classification"],
        "local_progress_metrics": row["local_progress_metrics"],
        "bridge_progress_metrics": policy["bridge_progress_metrics"],
        "foundation_progress_metrics": policy["foundation_progress_metrics"],
        "safety_metrics": row["safety_metrics"],
        "graph_evidence_summary_hash": _hash_dict({"positive": row["positive_feature_keys"], "bridge": row["bridge_feature_keys"], "score": row.get("current_graph_evidence_score")}),
        "foundation_config_hash": row["foundation_config_hash"],
        "cache_config_hash": row["cache_config_hash"],
        "live_graph_equivalence_hash": row["live_graph_equivalence_hash"],
        "source": "frozen_native_graph_response",
        "validator_labels_used_for_generation_only": True,
        "learner_visible_labels": False,
    }
    entry["cache_entry_id"] = "tg29h_" + entry["cache_key"]
    return entry


def _policy_row_from_cache_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "black_reply_policy": entry["black_reply_policy"],
        "black_reply": entry["black_reply_after_first"],
        "s1_fen": entry["s1_fen"],
        "graph_selected_second_move": entry["graph_selected_second_move"],
        "after_second_move_fen": entry["after_second_move_fen"],
        "second_black_reply": entry["second_black_reply"],
        "foundation_query_fen": entry["foundation_query_fen"],
        "foundation_selected_move": entry["foundation_selected_move"],
        "same_graph_foundation_continuation_count": entry["same_graph_foundation_continuation_count"],
        "next_phase": None,
        "foundation_after_first_reply_reachable": bool(entry["foundation_progress_metrics"]["foundation_reachable_after_first_reply"]),
        "foundation_after_second_reply_reachable": bool(entry["foundation_progress_metrics"]["foundation_reachable_after_second_reply"]),
        "trajectory_policy_classification": entry["trajectory_classification"],
        "bridge_progress_metrics": entry["bridge_progress_metrics"],
        "foundation_progress_metrics": entry["foundation_progress_metrics"],
        "deep_reply_checks_run": 0,
    }


def _compact_evidence(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "move": row["candidate_move"],
        "trajectory_classification": row["trajectory_classification"],
        "trajectory_score": row["trajectory_score"],
        "local_progress_score": row["local_progress_score"],
        "local_progress_metrics": row["local_progress_metrics"],
        "bridge_feature_keys": row["bridge_feature_keys"],
        "positive_feature_keys": row["positive_feature_keys"],
        "safety_metrics": row["safety_metrics"],
    }


def _failure_bucket(current, best_local, best_positive, best_trajectory, cap_blocked: bool) -> str:
    if best_positive is None:
        return "audit_cap_prevents_conclusion" if cap_blocked else "no_trajectory_positive_candidate_exists"
    if current == best_positive["candidate_move"]:
        return "none"
    if best_local is not None and best_trajectory is not None and best_local["candidate_move"] != best_trajectory["candidate_move"]:
        return "trajectory_positive_exists_but_loses_to_local_progress"
    return "trajectory_positive_exists_but_evidence_not_materialized"


def _best(rows: list[dict[str, Any]], *, key):
    return max(rows, key=key) if rows else None


def _skipped_ablations(reason: str) -> dict[str, Any]:
    names = (
        "mask_trajectory_positive_terminals",
        "mask_trajectory_vs_local_dominance_terminals",
        "mask_local_progress_only_veto_terminals",
        "mask_bridge_pressure_terminals",
        "mask_foundation_response_terminals",
        "mask_actuator_terminals",
        "disable_reply_envelope_checks",
        "mask_frozen_mate2_foundation_quorum",
    )
    return {name: {"skipped": True, "skip_reason": reason} for name in names}


def _purity_boundary() -> dict[str, Any]:
    return {
        "checkpoint": "TG29h",
        "trajectory_labels_trainer_side_only": True,
        "trajectory_labels_learner_visible": False,
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


def _write_progress(cfg: CachedTrajectorySelectionRepairConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
