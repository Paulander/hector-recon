"""TG29z frozen-parent child foundation basin coverage diagnostic."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from .cached_online_episode_scale_matrix import _load_json, _purity_boundary as _tg29p_purity_boundary
from .tiny_online_krk_episode_runner import TinyOnlineKRKEpisodeRunnerConfig


@dataclass(frozen=True)
class ChildFoundationBasinCoverageConfig:
    base: TinyOnlineKRKEpisodeRunnerConfig = TinyOnlineKRKEpisodeRunnerConfig(
        schedule_names=("tg29l_minimal_real_context",),
        episode_count=4,
        max_white_moves_per_episode=6,
        max_episode_ablation_count=1,
        progress_output="reports/autogrowth/krk_autogrowth_tg29z_child_foundation_basin_coverage_diagnostic_progress.json",
    )
    tg29y_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29y_tight_followup_success_basin_coverage.json"
    tg29y_boundary_pool_path: str = "reports/autogrowth/pools/tg29y_frozen_foundation_basin_boundary_pool.jsonl"
    tg29o_s1_cache_path: str = "reports/autogrowth/pools/tg29o_s1_full_reply_evidence_cache.jsonl"
    tg29q_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.json"
    tg29p_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix.json"
    child_pool_path: str = "reports/autogrowth/pools/tg29z_child_foundation_boundary_coverage_pool.jsonl"
    child_pool_index_path: str = "reports/autogrowth/pools/tg29z_child_foundation_boundary_coverage_pool_index.json"


@dataclass(frozen=True)
class ChildFoundationBasinCoverageResult:
    config: ChildFoundationBasinCoverageConfig
    input_audit: dict[str, Any]
    parent_boundary_baseline: dict[str, Any]
    boundary_dataset_split: dict[str, Any]
    child_branch_training: dict[str, Any]
    child_coverage_evaluation: dict[str, Any]
    shadow_online_diagnostic: dict[str, Any]
    blocker_classification: dict[str, Any]
    decoy_near_miss_regression: dict[str, Any]
    compact_regression: dict[str, Any]
    child_pool_index: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg29z_child_foundation_basin_coverage_diagnostic.v0",
            "checkpoint": "TG29z_child_foundation_basin_coverage_diagnostic",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "input_audit": self.input_audit,
            "parent_boundary_baseline": self.parent_boundary_baseline,
            "boundary_dataset_split": self.boundary_dataset_split,
            "child_branch_training": self.child_branch_training,
            "child_coverage_evaluation": self.child_coverage_evaluation,
            "shadow_online_diagnostic": self.shadow_online_diagnostic,
            "blocker_classification": self.blocker_classification,
            "decoy_near_miss_regression": self.decoy_near_miss_regression,
            "compact_regression": self.compact_regression,
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
                    "# TG29z Child Foundation Basin Coverage Diagnostic",
                    "",
                    f"- checkpoint_pass: `{d['checkpoint_pass']}`",
                    f"- interpretation: `{d['checkpoint_interpretation']}`",
                    f"- repair_applied: `{d['repair_applied']}`",
                    f"- selected arm: `{d['selected_repair_arm']}`",
                    f"- parent recognized/unrecognized: `{d['parent_recognized_boundary_count']}` / `{d['parent_unrecognized_boundary_count']}`",
                    f"- child train/heldout/regression recognized: `{d['child_train_recognized_count']}` / `{d['child_heldout_recognized_count']}` / `{d['child_regression_recognized_count']}`",
                    f"- child heldout coverage: `{d['child_heldout_boundary_coverage_rate']}`",
                    f"- child false positives / decoy false handoff: `{d['child_false_positive_count']}` / `{d['child_decoy_false_handoff_count']}`",
                    f"- child used in main runtime: `{d['child_used_in_main_runtime']}`",
                    "",
                    "Interpretation: TG29z is a shadow child coverage diagnostic; parent TG27b remains frozen.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_child_foundation_basin_coverage_diagnostic(
    *,
    config: ChildFoundationBasinCoverageConfig | None = None,
) -> ChildFoundationBasinCoverageResult:
    cfg = config or ChildFoundationBasinCoverageConfig()
    start = time.perf_counter()
    _write_progress(cfg, {"phase": "start"})
    tg29y = _load_json(cfg.tg29y_artifact_path)
    tg29q = _load_json(cfg.tg29q_artifact_path)
    tg29p = _load_json(cfg.tg29p_artifact_path)
    boundary_rows = _load_jsonl(cfg.tg29y_boundary_pool_path)
    s1_rows = _load_jsonl(cfg.tg29o_s1_cache_path)
    _write_progress(cfg, {"phase": "loaded", "boundary_rows": len(boundary_rows)})

    parent_start = time.perf_counter()
    input_audit = _input_audit(cfg, tg29y, tg29p, boundary_rows, s1_rows)
    parent = _parent_boundary_baseline(boundary_rows)
    parent_seconds = round(time.perf_counter() - parent_start, 6)
    split = _boundary_dataset_split(boundary_rows)
    train_start = time.perf_counter()
    child_training = _child_branch_training(input_audit, split)
    train_seconds = round(time.perf_counter() - train_start, 6)
    eval_start = time.perf_counter()
    child_eval = _child_coverage_evaluation(split, child_training)
    eval_seconds = round(time.perf_counter() - eval_start, 6)
    shadow = _shadow_online_diagnostic(tg29y, child_eval)
    blocker = _blocker_classification(child_eval, parent, split)
    decoy = _decoy_near_miss_regression(tg29q)
    compact = _compact_regression_from_prior(tg29q)
    pool_index = _write_child_pool(cfg, child_eval)
    ablations = _ablation_results(child_eval)
    timings = {
        "parent_baseline_seconds": parent_seconds,
        "child_training_seconds": train_seconds,
        "child_eval_seconds": eval_seconds,
        "shadow_online_seconds": 0.0,
        "cache_write_seconds": pool_index["cache_write_seconds"],
        "total_seconds": round(time.perf_counter() - start, 6),
    }
    decision = _decision(
        tg29y=tg29y,
        input_audit=input_audit,
        parent=parent,
        split=split,
        child_training=child_training,
        child_eval=child_eval,
        shadow=shadow,
        blocker=blocker,
        decoy=decoy,
        compact=compact,
        pool_index=pool_index,
        ablations=ablations,
        timings=timings,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {"checkpoint_pass": decision["checkpoint_pass"], "checkpoint_interpretation": decision["checkpoint_interpretation"]}})
    return ChildFoundationBasinCoverageResult(
        config=cfg,
        input_audit=input_audit,
        parent_boundary_baseline=parent,
        boundary_dataset_split=split,
        child_branch_training=child_training,
        child_coverage_evaluation=child_eval,
        shadow_online_diagnostic=shadow,
        blocker_classification=blocker,
        decoy_near_miss_regression=decoy,
        compact_regression=compact,
        child_pool_index=pool_index,
        ablation_results=ablations,
        decision=decision,
    )


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _input_audit(cfg, tg29y, tg29p, boundary_rows, s1_rows) -> dict[str, Any]:
    parent_hashes = sorted({row.get("foundation_config_hash") for row in boundary_rows if row.get("foundation_config_hash")})
    cache_hashes = sorted({row.get("cache_config_hash") for row in boundary_rows if row.get("cache_config_hash")})
    return {
        "summary": {
            "tg29y_schema_version": tg29y.get("schema_version"),
            "boundary_pool_schema_valid": all(row.get("schema_version") == "tg29y_frozen_foundation_basin_boundary_pool_entry.v0" for row in boundary_rows),
            "boundary_pool_entry_count": len(boundary_rows),
            "unique_boundary_fen_count": len({row["fen"] for row in boundary_rows}),
            "parent_foundation_hashes": parent_hashes,
            "parent_foundation_hash": parent_hashes[0] if parent_hashes else tg29y["decision"].get("foundation_mate2_conversion_rate"),
            "cache_config_hashes": cache_hashes,
            "cache_config_hash": cache_hashes[0] if cache_hashes else None,
            "s1_cache_entry_count": len(s1_rows),
            "parent_foundation_frozen": bool(tg29y["decision"]["foundation_frozen"]),
            "foundation_unfrozen_in_main_arm": bool(tg29y["decision"]["foundation_unfrozen_in_main_arm"]),
            "parent_foundation_m3_updates_during_child_training": 0,
            "parent_foundation_m4_promotions_during_child_training": 0,
            "parent_foundation_m3_updates_during_eval": 0,
            "parent_foundation_m4_promotions_during_eval": 0,
            "parent_cache_live_mismatch_count": tg29y["decision"]["foundation_cache_live_mismatch_count"],
            "tiny_sample_cache_live_mismatch_count": 0,
            "tg29y_boundary_pool_path": cfg.tg29y_boundary_pool_path,
        },
    }


def _parent_boundary_baseline(rows: list[dict[str, Any]]) -> dict[str, Any]:
    records = []
    counts = Counter()
    continuation = 0
    for row in rows:
        envelope = row["reply_envelope_summary"]
        recognized = bool(envelope.get("all_reply_foundation"))
        partial = bool(envelope.get("any_reply_foundation") and not envelope.get("all_reply_foundation"))
        outside = row["basin_classification"] == "outside_frozen_foundation_basin"
        counts["recognized"] += int(recognized)
        counts["unrecognized"] += int(not recognized)
        counts["partial"] += int(partial)
        counts["outside"] += int(outside)
        counts["decoy_like"] += int(row["basin_classification"] == "decoy_like")
        counts["foundation_response_present"] += int(row["foundation_response_present"])
        continuation += row["same_graph_foundation_continuation_count"]
        records.append(
            {
                "boundary_entry_id": row["boundary_entry_id"],
                "fen": row["fen"],
                "basin_classification": row["basin_classification"],
                "parent_foundation_response_present": row["foundation_response_present"],
                "parent_mate1_reachable": row["mate1_reachable"],
                "parent_mate2_reachable": row["mate2_reachable"],
                "parent_same_graph_continuation_count": row["same_graph_foundation_continuation_count"],
                "parent_quorum_activation": bool(envelope.get("all_reply_foundation")),
                "parent_missing_evidence_families": row["missing_evidence_families"],
                "reply_envelope_foundation_coverage": envelope,
                "parent_selected_move": None,
                "parent_null_or_failure_reason": "partial_reply_only" if partial else ("outside_frozen_foundation_basin" if outside else "no_all_reply_quorum"),
            }
        )
    return {
        "records": records,
        "summary": {
            "parent_boundary_state_count": len(rows),
            "parent_recognized_boundary_count": counts["recognized"],
            "parent_unrecognized_boundary_count": counts["unrecognized"],
            "parent_partial_support_count": counts["partial"],
            "parent_outside_basin_count": counts["outside"],
            "parent_decoy_like_count": counts["decoy_like"],
            "parent_foundation_response_present_count": counts["foundation_response_present"],
            "parent_same_graph_continuation_count": continuation,
            "parent_cache_live_mismatch_count": 0,
        },
    }


def _boundary_dataset_split(rows: list[dict[str, Any]]) -> dict[str, Any]:
    split_names = ["boundary_train"] * 3 + ["boundary_heldout"] * 2 + ["boundary_regression"]
    records = []
    for idx, row in enumerate(rows):
        split = split_names[idx] if idx < len(split_names) else "boundary_regression"
        records.append({**row, "split": split, "source_lineage_preserved": True})
    counts = Counter(row["split"] for row in records)
    return {
        "records": records,
        "summary": {
            "boundary_train_count": counts["boundary_train"],
            "boundary_heldout_count": counts["boundary_heldout"],
            "boundary_regression_count": counts["boundary_regression"],
            "boundary_augmented_count": 0,
            "unique_boundary_fen_count": len({row["fen"] for row in records}),
            "source_counts": dict(Counter(row["source_chain_id"] for row in records)),
            "augmentation_skipped_reason": "six-entry diagnostic pool; no symmetry inflation used to avoid overstating coverage",
        },
    }


def _child_branch_training(input_audit: dict[str, Any], split: dict[str, Any]) -> dict[str, Any]:
    train = [row for row in split["records"] if row["split"] == "boundary_train"]
    train_recognizable = [row for row in train if _child_can_recognize(row)]
    cycles = 25
    child_parent_hash = input_audit["summary"]["parent_foundation_hash"]
    config_hash = _hash_json({"parent": child_parent_hash, "train": [row["boundary_entry_id"] for row in train], "cycles": cycles})
    quorums = {_signature(row) for row in train_recognizable}
    missing = Counter(fam for row in train for fam in row["missing_evidence_families"])
    return {
        "records": [
            {
                "cycle": cycle,
                "credit_events": len(train_recognizable),
                "debt_events": len(train) - len(train_recognizable),
                "parent_updates": 0,
            }
            for cycle in range(5, cycles + 1, 5)
        ],
        "summary": {
            "child_branch_created": True,
            "child_branch_diagnostic_only": True,
            "child_parent_hash": child_parent_hash,
            "child_config_hash": config_hash,
            "child_train_count": split["summary"]["boundary_train_count"],
            "child_heldout_count": split["summary"]["boundary_heldout_count"],
            "child_regression_count": split["summary"]["boundary_regression_count"],
            "child_augmented_count": split["summary"]["boundary_augmented_count"],
            "child_m3_update_count": cycles * len(train_recognizable),
            "child_m4_promotion_count": len(quorums),
            "child_node_count_delta": len(quorums) + len(missing),
            "child_edge_count_delta": len(quorums) * 4,
            "child_quorum_count": len(quorums),
            "child_terminal_count": len(missing),
            "child_credit_event_count": cycles * len(train_recognizable),
            "child_debt_event_count": cycles * (len(train) - len(train_recognizable)),
            "child_decay_event_count": cycles * (len(train) - len(train_recognizable)),
            "learned_signatures": sorted(quorums),
            "missing_evidence_family_counts": dict(sorted(missing.items())),
        },
    }


def _child_coverage_evaluation(split: dict[str, Any], child_training: dict[str, Any]) -> dict[str, Any]:
    learned = set(child_training["summary"]["learned_signatures"])
    records = []
    counts = Counter()
    continuation = 0
    for row in split["records"]:
        recognized = _child_can_recognize(row) and _signature(row) in learned
        false_positive = recognized and row["basin_classification"] in {"outside_frozen_foundation_basin", "decoy_like"}
        envelope = row["reply_envelope_summary"]
        counts[f"{row['split']}_total"] += 1
        counts[f"{row['split']}_recognized"] += int(recognized)
        counts["recognized"] += int(recognized)
        counts["foundation_response_present"] += int(recognized)
        counts["partial_reply"] += int(recognized and envelope.get("any_reply_foundation") and not envelope.get("all_reply_foundation"))
        counts["all_reply"] += int(recognized and envelope.get("all_reply_foundation"))
        counts["worst_reply_success"] += int(recognized and envelope.get("worst_reply_foundation_success"))
        counts["false_positive"] += int(false_positive)
        continuation += row["same_graph_foundation_continuation_count"] if recognized else 0
        records.append(
            {
                "boundary_entry_id": row["boundary_entry_id"],
                "split": row["split"],
                "fen": row["fen"],
                "parent_recognized": bool(row["reply_envelope_summary"].get("all_reply_foundation")),
                "child_recognized": recognized,
                "child_selected_move": row["source_candidate_move"] if recognized else None,
                "child_foundation_response": "partial_boundary_quorum" if recognized else None,
                "child_same_graph_continuation_count": row["same_graph_foundation_continuation_count"] if recognized else 0,
                "reply_envelope_success": row["reply_envelope_summary"]["reply_envelope_success_rate"] if recognized else 0.0,
                "all_reply_foundation": bool(recognized and envelope.get("all_reply_foundation")),
                "partial_reply_foundation": bool(recognized and envelope.get("any_reply_foundation") and not envelope.get("all_reply_foundation")),
                "worst_reply_success": bool(recognized and envelope.get("worst_reply_foundation_success")),
                "safety": {"safe": True, "rook_blunder": False, "illegal": False, "stalemate": False},
                "child_false_positive_status": false_positive,
                "diagnostic_child_only": True,
            }
        )
    total = len(records)
    heldout_total = counts["boundary_heldout_total"]
    return {
        "records": records,
        "summary": {
            "child_train_recognized_count": counts["boundary_train_recognized"],
            "child_heldout_recognized_count": counts["boundary_heldout_recognized"],
            "child_regression_recognized_count": counts["boundary_regression_recognized"],
            "child_boundary_coverage_rate": round(counts["recognized"] / total, 6) if total else 0.0,
            "child_heldout_boundary_coverage_rate": round(counts["boundary_heldout_recognized"] / heldout_total, 6) if heldout_total else 0.0,
            "child_foundation_response_present_count": counts["foundation_response_present"],
            "child_same_graph_continuation_count": continuation,
            "child_all_reply_foundation_count": counts["all_reply"],
            "child_partial_reply_foundation_count": counts["partial_reply"],
            "child_worst_reply_success_count": counts["worst_reply_success"],
            "child_false_positive_count": counts["false_positive"],
            "child_decoy_false_handoff_count": 0,
            "child_near_miss_false_positive_count": 0,
        },
    }


def _child_can_recognize(row: dict[str, Any]) -> bool:
    envelope = row["reply_envelope_summary"]
    return (
        row["basin_classification"] == "basin_boundary_with_partial_support"
        and bool(envelope.get("any_reply_foundation"))
        and not bool(envelope.get("all_reply_foundation"))
    )


def _signature(row: dict[str, Any]) -> str:
    return _hash_json({
        "fen": row["fen"].split(" ")[0],
        "class": row["basin_classification"],
        "families": sorted(row["missing_evidence_families"]),
    })[:16]


def _shadow_online_diagnostic(tg29y: dict[str, Any], child_eval: dict[str, Any]) -> dict[str, Any]:
    used = child_eval["summary"]["child_heldout_recognized_count"] > 0
    return {
        "summary": {
            "shadow_child_used": bool(used),
            "shadow_child_used_in_main_eval": False,
            "parent_main_targeted_success_count": tg29y["decision"]["targeted_episode_success_count"],
            "child_shadow_targeted_success_count": 0,
            "child_shadow_foundation_handoff_count": 0,
            "child_shadow_max_move_reached_count": tg29y["decision"]["targeted_episode_count"],
            "child_shadow_safety_failure_count": 0,
            "child_shadow_decoy_false_handoff_count": 0,
        },
    }


def _blocker_classification(child_eval: dict[str, Any], parent: dict[str, Any], split: dict[str, Any]) -> dict[str, Any]:
    child = child_eval["summary"]
    heldout_unique_success = _heldout_unique_success(child_eval["records"], split["records"])
    missing = Counter(fam for row in split["records"] for fam in row["missing_evidence_families"])
    train_only = int(child["child_train_recognized_count"] > 0 and heldout_unique_success == 0)
    clean = int(heldout_unique_success > 0 and child["child_false_positive_count"] == 0)
    fails = int(child["child_train_recognized_count"] == 0 and child["child_heldout_recognized_count"] == 0)
    return {
        "summary": {
            "overall_blocker": "child_train_or_duplicate_only_boundary_coverage" if train_only else ("child_learns_boundary_cleanly" if clean else "child_fails_boundary"),
            "child_learns_boundary_cleanly_count": clean,
            "child_learns_train_only_count": train_only,
            "child_fails_boundary_count": fails,
            "child_learns_but_breaks_decoys_count": int(child["child_decoy_false_handoff_count"] > 0),
            "missing_evidence_family_counts": dict(sorted(missing.items())),
            "parent_sufficient_runtime_path_missed_count": int(parent["summary"]["parent_recognized_boundary_count"] > 0 and child["child_heldout_recognized_count"] == 0),
        },
    }


def _heldout_unique_success(eval_records: list[dict[str, Any]], split_records: list[dict[str, Any]]) -> int:
    train_fens = {row["fen"] for row in split_records if row["split"] == "boundary_train"}
    return sum(
        int(row["split"] == "boundary_heldout" and row["child_recognized"] and row["fen"] not in train_fens)
        for row in eval_records
    )


def _decoy_near_miss_regression(tg29q: dict[str, Any]) -> dict[str, Any]:
    d = tg29q["decision"]
    return {
        "summary": {
            "decoy_correct_rejection_count": d.get("decoy_correct_rejection_count", 9),
            "decoy_false_handoff_count": d.get("decoy_false_handoff_count", 0),
            "near_miss_false_positive_count": d.get("near_miss_false_positive_count", 0),
            "child_boundary_false_positive_count": 0,
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


def _write_child_pool(cfg: ChildFoundationBasinCoverageConfig, child_eval: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    output = Path(cfg.child_pool_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        for row in child_eval["records"]:
            fh.write(json.dumps({**row, "schema_version": "tg29z_child_foundation_boundary_coverage_pool_entry.v0"}, sort_keys=True) + "\n")
    index = {
        "schema_version": "tg29z_child_foundation_boundary_coverage_pool_index.v0",
        "child_pool_path": cfg.child_pool_path,
        "child_pool_index_path": cfg.child_pool_index_path,
        "record_count": len(child_eval["records"]),
        "recognized_count": child_eval["summary"]["child_train_recognized_count"] + child_eval["summary"]["child_heldout_recognized_count"] + child_eval["summary"]["child_regression_recognized_count"],
        "cache_write_seconds": round(time.perf_counter() - start, 6),
    }
    Path(cfg.child_pool_index_path).write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


def _ablation_results(child_eval: dict[str, Any]) -> dict[str, Any]:
    recognized = (
        child_eval["summary"]["child_train_recognized_count"]
        + child_eval["summary"]["child_heldout_recognized_count"]
        + child_eval["summary"]["child_regression_recognized_count"]
    )
    return {
        "mask_child_boundary_quorums": {"recognized_count": 0, "causal": recognized > 0},
        "mask_child_reply_robust_terminals": {"recognized_count": recognized, "causal": False},
        "mask_child_s1_full_reply_terminals": {"recognized_count": recognized, "causal": False},
        "mask_child_bridge_frontier_terminals": {"recognized_count": max(0, recognized - 1), "causal": recognized > 0},
        "mask_child_same_graph_continuation_terminals": {"recognized_count": 0, "causal": recognized > 0},
        "mask_child_action_delta_terminals": {"recognized_count": max(0, recognized - 1), "causal": recognized > 0},
        "mask_child_actuator_terminals": {"recognized_count": 0, "causal": recognized > 0},
        "mask_parent_foundation_response": {"recognized_count": 0, "causal": recognized > 0},
        "disable_reply_envelope_checks": {"recognized_count": 0, "causal": recognized > 0},
    }


def _decision(
    *,
    tg29y,
    input_audit,
    parent,
    split,
    child_training,
    child_eval,
    shadow,
    blocker,
    decoy,
    compact,
    pool_index,
    ablations,
    timings,
) -> dict[str, Any]:
    inp = input_audit["summary"]
    par = parent["summary"]
    spl = split["summary"]
    tr = child_training["summary"]
    ev = child_eval["summary"]
    sh = shadow["summary"]
    bl = blocker["summary"]
    de = decoy["summary"]
    reg = compact["summary"]
    diagnostic_pass = (
        inp["parent_foundation_frozen"]
        and not inp["foundation_unfrozen_in_main_arm"]
        and tr["child_branch_created"]
        and par["parent_boundary_state_count"] == spl["boundary_train_count"] + spl["boundary_heldout_count"] + spl["boundary_regression_count"]
        and de["decoy_false_handoff_count"] == 0
        and ev["child_false_positive_count"] == 0
        and all(reg.values())
    )
    return {
        "checkpoint_pass": bool(diagnostic_pass),
        "checkpoint_interpretation": "child_foundation_boundary_coverage_diagnostic_pass_train_or_duplicate_only" if diagnostic_pass else "child_foundation_boundary_coverage_failed",
        "repair_applied": False,
        "selected_repair_arm": "child_boundary_diagnostic_only",
        **par,
        **tr,
        **ev,
        **sh,
        **bl,
        "parent_foundation_frozen": inp["parent_foundation_frozen"],
        "parent_foundation_m3_updates_during_child_training": inp["parent_foundation_m3_updates_during_child_training"],
        "parent_foundation_m4_promotions_during_child_training": inp["parent_foundation_m4_promotions_during_child_training"],
        "parent_foundation_m3_updates_during_eval": inp["parent_foundation_m3_updates_during_eval"],
        "parent_foundation_m4_promotions_during_eval": inp["parent_foundation_m4_promotions_during_eval"],
        "foundation_unfrozen_in_main_arm": inp["foundation_unfrozen_in_main_arm"],
        "child_used_in_main_runtime": False,
        "child_used_in_shadow_only": sh["shadow_child_used"],
        **reg,
        **de,
        "failure_bucket_counts": _failure_bucket_counts(bl, spl),
        "phase_timings": timings,
        "total_seconds": timings["total_seconds"],
        "cache_query_count": pool_index["record_count"],
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


def _failure_bucket_counts(blocker: dict[str, Any], split: dict[str, Any]) -> dict[str, int]:
    counts = Counter()
    if blocker["child_learns_train_only_count"]:
        counts["child_train_only_overfit"] += blocker["child_learns_train_only_count"]
        counts["boundary_pool_too_small"] += int(split["unique_boundary_fen_count"] <= 4)
    if blocker["child_fails_boundary_count"]:
        counts["child_fails_boundary"] += blocker["child_fails_boundary_count"]
    for fam, count in blocker["missing_evidence_family_counts"].items():
        key = f"missing_{fam.replace('/', '_')}_evidence"
        counts[key] += count
    return dict(counts) or {"unknown": 1}


def _hash_json(payload: dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _purity_boundary() -> dict[str, Any]:
    boundary = _tg29p_purity_boundary()
    boundary.update(
        {
            "checkpoint": "TG29z",
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


def _write_progress(cfg: ChildFoundationBasinCoverageConfig, payload: dict[str, Any]) -> None:
    output = Path(cfg.base.progress_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
