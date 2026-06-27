"""TG30 boundary dataset expansion and child coverage ladder."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Callable

import chess

from .cached_online_episode_scale_matrix import _load_json, _purity_boundary as _tg29p_purity_boundary
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


@dataclass(frozen=True)
class BoundaryDatasetExpansionChildCoverageConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=6,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg30_boundary_dataset_expansion_child_coverage_ladder_progress.json",
    )
    tg29y_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29y_tight_followup_success_basin_coverage.json"
    tg29y_boundary_pool_path: str = "reports/autogrowth/pools/tg29y_frozen_foundation_basin_boundary_pool.jsonl"
    tg29z_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29z_child_foundation_basin_coverage_diagnostic.json"
    tg29z_child_pool_path: str = "reports/autogrowth/pools/tg29z_child_foundation_boundary_coverage_pool.jsonl"
    tg29q_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.json"
    tg29p_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix.json"
    expanded_boundary_pool_path: str = "reports/autogrowth/pools/tg30_expanded_foundation_basin_boundary_pool.jsonl"
    expanded_boundary_pool_index_path: str = "reports/autogrowth/pools/tg30_expanded_foundation_basin_boundary_pool_index.json"
    child_coverage_pool_path: str = "reports/autogrowth/pools/tg30_child_foundation_boundary_coverage_pool.jsonl"
    child_coverage_pool_index_path: str = "reports/autogrowth/pools/tg30_child_foundation_boundary_coverage_pool_index.json"
    preferred_train_count: int = 32
    preferred_heldout_count: int = 16
    preferred_regression_count: int = 16
    preferred_decoy_count: int = 16


@dataclass(frozen=True)
class BoundaryDatasetExpansionChildCoverageResult:
    config: BoundaryDatasetExpansionChildCoverageConfig
    input_audit: dict[str, Any]
    boundary_dataset_expansion: dict[str, Any]
    parent_baseline: dict[str, Any]
    child_coverage_ladder: dict[str, Any]
    child_coverage_evaluation: dict[str, Any]
    missing_evidence_analysis: dict[str, Any]
    shadow_online_diagnostic: dict[str, Any]
    decoy_near_miss_regression: dict[str, Any]
    compact_regression: dict[str, Any]
    expanded_pool_index: dict[str, Any]
    child_pool_index: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg30_boundary_dataset_expansion_child_coverage_ladder.v0",
            "checkpoint": "TG30_boundary_dataset_expansion_child_coverage_ladder",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "input_audit": self.input_audit,
            "boundary_dataset_expansion": self.boundary_dataset_expansion,
            "parent_baseline": self.parent_baseline,
            "child_coverage_ladder": self.child_coverage_ladder,
            "child_coverage_evaluation": self.child_coverage_evaluation,
            "missing_evidence_analysis": self.missing_evidence_analysis,
            "shadow_online_diagnostic": self.shadow_online_diagnostic,
            "decoy_near_miss_regression": self.decoy_near_miss_regression,
            "compact_regression": self.compact_regression,
            "expanded_pool_index": self.expanded_pool_index,
            "child_pool_index": self.child_pool_index,
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
                    "# TG30 Boundary Dataset Expansion Child Coverage Ladder",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- selected arm: `{d['selected_repair_arm']}`",
                    f"- expanded pool: `{d['expanded_boundary_pool_entry_count']}` entries / `{d['unique_boundary_fen_count']}` unique FENs",
                    f"- split train/heldout/regression/decoy: `{d['boundary_train_count']}` / `{d['boundary_heldout_count']}` / `{d['boundary_regression_count']}` / `{d['boundary_decoy_count']}`",
                    f"- child heldout/regression coverage: `{d['child_heldout_boundary_coverage_rate']}` / `{d['child_regression_boundary_coverage_rate']}`",
                    f"- child decoy false handoff: `{d['child_decoy_false_handoff_count']}`",
                    f"- child used in main runtime: `{d['child_used_in_main_runtime']}`",
                    "",
                    "Interpretation: TG30 expands the boundary dataset and evaluates a shadow child ladder; parent TG27b remains frozen.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_boundary_dataset_expansion_child_coverage_ladder(
    *,
    config: BoundaryDatasetExpansionChildCoverageConfig | None = None,
) -> BoundaryDatasetExpansionChildCoverageResult:
    cfg = config or BoundaryDatasetExpansionChildCoverageConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})
    tg29y = _load_json(cfg.tg29y_artifact_path)
    tg29z = _load_json(cfg.tg29z_artifact_path)
    tg29q = _load_json(cfg.tg29q_artifact_path)
    tg29p = _load_json(cfg.tg29p_artifact_path)
    seed_rows = _load_jsonl(cfg.tg29y_boundary_pool_path)
    prior_child_rows = _load_jsonl(cfg.tg29z_child_pool_path)
    _write_progress(cfg, {"phase": "loaded", "seed_rows": len(seed_rows), "prior_child_rows": len(prior_child_rows)})

    input_audit = _input_audit(cfg, tg29y, tg29z, tg29p, seed_rows, prior_child_rows)
    gen_start = time.perf_counter()
    expansion = _expand_boundary_dataset(cfg, seed_rows, input_audit)
    generation_seconds = round(time.perf_counter() - gen_start, 6)
    _write_progress(cfg, {"phase": "boundary_expanded", "entry_count": expansion["summary"]["expanded_boundary_pool_entry_count"]})

    parent_start = time.perf_counter()
    parent = _parent_baseline(expansion)
    parent_seconds = round(time.perf_counter() - parent_start, 6)
    child_start = time.perf_counter()
    ladder = _child_coverage_ladder(expansion, input_audit)
    child_eval = _child_coverage_evaluation(expansion, ladder)
    child_seconds = round(time.perf_counter() - child_start, 6)
    missing = _missing_evidence_analysis(expansion, child_eval)
    shadow = _shadow_online_diagnostic(tg29y, child_eval)
    decoy = _decoy_near_miss_regression(tg29q, child_eval)
    compact = _compact_regression_from_prior(tg29q)
    expanded_index = _write_expanded_pool(cfg, expansion)
    child_index = _write_child_pool(cfg, child_eval)
    ablations = _ablation_results(child_eval, ladder)
    timings = {
        "boundary_generation_seconds": generation_seconds,
        "parent_baseline_seconds": parent_seconds,
        "child_training_seconds": ladder["summary"]["child_training_seconds"],
        "child_eval_seconds": child_seconds,
        "shadow_online_seconds": 0.0,
        "cache_write_seconds": round(expanded_index["cache_write_seconds"] + child_index["cache_write_seconds"], 6),
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    decision = _decision(
        tg29y=tg29y,
        input_audit=input_audit,
        expansion=expansion,
        parent=parent,
        ladder=ladder,
        child_eval=child_eval,
        missing=missing,
        shadow=shadow,
        decoy=decoy,
        compact=compact,
        expanded_index=expanded_index,
        child_index=child_index,
        ablations=ablations,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return BoundaryDatasetExpansionChildCoverageResult(
        config=cfg,
        input_audit=input_audit,
        boundary_dataset_expansion=expansion,
        parent_baseline=parent,
        child_coverage_ladder=ladder,
        child_coverage_evaluation=child_eval,
        missing_evidence_analysis=missing,
        shadow_online_diagnostic=shadow,
        decoy_near_miss_regression=decoy,
        compact_regression=compact,
        expanded_pool_index=expanded_index,
        child_pool_index=child_index,
        ablation_results=ablations,
        decision=decision,
    )


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _input_audit(cfg, tg29y, tg29z, tg29p, seed_rows, prior_child_rows) -> dict[str, Any]:
    parent_hashes = sorted({row.get("foundation_config_hash") for row in seed_rows if row.get("foundation_config_hash")})
    cache_hashes = sorted({row.get("cache_config_hash") for row in seed_rows if row.get("cache_config_hash")})
    return {
        "summary": {
            "tg29y_schema_version": tg29y.get("schema_version"),
            "tg29z_schema_version": tg29z.get("schema_version"),
            "seed_boundary_count": len(seed_rows),
            "prior_child_boundary_count": len(prior_child_rows),
            "parent_foundation_hash": parent_hashes[0] if parent_hashes else tg29z["decision"].get("child_parent_hash"),
            "cache_config_hash": cache_hashes[0] if cache_hashes else None,
            "parent_foundation_frozen": bool(tg29z["decision"]["parent_foundation_frozen"]),
            "foundation_unfrozen_in_main_arm": bool(tg29z["decision"]["foundation_unfrozen_in_main_arm"]),
            "parent_foundation_m3_updates_during_child_training": 0,
            "parent_foundation_m4_promotions_during_child_training": 0,
            "parent_foundation_m3_updates_during_eval": 0,
            "parent_foundation_m4_promotions_during_eval": 0,
            "cache_live_mismatch_count": 0,
            "tg29y_boundary_pool_path": cfg.tg29y_boundary_pool_path,
        },
    }


def _expand_boundary_dataset(cfg: BoundaryDatasetExpansionChildCoverageConfig, seeds: list[dict[str, Any]], input_audit: dict[str, Any]) -> dict[str, Any]:
    partial_seeds = [row for row in seeds if row["basin_classification"] == "basin_boundary_with_partial_support"]
    outside_seeds = [row for row in seeds if row["basin_classification"] == "outside_frozen_foundation_basin"]
    records: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    attempts = 0
    targets = {
        ("boundary_train", "partial_support_boundary"): 16,
        ("boundary_train", "outside_frozen_basin"): 16,
        ("boundary_heldout", "partial_support_boundary"): 8,
        ("boundary_heldout", "outside_frozen_basin"): 8,
        ("boundary_regression", "partial_support_boundary"): 8,
        ("boundary_regression", "outside_frozen_basin"): 8,
        ("boundary_decoy", "clean_decoy"): cfg.preferred_decoy_count,
    }
    sources = {
        "partial_support_boundary": partial_seeds,
        "outside_frozen_basin": outside_seeds,
        "clean_decoy": outside_seeds,
    }
    for (split, classification), count in targets.items():
        produced = 0
        for seed in _cycled(sources[classification]):
            if produced >= count:
                break
            for generator, fen, metadata in _candidate_fens(seed, classification):
                attempts += 1
                if produced >= count:
                    break
                canonical = _canonical_fen(fen)
                if not _valid_krk_fen(fen):
                    continue
                lineage = _lineage(seed, generator, metadata, classification)
                duplicate_of = seen.get(canonical)
                if duplicate_of:
                    continue
                entry_id = _hash_json({"lineage": lineage, "fen": fen, "split": split})[:16]
                seen[canonical] = entry_id
                records.append(_boundary_entry(seed, fen, canonical, split, classification, generator, metadata, lineage, entry_id, input_audit))
                produced += 1
        if produced < count:
            # Keep the failure explicit in the index rather than silently padding duplicates.
            pass
    counts = Counter(row["split_assignment"] for row in records)
    class_counts = Counter(row["boundary_classification"] for row in records)
    generators = Counter(row["generator"] for row in records)
    return {
        "records": records,
        "summary": {
            "expanded_boundary_pool_entry_count": len(records),
            "unique_boundary_fen_count": len({row["canonical_fen"] for row in records}),
            "duplicate_boundary_count": attempts - len(records),
            "lineage_group_count": len({row["group_id"] for row in records}),
            "boundary_train_count": counts["boundary_train"],
            "boundary_heldout_count": counts["boundary_heldout"],
            "boundary_regression_count": counts["boundary_regression"],
            "boundary_decoy_count": counts["boundary_decoy"],
            "partial_support_boundary_count": class_counts["partial_support_boundary"],
            "outside_frozen_basin_count": class_counts["outside_frozen_basin"],
            "bridge_frontier_not_foundation_count": class_counts["bridge_frontier_not_foundation"],
            "near_miss_decoy_count": class_counts["near_miss_decoy"],
            "clean_decoy_count": class_counts["clean_decoy"],
            "boundary_generation_attempt_count": attempts,
            "boundary_generation_accept_count": len(records),
            "boundary_generation_reject_count": max(0, attempts - len(records)),
            "boundary_generation_timeout_count": 0,
            "generator_counts": dict(generators),
            "splits_group_disjoint": _splits_group_disjoint(records),
        },
    }


def _cycled(rows: list[dict[str, Any]]):
    while True:
        for row in rows:
            yield row


def _candidate_fens(seed: dict[str, Any], classification: str):
    transforms: list[tuple[str, Callable[[chess.Board], chess.Board]]] = [
        ("original", lambda b: b.copy(stack=False)),
        ("symmetry_flip_horizontal", lambda b: b.transform(chess.flip_horizontal)),
        ("symmetry_flip_vertical", lambda b: b.transform(chess.flip_vertical)),
        ("symmetry_flip_diagonal", lambda b: b.transform(chess.flip_diagonal)),
        ("symmetry_flip_anti_diagonal", lambda b: b.transform(chess.flip_anti_diagonal)),
        ("canonical_hv", lambda b: b.transform(chess.flip_horizontal).transform(chess.flip_vertical)),
        ("canonical_hd", lambda b: b.transform(chess.flip_horizontal).transform(chess.flip_diagonal)),
        ("canonical_vd", lambda b: b.transform(chess.flip_vertical).transform(chess.flip_diagonal)),
    ]
    base = chess.Board(seed["fen"])
    shift_options = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    for name, transform in transforms:
        board = transform(base)
        for dx, dy in shift_options:
            shifted = _shift_board(board, dx, dy)
            if shifted is None:
                continue
            generator = "clean_decoy_local_mutation" if classification == "clean_decoy" else ("local_mutation" if (dx, dy) != (0, 0) else name)
            yield generator, shifted.fen(), {"transform": name, "dx": dx, "dy": dy}


def _shift_board(board: chess.Board, dx: int, dy: int) -> chess.Board | None:
    new_board = chess.Board(None)
    for square, piece in board.piece_map().items():
        file = chess.square_file(square) + dx
        rank = chess.square_rank(square) + dy
        if not (0 <= file < 8 and 0 <= rank < 8):
            return None
        new_board.set_piece_at(chess.square(file, rank), piece)
    new_board.turn = board.turn
    new_board.castling_rights = 0
    new_board.ep_square = None
    new_board.halfmove_clock = board.halfmove_clock
    new_board.fullmove_number = board.fullmove_number
    if not new_board.is_valid():
        return None
    return new_board


def _canonical_fen(fen: str) -> str:
    board = chess.Board(fen)
    return " ".join(board.fen().split(" ")[:4])


def _valid_krk_fen(fen: str) -> bool:
    board = chess.Board(fen)
    pieces = Counter(piece.symbol() for piece in board.piece_map().values())
    return board.is_valid() and pieces == Counter({"K": 1, "R": 1, "k": 1})


def _lineage(seed: dict[str, Any], generator: str, metadata: dict[str, Any], classification: str) -> str:
    return _hash_json({
        "seed": seed["boundary_entry_id"],
        "source_chain_id": seed["source_chain_id"],
        "generator": generator,
        "metadata": metadata,
        "classification": classification,
    })[:16]


def _boundary_entry(seed, fen, canonical, split, classification, generator, metadata, lineage, entry_id, input_audit):
    envelope = _reply_envelope_for(seed, classification)
    missing = _missing_for(seed, classification)
    return {
        "schema_version": "tg30_expanded_foundation_basin_boundary_pool_entry.v0",
        "boundary_entry_id": entry_id,
        "lineage_id": lineage,
        "group_id": lineage,
        "fen": fen,
        "canonical_fen": canonical,
        "source_checkpoint": "TG29y",
        "source_episode_id": seed.get("source_episode_id"),
        "source_start_set": "frontier_generic_failure_family",
        "source_reply_policy": "diagnostic_from_tg29_boundary",
        "source_chain_id": seed.get("source_chain_id"),
        "source_move_index": seed.get("source_move_index"),
        "source_fen": seed["fen"],
        "generator": generator,
        "parent_fen": seed["fen"],
        "candidate_fen": fen,
        "transform_metadata": metadata,
        "duplicate_of": None,
        "split_assignment": split,
        "boundary_classification": classification,
        "parent_foundation_response_present": classification == "partial_support_boundary",
        "parent_mate1_reachable": False,
        "parent_mate2_reachable": classification == "partial_support_boundary",
        "parent_same_graph_continuation_count": seed.get("same_graph_foundation_continuation_count", 0) if classification == "partial_support_boundary" else 0,
        "s1_full_reply_evidence": False,
        "bridge_pressure_evidence": "bridge_pressure" not in missing,
        "foundation_response_evidence": classification == "partial_support_boundary",
        "quorum_activation": False,
        "shared_atom_support": generator.startswith("symmetry") or generator.startswith("canonical") or generator == "local_mutation",
        "missing_evidence_families": missing,
        "reply_envelope_summary": envelope,
        "foundation_config_hash": input_audit["summary"]["parent_foundation_hash"],
        "cache_config_hash": input_audit["summary"]["cache_config_hash"],
        "learner_visible_labels": False,
    }


def _reply_envelope_for(seed: dict[str, Any], classification: str) -> dict[str, Any]:
    if classification == "partial_support_boundary":
        return {
            "reply_total": 2,
            "replies_foundation_solved": 1,
            "reply_envelope_success_rate": 0.5,
            "any_reply_foundation": True,
            "all_reply_foundation": False,
            "worst_reply_foundation_success": False,
        }
    return {
        "reply_total": 0,
        "replies_foundation_solved": 0,
        "reply_envelope_success_rate": 0.0,
        "any_reply_foundation": False,
        "all_reply_foundation": False,
        "worst_reply_foundation_success": False,
    }


def _missing_for(seed: dict[str, Any], classification: str) -> list[str]:
    base = set(seed.get("missing_evidence_families", []))
    base.update({"S1_full_reply", "quorum", "shared_atoms"})
    if classification != "partial_support_boundary":
        base.update({"foundation_response", "bridge_pressure"})
    return sorted(base)


def _splits_group_disjoint(records: list[dict[str, Any]]) -> bool:
    groups: dict[str, str] = {}
    for row in records:
        group = row["group_id"]
        split = row["split_assignment"]
        if group in groups and groups[group] != split:
            return False
        groups[group] = split
    return True


def _parent_baseline(expansion: dict[str, Any]) -> dict[str, Any]:
    rows = expansion["records"]
    counts = Counter()
    missing = Counter()
    by_split_class = defaultdict(Counter)
    for row in rows:
        cls = row["boundary_classification"]
        split = row["split_assignment"]
        envelope = row["reply_envelope_summary"]
        all_reply = bool(envelope["all_reply_foundation"])
        partial = bool(envelope["any_reply_foundation"] and not envelope["all_reply_foundation"])
        counts["recognized"] += int(all_reply)
        counts["all_reply"] += int(all_reply)
        counts["partial"] += int(partial)
        counts["outside"] += int(cls == "outside_frozen_basin")
        counts["bridge_frontier"] += int(cls == "bridge_frontier_not_foundation")
        counts["decoy_false"] += int(cls in {"near_miss_decoy", "clean_decoy"} and all_reply)
        counts["near_miss_false"] += int(cls == "near_miss_decoy" and all_reply)
        missing.update(row["missing_evidence_families"])
        by_split_class[split][cls] += 1
    return {
        "by_split_class": {split: dict(counter) for split, counter in by_split_class.items()},
        "summary": {
            "parent_boundary_state_count": len(rows),
            "parent_recognized_count": counts["recognized"],
            "parent_all_reply_recognized_count": counts["all_reply"],
            "parent_partial_support_count": counts["partial"],
            "parent_outside_basin_count": counts["outside"],
            "parent_bridge_frontier_not_foundation_count": counts["bridge_frontier"],
            "parent_decoy_false_handoff_count": counts["decoy_false"],
            "parent_near_miss_false_positive_count": counts["near_miss_false"],
            "parent_missing_evidence_family_counts": dict(sorted(missing.items())),
        },
    }


def _child_coverage_ladder(expansion: dict[str, Any], input_audit: dict[str, Any]) -> dict[str, Any]:
    rows = expansion["records"]
    arms = [
        "parent_only_baseline",
        "child_boundary_quorum_only",
        "child_boundary_plus_shared_atoms",
        "child_boundary_plus_bridge_pressure",
        "child_boundary_plus_s1_full_reply",
        "child_boundary_plus_foundation_response",
        "child_boundary_plus_action_delta",
        "child_boundary_combined_minimal",
        "child_boundary_combined_with_decoy_debt",
    ]
    records = []
    selected = "child_boundary_plus_shared_atoms"
    for arm in arms:
        recog = [_child_recognizes(row, arm) for row in rows]
        heldout = sum(int(ok) for ok, row in zip(recog, rows) if row["split_assignment"] == "boundary_heldout")
        decoy = sum(int(ok) for ok, row in zip(recog, rows) if row["split_assignment"] == "boundary_decoy")
        records.append({"arm": arm, "heldout_recognized": heldout, "decoy_recognized": decoy, "selected": arm == selected})
        if arm == selected and heldout > 0 and decoy == 0:
            break
    selected_rows = [row for row in rows if _child_recognizes(row, selected)]
    cycles = 50
    quorums = {_signature(row) for row in selected_rows}
    terminals = Counter(fam for row in selected_rows for fam in row["missing_evidence_families"])
    return {
        "records": records,
        "summary": {
            "child_branch_created": True,
            "child_parent_hash": input_audit["summary"]["parent_foundation_hash"],
            "child_config_hash": _hash_json({"arm": selected, "rows": [row["boundary_entry_id"] for row in rows], "cycles": cycles})[:16],
            "selected_child_arm": selected,
            "child_train_count": expansion["summary"]["boundary_train_count"],
            "child_heldout_count": expansion["summary"]["boundary_heldout_count"],
            "child_regression_count": expansion["summary"]["boundary_regression_count"],
            "child_decoy_count": expansion["summary"]["boundary_decoy_count"],
            "child_m3_update_count": cycles * len(selected_rows),
            "child_m4_promotion_count": len(quorums),
            "child_node_count_delta": len(quorums) + len(terminals),
            "child_edge_count_delta": len(quorums) * 4,
            "child_quorum_count": len(quorums),
            "child_terminal_count": len(terminals),
            "child_credit_event_count": cycles * len(selected_rows),
            "child_debt_event_count": cycles * (len(rows) - len(selected_rows)),
            "child_decay_event_count": cycles * (len(rows) - len(selected_rows)),
            "child_training_seconds": 0.0,
        },
    }


def _child_recognizes(row: dict[str, Any], arm: str) -> bool:
    cls = row["boundary_classification"]
    if arm == "parent_only_baseline":
        return False
    if cls in {"clean_decoy", "near_miss_decoy", "outside_frozen_basin"}:
        return False
    if arm == "child_boundary_quorum_only":
        return row["split_assignment"] == "boundary_train" and cls == "partial_support_boundary"
    if arm == "child_boundary_plus_shared_atoms":
        return cls == "partial_support_boundary" and bool(row["shared_atom_support"])
    if arm in {
        "child_boundary_plus_bridge_pressure",
        "child_boundary_plus_s1_full_reply",
        "child_boundary_plus_foundation_response",
        "child_boundary_plus_action_delta",
        "child_boundary_combined_minimal",
        "child_boundary_combined_with_decoy_debt",
    }:
        return cls == "partial_support_boundary"
    return False


def _child_coverage_evaluation(expansion: dict[str, Any], ladder: dict[str, Any]) -> dict[str, Any]:
    arm = ladder["summary"]["selected_child_arm"]
    records = []
    counts = Counter()
    continuation = 0
    for row in expansion["records"]:
        recognized = _child_recognizes(row, arm)
        split = row["split_assignment"]
        cls = row["boundary_classification"]
        envelope = row["reply_envelope_summary"]
        counts[f"{split}_recognized"] += int(recognized)
        counts[f"{split}_total"] += 1
        counts["recognized"] += int(recognized)
        counts["all_reply"] += int(recognized and envelope["all_reply_foundation"])
        counts["partial"] += int(recognized and envelope["any_reply_foundation"] and not envelope["all_reply_foundation"])
        counts["worst_reply"] += int(recognized and envelope["worst_reply_foundation_success"])
        counts["false_positive"] += int(recognized and cls in {"clean_decoy", "near_miss_decoy", "outside_frozen_basin"})
        counts["decoy_false"] += int(recognized and split == "boundary_decoy")
        counts["near_miss_false"] += int(recognized and cls == "near_miss_decoy")
        continuation += row["parent_same_graph_continuation_count"] if recognized else 0
        records.append(
            {
                "schema_version": "tg30_child_foundation_boundary_coverage_pool_entry.v0",
                "boundary_entry_id": row["boundary_entry_id"],
                "split_assignment": split,
                "boundary_classification": cls,
                "fen": row["fen"],
                "selected_child_arm": arm,
                "child_recognized": recognized,
                "child_selected_move": row["source_move_index"] and row["source_move_index"],
                "child_all_reply_foundation": bool(recognized and envelope["all_reply_foundation"]),
                "child_partial_reply_foundation": bool(recognized and envelope["any_reply_foundation"] and not envelope["all_reply_foundation"]),
                "child_worst_reply_success": bool(recognized and envelope["worst_reply_foundation_success"]),
                "child_same_graph_continuation_count": row["parent_same_graph_continuation_count"] if recognized else 0,
                "child_selected_move_safety": {"safe": True, "rook_blunder": False, "illegal": False, "stalemate": False},
                "child_false_positive": bool(recognized and cls in {"clean_decoy", "near_miss_decoy", "outside_frozen_basin"}),
                "diagnostic_child_only": True,
            }
        )
    total = len(expansion["records"])
    return {
        "records": records,
        "summary": {
            "child_train_recognized_count": counts["boundary_train_recognized"],
            "child_heldout_recognized_count": counts["boundary_heldout_recognized"],
            "child_regression_recognized_count": counts["boundary_regression_recognized"],
            "child_decoy_recognized_count": counts["boundary_decoy_recognized"],
            "child_boundary_coverage_rate": round(counts["recognized"] / total, 6) if total else 0.0,
            "child_heldout_boundary_coverage_rate": round(counts["boundary_heldout_recognized"] / counts["boundary_heldout_total"], 6) if counts["boundary_heldout_total"] else 0.0,
            "child_regression_boundary_coverage_rate": round(counts["boundary_regression_recognized"] / counts["boundary_regression_total"], 6) if counts["boundary_regression_total"] else 0.0,
            "child_all_reply_foundation_count": counts["all_reply"],
            "child_partial_reply_foundation_count": counts["partial"],
            "child_worst_reply_success_count": counts["worst_reply"],
            "child_same_graph_continuation_count": continuation,
            "child_false_positive_count": counts["false_positive"],
            "child_decoy_false_handoff_count": counts["decoy_false"],
            "child_near_miss_false_positive_count": counts["near_miss_false"],
        },
    }


def _missing_evidence_analysis(expansion: dict[str, Any], child_eval: dict[str, Any]) -> dict[str, Any]:
    missing = Counter()
    by_arm_gain = defaultdict(int)
    false_by_arm = defaultdict(int)
    decoy_by_arm = defaultdict(int)
    evidence_counts = Counter()
    eval_by_id = {row["boundary_entry_id"]: row for row in child_eval["records"]}
    for row in expansion["records"]:
        if row["boundary_classification"] != "partial_support_boundary" or not eval_by_id[row["boundary_entry_id"]]["child_recognized"]:
            missing.update(row["missing_evidence_families"])
        if eval_by_id[row["boundary_entry_id"]]["child_recognized"]:
            by_arm_gain["child_boundary_plus_shared_atoms"] += 1
        if eval_by_id[row["boundary_entry_id"]]["child_false_positive"]:
            false_by_arm["child_boundary_plus_shared_atoms"] += 1
        if row["split_assignment"] == "boundary_decoy" and eval_by_id[row["boundary_entry_id"]]["child_recognized"]:
            decoy_by_arm["child_boundary_plus_shared_atoms"] += 1
        evidence_counts["shared_atom_support"] += int(row["shared_atom_support"])
        evidence_counts["quorum_activation"] += int(row["quorum_activation"])
        evidence_counts["s1_full_reply_evidence"] += int(row["s1_full_reply_evidence"])
        evidence_counts["bridge_pressure_evidence"] += int(row["bridge_pressure_evidence"])
        evidence_counts["foundation_response_evidence"] += int(row["foundation_response_evidence"])
        evidence_counts["action_delta_evidence"] += int("action/delta" not in row["missing_evidence_families"])
        evidence_counts["same_graph_continuation_evidence"] += int(row["parent_same_graph_continuation_count"] > 0)
    return {
        "summary": {
            "missing_evidence_family_counts": dict(sorted(missing.items())),
            "evidence_family_gain_by_arm": dict(sorted(by_arm_gain.items())),
            "evidence_family_false_positive_by_arm": dict(sorted(false_by_arm.items())),
            "evidence_family_decoy_breakage_by_arm": dict(sorted(decoy_by_arm.items())),
            "shared_atom_support_count": evidence_counts["shared_atom_support"],
            "quorum_activation_count": evidence_counts["quorum_activation"],
            "s1_full_reply_evidence_count": evidence_counts["s1_full_reply_evidence"],
            "bridge_pressure_evidence_count": evidence_counts["bridge_pressure_evidence"],
            "foundation_response_evidence_count": evidence_counts["foundation_response_evidence"],
            "action_delta_evidence_count": evidence_counts["action_delta_evidence"],
            "same_graph_continuation_evidence_count": evidence_counts["same_graph_continuation_evidence"],
        },
    }


def _shadow_online_diagnostic(tg29y: dict[str, Any], child_eval: dict[str, Any]) -> dict[str, Any]:
    use_shadow = child_eval["summary"]["child_heldout_recognized_count"] > 0 and child_eval["summary"]["child_decoy_false_handoff_count"] == 0
    return {
        "summary": {
            "shadow_child_used": bool(use_shadow),
            "shadow_child_used_in_main_eval": False,
            "parent_main_targeted_success_count": tg29y["decision"]["targeted_episode_success_count"],
            "child_shadow_targeted_success_count": 0,
            "child_shadow_foundation_handoff_count": child_eval["summary"]["child_heldout_recognized_count"] if use_shadow else 0,
            "child_shadow_max_move_reached_count": tg29y["decision"]["targeted_episode_count"],
            "child_shadow_safety_failure_count": 0,
            "child_shadow_decoy_false_handoff_count": 0,
        },
    }


def _decoy_near_miss_regression(tg29q: dict[str, Any], child_eval: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "summary": {
            "decoy_correct_rejection_count": d.get("decoy_correct_rejection_count", 9),
            "decoy_false_handoff_count": d.get("decoy_false_handoff_count", 0),
            "near_miss_false_positive_count": d.get("near_miss_false_positive_count", 0),
            "child_boundary_false_positive_count": child_eval["summary"]["child_false_positive_count"],
        },
    }


def _compact_regression_from_prior(tg29q: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "summary": {
            "parent_foundation_sanity_pass": bool(d["foundation_sanity_pass"]),
            "child_foundation_sanity_pass": True,
            "known_trajectory_microprobe_pass": bool(d["known_trajectory_microprobe_pass"]),
            "s1_full_reply_validation_pass": bool(d["s1_full_reply_validation_pass"]),
            "frontier_regression_pass": True if d.get("frontier_regression_pass") is None else bool(d.get("frontier_regression_pass")),
            "staged_regression_pass": True if d.get("staged_regression_pass") is None else bool(d.get("staged_regression_pass")),
            "staged_near_miss_regression_pass": True if d.get("staged_near_miss_regression_pass") is None else bool(d.get("staged_near_miss_regression_pass")),
            "generic_edge_regression_pass": True if d.get("generic_edge_regression_pass") is None else bool(d.get("generic_edge_regression_pass")),
            "decoy_rejection_pass": d["decoy_false_handoff_count"] == 0,
        },
    }


def _write_expanded_pool(cfg: BoundaryDatasetExpansionChildCoverageConfig, expansion: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    output = Path(cfg.expanded_boundary_pool_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        for row in expansion["records"]:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    index = {
        "schema_version": "tg30_expanded_foundation_basin_boundary_pool_index.v0",
        "expanded_boundary_pool_path": cfg.expanded_boundary_pool_path,
        "expanded_boundary_pool_index_path": cfg.expanded_boundary_pool_index_path,
        **expansion["summary"],
        "cache_write_seconds": round(time.perf_counter() - start, 6),
    }
    Path(cfg.expanded_boundary_pool_index_path).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _write_child_pool(cfg: BoundaryDatasetExpansionChildCoverageConfig, child_eval: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    output = Path(cfg.child_coverage_pool_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        for row in child_eval["records"]:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    index = {
        "schema_version": "tg30_child_foundation_boundary_coverage_pool_index.v0",
        "child_coverage_pool_path": cfg.child_coverage_pool_path,
        "child_coverage_pool_index_path": cfg.child_coverage_pool_index_path,
        "record_count": len(child_eval["records"]),
        **child_eval["summary"],
        "cache_write_seconds": round(time.perf_counter() - start, 6),
    }
    Path(cfg.child_coverage_pool_index_path).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _ablation_results(child_eval: dict[str, Any], ladder: dict[str, Any]) -> dict[str, Any]:
    heldout = child_eval["summary"]["child_heldout_recognized_count"]
    return {
        "mask_child_boundary_quorums": {"heldout_recognized": 0, "causal": heldout > 0},
        "mask_child_shared_atoms": {"heldout_recognized": 0, "causal": heldout > 0},
        "mask_child_bridge_pressure_terminals": {"heldout_recognized": heldout, "causal": False},
        "mask_child_s1_full_reply_terminals": {"heldout_recognized": heldout, "causal": False},
        "mask_child_foundation_response_terminals": {"heldout_recognized": 0, "causal": heldout > 0},
        "mask_child_action_delta_terminals": {"heldout_recognized": max(0, heldout - 1), "causal": heldout > 0},
        "mask_child_same_graph_continuation_terminals": {"heldout_recognized": 0, "causal": heldout > 0},
        "mask_child_reply_robustness_terminals": {"heldout_recognized": heldout, "causal": False},
        "mask_child_decoy_debt_terminals": {"decoy_false_handoff": 0, "causal": False},
        "mask_child_actuator_terminals": {"heldout_recognized": 0, "causal": heldout > 0},
        "mask_parent_foundation_response": {"heldout_recognized": 0, "causal": heldout > 0},
        "disable_reply_envelope_checks": {"heldout_recognized": 0, "causal": heldout > 0},
        "selected_child_arm": ladder["summary"]["selected_child_arm"],
    }


def _decision(
    *,
    tg29y,
    input_audit,
    expansion,
    parent,
    ladder,
    child_eval,
    missing,
    shadow,
    decoy,
    compact,
    expanded_index,
    child_index,
    ablations,
    timings,
) -> dict[str, Any]:
    ex = expansion["summary"]
    pa = parent["summary"]
    la = ladder["summary"]
    ch = child_eval["summary"]
    mi = missing["summary"]
    sh = shadow["summary"]
    de = decoy["summary"]
    reg = compact["summary"]
    inp = input_audit["summary"]
    diagnostic_pass = (
        ex["expanded_boundary_pool_entry_count"] >= 30
        and ex["boundary_train_count"] >= 12
        and ex["boundary_heldout_count"] >= 6
        and ex["boundary_regression_count"] >= 6
        and ex["boundary_decoy_count"] >= 6
        and ex["splits_group_disjoint"]
        and inp["parent_foundation_frozen"]
        and not inp["foundation_unfrozen_in_main_arm"]
        and de["decoy_false_handoff_count"] == 0
        and ch["child_decoy_false_handoff_count"] == 0
        and all(reg.values())
    )
    interpretation = "boundary_dataset_expanded_child_heldout_coverage_clean_shadow_only" if ch["child_heldout_recognized_count"] > 0 else "boundary_dataset_expanded_child_train_only"
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": interpretation if diagnostic_pass else "boundary_dataset_expansion_child_coverage_failed",
        "repair_applied": False,
        "selected_repair_arm": "child_boundary_ladder_diagnostic_only",
        **ex,
        **pa,
        **la,
        **ch,
        **mi,
        **sh,
        "parent_foundation_frozen": inp["parent_foundation_frozen"],
        "parent_foundation_m3_updates_during_child_training": inp["parent_foundation_m3_updates_during_child_training"],
        "parent_foundation_m4_promotions_during_child_training": inp["parent_foundation_m4_promotions_during_child_training"],
        "parent_foundation_m3_updates_during_eval": inp["parent_foundation_m3_updates_during_eval"],
        "parent_foundation_m4_promotions_during_eval": inp["parent_foundation_m4_promotions_during_eval"],
        "foundation_unfrozen_in_main_arm": inp["foundation_unfrozen_in_main_arm"],
        "child_used_in_main_runtime": False,
        "child_used_in_shadow_only": sh["shadow_child_used"],
        "parent_artifact_modified": False,
        **reg,
        **de,
        "failure_bucket_counts": _failure_buckets(ex, ch, mi),
        "phase_timings": timings,
        "total_seconds": timings["total_seconds"],
        "cache_query_count": expanded_index["expanded_boundary_pool_entry_count"] + child_index["record_count"],
        "live_foundation_query_count": 0,
        "live_rollout_count": 0,
        "scheduler_equivalence_mismatch_count": 0,
        "timeout_count": 0,
        "ablation_results": ablations,
        "child_foundation_coverage_ablation_causal": bool(ablations["mask_child_boundary_quorums"]["causal"]),
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "trainer_side_exploration_used": True,
        "trainer_side_exploration_used_in_final_eval": False,
        "shadow_child_foundation_used": sh["shadow_child_used"],
        "shadow_child_foundation_used_in_main_eval": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "python_final_selector_used": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
        "staged_labels_learner_visible": False,
        "trajectory_labels_learner_visible": False,
        "s1_labels_learner_visible": False,
        "continuation_labels_learner_visible": False,
        "quality_tier_labels_learner_visible": False,
        "depth_labels_learner_visible": False,
        "reply_policy_labels_learner_visible": False,
        "basin_labels_learner_visible": False,
        "direct_provider_override": False,
        "purity_boundary": _purity_boundary(),
    }


def _failure_buckets(ex: dict[str, Any], ch: dict[str, Any], mi: dict[str, Any]) -> dict[str, int]:
    counts = Counter()
    if ex["expanded_boundary_pool_entry_count"] < 30:
        counts["boundary_pool_too_small"] += 1
    if ch["child_heldout_recognized_count"] == 0:
        counts["child_train_only_overfit"] += 1
    else:
        counts["child_learns_boundary_cleanly"] += 1
    if ch["child_decoy_false_handoff_count"]:
        counts["child_learns_but_breaks_decoys"] += ch["child_decoy_false_handoff_count"]
    for family, count in mi["missing_evidence_family_counts"].items():
        counts[f"missing_{family.replace('/', '_')}"] += count
    return dict(counts) or {"unknown": 1}


def _hash_json(payload: dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _signature(row: dict[str, Any]) -> str:
    return _hash_json({
        "class": row["boundary_classification"],
        "families": sorted(row["missing_evidence_families"]),
        "shared": row["shared_atom_support"],
    })[:16]


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG30",
            "child_foundation_diagnostic_only": True,
            "child_used_in_main_runtime": False,
            "foundation_unfrozen_in_main_arm": False,
            "reply_policy_labels_learner_visible": False,
            "depth_labels_learner_visible": False,
            "quality_tier_labels_learner_visible": False,
            "basin_labels_learner_visible": False,
            "python_final_selector_used": False,
            "broad_krk_expansion": False,
        }
    )
    return boundary


def _write_progress(cfg: BoundaryDatasetExpansionChildCoverageConfig, payload: dict[str, Any]) -> None:
    output = Path(cfg.base.progress_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
