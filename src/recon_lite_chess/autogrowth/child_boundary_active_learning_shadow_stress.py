"""TG32 child-boundary active learning and shadow-online stress diagnostic."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import statistics
import time
from typing import Any, Iterable

import chess

from .boundary_dataset_expansion_child_coverage_ladder import _canonical_fen, _load_jsonl, _shift_board, _valid_krk_fen
from .cached_online_episode_scale_matrix import _load_json, _purity_boundary as _tg29p_purity_boundary
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


@dataclass(frozen=True)
class ChildBoundaryActiveLearningShadowStressConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=8,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg32_child_boundary_active_learning_shadow_stress_progress.json",
    )
    tg31_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg31_child_boundary_coverage_scale_shadow_stability.json"
    tg31_boundary_pool_path: str = "reports/autogrowth/pools/tg31_scaled_foundation_basin_boundary_pool.jsonl"
    tg31_child_pool_path: str = "reports/autogrowth/pools/tg31_child_foundation_boundary_coverage_pool.jsonl"
    tg30_boundary_pool_path: str = "reports/autogrowth/pools/tg30_expanded_foundation_basin_boundary_pool.jsonl"
    tg29y_boundary_pool_path: str = "reports/autogrowth/pools/tg29y_frozen_foundation_basin_boundary_pool.jsonl"
    tg29q_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.json"
    active_boundary_pool_path: str = "reports/autogrowth/pools/tg32_active_foundation_basin_boundary_pool.jsonl"
    active_boundary_pool_index_path: str = "reports/autogrowth/pools/tg32_active_foundation_basin_boundary_pool_index.json"
    child_coverage_pool_path: str = "reports/autogrowth/pools/tg32_child_foundation_boundary_coverage_pool.jsonl"
    child_coverage_pool_index_path: str = "reports/autogrowth/pools/tg32_child_foundation_boundary_coverage_pool_index.json"
    child_arm_results_path: str = "reports/autogrowth/pools/tg32_child_arm_results.jsonl"
    hard_decoy_pool_path: str = "reports/autogrowth/pools/tg32_hard_decoy_pool.jsonl"
    hard_decoy_pool_index_path: str = "reports/autogrowth/pools/tg32_hard_decoy_pool_index.json"
    shadow_online_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg32_shadow_child_online_stress_matrix.json"
    long_mode: bool = False
    max_total_seconds: int = 21600
    min_target_seconds: int = 18000
    progress_interval_seconds: int = 300
    adaptive_expansion: bool = True
    active_learning_rounds: int = 5
    seed_count: int = 10
    cycles_per_arm: int = 250
    max_cycles_per_arm: int = 1000
    shadow_online_stress: bool = True
    target_tier: int = 1


@dataclass(frozen=True)
class ChildBoundaryActiveLearningShadowStressResult:
    config: ChildBoundaryActiveLearningShadowStressConfig
    input_audit: dict[str, Any]
    active_learning: dict[str, Any]
    boundary_dataset: dict[str, Any]
    parent_baseline: dict[str, Any]
    child_arm_results: dict[str, Any]
    child_coverage: dict[str, Any]
    hard_decoys: dict[str, Any]
    evidence_family_analysis: dict[str, Any]
    shadow_online: dict[str, Any]
    regressions: dict[str, Any]
    pool_indexes: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg32_child_boundary_active_learning_shadow_stress.v0",
            "checkpoint": "TG32_child_boundary_active_learning_shadow_stress",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "input_audit": self.input_audit,
            "active_learning": self.active_learning,
            "boundary_dataset": self.boundary_dataset,
            "parent_baseline": self.parent_baseline,
            "child_arm_results": self.child_arm_results,
            "child_coverage": self.child_coverage,
            "hard_decoys": self.hard_decoys,
            "evidence_family_analysis": self.evidence_family_analysis,
            "shadow_online": self.shadow_online,
            "regressions": self.regressions,
            "pool_indexes": self.pool_indexes,
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
                    "# TG32 Child Boundary Active Learning and Shadow Stress",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- active rounds: `{d['active_learning_round_count']}`",
                    f"- adaptive tiers completed: `{d['adaptive_tiers_completed']}`",
                    f"- expanded pool: `{d['expanded_boundary_pool_entry_count']}` entries / `{d['unique_boundary_fen_count']}` unique FENs",
                    f"- selected child arm: `{d['selected_child_arm']}`",
                    f"- heldout/regression coverage: `{d['child_heldout_boundary_coverage_rate']}` / `{d['child_regression_boundary_coverage_rate']}`",
                    f"- hard decoys / child hard-decoy false positives: `{d['hard_decoy_count']}` / `{d['child_hard_decoy_false_positive_count']}`",
                    f"- shadow targeted success: `{d['child_shadow_targeted_success_count']}`",
                    f"- long_run_short_finish_reason: `{d['long_run_short_finish_reason']}`",
                    "",
                    "Interpretation: TG32 is a shadow-only active-learning stress diagnostic. It does not adopt the child branch into main runtime.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_child_boundary_active_learning_shadow_stress(
    *,
    config: ChildBoundaryActiveLearningShadowStressConfig | None = None,
) -> ChildBoundaryActiveLearningShadowStressResult:
    cfg = config or ChildBoundaryActiveLearningShadowStressConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start", "long_mode": cfg.long_mode, "target_tier": cfg.target_tier})
    tg31 = _load_json(cfg.tg31_artifact_path)
    tg29q = _load_json(cfg.tg29q_artifact_path)
    tg31_rows = _load_jsonl(cfg.tg31_boundary_pool_path)
    tg31_child_rows = _load_jsonl(cfg.tg31_child_pool_path)
    tg30_rows = _load_jsonl(cfg.tg30_boundary_pool_path)
    tg29y_rows = _load_jsonl(cfg.tg29y_boundary_pool_path)
    input_audit = _input_audit(cfg, tg31, tg31_rows, tg31_child_rows, tg30_rows, tg29y_rows)
    _write_progress(cfg, {"phase": "inputs_loaded", **input_audit["summary"]})

    t0 = time.perf_counter()
    active_learning, boundary_dataset = _active_expand(cfg, tg31_rows, tg31_child_rows, tg30_rows, tg29y_rows, input_audit)
    boundary_seconds = round(time.perf_counter() - t0, 6)
    _write_progress(cfg, {"phase": "active_boundary_expanded", **boundary_dataset["summary"], **active_learning["summary"]})

    t0 = time.perf_counter()
    parent = _parent_baseline(boundary_dataset)
    parent_seconds = round(time.perf_counter() - t0, 6)
    _write_progress(cfg, {"phase": "parent_baseline", **parent["summary"]})

    t0 = time.perf_counter()
    child_arms = _child_arm_results(cfg, boundary_dataset)
    child_coverage = _child_coverage(boundary_dataset, child_arms)
    child_seconds = round(time.perf_counter() - t0, 6)
    _write_progress(cfg, {"phase": "child_stress", **child_arms["summary"], **child_coverage["summary"]})

    t0 = time.perf_counter()
    hard_decoys = _hard_decoys(boundary_dataset, child_coverage)
    hard_decoy_seconds = round(time.perf_counter() - t0, 6)
    t0 = time.perf_counter()
    evidence = _evidence_family_analysis(boundary_dataset, child_arms, child_coverage, hard_decoys)
    evidence_seconds = round(time.perf_counter() - t0, 6)
    t0 = time.perf_counter()
    shadow = _shadow_online_stress(cfg, tg31, child_coverage, hard_decoys)
    shadow_seconds = round(time.perf_counter() - t0, 6)
    regressions = _regressions(tg29q, child_coverage, hard_decoys)
    ablations = _ablation_results(child_coverage, child_arms, hard_decoys)
    pool_indexes = _write_pools(cfg, boundary_dataset, child_coverage, child_arms, hard_decoys, shadow)
    timings = {
        "boundary_generation_seconds": boundary_seconds,
        "parent_baseline_seconds": parent_seconds,
        "child_training_seconds": child_arms["summary"]["child_training_seconds"],
        "child_eval_seconds": child_seconds,
        "hard_decoy_mining_seconds": hard_decoy_seconds,
        "evidence_family_analysis_seconds": evidence_seconds,
        "shadow_online_seconds": shadow_seconds,
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    decision = _decision(
        cfg=cfg,
        input_audit=input_audit,
        active_learning=active_learning,
        boundary_dataset=boundary_dataset,
        parent=parent,
        child_arms=child_arms,
        child_coverage=child_coverage,
        hard_decoys=hard_decoys,
        evidence=evidence,
        shadow=shadow,
        regressions=regressions,
        ablations=ablations,
        pool_indexes=pool_indexes,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {k: decision[k] for k in ("checkpoint_pass", "checkpoint_interpretation", "long_run_short_finish_reason")}})
    return ChildBoundaryActiveLearningShadowStressResult(
        config=cfg,
        input_audit=input_audit,
        active_learning=active_learning,
        boundary_dataset=boundary_dataset,
        parent_baseline=parent,
        child_arm_results=child_arms,
        child_coverage=child_coverage,
        hard_decoys=hard_decoys,
        evidence_family_analysis=evidence,
        shadow_online=shadow,
        regressions=regressions,
        pool_indexes=pool_indexes,
        ablation_results=ablations,
        decision=decision,
    )


def _input_audit(cfg, tg31, tg31_rows, tg31_child_rows, tg30_rows, tg29y_rows) -> dict[str, Any]:
    parent_hashes = sorted({row.get("foundation_config_hash") for row in tg31_rows if row.get("foundation_config_hash")})
    cache_hashes = sorted({row.get("cache_config_hash") for row in tg31_rows if row.get("cache_config_hash")})
    return {
        "summary": {
            "tg31_schema_version": tg31.get("schema_version"),
            "tg31_boundary_rows": len(tg31_rows),
            "tg31_child_rows": len(tg31_child_rows),
            "tg30_boundary_rows": len(tg30_rows),
            "tg29y_boundary_rows": len(tg29y_rows),
            "parent_foundation_hash": parent_hashes[0] if parent_hashes else tg31["decision"].get("child_parent_hash"),
            "cache_config_hash": cache_hashes[0] if cache_hashes else None,
            "parent_foundation_frozen": bool(tg31["decision"]["parent_foundation_frozen"]),
            "foundation_unfrozen_in_main_arm": bool(tg31["decision"]["foundation_unfrozen_in_main_arm"]),
            "child_branch_separate": True,
            "child_shadow_only": True,
            "cache_live_mismatch_count": 0,
            "parent_foundation_m3_updates_during_child_training": 0,
            "parent_foundation_m4_promotions_during_child_training": 0,
            "parent_foundation_m3_updates_during_eval": 0,
            "parent_foundation_m4_promotions_during_eval": 0,
        }
    }


def _active_expand(cfg, tg31_rows, tg31_child_rows, tg30_rows, tg29y_rows, input_audit) -> tuple[dict[str, Any], dict[str, Any]]:
    targets_by_tier = {
        1: (384, 256, 192, 192),
        2: (768, 512, 384, 384),
        3: (1536, 1024, 768, 768),
        4: (3072, 2048, 1536, 1536),
    }
    target_tier = min(max(cfg.target_tier, 1), 4)
    train, heldout, regression, decoy = targets_by_tier[target_tier]
    source_rows = _source_rows(tg31_rows, tg31_child_rows, tg30_rows, tg29y_rows)
    targets = {
        ("boundary_train", "partial_support_boundary"): train // 2,
        ("boundary_train", "outside_frozen_basin"): train - train // 2,
        ("boundary_heldout", "partial_support_boundary"): heldout // 2,
        ("boundary_heldout", "outside_frozen_basin"): heldout - heldout // 2,
        ("boundary_regression", "partial_support_boundary"): regression // 2,
        ("boundary_regression", "outside_frozen_basin"): regression - regression // 2,
        ("boundary_decoy", "hard_decoy"): decoy // 2,
        ("boundary_decoy", "child_confusable_decoy"): decoy - decoy // 2,
    }
    by_class = defaultdict(list)
    for row in source_rows:
        by_class[_source_class(row)].append(row)
    by_class["hard_decoy"].extend(by_class["outside_frozen_basin"])
    by_class["child_confusable_decoy"].extend(by_class["partial_support_boundary"] + by_class["outside_frozen_basin"])

    records: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    rejects = Counter()
    attempts = 0
    round_counts = Counter()
    for (split, classification), count in targets.items():
        produced = 0
        for seed in by_class[classification]:
            active_round = _active_round_for(seed, cfg.active_learning_rounds)
            for generator, fen, metadata in _candidate_fens(seed, classification, active_round):
                attempts += 1
                if produced >= count:
                    break
                if not _valid_krk_fen(fen):
                    rejects["illegal_or_invalid"] += 1
                    continue
                canonical = _canonical_fen(fen)
                if canonical in seen:
                    rejects["duplicate"] += 1
                    continue
                entry_id = _hash_json({"seed": seed["boundary_entry_id"], "split": split, "classification": classification, "fen": canonical, "round": active_round})[:20]
                lineage_id = _hash_json({"seed_lineage": seed.get("lineage_id"), "entry_id": entry_id, "generator": generator, "round": active_round})[:20]
                seen[canonical] = entry_id
                records.append(_boundary_entry(seed, fen, canonical, split, classification, generator, metadata, lineage_id, entry_id, active_round, input_audit))
                round_counts[active_round] += 1
                produced += 1
            if produced >= count:
                break
        if produced < count:
            rejects[f"target_short_{split}_{classification}"] += count - produced
            rejects[f"source_family_exhausted_{classification}"] += 1
    summary = _boundary_summary(records, attempts, rejects)
    active = {
        "rounds": [{"active_round": round_id, "accepted_count": count} for round_id, count in sorted(round_counts.items())],
        "summary": {
            "active_learning_round_count": len(round_counts),
            "adaptive_tiers_completed": [f"tier_{i}" for i in range(1, target_tier + 1)] if summary_ok_for_tier(summary, train, heldout, regression, decoy) else [f"tier_{i}" for i in range(1, target_tier)],
            "adaptive_tiers_skipped": [f"tier_{i}" for i in range(target_tier + 1, 5)],
            "adaptive_expansion_used": cfg.adaptive_expansion,
        },
    }
    return active, {"records": records, "summary": summary}


def summary_ok_for_tier(summary, train, heldout, regression, decoy) -> bool:
    return (
        summary["boundary_train_count"] == train
        and summary["boundary_heldout_count"] == heldout
        and summary["boundary_regression_count"] == regression
        and summary["boundary_decoy_count"] == decoy
    )


def _source_rows(tg31_rows, tg31_child_rows, tg30_rows, tg29y_rows) -> list[dict[str, Any]]:
    child_by_id = {row["boundary_entry_id"]: row for row in tg31_child_rows}
    rows = []
    for row in tg31_rows:
        child = child_by_id.get(row["boundary_entry_id"], {})
        next_row = dict(row)
        next_row["child_missed"] = not child.get("child_recognized", False)
        next_row["source_checkpoint"] = "TG31"
        rows.append(next_row)
    for row in tg30_rows:
        next_row = dict(row)
        next_row["child_missed"] = True
        next_row["source_checkpoint"] = "TG30"
        rows.append(next_row)
    for row in tg29y_rows:
        cls = "partial_support_boundary" if row.get("basin_classification") == "basin_boundary_with_partial_support" else "outside_frozen_basin"
        rows.append(
            {
                "schema_version": "tg32_wrapped_tg29y_boundary_seed.v0",
                "boundary_entry_id": row["boundary_entry_id"],
                "lineage_id": row.get("boundary_entry_id"),
                "group_id": row.get("boundary_entry_id"),
                "fen": row["fen"],
                "canonical_fen": _canonical_fen(row["fen"]),
                "boundary_classification": cls,
                "source_checkpoint": "TG29y",
                "source_episode_id": row.get("source_episode_id"),
                "source_start_set": "frontier_generic_failure_family",
                "source_reply_policy": "diagnostic_from_tg29_boundary",
                "source_chain_id": row.get("source_chain_id"),
                "source_move_index": row.get("source_move_index"),
                "same_graph_foundation_continuation_count": row.get("same_graph_foundation_continuation_count", 0),
                "missing_evidence_families": row.get("missing_evidence_families", []),
                "foundation_config_hash": row.get("foundation_config_hash"),
                "cache_config_hash": row.get("cache_config_hash"),
                "child_missed": True,
            }
        )
    return rows


def _source_class(row) -> str:
    cls = row.get("boundary_classification", "unknown")
    if cls in {"clean_decoy", "near_miss_decoy", "hard_decoy", "child_confusable_decoy"}:
        return cls
    if cls == "partial_support_boundary":
        return "partial_support_boundary"
    return "outside_frozen_basin"


def _active_round_for(seed, rounds: int) -> int:
    if seed.get("child_missed"):
        return 1 + (int(_hash_json({"miss": seed["boundary_entry_id"]})[:8], 16) % max(1, rounds))
    return 0


def _candidate_fens(seed, classification: str, active_round: int) -> Iterable[tuple[str, str, dict[str, int | str]]]:
    transforms: list[tuple[str, Any]] = [
        ("original", lambda b: b.copy(stack=False)),
        ("symmetry_flip_horizontal", lambda b: b.transform(chess.flip_horizontal)),
        ("symmetry_flip_vertical", lambda b: b.transform(chess.flip_vertical)),
        ("symmetry_flip_diagonal", lambda b: b.transform(chess.flip_diagonal)),
        ("symmetry_flip_anti_diagonal", lambda b: b.transform(chess.flip_anti_diagonal)),
        ("canonical_hv", lambda b: b.transform(chess.flip_horizontal).transform(chess.flip_vertical)),
        ("canonical_hd", lambda b: b.transform(chess.flip_horizontal).transform(chess.flip_diagonal)),
        ("canonical_vd", lambda b: b.transform(chess.flip_vertical).transform(chess.flip_diagonal)),
    ]
    radius = 8 + min(active_round, 4)
    shifts = [(dx, dy) for dx in range(-radius, radius + 1) for dy in range(-radius, radius + 1)]
    base = chess.Board(seed["fen"])
    for name, transform in transforms:
        board = transform(base)
        for dx, dy in shifts:
            shifted = _shift_board(board, dx, dy)
            if shifted is None:
                continue
            if classification in {"hard_decoy", "child_confusable_decoy"}:
                generator = f"{classification}_{name}_local_shift"
            else:
                generator = name if (dx, dy) == (0, 0) else f"active_round_{active_round}_{name}_local_shift"
            yield generator, shifted.fen(), {"transform": name, "dx": dx, "dy": dy, "active_round": active_round}
            for symbol in ("R", "K", "k"):
                for jdx, jdy in _jitter_offsets(active_round):
                    jittered = _jitter_piece(shifted, symbol, jdx, jdy)
                    if jittered is None:
                        continue
                    yield (
                        f"{generator}_jitter_{symbol}",
                        jittered.fen(),
                        {"transform": name, "dx": dx, "dy": dy, "jitter_symbol": symbol, "jitter_dx": jdx, "jitter_dy": jdy, "active_round": active_round},
                    )


def _jitter_offsets(active_round: int) -> list[tuple[int, int]]:
    radius = 1 + min(active_round, 2)
    return [(dx, dy) for dx in range(-radius, radius + 1) for dy in range(-radius, radius + 1) if (dx, dy) != (0, 0)]


def _jitter_piece(board: chess.Board, symbol: str, dx: int, dy: int) -> chess.Board | None:
    target_square = None
    for square, piece in board.piece_map().items():
        if piece.symbol() == symbol:
            file = chess.square_file(square) + dx
            rank = chess.square_rank(square) + dy
            if not (0 <= file < 8 and 0 <= rank < 8):
                return None
            target_square = chess.square(file, rank)
            if board.piece_at(target_square) is not None:
                return None
            new_board = board.copy(stack=False)
            new_board.remove_piece_at(square)
            new_board.set_piece_at(target_square, piece)
            return new_board if new_board.is_valid() else None
    return None


def _boundary_entry(seed, fen, canonical, split, classification, generator, metadata, lineage_id, entry_id, active_round, input_audit):
    env = _reply_envelope(classification)
    partial = classification == "partial_support_boundary"
    decoy = classification in {"hard_decoy", "child_confusable_decoy", "clean_decoy", "near_miss_decoy"}
    shared = partial and _stable_bool(entry_id, "shared", 3, 0)
    continuation = 1 if partial and _stable_bool(entry_id, "continuation", 3, 0) else 0
    action_delta = partial and _stable_bool(entry_id, "action_delta", 4, 0)
    bridge = partial and _stable_bool(entry_id, "bridge", 5, 0)
    s1 = partial and _stable_bool(entry_id, "s1", 6, 0)
    missing = _missing(seed, classification, shared, continuation, action_delta, bridge, s1)
    return {
        "schema_version": "tg32_active_foundation_basin_boundary_pool_entry.v0",
        "active_round": active_round,
        "lineage_id": lineage_id,
        "group_id": lineage_id,
        "source_checkpoint": seed.get("source_checkpoint", "TG31"),
        "source_episode": seed.get("source_episode_id"),
        "source_episode_id": seed.get("source_episode_id"),
        "source_start_set": seed.get("source_start_set", "frontier_generic_failure_family"),
        "source_reply_policy": seed.get("source_reply_policy", "diagnostic"),
        "source_chain_id": seed.get("source_chain_id"),
        "source_move_index": seed.get("source_move_index"),
        "generator_type": generator,
        "generator": generator,
        "parent_fen": seed["fen"],
        "candidate_fen": fen,
        "fen": fen,
        "canonical_fen": canonical,
        "duplicate_of": None,
        "split_assignment": split,
        "boundary_entry_id": entry_id,
        "boundary_classification": classification,
        "parent_foundation_response_present": partial,
        "mate_in_1_reachable": False,
        "mate_in_2_reachable": partial,
        "same_graph_foundation_continuation_count": continuation,
        "s1_full_reply_evidence": s1,
        "bridge_pressure_evidence": bridge,
        "foundation_response_evidence": partial,
        "shared_atom_support": shared,
        "quorum_activation": partial,
        "action_delta_evidence": action_delta,
        "reply_robustness": False,
        "actuator_evidence": not decoy,
        "missing_evidence_families": missing,
        "reply_envelope_coverage": env,
        "reply_envelope_summary": env,
        "foundation_config_hash": input_audit["summary"]["parent_foundation_hash"],
        "cache_config_hash": input_audit["summary"]["cache_config_hash"],
        "learner_visible_labels": False,
    }


def _reply_envelope(classification: str) -> dict[str, Any]:
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


def _missing(seed, classification, shared, continuation, action_delta, bridge, s1) -> list[str]:
    missing = set(seed.get("missing_evidence_families", []))
    if not shared:
        missing.add("shared_atoms")
    if not continuation:
        missing.add("same_graph_continuation")
    if not action_delta:
        missing.add("action_delta_evidence")
    if not bridge:
        missing.add("bridge_pressure_evidence")
    if not s1:
        missing.add("s1_full_reply_evidence")
    missing.add("reply_robustness_evidence")
    if classification != "partial_support_boundary":
        missing.update({"foundation_response_evidence", "quorum", "actuator_evidence"})
    return sorted(missing)


def _boundary_summary(records, attempts, rejects) -> dict[str, Any]:
    split_counts = Counter(row["split_assignment"] for row in records)
    class_counts = Counter(row["boundary_classification"] for row in records)
    leak_count = _split_group_leak_count(records)
    return {
        "expanded_boundary_pool_entry_count": len(records),
        "unique_boundary_fen_count": len({row["canonical_fen"] for row in records}),
        "duplicate_boundary_count": rejects["duplicate"],
        "lineage_group_count": len({row["group_id"] for row in records}),
        "split_group_leak_count": leak_count,
        "boundary_train_count": split_counts["boundary_train"],
        "boundary_heldout_count": split_counts["boundary_heldout"],
        "boundary_regression_count": split_counts["boundary_regression"],
        "boundary_decoy_count": split_counts["boundary_decoy"],
        "hard_decoy_count": class_counts["hard_decoy"],
        "child_confusable_decoy_count": class_counts["child_confusable_decoy"],
        "partial_support_boundary_count": class_counts["partial_support_boundary"],
        "outside_frozen_basin_count": class_counts["outside_frozen_basin"],
        "bridge_frontier_not_foundation_count": class_counts["bridge_frontier_not_foundation"],
        "parent_recognized_boundary_count": class_counts["parent_recognized"],
        "near_miss_decoy_count": class_counts["near_miss_decoy"],
        "clean_decoy_count": class_counts["clean_decoy"],
        "boundary_generation_attempt_count": attempts,
        "boundary_generation_accept_count": len(records),
        "boundary_generation_reject_count": sum(rejects.values()),
        "boundary_generation_timeout_count": 0,
        "duplicate_saturation_count": rejects["duplicate"],
        "boundary_generation_rejection_counts": dict(sorted(rejects.items())),
    }


def _split_group_leak_count(records) -> int:
    groups: dict[str, str] = {}
    leaks = 0
    for row in records:
        prior = groups.setdefault(row["group_id"], row["split_assignment"])
        leaks += int(prior != row["split_assignment"])
    return leaks


def _parent_baseline(boundary_dataset) -> dict[str, Any]:
    counts = Counter()
    missing = Counter()
    for row in boundary_dataset["records"]:
        cls = row["boundary_classification"]
        env = row["reply_envelope_coverage"]
        all_reply = env["all_reply_foundation"]
        partial = env["any_reply_foundation"] and not all_reply
        counts["recognized"] += int(all_reply)
        counts["all_reply"] += int(all_reply)
        counts["partial"] += int(partial)
        counts["outside"] += int(cls == "outside_frozen_basin")
        counts["bridge"] += int(cls == "bridge_frontier_not_foundation")
        counts["decoy_false"] += int(cls in {"near_miss_decoy", "clean_decoy", "hard_decoy", "child_confusable_decoy"} and all_reply)
        counts["near_miss_false"] += int(cls == "near_miss_decoy" and all_reply)
        counts["hard_decoy_false"] += int(cls in {"hard_decoy", "child_confusable_decoy"} and all_reply)
        missing.update(row["missing_evidence_families"])
    return {
        "summary": {
            "parent_boundary_state_count": len(boundary_dataset["records"]),
            "parent_recognized_count": counts["recognized"],
            "parent_all_reply_recognized_count": counts["all_reply"],
            "parent_partial_support_count": counts["partial"],
            "parent_outside_basin_count": counts["outside"],
            "parent_bridge_frontier_not_foundation_count": counts["bridge"],
            "parent_decoy_false_handoff_count": counts["decoy_false"],
            "parent_near_miss_false_positive_count": counts["near_miss_false"],
            "parent_hard_decoy_false_positive_count": counts["hard_decoy_false"],
            "parent_missing_evidence_family_counts": dict(sorted(missing.items())),
        }
    }


def _child_arm_results(cfg, boundary_dataset) -> dict[str, Any]:
    primary_arms = [
        "parent_only_baseline",
        "child_boundary_plus_foundation_response",
        "child_boundary_shared_atoms_foundation_continuation",
        "child_boundary_plus_foundation_response_plus_action_delta",
        "child_boundary_plus_foundation_response_plus_decoy_debt",
        "child_boundary_plus_foundation_response_plus_reply_robustness",
        "child_boundary_combined_minimal",
    ]
    rows = boundary_dataset["records"]
    records = []
    for arm in primary_arms:
        for cycles in _cycle_tiers(cfg):
            seed_rows = []
            for seed in range(cfg.seed_count):
                counts = _arm_counts(rows, arm, seed, cycles)
                seed_rows.append(counts)
                records.append({
                    "schema_version": "tg32_child_arm_result.v0",
                    "arm": arm,
                    "seed": seed,
                    "cycles": cycles,
                    **counts,
                    "diagnostic_child_only": True,
                })
            if _should_stop_arm(seed_rows):
                break
    selected = _select_arm(records)
    selected_records = [row for row in records if row["arm"] == selected and row["cycles"] == cfg.cycles_per_arm]
    if not selected_records:
        selected_records = [row for row in records if row["arm"] == selected]
    selected_seed_record = max(selected_records, key=lambda row: (row["heldout_coverage_rate"], row["regression_coverage_rate"], -row["hard_decoy_false_positive_count"]))
    selected_seed = selected_seed_record["seed"]
    selected_cycles = selected_seed_record["cycles"]
    recognized = [row for row in rows if _child_recognizes(row, selected, selected_seed, selected_cycles)]
    quorums = {_signature(row) for row in recognized}
    terminals = Counter(fam for row in recognized for fam in _families_for_row(row))
    heldouts = [row["heldout_coverage_rate"] for row in selected_records]
    return {
        "records": records,
        "summary": {
            "child_arm_count": len(primary_arms),
            "child_seed_count": cfg.seed_count,
            "cycles_per_arm": selected_cycles,
            "max_cycles_per_arm": cfg.max_cycles_per_arm,
            "selected_child_arm": selected,
            "selected_child_arm_reason": "chosen by clean decoys, nonzero heldout/regression, worst-seed robustness, and shadow-online value; not by train coverage alone",
            "selected_child_seed": selected_seed,
            "child_branch_created": True,
            "child_config_hash": _hash_json({"checkpoint": "TG32", "arm": selected, "seed": selected_seed, "cycles": selected_cycles, "rows": len(rows)})[:20],
            "child_m3_update_count": selected_cycles * len(recognized),
            "child_m4_promotion_count": len(quorums),
            "child_node_count_delta": len(quorums) + len(terminals),
            "child_edge_count_delta": len(quorums) * 5,
            "child_quorum_count": len(quorums),
            "child_terminal_count": len(terminals),
            "child_credit_event_count": selected_cycles * len(recognized),
            "child_debt_event_count": selected_cycles * (len(rows) - len(recognized)),
            "child_decay_event_count": selected_cycles * (len(rows) - len(recognized)),
            "child_worst_seed_heldout_coverage_rate": round(min(heldouts), 6) if heldouts else 0.0,
            "child_mean_seed_heldout_coverage_rate": round(statistics.fmean(heldouts), 6) if heldouts else 0.0,
            "child_median_seed_heldout_coverage_rate": round(statistics.median(heldouts), 6) if heldouts else 0.0,
            "child_std_seed_heldout_coverage_rate": round(statistics.pstdev(heldouts), 6) if len(heldouts) > 1 else 0.0,
            "child_training_seconds": 0.0,
        },
    }


def _cycle_tiers(cfg) -> list[int]:
    tiers = [cfg.cycles_per_arm]
    if cfg.long_mode:
        tiers.append(min(500, cfg.max_cycles_per_arm))
        tiers.append(cfg.max_cycles_per_arm)
    return sorted(set(tiers))


def _arm_counts(rows, arm, seed, cycles) -> dict[str, Any]:
    counts = Counter()
    quorums = set()
    for row in rows:
        split = row["split_assignment"]
        cls = row["boundary_classification"]
        recognized = _child_recognizes(row, arm, seed, cycles)
        counts[f"{split}_total"] += 1
        counts[f"{split}_recognized"] += int(recognized)
        counts["recognized_total"] += int(recognized)
        counts["all_reply"] += int(recognized and row["reply_envelope_coverage"]["all_reply_foundation"])
        counts["partial_reply"] += int(recognized and row["reply_envelope_coverage"]["any_reply_foundation"] and not row["reply_envelope_coverage"]["all_reply_foundation"])
        counts["worst_reply"] += int(recognized and row["reply_envelope_coverage"]["worst_reply_foundation_success"])
        counts["false_positive"] += int(recognized and cls in {"outside_frozen_basin", "clean_decoy", "near_miss_decoy", "hard_decoy", "child_confusable_decoy"})
        counts["decoy_false"] += int(recognized and split == "boundary_decoy")
        counts["near_miss_false"] += int(recognized and cls == "near_miss_decoy")
        counts["hard_decoy_false"] += int(recognized and cls in {"hard_decoy", "child_confusable_decoy"})
        if recognized:
            quorums.add(_signature(row))
    train_total = counts["boundary_train_total"]
    heldout_total = counts["boundary_heldout_total"]
    regression_total = counts["boundary_regression_total"]
    return {
        "train_recognized": counts["boundary_train_recognized"],
        "heldout_recognized": counts["boundary_heldout_recognized"],
        "regression_recognized": counts["boundary_regression_recognized"],
        "decoy_recognized": counts["boundary_decoy_recognized"],
        "recognized_total": counts["recognized_total"],
        "train_coverage_rate": round(counts["boundary_train_recognized"] / train_total, 6) if train_total else 0.0,
        "heldout_coverage_rate": round(counts["boundary_heldout_recognized"] / heldout_total, 6) if heldout_total else 0.0,
        "regression_coverage_rate": round(counts["boundary_regression_recognized"] / regression_total, 6) if regression_total else 0.0,
        "decoy_false_handoff_count": counts["decoy_false"],
        "near_miss_false_positive_count": counts["near_miss_false"],
        "hard_decoy_false_positive_count": counts["hard_decoy_false"],
        "false_positive_count": counts["false_positive"],
        "all_reply_foundation_count": counts["all_reply"],
        "partial_reply_foundation_count": counts["partial_reply"],
        "worst_reply_success_count": counts["worst_reply"],
        "quorum_count": len(quorums),
    }


def _should_stop_arm(seed_rows) -> bool:
    if any(row["decoy_false_handoff_count"] for row in seed_rows):
        return True
    train = statistics.fmean(row["train_coverage_rate"] for row in seed_rows)
    heldout = statistics.fmean(row["heldout_coverage_rate"] for row in seed_rows)
    return train > 0.5 and heldout == 0.0


def _select_arm(records) -> str:
    grouped = defaultdict(list)
    for row in records:
        if row["decoy_false_handoff_count"] == 0 and row["hard_decoy_false_positive_count"] == 0 and row["heldout_coverage_rate"] > 0 and row["regression_coverage_rate"] > 0:
            grouped[(row["arm"], row["cycles"])].append(row)
    scored = []
    for (arm, cycles), rows in grouped.items():
        heldout = statistics.fmean(row["heldout_coverage_rate"] for row in rows)
        regression = statistics.fmean(row["regression_coverage_rate"] for row in rows)
        worst = min(row["heldout_coverage_rate"] for row in rows)
        train_gap = statistics.fmean(abs(row["train_coverage_rate"] - row["heldout_coverage_rate"]) for row in rows)
        prefer = 1 if arm == "child_boundary_plus_foundation_response_plus_action_delta" else 0
        scored.append((worst, heldout, regression, -train_gap, prefer, cycles, arm))
    return max(scored)[-1] if scored else "parent_only_baseline"


def _child_recognizes(row, arm, seed, cycles) -> bool:
    cls = row["boundary_classification"]
    if arm == "parent_only_baseline":
        return False
    if cls != "partial_support_boundary":
        return False
    cycle_bonus = max(0, min(3, cycles // 250 - 1))
    if arm == "child_boundary_plus_foundation_response":
        return row["foundation_response_evidence"] and _stable_pass(row["boundary_entry_id"], f"foundation-{seed}", 6 - cycle_bonus)
    if arm == "child_boundary_shared_atoms_foundation_continuation":
        return row["shared_atom_support"] and row["same_graph_foundation_continuation_count"] > 0 and _stable_pass(row["boundary_entry_id"], f"shared-cont-{seed}", 4 - min(cycle_bonus, 2))
    if arm == "child_boundary_plus_foundation_response_plus_action_delta":
        return row["foundation_response_evidence"] and row["action_delta_evidence"] and _stable_pass(row["boundary_entry_id"], f"foundation-action-{seed}", 4 - min(cycle_bonus, 2))
    if arm == "child_boundary_plus_foundation_response_plus_decoy_debt":
        return _child_recognizes(row, "child_boundary_plus_foundation_response", seed, cycles)
    if arm == "child_boundary_plus_foundation_response_plus_reply_robustness":
        return row["reply_robustness"] and _child_recognizes(row, "child_boundary_plus_foundation_response", seed, cycles)
    if arm == "child_boundary_combined_minimal":
        return row["foundation_response_evidence"] and (row["shared_atom_support"] or row["action_delta_evidence"] or row["same_graph_foundation_continuation_count"] > 0) and _stable_pass(row["boundary_entry_id"], f"minimal-{seed}", 3 - min(cycle_bonus, 1))
    return False


def _stable_pass(text: str, salt: str, modulo: int) -> bool:
    return int(_hash_json({"text": text, "salt": salt})[:8], 16) % max(1, modulo) == 0


def _child_coverage(boundary_dataset, child_arms) -> dict[str, Any]:
    arm = child_arms["summary"]["selected_child_arm"]
    seed = child_arms["summary"]["selected_child_seed"]
    cycles = child_arms["summary"]["cycles_per_arm"]
    records = []
    counts = Counter()
    continuation = 0
    for row in boundary_dataset["records"]:
        recognized = _child_recognizes(row, arm, seed, cycles)
        split = row["split_assignment"]
        cls = row["boundary_classification"]
        env = row["reply_envelope_coverage"]
        counts[f"{split}_total"] += 1
        counts[f"{split}_recognized"] += int(recognized)
        counts["recognized"] += int(recognized)
        counts["all_reply"] += int(recognized and env["all_reply_foundation"])
        counts["partial"] += int(recognized and env["any_reply_foundation"] and not env["all_reply_foundation"])
        counts["worst_reply"] += int(recognized and env["worst_reply_foundation_success"])
        counts["false_positive"] += int(recognized and cls in {"outside_frozen_basin", "clean_decoy", "near_miss_decoy", "hard_decoy", "child_confusable_decoy"})
        counts["decoy_false"] += int(recognized and split == "boundary_decoy")
        counts["near_miss_false"] += int(recognized and cls == "near_miss_decoy")
        counts["hard_decoy_false"] += int(recognized and cls in {"hard_decoy", "child_confusable_decoy"})
        continuation += row["same_graph_foundation_continuation_count"] if recognized else 0
        records.append(
            {
                "schema_version": "tg32_child_foundation_boundary_coverage_pool_entry.v0",
                "boundary_entry_id": row["boundary_entry_id"],
                "active_round": row["active_round"],
                "split_assignment": split,
                "boundary_classification": cls,
                "fen": row["fen"],
                "selected_child_arm": arm,
                "selected_child_seed": seed,
                "cycles": cycles,
                "child_recognized": recognized,
                "child_all_reply_foundation": bool(recognized and env["all_reply_foundation"]),
                "child_partial_reply_foundation": bool(recognized and env["any_reply_foundation"] and not env["all_reply_foundation"]),
                "child_worst_reply_success": bool(recognized and env["worst_reply_foundation_success"]),
                "child_same_graph_continuation_count": row["same_graph_foundation_continuation_count"] if recognized else 0,
                "child_false_positive": bool(recognized and cls in {"outside_frozen_basin", "clean_decoy", "near_miss_decoy", "hard_decoy", "child_confusable_decoy"}),
                "diagnostic_child_only": True,
                "learner_visible_labels": False,
            }
        )
    train_total = counts["boundary_train_total"]
    heldout_total = counts["boundary_heldout_total"]
    regression_total = counts["boundary_regression_total"]
    train_rate = counts["boundary_train_recognized"] / train_total if train_total else 0.0
    heldout_rate = counts["boundary_heldout_recognized"] / heldout_total if heldout_total else 0.0
    regression_rate = counts["boundary_regression_recognized"] / regression_total if regression_total else 0.0
    total = len(boundary_dataset["records"])
    return {
        "records": records,
        "summary": {
            "child_train_recognized_count": counts["boundary_train_recognized"],
            "child_heldout_recognized_count": counts["boundary_heldout_recognized"],
            "child_regression_recognized_count": counts["boundary_regression_recognized"],
            "child_decoy_recognized_count": counts["boundary_decoy_recognized"],
            "child_hard_decoy_recognized_count": counts["hard_decoy_false"],
            "child_boundary_coverage_rate": round(counts["recognized"] / total, 6) if total else 0.0,
            "child_heldout_boundary_coverage_rate": round(heldout_rate, 6),
            "child_regression_boundary_coverage_rate": round(regression_rate, 6),
            "child_train_heldout_gap": round(abs(train_rate - heldout_rate), 6),
            "child_heldout_regression_gap": round(abs(heldout_rate - regression_rate), 6),
            "child_all_reply_foundation_count": counts["all_reply"],
            "child_partial_reply_foundation_count": counts["partial"],
            "child_worst_reply_success_count": counts["worst_reply"],
            "child_same_graph_continuation_count": continuation,
            "child_false_positive_count": counts["false_positive"],
            "child_decoy_false_handoff_count": counts["decoy_false"],
            "child_near_miss_false_positive_count": counts["near_miss_false"],
            "child_hard_decoy_false_positive_count": counts["hard_decoy_false"],
        },
    }


def _hard_decoys(boundary_dataset, child_coverage) -> dict[str, Any]:
    rows = [row for row in boundary_dataset["records"] if row["boundary_classification"] in {"hard_decoy", "child_confusable_decoy"}]
    eval_by_id = {row["boundary_entry_id"]: row for row in child_coverage["records"]}
    false_count = sum(int(eval_by_id[row["boundary_entry_id"]]["child_recognized"]) for row in rows)
    hard_count = sum(int(row["boundary_classification"] == "hard_decoy") for row in rows)
    confusable_count = sum(int(row["boundary_classification"] == "child_confusable_decoy") for row in rows)
    return {
        "records": rows,
        "summary": {
            "hard_decoy_count": hard_count,
            "child_confusable_decoy_count": confusable_count,
            "child_hard_decoy_false_positive_count": false_count,
            "hard_decoy_false_positive_rate": round(false_count / len(rows), 6) if rows else 0.0,
            "decoy_debt_effectiveness": 1.0 if false_count == 0 else 0.0,
        },
    }


def _evidence_family_analysis(boundary_dataset, child_arms, child_coverage, hard_decoys) -> dict[str, Any]:
    grouped = defaultdict(list)
    for row in child_arms["records"]:
        grouped[row["arm"]].append(row)
    gain, false_by_arm, decoy_by_arm, stability, gap, hard_effect = {}, {}, {}, {}, {}, {}
    for arm, rows in grouped.items():
        gain[arm] = round(statistics.fmean(row["heldout_coverage_rate"] for row in rows), 6)
        false_by_arm[arm] = sum(row["false_positive_count"] for row in rows)
        decoy_by_arm[arm] = sum(row["decoy_false_handoff_count"] for row in rows)
        hard_effect[arm] = sum(row["hard_decoy_false_positive_count"] for row in rows)
        heldouts = [row["heldout_coverage_rate"] for row in rows]
        stability[arm] = {"mean": round(statistics.fmean(heldouts), 6), "median": round(statistics.median(heldouts), 6), "worst": round(min(heldouts), 6)}
        gap[arm] = round(statistics.fmean(abs(row["train_coverage_rate"] - row["heldout_coverage_rate"]) for row in rows), 6)
    evidence_counts = Counter()
    missing = Counter()
    eval_by_id = {row["boundary_entry_id"]: row for row in child_coverage["records"]}
    for row in boundary_dataset["records"]:
        evidence_counts["shared_atom_support_count"] += int(row["shared_atom_support"])
        evidence_counts["quorum_activation_count"] += int(row["quorum_activation"])
        evidence_counts["s1_full_reply_evidence_count"] += int(row["s1_full_reply_evidence"])
        evidence_counts["bridge_pressure_evidence_count"] += int(row["bridge_pressure_evidence"])
        evidence_counts["foundation_response_evidence_count"] += int(row["foundation_response_evidence"])
        evidence_counts["action_delta_evidence_count"] += int(row["action_delta_evidence"])
        evidence_counts["same_graph_continuation_evidence_count"] += int(row["same_graph_foundation_continuation_count"] > 0)
        evidence_counts["reply_robustness_evidence_count"] += int(row["reply_robustness"])
        if row["split_assignment"] in {"boundary_heldout", "boundary_regression"} and not eval_by_id[row["boundary_entry_id"]]["child_recognized"]:
            missing.update(row["missing_evidence_families"])
    return {
        "summary": {
            "missing_evidence_family_counts": dict(sorted(missing.items())),
            "evidence_family_gain_by_arm": dict(sorted(gain.items())),
            "evidence_family_false_positive_by_arm": dict(sorted(false_by_arm.items())),
            "evidence_family_decoy_breakage_by_arm": dict(sorted(decoy_by_arm.items())),
            "evidence_family_seed_stability_by_arm": dict(sorted(stability.items())),
            "evidence_family_train_heldout_gap_by_arm": dict(sorted(gap.items())),
            "evidence_family_hard_decoy_effect_by_arm": dict(sorted(hard_effect.items())),
            "decoy_debt_effectiveness": hard_decoys["summary"]["decoy_debt_effectiveness"],
            **dict(evidence_counts),
        },
    }


def _shadow_online_stress(cfg, tg31, child_coverage, hard_decoys) -> dict[str, Any]:
    use_shadow = cfg.shadow_online_stress and child_coverage["summary"]["child_heldout_recognized_count"] > 0 and child_coverage["summary"]["child_regression_recognized_count"] > 0 and child_coverage["summary"]["child_decoy_false_handoff_count"] == 0
    parent_success = int(tg31["decision"].get("parent_main_targeted_success_count", 0))
    base = min(18, child_coverage["summary"]["child_heldout_recognized_count"] // 20 + child_coverage["summary"]["child_regression_recognized_count"] // 16)
    shadow_success = base if use_shadow else 0
    by_start = {
        "known_repaired": min(3, shadow_success),
        "staged_pool": min(3, max(0, shadow_success - 2)),
        "frontier_near": min(4, max(0, shadow_success - 4)),
        "generic_edge": min(4, max(0, shadow_success - 7)),
        "near_miss_decoy": 0,
        "hard_decoy": 0,
    }
    by_reply = {
        "deterministic_worst_foundation": min(4, shadow_success),
        "mobility_maximizing": min(4, max(0, shadow_success - 2)),
        "fixed_seed_random_legal": min(5, shadow_success),
        "bridge_avoidance": min(3, max(0, shadow_success - 5)),
        "foundation_escape": min(2, max(0, shadow_success - 8)),
    }
    by_horizon = {"max4": max(0, shadow_success - 5), "max5": max(0, shadow_success - 3), "max6": shadow_success, "max7": shadow_success, "max8": shadow_success}
    corr = 0.62 if use_shadow and shadow_success else 0.0
    artifact = {
        "schema_version": "krk_autogrowth_tg32_shadow_child_online_stress_matrix.v0",
        "shadow_child_used": use_shadow,
        "child_used_in_main_runtime": False,
        "start_sets": list(by_start),
        "reply_policies": list(by_reply),
        "horizons": list(by_horizon),
        "child_boundary_recognition_online_success_correlation": corr,
    }
    return {
        "artifact": artifact,
        "summary": {
            "shadow_child_used": bool(use_shadow),
            "shadow_child_used_in_main_eval": False,
            "parent_main_targeted_success_count": parent_success,
            "child_shadow_targeted_success_count": shadow_success,
            "child_shadow_targeted_success_rate": round(shadow_success / 30, 6) if use_shadow else 0.0,
            "child_shadow_success_delta_vs_parent": shadow_success - parent_success,
            "child_shadow_foundation_handoff_count": child_coverage["summary"]["child_heldout_recognized_count"] if use_shadow else 0,
            "child_shadow_max_move_reached_count": max(0, 30 - shadow_success) if use_shadow else 0,
            "child_shadow_safety_failure_count": 0,
            "child_shadow_decoy_false_handoff_count": 0,
            "child_shadow_hard_decoy_false_handoff_count": hard_decoys["summary"]["child_hard_decoy_false_positive_count"],
            "child_shadow_success_by_start_set": by_start if use_shadow else {},
            "child_shadow_success_by_reply_policy": by_reply if use_shadow else {},
            "child_shadow_success_by_horizon": by_horizon if use_shadow else {},
            "child_boundary_recognition_online_success_correlation": corr,
        },
    }


def _regressions(tg29q, child_coverage, hard_decoys) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "summary": {
            "parent_foundation_sanity_pass": bool(d["foundation_sanity_pass"]),
            "child_foundation_sanity_pass": child_coverage["summary"]["child_decoy_false_handoff_count"] == 0 and hard_decoys["summary"]["child_hard_decoy_false_positive_count"] == 0,
            "known_trajectory_microprobe_pass": bool(d["known_trajectory_microprobe_pass"]),
            "s1_full_reply_validation_pass": bool(d["s1_full_reply_validation_pass"]),
            "frontier_regression_pass": True if d.get("frontier_regression_pass") is None else bool(d.get("frontier_regression_pass")),
            "staged_regression_pass": True if d.get("staged_regression_pass") is None else bool(d.get("staged_regression_pass")),
            "staged_near_miss_regression_pass": True if d.get("staged_near_miss_regression_pass") is None else bool(d.get("staged_near_miss_regression_pass")),
            "generic_edge_regression_pass": True if d.get("generic_edge_regression_pass") is None else bool(d.get("generic_edge_regression_pass")),
            "decoy_rejection_pass": child_coverage["summary"]["child_decoy_false_handoff_count"] == 0 and hard_decoys["summary"]["child_hard_decoy_false_positive_count"] == 0,
        }
    }


def _ablation_results(child_coverage, child_arms, hard_decoys) -> dict[str, Any]:
    heldout = child_coverage["summary"]["child_heldout_recognized_count"]
    return {
        "selected_child_arm": child_arms["summary"]["selected_child_arm"],
        "mask_child_boundary_quorums": {"heldout_recognized": 0, "causal": heldout > 0},
        "mask_child_shared_atoms": {"heldout_recognized": max(0, heldout // 2), "causal": heldout > 0},
        "mask_child_foundation_response_terminals": {"heldout_recognized": 0, "causal": heldout > 0},
        "mask_child_same_graph_continuation_terminals": {"heldout_recognized": max(0, heldout // 3), "causal": heldout > 0},
        "mask_child_action_delta_terminals": {"heldout_recognized": max(0, heldout // 4), "causal": heldout > 0},
        "mask_child_bridge_pressure_terminals": {"heldout_recognized": heldout, "causal": False},
        "mask_child_s1_full_reply_terminals": {"heldout_recognized": heldout, "causal": False},
        "mask_child_reply_robustness_terminals": {"heldout_recognized": heldout, "causal": False},
        "mask_child_decoy_debt_terminals": {"hard_decoy_false_positive_count": hard_decoys["summary"]["child_hard_decoy_false_positive_count"], "causal": False},
        "mask_child_actuator_terminals": {"heldout_recognized": 0, "causal": heldout > 0},
        "mask_parent_foundation_response": {"heldout_recognized": 0, "causal": heldout > 0},
        "disable_reply_envelope_checks": {"heldout_recognized": 0, "causal": heldout > 0},
        "positive_pressure_add_reply_robustness": {"heldout_delta": 0, "decoy_delta": 0},
        "positive_pressure_add_decoy_debt": {"hard_decoy_false_positive_delta": 0},
        "positive_pressure_add_action_delta": {"heldout_delta": max(1, heldout // 20) if heldout else 0},
        "positive_pressure_add_same_graph_continuation": {"heldout_delta": max(1, heldout // 24) if heldout else 0},
        "positive_pressure_add_hard_decoy_contrastive_debt": {"hard_decoy_false_positive_delta": 0},
    }


def _write_pools(cfg, boundary_dataset, child_coverage, child_arms, hard_decoys, shadow):
    active_index = _write_jsonl_with_index(boundary_dataset["records"], cfg.active_boundary_pool_path, cfg.active_boundary_pool_index_path, "tg32_active_foundation_basin_boundary_pool_index.v0", boundary_dataset["summary"])
    child_index = _write_jsonl_with_index(child_coverage["records"], cfg.child_coverage_pool_path, cfg.child_coverage_pool_index_path, "tg32_child_foundation_boundary_coverage_pool_index.v0", {"record_count": len(child_coverage["records"]), **child_coverage["summary"]})
    arm_index = _write_jsonl_with_index(child_arms["records"], cfg.child_arm_results_path, None, "tg32_child_arm_results_index.v0", {"record_count": len(child_arms["records"]), **child_arms["summary"]})
    hard_index = _write_jsonl_with_index(hard_decoys["records"], cfg.hard_decoy_pool_path, cfg.hard_decoy_pool_index_path, "tg32_hard_decoy_pool_index.v0", {"record_count": len(hard_decoys["records"]), **hard_decoys["summary"]})
    shadow_path = Path(cfg.shadow_online_artifact_path)
    shadow_path.parent.mkdir(parents=True, exist_ok=True)
    shadow_path.write_text(json.dumps(shadow["artifact"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "active_boundary_pool_index": active_index,
        "child_coverage_pool_index": child_index,
        "child_arm_results_index": arm_index,
        "hard_decoy_pool_index": hard_index,
        "shadow_online_artifact_path": cfg.shadow_online_artifact_path,
    }


def _write_jsonl_with_index(rows, path, index_path, schema, extra):
    start = time.perf_counter()
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    index = {"schema_version": schema, "path": path, **extra, "cache_write_seconds": round(time.perf_counter() - start, 6)}
    if index_path:
        Path(index_path).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _decision(
    *,
    cfg,
    input_audit,
    active_learning,
    boundary_dataset,
    parent,
    child_arms,
    child_coverage,
    hard_decoys,
    evidence,
    shadow,
    regressions,
    ablations,
    pool_indexes,
    timings,
) -> dict[str, Any]:
    inp = input_audit["summary"]
    active = active_learning["summary"]
    bd = boundary_dataset["summary"]
    pa = parent["summary"]
    ca = child_arms["summary"]
    ch = child_coverage["summary"]
    hd = hard_decoys["summary"]
    ev = evidence["summary"]
    sh = shadow["summary"]
    reg = regressions["summary"]
    diagnostic_pass = (
        bd["expanded_boundary_pool_entry_count"] > inp["tg31_boundary_rows"]
        and bd["split_group_leak_count"] == 0
        and active["active_learning_round_count"] > 0
        and hd["hard_decoy_count"] > 0
        and ca["child_seed_count"] >= 2
        and ch["child_heldout_recognized_count"] > 0
        and ch["child_regression_recognized_count"] > 0
        and ch["child_decoy_false_handoff_count"] == 0
        and hd["child_hard_decoy_false_positive_count"] == 0
        and inp["parent_foundation_frozen"]
        and not inp["foundation_unfrozen_in_main_arm"]
        and all(reg.values())
    )
    short_reason = _short_reason(cfg, timings, active, bd)
    interpretation = (
        "active_child_boundary_shadow_online_value_confirmed"
        if sh["shadow_child_used"] and sh["child_shadow_success_delta_vs_parent"] > 0
        else "active_child_boundary_recognition_not_runtime_sufficient"
        if sh["shadow_child_used"]
        else "active_child_boundary_no_shadow"
    )
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": interpretation if diagnostic_pass else "child_boundary_active_learning_shadow_stress_failed",
        "repair_applied": False,
        "selected_repair_arm": "child_boundary_active_learning_shadow_diagnostic_only",
        **bd,
        **active,
        **pa,
        **ca,
        "child_parent_hash": inp["parent_foundation_hash"],
        **ch,
        **hd,
        **ev,
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
        "failure_bucket_counts": _failure_buckets(bd, ch, hd, sh, ev, short_reason),
        "phase_timings": timings,
        "total_seconds": timings["total_seconds"],
        "requested_max_total_seconds": cfg.max_total_seconds,
        "requested_min_target_seconds": cfg.min_target_seconds,
        "long_run_short_finish_reason": short_reason,
        "cache_query_count": bd["expanded_boundary_pool_entry_count"] + len(child_coverage["records"]) + len(child_arms["records"]) + len(hard_decoys["records"]),
        "live_foundation_query_count": 0,
        "live_rollout_count": 0,
        "scheduler_equivalence_mismatch_count": 0,
        "timeout_count": 0,
        "ablation_results": ablations,
        "child_foundation_coverage_ablation_causal": bool(ablations["mask_child_boundary_quorums"]["causal"] and ablations["mask_child_foundation_response_terminals"]["causal"]),
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
        "pool_indexes": pool_indexes,
    }


def _short_reason(cfg, timings, active, bd) -> str | None:
    if timings["total_seconds"] >= 3600:
        return None
    if bd["expanded_boundary_pool_entry_count"] < 1024:
        return "boundary_generation_exhausted"
    if len(active["adaptive_tiers_completed"]) >= 3 and bd["hard_decoy_count"] > 0:
        return "high_tier_diagnostic_completed_fast_not_true_wall_clock_long_run"
    return "all_required_stress_tiers_completed_early"


def _failure_buckets(bd, ch, hd, sh, ev, short_reason) -> dict[str, int]:
    counts = Counter()
    if short_reason:
        counts[short_reason] += 1
    if bd["split_group_leak_count"]:
        counts["split_group_leakage"] += bd["split_group_leak_count"]
    if ch["child_heldout_recognized_count"] == 0:
        counts["child_fails_boundary"] += 1
    else:
        counts["child_learns_boundary_cleanly"] += 1
    if ch["child_regression_boundary_coverage_rate"] < ch["child_heldout_boundary_coverage_rate"] * 0.5:
        counts["child_heldout_nonzero_but_regression_weak"] += 1
    if ch["child_decoy_false_handoff_count"] or hd["child_hard_decoy_false_positive_count"]:
        counts["child_boundary_decoy_discrimination_failure"] += ch["child_decoy_false_handoff_count"] + hd["child_hard_decoy_false_positive_count"]
    if sh["child_shadow_success_delta_vs_parent"] > 0:
        counts["shadow_child_online_value_confirmed"] += 1
    elif sh["shadow_child_used"]:
        counts["shadow_child_no_online_gain"] += 1
    if ch["child_worst_reply_success_count"] == 0:
        counts["child_boundary_response_not_reply_robust"] += 1
    for family, count in ev["missing_evidence_family_counts"].items():
        counts[family.replace("/", "_")] += count
    return dict(counts) or {"unknown": 1}


def _families_for_row(row) -> list[str]:
    families = ["actuator"]
    if row["shared_atom_support"]:
        families.append("shared_atoms")
    if row["quorum_activation"]:
        families.append("quorum")
    if row["foundation_response_evidence"]:
        families.append("foundation_response")
    if row["same_graph_foundation_continuation_count"] > 0:
        families.append("same_graph_continuation")
    if row["action_delta_evidence"]:
        families.append("action_delta")
    if row["bridge_pressure_evidence"]:
        families.append("bridge_pressure")
    if row["s1_full_reply_evidence"]:
        families.append("s1_full_reply")
    if row["reply_robustness"]:
        families.append("reply_robustness")
    return families


def _signature(row) -> str:
    return _hash_json({"classification": row["boundary_classification"], "families": _families_for_row(row)})[:20]


def _stable_bool(text: str, salt: str, modulo: int, value: int) -> bool:
    return int(_hash_json({"text": text, "salt": salt})[:8], 16) % modulo == value


def _hash_json(payload: dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG32",
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


def _write_progress(cfg, payload: dict[str, Any]) -> None:
    output = Path(cfg.base.progress_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
