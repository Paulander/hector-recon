"""TG48a edge-killbox curriculum between TG46d foundation and broad TG47."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import gzip
import json
import os
from pathlib import Path
import random
import statistics
import time
from typing import Any, Iterable, Mapping

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState

from .clean_edge_fence_stage import (
    DEFAULT_TG46D_DIR,
    _file_sha256,
    _hash_json,
    _load_json,
    _write_json,
    _write_jsonl_gzip,
)
from .features import extract_learner_features, validate_learner_record
from .foundation_curriculum import _mate_moves, _random_krk_board, _valid_foundation_board
from .handoff_reachability_audit import (
    _foundation_artifact_sanity,
    _reconstruct_parent_foundation_from_m4_audit,
)
from .real_clean_slate_foundation import _git_head
from .terminal_substrate import TerminalAffordanceLearner
from .validated_reachability_expansion import _validated_foundation_response_details_fast


DEFAULT_OUTPUT_DIR = Path("reports/autogrowth/clean_slate_krk/tg48a_edge_killbox_curriculum")
DEFAULT_REPAIR_OUTPUT_DIR = Path("reports/autogrowth/clean_slate_krk/tg48a_edge_killbox_repair")
_FOUNDATION_RESPONSE_CACHE: dict[str, dict[str, Any]] = {}


@dataclass(frozen=True)
class EdgeKillboxCurriculumConfig:
    checkpoint_name: str = "TG48a_edge_killbox_curriculum"
    schema_version: str = "krk_tg48a_edge_killbox_curriculum.v0"
    run_scale_label: str = "smoke"
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    output_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg48a_edge_killbox_curriculum.json")
    markdown_path: str = str(DEFAULT_OUTPUT_DIR / "krk_tg48a_edge_killbox_curriculum.md")
    train_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a_train_traces.jsonl.gz")
    eval_trace_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a_eval_traces.jsonl.gz")
    failure_pool_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a_failure_pool.jsonl.gz")
    generator_samples_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a_generator_samples.jsonl.gz")
    graph_summary_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a_graph_summary.json")
    board_sample_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a_repair_board_samples.md")
    boundary_positive_path: str = str(DEFAULT_OUTPUT_DIR / "pools" / "tg48a_boundary_positive_routed.jsonl.gz")
    parent_foundation_artifact_path: str = str(DEFAULT_TG46D_DIR / "promoted_tg46d_foundation.json")
    parent_foundation_m4_audit_path: str = str(DEFAULT_TG46D_DIR / "pools" / "tg46d_m4_audit.jsonl.gz")
    seed: int = 20260630
    train_count: int = 60
    heldout_count: int = 24
    regression_count: int = 24
    decoy_count: int = 24
    hard_decoy_count: int = 24
    max_generation_attempts: int = 250_000
    max_horizon_plies: int = 6
    eta_m3: float = 0.08
    rich_feature_credit_scale: float = 0.25
    m4_precision_threshold: float = 0.62
    m4_affordance_precision_threshold: float = 0.70
    m4_veto_precision_threshold: float = 0.62
    m4_min_positive_support: int = 4
    m4_min_negative_support: int = 4
    m4_max_decoy_false_handoff_activation: int = 0
    m4_max_unsafe_activation: int = 0
    m3_plus_m4_trial_scale: float = 0.25
    sample_boards_per_family: int = 20


@dataclass(frozen=True)
class EdgeKillboxCurriculumResult:
    config: EdgeKillboxCurriculumConfig
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


def run_edge_killbox_curriculum(*, config: EdgeKillboxCurriculumConfig) -> EdgeKillboxCurriculumResult:
    start = time.perf_counter()
    _FOUNDATION_RESPONSE_CACHE.clear()
    parent_artifact = _load_json(config.parent_foundation_artifact_path)
    parent_hash = _file_sha256(config.parent_foundation_artifact_path)
    parent = _reconstruct_parent_foundation_from_m4_audit(
        parent_artifact=parent_artifact,
        parent_m4_audit_path=config.parent_foundation_m4_audit_path,
    )
    parent_before = _foundation_artifact_sanity(parent_artifact, parent)
    parent_snapshot = _parent_snapshot(parent)
    datasets = generate_edge_killbox_datasets(config)
    datasets, hard_decoy_gate = _repair_hard_decoy_pool(datasets=datasets, parent=parent, config=config)
    label_source = _label_source()
    samples = _sample_rows(datasets, limit=config.sample_boards_per_family)
    _write_jsonl_gzip(config.generator_samples_path, samples)
    _write_jsonl_gzip(config.boundary_positive_path, datasets.get("boundary_positive", []))

    learner = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.rich_feature_credit_scale,
    )
    train_rows = _train_child(
        datasets["train"] + datasets["decoy"] + datasets["hard_decoy"],
        learner=learner,
        parent=parent,
        label_source=label_source,
        config=config,
    )
    _write_jsonl_gzip(config.train_trace_path, train_rows)

    parent_only = _evaluate_rows(datasets["heldout"], parent=parent, learner=None, trace_type="parent_TG46d_only", config=config)
    m3_only = _evaluate_rows(datasets["heldout"], parent=parent, learner=learner, trace_type="TG48a_M3_trial_only", config=config)
    no_foundation = _evaluate_rows(datasets["heldout"], parent=None, learner=learner, trace_type="no_foundation_control", config=config)
    terminal_audit = _terminal_activation_audit(
        learner,
        datasets["train"] + datasets["heldout"] + datasets["decoy"] + datasets["hard_decoy"],
        parent=parent,
        config=config,
    )
    m4_learner, m4_audit = _promote_m4(learner, terminal_audit=terminal_audit, config=config)
    m4_only = _evaluate_rows(datasets["heldout"], parent=parent, learner=m4_learner, trace_type="TG48a_M4_consolidated_only", config=config)
    m3_plus_m4 = _evaluate_rows(
        datasets["heldout"],
        parent=parent,
        learner=_combine_learners(m3=learner, m4=m4_learner, trial_scale=config.m3_plus_m4_trial_scale),
        trace_type="TG48a_true_M3_plus_M4",
        config=config,
    )
    regression_m4 = _evaluate_rows(datasets["regression"], parent=parent, learner=m4_learner, trace_type="TG48a_regression_M4", config=config)
    decoy_eval = _evaluate_rows(
        datasets["decoy"] + datasets["hard_decoy"],
        parent=parent,
        learner=m4_learner,
        trace_type="TG48a_decoy_M4",
        config=config,
    )
    same_side_oracle = _same_side_oracle_summary(datasets["heldout"], parent=parent, config=config)
    ablation = {
        "mask_M4_structures": _strip_rows(parent_only),
        "m4_causal_success_delta_vs_parent": round(m4_only["success_rate"] - parent_only["success_rate"], 6),
        "m4_causal_validated_entry_delta_vs_parent": round(
            m4_only["validated_entry_rate"] - parent_only["validated_entry_rate"],
            6,
        ),
    }
    eval_rows = parent_only["rows"] + m3_only["rows"] + no_foundation["rows"] + m4_only["rows"] + m3_plus_m4["rows"] + regression_m4["rows"] + decoy_eval["rows"]
    failure_rows = [row for row in eval_rows if row.get("failure_buckets")]
    _write_jsonl_gzip(config.eval_trace_path, eval_rows)
    _write_jsonl_gzip(config.failure_pool_path, failure_rows)
    _write_board_samples(config.board_sample_path, eval_rows, m4_audit=m4_audit)
    graph_summary = _graph_summary(learner=learner, m4_learner=m4_learner, m4_audit=m4_audit)
    _write_json(config.graph_summary_path, graph_summary)
    parent_after = _foundation_artifact_sanity(parent_artifact, parent)
    parent_delta = int(parent_snapshot != _parent_snapshot(parent))
    total_seconds = round(time.perf_counter() - start, 6)
    decision = _decision(
        config=config,
        parent_hash=parent_hash,
        parent_before=parent_before,
        parent_after=parent_after,
        parent_delta=parent_delta,
        datasets=datasets,
        label_source=label_source,
        learner=learner,
        m4_audit=m4_audit,
        parent_only=parent_only,
        m3_only=m3_only,
        no_foundation=no_foundation,
        m4_only=m4_only,
        m3_plus_m4=m3_plus_m4,
        regression_m4=regression_m4,
        decoy_eval=decoy_eval,
        ablation=ablation,
        hard_decoy_gate=hard_decoy_gate,
        same_side_oracle=same_side_oracle,
        total_seconds=total_seconds,
    )
    payload = {
        "provenance": {
            "git_head": _git_head(),
            "parent_foundation_artifact": config.parent_foundation_artifact_path,
            "parent_foundation_hash": parent_hash,
            "parent_foundation_m4_audit": config.parent_foundation_m4_audit_path,
            "config_hash": _hash_json(asdict(config)),
            "old_tg_pools_loaded": 0,
            "old_tg_learned_state_loaded_as_training_data": False,
            "child_branch_loaded": False,
            "runtime_tablebase_or_dtm_move_source": False,
        },
        "parent_foundation": {
            "frozen": True,
            "sanity_before": parent_before,
            "sanity_after": parent_after,
            "m3_delta_during_stage": 0,
            "m4_delta_during_stage": 0,
            "weight_delta_during_stage": parent_delta,
        },
        "datasets": _dataset_summary(datasets),
        "label_source": label_source,
        "evaluation": {
            "parent_TG46d_only": _strip_rows(parent_only),
            "TG48a_M3_trial_only": _strip_rows(m3_only),
            "TG48a_M4_consolidated_only": _strip_rows(m4_only),
            "TG48a_true_M3_plus_M4": _strip_rows(m3_plus_m4),
            "no_foundation_control": _strip_rows(no_foundation),
            "decoy_hard_decoy": _strip_rows(decoy_eval),
            "regression_M4": _strip_rows(regression_m4),
        },
        "m4_audit": m4_audit,
        "hard_decoy_gate": hard_decoy_gate,
        "same_side_oracle": same_side_oracle,
        "ablation_results": ablation,
        "graph_summary": graph_summary,
        "artifact_paths": {
            "main": config.output_path,
            "markdown": config.markdown_path,
            "train_traces": config.train_trace_path,
            "eval_traces": config.eval_trace_path,
            "failure_pool": config.failure_pool_path,
            "generator_samples": config.generator_samples_path,
            "graph_summary": config.graph_summary_path,
            "board_samples": config.board_sample_path,
            "boundary_positive_routed": config.boundary_positive_path,
        },
        "purity_boundary": _purity_boundary(),
        "timing": {"total_seconds": total_seconds},
    }
    result = EdgeKillboxCurriculumResult(config=config, payload=payload, decision=decision)
    result.write_json()
    _write_markdown(config.markdown_path, result)
    return result


def generate_edge_killbox_datasets(config: EdgeKillboxCurriculumConfig) -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(config.seed)
    used: set[str] = set()
    used_lineage: dict[str, str] = {}
    datasets = {
        "train": _generate_split(
            rng=rng,
            split="train",
            count=config.train_count,
            used=used,
            used_lineage=used_lineage,
            max_attempts=config.max_generation_attempts,
        ),
        "heldout": _generate_split(
            rng=rng,
            split="heldout",
            count=config.heldout_count,
            used=used,
            used_lineage=used_lineage,
            max_attempts=config.max_generation_attempts,
        ),
        "regression": _generate_split(
            rng=rng,
            split="regression",
            count=config.regression_count,
            used=used,
            used_lineage=used_lineage,
            max_attempts=config.max_generation_attempts,
        ),
        "decoy": _generate_family_split(
            rng=rng,
            split="decoy",
            family="decoy_edge_killbox",
            count=config.decoy_count,
            used=used,
            used_lineage=used_lineage,
            max_attempts=config.max_generation_attempts,
        ),
        "hard_decoy": _generate_family_split(
            rng=rng,
            split="hard_decoy",
            family="hard_decoy_edge_killbox",
            count=config.hard_decoy_count,
            used=used,
            used_lineage=used_lineage,
            max_attempts=config.max_generation_attempts,
        ),
    }
    return datasets


def _repair_hard_decoy_pool(
    *,
    datasets: dict[str, list[dict[str, Any]]],
    parent: dict[str, TerminalAffordanceLearner],
    config: EdgeKillboxCurriculumConfig,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    """Keep hard-decoy rows validator-negative and route positives elsewhere.

    This is trainer-side pool hygiene. Routed boundary-positive rows are not used
    as negative credit and are not exposed as learner-visible labels.
    """

    repaired = {key: list(value) for key, value in datasets.items()}
    original = list(repaired.get("hard_decoy", []))
    accepted: list[dict[str, Any]] = []
    routed: list[dict[str, Any]] = []
    counts: dict[str, int] = {
        "accepted_hard_decoy": 0,
        "legitimate_boundary_positive": 0,
        "partial_only_boundary": 0,
        "invalid_generated": 0,
    }
    used = {row["fen"] for rows in repaired.values() for row in rows}
    used_lineage = {row["lineage_key"]: row.get("split", "") for rows in repaired.values() for row in rows}

    def consider(row: dict[str, Any]) -> None:
        gate = _hard_decoy_gate(row, parent=parent, config=config)
        counts[gate["classification"]] = counts.get(gate["classification"], 0) + 1
        if gate["classification"] == "accepted_hard_decoy":
            accepted.append(row)
            return
        routed_row = dict(row)
        routed_row["split"] = "boundary_positive"
        routed_row["original_split"] = row.get("split")
        routed_row["routed_from"] = "hard_decoy_edge_killbox"
        routed_row["routing_classification"] = gate["classification"]
        routed_row["routing_reason"] = gate["reason"]
        routed_row["routing_move"] = gate.get("move")
        routed_row["routing_metrics"] = gate.get("metrics")
        routed_row["validator_metadata"] = {
            **dict(row.get("validator_metadata", {})),
            "learner_visible_labels": False,
            "trainer_side_boundary_positive": True,
        }
        routed.append(routed_row)

    for row in original:
        consider(row)

    rng = random.Random(config.seed + 4802)
    attempts = 0
    while len(accepted) < config.hard_decoy_count and attempts < config.max_generation_attempts:
        attempts += 1
        row = _generate_hard_decoy_candidate_row(rng, split="hard_decoy")
        if row is None or row["fen"] in used:
            continue
        lineage = row["lineage_key"]
        if lineage in used_lineage and used_lineage[lineage] != "hard_decoy":
            continue
        used.add(row["fen"])
        used_lineage[lineage] = "hard_decoy"
        consider(row)
    if len(accepted) < config.hard_decoy_count:
        raise RuntimeError(f"generated {len(accepted)}/{config.hard_decoy_count} validator-negative hard decoys")
    repaired["hard_decoy"] = accepted[:config.hard_decoy_count]
    repaired["boundary_positive"] = routed
    final_mislabels = [
        row
        for row in repaired["hard_decoy"]
        if _hard_decoy_gate(row, parent=parent, config=config)["classification"] != "accepted_hard_decoy"
    ]
    return repaired, {
        "schema_version": "tg48a_hard_decoy_gate.v0",
        "initial_hard_decoy_count": len(original),
        "accepted_hard_decoy_count": len(repaired["hard_decoy"]),
        "boundary_positive_routed_count": len(routed),
        "hard_decoy_candidate_routed_count": len(routed),
        "hard_decoy_generator_mislabel_count": len(final_mislabels),
        "true_hard_decoy_leak_count": 0,
        "routing_counts": dict(sorted(counts.items())),
        "generation_attempts": attempts,
        "learner_visible_labels": False,
    }


def _generate_hard_decoy_candidate_row(rng: random.Random, *, split: str) -> dict[str, Any] | None:
    """Generate trainer-side hard-negative candidates for the strict gate.

    The old hard-decoy shape mostly produced legitimate boundary positives or
    partial foundation hints. For strict negatives, start from broader edge
    decoy geometry, then let `_hard_decoy_gate` prove oracle-negativity.
    """

    for family in ("decoy_edge_killbox", "hard_decoy_edge_killbox"):
        row = _generate_family_row(rng, family=family, split=split)
        if row is None:
            continue
        if family == "hard_decoy_edge_killbox":
            return row
        rewritten = dict(row)
        rewritten["family"] = "hard_decoy_edge_killbox"
        rewritten["substage"] = "hard_decoy_edge_killbox"
        rewritten["lineage_key"] = _lineage_key(row["geometry_summary"], "hard_decoy_edge_killbox")
        rewritten["validator_metadata"] = {
            **dict(row.get("validator_metadata", {})),
            "trainer_side_negative_source_family": "decoy_edge_killbox",
            "learner_visible_labels": False,
        }
        return rewritten
    return None


def _hard_decoy_gate(
    row: Mapping[str, Any],
    *,
    parent: dict[str, TerminalAffordanceLearner],
    config: EdgeKillboxCurriculumConfig,
) -> dict[str, Any]:
    board = chess.Board(str(row["fen"]))
    if not edge_killbox_invariants(board, allow_rook_risk=True)["legal_krk"]:
        return {"classification": "invalid_generated", "reason": "invalid_krk_position"}
    partial_candidate: dict[str, Any] | None = None
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        metrics = _move_metrics(board, move, parent=parent, config=config)
        if metrics["validated_entry"] and not (
            metrics["illegal"]
            or metrics["rook_blunder"]
            or metrics["rook_missing"]
            or metrics["stalemate"]
            or metrics["confinement_regression"]
            or metrics["graph_positive_false_basin"]
        ):
            return {
                "classification": "legitimate_boundary_positive",
                "reason": "safe_legal_move_reaches_validated_all_reply_foundation_entry",
                "move": move.uci(),
                "metrics": metrics,
            }
        if metrics["partial_only_near_basin"] and partial_candidate is None:
            partial_candidate = {
                "classification": "partial_only_boundary",
                "reason": "partial_only_foundation_support_not_hard_negative",
                "move": move.uci(),
                "metrics": metrics,
            }
    if partial_candidate is not None:
        return partial_candidate
    return {
        "classification": "accepted_hard_decoy",
        "reason": "validator_negative_no_all_reply_or_partial_foundation_entry",
    }


def _generate_split(
    *,
    rng: random.Random,
    split: str,
    count: int,
    used: set[str],
    used_lineage: dict[str, str],
    max_attempts: int,
) -> list[dict[str, Any]]:
    families = (
        "edge_killbox_opposed_side",
        "edge_killbox_same_side_rook_danger",
        "edge_killbox_mixed",
    )
    out: list[dict[str, Any]] = []
    family_index = 0
    attempts = 0
    while len(out) < count and attempts < max_attempts:
        attempts += 1
        family = families[family_index % len(families)]
        family_index += 1
        row = _generate_family_row(rng, family=family, split=split)
        if row is None or row["fen"] in used:
            continue
        lineage = row["lineage_key"]
        if lineage in used_lineage and used_lineage[lineage] != split:
            continue
        used.add(row["fen"])
        used_lineage[lineage] = split
        out.append(row)
    if len(out) < count:
        raise RuntimeError(f"generated {len(out)}/{count} TG48a {split} positions")
    return out


def _generate_family_split(
    *,
    rng: random.Random,
    split: str,
    family: str,
    count: int,
    used: set[str],
    used_lineage: dict[str, str],
    max_attempts: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    attempts = 0
    while len(out) < count and attempts < max_attempts:
        attempts += 1
        row = _generate_family_row(rng, family=family, split=split)
        if row is None or row["fen"] in used:
            continue
        lineage = row["lineage_key"]
        if lineage in used_lineage and used_lineage[lineage] != split:
            continue
        used.add(row["fen"])
        used_lineage[lineage] = split
        out.append(row)
    if len(out) < count:
        raise RuntimeError(f"generated {len(out)}/{count} TG48a {split} {family} positions")
    return out


def _generate_family_row(rng: random.Random, *, family: str, split: str) -> dict[str, Any] | None:
    for _ in range(400):
        board = _construct_family_board(rng, family=family)
        if board is None:
            continue
        classification = classify_edge_killbox_family(board)
        if family == "edge_killbox_mixed":
            ok = classification in {"edge_killbox_opposed_side", "edge_killbox_same_side_rook_danger"}
            substage = classification
        else:
            ok = classification == family
            substage = family
        if not ok:
            continue
        summary = geometry_summary(board)
        lineage = _lineage_key(summary, family)
        return {
            "fen": board.fen(),
            "family": family,
            "substage": substage,
            "split": split,
            "lineage_key": lineage,
            "geometry_summary": summary,
            "validator_metadata": {
                "label_source": _label_source(),
                "mate_in_one_now": bool(_mate_moves(board)),
                "learner_visible_labels": False,
            },
        }
    for _ in range(400):
        board = _random_krk_board(rng)
        if not _valid_foundation_board(board):
            continue
        classification = classify_edge_killbox_family(board)
        if family == "edge_killbox_mixed":
            ok = classification in {"edge_killbox_opposed_side", "edge_killbox_same_side_rook_danger"}
            substage = classification
        else:
            ok = classification == family
            substage = family
        if not ok:
            continue
        summary = geometry_summary(board)
        lineage = _lineage_key(summary, family)
        return {
            "fen": board.fen(),
            "family": family,
            "substage": substage,
            "split": split,
            "lineage_key": lineage,
            "geometry_summary": summary,
            "validator_metadata": {
                "label_source": _label_source(),
                "mate_in_one_now": bool(_mate_moves(board)),
                "learner_visible_labels": False,
            },
        }
    return None


def _construct_family_board(rng: random.Random, *, family: str) -> chess.Board | None:
    target = family
    if family == "edge_killbox_mixed":
        target = rng.choice(("edge_killbox_opposed_side", "edge_killbox_same_side_rook_danger"))
    if target == "hard_decoy_edge_killbox":
        hard = _construct_hard_decoy_board(rng)
        if hard is not None:
            return hard
    for _ in range(160):
        bk = rng.choice(_edge_squares())
        axis = _primary_axis(bk)
        support_deltas = (
            [(3, 3), (-3, 3), (3, -3), (-3, -3), (4, 1), (-4, 1), (1, 4), (1, -4)]
            if target == "decoy_edge_killbox"
            else [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1), (2, 0), (-2, 0), (0, 2), (0, -2), (2, 2), (-2, 2), (2, -2), (-2, -2)]
        )
        rng.shuffle(support_deltas)
        for df, dr in support_deltas:
            wk_file = chess.square_file(bk) + df
            wk_rank = chess.square_rank(bk) + dr
            if not _inside(wk_file, wk_rank):
                continue
            wk = chess.square(wk_file, wk_rank)
            if chess.square_distance(wk, bk) <= 1:
                continue
            rook = _construct_rook_square(rng, bk=bk, wk=wk, axis=axis, target=target)
            if rook is None:
                continue
            board = _make_krk_board(wk=wk, wr=rook, bk=bk)
            if board is not None:
                return board
    return None


def _construct_hard_decoy_board(rng: random.Random) -> chess.Board | None:
    diagonal_offsets = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    support_deltas = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1), (2, 2), (-2, 2), (2, -2), (-2, -2)]
    for _ in range(200):
        bk = rng.choice(_edge_squares())
        rng.shuffle(diagonal_offsets)
        rng.shuffle(support_deltas)
        for rdf, rdr in diagonal_offsets:
            rook_file = chess.square_file(bk) + rdf
            rook_rank = chess.square_rank(bk) + rdr
            if not _inside(rook_file, rook_rank):
                continue
            rook = chess.square(rook_file, rook_rank)
            for kdf, kdr in support_deltas:
                wk_file = chess.square_file(bk) + kdf
                wk_rank = chess.square_rank(bk) + kdr
                if not _inside(wk_file, wk_rank):
                    continue
                wk = chess.square(wk_file, wk_rank)
                if wk in {bk, rook} or chess.square_distance(wk, bk) <= 1:
                    continue
                board = _make_krk_board(wk=wk, wr=rook, bk=bk)
                if board is not None:
                    return board
    return None


def _edge_squares() -> list[int]:
    return [
        chess.square(file_idx, rank_idx)
        for file_idx in range(8)
        for rank_idx in range(8)
        if file_idx in (0, 7) or rank_idx in (0, 7)
    ]


def _primary_axis(square: int) -> str:
    return "rank" if chess.square_rank(square) in (0, 7) else "file"


def _construct_rook_square(
    rng: random.Random,
    *,
    bk: int,
    wk: int,
    axis: str,
    target: str,
) -> int | None:
    wk_coord = chess.square_file(wk) if axis == "rank" else chess.square_rank(wk)
    bk_coord = chess.square_file(bk) if axis == "rank" else chess.square_rank(bk)
    bk_side = _sign(bk_coord - wk_coord)
    if bk_side == 0:
        bk_side = rng.choice((-1, 1))
    if target == "edge_killbox_opposed_side":
        rook_side = -bk_side
        adjacent_to_bk = False
    elif target == "edge_killbox_same_side_rook_danger":
        rook_side = bk_side
        adjacent_to_bk = False
    elif target == "hard_decoy_edge_killbox":
        rook_side = bk_side
        adjacent_to_bk = True
    else:
        rook_side = rng.choice((-1, 1))
        adjacent_to_bk = False
    offsets = [1, 2, 3, 4]
    rng.shuffle(offsets)
    for offset in offsets:
        coord = wk_coord + rook_side * offset
        if coord < 0 or coord > 7:
            continue
        cross_values = list(range(1, 7))
        rng.shuffle(cross_values)
        if adjacent_to_bk:
            cross_values = [chess.square_rank(bk) if axis == "rank" else chess.square_file(bk)] + cross_values
        for cross in cross_values:
            if axis == "rank":
                file_idx, rank_idx = coord, cross
            else:
                file_idx, rank_idx = cross, coord
            if not _inside(file_idx, rank_idx):
                continue
            rook = chess.square(file_idx, rank_idx)
            if rook in {wk, bk}:
                continue
            if target != "hard_decoy_edge_killbox" and chess.square_distance(rook, bk) <= 1:
                continue
            return rook
    return None


def _make_krk_board(*, wk: int, wr: int, bk: int) -> chess.Board | None:
    board = chess.Board(None)
    board.clear_board()
    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    board.turn = chess.WHITE
    board.castling_rights = 0
    board.ep_square = None
    board.halfmove_clock = 0
    board.fullmove_number = 1
    if not _valid_foundation_board(board):
        return None
    return board


def _inside(file_idx: int, rank_idx: int) -> bool:
    return 0 <= file_idx <= 7 and 0 <= rank_idx <= 7


def classify_edge_killbox_family(board: chess.Board) -> str | None:
    if not edge_killbox_invariants(board, allow_rook_risk=True)["legal_krk"]:
        return None
    f = extract_learner_features(board)
    if int(f["black_king_on_edge"]) != 1:
        return None
    support = _support_band(f)
    rook_safe = not _rook_capturable_by_reply(board) and bool(board.pieces(chess.ROOK, chess.WHITE))
    same_side = int(f["rook_black_king_same_side_of_white_king_on_primary_axis"]) == 1
    opposed = int(f["rook_black_king_opposite_sides_of_white_king_on_primary_axis"]) == 1
    if support and rook_safe and opposed:
        return "edge_killbox_opposed_side"
    if support and rook_safe and same_side and int(f["rook_lateral_escape_available"]) == 1:
        return "edge_killbox_same_side_rook_danger"
    if support and not rook_safe:
        return "hard_decoy_edge_killbox"
    if int(f["black_king_on_edge"]) == 1 and (not support or not rook_safe):
        return "decoy_edge_killbox"
    return None


def edge_killbox_invariants(board: chess.Board, *, allow_rook_risk: bool = False) -> dict[str, bool]:
    white_kings = len(board.pieces(chess.KING, chess.WHITE))
    black_kings = len(board.pieces(chess.KING, chess.BLACK))
    rooks = len(board.pieces(chess.ROOK, chess.WHITE))
    legal_krk = bool(
        board.turn == chess.WHITE
        and board.is_valid()
        and white_kings == 1
        and black_kings == 1
        and rooks == 1
        and len(board.piece_map()) == 3
        and not board.is_checkmate()
        and not board.is_stalemate()
    )
    f = extract_learner_features(board) if legal_krk else {}
    return {
        "legal_krk": legal_krk,
        "white_to_move": board.turn == chess.WHITE,
        "exactly_wk_wr_bk": white_kings == 1 and black_kings == 1 and rooks == 1 and len(board.piece_map()) == 3,
        "black_king_on_edge": bool(legal_krk and int(f["black_king_on_edge"]) == 1),
        "rook_present": rooks == 1,
        "rook_not_immediately_capturable": bool(legal_krk and (allow_rook_risk or not _rook_capturable_by_reply(board))),
        "not_checkmate": not board.is_checkmate(),
        "not_stalemate": not board.is_stalemate(),
        "support_band": bool(legal_krk and _support_band(f)),
    }


def geometry_summary(board: chess.Board) -> dict[str, Any]:
    f = extract_learner_features(board)
    summary = {
        "black_king_on_edge": int(f["black_king_on_edge"]),
        "black_king_corner_distance": int(f["black_king_corner_distance"]),
        "king_delta_file_abs": int(f["king_delta_file_abs"]),
        "king_delta_rank_abs": int(f["king_delta_rank_abs"]),
        "king_support_l_shape": int(f["king_support_l_shape"]),
        "king_support_chebyshev_distance": int(f["king_support_chebyshev_distance"]),
        "king_support_manhattan_distance": int(f["king_support_manhattan_distance"]),
        "same_side_rook_danger": int(f["rook_black_king_same_side_of_white_king_on_primary_axis"]),
        "opposed_side_basic": int(f["rook_black_king_opposite_sides_of_white_king_on_primary_axis"]),
        "rook_lateral_escape_available": int(f["rook_lateral_escape_available"]),
        "rook_distance_to_black_king_edge_line": int(f["rook_distance_to_black_king_edge_line"]),
        "rook_fence_depth_relative_to_black_king_edge": int(f["rook_fence_depth_relative_to_black_king_edge"]),
        "white_king_controls_escape_band": int(f["white_king_controls_escape_band"]),
        "rook_capturable_by_reply": int(_rook_capturable_by_reply(board)),
    }
    validate_learner_record(summary)
    return summary


def _support_band(features: Mapping[str, float]) -> bool:
    return bool(
        int(features["king_support_l_shape"]) == 1
        or (
            int(features["king_support_chebyshev_distance"]) <= 2
            and int(features["king_support_manhattan_distance"]) <= 3
        )
    )


def _lineage_key(summary: Mapping[str, Any], family: str) -> str:
    buckets = {
        "family": family,
        "corner": summary["black_king_corner_distance"],
        "kdf": summary["king_delta_file_abs"],
        "kdr": summary["king_delta_rank_abs"],
        "same": summary["same_side_rook_danger"],
        "opp": summary["opposed_side_basic"],
        "fdepth": min(4, int(summary["rook_fence_depth_relative_to_black_king_edge"])),
    }
    return "|".join(f"{key}={value}" for key, value in sorted(buckets.items()))


def _label_source() -> str:
    if os.environ.get("SYZYGY_PATH"):
        try:
            import chess.syzygy  # noqa: F401
            return "syzygy"
        except Exception:
            return "bounded_validator"
    if os.environ.get("STOCKFISH_EXECUTABLE"):
        return "stockfish"
    return "bounded_validator"


def _train_child(
    rows: list[dict[str, Any]],
    *,
    learner: TerminalAffordanceLearner,
    parent: dict[str, TerminalAffordanceLearner],
    label_source: str,
    config: EdgeKillboxCurriculumConfig,
) -> list[dict[str, Any]]:
    trace = []
    for index, row in enumerate(rows):
        board = chess.Board(row["fen"])
        rewards = {move.uci(): _reward(board, move, parent=parent, config=config) for move in board.legal_moves}
        is_decoy_training = row["family"] in {"decoy_edge_killbox", "hard_decoy_edge_killbox"}
        positive = [] if is_decoy_training else [
            move for move in sorted(board.legal_moves, key=lambda item: item.uci()) if rewards[move.uci()] >= 2.0
        ]
        catastrophic = [move for move in sorted(board.legal_moves, key=lambda item: item.uci()) if rewards[move.uci()] <= -5.0]
        if is_decoy_training:
            catastrophic = _decoy_debt_moves(board, parent=parent, config=config)
        if not positive and rewards and not is_decoy_training:
            best = max(rewards.values())
            positive = [move for move in sorted(board.legal_moves, key=lambda item: item.uci()) if rewards[move.uci()] == best and best > 0.0]
        weak = [
            move for move in sorted(board.legal_moves, key=lambda item: item.uci())
            if rewards[move.uci()] < 0.0 and move not in catastrophic
        ][:4]
        before = _choose_move(board, parent=parent, learner=learner)
        updates = {"positive": 0, "negative": 0, "neutral": 0}
        for move in positive:
            _update_move(learner, board, move, reward=max(1.0, rewards[move.uci()]))
            updates["positive"] += 1
        for move in catastrophic:
            _update_move(learner, board, move, reward=-8.0)
            updates["negative"] += 1
        for move in weak:
            _update_move(learner, board, move, reward=min(-1.0, rewards[move.uci()]))
            updates["negative"] += 1
        after = _choose_move(board, parent=parent, learner=learner)
        trace.append({
            "trace_type": "tg48a_train",
            "index": index,
            "fen": row["fen"],
            "family": row["family"],
            "substage": row["substage"],
            "split": row["split"],
            "label_source": label_source,
            "selected_before": None if before is None else before.uci(),
            "selected_after": None if after is None else after.uci(),
            "max_reward": max(rewards.values()) if rewards else 0.0,
            "positive_reward_count": sum(1 for value in rewards.values() if value > 0.0),
            "credited_move_count": len(positive),
            "catastrophic_debt_move_count": len(catastrophic),
            "weak_debt_move_count": len(weak),
            "decoy_debt_training": is_decoy_training,
            "updates": updates,
            "terminal_count_after": len(learner.terminals),
            "learner_visible_labels": False,
        })
    return trace


def _decoy_debt_moves(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    config: EdgeKillboxCurriculumConfig,
) -> list[chess.Move]:
    out = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        metrics = _move_metrics(board, move, parent=parent, config=config)
        if (
            metrics["rook_blunder"]
            or metrics["rook_missing"]
            or metrics["stalemate"]
            or metrics["illegal"]
            or metrics["confinement_regression"]
            or metrics["graph_positive_false_basin"]
            or metrics["partial_only_near_basin"]
            or metrics["validated_entry"]
        ):
            out.append(move)
    return out


def _reward(
    board: chess.Board,
    move: chess.Move,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    config: EdgeKillboxCurriculumConfig,
) -> float:
    _ = config
    after = board.copy(stack=False)
    after.push(move)
    if move not in board.legal_moves:
        return -8.0
    if after.is_stalemate() or not bool(after.pieces(chess.ROOK, chess.WHITE)) or _rook_capturable_by_reply(after):
        return -8.0
    before_f = extract_learner_features(board)
    after_f = extract_learner_features(after)
    response = _foundation_response(after, parent)
    if response["graph_positive_false_basin"]:
        return -4.0
    confinement_delta = _confinement_area(board) - _confinement_area(after)
    if confinement_delta < 0:
        return -3.0
    reward = -0.05
    reward += 10.0 if after.is_checkmate() else 0.0
    reward += 10.0 if response["validated_mate1_entry"] else 0.0
    reward += 8.0 if response["validated_mate2_entry"] else 0.0
    reward += 3.0 if _graded_positive_progress(board, after) else 0.0
    reward += 2.0 if after_f["rook_fence_depth_relative_to_black_king_edge"] <= before_f["rook_fence_depth_relative_to_black_king_edge"] else 0.0
    reward += 1.0 if confinement_delta > 0 else 0.0
    reward += 1.0 if after_f["black_reply_mobility"] < before_f["black_reply_mobility"] else 0.0
    reward += 1.0 if (
        after_f["king_support_manhattan_distance"] < before_f["king_support_manhattan_distance"]
        and not _rook_capturable_by_reply(after)
        and confinement_delta >= 0
    ) else 0.0
    if response["validated_partial_only"]:
        reward -= 1.5
    return max(-8.0, min(10.0, reward))


def _graded_positive_progress(before_board: chess.Board, after_board: chess.Board) -> bool:
    before_f = extract_learner_features(before_board)
    after_f = extract_learner_features(after_board)
    confinement_delta = _confinement_area(before_board) - _confinement_area(after_board)
    return bool(
        _preserves_or_establishes_killbox(after_f)
        and not _rook_capturable_by_reply(after_board)
        and not after_board.is_stalemate()
        and confinement_delta >= 0
        and (
            confinement_delta > 0
            or after_f["black_reply_mobility"] < before_f["black_reply_mobility"]
            or after_f["king_support_manhattan_distance"] < before_f["king_support_manhattan_distance"]
        )
    )


def _preserves_or_establishes_killbox(features: Mapping[str, float]) -> bool:
    return bool(
        int(features["black_king_on_edge"]) == 1
        and _support_band(features)
        and (
            int(features["rook_black_king_same_side_of_white_king_on_primary_axis"]) == 1
            or int(features["rook_black_king_opposite_sides_of_white_king_on_primary_axis"]) == 1
        )
    )


def _evaluate_rows(
    rows: list[dict[str, Any]],
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    learner: TerminalAffordanceLearner | None,
    trace_type: str,
    config: EdgeKillboxCurriculumConfig,
) -> dict[str, Any]:
    out = []
    for index, row in enumerate(rows):
        board = chess.Board(row["fen"])
        selected = _choose_move(board, parent=parent, learner=learner)
        metrics = _move_metrics(board, selected, parent=parent, config=config)
        success = _success(metrics)
        out.append({
            "trace_type": trace_type,
            "index": index,
            "fen": row["fen"],
            "family": row["family"],
            "substage": row.get("substage"),
            "split": row.get("split"),
            "lineage_key": row.get("lineage_key"),
            "selected": None if selected is None else selected.uci(),
            "success": success,
            "metrics": metrics,
            "failure_buckets": [] if success else _failure_buckets(metrics),
            "learner_visible_labels": False,
        })
    return _summarize_eval(out)


def _choose_move(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    learner: TerminalAffordanceLearner | None,
) -> chess.Move | None:
    options = [
        (_score_move(board, move, parent=parent, learner=learner), move.uci(), move)
        for move in sorted(board.legal_moves, key=lambda item: item.uci())
    ]
    options.sort(reverse=True)
    return options[0][-1] if options else None


def _score_move(
    board: chess.Board,
    move: chess.Move,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    learner: TerminalAffordanceLearner | None,
) -> float:
    parent_weight = 0.0 if parent is None else parent["mate2_first"].weight_for_move(board, move) * 0.20
    child_weight = 0.0 if learner is None else _weight_for_move(learner, board, move)
    return parent_weight + child_weight


def _update_move(learner: TerminalAffordanceLearner, board: chess.Board, move: chess.Move, *, reward: float) -> None:
    learner.cycle += 1
    for key, scale in _terminal_keys(board, move):
        terminal = learner.get_terminal(key)
        terminal.update(
            reward=reward,
            eta=learner.eta_m3,
            scale=scale,
            cycle=learner.cycle,
        )
        learner.m3_update_count += 1


def _weight_for_move(learner: TerminalAffordanceLearner, board: chess.Board, move: chess.Move) -> float:
    return sum(
        learner.terminals[key].local_weight * scale
        for key, scale in _terminal_keys(board, move)
        if key in learner.terminals
    )


def _terminal_keys(board: chess.Board, move: chess.Move) -> tuple[tuple[str, float], ...]:
    after = board.copy(stack=False)
    after.push(move)
    before = extract_learner_features(board)
    after_f = extract_learner_features(after)
    piece = board.piece_at(move.from_square)
    file_delta = chess.square_file(move.to_square) - chess.square_file(move.from_square)
    rank_delta = chess.square_rank(move.to_square) - chess.square_rank(move.from_square)
    keys = [
        (f"action_geometry:piece_type={0 if piece is None else int(piece.piece_type)}", 1.0),
        (f"action_geometry:file_delta_sign={_sign(file_delta)}", 1.0),
        (f"action_geometry:rank_delta_sign={_sign(rank_delta)}", 1.0),
        (f"action_geometry:file_delta_magnitude={min(3, abs(file_delta))}", 1.0),
        (f"action_geometry:rank_delta_magnitude={min(3, abs(rank_delta))}", 1.0),
        (f"before_geometry:black_king_on_edge={int(before['black_king_on_edge'])}", 0.5),
        (f"before_geometry:king_support_l_shape={int(before['king_support_l_shape'])}", 0.5),
        (f"before_geometry:king_support_chebyshev_distance={int(before['king_support_chebyshev_distance'])}", 0.5),
        (f"before_geometry:same_side_axis={int(before['rook_black_king_same_side_of_white_king_on_primary_axis'])}", 0.5),
        (f"before_geometry:opposite_side_axis={int(before['rook_black_king_opposite_sides_of_white_king_on_primary_axis'])}", 0.5),
        (f"before_geometry:rook_line_distance={min(4, int(before['rook_distance_to_black_king_edge_line']))}", 0.5),
        (f"after_geometry:black_king_on_edge={int(after_f['black_king_on_edge'])}", 0.5),
        (f"after_geometry:king_support_l_shape={int(after_f['king_support_l_shape'])}", 0.5),
        (f"after_geometry:same_side_axis={int(after_f['rook_black_king_same_side_of_white_king_on_primary_axis'])}", 0.5),
        (f"after_geometry:opposite_side_axis={int(after_f['rook_black_king_opposite_sides_of_white_king_on_primary_axis'])}", 0.5),
        (f"delta_geometry:confinement_area={_delta_bucket(_confinement_area(board) - _confinement_area(after))}", 1.0),
        (f"delta_geometry:black_mobility={_delta_bucket(before['black_reply_mobility'] - after_f['black_reply_mobility'])}", 1.0),
        (f"delta_geometry:king_support_manhattan={_delta_bucket(before['king_support_manhattan_distance'] - after_f['king_support_manhattan_distance'])}", 0.5),
        (f"safety_geometry:rook_capturable_after={int(_rook_capturable_by_reply(after))}", 1.0),
        (f"safety_geometry:stalemate_after={int(after.is_stalemate())}", 1.0),
    ]
    action_piece = 0 if piece is None else int(piece.piece_type)
    file_sign = _sign(file_delta)
    rank_sign = _sign(rank_delta)
    confinement_bucket = _delta_bucket(_confinement_area(board) - _confinement_area(after))
    mobility_bucket = _delta_bucket(before["black_reply_mobility"] - after_f["black_reply_mobility"])
    support_bucket = _delta_bucket(before["king_support_manhattan_distance"] - after_f["king_support_manhattan_distance"])
    keys.extend(
        [
            (
                "compound_geometry:"
                f"piece={action_piece}|fd={file_sign}|rd={rank_sign}|"
                f"b_same={int(before['rook_black_king_same_side_of_white_king_on_primary_axis'])}|"
                f"b_opp={int(before['rook_black_king_opposite_sides_of_white_king_on_primary_axis'])}|"
                f"a_same={int(after_f['rook_black_king_same_side_of_white_king_on_primary_axis'])}|"
                f"a_opp={int(after_f['rook_black_king_opposite_sides_of_white_king_on_primary_axis'])}|"
                f"conf={confinement_bucket}|mob={mobility_bucket}|support={support_bucket}",
                1.0,
            ),
            (
                "compound_support_action:"
                f"piece={action_piece}|fd_mag={min(3, abs(file_delta))}|rd_mag={min(3, abs(rank_delta))}|"
                f"b_support={int(_support_band(before))}|a_support={int(_support_band(after_f))}|"
                f"a_rook_safe={int(not _rook_capturable_by_reply(after))}|"
                f"conf={confinement_bucket}|mob={mobility_bucket}",
                1.0,
            ),
            (
                "compound_rook_edge_geometry:"
                f"piece={action_piece}|fd={file_sign}|rd={rank_sign}|"
                f"b_rook_line={min(4, int(before['rook_distance_to_black_king_edge_line']))}|"
                f"a_rook_line={min(4, int(after_f['rook_distance_to_black_king_edge_line']))}|"
                f"b_depth={min(4, int(before['rook_fence_depth_relative_to_black_king_edge']))}|"
                f"a_depth={min(4, int(after_f['rook_fence_depth_relative_to_black_king_edge']))}|"
                f"safe={int(not _rook_capturable_by_reply(after))}",
                1.0,
            ),
        ]
    )
    validate_learner_record([key for key, _scale in keys])
    return tuple(keys)


def _move_metrics(
    board: chess.Board,
    move: chess.Move | None,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    config: EdgeKillboxCurriculumConfig,
) -> dict[str, Any]:
    if move is None or move not in board.legal_moves:
        return {
            "illegal": True,
            "rook_blunder": False,
            "rook_missing": False,
            "stalemate": False,
            "confinement_regression": False,
            "fence_preserved": False,
            "validated_mate1_entry": False,
            "validated_mate2_entry": False,
            "validated_entry": False,
            "graph_positive_false_basin": False,
            "partial_only_near_basin": False,
            "mate_conversion_within_horizon": False,
            "dtm_improvement": None,
        }
    after = board.copy(stack=False)
    after.push(move)
    before_f = extract_learner_features(board)
    after_f = extract_learner_features(after)
    response = _foundation_response(after, parent)
    confinement_delta = _confinement_area(board) - _confinement_area(after)
    return {
        "illegal": False,
        "rook_blunder": _rook_capturable_by_reply(after),
        "rook_missing": not bool(after.pieces(chess.ROOK, chess.WHITE)),
        "stalemate": after.is_stalemate(),
        "confinement_regression": confinement_delta < 0,
        "confinement_improved": confinement_delta > 0,
        "fence_preserved": after_f["rook_fence_depth_relative_to_black_king_edge"] <= before_f["rook_fence_depth_relative_to_black_king_edge"],
        "black_mobility_reduced": after_f["black_reply_mobility"] < before_f["black_reply_mobility"],
        "support_geometry_improved": after_f["king_support_manhattan_distance"] < before_f["king_support_manhattan_distance"],
        "graded_positive_progress": _graded_positive_progress(board, after),
        "validated_mate1_entry": response["validated_mate1_entry"],
        "validated_mate2_entry": response["validated_mate2_entry"],
        "validated_entry": response["validated_all_reply_handoff"],
        "graph_positive_false_basin": response["graph_positive_false_basin"],
        "partial_only_near_basin": response["validated_partial_only"],
        "mate_conversion_within_horizon": _bounded_conversion(after, parent=parent, max_plies=config.max_horizon_plies),
        "immediate_checkmate": after.is_checkmate(),
        "dtm_improvement": None,
    }


def _foundation_response(after_white_move: chess.Board, parent: dict[str, TerminalAffordanceLearner] | None) -> dict[str, Any]:
    if parent is None:
        return {
            "validated_all_reply_handoff": False,
            "validated_mate1_entry": False,
            "validated_mate2_entry": False,
            "graph_positive_false_basin": False,
            "validated_partial_only": False,
        }
    response = _validated_foundation_response_details_fast(
        after_white_move,
        parent,
        response_cache=_FOUNDATION_RESPONSE_CACHE,
    )
    graph_type = response["graph_response_type"]
    return {
        "validated_all_reply_handoff": bool(response["validator_all_reply_foundation_response"]),
        "validated_mate1_entry": bool(response["validator_all_reply_foundation_response"] and "mate1" in graph_type),
        "validated_mate2_entry": bool(response["validator_all_reply_foundation_response"] and "mate2" in graph_type),
        "graph_positive_false_basin": bool(response["graph_positive_but_validator_failed_false_basin"]),
        "validated_partial_only": bool(
            response["validator_partial_reply_foundation_response"]
            and not response["validator_all_reply_foundation_response"]
        ),
    }


def _bounded_conversion(
    board: chess.Board,
    *,
    parent: dict[str, TerminalAffordanceLearner] | None,
    max_plies: int,
) -> bool:
    if board.is_checkmate():
        return True
    if parent is None or max_plies <= 0:
        return False
    response = _foundation_response(board, parent)
    return bool(response["validated_all_reply_handoff"])


def _success(metrics: Mapping[str, Any]) -> bool:
    return bool(
        not metrics["illegal"]
        and not metrics["rook_blunder"]
        and not metrics["rook_missing"]
        and not metrics["stalemate"]
        and not metrics["confinement_regression"]
        and not metrics["graph_positive_false_basin"]
        and not metrics["partial_only_near_basin"]
        and (
            metrics["immediate_checkmate"]
            or metrics["validated_entry"]
            or metrics["mate_conversion_within_horizon"]
        )
    )


def _summarize_eval(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_family.setdefault(row["family"], []).append(row)
    dtm_values = [
        row["metrics"]["dtm_improvement"]
        for row in rows
        if row["metrics"]["dtm_improvement"] is not None
    ]
    return {
        "position_count": total,
        "success_count": sum(int(row["success"]) for row in rows),
        "success_rate": _rate(sum(int(row["success"]) for row in rows), total),
        "validated_mate1_entry_count": sum(int(row["metrics"]["validated_mate1_entry"]) for row in rows),
        "validated_mate1_entry_rate": _rate(sum(int(row["metrics"]["validated_mate1_entry"]) for row in rows), total),
        "validated_mate2_entry_count": sum(int(row["metrics"]["validated_mate2_entry"]) for row in rows),
        "validated_mate2_entry_rate": _rate(sum(int(row["metrics"]["validated_mate2_entry"]) for row in rows), total),
        "validated_entry_count": sum(int(row["metrics"]["validated_entry"]) for row in rows),
        "validated_entry_rate": _rate(sum(int(row["metrics"]["validated_entry"]) for row in rows), total),
        "mate_conversion_within_horizon_count": sum(int(row["metrics"]["mate_conversion_within_horizon"]) for row in rows),
        "mate_conversion_rate_within_horizon": _rate(sum(int(row["metrics"]["mate_conversion_within_horizon"]) for row in rows), total),
        "fence_preserved_rate": _rate(sum(int(row["metrics"]["fence_preserved"]) for row in rows), total),
        "rook_blunder_count": sum(int(row["metrics"]["rook_blunder"]) for row in rows),
        "rook_missing_count": sum(int(row["metrics"]["rook_missing"]) for row in rows),
        "stalemate_count": sum(int(row["metrics"]["stalemate"]) for row in rows),
        "illegal_move_count": sum(int(row["metrics"]["illegal"]) for row in rows),
        "confinement_regression_count": sum(int(row["metrics"]["confinement_regression"]) for row in rows),
        "graph_positive_false_basin_count": sum(int(row["metrics"]["graph_positive_false_basin"]) for row in rows),
        "partial_only_near_basin_count": sum(int(row["metrics"]["partial_only_near_basin"]) for row in rows),
        "decoy_false_handoff_count": sum(
            int(row["family"] == "decoy_edge_killbox" and row["metrics"]["validated_entry"]) for row in rows
        ),
        "hard_decoy_false_handoff_count": sum(
            int(row["family"] == "hard_decoy_edge_killbox" and row["metrics"]["validated_entry"]) for row in rows
        ),
        "family_success_rates": {
            family: _rate(sum(int(row["success"]) for row in items), len(items))
            for family, items in sorted(by_family.items())
        },
        "average_dtm_improvement": None if not dtm_values else statistics.fmean(dtm_values),
        "median_dtm_improvement": None if not dtm_values else statistics.median(dtm_values),
        "rows": rows,
    }


def _terminal_activation_audit(
    learner: TerminalAffordanceLearner,
    rows: list[dict[str, Any]],
    *,
    parent: dict[str, TerminalAffordanceLearner],
    config: EdgeKillboxCurriculumConfig,
) -> dict[str, dict[str, Any]]:
    audit: dict[str, dict[str, Any]] = {}
    for row in rows:
        board = chess.Board(row["fen"])
        for move in board.legal_moves:
            metrics = _move_metrics(board, move, parent=parent, config=config)
            unsafe = bool(metrics["rook_blunder"] or metrics["rook_missing"] or metrics["stalemate"] or metrics["illegal"] or metrics["confinement_regression"])
            decoy_false = bool(row["family"] in {"decoy_edge_killbox", "hard_decoy_edge_killbox"} and metrics["validated_entry"])
            for key, _scale in _terminal_keys(board, move):
                if key not in learner.terminals:
                    continue
                item = audit.setdefault(
                    key,
                    {
                        "activation_count": 0,
                        "unsafe_activation_count": 0,
                        "decoy_false_handoff_activation_count": 0,
                        "positive_progress_activation_count": 0,
                        "validated_entry_activation_count": 0,
                        "positive_family_counts": {},
                    },
                )
                item["activation_count"] += 1
                item["unsafe_activation_count"] += int(unsafe)
                item["decoy_false_handoff_activation_count"] += int(decoy_false)
                positive_progress = bool(
                    not unsafe
                    and not metrics["graph_positive_false_basin"]
                    and not metrics["partial_only_near_basin"]
                    and (metrics["validated_entry"] or metrics["graded_positive_progress"])
                )
                item["positive_progress_activation_count"] += int(positive_progress)
                item["validated_entry_activation_count"] += int(metrics["validated_entry"])
                if positive_progress and row["family"] not in {"decoy_edge_killbox", "hard_decoy_edge_killbox"}:
                    family_counts = item["positive_family_counts"]
                    family_counts[row["family"]] = int(family_counts.get(row["family"], 0)) + 1
    return audit


def _promote_m4(
    learner: TerminalAffordanceLearner,
    *,
    terminal_audit: dict[str, dict[str, Any]],
    config: EdgeKillboxCurriculumConfig,
) -> tuple[TerminalAffordanceLearner, dict[str, Any]]:
    clone = TerminalAffordanceLearner.create(eta_m3=learner.eta_m3, rich_feature_credit_scale=learner.rich_feature_credit_scale)
    rows = []
    promoted = []
    veto_count = 0
    affordance_count = 0
    positive_affordance_candidate_count = 0
    positive_affordance_rejected_count = 0
    rejection_reason_counts: dict[str, int] = {}
    for key, terminal in learner.terminals.items():
        total = terminal.positive_credit + terminal.negative_credit
        precision = 0.0 if total == 0 else terminal.positive_credit / total
        negative_precision = 0.0 if total == 0 else terminal.negative_credit / total
        audit = terminal_audit.get(
            key,
            {
                "activation_count": 0,
                "unsafe_activation_count": 0,
                "decoy_false_handoff_activation_count": 0,
                "positive_progress_activation_count": 0,
                "validated_entry_activation_count": 0,
                "positive_family_counts": {},
            },
        )
        is_positive_candidate = terminal.local_weight > 0 and not _is_broad_key(key)
        positive_rejection_reasons = _positive_rejection_reasons(
            key=key,
            terminal=terminal,
            precision=precision,
            audit=audit,
            config=config,
        )
        positive_affordance_candidate_count += int(is_positive_candidate)
        promote_affordance = bool(
            is_positive_candidate
            and not positive_rejection_reasons
        )
        promote_veto = bool(
            terminal.local_weight < 0
            and terminal.negative_credit >= config.m4_min_negative_support
            and negative_precision >= config.m4_veto_precision_threshold
            and _is_veto_key(key)
        )
        promote = promote_affordance or promote_veto
        if promote:
            cloned_terminal = copy.deepcopy(terminal)
            cloned_terminal.cell.state = StemCellState.MATURE
            clone.terminals[key] = cloned_terminal
            promoted.append(key)
            affordance_count += int(promote_affordance)
            veto_count += int(promote_veto)
        elif is_positive_candidate:
            positive_affordance_rejected_count += 1
            for reason in positive_rejection_reasons:
                rejection_reason_counts[reason] = rejection_reason_counts.get(reason, 0) + 1
        rows.append({
            "terminal_key": key,
            "positive_intervention_count": terminal.positive_credit,
            "negative_intervention_count": terminal.negative_credit,
            "neutral_count": terminal.neutral_credit,
            "precision": round(precision, 6),
            "negative_precision": round(negative_precision, 6),
            "local_weight": round(terminal.local_weight, 6),
            "unsafe_activation_count": audit.get("unsafe_activation_count", 0),
            "decoy_false_handoff_activation_count": audit.get("decoy_false_handoff_activation_count", 0),
            "positive_progress_activation_count": audit.get("positive_progress_activation_count", 0),
            "validated_entry_activation_count": audit.get("validated_entry_activation_count", 0),
            "positive_family_counts": dict(sorted(audit.get("positive_family_counts", {}).items())),
            "positive_affordance_rejection_reasons": positive_rejection_reasons,
            "promoted_as": "affordance" if promote_affordance else "veto" if promote_veto else None,
            "promoted": promote,
        })
    return clone, {
        "M4_candidate_count": len(rows),
        "M4_promoted_terminal_count": len(promoted),
        "M4_promoted_veto_count": veto_count,
        "M4_promoted_affordance_count": affordance_count,
        "positive_affordance_candidate_count": positive_affordance_candidate_count,
        "positive_affordance_rejected_count": positive_affordance_rejected_count,
        "positive_affordance_rejection_reason_counts": dict(sorted(rejection_reason_counts.items())),
        "candidate_rows": rows,
    }


def _positive_rejection_reasons(
    *,
    key: str,
    terminal: Any,
    precision: float,
    audit: Mapping[str, Any],
    config: EdgeKillboxCurriculumConfig,
) -> list[str]:
    reasons = []
    if terminal.local_weight <= 0:
        reasons.append("non_positive_weight")
    if terminal.positive_credit < config.m4_min_positive_support:
        reasons.append("insufficient_positive_support")
    if precision < config.m4_affordance_precision_threshold:
        reasons.append("precision_below_affordance_threshold")
    if audit.get("unsafe_activation_count", 0) > config.m4_max_unsafe_activation:
        reasons.append("unsafe_activation")
    if audit.get("decoy_false_handoff_activation_count", 0) > config.m4_max_decoy_false_handoff_activation:
        reasons.append("decoy_false_handoff_activation")
    if audit.get("positive_progress_activation_count", 0) < config.m4_min_positive_support:
        reasons.append("insufficient_validated_or_graded_progress_activation")
    if _is_broad_key(key):
        reasons.append("broad_key")
    return reasons


def _combine_learners(
    *,
    m3: TerminalAffordanceLearner,
    m4: TerminalAffordanceLearner,
    trial_scale: float,
) -> TerminalAffordanceLearner:
    clone = TerminalAffordanceLearner.create(eta_m3=m3.eta_m3, rich_feature_credit_scale=m3.rich_feature_credit_scale)
    for key, value in m3.terminals.items():
        copied = copy.deepcopy(value)
        if key not in m4.terminals:
            copied.local_weight *= trial_scale
        clone.terminals[key] = copied
    clone.terminals.update({key: copy.deepcopy(value) for key, value in m4.terminals.items()})
    clone.m3_update_count = m3.m3_update_count
    return clone


def _graph_summary(
    *,
    learner: TerminalAffordanceLearner,
    m4_learner: TerminalAffordanceLearner,
    m4_audit: dict[str, Any],
) -> dict[str, Any]:
    top = sorted(learner.terminals.items(), key=lambda item: item[1].local_weight, reverse=True)[:20]
    bottom = sorted(learner.terminals.items(), key=lambda item: item[1].local_weight)[:20]
    payload = {
        "trial_terminal_count": len(learner.terminals),
        "mature_terminal_count": len(m4_learner.terminals),
        "m3_update_count": learner.m3_update_count,
        "m4": {key: value for key, value in m4_audit.items() if key != "candidate_rows"},
        "top_positive_terminal_keys": [key for key, _terminal in top],
        "top_negative_terminal_keys": [key for key, _terminal in bottom],
        "learner_visible_labels": False,
    }
    validate_learner_record({
        "top_positive_terminal_keys": payload["top_positive_terminal_keys"],
        "top_negative_terminal_keys": payload["top_negative_terminal_keys"],
    })
    return payload


def _same_side_oracle_summary(
    rows: list[dict[str, Any]],
    *,
    parent: dict[str, TerminalAffordanceLearner],
    config: EdgeKillboxCurriculumConfig,
) -> dict[str, Any]:
    """Trainer-side availability audit for same-side rows.

    This does not choose moves at runtime. It only records whether any legal
    action would satisfy the same validated entry criterion used for credit.
    """

    same_side = [row for row in rows if row["family"] == "edge_killbox_same_side_rook_danger"]
    successes = 0
    best_moves: list[dict[str, Any]] = []
    for row in same_side:
        board = chess.Board(row["fen"])
        valid_moves = []
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            metrics = _move_metrics(board, move, parent=parent, config=config)
            if _success(metrics):
                valid_moves.append(move.uci())
        successes += int(bool(valid_moves))
        best_moves.append({
            "fen": row["fen"],
            "valid_move_count": len(valid_moves),
            "valid_moves_sample": valid_moves[:8],
            "learner_visible_labels": False,
        })
    return {
        "same_side_position_count": len(same_side),
        "same_side_oracle_validated_success_count": successes,
        "same_side_oracle_validated_success_rate": None if not same_side else _rate(successes, len(same_side)),
        "sample_rows": best_moves[:12],
        "learner_visible_labels": False,
    }


def _decision(
    *,
    config: EdgeKillboxCurriculumConfig,
    parent_hash: str,
    parent_before: dict[str, Any],
    parent_after: dict[str, Any],
    parent_delta: int,
    datasets: dict[str, list[dict[str, Any]]],
    label_source: str,
    learner: TerminalAffordanceLearner,
    m4_audit: dict[str, Any],
    parent_only: dict[str, Any],
    m3_only: dict[str, Any],
    no_foundation: dict[str, Any],
    m4_only: dict[str, Any],
    m3_plus_m4: dict[str, Any],
    regression_m4: dict[str, Any],
    decoy_eval: dict[str, Any],
    ablation: dict[str, Any],
    hard_decoy_gate: dict[str, Any],
    same_side_oracle: dict[str, Any],
    total_seconds: float,
) -> dict[str, Any]:
    _ = regression_m4
    hard_decoy_generator_mislabels = int(hard_decoy_gate.get("hard_decoy_generator_mislabel_count", 0))
    true_hard_decoy_leaks = int(decoy_eval["hard_decoy_false_handoff_count"])
    hard_decoy_false_after_excluding_mislabels = true_hard_decoy_leaks
    safety_clean = bool(
        m4_only["rook_blunder_count"] == 0
        and m4_only["stalemate_count"] == 0
        and m4_only["illegal_move_count"] == 0
        and m4_only["confinement_regression_count"] == 0
    )
    decoy_clean = bool(decoy_eval["decoy_false_handoff_count"] == 0 and decoy_eval["hard_decoy_false_handoff_count"] == 0)
    a1_improved = _family_rate(m4_only, "edge_killbox_opposed_side") > _family_rate(parent_only, "edge_killbox_opposed_side")
    a2_improved = _family_rate(m4_only, "edge_killbox_same_side_rook_danger") > _family_rate(parent_only, "edge_killbox_same_side_rook_danger")
    m4_causal = bool(
        m4_audit["M4_promoted_affordance_count"] > 0
        and ablation["m4_causal_success_delta_vs_parent"] > 0
    )
    graph_false_basin_reduced = bool(
        m4_only["graph_positive_false_basin_count"] < parent_only["graph_positive_false_basin_count"]
    )
    m3_m4_not_large_regression = bool(
        m3_plus_m4["success_rate"] >= max(0.0, m4_only["success_rate"] - 0.15)
    )
    infrastructure_pass = bool(parent_delta == 0 and parent_before["pass"] and parent_after["pass"])
    behavioral_pass = bool(
        infrastructure_pass
        and safety_clean
        and decoy_clean
        and a1_improved
        and a2_improved
        and m4_causal
        and m4_only["validated_entry_rate"] > parent_only["validated_entry_rate"]
        and graph_false_basin_reduced
        and m3_m4_not_large_regression
    )
    if hard_decoy_generator_mislabels > 0:
        interpretation = "hard_decoy_generator_still_mislabels_boundary_positions"
        next_action = "repair_hard_decoy_generator_again"
    elif true_hard_decoy_leaks > 0:
        interpretation = "true_hard_decoy_leak_blocks_training"
        next_action = "tighten_false_basin_debt_and_decoy_vetoes"
    elif behavioral_pass:
        interpretation = "tg48a_behavioral_advancement"
        next_action = "scale_tg48a_or_start_tg48b_fence_establishment"
    elif (
        same_side_oracle.get("same_side_oracle_validated_success_rate") is not None
        and same_side_oracle.get("same_side_oracle_validated_success_rate", 0.0)
        > _family_rate(parent_only, "edge_killbox_same_side_rook_danger")
        and _family_rate(m4_only, "edge_killbox_same_side_rook_danger")
        <= _family_rate(parent_only, "edge_killbox_same_side_rook_danger")
    ):
        interpretation = "same_side_affordance_selection_blocker"
        next_action = "train_same_side_microstage_after_hard_decoy_gate_is_clean"
    elif infrastructure_pass:
        interpretation = "tg48a_infrastructure_pass_behavioral_not_advanced"
        next_action = "repair_tg48a_reward_or_generator_before_scaling"
    else:
        interpretation = "tg48a_infrastructure_failed"
        next_action = "repair_generator_or_parent_loading"
    summary = _dataset_geometry_rates(datasets)
    return {
        "checkpoint_pass": infrastructure_pass,
        "checkpoint_interpretation": interpretation,
        "selected_next_action": next_action,
        "behavioral_advancement": behavioral_pass,
        "run_scale_label": config.run_scale_label,
        "label_source": label_source,
        "parent_foundation_hash": parent_hash,
        "parent_foundation_frozen": True,
        "parent_foundation_m3_delta_during_stage": 0,
        "parent_foundation_m4_delta_during_stage": 0,
        "parent_foundation_weight_delta_during_stage": parent_delta,
        "edge_killbox_train_count": len(datasets["train"]),
        "edge_killbox_heldout_count": len(datasets["heldout"]),
        "edge_killbox_regression_count": len(datasets["regression"]),
        "decoy_count": len(datasets["decoy"]),
        "hard_decoy_count": len(datasets["hard_decoy"]),
        "boundary_positive_routed_count": len(datasets.get("boundary_positive", [])),
        "hard_decoy_generator_mislabel_count": hard_decoy_generator_mislabels,
        "true_hard_decoy_leak_count": true_hard_decoy_leaks,
        "hard_decoy_false_handoff_count_after_excluding_generator_mislabels": hard_decoy_false_after_excluding_mislabels,
        "hard_decoy_gate": hard_decoy_gate,
        "tg48a1_train_count": _count_family(datasets["train"], "edge_killbox_opposed_side"),
        "tg48a1_heldout_count": _count_family(datasets["heldout"], "edge_killbox_opposed_side"),
        "tg48a1_regression_count": _count_family(datasets["regression"], "edge_killbox_opposed_side"),
        "tg48a2_train_count": _count_family(datasets["train"], "edge_killbox_same_side_rook_danger"),
        "tg48a2_heldout_count": _count_family(datasets["heldout"], "edge_killbox_same_side_rook_danger"),
        "tg48a2_regression_count": _count_family(datasets["regression"], "edge_killbox_same_side_rook_danger"),
        "tg48a3_mixed_count": sum(_count_family(datasets[split], "edge_killbox_mixed") for split in ("train", "heldout", "regression")),
        **summary,
        "fence_preserved_rate": m4_only["fence_preserved_rate"],
        "rook_blunder_count": m4_only["rook_blunder_count"],
        "stalemate_count": m4_only["stalemate_count"],
        "illegal_move_count": m4_only["illegal_move_count"],
        "confinement_regression_count": m4_only["confinement_regression_count"],
        "validated_mate1_entry_rate": m4_only["validated_mate1_entry_rate"],
        "validated_mate2_entry_rate": m4_only["validated_mate2_entry_rate"],
        "mate_conversion_rate_within_horizon": m4_only["mate_conversion_rate_within_horizon"],
        "average_DTM_improvement": m4_only["average_dtm_improvement"],
        "median_DTM_improvement": m4_only["median_dtm_improvement"],
        "M3_update_count": learner.m3_update_count,
        "M4_promoted_terminal_count": m4_audit["M4_promoted_terminal_count"],
        "M4_promoted_veto_count": m4_audit["M4_promoted_veto_count"],
        "M4_promoted_affordance_count": m4_audit["M4_promoted_affordance_count"],
        "positive_affordance_candidate_count": m4_audit["positive_affordance_candidate_count"],
        "positive_affordance_rejected_count": m4_audit["positive_affordance_rejected_count"],
        "positive_affordance_rejection_reason_counts": m4_audit["positive_affordance_rejection_reason_counts"],
        "M4_positive_affordance_required_for_behavioral_advancement": True,
        "M3_plus_M4_not_large_regression": m3_m4_not_large_regression,
        "graph_positive_false_basin_reduced_vs_parent": graph_false_basin_reduced,
        "tg48a1_parent_success_rate": _family_rate(parent_only, "edge_killbox_opposed_side"),
        "tg48a1_M4_success_rate": _family_rate(m4_only, "edge_killbox_opposed_side"),
        "tg48a2_parent_success_rate": _family_rate(parent_only, "edge_killbox_same_side_rook_danger"),
        "tg48a2_M4_success_rate": _family_rate(m4_only, "edge_killbox_same_side_rook_danger"),
        "same_side_parent_success_rate": _family_rate(parent_only, "edge_killbox_same_side_rook_danger"),
        "same_side_M4_success_rate": _family_rate(m4_only, "edge_killbox_same_side_rook_danger"),
        "same_side_oracle_validated_success_rate": same_side_oracle.get("same_side_oracle_validated_success_rate"),
        "same_side_oracle_validated_success_count": same_side_oracle.get("same_side_oracle_validated_success_count"),
        "same_side_oracle_position_count": same_side_oracle.get("same_side_position_count"),
        "tg48a3_parent_success_rate": _family_rate(parent_only, "edge_killbox_mixed"),
        "tg48a3_M4_success_rate": _family_rate(m4_only, "edge_killbox_mixed"),
        "ablation_mask_M4_structures": ablation["mask_M4_structures"],
        "decoy_false_handoff_count": decoy_eval["decoy_false_handoff_count"],
        "hard_decoy_false_handoff_count": decoy_eval["hard_decoy_false_handoff_count"],
        "graph_positive_false_basin_count": m4_only["graph_positive_false_basin_count"],
        "partial_only_near_basin_count": m4_only["partial_only_near_basin_count"],
        "parent_only_success_rate": parent_only["success_rate"],
        "M3_trial_success_rate": m3_only["success_rate"],
        "M4_success_rate": m4_only["success_rate"],
        "true_M3_plus_M4_success_rate": m3_plus_m4["success_rate"],
        "no_foundation_success_rate": no_foundation["success_rate"],
        "runtime_tablebase_or_dtm_move_source": False,
        "stockfish_runtime_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "hardcoded_fen_or_move_repair": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "basin_labels_learner_visible": False,
        "tempo_opposition_labels_learner_visible": False,
        "quality_depth_reply_policy_labels_learner_visible": False,
        "total_seconds": total_seconds,
    }


def _dataset_geometry_rates(datasets: dict[str, list[dict[str, Any]]]) -> dict[str, float]:
    rows = datasets["train"] + datasets["heldout"] + datasets["regression"]
    total = len(rows)
    summaries = [row["geometry_summary"] for row in rows]
    return {
        "black_king_on_edge_rate": _rate(sum(int(item["black_king_on_edge"]) for item in summaries), total),
        "king_support_l_shape_rate": _rate(sum(int(item["king_support_l_shape"]) for item in summaries), total),
        "same_side_rook_danger_rate": _rate(sum(int(item["same_side_rook_danger"]) for item in summaries), total),
        "opposed_side_basic_rate": _rate(sum(int(item["opposed_side_basic"]) for item in summaries), total),
    }


def _dataset_summary(datasets: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {
        split: {
            "count": len(rows),
            "family_counts": {family: _count_family(rows, family) for family in sorted({row["family"] for row in rows})},
        }
        for split, rows in datasets.items()
    }


def _sample_rows(datasets: dict[str, list[dict[str, Any]]], *, limit: int) -> list[dict[str, Any]]:
    out = []
    counts: dict[str, int] = {}
    for rows in datasets.values():
        for row in rows:
            count = counts.get(row["family"], 0)
            if count >= limit:
                continue
            counts[row["family"]] = count + 1
            out.append(row)
    return out


def _count_family(rows: list[dict[str, Any]], family: str) -> int:
    return sum(int(row["family"] == family) for row in rows)


def _family_rate(metrics: dict[str, Any], family: str) -> float:
    return float(metrics.get("family_success_rates", {}).get(family, 0.0))


def _strip_rows(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if key != "rows"}


def _failure_buckets(metrics: Mapping[str, Any]) -> list[str]:
    buckets = []
    for key in (
        "illegal",
        "rook_blunder",
        "rook_missing",
        "stalemate",
        "confinement_regression",
        "graph_positive_false_basin",
        "partial_only_near_basin",
    ):
        if metrics.get(key):
            buckets.append(key)
    if not buckets and not metrics.get("validated_entry"):
        buckets.append("no_validated_foundation_entry")
    return buckets


def _is_veto_key(key: str) -> bool:
    return (
        "rook_capturable_after=1" in key
        or "stalemate_after=1" in key
        or "confinement_area=regressed" in key
        or "black_mobility=regressed" in key
        or key.startswith("compound_geometry:")
        or key.startswith("compound_support_action:")
        or key.startswith("compound_rook_edge_geometry:")
    )


def _is_broad_key(key: str) -> bool:
    return key.startswith("before_geometry:black_king_on_edge") or key.startswith("after_geometry:black_king_on_edge")


def _rook_capturable_by_reply(board: chess.Board) -> bool:
    rook_squares = set(board.pieces(chess.ROOK, chess.WHITE))
    if not rook_squares:
        return False
    reply_board = board.copy(stack=False)
    reply_board.turn = chess.BLACK
    return bool(any(reply.to_square in rook_squares for reply in reply_board.legal_moves))


def _confinement_area(board: chess.Board) -> int:
    rook = next(iter(board.pieces(chess.ROOK, chess.WHITE)), None)
    bk = board.king(chess.BLACK)
    if rook is None or bk is None:
        return 64
    rf, rr = chess.square_file(rook), chess.square_rank(rook)
    bf, br = chess.square_file(bk), chess.square_rank(bk)
    file_span = 8 if rf == bf else (7 - rf if rf < bf else rf)
    rank_span = 8 if rr == br else (7 - rr if rr < br else rr)
    return max(1, file_span) * max(1, rank_span)


def _sign(value: int) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def _delta_bucket(value: float | int) -> str:
    if value > 0:
        return "improved"
    if value < 0:
        return "regressed"
    return "same"


def _rate(count: int, total: int) -> float:
    return 0.0 if total == 0 else count / total


def _parent_snapshot(parent: dict[str, TerminalAffordanceLearner]) -> tuple[tuple[str, tuple[tuple[str, float, int, int, int, str], ...]], ...]:
    return tuple(
        sorted(
            (
                name,
                tuple(
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
                ),
            )
            for name, learner in parent.items()
        )
    )


def _purity_boundary() -> dict[str, bool]:
    return {
        "trainer_side_labels_allowed": True,
        "trainer_side_labels_used_as_runtime_provider": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stockfish_runtime_move_source": False,
        "action_ranker_used_for_runtime": False,
        "python_final_selector_used": False,
        "direct_provider_override": False,
        "hardcoded_fen_or_move_repair": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "basin_labels_learner_visible": False,
        "tempo_opposition_labels_learner_visible": False,
        "quality_depth_reply_policy_labels_learner_visible": False,
    }


def _write_board_samples(path: str | Path, eval_rows: list[dict[str, Any]], *, m4_audit: Mapping[str, Any]) -> None:
    categories = {
        "M3 failures": [
            row for row in eval_rows
            if row["trace_type"] == "TG48a_M3_trial_only" and not row["success"]
        ],
        "M4 failures": [
            row for row in eval_rows
            if row["trace_type"] == "TG48a_M4_consolidated_only" and not row["success"]
        ],
        "Hard-decoy false handoffs": [
            row for row in eval_rows
            if row["family"] == "hard_decoy_edge_killbox" and row["metrics"].get("validated_entry")
        ],
        "Graph-positive false basins": [
            row for row in eval_rows
            if row["metrics"].get("graph_positive_false_basin")
        ],
        "Parent succeeds but M3 worsens": _paired_regressions(
            eval_rows,
            better_trace="parent_TG46d_only",
            worse_trace="TG48a_M3_trial_only",
        ),
        "M4 succeeds with active veto terminal": _m4_veto_success_rows(eval_rows, m4_audit=m4_audit),
    }
    lines = [
        "# TG48a Repair Board Samples",
        "",
        "Human-readable samples from TG48a repair evaluation traces. Family/substage fields are trainer-side diagnostics only.",
        "",
    ]
    for title, rows in categories.items():
        lines.extend([f"## {title}", ""])
        if not rows:
            lines.extend(["No rows in this category.", ""])
            continue
        for row in rows[:20]:
            board = chess.Board(row["fen"])
            lines.extend(
                [
                    f"### {row['trace_type']} index {row['index']}",
                    "",
                    f"- FEN: `{row['fen']}`",
                    f"- Pieces: `{_piece_coordinates(board)}`",
                    f"- Family: `{row['family']}`",
                    f"- Selected move: `{row.get('selected')}`",
                    f"- Success: `{row['success']}`",
                    f"- Failure buckets: `{', '.join(row.get('failure_buckets') or []) or 'none'}`",
                    f"- Metrics: `{_compact_metrics(row['metrics'])}`",
                    "",
                    "```text",
                    str(board),
                    "```",
                    "",
                ]
            )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _paired_regressions(
    eval_rows: list[dict[str, Any]],
    *,
    better_trace: str,
    worse_trace: str,
) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    for row in eval_rows:
        by_key.setdefault((row["fen"], int(row["index"])), {})[row["trace_type"]] = row
    out = []
    for rows in by_key.values():
        better = rows.get(better_trace)
        worse = rows.get(worse_trace)
        if better and worse and better["success"] and not worse["success"]:
            out.append(worse)
    return out


def _m4_veto_success_rows(eval_rows: list[dict[str, Any]], *, m4_audit: Mapping[str, Any]) -> list[dict[str, Any]]:
    promoted_veto_keys = {
        row["terminal_key"]
        for row in m4_audit.get("candidate_rows", [])
        if row.get("promoted_as") == "veto"
    }
    out = []
    for row in eval_rows:
        if row["trace_type"] != "TG48a_M4_consolidated_only" or not row["success"] or not row.get("selected"):
            continue
        board = chess.Board(row["fen"])
        move = chess.Move.from_uci(row["selected"])
        active_keys = {key for key, _scale in _terminal_keys(board, move)}
        if active_keys & promoted_veto_keys:
            out.append(row)
    return out


def _piece_coordinates(board: chess.Board) -> str:
    pieces = []
    for square, piece in sorted(board.piece_map().items(), key=lambda item: item[0]):
        symbol = piece.symbol().upper() if piece.color == chess.WHITE else piece.symbol().lower()
        pieces.append(f"{symbol}{chess.square_name(square)}")
    return ", ".join(pieces)


def _compact_metrics(metrics: Mapping[str, Any]) -> str:
    keys = (
        "validated_entry",
        "validated_mate1_entry",
        "validated_mate2_entry",
        "mate_conversion_within_horizon",
        "graded_positive_progress",
        "graph_positive_false_basin",
        "partial_only_near_basin",
        "rook_blunder",
        "stalemate",
        "confinement_regression",
    )
    return ", ".join(f"{key}={metrics.get(key)}" for key in keys)


def _write_markdown(path: str | Path, result: EdgeKillboxCurriculumResult) -> None:
    d = result.decision
    lines = [
        f"# {result.config.checkpoint_name}",
        "",
        f"- Checkpoint pass: {d['checkpoint_pass']}",
        f"- Interpretation: {d['checkpoint_interpretation']}",
        f"- Selected next action: {d['selected_next_action']}",
        f"- Parent frozen deltas M3/M4/weight: {d['parent_foundation_m3_delta_during_stage']} / {d['parent_foundation_m4_delta_during_stage']} / {d['parent_foundation_weight_delta_during_stage']}",
        f"- Parent/M3/M4/M3+M4 success: {d['parent_only_success_rate']:.3f} / {d['M3_trial_success_rate']:.3f} / {d['M4_success_rate']:.3f} / {d['true_M3_plus_M4_success_rate']:.3f}",
        f"- Validated Mate-in-1 / Mate-in-2 entry: {d['validated_mate1_entry_rate']:.3f} / {d['validated_mate2_entry_rate']:.3f}",
        f"- Safety rook/stalemate/illegal/confinement: {d['rook_blunder_count']} / {d['stalemate_count']} / {d['illegal_move_count']} / {d['confinement_regression_count']}",
        f"- Decoy/hard-decoy false handoff: {d['decoy_false_handoff_count']} / {d['hard_decoy_false_handoff_count']}",
        f"- Hard-decoy generator mislabels / true leaks / routed boundary positives: {d.get('hard_decoy_generator_mislabel_count', 0)} / {d.get('true_hard_decoy_leak_count', 0)} / {d.get('boundary_positive_routed_count', 0)}",
        f"- Same-side parent/M4/oracle success: {d.get('same_side_parent_success_rate', 0.0):.3f} / {d.get('same_side_M4_success_rate', 0.0):.3f} / {0.0 if d.get('same_side_oracle_validated_success_rate') is None else d.get('same_side_oracle_validated_success_rate'):.3f}",
        f"- M3 updates: {d['M3_update_count']}",
        f"- M4 promoted terminals/veto/affordance: {d['M4_promoted_terminal_count']} / {d['M4_promoted_veto_count']} / {d['M4_promoted_affordance_count']}",
        f"- Label source: {d['label_source']}",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
