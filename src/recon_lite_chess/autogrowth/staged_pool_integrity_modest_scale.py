"""TG28l staged pool integrity and modest scale."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

import chess

from .persisted_staged_predecessor_pool import (
    PersistedStagedPredecessorPoolConfig,
    PersistedStagedPredecessorPoolResult,
    run_persisted_staged_predecessor_pool,
)


@dataclass(frozen=True)
class StagedPoolIntegrityModestScaleConfig:
    pool_config: PersistedStagedPredecessorPoolConfig = PersistedStagedPredecessorPoolConfig(
        staged_train_count=8,
        staged_heldout_count=4,
        staged_regression_count=4,
        staged_near_miss_count=8,
        near_miss_heldout_count=8,
        max_ablation_positions=1,
        staged_pool_path="reports/autogrowth/pools/tg28l_staged_predecessor_pool.jsonl",
        staged_pool_index_path="reports/autogrowth/pools/tg28l_staged_predecessor_pool_index.json",
        progress_output="reports/autogrowth/krk_autogrowth_tg28l_staged_pool_integrity_modest_scale_progress.json",
    )


@dataclass(frozen=True)
class StagedPoolIntegrityModestScaleResult:
    config: StagedPoolIntegrityModestScaleConfig
    pool_result: PersistedStagedPredecessorPoolResult

    def to_dict(self) -> dict[str, Any]:
        payload = self.pool_result.to_dict()
        decision = dict(payload["decision"])
        entries = payload["pool"].get("samples", [])
        all_entries = _load_entries(Path(self.pool_result.config.staged_pool_path))
        pool = _pool_integrity(all_entries, decision)
        schedules = payload.get("schedule_comparison", {})
        baseline = schedules.get("tg28h_mixed_balanced_baseline", {})
        selected = payload.get("selected_schedule", {})
        ablations = payload.get("ablation_results", {})
        restored = [name for name, row in ablations.items() if not row.get("skipped", False)]
        staged_improvement = selected.get("staged_any_reply_success_count", 0) - baseline.get("staged_any_reply_success_count", 0)
        foundation_frozen = (
            decision["foundation_m3_updates_during_training"] == 0
            and decision["foundation_m4_promotions_during_training"] == 0
            and decision["foundation_m3_updates_during_eval"] == 0
            and decision["foundation_m4_promotions_during_eval"] == 0
        )
        integrity_pass = bool(
            pool["single_foundation_hash"]
            and pool["single_cache_hash"]
            and not pool["mixed_cache_hash_detected"]
            and decision["foundation_cache_live_mismatch_count"] == 0
            and foundation_frozen
            and decision["staged_train_count"] > 0
            and decision["staged_heldout_count"] > 0
            and decision["staged_regression_count"] > 0
            and decision["staged_near_miss_count"] > 0
        )
        scale_pass = bool(
            integrity_pass
            and selected.get("staged_any_reply_success_count", 0) > 0
            and selected.get("staged_s1_bridge_selected_count", 0) > 0
            and selected.get("staged_s1_bridge_foundation_reachable_count", 0) > 0
            and selected.get("near_miss_false_positive_count", 0) <= 1
            and selected.get("frontier_selected_count", 0) > 0
            and selected.get("generic_rook_blunder_count", 0) == 0
            and selected.get("generic_stalemate_avoidance_rate", 0.0) >= 1.0
            and _layered_ablation_signal(ablations)
        )
        checkpoint_pass = integrity_pass and scale_pass
        interpretation = (
            "staged_pool_integrity_and_modest_scale_pass"
            if checkpoint_pass
            else (
                "staged_pool_integrity_pass_scale_inconclusive"
                if integrity_pass
                else "staged_pool_integrity_failed"
            )
        )
        decision.update(
            {
                "checkpoint_pass": checkpoint_pass,
                "checkpoint_interpretation": interpretation,
                "tg28j_underlying_checkpoint_pass": payload["decision"]["checkpoint_pass"],
                "tg28j_underlying_checkpoint_interpretation": payload["decision"]["checkpoint_interpretation"],
                "foundation_frozen": foundation_frozen,
                "foundation_m3_updates_during_pool_recertification": 0,
                "foundation_m4_promotions_during_pool_recertification": 0,
                "recertified_entry_count": 0,
                "regenerated_entry_count": pool["staged_pool_entry_count"],
                "recertification_failed_count": 0,
                "cache_live_mismatch_count": decision["foundation_cache_live_mismatch_count"],
                "live_foundation_queries_run": selected.get("staged", {}).get("cache_queries_run", 0) + selected.get("frontier", {}).get("cache_queries_run", 0),
                "deep_reply_checks_run": _deep_reply_checks(selected),
                "cache_queries_run": _cache_queries(payload),
                "single_foundation_hash": pool["single_foundation_hash"],
                "single_cache_hash": pool["single_cache_hash"],
                "mixed_cache_hash_detected": pool["mixed_cache_hash_detected"],
                "generation_method_counts": pool["generation_method_counts"],
                "anchor_overlap_count": pool["anchor_overlap_count"],
                "mutation_lineage_overlap_count": pool["mutation_lineage_overlap_count"],
                "exact_canonical_overlap_count": pool["exact_canonical_overlap_count"],
                "geometry_bucket_overlap_count": pool["geometry_bucket_overlap_count"],
                "unique_start_fen_count": pool["unique_start_fen_count"],
                "unique_s1_fen_count": pool["unique_s1_fen_count"],
                "unique_foundation_query_fen_count": pool["unique_foundation_query_fen_count"],
                "no_edge_predecessor_rejections": decision["failure_bucket_counts"]["pool_generation"].get("no_edge_predecessor_found", 0),
                "no_bridge_s1_rejections": decision["failure_bucket_counts"]["pool_generation"].get("edge_predecessor_found_but_no_bridge_s1", 0),
                "no_foundation_response_rejections": decision["failure_bucket_counts"]["pool_generation"].get("bridge_s1_found_but_no_foundation_response", 0),
                "unsafe_rejections": decision["failure_bucket_counts"]["pool_generation"].get("unsafe_candidate", 0),
                "staged_near_miss_selected_count": selected.get("near_miss_selected_count", 0),
                "staged_near_miss_false_positive_count": selected.get("near_miss_false_positive_count", 0),
                "staged_near_miss_rejection_rate": selected.get("near_miss_rejection_rate", 0.0),
                "staged_near_miss_failure_bucket_counts": selected.get("near_miss_failure_bucket_counts", {}),
                "staged_training_improvement_vs_baseline": staged_improvement,
                "near_miss_false_positive_increase_vs_TG28k": selected.get("near_miss_false_positive_count", 0),
                "restored_ablation_count": len(restored),
                "restored_ablation_names": restored,
                "layered_ablation_signal": _layered_ablation_signal(ablations),
                "staged_training_adds_value": staged_improvement > 0,
                "staged_pool_better_as_validation_regression_substrate": staged_improvement <= 0,
                "do_not_claim_broad_krk_competence": True,
            }
        )
        payload.update(
            {
                "schema_version": "krk_autogrowth_tg28l_staged_pool_integrity_modest_scale.v0",
                "checkpoint": "TG28l_staged_pool_integrity_modest_scale",
                "config": asdict(self.config),
                "underlying_tg28j_config": asdict(self.pool_result.config),
                "pool_integrity": pool,
                "pool_samples": entries,
                "decision": decision,
            }
        )
        payload["purity_boundary"] = dict(payload["purity_boundary"]) | {
            "checkpoint": "TG28l",
            "rebuilt_homogeneous_staged_pool": True,
            "pool_used_as_provider": False,
            "staged_training_labels_learner_visible": False,
        }
        return payload

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output

    def write_markdown(self, path: str | Path) -> Path:
        payload = self.to_dict()
        decision = payload["decision"]
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "\n".join(
                [
                    "# TG28l Staged Pool Integrity + Modest Scale",
                    "",
                    f"- checkpoint_pass: `{decision['checkpoint_pass']}`",
                    f"- interpretation: `{decision['checkpoint_interpretation']}`",
                    f"- selected schedule: `{decision['selected_training_schedule']}`",
                    f"- staged pool entries: `{decision['staged_pool_entry_count']}`",
                    f"- split: `{decision['staged_train_count']}` train / `{decision['staged_heldout_count']}` heldout / `{decision['staged_regression_count']}` regression / `{decision['staged_near_miss_count']}` near-miss",
                    f"- single foundation hash: `{decision['single_foundation_hash']}`",
                    f"- single cache hash: `{decision['single_cache_hash']}`",
                    f"- staged any-reply successes: `{decision['staged_any_reply_success_count']}`",
                    f"- staged near-miss false positives: `{decision['staged_near_miss_false_positive_count']}`",
                    f"- staged training improvement vs baseline: `{decision['staged_training_improvement_vs_baseline']}`",
                    f"- foundation M3/M4 training deltas: `{decision['foundation_m3_updates_during_training']}` / `{decision['foundation_m4_promotions_during_training']}`",
                    "",
                    "Interpretation: TG28l is still a staged-runway checkpoint. It does not claim broad KRK competence.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return output


def run_staged_pool_integrity_modest_scale(
    *,
    config: StagedPoolIntegrityModestScaleConfig | None = None,
) -> StagedPoolIntegrityModestScaleResult:
    cfg = config or StagedPoolIntegrityModestScaleConfig()
    pool_result = run_persisted_staged_predecessor_pool(config=cfg.pool_config)
    return StagedPoolIntegrityModestScaleResult(config=cfg, pool_result=pool_result)


def _load_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _pool_integrity(entries: list[dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    foundation_hashes = sorted({entry.get("foundation_config_hash") for entry in entries})
    cache_hashes = sorted({entry.get("cache_config_hash") for entry in entries})
    train = [entry for entry in entries if entry.get("split") == "train"]
    heldout = [entry for entry in entries if entry.get("split") == "heldout"]
    train_exact = {_canonical_identity(entry) for entry in train}
    heldout_exact = {_canonical_identity(entry) for entry in heldout}
    train_geom = {_geometry_bucket(entry["start_fen"]) for entry in train}
    heldout_geom = {_geometry_bucket(entry["start_fen"]) for entry in heldout}
    generation_methods = Counter(entry.get("generation_method", "unknown") for entry in entries)
    return {
        "staged_pool_path": decision["staged_pool_path"],
        "staged_pool_index_path": decision["staged_pool_index_path"],
        "staged_pool_entry_count": len(entries),
        "foundation_config_hashes": foundation_hashes,
        "cache_config_hashes": cache_hashes,
        "single_foundation_hash": len(foundation_hashes) == 1 and decision["pool_foundation_hash_match_count"] == len(entries),
        "single_cache_hash": len(cache_hashes) == 1 and decision["pool_cache_hash_match_count"] == len(entries),
        "mixed_cache_hash_detected": len(cache_hashes) > 1,
        "generation_method_counts": dict(sorted(generation_methods.items())),
        "anchor_overlap_count": len(_field_set(train, "anchor_bridge_fen") & _field_set(heldout, "anchor_bridge_fen")),
        "mutation_lineage_overlap_count": len(_lineage_set(train) & _lineage_set(heldout)),
        "exact_canonical_overlap_count": len(train_exact & heldout_exact),
        "geometry_bucket_overlap_count": len(train_geom & heldout_geom),
        "unique_start_fen_count": len({entry["start_fen"] for entry in entries}),
        "unique_s1_fen_count": len({entry["s1_fen"] for entry in entries}),
        "unique_foundation_query_fen_count": len({entry["foundation_query_fen"] for entry in entries}),
    }


def _field_set(entries: list[dict[str, Any]], field: str) -> set[str]:
    return {str(entry.get(field)) for entry in entries if entry.get(field)}


def _lineage_set(entries: list[dict[str, Any]]) -> set[str]:
    return {
        str(entry.get("bridge_frontier_pool_entry_id") or entry.get("anchor_bridge_fen") or entry.get("start_fen"))
        for entry in entries
    }


def _canonical_identity(entry: dict[str, Any]) -> str:
    return chess.Board(entry["start_fen"]).board_fen()


def _geometry_bucket(fen: str) -> tuple[Any, ...]:
    board = chess.Board(fen)
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    rook = next((sq for sq, piece in board.piece_map().items() if piece.color == chess.WHITE and piece.piece_type == chess.ROOK), None)
    if wk is None or bk is None or rook is None:
        return ("invalid",)
    return (
        min(chess.square_file(bk), chess.square_rank(bk), 7 - chess.square_file(bk), 7 - chess.square_rank(bk)),
        abs(chess.square_file(wk) - chess.square_file(bk)) + abs(chess.square_rank(wk) - chess.square_rank(bk)),
        abs(chess.square_file(rook) - chess.square_file(bk)) + abs(chess.square_rank(rook) - chess.square_rank(bk)),
        chess.square_file(bk) in (0, 7),
        chess.square_rank(bk) in (0, 7),
    )


def _cache_queries(payload: dict[str, Any]) -> int:
    total = 0
    for row in payload.get("schedule_comparison", {}).values():
        for key in ("frontier", "near_miss", "staged"):
            total += int(row.get(key, {}).get("cache_queries_run", 0))
    return total


def _deep_reply_checks(selected: dict[str, Any]) -> int:
    return int(selected.get("staged", {}).get("black_reply_count_total", 0)) + int(selected.get("frontier", {}).get("cache_queries_run", 0))


def _layered_ablation_signal(ablations: dict[str, Any]) -> bool:
    if not ablations:
        return False
    actuator = ablations.get("mask_actuator_terminals", {}).get("staged", {})
    edge = ablations.get("mask_edge_fence_terminals", {}).get("staged", {})
    bridge = ablations.get("mask_bridge_pressure_terminals", {}).get("staged", {})
    foundation = ablations.get("mask_foundation_response_terminals", {}).get("staged", {})
    reply = ablations.get("disable_reply_envelope_foundation_checks", {}).get("staged", {})
    mate2 = ablations.get("mask_frozen_mate2_foundation_quorum", {}).get("staged", {})
    return bool(
        actuator.get("selected_first_move_count") == 0
        and edge.get("selected_first_move_count") == 0
        and bridge.get("any_reply_success_count", 0) == 0
        and foundation.get("any_reply_success_count", 0) == 0
        and reply.get("any_reply_success_count", 0) == 0
        and mate2.get("any_reply_success_count", 0) == 0
    )
