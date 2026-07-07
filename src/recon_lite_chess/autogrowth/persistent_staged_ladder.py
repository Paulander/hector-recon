"""Persistent KRK staged ladder runners and stable plasticity probes."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import random
from typing import Any, Mapping, Sequence

import chess

from .stage_b_ecological_discovery_probe import (
    StageBEcologicalDiscoveryConfig,
    _MigratedStageBFlatGraphScoreProvider,
    _choose_migrated_flat_host_move,
    _design_spec,
    _legal_without_third_repetition,
    _load_weight_table,
    _new_judge_cache,
    _phase38_dispatcher_side_eval,
    _phase38_flat_policy_traces,
    _phase38_gate_result,
    _phase38_migrated_provider_traces,
    _phase38_provenance_law,
    _phase38_rebaseline_phase29e_discovery,
    _phase38_rebaseline_table,
    _position_repetition_key,
    _rollout_policy,
    _sealed_action_key_scales,
    _train_native_foundation_for_ecology,
    _write_json,
)


def run_phase39_stable_plasticity_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    """User-requested Phase 3.8: fast/slow consolidation on the living host."""

    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_9_stable_plasticity",
        seeds=(20272931, 20272932, 20272933),
        flat_baseline_seeds=(20272911, 20272912, 20272913),
        stage_a_train_row_limit=128,
        train_row_limit=128,
        heldout_row_limit=None,
        max_samples=8,
        max_guided_births=0,
        ecology_mode="stem_cell_graph",
        native_foundation_key_mode="coarse",
        native_foundation_prototype_scan_triplets=128,
        real_native_engine_max_ticks=80,
    )
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_9_stable_plasticity_design_spec.v0"
    design["phase_alias"] = "User-requested Phase 3.8 stable plasticity"
    design["split_law"] = _phase39_split_law(cfg)
    design["consolidation"] = _phase39_consolidation_spec()
    _write_json(output_dir / "design_spec.json", design)

    stage_a_payload = json.loads(Path(cfg.stage_a_rows_path).read_text(encoding="utf-8"))
    stage_b_payload = json.loads(Path(cfg.stage_b_rows_path).read_text(encoding="utf-8"))
    stage_a_train_pool = list(stage_a_payload["train"])
    stage_b_train_pool = list(stage_b_payload["train"])
    stage_a_gate_rows = list(stage_a_payload["heldout"])
    stage_b_gate_rows = list(stage_b_payload["heldout"])
    stage_a_limit = cfg.stage_a_train_row_limit if cfg.stage_a_train_row_limit is not None else cfg.train_row_limit
    if stage_a_limit is not None:
        stage_a_train_pool = stage_a_train_pool[: int(stage_a_limit)]
    if cfg.train_row_limit is not None:
        stage_b_train_pool = stage_b_train_pool[: int(cfg.train_row_limit)]
    if cfg.heldout_row_limit is not None:
        stage_a_gate_rows = stage_a_gate_rows[: int(cfg.heldout_row_limit)]
        stage_b_gate_rows = stage_b_gate_rows[: int(cfg.heldout_row_limit)]

    rebaseline = _phase38_rebaseline_phase29e_discovery(cfg, stage_b_gate_rows)
    _write_json(output_dir / "phase2_9e_rebaseline_audit.json", rebaseline)

    per_seed: list[dict[str, Any]] = []
    for index, seed in enumerate(cfg.seeds):
        flat_seed = int(cfg.flat_baseline_seeds[index % len(cfg.flat_baseline_seeds)])
        stage_a_train_rows, stage_a_validation_rows = _phase39_split_train_validation(
            stage_a_train_pool,
            seed=int(seed) + 101,
        )
        stage_b_train_rows, stage_b_validation_rows = _phase39_split_train_validation(
            stage_b_train_pool,
            seed=int(seed) + 202,
        )
        foundation = _train_native_foundation_for_ecology(cfg)
        native_graph = foundation["graph"]
        stage_a_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir) / f"stage_d_A_sealed_seed_{flat_seed}_weights.json"
        )
        stage_b_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir) / f"stage_d_B_sealed_seed_{flat_seed}_weights.json"
        )
        stage_a_baseline = _phase38_flat_policy_traces(
            cfg,
            stage_a_gate_rows,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 700,
            policy_name=f"phase3_9_stage_a_executable_flat_exact_adversarial_{flat_seed}",
            success_kind="approach_waypoint",
        )
        stage_b_baseline = _phase38_flat_policy_traces(
            cfg,
            stage_b_gate_rows,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 900,
            policy_name=f"phase3_9_stage_b_executable_flat_exact_adversarial_{flat_seed}",
            success_kind="stage_b_enter_mate2",
        )
        foundation_gate = _phase39_foundation_gate(foundation, cfg)
        seed_result: dict[str, Any] = {
            "schema_version": "phase3_9_stable_plasticity_seed.v0",
            "seed": int(seed),
            "flat_seed": flat_seed,
            "split_law": _phase39_split_law(cfg),
            "split_manifest": {
                "stage_a": _phase39_split_manifest(stage_a_train_rows, stage_a_validation_rows, stage_a_gate_rows),
                "stage_b": _phase39_split_manifest(stage_b_train_rows, stage_b_validation_rows, stage_b_gate_rows),
            },
            "foundation": foundation["summary"],
            "baselines": {
                "stage_a_exact_adversarial_flat_gate": stage_a_baseline,
                "stage_b_exact_adversarial_flat_gate": stage_b_baseline,
            },
            "gate_matrix": {
                "after_foundation": {
                    "foundation": foundation_gate,
                    "stage_a_approach": None,
                    "stage_b_chase": None,
                }
            },
            "stop_reasons": [],
        }
        if not foundation_gate["passed"]:
            seed_result["stop_reasons"].append("foundation_gate_failed")
            _write_json(output_dir / f"seed_{seed}_stable_plasticity.json", seed_result)
            per_seed.append(seed_result)
            continue

        stage_a_provider = _MigratedStageBFlatGraphScoreProvider(
            cfg,
            native_graph,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            policy_parent_id="stage_a_policy_stable_plasticity",
            terminal_namespace=f"phase3_9_stage_a_{flat_seed}",
        )
        stage_a_acceptance = (
            stage_a_provider.acceptance_check(stage_a_gate_rows[0], seed=int(seed))
            if stage_a_gate_rows
            else {}
        )
        stage_a_training = _phase39_train_with_fast_slow_consolidation(
            cfg,
            provider=stage_a_provider,
            train_rows=stage_a_train_rows,
            validation_rows=stage_a_validation_rows,
            prior_replay_checks=(),
            seed=int(seed) + 10_000,
            success_kind="approach_waypoint",
            rung_name="stage_a_approach",
        )
        stage_a_gate_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_a_gate_rows,
            stage_a_provider,
            seed=int(seed) + 11_000,
            policy_name=f"phase3_9_stage_a_slow_host_gate_{seed}",
            success_kind="approach_waypoint",
        )
        stage_a_gate = _phase38_gate_result(
            rung="stage_a_approach",
            evaluation=stage_a_gate_eval,
            baseline=stage_a_baseline,
        )
        seed_result["stage_a"] = {
            "acceptance_check": stage_a_acceptance,
            "training": stage_a_training,
            "gate_evaluation": stage_a_gate_eval,
            "gate": stage_a_gate,
            "host_stats": stage_a_provider.stats(),
        }
        seed_result["gate_matrix"]["after_stage_a"] = {
            "foundation": foundation_gate,
            "stage_a_approach": stage_a_gate,
            "stage_b_chase": None,
        }
        if int(stage_a_training["chunks_consolidated"]) == 0:
            seed_result["stop_reasons"].append("stage_a_zero_chunks_consolidated")
        if not stage_a_gate["passed"]:
            seed_result["stop_reasons"].append("stage_a_gate_unreachable_after_budget")
        if seed_result["stop_reasons"]:
            _write_json(output_dir / f"seed_{seed}_stable_plasticity.json", seed_result)
            per_seed.append(seed_result)
            continue

        stage_b_provider = _MigratedStageBFlatGraphScoreProvider(
            cfg,
            native_graph,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            policy_parent_id="stage_b_policy_stable_plasticity",
            terminal_namespace=f"phase3_9_stage_b_{flat_seed}",
        )
        stage_b_acceptance = (
            stage_b_provider.acceptance_check(stage_b_gate_rows[0], seed=int(seed))
            if stage_b_gate_rows
            else {}
        )

        def stage_a_prior_replay() -> dict[str, Any]:
            return _phase38_migrated_provider_traces(
                cfg,
                stage_a_validation_rows,
                stage_a_provider,
                seed=int(seed) + 12_000,
                policy_name=f"phase3_9_stage_a_validation_replay_for_stage_b_{seed}",
                success_kind="approach_waypoint",
            )

        stage_b_training = _phase39_train_with_fast_slow_consolidation(
            cfg,
            provider=stage_b_provider,
            train_rows=stage_b_train_rows,
            validation_rows=stage_b_validation_rows,
            prior_replay_checks=(
                {
                    "name": "stage_a_validation_replay",
                    "evaluate": stage_a_prior_replay,
                },
            ),
            seed=int(seed) + 20_000,
            success_kind="stage_b_enter_mate2",
            rung_name="stage_b_chase",
        )
        stage_b_gate_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_b_gate_rows,
            stage_b_provider,
            seed=int(seed) + 21_000,
            policy_name=f"phase3_9_stage_b_slow_host_gate_{seed}",
            success_kind="stage_b_enter_mate2",
        )
        stage_a_regression_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_a_gate_rows,
            stage_a_provider,
            seed=int(seed) + 22_000,
            policy_name=f"phase3_9_stage_a_regression_gate_after_stage_b_{seed}",
            success_kind="approach_waypoint",
        )
        stage_b_gate = _phase38_gate_result(
            rung="stage_b_chase",
            evaluation=stage_b_gate_eval,
            baseline=stage_b_baseline,
        )
        stage_a_regression_gate = _phase38_gate_result(
            rung="stage_a_approach_regression",
            evaluation=stage_a_regression_eval,
            baseline=stage_a_baseline,
        )
        seed_result["stage_b"] = {
            "acceptance_check": stage_b_acceptance,
            "training": stage_b_training,
            "gate_evaluation": stage_b_gate_eval,
            "gate": stage_b_gate,
            "host_stats": stage_b_provider.stats(),
        }
        seed_result["regression_checks"] = {
            "stage_a_after_stage_b": {
                "gate_evaluation": stage_a_regression_eval,
                "gate": stage_a_regression_gate,
            }
        }
        seed_result["gate_matrix"]["after_stage_b"] = {
            "foundation": foundation_gate,
            "stage_a_approach": stage_a_regression_gate,
            "stage_b_chase": stage_b_gate,
        }
        if int(stage_b_training["chunks_consolidated"]) == 0:
            seed_result["stop_reasons"].append("stage_b_zero_chunks_consolidated")
        if not stage_b_gate["passed"]:
            seed_result["stop_reasons"].append("stage_b_gate_unreachable_after_budget")
        if not stage_a_regression_gate["passed"]:
            seed_result["stop_reasons"].append("stage_a_regression_after_stage_b")
        _write_json(output_dir / f"seed_{seed}_stable_plasticity.json", seed_result)
        per_seed.append(seed_result)

    dispatcher_side_eval = _phase38_dispatcher_side_eval(cfg, stage_b_gate_rows)
    standing_ladder = all(
        not row.get("stop_reasons")
        and bool(row.get("gate_matrix", {}).get("after_stage_b", {}).get("foundation", {}).get("passed"))
        and bool(row.get("gate_matrix", {}).get("after_stage_b", {}).get("stage_a_approach", {}).get("passed"))
        and bool(row.get("gate_matrix", {}).get("after_stage_b", {}).get("stage_b_chase", {}).get("passed"))
        for row in per_seed
    )
    summary = {
        "schema_version": "phase3_9_stable_plasticity.v0",
        "phase": "User-requested Phase 3.8 stable plasticity",
        "artifact_path_note": "phase3_9 path used because phase3_8_persistent_staged_ladder already exists",
        "config": asdict(cfg),
        "split_law": _phase39_split_law(cfg),
        "consolidation": _phase39_consolidation_spec(),
        "dataset": {
            "recent_curriculum_only_for_stage_a_b": True,
            "old_krk_curriculum_imported_for_stage_a_b": False,
            "foundation_rung": "native Mate1/Mate2 sanity graph",
            "stage_a_rows_path": str(cfg.stage_a_rows_path),
            "stage_b_rows_path": str(cfg.stage_b_rows_path),
            "stage_a_train_pool_count": len(stage_a_train_pool),
            "stage_b_train_pool_count": len(stage_b_train_pool),
            "stage_a_gate_heldout_count": len(stage_a_gate_rows),
            "stage_b_gate_heldout_count": len(stage_b_gate_rows),
            "gate_rows_consulted_by_update_decisions": False,
        },
        "rebaseline_audit": rebaseline,
        "per_seed": per_seed,
        "dispatcher_side_eval": dispatcher_side_eval,
        "tables": {
            "phase3_9_gate_matrix": _phase39_gate_matrix_table(per_seed),
            "phase3_9_consolidation": _phase39_consolidation_table(per_seed),
            "phase3_9_rebaseline_correction": _phase38_rebaseline_table(rebaseline),
        },
        "decision": {
            "ecology_deferred": True,
            "standing_ladder_all_seeds_green": standing_ladder,
            "run_ecology_next": standing_ladder,
            "stop_reasons_by_seed": {
                str(row["seed"]): list(row.get("stop_reasons", ())) for row in per_seed
            },
        },
    }
    _write_json(output_dir / "summary.json", summary)
    return summary


def _phase39_split_law(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    return {
        "law": (
            "Every rung has train chunks, a validation buffer freshly split from the train pool, "
            "and a gate heldout. Consolidation may consult only the validation buffer plus "
            "previously-passed-rung replay rows; the gate heldout is never consulted by updates."
        ),
        "m3_fast_layer": "contrastive chunk updates on a temporary fast overlay",
        "m4_slow_layer": "merge fast into slow only when validation and prior replay do not regress",
        "supersedes": "per-key precision promotion criterion retired in Phase 1",
        "gate_void_if_consulted": True,
        "chunk_size": _phase39_chunk_size(cfg),
    }


def _phase39_consolidation_spec() -> dict[str, Any]:
    return {
        "variable_changed": "update acceptance only",
        "contrast_rule_changed": False,
        "learner_visible_features_changed": False,
        "acceptance": "validation wins non-regress and all prior-rung replay checks non-regress",
        "rejection": "discard fast deltas and restore slow host weights",
        "endpoint_delta_instrumentation": [
            "fence_broken",
            "rook_lost",
            "horizon",
            "third_repetition",
            "stalemate",
            "illegal",
        ],
    }


def _phase39_foundation_gate(foundation: Mapping[str, Any], cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    summary = foundation["summary"]
    return {
        "rung": "foundation_mate1_mate2",
        "passed": bool(summary["decision"]["checkpoint_pass"]),
        "mate1_accuracy": float(summary["mate1"]["evaluation"]["accuracy"]),
        "mate2_conversion_rate": float(summary["mate2"]["evaluation"]["conversion_rate"]),
        "tick_budget": int(cfg.native_foundation_max_ticks),
    }


def _phase39_split_train_validation(
    rows: Sequence[Mapping[str, Any]],
    *,
    seed: int,
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    shuffled = list(rows)
    rng = random.Random(seed)
    rng.shuffle(shuffled)
    if len(shuffled) <= 1:
        return shuffled, list(shuffled)
    validation_count = max(1, min(len(shuffled) - 1, max(8, len(shuffled) // 4)))
    validation = shuffled[:validation_count]
    train = shuffled[validation_count:]
    return train, validation


def _phase39_split_manifest(
    train_rows: Sequence[Mapping[str, Any]],
    validation_rows: Sequence[Mapping[str, Any]],
    gate_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "train_count": len(train_rows),
        "validation_count": len(validation_rows),
        "gate_heldout_count": len(gate_rows),
        "train_row_ids": [int(row["row_id"]) for row in train_rows],
        "validation_row_ids": [int(row["row_id"]) for row in validation_rows],
        "gate_heldout_row_ids": [int(row["row_id"]) for row in gate_rows],
        "train_validation_overlap": sorted(
            set(int(row["row_id"]) for row in train_rows)
            & set(int(row["row_id"]) for row in validation_rows)
        ),
        "validation_gate_overlap": sorted(
            set(int(row["row_id"]) for row in validation_rows)
            & set(int(row["row_id"]) for row in gate_rows)
        ),
        "gate_rows_consulted_by_update_decisions": False,
    }


def _phase39_train_with_fast_slow_consolidation(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    provider: _MigratedStageBFlatGraphScoreProvider,
    train_rows: Sequence[Mapping[str, Any]],
    validation_rows: Sequence[Mapping[str, Any]],
    prior_replay_checks: Sequence[Mapping[str, Any]],
    seed: int,
    success_kind: str,
    rung_name: str,
) -> dict[str, Any]:
    chunk_size = _phase39_chunk_size(cfg)
    chunks = [
        list(train_rows[index : index + chunk_size])
        for index in range(0, len(train_rows), chunk_size)
    ]
    chunk_records: list[dict[str, Any]] = []
    accepted = 0
    rejected = 0
    total_updates = 0
    for chunk_index, chunk in enumerate(chunks):
        validation_before = _phase38_migrated_provider_traces(
            cfg,
            validation_rows,
            provider,
            seed=int(seed) + chunk_index * 1000 + 1,
            policy_name=f"phase3_9_{rung_name}_validation_before_chunk_{chunk_index}",
            success_kind=success_kind,
        )
        prior_before = _phase39_eval_prior_replays(prior_replay_checks)
        slow_snapshot = _phase39_snapshot_provider_weights(provider)
        chunk_train = _phase39_apply_contrastive_fast_chunk(
            cfg,
            provider,
            chunk,
            seed=int(seed) + chunk_index * 1000 + 101,
            success_kind=success_kind,
        )
        total_updates += int(chunk_train["weight_update_count"])
        validation_after = _phase38_migrated_provider_traces(
            cfg,
            validation_rows,
            provider,
            seed=int(seed) + chunk_index * 1000 + 2,
            policy_name=f"phase3_9_{rung_name}_validation_after_chunk_{chunk_index}",
            success_kind=success_kind,
        )
        prior_after = _phase39_eval_prior_replays(prior_replay_checks)
        validation_delta = _phase39_eval_delta(validation_before, validation_after)
        prior_deltas = {
            name: _phase39_eval_delta(prior_before[name], prior_after[name])
            for name in prior_after
        }
        accepted_chunk = (
            int(validation_after["wins"]) >= int(validation_before["wins"])
            and all(int(after["wins"]) >= int(prior_before[name]["wins"]) for name, after in prior_after.items())
        )
        if accepted_chunk:
            accepted += 1
        else:
            rejected += 1
            _phase39_restore_provider_weights(provider, slow_snapshot)
        chunk_records.append(
            {
                "chunk_index": chunk_index,
                "row_count": len(chunk),
                "row_ids": [int(row["row_id"]) for row in chunk],
                "accepted": accepted_chunk,
                "reason": "non_regression_passed" if accepted_chunk else "validation_or_prior_replay_regressed",
                "training": chunk_train,
                "validation_delta": validation_delta,
                "prior_replay_deltas": prior_deltas,
            }
        )
    near_miss = _phase39_near_miss(chunk_records)
    return {
        "rung": rung_name,
        "success_kind": success_kind,
        "black_reply_policy": "exact_adversarial",
        "train_row_count": len(train_rows),
        "validation_row_count": len(validation_rows),
        "chunk_size": chunk_size,
        "chunk_count": len(chunks),
        "chunks_consolidated": accepted,
        "chunks_rejected": rejected,
        "weight_update_count": total_updates,
        "m3_m4_restored": True,
        "gate_heldout_consulted": False,
        "near_miss_margins": near_miss,
        "chunk_records": chunk_records,
    }


def _phase39_chunk_size(cfg: StageBEcologicalDiscoveryConfig) -> int:
    del cfg
    return 16


def _phase39_eval_prior_replays(prior_replay_checks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for check in prior_replay_checks:
        name = str(check["name"])
        evaluate = check["evaluate"]
        if not callable(evaluate):
            continue
        out[name] = evaluate()
    return out


def _phase39_snapshot_provider_weights(provider: _MigratedStageBFlatGraphScoreProvider) -> dict[str, float]:
    return {str(key): float(value) for key, value in provider.atom_weights.items()}


def _phase39_restore_provider_weights(
    provider: _MigratedStageBFlatGraphScoreProvider,
    snapshot: Mapping[str, float],
) -> None:
    for key, value in snapshot.items():
        provider.set_atom_weight(str(key), float(value))


def _phase39_apply_contrastive_fast_chunk(
    cfg: StageBEcologicalDiscoveryConfig,
    provider: _MigratedStageBFlatGraphScoreProvider,
    rows: Sequence[Mapping[str, Any]],
    *,
    seed: int,
    success_kind: str,
) -> dict[str, Any]:
    judge_cache = _new_judge_cache()
    endpoint_pairs: Counter[str] = Counter()
    selected_better = 0
    alternative_better = 0
    tied = 0
    update_count = 0
    samples: list[dict[str, Any]] = []
    learning_rate = 0.010
    for index, row in enumerate(rows):
        board = chess.Board(str(row["fen"]))
        counts: Counter[Any] = Counter({_position_repetition_key(board): 1, board._transposition_key(): 1})
        selected = _choose_migrated_flat_host_move(
            board,
            counts,
            score_provider=provider,
            seed=int(seed) + index,
        )
        legal = [move for move in _legal_without_third_repetition(board, counts) if move != selected]
        if not legal:
            legal = [move for move in sorted(board.legal_moves, key=lambda item: item.uci()) if move != selected]
        if selected is None or not legal:
            continue
        alternative = legal[(int(seed) + int(row["row_id"]) + index) % len(legal)]
        selected_out = _phase39_rollout_forced_first_move_provider(
            cfg,
            row,
            selected,
            provider,
            seed=int(seed) + index * 41,
            judge_cache=judge_cache,
            success_kind=success_kind,
        )
        alternative_out = _phase39_rollout_forced_first_move_provider(
            cfg,
            row,
            alternative,
            provider,
            seed=int(seed) + index * 41 + 17,
            judge_cache=judge_cache,
            success_kind=success_kind,
        )
        endpoint_pairs[f"{selected_out['endpoint']}|{alternative_out['endpoint']}"] += 1
        reward_delta = float(selected_out["reward"]) - float(alternative_out["reward"])
        if reward_delta > 0:
            selected_better += 1
        elif reward_delta < 0:
            alternative_better += 1
        else:
            tied += 1
            continue
        direction = 1.0 if reward_delta > 0 else -1.0
        scaled_lr = learning_rate * min(1.0, abs(reward_delta) / 12.0)
        selected_keys = _phase39_active_weighted_keys(provider, board, selected)
        alternative_keys = _phase39_active_weighted_keys(provider, board, alternative)
        for key in selected_keys:
            provider.adjust_atom_weight(key, direction * scaled_lr)
            update_count += 1
        for key in alternative_keys:
            provider.adjust_atom_weight(key, -direction * scaled_lr)
            update_count += 1
        if len(samples) < int(cfg.max_samples):
            samples.append(
                {
                    "row_id": int(row["row_id"]),
                    "selected": selected.uci(),
                    "alternative": alternative.uci(),
                    "selected_endpoint": selected_out["endpoint"],
                    "alternative_endpoint": alternative_out["endpoint"],
                    "reward_delta": round(reward_delta, 6),
                    "selected_weighted_key_count": len(selected_keys),
                    "alternative_weighted_key_count": len(alternative_keys),
                }
            )
    return {
        "row_count": len(rows),
        "learning_rate": learning_rate,
        "selected_better_count": selected_better,
        "alternative_better_count": alternative_better,
        "tied_count": tied,
        "weight_update_count": update_count,
        "endpoint_pair_counts": dict(sorted(endpoint_pairs.items())),
        "samples": samples,
    }


def _phase39_rollout_forced_first_move_provider(
    cfg: StageBEcologicalDiscoveryConfig,
    row: Mapping[str, Any],
    first_move: chess.Move,
    provider: _MigratedStageBFlatGraphScoreProvider,
    *,
    seed: int,
    judge_cache: tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]] | None,
    success_kind: str,
) -> dict[str, Any]:
    used = False

    def chooser(
        board: chess.Board,
        counts: Mapping[Any, int],
        row_id: int,
        ply: int,
        rng: random.Random,
    ) -> chess.Move | None:
        nonlocal used
        if not used:
            used = True
            return first_move if first_move in board.legal_moves else None
        del rng
        return _choose_migrated_flat_host_move(
            board,
            counts,
            score_provider=provider,
            seed=int(seed) + int(row_id) * 43 + int(ply),
        )

    return _rollout_policy(
        cfg,
        row,
        chooser,
        seed=int(seed),
        judge_cache=judge_cache,
        success_kind=success_kind,
        black_reply_policy="exact_adversarial",
    )


def _phase39_active_weighted_keys(
    provider: _MigratedStageBFlatGraphScoreProvider,
    board: chess.Board,
    move: chess.Move,
) -> tuple[str, ...]:
    return tuple(
        key
        for key, _scale in _sealed_action_key_scales(board, move)
        if key in provider.atom_weights
    )


def _phase39_eval_delta(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    endpoints = sorted(
        set(before.get("endpoint_counts", {}))
        | set(after.get("endpoint_counts", {}))
        | {"fence_broken", "rook_lost", "horizon", "third_repetition", "stalemate", "illegal"}
    )
    before_endpoints = before.get("endpoint_counts", {})
    after_endpoints = after.get("endpoint_counts", {})
    return {
        "before_wins": int(before["wins"]),
        "after_wins": int(after["wins"]),
        "delta_wins": int(after["wins"]) - int(before["wins"]),
        "endpoint_deltas": {
            endpoint: int(after_endpoints.get(endpoint, 0)) - int(before_endpoints.get(endpoint, 0))
            for endpoint in endpoints
        },
    }


def _phase39_near_miss(chunk_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not chunk_records:
        return {"best_validation_delta_wins": 0, "best_prior_delta_wins": 0}
    rejected = [record for record in chunk_records if not bool(record.get("accepted"))]
    pool = rejected or list(chunk_records)
    best_validation = max(int(record["validation_delta"]["delta_wins"]) for record in pool)
    best_prior = 0
    prior_values: list[int] = []
    for record in pool:
        for delta in record.get("prior_replay_deltas", {}).values():
            prior_values.append(int(delta["delta_wins"]))
    if prior_values:
        best_prior = max(prior_values)
    return {
        "best_validation_delta_wins": best_validation,
        "best_prior_delta_wins": best_prior,
        "rejected_chunk_count": len(rejected),
    }


def _phase39_gate_matrix_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    for row in per_seed:
        final_gate = (
            row.get("gate_matrix", {}).get("after_stage_b")
            or row.get("gate_matrix", {}).get("after_stage_a")
            or row.get("gate_matrix", {}).get("after_foundation", {})
        )
        foundation = final_gate.get("foundation") or {}
        stage_a = final_gate.get("stage_a_approach") or {}
        stage_b = final_gate.get("stage_b_chase") or {}
        table.append(
            {
                "seed": int(row["seed"]),
                "flat_seed": int(row["flat_seed"]),
                "foundation_pass": bool(foundation.get("passed", False)),
                "stage_a_pass": None if not stage_a else bool(stage_a.get("passed", False)),
                "stage_a_wins": None if not stage_a else int(stage_a.get("wins", 0)),
                "stage_a_baseline": None if not stage_a else int(stage_a.get("baseline_wins", 0)),
                "stage_b_pass": None if not stage_b else bool(stage_b.get("passed", False)),
                "stage_b_wins": None if not stage_b else int(stage_b.get("wins", 0)),
                "stage_b_baseline": None if not stage_b else int(stage_b.get("baseline_wins", 0)),
                "stop_reasons": list(row.get("stop_reasons", ())),
            }
        )
    return table


def _phase39_consolidation_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    for row in per_seed:
        stage_a = row.get("stage_a", {}).get("training", {})
        stage_b = row.get("stage_b", {}).get("training", {})
        table.append(
            {
                "seed": int(row["seed"]),
                "flat_seed": int(row["flat_seed"]),
                "stage_a_chunks_consolidated": int(stage_a.get("chunks_consolidated", 0)),
                "stage_a_chunks_rejected": int(stage_a.get("chunks_rejected", 0)),
                "stage_a_near_miss": dict(stage_a.get("near_miss_margins", {})),
                "stage_b_chunks_consolidated": None if not stage_b else int(stage_b.get("chunks_consolidated", 0)),
                "stage_b_chunks_rejected": None if not stage_b else int(stage_b.get("chunks_rejected", 0)),
                "stage_b_near_miss": None if not stage_b else dict(stage_b.get("near_miss_margins", {})),
            }
        )
    return table
