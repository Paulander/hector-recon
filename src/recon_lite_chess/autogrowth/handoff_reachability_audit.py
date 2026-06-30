"""TG47g frozen-foundation handoff reachability audit."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import gzip
import json
from pathlib import Path
import time
from typing import Any, Iterable

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState

from .clean_edge_fence_stage import (
    DEFAULT_TG46D_DIR,
    _choose_stage_move,
    _clear_foundation_diagnostic_caches,
    _confinement_area,
    _file_sha256,
    _graded_progress_class,
    _graded_progress_score,
    _load_json,
    _rook_capturable_by_reply,
    _stage_graded_success,
    _stage_success,
    _write_json,
    _write_jsonl_gzip,
)
from .features import extract_learner_features
from .real_clean_slate_foundation import _git_head
from .terminal_substrate import TerminalAffordanceLearner


DEFAULT_TG47F_DIR = Path("reports/autogrowth/clean_slate_krk/tg47f_edge_fence_continuation_handoff")
DEFAULT_OUTPUT_DIR = Path("reports/autogrowth/clean_slate_krk/tg47g_handoff_reachability_audit")


@dataclass(frozen=True)
class HandoffReachabilityAuditConfig:
    checkpoint_name: str = "TG47g_handoff_reachability_audit"
    schema_version: str = "krk_tg47g_handoff_reachability_audit.v0"
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    output_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg47g_handoff_reachability_audit.json")
    markdown_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg47g_handoff_reachability_audit.md")
    audit_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg47g_handoff_audit.jsonl.gz")
    boundary_failure_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg47g_boundary_failures.jsonl.gz")
    parent_foundation_artifact_path: str = str(DEFAULT_TG46D_DIR / "promoted_tg46d_foundation.json")
    parent_foundation_m4_audit_path: str = str(DEFAULT_TG46D_DIR / "pools" / "tg46d_m4_audit.jsonl.gz")
    source_tg47f_artifact_path: str = str(DEFAULT_TG47F_DIR / "krk_tg47f_edge_fence_continuation_handoff.json")
    source_tg47f_eval_trace_path: str = str(DEFAULT_TG47F_DIR / "pools" / "tg47f_eval_traces.jsonl.gz")
    source_tg47f_m4_audit_path: str = str(DEFAULT_TG47F_DIR / "pools" / "tg47f_m4_audit.jsonl.gz")
    max_positions: int | None = None
    selected_second_move_cap: int = 3
    oracle_first_move_cap: int = 3
    oracle_second_move_cap: int = 3


@dataclass(frozen=True)
class HandoffReachabilityAuditResult:
    config: HandoffReachabilityAuditConfig
    payload: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.config.schema_version,
            "checkpoint": self.config.checkpoint_name,
            "config": asdict(self.config),
            **self.payload,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path | None = None) -> Path:
        output = Path(path or self.config.output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_handoff_reachability_audit(*, config: HandoffReachabilityAuditConfig) -> HandoffReachabilityAuditResult:
    start = time.perf_counter()
    _clear_foundation_diagnostic_caches()
    parent_artifact = _load_json(config.parent_foundation_artifact_path)
    parent_hash = _file_sha256(config.parent_foundation_artifact_path)
    parent = _reconstruct_parent_foundation_from_m4_audit(
        parent_artifact=parent_artifact,
        parent_m4_audit_path=config.parent_foundation_m4_audit_path,
    )
    parent_before = _foundation_artifact_sanity(parent_artifact, parent)
    edge_learner = _reconstruct_m4_edge_learner(config.source_tg47f_m4_audit_path)
    input_rows = _load_audit_input_rows(config)
    metric_cache: dict[tuple[str, str], dict[str, Any]] = {}
    response_cache: dict[str, dict[str, Any]] = {}
    audit_rows = [
        _audit_position(
            index=index,
            row=row,
            parent=parent,
            edge_learner=edge_learner,
            metric_cache=metric_cache,
            response_cache=response_cache,
            selected_second_move_cap=config.selected_second_move_cap,
            oracle_first_move_cap=config.oracle_first_move_cap,
            oracle_second_move_cap=config.oracle_second_move_cap,
        )
        for index, row in enumerate(input_rows)
    ]
    parent_after = _foundation_artifact_sanity(parent_artifact, parent)
    boundary_rows = [row for row in audit_rows if row["blocker_classification"] != "reachable_with_selected_first"]
    _write_jsonl_gzip(config.audit_trace_path, audit_rows)
    _write_jsonl_gzip(config.boundary_failure_path, boundary_rows)
    decision = _decision(
        config=config,
        parent_hash=parent_hash,
        parent_before=parent_before,
        parent_after=parent_after,
        audit_rows=audit_rows,
        edge_learner=edge_learner,
        total_seconds=round(time.perf_counter() - start, 6),
    )
    payload = {
        "provenance": {
            "git_head": _git_head(),
            "parent_foundation_artifact": config.parent_foundation_artifact_path,
            "parent_foundation_hash": parent_hash,
            "parent_foundation_m4_audit": config.parent_foundation_m4_audit_path,
            "source_tg47f_artifact": config.source_tg47f_artifact_path,
            "source_tg47f_eval_trace": config.source_tg47f_eval_trace_path,
            "source_tg47f_m4_audit": config.source_tg47f_m4_audit_path,
            "input_source": "tg47f_generated_fens_audit_only",
            "old_tg_pools_loaded": 0,
            "old_canary_loaded": False,
            "child_branch_loaded": False,
            "boundary_pool_loaded": False,
        },
        "parent_foundation": {
            "frozen": True,
            "sanity_before": parent_before,
            "sanity_after": parent_after,
            "m3_delta_during_audit": 0,
            "m4_delta_during_audit": 0,
        },
        "edge_fence_m4": {
            "terminal_count": len(edge_learner.terminals),
            "m3_update_delta_during_audit": 0,
            "m4_promotion_delta_during_audit": 0,
        },
        "cache_summary": {
            "move_metric_cache_entries": len(metric_cache),
            "foundation_response_cache_entries": len(response_cache),
        },
        "artifact_paths": {
            "main": config.output_path,
            "markdown": config.markdown_path,
            "audit_traces": config.audit_trace_path,
            "boundary_failures": config.boundary_failure_path,
        },
        "purity_boundary": _purity_boundary(),
        "audit_summary": _strip_audit_rows(audit_rows),
        "timing": {"total_seconds": decision["total_seconds"]},
    }
    result = HandoffReachabilityAuditResult(config=config, payload=payload, decision=decision)
    result.write_json(config.output_path)
    _write_markdown(config.markdown_path, result)
    _clear_foundation_diagnostic_caches()
    return result


def _load_audit_input_rows(config: HandoffReachabilityAuditConfig) -> list[dict[str, Any]]:
    rows = []
    seen: set[tuple[str, str]] = set()
    for row in _read_jsonl_gzip(config.source_tg47f_eval_trace_path):
        if row.get("trace_type") not in {"edge_fence_M4_only", "edge_fence_M4_regression", "decoy_eval"}:
            continue
        key = (row["fen"], row["family"])
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "fen": row["fen"],
            "family": row["family"],
            "split": row.get("split") or _split_from_trace_type(row.get("trace_type", "")),
            "lineage_key": row.get("lineage_key"),
            "source_trace_type": row.get("trace_type"),
            "source_binary_success": row.get("success"),
            "source_graded_success": row.get("graded_success"),
            "source_selected": row.get("selected"),
        })
    if config.max_positions is not None:
        rows = rows[: config.max_positions]
    return rows


def _split_from_trace_type(trace_type: str) -> str:
    if trace_type == "edge_fence_M4_regression":
        return "regression"
    if trace_type == "decoy_eval":
        return "decoy"
    return "heldout"


def _reconstruct_m4_edge_learner(path: str | Path) -> TerminalAffordanceLearner:
    learner = TerminalAffordanceLearner.create(eta_m3=0.08, rich_feature_credit_scale=0.25)
    for row in _read_jsonl_gzip(path):
        if not row.get("promoted"):
            continue
        terminal = learner.get_terminal(row["terminal_key"])
        terminal.local_weight = float(row["local_weight"])
        terminal.positive_credit = int(row["positive_intervention_count"])
        terminal.negative_credit = int(row["negative_intervention_count"])
        terminal.neutral_credit = int(row["neutral_count"])
        terminal.cell.state = StemCellState.MATURE
    return learner


def _reconstruct_parent_foundation_from_m4_audit(
    *,
    parent_artifact: dict[str, Any],
    parent_m4_audit_path: str | Path,
) -> dict[str, TerminalAffordanceLearner]:
    mate1_keys = set(parent_artifact["promoted_mate1_terminal_keys"])
    mate2_first_keys = set(parent_artifact["promoted_mate2_first_terminal_keys"])
    mate1 = TerminalAffordanceLearner.create(eta_m3=0.08, rich_feature_credit_scale=0.25)
    mate2_first = TerminalAffordanceLearner.create(eta_m3=0.08, rich_feature_credit_scale=0.25)
    for row in _read_jsonl_gzip(parent_m4_audit_path):
        if not row.get("promoted"):
            continue
        terminal_key = row["terminal_key"]
        subgraph = row.get("subgraph")
        if subgraph == "mate1_continuation_evidence" and terminal_key in mate1_keys:
            _install_promoted_terminal(mate1, row)
        elif subgraph == "mate2_first_move_evidence" and terminal_key in mate2_first_keys:
            _install_promoted_terminal(mate2_first, row)
    if set(mate1.terminals) != mate1_keys:
        missing = sorted(mate1_keys - set(mate1.terminals))[:5]
        raise ValueError(f"missing promoted mate1 terminals from TG46d M4 audit: {missing}")
    if set(mate2_first.terminals) != mate2_first_keys:
        missing = sorted(mate2_first_keys - set(mate2_first.terminals))[:5]
        raise ValueError(f"missing promoted mate2-first terminals from TG46d M4 audit: {missing}")
    return {"mate1": mate1, "mate2_first": mate2_first}


def _install_promoted_terminal(learner: TerminalAffordanceLearner, row: dict[str, Any]) -> None:
    terminal = learner.get_terminal(row["terminal_key"])
    terminal.local_weight = float(row["local_weight"])
    terminal.positive_credit = int(row["positive_intervention_count"])
    terminal.negative_credit = int(row["negative_intervention_count"])
    terminal.neutral_credit = int(row["neutral_count"])
    terminal.cell.state = StemCellState.MATURE


def _foundation_artifact_sanity(
    parent_artifact: dict[str, Any],
    parent: dict[str, TerminalAffordanceLearner],
) -> dict[str, Any]:
    mate1_accuracy = float(parent_artifact["m4_only_mate1_regression_accuracy"])
    mate2_heldout = float(parent_artifact["m4_only_mate2_heldout_conversion"])
    mate2_regression = float(parent_artifact["m4_only_mate2_regression_conversion"])
    mate1_count = len(parent["mate1"].terminals)
    mate2_count = len(parent["mate2_first"].terminals)
    expected_mate1 = len(parent_artifact["promoted_mate1_terminal_keys"])
    expected_mate2 = len(parent_artifact["promoted_mate2_first_terminal_keys"])
    return {
        "pass": (
            mate1_accuracy >= 0.99
            and mate2_heldout >= 0.75
            and mate2_regression >= 0.75
            and mate1_count == expected_mate1
            and mate2_count == expected_mate2
        ),
        "mate1_regression_accuracy": mate1_accuracy,
        "mate2_heldout_conversion_rate": mate2_heldout,
        "mate2_regression_conversion_rate": mate2_regression,
        "mate2_all_reply_conversion_rate": mate2_heldout,
        "mate2_one_reply_false_positive_count": 0,
        "mate1_terminal_count": mate1_count,
        "mate2_first_terminal_count": mate2_count,
        "sanity_source": "tg46d_promoted_artifact_and_m4_audit_contract",
    }


def _audit_position(
    *,
    index: int,
    row: dict[str, Any],
    parent: dict[str, TerminalAffordanceLearner],
    edge_learner: TerminalAffordanceLearner,
    metric_cache: dict[tuple[str, str], dict[str, Any]],
    response_cache: dict[str, dict[str, Any]],
    selected_second_move_cap: int,
    oracle_first_move_cap: int,
    oracle_second_move_cap: int,
) -> dict[str, Any]:
    board = chess.Board(row["fen"])
    selected_first = _choose_stage_move(board, parent=parent, edge_learner=edge_learner)
    selected_metrics = _cached_move_metrics(
        board,
        selected_first,
        parent=parent,
        metric_cache=metric_cache,
        response_cache=response_cache,
    )
    selected_envelope = _audit_first_move(
        board,
        selected_first,
        parent=parent,
        family=row["family"],
        first_move_kind="selected",
        metric_cache=metric_cache,
        response_cache=response_cache,
        second_move_cap=selected_second_move_cap,
    )
    oracle = _oracle_first_move_audit(
        board,
        parent=parent,
        family=row["family"],
        metric_cache=metric_cache,
        response_cache=response_cache,
        first_move_cap=oracle_first_move_cap,
        second_move_cap=oracle_second_move_cap,
    )
    blocker = classify_blocker(
        family=row["family"],
        selected=selected_envelope,
        oracle=oracle,
    )
    return {
        "audit_id": f"tg47g_{index:04d}",
        **row,
        "selected_first_move": None if selected_first is None else selected_first.uci(),
        "selected_first_metrics": selected_metrics,
        "selected_first_audit": selected_envelope,
        "oracle_first_audit": oracle,
        "blocker_classification": blocker,
        "decoy_partial_handoff_leak": row["family"] in ("decoy_edge", "hard_decoy_edge") and (
            selected_envelope["has_partial_second_support"] or oracle["has_partial_second_support"]
        ),
        "decoy_all_reply_handoff_leak": row["family"] in ("decoy_edge", "hard_decoy_edge") and (
            selected_envelope["all_reply_second_handoff"] or oracle["all_reply_second_handoff"]
        ),
    }


def _audit_first_move(
    board: chess.Board,
    first: chess.Move | None,
    *,
    parent: dict[str, TerminalAffordanceLearner],
    family: str,
    first_move_kind: str,
    metric_cache: dict[tuple[str, str], dict[str, Any]],
    response_cache: dict[str, dict[str, Any]],
    second_move_cap: int | None,
) -> dict[str, Any]:
    if first is None or first not in board.legal_moves:
        return _empty_first_audit(first_move_kind=first_move_kind, first_move=None, reason="no_legal_first_move")
    first_metrics = _cached_move_metrics(
        board,
        first,
        parent=parent,
        metric_cache=metric_cache,
        response_cache=response_cache,
    )
    if _unsafe(first_metrics):
        return _empty_first_audit(
            first_move_kind=first_move_kind,
            first_move=first.uci(),
            reason="unsafe_first_move",
            first_metrics=first_metrics,
        )
    after_first = board.copy(stack=False)
    after_first.push(first)
    reply_rows = []
    for reply_index, reply in enumerate(sorted(after_first.legal_moves, key=lambda item: item.uci())):
        state = after_first.copy(stack=False)
        state.push(reply)
        second_moves = list(sorted(state.legal_moves, key=lambda item: item.uci()))
        total_second_moves = len(second_moves)
        if second_move_cap is not None:
            second_moves = _ranked_legal_moves(state, cap=second_move_cap)
        second_rows = [
            _audit_second_move(
                state,
                second,
                parent=parent,
                family=family,
                metric_cache=metric_cache,
                response_cache=response_cache,
            )
            for second in second_moves
        ]
        safe_all = [item for item in second_rows if item["safe"] and item["all_reply_foundation_handoff"]]
        safe_partial = [item for item in second_rows if item["safe"] and item["partial_reply_foundation_support"]]
        best = _best_second(second_rows)
        reply_rows.append({
            "reply_index": reply_index,
            "black_reply": reply.uci(),
            "successor_fen": state.fen(),
            "legal_second_count": total_second_moves,
            "audited_second_count": len(second_rows),
            "second_move_cap": second_move_cap,
            "second_move_audit_capped": bool(second_move_cap is not None and total_second_moves > len(second_rows)),
            "safe_second_count": sum(int(item["safe"]) for item in second_rows),
            "safe_all_reply_handoff_second_count": len(safe_all),
            "safe_partial_support_second_count": len(safe_partial),
            "has_safe_all_reply_handoff_second": bool(safe_all),
            "has_safe_partial_support_second": bool(safe_partial),
            "best_second": best,
        })
    reply_total = len(reply_rows)
    replies_with_all = sum(int(item["has_safe_all_reply_handoff_second"]) for item in reply_rows)
    replies_with_partial = sum(int(item["has_safe_partial_support_second"]) for item in reply_rows)
    return {
        "first_move_kind": first_move_kind,
        "first_move": first.uci(),
        "first_safe": True,
        "first_binary_success": _stage_success(first_metrics, family),
        "first_graded_success": _stage_graded_success(first_metrics, family),
        "first_metrics": first_metrics,
        "reply_total": reply_total,
        "replies_with_safe_all_reply_second_handoff": replies_with_all,
        "replies_with_safe_partial_second_support": replies_with_partial,
        "all_reply_second_handoff": bool(reply_total > 0 and replies_with_all == reply_total),
        "any_reply_second_handoff": bool(replies_with_all > 0),
        "has_partial_second_support": bool(replies_with_partial > 0),
        "reply_envelope_success_rate": 0.0 if reply_total == 0 else replies_with_all / reply_total,
        "unsafe_second_required": bool(reply_total > 0 and any(item["safe_second_count"] == 0 for item in reply_rows)),
        "reply_rows": reply_rows,
    }


def _empty_first_audit(
    *,
    first_move_kind: str,
    first_move: str | None,
    reason: str,
    first_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "first_move_kind": first_move_kind,
        "first_move": first_move,
        "first_safe": False,
        "first_binary_success": False,
        "first_graded_success": False,
        "first_metrics": first_metrics or {},
        "blocked_reason": reason,
        "reply_total": 0,
        "replies_with_safe_all_reply_second_handoff": 0,
        "replies_with_safe_partial_second_support": 0,
        "all_reply_second_handoff": False,
        "any_reply_second_handoff": False,
        "has_partial_second_support": False,
        "reply_envelope_success_rate": 0.0,
        "unsafe_second_required": False,
        "reply_rows": [],
    }


def _oracle_first_move_audit(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner],
    family: str,
    metric_cache: dict[tuple[str, str], dict[str, Any]],
    response_cache: dict[str, dict[str, Any]],
    first_move_cap: int,
    second_move_cap: int,
) -> dict[str, Any]:
    candidates = []
    all_first = list(sorted(board.legal_moves, key=lambda item: item.uci()))
    audited_first = _ranked_legal_moves(board, cap=first_move_cap)
    for first in audited_first:
        first_metrics = _cached_move_metrics(
            board,
            first,
            parent=parent,
            metric_cache=metric_cache,
            response_cache=response_cache,
        )
        if _unsafe(first_metrics):
            continue
        audit = _audit_first_move(
            board,
            first,
            parent=parent,
            family=family,
            first_move_kind="oracle_candidate",
            metric_cache=metric_cache,
            response_cache=response_cache,
            second_move_cap=second_move_cap,
        )
        candidates.append(audit)
    candidates.sort(
        key=lambda item: (
            int(item["all_reply_second_handoff"]),
            item["reply_envelope_success_rate"],
            int(item["any_reply_second_handoff"]),
            int(item["has_partial_second_support"]),
            item["first_move"] or "",
        ),
        reverse=True,
    )
    best = candidates[0] if candidates else _empty_first_audit(
        first_move_kind="oracle_candidate",
        first_move=None,
        reason="no_safe_first_move",
    )
    return {
        "safe_first_candidate_count": len(candidates),
        "legal_first_candidate_count": len(all_first),
        "audited_first_candidate_count": len(audited_first),
        "first_move_cap": first_move_cap,
        "second_move_cap": second_move_cap,
        "oracle_audit_capped": bool(len(all_first) > len(audited_first) or second_move_cap is not None),
        "all_reply_second_handoff": best["all_reply_second_handoff"],
        "any_reply_second_handoff": best["any_reply_second_handoff"],
        "has_partial_second_support": best["has_partial_second_support"],
        "reply_envelope_success_rate": best["reply_envelope_success_rate"],
        "best_first_move": best["first_move"],
        "best_first_audit": _strip_reply_rows(best),
    }


def _audit_second_move(
    board: chess.Board,
    second: chess.Move,
    *,
    parent: dict[str, TerminalAffordanceLearner],
    family: str,
    metric_cache: dict[tuple[str, str], dict[str, Any]],
    response_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    metrics = _cached_move_metrics(
        board,
        second,
        parent=parent,
        metric_cache=metric_cache,
        response_cache=response_cache,
    )
    after_second = board.copy(stack=False)
    after_second.push(second)
    responses = _cached_foundation_response_details(after_second, parent, response_cache=response_cache)
    safe = not _unsafe(metrics)
    return {
        "second_move": second.uci(),
        "safe": safe,
        "all_reply_foundation_handoff": bool(safe and metrics["all_reply_handoff"]),
        "partial_reply_foundation_support": bool(safe and metrics["partial_reply_handoff"]),
        "mate1_foundation_response": responses["mate1_foundation_response"],
        "mate2_first_foundation_response": responses["mate2_first_foundation_response"],
        "graded_success": _stage_graded_success(metrics, family),
        "graded_progress_score": metrics["graded_progress_score"],
        "graded_progress_class": metrics["graded_progress_class"],
        "rook_risk": metrics["rook_risk"],
        "rook_missing": metrics.get("rook_missing", False),
        "stalemate": metrics["stalemate"],
        "confinement_regression": metrics["confinement_regressed"],
        "after_second_fen": after_second.fen(),
    }


def _ranked_legal_moves(board: chess.Board, *, cap: int) -> list[chess.Move]:
    ranked = sorted(
        ((_cheap_progress_tuple(board, move), move.uci(), move) for move in board.legal_moves),
        reverse=True,
    )
    return [move for _score, _uci, move in ranked[:cap]]


def _cheap_progress_tuple(board: chess.Board, move: chess.Move) -> tuple[int, float, int, int, int]:
    after = board.copy(stack=False)
    after.push(move)
    before_f = extract_learner_features(board)
    after_f = extract_learner_features(after)
    before_area = _confinement_area(board)
    after_area = _confinement_area(after)
    rook_risk = _rook_capturable_by_reply(after)
    rook_missing = not bool(after.pieces(chess.ROOK, chess.WHITE))
    stalemate = after.is_stalemate()
    confinement_delta = before_area - after_area
    mobility_delta = before_f["black_reply_mobility"] - after_f["black_reply_mobility"]
    edge_delta = before_f["black_king_nearest_edge_distance"] - after_f["black_king_nearest_edge_distance"]
    king_delta = before_f["white_king_to_black_king_distance"] - after_f["white_king_to_black_king_distance"]
    safe = not (rook_risk or rook_missing or stalemate or confinement_delta < 0)
    progress = 0.0
    progress += 0.30 if confinement_delta > 0 else 0.0
    progress += 0.16 if edge_delta > 0 else 0.0
    progress += 0.14 if mobility_delta > 0 else 0.0
    progress += 0.08 if king_delta > 0 and confinement_delta >= 0 else 0.0
    return (int(safe), progress, confinement_delta, mobility_delta, edge_delta)


def _cached_move_metrics(
    board: chess.Board,
    move: chess.Move | None,
    *,
    parent: dict[str, TerminalAffordanceLearner],
    metric_cache: dict[tuple[str, str], dict[str, Any]],
    response_cache: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    key = (board.fen(), "" if move is None else move.uci())
    cached = metric_cache.get(key)
    if cached is None:
        cached = _graph_basin_move_metrics(
            board,
            move,
            parent=parent,
            response_cache={} if response_cache is None else response_cache,
        )
        metric_cache[key] = cached
    return cached


def _graph_basin_move_metrics(
    board: chess.Board,
    move: chess.Move | None,
    *,
    parent: dict[str, TerminalAffordanceLearner],
    response_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if move is None or move not in board.legal_moves:
        return {
            "illegal": True,
            "rook_risk": False,
            "rook_missing": False,
            "stalemate": False,
            "success_signal": 0.0,
            "graded_progress_score": -1.0,
            "graded_progress_class": "illegal_or_missing_move",
            "low_progress": True,
            "all_reply_handoff": False,
            "partial_reply_handoff": False,
            "confinement_improved": False,
            "confinement_regressed": False,
            "black_mobility_reduced": False,
            "rook_safe": False,
            "safe_confinement_progress": False,
            "safe_mobility_progress": False,
            "safe_edge_progress": False,
        }
    after = board.copy(stack=False)
    after.push(move)
    before_f = extract_learner_features(board)
    after_f = extract_learner_features(after)
    before_area = _confinement_area(board)
    after_area = _confinement_area(after)
    responses = _cached_foundation_response_details(after, parent, response_cache=response_cache)
    any_handoff = bool(responses["mate1_foundation_response"] or responses["mate2_first_foundation_response"])
    all_handoff = bool(responses["all_reply_graph_foundation_response"])
    rook_risk = _rook_capturable_by_reply(after)
    rook_missing = not bool(after.pieces(chess.ROOK, chess.WHITE))
    stalemate = after.is_stalemate()
    confinement_improved = after_area < before_area
    confinement_regressed = after_area > before_area
    mobility_reduced = after_f["black_reply_mobility"] < before_f["black_reply_mobility"]
    edge_progress = after_f["black_king_nearest_edge_distance"] < before_f["black_king_nearest_edge_distance"]
    king_approach = after_f["white_king_to_black_king_distance"] < before_f["white_king_to_black_king_distance"]
    rook_safe = not rook_risk and not rook_missing
    success_signal = sum([confinement_improved, mobility_reduced, edge_progress, all_handoff]) - sum([rook_risk, stalemate, confinement_regressed])
    graded_progress_score = _graded_progress_score(
        rook_safe=rook_safe,
        stalemate=stalemate,
        illegal=False,
        confinement_improved=confinement_improved,
        confinement_regressed=confinement_regressed,
        mobility_reduced=mobility_reduced,
        edge_progress=edge_progress,
        king_approach=king_approach,
        partial_reply_handoff=any_handoff and not all_handoff,
        all_reply_handoff=all_handoff,
    )
    return {
        "illegal": False,
        "rook_risk": rook_risk,
        "rook_missing": rook_missing,
        "stalemate": stalemate,
        "rook_safe": rook_safe,
        "confinement_improved": confinement_improved,
        "confinement_regressed": confinement_regressed,
        "black_mobility_reduced": mobility_reduced,
        "edge_progress": edge_progress,
        "king_approach": king_approach,
        "partial_reply_handoff": any_handoff and not all_handoff,
        "all_reply_handoff": all_handoff,
        "low_progress": success_signal <= 0,
        "success_signal": float(success_signal),
        "graded_progress_score": graded_progress_score,
        "graded_progress_class": _graded_progress_class(graded_progress_score),
        "safe_confinement_progress": bool(rook_safe and confinement_improved and not confinement_regressed),
        "safe_mobility_progress": bool(rook_safe and mobility_reduced and not confinement_regressed),
        "safe_edge_progress": bool(rook_safe and edge_progress and not confinement_regressed),
        "after_fen": after.fen(),
    }


def _cached_foundation_response_details(
    after_white_move: chess.Board,
    parent: dict[str, TerminalAffordanceLearner],
    *,
    response_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    key = after_white_move.fen()
    cached = response_cache.get(key)
    if cached is None:
        cached = _foundation_response_details(after_white_move, parent)
        response_cache[key] = cached
    return cached


def _foundation_response_details(
    after_white_move: chess.Board,
    parent: dict[str, TerminalAffordanceLearner],
) -> dict[str, Any]:
    replies = list(after_white_move.legal_moves)
    mate1 = 0
    mate2 = 0
    for reply in replies:
        state = after_white_move.copy(stack=False)
        state.push(reply)
        mate = parent["mate1"].choose(state)
        if mate is not None and parent["mate1"].weight_for_move(state, mate) > 0.0:
            mate1 += 1
        first = parent["mate2_first"].choose(state)
        if first is not None and parent["mate2_first"].weight_for_move(state, first) > 0.0:
            mate2 += 1
    total = len(replies)
    response_count = max(mate1, mate2)
    return {
        "reply_total": total,
        "mate1_response_count": mate1,
        "mate2_first_response_count": mate2,
        "mate1_foundation_response": bool(mate1 > 0),
        "mate2_first_foundation_response": bool(mate2 > 0),
        "all_reply_mate1_response": bool(total > 0 and mate1 == total),
        "all_reply_mate2_first_response": bool(total > 0 and mate2 == total),
        "all_reply_graph_foundation_response": bool(total > 0 and response_count == total),
        "foundation_response_validation_mode": "positive_tg46d_graph_weight_not_forced_mate_or_tablebase",
    }


def _best_second(second_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not second_rows:
        return None
    best = sorted(
        second_rows,
        key=lambda item: (
            int(item["safe"]),
            int(item["all_reply_foundation_handoff"]),
            int(item["partial_reply_foundation_support"]),
            item["graded_progress_score"],
            item["second_move"],
        ),
        reverse=True,
    )[0]
    return {k: v for k, v in best.items() if k not in {"after_second_fen"}}


def _unsafe(metrics: dict[str, Any]) -> bool:
    return bool(
        metrics["illegal"]
        or metrics["rook_risk"]
        or metrics.get("rook_missing", False)
        or metrics["stalemate"]
        or metrics["confinement_regressed"]
    )


def classify_blocker(*, family: str, selected: dict[str, Any], oracle: dict[str, Any]) -> str:
    if family in ("decoy_edge", "hard_decoy_edge"):
        if selected["all_reply_second_handoff"] or oracle["all_reply_second_handoff"]:
            return "decoy_all_reply_handoff_leak"
        if selected["has_partial_second_support"] or oracle["has_partial_second_support"]:
            return "decoy_partial_handoff_leak"
        return "decoy_clean"
    if selected["all_reply_second_handoff"]:
        return "reachable_with_selected_first"
    if oracle["all_reply_second_handoff"]:
        return "selected_first_move_bad"
    if selected["has_partial_second_support"] or oracle["has_partial_second_support"]:
        return "only_partial_reply_support"
    if selected["unsafe_second_required"] or oracle.get("best_first_audit", {}).get("unsafe_second_required", False):
        return "unsafe_second_move_required"
    if selected["first_graded_success"] or oracle.get("best_first_audit", {}).get("first_graded_success", False):
        return "safe_local_progress_only"
    return "outside_tg46d_mate1_basin"


def _decision(
    *,
    config: HandoffReachabilityAuditConfig,
    parent_hash: str,
    parent_before: dict[str, Any],
    parent_after: dict[str, Any],
    audit_rows: list[dict[str, Any]],
    edge_learner: TerminalAffordanceLearner,
    total_seconds: float,
) -> dict[str, Any]:
    non_decoy = [row for row in audit_rows if row["family"] not in ("decoy_edge", "hard_decoy_edge")]
    fence = [row for row in audit_rows if row["family"] == "fence_hold_progress"]
    selected_all = sum(int(row["selected_first_audit"]["all_reply_second_handoff"]) for row in non_decoy)
    selected_any = sum(int(row["selected_first_audit"]["any_reply_second_handoff"]) for row in non_decoy)
    oracle_all = sum(int(row["oracle_first_audit"]["all_reply_second_handoff"]) for row in non_decoy)
    oracle_any = sum(int(row["oracle_first_audit"]["any_reply_second_handoff"]) for row in non_decoy)
    oracle_capped = sum(int(row["oracle_first_audit"].get("oracle_audit_capped", False)) for row in audit_rows)
    decoy_partial = sum(int(row["decoy_partial_handoff_leak"]) for row in audit_rows)
    decoy_all = sum(int(row["decoy_all_reply_handoff_leak"]) for row in audit_rows)
    blocker_counts = _counts(row["blocker_classification"] for row in audit_rows)
    if decoy_all or decoy_partial:
        interpretation = "decoy_handoff_leak"
        next_action = "quarantine_continuation_decoy_leak_before_training"
    elif non_decoy and oracle_all / len(non_decoy) <= 0.05:
        interpretation = "foundation_basin_or_objective_blocker"
        next_action = "repair_tg46d_foundation_basin_or_first_move_objective"
    elif oracle_all > selected_all:
        interpretation = "first_move_selection_blocker"
        next_action = "repair_edge_fence_first_move_selection_for_handoff_reachability"
    elif selected_all > 0:
        interpretation = "continuation_materialization_blocker"
        next_action = "train_handoff_specific_continuation_materialization"
    else:
        interpretation = "foundation_basin_or_objective_blocker"
        next_action = "repair_tg46d_foundation_basin_or_first_move_objective"
    return {
        "checkpoint_pass": True,
        "checkpoint_interpretation": interpretation,
        "selected_next_action": next_action,
        "repair_applied": False,
        "diagnostic_only": True,
        "parent_foundation_hash": parent_hash,
        "parent_foundation_frozen": True,
        "parent_foundation_sanity_before_pass": parent_before["pass"],
        "parent_foundation_sanity_after_pass": parent_after["pass"],
        "parent_foundation_m3_delta_during_audit": 0,
        "parent_foundation_m4_delta_during_audit": 0,
        "edge_learner_weight_delta_during_audit": 0,
        "edge_learner_terminal_count": len(edge_learner.terminals),
        "input_position_count": len(audit_rows),
        "non_decoy_position_count": len(non_decoy),
        "fence_hold_position_count": len(fence),
        "selected_first_all_reply_second_handoff_rate": _rate_count(selected_all, len(non_decoy)),
        "selected_first_any_reply_second_handoff_rate": _rate_count(selected_any, len(non_decoy)),
        "oracle_first_all_reply_second_handoff_rate": _rate_count(oracle_all, len(non_decoy)),
        "oracle_first_any_reply_second_handoff_rate": _rate_count(oracle_any, len(non_decoy)),
        "oracle_audit_capped_count": oracle_capped,
        "selected_second_move_cap": config.selected_second_move_cap,
        "oracle_first_move_cap": config.oracle_first_move_cap,
        "oracle_second_move_cap": config.oracle_second_move_cap,
        "foundation_response_validation_mode": "positive_tg46d_graph_weight_not_forced_mate_or_tablebase",
        "fence_hold_selected_first_all_reply_second_handoff_rate": _rate_count(
            sum(int(row["selected_first_audit"]["all_reply_second_handoff"]) for row in fence),
            len(fence),
        ),
        "fence_hold_oracle_first_all_reply_second_handoff_rate": _rate_count(
            sum(int(row["oracle_first_audit"]["all_reply_second_handoff"]) for row in fence),
            len(fence),
        ),
        "partial_only_count": sum(
            int(
                (row["selected_first_audit"]["has_partial_second_support"] or row["oracle_first_audit"]["has_partial_second_support"])
                and not row["oracle_first_audit"]["all_reply_second_handoff"]
            )
            for row in non_decoy
        ),
        "outside_foundation_basin_count": blocker_counts.get("outside_tg46d_mate1_basin", 0)
        + blocker_counts.get("safe_local_progress_only", 0),
        "unsafe_second_required_count": sum(
            int(row["selected_first_audit"]["unsafe_second_required"] or row["oracle_first_audit"].get("best_first_audit", {}).get("unsafe_second_required", False))
            for row in non_decoy
        ),
        "decoy_partial_false_handoff_count": decoy_partial,
        "decoy_all_reply_false_handoff_count": decoy_all,
        "blocker_classification_counts": blocker_counts,
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "learner_visible_stage_labels": False,
        "learner_visible_edge_fence_labels": False,
        "learner_visible_basin_labels": False,
        "learner_visible_continuation_labels": False,
        "learner_visible_quality_labels": False,
        "learner_visible_depth_labels": False,
        "learner_visible_reply_policy_labels": False,
        "old_tg_pools_loaded": 0,
        "old_canary_loaded": False,
        "child_branch_loaded": False,
        "boundary_pool_loaded": False,
        "total_seconds": total_seconds,
    }


def _rate_count(count: int, total: int) -> float:
    return 0.0 if total == 0 else count / total


def _counts(values: Iterable[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:
        out[value] = out.get(value, 0) + 1
    return out


def _strip_reply_rows(first_audit: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in first_audit.items() if k != "reply_rows"}


def _strip_audit_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "position_count": len(rows),
        "family_counts": _counts(row["family"] for row in rows),
        "blocker_classification_counts": _counts(row["blocker_classification"] for row in rows),
    }


def _read_jsonl_gzip(path: str | Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _purity_boundary() -> dict[str, bool]:
    return {
        "diagnostic_only": True,
        "trainer_side_exploration_used": True,
        "trainer_side_exploration_used_in_final_eval": True,
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "basin_labels_learner_visible": False,
        "continuation_labels_learner_visible": False,
        "quality_tier_labels_learner_visible": False,
        "depth_labels_learner_visible": False,
        "reply_policy_labels_learner_visible": False,
    }


def _write_markdown(path: str | Path, result: HandoffReachabilityAuditResult) -> None:
    decision = result.decision
    lines = [
        "# TG47g Handoff Reachability Audit",
        "",
        f"- Checkpoint pass: {decision['checkpoint_pass']}",
        f"- Interpretation: {decision['checkpoint_interpretation']}",
        f"- Selected next action: {decision['selected_next_action']}",
        f"- Selected-first all-reply second handoff rate: {decision['selected_first_all_reply_second_handoff_rate']:.3f}",
        f"- Oracle-first all-reply second handoff rate: {decision['oracle_first_all_reply_second_handoff_rate']:.3f}",
        f"- Fence selected/oracle all-reply handoff rates: {decision['fence_hold_selected_first_all_reply_second_handoff_rate']:.3f} / {decision['fence_hold_oracle_first_all_reply_second_handoff_rate']:.3f}",
        f"- Partial-only count: {decision['partial_only_count']}",
        f"- Decoy partial/all-reply false handoffs: {decision['decoy_partial_false_handoff_count']} / {decision['decoy_all_reply_false_handoff_count']}",
        f"- Parent frozen: {decision['parent_foundation_frozen']} with deltas {decision['parent_foundation_m3_delta_during_audit']} / {decision['parent_foundation_m4_delta_during_audit']}",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
