"""TG48a2 diagnostic for hard-decoy labels and same-side rook-danger."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import gzip
import json
from pathlib import Path
import random
import time
from typing import Any, Mapping

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState

from .clean_edge_fence_stage import DEFAULT_TG46D_DIR, _file_sha256, _load_json, _write_json, _write_jsonl_gzip
from .edge_killbox_curriculum import (
    EdgeKillboxCurriculumConfig,
    _choose_move,
    _failure_buckets,
    _foundation_response,
    _generate_family_split,
    _graded_positive_progress,
    _move_metrics,
    _parent_snapshot,
    _rate,
    _rook_capturable_by_reply,
    _score_move,
    _success,
    _terminal_keys,
    _weight_for_move,
)
from .features import extract_learner_features, validate_learner_record
from .handoff_reachability_audit import _foundation_artifact_sanity, _reconstruct_parent_foundation_from_m4_audit
from .real_clean_slate_foundation import _git_head
from .terminal_substrate import TerminalAffordanceLearner
from .validated_reachability_expansion import _validated_foundation_response_details_fast


DEFAULT_TG48A_REPAIR_DIR = Path("reports/autogrowth/clean_slate_krk/tg48a_edge_killbox_repair")
DEFAULT_TG48A2_OUTPUT_DIR = Path("reports/autogrowth/clean_slate_krk/tg48a2_same_side_diagnostic")


@dataclass(frozen=True)
class TG48a2SameSideDiagnosticConfig:
    checkpoint_name: str = "TG48a2_same_side_diagnostic"
    schema_version: str = "krk_tg48a2_same_side_diagnostic.v0"
    output_dir: str = str(DEFAULT_TG48A2_OUTPUT_DIR)
    output_path: str = str(DEFAULT_TG48A2_OUTPUT_DIR / "krk_tg48a2_same_side_diagnostic.json")
    markdown_path: str = str(DEFAULT_TG48A2_OUTPUT_DIR / "krk_tg48a2_same_side_diagnostic.md")
    hard_decoy_relabel_path: str = str(DEFAULT_TG48A2_OUTPUT_DIR / "pools" / "tg48a2_hard_decoy_relabel_audit.jsonl.gz")
    hard_decoy_markdown_path: str = str(DEFAULT_TG48A2_OUTPUT_DIR / "tg48a2_hard_decoy_relabel_audit.md")
    same_side_slice_path: str = str(DEFAULT_TG48A2_OUTPUT_DIR / "pools" / "tg48a2_same_side_slice.jsonl.gz")
    same_side_markdown_path: str = str(DEFAULT_TG48A2_OUTPUT_DIR / "tg48a2_same_side_slice.md")
    terminal_precision_path: str = str(DEFAULT_TG48A2_OUTPUT_DIR / "pools" / "tg48a2_terminal_precision_audit.jsonl.gz")
    source_repair_artifact_path: str = str(DEFAULT_TG48A_REPAIR_DIR / "krk_tg48a_edge_killbox_repair.json")
    source_repair_eval_trace_path: str = str(DEFAULT_TG48A_REPAIR_DIR / "pools" / "tg48a_repair_eval_traces.jsonl.gz")
    parent_foundation_artifact_path: str = str(DEFAULT_TG46D_DIR / "promoted_tg46d_foundation.json")
    parent_foundation_m4_audit_path: str = str(DEFAULT_TG46D_DIR / "pools" / "tg46d_m4_audit.jsonl.gz")
    seed: int = 20260701
    same_side_count: int = 48
    max_generation_attempts: int = 250_000
    top_rejected_affordance_count: int = 20


@dataclass(frozen=True)
class TG48a2SameSideDiagnosticResult:
    config: TG48a2SameSideDiagnosticConfig
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


def run_tg48a2_same_side_diagnostic(
    *,
    config: TG48a2SameSideDiagnosticConfig,
) -> TG48a2SameSideDiagnosticResult:
    start = time.perf_counter()
    repair_artifact = _load_json(config.source_repair_artifact_path)
    repair_eval_rows = _read_jsonl_gzip(config.source_repair_eval_trace_path)
    parent_artifact = _load_json(config.parent_foundation_artifact_path)
    parent_hash = _file_sha256(config.parent_foundation_artifact_path)
    parent = _reconstruct_parent_foundation_from_m4_audit(
        parent_artifact=parent_artifact,
        parent_m4_audit_path=config.parent_foundation_m4_audit_path,
    )
    parent_before = _foundation_artifact_sanity(parent_artifact, parent)
    parent_snapshot = _parent_snapshot(parent)
    m4_learner = _reconstruct_m4_learner(repair_artifact)

    hard_decoy_rows = _hard_decoy_relabel_audit(
        repair_eval_rows=repair_eval_rows,
        parent=parent,
        config=config,
    )
    same_side_rows = _same_side_slice_audit(
        parent=parent,
        m4_learner=m4_learner,
        config=config,
    )
    terminal_rows = _terminal_precision_audit(
        repair_artifact=repair_artifact,
        repair_eval_rows=repair_eval_rows,
        parent=parent,
        config=config,
    )

    _write_jsonl_gzip(config.hard_decoy_relabel_path, hard_decoy_rows)
    _write_jsonl_gzip(config.same_side_slice_path, same_side_rows)
    _write_jsonl_gzip(config.terminal_precision_path, terminal_rows)
    _write_hard_decoy_markdown(config.hard_decoy_markdown_path, hard_decoy_rows)
    _write_same_side_markdown(config.same_side_markdown_path, same_side_rows)

    parent_after = _foundation_artifact_sanity(parent_artifact, parent)
    parent_delta = int(parent_snapshot != _parent_snapshot(parent))
    decision = _decision(
        hard_decoy_rows=hard_decoy_rows,
        same_side_rows=same_side_rows,
        terminal_rows=terminal_rows,
        parent_delta=parent_delta,
        parent_before=parent_before,
        parent_after=parent_after,
        repair_artifact=repair_artifact,
    )
    payload = {
        "provenance": {
            "git_head": _git_head(),
            "source_repair_artifact": config.source_repair_artifact_path,
            "source_repair_eval_trace": config.source_repair_eval_trace_path,
            "parent_foundation_artifact": config.parent_foundation_artifact_path,
            "parent_foundation_hash": parent_hash,
            "old_tg_learned_state_loaded_as_training_data": False,
            "training_applied": False,
            "runtime_behavior_changed": False,
        },
        "parent_foundation": {
            "frozen": True,
            "sanity_before": parent_before,
            "sanity_after": parent_after,
            "m3_delta_during_diagnostic": 0,
            "m4_delta_during_diagnostic": 0,
            "weight_delta_during_diagnostic": parent_delta,
        },
        "artifact_paths": {
            "main": config.output_path,
            "markdown": config.markdown_path,
            "hard_decoy_relabel": config.hard_decoy_relabel_path,
            "hard_decoy_markdown": config.hard_decoy_markdown_path,
            "same_side_slice": config.same_side_slice_path,
            "same_side_markdown": config.same_side_markdown_path,
            "terminal_precision": config.terminal_precision_path,
        },
        "purity_boundary": _purity_boundary(),
        "timing": {"total_seconds": round(time.perf_counter() - start, 6)},
    }
    result = TG48a2SameSideDiagnosticResult(config=config, payload=payload, decision=decision)
    result.write_json()
    _write_main_markdown(config.markdown_path, result)
    return result


def _hard_decoy_relabel_audit(
    *,
    repair_eval_rows: list[dict[str, Any]],
    parent: dict[str, TerminalAffordanceLearner],
    config: TG48a2SameSideDiagnosticConfig,
) -> list[dict[str, Any]]:
    out = []
    response_cache: dict[str, dict[str, Any]] = {}
    for row in repair_eval_rows:
        if not (
            row.get("trace_type") == "TG48a_decoy_M4"
            and row.get("family") == "hard_decoy_edge_killbox"
            and row.get("metrics", {}).get("validated_entry")
        ):
            continue
        board = chess.Board(row["fen"])
        selected = chess.Move.from_uci(row["selected"])
        after = board.copy(stack=False)
        after.push(selected)
        response = _validated_foundation_response_details_fast(after, parent, response_cache=response_cache)
        partial_only = bool(
            response["validator_partial_reply_foundation_response"]
            and not response["validator_all_reply_foundation_response"]
        )
        after_metrics = _move_metrics(
            board,
            selected,
            parent=parent,
            config=EdgeKillboxCurriculumConfig(max_horizon_plies=6),
        )
        classification = _classify_hard_decoy(
            board=board,
            after=after,
            response=response,
            partial_only=partial_only,
            metrics=after_metrics,
        )
        out.append({
            "schema_version": "tg48a2_hard_decoy_relabel.v0",
            "source_trace_type": row["trace_type"],
            "source_index": row["index"],
            "fen": row["fen"],
            "ascii_board": str(board),
            "selected_move": selected.uci(),
            "after_fen": after.fen(),
            "after_ascii_board": str(after),
            "initial_rook_capturable_by_reply": _rook_capturable_by_reply(board),
            "after_rook_capturable_by_reply": _rook_capturable_by_reply(after),
            "after_stalemate": after.is_stalemate(),
            "after_checkmate": after.is_checkmate(),
            "validated_response_details": response,
            "partial_only": partial_only,
            "metrics": after_metrics,
            "classification": classification,
            "relabel_proposal": _relabel_proposal(classification),
            "learner_visible_labels": False,
        })
    return out


def _classify_hard_decoy(
    *,
    board: chess.Board,
    after: chess.Board,
    response: Mapping[str, Any],
    partial_only: bool,
    metrics: Mapping[str, Any],
) -> str:
    if partial_only:
        return "partial_only_boundary"
    if response["validator_all_reply_foundation_response"] and metrics["validated_entry"]:
        if not _rook_capturable_by_reply(board):
            return "hard_decoy_generator_mislabel"
        if _rook_capturable_by_reply(after) or after.is_stalemate():
            return "validator_bug"
        return "legitimate_boundary_positive"
    if response["graph_positive_but_validator_failed_false_basin"]:
        return "true_hard_decoy_leak"
    if metrics["validated_entry"] and not response["validator_all_reply_foundation_response"]:
        return "validator_bug"
    return "ambiguous"


def _relabel_proposal(classification: str) -> str:
    return {
        "true_hard_decoy_leak": "keep_as_hard_decoy_negative_and_tighten_veto_debt",
        "hard_decoy_generator_mislabel": "remove_from_hard_decoy_pool_or_require_initial_rook_risk",
        "legitimate_boundary_positive": "move_to_boundary_positive_or_near_foundation_pool",
        "partial_only_boundary": "move_to_partial_boundary_pool_not_full_success",
        "validator_bug": "fix_validator_before_training",
        "ambiguous": "manual_review_before_credit",
    }[classification]


def _same_side_slice_audit(
    *,
    parent: dict[str, TerminalAffordanceLearner],
    m4_learner: TerminalAffordanceLearner,
    config: TG48a2SameSideDiagnosticConfig,
) -> list[dict[str, Any]]:
    rng = random.Random(config.seed)
    rows = _generate_family_split(
        rng=rng,
        split="tg48a2_same_side",
        family="edge_killbox_same_side_rook_danger",
        count=config.same_side_count,
        used=set(),
        used_lineage={},
        max_attempts=config.max_generation_attempts,
    )
    out = []
    eval_config = EdgeKillboxCurriculumConfig(max_horizon_plies=6)
    for index, row in enumerate(rows):
        board = chess.Board(row["fen"])
        parent_move = _choose_move(board, parent=parent, learner=None)
        m4_move = _choose_move(board, parent=parent, learner=m4_learner)
        parent_metrics = _move_metrics(board, parent_move, parent=parent, config=eval_config)
        m4_metrics = _move_metrics(board, m4_move, parent=parent, config=eval_config)
        oracle = _oracle_safe_validated_move(board, parent=parent, config=eval_config)
        lateral = _safe_lateral_rook_moves(board, parent=parent, config=eval_config)
        m4_is_lateral = bool(m4_move is not None and m4_move.uci() in {item["move"] for item in lateral})
        parent_is_lateral = bool(parent_move is not None and parent_move.uci() in {item["move"] for item in lateral})
        out.append({
            "schema_version": "tg48a2_same_side_slice.v0",
            "index": index,
            "fen": row["fen"],
            "ascii_board": str(board),
            "family": row["family"],
            "geometry_summary": row["geometry_summary"],
            "parent_selected_move": None if parent_move is None else parent_move.uci(),
            "parent_success": _success(parent_metrics),
            "parent_metrics": parent_metrics,
            "m4_selected_move": None if m4_move is None else m4_move.uci(),
            "m4_success": _success(m4_metrics),
            "m4_metrics": m4_metrics,
            "bounded_oracle": oracle,
            "safe_lateral_rook_moves": lateral,
            "safe_lateral_rook_move_exists": bool(lateral),
            "parent_selects_lateral_rook": parent_is_lateral,
            "m4_selects_lateral_rook": m4_is_lateral,
            "feature_distinguishes_lateral_rook_from_king_walk": _feature_distinguishes_lateral_rook_from_king_walk(board),
            "learner_visible_labels": False,
        })
    return out


def _oracle_safe_validated_move(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner],
    config: EdgeKillboxCurriculumConfig,
) -> dict[str, Any]:
    candidates = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        metrics = _move_metrics(board, move, parent=parent, config=config)
        if (
            not metrics["illegal"]
            and not metrics["rook_blunder"]
            and not metrics["rook_missing"]
            and not metrics["stalemate"]
            and not metrics["confinement_regression"]
            and not metrics["partial_only_near_basin"]
            and not metrics["graph_positive_false_basin"]
        ):
            candidates.append({
                "move": move.uci(),
                "success": _success(metrics),
                "validated_entry": metrics["validated_entry"],
                "validated_mate1_entry": metrics["validated_mate1_entry"],
                "validated_mate2_entry": metrics["validated_mate2_entry"],
                "graded_positive_progress": metrics["graded_positive_progress"],
                "metrics": metrics,
                "parent_score": _score_move(board, move, parent=parent, learner=None),
            })
    candidates.sort(key=lambda item: (item["success"], item["validated_entry"], item["graded_positive_progress"], item["parent_score"], item["move"]), reverse=True)
    best = candidates[0] if candidates else None
    return {
        "safe_candidate_count": len(candidates),
        "validated_success_available": bool(best and best["success"]),
        "validated_entry_available": any(item["validated_entry"] for item in candidates),
        "best_move": None if best is None else best["move"],
        "best_success": bool(best and best["success"]),
        "best_metrics": None if best is None else best["metrics"],
    }


def _safe_lateral_rook_moves(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner],
    config: EdgeKillboxCurriculumConfig,
) -> list[dict[str, Any]]:
    out = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        piece = board.piece_at(move.from_square)
        if piece is None or piece.color != chess.WHITE or piece.piece_type != chess.ROOK:
            continue
        metrics = _move_metrics(board, move, parent=parent, config=config)
        after = board.copy(stack=False)
        after.push(move)
        if (
            not metrics["rook_blunder"]
            and not metrics["rook_missing"]
            and not metrics["stalemate"]
            and not metrics["confinement_regression"]
            and not metrics["partial_only_near_basin"]
        ):
            out.append({
                "move": move.uci(),
                "validated_entry": metrics["validated_entry"],
                "graded_positive_progress": _graded_positive_progress(board, after),
                "metrics": metrics,
            })
    return out


def _feature_distinguishes_lateral_rook_from_king_walk(board: chess.Board) -> dict[str, Any]:
    rook_keys: set[str] = set()
    king_keys: set[str] = set()
    for move in board.legal_moves:
        piece = board.piece_at(move.from_square)
        if piece is None or piece.color != chess.WHITE:
            continue
        keys = {key for key, _scale in _terminal_keys(board, move)}
        if piece.piece_type == chess.ROOK:
            rook_keys.update(keys)
        elif piece.piece_type == chess.KING:
            king_keys.update(keys)
    unique_rook = sorted(key for key in rook_keys - king_keys if key.startswith(("action_geometry:", "compound_")))[:20]
    return {
        "rook_action_key_count": len(rook_keys),
        "king_action_key_count": len(king_keys),
        "unique_rook_action_key_count": len(rook_keys - king_keys),
        "unique_rook_action_key_examples": unique_rook,
    }


def _terminal_precision_audit(
    *,
    repair_artifact: Mapping[str, Any],
    repair_eval_rows: list[dict[str, Any]],
    parent: dict[str, TerminalAffordanceLearner],
    config: TG48a2SameSideDiagnosticConfig,
) -> list[dict[str, Any]]:
    candidate_rows = repair_artifact["m4_audit"]["candidate_rows"]
    promoted = [row for row in candidate_rows if row.get("promoted_as") == "affordance"]
    rejected = [
        row for row in candidate_rows
        if row.get("local_weight", 0.0) > 0.0 and not row.get("promoted")
    ]
    rejected.sort(key=lambda item: (item.get("local_weight", 0.0), item.get("positive_intervention_count", 0)), reverse=True)
    targets = promoted + rejected[:config.top_rejected_affordance_count]
    target_keys = {row["terminal_key"] for row in targets}
    eval_config = EdgeKillboxCurriculumConfig(max_horizon_plies=6)
    activation = {
        key: {
            "terminal_key": key,
            "activation_count": 0,
            "decoy_activation_count": 0,
            "hard_decoy_activation_count": 0,
            "unsafe_activation_count": 0,
            "same_side_activation_count": 0,
            "opposed_side_activation_count": 0,
            "same_side_validated_success_activation_count": 0,
            "opposed_side_validated_success_activation_count": 0,
            "validated_success_activation_count": 0,
            "false_basin_activation_count": 0,
        }
        for key in target_keys
    }
    unique_positions = _unique_eval_positions(repair_eval_rows)
    for row in unique_positions:
        board = chess.Board(row["fen"])
        for move in board.legal_moves:
            keys = {key for key, _scale in _terminal_keys(board, move)}
            active_targets = keys & target_keys
            if not active_targets:
                continue
            metrics = _move_metrics(board, move, parent=parent, config=eval_config)
            unsafe = bool(metrics["rook_blunder"] or metrics["rook_missing"] or metrics["stalemate"] or metrics["illegal"] or metrics["confinement_regression"])
            for key in active_targets:
                item = activation[key]
                item["activation_count"] += 1
                item["decoy_activation_count"] += int(row["family"] == "decoy_edge_killbox")
                item["hard_decoy_activation_count"] += int(row["family"] == "hard_decoy_edge_killbox")
                item["unsafe_activation_count"] += int(unsafe)
                item["same_side_activation_count"] += int(row["family"] == "edge_killbox_same_side_rook_danger")
                item["opposed_side_activation_count"] += int(row["family"] == "edge_killbox_opposed_side")
                validated_success = bool(metrics["validated_entry"] and not metrics["graph_positive_false_basin"])
                item["validated_success_activation_count"] += int(validated_success)
                item["same_side_validated_success_activation_count"] += int(
                    row["family"] == "edge_killbox_same_side_rook_danger" and validated_success
                )
                item["opposed_side_validated_success_activation_count"] += int(
                    row["family"] == "edge_killbox_opposed_side" and validated_success
                )
                item["false_basin_activation_count"] += int(metrics["graph_positive_false_basin"])
    out = []
    for row in targets:
        item = dict(activation[row["terminal_key"]])
        same = item["same_side_activation_count"]
        opposed = item["opposed_side_activation_count"]
        item.update({
            "schema_version": "tg48a2_terminal_precision.v0",
            "promoted": bool(row.get("promoted")),
            "promoted_as": row.get("promoted_as"),
            "positive_support": row.get("positive_intervention_count", 0),
            "negative_support": row.get("negative_intervention_count", 0),
            "local_weight": row.get("local_weight", 0.0),
            "precision": row.get("precision", 0.0),
            "same_side_precision": _rate(item["same_side_validated_success_activation_count"], same) if same else None,
            "opposed_side_precision": _rate(item["opposed_side_validated_success_activation_count"], opposed) if opposed else None,
            "classification": _terminal_precision_classification(item),
            "learner_visible_labels": False,
        })
        validate_learner_record({"terminal_key": item["terminal_key"]})
        out.append(item)
    return out


def _terminal_precision_classification(item: Mapping[str, Any]) -> str:
    if item["hard_decoy_activation_count"] or item["decoy_activation_count"]:
        return "decoy_contaminated"
    if item["false_basin_activation_count"]:
        return "false_basin_contaminated"
    if item["same_side_activation_count"] and not item["opposed_side_activation_count"]:
        return "same_side_specific"
    if item["opposed_side_activation_count"] and not item["same_side_activation_count"]:
        return "opposed_side_only"
    if item["same_side_activation_count"] and item["opposed_side_activation_count"]:
        return "mixed_too_broad"
    return "unactivated_on_audit_slice"


def _unique_eval_positions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["fen"], row["family"])
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _decision(
    *,
    hard_decoy_rows: list[dict[str, Any]],
    same_side_rows: list[dict[str, Any]],
    terminal_rows: list[dict[str, Any]],
    parent_delta: int,
    parent_before: Mapping[str, Any],
    parent_after: Mapping[str, Any],
    repair_artifact: Mapping[str, Any],
) -> dict[str, Any]:
    hard_counts = _counts(row["classification"] for row in hard_decoy_rows)
    same_total = len(same_side_rows)
    same_parent_success = sum(int(row["parent_success"]) for row in same_side_rows)
    same_m4_success = sum(int(row["m4_success"]) for row in same_side_rows)
    same_oracle_success = sum(int(row["bounded_oracle"]["validated_success_available"]) for row in same_side_rows)
    safe_lateral = sum(int(row["safe_lateral_rook_move_exists"]) for row in same_side_rows)
    m4_lateral = sum(int(row["m4_selects_lateral_rook"]) for row in same_side_rows)
    promoted = [row for row in terminal_rows if row["promoted_as"] == "affordance"]
    promoted_same_activations = sum(row["same_side_activation_count"] for row in promoted)
    promoted_opposed_activations = sum(row["opposed_side_activation_count"] for row in promoted)
    promoted_same_success = sum(row["same_side_validated_success_activation_count"] for row in promoted)
    promoted_opposed_success = sum(row["opposed_side_validated_success_activation_count"] for row in promoted)
    hard_mislabels = hard_counts.get("hard_decoy_generator_mislabel", 0)
    legitimate = hard_counts.get("legitimate_boundary_positive", 0)
    generator_mislabel_total = hard_mislabels + legitimate
    true_leaks = hard_counts.get("true_hard_decoy_leak", 0)
    validator_bugs = hard_counts.get("validator_bug", 0)
    same_oracle_rate = _rate(same_oracle_success, same_total)
    same_m4_rate = _rate(same_m4_success, same_total)
    if generator_mislabel_total > 0:
        interpretation = "hard_decoy_generator_mislabels_boundary_positions"
        next_action = "repair_hard_decoy_generator_then_rerun_tg48a_repair"
    elif true_leaks > 0:
        interpretation = "true_hard_decoy_leak_blocks_training"
        next_action = "tighten_false_basin_debt_and_decoy_vetoes"
    elif same_oracle_rate < 0.25:
        interpretation = "same_side_target_not_available_under_current_horizon"
        next_action = "extend_same_side_horizon_or_add_trainer_side_DTM_reward"
    elif same_oracle_rate >= 0.25 and same_m4_rate == 0.0:
        interpretation = "same_side_affordance_selection_blocker"
        next_action = "train_same_side_lateral_rook_affordance_microstage"
    else:
        interpretation = "ready_for_narrow_same_side_repair"
        next_action = "implement_tg48a2_same_side_microstage"
    return {
        "checkpoint_pass": bool(parent_delta == 0 and parent_before["pass"] and parent_after["pass"]),
        "checkpoint_interpretation": interpretation,
        "selected_next_action": next_action,
        "hard_decoy_false_handoff_count": len(hard_decoy_rows),
        "hard_decoy_generator_mislabel_count": generator_mislabel_total,
        "hard_decoy_generator_strict_mislabel_count": hard_mislabels,
        "legitimate_boundary_positive_count": legitimate,
        "true_hard_decoy_leak_count": true_leaks,
        "partial_only_boundary_count": hard_counts.get("partial_only_boundary", 0),
        "validator_bug_count": validator_bugs,
        "ambiguous_hard_decoy_count": hard_counts.get("ambiguous", 0),
        "same_side_position_count": same_total,
        "same_side_parent_success_rate": _rate(same_parent_success, same_total),
        "same_side_m4_success_rate": same_m4_rate,
        "same_side_oracle_validated_success_rate": same_oracle_rate,
        "same_side_safe_lateral_rook_move_available_rate": _rate(safe_lateral, same_total),
        "same_side_current_graph_selects_lateral_rook_rate": _rate(m4_lateral, same_total),
        "promoted_affordance_same_side_precision": _rate(promoted_same_success, promoted_same_activations) if promoted_same_activations else None,
        "promoted_affordance_opposed_side_precision": _rate(promoted_opposed_success, promoted_opposed_activations) if promoted_opposed_activations else None,
        "promoted_affordance_false_basin_activation_count": sum(row["false_basin_activation_count"] for row in promoted),
        "promoted_affordance_hard_decoy_activation_count": sum(row["hard_decoy_activation_count"] for row in promoted),
        "terminal_precision_classification_counts": _counts(row["classification"] for row in terminal_rows),
        "parent_frozen_deltas": {
            "m3": 0,
            "m4": 0,
            "weight": parent_delta,
        },
        "source_repair_behavioral_advancement": repair_artifact["decision"]["behavioral_advancement"],
        **_purity_boundary(),
    }


def _reconstruct_m4_learner(repair_artifact: Mapping[str, Any]) -> TerminalAffordanceLearner:
    learner = TerminalAffordanceLearner.create(eta_m3=0.08, rich_feature_credit_scale=0.25)
    for row in repair_artifact["m4_audit"]["candidate_rows"]:
        if not row.get("promoted"):
            continue
        terminal = learner.get_terminal(row["terminal_key"])
        terminal.local_weight = float(row["local_weight"])
        terminal.positive_credit = int(row["positive_intervention_count"])
        terminal.negative_credit = int(row["negative_intervention_count"])
        terminal.neutral_credit = int(row["neutral_count"])
        terminal.cell.state = StemCellState.MATURE
    return learner


def _read_jsonl_gzip(path: str | Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def _counts(values) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:
        out[str(value)] = out.get(str(value), 0) + 1
    return dict(sorted(out.items()))


def _piece_coordinates(board: chess.Board) -> str:
    return ", ".join(
        (piece.symbol().upper() if piece.color == chess.WHITE else piece.symbol().lower()) + chess.square_name(square)
        for square, piece in sorted(board.piece_map().items())
    )


def _write_hard_decoy_markdown(path: str | Path, rows: list[dict[str, Any]]) -> None:
    lines = ["# TG48a2 Hard-Decoy Relabel Audit", ""]
    lines.append(f"- Audited hard-decoy false handoffs: {len(rows)}")
    lines.append(f"- Classifications: `{_counts(row['classification'] for row in rows)}`")
    lines.append("")
    for row in rows:
        lines.extend([
            f"## Source index {row['source_index']}",
            "",
            f"- Classification: `{row['classification']}`",
            f"- Relabel proposal: `{row['relabel_proposal']}`",
            f"- FEN: `{row['fen']}`",
            f"- Pieces: `{_piece_coordinates(chess.Board(row['fen']))}`",
            f"- Selected move: `{row['selected_move']}`",
            f"- After FEN: `{row['after_fen']}`",
            f"- Validator all/partial: `{row['validated_response_details']['validator_all_reply_foundation_response']}` / `{row['validated_response_details']['validator_partial_reply_foundation_response']}`",
            "",
            "Before:",
            "```text",
            row["ascii_board"],
            "```",
            "",
            "After:",
            "```text",
            row["after_ascii_board"],
            "```",
            "",
        ])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _write_same_side_markdown(path: str | Path, rows: list[dict[str, Any]]) -> None:
    total = len(rows)
    lines = [
        "# TG48a2 Same-Side Rook-Danger Slice",
        "",
        f"- Positions: {total}",
        f"- Parent success: {_rate(sum(int(row['parent_success']) for row in rows), total):.3f}",
        f"- M4 success: {_rate(sum(int(row['m4_success']) for row in rows), total):.3f}",
        f"- Oracle validated success available: {_rate(sum(int(row['bounded_oracle']['validated_success_available']) for row in rows), total):.3f}",
        f"- Safe lateral rook move available: {_rate(sum(int(row['safe_lateral_rook_move_exists']) for row in rows), total):.3f}",
        f"- M4 selects lateral rook: {_rate(sum(int(row['m4_selects_lateral_rook']) for row in rows), total):.3f}",
        "",
    ]
    for row in rows[:20]:
        lines.extend([
            f"## Index {row['index']}",
            "",
            f"- FEN: `{row['fen']}`",
            f"- Pieces: `{_piece_coordinates(chess.Board(row['fen']))}`",
            f"- Parent: `{row['parent_selected_move']}` success `{row['parent_success']}`",
            f"- M4: `{row['m4_selected_move']}` success `{row['m4_success']}` lateral `{row['m4_selects_lateral_rook']}`",
            f"- Oracle best: `{row['bounded_oracle']['best_move']}` success `{row['bounded_oracle']['best_success']}`",
            f"- Safe lateral moves: `{[item['move'] for item in row['safe_lateral_rook_moves']]}`",
            "",
            "```text",
            row["ascii_board"],
            "```",
            "",
        ])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _write_main_markdown(path: str | Path, result: TG48a2SameSideDiagnosticResult) -> None:
    d = result.decision
    lines = [
        "# TG48a2 Same-Side Diagnostic",
        "",
        f"- Checkpoint pass: {d['checkpoint_pass']}",
        f"- Interpretation: {d['checkpoint_interpretation']}",
        f"- Selected next action: {d['selected_next_action']}",
        f"- Hard-decoy false handoffs: {d['hard_decoy_false_handoff_count']}",
        f"- Hard-decoy relabel counts generator/legitimate/leak/partial/validator: {d['hard_decoy_generator_mislabel_count']} / {d['legitimate_boundary_positive_count']} / {d['true_hard_decoy_leak_count']} / {d['partial_only_boundary_count']} / {d['validator_bug_count']}",
        f"- Same-side parent/M4/oracle success: {d['same_side_parent_success_rate']:.3f} / {d['same_side_m4_success_rate']:.3f} / {d['same_side_oracle_validated_success_rate']:.3f}",
        f"- Same-side safe lateral available / M4 selects lateral: {d['same_side_safe_lateral_rook_move_available_rate']:.3f} / {d['same_side_current_graph_selects_lateral_rook_rate']:.3f}",
        f"- Promoted affordance same/opposed precision: {d['promoted_affordance_same_side_precision']} / {d['promoted_affordance_opposed_side_precision']}",
        f"- Promoted affordance false-basin / hard-decoy activations: {d['promoted_affordance_false_basin_activation_count']} / {d['promoted_affordance_hard_decoy_activation_count']}",
        f"- Parent frozen deltas M3/M4/weight: {d['parent_frozen_deltas']['m3']} / {d['parent_frozen_deltas']['m4']} / {d['parent_frozen_deltas']['weight']}",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _purity_boundary() -> dict[str, bool]:
    return {
        "runtime_tablebase_or_dtm_move_source": False,
        "stockfish_runtime_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "hardcoded_fen_or_move_repair": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "basin_labels_learner_visible": False,
        "curriculum_labels_learner_visible": False,
        "tempo_opposition_labels_learner_visible": False,
        "quality_depth_reply_policy_labels_learner_visible": False,
        "trainer_side_labels_used_as_runtime_provider": False,
        "diagnostic_only": True,
        "training_applied": False,
    }
