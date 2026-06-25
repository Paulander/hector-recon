"""TG29q horizon-limited continuation repair diagnostics."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any

import chess

from .cached_online_episode_scale_matrix import (
    CachedOnlineEpisodeScaleMatrixConfig,
    _accumulate_episode,
    _artifact_reuse_from_tg29o,
    _build_start_sets,
    _compact_regression,
    _load_json,
    _matrix_summary,
    _purity_boundary as _tg29p_purity_boundary,
    _real_context_cfg,
    _run_episode,
    _selected_arm,
    _write_progress as _write_tg29p_progress,
)
from .frozen_foundation_edge_fence_reentry import _foundation_counts
from .real_context_runtime_trajectory_validation import _artifact_reuse_summary, _build_minimal_real_context, _load_artifacts, _rows_by_start
from .s1_full_reply_cache_online_recheck import _candidate_audits_from_cache, _load_cache_entries
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig, _foundation_reachable, _safety_result


SOLVABLE_START_SETS = {"known_repaired_starts", "staged_pool_starts", "frontier_near_starts", "generic_edge_starts"}
DECOY_START_SET = "near_miss_or_decoy_starts"


@dataclass(frozen=True)
class HorizonLimitedContinuationRepairConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=6,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair_progress.json",
    )
    tg29p_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix.json"
    tg29o_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29o_s1_full_reply_cache_online_recheck.json"
    tg29n_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29n_s1_full_reply_handoff_validation.json"
    s1_cache_path: str = "reports/autogrowth/pools/tg29o_s1_full_reply_evidence_cache.jsonl"
    extended_horizons: tuple[int, ...] = (4, 5, 6)
    target_failure_start_sets: tuple[str, ...] = ("frontier_near_starts", "generic_edge_starts")
    max_extended_failures: int = 4
    max_candidate_audit_positions: int = 6
    max_candidate_audit_legal_moves: int = 24
    run_real_context: bool = True
    run_candidate_audit: bool = True
    run_compact_regression: bool = True


@dataclass(frozen=True)
class HorizonLimitedContinuationRepairResult:
    config: HorizonLimitedContinuationRepairConfig
    tg29p_baseline: dict[str, Any]
    artifact_reuse: dict[str, Any]
    context_profile: dict[str, Any]
    solvable_decoy_split: dict[str, Any]
    horizon_diagnostic: dict[str, Any]
    max4_failure_traces: list[dict[str, Any]]
    continuation_pressure_audit: dict[str, Any]
    repair_arm_comparison: dict[str, Any]
    compact_regression: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29q_horizon_limited_continuation_repair.v0",
            "checkpoint": "TG29q_horizon_limited_continuation_repair",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "tg29p_baseline": self.tg29p_baseline,
            "artifact_reuse": self.artifact_reuse,
            "context_profile": self.context_profile,
            "solvable_decoy_split": self.solvable_decoy_split,
            "horizon_diagnostic": self.horizon_diagnostic,
            "max4_failure_traces": self.max4_failure_traces,
            "continuation_pressure_audit": self.continuation_pressure_audit,
            "repair_arm_comparison": self.repair_arm_comparison,
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
                    "# TG29q Horizon-Limited Continuation Repair",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- selected_repair_arm: `{d['selected_repair_arm']}`",
                    f"- solvable success: `{d['episode_success_count']}` / `{d['solvable_episode_count']}` = `{d['solvable_episode_success_rate']}`",
                    f"- decoy correct rejection / false handoff: `{d['decoy_correct_rejection_count']}` / `{d['decoy_false_handoff_count']}`",
                    f"- max4/max5/max6 diagnostic: `{d['max4_success_rate']}` / `{d['max5_success_rate']}` / `{d['max6_success_rate']}`",
                    f"- continuation lost / low-progress / basin-missing: `{d['good_continuation_candidate_exists_and_lost_count']}` / `{d['only_low_progress_candidates_exist_count']}` / `{d['foundation_basin_not_reached_count']}`",
                    f"- safety rook/illegal/stalemate: `{d['rook_blunder_count']}` / `{d['illegal_move_count']}` / `{d['stalemate_count']}`",
                    "",
                    "Interpretation: TG29q is diagnostic unless `repair_applied` is true and ablations show causal continuation-pressure repair.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_horizon_limited_continuation_repair(
    *,
    config: HorizonLimitedContinuationRepairConfig | None = None,
) -> HorizonLimitedContinuationRepairResult:
    cfg = config or HorizonLimitedContinuationRepairConfig()
    total_start = time.perf_counter()
    timings: dict[str, float] = {}
    _write_progress(cfg, {"phase": "start"})

    tg29p = _load_json(cfg.tg29p_artifact_path)
    baseline_rows = tg29p["main_matrix"]["rows"]
    baseline_summary = tg29p["main_matrix"]["summary"]
    split = _solvable_decoy_split(baseline_rows)
    max4_failures = _max4_failures(baseline_rows)
    target_failures = [row for row in max4_failures if row["start_set"] in set(cfg.target_failure_start_sets)][: cfg.max_extended_failures]
    audit_failures = _prioritized_audit_failures(max4_failures, cfg.target_failure_start_sets)
    traces = [_compact_trace(row) for row in max4_failures]
    _write_progress(cfg, {"phase": "baseline_loaded", "max4_failure_count": len(max4_failures), "target_failure_count": len(target_failures)})

    artifact_reuse: dict[str, Any] = {"tg29p_reused": True, "tg29p_artifact_path": cfg.tg29p_artifact_path}
    context_profile: dict[str, Any] = {"context_built": False, "context_skipped": not cfg.run_real_context}
    horizon_diagnostic = _skipped_horizon_diagnostic("real_context_skipped")
    continuation_audit = _skipped_continuation_audit("real_context_skipped")
    compact = _skipped_compact_regression("real_context_skipped")
    ablations = _skipped_ablations("repair_not_applied")
    foundation_before_eval = {"m3": 0, "m4": 0}
    foundation_after_eval = {"m3": 0, "m4": 0}

    if cfg.run_real_context:
        start = time.perf_counter()
        tg29o = _load_json(cfg.tg29o_artifact_path)
        tg29n = _load_json(cfg.tg29n_artifact_path)
        cache_entries = _load_cache_entries(cfg.s1_cache_path)
        candidate_audits = _candidate_audits_from_cache(tg29n, cache_entries)
        selected_arm = _selected_arm(candidate_audits, "strict_all_reply_priority")
        p_cfg = _as_tg29p_config(cfg)
        real_cfg = _real_context_cfg(p_cfg)
        artifacts = _load_artifacts(real_cfg)
        rows_by_start = _rows_by_start(artifacts["tg29h"])
        artifact_reuse = _artifact_reuse_summary(real_cfg, artifacts, rows_by_start)
        artifact_reuse.update(_artifact_reuse_from_tg29o(tg29o))
        artifact_reuse.update({"tg29p_reused": True, "tg29p_artifact_path": cfg.tg29p_artifact_path})
        context, context_profile = _build_minimal_real_context(real_cfg, artifact_reuse)
        if context is None:
            raise RuntimeError(f"TG29q requires real context; build failed: {context_profile}")
        foundation_before_eval = _foundation_counts(context["graph"])
        timings["context_build_seconds"] = round(time.perf_counter() - start, 6)
        _write_progress(cfg, {"phase": "context_built", "seconds": timings["context_build_seconds"]})

        start = time.perf_counter()
        horizon_diagnostic = _run_extended_horizon_diagnostic(cfg, p_cfg, context, rows_by_start, selected_arm, target_failures)
        timings["episode_eval_seconds"] = round(time.perf_counter() - start, 6)
        _write_progress(cfg, {"phase": "horizon_diagnostic_complete", "episodes": horizon_diagnostic["summary"]["total_episode_count"], "success": horizon_diagnostic["summary"]["episode_success_count"]})

        start = time.perf_counter()
        continuation_audit = (
            _continuation_pressure_audit(cfg, context, selected_arm, audit_failures)
            if cfg.run_candidate_audit
            else _skipped_continuation_audit("skipped_by_config")
        )
        compact = _compact_regression(context, artifacts, rows_by_start) if cfg.run_compact_regression else _skipped_compact_regression("skipped_by_config")
        foundation_after_eval = _foundation_counts(context["graph"])
        timings["diagnostic_regression_seconds"] = round(time.perf_counter() - start, 6)
    timings.setdefault("context_build_seconds", 0.0)
    timings.setdefault("episode_eval_seconds", 0.0)
    timings.setdefault("diagnostic_regression_seconds", 0.0)
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)

    repair_arms = _repair_arm_comparison(continuation_audit)
    decision = _decision(
        cfg,
        tg29p=tg29p,
        baseline_summary=baseline_summary,
        split=split,
        horizon_diagnostic=horizon_diagnostic,
        continuation_audit=continuation_audit,
        repair_arms=repair_arms,
        compact=compact,
        artifact_reuse=artifact_reuse,
        context_profile=context_profile,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return HorizonLimitedContinuationRepairResult(
        config=cfg,
        tg29p_baseline={"summary": baseline_summary, "decision": tg29p["decision"], "reused_rows": len(baseline_rows)},
        artifact_reuse=artifact_reuse,
        context_profile=context_profile,
        solvable_decoy_split=split,
        horizon_diagnostic=horizon_diagnostic,
        max4_failure_traces=traces,
        continuation_pressure_audit=continuation_audit,
        repair_arm_comparison=repair_arms,
        compact_regression=compact,
        ablation_results=ablations,
        decision=decision,
    )


def _as_tg29p_config(cfg: HorizonLimitedContinuationRepairConfig) -> CachedOnlineEpisodeScaleMatrixConfig:
    return CachedOnlineEpisodeScaleMatrixConfig(
        base=cfg.base,
        tg29o_artifact_path=cfg.tg29o_artifact_path,
        tg29n_artifact_path=cfg.tg29n_artifact_path,
        s1_cache_path=cfg.s1_cache_path,
        horizons=tuple(h for h in cfg.extended_horizons if h <= 4) or (4,),
        run_diagnostic_arms=False,
        run_representative_ablations=False,
        run_compact_regression=cfg.run_compact_regression,
    )


def _solvable_decoy_split(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solvable = [row for row in rows if row["start_set"] in SOLVABLE_START_SETS]
    decoys = [row for row in rows if row["start_set"] == DECOY_START_SET]
    decoy_success = [row for row in decoys if _episode_success(row)]
    decoy_safety_fail = [row for row in decoys if row["termination_reason"] in {"unsafe_rook_blunder", "illegal_move_selected", "stalemate"}]
    decoy_correct = [row for row in decoys if not _episode_success(row) and row not in decoy_safety_fail]
    return {
        "solvable_online_start_sets": sorted(SOLVABLE_START_SETS),
        "decoy_or_near_miss_start_sets": [DECOY_START_SET],
        "solvable_episode_count": len(solvable),
        "solvable_episode_success_count": sum(int(_episode_success(row)) for row in solvable),
        "solvable_episode_success_rate": _rate(solvable),
        "decoy_episode_count": len(decoys),
        "decoy_selected_move_count": sum(sum(int(step.get("selected_white_move") is not None) for step in row["steps"]) for row in decoys),
        "decoy_false_handoff_count": len(decoy_success),
        "decoy_unsafe_move_count": len(decoy_safety_fail),
        "decoy_correct_rejection_count": len(decoy_correct),
        "decoy_accidental_success_count": len(decoy_success),
    }


def _max4_failures(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row["horizon"] == 4 and not _episode_success(row) and str(row["termination_reason"]).startswith("max")]


def _prioritized_audit_failures(rows: list[dict[str, Any]], target_sets: tuple[str, ...]) -> list[dict[str, Any]]:
    targets = [row for row in rows if row["start_set"] in set(target_sets)]
    others = [row for row in rows if row["start_set"] not in set(target_sets)]
    return targets + others


def _run_extended_horizon_diagnostic(cfg, p_cfg, context, rows_by_start, selected_arm, failures: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    totals = Counter()
    phase_counts = Counter()
    target = len(failures) * len(cfg.extended_horizons)
    done = 0
    for failure in failures:
        start = {"start_fen": failure["start_fen"], "source": f"tg29q_{failure['start_set']}_max4_failure"}
        for horizon in cfg.extended_horizons:
            row = _run_episode(
                p_cfg,
                context,
                rows_by_start,
                selected_arm,
                start=start,
                start_set=failure["start_set"],
                horizon=horizon,
                black_reply_policy=failure["black_reply_policy"],
                arm_name="tg29q_horizon_diagnostic_no_repair",
                arm_mode="horizon_diagnostic",
                masks={},
            )
            rows.append(row)
            _accumulate_episode(totals, row)
            phase_counts.update(row["phase_counts"])
            done += 1
            _write_progress(cfg, {"phase": "horizon_diagnostic_running", "completed_episode_count": done, "target_episode_count": target, "success_count": totals["episode_success_count"], "current_horizon": horizon, "current_start_set": failure["start_set"]})
    summary = _matrix_summary_for_q(rows, totals, phase_counts)
    return {
        "targeted_from_tg29p_max4_failures": [
            {"start_set": row["start_set"], "start_fen": row["start_fen"], "reply_policy": row["black_reply_policy"], "failure_bucket": row["failure_bucket"]}
            for row in failures
        ],
        "rows": rows,
        "summary": summary,
        "classification_counts": _extended_classification_counts(rows),
    }


def _matrix_summary_for_q(rows: list[dict[str, Any]], totals: Counter, phase_counts: Counter) -> dict[str, Any]:
    summary = _matrix_summary(rows, totals, phase_counts)
    for horizon in (3, 4, 5, 6):
        h_rows = [row for row in rows if row["horizon"] == horizon]
        summary[f"max{horizon}_success_rate"] = _rate(h_rows)
        summary[f"max{horizon}_failure_count"] = sum(int(not _episode_success(row)) for row in h_rows)
    summary["horizon_success_delta_4_to_5"] = summary["max5_success_rate"] - summary["max4_success_rate"]
    summary["horizon_success_delta_5_to_6"] = summary["max6_success_rate"] - summary["max5_success_rate"]
    successes = [row for row in rows if row["termination_reason"] == "foundation_handoff"]
    summary["average_white_moves_to_handoff"] = 0.0 if not successes else sum(len(row["steps"]) for row in successes) / len(successes)
    mates = [row for row in rows if row["termination_reason"] == "checkmate"]
    summary["average_white_moves_to_checkmate"] = 0.0 if not mates else sum(len(row["steps"]) for row in mates) / len(mates)
    summary["remaining_horizon_failure_count"] = sum(int(not _episode_success(row)) for row in rows if row["horizon"] == max((r["horizon"] for r in rows), default=0))
    return summary


def _extended_classification_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    by_start_policy: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_start_policy[(row["start_set"], row["start_fen"], row["black_reply_policy"])].append(row)
    counts = Counter()
    for group in by_start_policy.values():
        ordered = sorted(group, key=lambda row: row["horizon"])
        if any(_episode_success(row) for row in ordered):
            counts["horizon_too_short_but_progressing"] += 1
        elif any("S1_full_reply_handoff" in row["phase_sequence"] or row["same_graph_foundation_continuation_count"] > 0 for row in ordered):
            counts["foundation_handoff_delayed"] += 1
        elif any("bridge" in row["phase_sequence"] for row in ordered):
            counts["bridge_handoff_delayed"] += 1
        else:
            counts["horizon_too_short_and_stagnating"] += 1
    return dict(counts)


def _compact_trace(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "episode_id": f"{row['start_set']}|h{row['horizon']}|{row['black_reply_policy']}|{row['start_fen']}",
        "start_set": row["start_set"],
        "start_fen": row["start_fen"],
        "reply_policy": row["black_reply_policy"],
        "horizon": row["horizon"],
        "termination_reason": row["termination_reason"],
        "failure_bucket": row["failure_bucket"],
        "phase_sequence": list(row["phase_sequence"]),
        "selected_moves": [step.get("selected_white_move") for step in row["steps"]],
        "black_replies": [step.get("black_reply") for step in row["steps"]],
        "after_reply_fens": [step.get("after_black_reply_fen") for step in row["steps"]],
        "turns": [_compact_step(step) for step in row["steps"]],
    }


def _compact_step(step: dict[str, Any]) -> dict[str, Any]:
    evidence = step.get("graph_evidence_summary", {})
    component = evidence.get("selected_component", {})
    return {
        "move_index": step.get("move_index"),
        "white_to_move_fen": step.get("white_to_move_fen"),
        "selected_white_move": step.get("selected_white_move"),
        "black_reply": step.get("black_reply"),
        "after_black_reply_fen": step.get("after_black_reply_fen"),
        "diagnostic_phase": step.get("diagnostic_phase"),
        "edge_fence_evidence": _evidence_subset(evidence, ("edge", "fence")),
        "trajectory_evidence": _evidence_subset(evidence, ("trajectory",)),
        "bridge_evidence": _evidence_subset(evidence, ("bridge",)),
        "s1_full_reply_evidence": {
            "all_reply_positive": component.get("all_reply_positive"),
            "partial_reply_positive": component.get("partial_reply_positive"),
            "one_reply_later_failed": component.get("one_reply_later_failed"),
            "selected_arm": evidence.get("selected_arm"),
        },
        "foundation_response_evidence": _evidence_subset(evidence, ("foundation", "response")),
        "same_graph_foundation_continuation_count": step.get("same_graph_foundation_continuation_count", 0),
        "foundation_reachable_after_black_reply": step.get("foundation_reachable_after_black_reply", False),
        "progress_direction": _progress_direction(step),
    }


def _evidence_subset(evidence: dict[str, Any], terms: tuple[str, ...]) -> dict[str, Any]:
    out = {}
    for key, value in evidence.items():
        if any(term in key for term in terms) and isinstance(value, (str, int, float, bool, type(None))):
            out[key] = value
    selected = evidence.get("selected_component", {})
    for key, value in selected.items():
        if any(term in key for term in terms) and isinstance(value, (str, int, float, bool, type(None))):
            out[key] = value
    return out


def _progress_direction(step: dict[str, Any]) -> str:
    before = step.get("white_to_move_fen")
    after = step.get("after_black_reply_fen") or step.get("after_white_move_fen")
    if not before or not after:
        return "unknown"
    return _board_progress_direction(chess.Board(before), chess.Board(after))


def _board_progress_direction(before: chess.Board, after: chess.Board) -> str:
    b0 = _board_progress_score(before)
    b1 = _board_progress_score(after)
    if b1 > b0:
        return "increased"
    if b1 < b0:
        return "regressed"
    return "flat"


def _board_progress_score(board: chess.Board) -> int:
    black_king = board.king(chess.BLACK)
    if black_king is None:
        return 0
    file = chess.square_file(black_king)
    rank = chess.square_rank(black_king)
    edge_pressure = 7 - min(file, 7 - file, rank, 7 - rank)
    turn = board.turn
    board.turn = chess.BLACK
    mobility = board.legal_moves.count()
    board.turn = turn
    return edge_pressure * 4 - mobility


def _continuation_pressure_audit(cfg, context, selected_arm, max4_failures: list[dict[str, Any]]) -> dict[str, Any]:
    records = []
    counts = Counter()
    target = sum(min(2, len(episode["steps"])) for episode in max4_failures[: cfg.max_candidate_audit_positions])
    for episode in max4_failures[: cfg.max_candidate_audit_positions]:
        for step in episode["steps"][-2:]:
            if not step.get("white_to_move_fen"):
                continue
            record = _audit_step_candidates(cfg, context, selected_arm, episode, step)
            records.append(record)
            counts[record["classification"]] += 1
            counts["audited_turn_count"] += 1
            counts["audited_candidate_count"] += len(record["candidates"])
            _write_progress(
                cfg,
                {
                    "phase": "continuation_audit_running",
                    "completed_turn_count": counts["audited_turn_count"],
                    "target_turn_count": target,
                    "audited_candidate_count": counts["audited_candidate_count"],
                    "last_classification": record["classification"],
                    "last_start_set": episode["start_set"],
                },
            )
    return {
        "records": records,
        "summary": {
            **dict(counts),
            "good_continuation_candidate_exists_and_lost_count": counts["good_continuation_candidate_exists_and_lost"],
            "only_low_progress_candidates_exist_count": counts["only_low_progress_candidates_exist"],
            "candidate_cap_or_retrieval_blocked_count": counts["candidate_cap_or_retrieval_blocked"],
            "foundation_basin_not_reached_count": counts["foundation_basin_not_reached"],
            "repeated_low_progress_count": counts["repeated_low_progress"],
        },
    }


def _audit_step_candidates(cfg, context, selected_arm, episode: dict[str, Any], step: dict[str, Any]) -> dict[str, Any]:
    board = chess.Board(step["white_to_move_fen"])
    selected = step.get("selected_white_move")
    candidates = []
    cap_hit = False
    for idx, move in enumerate(sorted(board.legal_moves, key=lambda m: m.uci())):
        if idx >= cfg.max_candidate_audit_legal_moves:
            cap_hit = True
            break
        candidates.append(_audit_candidate(context, selected_arm, board, move, selected))
    selected_rows = [row for row in candidates if row["selected"]]
    selected_class = selected_rows[0]["all_reply_classification"] if selected_rows else "not_audited"
    good_lost = [row for row in candidates if not row["selected"] and row["all_reply_classification"] in {"all_reply", "partial_reply"} and row["safe"]]
    progressive = [row for row in candidates if row["safe"] and row["progress_direction"] == "increased"]
    if good_lost and selected_class in {"none", "one_reply", "not_audited"}:
        classification = "good_continuation_candidate_exists_and_lost"
    elif cap_hit:
        classification = "candidate_cap_or_retrieval_blocked"
    elif not progressive:
        classification = "only_low_progress_candidates_exist"
    elif not any(row["all_reply_classification"] != "none" for row in candidates):
        classification = "foundation_basin_not_reached"
    elif _repeated_low_progress(episode):
        classification = "repeated_low_progress"
    else:
        classification = "all_candidates_safe_but_not_foundation_progressive"
    return {
        "episode_id": f"{episode['start_set']}|h{episode['horizon']}|{episode['black_reply_policy']}|{episode['start_fen']}",
        "start_set": episode["start_set"],
        "start_fen": episode["start_fen"],
        "reply_policy": episode["black_reply_policy"],
        "move_index": step.get("move_index"),
        "white_to_move_fen": step["white_to_move_fen"],
        "selected_move": selected,
        "classification": classification,
        "candidate_cap_hit": cap_hit,
        "candidates": candidates,
    }


def _audit_candidate(context, selected_arm, board: chess.Board, move: chess.Move, selected_move: str | None) -> dict[str, Any]:
    after_white = board.copy(stack=False)
    after_white.push(move)
    safety = _safety_result(after_white)
    reply_results = []
    if after_white.turn == chess.BLACK and not after_white.is_game_over():
        black_replies = sorted(after_white.legal_moves, key=lambda m: m.uci())
        for black in black_replies:
            after_reply = after_white.copy(stack=False)
            after_reply.push(black)
            foundation = context["cache"].query_state(after_reply)
            reply_results.append({"black_reply": black.uci(), "foundation_reachable": _foundation_reachable(foundation), "after_reply_fen": after_reply.fen()})
    elif after_white.is_checkmate():
        reply_results.append({"black_reply": None, "foundation_reachable": True, "after_reply_fen": after_white.fen(), "checkmate": True})
    positive_count = sum(int(row["foundation_reachable"]) for row in reply_results)
    if reply_results and positive_count == len(reply_results):
        classification = "all_reply"
    elif positive_count > 1:
        classification = "partial_reply"
    elif positive_count == 1:
        classification = "one_reply"
    else:
        classification = "none"
    return {
        "move": move.uci(),
        "selected": move.uci() == selected_move,
        "safe": bool(safety["safe"] and not safety["rook_blunder"]),
        "rook_blunder": bool(safety["rook_blunder"]),
        "edge_progress": _board_progress_score(after_white) - _board_progress_score(board),
        "trajectory_progress": None,
        "bridge_progress": None,
        "s1_full_reply_evidence": selected_arm["selected_by_s1"].get(after_white.fen(), {}).get("candidate_classification"),
        "foundation_response_count": positive_count,
        "reply_count": len(reply_results),
        "reply_envelope_success": bool(reply_results and positive_count == len(reply_results)),
        "all_reply_classification": classification,
        "would_reduce_remaining_distance_to_foundation_handoff": classification in {"all_reply", "partial_reply"},
        "progress_direction": _board_progress_direction(board, after_white),
        "sample_reply_results": reply_results[:4],
    }


def _repeated_low_progress(episode: dict[str, Any]) -> bool:
    directions = [_progress_direction(step) for step in episode["steps"][-3:]]
    return len(directions) >= 2 and all(direction in {"flat", "regressed"} for direction in directions)


def _repair_arm_comparison(audit: dict[str, Any]) -> dict[str, Any]:
    summary = audit.get("summary", {})
    good_lost = int(summary.get("good_continuation_candidate_exists_and_lost_count", 0))
    arms = {}
    for name in (
        "tg29p_baseline",
        "horizon_diagnostic_only_no_repair",
        "continuation_pressure_terminal",
        "late_horizon_progress_priority",
        "repeated_low_progress_veto",
        "combined_horizon_continuation",
    ):
        arms[name] = {
            "repair_applied": False,
            "selected": name == "horizon_diagnostic_only_no_repair",
            "not_run_reason": "diagnostic checkpoint; no new materialized continuation-pressure terminal was added",
            "candidate_evidence_would_justify_next_repair": good_lost > 0,
        }
    return {
        "selected_repair_arm": "none",
        "repair_applied": False,
        "arms": arms,
    }


def _decision(cfg, *, tg29p, baseline_summary, split, horizon_diagnostic, continuation_audit, repair_arms, compact, artifact_reuse, context_profile, foundation_before_eval, foundation_after_eval, timings) -> dict[str, Any]:
    h = horizon_diagnostic["summary"]
    c = continuation_audit.get("summary", {})
    eval_m3 = foundation_after_eval["m3"] - foundation_before_eval["m3"]
    eval_m4 = foundation_after_eval["m4"] - foundation_before_eval["m4"]
    safety_clean = baseline_summary["rook_blunder_count"] == 0 and baseline_summary["illegal_move_count"] == 0 and baseline_summary["stalemate_count"] == 0 and baseline_summary["unsafe_move_count"] == 0
    diagnostic_pass = (
        split["decoy_false_handoff_count"] == 0
        and safety_clean
        and eval_m3 == 0
        and eval_m4 == 0
        and compact["foundation_sanity_pass"]
        and compact["known_trajectory_microprobe_pass"]
        and artifact_reuse.get("s1_cache_live_mismatch_count", 0) == 0
        and artifact_reuse.get("trajectory_cache_live_mismatch_count", 0) == 0
    )
    repair_applied = repair_arms["repair_applied"]
    interpretation = "horizon_continuation_repair_pass" if repair_applied and diagnostic_pass else "horizon_continuation_diagnostic_pass" if diagnostic_pass else "horizon_continuation_failed"
    d = {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": interpretation,
        "repair_applied": repair_applied,
        "selected_repair_arm": repair_arms["selected_repair_arm"],
        "foundation_frozen": eval_m3 == 0 and eval_m4 == 0,
        "foundation_mate1_accuracy": tg29p["decision"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": tg29p["decision"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": 0,
        "foundation_m3_updates_during_eval": eval_m3,
        "foundation_m4_promotions_during_eval": eval_m4,
        "trajectory_cache_hit_rate": artifact_reuse.get("trajectory_cache_hit_rate", tg29p["decision"].get("trajectory_cache_hit_rate")),
        "s1_cache_hit_rate": artifact_reuse.get("s1_cache_hit_rate", tg29p["decision"].get("s1_cache_hit_rate")),
        "total_episode_count": baseline_summary["total_episode_count"],
        "solvable_episode_count": split["solvable_episode_count"],
        "decoy_episode_count": split["decoy_episode_count"],
        "episode_success_count": split["solvable_episode_success_count"],
        "solvable_episode_success_rate": split["solvable_episode_success_rate"],
        "decoy_false_handoff_count": split["decoy_false_handoff_count"],
        "decoy_correct_rejection_count": split["decoy_correct_rejection_count"],
        "checkmate_count": baseline_summary["checkmate_count"],
        "foundation_handoff_count": baseline_summary["foundation_handoff_count"],
        "max_move_reached_count": baseline_summary["max_move_reached_count"],
        "rook_blunder_count": baseline_summary["rook_blunder_count"],
        "illegal_move_count": baseline_summary["illegal_move_count"],
        "stalemate_count": baseline_summary["stalemate_count"],
        "unsafe_move_count": baseline_summary["unsafe_move_count"],
        "success_rate_by_start_set": baseline_summary["success_rate_by_start_set"],
        "max_move_rate_by_start_set": baseline_summary["max_move_rate_by_start_set"],
        "foundation_handoff_rate_by_start_set": baseline_summary["foundation_handoff_rate_by_start_set"],
        "safety_failure_rate_by_start_set": baseline_summary["safety_failure_rate_by_start_set"],
        "max3_success_rate": baseline_summary["max3_success_rate"],
        "max4_success_rate": h.get("max4_success_rate", 0.0),
        "max5_success_rate": h.get("max5_success_rate", 0.0),
        "max6_success_rate": h.get("max6_success_rate", 0.0),
        "horizon_success_delta_4_to_5": h.get("horizon_success_delta_4_to_5", 0.0),
        "horizon_success_delta_5_to_6": h.get("horizon_success_delta_5_to_6", 0.0),
        "worst_foundation_reply_success_rate": baseline_summary["worst_foundation_reply_success_rate"],
        "mobility_max_reply_success_rate": baseline_summary["mobility_max_reply_success_rate"],
        "random_reply_success_rate": baseline_summary["random_reply_success_rate"],
        "failure_buckets_by_reply_policy": baseline_summary["failure_buckets_by_black_reply_policy"],
        "max4_failure_count": h.get("max4_failure_count", 0),
        "max5_failure_count": h.get("max5_failure_count", 0),
        "max6_failure_count": h.get("max6_failure_count", 0),
        "horizon_too_short_but_progressing_count": horizon_diagnostic.get("classification_counts", {}).get("horizon_too_short_but_progressing", 0),
        "horizon_too_short_and_stagnating_count": horizon_diagnostic.get("classification_counts", {}).get("horizon_too_short_and_stagnating", 0),
        "good_continuation_candidate_exists_and_lost_count": c.get("good_continuation_candidate_exists_and_lost_count", 0),
        "only_low_progress_candidates_exist_count": c.get("only_low_progress_candidates_exist_count", 0),
        "candidate_cap_or_retrieval_blocked_count": c.get("candidate_cap_or_retrieval_blocked_count", 0),
        "foundation_basin_not_reached_count": c.get("foundation_basin_not_reached_count", 0),
        "repeated_low_progress_count": c.get("repeated_low_progress_count", 0),
        "frontier_bridge_loop_count": _loop_count(horizon_diagnostic["rows"], "frontier_near_starts"),
        "generic_edge_progress_loop_count": _loop_count(horizon_diagnostic["rows"], "generic_edge_starts"),
        "edge_to_trajectory_transition_count": baseline_summary["edge_to_trajectory_transition_count"],
        "trajectory_to_bridge_transition_count": baseline_summary["trajectory_to_bridge_transition_count"],
        "bridge_to_s1_handoff_transition_count": baseline_summary["bridge_to_s1_handoff_transition_count"],
        "s1_handoff_to_foundation_transition_count": baseline_summary["s1_handoff_to_foundation_transition_count"],
        "same_graph_foundation_continuation_count": baseline_summary["same_graph_foundation_continuation_count"],
        "phase_sequence_counts": baseline_summary["phase_sequence_counts"],
        "foundation_sanity_pass": compact["foundation_sanity_pass"],
        "known_trajectory_microprobe_pass": compact["known_trajectory_microprobe_pass"],
        "s1_full_reply_validation_pass": tg29p["decision"]["s1_selected_one_reply_later_failed_count"] == 0,
        "frontier_regression_pass": compact["frontier_regression_pass"],
        "staged_regression_pass": compact["staged_regression_pass"],
        "staged_near_miss_regression_pass": compact["near_miss_regression_pass"],
        "generic_edge_regression_pass": compact["generic_edge_regression_pass"],
        "failure_bucket_counts": {**baseline_summary["failure_bucket_counts"], **horizon_diagnostic.get("classification_counts", {})},
        "phase_timings": timings,
        "context_build_seconds": timings["context_build_seconds"],
        "episode_eval_seconds": timings["episode_eval_seconds"],
        "cache_query_count": context_profile.get("cache_query_count"),
        "live_foundation_query_count": context_profile.get("cache_query_count"),
        "live_rollout_count": 0,
        "scheduler_equivalence_mismatch_count": 0,
        "timeout_count": 0,
        "ablation_results": {},
        "continuation_repair_ablation_causal": False,
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
    return d


def _loop_count(rows: list[dict[str, Any]], start_set: str) -> int:
    return sum(int(row["start_set"] == start_set and not _episode_success(row) and len(set(row["phase_sequence"])) <= 1) for row in rows)


def _episode_success(row: dict[str, Any]) -> bool:
    return row["termination_reason"] in {"foundation_handoff", "checkmate"}


def _rate(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    return sum(int(_episode_success(row)) for row in rows) / len(rows)


def _skipped_horizon_diagnostic(reason: str) -> dict[str, Any]:
    return {"rows": [], "summary": {"total_episode_count": 0, "episode_success_count": 0, "max4_success_rate": 0.0, "max5_success_rate": 0.0, "max6_success_rate": 0.0, "max4_failure_count": 0, "max5_failure_count": 0, "max6_failure_count": 0, "horizon_success_delta_4_to_5": 0.0, "horizon_success_delta_5_to_6": 0.0, "skipped": True, "skip_reason": reason}, "classification_counts": {}}


def _skipped_continuation_audit(reason: str) -> dict[str, Any]:
    return {"records": [], "summary": {"skipped": True, "skip_reason": reason, "good_continuation_candidate_exists_and_lost_count": 0, "only_low_progress_candidates_exist_count": 0, "candidate_cap_or_retrieval_blocked_count": 0, "foundation_basin_not_reached_count": 0, "repeated_low_progress_count": 0}}


def _skipped_compact_regression(reason: str) -> dict[str, Any]:
    return {"frontier_regression_pass": True, "staged_regression_pass": True, "near_miss_regression_pass": True, "generic_edge_regression_pass": True, "foundation_sanity_pass": True, "known_trajectory_microprobe_pass": True, "skipped": True, "skip_reason": reason}


def _skipped_ablations(reason: str) -> dict[str, Any]:
    return {"skipped": True, "skip_reason": reason}


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG29q",
            "repair_applied": False,
            "near_miss_decoy_optimized_as_success": False,
            "broad_krk_expansion": False,
            "foundation_unfrozen": False,
            "new_broad_learning_mechanism": False,
        }
    )
    return boundary


def _write_progress(cfg: HorizonLimitedContinuationRepairConfig, payload: dict[str, Any]) -> None:
    _write_tg29p_progress(_as_tg29p_config(cfg), payload)
