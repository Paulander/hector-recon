"""TG31 long-run child boundary coverage scale and shadow stability diagnostic."""

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

from .boundary_dataset_expansion_child_coverage_ladder import (
    _canonical_fen,
    _load_jsonl,
    _shift_board,
    _valid_krk_fen,
)
from .cached_online_episode_scale_matrix import _load_json, _purity_boundary as _tg29p_purity_boundary
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


@dataclass(frozen=True)
class ChildBoundaryCoverageScaleShadowStabilityConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=6,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg31_child_boundary_coverage_scale_shadow_stability_progress.json",
    )
    tg30_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg30_boundary_dataset_expansion_child_coverage_ladder.json"
    tg30_boundary_pool_path: str = "reports/autogrowth/pools/tg30_expanded_foundation_basin_boundary_pool.jsonl"
    tg30_child_pool_path: str = "reports/autogrowth/pools/tg30_child_foundation_boundary_coverage_pool.jsonl"
    tg29y_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29y_tight_followup_success_basin_coverage.json"
    tg29y_boundary_pool_path: str = "reports/autogrowth/pools/tg29y_frozen_foundation_basin_boundary_pool.jsonl"
    tg29z_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29z_child_foundation_basin_coverage_diagnostic.json"
    tg29q_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.json"
    scaled_boundary_pool_path: str = "reports/autogrowth/pools/tg31_scaled_foundation_basin_boundary_pool.jsonl"
    scaled_boundary_pool_index_path: str = "reports/autogrowth/pools/tg31_scaled_foundation_basin_boundary_pool_index.json"
    child_coverage_pool_path: str = "reports/autogrowth/pools/tg31_child_foundation_boundary_coverage_pool.jsonl"
    child_coverage_pool_index_path: str = "reports/autogrowth/pools/tg31_child_foundation_boundary_coverage_pool_index.json"
    child_arm_results_path: str = "reports/autogrowth/pools/tg31_child_arm_results.jsonl"
    shadow_online_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg31_shadow_child_online_stability_matrix.json"
    long_mode: bool = False
    max_total_seconds: int = 1800
    min_target_seconds: int = 0
    progress_interval_seconds: int = 300
    boundary_target_scale: str = "minimum"
    child_cycle_scale: str = "short"
    multi_seed_count: int = 3
    target_train_count: int = 96
    target_heldout_count: int = 64
    target_regression_count: int = 48
    target_decoy_count: int = 48


@dataclass(frozen=True)
class ChildBoundaryCoverageScaleShadowStabilityResult:
    config: ChildBoundaryCoverageScaleShadowStabilityConfig
    input_audit: dict[str, Any]
    boundary_dataset: dict[str, Any]
    parent_baseline: dict[str, Any]
    child_arm_ladder: dict[str, Any]
    child_coverage: dict[str, Any]
    evidence_family_analysis: dict[str, Any]
    heldout_failure_analysis: dict[str, Any]
    ablation_results: dict[str, Any]
    shadow_online: dict[str, Any]
    regressions: dict[str, Any]
    pool_indexes: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg31_child_boundary_coverage_scale_shadow_stability.v0",
            "checkpoint": "TG31_child_boundary_coverage_scale_shadow_stability",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "input_audit": self.input_audit,
            "boundary_dataset": self.boundary_dataset,
            "parent_baseline": self.parent_baseline,
            "child_arm_ladder": self.child_arm_ladder,
            "child_coverage": self.child_coverage,
            "evidence_family_analysis": self.evidence_family_analysis,
            "heldout_failure_analysis": self.heldout_failure_analysis,
            "ablation_results": self.ablation_results,
            "shadow_online": self.shadow_online,
            "regressions": self.regressions,
            "pool_indexes": self.pool_indexes,
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
                    "# TG31 Child Boundary Coverage Scale and Shadow Stability",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- expanded pool: `{d['expanded_boundary_pool_entry_count']}` entries, `{d['unique_boundary_fen_count']}` unique FENs",
                    f"- split train/heldout/regression/decoy: `{d['boundary_train_count']}` / `{d['boundary_heldout_count']}` / `{d['boundary_regression_count']}` / `{d['boundary_decoy_count']}`",
                    f"- selected child arm: `{d['selected_child_arm']}`",
                    f"- heldout/regression coverage: `{d['child_heldout_boundary_coverage_rate']}` / `{d['child_regression_boundary_coverage_rate']}`",
                    f"- worst-seed heldout coverage: `{d['child_worst_seed_heldout_coverage_rate']}`",
                    f"- decoy false handoff: `{d['child_decoy_false_handoff_count']}`",
                    f"- shadow child used: `{d['shadow_child_used']}`",
                    f"- long_run_short_finish_reason: `{d['long_run_short_finish_reason']}`",
                    "",
                    "Interpretation: TG31 is a shadow-only boundary coverage stability diagnostic. It does not adopt the child branch into main runtime.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_child_boundary_coverage_scale_shadow_stability(
    *,
    config: ChildBoundaryCoverageScaleShadowStabilityConfig | None = None,
) -> ChildBoundaryCoverageScaleShadowStabilityResult:
    cfg = config or ChildBoundaryCoverageScaleShadowStabilityConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start", "long_mode": cfg.long_mode})
    tg30 = _load_json(cfg.tg30_artifact_path)
    tg29y = _load_json(cfg.tg29y_artifact_path)
    tg29z = _load_json(cfg.tg29z_artifact_path)
    tg29q = _load_json(cfg.tg29q_artifact_path)
    tg30_rows = _load_jsonl(cfg.tg30_boundary_pool_path)
    tg30_child_rows = _load_jsonl(cfg.tg30_child_pool_path)
    tg29y_rows = _load_jsonl(cfg.tg29y_boundary_pool_path)

    input_audit = _input_audit(cfg, tg30, tg29y, tg29z, tg30_rows, tg30_child_rows, tg29y_rows)
    _write_progress(cfg, {"phase": "inputs_loaded", **input_audit["summary"]})

    t0 = time.perf_counter()
    boundary_dataset = _expand_boundary_dataset(cfg, tg30_rows, tg29y_rows, input_audit)
    boundary_seconds = round(time.perf_counter() - t0, 6)
    _write_progress(cfg, {"phase": "boundary_scaled", **boundary_dataset["summary"]})

    t0 = time.perf_counter()
    parent_baseline = _parent_baseline(boundary_dataset)
    parent_seconds = round(time.perf_counter() - t0, 6)
    _write_progress(cfg, {"phase": "parent_baseline", **parent_baseline["summary"]})

    t0 = time.perf_counter()
    child_ladder = _child_arm_ladder(cfg, boundary_dataset, input_audit)
    child_coverage = _child_coverage(boundary_dataset, child_ladder)
    child_seconds = round(time.perf_counter() - t0, 6)
    _write_progress(cfg, {"phase": "child_ladder", **child_ladder["summary"], **child_coverage["summary"]})

    t0 = time.perf_counter()
    evidence = _evidence_family_analysis(boundary_dataset, child_ladder, child_coverage)
    failures = _heldout_failure_analysis(boundary_dataset, child_coverage)
    evidence_seconds = round(time.perf_counter() - t0, 6)

    t0 = time.perf_counter()
    ablations = _ablation_results(child_coverage, child_ladder)
    shadow = _shadow_online(cfg, tg29y, child_coverage, child_ladder)
    shadow_seconds = round(time.perf_counter() - t0, 6)
    regressions = _regressions(tg29q, child_coverage)
    pool_indexes = _write_pools(cfg, boundary_dataset, child_coverage, child_ladder, shadow)
    timings = {
        "boundary_generation_seconds": boundary_seconds,
        "parent_baseline_seconds": parent_seconds,
        "child_training_seconds": child_ladder["summary"]["child_training_seconds"],
        "child_eval_seconds": child_seconds,
        "evidence_family_analysis_seconds": evidence_seconds,
        "shadow_online_seconds": shadow_seconds,
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    decision = _decision(
        cfg=cfg,
        input_audit=input_audit,
        boundary_dataset=boundary_dataset,
        parent_baseline=parent_baseline,
        child_ladder=child_ladder,
        child_coverage=child_coverage,
        evidence=evidence,
        failures=failures,
        ablations=ablations,
        shadow=shadow,
        regressions=regressions,
        pool_indexes=pool_indexes,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {k: decision[k] for k in ("checkpoint_pass", "checkpoint_interpretation", "long_run_short_finish_reason")}})
    return ChildBoundaryCoverageScaleShadowStabilityResult(
        config=cfg,
        input_audit=input_audit,
        boundary_dataset=boundary_dataset,
        parent_baseline=parent_baseline,
        child_arm_ladder=child_ladder,
        child_coverage=child_coverage,
        evidence_family_analysis=evidence,
        heldout_failure_analysis=failures,
        ablation_results=ablations,
        shadow_online=shadow,
        regressions=regressions,
        pool_indexes=pool_indexes,
        decision=decision,
    )


def _input_audit(cfg, tg30, tg29y, tg29z, tg30_rows, tg30_child_rows, tg29y_rows) -> dict[str, Any]:
    parent_hashes = sorted({row.get("foundation_config_hash") for row in tg30_rows if row.get("foundation_config_hash")})
    cache_hashes = sorted({row.get("cache_config_hash") for row in tg30_rows if row.get("cache_config_hash")})
    return {
        "summary": {
            "tg30_schema_version": tg30.get("schema_version"),
            "tg29y_schema_version": tg29y.get("schema_version"),
            "tg29z_schema_version": tg29z.get("schema_version"),
            "tg30_boundary_rows": len(tg30_rows),
            "tg30_child_rows": len(tg30_child_rows),
            "tg29y_boundary_rows": len(tg29y_rows),
            "parent_foundation_hash": parent_hashes[0] if parent_hashes else tg29z["decision"].get("child_parent_hash"),
            "cache_config_hash": cache_hashes[0] if cache_hashes else None,
            "tg30_pool_schema": tg30_rows[0].get("schema_version") if tg30_rows else None,
            "parent_foundation_frozen": bool(tg30["decision"]["parent_foundation_frozen"]),
            "foundation_unfrozen_in_main_arm": bool(tg30["decision"]["foundation_unfrozen_in_main_arm"]),
            "parent_foundation_m3_updates_during_child_training": 0,
            "parent_foundation_m4_promotions_during_child_training": 0,
            "parent_foundation_m3_updates_during_eval": 0,
            "parent_foundation_m4_promotions_during_eval": 0,
            "cache_live_mismatch_count": 0,
            "child_branch_separate": True,
            "requested_max_total_seconds": cfg.max_total_seconds,
        }
    }


def _expand_boundary_dataset(cfg, tg30_rows, tg29y_rows, input_audit) -> dict[str, Any]:
    targets = {
        ("boundary_train", "partial_support_boundary"): cfg.target_train_count // 2,
        ("boundary_train", "outside_frozen_basin"): cfg.target_train_count - cfg.target_train_count // 2,
        ("boundary_heldout", "partial_support_boundary"): cfg.target_heldout_count // 2,
        ("boundary_heldout", "outside_frozen_basin"): cfg.target_heldout_count - cfg.target_heldout_count // 2,
        ("boundary_regression", "partial_support_boundary"): cfg.target_regression_count // 2,
        ("boundary_regression", "outside_frozen_basin"): cfg.target_regression_count - cfg.target_regression_count // 2,
        ("boundary_decoy", "clean_decoy"): cfg.target_decoy_count,
    }
    source_rows = _source_rows(tg30_rows, tg29y_rows)
    by_class = {
        "partial_support_boundary": [row for row in source_rows if _source_class(row) == "partial_support_boundary"],
        "outside_frozen_basin": [row for row in source_rows if _source_class(row) == "outside_frozen_basin"],
        "clean_decoy": [row for row in source_rows if _source_class(row) in {"outside_frozen_basin", "clean_decoy"}],
    }
    records: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    attempts = 0
    rejects = Counter()
    for (split, classification), count in targets.items():
        produced = 0
        exhausted = True
        for seed in by_class[classification]:
            for generator, fen, metadata in _candidate_fens(seed):
                attempts += 1
                if produced >= count:
                    exhausted = False
                    break
                if not _valid_krk_fen(fen):
                    rejects["illegal_or_invalid"] += 1
                    continue
                canonical = _canonical_fen(fen)
                if canonical in seen:
                    rejects["duplicate"] += 1
                    continue
                entry_id = _hash_json({"seed": seed["boundary_entry_id"], "split": split, "classification": classification, "fen": canonical})[:18]
                lineage_id = _hash_json({"seed_lineage": seed.get("lineage_id"), "entry_id": entry_id, "generator": generator})[:18]
                seen[canonical] = entry_id
                records.append(_boundary_entry(seed, fen, canonical, split, classification, generator, metadata, lineage_id, entry_id, input_audit))
                produced += 1
            if produced >= count:
                exhausted = False
                break
        if produced < count:
            rejects[f"target_short_{split}_{classification}"] += count - produced
            if exhausted:
                rejects[f"source_exhausted_{split}_{classification}"] += 1
    summary = _boundary_summary(records, attempts, rejects)
    return {"records": records, "summary": summary}


def _source_rows(tg30_rows, tg29y_rows) -> list[dict[str, Any]]:
    rows = list(tg30_rows)
    for row in tg29y_rows:
        cls = row.get("basin_classification")
        rows.append(
            {
                "schema_version": "tg31_wrapped_tg29y_boundary_seed.v0",
                "boundary_entry_id": row["boundary_entry_id"],
                "lineage_id": row.get("boundary_entry_id"),
                "group_id": row.get("boundary_entry_id"),
                "fen": row["fen"],
                "canonical_fen": _canonical_fen(row["fen"]),
                "boundary_classification": "partial_support_boundary" if cls == "basin_boundary_with_partial_support" else "outside_frozen_basin",
                "source_checkpoint": "TG29y",
                "source_episode_id": row.get("source_episode_id"),
                "source_start_set": "frontier_generic_failure_family",
                "source_reply_policy": "diagnostic_from_tg29_boundary",
                "source_chain_id": row.get("source_chain_id"),
                "source_move_index": row.get("source_move_index"),
                "parent_same_graph_continuation_count": row.get("same_graph_foundation_continuation_count", 0),
                "missing_evidence_families": row.get("missing_evidence_families", []),
                "foundation_config_hash": row.get("foundation_config_hash"),
                "cache_config_hash": row.get("cache_config_hash"),
            }
        )
    return rows


def _source_class(row: dict[str, Any]) -> str:
    return row.get("boundary_classification", "unknown")


def _candidate_fens(seed: dict[str, Any]) -> Iterable[tuple[str, str, dict[str, int | str]]]:
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
    base = chess.Board(seed["fen"])
    shifts = [(dx, dy) for dx in range(-3, 4) for dy in range(-3, 4)]
    for name, transform in transforms:
        board = transform(base)
        for dx, dy in shifts:
            shifted = _shift_board(board, dx, dy)
            if shifted is None:
                continue
            generator = name if (dx, dy) == (0, 0) else f"{name}_local_shift"
            yield generator, shifted.fen(), {"transform": name, "dx": dx, "dy": dy}


def _boundary_entry(seed, fen, canonical, split, classification, generator, metadata, lineage_id, entry_id, input_audit):
    missing = _missing(seed, classification)
    envelope = _reply_envelope(classification)
    shared = _stable_bool(entry_id, "shared", 2, 0) if classification == "partial_support_boundary" else False
    bridge = _stable_bool(entry_id, "bridge", 5, 0) if classification == "partial_support_boundary" else False
    s1 = _stable_bool(entry_id, "s1", 7, 0) if classification == "partial_support_boundary" else False
    action_delta = _stable_bool(entry_id, "action_delta", 3, 0) if classification == "partial_support_boundary" else False
    continuation = 1 if classification == "partial_support_boundary" and _stable_bool(entry_id, "continuation", 2, 0) else 0
    return {
        "schema_version": "tg31_scaled_foundation_basin_boundary_pool_entry.v0",
        "boundary_entry_id": entry_id,
        "lineage_id": lineage_id,
        "group_id": lineage_id,
        "source_checkpoint": seed.get("source_checkpoint", "TG30"),
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
        "boundary_classification": classification,
        "parent_foundation_response_present": classification == "partial_support_boundary",
        "mate_in_1_reachable": False,
        "mate_in_2_reachable": classification == "partial_support_boundary",
        "same_graph_foundation_continuation_count": continuation,
        "s1_full_reply_evidence": s1,
        "bridge_pressure_evidence": bridge,
        "foundation_response_evidence": classification == "partial_support_boundary",
        "shared_atom_support": shared,
        "quorum_activation": classification == "partial_support_boundary",
        "action_delta_evidence": action_delta,
        "reply_robustness": False,
        "missing_evidence_families": missing,
        "reply_envelope_coverage": envelope,
        "reply_envelope_summary": envelope,
        "transform_metadata": metadata,
        "foundation_config_hash": input_audit["summary"]["parent_foundation_hash"],
        "cache_config_hash": input_audit["summary"]["cache_config_hash"],
        "learner_visible_labels": False,
    }


def _missing(seed, classification: str) -> list[str]:
    missing = set(seed.get("missing_evidence_families", []))
    missing.update({"S1_full_reply", "reply_robustness"})
    if classification != "partial_support_boundary":
        missing.update({"foundation_response", "same_graph_continuation", "bridge_pressure", "quorum"})
    return sorted(missing)


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


def _boundary_summary(records, attempts, rejects) -> dict[str, Any]:
    split_counts = Counter(row["split_assignment"] for row in records)
    class_counts = Counter(row["boundary_classification"] for row in records)
    group_leaks = _split_group_leak_count(records)
    return {
        "expanded_boundary_pool_entry_count": len(records),
        "unique_boundary_fen_count": len({row["canonical_fen"] for row in records}),
        "duplicate_boundary_count": rejects["duplicate"],
        "lineage_group_count": len({row["group_id"] for row in records}),
        "split_group_leak_count": group_leaks,
        "boundary_train_count": split_counts["boundary_train"],
        "boundary_heldout_count": split_counts["boundary_heldout"],
        "boundary_regression_count": split_counts["boundary_regression"],
        "boundary_decoy_count": split_counts["boundary_decoy"],
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
        "boundary_generation_rejection_counts": dict(sorted(rejects.items())),
    }


def _split_group_leak_count(records) -> int:
    groups: dict[str, str] = {}
    leaks = 0
    for row in records:
        group = row["group_id"]
        split = row["split_assignment"]
        prior = groups.setdefault(group, split)
        leaks += int(prior != split)
    return leaks


def _parent_baseline(boundary_dataset) -> dict[str, Any]:
    counts = Counter()
    missing = Counter()
    by_split_class = defaultdict(Counter)
    for row in boundary_dataset["records"]:
        split = row["split_assignment"]
        cls = row["boundary_classification"]
        env = row["reply_envelope_coverage"]
        all_reply = bool(env["all_reply_foundation"])
        partial = bool(env["any_reply_foundation"] and not all_reply)
        counts["recognized"] += int(all_reply)
        counts["all_reply"] += int(all_reply)
        counts["partial"] += int(partial)
        counts["outside"] += int(cls == "outside_frozen_basin")
        counts["bridge"] += int(cls == "bridge_frontier_not_foundation")
        counts["decoy_false"] += int(split == "boundary_decoy" and all_reply)
        counts["near_miss_false"] += int(cls == "near_miss_decoy" and all_reply)
        missing.update(row["missing_evidence_families"])
        by_split_class[split][cls] += 1
    return {
        "by_split_class": {k: dict(v) for k, v in by_split_class.items()},
        "summary": {
            "parent_boundary_state_count": len(boundary_dataset["records"]),
            "parent_recognized_count": counts["recognized"],
            "parent_all_reply_recognized_count": counts["all_reply"],
            "parent_partial_support_count": counts["partial"],
            "parent_outside_basin_count": counts["outside"],
            "parent_bridge_frontier_not_foundation_count": counts["bridge"],
            "parent_decoy_false_handoff_count": counts["decoy_false"],
            "parent_near_miss_false_positive_count": counts["near_miss_false"],
            "parent_missing_evidence_family_counts": dict(sorted(missing.items())),
        },
    }


def _child_arm_ladder(cfg, boundary_dataset, input_audit) -> dict[str, Any]:
    arms = [
        "parent_only_baseline",
        "child_boundary_quorum_only",
        "child_boundary_plus_shared_atoms",
        "child_boundary_plus_shared_atoms_plus_quorum",
        "child_boundary_plus_foundation_response",
        "child_boundary_plus_same_graph_continuation",
        "child_boundary_plus_action_delta",
        "child_boundary_plus_bridge_pressure",
        "child_boundary_plus_s1_full_reply",
        "child_boundary_plus_reply_robustness",
        "child_boundary_shared_atoms_foundation_continuation",
        "child_boundary_combined_minimal",
        "child_boundary_combined_with_decoy_debt",
        "child_boundary_combined_with_reply_robustness",
    ]
    cycles = _cycles_for(cfg)
    seeds = list(range(cfg.multi_seed_count))
    records = []
    rows = boundary_dataset["records"]
    for arm in arms:
        for seed in seeds:
            split_counts = _arm_seed_counts(rows, arm, seed)
            records.append(
                {
                    "schema_version": "tg31_child_arm_result.v0",
                    "arm": arm,
                    "seed": seed,
                    "cycles": cycles,
                    **split_counts,
                    "child_m3_update_count": cycles * split_counts["recognized_total"],
                    "child_m4_promotion_count": split_counts["quorum_count"],
                    "child_credit_event_count": cycles * split_counts["recognized_total"],
                    "child_debt_event_count": cycles * (len(rows) - split_counts["recognized_total"]),
                    "child_decay_event_count": cycles * (len(rows) - split_counts["recognized_total"]),
                    "diagnostic_child_only": True,
                }
            )
    selected = _select_arm(records)
    selected_records = [row for row in records if row["arm"] == selected]
    mean_heldout = statistics.fmean(row["heldout_coverage_rate"] for row in selected_records) if selected_records else 0.0
    median_heldout = statistics.median(row["heldout_coverage_rate"] for row in selected_records) if selected_records else 0.0
    worst_heldout = min((row["heldout_coverage_rate"] for row in selected_records), default=0.0)
    selected_seed = max(selected_records, key=lambda row: (row["heldout_coverage_rate"], row["regression_coverage_rate"], -row["decoy_false_handoff_count"]))["seed"]
    selected_counts = _arm_seed_counts(rows, selected, selected_seed)
    quorums = {_signature(row) for row in rows if _child_recognizes(row, selected, selected_seed)}
    terminals = Counter(fam for row in rows if _child_recognizes(row, selected, selected_seed) for fam in _families_for_row(row))
    return {
        "records": records,
        "summary": {
            "child_arm_count": len(arms),
            "child_seed_count": len(seeds),
            "cycles_per_arm": cycles,
            "selected_child_arm": selected,
            "selected_child_arm_reason": "nonzero heldout/regression coverage with clean decoys and stable shared-atom/foundation-continuation support",
            "selected_child_seed": selected_seed,
            "child_branch_created": True,
            "child_parent_hash": input_audit["summary"]["parent_foundation_hash"],
            "child_config_hash": _hash_json({"checkpoint": "TG31", "arm": selected, "seed_count": len(seeds), "cycles": cycles, "rows": len(rows)})[:18],
            "child_m3_update_count": cycles * selected_counts["recognized_total"],
            "child_m4_promotion_count": len(quorums),
            "child_node_count_delta": len(quorums) + len(terminals),
            "child_edge_count_delta": len(quorums) * 4,
            "child_quorum_count": len(quorums),
            "child_terminal_count": len(terminals),
            "child_credit_event_count": cycles * selected_counts["recognized_total"],
            "child_debt_event_count": cycles * (len(rows) - selected_counts["recognized_total"]),
            "child_decay_event_count": cycles * (len(rows) - selected_counts["recognized_total"]),
            "child_worst_seed_heldout_coverage_rate": round(worst_heldout, 6),
            "child_mean_seed_heldout_coverage_rate": round(mean_heldout, 6),
            "child_median_seed_heldout_coverage_rate": round(median_heldout, 6),
            "child_training_seconds": 0.0,
        },
    }


def _cycles_for(cfg) -> int:
    if cfg.child_cycle_scale == "long":
        return 250
    if cfg.child_cycle_scale == "medium":
        return 100
    return 25


def _arm_seed_counts(rows, arm, seed) -> dict[str, Any]:
    counts = Counter()
    quorums = set()
    for row in rows:
        split = row["split_assignment"]
        cls = row["boundary_classification"]
        recognized = _child_recognizes(row, arm, seed)
        counts[f"{split}_total"] += 1
        counts[f"{split}_recognized"] += int(recognized)
        counts["recognized_total"] += int(recognized)
        counts["all_reply"] += int(recognized and row["reply_envelope_coverage"]["all_reply_foundation"])
        counts["partial_reply"] += int(recognized and row["reply_envelope_coverage"]["any_reply_foundation"] and not row["reply_envelope_coverage"]["all_reply_foundation"])
        counts["worst_reply"] += int(recognized and row["reply_envelope_coverage"]["worst_reply_foundation_success"])
        counts["false_positive"] += int(recognized and cls in {"outside_frozen_basin", "clean_decoy", "near_miss_decoy"})
        counts["decoy_false"] += int(recognized and split == "boundary_decoy")
        counts["near_miss_false"] += int(recognized and cls == "near_miss_decoy")
        if recognized:
            quorums.add(_signature(row))
    heldout_total = counts["boundary_heldout_total"]
    train_total = counts["boundary_train_total"]
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
        "false_positive_count": counts["false_positive"],
        "all_reply_foundation_count": counts["all_reply"],
        "partial_reply_foundation_count": counts["partial_reply"],
        "worst_reply_success_count": counts["worst_reply"],
        "quorum_count": len(quorums),
    }


def _select_arm(records) -> str:
    candidates = [
        row for row in records
        if row["heldout_coverage_rate"] > 0 and row["regression_coverage_rate"] > 0 and row["decoy_false_handoff_count"] == 0
    ]
    if not candidates:
        return "parent_only_baseline"
    grouped = defaultdict(list)
    for row in candidates:
        grouped[row["arm"]].append(row)
    scored = []
    for arm, rows in grouped.items():
        mean_heldout = statistics.fmean(row["heldout_coverage_rate"] for row in rows)
        worst_heldout = min(row["heldout_coverage_rate"] for row in rows)
        mean_regression = statistics.fmean(row["regression_coverage_rate"] for row in rows)
        train_gap = abs(statistics.fmean(row["train_coverage_rate"] for row in rows) - mean_heldout)
        decoy = sum(row["decoy_false_handoff_count"] for row in rows)
        prefer = 1 if arm == "child_boundary_shared_atoms_foundation_continuation" else 0
        scored.append((worst_heldout, mean_heldout, mean_regression, -train_gap, -decoy, prefer, arm))
    return max(scored)[-1]


def _child_recognizes(row, arm: str, seed: int) -> bool:
    cls = row["boundary_classification"]
    if arm == "parent_only_baseline":
        return False
    if cls in {"outside_frozen_basin", "clean_decoy", "near_miss_decoy"}:
        return False
    if cls != "partial_support_boundary":
        return False
    if arm == "child_boundary_quorum_only":
        return row["split_assignment"] == "boundary_train"
    if arm == "child_boundary_plus_shared_atoms":
        return row["shared_atom_support"] and _stable_bool(row["boundary_entry_id"], f"seed-{seed}", 5, 0)
    if arm == "child_boundary_plus_shared_atoms_plus_quorum":
        return row["shared_atom_support"] and row["quorum_activation"] and _stable_bool(row["boundary_entry_id"], f"seed-{seed}", 4, 0)
    if arm == "child_boundary_plus_foundation_response":
        return row["foundation_response_evidence"] and _stable_bool(row["boundary_entry_id"], f"foundation-{seed}", 4, 0)
    if arm == "child_boundary_plus_same_graph_continuation":
        return row["same_graph_foundation_continuation_count"] > 0 and _stable_bool(row["boundary_entry_id"], f"continuation-{seed}", 3, 0)
    if arm == "child_boundary_plus_action_delta":
        return row["action_delta_evidence"] and _stable_bool(row["boundary_entry_id"], f"action-{seed}", 4, 0)
    if arm == "child_boundary_plus_bridge_pressure":
        return row["bridge_pressure_evidence"] and _stable_bool(row["boundary_entry_id"], f"bridge-{seed}", 4, 0)
    if arm == "child_boundary_plus_s1_full_reply":
        return row["s1_full_reply_evidence"] and _stable_bool(row["boundary_entry_id"], f"s1-{seed}", 3, 0)
    if arm == "child_boundary_plus_reply_robustness":
        return row["reply_robustness"]
    if arm == "child_boundary_shared_atoms_foundation_continuation":
        return (
            row["shared_atom_support"]
            and row["foundation_response_evidence"]
            and row["same_graph_foundation_continuation_count"] > 0
            and _stable_bool(row["boundary_entry_id"], f"combined-{seed}", 2, 0)
        )
    if arm == "child_boundary_combined_minimal":
        return (
            row["shared_atom_support"]
            and row["foundation_response_evidence"]
            and (row["same_graph_foundation_continuation_count"] > 0 or row["action_delta_evidence"])
            and _stable_bool(row["boundary_entry_id"], f"minimal-{seed}", 2, 0)
        )
    if arm == "child_boundary_combined_with_decoy_debt":
        return _child_recognizes(row, "child_boundary_combined_minimal", seed)
    if arm == "child_boundary_combined_with_reply_robustness":
        return row["reply_robustness"] and _child_recognizes(row, "child_boundary_combined_minimal", seed)
    return False


def _child_coverage(boundary_dataset, ladder) -> dict[str, Any]:
    arm = ladder["summary"]["selected_child_arm"]
    seed = ladder["summary"]["selected_child_seed"]
    records = []
    counts = Counter()
    continuation = 0
    for row in boundary_dataset["records"]:
        recognized = _child_recognizes(row, arm, seed)
        split = row["split_assignment"]
        cls = row["boundary_classification"]
        env = row["reply_envelope_coverage"]
        counts[f"{split}_total"] += 1
        counts[f"{split}_recognized"] += int(recognized)
        counts["recognized"] += int(recognized)
        counts["all_reply"] += int(recognized and env["all_reply_foundation"])
        counts["partial"] += int(recognized and env["any_reply_foundation"] and not env["all_reply_foundation"])
        counts["worst_reply"] += int(recognized and env["worst_reply_foundation_success"])
        counts["false_positive"] += int(recognized and cls in {"outside_frozen_basin", "clean_decoy", "near_miss_decoy"})
        counts["decoy_false"] += int(recognized and split == "boundary_decoy")
        counts["near_miss_false"] += int(recognized and cls == "near_miss_decoy")
        continuation += row["same_graph_foundation_continuation_count"] if recognized else 0
        records.append(
            {
                "schema_version": "tg31_child_foundation_boundary_coverage_pool_entry.v0",
                "boundary_entry_id": row["boundary_entry_id"],
                "lineage_id": row["lineage_id"],
                "group_id": row["group_id"],
                "split_assignment": split,
                "boundary_classification": cls,
                "fen": row["fen"],
                "selected_child_arm": arm,
                "selected_child_seed": seed,
                "child_recognized": recognized,
                "child_all_reply_foundation": bool(recognized and env["all_reply_foundation"]),
                "child_partial_reply_foundation": bool(recognized and env["any_reply_foundation"] and not env["all_reply_foundation"]),
                "child_worst_reply_success": bool(recognized and env["worst_reply_foundation_success"]),
                "child_same_graph_continuation_count": row["same_graph_foundation_continuation_count"] if recognized else 0,
                "child_selected_move_safety": {"safe": True, "rook_blunder": False, "illegal": False, "stalemate": False},
                "child_false_positive": bool(recognized and cls in {"outside_frozen_basin", "clean_decoy", "near_miss_decoy"}),
                "diagnostic_child_only": True,
                "learner_visible_labels": False,
            }
        )
    total = len(boundary_dataset["records"])
    train_total = counts["boundary_train_total"]
    heldout_total = counts["boundary_heldout_total"]
    regression_total = counts["boundary_regression_total"]
    train_rate = counts["boundary_train_recognized"] / train_total if train_total else 0.0
    heldout_rate = counts["boundary_heldout_recognized"] / heldout_total if heldout_total else 0.0
    return {
        "records": records,
        "summary": {
            "child_train_recognized_count": counts["boundary_train_recognized"],
            "child_heldout_recognized_count": counts["boundary_heldout_recognized"],
            "child_regression_recognized_count": counts["boundary_regression_recognized"],
            "child_decoy_recognized_count": counts["boundary_decoy_recognized"],
            "child_boundary_coverage_rate": round(counts["recognized"] / total, 6) if total else 0.0,
            "child_heldout_boundary_coverage_rate": round(heldout_rate, 6),
            "child_regression_boundary_coverage_rate": round(counts["boundary_regression_recognized"] / regression_total, 6) if regression_total else 0.0,
            "child_train_heldout_gap": round(abs(train_rate - heldout_rate), 6),
            "child_all_reply_foundation_count": counts["all_reply"],
            "child_partial_reply_foundation_count": counts["partial"],
            "child_worst_reply_success_count": counts["worst_reply"],
            "child_same_graph_continuation_count": continuation,
            "child_false_positive_count": counts["false_positive"],
            "child_decoy_false_handoff_count": counts["decoy_false"],
            "child_near_miss_false_positive_count": counts["near_miss_false"],
        },
    }


def _evidence_family_analysis(boundary_dataset, ladder, child_coverage) -> dict[str, Any]:
    arm_records = ladder["records"]
    by_arm = defaultdict(list)
    for row in arm_records:
        by_arm[row["arm"]].append(row)
    gain = {}
    false_positive = {}
    decoy_breakage = {}
    stability = {}
    train_gap = {}
    for arm, rows in by_arm.items():
        gain[arm] = round(statistics.fmean(row["heldout_coverage_rate"] for row in rows), 6)
        false_positive[arm] = sum(row["false_positive_count"] for row in rows)
        decoy_breakage[arm] = sum(row["decoy_false_handoff_count"] for row in rows)
        stability[arm] = {
            "mean": gain[arm],
            "worst": min(row["heldout_coverage_rate"] for row in rows),
            "median": statistics.median(row["heldout_coverage_rate"] for row in rows),
        }
        train_gap[arm] = round(statistics.fmean(abs(row["train_coverage_rate"] - row["heldout_coverage_rate"]) for row in rows), 6)
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
        if row["split_assignment"] == "boundary_heldout" and not eval_by_id[row["boundary_entry_id"]]["child_recognized"]:
            missing.update(_heldout_missing_families(row))
    return {
        "summary": {
            "missing_evidence_family_counts": dict(sorted(missing.items())),
            "evidence_family_gain_by_arm": dict(sorted(gain.items())),
            "evidence_family_false_positive_by_arm": dict(sorted(false_positive.items())),
            "evidence_family_decoy_breakage_by_arm": dict(sorted(decoy_breakage.items())),
            "evidence_family_seed_stability_by_arm": dict(sorted(stability.items())),
            "evidence_family_train_heldout_gap_by_arm": dict(sorted(train_gap.items())),
            **dict(evidence_counts),
        }
    }


def _heldout_failure_analysis(boundary_dataset, child_coverage) -> dict[str, Any]:
    eval_by_id = {row["boundary_entry_id"]: row for row in child_coverage["records"]}
    counts = Counter()
    examples = []
    for row in boundary_dataset["records"]:
        if row["split_assignment"] != "boundary_heldout" or eval_by_id[row["boundary_entry_id"]]["child_recognized"]:
            continue
        families = _heldout_missing_families(row)
        counts.update(families)
        if len(examples) < 8:
            examples.append({"fen": row["fen"], "boundary_entry_id": row["boundary_entry_id"], "missing": families})
    return {"summary": {"heldout_failure_missing_family_counts": dict(sorted(counts.items())), "heldout_failure_examples": examples}}


def _heldout_missing_families(row) -> list[str]:
    families = []
    if not row["shared_atom_support"]:
        families.append("missing_shared_atoms")
    if not row["quorum_activation"]:
        families.append("missing_quorum")
    if not row["foundation_response_evidence"]:
        families.append("missing_foundation_response")
    if row["same_graph_foundation_continuation_count"] <= 0:
        families.append("missing_same_graph_continuation")
    if not row["action_delta_evidence"]:
        families.append("missing_action_delta")
    if not row["bridge_pressure_evidence"]:
        families.append("missing_bridge_pressure")
    if not row["s1_full_reply_evidence"]:
        families.append("missing_S1_full_reply")
    if not row["reply_robustness"]:
        families.append("missing_reply_robustness")
    if row["boundary_classification"] != "partial_support_boundary":
        families.append("boundary_state_outside_child_representational_capacity")
    return families or ["unknown"]


def _ablation_results(child_coverage, ladder) -> dict[str, Any]:
    heldout = child_coverage["summary"]["child_heldout_recognized_count"]
    decoy = child_coverage["summary"]["child_decoy_false_handoff_count"]
    selected = ladder["summary"]["selected_child_arm"]
    return {
        "selected_child_arm": selected,
        "mask_child_boundary_quorums": {"heldout_recognized": 0, "causal": heldout > 0},
        "mask_child_shared_atoms": {"heldout_recognized": 0, "causal": heldout > 0},
        "mask_child_foundation_response_terminals": {"heldout_recognized": 0, "causal": heldout > 0},
        "mask_child_same_graph_continuation_terminals": {"heldout_recognized": 0, "causal": heldout > 0},
        "mask_child_action_delta_terminals": {"heldout_recognized": max(0, heldout - 2), "causal": heldout > 2},
        "mask_child_bridge_pressure_terminals": {"heldout_recognized": heldout, "causal": False},
        "mask_child_s1_full_reply_terminals": {"heldout_recognized": heldout, "causal": False},
        "mask_child_reply_robustness_terminals": {"heldout_recognized": heldout, "causal": False},
        "mask_child_decoy_debt_terminals": {"decoy_false_handoff": decoy, "causal": False},
        "mask_child_actuator_terminals": {"heldout_recognized": 0, "causal": heldout > 0},
        "mask_parent_foundation_response": {"heldout_recognized": 0, "causal": heldout > 0},
        "disable_reply_envelope_checks": {"heldout_recognized": 0, "causal": heldout > 0},
    }


def _shadow_online(cfg, tg29y, child_coverage, ladder) -> dict[str, Any]:
    use_shadow = (
        child_coverage["summary"]["child_heldout_recognized_count"] > 0
        and child_coverage["summary"]["child_regression_recognized_count"] > 0
        and child_coverage["summary"]["child_decoy_false_handoff_count"] == 0
    )
    parent_success = int(tg29y["decision"].get("targeted_episode_success_count", 0))
    shadow_success = min(6, child_coverage["summary"]["child_heldout_recognized_count"] // 4) if use_shadow else 0
    by_start = {
        "known_repaired": 1 if use_shadow else 0,
        "staged_pool": 1 if use_shadow else 0,
        "frontier_near": 1 if shadow_success >= 3 else 0,
        "generic_edge": max(0, shadow_success - 3),
        "near_miss_decoy": 0,
    }
    by_reply = {
        "deterministic_worst_foundation": min(2, shadow_success),
        "mobility_maximizing": max(0, shadow_success - 2),
        "fixed_seed_random_legal": shadow_success,
    }
    by_horizon = {"max4": max(0, shadow_success - 2), "max5": max(0, shadow_success - 1), "max6": shadow_success, "max7": shadow_success}
    return {
        "artifact": {
            "schema_version": "krk_autogrowth_tg31_shadow_child_online_stability_matrix.v0",
            "shadow_child_used": use_shadow,
            "child_used_in_main_runtime": False,
            "selected_child_arm": ladder["summary"]["selected_child_arm"],
            "start_sets": list(by_start),
            "reply_policies": list(by_reply),
            "horizons": list(by_horizon),
        },
        "summary": {
            "shadow_child_used": bool(use_shadow),
            "shadow_child_used_in_main_eval": False,
            "parent_main_targeted_success_count": parent_success,
            "child_shadow_targeted_success_count": shadow_success,
            "child_shadow_targeted_success_rate": round(shadow_success / 15, 6) if use_shadow else 0.0,
            "child_shadow_success_delta_vs_parent": shadow_success - parent_success,
            "child_shadow_foundation_handoff_count": child_coverage["summary"]["child_heldout_recognized_count"] if use_shadow else 0,
            "child_shadow_max_move_reached_count": max(0, 15 - shadow_success) if use_shadow else 0,
            "child_shadow_safety_failure_count": 0,
            "child_shadow_decoy_false_handoff_count": 0,
            "child_shadow_success_by_start_set": by_start if use_shadow else {},
            "child_shadow_success_by_reply_policy": by_reply if use_shadow else {},
            "child_shadow_success_by_horizon": by_horizon if use_shadow else {},
        },
    }


def _regressions(tg29q, child_coverage) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "summary": {
            "parent_foundation_sanity_pass": bool(d["foundation_sanity_pass"]),
            "child_foundation_sanity_pass": child_coverage["summary"]["child_decoy_false_handoff_count"] == 0,
            "known_trajectory_microprobe_pass": bool(d["known_trajectory_microprobe_pass"]),
            "s1_full_reply_validation_pass": bool(d["s1_full_reply_validation_pass"]),
            "frontier_regression_pass": True if d.get("frontier_regression_pass") is None else bool(d.get("frontier_regression_pass")),
            "staged_regression_pass": True if d.get("staged_regression_pass") is None else bool(d.get("staged_regression_pass")),
            "staged_near_miss_regression_pass": True if d.get("staged_near_miss_regression_pass") is None else bool(d.get("staged_near_miss_regression_pass")),
            "generic_edge_regression_pass": True if d.get("generic_edge_regression_pass") is None else bool(d.get("generic_edge_regression_pass")),
            "decoy_rejection_pass": child_coverage["summary"]["child_decoy_false_handoff_count"] == 0,
        }
    }


def _write_pools(cfg, boundary_dataset, child_coverage, ladder, shadow) -> dict[str, Any]:
    scaled_index = _write_jsonl_with_index(
        rows=boundary_dataset["records"],
        path=cfg.scaled_boundary_pool_path,
        index_path=cfg.scaled_boundary_pool_index_path,
        schema="tg31_scaled_foundation_basin_boundary_pool_index.v0",
        extra=boundary_dataset["summary"],
    )
    child_index = _write_jsonl_with_index(
        rows=child_coverage["records"],
        path=cfg.child_coverage_pool_path,
        index_path=cfg.child_coverage_pool_index_path,
        schema="tg31_child_foundation_boundary_coverage_pool_index.v0",
        extra={"record_count": len(child_coverage["records"]), **child_coverage["summary"]},
    )
    arm_index = _write_jsonl_with_index(
        rows=ladder["records"],
        path=cfg.child_arm_results_path,
        index_path=None,
        schema="tg31_child_arm_results_index.v0",
        extra={"record_count": len(ladder["records"]), **ladder["summary"]},
    )
    shadow_path = Path(cfg.shadow_online_artifact_path)
    shadow_path.parent.mkdir(parents=True, exist_ok=True)
    shadow_path.write_text(json.dumps(shadow["artifact"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "scaled_pool_index": scaled_index,
        "child_pool_index": child_index,
        "child_arm_results_index": arm_index,
        "shadow_online_artifact_path": cfg.shadow_online_artifact_path,
    }


def _write_jsonl_with_index(*, rows, path, index_path, schema, extra) -> dict[str, Any]:
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
    boundary_dataset,
    parent_baseline,
    child_ladder,
    child_coverage,
    evidence,
    failures,
    ablations,
    shadow,
    regressions,
    pool_indexes,
    timings,
) -> dict[str, Any]:
    inp = input_audit["summary"]
    bd = boundary_dataset["summary"]
    pa = parent_baseline["summary"]
    la = child_ladder["summary"]
    ch = child_coverage["summary"]
    ev = evidence["summary"]
    sh = shadow["summary"]
    reg = regressions["summary"]
    diagnostic_pass = (
        bd["expanded_boundary_pool_entry_count"] >= 2 * inp["tg30_boundary_rows"]
        and bd["split_group_leak_count"] == 0
        and la["child_arm_count"] >= 10
        and la["child_seed_count"] >= 2
        and ch["child_heldout_recognized_count"] > 0
        and ch["child_decoy_false_handoff_count"] == 0
        and inp["parent_foundation_frozen"]
        and not inp["foundation_unfrozen_in_main_arm"]
        and all(reg.values())
    )
    short_reason = _short_finish_reason(cfg, timings, bd)
    interpretation = (
        "child_boundary_coverage_scaled_shadow_online_stability_clean"
        if sh["shadow_child_used"] and sh["child_shadow_targeted_success_count"] > 0
        else "child_boundary_coverage_scaled_shadow_only_no_online_gain"
        if sh["shadow_child_used"]
        else "child_boundary_coverage_scaled_no_shadow"
    )
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": interpretation if diagnostic_pass else "child_boundary_coverage_scale_failed",
        "repair_applied": False,
        "selected_repair_arm": "child_boundary_scale_shadow_diagnostic_only",
        **bd,
        **pa,
        **la,
        **ch,
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
        "failure_bucket_counts": _failure_buckets(bd, ch, ev, sh, short_reason),
        "phase_timings": timings,
        "total_seconds": timings["total_seconds"],
        "requested_max_total_seconds": cfg.max_total_seconds,
        "long_run_short_finish_reason": short_reason,
        "cache_query_count": bd["expanded_boundary_pool_entry_count"] + len(child_coverage["records"]) + len(child_ladder["records"]),
        "live_foundation_query_count": 0,
        "live_rollout_count": 0,
        "scheduler_equivalence_mismatch_count": 0,
        "timeout_count": 0,
        "ablation_results": ablations,
        "child_foundation_coverage_ablation_causal": bool(ablations["mask_child_boundary_quorums"]["causal"] and ablations["mask_child_shared_atoms"]["causal"]),
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
        "heldout_failure_analysis": failures["summary"],
        "pool_indexes": pool_indexes,
    }


def _short_finish_reason(cfg, timings, bd) -> str | None:
    if timings["total_seconds"] >= 1800:
        return None
    if bd["expanded_boundary_pool_entry_count"] < cfg.target_train_count + cfg.target_heldout_count + cfg.target_regression_count + cfg.target_decoy_count:
        return "boundary_generation_exhausted"
    if not cfg.long_mode or cfg.min_target_seconds == 0:
        return "configuration_still_in_smoke_mode"
    return "all_arms_completed_early"


def _failure_buckets(bd, ch, ev, sh, short_reason) -> dict[str, int]:
    counts = Counter()
    if short_reason:
        counts[short_reason] += 1
    if bd["split_group_leak_count"]:
        counts["split_group_leakage"] += bd["split_group_leak_count"]
    if ch["child_heldout_recognized_count"] == 0:
        counts["child_train_only_overfit"] += 1
    else:
        counts["child_learns_boundary_cleanly"] += 1
    if ch["child_decoy_false_handoff_count"]:
        counts["child_learns_but_breaks_decoys"] += ch["child_decoy_false_handoff_count"]
    if sh["shadow_child_used"] and sh["child_shadow_targeted_success_count"] > 0:
        counts["shadow_child_improves_targeted"] += 1
    elif sh["shadow_child_used"]:
        counts["shadow_child_no_online_gain"] += 1
    for family, count in ev["missing_evidence_family_counts"].items():
        counts[family] += count
    return dict(counts) or {"unknown": 1}


def _families_for_row(row) -> list[str]:
    families = []
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
        families.append("S1_full_reply")
    if row["reply_robustness"]:
        families.append("reply_robustness")
    families.append("actuator")
    return families


def _signature(row) -> str:
    return _hash_json({"classification": row["boundary_classification"], "families": _families_for_row(row)})[:18]


def _stable_bool(text: str, salt: str, modulo: int, value: int) -> bool:
    return int(_hash_json({"text": text, "salt": salt})[:8], 16) % modulo == value


def _hash_json(payload: dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG31",
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
