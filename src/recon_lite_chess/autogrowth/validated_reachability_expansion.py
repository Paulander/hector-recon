"""TG47i validated reachability expansion and target classification."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any, Iterable, Literal

import chess

from .clean_edge_fence_stage import (
    DEFAULT_TG46D_DIR,
    _choose_stage_move,
    _file_sha256,
    _write_jsonl_gzip,
)
from .handoff_reachability_audit import (
    DEFAULT_TG47F_DIR,
    _foundation_artifact_sanity,
    _load_json,
    _ranked_legal_moves,
    _read_jsonl_gzip,
    _reconstruct_m4_edge_learner,
    _reconstruct_parent_foundation_from_m4_audit,
)
from .real_clean_slate_foundation import _git_head
from .terminal_substrate import TerminalAffordanceLearner
from .validated_basin_acceptance import (
    DEFAULT_TG47G_DIR,
    DEFAULT_OUTPUT_DIR as DEFAULT_TG47H_DIR,
    _is_decoy,
    _learner_snapshot,
    _purity_boundary,
    _second_safe,
    _validate_mate1_response,
)


DEFAULT_OUTPUT_DIR = Path("reports/autogrowth/clean_slate_krk/tg47i_validated_reachability_expansion")

FirstMoveMode = Literal["selected_only", "top_k", "exhaustive"]
SecondMoveMode = Literal["top_k", "exhaustive"]


@dataclass(frozen=True)
class ValidatedReachabilityExpansionConfig:
    checkpoint_name: str = "TG47i_validated_reachability_expansion"
    schema_version: str = "krk_tg47i_validated_reachability_expansion.v0"
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    output_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg47i_validated_reachability_expansion.json")
    markdown_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg47i_validated_reachability_expansion.md")
    trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg47i_validated_reachability_traces.jsonl.gz")
    boundary_failure_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg47i_boundary_failures.jsonl.gz")
    partial_near_basin_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg47i_validated_partial_near_basin.jsonl.gz")
    parent_foundation_artifact_path: str = str(DEFAULT_TG46D_DIR / "promoted_tg46d_foundation.json")
    parent_foundation_m4_audit_path: str = str(DEFAULT_TG46D_DIR / "pools" / "tg46d_m4_audit.jsonl.gz")
    source_tg47f_m4_audit_path: str = str(DEFAULT_TG47F_DIR / "pools" / "tg47f_m4_audit.jsonl.gz")
    source_tg47g_artifact_path: str = str(DEFAULT_TG47G_DIR / "krk_tg47g_handoff_reachability_audit.json")
    source_tg47g_trace_path: str = str(DEFAULT_TG47G_DIR / "pools" / "tg47g_handoff_audit.jsonl.gz")
    source_tg47h_artifact_path: str = str(DEFAULT_TG47H_DIR / "krk_tg47h_validated_basin_acceptance.json")
    source_tg47h_quarantine_path: str = str(DEFAULT_TG47H_DIR / "pools" / "tg47h_false_basin_quarantine.jsonl.gz")
    first_move_mode: FirstMoveMode = "top_k"
    second_move_mode: SecondMoveMode = "exhaustive"
    top_k_first: int = 3
    top_k_second: int = 3
    max_white_horizon: int = 2
    max_positions: int | None = None


@dataclass(frozen=True)
class ValidatedReachabilityExpansionResult:
    config: ValidatedReachabilityExpansionConfig
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


def run_validated_reachability_expansion(
    *,
    config: ValidatedReachabilityExpansionConfig,
) -> ValidatedReachabilityExpansionResult:
    _validate_config(config)
    start = time.perf_counter()
    parent_artifact = _load_json(config.parent_foundation_artifact_path)
    parent_hash = _file_sha256(config.parent_foundation_artifact_path)
    parent = _reconstruct_parent_foundation_from_m4_audit(
        parent_artifact=parent_artifact,
        parent_m4_audit_path=config.parent_foundation_m4_audit_path,
    )
    parent_before = _foundation_artifact_sanity(parent_artifact, parent)
    edge_learner = _reconstruct_m4_edge_learner(config.source_tg47f_m4_audit_path)
    parent_snapshot = {name: _learner_snapshot(learner) for name, learner in parent.items()}
    edge_snapshot = _learner_snapshot(edge_learner)
    source_rows = _load_tg47g_rows(config)
    tg47h_artifact = _load_json(config.source_tg47h_artifact_path)
    response_cache: dict[str, dict[str, Any]] = {}
    trace_rows = [
        _audit_trace_row(
            index=index,
            row=row,
            parent=parent,
            edge_learner=edge_learner,
            response_cache=response_cache,
            config=config,
        )
        for index, row in enumerate(source_rows)
    ]
    parent_after = _foundation_artifact_sanity(parent_artifact, parent)
    parent_weight_delta = int(parent_snapshot != {name: _learner_snapshot(learner) for name, learner in parent.items()})
    edge_weight_delta = int(edge_snapshot != _learner_snapshot(edge_learner))
    boundary_rows = [row for row in trace_rows if row["blocking_family"] not in {"validated_target_selected", "decoy_clean"}]
    partial_rows = [
        row for row in trace_rows
        if row["selected_first_audit"]["validated_partial_handoff"] or row["oracle_first_audit"]["validated_partial_handoff"]
    ]
    _write_jsonl_gzip(config.trace_path, trace_rows)
    _write_jsonl_gzip(config.boundary_failure_path, boundary_rows)
    _write_jsonl_gzip(config.partial_near_basin_path, partial_rows)
    total_seconds = round(time.perf_counter() - start, 6)
    false_basin_terminal_counts = _false_basin_terminal_counts(tg47h_artifact, config)
    decision = _decision(
        config=config,
        parent_hash=parent_hash,
        parent_before=parent_before,
        parent_after=parent_after,
        trace_rows=trace_rows,
        false_basin_terminal_counts=false_basin_terminal_counts,
        parent_weight_delta=parent_weight_delta,
        edge_weight_delta=edge_weight_delta,
        total_seconds=total_seconds,
    )
    payload = {
        "provenance": {
            "git_head": _git_head(),
            "parent_foundation_artifact": config.parent_foundation_artifact_path,
            "parent_foundation_hash": parent_hash,
            "parent_foundation_m4_audit": config.parent_foundation_m4_audit_path,
            "source_tg47f_m4_audit": config.source_tg47f_m4_audit_path,
            "source_tg47g_artifact": config.source_tg47g_artifact_path,
            "source_tg47g_trace": config.source_tg47g_trace_path,
            "source_tg47h_artifact": config.source_tg47h_artifact_path,
            "source_tg47h_quarantine": config.source_tg47h_quarantine_path,
            "input_source": "tg47g_trace_revalidated_expanded_search_only",
            "old_tg_pools_loaded": 0,
            "old_canary_loaded": False,
            "child_branch_loaded": False,
            "boundary_pool_loaded": False,
            "rescue_artifacts_loaded": False,
        },
        "parent_foundation": {
            "frozen": True,
            "sanity_before": parent_before,
            "sanity_after": parent_after,
            "m3_delta_during_audit": 0,
            "m4_delta_during_audit": 0,
            "weight_delta_during_audit": parent_weight_delta,
        },
        "edge_fence_m4": {
            "terminal_count": len(edge_learner.terminals),
            "m3_update_delta_during_audit": 0,
            "m4_promotion_delta_during_audit": 0,
            "weight_delta_during_audit": edge_weight_delta,
        },
        "artifact_paths": {
            "main": config.output_path,
            "markdown": config.markdown_path,
            "validated_reachability_traces": config.trace_path,
            "boundary_failures": config.boundary_failure_path,
            "validated_partial_near_basin": config.partial_near_basin_path,
        },
        "cache_summary": {
            "foundation_response_cache_entries": len(response_cache),
        },
        "purity_boundary": _tg47i_purity_boundary(),
        "audit_summary": _strip_trace_rows(trace_rows),
        "timing": {"total_seconds": total_seconds},
    }
    result = ValidatedReachabilityExpansionResult(config=config, payload=payload, decision=decision)
    result.write_json(config.output_path)
    _write_markdown(config.markdown_path, result)
    return result


def _validate_config(config: ValidatedReachabilityExpansionConfig) -> None:
    if config.first_move_mode not in {"selected_only", "top_k", "exhaustive"}:
        raise ValueError(f"invalid first_move_mode: {config.first_move_mode}")
    if config.second_move_mode not in {"top_k", "exhaustive"}:
        raise ValueError(f"invalid second_move_mode: {config.second_move_mode}")
    if config.max_white_horizon not in {2, 3}:
        raise ValueError("max_white_horizon must be 2 or 3")
    if config.top_k_first < 1 or config.top_k_second < 1:
        raise ValueError("top_k_first/top_k_second must be positive")


def _load_tg47g_rows(config: ValidatedReachabilityExpansionConfig) -> list[dict[str, Any]]:
    rows = _read_jsonl_gzip(config.source_tg47g_trace_path)
    if config.max_positions is not None:
        return rows[: config.max_positions]
    return rows


def _audit_trace_row(
    *,
    index: int,
    row: dict[str, Any],
    parent: dict[str, TerminalAffordanceLearner],
    edge_learner: TerminalAffordanceLearner,
    response_cache: dict[str, dict[str, Any]],
    config: ValidatedReachabilityExpansionConfig,
) -> dict[str, Any]:
    board = chess.Board(row["fen"])
    selected_first = _selected_first_move(board, row, parent=parent, edge_learner=edge_learner)
    selected = _audit_first_expanded(
        board=board,
        first=selected_first,
        first_kind="selected",
        family=row["family"],
        split=row.get("split", ""),
        source_row=row,
        parent=parent,
        edge_learner=edge_learner,
        response_cache=response_cache,
        second_move_mode=config.second_move_mode,
        top_k_second=config.top_k_second,
    )
    oracle_candidates = [
        _audit_first_expanded(
            board=board,
            first=first,
            first_kind="oracle_candidate",
            family=row["family"],
            split=row.get("split", ""),
            source_row=row,
            parent=parent,
            edge_learner=edge_learner,
            response_cache=response_cache,
            second_move_mode=config.second_move_mode,
            top_k_second=config.top_k_second,
        )
        for first in _first_candidates(board, config=config)
    ]
    oracle = _best_first_audit(oracle_candidates, first_move_mode=config.first_move_mode)
    blocking_family = _blocking_family(family=row["family"], selected=selected, oracle=oracle)
    quarantine_rows = selected["false_basin_quarantine_rows"] + oracle["false_basin_quarantine_rows"]
    return {
        "trace_id": f"tg47i_{index:04d}",
        "source_tg47g_audit_id": row.get("audit_id"),
        "fen": row["fen"],
        "family": row["family"],
        "split": row.get("split"),
        "lineage_key": row.get("lineage_key"),
        "source_tg47g_blocker_classification": row.get("blocker_classification"),
        "selected_first_audit": _strip_quarantine(selected),
        "oracle_first_audit": _strip_quarantine(oracle),
        "blocking_family": blocking_family,
        "target_success": bool((not _is_decoy(row["family"])) and selected["validated_all_reply_handoff"]),
        "oracle_target_available": bool((not _is_decoy(row["family"])) and oracle["validated_all_reply_handoff"]),
        "validated_partial_only": bool(
            not selected["validated_all_reply_handoff"]
            and not oracle["validated_all_reply_handoff"]
            and (selected["validated_partial_handoff"] or oracle["validated_partial_handoff"])
        ),
        "no_validated_response": bool(
            not selected["validated_all_reply_handoff"]
            and not oracle["validated_all_reply_handoff"]
            and not selected["validated_partial_handoff"]
            and not oracle["validated_partial_handoff"]
        ),
        "decoy_validated_all_reply_false_handoff": bool(
            _is_decoy(row["family"])
            and (selected["validated_all_reply_handoff"] or oracle["validated_all_reply_handoff"])
        ),
        "decoy_validated_partial_false_handoff": bool(
            _is_decoy(row["family"])
            and (selected["validated_partial_handoff"] or oracle["validated_partial_handoff"])
        ),
        "false_basin_quarantine_count": len(quarantine_rows),
        "false_basin_quarantine_rows": quarantine_rows,
        "learner_visible_labels": False,
    }


def _selected_first_move(
    board: chess.Board,
    row: dict[str, Any],
    *,
    parent: dict[str, TerminalAffordanceLearner],
    edge_learner: TerminalAffordanceLearner,
) -> chess.Move | None:
    raw = row.get("selected_first_move")
    if raw:
        move = chess.Move.from_uci(raw)
        if move in board.legal_moves:
            return move
    return _choose_stage_move(board, parent=parent, edge_learner=edge_learner)


def _first_candidates(board: chess.Board, *, config: ValidatedReachabilityExpansionConfig) -> list[chess.Move]:
    if config.first_move_mode == "selected_only":
        return []
    if config.first_move_mode == "top_k":
        candidates = _ranked_legal_moves(board, cap=config.top_k_first)
    else:
        candidates = sorted(board.legal_moves, key=lambda item: item.uci())
    return [move for move in candidates if _first_safe(board, move)]


def _first_safe(board: chess.Board, move: chess.Move) -> bool:
    if move not in board.legal_moves:
        return False
    after = board.copy(stack=False)
    after.push(move)
    rook_squares = set(after.pieces(chess.ROOK, chess.WHITE))
    return bool(
        not after.is_stalemate()
        and bool(rook_squares)
        and not any(reply.to_square in rook_squares for reply in after.legal_moves)
    )


def _audit_first_expanded(
    *,
    board: chess.Board,
    first: chess.Move | None,
    first_kind: str,
    family: str,
    split: str,
    source_row: dict[str, Any],
    parent: dict[str, TerminalAffordanceLearner],
    edge_learner: TerminalAffordanceLearner,
    response_cache: dict[str, dict[str, Any]],
    second_move_mode: SecondMoveMode,
    top_k_second: int,
) -> dict[str, Any]:
    if first is None or first not in board.legal_moves:
        return _empty_first(first_kind, first_move=None, blocked_reason="no_legal_first_move")
    if not _first_safe(board, first):
        return _empty_first(first_kind, first_move=first.uci(), blocked_reason="unsafe_first_move")
    after_first = board.copy(stack=False)
    after_first.push(first)
    reply_rows = []
    quarantine_rows: list[dict[str, Any]] = []
    for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
        state = after_first.copy(stack=False)
        state.push(reply)
        legal_seconds = sorted(state.legal_moves, key=lambda item: item.uci())
        audited_seconds = _second_candidates(state, mode=second_move_mode, top_k=top_k_second)
        second_rows = [
            _audit_second_expanded(
                board=state,
                second=second,
                source_row=source_row,
                first=first,
                black_reply=reply,
                first_kind=first_kind,
                parent=parent,
                edge_learner=edge_learner,
                response_cache=response_cache,
            )
            for second in audited_seconds
        ]
        quarantine_rows.extend(item["quarantine_row"] for item in second_rows if item["quarantine_row"] is not None)
        safe = [item for item in second_rows if item["safe"]]
        validated_all = [item for item in safe if item["validated_all_reply_handoff"]]
        validated_partial = [item for item in safe if item["validated_partial_handoff"]]
        graph_all = [item for item in safe if item["graph_positive_all_reply_handoff"]]
        graph_partial = [item for item in safe if item["graph_positive_partial_handoff"]]
        reply_rows.append({
            "black_reply": reply.uci(),
            "successor_fen": state.fen(),
            "legal_second_count": len(legal_seconds),
            "audited_second_count": len(second_rows),
            "second_move_mode": second_move_mode,
            "second_move_cap": None if second_move_mode == "exhaustive" else top_k_second,
            "second_move_audit_capped": bool(second_move_mode != "exhaustive" and len(legal_seconds) > len(second_rows)),
            "safe_second_count": len(safe),
            "has_validated_all_reply_second": bool(validated_all),
            "has_validated_partial_second": bool(validated_partial),
            "has_graph_positive_all_reply_second": bool(graph_all),
            "has_graph_positive_partial_second": bool(graph_partial),
            "best_second": _best_second(second_rows),
        })
    reply_total = len(reply_rows)
    validated_all_replies = sum(int(item["has_validated_all_reply_second"]) for item in reply_rows)
    validated_partial_replies = sum(int(item["has_validated_partial_second"]) for item in reply_rows)
    graph_all_replies = sum(int(item["has_graph_positive_all_reply_second"]) for item in reply_rows)
    graph_partial_replies = sum(int(item["has_graph_positive_partial_second"]) for item in reply_rows)
    return {
        "first_move_kind": first_kind,
        "first_move": first.uci(),
        "first_safe": True,
        "blocked_reason": None,
        "reply_total": reply_total,
        "validated_all_reply_handoff": bool(reply_total > 0 and validated_all_replies == reply_total),
        "validated_any_reply_handoff": bool(validated_all_replies > 0),
        "validated_partial_handoff": bool(validated_partial_replies > 0),
        "validated_reply_success_rate": _rate(validated_all_replies, reply_total),
        "graph_positive_all_reply_handoff": bool(reply_total > 0 and graph_all_replies == reply_total),
        "graph_positive_any_reply_handoff": bool(graph_all_replies > 0),
        "graph_positive_partial_handoff": bool(graph_partial_replies > 0),
        "graph_positive_reply_success_rate": _rate(graph_all_replies, reply_total),
        "total_legal_second_count": sum(item["legal_second_count"] for item in reply_rows),
        "total_audited_second_count": sum(item["audited_second_count"] for item in reply_rows),
        "second_move_mode": second_move_mode,
        "reply_rows": reply_rows,
        "false_basin_quarantine_rows": quarantine_rows,
        "split": split,
        "family": family,
    }


def _second_candidates(board: chess.Board, *, mode: SecondMoveMode, top_k: int) -> list[chess.Move]:
    if mode == "top_k":
        return _ranked_legal_moves(board, cap=top_k)
    return sorted(board.legal_moves, key=lambda item: item.uci())


def _audit_second_expanded(
    *,
    board: chess.Board,
    second: chess.Move,
    source_row: dict[str, Any],
    first: chess.Move,
    black_reply: chess.Move,
    first_kind: str,
    parent: dict[str, TerminalAffordanceLearner],
    edge_learner: TerminalAffordanceLearner,
    response_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    after_second = board.copy(stack=False)
    after_second.push(second)
    safe = _second_safe(board, second)
    response = _validated_foundation_response_details_fast(after_second, parent, response_cache=response_cache)
    graph_all = bool(response["graph_all_reply_foundation_response"])
    graph_partial = bool(response["graph_partial_reply_foundation_response"])
    validated_all = bool(response["validator_all_reply_foundation_response"])
    validated_partial = bool(response["validator_partial_reply_foundation_response"])
    quarantine = None
    if safe and (graph_all or graph_partial) and not validated_all:
        quarantine = _quarantine_row(
            source_row=source_row,
            first=first,
            black_reply=black_reply,
            second=second,
            after_second=after_second,
            first_kind=first_kind,
            response=response,
            edge_learner=edge_learner,
        )
    return {
        "second_move": second.uci(),
        "after_second_fen": after_second.fen(),
        "safe": safe,
        "graph_positive_all_reply_handoff": bool(safe and graph_all),
        "graph_positive_partial_handoff": bool(safe and graph_partial and not graph_all),
        "validated_all_reply_handoff": bool(safe and validated_all),
        "validated_partial_handoff": bool(safe and validated_partial and not validated_all),
        "graph_response_type": response["graph_response_type"],
        "validator_failure_reason": response["validator_failure_reason"],
        "quarantine_row": quarantine,
    }


def _validated_foundation_response_details_fast(
    after_white_move: chess.Board,
    parent: dict[str, TerminalAffordanceLearner],
    *,
    response_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    key = after_white_move.fen()
    cached = response_cache.get(key)
    if cached is not None:
        return cached
    replies = list(after_white_move.legal_moves)
    graph_positive_count = 0
    validator_count = 0
    graph_types: dict[str, int] = {}
    selected_mate1: list[str | None] = []
    selected_mate2: list[str | None] = []
    failure_reasons: dict[str, int] = {}
    for reply in replies:
        state = after_white_move.copy(stack=False)
        state.push(reply)
        detail = _validate_foundation_response_at_white_turn_fast(state, parent)
        graph_positive_count += int(detail["graph_positive_response"])
        validator_count += int(detail["validator_confirmed_response"])
        graph_types[detail["graph_response_type"]] = graph_types.get(detail["graph_response_type"], 0) + 1
        failure_reasons[detail["validator_failure_reason"]] = failure_reasons.get(detail["validator_failure_reason"], 0) + 1
        selected_mate1.append(detail["selected_mate1_move"])
        selected_mate2.append(detail["selected_mate2_first_move"])
    total = len(replies)
    failure_reason = _majority_key(failure_reasons)
    if 0 < validator_count < total:
        failure_reason = "partial_validator_confirmation_not_all_reply"
    result = {
        "reply_total": total,
        "graph_positive_reply_count": graph_positive_count,
        "validator_confirmed_reply_count": validator_count,
        "graph_partial_reply_foundation_response": bool(graph_positive_count > 0),
        "graph_all_reply_foundation_response": bool(total > 0 and graph_positive_count == total),
        "validator_partial_reply_foundation_response": bool(validator_count > 0),
        "validator_all_reply_foundation_response": bool(total > 0 and validator_count == total),
        "graph_positive_but_validator_failed_false_basin": bool(graph_positive_count > 0 and validator_count < total),
        "graph_response_type": _majority_key(graph_types),
        "validator_failure_reason": failure_reason,
        "selected_tg46d_mate1_move": _first_present(selected_mate1),
        "selected_tg46d_mate2_first_move": _first_present(selected_mate2),
        "active_tg46d_terminal_keys": [],
        "validation_mode": "graph_positive_precheck_plus_same_graph_tg46d_validation",
    }
    response_cache[key] = result
    return result


def _validate_foundation_response_at_white_turn_fast(
    board: chess.Board,
    parent: dict[str, TerminalAffordanceLearner],
) -> dict[str, Any]:
    mate = parent["mate1"].choose(board)
    selected_mate = None if mate is None else mate.uci()
    mate_graph_positive = bool(mate is not None and parent["mate1"].weight_for_move(board, mate) > 0.0)
    mate_valid = bool(mate_graph_positive and _validate_mate1_response(board, mate))
    first = parent["mate2_first"].choose(board)
    selected_first = None if first is None else first.uci()
    first_graph_positive = bool(first is not None and parent["mate2_first"].weight_for_move(board, first) > 0.0)
    first_valid = bool(first_graph_positive and _validate_mate2_same_graph_response(board, first, parent))
    graph_positive = bool(mate_graph_positive or first_graph_positive)
    validator_confirmed = bool(mate_valid or first_valid)
    if mate_graph_positive and first_graph_positive:
        graph_type = "mate1_and_mate2_graph_positive"
    elif mate_graph_positive:
        graph_type = "mate1_graph_positive"
    elif first_graph_positive:
        graph_type = "mate2_first_graph_positive"
    else:
        graph_type = "no_graph_positive_response"
    return {
        "graph_positive_response": graph_positive,
        "validator_confirmed_response": validator_confirmed,
        "graph_response_type": graph_type,
        "validator_failure_reason": _validator_failure_reason_fast(
            mate_graph_positive=mate_graph_positive,
            first_graph_positive=first_graph_positive,
            mate_valid=mate_valid,
            first_valid=first_valid,
        ),
        "selected_mate1_move": selected_mate,
        "selected_mate2_first_move": selected_first,
    }


def _validator_failure_reason_fast(
    *,
    mate_graph_positive: bool,
    first_graph_positive: bool,
    mate_valid: bool,
    first_valid: bool,
) -> str:
    if mate_valid or first_valid:
        return "validator_confirmed"
    if not mate_graph_positive and not first_graph_positive:
        return "no_graph_positive_response"
    if mate_graph_positive and not first_graph_positive:
        return "mate1_selected_move_not_checkmate"
    if first_graph_positive and not mate_graph_positive:
        return "mate2_selected_move_not_all_reply_forced"
    return "graph_positive_not_validator_confirmed"


def _validate_mate2_same_graph_response(
    board: chess.Board,
    first: chess.Move | None,
    parent: dict[str, TerminalAffordanceLearner],
) -> bool:
    if first is None or first not in board.legal_moves:
        return False
    after_first = board.copy(stack=False)
    after_first.push(first)
    replies = list(after_first.legal_moves)
    if not replies:
        return False
    for reply in replies:
        state = after_first.copy(stack=False)
        state.push(reply)
        mate = parent["mate1"].choose(state)
        if not _validate_mate1_response(state, mate):
            return False
    return True


def _quarantine_row(
    *,
    source_row: dict[str, Any],
    first: chess.Move,
    black_reply: chess.Move,
    second: chess.Move,
    after_second: chess.Board,
    first_kind: str,
    response: dict[str, Any],
    edge_learner: TerminalAffordanceLearner,
) -> dict[str, Any]:
    _ = edge_learner
    return {
        "schema_version": "tg47i_false_basin_quarantine.v0",
        "fen": source_row["fen"],
        "family": source_row["family"],
        "split": source_row.get("split"),
        "first_move_kind": first_kind,
        "first_move": first.uci(),
        "black_reply": black_reply.uci(),
        "second_move": second.uci(),
        "after_second_fen": after_second.fen(),
        "selected_tg46d_mate1_move": response["selected_tg46d_mate1_move"],
        "selected_tg46d_mate2_first_move": response["selected_tg46d_mate2_first_move"],
        "graph_response_type": response["graph_response_type"],
        "validator_failure_reason": response["validator_failure_reason"],
        "active_tg46d_terminal_keys": response["active_tg46d_terminal_keys"],
        "decoy": _is_decoy(source_row["family"]),
        "blocker_classification": "graph_positive_but_validator_failed_false_basin",
        "learner_visible_labels": False,
    }


def _empty_first(first_kind: str, *, first_move: str | None, blocked_reason: str) -> dict[str, Any]:
    return {
        "first_move_kind": first_kind,
        "first_move": first_move,
        "first_safe": False,
        "blocked_reason": blocked_reason,
        "reply_total": 0,
        "validated_all_reply_handoff": False,
        "validated_any_reply_handoff": False,
        "validated_partial_handoff": False,
        "validated_reply_success_rate": 0.0,
        "graph_positive_all_reply_handoff": False,
        "graph_positive_any_reply_handoff": False,
        "graph_positive_partial_handoff": False,
        "graph_positive_reply_success_rate": 0.0,
        "total_legal_second_count": 0,
        "total_audited_second_count": 0,
        "second_move_mode": None,
        "reply_rows": [],
        "false_basin_quarantine_rows": [],
    }


def _best_first_audit(candidates: list[dict[str, Any]], *, first_move_mode: FirstMoveMode) -> dict[str, Any]:
    if first_move_mode == "selected_only":
        return {
            **_empty_first("oracle_candidate", first_move=None, blocked_reason="oracle_disabled_selected_only"),
            "safe_first_candidate_count": 0,
            "audited_first_candidate_count": 0,
            "legal_first_candidate_count": 0,
            "first_move_mode": first_move_mode,
        }
    if not candidates:
        return {
            **_empty_first("oracle_candidate", first_move=None, blocked_reason="no_safe_first_move"),
            "safe_first_candidate_count": 0,
            "audited_first_candidate_count": 0,
            "legal_first_candidate_count": 0,
            "first_move_mode": first_move_mode,
        }
    best = sorted(
        candidates,
        key=lambda item: (
            int(item["validated_all_reply_handoff"]),
            item["validated_reply_success_rate"],
            int(item["validated_partial_handoff"]),
            int(item["graph_positive_all_reply_handoff"]),
            item["graph_positive_reply_success_rate"],
            item["first_move"] or "",
        ),
        reverse=True,
    )[0]
    return {
        **best,
        "safe_first_candidate_count": len([item for item in candidates if item["first_safe"]]),
        "audited_first_candidate_count": len(candidates),
        "legal_first_candidate_count": len(candidates),
        "first_move_mode": first_move_mode,
        "candidate_summaries": [
            {
                "first_move": item["first_move"],
                "validated_all_reply_handoff": item["validated_all_reply_handoff"],
                "validated_partial_handoff": item["validated_partial_handoff"],
                "validated_reply_success_rate": item["validated_reply_success_rate"],
                "reply_total": item["reply_total"],
            }
            for item in candidates[:16]
        ],
    }


def _best_second(second_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not second_rows:
        return None
    best = sorted(
        second_rows,
        key=lambda item: (
            int(item["safe"]),
            int(item["validated_all_reply_handoff"]),
            int(item["validated_partial_handoff"]),
            int(item["graph_positive_all_reply_handoff"]),
            int(item["graph_positive_partial_handoff"]),
            item["second_move"],
        ),
        reverse=True,
    )[0]
    return {key: value for key, value in best.items() if key != "quarantine_row"}


def _blocking_family(*, family: str, selected: dict[str, Any], oracle: dict[str, Any]) -> str:
    if _is_decoy(family):
        if selected["validated_all_reply_handoff"] or oracle["validated_all_reply_handoff"]:
            return "decoy_all_reply_leak"
        if selected["validated_partial_handoff"] or oracle["validated_partial_handoff"]:
            return "decoy_partial_near_basin"
        return "decoy_clean"
    if selected["validated_all_reply_handoff"]:
        return "validated_target_selected"
    if oracle["validated_all_reply_handoff"]:
        return "selected_first_wrong_but_oracle_exists"
    if selected["validated_partial_handoff"] or oracle["validated_partial_handoff"]:
        return "only_partial_validated_support"
    if selected["graph_positive_any_reply_handoff"] or oracle["graph_positive_any_reply_handoff"]:
        return "parent_foundation_basin_too_narrow"
    return "no_validated_second_move"


def _decision(
    *,
    config: ValidatedReachabilityExpansionConfig,
    parent_hash: str,
    parent_before: dict[str, Any],
    parent_after: dict[str, Any],
    trace_rows: list[dict[str, Any]],
    false_basin_terminal_counts: dict[str, int],
    parent_weight_delta: int,
    edge_weight_delta: int,
    total_seconds: float,
) -> dict[str, Any]:
    non_decoy = [row for row in trace_rows if not _is_decoy(row["family"])]
    fence = [row for row in trace_rows if row["family"] == "fence_hold_progress"]
    decoy = [row for row in trace_rows if row["family"] == "decoy_edge"]
    hard_decoy = [row for row in trace_rows if row["family"] == "hard_decoy_edge"]
    selected_valid = sum(int(row["selected_first_audit"]["validated_all_reply_handoff"]) for row in non_decoy)
    oracle_valid = sum(int(row["oracle_first_audit"]["validated_all_reply_handoff"]) for row in non_decoy)
    selected_rate = _rate(selected_valid, len(non_decoy))
    oracle_rate = _rate(oracle_valid, len(non_decoy))
    decoy_all = sum(int(row["decoy_validated_all_reply_false_handoff"]) for row in decoy)
    decoy_partial = sum(int(row["decoy_validated_partial_false_handoff"]) for row in decoy)
    hard_decoy_all = sum(int(row["decoy_validated_all_reply_false_handoff"]) for row in hard_decoy)
    hard_decoy_partial = sum(int(row["decoy_validated_partial_false_handoff"]) for row in hard_decoy)
    total_decoy_all = decoy_all + hard_decoy_all
    if total_decoy_all > 0:
        interpretation = "validated_decoy_all_reply_leak"
        next_action = "quarantine_validated_decoy_all_reply_leak"
    elif oracle_rate < 0.20:
        interpretation = "foundation_basin_or_objective_blocker"
        next_action = "repair_tg46d_foundation_boundary_or_edge_fence_objective"
    elif oracle_rate >= 0.20 and selected_rate < oracle_rate:
        interpretation = "first_move_selection_blocker"
        next_action = "repair_edge_fence_first_move_selection_for_validated_handoff"
    elif selected_valid > 0 and (decoy_partial + hard_decoy_partial) == 0:
        interpretation = "handoff_materialization_target_available"
        next_action = "train_handoff_specific_continuation_materialization"
    else:
        interpretation = "continue_validated_reachability_diagnostics"
        next_action = "inspect_boundary_failures"
    return {
        "checkpoint_pass": True,
        "checkpoint_interpretation": interpretation,
        "selected_next_action": next_action,
        "diagnostic_only": True,
        "repair_applied": False,
        "training_applied": False,
        "runtime_behavior_changed": False,
        "validation_mode": "validated_all_reply_same_graph_tg46d_foundation_handoff_only",
        "search_modes": {
            "selected_first": "source_selected_plus_exhaustive_second" if config.second_move_mode == "exhaustive" else "source_selected_plus_top_k_second",
            "oracle_first": f"{config.first_move_mode}_safe_first_plus_{config.second_move_mode}_second",
            "max_white_horizon": config.max_white_horizon,
            "horizon_3_bounded_audit": "not_run_in_canonical_two_white_reachability_audit",
            "exhaustive_safe_first_exhaustive_second_status": (
                "completed"
                if config.first_move_mode == "exhaustive" and config.second_move_mode == "exhaustive"
                else "not_run_throughput_blocked_by_smoke_attempts"
            ),
        },
        "exhaustive_safe_first_exhaustive_second_throughput_blocked": not (
            config.first_move_mode == "exhaustive" and config.second_move_mode == "exhaustive"
        ),
        "parent_foundation_hash": parent_hash,
        "parent_foundation_frozen": True,
        "parent_foundation_sanity_before_pass": parent_before["pass"],
        "parent_foundation_sanity_after_pass": parent_after["pass"],
        "parent_foundation_m3_delta_during_audit": 0,
        "parent_foundation_m4_delta_during_audit": 0,
        "parent_foundation_weight_delta_during_audit": parent_weight_delta,
        "edge_learner_weight_delta_during_audit": edge_weight_delta,
        "input_position_count": len(trace_rows),
        "non_decoy_position_count": len(non_decoy),
        "non_decoy_selected_first_validated_all_reply_rate": selected_rate,
        "non_decoy_oracle_first_validated_all_reply_rate": oracle_rate,
        "fence_hold_selected_first_validated_all_reply_rate": _rate(
            sum(int(row["selected_first_audit"]["validated_all_reply_handoff"]) for row in fence),
            len(fence),
        ),
        "fence_hold_oracle_first_validated_all_reply_rate": _rate(
            sum(int(row["oracle_first_audit"]["validated_all_reply_handoff"]) for row in fence),
            len(fence),
        ),
        "non_decoy_validated_partial_only_count": sum(int(row["validated_partial_only"]) for row in non_decoy),
        "fence_hold_validated_partial_only_count": sum(int(row["validated_partial_only"]) for row in fence),
        "non_decoy_no_validated_response_count": sum(int(row["no_validated_response"]) for row in non_decoy),
        "decoy_validated_all_reply_false_handoff_count": decoy_all,
        "decoy_validated_partial_false_handoff_count": decoy_partial,
        "hard_decoy_validated_all_reply_false_handoff_count": hard_decoy_all,
        "hard_decoy_validated_partial_false_handoff_count": hard_decoy_partial,
        "validated_target_density_by_family": _target_density_by_family(trace_rows),
        "validated_target_density_by_horizon": _target_density_by_horizon(trace_rows, max_white_horizon=config.max_white_horizon),
        "false_basin_terminal_counts": false_basin_terminal_counts,
        "top_blocking_families": _counts(row["blocking_family"] for row in trace_rows),
        "blocking_family_counts": _counts(row["blocking_family"] for row in trace_rows),
        "false_basin_quarantine_count": sum(row["false_basin_quarantine_count"] for row in trace_rows),
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "hardcoded_fen_or_move_repair": False,
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
        "rescue_artifacts_loaded": False,
        "total_seconds": total_seconds,
    }


def _target_density_by_family(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for family in sorted({row["family"] for row in rows}):
        family_rows = [row for row in rows if row["family"] == family]
        selected = sum(int(row["selected_first_audit"]["validated_all_reply_handoff"]) for row in family_rows)
        oracle = sum(int(row["oracle_first_audit"]["validated_all_reply_handoff"]) for row in family_rows)
        out[family] = {
            "position_count": len(family_rows),
            "selected_validated_all_reply_count": selected,
            "oracle_validated_all_reply_count": oracle,
            "selected_validated_all_reply_rate": _rate(selected, len(family_rows)),
            "oracle_validated_all_reply_rate": _rate(oracle, len(family_rows)),
            "partial_only_count": sum(int(row["validated_partial_only"]) for row in family_rows),
            "no_validated_response_count": sum(int(row["no_validated_response"]) for row in family_rows),
        }
    return out


def _target_density_by_horizon(rows: list[dict[str, Any]], *, max_white_horizon: int) -> dict[str, dict[str, Any]]:
    selected = sum(int(row["selected_first_audit"]["validated_all_reply_handoff"]) for row in rows if not _is_decoy(row["family"]))
    oracle = sum(int(row["oracle_first_audit"]["validated_all_reply_handoff"]) for row in rows if not _is_decoy(row["family"]))
    total = len([row for row in rows if not _is_decoy(row["family"])])
    density = {
        "horizon_2": {
            "non_decoy_position_count": total,
            "selected_validated_all_reply_count": selected,
            "oracle_validated_all_reply_count": oracle,
            "selected_validated_all_reply_rate": _rate(selected, total),
            "oracle_validated_all_reply_rate": _rate(oracle, total),
        }
    }
    if max_white_horizon == 3:
        density["horizon_3"] = {
            "run": False,
            "reason": "optional_fence_hold_horizon3_not_run_in_canonical_tg47i",
        }
    return density


def _false_basin_terminal_counts(
    tg47h_artifact: dict[str, Any],
    config: ValidatedReachabilityExpansionConfig,
) -> dict[str, int]:
    decision = tg47h_artifact.get("decision", {})
    counts = decision.get("false_basin_activation_by_terminal_key")
    if isinstance(counts, dict) and counts:
        return {str(key): int(value) for key, value in counts.items()}
    rows = _read_jsonl_gzip(config.source_tg47h_quarantine_path)
    out: dict[str, int] = {}
    for row in rows:
        for key in row.get("active_tg46d_terminal_keys", []):
            out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items(), key=lambda item: (-item[1], item[0]))[:25])


def _strip_quarantine(first_audit: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in first_audit.items() if key != "false_basin_quarantine_rows"}


def _strip_trace_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "position_count": len(rows),
        "family_counts": _counts(row["family"] for row in rows),
        "blocking_family_counts": _counts(row["blocking_family"] for row in rows),
        "target_success_count": sum(int(row["target_success"]) for row in rows),
        "oracle_target_available_count": sum(int(row["oracle_target_available"]) for row in rows),
        "false_basin_quarantine_count": sum(row["false_basin_quarantine_count"] for row in rows),
    }


def _counts(values: Iterable[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items(), key=lambda item: (-item[1], item[0])))


def _majority_key(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)[0][0]


def _first_present(values: Iterable[str | None]) -> str | None:
    return next((value for value in values if value), None)


def _rate(count: int, total: int) -> float:
    return 0.0 if total == 0 else count / total


def _tg47i_purity_boundary() -> dict[str, bool]:
    purity = _purity_boundary()
    purity.update({
        "diagnostic_only": True,
        "training_applied": False,
        "runtime_behavior_changed": False,
        "trainer_side_validation_used": True,
        "trainer_side_validation_used_as_runtime_provider": False,
        "hardcoded_fen_or_move_repair": False,
    })
    return purity


def _write_markdown(path: str | Path, result: ValidatedReachabilityExpansionResult) -> None:
    d = result.decision
    lines = [
        "# TG47i Validated Reachability Expansion",
        "",
        f"- Checkpoint pass: {d['checkpoint_pass']}",
        f"- Interpretation: {d['checkpoint_interpretation']}",
        f"- Selected next action: {d['selected_next_action']}",
        f"- Non-decoy selected/oracle validated all-reply: {d['non_decoy_selected_first_validated_all_reply_rate']:.3f} / {d['non_decoy_oracle_first_validated_all_reply_rate']:.3f}",
        f"- Fence selected/oracle validated all-reply: {d['fence_hold_selected_first_validated_all_reply_rate']:.3f} / {d['fence_hold_oracle_first_validated_all_reply_rate']:.3f}",
        f"- Non-decoy partial-only / no validated response: {d['non_decoy_validated_partial_only_count']} / {d['non_decoy_no_validated_response_count']}",
        f"- Decoy validated all/partial false handoffs: {d['decoy_validated_all_reply_false_handoff_count']} / {d['decoy_validated_partial_false_handoff_count']}",
        f"- Hard-decoy validated all/partial false handoffs: {d['hard_decoy_validated_all_reply_false_handoff_count']} / {d['hard_decoy_validated_partial_false_handoff_count']}",
        f"- Parent weight delta: {d['parent_foundation_weight_delta_during_audit']}",
        f"- Edge learner weight delta: {d['edge_learner_weight_delta_during_audit']}",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
