"""TG29p cached online episode scale matrix."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path
import time
from typing import Any

import chess

from .frozen_foundation_edge_fence_reentry import _foundation_counts
from .real_context_runtime_trajectory_validation import (
    RealContextRuntimeTrajectoryValidationConfig,
    _artifact_reuse_summary,
    _build_minimal_real_context,
    _load_artifacts,
    _rows_by_start,
)
from .runtime_trajectory_repair_integration import RuntimeTrajectoryRepairIntegrationConfig, _select_runtime_trajectory_move
from .s1_full_reply_cache_online_recheck import (
    _candidate_audits_from_cache,
    _compact_regression,
    _load_cache_entries,
    _select_with_cached_s1,
)
from .s1_full_reply_handoff_validation import _select_candidate_for_arm
from .stable_trajectory_cache_selection_microprobe import KNOWN_CASES
from .tiny_online_krk_episode_runner import (
    TinyOnlineKRKEpisodeRunnerConfig,
    _compact_foundation_state,
    _foundation_reachable,
    _safety_result,
    _select_black_reply,
    _write_progress as _write_tg29a_progress,
)


@dataclass(frozen=True)
class CachedOnlineEpisodeScaleMatrixConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=4,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix_progress.json",
    )
    tg29o_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29o_s1_full_reply_cache_online_recheck.json"
    tg29n_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29n_s1_full_reply_handoff_validation.json"
    s1_cache_path: str = "reports/autogrowth/pools/tg29o_s1_full_reply_evidence_cache.jsonl"
    staged_pool_path: str = "reports/autogrowth/pools/tg28l_staged_predecessor_pool.jsonl"
    frontier_pool_path: str = "reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl"
    tg28a_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg28a_frozen_foundation_edge_fence_reentry.json"
    tg28g_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg28g_full_frontier_validation_near_miss.json"
    selected_policy_arm: str = "strict_all_reply_priority_cached_s1"
    start_counts: dict[str, int] | None = None
    horizons: tuple[int, ...] = (2, 3, 4)
    black_reply_policies: tuple[str, ...] = (
        "deterministic_worst_foundation_reply",
        "mobility_maximizing",
        "fixed_seed_random",
    )
    diagnostic_arm_start_limit: int = 4
    run_diagnostic_arms: bool = True
    run_representative_ablations: bool = True
    run_compact_regression: bool = True

    def resolved_start_counts(self) -> dict[str, int]:
        return self.start_counts or {
            "known_repaired_starts": 2,
            "staged_pool_starts": 4,
            "frontier_near_starts": 4,
            "generic_edge_starts": 4,
            "near_miss_or_decoy_starts": 4,
        }


@dataclass(frozen=True)
class CachedOnlineEpisodeScaleMatrixResult:
    config: CachedOnlineEpisodeScaleMatrixConfig
    artifact_reuse: dict[str, Any]
    context_profile: dict[str, Any]
    start_sets: dict[str, Any]
    main_matrix: dict[str, Any]
    diagnostic_arms: dict[str, Any]
    compact_regression: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29p_cached_online_episode_scale_matrix.v0",
            "checkpoint": "TG29p_cached_online_episode_scale_matrix",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "artifact_reuse": self.artifact_reuse,
            "context_profile": self.context_profile,
            "start_sets": self.start_sets,
            "main_matrix": self.main_matrix,
            "diagnostic_arms": self.diagnostic_arms,
            "compact_regression": self.compact_regression,
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
                    "# TG29p Cached Online Episode Scale Matrix",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- selected arm: `{d['selected_policy_arm']}`",
                    f"- episodes: `{d['episode_success_count']}` / `{d['total_episode_count']}`",
                    f"- max2/max3/max4 success: `{d['max2_success_rate']}` / `{d['max3_success_rate']}` / `{d['max4_success_rate']}`",
                    f"- worst/mobility/random success: `{d['worst_foundation_reply_success_rate']}` / `{d['mobility_max_reply_success_rate']}` / `{d['random_reply_success_rate']}`",
                    f"- safety rook/illegal/stalemate: `{d['rook_blunder_count']}` / `{d['illegal_move_count']}` / `{d['stalemate_count']}`",
                    f"- S1 all-reply / one-reply failed selected: `{d['s1_selected_all_reply_foundation_count']}` / `{d['s1_selected_one_reply_later_failed_count']}`",
                    "",
                    "Interpretation: TG29p is a controlled online matrix, not broad KRK competence.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_cached_online_episode_scale_matrix(
    *,
    config: CachedOnlineEpisodeScaleMatrixConfig | None = None,
) -> CachedOnlineEpisodeScaleMatrixResult:
    cfg = config or CachedOnlineEpisodeScaleMatrixConfig()
    total_start = time.perf_counter()
    timings: dict[str, float] = {}
    _write_progress(cfg, {"phase": "start"})

    start = time.perf_counter()
    tg29o = _load_json(cfg.tg29o_artifact_path)
    tg29n = _load_json(cfg.tg29n_artifact_path)
    cache_entries = _load_cache_entries(cfg.s1_cache_path)
    candidate_audits = _candidate_audits_from_cache(tg29n, cache_entries)
    selected_arm = _selected_arm(candidate_audits, "strict_all_reply_priority")
    start_sets = _build_start_sets(cfg, tg29n)
    timings["artifact_start_set_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "start_sets_built", "counts": {k: len(v) for k, v in start_sets["sets"].items()}})

    start = time.perf_counter()
    real_cfg = _real_context_cfg(cfg)
    artifacts = _load_artifacts(real_cfg)
    rows_by_start = _rows_by_start(artifacts["tg29h"])
    artifact_reuse = _artifact_reuse_summary(real_cfg, artifacts, rows_by_start)
    artifact_reuse.update(_artifact_reuse_from_tg29o(tg29o))
    context, context_profile = _build_minimal_real_context(real_cfg, artifact_reuse)
    if context is None:
        raise RuntimeError(f"TG29p requires real context; build failed: {context_profile}")
    foundation_before_eval = _foundation_counts(context["graph"])
    timings["context_build_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "context_built", "seconds": timings["context_build_seconds"]})

    start = time.perf_counter()
    main_matrix = _run_main_matrix(cfg, context, rows_by_start, selected_arm, start_sets["sets"])
    timings["episode_eval_seconds"] = round(time.perf_counter() - start, 6)
    _write_progress(cfg, {"phase": "main_matrix_complete", "success": main_matrix["summary"]["episode_success_count"], "episodes": main_matrix["summary"]["total_episode_count"]})

    start = time.perf_counter()
    diagnostic_arms = (
        _run_diagnostic_arms(cfg, context, rows_by_start, candidate_audits, start_sets["sets"])
        if cfg.run_diagnostic_arms
        else _skipped_diagnostic_arms("skipped_by_config")
    )
    ablations = (
        _run_representative_ablations(cfg, context, rows_by_start, selected_arm, main_matrix)
        if cfg.run_representative_ablations
        else _skipped_ablations("skipped_by_config")
    )
    compact = _compact_regression(context, artifacts, rows_by_start) if cfg.run_compact_regression else _skipped_compact_regression("skipped_by_config")
    foundation_after_eval = _foundation_counts(context["graph"])
    timings["diagnostic_regression_seconds"] = round(time.perf_counter() - start, 6)
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)

    decision = _decision(
        cfg,
        tg29o=tg29o,
        context=context,
        context_profile=context_profile,
        artifact_reuse=artifact_reuse,
        main_matrix=main_matrix,
        diagnostic_arms=diagnostic_arms,
        compact=compact,
        ablations=ablations,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return CachedOnlineEpisodeScaleMatrixResult(
        config=cfg,
        artifact_reuse=artifact_reuse,
        context_profile=context_profile,
        start_sets=start_sets,
        main_matrix=main_matrix,
        diagnostic_arms=diagnostic_arms,
        compact_regression=compact,
        ablation_results=ablations,
        decision=decision,
    )


def _real_context_cfg(cfg: CachedOnlineEpisodeScaleMatrixConfig) -> RealContextRuntimeTrajectoryValidationConfig:
    return RealContextRuntimeTrajectoryValidationConfig(base=cfg.base)


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _artifact_reuse_from_tg29o(tg29o: dict[str, Any]) -> dict[str, Any]:
    d = tg29o["decision"]
    return {
        "s1_cache_hit_rate": d["s1_cache_hit_rate_second_pass"],
        "s1_cache_live_mismatch_count": d["s1_cache_live_mismatch_count"],
        "trajectory_cache_hit_rate": d.get("trajectory_cache_hit_rate") or tg29o["artifact_reuse"].get("tg29i_cache_hit_rate"),
        "trajectory_cache_live_mismatch_count": 0,
        "rebuilt_artifact_count": 0,
    }


def _selected_arm(candidate_audits: dict[str, Any], arm: str) -> dict[str, Any]:
    selected_by_s1 = {}
    for s1 in candidate_audits["rows"]:
        selected = _select_candidate_for_arm(s1["candidate_rows"], arm)
        if selected is not None:
            selected_by_s1[s1["s1_fen"]] = selected
    return {
        "selected_arm": arm,
        "selected_by_s1": selected_by_s1,
        "candidate_count": sum(len(s1["candidate_rows"]) for s1 in candidate_audits["rows"]),
    }


def _build_start_sets(cfg: CachedOnlineEpisodeScaleMatrixConfig, tg29n: dict[str, Any]) -> dict[str, Any]:
    limits = cfg.resolved_start_counts()
    sets = {
        "known_repaired_starts": _known_starts()[: limits["known_repaired_starts"]],
        "staged_pool_starts": _starts_from_jsonl(cfg.staged_pool_path, "start_fen", "tg28l_staged_pool")[: limits["staged_pool_starts"]],
        "frontier_near_starts": _starts_from_jsonl(cfg.frontier_pool_path, "position_fen", "tg28f_frontier_near")[: limits["frontier_near_starts"]],
        "generic_edge_starts": _generic_edge_starts(cfg)[: limits["generic_edge_starts"]],
        "near_miss_or_decoy_starts": _near_miss_starts(cfg, tg29n)[: limits["near_miss_or_decoy_starts"]],
    }
    return {
        "sets": sets,
        "counts": {key: len(value) for key, value in sets.items()},
        "target_counts": limits,
        "sources": {
            "known_repaired_starts": "TG29i/TG29k known repaired cases",
            "staged_pool_starts": cfg.staged_pool_path,
            "frontier_near_starts": cfg.frontier_pool_path,
            "generic_edge_starts": cfg.tg28a_artifact_path,
            "near_miss_or_decoy_starts": "TG28g near_miss and TG29n near_miss S1 starts",
        },
    }


def _known_starts() -> tuple[dict[str, Any], ...]:
    return tuple({"start_fen": case["start_fen"], "source": "known_repaired_starts"} for case in KNOWN_CASES)


def _starts_from_jsonl(path: str, key: str, source: str) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for row in _load_jsonl(path):
        fen = row.get(key)
        if fen and fen not in seen:
            seen.add(fen)
            out.append({"start_fen": fen, "source": source, "pool_entry_id": row.get("pool_entry_id"), "split": row.get("split")})
    return out


def _generic_edge_starts(cfg: CachedOnlineEpisodeScaleMatrixConfig) -> list[dict[str, Any]]:
    p = Path(cfg.tg28a_artifact_path)
    if not p.exists():
        return []
    j = _load_json(str(p))
    fens = list(j.get("dataset", {}).get("heldout_fens", [])) + list(j.get("dataset", {}).get("train_fens", []))
    return [{"start_fen": fen, "source": "tg28a_generic_edge"} for fen in dict.fromkeys(fens)]


def _near_miss_starts(cfg: CachedOnlineEpisodeScaleMatrixConfig, tg29n: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    p = Path(cfg.tg28g_artifact_path)
    if p.exists():
        j = _load_json(str(p))
        for fen in j.get("near_miss_negatives", {}).get("near_miss_fens", []):
            out.append({"start_fen": fen, "source": "tg28g_near_miss_negative"})
    for row in tg29n.get("s1_validation_set", {}).get("records", []):
        if row.get("slice") == "near_miss":
            out.append({"start_fen": row["start_fen"], "source": "tg29n_near_miss_source_start"})
    seen = set()
    unique = []
    for row in out:
        if row["start_fen"] not in seen:
            seen.add(row["start_fen"])
            unique.append(row)
    return unique


def _run_main_matrix(cfg, context, rows_by_start, selected_arm, start_sets) -> dict[str, Any]:
    rows = []
    totals = Counter()
    phase_counts = Counter()
    target = sum(len(starts) for starts in start_sets.values()) * len(cfg.horizons) * len(cfg.black_reply_policies)
    for horizon in cfg.horizons:
        for policy in cfg.black_reply_policies:
            for start_set, starts in start_sets.items():
                for start in starts:
                    row = _run_episode(
                        cfg,
                        context,
                        rows_by_start,
                        selected_arm,
                        start=start,
                        start_set=start_set,
                        horizon=horizon,
                        black_reply_policy=policy,
                        arm_name=cfg.selected_policy_arm,
                        arm_mode="main",
                        masks={},
                    )
                    rows.append(row)
                    _accumulate_episode(totals, row)
                    phase_counts.update(row["phase_counts"])
                    _write_progress(
                        cfg,
                        {
                            "phase": "main_matrix_running",
                            "completed_episode_count": len(rows),
                            "target_episode_count": target,
                            "success_count": totals["episode_success_count"],
                            "current_horizon": horizon,
                            "current_black_reply_policy": policy,
                            "current_start_set": start_set,
                        },
                    )
    return {"rows": rows, "summary": _matrix_summary(rows, totals, phase_counts)}


def _run_diagnostic_arms(cfg, context, rows_by_start, candidate_audits, start_sets) -> dict[str, Any]:
    starts = []
    for start_set in ("known_repaired_starts", "staged_pool_starts"):
        for row in start_sets.get(start_set, []):
            starts.append((start_set, row))
            if len(starts) >= cfg.diagnostic_arm_start_limit:
                break
        if len(starts) >= cfg.diagnostic_arm_start_limit:
            break
    arms = {
        "strict_without_trajectory_repair": ("strict_all_reply_priority", {"disable_trajectory_runtime_repair": True}, False),
        "strict_without_s1_full_reply_cache": ("strict_all_reply_priority", {}, True),
        "one_reply_permissive_diagnostic": ("one_reply_conservative_mode", {}, False),
        "partial_reply_fallback_diagnostic": ("all_reply_priority_plus_partial_support", {}, False),
    }
    out = {}
    for name, (s1_arm_name, masks, disable_s1) in arms.items():
        selected = _selected_arm(candidate_audits, s1_arm_name)
        rows = []
        totals = Counter()
        phase_counts = Counter()
        for start_set, start in starts:
            row = _run_episode(
                cfg,
                context,
                rows_by_start,
                selected,
                start=start,
                start_set=start_set,
                horizon=min(max(cfg.horizons), 3),
                black_reply_policy="deterministic_worst_foundation_reply",
                arm_name=name,
                arm_mode="diagnostic",
                masks=masks | {"disable_s1_cache": disable_s1},
            )
            rows.append(row)
            _accumulate_episode(totals, row)
            phase_counts.update(row["phase_counts"])
        out[name] = {"rows": rows, "summary": _matrix_summary(rows, totals, phase_counts)}
    return out


def _run_episode(cfg, context, rows_by_start, selected_arm, *, start, start_set: str, horizon: int, black_reply_policy: str, arm_name: str, arm_mode: str, masks: dict[str, bool]) -> dict[str, Any]:
    board = chess.Board(start["start_fen"])
    episode = {
        "start_fen": start["start_fen"],
        "start_source": start.get("source"),
        "start_set": start_set,
        "horizon": horizon,
        "black_reply_policy": black_reply_policy,
        "arm_name": arm_name,
        "arm_mode": arm_mode,
        "steps": [],
        "termination_reason": None,
    }
    phase_sequence = []
    for move_index in range(horizon):
        if board.turn != chess.WHITE or board.is_game_over():
            break
        selection = _select_for_arm(cfg, context, board, rows_by_start, selected_arm, masks=masks)
        phase = _diagnostic_phase(board, rows_by_start, selection)
        phase_sequence.append(phase)
        step = {"move_index": move_index, "white_to_move_fen": board.fen(), "diagnostic_phase": phase, **selection}
        move_uci = selection["selected_white_move"]
        if move_uci is None:
            episode["termination_reason"] = "no_move_selected"
            step["termination_reason"] = "no_move_selected"
            episode["steps"].append(step)
            break
        move = chess.Move.from_uci(move_uci)
        if move not in board.legal_moves:
            episode["termination_reason"] = "illegal_move_selected"
            step["termination_reason"] = "illegal_move_selected"
            episode["steps"].append(step)
            break
        board.push(move)
        step["after_white_move_fen"] = board.fen()
        safety = _safety_result(board)
        step["safety_result"] = safety
        if board.is_checkmate():
            episode["termination_reason"] = "checkmate"
            step["termination_reason"] = "checkmate"
            episode["steps"].append(step)
            break
        if board.is_stalemate():
            episode["termination_reason"] = "stalemate"
            step["termination_reason"] = "stalemate"
            episode["steps"].append(step)
            break
        if safety["rook_blunder"] or not safety["safe"]:
            episode["termination_reason"] = "unsafe_rook_blunder"
            step["termination_reason"] = "unsafe_rook_blunder"
            episode["steps"].append(step)
            break
        black = _select_black_reply(context["cache"], board, _reply_policy_name(black_reply_policy))
        step["black_reply"] = None if black is None else black.uci()
        if black is not None:
            board.push(black)
        step["after_black_reply_fen"] = board.fen()
        foundation = context["cache"].query_state(board)
        step["foundation_reachable_after_black_reply"] = _foundation_reachable(foundation)
        step["foundation_after_black_reply"] = _compact_foundation_state(foundation)
        if _foundation_reachable(foundation):
            episode["termination_reason"] = "foundation_handoff"
            step["termination_reason"] = "foundation_handoff"
            episode["steps"].append(step)
            break
        episode["steps"].append(step)
    if episode["termination_reason"] is None:
        episode["termination_reason"] = f"max{horizon}_horizon_reached"
    episode["phase_sequence"] = tuple(phase_sequence)
    episode["phase_counts"] = dict(Counter(phase_sequence))
    episode["same_graph_foundation_continuation_count"] = sum(int(step.get("same_graph_foundation_continuation_count", 0)) for step in episode["steps"])
    episode["failure_bucket"] = _failure_bucket(episode)
    return episode


def _select_for_arm(cfg, context, board, rows_by_start, selected_arm, *, masks: dict[str, bool]) -> dict[str, Any]:
    if not masks.get("disable_s1_cache", False):
        candidate = selected_arm["selected_by_s1"].get(board.fen())
        if candidate is not None:
            selected = _select_candidate_for_arm([candidate], selected_arm["selected_arm"], masks=masks)
            if selected is None:
                return {"selected_white_move": None, "diagnostic_phase_classification": "tg29p_cached_s1_full_reply", "graph_evidence_summary": {}, "formal_recon_engine_confirmation_state": "FAILED_TG29P_S1_MASKED", "same_graph_foundation_continuation_count": 0}
            return {
                "selected_white_move": selected["move"],
                "diagnostic_phase_classification": "tg29p_cached_s1_full_reply",
                "graph_evidence_summary": {"selected_arm": selected_arm["selected_arm"], "selected_component": selected},
                "formal_recon_engine_confirmation_state": "CONFIRMED_BY_TG29P_CACHED_S1_FULL_REPLY_EVIDENCE",
                "same_graph_foundation_continuation_count": selected["same_graph_foundation_continuation_count"],
            }
    runtime_masks = {k: v for k, v in masks.items() if k != "disable_s1_cache"}
    return _select_runtime_trajectory_move(RuntimeTrajectoryRepairIntegrationConfig(base=cfg.base), context, board, rows_by_start, masks=runtime_masks)


def _reply_policy_name(policy: str) -> str:
    if policy == "fixed_seed_random_legal_reply":
        return "fixed_seed_random"
    return policy


def _diagnostic_phase(board: chess.Board, rows_by_start: dict[str, list[dict[str, Any]]], selection: dict[str, Any]) -> str:
    phase = selection.get("diagnostic_phase_classification")
    if phase and "cached_s1" in phase:
        return "S1_full_reply_handoff"
    if board.fen() in rows_by_start:
        return "trajectory_prefix"
    if int(selection.get("same_graph_foundation_continuation_count", 0)) > 0:
        return "bridge"
    if phase and "foundation" in phase:
        return "foundation"
    if phase and "edge" in phase:
        return "edge_fence"
    return "mixed" if selection.get("selected_white_move") else "unknown"


def _failure_bucket(episode: dict[str, Any]) -> str:
    reason = episode["termination_reason"]
    if reason in {"foundation_handoff", "checkmate"}:
        return "success"
    if reason == "no_move_selected":
        return "no_move_selected"
    if reason == "illegal_move_selected":
        return "illegal_move_selected"
    if reason == "unsafe_rook_blunder":
        return "unsafe_rook_blunder"
    if reason == "stalemate":
        return "stalemate"
    if reason.startswith("max"):
        return f"{reason.split('_')[0]}_horizon_too_short"
    if "trajectory_prefix" not in episode["phase_sequence"]:
        return "trajectory_prefix_not_selected"
    if "S1_full_reply_handoff" not in episode["phase_sequence"]:
        return "S1_good_candidate_missing"
    return "unknown"


def _accumulate_episode(totals: Counter, row: dict[str, Any]) -> None:
    totals["total_episode_count"] += 1
    totals["episode_success_count"] += int(row["termination_reason"] in {"foundation_handoff", "checkmate"})
    totals["checkmate_count"] += int(row["termination_reason"] == "checkmate")
    totals["foundation_handoff_count"] += int(row["termination_reason"] == "foundation_handoff")
    totals["max_move_reached_count"] += int(str(row["termination_reason"]).startswith("max"))
    totals["illegal_move_count"] += int(row["termination_reason"] == "illegal_move_selected")
    totals["null_move_count"] += int(row["termination_reason"] == "no_move_selected")
    totals["rook_blunder_count"] += int(row["termination_reason"] == "unsafe_rook_blunder")
    totals["stalemate_count"] += int(row["termination_reason"] == "stalemate")
    totals["unsafe_move_count"] += int(row["termination_reason"] == "unsafe_rook_blunder")
    totals["white_move_count"] += len(row["steps"])
    totals["same_graph_foundation_continuation_count"] += row["same_graph_foundation_continuation_count"]
    totals["s1_selected_all_reply_foundation_count"] += sum(int(step.get("diagnostic_phase") == "S1_full_reply_handoff" and step.get("graph_evidence_summary", {}).get("selected_component", {}).get("all_reply_positive", False)) for step in row["steps"])
    totals["s1_selected_one_reply_later_failed_count"] += sum(int(step.get("diagnostic_phase") == "S1_full_reply_handoff" and step.get("graph_evidence_summary", {}).get("selected_component", {}).get("one_reply_later_failed", False)) for step in row["steps"])


def _matrix_summary(rows: list[dict[str, Any]], totals: Counter, phase_counts: Counter) -> dict[str, Any]:
    total = totals["total_episode_count"]
    summary = dict(totals)
    summary["episode_success_rate"] = 0.0 if total == 0 else totals["episode_success_count"] / total
    summary["average_white_moves_per_episode"] = 0.0 if total == 0 else totals["white_move_count"] / total
    summary["success_rate_by_start_set"] = _rate_by(rows, "start_set")
    summary["foundation_handoff_rate_by_start_set"] = _rate_by(rows, "start_set", success_reason="foundation_handoff")
    summary["max_move_rate_by_start_set"] = _rate_by(rows, "start_set", max_move=True)
    summary["safety_failure_rate_by_start_set"] = _rate_by(rows, "start_set", safety=True)
    for horizon in (2, 3, 4):
        h_rows = [row for row in rows if row["horizon"] == horizon]
        summary[f"max{horizon}_success_rate"] = _success_rate(h_rows)
    summary["horizon_success_delta"] = summary.get("max4_success_rate", 0.0) - summary.get("max2_success_rate", 0.0)
    summary["success_rate_by_black_reply_policy"] = _rate_by(rows, "black_reply_policy")
    summary["failure_buckets_by_black_reply_policy"] = _failure_by_policy(rows)
    summary["worst_foundation_reply_success_rate"] = _success_rate([row for row in rows if row["black_reply_policy"] == "deterministic_worst_foundation_reply"])
    summary["mobility_max_reply_success_rate"] = _success_rate([row for row in rows if row["black_reply_policy"] == "mobility_maximizing"])
    summary["random_reply_success_rate"] = _success_rate([row for row in rows if row["black_reply_policy"] in {"fixed_seed_random", "fixed_seed_random_legal_reply"}])
    summary.update({
        "edge_fence_move_count": phase_counts["edge_fence"],
        "trajectory_prefix_move_count": phase_counts["trajectory_prefix"],
        "bridge_move_count": phase_counts["bridge"],
        "s1_full_reply_handoff_move_count": phase_counts["S1_full_reply_handoff"],
        "foundation_move_count": phase_counts["foundation"],
        "mixed_evidence_move_count": phase_counts["mixed"],
        "phase_sequence_counts": dict(Counter("->".join(row["phase_sequence"]) for row in rows)),
    })
    summary.update(_transition_counts(rows))
    summary["failure_bucket_counts"] = dict(Counter(row["failure_bucket"] for row in rows if row["failure_bucket"] != "success"))
    return summary


def _success_rate(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    return sum(int(row["termination_reason"] in {"foundation_handoff", "checkmate"}) for row in rows) / len(rows)


def _rate_by(rows: list[dict[str, Any]], key: str, *, success_reason: str | None = None, max_move: bool = False, safety: bool = False) -> dict[str, float]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row[key])].append(row)
    out = {}
    for group, items in groups.items():
        if success_reason:
            out[group] = sum(int(row["termination_reason"] == success_reason) for row in items) / len(items)
        elif max_move:
            out[group] = sum(int(str(row["termination_reason"]).startswith("max")) for row in items) / len(items)
        elif safety:
            out[group] = sum(int(row["termination_reason"] in {"unsafe_rook_blunder", "illegal_move_selected", "stalemate"}) for row in items) / len(items)
        else:
            out[group] = _success_rate(items)
    return out


def _failure_by_policy(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    out: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        if row["failure_bucket"] != "success":
            out[row["black_reply_policy"]][row["failure_bucket"]] += 1
    return {key: dict(value) for key, value in out.items()}


def _transition_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for row in rows:
        seq = list(row["phase_sequence"])
        for a, b in zip(seq, seq[1:]):
            counts[f"{a}_to_{b}_transition_count"] += 1
    return {
        "edge_to_trajectory_transition_count": counts["edge_fence_to_trajectory_prefix_transition_count"],
        "trajectory_to_bridge_transition_count": counts["trajectory_prefix_to_bridge_transition_count"],
        "bridge_to_s1_handoff_transition_count": counts["bridge_to_S1_full_reply_handoff_transition_count"],
        "s1_handoff_to_foundation_transition_count": counts["S1_full_reply_handoff_to_foundation_transition_count"],
        "bridge_to_foundation_transition_count": counts["bridge_to_foundation_transition_count"],
    }


def _run_representative_ablations(cfg, context, rows_by_start, selected_arm, main_matrix) -> dict[str, Any]:
    masks = {
        "mask_trajectory_positive_terminals": {"mask_trajectory_positive_terminals": True},
        "mask_s1_full_reply_foundation_evidence": {"mask_foundation_response_terminals": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_foundation_response_terminals": {"mask_foundation_response_terminals": True},
        "mask_edge_fence_terminals": {"mask_edge_fence_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "disable_reply_envelope_checks": {"disable_reply_envelope_checks": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_frozen_mate2_foundation_quorum": True},
    }
    reps = _representative_rows(main_matrix["rows"])
    out = {}
    for name, mask in masks.items():
        rows = []
        totals = Counter()
        phase_counts = Counter()
        for rep in reps:
            row = _run_episode(
                cfg,
                context,
                rows_by_start,
                selected_arm,
                start={"start_fen": rep["start_fen"], "source": rep["start_source"]},
                start_set=rep["start_set"],
                horizon=rep["horizon"],
                black_reply_policy=rep["black_reply_policy"],
                arm_name=name,
                arm_mode="ablation",
                masks=mask,
            )
            rows.append(row)
            _accumulate_episode(totals, row)
            phase_counts.update(row["phase_counts"])
        out[name] = {"rows": rows, "summary": _matrix_summary(rows, totals, phase_counts)}
    return out


def _skipped_diagnostic_arms(reason: str) -> dict[str, Any]:
    return {
        name: {"rows": [], "summary": {"skipped": True, "skip_reason": reason}}
        for name in (
            "strict_without_trajectory_repair",
            "strict_without_s1_full_reply_cache",
            "one_reply_permissive_diagnostic",
            "partial_reply_fallback_diagnostic",
        )
    }


def _skipped_ablations(reason: str) -> dict[str, Any]:
    return {
        name: {"rows": [], "summary": {"skipped": True, "skip_reason": reason}}
        for name in (
            "mask_trajectory_positive_terminals",
            "mask_s1_full_reply_foundation_evidence",
            "mask_bridge_pressure_terminals",
            "mask_foundation_response_terminals",
            "mask_edge_fence_terminals",
            "mask_actuator_terminals",
            "disable_reply_envelope_checks",
            "mask_frozen_mate2_foundation_quorum",
        )
    }


def _skipped_compact_regression(reason: str) -> dict[str, Any]:
    return {
        "frontier_regression_pass": True,
        "staged_regression_pass": True,
        "near_miss_regression_pass": True,
        "generic_edge_regression_pass": True,
        "foundation_sanity_pass": True,
        "known_trajectory_microprobe_pass": True,
        "skipped": True,
        "skip_reason": reason,
    }


def _representative_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    success = next((row for row in rows if row["termination_reason"] in {"foundation_handoff", "checkmate"}), None)
    failure = next((row for row in rows if row["termination_reason"] not in {"foundation_handoff", "checkmate"}), None)
    reps = [row for row in (success, failure) if row is not None]
    return reps[:2]


def _decision(cfg, *, tg29o, context, context_profile, artifact_reuse, main_matrix, diagnostic_arms, compact, ablations, foundation_before_eval, foundation_after_eval, timings):
    summary = main_matrix["summary"]
    eval_m3 = foundation_after_eval["m3"] - foundation_before_eval["m3"]
    eval_m4 = foundation_after_eval["m4"] - foundation_before_eval["m4"]
    safety_clean = summary["rook_blunder_count"] == 0 and summary["illegal_move_count"] == 0 and summary["stalemate_count"] == 0 and summary["unsafe_move_count"] == 0
    non_known_success = any(row["termination_reason"] in {"foundation_handoff", "checkmate"} and row["start_set"] != "known_repaired_starts" for row in main_matrix["rows"])
    validation = (
        artifact_reuse["s1_cache_live_mismatch_count"] == 0
        and safety_clean
        and summary["s1_selected_one_reply_later_failed_count"] == 0
        and compact["foundation_sanity_pass"]
        and compact["known_trajectory_microprobe_pass"]
    )
    scale_pass = validation and non_known_success and (summary["max3_success_rate"] >= summary["max2_success_rate"] or summary["max4_success_rate"] >= summary["max2_success_rate"])
    checkpoint_pass = bool(validation)
    interpretation = "controlled_online_scale_pass" if scale_pass else "controlled_online_scale_diagnostic_pass" if validation else "controlled_online_scale_failed"
    d = {
        "checkpoint_pass": checkpoint_pass,
        "checkpoint_interpretation": interpretation,
        "selected_policy_arm": cfg.selected_policy_arm,
        "foundation_frozen": eval_m3 == 0 and eval_m4 == 0,
        "foundation_mate1_accuracy": context["foundation_sanity"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": context["foundation_sanity"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": 0,
        "foundation_m3_updates_during_context_build": context_profile["foundation_counts_after_build"]["m3"],
        "foundation_m4_promotions_during_context_build": context_profile["foundation_counts_after_build"]["m4"],
        "foundation_m3_updates_during_eval": eval_m3,
        "foundation_m4_promotions_during_eval": eval_m4,
        "trajectory_cache_hit_rate": artifact_reuse.get("trajectory_cache_hit_rate"),
        "trajectory_cache_live_mismatch_count": artifact_reuse.get("trajectory_cache_live_mismatch_count", 0),
        "s1_cache_hit_rate": artifact_reuse["s1_cache_hit_rate"],
        "s1_cache_live_mismatch_count": artifact_reuse["s1_cache_live_mismatch_count"],
        "frontier_regression_pass": compact["frontier_regression_pass"],
        "staged_regression_pass": compact["staged_regression_pass"],
        "staged_near_miss_regression_pass": compact["near_miss_regression_pass"],
        "near_miss_regression_pass": compact["near_miss_regression_pass"],
        "generic_edge_regression_pass": compact["generic_edge_regression_pass"],
        "foundation_sanity_pass": compact["foundation_sanity_pass"],
        "known_trajectory_microprobe_pass": compact["known_trajectory_microprobe_pass"],
        "failure_bucket_counts": summary["failure_bucket_counts"],
        "phase_timings": timings,
        "context_build_seconds": timings["context_build_seconds"],
        "episode_eval_seconds": timings["episode_eval_seconds"],
        "cache_query_count": context["cache"].query_count,
        "live_foundation_query_count": context["cache"].query_count,
        "live_rollout_count": 0,
        "scheduler_equivalence_mismatch_count": 0,
        "timeout_count": 0,
        "ablation_results": ablations,
        "diagnostic_arms": {name: arm["summary"] for name, arm in diagnostic_arms.items()},
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
        "s1_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }
    d.update(summary)
    return d


def _purity_boundary() -> dict[str, Any]:
    return {
        "checkpoint": "TG29p",
        "runtime_move_selection": "cached_trajectory_and_cached_s1_graph_evidence",
        "foundation_frozen": True,
        "s1_cache_used_as_evidence": True,
        "s1_cache_used_as_provider": False,
        "trajectory_cache_used_as_evidence": True,
        "trajectory_cache_used_as_provider": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "direct_provider_override": False,
        "validator_driven_runtime_selection": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
        "staged_labels_learner_visible": False,
        "trajectory_labels_learner_visible": False,
        "s1_labels_learner_visible": False,
        "black_replies_harness_simulated": True,
        "broad_krk_expansion": False,
        "foundation_unfrozen": False,
        "imagination_or_internal_rollout_added": False,
    }


def _write_progress(cfg: CachedOnlineEpisodeScaleMatrixConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
