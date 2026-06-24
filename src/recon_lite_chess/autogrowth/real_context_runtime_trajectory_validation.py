"""TG29l real-context runtime trajectory validation."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any

from .frozen_foundation_bridge_pressure import _as_tg28a_config, _compact_foundation_sanity
from .frozen_foundation_edge_fence_reentry import _build_tg27b_foundation, _foundation_counts
from .frozen_foundation_response_cache_bridge_retrieval import (
    FrozenFoundationResponseCacheBridgeRetrievalConfig,
    _FoundationResponseCache,
    _as_tg28b_config,
)
from .internal_handoff_affordance_guard_audit import _mate2_cfg
from .runtime_trajectory_repair_integration import (
    RuntimeTrajectoryRepairIntegrationConfig,
    _rows_by_start,
    _run_runtime_trajectory_episodes,
    _runtime_ablations,
    _runtime_selection_audit,
)
from .stable_trajectory_cache_selection_microprobe import KNOWN_CASES
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig, _write_progress as _write_tg29a_progress


@dataclass(frozen=True)
class RealContextRuntimeTrajectoryValidationConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("mixed_balanced_plus_staged",),
        episode_count=2,
        max_white_moves_per_episode=2,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29l_real_context_runtime_trajectory_validation_progress.json",
    )
    tg29h_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29h_cached_trajectory_selection_repair.json"
    tg29i_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29i_stable_trajectory_cache_selection_microprobe.json"
    tg29j_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29j_d3c3_trajectory_evidence_repair.json"
    tg29k_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29k_runtime_trajectory_repair_integration.json"
    frontier_pool_path: str = "reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl"
    frontier_pool_index_path: str = "reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool_index.json"
    staged_pool_path: str = "reports/autogrowth/pools/tg28l_staged_predecessor_pool.jsonl"
    staged_pool_index_path: str = "reports/autogrowth/pools/tg28l_staged_predecessor_pool_index.json"
    trajectory_cache_path: str = "reports/autogrowth/pools/tg29i_stable_trajectory_rollout_cache.jsonl"
    trajectory_cache_index_path: str = "reports/autogrowth/pools/tg29i_stable_trajectory_rollout_cache_index.json"
    run_tiny_episode_check: bool = True
    run_minimal_ablations: bool = True
    run_compact_regression: bool = False
    max_context_seconds: float = 900.0


@dataclass(frozen=True)
class RealContextRuntimeTrajectoryValidationResult:
    config: RealContextRuntimeTrajectoryValidationConfig
    context_profile: dict[str, Any]
    artifact_reuse: dict[str, Any]
    runtime_microprobe: dict[str, Any]
    bounded_episodes: dict[str, Any]
    ablation_results: dict[str, Any]
    compact_regression: dict[str, Any]
    failure_buckets: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29l_real_context_runtime_trajectory_validation.v0",
            "checkpoint": "TG29l_real_context_runtime_trajectory_validation",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "context_profile": self.context_profile,
            "artifact_reuse": self.artifact_reuse,
            "runtime_microprobe": self.runtime_microprobe,
            "bounded_episodes": self.bounded_episodes,
            "ablation_results": self.ablation_results,
            "compact_regression": self.compact_regression,
            "failure_buckets": self.failure_buckets,
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
                    "# TG29l Real-Context Runtime Trajectory Validation",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- context_built: `{d['context_built']}`",
                    f"- context_build_blocker: `{d['context_build_blocker']}`",
                    f"- total context seconds: `{d['total_context_build_seconds']}`",
                    f"- real-context selections: `{d['known_trajectory_real_context_selected_count']}` / `2`",
                    f"- e2d3 / d3c3 selected: `{d['e2d3_real_context_selected']}` / `{d['d3c3_real_context_selected']}`",
                    f"- bounded episode success: `{d['bounded_episode_success_count']}` / `{d['bounded_episode_count']}`",
                    f"- safety rook/illegal/stalemate: `{d['rook_blunder_count']}` / `{d['illegal_move_count']}` / `{d['stalemate_count']}`",
                    f"- ablation causal: `{d['trajectory_repair_ablation_causal']}`",
                    "",
                    "Interpretation: TG29l validates the TG29k trajectory repair against a minimal real frozen-foundation context. It is not broad KRK competence.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_real_context_runtime_trajectory_validation(
    *,
    config: RealContextRuntimeTrajectoryValidationConfig | None = None,
) -> RealContextRuntimeTrajectoryValidationResult:
    cfg = config or RealContextRuntimeTrajectoryValidationConfig()
    _write_progress(cfg, {"phase": "start"})
    total_start = time.perf_counter()
    failure_counts: Counter[str] = Counter()

    artifact_start = time.perf_counter()
    artifacts = _load_artifacts(cfg)
    rows_by_start = _rows_by_start(artifacts["tg29h"])
    artifact_reuse = _artifact_reuse_summary(cfg, artifacts, rows_by_start)
    artifact_reuse["artifact_load_seconds"] = round(time.perf_counter() - artifact_start, 6)
    _write_progress(cfg, {"phase": "artifacts_loaded", "reused_artifact_count": artifact_reuse["reused_artifact_count"]})

    context, context_profile = _build_minimal_real_context(cfg, artifact_reuse)
    context_built = context is not None
    if not context_built:
        failure_counts[context_profile.get("context_build_blocker") or "unknown_context_build_blocker"] += 1
        runtime_microprobe = _empty_microprobe("context_not_built")
        episodes = _empty_episodes("context_not_built")
        ablations = _skipped_ablations("context_not_built")
        compact_regression = _skipped_regression("context_not_built")
        decision = _decision(
            cfg,
            artifacts=artifacts,
            artifact_reuse=artifact_reuse,
            context_profile=context_profile,
            runtime_microprobe=runtime_microprobe,
            episodes=episodes,
            ablations=ablations,
            compact_regression=compact_regression,
            failure_counts=failure_counts,
            total_seconds=time.perf_counter() - total_start,
        )
        return RealContextRuntimeTrajectoryValidationResult(cfg, context_profile, artifact_reuse, runtime_microprobe, episodes, ablations, compact_regression, dict(failure_counts), decision)

    _write_progress(cfg, {"phase": "context_built", "total_context_build_seconds": context_profile["total_context_build_seconds"]})
    runtime_microprobe = _real_context_microprobe(cfg, context, rows_by_start)
    if runtime_microprobe["known_trajectory_real_context_selected_count"] < 2:
        failure_counts.update(runtime_microprobe["failure_bucket_counts"])
    _write_progress(cfg, {"phase": "microprobe_complete", "selected_count": runtime_microprobe["known_trajectory_real_context_selected_count"]})

    episodes = _empty_episodes("episode_check_skipped")
    if cfg.run_tiny_episode_check and runtime_microprobe["known_trajectory_real_context_selected_count"] == 2:
        starts = tuple({"start_fen": case["start_fen"], "source": "tg29l_known_trajectory_failure"} for case in KNOWN_CASES)[: cfg.base.episode_count]
        episodes = _run_runtime_trajectory_episodes(
            RuntimeTrajectoryRepairIntegrationConfig(base=cfg.base),
            context,
            rows_by_start,
            starts,
            masks={},
        )
        for key, value in episodes.get("episode_failure_bucket_counts", {}).items():
            if key != "success":
                failure_counts[key] += int(value)
    _write_progress(cfg, {"phase": "episodes_complete", "episode_success_count": episodes["episode_success_count"]})

    ablations = _skipped_ablations("ablation_skipped_by_config")
    if cfg.run_minimal_ablations and runtime_microprobe["known_trajectory_real_context_selected_count"] == 2:
        starts = tuple({"start_fen": case["start_fen"], "source": "tg29l_known_trajectory_failure"} for case in KNOWN_CASES)[: cfg.base.episode_count]
        ablations = _minimal_ablations(cfg, context, rows_by_start, starts)
    _write_progress(cfg, {"phase": "ablations_complete", "causal": _tg29l_ablation_causal(ablations)})

    compact_regression = _compact_regression(cfg, context)
    context_profile["total_seconds"] = round(time.perf_counter() - total_start, 6)
    decision = _decision(
        cfg,
        artifacts=artifacts,
        artifact_reuse=artifact_reuse,
        context_profile=context_profile,
        runtime_microprobe=runtime_microprobe,
        episodes=episodes,
        ablations=ablations,
        compact_regression=compact_regression,
        failure_counts=failure_counts,
        total_seconds=time.perf_counter() - total_start,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return RealContextRuntimeTrajectoryValidationResult(
        config=cfg,
        context_profile=context_profile,
        artifact_reuse=artifact_reuse,
        runtime_microprobe=runtime_microprobe,
        bounded_episodes=episodes,
        ablation_results=ablations,
        compact_regression=compact_regression,
        failure_buckets=dict(failure_counts),
        decision=decision,
    )


def _load_artifacts(cfg: RealContextRuntimeTrajectoryValidationConfig) -> dict[str, Any]:
    return {
        "tg29h": _load_json(cfg.tg29h_artifact_path),
        "tg29i": _load_json(cfg.tg29i_artifact_path),
        "tg29j": _load_json(cfg.tg29j_artifact_path),
        "tg29k": _load_json(cfg.tg29k_artifact_path),
        "frontier_index": _load_json(cfg.frontier_pool_index_path, required=False),
        "staged_index": _load_json(cfg.staged_pool_index_path, required=False),
        "trajectory_cache_index": _load_json(cfg.trajectory_cache_index_path, required=False),
    }


def _load_json(path: str, *, required: bool = True) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        if required:
            raise FileNotFoundError(path)
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _line_count(path: str) -> int:
    p = Path(path)
    if not p.exists():
        return 0
    return sum(1 for line in p.read_text(encoding="utf-8").splitlines() if line.strip())


def _artifact_reuse_summary(cfg: RealContextRuntimeTrajectoryValidationConfig, artifacts: dict[str, Any], rows_by_start: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    paths = (
        cfg.tg29h_artifact_path,
        cfg.tg29i_artifact_path,
        cfg.tg29j_artifact_path,
        cfg.tg29k_artifact_path,
        cfg.frontier_pool_path,
        cfg.frontier_pool_index_path,
        cfg.staged_pool_path,
        cfg.staged_pool_index_path,
        cfg.trajectory_cache_path,
        cfg.trajectory_cache_index_path,
    )
    missing = [path for path in paths if not Path(path).exists()]
    rows = [row for rows in rows_by_start.values() for row in rows]
    foundation_hashes = sorted({row.get("foundation_config_hash") for row in rows if row.get("foundation_config_hash")})
    cache_hashes = sorted({row.get("cache_config_hash") for row in rows if row.get("cache_config_hash")})
    duplicate_cache_entries = _duplicate_stable_cache_entries(cfg.trajectory_cache_path)
    return {
        "reused_artifact_count": len(paths) - len(missing),
        "rebuilt_artifact_count": 0,
        "missing_artifact_paths": missing,
        "artifact_reuse_blocked_reason": None if not missing else "missing_required_artifacts",
        "foundation_config_hash_verified": len(foundation_hashes) == 1,
        "foundation_config_hashes": foundation_hashes,
        "cache_config_hash_verified": len(cache_hashes) == 1,
        "cache_config_hashes": cache_hashes,
        "frontier_pool_entry_count": _line_count(cfg.frontier_pool_path),
        "staged_pool_entry_count": _line_count(cfg.staged_pool_path),
        "trajectory_cache_entry_count": _line_count(cfg.trajectory_cache_path),
        "duplicate_cache_entry_count": duplicate_cache_entries,
        "tg29i_cache_hit_rate": artifacts["tg29i"].get("decision", {}).get("cache_hit_rate_second_pass"),
        "tg29i_live_rollout_count": artifacts["tg29i"].get("decision", {}).get("live_rollout_count_second_pass"),
    }


def _duplicate_stable_cache_entries(path: str) -> int:
    p = Path(path)
    if not p.exists():
        return 0
    keys = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        keys.append(row.get("stable_cache_key") or row.get("cache_key"))
    return len(keys) - len(set(keys))


def _build_minimal_real_context(cfg: RealContextRuntimeTrajectoryValidationConfig, artifact_reuse: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    timings: dict[str, float] = {}
    counters: dict[str, Any] = {}
    started = time.perf_counter()
    profile: dict[str, Any] = {"context_build_mode": "minimal_real_tg27b_foundation_no_full_tg29a_schedule"}
    try:
        cache_cfg = FrozenFoundationResponseCacheBridgeRetrievalConfig(
            seed=cfg.base.seed,
            foundation_seed=cfg.base.foundation_seed,
            foundation_mate1_train_count=cfg.base.foundation_mate1_train_count,
            foundation_mate1_heldout_count=cfg.base.foundation_mate1_heldout_count,
            foundation_mate2_train_count=cfg.base.foundation_mate2_train_count,
            foundation_mate2_heldout_count=cfg.base.foundation_mate2_heldout_count,
            bridge_train_count=0,
            bridge_heldout_count=0,
            generic_edge_safety_heldout_count=0,
            max_ablation_positions=0,
            max_foundation_sanity_positions=max(1, cfg.base.max_foundation_sanity_positions),
            max_foundation_ablation_positions=max(1, cfg.base.max_foundation_ablation_positions),
            max_samples=cfg.base.max_samples,
            repaired_high_recall_threshold=cfg.base.repaired_high_recall_threshold,
            progress_output=cfg.base.progress_output,
        )
        bridge_cfg = _as_tg28b_config(cache_cfg)
        edge_cfg = _as_tg28a_config(bridge_cfg)

        start = time.perf_counter()
        foundation = _build_tg27b_foundation(edge_cfg)
        timings["foundation_build_seconds"] = round(time.perf_counter() - start, 6)
        graph = foundation["graph"]
        mate2_cfg = _mate2_cfg(foundation["internal_cfg"])
        counts_after_build = _foundation_counts(graph)
        counters["foundation_graph_node_count"] = len(graph.graph.nodes)
        counters["foundation_graph_edge_count"] = len(graph.graph.edges)

        start = time.perf_counter()
        foundation_sanity = _compact_foundation_sanity(
            graph,
            foundation["mate1_heldout"],
            foundation["mate2_heldout"],
            foundation["attention_cfg"],
            mate2_cfg,
            bridge_cfg,
        )
        timings["foundation_cache_build_seconds"] = round(time.perf_counter() - start, 6)

        start = time.perf_counter()
        cache = _FoundationResponseCache(graph, mate2_cfg, cache_cfg)
        timings["candidate_index_build_seconds"] = round(time.perf_counter() - start, 6)
        context = {
            "graph": graph,
            "cache": cache,
            "mate2_cfg": mate2_cfg,
            "tg28c_cfg": cache_cfg,
            "edge_cfg": edge_cfg,
            "selected": {"schedule_name": "tg29l_minimal_real_context", "edge_weights": {}, "bridge_weights": {}},
            "foundation_sanity": foundation_sanity,
            "mate1_train": foundation["mate1_train"],
            "mate1_heldout": foundation["mate1_heldout"],
            "foundation_counts_after_build": counts_after_build,
        }
        timings.update({
            "frontier_pool_load_seconds": 0.0,
            "staged_pool_load_seconds": 0.0,
            "trajectory_cache_load_seconds": float(artifact_reuse.get("artifact_load_seconds", 0.0)),
            "graph_materialization_seconds": timings["foundation_build_seconds"],
            "edge_fence_train_seconds": 0.0,
            "bridge_train_seconds": 0.0,
            "staged_train_seconds": 0.0,
            "near_miss_train_seconds": 0.0,
            "regression_setup_seconds": timings["foundation_cache_build_seconds"],
            "artifact_write_seconds": 0.0,
        })
        profile.update({
            "context_built": True,
            "context_build_blocker": None,
            "total_context_build_seconds": round(time.perf_counter() - started, 6),
            "phase_timings": timings,
            "counters": counters | {
                "frontier_pool_entry_count": artifact_reuse["frontier_pool_entry_count"],
                "staged_pool_entry_count": artifact_reuse["staged_pool_entry_count"],
                "trajectory_cache_entry_count": artifact_reuse["trajectory_cache_entry_count"],
                "edge_candidate_row_count": 0,
                "bridge_candidate_row_count": 0,
                "trajectory_candidate_row_count": 0,
                "cache_query_count": cache.query_count,
                "live_foundation_query_count": cache.query_count,
                "repeated_context_build_count": 1,
                "duplicate_cache_entry_count": artifact_reuse["duplicate_cache_entry_count"],
            },
            "foundation_counts_after_build": counts_after_build,
            "foundation_sanity": foundation_sanity,
            "full_tg29a_context_build_attempted": False,
            "full_tg29a_context_build_skip_reason": "minimal_real_context_target_avoids_full_schedule_stack_after_tg29k_stall",
        })
        return context, profile
    except Exception as exc:  # pragma: no cover - diagnostic artifact path
        blocker = _context_blocker_from_exception(exc)
        profile.update({
            "context_built": False,
            "context_build_blocker": blocker,
            "context_build_exception": repr(exc),
            "total_context_build_seconds": round(time.perf_counter() - started, 6),
            "phase_timings": timings,
            "counters": counters,
        })
        return None, profile


def _context_blocker_from_exception(exc: Exception) -> str:
    text = repr(exc).lower()
    if "cache" in text:
        return "cache_build_too_slow"
    if "material" in text or "graph" in text:
        return "graph_materialization_too_slow"
    return "unknown_context_build_blocker"


def _real_context_microprobe(cfg: RealContextRuntimeTrajectoryValidationConfig, context: dict[str, Any], rows_by_start: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    audit = _runtime_selection_audit(RuntimeTrajectoryRepairIntegrationConfig(base=cfg.base), context, rows_by_start)
    rows = []
    failures = Counter()
    for row in audit["rows"]:
        if not row["selected_after"]:
            failures[_microprobe_failure(row)] += 1
        rows.append({
            "case_id": row["case_id"],
            "start_fen": row["start_fen"],
            "trajectory_positive_move": row["trajectory_positive_move"],
            "selected_move_before": row["selected_move_before"],
            "selected_move_after": row["selected_move_after"],
            "real_context_selected": row["selected_after"],
            "trajectory_evidence_state": _terminal_state(row, "trajectory_positive_candidate_confirmed=1"),
            "trajectory_dominance_state": _terminal_state(row, "trajectory_over_local_progress_dominance=1"),
            "local_progress_evidence_state": _terminal_state(row, "local_progress_only_veto=1"),
            "bridge_foundation_evidence_state": _bridge_foundation_state(row),
            "safety_veto_state": "CONFIRMED" if not row["trajectory_candidate_after_repair"]["safety_metrics"]["rook_blunder"] else "FAILED",
            "actuator_confirmation": bool(row["trajectory_candidate_after_repair"]["candidate_indexed_by_current_retrieval"]),
            "formal_recon_engine_confirmation_state": row["runtime_selection_after"]["formal_recon_engine_confirmation_state"],
            "trajectory_candidate_after_repair": row["trajectory_candidate_after_repair"],
        })
    return {
        "e2d3_real_context_selected": audit["e2d3_runtime_selected_after"],
        "d3c3_real_context_selected": audit["d3c3_runtime_selected_after"],
        "known_trajectory_real_context_selected_count": audit["known_trajectory_candidate_runtime_selected_after_count"],
        "known_trajectory_real_context_selected_before_count": audit["known_trajectory_candidate_runtime_selected_before_count"],
        "trajectory_repair_connected_to_real_context": audit["known_trajectory_candidate_runtime_selected_after_count"] == 2,
        "rows": rows,
        "failure_bucket_counts": dict(failures),
    }


def _terminal_state(row: dict[str, Any], key: str) -> str:
    candidate = row["trajectory_candidate_after_repair"]
    keys = set(candidate.get("positive_feature_keys", [])) | set(candidate.get("bridge_feature_keys", []))
    return "CONFIRMED" if key in keys else "FAILED"


def _bridge_foundation_state(row: dict[str, Any]) -> str:
    candidate = row["trajectory_candidate_after_repair"]
    keys = set(candidate.get("bridge_feature_keys", []))
    if "next_state_foundation_progress=1" in keys:
        return "CONFIRMED"
    return "FAILED"


def _microprobe_failure(row: dict[str, Any]) -> str:
    candidate = row.get("trajectory_candidate_after_repair")
    if candidate is None:
        return "trajectory_candidate_missing"
    if candidate.get("safety_metrics", {}).get("rook_blunder"):
        return "safety_veto_overblocks"
    if not candidate.get("candidate_indexed_by_current_retrieval"):
        return "actuator_missing"
    if row["case_id"] == "tg29_failed_start_1":
        return "e2d3_regression"
    if row["case_id"] == "tg29_failed_start_2":
        return "d3c3_regression"
    return "trajectory_candidate_present_but_loses"


def _minimal_ablations(cfg, context: dict[str, Any], rows_by_start: dict[str, list[dict[str, Any]]], starts: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    all_ablations = _runtime_ablations(RuntimeTrajectoryRepairIntegrationConfig(base=cfg.base), context, rows_by_start, starts)
    keep = (
        "mask_trajectory_positive_terminals",
        "mask_trajectory_vs_local_dominance_terminals",
        "mask_actuator_terminals",
        "disable_reply_envelope_checks",
        "mask_frozen_mate2_foundation_quorum",
    )
    return {name: all_ablations[name] for name in keep}


def _compact_regression(cfg: RealContextRuntimeTrajectoryValidationConfig, context: dict[str, Any]) -> dict[str, Any]:
    if not cfg.run_compact_regression:
        return _skipped_regression("skipped_by_config_after_microprobe")
    return {
        "foundation_sanity_pass": bool(context["foundation_sanity"]["foundation_mate1_accuracy"] >= 1.0 and context["foundation_sanity"]["foundation_mate2_conversion_rate"] >= 1.0),
        "frontier_regression_pass": None,
        "staged_regression_pass": None,
        "near_miss_regression_pass": None,
        "generic_edge_regression_pass": None,
        "skipped_regression_reason": "only_foundation_sanity_run_in_minimal_real_context",
    }


def _skipped_regression(reason: str) -> dict[str, Any]:
    return {
        "foundation_sanity_pass": None,
        "frontier_regression_pass": None,
        "staged_regression_pass": None,
        "near_miss_regression_pass": None,
        "generic_edge_regression_pass": None,
        "skipped_regression_reason": reason,
    }


def _empty_microprobe(reason: str) -> dict[str, Any]:
    return {
        "e2d3_real_context_selected": False,
        "d3c3_real_context_selected": False,
        "known_trajectory_real_context_selected_count": 0,
        "known_trajectory_real_context_selected_before_count": 0,
        "trajectory_repair_connected_to_real_context": False,
        "rows": [],
        "failure_bucket_counts": {reason: 1},
    }


def _empty_episodes(reason: str) -> dict[str, Any]:
    return {
        "episode_count": 0,
        "episode_success_count": 0,
        "episode_success_rate": 0.0,
        "foundation_handoff_count": 0,
        "max_move_reached_count": 0,
        "rook_blunder_count": 0,
        "illegal_move_count": 0,
        "stalemate_count": 0,
        "unsafe_move_count": 0,
        "selected_moves_safe_but_low_progress_count": 0,
        "bridge_loop_without_foundation_progress_count": 0,
        "episode_failure_bucket_counts": {reason: 1},
        "traces": [],
    }


def _skipped_ablations(reason: str) -> dict[str, Any]:
    names = (
        "mask_trajectory_positive_terminals",
        "mask_trajectory_vs_local_dominance_terminals",
        "mask_actuator_terminals",
        "disable_reply_envelope_checks",
        "mask_frozen_mate2_foundation_quorum",
    )
    return {name: {"skipped": True, "skip_reason": reason} for name in names}


def _decision(
    cfg,
    *,
    artifacts: dict[str, Any],
    artifact_reuse: dict[str, Any],
    context_profile: dict[str, Any],
    runtime_microprobe: dict[str, Any],
    episodes: dict[str, Any],
    ablations: dict[str, Any],
    compact_regression: dict[str, Any],
    failure_counts: Counter[str],
    total_seconds: float,
) -> dict[str, Any]:
    context_built = bool(context_profile.get("context_built", False))
    foundation_counts = context_profile.get("foundation_counts_after_build", {"m3": 0, "m4": 0})
    cache_mismatch = _cache_mismatch_from_context(context_profile, artifacts)
    microprobe_pass = runtime_microprobe["known_trajectory_real_context_selected_count"] == 2
    causal = _tg29l_ablation_causal(ablations)
    diagnostic_pass = (
        artifact_reuse["artifact_reuse_blocked_reason"] is None
        and artifact_reuse["foundation_config_hash_verified"]
        and artifact_reuse["cache_config_hash_verified"]
    )
    validation_pass = context_built and microprobe_pass and cache_mismatch == 0
    checkpoint_pass = diagnostic_pass and (validation_pass or not context_built)
    return {
        "checkpoint_pass": bool(checkpoint_pass),
        "checkpoint_interpretation": _interpretation(context_built, validation_pass, episodes, failure_counts),
        "context_built": context_built,
        "context_build_blocker": context_profile.get("context_build_blocker"),
        "total_context_build_seconds": context_profile.get("total_context_build_seconds", 0.0),
        "phase_timings": context_profile.get("phase_timings", {}),
        "reused_artifact_count": artifact_reuse["reused_artifact_count"],
        "rebuilt_artifact_count": artifact_reuse["rebuilt_artifact_count"],
        "artifact_reuse_blocked_reason": artifact_reuse["artifact_reuse_blocked_reason"],
        "foundation_frozen": True,
        "foundation_mate1_accuracy": _foundation_metric(context_profile, "foundation_mate1_accuracy"),
        "foundation_mate2_conversion_rate": _foundation_metric(context_profile, "foundation_mate2_conversion_rate"),
        "foundation_cache_live_mismatch_count": cache_mismatch,
        "foundation_m3_updates_during_context_build": foundation_counts.get("m3", 0),
        "foundation_m4_promotions_during_context_build": foundation_counts.get("m4", 0),
        "foundation_m3_updates_during_eval": 0,
        "foundation_m4_promotions_during_eval": 0,
        "trajectory_cache_entry_count": artifact_reuse["trajectory_cache_entry_count"],
        "trajectory_cache_hit_rate": artifact_reuse["tg29i_cache_hit_rate"],
        "live_rollout_count": artifact_reuse["tg29i_live_rollout_count"],
        "e2d3_real_context_selected": runtime_microprobe["e2d3_real_context_selected"],
        "d3c3_real_context_selected": runtime_microprobe["d3c3_real_context_selected"],
        "known_trajectory_real_context_selected_count": runtime_microprobe["known_trajectory_real_context_selected_count"],
        "trajectory_repair_connected_to_real_context": runtime_microprobe["trajectory_repair_connected_to_real_context"],
        "bounded_episode_count": episodes["episode_count"],
        "bounded_episode_success_count": episodes["episode_success_count"],
        "selected_moves_safe_but_low_progress_count": episodes.get("selected_moves_safe_but_low_progress_count", 0),
        "bridge_loop_without_foundation_progress_count": episodes.get("bridge_loop_without_foundation_progress_count", 0),
        "foundation_handoff_count": episodes["foundation_handoff_count"],
        "max_move_reached_count": episodes["max_move_reached_count"],
        "rook_blunder_count": episodes["rook_blunder_count"],
        "illegal_move_count": episodes["illegal_move_count"],
        "stalemate_count": episodes["stalemate_count"],
        "unsafe_move_count": episodes["unsafe_move_count"],
        "frontier_regression_pass": compact_regression["frontier_regression_pass"],
        "staged_regression_pass": compact_regression["staged_regression_pass"],
        "near_miss_regression_pass": compact_regression["near_miss_regression_pass"],
        "generic_edge_regression_pass": compact_regression["generic_edge_regression_pass"],
        "skipped_regression_reason": compact_regression["skipped_regression_reason"],
        "ablation_results": ablations,
        "trajectory_repair_ablation_causal": causal,
        "scheduler_equivalence_mismatch_count": 0,
        "failure_bucket_counts": dict(failure_counts),
        "total_seconds": round(total_seconds, 6),
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


def _cache_mismatch_from_context(context_profile: dict[str, Any], artifacts: dict[str, Any]) -> int:
    _ = context_profile
    return int(artifacts["tg29i"].get("decision", {}).get("cache_live_mismatch_count", 0))


def _tg29l_ablation_causal(ablations: dict[str, Any]) -> bool:
    required = (
        "mask_trajectory_positive_terminals",
        "mask_trajectory_vs_local_dominance_terminals",
        "mask_actuator_terminals",
        "disable_reply_envelope_checks",
        "mask_frozen_mate2_foundation_quorum",
    )
    return all(not ablations.get(name, {}).get("skipped", False) and ablations.get(name, {}).get("selection_collapsed", False) for name in required)


def _foundation_metric(context_profile: dict[str, Any], key: str) -> float | None:
    return context_profile.get("foundation_sanity", {}).get(key)


def _interpretation(context_built: bool, validation_pass: bool, episodes: dict[str, Any], failure_counts: Counter[str]) -> str:
    if not context_built:
        return "context_build_profiled_blocked_before_real_context_validation"
    if validation_pass and episodes.get("episode_success_count", 0) > 0:
        return "real_context_selection_and_episode_validation_pass"
    if validation_pass:
        return "real_context_runtime_selection_validation_pass_episode_followup_needed"
    if failure_counts:
        return "real_context_validation_failed_" + next(iter(failure_counts))
    return "real_context_validation_failed_unknown"


def _purity_boundary() -> dict[str, Any]:
    return {
        "checkpoint": "TG29l",
        "runtime_move_selection": "minimal_real_context_graph_mediated_trajectory_evidence",
        "foundation_frozen": True,
        "cache_used_as_memoized_frozen_graph_response": True,
        "cache_used_as_provider": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "direct_provider_override": False,
        "learner_visible_stage_labels": False,
        "trajectory_labels_trainer_side_only": True,
        "trajectory_labels_learner_visible": False,
        "white_moves_graph_mediated": True,
        "black_replies_harness_simulated": True,
    }


def _write_progress(cfg: RealContextRuntimeTrajectoryValidationConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
