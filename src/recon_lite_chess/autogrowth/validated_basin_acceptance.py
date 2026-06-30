"""TG47h validated foundation-basin acceptance and quarantine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import gzip
import json
from pathlib import Path
import time
from typing import Any, Iterable

import chess

from .clean_edge_fence_stage import (
    DEFAULT_TG46D_DIR,
    _choose_stage_move,
    _file_sha256,
    _local_progress_terminal_keys,
    _write_jsonl_gzip,
)
from .foundation_curriculum import _forced_mate_in_two_first_moves
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
from .terminal_substrate import TerminalAffordanceLearner, terminal_action_feature_keys


DEFAULT_TG47G_DIR = Path("reports/autogrowth/clean_slate_krk/tg47g_handoff_reachability_audit")
DEFAULT_OUTPUT_DIR = Path("reports/autogrowth/clean_slate_krk/tg47h_validated_basin_acceptance")


@dataclass(frozen=True)
class ValidatedBasinAcceptanceConfig:
    checkpoint_name: str = "TG47h_validated_basin_acceptance"
    schema_version: str = "krk_tg47h_validated_basin_acceptance.v0"
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    output_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg47h_validated_basin_acceptance.json")
    markdown_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg47h_validated_basin_acceptance.md")
    audit_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg47h_validated_handoff_audit.jsonl.gz")
    quarantine_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg47h_false_basin_quarantine.jsonl.gz")
    parent_foundation_artifact_path: str = str(DEFAULT_TG46D_DIR / "promoted_tg46d_foundation.json")
    parent_foundation_m4_audit_path: str = str(DEFAULT_TG46D_DIR / "pools" / "tg46d_m4_audit.jsonl.gz")
    source_tg47f_m4_audit_path: str = str(DEFAULT_TG47F_DIR / "pools" / "tg47f_m4_audit.jsonl.gz")
    source_tg47g_artifact_path: str = str(DEFAULT_TG47G_DIR / "krk_tg47g_handoff_reachability_audit.json")
    source_tg47g_trace_path: str = str(DEFAULT_TG47G_DIR / "pools" / "tg47g_handoff_audit.jsonl.gz")
    selected_second_move_cap: int = 3
    oracle_first_move_cap: int = 3
    oracle_second_move_cap: int = 3
    max_positions: int | None = None


@dataclass(frozen=True)
class ValidatedBasinAcceptanceResult:
    config: ValidatedBasinAcceptanceConfig
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


def run_validated_basin_acceptance(*, config: ValidatedBasinAcceptanceConfig) -> ValidatedBasinAcceptanceResult:
    start = time.perf_counter()
    parent_artifact = _load_json(config.parent_foundation_artifact_path)
    parent_hash = _file_sha256(config.parent_foundation_artifact_path)
    parent = _reconstruct_parent_foundation_from_m4_audit(
        parent_artifact=parent_artifact,
        parent_m4_audit_path=config.parent_foundation_m4_audit_path,
    )
    parent_before = _foundation_artifact_sanity(parent_artifact, parent)
    edge_learner = _reconstruct_m4_edge_learner(config.source_tg47f_m4_audit_path)
    edge_snapshot = _learner_snapshot(edge_learner)
    parent_snapshot = {name: _learner_snapshot(learner) for name, learner in parent.items()}
    tg47g_trace_rows = _load_tg47g_trace_rows(config)
    response_cache: dict[str, dict[str, Any]] = {}
    audit_rows: list[dict[str, Any]] = []
    quarantine_rows: list[dict[str, Any]] = []
    for index, row in enumerate(tg47g_trace_rows):
        audited = _audit_trace_row(
            index=index,
            row=row,
            parent=parent,
            edge_learner=edge_learner,
            response_cache=response_cache,
            config=config,
        )
        audit_rows.append(audited)
        quarantine_rows.extend(audited["false_basin_quarantine_rows"])
    parent_after = _foundation_artifact_sanity(parent_artifact, parent)
    parent_weight_delta = int(parent_snapshot != {name: _learner_snapshot(learner) for name, learner in parent.items()})
    edge_weight_delta = int(edge_snapshot != _learner_snapshot(edge_learner))
    _write_jsonl_gzip(config.audit_trace_path, audit_rows)
    _write_jsonl_gzip(config.quarantine_path, quarantine_rows)
    decision = _decision(
        config=config,
        parent_hash=parent_hash,
        parent_before=parent_before,
        parent_after=parent_after,
        audit_rows=audit_rows,
        quarantine_rows=quarantine_rows,
        parent_weight_delta=parent_weight_delta,
        edge_weight_delta=edge_weight_delta,
        total_seconds=round(time.perf_counter() - start, 6),
    )
    payload = {
        "provenance": {
            "git_head": _git_head(),
            "parent_foundation_artifact": config.parent_foundation_artifact_path,
            "parent_foundation_hash": parent_hash,
            "parent_foundation_m4_audit": config.parent_foundation_m4_audit_path,
            "source_tg47g_artifact": config.source_tg47g_artifact_path,
            "source_tg47g_trace": config.source_tg47g_trace_path,
            "source_tg47f_m4_audit": config.source_tg47f_m4_audit_path,
            "input_source": "tg47g_trace_revalidated_only",
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
            "audit_traces": config.audit_trace_path,
            "false_basin_quarantine": config.quarantine_path,
        },
        "purity_boundary": _purity_boundary(),
        "audit_summary": _strip_audit_rows(audit_rows),
        "timing": {"total_seconds": decision["total_seconds"]},
    }
    result = ValidatedBasinAcceptanceResult(config=config, payload=payload, decision=decision)
    result.write_json(config.output_path)
    _write_markdown(config.markdown_path, result)
    return result


def _load_tg47g_trace_rows(config: ValidatedBasinAcceptanceConfig) -> list[dict[str, Any]]:
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
    config: ValidatedBasinAcceptanceConfig,
) -> dict[str, Any]:
    board = chess.Board(row["fen"])
    selected_first = chess.Move.from_uci(row["selected_first_move"]) if row.get("selected_first_move") else None
    if selected_first is None:
        selected_first = _choose_stage_move(board, parent=parent, edge_learner=edge_learner)
    selected = _audit_first(
        board=board,
        first=selected_first,
        first_kind="selected",
        family=row["family"],
        split=row.get("split", ""),
        source_row=row,
        parent=parent,
        edge_learner=edge_learner,
        response_cache=response_cache,
        second_move_cap=config.selected_second_move_cap,
    )
    oracle_first_uci = row.get("oracle_first_audit", {}).get("best_first_move")
    oracle_first = chess.Move.from_uci(oracle_first_uci) if oracle_first_uci else None
    if oracle_first is None or oracle_first not in board.legal_moves:
        candidates = _ranked_legal_moves(board, cap=config.oracle_first_move_cap)
    else:
        candidates = [oracle_first]
    oracle_candidates = [
        _audit_first(
            board=board,
            first=first,
            first_kind="oracle_candidate",
            family=row["family"],
            split=row.get("split", ""),
            source_row=row,
            parent=parent,
            edge_learner=edge_learner,
            response_cache=response_cache,
            second_move_cap=config.oracle_second_move_cap,
        )
        for first in candidates
    ]
    oracle = _best_first_audit(oracle_candidates)
    blocker = _classify_validated_blocker(family=row["family"], selected=selected, oracle=oracle)
    quarantine_rows = selected["false_basin_quarantine_rows"] + oracle["false_basin_quarantine_rows"]
    return {
        "audit_id": f"tg47h_{index:04d}",
        "source_tg47g_audit_id": row.get("audit_id"),
        "fen": row["fen"],
        "family": row["family"],
        "split": row.get("split"),
        "lineage_key": row.get("lineage_key"),
        "source_tg47g_blocker_classification": row.get("blocker_classification"),
        "selected_first_validated_audit": _strip_quarantine(selected),
        "oracle_first_validated_audit": _strip_quarantine(oracle),
        "validated_blocker_classification": blocker,
        "graph_positive_decoy_partial_false_handoff": _is_decoy(row["family"]) and (
            selected["graph_positive_partial_handoff"] or oracle["graph_positive_partial_handoff"]
        ),
        "graph_positive_decoy_all_reply_false_handoff": _is_decoy(row["family"]) and (
            selected["graph_positive_all_reply_handoff"] or oracle["graph_positive_all_reply_handoff"]
        ),
        "validated_decoy_partial_false_handoff": _is_decoy(row["family"]) and (
            selected["validated_partial_handoff"] or oracle["validated_partial_handoff"]
        ),
        "validated_decoy_all_reply_false_handoff": _is_decoy(row["family"]) and (
            selected["validated_all_reply_handoff"] or oracle["validated_all_reply_handoff"]
        ),
        "false_basin_quarantine_count": len(quarantine_rows),
        "false_basin_quarantine_rows": quarantine_rows,
    }


def _audit_first(
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
    second_move_cap: int,
) -> dict[str, Any]:
    if first is None or first not in board.legal_moves:
        return _empty_first(first_kind, first_move=None)
    after_first = board.copy(stack=False)
    after_first.push(first)
    reply_rows = []
    quarantine_rows: list[dict[str, Any]] = []
    for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
        state = after_first.copy(stack=False)
        state.push(reply)
        second_rows = [
            _audit_second(
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
            for second in _ranked_legal_moves(state, cap=second_move_cap)
        ]
        quarantine_rows.extend(item["quarantine_row"] for item in second_rows if item["quarantine_row"] is not None)
        graph_all = [item for item in second_rows if item["safe"] and item["graph_positive_all_reply_handoff"]]
        graph_partial = [item for item in second_rows if item["safe"] and item["graph_positive_partial_handoff"]]
        validated_all = [item for item in second_rows if item["safe"] and item["validated_all_reply_handoff"]]
        validated_partial = [item for item in second_rows if item["safe"] and item["validated_partial_handoff"]]
        reply_rows.append({
            "black_reply": reply.uci(),
            "successor_fen": state.fen(),
            "audited_second_count": len(second_rows),
            "second_move_cap": second_move_cap,
            "has_graph_positive_all_reply_second": bool(graph_all),
            "has_graph_positive_partial_second": bool(graph_partial),
            "has_validated_all_reply_second": bool(validated_all),
            "has_validated_partial_second": bool(validated_partial),
            "best_second": _best_second(second_rows),
        })
    reply_total = len(reply_rows)
    graph_all_replies = sum(int(item["has_graph_positive_all_reply_second"]) for item in reply_rows)
    graph_partial_replies = sum(int(item["has_graph_positive_partial_second"]) for item in reply_rows)
    validated_all_replies = sum(int(item["has_validated_all_reply_second"]) for item in reply_rows)
    validated_partial_replies = sum(int(item["has_validated_partial_second"]) for item in reply_rows)
    return {
        "first_move_kind": first_kind,
        "first_move": first.uci(),
        "reply_total": reply_total,
        "graph_positive_all_reply_handoff": bool(reply_total > 0 and graph_all_replies == reply_total),
        "graph_positive_any_reply_handoff": bool(graph_all_replies > 0),
        "graph_positive_partial_handoff": bool(graph_partial_replies > 0),
        "validated_all_reply_handoff": bool(reply_total > 0 and validated_all_replies == reply_total),
        "validated_any_reply_handoff": bool(validated_all_replies > 0),
        "validated_partial_handoff": bool(validated_partial_replies > 0),
        "graph_positive_reply_success_rate": 0.0 if reply_total == 0 else graph_all_replies / reply_total,
        "validated_reply_success_rate": 0.0 if reply_total == 0 else validated_all_replies / reply_total,
        "reply_rows": reply_rows,
        "false_basin_quarantine_rows": quarantine_rows,
        "split": split,
        "family": family,
    }


def _audit_second(
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
    response = _validated_foundation_response_details(after_second, parent, response_cache=response_cache)
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
            parent=parent,
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


def _validated_foundation_response_details(
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
    active_terminal_keys: set[str] = set()
    for reply in replies:
        state = after_white_move.copy(stack=False)
        state.push(reply)
        detail = _validate_foundation_response_at_white_turn(state, parent)
        graph_positive_count += int(detail["graph_positive_response"])
        validator_count += int(detail["validator_confirmed_response"])
        graph_types[detail["graph_response_type"]] = graph_types.get(detail["graph_response_type"], 0) + 1
        failure_reasons[detail["validator_failure_reason"]] = failure_reasons.get(detail["validator_failure_reason"], 0) + 1
        selected_mate1.append(detail["selected_mate1_move"])
        selected_mate2.append(detail["selected_mate2_first_move"])
        active_terminal_keys.update(detail["active_tg46d_terminal_keys"])
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
        "active_tg46d_terminal_keys": sorted(active_terminal_keys),
        "validation_mode": "graph_positive_plus_exact_trainer_validation",
    }
    response_cache[key] = result
    return result


def _validate_foundation_response_at_white_turn(
    board: chess.Board,
    parent: dict[str, TerminalAffordanceLearner],
) -> dict[str, Any]:
    active_keys: set[str] = set()
    mate = parent["mate1"].choose(board)
    selected_mate = None if mate is None else mate.uci()
    mate_graph_positive = bool(mate is not None and parent["mate1"].weight_for_move(board, mate) > 0.0)
    if mate is not None and mate in board.legal_moves:
        active_keys.update(_active_terminal_keys(parent["mate1"], board, mate))
    mate_valid = _validate_mate1_response(board, mate)
    first = parent["mate2_first"].choose(board)
    selected_first = None if first is None else first.uci()
    first_graph_positive = bool(first is not None and parent["mate2_first"].weight_for_move(board, first) > 0.0)
    if first is not None and first in board.legal_moves:
        active_keys.update(_active_terminal_keys(parent["mate2_first"], board, first))
    first_valid = _validate_mate2_response(board, first, parent)
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
        "validator_failure_reason": _validator_failure_reason(
            mate=mate,
            first=first,
            mate_graph_positive=mate_graph_positive,
            first_graph_positive=first_graph_positive,
            mate_valid=mate_valid,
            first_valid=first_valid,
        ),
        "selected_mate1_move": selected_mate,
        "selected_mate2_first_move": selected_first,
        "active_tg46d_terminal_keys": sorted(active_keys),
    }


def _validate_mate1_response(board: chess.Board, mate: chess.Move | None) -> bool:
    if mate is None or mate not in board.legal_moves:
        return False
    after = board.copy(stack=False)
    after.push(mate)
    return after.is_checkmate()


def _validate_mate2_response(
    board: chess.Board,
    first: chess.Move | None,
    parent: dict[str, TerminalAffordanceLearner],
) -> bool:
    if first is None or first not in board.legal_moves:
        return False
    if first.uci() in {move.uci() for move in _forced_mate_in_two_first_moves(board)}:
        return True
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


def _validator_failure_reason(
    *,
    mate: chess.Move | None,
    first: chess.Move | None,
    mate_graph_positive: bool,
    first_graph_positive: bool,
    mate_valid: bool,
    first_valid: bool,
) -> str:
    if mate_valid or first_valid:
        return "validator_confirmed"
    if not mate_graph_positive and not first_graph_positive:
        return "no_graph_positive_response"
    if mate_graph_positive and (mate is None):
        return "mate1_no_selected_move"
    if first_graph_positive and (first is None):
        return "mate2_no_selected_move"
    if mate_graph_positive and not mate_valid and not first_graph_positive:
        return "mate1_selected_move_not_checkmate"
    if first_graph_positive and not first_valid and not mate_graph_positive:
        return "mate2_selected_move_not_all_reply_forced"
    return "graph_positive_not_validator_confirmed"


def _quarantine_row(
    *,
    source_row: dict[str, Any],
    first: chess.Move,
    black_reply: chess.Move,
    second: chess.Move,
    after_second: chess.Board,
    first_kind: str,
    response: dict[str, Any],
    parent: dict[str, TerminalAffordanceLearner],
    edge_learner: TerminalAffordanceLearner,
) -> dict[str, Any]:
    board = chess.Board(source_row["fen"])
    active_edge = _active_edge_keys(edge_learner, board, first)
    return {
        "schema_version": "tg47h_false_basin_quarantine.v0",
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
        "active_edge_fence_terminal_keys": active_edge,
        "decoy": _is_decoy(source_row["family"]),
        "blocker_classification": "graph_positive_but_validator_failed_false_basin",
        "learner_visible_labels": False,
    }


def _second_safe(board: chess.Board, move: chess.Move) -> bool:
    after = board.copy(stack=False)
    after.push(move)
    return bool(
        not after.is_stalemate()
        and bool(after.pieces(chess.ROOK, chess.WHITE))
        and not any(reply.to_square in set(after.pieces(chess.ROOK, chess.WHITE)) for reply in after.legal_moves)
    )


def _active_terminal_keys(learner: TerminalAffordanceLearner, board: chess.Board, move: chess.Move) -> list[str]:
    return sorted(
        key
        for key, _scale in terminal_action_feature_keys(
            board,
            move,
            hub=learner.hub,
            feature_cache=learner.feature_cache,
        )
        if key in learner.terminals
    )


def _active_edge_keys(learner: TerminalAffordanceLearner, board: chess.Board, move: chess.Move) -> list[str]:
    keys = {
        key
        for key, _scale in terminal_action_feature_keys(
            board,
            move,
            hub=learner.hub,
            feature_cache=learner.feature_cache,
        )
        if key in learner.terminals
    }
    keys.update(key for key, _scale in _local_progress_terminal_keys(board, move) if key in learner.terminals)
    return sorted(keys)


def _empty_first(first_kind: str, *, first_move: str | None) -> dict[str, Any]:
    return {
        "first_move_kind": first_kind,
        "first_move": first_move,
        "reply_total": 0,
        "graph_positive_all_reply_handoff": False,
        "graph_positive_any_reply_handoff": False,
        "graph_positive_partial_handoff": False,
        "validated_all_reply_handoff": False,
        "validated_any_reply_handoff": False,
        "validated_partial_handoff": False,
        "graph_positive_reply_success_rate": 0.0,
        "validated_reply_success_rate": 0.0,
        "reply_rows": [],
        "false_basin_quarantine_rows": [],
    }


def _best_first_audit(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    if not candidates:
        return _empty_first("oracle_candidate", first_move=None)
    return sorted(
        candidates,
        key=lambda item: (
            int(item["validated_all_reply_handoff"]),
            item["validated_reply_success_rate"],
            int(item["graph_positive_all_reply_handoff"]),
            item["graph_positive_reply_success_rate"],
            item["first_move"] or "",
        ),
        reverse=True,
    )[0]


def _best_second(second_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not second_rows:
        return None
    best = sorted(
        second_rows,
        key=lambda item: (
            int(item["safe"]),
            int(item["validated_all_reply_handoff"]),
            int(item["graph_positive_all_reply_handoff"]),
            int(item["validated_partial_handoff"]),
            int(item["graph_positive_partial_handoff"]),
            item["second_move"],
        ),
        reverse=True,
    )[0]
    return {k: v for k, v in best.items() if k != "quarantine_row"}


def _classify_validated_blocker(*, family: str, selected: dict[str, Any], oracle: dict[str, Any]) -> str:
    if _is_decoy(family):
        if selected["validated_all_reply_handoff"] or oracle["validated_all_reply_handoff"]:
            return "validated_decoy_handoff_leak"
        if selected["graph_positive_all_reply_handoff"] or oracle["graph_positive_all_reply_handoff"]:
            return "graph_positive_decoy_false_basin_quarantined"
        if selected["graph_positive_partial_handoff"] or oracle["graph_positive_partial_handoff"]:
            return "graph_positive_decoy_partial_false_basin_quarantined"
        return "decoy_clean"
    if selected["validated_all_reply_handoff"]:
        return "validated_reachable_with_selected_first"
    if oracle["validated_all_reply_handoff"]:
        return "validated_reachable_with_oracle_first"
    if selected["graph_positive_all_reply_handoff"] or oracle["graph_positive_all_reply_handoff"]:
        return "graph_positive_basin_overgeneralization_quarantined"
    if selected["validated_partial_handoff"] or oracle["validated_partial_handoff"]:
        return "validated_partial_only_support"
    return "foundation_basin_or_objective_blocker"


def _decision(
    *,
    config: ValidatedBasinAcceptanceConfig,
    parent_hash: str,
    parent_before: dict[str, Any],
    parent_after: dict[str, Any],
    audit_rows: list[dict[str, Any]],
    quarantine_rows: list[dict[str, Any]],
    parent_weight_delta: int,
    edge_weight_delta: int,
    total_seconds: float,
) -> dict[str, Any]:
    non_decoy = [row for row in audit_rows if not _is_decoy(row["family"])]
    fence = [row for row in audit_rows if row["family"] == "fence_hold_progress"]
    selected_graph = sum(int(row["selected_first_validated_audit"]["graph_positive_all_reply_handoff"]) for row in non_decoy)
    selected_valid = sum(int(row["selected_first_validated_audit"]["validated_all_reply_handoff"]) for row in non_decoy)
    oracle_graph = sum(int(row["oracle_first_validated_audit"]["graph_positive_all_reply_handoff"]) for row in non_decoy)
    oracle_valid = sum(int(row["oracle_first_validated_audit"]["validated_all_reply_handoff"]) for row in non_decoy)
    decoy_graph_all = sum(int(row["graph_positive_decoy_all_reply_false_handoff"]) for row in audit_rows)
    decoy_graph_partial = sum(int(row["graph_positive_decoy_partial_false_handoff"]) for row in audit_rows)
    decoy_valid_all = sum(int(row["validated_decoy_all_reply_false_handoff"]) for row in audit_rows)
    decoy_valid_partial = sum(int(row["validated_decoy_partial_false_handoff"]) for row in audit_rows)
    if decoy_valid_all > 0 or decoy_valid_partial > 0:
        interpretation = "validated_decoy_handoff_leak"
        next_action = "quarantine_validated_decoy_leak_before_training"
    elif (decoy_graph_all > 0 or decoy_graph_partial > 0) and decoy_valid_all == 0:
        interpretation = "graph_positive_basin_overgeneralization_quarantined"
        next_action = "rerun_tg47g_reachability_with_validated_basin"
    elif non_decoy and oracle_valid / len(non_decoy) >= 0.50:
        interpretation = "validated_handoff_reachability_available"
        next_action = "train_handoff_specific_continuation_materialization"
    else:
        interpretation = "foundation_basin_or_objective_blocker"
        next_action = "repair_tg46d_foundation_basin_or_edge_fence_first_move_objective"
    return {
        "checkpoint_pass": True,
        "checkpoint_interpretation": interpretation,
        "selected_next_action": next_action,
        "repair_applied": True,
        "diagnostic_only": True,
        "quarantine_only": True,
        "validation_mode": "graph_positive_plus_exact_trainer_validation",
        "parent_foundation_hash": parent_hash,
        "parent_foundation_frozen": True,
        "parent_foundation_sanity_before_pass": parent_before["pass"],
        "parent_foundation_sanity_after_pass": parent_after["pass"],
        "parent_foundation_m3_delta_during_audit": 0,
        "parent_foundation_m4_delta_during_audit": 0,
        "parent_foundation_weight_delta_during_audit": parent_weight_delta,
        "edge_learner_weight_delta_during_audit": edge_weight_delta,
        "input_position_count": len(audit_rows),
        "non_decoy_position_count": len(non_decoy),
        "graph_positive_selected_first_reachability_rate": _rate(selected_graph, len(non_decoy)),
        "validated_selected_first_reachability_rate": _rate(selected_valid, len(non_decoy)),
        "graph_positive_oracle_reachability_rate": _rate(oracle_graph, len(non_decoy)),
        "validated_oracle_reachability_rate": _rate(oracle_valid, len(non_decoy)),
        "graph_positive_decoy_all_reply_false_handoff_count": decoy_graph_all,
        "validated_decoy_all_reply_false_handoff_count": decoy_valid_all,
        "graph_positive_decoy_partial_false_handoff_count": decoy_graph_partial,
        "validated_decoy_partial_false_handoff_count": decoy_valid_partial,
        "false_basin_activation_count": len(quarantine_rows),
        "false_basin_activation_by_terminal_key": _count_terminal_keys(quarantine_rows),
        "false_basin_activation_by_family": _counts(row["family"] for row in quarantine_rows),
        "non_decoy_validated_reachable_count": sum(
            int(row["selected_first_validated_audit"]["validated_all_reply_handoff"] or row["oracle_first_validated_audit"]["validated_all_reply_handoff"])
            for row in non_decoy
        ),
        "fence_hold_validated_reachable_count": sum(
            int(row["selected_first_validated_audit"]["validated_all_reply_handoff"] or row["oracle_first_validated_audit"]["validated_all_reply_handoff"])
            for row in fence
        ),
        "oracle_validated_reachable_count": oracle_valid,
        "selected_first_validated_reachable_count": selected_valid,
        "blocker_classification_counts": _counts(row["validated_blocker_classification"] for row in audit_rows),
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
        "rescue_artifacts_loaded": False,
        "total_seconds": total_seconds,
    }


def _learner_snapshot(learner: TerminalAffordanceLearner) -> tuple[tuple[str, float, int, int, int, str], ...]:
    return tuple(
        sorted(
            (
                key,
                terminal.local_weight,
                terminal.positive_credit,
                terminal.negative_credit,
                terminal.neutral_credit,
                terminal.cell.state.name,
            )
            for key, terminal in learner.terminals.items()
        )
    )


def _strip_quarantine(first_audit: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in first_audit.items() if k != "false_basin_quarantine_rows"}


def _strip_audit_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "position_count": len(rows),
        "family_counts": _counts(row["family"] for row in rows),
        "validated_blocker_classification_counts": _counts(row["validated_blocker_classification"] for row in rows),
        "false_basin_quarantine_count": sum(row["false_basin_quarantine_count"] for row in rows),
    }


def _count_terminal_keys(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for key in row.get("active_tg46d_terminal_keys", []):
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:25])


def _counts(values: Iterable[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:
        out[value] = out.get(value, 0) + 1
    return out


def _majority_key(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)[0][0]


def _first_present(values: Iterable[str | None]) -> str | None:
    return next((value for value in values if value), None)


def _rate(count: int, total: int) -> float:
    return 0.0 if total == 0 else count / total


def _is_decoy(family: str) -> bool:
    return family in {"decoy_edge", "hard_decoy_edge"}


def _purity_boundary() -> dict[str, bool]:
    return {
        "diagnostic_only": True,
        "quarantine_only": True,
        "trainer_side_validation_used": True,
        "trainer_side_validation_used_as_runtime_provider": False,
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


def _write_markdown(path: str | Path, result: ValidatedBasinAcceptanceResult) -> None:
    d = result.decision
    lines = [
        "# TG47h Validated Basin Acceptance",
        "",
        f"- Checkpoint pass: {d['checkpoint_pass']}",
        f"- Interpretation: {d['checkpoint_interpretation']}",
        f"- Selected next action: {d['selected_next_action']}",
        f"- Graph-positive selected/oracle reachability: {d['graph_positive_selected_first_reachability_rate']:.3f} / {d['graph_positive_oracle_reachability_rate']:.3f}",
        f"- Validated selected/oracle reachability: {d['validated_selected_first_reachability_rate']:.3f} / {d['validated_oracle_reachability_rate']:.3f}",
        f"- Decoy graph-positive all/partial false handoffs: {d['graph_positive_decoy_all_reply_false_handoff_count']} / {d['graph_positive_decoy_partial_false_handoff_count']}",
        f"- Decoy validated all/partial false handoffs: {d['validated_decoy_all_reply_false_handoff_count']} / {d['validated_decoy_partial_false_handoff_count']}",
        f"- False basin quarantine rows: {d['false_basin_activation_count']}",
        f"- Parent frozen: {d['parent_foundation_frozen']} with M3/M4 deltas {d['parent_foundation_m3_delta_during_audit']} / {d['parent_foundation_m4_delta_during_audit']}",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
