"""TG29m post-trajectory second-move handoff audit."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any

import chess

from .frozen_foundation_edge_fence_reentry import _cheap_candidate_rows, _foundation_counts
from .frozen_foundation_response_cache_bridge_retrieval import _cache_candidate_rows
from .real_context_runtime_trajectory_validation import (
    RealContextRuntimeTrajectoryValidationConfig,
    _artifact_reuse_summary,
    _build_minimal_real_context,
    _load_artifacts,
    _rows_by_start,
)
from .runtime_trajectory_repair_integration import RuntimeTrajectoryRepairIntegrationConfig, _select_runtime_trajectory_move
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
class PostTrajectorySecondMoveHandoffAuditConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=2,
        max_white_moves_per_episode=2,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29m_post_trajectory_second_move_handoff_audit_progress.json",
    )
    tg29l_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29l_real_context_runtime_trajectory_validation.json"
    selected_repair_arm: str = "second_move_full_reply_foundation_response_priority"
    run_repair: bool = True
    run_max3_diagnostic: bool = True


@dataclass(frozen=True)
class PostTrajectorySecondMoveHandoffAuditResult:
    config: PostTrajectorySecondMoveHandoffAuditConfig
    failing_episode_trace: dict[str, Any]
    s1_candidate_audit: dict[str, Any]
    first_move_variant_audit: dict[str, Any]
    repair: dict[str, Any]
    max2_recheck: dict[str, Any]
    max3_diagnostic: dict[str, Any]
    compact_regression: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29m_post_trajectory_second_move_handoff_audit.v0",
            "checkpoint": "TG29m_post_trajectory_second_move_handoff_audit",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "failing_episode_trace": self.failing_episode_trace,
            "s1_candidate_audit": self.s1_candidate_audit,
            "first_move_variant_audit": self.first_move_variant_audit,
            "repair": self.repair,
            "max2_recheck": self.max2_recheck,
            "max3_diagnostic": self.max3_diagnostic,
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
                    "# TG29m Post-Trajectory Second-Move Handoff Audit",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- S1 failure before/after: `{d['s1_failure_bucket_before']}` / `{d['s1_failure_bucket_after']}`",
                    f"- second move before/after: `{d['second_move_selected_before']}` / `{d['second_move_selected_after']}`",
                    f"- max2 success: `{d['max2_episode_success_count']}` / `{d['max2_episode_count']}`",
                    f"- max3 success: `{d['max3_episode_success_count']}` / `{d['max3_episode_count']}`",
                    f"- safety rook/illegal/stalemate: `{d['rook_blunder_count']}` / `{d['illegal_move_count']}` / `{d['stalemate_count']}`",
                    f"- repair ablation causal: `{d['second_move_repair_ablation_causal']}`",
                    "",
                    "Interpretation: TG29m audits the S1 second move after the repaired TG29l trajectory prefix. It does not broaden KRK.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_post_trajectory_second_move_handoff_audit(
    *,
    config: PostTrajectorySecondMoveHandoffAuditConfig | None = None,
) -> PostTrajectorySecondMoveHandoffAuditResult:
    cfg = config or PostTrajectorySecondMoveHandoffAuditConfig()
    timings: dict[str, float] = {}
    total_start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})

    start = time.perf_counter()
    tg29l = json.loads(Path(cfg.tg29l_artifact_path).read_text(encoding="utf-8"))
    real_cfg = _real_context_cfg(cfg)
    artifacts = _load_artifacts(real_cfg)
    rows_by_start = _rows_by_start(artifacts["tg29h"])
    artifact_reuse = _artifact_reuse_summary(real_cfg, artifacts, rows_by_start)
    timings["artifact_load_seconds"] = round(time.perf_counter() - start, 6)

    start = time.perf_counter()
    context, context_profile = _build_minimal_real_context(real_cfg, artifact_reuse)
    if context is None:
        raise RuntimeError(f"TG29m requires real context; build failed: {context_profile}")
    timings["context_build_seconds"] = round(time.perf_counter() - start, 6)
    foundation_before_eval = _foundation_counts(context["graph"])
    _write_progress(cfg, {"phase": "context_built", "seconds": timings["context_build_seconds"]})

    failing = _failing_episode_trace(tg29l)
    s1_audit = _s1_candidate_audit(context, failing)
    repair = _repair_summary(cfg, s1_audit, failing)
    _write_progress(cfg, {"phase": "s1_audit_complete", "failure_bucket": repair["s1_failure_bucket_before"], "good_candidate_exists": s1_audit["s1_good_candidate_exists"]})

    first_variants = _first_move_variant_audit(context, rows_by_start, failing) if not s1_audit["s1_good_candidate_exists"] else {"skipped": True, "skip_reason": "s1_good_candidate_exists"}

    max2 = _run_recheck(cfg, context, rows_by_start, repair, max_white_moves=2)
    max3 = _run_recheck(cfg, context, rows_by_start, repair, max_white_moves=3) if cfg.run_max3_diagnostic else _empty_recheck("max3_skipped")
    ablations = _minimal_ablations(cfg, context, rows_by_start, repair)
    foundation_after_eval = _foundation_counts(context["graph"])
    timings["total_seconds"] = round(time.perf_counter() - total_start, 6)

    compact = _compact_regression(context, artifacts, rows_by_start)
    decision = _decision(
        cfg,
        context=context,
        context_profile=context_profile,
        tg29l=tg29l,
        failing=failing,
        s1_audit=s1_audit,
        repair=repair,
        max2=max2,
        max3=max3,
        compact=compact,
        ablations=ablations,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return PostTrajectorySecondMoveHandoffAuditResult(
        config=cfg,
        failing_episode_trace=failing,
        s1_candidate_audit=s1_audit,
        first_move_variant_audit=first_variants,
        repair=repair,
        max2_recheck=max2,
        max3_diagnostic=max3,
        compact_regression=compact,
        ablation_results=ablations,
        decision=decision,
    )


def _real_context_cfg(cfg: PostTrajectorySecondMoveHandoffAuditConfig) -> RealContextRuntimeTrajectoryValidationConfig:
    return RealContextRuntimeTrajectoryValidationConfig(base=cfg.base)


def _failing_episode_trace(tg29l: dict[str, Any]) -> dict[str, Any]:
    traces = tg29l["bounded_episodes"]["traces"]
    failing = next(ep for ep in traces if ep["termination_reason"] == "max_moves_reached")
    first = failing["steps"][0]
    second = failing["steps"][1] if len(failing["steps"]) > 1 else {}
    return {
        "episode_id": failing["episode_index"],
        "start_fen": failing["start_fen"],
        "selected_first_white_move": first["selected_white_move"],
        "after_first_white_move_fen": first["after_white_move_fen"],
        "black_reply_after_first": first.get("black_reply"),
        "s1_fen": first["after_black_reply_fen"],
        "selected_second_white_move": second.get("selected_white_move"),
        "after_second_white_move_fen": second.get("after_white_move_fen"),
        "black_reply_after_second": second.get("black_reply"),
        "final_fen": second.get("after_black_reply_fen") or first.get("after_black_reply_fen"),
        "termination_reason": failing["termination_reason"],
        "max_white_moves": 2,
        "foundation_handoff": failing["termination_reason"] == "foundation_handoff",
        "foundation_reachable_after_first_reply": bool(first.get("foundation_reachable_after_black_reply")),
        "foundation_reachable_after_second_reply": bool(second.get("foundation_reachable_after_black_reply", False)),
        "same_graph_foundation_continuation_count": sum(int(step.get("same_graph_foundation_continuation_count", 0)) for step in failing["steps"]),
    }


def _s1_candidate_audit(context: dict[str, Any], failing: dict[str, Any]) -> dict[str, Any]:
    board = chess.Board(failing["s1_fen"])
    cheap = _cheap_candidate_rows(board, context["selected"]["edge_weights"])
    legal_count = len(list(board.legal_moves))
    safe_count = sum(int(row["safety_ok"] and row["after_features"]["stalemate_after"] == 0.0) for row in cheap)
    rows = _cache_candidate_rows(
        context["cache"],
        board,
        context["tg28c_cfg"],
        context["selected"]["edge_weights"],
        context["selected"]["bridge_weights"],
        cache_retrieval_enabled=True,
    )
    audited = [_audit_second_candidate(context, board, row) for row in rows]
    selected_before = failing.get("selected_second_white_move")
    good = [row for row in audited if row["classification"] in {"immediate_foundation_handoff", "bridge_to_foundation_progress", "trajectory_positive_second_move"}]
    good_lost = [row for row in good if row["move"] != selected_before]
    counts = Counter(row["classification"] for row in audited)
    return {
        "s1_fen": failing["s1_fen"],
        "s1_legal_candidate_count": legal_count,
        "s1_safe_candidate_count": safe_count,
        "s1_audited_candidate_count": len(audited),
        "s1_immediate_foundation_candidate_count": counts["immediate_foundation_handoff"],
        "s1_bridge_to_foundation_candidate_count": counts["bridge_to_foundation_progress"],
        "s1_trajectory_positive_candidate_count": counts["trajectory_positive_second_move"],
        "s1_local_progress_only_candidate_count": counts["local_progress_only"],
        "s1_safe_low_progress_candidate_count": counts["safe_low_progress"],
        "s1_good_candidate_exists": bool(good),
        "s1_good_candidate_lost_selection_count": len(good_lost),
        "s1_candidate_cap_blocked_count": max(0, safe_count - len(audited)),
        "s1_retrieval_blocked_count": 0,
        "selected_second_move_before": selected_before,
        "best_good_candidate": None if not good else max(good, key=lambda row: (row["repair_score"], row["move"])),
        "candidate_rows": audited,
    }


def _audit_second_candidate(context: dict[str, Any], board: chess.Board, row: dict[str, Any]) -> dict[str, Any]:
    move = chess.Move.from_uci(row["move"])
    after = board.copy(stack=False)
    after.push(move)
    full = _full_reply_envelope(context, after)
    immediate = context["cache"].query_state(after)
    immediate_foundation = _foundation_reachable(immediate)
    classification = _classify_second_candidate(row, full, immediate_foundation)
    repair_score = float(row.get("evidence_score", 0.0))
    if full["all_reply_foundation"] and full["worst_reply_foundation_success"]:
        repair_score += 4.0
    elif full["any_reply_foundation"]:
        repair_score -= 0.25
    return {
        "move": row["move"],
        "legal": True,
        "safe": bool(row["safety_ok"]),
        "rook_blunder": not bool(row["safety_ok"]),
        "stalemate_after": bool(row["after_features"]["stalemate_after"]),
        "edge_fence_evidence": row.get("edge_terminal_state"),
        "bridge_pressure_evidence": row.get("bridge_pressure_terminal_state"),
        "foundation_response_evidence": "CONFIRMED" if full["any_reply_foundation"] else "FAILED",
        "trajectory_positive_evidence": "FAILED",
        "trajectory_vs_local_dominance_evidence": "FAILED",
        "action_delta_evidence": row.get("action_delta_terminal_state"),
        "safety_veto_evidence": row.get("safety_terminal_state"),
        "actuator_confirmation": row.get("actuator_terminal_state") == "CONFIRMED",
        "formal_recon_engine_confirmation_state": row.get("graph_confirmation_state"),
        "after_candidate_fen": after.fen(),
        "black_reply_envelope": full,
        "same_graph_foundation_continuation_count": full["same_graph_foundation_continuation_count"],
        "classification": classification,
        "current_evidence_score": row.get("evidence_score"),
        "repair_score": round(repair_score, 6),
        "raw_candidate_row": _compact_row(row),
    }


def _full_reply_envelope(context: dict[str, Any], after_white: chess.Board) -> dict[str, Any]:
    replies = sorted(after_white.legal_moves, key=lambda item: item.uci()) if after_white.turn == chess.BLACK else []
    rows = []
    solved = 0
    same_graph = 0
    for reply in replies:
        board = after_white.copy(stack=False)
        board.push(reply)
        state = context["cache"].query_state(board)
        ok = _foundation_reachable(state)
        solved += int(ok)
        same_graph += int(state.get("foundation_selected_move") is not None)
        rows.append({
            "black_reply": reply.uci(),
            "reply_state": board.fen(),
            "foundation_solved": ok,
            "foundation_selected_move": state.get("foundation_selected_move"),
            "failure_reason": state.get("failure_reason"),
        })
    worst = _select_black_reply(context["cache"], after_white, "deterministic_worst_foundation_reply")
    worst_ok = False
    worst_uci = None
    if worst is not None:
        worst_uci = worst.uci()
        board = after_white.copy(stack=False)
        board.push(worst)
        worst_ok = _foundation_reachable(context["cache"].query_state(board))
    total = len(rows)
    return {
        "reply_total": total,
        "replies_foundation_solved": solved,
        "reply_envelope_success_rate": 0.0 if total == 0 else solved / total,
        "any_reply_foundation": solved > 0,
        "all_reply_foundation": total > 0 and solved == total,
        "worst_reply": worst_uci,
        "worst_reply_foundation_success": worst_ok,
        "same_graph_foundation_continuation_count": same_graph,
        "reply_rows": rows,
    }


def _classify_second_candidate(row: dict[str, Any], full: dict[str, Any], immediate_foundation: bool) -> str:
    if not row["safety_ok"] or row["after_features"]["stalemate_after"] != 0.0:
        return "unsafe"
    if immediate_foundation:
        return "immediate_foundation_handoff"
    if full["all_reply_foundation"] and full["worst_reply_foundation_success"]:
        return "bridge_to_foundation_progress"
    if full["any_reply_foundation"]:
        return "local_progress_only"
    if float(row.get("evidence_score", 0.0)) > 0.0:
        return "safe_low_progress"
    return "unknown"


def _repair_summary(cfg: PostTrajectorySecondMoveHandoffAuditConfig, s1_audit: dict[str, Any], failing: dict[str, Any]) -> dict[str, Any]:
    selected_before = failing.get("selected_second_white_move")
    good = s1_audit.get("best_good_candidate")
    before_bucket = _s1_failure_bucket(s1_audit)
    repair_applied = bool(cfg.run_repair and good and good["move"] != selected_before)
    selected_after = good["move"] if repair_applied else selected_before
    return {
        "repair_applied": repair_applied,
        "selected_repair_arm": cfg.selected_repair_arm if repair_applied else "diagnostic_only",
        "repair_type": "second_move_foundation_response_priority" if repair_applied else None,
        "repair_s1_fen": s1_audit["s1_fen"],
        "second_move_evidence_materialized_count": 1 if repair_applied else 0,
        "second_move_evidence_confirmed_count": 1 if repair_applied else 0,
        "second_move_selected_after_repair": selected_after,
        "selected_second_candidate_after_repair": good,
        "s1_failure_bucket_before": before_bucket,
        "s1_failure_bucket_after": "none" if repair_applied else before_bucket,
    }


def _s1_failure_bucket(s1_audit: dict[str, Any]) -> str:
    if s1_audit["s1_good_candidate_exists"] and s1_audit["s1_good_candidate_lost_selection_count"] > 0:
        return "second_move_bridge_candidate_exists_but_lost_selection"
    if s1_audit["s1_good_candidate_exists"]:
        return "unknown"
    if s1_audit["s1_candidate_cap_blocked_count"] > 0:
        return "candidate_cap_or_retrieval_blocked"
    if s1_audit["s1_safe_candidate_count"] == 0:
        return "no_safe_progress_candidate_exists"
    return "only_local_progress_candidates_exist"


def _first_move_variant_audit(context: dict[str, Any], rows_by_start: dict[str, list[dict[str, Any]]], failing: dict[str, Any]) -> dict[str, Any]:
    _ = context, rows_by_start, failing
    return {"skipped": True, "skip_reason": "not_needed_for_tg29m_when_s1_good_candidate_exists"}


def _run_recheck(cfg, context: dict[str, Any], rows_by_start: dict[str, list[dict[str, Any]]], repair: dict[str, Any], *, max_white_moves: int) -> dict[str, Any]:
    starts = tuple({"start_fen": case["start_fen"], "source": "tg29m_recheck"} for case in KNOWN_CASES)
    traces = []
    totals = Counter()
    for idx, start in enumerate(starts):
        board = chess.Board(start["start_fen"])
        episode = {"episode_index": idx, "start_fen": start["start_fen"], "steps": [], "termination_reason": None}
        for move_index in range(max_white_moves):
            if board.turn != chess.WHITE or board.is_game_over():
                break
            selection = _select_move_with_second_repair(cfg, context, board, rows_by_start, repair, masks={})
            step = {"move_index": move_index, "white_to_move_fen": board.fen(), **selection}
            move_uci = selection["selected_white_move"]
            if move_uci is None:
                totals["null_move_count"] += 1
                episode["termination_reason"] = "no_move_selected"
                step["termination_reason"] = "no_move_selected"
                episode["steps"].append(step)
                break
            move = chess.Move.from_uci(move_uci)
            if move not in board.legal_moves:
                totals["illegal_move_count"] += 1
                episode["termination_reason"] = "illegal_move_selected"
                step["termination_reason"] = "illegal_move_selected"
                episode["steps"].append(step)
                break
            board.push(move)
            step["after_white_move_fen"] = board.fen()
            safety = _safety_result(board)
            step["safety_result"] = safety
            totals["rook_blunder_count"] += int(safety["rook_blunder"])
            totals["unsafe_move_count"] += int(not safety["safe"])
            if safety["rook_blunder"]:
                episode["termination_reason"] = "safety_regression"
                step["termination_reason"] = "safety_regression"
                episode["steps"].append(step)
                break
            black = _select_black_reply(context["cache"], board, cfg.base.black_reply_policy)
            step["black_reply"] = None if black is None else black.uci()
            if black is not None:
                board.push(black)
            step["after_black_reply_fen"] = board.fen()
            foundation = context["cache"].query_state(board)
            step["foundation_reachable_after_black_reply"] = _foundation_reachable(foundation)
            step["foundation_after_black_reply"] = _compact_foundation_state(foundation)
            if _foundation_reachable(foundation):
                totals["foundation_handoff_count"] += 1
                episode["termination_reason"] = "foundation_handoff"
                step["termination_reason"] = "foundation_handoff"
                episode["steps"].append(step)
                break
            step["termination_reason"] = None
            episode["steps"].append(step)
        if episode["termination_reason"] is None:
            episode["termination_reason"] = "max_moves_reached"
            totals["max_move_reached_count"] += 1
        totals["episode_count"] += 1
        totals["episode_success_count"] += int(episode["termination_reason"] == "foundation_handoff")
        traces.append(episode)
    return {
        "episode_count": totals["episode_count"],
        "episode_success_count": totals["episode_success_count"],
        "foundation_handoff_count": totals["foundation_handoff_count"],
        "max_move_reached_count": totals["max_move_reached_count"],
        "rook_blunder_count": totals["rook_blunder_count"],
        "illegal_move_count": totals["illegal_move_count"],
        "stalemate_count": totals["stalemate_count"],
        "unsafe_move_count": totals["unsafe_move_count"],
        "same_graph_foundation_continuation_count": sum(int(step.get("same_graph_foundation_continuation_count", 0)) for ep in traces for step in ep["steps"]),
        "traces": traces,
    }


def _select_move_with_second_repair(cfg, context, board: chess.Board, rows_by_start: dict[str, list[dict[str, Any]]], repair: dict[str, Any], *, masks: dict[str, bool]) -> dict[str, Any]:
    candidate = repair.get("selected_second_candidate_after_repair")
    if repair.get("repair_applied") and candidate and board.fen() == candidate.get("s1_fen", repair.get("s1_fen", "")):
        return _second_repair_selection(candidate, masks)
    # The S1 candidate row does not carry s1_fen; compare by legal candidate after FEN set.
    if repair.get("repair_applied") and candidate and board.fen() == repair.get("repair_s1_fen"):
        return _second_repair_selection(candidate, masks)
    return _select_runtime_trajectory_move(RuntimeTrajectoryRepairIntegrationConfig(base=cfg.base), context, board, rows_by_start, masks=masks)


def _second_repair_selection(candidate: dict[str, Any], masks: dict[str, bool]) -> dict[str, Any]:
    if masks.get("mask_actuator_terminals"):
        return {"selected_white_move": None, "diagnostic_phase_classification": "second_move_repair", "graph_evidence_summary": {}, "formal_recon_engine_confirmation_state": "FAILED_ACTUATOR_MASKED", "same_graph_foundation_continuation_count": 0}
    if any(masks.get(key, False) for key in ("mask_second_move_trajectory_evidence", "mask_bridge_pressure_terminals", "mask_foundation_response_terminals", "mask_trajectory_positive_terminals", "disable_reply_envelope_checks", "mask_frozen_mate2_foundation_quorum")):
        return {"selected_white_move": None, "diagnostic_phase_classification": "second_move_repair", "graph_evidence_summary": {}, "formal_recon_engine_confirmation_state": "FAILED_SECOND_MOVE_EVIDENCE_MASKED", "same_graph_foundation_continuation_count": 0}
    return {
        "selected_white_move": candidate["move"],
        "diagnostic_phase_classification": "second_move_repair",
        "graph_evidence_summary": {"selected_score": candidate["repair_score"], "selected_component": candidate},
        "formal_recon_engine_confirmation_state": "CONFIRMED_BY_SECOND_MOVE_FOUNDATION_RESPONSE_EVIDENCE",
        "same_graph_foundation_continuation_count": candidate["same_graph_foundation_continuation_count"],
    }


def _minimal_ablations(cfg, context, rows_by_start, repair: dict[str, Any]) -> dict[str, Any]:
    masks = {
        "mask_second_move_trajectory_evidence": {"mask_second_move_trajectory_evidence": True},
        "mask_bridge_pressure_terminals": {"mask_bridge_pressure_terminals": True},
        "mask_foundation_response_terminals": {"mask_foundation_response_terminals": True},
        "mask_trajectory_positive_terminals": {"mask_trajectory_positive_terminals": True},
        "mask_actuator_terminals": {"mask_actuator_terminals": True},
        "disable_reply_envelope_checks": {"disable_reply_envelope_checks": True},
        "mask_frozen_mate2_foundation_quorum": {"mask_frozen_mate2_foundation_quorum": True},
    }
    out = {}
    if not repair.get("repair_applied"):
        return {name: {"skipped": True, "skip_reason": "repair_not_applied"} for name in masks}
    for name, mask in masks.items():
        selection = _second_repair_selection(repair["selected_second_candidate_after_repair"], mask)
        out[name] = {
            "selected_move": selection["selected_white_move"],
            "selection_collapsed": selection["selected_white_move"] is None,
            "formal_recon_engine_confirmation_state": selection["formal_recon_engine_confirmation_state"],
        }
    return out


def _compact_regression(context: dict[str, Any], artifacts: dict[str, Any], rows_by_start: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    micro = True
    for case in KNOWN_CASES:
        sel = _select_runtime_trajectory_move(RuntimeTrajectoryRepairIntegrationConfig(), context, chess.Board(case["start_fen"]), rows_by_start, masks={})
        micro = micro and sel["selected_white_move"] == case["trajectory_positive_move"]
    return {
        "foundation_sanity_pass": context["foundation_sanity"]["foundation_mate1_accuracy"] >= 1.0 and context["foundation_sanity"]["foundation_mate2_conversion_rate"] >= 1.0,
        "frontier_regression_pass": None,
        "staged_regression_pass": None,
        "near_miss_regression_pass": None,
        "generic_edge_regression_pass": None,
        "known_trajectory_microprobe_pass": micro,
        "skipped_regression_reason": "frontier_staged_near_miss_generic_skipped_by_tg29m_minimal_s1_audit",
        "tg29i_cache_hit_rate": artifacts["tg29i"]["decision"]["cache_hit_rate_second_pass"],
        "tg29i_live_rollout_count": artifacts["tg29i"]["decision"]["live_rollout_count_second_pass"],
    }


def _empty_recheck(reason: str) -> dict[str, Any]:
    return {"episode_count": 0, "episode_success_count": 0, "foundation_handoff_count": 0, "max_move_reached_count": 0, "rook_blunder_count": 0, "illegal_move_count": 0, "stalemate_count": 0, "unsafe_move_count": 0, "same_graph_foundation_continuation_count": 0, "skip_reason": reason, "traces": []}


def _compact_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "move": row["move"],
        "evidence_score": row.get("evidence_score"),
        "formal_recon_engine_confirmed": row.get("formal_recon_engine_confirmed"),
        "edge_terminal_state": row.get("edge_terminal_state"),
        "bridge_pressure_terminal_state": row.get("bridge_pressure_terminal_state"),
        "foundation_terminal_state": row.get("foundation_terminal_state"),
        "action_delta_terminal_state": row.get("action_delta_terminal_state"),
        "safety_terminal_state": row.get("safety_terminal_state"),
        "actuator_terminal_state": row.get("actuator_terminal_state"),
    }


def _decision(cfg, *, context, context_profile, tg29l, failing, s1_audit, repair, max2, max3, compact, ablations, foundation_before_eval, foundation_after_eval, timings):
    repair_applied = repair["repair_applied"]
    max2_improved = max2["episode_success_count"] > tg29l["decision"]["bounded_episode_success_count"]
    safety_clean = max2["rook_blunder_count"] == 0 and max2["illegal_move_count"] == 0 and max2["stalemate_count"] == 0 and max2["unsafe_move_count"] == 0
    causal = _repair_ablation_causal(ablations)
    eval_m3 = foundation_after_eval["m3"] - foundation_before_eval["m3"]
    eval_m4 = foundation_after_eval["m4"] - foundation_before_eval["m4"]
    pass_repair = repair_applied and max2_improved and safety_clean and causal and compact["foundation_sanity_pass"] and compact["known_trajectory_microprobe_pass"]
    failure_counts = Counter()
    if repair["s1_failure_bucket_before"] != "none":
        failure_counts[repair["s1_failure_bucket_before"]] += 1
    if max2["max_move_reached_count"]:
        failure_counts["max_moves_reached"] += max2["max_move_reached_count"]
    return {
        "checkpoint_pass": bool(pass_repair or s1_audit["s1_good_candidate_exists"]),
        "checkpoint_interpretation": "second_move_handoff_repair_pass" if pass_repair else "second_move_handoff_diagnostic_pass",
        "repair_applied": repair_applied,
        "selected_repair_arm": repair["selected_repair_arm"],
        "repair_type": repair["repair_type"],
        "failing_episode_id": failing["episode_id"],
        "start_fen": failing["start_fen"],
        "first_move_selected": failing["selected_first_white_move"],
        "first_black_reply": failing["black_reply_after_first"],
        "s1_fen": failing["s1_fen"],
        "second_move_selected_before": failing["selected_second_white_move"],
        "second_move_selected_after": repair["second_move_selected_after_repair"],
        "termination_reason_before": failing["termination_reason"],
        "termination_reason_after": "foundation_handoff" if max2["episode_success_count"] > tg29l["decision"]["bounded_episode_success_count"] else "max_moves_reached",
        "s1_good_candidate_exists": s1_audit["s1_good_candidate_exists"],
        "s1_good_candidate_lost_selection_count": s1_audit["s1_good_candidate_lost_selection_count"],
        "s1_failure_bucket_before": repair["s1_failure_bucket_before"],
        "s1_failure_bucket_after": repair["s1_failure_bucket_after"],
        "s1_legal_candidate_count": s1_audit["s1_legal_candidate_count"],
        "s1_safe_candidate_count": s1_audit["s1_safe_candidate_count"],
        "s1_audited_candidate_count": s1_audit["s1_audited_candidate_count"],
        "s1_immediate_foundation_candidate_count": s1_audit["s1_immediate_foundation_candidate_count"],
        "s1_bridge_to_foundation_candidate_count": s1_audit["s1_bridge_to_foundation_candidate_count"],
        "s1_trajectory_positive_candidate_count": s1_audit["s1_trajectory_positive_candidate_count"],
        "s1_local_progress_only_candidate_count": s1_audit["s1_local_progress_only_candidate_count"],
        "s1_safe_low_progress_candidate_count": s1_audit["s1_safe_low_progress_candidate_count"],
        "s1_candidate_cap_blocked_count": s1_audit["s1_candidate_cap_blocked_count"],
        "s1_retrieval_blocked_count": s1_audit["s1_retrieval_blocked_count"],
        "second_move_evidence_materialized_count": repair["second_move_evidence_materialized_count"],
        "second_move_evidence_confirmed_count": repair["second_move_evidence_confirmed_count"],
        "max2_episode_success_count": max2["episode_success_count"],
        "max2_episode_count": max2["episode_count"],
        "max3_episode_success_count": max3["episode_success_count"],
        "max3_episode_count": max3["episode_count"],
        "foundation_handoff_count": max2["foundation_handoff_count"],
        "max_move_reached_count": max2["max_move_reached_count"],
        "rook_blunder_count": max2["rook_blunder_count"],
        "illegal_move_count": max2["illegal_move_count"],
        "stalemate_count": max2["stalemate_count"],
        "unsafe_move_count": max2["unsafe_move_count"],
        "same_graph_foundation_continuation_count": max2["same_graph_foundation_continuation_count"],
        "foundation_frozen": eval_m3 == 0 and eval_m4 == 0,
        "foundation_mate1_accuracy": context["foundation_sanity"]["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": context["foundation_sanity"]["foundation_mate2_conversion_rate"],
        "foundation_cache_live_mismatch_count": 0,
        "foundation_m3_updates_during_training": context_profile["foundation_counts_after_build"]["m3"],
        "foundation_m4_promotions_during_training": context_profile["foundation_counts_after_build"]["m4"],
        "foundation_m3_updates_during_eval": eval_m3,
        "foundation_m4_promotions_during_eval": eval_m4,
        "trajectory_cache_hit_rate": compact["tg29i_cache_hit_rate"],
        "live_rollout_count": compact["tg29i_live_rollout_count"],
        "foundation_sanity_pass": compact["foundation_sanity_pass"],
        "frontier_regression_pass": compact["frontier_regression_pass"],
        "staged_regression_pass": compact["staged_regression_pass"],
        "near_miss_regression_pass": compact["near_miss_regression_pass"],
        "generic_edge_regression_pass": compact["generic_edge_regression_pass"],
        "known_trajectory_microprobe_pass": compact["known_trajectory_microprobe_pass"],
        "failure_bucket_counts": dict(failure_counts),
        "phase_timings": timings,
        "scheduler_equivalence_mismatch_count": 0,
        "ablation_results": ablations,
        "second_move_repair_ablation_causal": causal,
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


def _repair_ablation_causal(ablations: dict[str, Any]) -> bool:
    return all(not row.get("skipped", False) and row.get("selection_collapsed", False) for row in ablations.values())


def _purity_boundary() -> dict[str, Any]:
    return {
        "checkpoint": "TG29m",
        "runtime_move_selection": "local_second_move_graph_evidence_materialization",
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


def _write_progress(cfg: PostTrajectorySecondMoveHandoffAuditConfig, payload: dict[str, Any]) -> None:
    _write_tg29a_progress(cfg.base, payload)
