"""Persistent KRK staged ladder runners and stable plasticity probes."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
from itertools import combinations
import json
from pathlib import Path
import random
from typing import Any, Mapping, Sequence

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState

from .stage_b_ecological_discovery_probe import (
    StageBEcologicalDiscoveryConfig,
    _GraphNativeCompositeRuntime,
    _MigratedStageBFlatGraphScoreProvider,
    _NativeFoundationScoreProvider,
    _after_move_repetition_key,
    _approach_waypoint_success,
    _candidate_child_pool,
    _choose_migrated_flat_host_move,
    _decision_context,
    _design_spec,
    _foundation_ecology_rows,
    _generic_child_pool,
    _internal_triggers,
    _legal_without_third_repetition,
    _load_weight_table,
    _new_judge_cache,
    _phase32_real_recurring_mature_composites,
    _real_native_ablation_health,
    _real_native_composite_weight,
    _real_native_evaluate_policy,
    _real_native_parent_id,
    _real_native_pruned_rescue_audit,
    _real_native_spawn_from_context,
    _phase38_dispatcher_side_eval,
    _phase38_flat_policy_traces,
    _phase38_gate_result,
    _phase38_migrated_provider_traces,
    _phase38_provenance_law,
    _phase38_rebaseline_phase29e_discovery,
    _phase38_rebaseline_table,
    _phase38_runner_config,
    _percept_signature,
    _position_repetition_key,
    _rollout_policy,
    _rollout_success_check,
    _score_options,
    _sealed_action_key_scales,
    _select_black_reply_for_rollout,
    _train_native_foundation_for_ecology,
    _white_rook_square,
    fence_established_geometry,
    load_canonical_mate2_first_scorer,
    _write_json,
)

_PHASE40_HARD_ENDPOINTS = (
    "fence_broken",
    "rook_lost",
    "horizon",
    "third_repetition",
    "stalemate",
    "illegal",
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


def run_phase40_stratified_acceptance_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    """Phase 3.9/3.10 repair: stratified validation plus endpoint non-regression."""

    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_10_stratified_acceptance",
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
    design["schema_version"] = "phase3_10_stratified_acceptance_design_spec.v0"
    design["phase_alias"] = "stratified stable-plasticity acceptance repair"
    design["split_law"] = _phase39_split_law(cfg)
    design["consolidation"] = _phase40_consolidation_spec()
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
        foundation = _train_native_foundation_for_ecology(cfg)
        native_graph = foundation["graph"]
        stage_a_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir) / f"stage_d_A_sealed_seed_{flat_seed}_weights.json"
        )
        stage_b_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir) / f"stage_d_B_sealed_seed_{flat_seed}_weights.json"
        )
        stage_a_train_rows, stage_a_validation_rows, stage_a_split_diag = _phase40_stratified_train_validation_split(
            cfg,
            stage_a_train_pool,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 101,
            success_kind="approach_waypoint",
            policy_name=f"phase3_10_stage_a_train_pool_stratifier_{flat_seed}_{seed}",
        )
        stage_a_baseline = _phase38_flat_policy_traces(
            cfg,
            stage_a_gate_rows,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 700,
            policy_name=f"phase3_10_stage_a_executable_flat_exact_adversarial_{flat_seed}",
            success_kind="approach_waypoint",
        )
        foundation_gate = _phase39_foundation_gate(foundation, cfg)
        seed_result: dict[str, Any] = {
            "schema_version": "phase3_10_stratified_acceptance_seed.v0",
            "seed": int(seed),
            "flat_seed": flat_seed,
            "split_law": _phase39_split_law(cfg),
            "split_manifest": {
                "stage_a": _phase40_split_manifest(
                    stage_a_train_rows,
                    stage_a_validation_rows,
                    stage_a_gate_rows,
                    stage_a_split_diag,
                ),
                "stage_b": None,
            },
            "foundation": foundation["summary"],
            "baselines": {
                "stage_a_exact_adversarial_flat_gate": stage_a_baseline,
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
            _write_json(output_dir / f"seed_{seed}_stratified_acceptance.json", seed_result)
            per_seed.append(seed_result)
            continue

        stage_a_provider = _MigratedStageBFlatGraphScoreProvider(
            cfg,
            native_graph,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            policy_parent_id="stage_a_policy_stratified_acceptance",
            terminal_namespace=f"phase3_10_stage_a_{flat_seed}",
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
            endpoint_non_regression=True,
        )
        stage_a_gate_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_a_gate_rows,
            stage_a_provider,
            seed=int(seed) + 11_000,
            policy_name=f"phase3_10_stage_a_slow_host_gate_{seed}",
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
            _write_json(output_dir / f"seed_{seed}_stratified_acceptance.json", seed_result)
            per_seed.append(seed_result)
            continue

        stage_b_train_rows, stage_b_validation_rows, stage_b_split_diag = _phase40_stratified_train_validation_split(
            cfg,
            stage_b_train_pool,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 202,
            success_kind="stage_b_enter_mate2",
            policy_name=f"phase3_10_stage_b_train_pool_stratifier_{flat_seed}_{seed}",
        )
        seed_result["split_manifest"]["stage_b"] = _phase40_split_manifest(
            stage_b_train_rows,
            stage_b_validation_rows,
            stage_b_gate_rows,
            stage_b_split_diag,
        )
        stage_b_baseline = _phase38_flat_policy_traces(
            cfg,
            stage_b_gate_rows,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 900,
            policy_name=f"phase3_10_stage_b_executable_flat_exact_adversarial_{flat_seed}",
            success_kind="stage_b_enter_mate2",
        )
        seed_result["baselines"]["stage_b_exact_adversarial_flat_gate"] = stage_b_baseline
        stage_b_provider = _MigratedStageBFlatGraphScoreProvider(
            cfg,
            native_graph,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            policy_parent_id="stage_b_policy_stratified_acceptance",
            terminal_namespace=f"phase3_10_stage_b_{flat_seed}",
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
                policy_name=f"phase3_10_stage_a_validation_replay_for_stage_b_{seed}",
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
            endpoint_non_regression=True,
        )
        stage_b_gate_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_b_gate_rows,
            stage_b_provider,
            seed=int(seed) + 21_000,
            policy_name=f"phase3_10_stage_b_slow_host_gate_{seed}",
            success_kind="stage_b_enter_mate2",
        )
        stage_a_regression_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_a_gate_rows,
            stage_a_provider,
            seed=int(seed) + 22_000,
            policy_name=f"phase3_10_stage_a_regression_gate_after_stage_b_{seed}",
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
        _write_json(output_dir / f"seed_{seed}_stratified_acceptance.json", seed_result)
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
        "schema_version": "phase3_10_stratified_acceptance.v0",
        "phase": "stratified stable-plasticity acceptance repair",
        "config": asdict(cfg),
        "split_law": _phase39_split_law(cfg),
        "consolidation": _phase40_consolidation_spec(),
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
            "phase3_10_gate_matrix": _phase39_gate_matrix_table(per_seed),
            "phase3_10_consolidation": _phase39_consolidation_table(per_seed),
            "phase3_10_rebaseline_correction": _phase38_rebaseline_table(rebaseline),
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


def run_phase41_credit_precision_paired_gates_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    """Phase 3.9: recognizer-localized credit plus paired gates."""

    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_11_credit_precision_paired_gates",
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
    gate_margin = _phase41_gate_margin_wins()
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_11_credit_precision_paired_gates_design_spec.v0"
    design["phase_alias"] = "User-requested Phase 3.9 credit precision + honest gates"
    design["credit_precision"] = _phase41_credit_precision_spec()
    design["paired_gates"] = _phase41_paired_gate_spec(gate_margin)
    design["consolidation"] = _phase41_consolidation_spec()
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
    calibration = _phase41_calibrate_phase310_paired_gates(gate_margin)
    _write_json(output_dir / "phase2_9e_rebaseline_audit.json", rebaseline)
    _write_json(output_dir / "phase3_10_paired_gate_calibration.json", calibration)

    per_seed: list[dict[str, Any]] = []
    for index, seed in enumerate(cfg.seeds):
        flat_seed = int(cfg.flat_baseline_seeds[index % len(cfg.flat_baseline_seeds)])
        foundation = _train_native_foundation_for_ecology(cfg)
        native_graph = foundation["graph"]
        stage_a_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir) / f"stage_d_A_sealed_seed_{flat_seed}_weights.json"
        )
        stage_b_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir) / f"stage_d_B_sealed_seed_{flat_seed}_weights.json"
        )
        stage_a_pool_traces = _phase38_flat_policy_traces(
            cfg,
            stage_a_train_pool,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 404,
            policy_name=f"phase3_11_stage_a_train_pool_stratifier_{flat_seed}_{seed}",
            success_kind="approach_waypoint",
        )
        stage_a_baseline = _phase38_flat_policy_traces(
            cfg,
            stage_a_gate_rows,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 700,
            policy_name=f"phase3_11_stage_a_executable_flat_exact_adversarial_{flat_seed}",
            success_kind="approach_waypoint",
        )
        foundation_gate = _phase39_foundation_gate(foundation, cfg)
        seed_result: dict[str, Any] = {
            "schema_version": "phase3_11_credit_precision_paired_gates_seed.v0",
            "seed": int(seed),
            "flat_seed": flat_seed,
            "credit_precision": _phase41_credit_precision_spec(),
            "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
            "split_manifest": {
                "stage_a": _phase41_pool_manifest(stage_a_train_pool, stage_a_gate_rows, stage_a_pool_traces),
                "stage_b": None,
            },
            "foundation": foundation["summary"],
            "baselines": {
                "stage_a_exact_adversarial_flat_gate": stage_a_baseline,
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
            _write_json(output_dir / f"seed_{seed}_credit_precision.json", seed_result)
            per_seed.append(seed_result)
            continue

        stage_a_provider = _MigratedStageBFlatGraphScoreProvider(
            cfg,
            native_graph,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            policy_parent_id="stage_a_policy_credit_precision",
            terminal_namespace=f"phase3_11_stage_a_{flat_seed}",
        )
        stage_a_training = _phase41_train_credit_precision(
            cfg,
            provider=stage_a_provider,
            train_pool_rows=stage_a_train_pool,
            pool_endpoint_by_row=stage_a_pool_traces["endpoint_by_row"],
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
            policy_name=f"phase3_11_stage_a_slow_host_gate_{seed}",
            success_kind="approach_waypoint",
        )
        stage_a_gate = _phase41_gate_result_paired(
            rung="stage_a_approach",
            learner=stage_a_gate_eval,
            flat=stage_a_baseline,
            margin_wins=gate_margin,
        )
        seed_result["stage_a"] = {
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
            _write_json(output_dir / f"seed_{seed}_credit_precision.json", seed_result)
            per_seed.append(seed_result)
            continue

        stage_b_pool_traces = _phase38_flat_policy_traces(
            cfg,
            stage_b_train_pool,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 504,
            policy_name=f"phase3_11_stage_b_train_pool_stratifier_{flat_seed}_{seed}",
            success_kind="stage_b_enter_mate2",
        )
        seed_result["split_manifest"]["stage_b"] = _phase41_pool_manifest(
            stage_b_train_pool,
            stage_b_gate_rows,
            stage_b_pool_traces,
        )
        stage_b_baseline = _phase38_flat_policy_traces(
            cfg,
            stage_b_gate_rows,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 900,
            policy_name=f"phase3_11_stage_b_executable_flat_exact_adversarial_{flat_seed}",
            success_kind="stage_b_enter_mate2",
        )
        seed_result["baselines"]["stage_b_exact_adversarial_flat_gate"] = stage_b_baseline
        stage_b_provider = _MigratedStageBFlatGraphScoreProvider(
            cfg,
            native_graph,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            policy_parent_id="stage_b_policy_credit_precision",
            terminal_namespace=f"phase3_11_stage_b_{flat_seed}",
        )
        stage_a_replay_rows = _phase41_stratified_fold_from_endpoint_map(
            stage_a_train_pool,
            stage_a_pool_traces["endpoint_by_row"],
            seed=int(seed) + 60_000,
            excluded_row_ids=set(),
            target_count=_phase41_validation_target_count(stage_a_train_pool),
        )[0]

        def stage_a_prior_replay() -> dict[str, Any]:
            return _phase38_migrated_provider_traces(
                cfg,
                stage_a_replay_rows,
                stage_a_provider,
                seed=int(seed) + 12_000,
                policy_name=f"phase3_11_stage_a_replay_for_stage_b_{seed}",
                success_kind="approach_waypoint",
            )

        stage_b_training = _phase41_train_credit_precision(
            cfg,
            provider=stage_b_provider,
            train_pool_rows=stage_b_train_pool,
            pool_endpoint_by_row=stage_b_pool_traces["endpoint_by_row"],
            prior_replay_checks=(
                {
                    "name": "stage_a_replay",
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
            policy_name=f"phase3_11_stage_b_slow_host_gate_{seed}",
            success_kind="stage_b_enter_mate2",
        )
        stage_a_regression_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_a_gate_rows,
            stage_a_provider,
            seed=int(seed) + 22_000,
            policy_name=f"phase3_11_stage_a_regression_gate_after_stage_b_{seed}",
            success_kind="approach_waypoint",
        )
        stage_b_gate = _phase41_gate_result_paired(
            rung="stage_b_chase",
            learner=stage_b_gate_eval,
            flat=stage_b_baseline,
            margin_wins=gate_margin,
        )
        stage_a_regression_gate = _phase41_gate_result_paired(
            rung="stage_a_approach_regression",
            learner=stage_a_regression_eval,
            flat=stage_a_baseline,
            margin_wins=gate_margin,
        )
        seed_result["stage_b"] = {
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
        _write_json(output_dir / f"seed_{seed}_credit_precision.json", seed_result)
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
        "schema_version": "phase3_11_credit_precision_paired_gates.v0",
        "phase": "User-requested Phase 3.9 credit precision + honest gates",
        "config": asdict(cfg),
        "credit_precision": _phase41_credit_precision_spec(),
        "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
        "consolidation": _phase41_consolidation_spec(),
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
        "phase3_10_paired_gate_calibration": calibration,
        "rebaseline_audit": rebaseline,
        "per_seed": per_seed,
        "dispatcher_side_eval": dispatcher_side_eval,
        "tables": {
            "phase3_11_gate_matrix": _phase39_gate_matrix_table(per_seed),
            "phase3_11_paired_gates": _phase41_paired_gate_table(per_seed),
            "phase3_11_consolidation": _phase39_consolidation_table(per_seed),
            "phase3_11_flip_ply": _phase41_flip_ply_table(per_seed),
            "phase3_11_rebaseline_correction": _phase38_rebaseline_table(rebaseline),
        },
        "decision": {
            "ecology_deferred": True,
            "standing_ladder_all_seeds_green": standing_ladder,
            "run_ecology_next": standing_ladder,
            "stage_a_paired_passing_seed_count": sum(
                int(bool(row.get("stage_a", {}).get("gate", {}).get("passed")))
                for row in per_seed
            ),
            "stop_reasons_by_seed": {
                str(row["seed"]): list(row.get("stop_reasons", ())) for row in per_seed
            },
        },
    }
    _write_json(output_dir / "summary.json", summary)
    return summary


def run_phase42_standing_ladder_ecology_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    """Phase 3.12: graph-native stem-cell ecology on the standing 3.9 ladder."""

    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_12_standing_ladder_ecology",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
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
        real_native_max_live_composites=32,
        real_native_max_live_siblings_per_parent=4,
        real_native_trial_grace_exposures=3,
        real_native_critical_period_exposures=5,
        real_native_critical_period_credit_multiplier=1.75,
        real_native_critical_period_optimism=0.025,
        real_native_positive_flip_credit=0.060,
        real_native_positive_flip_window=2,
    )
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    gate_margin = _phase41_gate_margin_wins()
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_12_standing_ladder_ecology_design_spec.v0"
    design["phase_alias"] = "User-requested Phase 3.12 ecology on the standing ladder"
    design["host_ladder"] = {
        "base_commit": "67edd64",
        "consolidation_and_paired_gate": _phase41_consolidation_spec(),
        "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
        "exact_adversarial_black": True,
    }
    design["ecology"] = _phase42_ecology_spec(cfg)
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

    calibration = _phase41_calibrate_phase310_paired_gates(gate_margin)
    _write_json(output_dir / "phase3_10_paired_gate_calibration.json", calibration)

    per_seed: list[dict[str, Any]] = []
    global_stop_reasons: list[str] = []

    for index, seed in enumerate(cfg.seeds):
        flat_seed = int(cfg.flat_baseline_seeds[index % len(cfg.flat_baseline_seeds)])
        foundation = _train_native_foundation_for_ecology(cfg)
        native_graph = foundation["graph"]
        runtime = _GraphNativeCompositeRuntime(cfg, native_graph, seed=int(seed))
        foundation_rows = _foundation_ecology_rows(cfg, seed=int(seed))
        acceptance_row = foundation_rows[0] if foundation_rows else stage_a_train_pool[0]
        acceptance = runtime.acceptance_check(acceptance_row)
        foundation_gate = _phase39_foundation_gate(foundation, cfg)
        stage_a_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir) / f"stage_d_A_sealed_seed_{flat_seed}_weights.json"
        )
        stage_b_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir) / f"stage_d_B_sealed_seed_{flat_seed}_weights.json"
        )
        stage_a_pool_traces = _phase38_flat_policy_traces(
            cfg,
            stage_a_train_pool,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 404,
            policy_name=f"phase3_12_stage_a_train_pool_stratifier_{flat_seed}_{seed}",
            success_kind="approach_waypoint",
        )
        stage_a_baseline = _phase38_flat_policy_traces(
            cfg,
            stage_a_gate_rows,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 700,
            policy_name=f"phase3_12_stage_a_executable_flat_exact_adversarial_{flat_seed}",
            success_kind="approach_waypoint",
        )
        seed_result: dict[str, Any] = {
            "schema_version": "phase3_12_standing_ladder_ecology_seed.v0",
            "seed": int(seed),
            "flat_seed": flat_seed,
            "acceptance_check": acceptance,
            "foundation": foundation["summary"],
            "foundation_gate": foundation_gate,
            "ecology_spec": _phase42_ecology_spec(cfg),
            "split_manifest": {
                "stage_a": _phase41_pool_manifest(stage_a_train_pool, stage_a_gate_rows, stage_a_pool_traces),
                "stage_b": None,
            },
            "baselines": {
                "stage_a_exact_adversarial_flat_gate": stage_a_baseline,
            },
            "stop_reasons": [],
        }
        if not acceptance["passed"]:
            seed_result["stop_reasons"].append("acceptance_check_failed")
        if not foundation_gate["passed"]:
            seed_result["stop_reasons"].append("foundation_gate_failed")
        if seed_result["stop_reasons"]:
            _write_json(output_dir / f"seed_{seed}_standing_ladder_ecology.json", seed_result)
            per_seed.append(seed_result)
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
            continue

        foundation_provider = _NativeFoundationScoreProvider(native_graph)
        seed_result["foundation_ecology_training"] = _phase42_train_ecology_segment(
            cfg,
            runtime=runtime,
            score_provider=foundation_provider,
            rows=foundation_rows,
            segment_name="foundation_mate1_mate2",
            success_kind="stage_b_enter_mate2",
            seed=int(seed) + 3_000,
            step_offset=0,
        )

        stage_a_provider = _MigratedStageBFlatGraphScoreProvider(
            cfg,
            native_graph,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            policy_parent_id="stage_a_policy_phase3_12",
            terminal_namespace=f"phase3_12_stage_a_{flat_seed}",
        )
        stage_a_training = _phase41_train_credit_precision(
            cfg,
            provider=stage_a_provider,
            train_pool_rows=stage_a_train_pool,
            pool_endpoint_by_row=stage_a_pool_traces["endpoint_by_row"],
            prior_replay_checks=(),
            seed=int(seed) + 10_000,
            success_kind="approach_waypoint",
            rung_name="stage_a_approach",
        )
        stage_a_host_gate_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_a_gate_rows,
            stage_a_provider,
            seed=int(seed) + 11_000,
            policy_name=f"phase3_12_stage_a_host_gate_{seed}",
            success_kind="approach_waypoint",
        )
        stage_a_host_gate = _phase41_gate_result_paired(
            rung="stage_a_approach_host",
            learner=stage_a_host_gate_eval,
            flat=stage_a_baseline,
            margin_wins=gate_margin,
        )
        seed_result["stage_a"] = {
            "host_training": stage_a_training,
            "host_gate_evaluation": stage_a_host_gate_eval,
            "host_gate": stage_a_host_gate,
        }
        if int(stage_a_training["chunks_consolidated"]) == 0:
            seed_result["stop_reasons"].append("stage_a_zero_chunks_consolidated")
        if not stage_a_host_gate["passed"]:
            seed_result["stop_reasons"].append("stage_a_host_gate_unreachable_after_budget")
        if seed_result["stop_reasons"]:
            _write_json(output_dir / f"seed_{seed}_standing_ladder_ecology.json", seed_result)
            per_seed.append(seed_result)
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
            continue

        seed_result["stage_a"]["ecology_training"] = _phase42_train_ecology_segment(
            cfg,
            runtime=runtime,
            score_provider=stage_a_provider,
            rows=stage_a_train_pool,
            segment_name="stage_a_approach",
            success_kind="approach_waypoint",
            seed=int(seed) + 12_000,
            step_offset=10_000,
        )
        stage_a_ecology_gates = _phase42_ecology_gate_bundle(
            cfg,
            runtime=runtime,
            score_provider=stage_a_provider,
            gate_rows=stage_a_gate_rows,
            flat_baseline=stage_a_baseline,
            host_eval=stage_a_host_gate_eval,
            seed=int(seed) + 13_000,
            rung="stage_a_approach",
            success_kind="approach_waypoint",
            gate_margin=gate_margin,
        )
        seed_result["stage_a"]["ecology_gates"] = stage_a_ecology_gates
        if not stage_a_ecology_gates["mature_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_a_mature_cell_gate_regression_vs_flat")
        if not stage_a_ecology_gates["live_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_a_live_cell_gate_regression_vs_flat")
        population_stop = runtime.population_stop_rule()
        if population_stop["population_collapse_to_zero"] or population_stop["unbounded_explosion"]:
            seed_result["stop_reasons"].append("population_stop_after_stage_a")
        if seed_result["stop_reasons"]:
            seed_result["population"] = runtime.population_summary()
            seed_result["birth_death_curve"] = runtime.birth_curve
            seed_result["candidate_fate_log"] = runtime.fate_log()
            _write_json(output_dir / f"seed_{seed}_standing_ladder_ecology.json", seed_result)
            per_seed.append(seed_result)
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
            if (
                "population_stop_after_stage_a" in seed_result["stop_reasons"]
                or any("gate_regression" in reason for reason in seed_result["stop_reasons"])
            ):
                break
            continue

        stage_b_pool_traces = _phase38_flat_policy_traces(
            cfg,
            stage_b_train_pool,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 504,
            policy_name=f"phase3_12_stage_b_train_pool_stratifier_{flat_seed}_{seed}",
            success_kind="stage_b_enter_mate2",
        )
        seed_result["split_manifest"]["stage_b"] = _phase41_pool_manifest(
            stage_b_train_pool,
            stage_b_gate_rows,
            stage_b_pool_traces,
        )
        stage_b_baseline = _phase38_flat_policy_traces(
            cfg,
            stage_b_gate_rows,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 900,
            policy_name=f"phase3_12_stage_b_executable_flat_exact_adversarial_{flat_seed}",
            success_kind="stage_b_enter_mate2",
        )
        seed_result["baselines"]["stage_b_exact_adversarial_flat_gate"] = stage_b_baseline
        stage_b_provider = _MigratedStageBFlatGraphScoreProvider(
            cfg,
            native_graph,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            policy_parent_id="stage_b_policy_phase3_12",
            terminal_namespace=f"phase3_12_stage_b_{flat_seed}",
        )
        stage_a_replay_rows = _phase41_stratified_fold_from_endpoint_map(
            stage_a_train_pool,
            stage_a_pool_traces["endpoint_by_row"],
            seed=int(seed) + 60_000,
            excluded_row_ids=set(),
            target_count=_phase41_validation_target_count(stage_a_train_pool),
        )[0]

        def stage_a_prior_replay() -> dict[str, Any]:
            return _phase38_migrated_provider_traces(
                cfg,
                stage_a_replay_rows,
                stage_a_provider,
                seed=int(seed) + 14_000,
                policy_name=f"phase3_12_stage_a_replay_for_stage_b_{seed}",
                success_kind="approach_waypoint",
            )

        stage_b_training = _phase41_train_credit_precision(
            cfg,
            provider=stage_b_provider,
            train_pool_rows=stage_b_train_pool,
            pool_endpoint_by_row=stage_b_pool_traces["endpoint_by_row"],
            prior_replay_checks=(
                {
                    "name": "stage_a_replay",
                    "evaluate": stage_a_prior_replay,
                },
            ),
            seed=int(seed) + 20_000,
            success_kind="stage_b_enter_mate2",
            rung_name="stage_b_chase",
        )
        stage_b_host_gate_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_b_gate_rows,
            stage_b_provider,
            seed=int(seed) + 21_000,
            policy_name=f"phase3_12_stage_b_host_gate_{seed}",
            success_kind="stage_b_enter_mate2",
        )
        stage_a_regression_host_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_a_gate_rows,
            stage_a_provider,
            seed=int(seed) + 22_000,
            policy_name=f"phase3_12_stage_a_host_regression_after_stage_b_{seed}",
            success_kind="approach_waypoint",
        )
        stage_b_host_gate = _phase41_gate_result_paired(
            rung="stage_b_chase_host",
            learner=stage_b_host_gate_eval,
            flat=stage_b_baseline,
            margin_wins=gate_margin,
        )
        stage_a_host_regression_gate = _phase41_gate_result_paired(
            rung="stage_a_approach_host_regression_after_stage_b",
            learner=stage_a_regression_host_eval,
            flat=stage_a_baseline,
            margin_wins=gate_margin,
        )
        seed_result["stage_b"] = {
            "host_training": stage_b_training,
            "host_gate_evaluation": stage_b_host_gate_eval,
            "host_gate": stage_b_host_gate,
        }
        seed_result["regression_checks"] = {
            "stage_a_host_after_stage_b": {
                "gate_evaluation": stage_a_regression_host_eval,
                "gate": stage_a_host_regression_gate,
            }
        }
        if int(stage_b_training["chunks_consolidated"]) == 0:
            seed_result["stop_reasons"].append("stage_b_zero_chunks_consolidated")
        if not stage_b_host_gate["passed"]:
            seed_result["stop_reasons"].append("stage_b_host_gate_unreachable_after_budget")
        if not stage_a_host_regression_gate["passed"]:
            seed_result["stop_reasons"].append("stage_a_host_regression_after_stage_b")
        if seed_result["stop_reasons"]:
            seed_result["population"] = runtime.population_summary()
            seed_result["birth_death_curve"] = runtime.birth_curve
            seed_result["candidate_fate_log"] = runtime.fate_log()
            _write_json(output_dir / f"seed_{seed}_standing_ladder_ecology.json", seed_result)
            per_seed.append(seed_result)
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
            continue

        seed_result["stage_b"]["ecology_training"] = _phase42_train_ecology_segment(
            cfg,
            runtime=runtime,
            score_provider=stage_b_provider,
            rows=stage_b_train_pool,
            segment_name="stage_b_chase",
            success_kind="stage_b_enter_mate2",
            seed=int(seed) + 23_000,
            step_offset=20_000,
        )
        stage_b_ecology_gates = _phase42_ecology_gate_bundle(
            cfg,
            runtime=runtime,
            score_provider=stage_b_provider,
            gate_rows=stage_b_gate_rows,
            flat_baseline=stage_b_baseline,
            host_eval=stage_b_host_gate_eval,
            seed=int(seed) + 24_000,
            rung="stage_b_chase",
            success_kind="stage_b_enter_mate2",
            gate_margin=gate_margin,
        )
        stage_a_ecology_regression_gates = _phase42_ecology_gate_bundle(
            cfg,
            runtime=runtime,
            score_provider=stage_a_provider,
            gate_rows=stage_a_gate_rows,
            flat_baseline=stage_a_baseline,
            host_eval=stage_a_regression_host_eval,
            seed=int(seed) + 25_000,
            rung="stage_a_approach_regression_after_stage_b",
            success_kind="approach_waypoint",
            gate_margin=gate_margin,
        )
        stage_b_mature_eval = stage_b_ecology_gates["mature_eval"]
        noop_control = None
        if bool(getattr(cfg, "real_native_noop_ablation_control_enabled", False)):
            noop_control = _phase49_noop_ablation_control_old_pipeline(
                cfg,
                stage_b_gate_rows,
                runtime,
                stage_b_provider,
                full_eval=stage_b_mature_eval,
                seed=int(seed) + 30_000,
            )
        if bool(getattr(cfg, "real_native_controlled_ablation_enabled", False)):
            ablation = _phase49_controlled_ablation_health(
                cfg,
                stage_b_gate_rows,
                runtime,
                stage_b_provider,
                full_eval=stage_b_mature_eval,
                seed=int(seed) + 24_000,
                success_kind="stage_b_enter_mate2",
            )
        else:
            ablation = _real_native_ablation_health(
                cfg,
                stage_b_gate_rows,
                runtime,
                stage_b_provider,
                full_eval=stage_b_mature_eval,
                seed=int(seed) + 30_000,
            )
        rescue = _real_native_pruned_rescue_audit(
            cfg,
            stage_b_gate_rows,
            runtime,
            stage_b_provider,
            full_eval=stage_b_mature_eval,
            seed=int(seed) + 40_000,
        )
        seed_result["stage_b"]["ecology_gates"] = stage_b_ecology_gates
        seed_result["regression_checks"]["stage_a_ecology_after_stage_b"] = stage_a_ecology_regression_gates
        seed_result["post_hoc_ablation"] = ablation
        if noop_control is not None:
            seed_result["noop_ablation_control"] = noop_control
        seed_result["pruned_rescue_audit"] = rescue
        seed_result["population"] = runtime.population_summary()
        seed_result["birth_death_curve"] = runtime.birth_curve
        seed_result["candidate_fate_log"] = runtime.fate_log()
        seed_result["runtime_instrumentation"] = runtime.instrumentation_summary(stage_b_provider)
        seed_result["host_instrumentation"] = {
            "stage_a": stage_a_provider.stats(),
            "stage_b": stage_b_provider.stats(),
        }
        population_stop = runtime.population_stop_rule()
        seed_result["population_stop"] = population_stop
        if population_stop["population_collapse_to_zero"] or population_stop["unbounded_explosion"]:
            seed_result["stop_reasons"].append("population_stop_after_stage_b")
        if not stage_b_ecology_gates["mature_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_b_mature_cell_gate_regression_vs_flat")
        if not stage_b_ecology_gates["live_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_b_live_cell_gate_regression_vs_flat")
        if not stage_a_ecology_regression_gates["mature_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_a_mature_cell_regression_after_stage_b")
        if not stage_a_ecology_regression_gates["live_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_a_live_cell_regression_after_stage_b")
        if seed_result["stop_reasons"]:
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
        _write_json(output_dir / f"seed_{seed}_standing_ladder_ecology.json", seed_result)
        per_seed.append(seed_result)
        if (
            population_stop["population_collapse_to_zero"]
            or population_stop["unbounded_explosion"]
            or any("gate_regression" in reason or "regression_after_stage_b" in reason for reason in seed_result["stop_reasons"])
        ):
            break

    seed_results = {str(row["seed"]): row for row in per_seed}
    recurrence = _phase32_real_recurring_mature_composites(seed_results)
    cross_rung = _phase42_cross_rung_load_bearing_survivors(seed_results)
    summary = {
        "schema_version": "phase3_12_standing_ladder_ecology.v0",
        "phase": "Phase 3.12 ecology on the standing persistent ladder",
        "config": asdict(cfg),
        "dataset": {
            "recent_curriculum_only_for_stage_a_b": True,
            "old_krk_curriculum_imported_for_stage_a_b": False,
            "foundation_row_count_per_seed": int(cfg.real_native_foundation_row_limit),
            "stage_a_train_pool_count": len(stage_a_train_pool),
            "stage_b_train_pool_count": len(stage_b_train_pool),
            "stage_a_gate_heldout_count": len(stage_a_gate_rows),
            "stage_b_gate_heldout_count": len(stage_b_gate_rows),
            "gate_rows_consulted_by_update_decisions": False,
        },
        "host_ladder": {
            "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
            "consolidation": _phase41_consolidation_spec(),
        },
        "ecology": _phase42_ecology_spec(cfg),
        "phase3_10_paired_gate_calibration": calibration,
        "per_seed": per_seed,
        "cross_seed_recurring_mature_composites": recurrence,
        "cross_rung_load_bearing_survivors": cross_rung,
        "tables": {
            "phase3_12_headline": _phase42_headline_table(per_seed),
            "phase3_12_acceptance_margins": _phase42_acceptance_margin_table(per_seed),
            "phase3_12_mature_recurrence": recurrence,
            "phase3_12_cross_rung_survivors": cross_rung,
        },
        "decision": {
            "stop_reasons": global_stop_reasons,
            "population_stop": any("population_stop" in reason for reason in global_stop_reasons),
            "gate_regression_stop": any("gate_regression" in reason or "regression_after_stage_b" in reason for reason in global_stop_reasons),
            "mature_population_formed_any_seed": any(
                int(row.get("population", {}).get("mature_count", 0)) > 0 for row in per_seed
            ),
            "helpful_pruned_total": sum(
                int(row.get("pruned_rescue_audit", {}).get("load_bearing_but_pruned_count", 0))
                for row in per_seed
            ),
            "cross_rung_survivor_count": len(cross_rung),
            "recurring_mature_composite_count": sum(1 for row in recurrence if int(row.get("seed_count", 0)) > 1),
        },
    }
    _write_json(output_dir / "summary.json", summary)
    return summary


def run_phase43_discriminative_cell_economy_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    """Phase 3.13: counterfactual per-ply attribution for ecological cells."""

    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_13_discriminative_cell_economy",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
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
        real_native_max_live_composites=32,
        real_native_max_live_siblings_per_parent=4,
        real_native_trial_grace_exposures=3,
        real_native_dormant_decay=0.002,
        real_native_critical_period_exposures=5,
        real_native_critical_period_credit_multiplier=1.75,
        real_native_critical_period_optimism=0.025,
        real_native_positive_flip_credit=0.060,
        real_native_positive_flip_window=2,
        real_native_choice_change_mature_events=3,
        real_native_choice_change_neutral_rent=0.006,
        real_native_near_zero_choice_change_rate=0.01,
        real_native_stability_band_multiplier=5,
    )
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    gate_margin = _phase41_gate_margin_wins()
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_13_discriminative_cell_economy_design_spec.v0"
    design["phase_alias"] = "User-requested Phase 3.13 discriminative cell economy"
    design["host_ladder"] = {
        "base_commit": "54dc268",
        "frozen_from": "Phase 3.12/3.9 ladder, gates, ratchet, spawn triggers, and learner-visible boundary",
        "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
    }
    design["ecology"] = _phase43_ecology_spec(cfg)
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

    calibration = _phase41_calibrate_phase310_paired_gates(gate_margin)
    _write_json(output_dir / "phase3_10_paired_gate_calibration.json", calibration)

    per_seed: list[dict[str, Any]] = []
    global_stop_reasons: list[str] = []

    for index, seed in enumerate(cfg.seeds):
        flat_seed = int(cfg.flat_baseline_seeds[index % len(cfg.flat_baseline_seeds)])
        foundation = _train_native_foundation_for_ecology(cfg)
        native_graph = foundation["graph"]
        runtime = _GraphNativeCompositeRuntime(cfg, native_graph, seed=int(seed))
        foundation_rows = _foundation_ecology_rows(cfg, seed=int(seed))
        acceptance_row = foundation_rows[0] if foundation_rows else stage_a_train_pool[0]
        acceptance = runtime.acceptance_check(acceptance_row)
        foundation_gate = _phase39_foundation_gate(foundation, cfg)
        stage_a_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir) / f"stage_d_A_sealed_seed_{flat_seed}_weights.json"
        )
        stage_b_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir) / f"stage_d_B_sealed_seed_{flat_seed}_weights.json"
        )
        stage_a_pool_traces = _phase38_flat_policy_traces(
            cfg,
            stage_a_train_pool,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 404,
            policy_name=f"phase3_13_stage_a_train_pool_stratifier_{flat_seed}_{seed}",
            success_kind="approach_waypoint",
        )
        stage_a_baseline = _phase38_flat_policy_traces(
            cfg,
            stage_a_gate_rows,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 700,
            policy_name=f"phase3_13_stage_a_executable_flat_exact_adversarial_{flat_seed}",
            success_kind="approach_waypoint",
        )
        seed_result: dict[str, Any] = {
            "schema_version": "phase3_13_discriminative_cell_economy_seed.v0",
            "seed": int(seed),
            "flat_seed": flat_seed,
            "acceptance_check": acceptance,
            "foundation": foundation["summary"],
            "foundation_gate": foundation_gate,
            "ecology_spec": _phase43_ecology_spec(cfg),
            "split_manifest": {
                "stage_a": _phase41_pool_manifest(stage_a_train_pool, stage_a_gate_rows, stage_a_pool_traces),
                "stage_b": None,
            },
            "baselines": {
                "stage_a_exact_adversarial_flat_gate": stage_a_baseline,
            },
            "stop_reasons": [],
        }
        if not acceptance["passed"]:
            seed_result["stop_reasons"].append("acceptance_check_failed")
        if not foundation_gate["passed"]:
            seed_result["stop_reasons"].append("foundation_gate_failed")
        if seed_result["stop_reasons"]:
            _write_json(output_dir / f"seed_{seed}_discriminative_cell_economy.json", seed_result)
            per_seed.append(seed_result)
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
            continue

        foundation_provider = _NativeFoundationScoreProvider(native_graph)
        seed_result["foundation_ecology_training"] = _phase43_train_discriminative_ecology_segment(
            cfg,
            runtime=runtime,
            score_provider=foundation_provider,
            rows=foundation_rows,
            segment_name="foundation_mate1_mate2",
            success_kind="stage_b_enter_mate2",
            seed=int(seed) + 3_000,
            step_offset=0,
        )

        stage_a_provider = _MigratedStageBFlatGraphScoreProvider(
            cfg,
            native_graph,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            policy_parent_id="stage_a_policy_phase3_13",
            terminal_namespace=f"phase3_13_stage_a_{flat_seed}",
        )
        stage_a_training = _phase41_train_credit_precision(
            cfg,
            provider=stage_a_provider,
            train_pool_rows=stage_a_train_pool,
            pool_endpoint_by_row=stage_a_pool_traces["endpoint_by_row"],
            prior_replay_checks=(),
            seed=int(seed) + 10_000,
            success_kind="approach_waypoint",
            rung_name="stage_a_approach",
        )
        stage_a_host_gate_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_a_gate_rows,
            stage_a_provider,
            seed=int(seed) + 11_000,
            policy_name=f"phase3_13_stage_a_host_gate_{seed}",
            success_kind="approach_waypoint",
        )
        stage_a_host_gate = _phase41_gate_result_paired(
            rung="stage_a_approach_host",
            learner=stage_a_host_gate_eval,
            flat=stage_a_baseline,
            margin_wins=gate_margin,
        )
        seed_result["stage_a"] = {
            "host_training": stage_a_training,
            "host_gate_evaluation": stage_a_host_gate_eval,
            "host_gate": stage_a_host_gate,
        }
        if int(stage_a_training["chunks_consolidated"]) == 0:
            seed_result["stop_reasons"].append("stage_a_zero_chunks_consolidated")
        if not stage_a_host_gate["passed"]:
            seed_result["stop_reasons"].append("stage_a_host_gate_unreachable_after_budget")
        if seed_result["stop_reasons"]:
            _write_json(output_dir / f"seed_{seed}_discriminative_cell_economy.json", seed_result)
            per_seed.append(seed_result)
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
            continue

        seed_result["stage_a"]["ecology_training"] = _phase43_train_discriminative_ecology_segment(
            cfg,
            runtime=runtime,
            score_provider=stage_a_provider,
            rows=stage_a_train_pool,
            segment_name="stage_a_approach",
            success_kind="approach_waypoint",
            seed=int(seed) + 12_000,
            step_offset=10_000,
        )
        stage_a_ecology_gates = _phase42_ecology_gate_bundle(
            cfg,
            runtime=runtime,
            score_provider=stage_a_provider,
            gate_rows=stage_a_gate_rows,
            flat_baseline=stage_a_baseline,
            host_eval=stage_a_host_gate_eval,
            seed=int(seed) + 13_000,
            rung="stage_a_approach",
            success_kind="approach_waypoint",
            gate_margin=gate_margin,
        )
        seed_result["stage_a"]["ecology_gates"] = stage_a_ecology_gates
        stage_a_stability = _phase43_population_stability(
            cfg,
            runtime.birth_curve,
            segment="stage_a_approach",
        )
        seed_result["stage_a"]["population_stability"] = stage_a_stability
        if not stage_a_ecology_gates["mature_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_a_mature_cell_gate_regression_vs_flat")
        if not stage_a_ecology_gates["live_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_a_live_cell_gate_regression_vs_flat")
        population_stop = _phase43_population_stop_rule(cfg, runtime)
        if population_stop["population_collapse_to_zero"] or population_stop["unbounded_explosion"]:
            seed_result["stop_reasons"].append("population_stop_after_stage_a")
        if not stage_a_stability["stable"]:
            seed_result["stop_reasons"].append("population_unstable_after_stage_a")
        if _phase43_choice_change_rate(seed_result["stage_a"]["ecology_training"]) < float(cfg.real_native_near_zero_choice_change_rate):
            seed_result["stop_reasons"].append("near_zero_choice_changing_plies_after_stage_a")
        if seed_result["stop_reasons"]:
            seed_result["population"] = runtime.population_summary()
            seed_result["birth_death_curve"] = runtime.birth_curve
            seed_result["candidate_fate_log"] = runtime.fate_log()
            _write_json(output_dir / f"seed_{seed}_discriminative_cell_economy.json", seed_result)
            per_seed.append(seed_result)
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
            if (
                any("population" in reason for reason in seed_result["stop_reasons"])
                or any("gate_regression" in reason for reason in seed_result["stop_reasons"])
                or any("near_zero_choice" in reason for reason in seed_result["stop_reasons"])
            ):
                break
            continue

        stage_b_pool_traces = _phase38_flat_policy_traces(
            cfg,
            stage_b_train_pool,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 504,
            policy_name=f"phase3_13_stage_b_train_pool_stratifier_{flat_seed}_{seed}",
            success_kind="stage_b_enter_mate2",
        )
        seed_result["split_manifest"]["stage_b"] = _phase41_pool_manifest(
            stage_b_train_pool,
            stage_b_gate_rows,
            stage_b_pool_traces,
        )
        stage_b_baseline = _phase38_flat_policy_traces(
            cfg,
            stage_b_gate_rows,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 900,
            policy_name=f"phase3_13_stage_b_executable_flat_exact_adversarial_{flat_seed}",
            success_kind="stage_b_enter_mate2",
        )
        seed_result["baselines"]["stage_b_exact_adversarial_flat_gate"] = stage_b_baseline
        stage_b_provider = _MigratedStageBFlatGraphScoreProvider(
            cfg,
            native_graph,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            policy_parent_id="stage_b_policy_phase3_13",
            terminal_namespace=f"phase3_13_stage_b_{flat_seed}",
        )
        stage_a_replay_rows = _phase41_stratified_fold_from_endpoint_map(
            stage_a_train_pool,
            stage_a_pool_traces["endpoint_by_row"],
            seed=int(seed) + 60_000,
            excluded_row_ids=set(),
            target_count=_phase41_validation_target_count(stage_a_train_pool),
        )[0]

        def stage_a_prior_replay() -> dict[str, Any]:
            return _phase38_migrated_provider_traces(
                cfg,
                stage_a_replay_rows,
                stage_a_provider,
                seed=int(seed) + 14_000,
                policy_name=f"phase3_13_stage_a_replay_for_stage_b_{seed}",
                success_kind="approach_waypoint",
            )

        stage_b_training = _phase41_train_credit_precision(
            cfg,
            provider=stage_b_provider,
            train_pool_rows=stage_b_train_pool,
            pool_endpoint_by_row=stage_b_pool_traces["endpoint_by_row"],
            prior_replay_checks=(
                {
                    "name": "stage_a_replay",
                    "evaluate": stage_a_prior_replay,
                },
            ),
            seed=int(seed) + 20_000,
            success_kind="stage_b_enter_mate2",
            rung_name="stage_b_chase",
        )
        stage_b_host_gate_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_b_gate_rows,
            stage_b_provider,
            seed=int(seed) + 21_000,
            policy_name=f"phase3_13_stage_b_host_gate_{seed}",
            success_kind="stage_b_enter_mate2",
        )
        stage_a_regression_host_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_a_gate_rows,
            stage_a_provider,
            seed=int(seed) + 22_000,
            policy_name=f"phase3_13_stage_a_host_regression_after_stage_b_{seed}",
            success_kind="approach_waypoint",
        )
        stage_b_host_gate = _phase41_gate_result_paired(
            rung="stage_b_chase_host",
            learner=stage_b_host_gate_eval,
            flat=stage_b_baseline,
            margin_wins=gate_margin,
        )
        stage_a_host_regression_gate = _phase41_gate_result_paired(
            rung="stage_a_approach_host_regression_after_stage_b",
            learner=stage_a_regression_host_eval,
            flat=stage_a_baseline,
            margin_wins=gate_margin,
        )
        seed_result["stage_b"] = {
            "host_training": stage_b_training,
            "host_gate_evaluation": stage_b_host_gate_eval,
            "host_gate": stage_b_host_gate,
        }
        seed_result["regression_checks"] = {
            "stage_a_host_after_stage_b": {
                "gate_evaluation": stage_a_regression_host_eval,
                "gate": stage_a_host_regression_gate,
            }
        }
        if int(stage_b_training["chunks_consolidated"]) == 0:
            seed_result["stop_reasons"].append("stage_b_zero_chunks_consolidated")
        if not stage_b_host_gate["passed"]:
            seed_result["stop_reasons"].append("stage_b_host_gate_unreachable_after_budget")
        if not stage_a_host_regression_gate["passed"]:
            seed_result["stop_reasons"].append("stage_a_host_regression_after_stage_b")
        if seed_result["stop_reasons"]:
            seed_result["population"] = runtime.population_summary()
            seed_result["birth_death_curve"] = runtime.birth_curve
            seed_result["candidate_fate_log"] = runtime.fate_log()
            _write_json(output_dir / f"seed_{seed}_discriminative_cell_economy.json", seed_result)
            per_seed.append(seed_result)
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
            continue

        seed_result["stage_b"]["ecology_training"] = _phase43_train_discriminative_ecology_segment(
            cfg,
            runtime=runtime,
            score_provider=stage_b_provider,
            rows=stage_b_train_pool,
            segment_name="stage_b_chase",
            success_kind="stage_b_enter_mate2",
            seed=int(seed) + 23_000,
            step_offset=20_000,
        )
        stage_b_ecology_gates = _phase42_ecology_gate_bundle(
            cfg,
            runtime=runtime,
            score_provider=stage_b_provider,
            gate_rows=stage_b_gate_rows,
            flat_baseline=stage_b_baseline,
            host_eval=stage_b_host_gate_eval,
            seed=int(seed) + 24_000,
            rung="stage_b_chase",
            success_kind="stage_b_enter_mate2",
            gate_margin=gate_margin,
        )
        stage_a_ecology_regression_gates = _phase42_ecology_gate_bundle(
            cfg,
            runtime=runtime,
            score_provider=stage_a_provider,
            gate_rows=stage_a_gate_rows,
            flat_baseline=stage_a_baseline,
            host_eval=stage_a_regression_host_eval,
            seed=int(seed) + 25_000,
            rung="stage_a_approach_regression_after_stage_b",
            success_kind="approach_waypoint",
            gate_margin=gate_margin,
        )
        stage_b_mature_eval = stage_b_ecology_gates["mature_eval"]
        noop_control = None
        if bool(getattr(cfg, "real_native_noop_ablation_control_enabled", False)):
            noop_control = _phase49_noop_ablation_control_old_pipeline(
                cfg,
                stage_b_gate_rows,
                runtime,
                stage_b_provider,
                full_eval=stage_b_mature_eval,
                seed=int(seed) + 30_000,
            )
        if bool(getattr(cfg, "real_native_controlled_ablation_enabled", False)):
            ablation = _phase49_controlled_ablation_health(
                cfg,
                stage_b_gate_rows,
                runtime,
                stage_b_provider,
                full_eval=stage_b_mature_eval,
                seed=int(seed) + 24_000,
                success_kind="stage_b_enter_mate2",
            )
        else:
            ablation = _real_native_ablation_health(
                cfg,
                stage_b_gate_rows,
                runtime,
                stage_b_provider,
                full_eval=stage_b_mature_eval,
                seed=int(seed) + 30_000,
            )
        rescue = _real_native_pruned_rescue_audit(
            cfg,
            stage_b_gate_rows,
            runtime,
            stage_b_provider,
            full_eval=stage_b_mature_eval,
            seed=int(seed) + 40_000,
        )
        seed_result["stage_b"]["ecology_gates"] = stage_b_ecology_gates
        seed_result["stage_b"]["population_stability"] = _phase43_population_stability(
            cfg,
            runtime.birth_curve,
            segment="stage_b_chase",
        )
        seed_result["regression_checks"]["stage_a_ecology_after_stage_b"] = stage_a_ecology_regression_gates
        seed_result["post_hoc_ablation"] = ablation
        if noop_control is not None:
            seed_result["noop_ablation_control"] = noop_control
        seed_result["pruned_rescue_audit"] = rescue
        seed_result["population"] = runtime.population_summary()
        seed_result["birth_death_curve"] = runtime.birth_curve
        seed_result["candidate_fate_log"] = runtime.fate_log()
        seed_result["runtime_instrumentation"] = runtime.instrumentation_summary(stage_b_provider)
        seed_result["host_instrumentation"] = {
            "stage_a": stage_a_provider.stats(),
            "stage_b": stage_b_provider.stats(),
        }
        population_stop = _phase43_population_stop_rule(cfg, runtime)
        seed_result["population_stop"] = population_stop
        if population_stop["population_collapse_to_zero"] or population_stop["unbounded_explosion"]:
            seed_result["stop_reasons"].append("population_stop_after_stage_b")
        if not seed_result["stage_b"]["population_stability"]["stable"]:
            seed_result["stop_reasons"].append("population_unstable_after_stage_b")
        if _phase43_choice_change_rate(seed_result["stage_b"]["ecology_training"]) < float(cfg.real_native_near_zero_choice_change_rate):
            seed_result["stop_reasons"].append("near_zero_choice_changing_plies_after_stage_b")
        if not stage_b_ecology_gates["mature_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_b_mature_cell_gate_regression_vs_flat")
        if not stage_b_ecology_gates["live_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_b_live_cell_gate_regression_vs_flat")
        if not stage_a_ecology_regression_gates["mature_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_a_mature_cell_regression_after_stage_b")
        if not stage_a_ecology_regression_gates["live_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_a_live_cell_regression_after_stage_b")
        if seed_result["stop_reasons"]:
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
        _write_json(output_dir / f"seed_{seed}_discriminative_cell_economy.json", seed_result)
        per_seed.append(seed_result)
        if (
            any("population" in reason for reason in seed_result["stop_reasons"])
            or any("gate_regression" in reason or "regression_after_stage_b" in reason for reason in seed_result["stop_reasons"])
            or any("near_zero_choice" in reason for reason in seed_result["stop_reasons"])
        ):
            break

    seed_results = {str(row["seed"]): row for row in per_seed}
    recurrence = _phase32_real_recurring_mature_composites(seed_results)
    cross_rung = _phase42_cross_rung_load_bearing_survivors(seed_results)
    summary = {
        "schema_version": "phase3_13_discriminative_cell_economy.v0",
        "phase": "Phase 3.13 discriminative cell economy",
        "config": asdict(cfg),
        "dataset": {
            "recent_curriculum_only_for_stage_a_b": True,
            "old_krk_curriculum_imported_for_stage_a_b": False,
            "foundation_row_count_per_seed": int(cfg.real_native_foundation_row_limit),
            "stage_a_train_pool_count": len(stage_a_train_pool),
            "stage_b_train_pool_count": len(stage_b_train_pool),
            "stage_a_gate_heldout_count": len(stage_a_gate_rows),
            "stage_b_gate_heldout_count": len(stage_b_gate_rows),
            "gate_rows_consulted_by_update_decisions": False,
        },
        "host_ladder": {
            "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
            "consolidation": _phase41_consolidation_spec(),
        },
        "ecology": _phase43_ecology_spec(cfg),
        "phase3_10_paired_gate_calibration": calibration,
        "per_seed": per_seed,
        "cross_seed_recurring_mature_composites": recurrence,
        "cross_rung_load_bearing_survivors": cross_rung,
        "tables": {
            "phase3_13_headline": _phase43_headline_table(per_seed),
            "phase3_13_choice_change_signal": _phase43_choice_change_table(per_seed),
            "phase3_13_acceptance_margins": _phase42_acceptance_margin_table(per_seed),
            "phase3_13_mature_recurrence": recurrence,
            "phase3_13_cross_rung_survivors": cross_rung,
        },
        "decision": {
            "stop_reasons": global_stop_reasons,
            "population_stop": any("population" in reason for reason in global_stop_reasons),
            "gate_regression_stop": any("gate_regression" in reason or "regression_after_stage_b" in reason for reason in global_stop_reasons),
            "near_zero_choice_change_stop": any("near_zero_choice" in reason for reason in global_stop_reasons),
            "mature_population_formed_any_seed": any(
                int(row.get("population", {}).get("mature_count", 0)) > 0 for row in per_seed
            ),
            "helpful_pruned_total": sum(
                int(row.get("pruned_rescue_audit", {}).get("load_bearing_but_pruned_count", 0))
                for row in per_seed
            ),
            "cross_rung_survivor_count": len(cross_rung),
            "recurring_mature_composite_count": sum(1 for row in recurrence if int(row.get("seed_count", 0)) > 1),
        },
    }
    _write_json(output_dir / "summary.json", summary)
    return summary


def run_phase44_audition_cell_economy_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    """Phase 3.14: imagination-paired auditions for TRIAL ecological cells."""

    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_14_audition_cell_economy",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
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
        real_native_max_live_composites=32,
        real_native_max_live_siblings_per_parent=4,
        real_native_trial_grace_exposures=3,
        real_native_dormant_decay=0.002,
        real_native_critical_period_exposures=5,
        real_native_critical_period_credit_multiplier=1.75,
        real_native_critical_period_optimism=0.025,
        real_native_positive_flip_credit=0.060,
        real_native_positive_flip_window=2,
        real_native_choice_change_mature_events=3,
        real_native_choice_change_neutral_rent=0.006,
        real_native_near_zero_choice_change_rate=0.01,
        real_native_stability_band_multiplier=5,
        real_native_audition_budget_per_cell=12,
        real_native_audition_per_ply_cap=2,
        real_native_audition_horizon_plies=8,
        real_native_audition_mature_better_events=3,
        real_native_audition_neutral_rent=0.004,
        real_native_audition_debt_threshold=3,
        real_native_audition_starvation_min_per_cell=1.0,
    )
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    gate_margin = _phase41_gate_margin_wins()
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_14_audition_cell_economy_design_spec.v0"
    design["phase_alias"] = "User-requested Phase 3.14 audition cell economy"
    design["host_ladder"] = {
        "base_commit": "175da26",
        "frozen_from": "Phase 3.13 ladder, gates, ratchet, spawn triggers, capacity throttle, and boundary",
        "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
    }
    design["ecology"] = _phase44_ecology_spec(cfg)
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

    calibration = _phase41_calibrate_phase310_paired_gates(gate_margin)
    _write_json(output_dir / "phase3_10_paired_gate_calibration.json", calibration)

    per_seed: list[dict[str, Any]] = []
    global_stop_reasons: list[str] = []

    def write_probation_progress(seed_value: int, status: str, payload: Mapping[str, Any] | None = None) -> None:
        if not bool(getattr(cfg, "real_native_probation_enabled", False)):
            return
        _write_json(
            output_dir / f"seed_{seed_value}_probation_progress.json",
            {
                "seed": int(seed_value),
                "status": str(status),
                "payload": dict(payload or {}),
            },
        )

    for index, seed in enumerate(cfg.seeds):
        flat_seed = int(cfg.flat_baseline_seeds[index % len(cfg.flat_baseline_seeds)])
        write_probation_progress(int(seed), "foundation_training_start", {"flat_seed": flat_seed})
        foundation = _train_native_foundation_for_ecology(cfg)
        write_probation_progress(int(seed), "foundation_training_done")
        native_graph = foundation["graph"]
        runtime = _GraphNativeCompositeRuntime(cfg, native_graph, seed=int(seed))
        foundation_rows = _foundation_ecology_rows(cfg, seed=int(seed))
        acceptance_row = foundation_rows[0] if foundation_rows else stage_a_train_pool[0]
        acceptance = runtime.acceptance_check(acceptance_row)
        foundation_gate = _phase39_foundation_gate(foundation, cfg)
        stage_a_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir) / f"stage_d_A_sealed_seed_{flat_seed}_weights.json"
        )
        stage_b_weights = _load_weight_table(
            Path(cfg.stage_b_baseline_dir) / f"stage_d_B_sealed_seed_{flat_seed}_weights.json"
        )
        stage_a_pool_traces = _phase38_flat_policy_traces(
            cfg,
            stage_a_train_pool,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 404,
            policy_name=f"phase3_14_stage_a_train_pool_stratifier_{flat_seed}_{seed}",
            success_kind="approach_waypoint",
        )
        stage_a_baseline = _phase38_flat_policy_traces(
            cfg,
            stage_a_gate_rows,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 700,
            policy_name=f"phase3_14_stage_a_executable_flat_exact_adversarial_{flat_seed}",
            success_kind="approach_waypoint",
        )
        seed_result: dict[str, Any] = {
            "schema_version": "phase3_14_audition_cell_economy_seed.v0",
            "seed": int(seed),
            "flat_seed": flat_seed,
            "acceptance_check": acceptance,
            "foundation": foundation["summary"],
            "foundation_gate": foundation_gate,
            "ecology_spec": _phase44_ecology_spec(cfg),
            "split_manifest": {
                "stage_a": _phase41_pool_manifest(stage_a_train_pool, stage_a_gate_rows, stage_a_pool_traces),
                "stage_b": None,
            },
            "baselines": {
                "stage_a_exact_adversarial_flat_gate": stage_a_baseline,
            },
            "stop_reasons": [],
        }
        if not acceptance["passed"]:
            seed_result["stop_reasons"].append("acceptance_check_failed")
        if not foundation_gate["passed"]:
            seed_result["stop_reasons"].append("foundation_gate_failed")
        if seed_result["stop_reasons"]:
            write_probation_progress(int(seed), "stopped_after_acceptance_or_foundation", {"stop_reasons": seed_result["stop_reasons"]})
            _write_json(output_dir / f"seed_{seed}_audition_cell_economy.json", seed_result)
            per_seed.append(seed_result)
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
            continue

        foundation_provider = _NativeFoundationScoreProvider(native_graph)
        write_probation_progress(int(seed), "foundation_ecology_start")
        seed_result["foundation_ecology_training"] = _phase44_train_audition_ecology_segment(
            cfg,
            runtime=runtime,
            score_provider=foundation_provider,
            rows=foundation_rows,
            segment_name="foundation_mate1_mate2",
            success_kind="stage_b_enter_mate2",
            seed=int(seed) + 3_000,
            step_offset=0,
        )
        write_probation_progress(
            int(seed),
            "foundation_ecology_done",
            {"population": runtime.population_summary()},
        )

        stage_a_provider = _MigratedStageBFlatGraphScoreProvider(
            cfg,
            native_graph,
            atom_weights=stage_a_weights,
            flat_seed=flat_seed,
            policy_parent_id="stage_a_policy_phase3_14",
            terminal_namespace=f"phase3_14_stage_a_{flat_seed}",
        )
        write_probation_progress(int(seed), "stage_a_host_training_start")
        stage_a_training = _phase41_train_credit_precision(
            cfg,
            provider=stage_a_provider,
            train_pool_rows=stage_a_train_pool,
            pool_endpoint_by_row=stage_a_pool_traces["endpoint_by_row"],
            prior_replay_checks=(),
            seed=int(seed) + 10_000,
            success_kind="approach_waypoint",
            rung_name="stage_a_approach",
        )
        write_probation_progress(int(seed), "stage_a_host_training_done", {"chunks_consolidated": int(stage_a_training["chunks_consolidated"])})
        stage_a_host_gate_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_a_gate_rows,
            stage_a_provider,
            seed=int(seed) + 11_000,
            policy_name=f"phase3_14_stage_a_host_gate_{seed}",
            success_kind="approach_waypoint",
        )
        stage_a_host_gate = _phase41_gate_result_paired(
            rung="stage_a_approach_host",
            learner=stage_a_host_gate_eval,
            flat=stage_a_baseline,
            margin_wins=gate_margin,
        )
        seed_result["stage_a"] = {
            "host_training": stage_a_training,
            "host_gate_evaluation": stage_a_host_gate_eval,
            "host_gate": stage_a_host_gate,
        }
        if int(stage_a_training["chunks_consolidated"]) == 0:
            seed_result["stop_reasons"].append("stage_a_zero_chunks_consolidated")
        if not stage_a_host_gate["passed"]:
            seed_result["stop_reasons"].append("stage_a_host_gate_unreachable_after_budget")
        if seed_result["stop_reasons"]:
            write_probation_progress(int(seed), "stopped_after_stage_a_host", {"stop_reasons": seed_result["stop_reasons"]})
            _write_json(output_dir / f"seed_{seed}_audition_cell_economy.json", seed_result)
            per_seed.append(seed_result)
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
            continue

        write_probation_progress(int(seed), "stage_a_ecology_start")
        seed_result["stage_a"]["ecology_training"] = _phase44_train_audition_ecology_segment(
            cfg,
            runtime=runtime,
            score_provider=stage_a_provider,
            rows=stage_a_train_pool,
            segment_name="stage_a_approach",
            success_kind="approach_waypoint",
            seed=int(seed) + 12_000,
            step_offset=10_000,
        )
        write_probation_progress(
            int(seed),
            "stage_a_ecology_done",
            {"population": runtime.population_summary()},
        )
        stage_a_ecology_gates = _phase42_ecology_gate_bundle(
            cfg,
            runtime=runtime,
            score_provider=stage_a_provider,
            gate_rows=stage_a_gate_rows,
            flat_baseline=stage_a_baseline,
            host_eval=stage_a_host_gate_eval,
            seed=int(seed) + 13_000,
            rung="stage_a_approach",
            success_kind="approach_waypoint",
            gate_margin=gate_margin,
        )
        seed_result["stage_a"]["ecology_gates"] = stage_a_ecology_gates
        stage_a_stability = _phase43_population_stability(
            cfg,
            runtime.birth_curve,
            segment="stage_a_approach",
        )
        seed_result["stage_a"]["population_stability"] = stage_a_stability
        stage_a_starvation = _phase44_audition_starvation(seed_result["stage_a"]["ecology_training"])
        seed_result["stage_a"]["audition_starvation"] = stage_a_starvation
        if int(getattr(cfg, "real_native_scheduled_audition_chunk_size", 0)) > 0:
            stage_a_scheduled_stop = _phase45_scheduled_unjudged_stop(
                cfg,
                seed_result["stage_a"]["ecology_training"],
            )
            seed_result["stage_a"]["scheduled_unjudged"] = stage_a_scheduled_stop
        else:
            stage_a_scheduled_stop = {"stop": False}
        if not stage_a_ecology_gates["mature_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_a_mature_cell_gate_regression_vs_flat")
        if not stage_a_ecology_gates["live_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_a_live_cell_gate_regression_vs_flat")
        population_stop = _phase43_population_stop_rule(cfg, runtime)
        if population_stop["population_collapse_to_zero"] or population_stop["unbounded_explosion"]:
            seed_result["stop_reasons"].append("population_stop_after_stage_a")
        if not stage_a_stability["stable"]:
            seed_result["stop_reasons"].append("population_unstable_after_stage_a")
        if stage_a_starvation["starved"]:
            seed_result["stop_reasons"].append("audition_starved_after_stage_a")
        if stage_a_scheduled_stop["stop"]:
            seed_result["stop_reasons"].append("scheduled_unjudged_after_stage_a")
        if seed_result["stop_reasons"]:
            write_probation_progress(int(seed), "stopped_after_stage_a_ecology", {"stop_reasons": seed_result["stop_reasons"]})
            seed_result["population"] = runtime.population_summary()
            seed_result["birth_death_curve"] = runtime.birth_curve
            seed_result["candidate_fate_log"] = runtime.fate_log()
            _write_json(output_dir / f"seed_{seed}_audition_cell_economy.json", seed_result)
            per_seed.append(seed_result)
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
            if (
                any("population" in reason for reason in seed_result["stop_reasons"])
                or any("gate_regression" in reason for reason in seed_result["stop_reasons"])
                or any("audition_starved" in reason for reason in seed_result["stop_reasons"])
                or any("scheduled_unjudged" in reason for reason in seed_result["stop_reasons"])
            ):
                if not bool(getattr(cfg, "real_native_continue_after_seed_stop", False)):
                    break
            continue

        stage_b_pool_traces = _phase38_flat_policy_traces(
            cfg,
            stage_b_train_pool,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 504,
            policy_name=f"phase3_14_stage_b_train_pool_stratifier_{flat_seed}_{seed}",
            success_kind="stage_b_enter_mate2",
        )
        seed_result["split_manifest"]["stage_b"] = _phase41_pool_manifest(
            stage_b_train_pool,
            stage_b_gate_rows,
            stage_b_pool_traces,
        )
        stage_b_baseline = _phase38_flat_policy_traces(
            cfg,
            stage_b_gate_rows,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            seed=int(seed) + 900,
            policy_name=f"phase3_14_stage_b_executable_flat_exact_adversarial_{flat_seed}",
            success_kind="stage_b_enter_mate2",
        )
        seed_result["baselines"]["stage_b_exact_adversarial_flat_gate"] = stage_b_baseline
        stage_b_provider = _MigratedStageBFlatGraphScoreProvider(
            cfg,
            native_graph,
            atom_weights=stage_b_weights,
            flat_seed=flat_seed,
            policy_parent_id="stage_b_policy_phase3_14",
            terminal_namespace=f"phase3_14_stage_b_{flat_seed}",
        )
        stage_a_replay_rows = _phase41_stratified_fold_from_endpoint_map(
            stage_a_train_pool,
            stage_a_pool_traces["endpoint_by_row"],
            seed=int(seed) + 60_000,
            excluded_row_ids=set(),
            target_count=_phase41_validation_target_count(stage_a_train_pool),
        )[0]

        def stage_a_prior_replay() -> dict[str, Any]:
            return _phase38_migrated_provider_traces(
                cfg,
                stage_a_replay_rows,
                stage_a_provider,
                seed=int(seed) + 14_000,
                policy_name=f"phase3_14_stage_a_replay_for_stage_b_{seed}",
                success_kind="approach_waypoint",
            )

        write_probation_progress(int(seed), "stage_b_host_training_start")
        stage_b_training = _phase41_train_credit_precision(
            cfg,
            provider=stage_b_provider,
            train_pool_rows=stage_b_train_pool,
            pool_endpoint_by_row=stage_b_pool_traces["endpoint_by_row"],
            prior_replay_checks=(
                {
                    "name": "stage_a_replay",
                    "evaluate": stage_a_prior_replay,
                },
            ),
            seed=int(seed) + 20_000,
            success_kind="stage_b_enter_mate2",
            rung_name="stage_b_chase",
        )
        write_probation_progress(int(seed), "stage_b_host_training_done", {"chunks_consolidated": int(stage_b_training["chunks_consolidated"])})
        stage_b_host_gate_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_b_gate_rows,
            stage_b_provider,
            seed=int(seed) + 21_000,
            policy_name=f"phase3_14_stage_b_host_gate_{seed}",
            success_kind="stage_b_enter_mate2",
        )
        stage_a_regression_host_eval = _phase38_migrated_provider_traces(
            cfg,
            stage_a_gate_rows,
            stage_a_provider,
            seed=int(seed) + 22_000,
            policy_name=f"phase3_14_stage_a_host_regression_after_stage_b_{seed}",
            success_kind="approach_waypoint",
        )
        stage_b_host_gate = _phase41_gate_result_paired(
            rung="stage_b_chase_host",
            learner=stage_b_host_gate_eval,
            flat=stage_b_baseline,
            margin_wins=gate_margin,
        )
        stage_a_host_regression_gate = _phase41_gate_result_paired(
            rung="stage_a_approach_host_regression_after_stage_b",
            learner=stage_a_regression_host_eval,
            flat=stage_a_baseline,
            margin_wins=gate_margin,
        )
        seed_result["stage_b"] = {
            "host_training": stage_b_training,
            "host_gate_evaluation": stage_b_host_gate_eval,
            "host_gate": stage_b_host_gate,
        }
        seed_result["regression_checks"] = {
            "stage_a_host_after_stage_b": {
                "gate_evaluation": stage_a_regression_host_eval,
                "gate": stage_a_host_regression_gate,
            }
        }
        if int(stage_b_training["chunks_consolidated"]) == 0:
            seed_result["stop_reasons"].append("stage_b_zero_chunks_consolidated")
        if not stage_b_host_gate["passed"]:
            seed_result["stop_reasons"].append("stage_b_host_gate_unreachable_after_budget")
        if not stage_a_host_regression_gate["passed"]:
            seed_result["stop_reasons"].append("stage_a_host_regression_after_stage_b")
        if seed_result["stop_reasons"]:
            write_probation_progress(int(seed), "stopped_after_stage_b_host", {"stop_reasons": seed_result["stop_reasons"]})
            seed_result["population"] = runtime.population_summary()
            seed_result["birth_death_curve"] = runtime.birth_curve
            seed_result["candidate_fate_log"] = runtime.fate_log()
            _write_json(output_dir / f"seed_{seed}_audition_cell_economy.json", seed_result)
            per_seed.append(seed_result)
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
            continue

        write_probation_progress(int(seed), "stage_b_ecology_start")
        seed_result["stage_b"]["ecology_training"] = _phase44_train_audition_ecology_segment(
            cfg,
            runtime=runtime,
            score_provider=stage_b_provider,
            rows=stage_b_train_pool,
            segment_name="stage_b_chase",
            success_kind="stage_b_enter_mate2",
            seed=int(seed) + 23_000,
            step_offset=20_000,
        )
        write_probation_progress(
            int(seed),
            "stage_b_ecology_done",
            {"population": runtime.population_summary()},
        )
        stage_b_ecology_gates = _phase42_ecology_gate_bundle(
            cfg,
            runtime=runtime,
            score_provider=stage_b_provider,
            gate_rows=stage_b_gate_rows,
            flat_baseline=stage_b_baseline,
            host_eval=stage_b_host_gate_eval,
            seed=int(seed) + 24_000,
            rung="stage_b_chase",
            success_kind="stage_b_enter_mate2",
            gate_margin=gate_margin,
        )
        stage_a_ecology_regression_gates = _phase42_ecology_gate_bundle(
            cfg,
            runtime=runtime,
            score_provider=stage_a_provider,
            gate_rows=stage_a_gate_rows,
            flat_baseline=stage_a_baseline,
            host_eval=stage_a_regression_host_eval,
            seed=int(seed) + 25_000,
            rung="stage_a_approach_regression_after_stage_b",
            success_kind="approach_waypoint",
            gate_margin=gate_margin,
        )
        stage_b_mature_eval = stage_b_ecology_gates["mature_eval"]
        noop_control = None
        if bool(getattr(cfg, "real_native_noop_ablation_control_enabled", False)):
            noop_control = _phase49_noop_ablation_control_old_pipeline(
                cfg,
                stage_b_gate_rows,
                runtime,
                stage_b_provider,
                full_eval=stage_b_mature_eval,
                seed=int(seed) + 30_000,
            )
        if bool(getattr(cfg, "real_native_controlled_ablation_enabled", False)):
            ablation = _phase49_controlled_ablation_health(
                cfg,
                stage_b_gate_rows,
                runtime,
                stage_b_provider,
                full_eval=stage_b_mature_eval,
                seed=int(seed) + 24_000,
                success_kind="stage_b_enter_mate2",
            )
        else:
            ablation = _real_native_ablation_health(
                cfg,
                stage_b_gate_rows,
                runtime,
                stage_b_provider,
                full_eval=stage_b_mature_eval,
                seed=int(seed) + 30_000,
            )
        rescue = _real_native_pruned_rescue_audit(
            cfg,
            stage_b_gate_rows,
            runtime,
            stage_b_provider,
            full_eval=stage_b_mature_eval,
            seed=int(seed) + 40_000,
        )
        seed_result["stage_b"]["ecology_gates"] = stage_b_ecology_gates
        seed_result["stage_b"]["population_stability"] = _phase43_population_stability(
            cfg,
            runtime.birth_curve,
            segment="stage_b_chase",
        )
        seed_result["stage_b"]["audition_starvation"] = _phase44_audition_starvation(
            seed_result["stage_b"]["ecology_training"]
        )
        if int(getattr(cfg, "real_native_scheduled_audition_chunk_size", 0)) > 0:
            seed_result["stage_b"]["scheduled_unjudged"] = _phase45_scheduled_unjudged_stop(
                cfg,
                seed_result["stage_b"]["ecology_training"],
            )
        seed_result["regression_checks"]["stage_a_ecology_after_stage_b"] = stage_a_ecology_regression_gates
        seed_result["post_hoc_ablation"] = ablation
        if noop_control is not None:
            seed_result["noop_ablation_control"] = noop_control
        seed_result["pruned_rescue_audit"] = rescue
        seed_result["population"] = runtime.population_summary()
        seed_result["birth_death_curve"] = runtime.birth_curve
        seed_result["candidate_fate_log"] = runtime.fate_log()
        seed_result["runtime_instrumentation"] = runtime.instrumentation_summary(stage_b_provider)
        seed_result["host_instrumentation"] = {
            "stage_a": stage_a_provider.stats(),
            "stage_b": stage_b_provider.stats(),
        }
        population_stop = _phase43_population_stop_rule(cfg, runtime)
        seed_result["population_stop"] = population_stop
        if population_stop["population_collapse_to_zero"] or population_stop["unbounded_explosion"]:
            seed_result["stop_reasons"].append("population_stop_after_stage_b")
        if not seed_result["stage_b"]["population_stability"]["stable"]:
            seed_result["stop_reasons"].append("population_unstable_after_stage_b")
        if seed_result["stage_b"]["audition_starvation"]["starved"]:
            seed_result["stop_reasons"].append("audition_starved_after_stage_b")
        if seed_result.get("stage_b", {}).get("scheduled_unjudged", {}).get("stop"):
            seed_result["stop_reasons"].append("scheduled_unjudged_after_stage_b")
        if not stage_b_ecology_gates["mature_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_b_mature_cell_gate_regression_vs_flat")
        if not stage_b_ecology_gates["live_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_b_live_cell_gate_regression_vs_flat")
        if not stage_a_ecology_regression_gates["mature_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_a_mature_cell_regression_after_stage_b")
        if not stage_a_ecology_regression_gates["live_vs_flat_gate"]["passed"]:
            seed_result["stop_reasons"].append("stage_a_live_cell_regression_after_stage_b")
        if seed_result["stop_reasons"]:
            global_stop_reasons.extend(f"{reason}:{seed}" for reason in seed_result["stop_reasons"])
        write_probation_progress(int(seed), "seed_done", {"stop_reasons": seed_result["stop_reasons"]})
        _write_json(output_dir / f"seed_{seed}_audition_cell_economy.json", seed_result)
        per_seed.append(seed_result)
        if (
            any("population" in reason for reason in seed_result["stop_reasons"])
            or any("gate_regression" in reason or "regression_after_stage_b" in reason for reason in seed_result["stop_reasons"])
            or any("audition_starved" in reason for reason in seed_result["stop_reasons"])
            or any("scheduled_unjudged" in reason for reason in seed_result["stop_reasons"])
        ):
            if not bool(getattr(cfg, "real_native_continue_after_seed_stop", False)):
                break

    seed_results = {str(row["seed"]): row for row in per_seed}
    recurrence = _phase32_real_recurring_mature_composites(seed_results)
    cross_rung = _phase42_cross_rung_load_bearing_survivors(seed_results)
    summary = {
        "schema_version": "phase3_14_audition_cell_economy.v0",
        "phase": "Phase 3.14 audition economy for TRIAL cells",
        "config": asdict(cfg),
        "dataset": {
            "recent_curriculum_only_for_stage_a_b": True,
            "old_krk_curriculum_imported_for_stage_a_b": False,
            "foundation_row_count_per_seed": int(cfg.real_native_foundation_row_limit),
            "stage_a_train_pool_count": len(stage_a_train_pool),
            "stage_b_train_pool_count": len(stage_b_train_pool),
            "stage_a_gate_heldout_count": len(stage_a_gate_rows),
            "stage_b_gate_heldout_count": len(stage_b_gate_rows),
            "gate_rows_consulted_by_update_decisions": False,
        },
        "host_ladder": {
            "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
            "consolidation": _phase41_consolidation_spec(),
        },
        "ecology": _phase44_ecology_spec(cfg),
        "phase3_10_paired_gate_calibration": calibration,
        "per_seed": per_seed,
        "cross_seed_recurring_mature_composites": recurrence,
        "cross_rung_load_bearing_survivors": cross_rung,
        "tables": {
            "phase3_14_headline": _phase44_headline_table(per_seed),
            "phase3_14_audition_signal": _phase44_audition_signal_table(per_seed),
            "phase3_14_acceptance_margins": _phase42_acceptance_margin_table(per_seed),
            "phase3_14_mature_recurrence": recurrence,
            "phase3_14_cross_rung_survivors": cross_rung,
        },
        "decision": {
            "stop_reasons": global_stop_reasons,
            "population_stop": any("population" in reason for reason in global_stop_reasons),
            "gate_regression_stop": any("gate_regression" in reason or "regression_after_stage_b" in reason for reason in global_stop_reasons),
            "audition_starvation_stop": any("audition_starved" in reason for reason in global_stop_reasons),
            "scheduled_unjudged_stop": any("scheduled_unjudged" in reason for reason in global_stop_reasons),
            "mature_population_formed_any_seed": any(
                int(row.get("population", {}).get("mature_count", 0)) > 0 for row in per_seed
            ),
            "helpful_pruned_total": sum(
                int(row.get("pruned_rescue_audit", {}).get("load_bearing_but_pruned_count", 0))
                for row in per_seed
            ),
            "cross_rung_survivor_count": len(cross_rung),
            "recurring_mature_composite_count": sum(1 for row in recurrence if int(row.get("seed_count", 0)) > 1),
        },
    }
    _write_json(output_dir / "summary.json", summary)
    return summary


def run_phase45_scheduled_audition_economy_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    """Phase 3.15: scheduled auditions so every TRIAL cell gets judged."""

    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_15_scheduled_audition_economy",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
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
        real_native_max_live_composites=32,
        real_native_max_live_siblings_per_parent=4,
        real_native_trial_grace_exposures=3,
        real_native_dormant_decay=0.002,
        real_native_critical_period_exposures=5,
        real_native_critical_period_credit_multiplier=1.75,
        real_native_critical_period_optimism=0.025,
        real_native_positive_flip_credit=0.060,
        real_native_positive_flip_window=2,
        real_native_choice_change_mature_events=3,
        real_native_choice_change_neutral_rent=0.006,
        real_native_near_zero_choice_change_rate=0.01,
        real_native_stability_band_multiplier=5,
        real_native_audition_budget_per_cell=10,
        real_native_audition_per_ply_cap=2,
        real_native_audition_horizon_plies=8,
        real_native_audition_mature_better_events=3,
        real_native_audition_neutral_rent=0.004,
        real_native_audition_debt_threshold=3,
        real_native_audition_starvation_min_per_cell=0.0,
        real_native_scheduled_audition_chunk_size=8,
        real_native_scheduled_unjudged_fraction_stop=0.25,
        real_native_scheduled_complete_flush=False,
        real_native_homeostatic_backlog_threshold=0.0,
    )
    output_dir = Path(cfg.output_dir)
    summary = run_phase44_audition_cell_economy_probe(config=cfg)
    correspondence = _phase45_composite_correspondence_table()
    gate_margin = _phase41_gate_margin_wins()
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_15_scheduled_audition_economy_design_spec.v0"
    design["phase_alias"] = "User-requested Phase 3.15 scheduled audition economy"
    design["host_ladder"] = {
        "base_commit": "2086dd6",
        "frozen_from": "Phase 3.14 audition mechanics with scheduled coverage added",
        "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
    }
    design["ecology"] = _phase45_ecology_spec(cfg)
    design["cross_experiment_composite_correspondence"] = correspondence
    _write_json(output_dir / "design_spec.json", design)

    for row in summary.get("per_seed", []):
        row["schema_version"] = "phase3_15_scheduled_audition_economy_seed.v0"
        row["ecology_spec"] = _phase45_ecology_spec(cfg)
        row["cross_experiment_composite_correspondence"] = correspondence
        _write_json(output_dir / f"seed_{row['seed']}_audition_cell_economy.json", row)
        _write_json(output_dir / f"seed_{row['seed']}_scheduled_audition_economy.json", row)

    tables = dict(summary.get("tables", {}))
    summary["schema_version"] = "phase3_15_scheduled_audition_economy.v0"
    summary["phase"] = "Phase 3.15 scheduled audition economy"
    summary["ecology"] = _phase45_ecology_spec(cfg)
    summary["cross_experiment_composite_correspondence"] = correspondence
    summary["tables"] = {
        "phase3_15_headline": tables.get("phase3_14_headline", []),
        "phase3_15_audition_signal": tables.get("phase3_14_audition_signal", []),
        "phase3_15_acceptance_margins": tables.get("phase3_14_acceptance_margins", []),
        "phase3_15_mature_recurrence": tables.get("phase3_14_mature_recurrence", []),
        "phase3_15_cross_rung_survivors": tables.get("phase3_14_cross_rung_survivors", []),
        "phase3_15_cross_experiment_composite_correspondence": correspondence,
    }
    summary["decision"]["scheduled_unjudged_stop"] = any(
        "scheduled_unjudged" in reason
        for reason in summary.get("decision", {}).get("stop_reasons", ())
    )
    _write_json(output_dir / "summary.json", summary)
    return summary


def run_phase46_homeostatic_audition_economy_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    """Phase 3.16: scheduled auditions with homeostatic birth gating."""

    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_16_homeostatic_audition_economy",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
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
        real_native_max_live_composites=32,
        real_native_max_live_siblings_per_parent=4,
        real_native_trial_grace_exposures=3,
        real_native_dormant_decay=0.002,
        real_native_critical_period_exposures=5,
        real_native_critical_period_credit_multiplier=1.75,
        real_native_critical_period_optimism=0.025,
        real_native_positive_flip_credit=0.060,
        real_native_positive_flip_window=2,
        real_native_choice_change_mature_events=3,
        real_native_choice_change_neutral_rent=0.006,
        real_native_near_zero_choice_change_rate=0.01,
        real_native_stability_band_multiplier=5,
        real_native_audition_budget_per_cell=10,
        real_native_audition_per_ply_cap=2,
        real_native_audition_horizon_plies=8,
        real_native_audition_mature_better_events=3,
        real_native_audition_neutral_rent=0.004,
        real_native_audition_debt_threshold=3,
        real_native_audition_starvation_min_per_cell=0.0,
        real_native_scheduled_audition_chunk_size=8,
        real_native_scheduled_unjudged_fraction_stop=0.25,
        real_native_scheduled_complete_flush=True,
        real_native_homeostatic_backlog_threshold=0.30,
        real_native_continue_after_seed_stop=True,
        real_native_max_ablation_subjects=256,
    )
    output_dir = Path(cfg.output_dir)
    summary = run_phase44_audition_cell_economy_probe(config=cfg)
    correspondence = _phase45_composite_correspondence_table()
    phase315_diagnosis = _phase46_phase315_under_k_diagnosis()
    family_recurrence = _phase46_mature_family_recurrence(summary.get("per_seed", []))
    gate_margin = _phase41_gate_margin_wins()
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_16_homeostatic_audition_economy_design_spec.v0"
    design["phase_alias"] = "User-requested Phase 3.16 homeostatic audition economy"
    design["host_ladder"] = {
        "base_commit": "d9680ea",
        "frozen_from": "Phase 3.15 scheduled audition mechanics, with only flush completion and backlog birth gating added",
        "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
    }
    design["ecology"] = _phase46_ecology_spec(cfg)
    design["phase3_15_under_k_diagnosis"] = phase315_diagnosis
    design["cross_experiment_composite_correspondence"] = correspondence
    _write_json(output_dir / "design_spec.json", design)

    for row in summary.get("per_seed", []):
        row["schema_version"] = "phase3_16_homeostatic_audition_economy_seed.v0"
        row["ecology_spec"] = _phase46_ecology_spec(cfg)
        row["cross_experiment_composite_correspondence"] = correspondence
        row["phase3_15_under_k_diagnosis"] = phase315_diagnosis
        _write_json(output_dir / f"seed_{row['seed']}_audition_cell_economy.json", row)
        _write_json(output_dir / f"seed_{row['seed']}_homeostatic_audition_economy.json", row)

    tables = dict(summary.get("tables", {}))
    summary["schema_version"] = "phase3_16_homeostatic_audition_economy.v0"
    summary["phase"] = "Phase 3.16 homeostatic audition economy"
    summary["ecology"] = _phase46_ecology_spec(cfg)
    summary["phase3_15_under_k_diagnosis"] = phase315_diagnosis
    summary["cross_experiment_composite_correspondence"] = correspondence
    summary["cross_seed_recurring_mature_families"] = family_recurrence
    summary["tables"] = {
        "phase3_16_headline": _phase46_headline_table(summary.get("per_seed", [])),
        "phase3_16_audition_signal": tables.get("phase3_14_audition_signal", []),
        "phase3_16_acceptance_margins": tables.get("phase3_14_acceptance_margins", []),
        "phase3_16_mature_recurrence_by_family": family_recurrence,
        "phase3_16_cross_rung_survivors": summary.get("cross_rung_load_bearing_survivors", []),
        "phase3_16_cross_experiment_composite_correspondence": correspondence,
        "phase3_16_phase3_15_under_k_diagnosis": phase315_diagnosis,
    }
    summary["decision"]["scheduled_unjudged_stop"] = any(
        "scheduled_unjudged" in reason
        for reason in summary.get("decision", {}).get("stop_reasons", ())
    )
    summary["decision"]["recurring_mature_family_count"] = sum(
        1 for row in family_recurrence if bool(row.get("recurs_3_of_5"))
    )
    _write_json(output_dir / "summary.json", summary)
    return summary


def run_phase47_supply_side_audition_economy_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    """Phase 3.17: pool-scan audition supply plus count homeostasis."""

    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_17_supply_side_audition_economy",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
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
        real_native_max_live_composites=32,
        real_native_max_live_siblings_per_parent=4,
        real_native_trial_grace_exposures=3,
        real_native_dormant_decay=0.002,
        real_native_critical_period_exposures=5,
        real_native_critical_period_credit_multiplier=1.75,
        real_native_critical_period_optimism=0.025,
        real_native_positive_flip_credit=0.060,
        real_native_positive_flip_window=2,
        real_native_choice_change_mature_events=3,
        real_native_choice_change_neutral_rent=0.006,
        real_native_near_zero_choice_change_rate=0.01,
        real_native_stability_band_multiplier=5,
        real_native_audition_budget_per_cell=10,
        real_native_audition_per_ply_cap=2,
        real_native_audition_horizon_plies=8,
        real_native_audition_mature_better_events=3,
        real_native_audition_neutral_rent=0.004,
        real_native_audition_debt_threshold=3,
        real_native_audition_starvation_min_per_cell=0.0,
        real_native_scheduled_audition_chunk_size=8,
        real_native_scheduled_unjudged_fraction_stop=0.0,
        real_native_scheduled_complete_flush=True,
        real_native_homeostatic_backlog_threshold=0.0,
        real_native_pool_scan_auditions=True,
        real_native_trial_band_min=20,
        real_native_trial_band_max=60,
        real_native_court_throughput_per_chunk=0,
        real_native_continue_after_seed_stop=True,
        real_native_max_ablation_subjects=256,
    )
    output_dir = Path(cfg.output_dir)
    summary = run_phase44_audition_cell_economy_probe(config=cfg)
    correspondence = _phase45_composite_correspondence_table()
    family_recurrence = _phase46_mature_family_recurrence(summary.get("per_seed", []))
    gate_margin = _phase41_gate_margin_wins()
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_17_supply_side_audition_economy_design_spec.v0"
    design["phase_alias"] = "User-requested Phase 3.17 supply-side audition economy"
    design["host_ladder"] = {
        "base_commit": "157e6b5",
        "frozen_from": "Phase 3.16 court mechanics, with only audition supply and count homeostasis changed",
        "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
    }
    design["ecology"] = _phase47_ecology_spec(cfg)
    design["cross_experiment_composite_correspondence"] = correspondence
    _write_json(output_dir / "design_spec.json", design)

    for row in summary.get("per_seed", []):
        row["schema_version"] = "phase3_17_supply_side_audition_economy_seed.v0"
        row["ecology_spec"] = _phase47_ecology_spec(cfg)
        row["cross_experiment_composite_correspondence"] = correspondence
        _write_json(output_dir / f"seed_{row['seed']}_audition_cell_economy.json", row)
        _write_json(output_dir / f"seed_{row['seed']}_supply_side_audition_economy.json", row)

    tables = dict(summary.get("tables", {}))
    summary["schema_version"] = "phase3_17_supply_side_audition_economy.v0"
    summary["phase"] = "Phase 3.17 supply-side audition economy"
    summary["ecology"] = _phase47_ecology_spec(cfg)
    summary["cross_experiment_composite_correspondence"] = correspondence
    summary["cross_seed_recurring_mature_families"] = family_recurrence
    summary["tables"] = {
        "phase3_17_headline": _phase47_headline_table(summary.get("per_seed", [])),
        "phase3_17_audition_signal": tables.get("phase3_14_audition_signal", []),
        "phase3_17_acceptance_margins": tables.get("phase3_14_acceptance_margins", []),
        "phase3_17_mature_recurrence_by_family": family_recurrence,
        "phase3_17_cross_rung_survivors": summary.get("cross_rung_load_bearing_survivors", []),
        "phase3_17_cross_experiment_composite_correspondence": correspondence,
    }
    summary["decision"]["recurring_mature_family_count"] = sum(
        1 for row in family_recurrence if bool(row.get("recurs_3_of_5"))
    )
    _write_json(output_dir / "summary.json", summary)
    return summary


def run_phase48_probation_audition_economy_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    """Phase 3.18: audition nominates, validation counterfactual confirms."""

    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_18_probation_audition_economy",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
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
        real_native_max_live_composites=32,
        real_native_max_live_siblings_per_parent=4,
        real_native_trial_grace_exposures=3,
        real_native_dormant_decay=0.002,
        real_native_critical_period_exposures=5,
        real_native_critical_period_credit_multiplier=1.75,
        real_native_critical_period_optimism=0.025,
        real_native_positive_flip_credit=0.060,
        real_native_positive_flip_window=2,
        real_native_choice_change_mature_events=3,
        real_native_choice_change_neutral_rent=0.006,
        real_native_near_zero_choice_change_rate=0.01,
        real_native_stability_band_multiplier=5,
        real_native_audition_budget_per_cell=10,
        real_native_audition_per_ply_cap=2,
        real_native_audition_horizon_plies=8,
        real_native_audition_mature_better_events=3,
        real_native_audition_neutral_rent=0.004,
        real_native_audition_debt_threshold=3,
        real_native_audition_starvation_min_per_cell=0.0,
        real_native_scheduled_audition_chunk_size=8,
        real_native_scheduled_unjudged_fraction_stop=0.0,
        real_native_scheduled_complete_flush=True,
        real_native_homeostatic_backlog_threshold=0.0,
        real_native_pool_scan_auditions=True,
        real_native_trial_band_min=20,
        real_native_trial_band_max=60,
        real_native_court_throughput_per_chunk=0,
        real_native_probation_enabled=True,
        real_native_probation_validation_rows=32,
        real_native_probation_noise_margin_wins=1,
        real_native_probation_max_retests=2,
        real_native_continue_after_seed_stop=True,
        real_native_max_ablation_subjects=256,
    )
    output_dir = Path(cfg.output_dir)
    forensics = _phase48_phase317_forensics()
    summary = run_phase44_audition_cell_economy_probe(config=cfg)
    correspondence = _phase45_composite_correspondence_table()
    confirmed_recurrence = _phase48_family_recurrence(summary.get("per_seed", []), tier="confirmed")
    nomination_recurrence = _phase48_family_recurrence(summary.get("per_seed", []), tier="nomination")
    confirmed_dumps = _phase48_confirmed_cell_dumps(summary.get("per_seed", []))
    funnel = _phase48_funnel_table(summary.get("per_seed", []))
    gate_margin = _phase41_gate_margin_wins()
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_18_probation_audition_economy_design_spec.v0"
    design["phase_alias"] = "User-requested Phase 3.18 probation tier: nominate by audition, confirm by counterfactual"
    design["host_ladder"] = {
        "base_commit": "ad0fd99",
        "frozen_from": "Phase 3.17 supply-side audition economy, with only the lifecycle acceptance tier changed",
        "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
    }
    design["ecology"] = _phase48_ecology_spec(cfg)
    design["phase3_17_forensics_before_mechanism"] = forensics
    design["cross_experiment_composite_correspondence"] = correspondence
    _write_json(output_dir / "design_spec.json", design)

    for row in summary.get("per_seed", []):
        row["schema_version"] = "phase3_18_probation_audition_economy_seed.v0"
        row["ecology_spec"] = _phase48_ecology_spec(cfg)
        row["phase3_17_forensics_before_mechanism"] = forensics
        row["cross_experiment_composite_correspondence"] = correspondence
        _write_json(output_dir / f"seed_{row['seed']}_probation_audition_economy.json", row)

    tables = dict(summary.get("tables", {}))
    summary["schema_version"] = "phase3_18_probation_audition_economy.v0"
    summary["phase"] = "Phase 3.18 probation tier: nominate by audition, confirm by counterfactual"
    summary["ecology"] = _phase48_ecology_spec(cfg)
    summary["phase3_17_forensics_before_mechanism"] = forensics
    summary["cross_experiment_composite_correspondence"] = correspondence
    summary["cross_seed_recurring_confirmed_families"] = confirmed_recurrence
    summary["cross_seed_recurring_nomination_families"] = nomination_recurrence
    summary["confirmed_cell_dumps"] = confirmed_dumps
    summary["tables"] = {
        "phase3_18_forensics": [forensics],
        "phase3_18_funnel": funnel,
        "phase3_18_confirmed_recurrence_by_family": confirmed_recurrence,
        "phase3_18_nomination_recurrence_by_family": nomination_recurrence,
        "phase3_18_confirmed_cell_dumps": confirmed_dumps,
        "phase3_18_headline": _phase48_headline_table(summary.get("per_seed", [])),
        "phase3_18_audition_signal": tables.get("phase3_14_audition_signal", []),
        "phase3_18_acceptance_margins": tables.get("phase3_14_acceptance_margins", []),
        "phase3_18_cross_rung_survivors": summary.get("cross_rung_load_bearing_survivors", []),
        "phase3_18_cross_experiment_composite_correspondence": correspondence,
    }
    summary["decision"]["confirmed_cell_count"] = len(confirmed_dumps)
    summary["decision"]["recurring_confirmed_family_count"] = sum(
        1 for row in confirmed_recurrence if bool(row.get("recurs_3_of_5"))
    )
    summary["decision"]["recurring_nomination_family_count"] = sum(
        1 for row in nomination_recurrence if bool(row.get("recurs_3_of_5"))
    )
    _write_json(output_dir / "summary.json", summary)
    return summary


def run_phase49_noop_ablation_control_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    """Phase 3.19 Part 0: no-op control for the old 3.17 ablation path."""

    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_19_noop_ablation_control",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
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
        real_native_max_live_composites=32,
        real_native_max_live_siblings_per_parent=4,
        real_native_trial_grace_exposures=3,
        real_native_dormant_decay=0.002,
        real_native_critical_period_exposures=5,
        real_native_critical_period_credit_multiplier=1.75,
        real_native_critical_period_optimism=0.025,
        real_native_positive_flip_credit=0.060,
        real_native_positive_flip_window=2,
        real_native_choice_change_mature_events=3,
        real_native_choice_change_neutral_rent=0.006,
        real_native_near_zero_choice_change_rate=0.01,
        real_native_stability_band_multiplier=5,
        real_native_audition_budget_per_cell=10,
        real_native_audition_per_ply_cap=2,
        real_native_audition_horizon_plies=8,
        real_native_audition_mature_better_events=3,
        real_native_audition_neutral_rent=0.004,
        real_native_audition_debt_threshold=3,
        real_native_audition_starvation_min_per_cell=0.0,
        real_native_scheduled_audition_chunk_size=8,
        real_native_scheduled_unjudged_fraction_stop=0.0,
        real_native_scheduled_complete_flush=True,
        real_native_homeostatic_backlog_threshold=0.0,
        real_native_pool_scan_auditions=True,
        real_native_trial_band_min=20,
        real_native_trial_band_max=60,
        real_native_court_throughput_per_chunk=0,
        real_native_continue_after_seed_stop=True,
        real_native_max_ablation_subjects=256,
        real_native_noop_ablation_control_enabled=True,
    )
    output_dir = Path(cfg.output_dir)
    summary = run_phase44_audition_cell_economy_probe(config=cfg)
    correspondence = _phase45_composite_correspondence_table()
    noop_table = _phase49_noop_control_table(summary.get("per_seed", []))
    gate_margin = _phase41_gate_margin_wins()
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_19_noop_ablation_control_design_spec.v0"
    design["phase_alias"] = "User-requested Phase 3.19 Part 0 no-op ablation provenance control"
    design["host_ladder"] = {
        "base_commit": "04e7c33",
        "frozen_from": "Phase 3.17 supply-side audition economy; no mechanism change, no-op ablation control only",
        "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
    }
    design["ecology"] = _phase47_ecology_spec(cfg)
    design["ablation_control"] = {
        "control": "old 3.17 ablation path with disabled=set(), compared against the full ecology gate path",
        "required_before_verdicts_count": True,
    }
    design["cross_experiment_composite_correspondence"] = correspondence
    _write_json(output_dir / "design_spec.json", design)

    for row in summary.get("per_seed", []):
        row["schema_version"] = "phase3_19_noop_ablation_control_seed.v0"
        row["ecology_spec"] = _phase47_ecology_spec(cfg)
        row["cross_experiment_composite_correspondence"] = correspondence
        _write_json(output_dir / f"seed_{row['seed']}_noop_ablation_control.json", row)

    tables = dict(summary.get("tables", {}))
    summary["schema_version"] = "phase3_19_noop_ablation_control.v0"
    summary["phase"] = "Phase 3.19 Part 0: no-op control for 3.17 ablation provenance"
    summary["ecology"] = _phase47_ecology_spec(cfg)
    summary["cross_experiment_composite_correspondence"] = correspondence
    summary["noop_ablation_control_verdict"] = _phase49_noop_control_verdict(noop_table)
    summary["tables"] = {
        "phase3_19_noop_control": noop_table,
        "phase3_19_noop_config_diff": _phase49_noop_config_diff_table(summary.get("per_seed", [])),
        "phase3_19_underlying_3_17_headline": _phase47_headline_table(summary.get("per_seed", [])),
        "phase3_19_underlying_audition_signal": tables.get("phase3_14_audition_signal", []),
        "phase3_19_cross_experiment_composite_correspondence": correspondence,
    }
    summary["decision"]["noop_ablation_control_passed"] = bool(summary["noop_ablation_control_verdict"]["passed"])
    summary["decision"]["old_ablation_verdicts_valid"] = bool(summary["noop_ablation_control_verdict"]["passed"])
    _write_json(output_dir / "summary.json", summary)
    return summary


def run_phase49_dose_response_outcome_audition_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    """Phase 3.19: dose-response probation plus outcome-aligned audition accounting."""

    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_19_dose_response_outcome_audition",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
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
        real_native_max_live_composites=32,
        real_native_max_live_siblings_per_parent=4,
        real_native_trial_grace_exposures=3,
        real_native_dormant_decay=0.002,
        real_native_critical_period_exposures=5,
        real_native_critical_period_credit_multiplier=1.75,
        real_native_critical_period_optimism=0.025,
        real_native_positive_flip_credit=0.060,
        real_native_positive_flip_window=2,
        real_native_choice_change_mature_events=3,
        real_native_choice_change_neutral_rent=0.006,
        real_native_near_zero_choice_change_rate=0.01,
        real_native_stability_band_multiplier=5,
        real_native_audition_budget_per_cell=10,
        real_native_audition_per_ply_cap=2,
        real_native_audition_horizon_plies=8,
        real_native_audition_mature_better_events=3,
        real_native_audition_neutral_rent=0.004,
        real_native_audition_debt_threshold=3,
        real_native_audition_starvation_min_per_cell=0.0,
        real_native_scheduled_audition_chunk_size=8,
        real_native_scheduled_unjudged_fraction_stop=0.0,
        real_native_scheduled_complete_flush=True,
        real_native_homeostatic_backlog_threshold=0.0,
        real_native_pool_scan_auditions=True,
        real_native_trial_band_min=20,
        real_native_trial_band_max=60,
        real_native_court_throughput_per_chunk=0,
        real_native_probation_enabled=True,
        real_native_probation_validation_rows=32,
        real_native_probation_noise_margin_wins=1,
        real_native_probation_max_retests=2,
        real_native_probation_dose_response_enabled=True,
        real_native_probation_dose_multipliers=(1.0, 3.0, 9.0, 27.0),
        real_native_controlled_ablation_enabled=True,
        real_native_outcome_audition_enabled=True,
        real_native_outcome_audition_horizon_plies=16,
        real_native_continue_after_seed_stop=True,
        real_native_max_ablation_subjects=256,
    )
    output_dir = Path(cfg.output_dir)
    summary = run_phase44_audition_cell_economy_probe(config=cfg)
    correspondence = _phase45_composite_correspondence_table()
    confirmed_recurrence = _phase48_family_recurrence(summary.get("per_seed", []), tier="confirmed")
    nomination_recurrence = _phase48_family_recurrence(summary.get("per_seed", []), tier="nomination")
    confirmed_dumps = _phase48_confirmed_cell_dumps(summary.get("per_seed", []))
    funnel = _phase48_funnel_table(summary.get("per_seed", []))
    dose_table = _phase49_dose_response_table(summary.get("per_seed", []))
    outcome_table = _phase49_outcome_agreement_table(summary.get("per_seed", []))
    gate_margin = _phase41_gate_margin_wins()
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_19_dose_response_outcome_audition_design_spec.v0"
    design["phase_alias"] = "User-requested Phase 3.19 dose-response probation and outcome-aligned auditions"
    design["host_ladder"] = {
        "base_commit": "04e7c33",
        "frozen_from": "Phase 3.18 probation funnel; supply, homeostasis, spawn triggers, gates, ratchet, boundary, funnel structure frozen",
        "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
    }
    design["ecology"] = _phase49_ecology_spec(cfg)
    design["cross_experiment_composite_correspondence"] = correspondence
    _write_json(output_dir / "design_spec.json", design)

    for row in summary.get("per_seed", []):
        row["schema_version"] = "phase3_19_dose_response_outcome_audition_seed.v0"
        row["ecology_spec"] = _phase49_ecology_spec(cfg)
        row["cross_experiment_composite_correspondence"] = correspondence
        _write_json(output_dir / f"seed_{row['seed']}_dose_response_outcome_audition.json", row)

    tables = dict(summary.get("tables", {}))
    summary["schema_version"] = "phase3_19_dose_response_outcome_audition.v0"
    summary["phase"] = "Phase 3.19 dose-response probation and outcome-aligned auditions"
    summary["ecology"] = _phase49_ecology_spec(cfg)
    summary["cross_experiment_composite_correspondence"] = correspondence
    summary["cross_seed_recurring_confirmed_families"] = confirmed_recurrence
    summary["cross_seed_recurring_nomination_families"] = nomination_recurrence
    summary["confirmed_cell_dumps"] = confirmed_dumps
    summary["tables"] = {
        "phase3_19_funnel": funnel,
        "phase3_19_dose_response": dose_table,
        "phase3_19_first_flip_vs_outcome": outcome_table,
        "phase3_19_confirmed_recurrence_by_family": confirmed_recurrence,
        "phase3_19_nomination_recurrence_by_family": nomination_recurrence,
        "phase3_19_confirmed_cell_dumps": confirmed_dumps,
        "phase3_19_headline": _phase48_headline_table(summary.get("per_seed", [])),
        "phase3_19_audition_signal": tables.get("phase3_14_audition_signal", []),
        "phase3_19_acceptance_margins": tables.get("phase3_14_acceptance_margins", []),
        "phase3_19_cross_rung_survivors": summary.get("cross_rung_load_bearing_survivors", []),
        "phase3_19_cross_experiment_composite_correspondence": correspondence,
    }
    summary["decision"]["confirmed_cell_count"] = len(confirmed_dumps)
    summary["decision"]["recurring_confirmed_family_count"] = sum(
        1 for row in confirmed_recurrence if bool(row.get("recurs_3_of_5"))
    )
    summary["decision"]["first_flip_vs_outcome_agreement_rate"] = _phase49_weighted_outcome_agreement(outcome_table)
    _write_json(output_dir / "summary.json", summary)
    return summary


def run_phase50_conditional_gate_composite_probe(
    *,
    config: StageBEcologicalDiscoveryConfig | None = None,
) -> dict[str, Any]:
    """Phase 3.20: route probation/confirmed composites as conditional gates."""

    cfg = config or StageBEcologicalDiscoveryConfig(
        output_dir="reports/autogrowth/clean_slate_krk/phase3_20_conditional_gate_composites",
        seeds=(20272931, 20272932, 20272933, 20272934, 20272935),
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
        real_native_max_live_composites=32,
        real_native_max_live_siblings_per_parent=4,
        real_native_trial_grace_exposures=3,
        real_native_dormant_decay=0.002,
        real_native_critical_period_exposures=5,
        real_native_critical_period_credit_multiplier=1.75,
        real_native_critical_period_optimism=0.025,
        real_native_positive_flip_credit=0.060,
        real_native_positive_flip_window=2,
        real_native_choice_change_mature_events=3,
        real_native_choice_change_neutral_rent=0.006,
        real_native_near_zero_choice_change_rate=0.01,
        real_native_stability_band_multiplier=5,
        real_native_audition_budget_per_cell=10,
        real_native_audition_per_ply_cap=2,
        real_native_audition_horizon_plies=8,
        real_native_audition_mature_better_events=3,
        real_native_audition_neutral_rent=0.004,
        real_native_audition_debt_threshold=3,
        real_native_audition_starvation_min_per_cell=0.0,
        real_native_scheduled_audition_chunk_size=8,
        real_native_scheduled_unjudged_fraction_stop=0.0,
        real_native_scheduled_complete_flush=True,
        real_native_homeostatic_backlog_threshold=0.0,
        real_native_pool_scan_auditions=True,
        real_native_trial_band_min=20,
        real_native_trial_band_max=60,
        real_native_court_throughput_per_chunk=0,
        real_native_probation_enabled=True,
        real_native_probation_validation_rows=32,
        real_native_probation_noise_margin_wins=1,
        real_native_probation_max_retests=2,
        real_native_probation_dose_response_enabled=True,
        real_native_probation_dose_multipliers=(1.0, 3.0, 9.0, 27.0),
        real_native_controlled_ablation_enabled=True,
        real_native_outcome_audition_enabled=True,
        real_native_outcome_audition_horizon_plies=16,
        real_native_outcome_audition_verdict_is_standing=True,
        real_native_conditional_gate_enabled=True,
        real_native_conditional_gate_mode="action_pattern_eligibility",
        real_native_conditional_gate_states=("PROBATION", "MATURE"),
        real_native_continue_after_seed_stop=True,
        real_native_max_ablation_subjects=256,
    )
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    gate_margin = _phase41_gate_margin_wins()
    gate_proof = _phase50_constructed_gate_flip_proof(cfg)
    design = _design_spec(cfg)
    design["schema_version"] = "phase3_20_conditional_gate_composites_design_spec.v0"
    design["phase_alias"] = "User-requested Phase 3.20 conditional-gate routing for composites"
    design["linear_host_boundary_record"] = {
        "phase3_19_result": "792/792 dose tests were flat_all_doses with zero nonzero validation discordants",
        "interpretation": "additive composite routing is structurally inert on the linear atom-sum host",
        "effect_channel_changed": "conditional action-pattern eligibility gate",
    }
    design["conditional_gate"] = _phase50_conditional_gate_spec(cfg)
    design["constructed_move_flip_proof"] = gate_proof
    design["host_ladder"] = {
        "frozen_from": "Phase 3.19 supply, homeostasis, spawn triggers, gates, ratchet, boundary, and funnel structure",
        "paired_gate_spec": _phase41_paired_gate_spec(gate_margin),
    }
    design["ecology"] = _phase50_ecology_spec(cfg)
    _write_json(output_dir / "design_spec.json", design)
    if not bool(gate_proof.get("passed", False)):
        summary = {
            "schema_version": "phase3_20_conditional_gate_composites.v0",
            "phase": "Phase 3.20 conditional-gate composite routing",
            "config": asdict(cfg),
            "constructed_move_flip_proof": gate_proof,
            "per_seed": [],
            "decision": {
                "acceptance_check_passed": False,
                "stop_reason": "constructed_conditional_gate_move_flip_proof_failed",
                "confirmed_through_gate_count": 0,
            },
        }
        _write_json(output_dir / "summary.json", summary)
        return summary

    summary = run_phase44_audition_cell_economy_probe(config=cfg)
    correspondence = _phase45_composite_correspondence_table()
    confirmed_recurrence = _phase48_family_recurrence(summary.get("per_seed", []), tier="confirmed")
    nomination_recurrence = _phase48_family_recurrence(summary.get("per_seed", []), tier="nomination")
    confirmed_dumps = _phase48_confirmed_cell_dumps(summary.get("per_seed", []))
    funnel = _phase48_funnel_table(summary.get("per_seed", []))
    dose_table = _phase49_dose_response_table(summary.get("per_seed", []))
    outcome_table = _phase49_outcome_agreement_table(summary.get("per_seed", []))
    gate_validation = _phase50_gate_validation_table(summary.get("per_seed", []))

    design["ecology"] = _phase50_ecology_spec(cfg)
    design["cross_experiment_composite_correspondence"] = correspondence
    _write_json(output_dir / "design_spec.json", design)
    for row in summary.get("per_seed", []):
        row["schema_version"] = "phase3_20_conditional_gate_composites_seed.v0"
        row["ecology_spec"] = _phase50_ecology_spec(cfg)
        row["constructed_move_flip_proof"] = gate_proof
        row["cross_experiment_composite_correspondence"] = correspondence
        _write_json(output_dir / f"seed_{row['seed']}_conditional_gate_composites.json", row)

    tables = dict(summary.get("tables", {}))
    summary["schema_version"] = "phase3_20_conditional_gate_composites.v0"
    summary["phase"] = "Phase 3.20 conditional-gate composite routing"
    summary["linear_host_boundary_record"] = design["linear_host_boundary_record"]
    summary["conditional_gate"] = _phase50_conditional_gate_spec(cfg)
    summary["constructed_move_flip_proof"] = gate_proof
    summary["ecology"] = _phase50_ecology_spec(cfg)
    summary["cross_experiment_composite_correspondence"] = correspondence
    summary["cross_seed_recurring_confirmed_families"] = confirmed_recurrence
    summary["cross_seed_recurring_nomination_families"] = nomination_recurrence
    summary["confirmed_cell_dumps"] = confirmed_dumps
    summary["tables"] = {
        "phase3_20_constructed_gate_flip_proof": [gate_proof],
        "phase3_20_funnel": funnel,
        "phase3_20_dose_response": dose_table,
        "phase3_20_gate_validation": gate_validation,
        "phase3_20_first_flip_vs_outcome": outcome_table,
        "phase3_20_confirmed_recurrence_by_family": confirmed_recurrence,
        "phase3_20_nomination_recurrence_by_family": nomination_recurrence,
        "phase3_20_confirmed_cell_dumps": confirmed_dumps,
        "phase3_20_headline": _phase48_headline_table(summary.get("per_seed", [])),
        "phase3_20_audition_signal": tables.get("phase3_14_audition_signal", []),
        "phase3_20_acceptance_margins": tables.get("phase3_14_acceptance_margins", []),
        "phase3_20_cross_rung_survivors": summary.get("cross_rung_load_bearing_survivors", []),
        "phase3_20_cross_experiment_composite_correspondence": correspondence,
    }
    confirmed_gate_count = sum(
        int(row.get("confirmed_gate_cells", 0))
        for row in gate_validation
    )
    nonzero_validation_discordants = sum(
        int(row.get("nonzero_gate_validation_discordants", 0))
        for row in gate_validation
    )
    summary["decision"]["constructed_gate_flip_proof_passed"] = bool(gate_proof.get("passed", False))
    summary["decision"]["confirmed_through_gate_count"] = confirmed_gate_count
    summary["decision"]["nonzero_gate_validation_discordants"] = nonzero_validation_discordants
    summary["decision"]["terminal_substrate_finding"] = bool(
        gate_proof.get("passed", False)
        and confirmed_gate_count == 0
        and nonzero_validation_discordants == 0
    )
    _write_json(output_dir / "summary.json", summary)
    return summary


def _phase50_conditional_gate_spec(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    return {
        "enabled": bool(getattr(cfg, "real_native_conditional_gate_enabled", False)),
        "mode": str(getattr(cfg, "real_native_conditional_gate_mode", "")),
        "eligible_states": list(map(str, getattr(cfg, "real_native_conditional_gate_states", ()))),
        "mechanism": (
            "A PROBATION/MATURE composite with at least one action_pattern child stops contributing "
            "an additive score. When it confirms, the runtime restricts the argmax to moves where "
            "an eligible gate composite confirms, then chooses the host-best move inside that gated set."
        ),
        "fallback": "If no eligible gate composite confirms on any legal move, the host/additive selector is unchanged.",
        "non_additive_for_gate_states": True,
        "constructed_flip_required_before_full_run": True,
    }


def _phase50_ecology_spec(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    spec = _phase49_ecology_spec(cfg)
    spec["audition_verdict"] = {
        "first_flip_retired_as_standing_verdict": bool(
            getattr(cfg, "real_native_outcome_audition_verdict_is_standing", False)
        ),
        "standing_verdict": (
            "bounded_outcome_paired_rollout"
            if bool(getattr(cfg, "real_native_outcome_audition_verdict_is_standing", False))
            else "first_flip"
        ),
        "outcome_horizon_plies": int(getattr(cfg, "real_native_outcome_audition_horizon_plies", 0)),
    }
    spec["conditional_gate"] = _phase50_conditional_gate_spec(cfg)
    return spec


def _phase50_constructed_gate_flip_proof(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    if not bool(getattr(cfg, "real_native_conditional_gate_enabled", False)):
        return {"passed": False, "reason": "conditional_gate_disabled"}
    stage_b_payload = json.loads(Path(cfg.stage_b_rows_path).read_text(encoding="utf-8"))
    row_pool = list(stage_b_payload.get("train", ())) + list(stage_b_payload.get("heldout", ()))
    if not row_pool:
        return {"passed": False, "reason": "no_stage_b_rows"}
    flat_seed = int(cfg.flat_baseline_seeds[0])
    foundation = _train_native_foundation_for_ecology(cfg)
    native_graph = foundation["graph"]
    stage_b_weights = _load_weight_table(
        Path(cfg.stage_b_baseline_dir) / f"stage_d_B_sealed_seed_{flat_seed}_weights.json"
    )
    provider = _MigratedStageBFlatGraphScoreProvider(
        cfg,
        native_graph,
        atom_weights=stage_b_weights,
        flat_seed=flat_seed,
        policy_parent_id="phase3_20_gate_proof_stage_b_policy",
        terminal_namespace=f"phase3_20_gate_proof_stage_b_{flat_seed}",
    )
    runtime = _GraphNativeCompositeRuntime(cfg, native_graph, seed=int(cfg.seeds[0]) if cfg.seeds else 0)
    inspected = 0
    for row in row_pool[: max(32, int(getattr(cfg, "max_samples", 8)) * 16)]:
        board = chess.Board(str(row["fen"]))
        if board.turn != chess.WHITE:
            continue
        counts: Counter[Any] = Counter()
        legal = _legal_without_third_repetition(board, counts)
        if len(legal) < 2:
            continue
        inspected += 1
        base_scores = provider(board, counts)
        host_rows = [(float(base_scores.get(move.uci(), 0.0)), move.uci(), move) for move in legal]
        host_rows.sort(reverse=True)
        host_move = host_rows[0][-1]
        host_keys = set(key for key, _scale in _sealed_action_key_scales(board, host_move))
        for _score, _uci, target_move in reversed(host_rows):
            if target_move == host_move:
                continue
            target_keys = tuple(key for key, _scale in _sealed_action_key_scales(board, target_move))
            action_keys = [key for key in target_keys if str(key).startswith("action_pattern:")]
            distinguishing_action_keys = [key for key in action_keys if key not in host_keys]
            if not distinguishing_action_keys:
                continue
            child_pool = tuple(dict.fromkeys(distinguishing_action_keys + action_keys + list(_generic_child_pool(target_keys))))
            if len(child_pool) < int(cfg.composite_width):
                continue
            children = tuple(child_pool[: int(cfg.composite_width)])
            source_signature = _percept_signature(target_keys)
            item = runtime.spawn(
                children,
                trigger="phase3_20_constructed_gate_flip_proof",
                birth_segment="constructed_gate_flip_proof",
                birth_row_id=int(row.get("row_id", -1)),
                source_signature=source_signature,
                birth_step=0,
            )
            cid = str(item["composite_id"])
            item["state"] = "PROBATION"
            item["probation_entry_weight"] = 0.0
            item["routing_weight_override"] = 0.0
            item["conditional_gate_mechanism"] = str(getattr(cfg, "real_native_conditional_gate_mode", "action_pattern_eligibility"))
            item["conditional_gate_action_keys"] = [
                str(child)
                for child in children
                if str(child).startswith("action_pattern:")
            ]
            runtime.cells[cid].state = StemCellState.PROBATION
            node_id = str(item["node_id"])
            if node_id in native_graph.graph.nodes:
                node = native_graph.graph.nodes[node_id]
                node.meta["stem_cell_state"] = StemCellState.PROBATION.name
                node.meta["conditional_gate_mechanism"] = item["conditional_gate_mechanism"]
                node.meta["conditional_gate_action_keys"] = list(item["conditional_gate_action_keys"])
            off = runtime.choose_move(
                board,
                counts,
                provider,
                seed=20272050,
                disabled={cid},
                discriminative=True,
            )
            on = runtime.choose_move(
                board,
                counts,
                provider,
                seed=20272050,
                discriminative=True,
            )
            off_move = off.get("move")
            on_move = on.get("move")
            passed = bool(
                off_move is not None
                and on_move is not None
                and off_move != on_move
                and on.get("conditional_gate_applied")
                and on.get("conditional_gate_changed_choice")
            )
            proof = {
                "passed": passed,
                "mechanism": "action_pattern_eligibility",
                "row_id": int(row.get("row_id", -1)),
                "fen": str(row["fen"]),
                "flat_seed": flat_seed,
                "composite_id": cid,
                "children": list(children),
                "distinguishing_action_keys": list(distinguishing_action_keys),
                "gate_action_keys": list(item["conditional_gate_action_keys"]),
                "host_off_move": None if off_move is None else off_move.uci(),
                "gated_on_move": None if on_move is None else on_move.uci(),
                "target_gate_move": target_move.uci(),
                "host_base_score": float(base_scores.get(host_move.uci(), 0.0)),
                "target_base_score": float(base_scores.get(target_move.uci(), 0.0)),
                "conditional_gate_candidate_count": int(on.get("conditional_gate_candidate_count", 0)),
                "conditional_gate_composite_ids": list(on.get("conditional_gate_composite_ids", ())),
                "inspected_white_positions": inspected,
                "runtime_path": "GraphNativeCompositeRuntime.choose_move -> evaluate_composite -> FormalReConEngine request/confirmation -> conditional gate eligibility",
            }
            if passed:
                return proof
            item["state"] = "PRUNED"
            item["prune_reason"] = "constructed_gate_flip_probe_no_flip"
            runtime.cells[cid].state = StemCellState.PRUNED
    return {
        "passed": False,
        "reason": "no_constructed_action_pattern_gate_flipped_move",
        "inspected_white_positions": inspected,
        "mechanism": "action_pattern_eligibility",
    }


def _phase50_gate_validation_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed_row in per_seed:
        records = _phase48_probation_records(seed_row)
        gate_applied = 0
        gate_changed = 0
        nonzero_discordants = 0
        confirmed_gate = 0
        for record in records:
            if record.get("decision") == "confirmed":
                confirmed_gate += int(any(
                    int(dose.get("conditional_gate_applied_count", 0)) > 0
                    for dose in record.get("dose_records", ())
                ))
            for dose in record.get("dose_records", ()):
                gate_applied += int(dose.get("conditional_gate_applied_count", 0))
                gate_changed += int(dose.get("conditional_gate_changed_choice_count", 0))
                nonzero_discordants += int(int(dose.get("discordant_delta", 0)) != 0)
        rows.append(
            {
                "seed": int(seed_row.get("seed", 0)),
                "probation_tests": len(records),
                "confirmed_gate_cells": confirmed_gate,
                "gate_validation_applied_count": gate_applied,
                "gate_validation_changed_choice_count": gate_changed,
                "nonzero_gate_validation_discordants": nonzero_discordants,
            }
        )
    return rows


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


def _phase40_consolidation_spec() -> dict[str, Any]:
    spec = _phase39_consolidation_spec()
    spec.update(
        {
            "acceptance": (
                "stratified validation wins non-regress, hard endpoint counts non-regress, "
                "and all prior-rung replay checks satisfy the same endpoint-aware rule"
            ),
            "validation_split": "train-pool rows stratified by initial exact-adversarial endpoint family",
            "endpoint_non_regression": True,
        }
    )
    return spec


def _phase41_credit_precision_spec() -> dict[str, Any]:
    return {
        "hard_fail_endpoints": ["fence_broken", "rook_lost"],
        "flip_ply_rule": (
            "find first transition where fence_established or rook_present flips from true to false; "
            "assign negative credit to that white ply plus discounted shares to the previous two white plies"
        ),
        "discounts": {"flip_ply": 1.0, "previous_1": 0.5, "previous_2": 0.25},
        "fallback": "hard failures without an identified flip-ply use the previous first-move endpoint credit",
        "features_changed": False,
    }


def _phase41_paired_gate_spec(margin_wins: int) -> dict[str, Any]:
    return {
        "paired_rows": True,
        "gate_rule": (
            "pass if discordant pairs favor learner, or learner is non-inferior within the declared margin"
        ),
        "non_inferiority_margin_wins_on_128": int(margin_wins),
        "margin_interpretation": "3/128 = 2.34 percentage points; smaller folds scale proportionally with minimum 1",
        "gate_rows_consulted_by_update_decisions": False,
    }


def _phase41_consolidation_spec() -> dict[str, Any]:
    spec = _phase40_consolidation_spec()
    spec.update(
        {
            "validation_split": "fresh endpoint-stratified validation fold resampled from train pool each chunk",
            "chunk_budget": 12,
            "acceptance": (
                "paired after-vs-before validation pass, hard endpoint non-regression, "
                "and paired prior-rung replay pass"
            ),
            "credit_precision": _phase41_credit_precision_spec(),
        }
    )
    return spec


def _phase42_ecology_spec(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    return {
        "substrate": "GraphNativeCompositeRuntime StemCellTerminal nodes inside the persistent FormalReConEngine graph",
        "birth_boundary": "internal surprise triggers only; guided residual arm quarantined and disabled",
        "guided_birth_budget": int(cfg.max_guided_births),
        "cells_carried_across_rungs": True,
        "trial_cells_advisory_during_training": True,
        "final_headline_eval": "host plus MATURE cells versus host alone; all-live gate also checked for interference",
        "activation_conditioned_decay": True,
        "trial_grace_requested_exposures": int(cfg.real_native_trial_grace_exposures),
        "critical_period": {
            "requested_exposure_window": int(cfg.real_native_critical_period_exposures),
            "credit_multiplier_initial": float(cfg.real_native_critical_period_credit_multiplier),
            "optimism_bonus_initial": float(cfg.real_native_critical_period_optimism),
            "anneals_to": {"credit_multiplier": 1.0, "optimism_bonus": 0.0},
        },
        "positive_achievement_flip_nutrition": {
            "credit": float(cfg.real_native_positive_flip_credit),
            "eligibility_window_white_plies": int(cfg.real_native_positive_flip_window),
            "recognizers": [
                "fence_established_geometry false->true",
                "_approach_waypoint_success false->true",
                "post-hoc success endpoint fallback if no geometric flip fires",
            ],
            "exact_judges_decide_birth_sites": False,
        },
    }


def _phase43_ecology_spec(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    spec = _phase42_ecology_spec(cfg)
    spec.update(
        {
            "credit_assignment": (
                "per-ply host-alone argmax is compared with host+advisory choice; "
                "only cells responsible for a changed choice receive later flip credit/debt"
            ),
            "same_choice_credit": "zero nutrition/debt to all cells on plies where cells do not change the host choice",
            "maturity_rule": f"{int(cfg.real_native_choice_change_mature_events)} choice-changing positive events",
            "neutral_rent": float(cfg.real_native_choice_change_neutral_rent),
            "near_zero_choice_change_stop_rate": float(cfg.real_native_near_zero_choice_change_rate),
            "birth_throttle": {
                "rule": "internal spawn triggers fire only into open parent habitat slots",
                "per_parent_live_capacity": int(cfg.real_native_max_live_siblings_per_parent),
            },
            "stage_b_stability_gate": {
                "alive_limit": int(cfg.real_native_max_live_composites) * int(cfg.real_native_stability_band_multiplier),
                "trial_plateau_window": 4,
                "trial_plateau_tolerance": max(4, int(cfg.real_native_max_live_composites)),
            },
        }
    )
    return spec


def _phase44_ecology_spec(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    spec = _phase43_ecology_spec(cfg)
    spec.update(
        {
            "audition_economy": {
                "trigger": (
                    "TRIAL cell requests an audition when its own active-proposal argmax "
                    "differs from the host-alone argmax on a training ply"
                ),
                "per_cell_budget": int(cfg.real_native_audition_budget_per_cell),
                "per_ply_cap": int(cfg.real_native_audition_per_ply_cap),
                "audition_horizon_white_plies": int(cfg.real_native_audition_horizon_plies),
                "maturity_rule": f"{int(cfg.real_native_audition_mature_better_events)} cell-better verdicts",
                "debt_prune_threshold": int(cfg.real_native_audition_debt_threshold),
                "budget_exhaustion_rule": "prune TRIAL cell when audition budget is exhausted with better-worse <= 0",
                "neutral_rent": float(cfg.real_native_audition_neutral_rent),
                "played_moves": "unchanged host+advisory path from Phase 3.13",
                "imagination_only": True,
            },
            "purity_notes": {
                "adversarial_black": "opponent-side exact-adversarial reply selection in paired virtual rollouts",
                "white_move_source": "cell's own active-proposal move versus host-alone argmax; no white oracle",
                "verdict_source": "internal recognizer flips from the paired virtual lines",
                "exact_judges": "post-hoc reporting only for audition verdicts",
            },
            "starvation_stop": {
                "min_auditions_per_cell": float(cfg.real_native_audition_starvation_min_per_cell),
            },
        }
    )
    return spec


def _phase45_ecology_spec(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    spec = _phase44_ecology_spec(cfg)
    spec.update(
        {
            "scheduled_auditions": {
                "enabled": True,
                "chunk_size_rows": int(cfg.real_native_scheduled_audition_chunk_size),
                "per_cell_budget": int(cfg.real_native_audition_budget_per_cell),
                "firing_replay_buffer": "training positions tagged by TRIAL cells whose own proposal fired",
                "agreement_rule": (
                    "if all sampled firing positions agree with host-alone for the remaining budget, "
                    "prune as scheduled_redundancy, distinct from debt pruning"
                ),
                "spontaneous_live_auditions": "remain enabled and count against the same per-cell budget",
                "unjudged_fraction_stop": float(cfg.real_native_scheduled_unjudged_fraction_stop),
            },
        }
    )
    return spec


def _phase46_ecology_spec(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    spec = _phase45_ecology_spec(cfg)
    spec.update(
        {
            "scheduled_auditions": {
                **spec["scheduled_auditions"],
                "complete_end_of_stage_flush": bool(cfg.real_native_scheduled_complete_flush),
                "complete_flush_rule": (
                    "before stability checks, actively scan host trajectories over the segment rows to fill each "
                    "TRIAL cell's own firing set; spend the remaining per-cell budget, sampling with replacement "
                    "from that firing set if needed; cells with no firing samples are pruned as no-firing"
                ),
                "complete_flush_compute_reported": True,
            },
            "homeostatic_birth_gate": {
                "enabled": float(cfg.real_native_homeostatic_backlog_threshold) > 0.0,
                "backlog_threshold": float(cfg.real_native_homeostatic_backlog_threshold),
                "rule": (
                    "internal spawn triggers fire only when the under-K TRIAL fraction is below the threshold; "
                    "otherwise the trigger is counted as deferred and may reappear naturally if still valid"
                ),
            },
            "recurrence_families": {
                "FAMILY-CONFINE": "both atoms match bk_neighbor_*_available=zero",
                "FAMILY-SAFEROOK": "rook_attacked_after=0 AND to_file_or_rank_edge_distance=k",
                "other": "exact sorted child-atom conjunction",
                "recurrence_rule": "same predeclared family matures in at least 3 of 5 seeds",
            },
        }
    )
    return spec


def _phase47_ecology_spec(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    spec = _phase46_ecology_spec(cfg)
    spec.update(
        {
            "scheduled_auditions": {
                **spec["scheduled_auditions"],
                "supply_source": (
                    "for each TRIAL cell, scan the current rung train row pool directly under the "
                    "host trajectory; visited rollout firing samples are retained as bonus supply"
                ),
                "vacuous_rule": "fires nowhere in the current rung pool plus visited bonus -> VACUOUS prune",
                "redundancy_rule": (
                    "sample up to K positions from the firing set; prune redundant only if every "
                    "sampled firing agrees with the host"
                ),
                "disagreement_rule": (
                    "audition only sampled firing positions where the cell proposal differs from host; "
                    "maturity remains N cell-better verdicts"
                ),
            },
            "count_homeostasis": {
                "trial_band": [int(cfg.real_native_trial_band_min), int(cfg.real_native_trial_band_max)],
                "court_throughput_per_chunk": _phase47_court_throughput_per_chunk(cfg),
                "birth_rule": (
                    "spawn while TRIAL count is below the upper band and under-K TRIAL count is below "
                    "the computed court throughput; no fractional backlog gate is used"
                ),
            },
            "recurrence_families": {
                "FAMILY-CONFINE": "both atoms match bk_neighbor_*_available=zero",
                "FAMILY-SAFEROOK": "rook_attacked_after=0 AND to_file_or_rank_edge_distance=k",
                "other": "exact sorted child-atom conjunction",
                "recurrence_rule": "same predeclared family matures in at least 3 of 5 seeds",
            },
        }
    )
    return spec


def _phase48_ecology_spec(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    spec = _phase47_ecology_spec(cfg)
    spec["probation_confirmation"] = {
        "enabled": bool(getattr(cfg, "real_native_probation_enabled", False)),
        "lifecycle": "TRIAL -> PROBATION on audition nomination -> MATURE only after validation counterfactual confirmation",
        "validation_source": "fresh sample from the current rung train pool; gate heldout remains post-hoc only",
        "validation_rows": int(getattr(cfg, "real_native_probation_validation_rows", 32)),
        "noise_margin_wins": int(getattr(cfg, "real_native_probation_noise_margin_wins", 1)),
        "max_retests_before_prune": int(getattr(cfg, "real_native_probation_max_retests", 2)),
        "confirmation_cadence": "after each rung's complete audition flush, before stability and gate checks",
        "weight_rule": (
            "probation freezes the audition-time advisory weight as routing_weight_override; "
            "confirmation preserves that weight, so MATURE routing has no promotion-time scale jump"
        ),
        "recurrence_claim_tier": "confirmed/MATURE after validation, not audition nomination",
    }
    return spec


def _phase49_ecology_spec(cfg: StageBEcologicalDiscoveryConfig) -> dict[str, Any]:
    spec = _phase48_ecology_spec(cfg)
    spec["probation_confirmation"].update(
        {
            "dose_response_enabled": bool(getattr(cfg, "real_native_probation_dose_response_enabled", False)),
            "dose_multipliers": [
                float(value) for value in getattr(cfg, "real_native_probation_dose_multipliers", (1.0,))
            ],
            "dose_rule": (
                "test each nominee at audition weight times the predeclared ladder; confirm at the "
                "lowest dose with positive paired discordant balance beyond margin, demote only if "
                "all doses are negative beyond margin, otherwise park as flat or mixed"
            ),
            "confirmed_routing_rule": "confirmed cells route at their selected validation dose",
        }
    )
    spec["outcome_aligned_auditions"] = {
        "enabled": bool(getattr(cfg, "real_native_outcome_audition_enabled", False)),
        "horizon_plies": int(getattr(cfg, "real_native_outcome_audition_horizon_plies", 16)),
        "parallel_accounting_only": True,
        "standing_first_flip_verdicts_unchanged": True,
        "outcome_verdict": (
            "paired virtual rollout from identical position, host move versus cell move, exact-adversarial "
            "black, bounded by horizon or terminal; win/loss/draw pair decides better/worse/tie"
        ),
    }
    spec["controlled_ablation"] = {
        "enabled": bool(getattr(cfg, "real_native_controlled_ablation_enabled", False)),
        "no_op_required_before_verdicts_count": True,
        "evaluator": "_phase42_ecology_policy_traces exact-adversarial path for full, no-op, and cell-off",
    }
    return spec


def _phase48_phase317_forensics(
    path: str = "reports/autogrowth/clean_slate_krk/phase3_17_supply_side_audition_economy/summary.json",
) -> dict[str, Any]:
    artifact = Path(path)
    if not artifact.exists():
        return {"artifact": str(artifact), "available": False, "reason": "phase3_17_summary_not_found"}
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    deltas: list[int] = []
    paired_available = True
    for seed_row in payload.get("per_seed", ()):
        for record in seed_row.get("post_hoc_ablation", {}).get("records", ()):
            deltas.append(int(record.get("ablation_delta", 0)))
            paired_available = paired_available and isinstance(record.get("paired"), Mapping)
    abs_deltas = sorted(abs(value) for value in deltas)

    def quantile(q: float) -> int | None:
        if not abs_deltas:
            return None
        return int(abs_deltas[int(q * (len(abs_deltas) - 1))])

    negative = sum(1 for value in deltas if value < 0)
    zero = sum(1 for value in deltas if value == 0)
    positive = sum(1 for value in deltas if value > 0)
    return {
        "artifact": str(artifact),
        "available": True,
        "mature_cell_count": len(deltas),
        "delta_sign_counts": {"negative": negative, "zero": zero, "positive": positive},
        "delta_range": {"min": min(deltas) if deltas else None, "max": max(deltas) if deltas else None},
        "absolute_delta_distribution": {
            "min": quantile(0.0),
            "p25": quantile(0.25),
            "median": quantile(0.50),
            "p75": quantile(0.75),
            "p90": quantile(0.90),
            "max": quantile(1.0),
            "mean": (sum(abs_deltas) / len(abs_deltas)) if abs_deltas else None,
            "count_abs_le_1": sum(1 for value in abs_deltas if value <= 1),
            "count_abs_le_3": sum(1 for value in abs_deltas if value <= 3),
            "count_abs_le_5": sum(1 for value in abs_deltas if value <= 5),
        },
        "paired_discordant_tables_available": bool(paired_available and deltas),
        "paired_discordant_tables_gap": (
            None if paired_available and deltas
            else "3.17 persisted full/ablated win counts but not per-cell ablated success_by_row vectors; exact row flip tables cannot be reconstructed"
        ),
        "maturation_weight_forensics": {
            "state_label_enters_weight_formula": False,
            "formula": "min(max_advisory_weight, initial_weight + 0.04 * local_resource + critical_period_optimism)",
            "explicit_mature_scale_jump": False,
            "remaining_confound": "resource/optimism can drift before maturity; Phase 3.18 freezes audition-time routed weight at PROBATION",
        },
        "verdict": (
            "154_harmful_survives_magnitude_scrutiny"
            if len(deltas) == 154 and negative == 154 and abs_deltas and min(abs_deltas) > 5
            else "inspect_distribution"
        ),
    }


def _phase48_probation_records(seed_row: Mapping[str, Any]) -> list[dict[str, Any]]:
    segments: list[Mapping[str, Any]] = []
    foundation = seed_row.get("foundation_ecology_training", {})
    if isinstance(foundation, Mapping):
        segments.append(foundation)
    stage_a = seed_row.get("stage_a", {}) if isinstance(seed_row.get("stage_a"), Mapping) else {}
    stage_b = seed_row.get("stage_b", {}) if isinstance(seed_row.get("stage_b"), Mapping) else {}
    for segment in (stage_a.get("ecology_training", {}), stage_b.get("ecology_training", {})):
        if isinstance(segment, Mapping):
            segments.append(segment)
    records: list[dict[str, Any]] = []
    for segment in segments:
        records.extend(dict(record) for record in segment.get("probation_confirmation_records", ()))
    return records


def _phase48_funnel_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed_row in per_seed:
        fate_log = list(seed_row.get("candidate_fate_log", ()))
        nominated_ids = {
            str(item.get("composite_id"))
            for item in fate_log
            if item.get("probation_entry_weight") is not None
            or any(str(event.get("event", "")).startswith("probation_") for event in item.get("fate_events", ()))
        }
        records = _phase48_probation_records(seed_row)
        decision_counts = Counter(str(record.get("decision", "unknown")) for record in records)
        final_counts = Counter(str(item.get("state", "unknown")) for item in fate_log if str(item.get("composite_id")) in nominated_ids)
        rows.append(
            {
                "seed": int(seed_row.get("seed", 0)),
                "nominated": len(nominated_ids),
                "probation_tests": len(records),
                "confirmed": int(decision_counts["confirmed"]),
                "demoted": int(decision_counts["demoted"]),
                "parked": int(decision_counts["parked"]),
                "final_mature_confirmed": int(final_counts["MATURE"]),
                "final_probation": int(final_counts["PROBATION"]),
                "final_pruned_after_probation": int(final_counts["PRUNED"]),
                "validation_win_loss": sum(int(record.get("paired", {}).get("win_loss", 0)) for record in records),
                "validation_loss_win": sum(int(record.get("paired", {}).get("loss_win", 0)) for record in records),
                "max_abs_promotion_weight_jump": max(
                    [abs(float(record.get("promotion_weight_jump", 0.0))) for record in records] or [0.0]
                ),
            }
        )
    return rows


def _phase48_family_recurrence(per_seed: Sequence[Mapping[str, Any]], *, tier: str) -> list[dict[str, Any]]:
    families: dict[str, dict[str, Any]] = {}
    for seed_row in per_seed:
        seed = int(seed_row.get("seed", 0))
        if tier == "confirmed":
            source_items = [
                item for item in seed_row.get("candidate_fate_log", ())
                if item.get("state") == "MATURE" and item.get("probation_entry_weight") is not None
            ]
        else:
            source_items = [
                item for item in seed_row.get("candidate_fate_log", ())
                if item.get("probation_entry_weight") is not None
            ]
        for item in source_items:
            family = _phase46_composite_family(item.get("children", ()))
            record = families.setdefault(
                family,
                {
                    "family": family,
                    "tier": tier,
                    "seeds": set(),
                    "cell_count": 0,
                    "examples": [],
                    "birth_segments": Counter(),
                },
            )
            record["seeds"].add(seed)
            record["cell_count"] += 1
            record["birth_segments"][str(item.get("birth_segment"))] += 1
            if len(record["examples"]) < 8:
                record["examples"].append(
                    {
                        "seed": seed,
                        "composite_id": str(item.get("composite_id")),
                        "children": list(item.get("children", ())),
                        "birth_segment": str(item.get("birth_segment")),
                        "state": str(item.get("state")),
                    }
                )
    rows: list[dict[str, Any]] = []
    for record in families.values():
        seeds = sorted(record["seeds"])
        rows.append(
            {
                "family": str(record["family"]),
                "tier": str(record["tier"]),
                "seed_count": len(seeds),
                "seeds": seeds,
                "cell_count": int(record["cell_count"]),
                "recurs_3_of_5": len(seeds) >= 3,
                "birth_segments": dict(sorted(record["birth_segments"].items())),
                "examples": list(record["examples"]),
            }
        )
    rows.sort(key=lambda item: (-int(item["seed_count"]), str(item["family"])))
    return rows


def _phase48_confirmed_cell_dumps(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    dumps: list[dict[str, Any]] = []
    for seed_row in per_seed:
        seed = int(seed_row.get("seed", 0))
        ablation_by_id = {
            str(record.get("composite_id")): record
            for record in seed_row.get("post_hoc_ablation", {}).get("records", ())
        }
        validation_by_id: dict[str, dict[str, Any]] = {}
        for record in _phase48_probation_records(seed_row):
            if record.get("decision") == "confirmed":
                validation_by_id[str(record.get("composite_id"))] = record
        for item in seed_row.get("candidate_fate_log", ()):
            cid = str(item.get("composite_id"))
            if item.get("state") != "MATURE" or item.get("probation_entry_weight") is None:
                continue
            validation = validation_by_id.get(cid, {})
            ablation = ablation_by_id.get(cid, {})
            gate_action_keys = list(item.get("conditional_gate_action_keys", ()))
            if not gate_action_keys:
                gate_action_keys = [
                    str(child)
                    for child in item.get("children", ())
                    if str(child).startswith("action_pattern:")
                ]
            gate_mechanism = item.get("conditional_gate_mechanism")
            if gate_mechanism is None and gate_action_keys:
                gate_mechanism = "action_pattern_eligibility"
            dumps.append(
                {
                    "seed": seed,
                    "composite_id": cid,
                    "family": _phase46_composite_family(item.get("children", ())),
                    "children": list(item.get("children", ())),
                    "birth_segment": str(item.get("birth_segment")),
                    "probation_entry_event": item.get("probation_entry_event"),
                    "validation_delta_on_minus_off": validation.get("validation_delta_on_minus_off"),
                    "validation_paired": validation.get("paired", {}),
                    "validation_dose_records": validation.get("dose_records", ()),
                    "heldout_ablation_delta": ablation.get("ablation_delta"),
                    "heldout_classification": ablation.get("classification"),
                    "heldout_paired": ablation.get("paired", {}),
                    "routing_weight": item.get("routing_weight_override"),
                    "gate_mechanism": gate_mechanism,
                    "gate_action_keys": gate_action_keys,
                    "flipped_move_proof": item.get("conditional_gate_flip_sample"),
                }
            )
    dumps.sort(key=lambda item: (int(item["seed"]), str(item["family"]), str(item["composite_id"])))
    return dumps


def _phase48_headline_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    funnel_by_seed = {int(row["seed"]): row for row in _phase48_funnel_table(per_seed)}
    rows: list[dict[str, Any]] = []
    for seed_row in per_seed:
        population = seed_row.get("population", {})
        stage_b = seed_row.get("stage_b", {}) if isinstance(seed_row.get("stage_b"), Mapping) else {}
        stage_b_training = stage_b.get("ecology_training", {}) if isinstance(stage_b, Mapping) else {}
        stage_b_gates = stage_b.get("ecology_gates", {}) if isinstance(stage_b, Mapping) else {}
        funnel = funnel_by_seed.get(int(seed_row.get("seed", 0)), {})
        rows.append(
            {
                "seed": int(seed_row.get("seed", 0)),
                "stop_reasons": list(seed_row.get("stop_reasons", ())),
                "nominated": int(funnel.get("nominated", 0)),
                "confirmed": int(funnel.get("confirmed", 0)),
                "demoted": int(funnel.get("demoted", 0)),
                "parked": int(funnel.get("parked", 0)),
                "trial_count": int(population.get("trial_count", 0)),
                "probation_count": int(population.get("probation_count", 0)),
                "mature_count": int(population.get("mature_count", 0)),
                "pruned_count": int(population.get("pruned_count", 0)),
                "stage_b_population_curve": [
                    {
                        "step": int(curve.get("step", 0)),
                        "trial": int(curve.get("trial", 0)),
                        "probation": int(curve.get("probation", 0)),
                        "mature": int(curve.get("mature", 0)),
                        "pruned": int(curve.get("pruned", 0)),
                    }
                    for curve in seed_row.get("birth_death_curve", ())
                    if curve.get("segment") == "stage_b_chase"
                ],
                "stage_b_probation_stats": dict(stage_b_training.get("probation_confirmation_stats", {})) if isinstance(stage_b_training, Mapping) else {},
                "stage_b_host_plus_confirmed_wins": _phase42_nested_int(stage_b_gates, ("mature_eval", "wins")),
                "stage_b_host_wins": _phase42_nested_int(stage_b, ("host_gate", "wins")),
                "stage_b_confirmed_minus_host": int(stage_b_gates.get("mature_minus_host_wins", 0)) if stage_b_gates else None,
            }
        )
    return rows


def _phase49_noop_control_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed_row in per_seed:
        control = seed_row.get("noop_ablation_control", {})
        if not isinstance(control, Mapping):
            control = {}
        rows.append(
            {
                "seed": int(seed_row.get("seed", 0)),
                "flat_seed": int(seed_row.get("flat_seed", 0)),
                "stop_reasons": list(seed_row.get("stop_reasons", ())),
                "control_available": bool(control),
                "passed": bool(control.get("passed", False)),
                "subject_count": int(control.get("subject_count", 0)),
                "nonzero_offset_count": int(control.get("nonzero_offset_count", 0)),
                "offset_min": control.get("offset_min"),
                "offset_median": control.get("offset_median"),
                "offset_max": control.get("offset_max"),
                "verdict": str(control.get("verdict", "not_run")),
            }
        )
    return rows


def _phase49_noop_config_diff_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[tuple[str, str], ...]] = set()
    for seed_row in per_seed:
        control = seed_row.get("noop_ablation_control", {})
        if not isinstance(control, Mapping):
            continue
        diff = control.get("config_diff", {})
        if not isinstance(diff, Mapping):
            continue
        key = tuple(sorted((str(k), str(v)) for k, v in diff.items()))
        if key in seen:
            continue
        seen.add(key)
        rows.append({str(k): v for k, v in sorted(diff.items())})
    return rows


def _phase49_noop_control_verdict(table: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    available = [row for row in table if bool(row.get("control_available"))]
    nonzero_total = sum(int(row.get("nonzero_offset_count", 0)) for row in available)
    subject_total = sum(int(row.get("subject_count", 0)) for row in available)
    passed = bool(available) and subject_total > 0 and nonzero_total == 0
    return {
        "passed": passed,
        "control_seed_count": len(available),
        "subject_count": subject_total,
        "nonzero_offset_count": nonzero_total,
        "verdict": "pass_no_offset" if passed else "fail_runner_provenance_offset",
    }


def _phase49_dose_response_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed_row in per_seed:
        records = _phase48_probation_records(seed_row)
        decisions = Counter(str(record.get("decision", "unknown")) for record in records)
        classes = Counter(str(record.get("decision_class", "legacy")) for record in records)
        confirmed_doses = Counter(
            str(record.get("confirmed_dose_multiplier"))
            for record in records
            if record.get("confirmed_dose_multiplier") is not None
        )
        dose_tests = 0
        dose_discordants: list[int] = []
        for record in records:
            for dose_record in record.get("dose_records", ()):
                dose_tests += 1
                dose_discordants.append(int(dose_record.get("discordant_delta", 0)))
        rows.append(
            {
                "seed": int(seed_row.get("seed", 0)),
                "probation_tests": len(records),
                "dose_tests": dose_tests,
                "confirmed": int(decisions["confirmed"]),
                "demoted": int(decisions["demoted"]),
                "parked": int(decisions["parked"]),
                "decision_classes": dict(sorted(classes.items())),
                "confirmed_doses": dict(sorted(confirmed_doses.items())),
                "min_dose_discordant": min(dose_discordants) if dose_discordants else None,
                "max_dose_discordant": max(dose_discordants) if dose_discordants else None,
                "nonzero_dose_discordants": sum(1 for value in dose_discordants if value != 0),
            }
        )
    return rows


def _phase49_outcome_agreement_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed_row in per_seed:
        segments = [
            ("foundation", seed_row.get("foundation_ecology_training", {})),
        ]
        stage_a = seed_row.get("stage_a", {}) if isinstance(seed_row.get("stage_a"), Mapping) else {}
        stage_b = seed_row.get("stage_b", {}) if isinstance(seed_row.get("stage_b"), Mapping) else {}
        segments.append(("stage_a", stage_a.get("ecology_training", {})))
        segments.append(("stage_b", stage_b.get("ecology_training", {})))
        for segment_name, training in segments:
            if not isinstance(training, Mapping) or not training:
                continue
            counts = {
                str(key): int(value)
                for key, value in dict(training.get("first_flip_vs_outcome_counts", {})).items()
            }
            total = sum(counts.values())
            agreement = sum(
                value
                for key, value in counts.items()
                if "->" in key and key.split("->", 1)[0] == key.split("->", 1)[1]
            )
            rows.append(
                {
                    "seed": int(seed_row.get("seed", 0)),
                    "segment": segment_name,
                    "outcome_auditions": total,
                    "agreement_count": agreement,
                    "agreement_rate": agreement / max(1, total),
                    "counts": counts,
                    "outcome_verdict_counts": dict(training.get("outcome_audition_verdict_counts", {})),
                    "first_flip_verdict_counts": dict(training.get("audition_verdict_counts", {})),
                }
            )
    return rows


def _phase49_weighted_outcome_agreement(table: Sequence[Mapping[str, Any]]) -> float:
    total = sum(int(row.get("outcome_auditions", 0)) for row in table)
    agreement = sum(int(row.get("agreement_count", 0)) for row in table)
    return agreement / max(1, total)


def _phase45_composite_correspondence_table() -> list[dict[str, Any]]:
    return [
        {
            "concept": "safe rook reposition",
            "phase2_9e_survivor": "rook_attacked_after=0 AND to_file_edge_distance=2",
            "phase3_14_survivor": "rook_attacked_after=0 AND to_rank_edge_distance=2",
            "interpretation": "safe rook move onto a working edge-distance file/rank under different substrate/economy/opponent",
        },
        {
            "concept": "confinement",
            "phase2_9e_survivor": "bk_neighbor_ne_available=zero AND bk_neighbor_se_available=zero",
            "phase3_14_survivor": "bk_neighbor_s_available=zero AND bk_neighbor_w_available=zero",
            "interpretation": "two black-king escape squares sealed; orientation differs but conjunction family recurs",
        },
    ]


def _phase41_gate_margin_wins() -> int:
    return 3


def _phase41_margin_for_count(row_count: int) -> int:
    return max(1, round(int(row_count) * _phase41_gate_margin_wins() / 128))


def _phase41_paired_outcome_table(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    margin_wins: int,
    label: str,
) -> dict[str, Any]:
    left_rows = {str(key): bool(value) for key, value in left.get("success_by_row", {}).items()}
    right_rows = {str(key): bool(value) for key, value in right.get("success_by_row", {}).items()}
    common = sorted(set(left_rows) & set(right_rows), key=lambda item: int(item))
    counts = Counter()
    for row_id in common:
        pair = (left_rows[row_id], right_rows[row_id])
        if pair == (True, True):
            counts["win_win"] += 1
        elif pair == (True, False):
            counts["win_loss"] += 1
        elif pair == (False, True):
            counts["loss_win"] += 1
        else:
            counts["loss_loss"] += 1
    left_wins = int(sum(int(left_rows[row_id]) for row_id in common))
    right_wins = int(sum(int(right_rows[row_id]) for row_id in common))
    discordant_delta = int(counts["win_loss"]) - int(counts["loss_win"])
    left_minus_right = left_wins - right_wins
    return {
        "label": label,
        "left_policy": str(left.get("policy", "left")),
        "right_policy": str(right.get("policy", "right")),
        "paired_row_count": len(common),
        "left_wins": left_wins,
        "right_wins": right_wins,
        "left_minus_right_wins": left_minus_right,
        "win_win": int(counts["win_win"]),
        "win_loss": int(counts["win_loss"]),
        "loss_win": int(counts["loss_win"]),
        "loss_loss": int(counts["loss_loss"]),
        "discordant_delta_left_minus_right": discordant_delta,
        "discordants_favor_left": discordant_delta > 0,
        "non_inferiority_margin_wins": int(margin_wins),
        "non_inferior": left_minus_right >= -int(margin_wins),
        "passed": bool(discordant_delta > 0 or left_minus_right >= -int(margin_wins)),
    }


def _phase41_gate_result_paired(
    *,
    rung: str,
    learner: Mapping[str, Any],
    flat: Mapping[str, Any],
    margin_wins: int,
) -> dict[str, Any]:
    paired = _phase41_paired_outcome_table(
        learner,
        flat,
        margin_wins=margin_wins,
        label=f"{rung}_learner_vs_flat",
    )
    return {
        "rung": rung,
        "wins": int(learner["wins"]),
        "baseline_wins": int(flat["wins"]),
        "delta_vs_executable_flat": int(learner["wins"]) - int(flat["wins"]),
        "row_count": int(learner["row_count"]),
        "passed": bool(paired["passed"]),
        "endpoint_counts": dict(learner["endpoint_counts"]),
        "paired_gate": paired,
    }


def _phase41_calibrate_phase310_paired_gates(margin_wins: int) -> dict[str, Any]:
    path = Path("reports/autogrowth/clean_slate_krk/phase3_10_stratified_acceptance/summary.json")
    if not path.exists():
        return {"enabled": False, "reason": f"missing artifact: {path}"}
    prior = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for seed_result in prior.get("per_seed", ()):
        seed = int(seed_result["seed"])
        stage_a = seed_result.get("stage_a")
        if stage_a:
            flat = seed_result["baselines"]["stage_a_exact_adversarial_flat_gate"]
            paired = _phase41_paired_outcome_table(
                stage_a["gate_evaluation"],
                flat,
                margin_wins=margin_wins,
                label="phase3_10_stage_a_gate_recomputed",
            )
            rows.append(
                {
                    "seed": seed,
                    "rung": "stage_a",
                    "old_total_gate_passed": bool(stage_a["gate"]["passed"]),
                    "paired_gate_passed": bool(paired["passed"]),
                    "paired_gate": paired,
                    "interpretation": (
                        "noise_level_parity" if paired["passed"] and not stage_a["gate"]["passed"]
                        else "still_regressing" if not paired["passed"]
                        else "passed_under_both"
                    ),
                }
            )
        stage_b = seed_result.get("stage_b")
        if stage_b:
            flat = seed_result["baselines"]["stage_b_exact_adversarial_flat_gate"]
            paired = _phase41_paired_outcome_table(
                stage_b["gate_evaluation"],
                flat,
                margin_wins=margin_wins,
                label="phase3_10_stage_b_gate_recomputed",
            )
            rows.append(
                {
                    "seed": seed,
                    "rung": "stage_b",
                    "old_total_gate_passed": bool(stage_b["gate"]["passed"]),
                    "paired_gate_passed": bool(paired["passed"]),
                    "paired_gate": paired,
                    "interpretation": (
                        "noise_level_parity" if paired["passed"] and not stage_b["gate"]["passed"]
                        else "still_regressing" if not paired["passed"]
                        else "passed_under_both"
                    ),
                }
            )
    return {
        "enabled": True,
        "source_artifact": str(path),
        "margin_wins": int(margin_wins),
        "rows": rows,
        "seed31_33_stage_a_interpretation": {
            str(row["seed"]): row["interpretation"]
            for row in rows
            if row["rung"] == "stage_a" and int(row["seed"]) in {20272931, 20272933}
        },
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


def _phase40_stratified_train_validation_split(
    cfg: StageBEcologicalDiscoveryConfig,
    rows: Sequence[Mapping[str, Any]],
    *,
    atom_weights: Mapping[str, float],
    flat_seed: int,
    seed: int,
    success_kind: str,
    policy_name: str,
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]], dict[str, Any]]:
    pool = list(rows)
    if len(pool) <= 1:
        return pool, list(pool), {
            "stratifier_policy": policy_name,
            "endpoint_counts": {},
            "validation_endpoint_counts": {},
            "fallback": "pool_too_small",
        }
    traces = _phase38_flat_policy_traces(
        cfg,
        pool,
        atom_weights=atom_weights,
        flat_seed=flat_seed,
        seed=int(seed) + 404,
        policy_name=policy_name,
        success_kind=success_kind,
    )
    by_endpoint: dict[str, list[Mapping[str, Any]]] = {}
    rows_by_id = {str(row["row_id"]): row for row in pool}
    for row_id, endpoint in traces.get("endpoint_by_row", {}).items():
        row = rows_by_id.get(str(row_id))
        if row is None:
            continue
        by_endpoint.setdefault(str(endpoint), []).append(row)
    rng = random.Random(seed)
    for bucket in by_endpoint.values():
        rng.shuffle(bucket)
    validation_target = max(1, min(len(pool) - 1, max(16, len(pool) // 3)))
    priority = [
        "rook_lost",
        "stalemate",
        "illegal",
        "third_repetition",
        "fence_broken",
        "horizon",
        "terminal",
        "waypoint_reached",
        "ungated_exact_mate3_or_better_confirmed",
        "mate_delivered",
    ]
    validation_ids: set[int] = set()
    validation: list[Mapping[str, Any]] = []

    def take(row: Mapping[str, Any]) -> None:
        row_id = int(row["row_id"])
        if row_id in validation_ids or len(validation) >= validation_target:
            return
        validation_ids.add(row_id)
        validation.append(row)

    per_hard_family = max(2, validation_target // 8)
    for endpoint in priority[:6]:
        for row in by_endpoint.get(endpoint, ())[:per_hard_family]:
            take(row)
    cursor = 0
    while len(validation) < validation_target and by_endpoint:
        endpoint = priority[cursor % len(priority)]
        bucket = by_endpoint.get(endpoint, ())
        if bucket:
            take(bucket[(cursor // len(priority)) % len(bucket)])
        cursor += 1
        if cursor > len(priority) * (len(pool) + 1):
            break
    if len(validation) < validation_target:
        shuffled = list(pool)
        rng.shuffle(shuffled)
        for row in shuffled:
            take(row)
            if len(validation) >= validation_target:
                break
    train = [row for row in pool if int(row["row_id"]) not in validation_ids]
    validation_endpoint_counts = Counter(
        str(traces.get("endpoint_by_row", {}).get(str(row["row_id"]), "unknown"))
        for row in validation
    )
    return train, validation, {
        "stratifier_policy": policy_name,
        "stratifier_runner_config": traces.get("runner_config", {}),
        "endpoint_counts": dict(sorted(Counter(traces.get("endpoint_by_row", {}).values()).items())),
        "validation_endpoint_counts": dict(sorted(validation_endpoint_counts.items())),
        "validation_target": validation_target,
        "hard_endpoint_priority": priority[:6],
        "gate_rows_consulted_by_update_decisions": False,
    }


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


def _phase40_split_manifest(
    train_rows: Sequence[Mapping[str, Any]],
    validation_rows: Sequence[Mapping[str, Any]],
    gate_rows: Sequence[Mapping[str, Any]],
    split_diag: Mapping[str, Any],
) -> dict[str, Any]:
    manifest = _phase39_split_manifest(train_rows, validation_rows, gate_rows)
    manifest["split_strategy"] = "stratified_by_train_pool_initial_endpoint"
    manifest["stratification"] = dict(split_diag)
    return manifest


def _phase41_pool_manifest(
    train_pool_rows: Sequence[Mapping[str, Any]],
    gate_rows: Sequence[Mapping[str, Any]],
    pool_traces: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "train_pool_count": len(train_pool_rows),
        "gate_heldout_count": len(gate_rows),
        "train_pool_row_ids": [int(row["row_id"]) for row in train_pool_rows],
        "gate_heldout_row_ids": [int(row["row_id"]) for row in gate_rows],
        "train_gate_overlap": sorted(
            set(int(row["row_id"]) for row in train_pool_rows)
            & set(int(row["row_id"]) for row in gate_rows)
        ),
        "train_pool_endpoint_counts": dict(sorted(Counter(pool_traces.get("endpoint_by_row", {}).values()).items())),
        "gate_rows_consulted_by_update_decisions": False,
        "validation_strategy": "fresh endpoint-stratified fold per chunk from train pool",
    }


def _phase41_validation_target_count(rows: Sequence[Mapping[str, Any]]) -> int:
    if len(rows) <= 1:
        return len(rows)
    return max(16, min(len(rows) - 1, len(rows) // 3))


def _phase41_chunk_size(rows: Sequence[Mapping[str, Any]]) -> int:
    if not rows:
        return 1
    return max(1, (len(rows) + 11) // 12)


def _phase41_stratified_fold_from_endpoint_map(
    rows: Sequence[Mapping[str, Any]],
    endpoint_by_row: Mapping[str, Any],
    *,
    seed: int,
    excluded_row_ids: set[int],
    target_count: int,
) -> tuple[list[Mapping[str, Any]], dict[str, Any]]:
    pool = [row for row in rows if int(row["row_id"]) not in excluded_row_ids]
    if len(pool) <= target_count:
        selected = list(pool)
    else:
        by_endpoint: dict[str, list[Mapping[str, Any]]] = {}
        for row in pool:
            endpoint = str(endpoint_by_row.get(str(row["row_id"]), "unknown"))
            by_endpoint.setdefault(endpoint, []).append(row)
        rng = random.Random(seed)
        for bucket in by_endpoint.values():
            rng.shuffle(bucket)
        priority = [
            "rook_lost",
            "stalemate",
            "illegal",
            "third_repetition",
            "fence_broken",
            "horizon",
            "terminal",
            "waypoint_reached",
            "ungated_exact_mate3_or_better_confirmed",
            "mate_delivered",
            "unknown",
        ]
        selected_ids: set[int] = set()
        selected = []

        def take(row: Mapping[str, Any]) -> None:
            row_id = int(row["row_id"])
            if row_id in selected_ids or len(selected) >= target_count:
                return
            selected_ids.add(row_id)
            selected.append(row)

        per_hard_family = max(2, target_count // 8)
        for endpoint in priority[:6]:
            for row in by_endpoint.get(endpoint, ())[:per_hard_family]:
                take(row)
        cursor = 0
        while len(selected) < target_count and by_endpoint:
            endpoint = priority[cursor % len(priority)]
            bucket = by_endpoint.get(endpoint, ())
            if bucket:
                take(bucket[(cursor // len(priority)) % len(bucket)])
            cursor += 1
            if cursor > len(priority) * (len(pool) + 1):
                break
        if len(selected) < target_count:
            shuffled = list(pool)
            rng.shuffle(shuffled)
            for row in shuffled:
                take(row)
                if len(selected) >= target_count:
                    break
    endpoint_counts = Counter(str(endpoint_by_row.get(str(row["row_id"]), "unknown")) for row in selected)
    return selected, {
        "validation_count": len(selected),
        "validation_row_ids": [int(row["row_id"]) for row in selected],
        "validation_endpoint_counts": dict(sorted(endpoint_counts.items())),
        "excluded_row_ids": sorted(excluded_row_ids),
        "gate_rows_consulted_by_update_decisions": False,
    }


def _phase41_train_credit_precision(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    provider: _MigratedStageBFlatGraphScoreProvider,
    train_pool_rows: Sequence[Mapping[str, Any]],
    pool_endpoint_by_row: Mapping[str, Any],
    prior_replay_checks: Sequence[Mapping[str, Any]],
    seed: int,
    success_kind: str,
    rung_name: str,
) -> dict[str, Any]:
    ordered = list(train_pool_rows)
    random.Random(seed).shuffle(ordered)
    chunk_size = _phase41_chunk_size(ordered)
    chunks = [ordered[index : index + chunk_size] for index in range(0, len(ordered), chunk_size)][:12]
    chunk_records: list[dict[str, Any]] = []
    accepted = 0
    rejected = 0
    total_updates = 0
    flip_identified = 0
    hard_fail_episodes = 0
    for chunk_index, chunk in enumerate(chunks):
        excluded = {int(row["row_id"]) for row in chunk}
        validation_rows, validation_fold = _phase41_stratified_fold_from_endpoint_map(
            train_pool_rows,
            pool_endpoint_by_row,
            seed=int(seed) + chunk_index * 1009,
            excluded_row_ids=excluded,
            target_count=_phase41_validation_target_count(train_pool_rows),
        )
        validation_before = _phase38_migrated_provider_traces(
            cfg,
            validation_rows,
            provider,
            seed=int(seed) + chunk_index * 1000 + 1,
            policy_name=f"phase3_11_{rung_name}_validation_before_chunk_{chunk_index}",
            success_kind=success_kind,
        )
        prior_before = _phase39_eval_prior_replays(prior_replay_checks)
        slow_snapshot = _phase39_snapshot_provider_weights(provider)
        chunk_train = _phase41_apply_contrastive_fast_chunk_localized(
            cfg,
            provider,
            chunk,
            seed=int(seed) + chunk_index * 1000 + 101,
            success_kind=success_kind,
        )
        total_updates += int(chunk_train["weight_update_count"])
        flip_identified += int(chunk_train["flip_ply_identified_count"])
        hard_fail_episodes += int(chunk_train["hard_fail_episode_count"])
        validation_after = _phase38_migrated_provider_traces(
            cfg,
            validation_rows,
            provider,
            seed=int(seed) + chunk_index * 1000 + 2,
            policy_name=f"phase3_11_{rung_name}_validation_after_chunk_{chunk_index}",
            success_kind=success_kind,
        )
        prior_after = _phase39_eval_prior_replays(prior_replay_checks)
        validation_delta = _phase39_eval_delta(validation_before, validation_after)
        validation_margin = _phase41_margin_for_count(len(validation_rows))
        validation_paired = _phase41_paired_outcome_table(
            validation_after,
            validation_before,
            margin_wins=validation_margin,
            label=f"{rung_name}_validation_after_vs_before_chunk_{chunk_index}",
        )
        prior_deltas = {
            name: _phase39_eval_delta(prior_before[name], prior_after[name])
            for name in prior_after
        }
        prior_paired = {
            name: _phase41_paired_outcome_table(
                prior_after[name],
                prior_before[name],
                margin_wins=_phase41_margin_for_count(int(prior_after[name]["row_count"])),
                label=f"{rung_name}_{name}_after_vs_before_chunk_{chunk_index}",
            )
            for name in prior_after
        }
        validation_endpoint_pass = _phase40_acceptance_delta_pass(
            validation_delta,
            endpoint_non_regression=True,
        )
        prior_endpoint_passes = {
            name: _phase40_acceptance_delta_pass(delta, endpoint_non_regression=True)
            for name, delta in prior_deltas.items()
        }
        accepted_chunk = (
            bool(validation_paired["passed"])
            and validation_endpoint_pass
            and all(bool(item["passed"]) for item in prior_paired.values())
            and all(prior_endpoint_passes.values())
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
                "reason": "paired_endpoint_non_regression_passed" if accepted_chunk else "paired_or_endpoint_regressed",
                "training": chunk_train,
                "validation_fold": validation_fold,
                "validation_delta": validation_delta,
                "validation_paired": validation_paired,
                "validation_endpoint_acceptance_pass": validation_endpoint_pass,
                "prior_replay_deltas": prior_deltas,
                "prior_replay_paired": prior_paired,
                "prior_replay_endpoint_acceptance_passes": prior_endpoint_passes,
            }
        )
    near_miss = _phase39_near_miss(chunk_records)
    return {
        "rung": rung_name,
        "success_kind": success_kind,
        "black_reply_policy": "exact_adversarial",
        "train_pool_row_count": len(train_pool_rows),
        "chunk_size": chunk_size,
        "chunk_budget": 12,
        "chunk_count": len(chunks),
        "chunks_consolidated": accepted,
        "chunks_rejected": rejected,
        "weight_update_count": total_updates,
        "m3_m4_restored": True,
        "gate_heldout_consulted": False,
        "fresh_validation_fold_per_chunk": True,
        "paired_acceptance": True,
        "endpoint_non_regression_required": True,
        "flip_ply_identified_count": flip_identified,
        "hard_fail_episode_count": hard_fail_episodes,
        "flip_ply_identification_rate": flip_identified / max(1, hard_fail_episodes),
        "near_miss_margins": near_miss,
        "chunk_records": chunk_records,
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
    endpoint_non_regression: bool = False,
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
        validation_pass = _phase40_acceptance_delta_pass(
            validation_delta,
            endpoint_non_regression=endpoint_non_regression,
        )
        prior_passes = {
            name: _phase40_acceptance_delta_pass(
                delta,
                endpoint_non_regression=endpoint_non_regression,
            )
            for name, delta in prior_deltas.items()
        }
        accepted_chunk = validation_pass and all(prior_passes.values())
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
                "reason": (
                    "endpoint_aware_non_regression_passed"
                    if accepted_chunk and endpoint_non_regression
                    else "non_regression_passed"
                    if accepted_chunk
                    else "validation_or_prior_replay_regressed"
                ),
                "training": chunk_train,
                "validation_delta": validation_delta,
                "validation_acceptance_pass": validation_pass,
                "prior_replay_acceptance_passes": prior_passes,
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
        "endpoint_non_regression_required": endpoint_non_regression,
        "acceptance_endpoint_keys": list(_PHASE40_HARD_ENDPOINTS),
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


def _phase41_apply_contrastive_fast_chunk_localized(
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
    hard_fail_episode_count = 0
    flip_ply_identified_count = 0
    localized_negative_update_count = 0
    fallback_negative_update_count = 0
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
        for outcome in (selected_out, alternative_out):
            if str(outcome.get("endpoint")) in {"fence_broken", "rook_lost"}:
                hard_fail_episode_count += 1
                if _phase41_flip_credit_targets(provider, outcome):
                    flip_ply_identified_count += 1
        endpoint_pairs[f"{selected_out['endpoint']}|{alternative_out['endpoint']}"] += 1
        reward_delta = float(selected_out["reward"]) - float(alternative_out["reward"])
        if reward_delta > 0:
            selected_better += 1
            better_move = selected
            worse_move = alternative
            worse_out = alternative_out
        elif reward_delta < 0:
            alternative_better += 1
            better_move = alternative
            worse_move = selected
            worse_out = selected_out
        else:
            tied += 1
            continue
        scaled_lr = learning_rate * min(1.0, abs(reward_delta) / 12.0)
        better_keys = _phase39_active_weighted_keys(provider, board, better_move)
        for key in better_keys:
            provider.adjust_atom_weight(key, scaled_lr)
            update_count += 1
        targets = _phase41_flip_credit_targets(provider, worse_out)
        if targets:
            for target in targets:
                for key in target["active_weighted_keys"]:
                    provider.adjust_atom_weight(key, -scaled_lr * float(target["discount"]))
                    update_count += 1
                    localized_negative_update_count += 1
        else:
            worse_keys = _phase39_active_weighted_keys(provider, board, worse_move)
            for key in worse_keys:
                provider.adjust_atom_weight(key, -scaled_lr)
                update_count += 1
                fallback_negative_update_count += 1
        if len(samples) < int(cfg.max_samples):
            samples.append(
                {
                    "row_id": int(row["row_id"]),
                    "selected": selected.uci(),
                    "alternative": alternative.uci(),
                    "selected_endpoint": selected_out["endpoint"],
                    "alternative_endpoint": alternative_out["endpoint"],
                    "reward_delta": round(reward_delta, 6),
                    "worse_flip_targets": targets,
                    "localized_credit_used": bool(targets),
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
        "hard_fail_episode_count": hard_fail_episode_count,
        "flip_ply_identified_count": flip_ply_identified_count,
        "flip_ply_identification_rate": flip_ply_identified_count / max(1, hard_fail_episode_count),
        "localized_negative_update_count": localized_negative_update_count,
        "fallback_negative_update_count": fallback_negative_update_count,
        "samples": samples,
    }


def _phase41_flip_credit_targets(
    provider: _MigratedStageBFlatGraphScoreProvider,
    outcome: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if str(outcome.get("endpoint")) not in {"fence_broken", "rook_lost"}:
        return []
    transitions = [
        item for item in outcome.get("transition_steps", ())
        if isinstance(item, Mapping)
    ]
    flip_index: int | None = None
    flip_reason = ""
    for index, step in enumerate(transitions):
        before_fence = bool(step.get("before_fence_established"))
        after_white_fence = step.get("after_white_fence_established")
        after_black_fence = step.get("after_black_fence_established")
        before_rook = bool(step.get("before_rook_present"))
        after_white_rook = step.get("after_white_rook_present")
        after_black_rook = step.get("after_black_rook_present")
        if before_rook and after_white_rook is False:
            flip_index = index
            flip_reason = "rook_lost_after_white"
            break
        if after_white_rook is True and after_black_rook is False:
            flip_index = index
            flip_reason = "rook_lost_after_black"
            break
        if before_fence and after_white_fence is False:
            flip_index = index
            flip_reason = "fence_broken_after_white"
            break
        if after_white_fence is True and after_black_fence is False:
            flip_index = index
            flip_reason = "fence_broken_after_black"
            break
    if flip_index is None:
        return []
    discounts = ((flip_index, 1.0), (flip_index - 1, 0.5), (flip_index - 2, 0.25))
    targets: list[dict[str, Any]] = []
    for target_index, discount in discounts:
        if target_index < 0 or target_index >= len(transitions):
            continue
        step = transitions[target_index]
        before_fen = step.get("before_fen")
        move_uci = step.get("white_move")
        if not before_fen or not move_uci:
            continue
        board = chess.Board(str(before_fen))
        move = chess.Move.from_uci(str(move_uci))
        keys = _phase39_active_weighted_keys(provider, board, move)
        if not keys:
            continue
        targets.append(
            {
                "ply": int(step.get("ply", target_index)),
                "move": move.uci(),
                "discount": float(discount),
                "flip_reason": flip_reason if target_index == flip_index else "pre_flip_discount",
                "active_weighted_keys": list(keys),
            }
        )
    return targets


def _phase42_train_ecology_segment(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    runtime: _GraphNativeCompositeRuntime,
    score_provider: Any,
    rows: Sequence[Mapping[str, Any]],
    segment_name: str,
    success_kind: str,
    seed: int,
    step_offset: int,
) -> dict[str, Any]:
    judge_cache = _new_judge_cache()
    endpoints: Counter[str] = Counter()
    success_by_row: dict[str, bool] = {}
    endpoint_by_row: dict[str, str] = {}
    trace_sample: list[dict[str, Any]] = []
    positive_flip_rows = 0
    positive_flip_credit_events = 0
    requested_total = 0
    active_total = 0
    changed_base_choice_count = 0
    for index, row in enumerate(rows):
        row_decisions: list[dict[str, Any]] = []

        def choose(board: chess.Board, counts: Mapping[Any, int], row_id: int, ply: int, rng: random.Random) -> chess.Move | None:
            base_scores = score_provider(board, counts)
            options = _score_options(
                board,
                counts,
                atom_weights={},
                base_move_scores=base_scores,
                composites=(),
                disabled_composite_ids=set(),
            )
            if options:
                ctx = _decision_context(
                    cfg,
                    board,
                    counts,
                    options,
                    seed=int(seed) + index * 1000 + ply,
                    row_id=row_id,
                    ply=ply,
                    segment_name=segment_name,
                )
                _real_native_spawn_from_context(
                    cfg,
                    runtime,
                    ctx,
                    rng=random.Random(int(seed) + index * 1009 + ply),
                )
            selected = runtime.choose_move(
                board,
                counts,
                score_provider,
                seed=int(seed) + int(row_id) * 47 + ply,
            )
            move = selected.get("move")
            base_move = selected.get("base_move")
            changed = bool(move is not None and base_move is not None and move != base_move)
            nonlocal requested_total, active_total, changed_base_choice_count
            requested_total += len(selected.get("requested_composite_ids", ()))
            active_total += len(selected.get("active_composite_ids", ()))
            changed_base_choice_count += int(changed)
            runtime.apply_local_credit(
                requested_ids=selected.get("requested_composite_ids", ()),
                active_ids=selected.get("active_composite_ids", ()),
                changed_base_choice=changed,
                step=int(step_offset) + index * 100 + ply,
            )
            row_decisions.append(
                {
                    "ply": int(ply),
                    "move": None if move is None else move.uci(),
                    "base_move": None if base_move is None else base_move.uci(),
                    "changed_base_choice": changed,
                    "requested_composite_ids": list(selected.get("requested_composite_ids", ())),
                    "active_composite_ids": list(selected.get("active_composite_ids", ())),
                }
            )
            return move

        outcome = _rollout_policy(
            cfg,
            row,
            choose,
            seed=int(seed) + index * 31,
            policy_name=f"phase3_12_{segment_name}_ecology_train",
            judge_cache=judge_cache,
            success_kind=success_kind,
            black_reply_policy="exact_adversarial",
        )
        flip_targets = _phase42_positive_flip_targets(cfg, outcome, row_decisions, success_kind=success_kind)
        if flip_targets:
            positive_flip_rows += 1
            for target in flip_targets:
                positive_flip_credit_events += runtime.apply_positive_flip_nutrition(
                    active_ids=target["active_composite_ids"],
                    step=int(step_offset) + index * 100 + int(target["ply"]),
                    reason=str(target["reason"]),
                    discount=float(target["discount"]),
                )
        endpoints[str(outcome["endpoint"])] += 1
        success_by_row[str(row["row_id"])] = bool(outcome["success"])
        endpoint_by_row[str(row["row_id"])] = str(outcome["endpoint"])
        if index % 8 == 0 or index == len(rows) - 1:
            runtime.snapshot(step=int(step_offset) + index, segment=segment_name)
        if len(trace_sample) < int(cfg.max_samples):
            trace_sample.append(
                {
                    "row_id": int(row["row_id"]),
                    "endpoint": str(outcome["endpoint"]),
                    "success": bool(outcome["success"]),
                    "white_step_count": len(outcome.get("white_steps", ())),
                    "positive_flip_targets": flip_targets,
                    "decisions": row_decisions[: int(cfg.max_samples)],
                }
            )
    return {
        "segment": segment_name,
        "row_count": len(rows),
        "success_kind": success_kind,
        "black_reply_policy": "exact_adversarial",
        "endpoint_counts": dict(sorted(endpoints.items())),
        "success_by_row": success_by_row,
        "endpoint_by_row": endpoint_by_row,
        "positive_flip_row_count": positive_flip_rows,
        "positive_flip_credit_event_count": positive_flip_credit_events,
        "requested_composite_count": requested_total,
        "active_composite_count": active_total,
        "changed_base_choice_count": changed_base_choice_count,
        "population_snapshot": runtime.population_summary(),
        "runner_config": _phase38_runner_config(
            cfg,
            seed=int(seed),
            success_kind=success_kind,
            black_reply_policy="exact_adversarial",
            row_count=len(rows),
        ),
        "trace_sample": trace_sample,
    }


def _phase43_train_discriminative_ecology_segment(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    runtime: _GraphNativeCompositeRuntime,
    score_provider: Any,
    rows: Sequence[Mapping[str, Any]],
    segment_name: str,
    success_kind: str,
    seed: int,
    step_offset: int,
) -> dict[str, Any]:
    judge_cache = _new_judge_cache()
    endpoints: Counter[str] = Counter()
    success_by_row: dict[str, bool] = {}
    endpoint_by_row: dict[str, str] = {}
    trace_sample: list[dict[str, Any]] = []
    decision_ply_count = 0
    choice_changed_count = 0
    responsible_cell_event_count = 0
    outcome_distribution: Counter[str] = Counter()
    changed_endpoint_distribution: Counter[str] = Counter()
    requested_total = 0
    active_total = 0
    blocked_before = sum(runtime.births_blocked_by_capacity.values())
    for index, row in enumerate(rows):
        row_decisions: list[dict[str, Any]] = []

        def choose(board: chess.Board, counts: Mapping[Any, int], row_id: int, ply: int, rng: random.Random) -> chess.Move | None:
            base_scores = score_provider(board, counts)
            options = _score_options(
                board,
                counts,
                atom_weights={},
                base_move_scores=base_scores,
                composites=(),
                disabled_composite_ids=set(),
            )
            if options:
                ctx = _decision_context(
                    cfg,
                    board,
                    counts,
                    options,
                    seed=int(seed) + index * 1000 + ply,
                    row_id=row_id,
                    ply=ply,
                    segment_name=segment_name,
                )
                _phase43_spawn_from_context(
                    cfg,
                    runtime,
                    ctx,
                    rng=random.Random(int(seed) + index * 1009 + ply),
                )
            selected = runtime.choose_move(
                board,
                counts,
                score_provider,
                seed=int(seed) + int(row_id) * 47 + ply,
                discriminative=True,
            )
            move = selected.get("move")
            nonlocal decision_ply_count, choice_changed_count, requested_total, active_total
            decision_ply_count += 1
            requested_total += len(selected.get("requested_composite_ids", ()))
            active_total += len(selected.get("active_composite_ids", ()))
            changed = bool(selected.get("choice_changed_by_cells"))
            choice_changed_count += int(changed)
            row_decisions.append(
                {
                    "ply": int(ply),
                    "move": None if move is None else move.uci(),
                    "host_move": None if selected.get("base_move") is None else selected["base_move"].uci(),
                    "choice_changed_by_cells": changed,
                    "responsible_composite_ids": list(selected.get("responsible_composite_ids", ())),
                    "requested_composite_ids": list(selected.get("requested_composite_ids", ())),
                    "active_composite_ids": list(selected.get("active_composite_ids", ())),
                    "responsibility_margin": selected.get("responsibility_margin"),
                    "selected_composite_score": selected.get("selected_composite_score"),
                }
            )
            return move

        outcome = _rollout_policy(
            cfg,
            row,
            choose,
            seed=int(seed) + index * 31,
            policy_name=f"phase3_13_{segment_name}_ecology_train",
            judge_cache=judge_cache,
            success_kind=success_kind,
            black_reply_policy="exact_adversarial",
        )
        flip_event = _phase43_first_flip_event(cfg, outcome, success_kind=success_kind)
        for decision in row_decisions:
            if not decision["choice_changed_by_cells"]:
                continue
            changed_endpoint_distribution[str(outcome["endpoint"])] += 1
            ply = int(decision["ply"])
            if flip_event and 0 <= int(flip_event["ply"]) - ply <= int(cfg.real_native_positive_flip_window):
                valence = str(flip_event["valence"])
                outcome_key = "achievement_flip" if valence == "positive" else "failure_flip"
                discount = 1.0 if int(flip_event["ply"]) == ply else 0.5 if int(flip_event["ply"]) - ply == 1 else 0.25
                responsible_cell_event_count += runtime.apply_choice_change_attribution(
                    responsible_ids=decision["responsible_composite_ids"],
                    valence=valence,
                    step=int(step_offset) + index * 100 + ply,
                    reason=str(flip_event["reason"]),
                    discount=discount,
                )
            else:
                outcome_key = "neutral_no_flip"
                responsible_cell_event_count += runtime.apply_choice_change_attribution(
                    responsible_ids=decision["responsible_composite_ids"],
                    valence="neutral",
                    step=int(step_offset) + index * 100 + ply,
                    reason="changed_choice_without_flip_in_eligibility_window",
                    discount=1.0,
                )
            outcome_distribution[outcome_key] += 1
        endpoints[str(outcome["endpoint"])] += 1
        success_by_row[str(row["row_id"])] = bool(outcome["success"])
        endpoint_by_row[str(row["row_id"])] = str(outcome["endpoint"])
        if index % 8 == 0 or index == len(rows) - 1:
            runtime.snapshot(step=int(step_offset) + index, segment=segment_name)
        if len(trace_sample) < int(cfg.max_samples):
            trace_sample.append(
                {
                    "row_id": int(row["row_id"]),
                    "endpoint": str(outcome["endpoint"]),
                    "success": bool(outcome["success"]),
                    "flip_event": flip_event,
                    "white_step_count": len(outcome.get("white_steps", ())),
                    "decisions": row_decisions[: int(cfg.max_samples)],
                }
            )
    blocked_after = sum(runtime.births_blocked_by_capacity.values())
    return {
        "segment": segment_name,
        "row_count": len(rows),
        "success_kind": success_kind,
        "black_reply_policy": "exact_adversarial",
        "endpoint_counts": dict(sorted(endpoints.items())),
        "success_by_row": success_by_row,
        "endpoint_by_row": endpoint_by_row,
        "decision_ply_count": decision_ply_count,
        "choice_changed_ply_count": choice_changed_count,
        "choice_changed_ply_rate": choice_changed_count / max(1, decision_ply_count),
        "changed_choice_outcome_distribution": dict(sorted(outcome_distribution.items())),
        "changed_choice_endpoint_distribution": dict(sorted(changed_endpoint_distribution.items())),
        "responsible_cell_credit_event_count": responsible_cell_event_count,
        "requested_composite_count": requested_total,
        "active_composite_count": active_total,
        "births_blocked_by_capacity_delta": int(blocked_after - blocked_before),
        "births_blocked_by_capacity_total": int(blocked_after),
        "population_snapshot": runtime.population_summary(),
        "runner_config": _phase38_runner_config(
            cfg,
            seed=int(seed),
            success_kind=success_kind,
            black_reply_policy="exact_adversarial",
            row_count=len(rows),
        ),
        "trace_sample": trace_sample,
    }


def _phase44_train_audition_ecology_segment(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    runtime: _GraphNativeCompositeRuntime,
    score_provider: Any,
    rows: Sequence[Mapping[str, Any]],
    segment_name: str,
    success_kind: str,
    seed: int,
    step_offset: int,
) -> dict[str, Any]:
    judge_cache = _new_judge_cache()
    audition_judge_cache = _new_judge_cache()
    endpoints: Counter[str] = Counter()
    success_by_row: dict[str, bool] = {}
    endpoint_by_row: dict[str, str] = {}
    trace_sample: list[dict[str, Any]] = []
    decision_ply_count = 0
    choice_changed_count = 0
    requested_total = 0
    active_total = 0
    proposal_count = 0
    request_count = 0
    budget_skip_count = 0
    cap_skip_count = 0
    audition_count = 0
    audition_frames_spent = 0
    disagreement_ply_count = 0
    verdicts: Counter[str] = Counter()
    verdict_endpoints: Counter[str] = Counter()
    outcome_verdicts: Counter[str] = Counter()
    first_flip_vs_outcome: Counter[str] = Counter()
    scheduled_stats: Counter[str] = Counter()
    probation_stats: Counter[str] = Counter()
    probation_records: list[dict[str, Any]] = []
    firing_buffer: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    birth_deferred_stats: Counter[str] = Counter()
    backlog_curve: list[dict[str, Any]] = []
    complete_flush_report: dict[str, Any] = {}
    pool_scanned_cell_ids: set[str] = set()
    pool_supply_stats: Counter[str] = Counter()
    blocked_before = sum(runtime.births_blocked_by_capacity.values())
    for index, row in enumerate(rows):
        row_decisions: list[dict[str, Any]] = []

        def choose(board: chess.Board, counts: Mapping[Any, int], row_id: int, ply: int, rng: random.Random) -> chess.Move | None:
            base_scores = score_provider(board, counts)
            options = _score_options(
                board,
                counts,
                atom_weights={},
                base_move_scores=base_scores,
                composites=(),
                disabled_composite_ids=set(),
            )
            if options:
                ctx = _decision_context(
                    cfg,
                    board,
                    counts,
                    options,
                    seed=int(seed) + index * 1000 + ply,
                    row_id=row_id,
                    ply=ply,
                    segment_name=segment_name,
                )
                ctx["global_step"] = int(step_offset) + index * 100 + ply
                ctx["segment_row_index"] = int(index)
                if bool(getattr(cfg, "real_native_pool_scan_auditions", False)):
                    spawn_report = _phase47_spawn_from_context(
                        cfg,
                        runtime,
                        ctx,
                        rng=random.Random(int(seed) + index * 1009 + ply),
                    )
                else:
                    spawn_report = _phase46_spawn_from_context(
                        cfg,
                        runtime,
                        ctx,
                        rng=random.Random(int(seed) + index * 1009 + ply),
                    )
                birth_deferred_stats.update(spawn_report)
            selected = runtime.choose_move(
                board,
                counts,
                score_provider,
                seed=int(seed) + int(row_id) * 47 + ply,
                discriminative=True,
                include_trial_proposals=True,
            )
            move = selected.get("move")
            nonlocal decision_ply_count, choice_changed_count, requested_total, active_total
            nonlocal proposal_count, request_count, budget_skip_count, cap_skip_count
            nonlocal audition_count, audition_frames_spent, disagreement_ply_count
            nonlocal scheduled_stats
            decision_ply_count += 1
            requested_total += len(selected.get("requested_composite_ids", ()))
            active_total += len(selected.get("active_composite_ids", ()))
            changed = bool(selected.get("choice_changed_by_cells"))
            choice_changed_count += int(changed)
            proposals = [
                proposal for proposal in selected.get("trial_cell_proposals", ())
                if proposal.get("move") is not None and proposal.get("host_move") is not None
            ]
            firings = [
                firing for firing in selected.get("trial_cell_firings", ())
                if firing.get("move") is not None and firing.get("host_move") is not None
            ]
            for firing in firings:
                cid = str(firing["composite_id"])
                item = runtime.population.get(cid)
                if not item or item.get("state") != "TRIAL":
                    continue
                firing_buffer[cid].append(
                    {
                        "fen": board.fen(),
                        "counts": Counter(counts),
                        "host_move_uci": str(firing["host_move_uci"]),
                        "cell_move_uci": str(firing["move_uci"]),
                        "agrees_with_host": bool(firing.get("agrees_with_host", False)),
                        "row_id": int(row_id),
                        "ply": int(ply),
                    }
                )
            proposal_count += len(proposals)
            eligible: list[dict[str, Any]] = []
            for proposal in proposals:
                cid = str(proposal["composite_id"])
                item = runtime.population.get(cid)
                if not item or item.get("state") != "TRIAL":
                    continue
                if int(item.get("audition_count", 0)) >= int(cfg.real_native_audition_budget_per_cell):
                    budget_skip_count += 1
                    continue
                item["audition_requested_count"] = int(item.get("audition_requested_count", 0)) + 1
                request_count += 1
                eligible.append(proposal)
            sampled = eligible
            cap = int(cfg.real_native_audition_per_ply_cap)
            if cap > 0 and len(eligible) > cap:
                local_rng = random.Random(int(seed) + int(row_id) * 997 + ply)
                sampled = local_rng.sample(eligible, cap)
                cap_skip_count += len(eligible) - cap
            if sampled:
                disagreement_ply_count += 1
            audition_records: list[dict[str, Any]] = []
            for proposal in sampled:
                host_move = proposal["host_move"]
                cell_move = proposal["move"]
                audition = _phase44_run_audition_pair(
                    cfg,
                    board,
                    counts,
                    score_provider=score_provider,
                    host_move=host_move,
                    cell_move=cell_move,
                    success_kind=success_kind,
                    seed=int(seed) + int(row_id) * 7919 + ply * 101 + audition_count,
                    judge_cache=audition_judge_cache,
                )
                applied = _phase50_applied_audition_verdict(cfg, audition)
                verdict = str(applied["verdict"])
                verdicts[verdict] += 1
                verdict_endpoints[str(applied["verdict_reason"])] += 1
                outcome_verdict = audition.get("outcome_verdict")
                if outcome_verdict is not None:
                    outcome_verdicts[str(outcome_verdict)] += 1
                    first_flip_vs_outcome[f"{audition['verdict']}->{outcome_verdict}"] += 1
                audition_count += 1
                audition_frames_spent += int(audition["frames_spent"]) + int(audition.get("outcome_frames_spent", 0))
                before_state = str(runtime.population.get(str(proposal["composite_id"]), {}).get("state", "missing"))
                runtime.apply_audition_verdict(
                    composite_id=str(proposal["composite_id"]),
                    verdict=verdict,
                    step=int(step_offset) + index * 100 + ply,
                    reason=str(applied["verdict_reason"]),
                    frames_spent=int(applied["frames_spent"]),
                )
                after_state = str(runtime.population.get(str(proposal["composite_id"]), {}).get("state", "missing"))
                if before_state == "TRIAL" and after_state == "PROBATION":
                    probation_stats["probation_nominated_live_audition"] += 1
                if len(audition_records) < int(cfg.max_samples):
                    audition_records.append(
                        {
                            "composite_id": str(proposal["composite_id"]),
                            "host_move": host_move.uci(),
                            "cell_move": cell_move.uci(),
                            "verdict": verdict,
                            "verdict_reason": str(applied["verdict_reason"]),
                            "verdict_source": str(applied["verdict_source"]),
                            "first_flip_verdict": str(audition["verdict"]),
                            "first_flip_verdict_reason": str(audition["verdict_reason"]),
                            "outcome_verdict": audition.get("outcome_verdict"),
                            "outcome_verdict_reason": audition.get("outcome_verdict_reason"),
                            "host_flip": audition["host"].get("first_flip"),
                            "cell_flip": audition["cell"].get("first_flip"),
                            "frames_spent": int(audition["frames_spent"]) + int(audition.get("outcome_frames_spent", 0)),
                        }
                    )
            row_decisions.append(
                {
                    "ply": int(ply),
                    "move": None if move is None else move.uci(),
                    "host_move": None if selected.get("base_move") is None else selected["base_move"].uci(),
                    "choice_changed_by_cells": changed,
                    "trial_cell_firing_count": len(firings),
                    "trial_cell_proposal_count": len(proposals),
                    "audition_eligible_count": len(eligible),
                    "audition_run_count": len(sampled),
                    "auditions": audition_records,
                }
            )
            return move

        outcome = _rollout_policy(
            cfg,
            row,
            choose,
            seed=int(seed) + index * 31,
            policy_name=f"phase3_14_{segment_name}_ecology_train",
            judge_cache=judge_cache,
            success_kind=success_kind,
            black_reply_policy="exact_adversarial",
        )
        endpoints[str(outcome["endpoint"])] += 1
        success_by_row[str(row["row_id"])] = bool(outcome["success"])
        endpoint_by_row[str(row["row_id"])] = str(outcome["endpoint"])
        if index % 8 == 0 or index == len(rows) - 1:
            runtime.snapshot(step=int(step_offset) + index, segment=segment_name)
        chunk_size = int(getattr(cfg, "real_native_scheduled_audition_chunk_size", 0))
        if chunk_size > 0 and ((index + 1) % chunk_size == 0 or index == len(rows) - 1):
            if bool(getattr(cfg, "real_native_pool_scan_auditions", False)):
                new_targets = _phase47_pool_scan_targets(runtime, pool_scanned_cell_ids)
                supply = _phase47_collect_pool_firing_sets(
                    cfg,
                    runtime=runtime,
                    score_provider=score_provider,
                    rows=rows,
                    firing_buffer=firing_buffer,
                    target_ids=new_targets,
                    success_kind=success_kind,
                    seed=int(seed) + index * 10_003,
                )
                pool_scanned_cell_ids.update(new_targets)
                pool_supply_stats.update(supply["counter"])
                scheduled = _phase47_run_pool_scan_auditions(
                    cfg,
                    runtime=runtime,
                    score_provider=score_provider,
                    firing_buffer=firing_buffer,
                    success_kind=success_kind,
                    seed=int(seed) + index * 10_003,
                    step=int(step_offset) + index,
                    max_trace_samples=int(cfg.max_samples),
                )
            else:
                scheduled = _phase45_run_scheduled_auditions(
                    cfg,
                    runtime=runtime,
                    score_provider=score_provider,
                    firing_buffer=firing_buffer,
                    success_kind=success_kind,
                    seed=int(seed) + index * 10_003,
                    step=int(step_offset) + index,
                    max_trace_samples=int(cfg.max_samples),
                )
            scheduled_stats.update(scheduled["counter"])
            verdicts.update(scheduled["verdict_counts"])
            verdict_endpoints.update(scheduled["verdict_reason_counts"])
            outcome_verdicts.update(scheduled.get("outcome_verdict_counts", {}))
            first_flip_vs_outcome.update(scheduled.get("first_flip_vs_outcome_counts", {}))
            audition_count += int(scheduled["audition_count"])
            audition_frames_spent += int(scheduled["audition_frames_spent"])
            backlog_curve.append(
                _phase46_backlog_snapshot(
                    cfg,
                    runtime,
                    segment=segment_name,
                    step=int(step_offset) + index,
                    row_index=index,
                    event="scheduled_chunk",
                )
            )
        if len(trace_sample) < int(cfg.max_samples):
            trace_sample.append(
                {
                    "row_id": int(row["row_id"]),
                    "endpoint": str(outcome["endpoint"]),
                    "success": bool(outcome["success"]),
                    "white_step_count": len(outcome.get("white_steps", ())),
                    "decisions": row_decisions[: int(cfg.max_samples)],
                }
            )
    chunk_size = int(getattr(cfg, "real_native_scheduled_audition_chunk_size", 0))
    if chunk_size > 0 and bool(getattr(cfg, "real_native_scheduled_complete_flush", False)):
        before_flush = _phase45_scheduled_coverage(runtime, int(cfg.real_native_audition_budget_per_cell))
        before_explanation = _phase46_under_k_explanation(
            runtime,
            firing_buffer=firing_buffer,
            budget=int(cfg.real_native_audition_budget_per_cell),
        )
        if bool(getattr(cfg, "real_native_pool_scan_auditions", False)):
            new_targets = _phase47_pool_scan_targets(runtime, pool_scanned_cell_ids)
            collected = _phase47_collect_pool_firing_sets(
                cfg,
                runtime=runtime,
                score_provider=score_provider,
                rows=rows,
                firing_buffer=firing_buffer,
                target_ids=new_targets,
                success_kind=success_kind,
                seed=int(seed) + 91_000,
            )
            pool_scanned_cell_ids.update(new_targets)
            pool_supply_stats.update(collected["counter"])
            scheduled = _phase47_run_pool_scan_auditions(
                cfg,
                runtime=runtime,
                score_provider=score_provider,
                firing_buffer=firing_buffer,
                success_kind=success_kind,
                seed=int(seed) + 92_000,
                step=int(step_offset) + len(rows),
                max_trace_samples=int(cfg.max_samples),
            )
        else:
            collected = _phase46_collect_complete_flush_samples(
                cfg,
                runtime=runtime,
                score_provider=score_provider,
                rows=rows,
                firing_buffer=firing_buffer,
                success_kind=success_kind,
                seed=int(seed) + 91_000,
            )
            scheduled = _phase45_run_scheduled_auditions(
                cfg,
                runtime=runtime,
                score_provider=score_provider,
                firing_buffer=firing_buffer,
                success_kind=success_kind,
                seed=int(seed) + 92_000,
                step=int(step_offset) + len(rows),
                max_trace_samples=int(cfg.max_samples),
                complete_flush=True,
            )
        scheduled_stats.update(scheduled["counter"])
        verdicts.update(scheduled["verdict_counts"])
        verdict_endpoints.update(scheduled["verdict_reason_counts"])
        outcome_verdicts.update(scheduled.get("outcome_verdict_counts", {}))
        first_flip_vs_outcome.update(scheduled.get("first_flip_vs_outcome_counts", {}))
        audition_count += int(scheduled["audition_count"])
        audition_frames_spent += int(scheduled["audition_frames_spent"])
        if bool(getattr(cfg, "real_native_probation_enabled", False)):
            confirm = (
                _phase49_confirm_probation_cells_dose_response
                if bool(getattr(cfg, "real_native_probation_dose_response_enabled", False))
                else _phase48_confirm_probation_cells
            )
            probation = confirm(
                cfg,
                runtime=runtime,
                score_provider=score_provider,
                rows=rows,
                success_kind=success_kind,
                seed=int(seed) + 93_000,
                step=int(step_offset) + len(rows),
                segment_name=segment_name,
            )
            probation_stats.update(probation["counter"])
            probation_records.extend(probation["records"])
        after_flush = _phase45_scheduled_coverage(runtime, int(cfg.real_native_audition_budget_per_cell))
        after_explanation = _phase46_under_k_explanation(
            runtime,
            firing_buffer=firing_buffer,
            budget=int(cfg.real_native_audition_budget_per_cell),
        )
        complete_flush_report = {
            "enabled": True,
            "before_coverage": before_flush,
            "after_coverage": after_flush,
            "before_under_k_explanation": before_explanation,
            "after_under_k_explanation": after_explanation,
            "active_scan": collected,
            "scheduled_flush_counter": dict(sorted(scheduled["counter"].items())),
            "scheduled_flush_verdict_counts": dict(sorted(scheduled["verdict_counts"].items())),
            "scheduled_flush_frames_spent": int(scheduled["audition_frames_spent"]),
            "scheduled_flush_auditions": int(scheduled["audition_count"]),
            "scheduled_flush_frames_per_audition": (
                int(scheduled["audition_frames_spent"]) / max(1, int(scheduled["audition_count"]))
            ),
        }
        runtime.snapshot(step=int(step_offset) + len(rows), segment=segment_name)
        backlog_curve.append(
            _phase46_backlog_snapshot(
                cfg,
                runtime,
                segment=segment_name,
                step=int(step_offset) + len(rows),
                row_index=len(rows),
                event="complete_flush",
            )
        )
    blocked_after = sum(runtime.births_blocked_by_capacity.values())
    distribution = _phase44_audition_distribution(runtime)
    scheduled_coverage = _phase45_scheduled_coverage(runtime, int(cfg.real_native_audition_budget_per_cell))
    verdict_total = sum(verdicts.values())
    outcome_total = sum(outcome_verdicts.values())
    outcome_agree = sum(
        value
        for key, value in first_flip_vs_outcome.items()
        if key.split("->", 1)[0] == key.split("->", 1)[1]
    )
    return {
        "segment": segment_name,
        "row_count": len(rows),
        "success_kind": success_kind,
        "black_reply_policy": "exact_adversarial",
        "endpoint_counts": dict(sorted(endpoints.items())),
        "success_by_row": success_by_row,
        "endpoint_by_row": endpoint_by_row,
        "decision_ply_count": decision_ply_count,
        "choice_changed_ply_count": choice_changed_count,
        "choice_changed_ply_rate": choice_changed_count / max(1, decision_ply_count),
        "trial_cell_proposal_count": proposal_count,
        "audition_request_count": request_count,
        "audition_budget_skip_count": budget_skip_count,
        "audition_cap_skip_count": cap_skip_count,
        "disagreement_ply_count": disagreement_ply_count,
        "disagreement_ply_rate": disagreement_ply_count / max(1, decision_ply_count),
        "audition_count": audition_count,
        "auditions_per_cell_distribution": distribution,
        "audition_verdict_counts": dict(sorted(verdicts.items())),
        "audition_verdict_rates": {
            key: value / max(1, verdict_total)
            for key, value in sorted(verdicts.items())
        },
        "audition_verdict_reason_counts": dict(sorted(verdict_endpoints.items())),
        "outcome_audition_enabled": bool(getattr(cfg, "real_native_outcome_audition_enabled", False)),
        "outcome_audition_horizon_plies": int(getattr(cfg, "real_native_outcome_audition_horizon_plies", 0)),
        "outcome_audition_verdict_counts": dict(sorted(outcome_verdicts.items())),
        "outcome_audition_verdict_rates": {
            key: value / max(1, outcome_total)
            for key, value in sorted(outcome_verdicts.items())
        },
        "first_flip_vs_outcome_counts": dict(sorted(first_flip_vs_outcome.items())),
        "first_flip_vs_outcome_agreement_rate": outcome_agree / max(1, outcome_total),
        "audition_frames_spent": audition_frames_spent,
        "audition_starvation_min_per_cell": float(cfg.real_native_audition_starvation_min_per_cell),
        "scheduled_audition_stats": dict(sorted(scheduled_stats.items())),
        "probation_confirmation_stats": dict(sorted(probation_stats.items())),
        "probation_confirmation_records": probation_records,
        "pool_supply_stats": dict(sorted(pool_supply_stats.items())),
        "court_throughput_per_chunk": _phase47_court_throughput_per_chunk(cfg),
        "scheduled_coverage": scheduled_coverage,
        "complete_flush": complete_flush_report or {"enabled": False},
        "backlog_curve": backlog_curve,
        "births_deferred_by_backlog_total": int(birth_deferred_stats["births_deferred_by_backlog"]),
        "births_deferred_by_count_homeostasis_total": int(
            birth_deferred_stats["births_deferred_by_count_homeostasis"]
        ),
        "births_deferred_by_count_homeostasis_by_trigger": {
            key.removeprefix("births_deferred_by_count_homeostasis_trigger:")
            if key.startswith("births_deferred_by_count_homeostasis_trigger:")
            else key: int(value)
            for key, value in sorted(birth_deferred_stats.items())
            if key.startswith("births_deferred_by_count_homeostasis_trigger:")
        },
        "births_deferred_by_count_homeostasis_by_reason": {
            key.removeprefix("births_deferred_by_count_homeostasis_reason:")
            if key.startswith("births_deferred_by_count_homeostasis_reason:")
            else key: int(value)
            for key, value in sorted(birth_deferred_stats.items())
            if key.startswith("births_deferred_by_count_homeostasis_reason:")
        },
        "births_deferred_by_backlog_by_trigger": {
            key.removeprefix("births_deferred_by_backlog_trigger:")
            if key.startswith("births_deferred_by_backlog_trigger:")
            else key: int(value)
            for key, value in sorted(birth_deferred_stats.items())
            if key.startswith("births_deferred_by_backlog_trigger:")
        },
        "births_deferred_by_backlog_by_parent": {
            key.removeprefix("births_deferred_by_backlog_parent:")
            if key.startswith("births_deferred_by_backlog_parent:")
            else key: int(value)
            for key, value in sorted(birth_deferred_stats.items())
            if key.startswith("births_deferred_by_backlog_parent:")
        },
        "requested_composite_count": requested_total,
        "active_composite_count": active_total,
        "births_blocked_by_capacity_delta": int(blocked_after - blocked_before),
        "births_blocked_by_capacity_total": int(blocked_after),
        "population_snapshot": runtime.population_summary(),
        "runner_config": _phase38_runner_config(
            cfg,
            seed=int(seed),
            success_kind=success_kind,
            black_reply_policy="exact_adversarial",
            row_count=len(rows),
        ),
        "trace_sample": trace_sample,
    }


def _phase44_run_audition_pair(
    cfg: StageBEcologicalDiscoveryConfig,
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    score_provider: Any,
    host_move: chess.Move,
    cell_move: chess.Move,
    success_kind: str,
    seed: int,
    judge_cache: tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    host = _phase44_audition_rollout(
        cfg,
        board,
        counts,
        score_provider=score_provider,
        first_move=host_move,
        success_kind=success_kind,
        seed=int(seed),
        judge_cache=judge_cache,
    )
    cell = _phase44_audition_rollout(
        cfg,
        board,
        counts,
        score_provider=score_provider,
        first_move=cell_move,
        success_kind=success_kind,
        seed=int(seed),
        judge_cache=judge_cache,
    )
    verdict, reason = _phase44_compare_audition_flips(host.get("first_flip"), cell.get("first_flip"))
    result = {
        "host": host,
        "cell": cell,
        "verdict": verdict,
        "verdict_reason": reason,
        "frames_spent": int(host.get("frames_spent", 0)) + int(cell.get("frames_spent", 0)),
    }
    if bool(getattr(cfg, "real_native_outcome_audition_enabled", False)):
        outcome = _phase49_run_audition_outcome_pair(
            cfg,
            board,
            counts,
            score_provider=score_provider,
            host_move=host_move,
            cell_move=cell_move,
            success_kind=success_kind,
            seed=int(seed) + 53_000,
            judge_cache=judge_cache,
        )
        result["outcome_verdict"] = outcome["verdict"]
        result["outcome_verdict_reason"] = outcome["verdict_reason"]
        result["outcome_pair"] = outcome
        result["outcome_frames_spent"] = int(outcome["frames_spent"])
        result["first_flip_outcome_agree"] = bool(outcome["verdict"] == verdict)
    return result


def _phase50_applied_audition_verdict(
    cfg: StageBEcologicalDiscoveryConfig,
    audition: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        bool(getattr(cfg, "real_native_outcome_audition_verdict_is_standing", False))
        and audition.get("outcome_verdict") is not None
    ):
        return {
            "verdict": str(audition["outcome_verdict"]),
            "verdict_reason": str(audition.get("outcome_verdict_reason", "bounded_outcome")),
            "verdict_source": "bounded_outcome",
            "frames_spent": int(audition.get("frames_spent", 0)) + int(audition.get("outcome_frames_spent", 0)),
        }
    return {
        "verdict": str(audition["verdict"]),
        "verdict_reason": str(audition["verdict_reason"]),
        "verdict_source": "first_flip",
        "frames_spent": int(audition.get("frames_spent", 0)),
    }


def _phase49_run_audition_outcome_pair(
    cfg: StageBEcologicalDiscoveryConfig,
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    score_provider: Any,
    host_move: chess.Move,
    cell_move: chess.Move,
    success_kind: str,
    seed: int,
    judge_cache: tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    host = _phase49_audition_outcome_rollout(
        cfg,
        board,
        counts,
        score_provider=score_provider,
        first_move=host_move,
        success_kind=success_kind,
        seed=int(seed),
        judge_cache=judge_cache,
    )
    cell = _phase49_audition_outcome_rollout(
        cfg,
        board,
        counts,
        score_provider=score_provider,
        first_move=cell_move,
        success_kind=success_kind,
        seed=int(seed),
        judge_cache=judge_cache,
    )
    verdict, reason = _phase49_compare_outcomes(host, cell)
    return {
        "host": host,
        "cell": cell,
        "verdict": verdict,
        "verdict_reason": reason,
        "frames_spent": int(host.get("frames_spent", 0)) + int(cell.get("frames_spent", 0)),
    }


def _phase49_audition_outcome_rollout(
    cfg: StageBEcologicalDiscoveryConfig,
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    score_provider: Any,
    first_move: chess.Move,
    success_kind: str,
    seed: int,
    judge_cache: tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    scorer = None if cfg.fast_exact_judge or success_kind == "approach_waypoint" else load_canonical_mate2_first_scorer()
    mate2_cache, enter_cache = judge_cache
    local_board = board.copy(stack=False)
    local_counts: Counter[Any] = Counter(counts)
    rng = random.Random(seed)
    horizon = max(1, int(getattr(cfg, "real_native_outcome_audition_horizon_plies", 16)))
    transitions: list[dict[str, Any]] = []
    endpoint = "horizon"
    success = False
    for ply in range(horizon):
        success_now, success_endpoint = _rollout_success_check(
            cfg,
            local_board,
            success_kind=success_kind,
            scorer=scorer,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
        )
        if success_now:
            endpoint = success_endpoint
            success = True
            break
        if local_board.turn != chess.WHITE or local_board.is_game_over(claim_draw=False):
            endpoint = "terminal"
            break
        move = first_move if ply == 0 else _phase44_host_argmax_move(local_board, local_counts, score_provider)
        if move is None or move not in local_board.legal_moves:
            endpoint = "illegal"
            break
        if int(local_counts.get(_after_move_repetition_key(local_board, move), 0)) >= 2:
            endpoint = "third_repetition"
            break
        transition = {
            "ply": int(ply),
            "before_fen": local_board.fen(),
            "white_move": move.uci(),
        }
        local_board.push(move)
        local_counts[_position_repetition_key(local_board)] += 1
        local_counts[local_board._transposition_key()] += 1
        transition["after_white_fen"] = local_board.fen()
        if _white_rook_square(local_board) is None:
            endpoint = "rook_lost"
            transitions.append(transition)
            break
        if local_board.is_stalemate():
            endpoint = "stalemate"
            transitions.append(transition)
            break
        if local_board.is_checkmate():
            endpoint = "mate_delivered"
            success = True
            transitions.append(transition)
            break
        reply = _select_black_reply_for_rollout(
            cfg,
            local_board,
            rng,
            success_kind=success_kind,
            scorer=scorer,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
            black_reply_policy="exact_adversarial",
        )
        if reply is None:
            endpoint = "mate_delivered" if local_board.is_check() else "stalemate"
            success = local_board.is_check()
            transition["black_reply"] = None
            transitions.append(transition)
            break
        transition["black_reply"] = reply.uci()
        local_board.push(reply)
        local_counts[_position_repetition_key(local_board)] += 1
        local_counts[local_board._transposition_key()] += 1
        transition["after_black_fen"] = local_board.fen()
        transitions.append(transition)
        if _white_rook_square(local_board) is None:
            endpoint = "rook_lost"
            break
        if local_board.is_stalemate():
            endpoint = "stalemate"
            break
        if not fence_established_geometry(local_board):
            endpoint = "fence_broken"
            break
    if not success and success_kind == "approach_waypoint" and _approach_waypoint_success(local_board):
        endpoint = "waypoint_reached"
        success = True
    hard_loss = endpoint in {"fence_broken", "rook_lost", "stalemate", "illegal"}
    outcome = "win" if success else "loss" if hard_loss else "draw"
    score = 1 if outcome == "win" else -1 if outcome == "loss" else 0
    return {
        "first_move": first_move.uci(),
        "endpoint": endpoint,
        "success": bool(success),
        "outcome": outcome,
        "outcome_score": score,
        "frames_spent": len(transitions),
        "transition_sample": transitions[: int(cfg.max_samples)],
    }


def _phase49_compare_outcomes(
    host: Mapping[str, Any],
    cell: Mapping[str, Any],
) -> tuple[str, str]:
    host_score = int(host.get("outcome_score", 0))
    cell_score = int(cell.get("outcome_score", 0))
    if cell_score > host_score:
        return "cell_better", f"cell_{cell.get('outcome')}_host_{host.get('outcome')}"
    if cell_score < host_score:
        return "cell_worse", f"cell_{cell.get('outcome')}_host_{host.get('outcome')}"
    return "tie", f"both_{cell.get('outcome')}"


def _phase44_audition_rollout(
    cfg: StageBEcologicalDiscoveryConfig,
    board: chess.Board,
    counts: Mapping[Any, int],
    *,
    score_provider: Any,
    first_move: chess.Move,
    success_kind: str,
    seed: int,
    judge_cache: tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    scorer = None if cfg.fast_exact_judge or success_kind == "approach_waypoint" else load_canonical_mate2_first_scorer()
    mate2_cache, enter_cache = judge_cache
    local_board = board.copy(stack=False)
    local_counts: Counter[Any] = Counter(counts)
    rng = random.Random(seed)
    transitions: list[dict[str, Any]] = []
    endpoint = "horizon"
    first_flip: dict[str, Any] | None = None
    horizon = max(1, int(cfg.real_native_audition_horizon_plies))
    for ply in range(horizon):
        if local_board.turn != chess.WHITE or local_board.is_game_over(claim_draw=False):
            endpoint = "terminal"
            break
        move = first_move if ply == 0 else _phase44_host_argmax_move(local_board, local_counts, score_provider)
        if move is None or move not in local_board.legal_moves:
            endpoint = "illegal"
            break
        if int(local_counts.get(_after_move_repetition_key(local_board, move), 0)) >= 2:
            endpoint = "third_repetition"
            break
        transition = {
            "ply": int(ply),
            "before_fen": local_board.fen(),
            "white_move": move.uci(),
            "before_fence_established": bool(fence_established_geometry(local_board)),
            "before_rook_present": bool(_white_rook_square(local_board) is not None),
        }
        local_board.push(move)
        local_counts[_position_repetition_key(local_board)] += 1
        local_counts[local_board._transposition_key()] += 1
        transition.update(
            {
                "after_white_fen": local_board.fen(),
                "after_white_fence_established": bool(fence_established_geometry(local_board)),
                "after_white_rook_present": bool(_white_rook_square(local_board) is not None),
            }
        )
        first_flip = _phase44_transition_flip_event(transition)
        if first_flip is not None:
            endpoint = str(first_flip["reason"])
            transitions.append(transition)
            break
        if _white_rook_square(local_board) is None:
            endpoint = "rook_lost"
            transitions.append(transition)
            break
        if local_board.is_stalemate():
            endpoint = "stalemate"
            transitions.append(transition)
            break
        if local_board.is_checkmate():
            first_flip = {"ply": int(ply), "valence": "positive", "reason": "mate_delivered_after_white"}
            endpoint = "mate_delivered"
            transitions.append(transition)
            break
        reply = _select_black_reply_for_rollout(
            cfg,
            local_board,
            rng,
            success_kind=success_kind,
            scorer=scorer,
            mate2_cache=mate2_cache,
            enter_cache=enter_cache,
            black_reply_policy="exact_adversarial",
        )
        if reply is None:
            endpoint = "mate_delivered" if local_board.is_check() else "stalemate"
            if local_board.is_check():
                first_flip = {"ply": int(ply), "valence": "positive", "reason": "mate_delivered_black_no_reply"}
            transition["black_reply"] = None
            transitions.append(transition)
            break
        transition["black_reply"] = reply.uci()
        local_board.push(reply)
        local_counts[_position_repetition_key(local_board)] += 1
        local_counts[local_board._transposition_key()] += 1
        transition.update(
            {
                "after_black_fen": local_board.fen(),
                "after_black_fence_established": bool(fence_established_geometry(local_board)),
                "after_black_rook_present": bool(_white_rook_square(local_board) is not None),
            }
        )
        first_flip = _phase44_transition_flip_event(transition)
        transitions.append(transition)
        if first_flip is not None:
            endpoint = str(first_flip["reason"])
            break
        if _white_rook_square(local_board) is None:
            endpoint = "rook_lost"
            break
        if local_board.is_stalemate():
            endpoint = "stalemate"
            break
        if not fence_established_geometry(local_board):
            first_flip = {"ply": int(ply), "valence": "negative", "reason": "fence_broken_after_black"}
            endpoint = "fence_broken_after_black"
            break
    return {
        "first_move": first_move.uci(),
        "endpoint": endpoint,
        "first_flip": first_flip,
        "frames_spent": len(transitions),
        "transition_sample": transitions[: int(cfg.max_samples)],
    }


def _phase44_host_argmax_move(
    board: chess.Board,
    counts: Mapping[Any, int],
    score_provider: Any,
) -> chess.Move | None:
    legal = _legal_without_third_repetition(board, counts)
    if not legal:
        legal = tuple(sorted(board.legal_moves, key=lambda move: move.uci()))
    if not legal:
        return None
    scores = score_provider(board, counts)
    rows = [(float(scores.get(move.uci(), 0.0)), move.uci(), move) for move in legal]
    rows.sort(reverse=True)
    return rows[0][-1]


def _phase44_transition_flip_event(transition: Mapping[str, Any]) -> dict[str, Any] | None:
    ply = int(transition.get("ply", 0))
    before_fence = bool(transition.get("before_fence_established"))
    before_rook = bool(transition.get("before_rook_present"))
    before_waypoint = _phase42_waypoint_from_fen(transition.get("before_fen"))
    after_white_fence = transition.get("after_white_fence_established")
    after_white_rook = transition.get("after_white_rook_present")
    after_white_waypoint = _phase42_waypoint_from_fen(transition.get("after_white_fen"))
    if before_rook and after_white_rook is False:
        return {"ply": ply, "valence": "negative", "reason": "rook_lost_after_white"}
    if before_fence and after_white_fence is False:
        return {"ply": ply, "valence": "negative", "reason": "fence_broken_after_white"}
    if before_fence is False and after_white_fence is True:
        return {"ply": ply, "valence": "positive", "reason": "fence_established_after_white"}
    if before_waypoint is False and after_white_waypoint is True:
        return {"ply": ply, "valence": "positive", "reason": "waypoint_entered_after_white"}
    if "after_black_fen" not in transition:
        return None
    after_black_fence = transition.get("after_black_fence_established")
    after_black_rook = transition.get("after_black_rook_present")
    after_black_waypoint = _phase42_waypoint_from_fen(transition.get("after_black_fen"))
    if after_white_rook is True and after_black_rook is False:
        return {"ply": ply, "valence": "negative", "reason": "rook_lost_after_black"}
    if after_white_fence is True and after_black_fence is False:
        return {"ply": ply, "valence": "negative", "reason": "fence_broken_after_black"}
    if after_white_fence is False and after_black_fence is True:
        return {"ply": ply, "valence": "positive", "reason": "fence_established_after_black"}
    if after_white_waypoint is False and after_black_waypoint is True:
        return {"ply": ply, "valence": "positive", "reason": "waypoint_entered_after_black"}
    return None


def _phase44_compare_audition_flips(
    host_flip: Any,
    cell_flip: Any,
) -> tuple[str, str]:
    host = host_flip if isinstance(host_flip, Mapping) else None
    cell = cell_flip if isinstance(cell_flip, Mapping) else None
    if host is None and cell is None:
        return "tie", "no_flip_both_lines"
    if host is None and cell is not None:
        return (
            ("cell_better", "cell_positive_host_no_flip")
            if cell.get("valence") == "positive"
            else ("cell_worse", "cell_negative_host_no_flip")
        )
    if host is not None and cell is None:
        return (
            ("cell_worse", "host_positive_cell_no_flip")
            if host.get("valence") == "positive"
            else ("cell_better", "host_negative_cell_no_flip")
        )
    host_valence = str(host.get("valence"))
    cell_valence = str(cell.get("valence"))
    host_ply = int(host.get("ply", 0))
    cell_ply = int(cell.get("ply", 0))
    if cell_valence == "positive" and host_valence == "negative":
        return "cell_better", "cell_positive_host_negative"
    if cell_valence == "negative" and host_valence == "positive":
        return "cell_worse", "cell_negative_host_positive"
    if cell_valence == "positive" and host_valence == "positive":
        if cell_ply < host_ply:
            return "cell_better", "cell_positive_first"
        if host_ply < cell_ply:
            return "cell_worse", "host_positive_first"
        return "tie", "same_positive_flip_ply"
    if cell_valence == "negative" and host_valence == "negative":
        if host_ply < cell_ply:
            return "cell_better", "host_negative_first"
        if cell_ply < host_ply:
            return "cell_worse", "cell_negative_first"
        return "tie", "same_negative_flip_ply"
    return "tie", "unclassified_equal_flip"


def _phase44_audition_distribution(runtime: _GraphNativeCompositeRuntime) -> dict[str, Any]:
    counts = [
        int(item.get("audition_count", 0))
        for item in runtime.population.values()
        if item.get("birth_segment") != "acceptance_probe"
    ]
    histogram = Counter(counts)
    sorted_counts = sorted(counts)
    median = sorted_counts[len(sorted_counts) // 2] if sorted_counts else 0
    return {
        "cell_count": len(counts),
        "min": min(counts) if counts else 0,
        "median": median,
        "max": max(counts) if counts else 0,
        "mean": sum(counts) / max(1, len(counts)),
        "histogram": {str(key): int(value) for key, value in sorted(histogram.items())},
    }


def _phase45_run_scheduled_auditions(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    runtime: _GraphNativeCompositeRuntime,
    score_provider: Any,
    firing_buffer: Mapping[str, Sequence[Mapping[str, Any]]],
    success_kind: str,
    seed: int,
    step: int,
    max_trace_samples: int,
    complete_flush: bool = False,
) -> dict[str, Any]:
    counter: Counter[str] = Counter()
    verdict_counts: Counter[str] = Counter()
    verdict_reason_counts: Counter[str] = Counter()
    outcome_verdict_counts: Counter[str] = Counter()
    first_flip_vs_outcome_counts: Counter[str] = Counter()
    audition_count = 0
    audition_frames_spent = 0
    budget = int(cfg.real_native_audition_budget_per_cell)
    if budget <= 0:
        return {
            "counter": counter,
            "verdict_counts": verdict_counts,
            "verdict_reason_counts": verdict_reason_counts,
            "outcome_verdict_counts": outcome_verdict_counts,
            "first_flip_vs_outcome_counts": first_flip_vs_outcome_counts,
            "audition_count": 0,
            "audition_frames_spent": 0,
        }
    judge_cache = _new_judge_cache()
    for cid, item in sorted(runtime.population.items()):
        if item.get("state") != "TRIAL" or item.get("birth_segment") == "acceptance_probe":
            continue
        counter["trial_cells_considered"] += 1
        already = int(item.get("audition_count", 0)) + int(item.get("scheduled_audition_sample_count", 0))
        remaining = max(0, budget - already)
        if remaining <= 0:
            counter["trial_cells_budget_satisfied"] += 1
            continue
        samples = list(firing_buffer.get(cid, ()))
        if not samples:
            counter["trial_cells_without_firing_samples"] += 1
            if complete_flush:
                if runtime.apply_redundancy_prune(
                    composite_id=cid,
                    step=int(step),
                    reason="complete_flush_no_firing_samples",
                    sample_count=0,
                    prune_reason="complete_flush_no_firing_samples",
                ):
                    counter["complete_flush_no_firing_prunes"] += 1
                    verdict_counts["no_firing_prune"] += 1
                    verdict_reason_counts["complete_flush_no_firing_samples"] += 1
            continue
        rng = random.Random(int(seed) + _phase45_stable_int(cid))
        if complete_flush and len(samples) < remaining:
            selected = [rng.choice(samples) for _ in range(remaining)]
            counter["complete_flush_replacement_samples"] += remaining - len(samples)
        else:
            sample_count = min(remaining, len(samples))
            selected = rng.sample(samples, sample_count) if len(samples) > sample_count else samples[:sample_count]
        counter["scheduled_samples"] += len(selected)
        disagreements = [sample for sample in selected if not bool(sample.get("agrees_with_host"))]
        if not disagreements and len(selected) >= remaining:
            if runtime.apply_redundancy_prune(
                composite_id=cid,
                step=int(step),
                reason="scheduled_all_sampled_firings_agreed_with_host",
                sample_count=len(selected),
                prune_reason="scheduled_redundancy_all_samples_agreed_with_host",
            ):
                counter["redundancy_prunes"] += 1
                verdict_counts["redundancy_prune"] += 1
                verdict_reason_counts["scheduled_all_sampled_firings_agreed_with_host"] += 1
            continue
        agreement_count = len(selected) - len(disagreements)
        if agreement_count:
            item["scheduled_audition_sample_count"] = (
                int(item.get("scheduled_audition_sample_count", 0)) + agreement_count
            )
        if not disagreements:
            counter["agreement_only_underfilled"] += 1
            continue
        for sample in disagreements:
            if item.get("state") != "TRIAL":
                break
            if int(item.get("audition_count", 0)) >= budget:
                counter["scheduled_budget_reached_mid_cell"] += 1
                break
            board = chess.Board(str(sample["fen"]))
            host_move = chess.Move.from_uci(str(sample["host_move_uci"]))
            cell_move = chess.Move.from_uci(str(sample["cell_move_uci"]))
            if host_move not in board.legal_moves or cell_move not in board.legal_moves:
                counter["scheduled_illegal_sample_skip"] += 1
                continue
            audition = _phase44_run_audition_pair(
                cfg,
                board,
                sample["counts"],
                score_provider=score_provider,
                host_move=host_move,
                cell_move=cell_move,
                success_kind=success_kind,
                seed=int(seed) + _phase45_stable_int(cid) + audition_count,
                judge_cache=judge_cache,
            )
            applied = _phase50_applied_audition_verdict(cfg, audition)
            verdict = str(applied["verdict"])
            verdict_counts[verdict] += 1
            verdict_reason_counts[str(applied["verdict_reason"])] += 1
            outcome_verdict = audition.get("outcome_verdict")
            if outcome_verdict is not None:
                outcome_verdict_counts[str(outcome_verdict)] += 1
                first_flip_vs_outcome_counts[f"{audition['verdict']}->{outcome_verdict}"] += 1
            audition_count += 1
            audition_frames_spent += int(audition["frames_spent"]) + int(audition.get("outcome_frames_spent", 0))
            counter["scheduled_paired_auditions"] += 1
            runtime.apply_audition_verdict(
                composite_id=cid,
                verdict=verdict,
                step=int(step),
                reason=f"scheduled:{applied['verdict_reason']}",
                frames_spent=int(applied["frames_spent"]),
            )
            if counter["scheduled_trace_samples"] < max_trace_samples:
                counter["scheduled_trace_samples"] += 1
        refreshed = runtime.population.get(cid)
        if refreshed and refreshed.get("state") == "TRIAL":
            judged = int(refreshed.get("audition_count", 0)) + int(
                refreshed.get("scheduled_audition_sample_count", 0)
            )
            if judged < budget:
                counter["trial_cells_under_budget_after_schedule"] += 1
    return {
        "counter": counter,
        "verdict_counts": verdict_counts,
        "verdict_reason_counts": verdict_reason_counts,
        "outcome_verdict_counts": outcome_verdict_counts,
        "first_flip_vs_outcome_counts": first_flip_vs_outcome_counts,
        "audition_count": audition_count,
        "audition_frames_spent": audition_frames_spent,
    }


def _phase45_stable_int(text: str) -> int:
    total = 0
    for char in str(text):
        total = (total * 131 + ord(char)) % 1_000_000_007
    return total


def _phase45_scheduled_coverage(
    runtime: _GraphNativeCompositeRuntime,
    budget: int,
) -> dict[str, Any]:
    trial_cells = [
        item for item in runtime.population.values()
        if item.get("state") == "TRIAL" and item.get("birth_segment") != "acceptance_probe"
    ]
    judged_counts = [
        int(item.get("audition_count", 0)) + int(item.get("scheduled_audition_sample_count", 0))
        for item in trial_cells
    ]
    under = [count for count in judged_counts if count < int(budget)]
    histogram = Counter(judged_counts)
    return {
        "trial_cell_count": len(trial_cells),
        "budget": int(budget),
        "under_budget_trial_count": len(under),
        "under_budget_trial_fraction": len(under) / max(1, len(trial_cells)),
        "min_judged": min(judged_counts) if judged_counts else 0,
        "median_judged": sorted(judged_counts)[len(judged_counts) // 2] if judged_counts else 0,
        "max_judged": max(judged_counts) if judged_counts else 0,
        "histogram": {str(key): int(value) for key, value in sorted(histogram.items())},
    }


def _phase45_scheduled_unjudged_stop(
    cfg: StageBEcologicalDiscoveryConfig,
    training: Mapping[str, Any],
) -> dict[str, Any]:
    coverage = training.get("scheduled_coverage", {})
    fraction = float(coverage.get("under_budget_trial_fraction", 0.0)) if isinstance(coverage, Mapping) else 0.0
    trial_count = int(coverage.get("trial_cell_count", 0)) if isinstance(coverage, Mapping) else 0
    threshold = float(getattr(cfg, "real_native_scheduled_unjudged_fraction_stop", 0.0))
    return {
        "stop": bool(trial_count > 0 and threshold > 0.0 and fraction > threshold),
        "under_budget_trial_fraction": fraction,
        "under_budget_trial_count": int(coverage.get("under_budget_trial_count", 0)) if isinstance(coverage, Mapping) else 0,
        "trial_cell_count": trial_count,
        "threshold": threshold,
        "coverage": dict(coverage) if isinstance(coverage, Mapping) else {},
        "scheduled_audition_stats": dict(training.get("scheduled_audition_stats", {})),
    }


def _phase47_court_throughput_per_chunk(cfg: StageBEcologicalDiscoveryConfig) -> int:
    configured = int(getattr(cfg, "real_native_court_throughput_per_chunk", 0))
    if configured > 0:
        return configured
    if bool(getattr(cfg, "real_native_pool_scan_auditions", False)):
        return max(1, int(getattr(cfg, "real_native_trial_band_max", 0)) or 1)
    return max(
        1,
        int(getattr(cfg, "real_native_scheduled_audition_chunk_size", 0))
        * max(1, int(getattr(cfg, "real_native_audition_per_ply_cap", 0))),
    )


def _phase47_pool_scan_targets(
    runtime: _GraphNativeCompositeRuntime,
    already_scanned: set[str],
) -> set[str]:
    return {
        str(cid)
        for cid, item in runtime.population.items()
        if str(cid) not in already_scanned
        and item.get("state") == "TRIAL"
        and item.get("birth_segment") != "acceptance_probe"
    }


def _phase47_sample_key(sample: Mapping[str, Any]) -> str:
    return "|".join(
        [
            str(sample.get("fen")),
            str(sample.get("host_move_uci")),
            str(sample.get("cell_move_uci")),
            str(sample.get("row_id")),
            str(sample.get("ply")),
        ]
    )


def _phase47_collect_pool_firing_sets(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    runtime: _GraphNativeCompositeRuntime,
    score_provider: Any,
    rows: Sequence[Mapping[str, Any]],
    firing_buffer: defaultdict[str, list[dict[str, Any]]],
    target_ids: set[str],
    success_kind: str,
    seed: int,
) -> dict[str, Any]:
    counter: Counter[str] = Counter()
    if not target_ids:
        return {"counter": counter}
    scorer = None if cfg.fast_exact_judge or success_kind == "approach_waypoint" else load_canonical_mate2_first_scorer()
    mate2_cache, enter_cache = _new_judge_cache()
    seen: set[tuple[str, str, str, str, int, int]] = set()
    for cid, samples in firing_buffer.items():
        for sample in samples:
            seen.add(
                (
                    str(cid),
                    str(sample.get("fen")),
                    str(sample.get("host_move_uci")),
                    str(sample.get("cell_move_uci")),
                    int(sample.get("row_id", -1)),
                    int(sample.get("ply", -1)),
                )
            )
    disabled = set(runtime.population) - set(target_ids)
    rng = random.Random(seed)
    for row_index, row in enumerate(rows):
        board = chess.Board(str(row["fen"]))
        counts: Counter[Any] = Counter({_position_repetition_key(board): 1, board._transposition_key(): 1})
        for ply in range(int(cfg.horizon_plies)):
            if board.turn != chess.WHITE or board.is_game_over(claim_draw=False):
                break
            counter["pool_scan_white_positions"] += 1
            selected = runtime.choose_move(
                board,
                counts,
                score_provider,
                seed=int(seed) + row_index * 997 + ply,
                disabled=disabled,
                discriminative=True,
                include_trial_proposals=True,
            )
            for firing in selected.get("trial_cell_firings", ()):
                cid = str(firing.get("composite_id"))
                if cid not in target_ids:
                    continue
                if firing.get("move") is None or firing.get("host_move") is None:
                    continue
                key = (
                    cid,
                    board.fen(),
                    str(firing.get("host_move_uci")),
                    str(firing.get("move_uci")),
                    int(row.get("row_id", row_index)),
                    int(ply),
                )
                if key in seen:
                    continue
                seen.add(key)
                firing_buffer[cid].append(
                    {
                        "fen": board.fen(),
                        "counts": Counter(counts),
                        "host_move_uci": str(firing["host_move_uci"]),
                        "cell_move_uci": str(firing["move_uci"]),
                        "agrees_with_host": bool(firing.get("agrees_with_host", False)),
                        "row_id": int(row.get("row_id", row_index)),
                        "ply": int(ply),
                        "source": "rung_pool_scan",
                    }
                )
                counter["pool_scan_samples_added"] += 1
            move = _phase44_host_argmax_move(board, counts, score_provider)
            if move is None or move not in board.legal_moves:
                break
            if int(counts.get(_after_move_repetition_key(board, move), 0)) >= 2:
                break
            board.push(move)
            counts[_position_repetition_key(board)] += 1
            counts[board._transposition_key()] += 1
            if board.is_game_over(claim_draw=False):
                break
            reply = _select_black_reply_for_rollout(
                cfg,
                board,
                rng,
                success_kind=success_kind,
                scorer=scorer,
                mate2_cache=mate2_cache,
                enter_cache=enter_cache,
                black_reply_policy="exact_adversarial",
            )
            if reply is None or reply not in board.legal_moves:
                break
            board.push(reply)
            counts[_position_repetition_key(board)] += 1
            counts[board._transposition_key()] += 1
    for cid in target_ids:
        size = len(firing_buffer.get(cid, ()))
        counter[f"pool_firing_set_size:{min(size, int(cfg.real_native_audition_budget_per_cell))}"] += 1
        if size <= 0:
            counter["pool_cells_fire_nowhere"] += 1
        else:
            counter["pool_cells_fire_somewhere"] += 1
    counter["pool_scan_target_cells"] += len(target_ids)
    counter["pool_scan_rows"] += len(rows)
    return {"counter": counter}


def _phase47_run_pool_scan_auditions(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    runtime: _GraphNativeCompositeRuntime,
    score_provider: Any,
    firing_buffer: Mapping[str, Sequence[Mapping[str, Any]]],
    success_kind: str,
    seed: int,
    step: int,
    max_trace_samples: int,
) -> dict[str, Any]:
    counter: Counter[str] = Counter()
    verdict_counts: Counter[str] = Counter()
    verdict_reason_counts: Counter[str] = Counter()
    outcome_verdict_counts: Counter[str] = Counter()
    first_flip_vs_outcome_counts: Counter[str] = Counter()
    audition_count = 0
    audition_frames_spent = 0
    budget = int(cfg.real_native_audition_budget_per_cell)
    if budget <= 0:
        return {
            "counter": counter,
            "verdict_counts": verdict_counts,
            "verdict_reason_counts": verdict_reason_counts,
            "outcome_verdict_counts": outcome_verdict_counts,
            "first_flip_vs_outcome_counts": first_flip_vs_outcome_counts,
            "audition_count": 0,
            "audition_frames_spent": 0,
        }
    judge_cache = _new_judge_cache()
    for cid, item in sorted(runtime.population.items()):
        if item.get("state") != "TRIAL" or item.get("birth_segment") == "acceptance_probe":
            continue
        counter["trial_cells_considered"] += 1
        samples = list(firing_buffer.get(cid, ()))
        counter[f"firing_set_size:{min(len(samples), budget)}"] += 1
        if not samples:
            if runtime.apply_vacuous_prune(
                composite_id=cid,
                step=int(step),
                reason="pool_scan_no_firing_samples",
            ):
                counter["vacuous_prunes"] += 1
                verdict_counts["vacuous_prune"] += 1
                verdict_reason_counts["pool_scan_no_firing_samples"] += 1
            continue
        offered_keys = set(map(str, item.setdefault("pool_scan_offered_sample_keys", [])))
        unoffered = [sample for sample in samples if _phase47_sample_key(sample) not in offered_keys]
        if not unoffered:
            counter["trial_cells_no_unoffered_samples"] += 1
            continue
        rng = random.Random(int(seed) + _phase45_stable_int(cid))
        selected_count = min(budget, len(unoffered))
        selected = rng.sample(unoffered, selected_count) if len(unoffered) > selected_count else unoffered[:selected_count]
        for sample in selected:
            offered_keys.add(_phase47_sample_key(sample))
        item["pool_scan_offered_sample_keys"] = sorted(offered_keys)
        counter["pool_samples_offered"] += len(selected)
        counter[f"pool_samples_offered_per_cell:{len(selected)}"] += 1
        disagreements = [sample for sample in selected if not bool(sample.get("agrees_with_host"))]
        agreement_count = len(selected) - len(disagreements)
        if not disagreements:
            if runtime.apply_redundancy_prune(
                composite_id=cid,
                step=int(step),
                reason="pool_scan_all_sampled_firings_agreed_with_host",
                sample_count=len(selected),
                prune_reason="pool_scan_redundancy_all_sampled_firings_agreed_with_host",
            ):
                counter["redundancy_prunes"] += 1
                verdict_counts["redundancy_prune"] += 1
                verdict_reason_counts["pool_scan_all_sampled_firings_agreed_with_host"] += 1
            continue
        if agreement_count:
            item["scheduled_audition_sample_count"] = (
                int(item.get("scheduled_audition_sample_count", 0)) + agreement_count
            )
        for sample in disagreements:
            refreshed = runtime.population.get(cid)
            if not refreshed or refreshed.get("state") != "TRIAL":
                break
            board = chess.Board(str(sample["fen"]))
            host_move = chess.Move.from_uci(str(sample["host_move_uci"]))
            cell_move = chess.Move.from_uci(str(sample["cell_move_uci"]))
            if host_move not in board.legal_moves or cell_move not in board.legal_moves:
                counter["pool_scan_illegal_sample_skip"] += 1
                continue
            audition = _phase44_run_audition_pair(
                cfg,
                board,
                sample["counts"],
                score_provider=score_provider,
                host_move=host_move,
                cell_move=cell_move,
                success_kind=success_kind,
                seed=int(seed) + _phase45_stable_int(cid) + audition_count,
                judge_cache=judge_cache,
            )
            applied = _phase50_applied_audition_verdict(cfg, audition)
            verdict = str(applied["verdict"])
            verdict_counts[verdict] += 1
            verdict_reason_counts[str(applied["verdict_reason"])] += 1
            outcome_verdict = audition.get("outcome_verdict")
            if outcome_verdict is not None:
                outcome_verdict_counts[str(outcome_verdict)] += 1
                first_flip_vs_outcome_counts[f"{audition['verdict']}->{outcome_verdict}"] += 1
            audition_count += 1
            audition_frames_spent += int(audition["frames_spent"]) + int(audition.get("outcome_frames_spent", 0))
            counter["pool_paired_auditions"] += 1
            before_state = str(refreshed.get("state"))
            runtime.apply_audition_verdict(
                composite_id=cid,
                verdict=verdict,
                step=int(step),
                reason=f"pool_scan:{applied['verdict_reason']}",
                frames_spent=int(applied["frames_spent"]),
            )
            after = runtime.population.get(cid, {})
            if before_state == "TRIAL" and after.get("state") == "PROBATION":
                counter["probation_nominations"] += 1
            if before_state == "TRIAL" and after.get("state") == "PRUNED":
                reason = str(after.get("prune_reason", "unknown"))
                counter[f"prune_class:{reason}"] += 1
                if reason == "audition_debt_threshold":
                    counter["debt_prunes"] += 1
            if counter["pool_trace_samples"] < max_trace_samples:
                counter["pool_trace_samples"] += 1
        refreshed = runtime.population.get(cid)
        if refreshed and refreshed.get("state") == "TRIAL":
            offered = len(refreshed.get("pool_scan_offered_sample_keys", ()))
            better = int(refreshed.get("audition_better_events", 0))
            worse = int(refreshed.get("audition_worse_events", 0))
            if offered > 0 and better - worse <= 0:
                if runtime.apply_budget_offered_prune(
                    composite_id=cid,
                    step=int(step),
                    reason="pool_scan_budget_offered_net_nonpositive",
                    offered_count=offered,
                ):
                    counter["budget_offered_prunes"] += 1
                    verdict_counts["budget_offered_prune"] += 1
                    verdict_reason_counts["pool_scan_budget_offered_net_nonpositive"] += 1
    return {
        "counter": counter,
        "verdict_counts": verdict_counts,
        "verdict_reason_counts": verdict_reason_counts,
        "outcome_verdict_counts": outcome_verdict_counts,
        "first_flip_vs_outcome_counts": first_flip_vs_outcome_counts,
        "audition_count": audition_count,
        "audition_frames_spent": audition_frames_spent,
    }


def _phase48_confirm_probation_cells(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    runtime: _GraphNativeCompositeRuntime,
    score_provider: Any,
    rows: Sequence[Mapping[str, Any]],
    success_kind: str,
    seed: int,
    step: int,
    segment_name: str,
) -> dict[str, Any]:
    counter: Counter[str] = Counter()
    records: list[dict[str, Any]] = []
    targets = [
        (str(cid), item)
        for cid, item in sorted(runtime.population.items())
        if item.get("state") == "PROBATION" and item.get("birth_segment") != "acceptance_probe"
    ]
    if not targets:
        return {"counter": counter, "records": records}
    row_pool = list(rows)
    if not row_pool:
        return {"counter": counter, "records": records}
    target_count = min(
        len(row_pool),
        max(1, int(getattr(cfg, "real_native_probation_validation_rows", 32))),
    )
    margin = int(getattr(cfg, "real_native_probation_noise_margin_wins", 1))
    for cid, item in targets:
        rng = random.Random(int(seed) + _phase45_stable_int(cid))
        validation_rows = rng.sample(row_pool, target_count) if len(row_pool) > target_count else list(row_pool)
        row_ids = [int(row.get("row_id", index)) for index, row in enumerate(validation_rows)]
        eval_seed = int(seed) + _phase45_stable_int(cid) + 17
        off_eval = _phase42_ecology_policy_traces(
            cfg,
            validation_rows,
            runtime,
            score_provider,
            seed=eval_seed,
            policy_name=f"phase3_18_{segment_name}_probation_off_{cid}",
            success_kind=success_kind,
            mature_only=True,
        )
        on_eval = _phase42_ecology_policy_traces(
            cfg,
            validation_rows,
            runtime,
            score_provider,
            seed=eval_seed,
            policy_name=f"phase3_18_{segment_name}_probation_on_{cid}",
            success_kind=success_kind,
            mature_only=True,
            enabled_non_mature_ids=(cid,),
        )
        paired = _phase41_paired_outcome_table(
            on_eval,
            off_eval,
            margin_wins=margin,
            label=f"{segment_name}_probation_{cid}_on_vs_off",
        )
        discordant = int(paired["discordant_delta_left_minus_right"])
        if discordant > margin:
            decision = "confirmed"
        elif discordant < -margin:
            decision = "demoted"
        else:
            decision = "parked"
        before_weight = float(item.get("routing_weight_override", _real_native_composite_weight(item, cfg)))
        runtime.apply_probation_confirmation(
            composite_id=cid,
            decision=decision,
            step=int(step),
            reason=f"{segment_name}_validation_discordant_delta_{discordant}_margin_{margin}",
            paired=paired,
            validation_row_ids=row_ids,
        )
        after_item = runtime.population.get(cid, {})
        after_weight = float(after_item.get("routing_weight_override", _real_native_composite_weight(after_item or item, cfg)))
        counter["probation_cells_tested"] += 1
        counter[f"probation_{decision}"] += 1
        counter[f"probation_state_after:{after_item.get('state', 'missing')}"] += 1
        records.append(
            {
                "segment": str(segment_name),
                "composite_id": cid,
                "decision": decision,
                "state_after": str(after_item.get("state", "missing")),
                "children": list(item.get("children", ())),
                "birth_segment": item.get("birth_segment"),
                "probation_entry_event": item.get("probation_entry_event"),
                "probation_retest_count_after": int(after_item.get("probation_retest_count", 0)),
                "validation_row_ids": row_ids,
                "validation_row_count": len(validation_rows),
                "validation_margin_wins": margin,
                "paired": paired,
                "wins_on": int(on_eval["wins"]),
                "wins_off": int(off_eval["wins"]),
                "validation_delta_on_minus_off": int(on_eval["wins"]) - int(off_eval["wins"]),
                "routing_weight_before": round(before_weight, 6),
                "routing_weight_after": round(after_weight, 6),
                "promotion_weight_jump": round(after_weight - before_weight, 6),
            }
        )
    return {"counter": counter, "records": records}


def _phase49_confirm_probation_cells_dose_response(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    runtime: _GraphNativeCompositeRuntime,
    score_provider: Any,
    rows: Sequence[Mapping[str, Any]],
    success_kind: str,
    seed: int,
    step: int,
    segment_name: str,
) -> dict[str, Any]:
    counter: Counter[str] = Counter()
    records: list[dict[str, Any]] = []
    targets = [
        (str(cid), item)
        for cid, item in sorted(runtime.population.items())
        if item.get("state") == "PROBATION" and item.get("birth_segment") != "acceptance_probe"
    ]
    if not targets:
        return {"counter": counter, "records": records}
    row_pool = list(rows)
    if not row_pool:
        return {"counter": counter, "records": records}
    target_count = min(
        len(row_pool),
        max(1, int(getattr(cfg, "real_native_probation_validation_rows", 32))),
    )
    margin = int(getattr(cfg, "real_native_probation_noise_margin_wins", 1))
    doses = tuple(float(value) for value in getattr(cfg, "real_native_probation_dose_multipliers", (1.0,)) if float(value) > 0)
    if not doses:
        doses = (1.0,)
    for cid, item in targets:
        rng = random.Random(int(seed) + _phase45_stable_int(cid))
        validation_rows = rng.sample(row_pool, target_count) if len(row_pool) > target_count else list(row_pool)
        row_ids = [int(row.get("row_id", index)) for index, row in enumerate(validation_rows)]
        eval_seed = int(seed) + _phase45_stable_int(cid) + 17
        original_override = item.get("routing_weight_override")
        base_weight = float(original_override if original_override is not None else _real_native_composite_weight(item, cfg))
        off_eval = _phase42_ecology_policy_traces(
            cfg,
            validation_rows,
            runtime,
            score_provider,
            seed=eval_seed,
            policy_name=f"phase3_19_{segment_name}_dose_probation_off_{cid}",
            success_kind=success_kind,
            mature_only=True,
        )
        dose_records: list[dict[str, Any]] = []
        confirmed_dose: float | None = None
        confirmed_weight: float | None = None
        representative_paired: Mapping[str, Any] | None = None
        for dose in doses:
            item["routing_weight_override"] = float(base_weight * dose)
            on_eval = _phase42_ecology_policy_traces(
                cfg,
                validation_rows,
                runtime,
                score_provider,
                seed=eval_seed,
                policy_name=f"phase3_19_{segment_name}_dose_{dose:g}_probation_on_{cid}",
                success_kind=success_kind,
                mature_only=True,
                enabled_non_mature_ids=(cid,),
            )
            paired = _phase41_paired_outcome_table(
                on_eval,
                off_eval,
                margin_wins=margin,
                label=f"{segment_name}_probation_{cid}_dose_{dose:g}_on_vs_off",
            )
            discordant = int(paired["discordant_delta_left_minus_right"])
            row = {
                "dose_multiplier": float(dose),
                "routed_weight": round(float(base_weight * dose), 6),
                "wins_on": int(on_eval["wins"]),
                "wins_off": int(off_eval["wins"]),
                "validation_delta_on_minus_off": int(on_eval["wins"]) - int(off_eval["wins"]),
                "discordant_delta": discordant,
                "conditional_gate_applied_count": int(on_eval.get("conditional_gate_applied_count", 0)),
                "conditional_gate_changed_choice_count": int(on_eval.get("conditional_gate_changed_choice_count", 0)),
                "conditional_gate_composite_ids": list(on_eval.get("conditional_gate_composite_ids", ())),
                "off_conditional_gate_applied_count": int(off_eval.get("conditional_gate_applied_count", 0)),
                "off_conditional_gate_changed_choice_count": int(off_eval.get("conditional_gate_changed_choice_count", 0)),
                "paired": paired,
            }
            dose_records.append(row)
            if confirmed_dose is None and discordant > margin:
                confirmed_dose = float(dose)
                confirmed_weight = float(base_weight * dose)
                representative_paired = paired
        if original_override is None:
            item.pop("routing_weight_override", None)
        else:
            item["routing_weight_override"] = float(original_override)
        discordants = [int(record["discordant_delta"]) for record in dose_records]
        if confirmed_dose is not None:
            decision = "confirmed"
            decision_class = "positive_lowest_dose"
            paired_for_decision = representative_paired or dose_records[0]["paired"]
        elif discordants and all(value < -margin for value in discordants):
            decision = "demoted"
            decision_class = "negative_all_doses"
            paired_for_decision = dose_records[-1]["paired"]
        elif discordants and all(abs(value) <= margin for value in discordants):
            decision = "parked"
            decision_class = "flat_all_doses"
            paired_for_decision = dose_records[-1]["paired"]
        else:
            decision = "parked"
            decision_class = "mixed_nonconfirming"
            paired_for_decision = dose_records[-1]["paired"]
        runtime.apply_probation_confirmation(
            composite_id=cid,
            decision=decision,
            step=int(step),
            reason=f"{segment_name}_dose_response_{decision_class}_margin_{margin}",
            paired=paired_for_decision,
            validation_row_ids=row_ids,
            confirmed_routing_weight=confirmed_weight,
            confirmed_dose_multiplier=confirmed_dose,
            validation_dose_records=dose_records,
            decision_class=decision_class,
        )
        after_item = runtime.population.get(cid, {})
        counter["probation_cells_tested"] += 1
        counter[f"probation_{decision}"] += 1
        counter[f"probation_decision_class:{decision_class}"] += 1
        counter[f"probation_state_after:{after_item.get('state', 'missing')}"] += 1
        if confirmed_dose is not None:
            counter[f"confirmed_dose:{confirmed_dose:g}"] += 1
        records.append(
            {
                "segment": str(segment_name),
                "composite_id": cid,
                "decision": decision,
                "decision_class": decision_class,
                "state_after": str(after_item.get("state", "missing")),
                "children": list(item.get("children", ())),
                "birth_segment": item.get("birth_segment"),
                "probation_entry_event": item.get("probation_entry_event"),
                "probation_retest_count_after": int(after_item.get("probation_retest_count", 0)),
                "validation_row_ids": row_ids,
                "validation_row_count": len(validation_rows),
                "validation_margin_wins": margin,
                "base_routing_weight": round(base_weight, 6),
                "confirmed_dose_multiplier": confirmed_dose,
                "confirmed_routing_weight": None if confirmed_weight is None else round(float(confirmed_weight), 6),
                "dose_records": dose_records,
                "paired": paired_for_decision,
                "validation_delta_on_minus_off": int(paired_for_decision.get("left_minus_right_wins", 0)),
            }
        )
    return {"counter": counter, "records": records}


def _phase49_noop_ablation_control_old_pipeline(
    cfg: StageBEcologicalDiscoveryConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
    runtime: _GraphNativeCompositeRuntime,
    score_provider: Any,
    *,
    full_eval: Mapping[str, Any],
    seed: int,
) -> dict[str, Any]:
    subjects = [
        item for item in runtime.population.values()
        if item["state"] == "MATURE"
    ][: int(cfg.real_native_max_ablation_subjects)]
    records: list[dict[str, Any]] = []
    offsets: list[int] = []
    for index, item in enumerate(subjects):
        noop = _real_native_evaluate_policy(
            cfg,
            heldout_rows,
            runtime,
            score_provider,
            seed=int(seed) + index * 101,
            policy_name=f"noop_without_{item['composite_id']}",
            disabled=set(),
        )
        offset = int(full_eval["wins"]) - int(noop["wins"])
        offsets.append(offset)
        records.append(
            {
                "composite_id": str(item["composite_id"]),
                "children": list(item.get("children", ())),
                "full_wins": int(full_eval["wins"]),
                "noop_wins": int(noop["wins"]),
                "noop_offset_full_minus_noop": offset,
                "paired": _phase41_paired_outcome_table(
                    full_eval,
                    noop,
                    margin_wins=0,
                    label=f"noop_old_ablation_path_{item['composite_id']}",
                ),
            }
        )
    nonzero = [value for value in offsets if value != 0]
    return {
        "control": "old_3_17_ablation_pipeline_noop_disable_none",
        "subject_count": len(subjects),
        "nonzero_offset_count": len(nonzero),
        "passed": bool(not nonzero),
        "offset_min": min(offsets) if offsets else None,
        "offset_median": sorted(offsets)[len(offsets) // 2] if offsets else None,
        "offset_max": max(offsets) if offsets else None,
        "config_diff": {
            "full_eval_path": "_phase42_ecology_policy_traces",
            "full_eval_black_reply_policy": str(full_eval.get("black_reply_policy", "unknown")),
            "noop_path": "_real_native_evaluate_policy -> _evaluate_policy",
            "noop_default_black_reply_policy": "fixed_seed",
            "seed_schedule_same_as_old_ablation": True,
        },
        "verdict": (
            "pass_no_offset"
            if not nonzero
            else "fail_runner_provenance_offset"
        ),
        "records": records,
    }


def _phase49_controlled_ablation_health(
    cfg: StageBEcologicalDiscoveryConfig,
    heldout_rows: Sequence[Mapping[str, Any]],
    runtime: _GraphNativeCompositeRuntime,
    score_provider: Any,
    *,
    full_eval: Mapping[str, Any],
    seed: int,
    success_kind: str,
) -> dict[str, Any]:
    subjects = [
        item for item in runtime.population.values()
        if item["state"] == "MATURE"
    ][: int(cfg.real_native_max_ablation_subjects)]
    records: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    noop = _phase42_ecology_policy_traces(
        cfg,
        heldout_rows,
        runtime,
        score_provider,
        seed=int(seed),
        policy_name="controlled_ablation_noop",
        success_kind=success_kind,
        mature_only=True,
    )
    noop_paired = _phase41_paired_outcome_table(
        full_eval,
        noop,
        margin_wins=0,
        label="controlled_ablation_noop_full_vs_noop",
    )
    noop_passed = int(noop_paired["discordant_delta_left_minus_right"]) == 0 and int(noop_paired["left_minus_right_wins"]) == 0
    for item in subjects:
        ablated = _phase42_ecology_policy_traces(
            cfg,
            heldout_rows,
            runtime,
            score_provider,
            seed=int(seed),
            policy_name=f"controlled_without_{item['composite_id']}",
            success_kind=success_kind,
            mature_only=True,
            disabled_mature_ids=(str(item["composite_id"]),),
        )
        paired = _phase41_paired_outcome_table(
            full_eval,
            ablated,
            margin_wins=0,
            label=f"controlled_cell_on_vs_removed_{item['composite_id']}",
        )
        delta = int(full_eval["wins"]) - int(ablated["wins"])
        classification = "load_bearing" if delta > 0 else "inert" if delta == 0 else "harmful"
        counts[classification] += 1
        records.append(
            {
                "composite_id": str(item["composite_id"]),
                "classification": classification,
                "ablation_delta": delta,
                "full_wins": int(full_eval["wins"]),
                "ablated_wins": int(ablated["wins"]),
                "paired": paired,
                "birth_segment": item.get("birth_segment"),
                "confirmed_dose_multiplier": item.get("confirmed_dose_multiplier"),
                "routing_weight": item.get("routing_weight_override"),
                "children": list(item.get("children", ())),
            }
        )
    return {
        "subject": "mature_composites_only_controlled_exact_adversarial",
        "control_noop_passed": bool(noop_passed),
        "control_noop": {
            "full_wins": int(full_eval["wins"]),
            "noop_wins": int(noop["wins"]),
            "paired": noop_paired,
        },
        "composite_count": len(subjects),
        "load_bearing_count": int(counts["load_bearing"]),
        "inert_count": int(counts["inert"]),
        "harmful_count": int(counts["harmful"]),
        "records": records,
    }


def _phase46_backlog_snapshot(
    cfg: StageBEcologicalDiscoveryConfig,
    runtime: _GraphNativeCompositeRuntime,
    *,
    segment: str,
    step: int,
    row_index: int,
    event: str,
) -> dict[str, Any]:
    coverage = _phase45_scheduled_coverage(runtime, int(cfg.real_native_audition_budget_per_cell))
    return {
        "segment": segment,
        "step": int(step),
        "row_index": int(row_index),
        "event": str(event),
        "trial_cell_count": int(coverage.get("trial_cell_count", 0)),
        "under_budget_trial_count": int(coverage.get("under_budget_trial_count", 0)),
        "under_budget_trial_fraction": float(coverage.get("under_budget_trial_fraction", 0.0)),
        "threshold": float(getattr(cfg, "real_native_homeostatic_backlog_threshold", 0.0)),
        "histogram": dict(coverage.get("histogram", {})),
    }


def _phase46_under_k_explanation(
    runtime: _GraphNativeCompositeRuntime,
    *,
    firing_buffer: Mapping[str, Sequence[Mapping[str, Any]]],
    budget: int,
) -> dict[str, Any]:
    reasons: Counter[str] = Counter()
    judged_hist: Counter[int] = Counter()
    buffer_hist: Counter[int] = Counter()
    examples: list[dict[str, Any]] = []
    for cid, item in sorted(runtime.population.items()):
        if item.get("state") != "TRIAL" or item.get("birth_segment") == "acceptance_probe":
            continue
        judged = int(item.get("audition_count", 0)) + int(item.get("scheduled_audition_sample_count", 0))
        if judged >= int(budget):
            continue
        remaining = int(budget) - judged
        buffer_count = len(firing_buffer.get(cid, ()))
        judged_hist[judged] += 1
        buffer_hist[min(buffer_count, int(budget))] += 1
        if buffer_count <= 0:
            reason = "no_firing_samples_in_replay_buffer"
        elif buffer_count < remaining:
            reason = "firing_set_smaller_than_remaining_budget"
        else:
            reason = "scheduler_did_not_spend_available_samples"
        reasons[reason] += 1
        if len(examples) < 8:
            examples.append(
                {
                    "composite_id": cid,
                    "judged": judged,
                    "remaining": remaining,
                    "buffer_samples": buffer_count,
                    "birth_step": item.get("birth_step"),
                    "children": list(item.get("children", ())),
                }
            )
    return {
        "under_budget_trial_count": int(sum(reasons.values())),
        "reason_counts": dict(sorted(reasons.items())),
        "judged_histogram": {str(key): int(value) for key, value in sorted(judged_hist.items())},
        "buffer_sample_histogram_capped_at_budget": {
            str(key): int(value) for key, value in sorted(buffer_hist.items())
        },
        "examples": examples,
    }


def _phase46_collect_complete_flush_samples(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    runtime: _GraphNativeCompositeRuntime,
    score_provider: Any,
    rows: Sequence[Mapping[str, Any]],
    firing_buffer: defaultdict[str, list[dict[str, Any]]],
    success_kind: str,
    seed: int,
) -> dict[str, Any]:
    budget = int(cfg.real_native_audition_budget_per_cell)
    target_ids = {
        str(cid)
        for cid, item in runtime.population.items()
        if item.get("state") == "TRIAL"
        and item.get("birth_segment") != "acceptance_probe"
        and int(item.get("audition_count", 0)) + int(item.get("scheduled_audition_sample_count", 0)) < budget
    }
    if not target_ids:
        return {
            "target_trial_cells": 0,
            "rows_scanned": 0,
            "white_positions_scanned": 0,
            "samples_added": 0,
            "cells_with_samples_after_scan": 0,
        }
    scorer = None if cfg.fast_exact_judge or success_kind == "approach_waypoint" else load_canonical_mate2_first_scorer()
    mate2_cache, enter_cache = _new_judge_cache()
    seen: set[tuple[str, str, str, str]] = set()
    for cid, samples in firing_buffer.items():
        for sample in samples:
            seen.add(
                (
                    str(cid),
                    str(sample.get("fen")),
                    str(sample.get("host_move_uci")),
                    str(sample.get("cell_move_uci")),
                )
            )
    rows_scanned = 0
    white_positions_scanned = 0
    samples_added = 0
    rng = random.Random(seed)
    for row_index, row in enumerate(rows):
        if all(len(firing_buffer.get(cid, ())) >= budget for cid in target_ids):
            break
        rows_scanned += 1
        board = chess.Board(str(row["fen"]))
        counts: Counter[Any] = Counter({_position_repetition_key(board): 1, board._transposition_key(): 1})
        for ply in range(int(cfg.horizon_plies)):
            if board.turn != chess.WHITE or board.is_game_over(claim_draw=False):
                break
            white_positions_scanned += 1
            selected = runtime.choose_move(
                board,
                counts,
                score_provider,
                seed=int(seed) + row_index * 997 + ply,
                discriminative=True,
                include_trial_proposals=True,
            )
            for firing in selected.get("trial_cell_firings", ()):
                cid = str(firing.get("composite_id"))
                if cid not in target_ids or len(firing_buffer.get(cid, ())) >= budget:
                    continue
                if firing.get("move") is None or firing.get("host_move") is None:
                    continue
                key = (
                    cid,
                    board.fen(),
                    str(firing.get("host_move_uci")),
                    str(firing.get("move_uci")),
                )
                if key in seen:
                    continue
                seen.add(key)
                firing_buffer[cid].append(
                    {
                        "fen": board.fen(),
                        "counts": Counter(counts),
                        "host_move_uci": str(firing["host_move_uci"]),
                        "cell_move_uci": str(firing["move_uci"]),
                        "agrees_with_host": bool(firing.get("agrees_with_host", False)),
                        "row_id": int(row.get("row_id", row_index)),
                        "ply": int(ply),
                        "source": "complete_flush_active_scan",
                    }
                )
                samples_added += 1
            move = _phase44_host_argmax_move(board, counts, score_provider)
            if move is None or move not in board.legal_moves:
                break
            if int(counts.get(_after_move_repetition_key(board, move), 0)) >= 2:
                break
            board.push(move)
            counts[_position_repetition_key(board)] += 1
            counts[board._transposition_key()] += 1
            if board.is_game_over(claim_draw=False):
                break
            reply = _select_black_reply_for_rollout(
                cfg,
                board,
                rng,
                success_kind=success_kind,
                scorer=scorer,
                mate2_cache=mate2_cache,
                enter_cache=enter_cache,
                black_reply_policy="exact_adversarial",
            )
            if reply is None or reply not in board.legal_moves:
                break
            board.push(reply)
            counts[_position_repetition_key(board)] += 1
            counts[board._transposition_key()] += 1
    cells_with_samples = sum(1 for cid in target_ids if len(firing_buffer.get(cid, ())) > 0)
    return {
        "target_trial_cells": len(target_ids),
        "rows_scanned": rows_scanned,
        "white_positions_scanned": white_positions_scanned,
        "samples_added": samples_added,
        "cells_with_samples_after_scan": cells_with_samples,
        "cells_without_samples_after_scan": len(target_ids) - cells_with_samples,
    }


def _phase46_phase315_under_k_diagnosis() -> dict[str, Any]:
    path = Path("reports/autogrowth/clean_slate_krk/phase3_15_scheduled_audition_economy/summary.json")
    if not path.exists():
        return {"available": False, "path": str(path)}
    summary = json.loads(path.read_text(encoding="utf-8"))
    rows = list(summary.get("per_seed", ()))
    if not rows:
        return {"available": False, "path": str(path), "reason": "no_per_seed_rows"}
    row = rows[0]
    stage_a_training = row.get("stage_a", {}).get("ecology_training", {})
    coverage = stage_a_training.get("scheduled_coverage", {})
    stats = stage_a_training.get("scheduled_audition_stats", {})
    return {
        "available": True,
        "source_schema": summary.get("schema_version"),
        "source_seed": int(row.get("seed", 0)),
        "under_k": {
            "trial_cell_count": int(coverage.get("trial_cell_count", 0)),
            "under_budget_trial_count": int(coverage.get("under_budget_trial_count", 0)),
            "under_budget_trial_fraction": float(coverage.get("under_budget_trial_fraction", 0.0)),
            "histogram": dict(coverage.get("histogram", {})),
        },
        "cap_forensics": {
            "live_audition_per_ply_cap_skips": int(stage_a_training.get("audition_cap_skip_count", 0)),
            "scheduled_per_chunk_compute_cap": False,
            "scheduled_complete_flush_existed": False,
            "scheduled_samples": int(stats.get("scheduled_samples", 0)),
            "agreement_only_underfilled_events": int(stats.get("agreement_only_underfilled", 0)),
            "trial_cells_without_firing_samples_events": int(stats.get("trial_cells_without_firing_samples", 0)),
        },
        "conclusion": (
            "The 3.15 court was not blocked by the live per-ply audition cap. It reused only the replay "
            "firing buffer, so agreement-only cells with fewer than K samples and cells with no buffered "
            "firings survived under-K. Birth timing was not stored in 3.15, so late-birth contribution "
            "cannot be reconstructed from that artifact."
        ),
    }


def _phase46_composite_family(children: Sequence[str]) -> str:
    atoms = sorted(str(child) for child in children)
    neighbor_zero = [
        atom for atom in atoms
        if "bk_neighbor_" in atom and "available=zero" in atom
    ]
    if len(atoms) == 2 and len(neighbor_zero) == 2:
        return "FAMILY-CONFINE"
    has_safe_rook = any("rook_attacked_after=0" in atom for atom in atoms)
    has_edge_distance = any(
        "to_file_edge_distance=" in atom or "to_rank_edge_distance=" in atom
        for atom in atoms
    )
    if len(atoms) == 2 and has_safe_rook and has_edge_distance:
        return "FAMILY-SAFEROOK"
    return "FAMILY-EXACT:" + " AND ".join(atoms)


def _phase46_mature_family_recurrence(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    families: dict[str, dict[str, Any]] = {}
    for row in per_seed:
        seed = int(row.get("seed", 0))
        for item in row.get("candidate_fate_log", ()):
            if item.get("state") != "MATURE":
                continue
            family = _phase46_composite_family(item.get("children", ()))
            record = families.setdefault(
                family,
                {
                    "family": family,
                    "seeds": set(),
                    "mature_count": 0,
                    "examples": [],
                    "birth_segments": Counter(),
                },
            )
            record["seeds"].add(seed)
            record["mature_count"] += 1
            record["birth_segments"][str(item.get("birth_segment"))] += 1
            if len(record["examples"]) < 8:
                record["examples"].append(
                    {
                        "seed": seed,
                        "composite_id": str(item.get("composite_id")),
                        "children": list(item.get("children", ())),
                        "birth_segment": str(item.get("birth_segment")),
                    }
                )
    rows: list[dict[str, Any]] = []
    for family, record in families.items():
        seeds = sorted(record["seeds"])
        rows.append(
            {
                "family": family,
                "seed_count": len(seeds),
                "seeds": seeds,
                "mature_count": int(record["mature_count"]),
                "recurs_3_of_5": len(seeds) >= 3,
                "birth_segments": dict(sorted(record["birth_segments"].items())),
                "examples": record["examples"],
            }
        )
    rows.sort(key=lambda item: (-int(item["seed_count"]), str(item["family"])))
    return rows


def _phase44_audition_starvation(training: Mapping[str, Any]) -> dict[str, Any]:
    distribution = training.get("auditions_per_cell_distribution", {})
    mean = float(distribution.get("mean", 0.0)) if isinstance(distribution, Mapping) else 0.0
    cell_count = int(distribution.get("cell_count", 0)) if isinstance(distribution, Mapping) else 0
    threshold = float(training.get("audition_starvation_min_per_cell", 1.0))
    return {
        "starved": bool(cell_count > 0 and mean < threshold),
        "mean_auditions_per_cell": mean,
        "cell_count": cell_count,
        "threshold": threshold,
        "trial_cell_proposal_count": int(training.get("trial_cell_proposal_count", 0)),
        "audition_request_count": int(training.get("audition_request_count", 0)),
        "audition_count": int(training.get("audition_count", 0)),
    }


def _phase46_spawn_from_context(
    cfg: StageBEcologicalDiscoveryConfig,
    runtime: _GraphNativeCompositeRuntime,
    ctx: Mapping[str, Any],
    *,
    rng: random.Random,
) -> Counter[str]:
    stats: Counter[str] = Counter()
    threshold = float(getattr(cfg, "real_native_homeostatic_backlog_threshold", 0.0))
    triggers = _internal_triggers(cfg, ctx, Counter(), defaultdict(Counter))
    source_signature = str(ctx["percept_signature"])
    if threshold > 0.0:
        coverage = _phase45_scheduled_coverage(runtime, int(cfg.real_native_audition_budget_per_cell))
        trial_count = int(coverage.get("trial_cell_count", 0))
        backlog = float(coverage.get("under_budget_trial_fraction", 0.0))
        if trial_count > 0 and backlog >= threshold:
            for trigger in triggers[: int(cfg.real_native_max_births_per_row)]:
                stats["births_deferred_by_backlog"] += 1
                stats[f"births_deferred_by_backlog_trigger:{trigger}"] += 1
                stats[f"births_deferred_by_backlog_parent:{_real_native_parent_id(source_signature)}"] += 1
            return stats
    before = len(runtime.population)
    _phase43_spawn_from_context(cfg, runtime, ctx, rng=rng)
    stats["births_spawned_after_backlog_gate"] += max(0, len(runtime.population) - before)
    return stats


def _phase47_spawn_from_context(
    cfg: StageBEcologicalDiscoveryConfig,
    runtime: _GraphNativeCompositeRuntime,
    ctx: Mapping[str, Any],
    *,
    rng: random.Random,
) -> Counter[str]:
    stats: Counter[str] = Counter()
    triggers = _internal_triggers(cfg, ctx, Counter(), defaultdict(Counter))
    source_signature = str(ctx["percept_signature"])
    live_trial_states = {"TRIAL", "PROBATION"} if bool(getattr(cfg, "real_native_probation_enabled", False)) else {"TRIAL"}
    trial_count = sum(
        1
        for item in runtime.population.values()
        if item.get("state") in live_trial_states and item.get("birth_segment") != "acceptance_probe"
    )
    under_k_count = int(
        _phase45_scheduled_coverage(
            runtime,
            int(cfg.real_native_audition_budget_per_cell),
        ).get("under_budget_trial_count", 0)
    )
    trial_max = int(getattr(cfg, "real_native_trial_band_max", 0))
    throughput = _phase47_court_throughput_per_chunk(cfg)
    reasons: list[str] = []
    if trial_max > 0 and trial_count >= trial_max:
        reasons.append("trial_band_max_reached")
    if under_k_count >= throughput:
        reasons.append("under_k_count_at_or_above_court_throughput")
    if reasons:
        for trigger in triggers[: int(cfg.real_native_max_births_per_row)]:
            stats["births_deferred_by_count_homeostasis"] += 1
            stats[f"births_deferred_by_count_homeostasis_trigger:{trigger}"] += 1
            for reason in reasons:
                stats[f"births_deferred_by_count_homeostasis_reason:{reason}"] += 1
            stats[f"births_deferred_by_count_homeostasis_parent:{_real_native_parent_id(source_signature)}"] += 1
        return stats
    before = len(runtime.population)
    _phase43_spawn_from_context(cfg, runtime, ctx, rng=rng)
    stats["births_spawned_after_count_homeostasis_gate"] += max(0, len(runtime.population) - before)
    stats["trial_count_before_birth_gate"] += trial_count
    stats["under_k_count_before_birth_gate"] += under_k_count
    stats["court_throughput_per_chunk"] += throughput
    return stats


def _phase43_spawn_from_context(
    cfg: StageBEcologicalDiscoveryConfig,
    runtime: _GraphNativeCompositeRuntime,
    ctx: Mapping[str, Any],
    *,
    rng: random.Random,
) -> None:
    triggers = _internal_triggers(cfg, ctx, Counter(), defaultdict(Counter))
    spawned = 0
    source_signature = str(ctx["percept_signature"])
    for trigger in triggers:
        if spawned >= int(cfg.real_native_max_births_per_row):
            break
        if not runtime.parent_capacity_open(source_signature):
            runtime.record_birth_blocked_by_capacity(trigger=trigger, source_signature=source_signature)
            continue
        children = _candidate_child_pool(ctx, trigger=trigger)
        if len(children) < cfg.composite_width:
            continue
        combos = list(combinations(children[: cfg.max_child_pool], cfg.composite_width))
        if not combos:
            continue
        before = len(runtime.population)
        selected_children = tuple(sorted(rng.choice(combos)))
        runtime.spawn(
            selected_children,
            trigger=trigger,
            birth_segment=str(ctx.get("segment", "unknown")),
            birth_row_id=int(ctx.get("row_id", -1)),
            source_signature=source_signature,
            birth_step=int(ctx.get("global_step", ctx.get("step", -1))),
        )
        if len(runtime.population) > before:
            runtime.trigger_counts[trigger] += 1
            spawned += 1


def _phase43_first_flip_event(
    cfg: StageBEcologicalDiscoveryConfig,
    outcome: Mapping[str, Any],
    *,
    success_kind: str,
) -> dict[str, Any] | None:
    transitions = [item for item in outcome.get("transition_steps", ()) if isinstance(item, Mapping)]
    for index, step in enumerate(transitions):
        before_fence = bool(step.get("before_fence_established"))
        after_white_fence = step.get("after_white_fence_established")
        after_black_fence = step.get("after_black_fence_established")
        before_rook = bool(step.get("before_rook_present"))
        after_white_rook = step.get("after_white_rook_present")
        after_black_rook = step.get("after_black_rook_present")
        before_waypoint = _phase42_waypoint_from_fen(step.get("before_fen"))
        after_white_waypoint = _phase42_waypoint_from_fen(step.get("after_white_fen"))
        after_black_waypoint = _phase42_waypoint_from_fen(step.get("after_black_fen"))
        if before_rook and after_white_rook is False:
            return {"ply": index, "valence": "negative", "reason": "rook_lost_after_white"}
        if after_white_rook is True and after_black_rook is False:
            return {"ply": index, "valence": "negative", "reason": "rook_lost_after_black"}
        if before_fence and after_white_fence is False:
            return {"ply": index, "valence": "negative", "reason": "fence_broken_after_white"}
        if after_white_fence is True and after_black_fence is False:
            return {"ply": index, "valence": "negative", "reason": "fence_broken_after_black"}
        if before_fence is False and after_white_fence is True:
            return {"ply": index, "valence": "positive", "reason": "fence_established_after_white"}
        if after_white_fence is False and after_black_fence is True:
            return {"ply": index, "valence": "positive", "reason": "fence_established_after_black"}
        if before_waypoint is False and after_white_waypoint is True:
            return {"ply": index, "valence": "positive", "reason": "waypoint_entered_after_white"}
        if after_white_waypoint is False and after_black_waypoint is True:
            return {"ply": index, "valence": "positive", "reason": "waypoint_entered_after_black"}
    if bool(outcome.get("success")) and transitions:
        return {
            "ply": len(transitions) - 1,
            "valence": "positive",
            "reason": f"{success_kind}_success_endpoint_confirmed",
        }
    return None


def _phase43_choice_change_rate(training: Mapping[str, Any]) -> float:
    return float(training.get("choice_changed_ply_rate", 0.0))


def _phase43_population_stability(
    cfg: StageBEcologicalDiscoveryConfig,
    curve: Sequence[Mapping[str, Any]],
    *,
    segment: str,
) -> dict[str, Any]:
    rows = [row for row in curve if row.get("segment") == segment]
    if not rows:
        return {"stable": False, "reason": "no_population_curve_for_segment"}
    final = rows[-1]
    alive_limit = int(cfg.real_native_max_live_composites) * int(cfg.real_native_stability_band_multiplier)
    alive_ok = int(final.get("alive_total", 0)) <= alive_limit
    window = rows[-4:] if len(rows) >= 4 else rows
    trial_values = [
        int(row.get("trial", 0)) + int(row.get("probation", 0))
        for row in window
    ]
    plateau_tolerance = max(4, int(cfg.real_native_max_live_composites))
    trial_plateau = (max(trial_values) - min(trial_values)) <= plateau_tolerance if trial_values else False
    first_mp = int(rows[0].get("mature", 0)) + int(rows[0].get("pruned", 0))
    final_mp = int(final.get("mature", 0)) + int(final.get("pruned", 0))
    mature_or_pruned_growing = final_mp > first_mp
    return {
        "stable": bool(alive_ok and trial_plateau and mature_or_pruned_growing),
        "alive_ok": bool(alive_ok),
        "alive_limit": alive_limit,
        "final_alive": int(final.get("alive_total", 0)),
        "trial_plateau": bool(trial_plateau),
        "trial_plus_probation_plateau_window_values": trial_values,
        "trial_plateau_tolerance": plateau_tolerance,
        "mature_or_pruned_growing": bool(mature_or_pruned_growing),
        "first_mature_plus_pruned": first_mp,
        "final_mature_plus_pruned": final_mp,
    }


def _phase43_population_stop_rule(
    cfg: StageBEcologicalDiscoveryConfig,
    runtime: _GraphNativeCompositeRuntime,
) -> dict[str, Any]:
    births = len(
        [
            item for item in runtime.population.values()
            if item.get("birth_segment") != "acceptance_probe"
        ]
    )
    alive = sum(1 for item in runtime.population.values() if item["state"] in {"TRIAL", "PROBATION", "MATURE"})
    mature = sum(1 for item in runtime.population.values() if item["state"] == "MATURE")
    alive_limit = int(cfg.real_native_max_live_composites) * int(cfg.real_native_stability_band_multiplier)
    return {
        "population_collapse_to_zero": bool(births > 0 and alive == 0),
        "unbounded_explosion": bool(alive > alive_limit),
        "mature_population_failed_to_form": bool(births > 0 and mature == 0),
        "birth_count_excluding_acceptance_probe": births,
        "alive_total": alive,
        "mature_count": mature,
        "alive_limit": alive_limit,
    }


def _phase42_positive_flip_targets(
    cfg: StageBEcologicalDiscoveryConfig,
    outcome: Mapping[str, Any],
    decisions: Sequence[Mapping[str, Any]],
    *,
    success_kind: str,
) -> list[dict[str, Any]]:
    decision_by_ply = {int(item.get("ply", -1)): item for item in decisions}
    transitions = [item for item in outcome.get("transition_steps", ()) if isinstance(item, Mapping)]
    flip_index: int | None = None
    reason = ""
    for index, step in enumerate(transitions):
        before_fence = bool(step.get("before_fence_established"))
        after_white_fence = step.get("after_white_fence_established")
        after_black_fence = step.get("after_black_fence_established")
        before_waypoint = _phase42_waypoint_from_fen(step.get("before_fen"))
        after_white_waypoint = _phase42_waypoint_from_fen(step.get("after_white_fen"))
        after_black_waypoint = _phase42_waypoint_from_fen(step.get("after_black_fen"))
        if before_fence is False and after_white_fence is True:
            flip_index = index
            reason = "fence_established_after_white"
            break
        if after_white_fence is False and after_black_fence is True:
            flip_index = index
            reason = "fence_established_after_black"
            break
        if before_waypoint is False and after_white_waypoint is True:
            flip_index = index
            reason = "waypoint_entered_after_white"
            break
        if after_white_waypoint is False and after_black_waypoint is True:
            flip_index = index
            reason = "waypoint_entered_after_black"
            break
    if flip_index is None and bool(outcome.get("success")) and decisions:
        flip_index = max(int(item.get("ply", 0)) for item in decisions)
        reason = f"{success_kind}_success_endpoint_confirmed"
    if flip_index is None:
        return []
    targets: list[dict[str, Any]] = []
    for offset in range(0, int(cfg.real_native_positive_flip_window) + 1):
        ply = int(flip_index) - offset
        decision = decision_by_ply.get(ply)
        if not decision:
            continue
        active_ids = list(decision.get("active_composite_ids", ()))
        if not active_ids:
            continue
        targets.append(
            {
                "ply": ply,
                "discount": 1.0 if offset == 0 else 0.5 if offset == 1 else 0.25,
                "reason": reason if offset == 0 else "pre_positive_flip_eligibility",
                "active_composite_ids": active_ids,
            }
        )
    return targets


def _phase42_waypoint_from_fen(fen: Any) -> bool | None:
    if not fen:
        return None
    try:
        return bool(_approach_waypoint_success(chess.Board(str(fen))))
    except ValueError:
        return None


def _phase42_ecology_policy_traces(
    cfg: StageBEcologicalDiscoveryConfig,
    rows: Sequence[Mapping[str, Any]],
    runtime: _GraphNativeCompositeRuntime,
    score_provider: Any,
    *,
    seed: int,
    policy_name: str,
    success_kind: str,
    mature_only: bool,
    enabled_non_mature_ids: Sequence[str] = (),
    disabled_mature_ids: Sequence[str] = (),
) -> dict[str, Any]:
    if mature_only:
        enabled = set(map(str, enabled_non_mature_ids))
        disabled_mature = set(map(str, disabled_mature_ids))
        disabled = {
            str(item["composite_id"])
            for item in runtime.population.values()
            if (
                (item.get("state") != "MATURE" and str(item["composite_id"]) not in enabled)
                or str(item["composite_id"]) in disabled_mature
            )
        }
    else:
        disabled = set()
    endpoints: Counter[str] = Counter()
    success_by_row: dict[str, bool] = {}
    endpoint_by_row: dict[str, str] = {}
    active_by_row: dict[str, list[str]] = {}
    all_active: set[str] = set()
    gate_applied_count = 0
    gate_changed_count = 0
    gate_composite_ids: set[str] = set()
    samples: list[dict[str, Any]] = []
    judge_cache = _new_judge_cache()
    for index, row in enumerate(rows):
        row_active: set[str] = set()
        row_gate_applied = 0
        row_gate_changed = 0

        def choose(board: chess.Board, counts: Mapping[Any, int], row_id: int, ply: int, rng: random.Random) -> chess.Move | None:
            nonlocal gate_applied_count, gate_changed_count, row_gate_applied, row_gate_changed
            selected = runtime.choose_move(
                board,
                counts,
                score_provider,
                seed=int(seed) + int(row_id) * 47 + ply,
                disabled=disabled,
            )
            row_active.update(map(str, selected.get("active_composite_ids", ())))
            gate_ids = list(map(str, selected.get("conditional_gate_composite_ids", ())))
            if bool(selected.get("conditional_gate_applied", False)):
                gate_applied_count += 1
                row_gate_applied += 1
                gate_composite_ids.update(gate_ids)
            if bool(selected.get("conditional_gate_changed_choice", False)):
                gate_changed_count += 1
                row_gate_changed += 1
            return selected.get("move")

        outcome = _rollout_policy(
            cfg,
            row,
            choose,
            seed=int(seed) + index * 31,
            policy_name=policy_name,
            judge_cache=judge_cache,
            success_kind=success_kind,
            black_reply_policy="exact_adversarial",
        )
        success_by_row[str(row["row_id"])] = bool(outcome["success"])
        endpoint_by_row[str(row["row_id"])] = str(outcome["endpoint"])
        endpoints[str(outcome["endpoint"])] += 1
        active_by_row[str(row["row_id"])] = sorted(row_active)
        all_active.update(row_active)
        if not outcome["success"] and len(samples) < int(cfg.max_samples):
            samples.append(
                {
                    "fen": row["fen"],
                    "endpoint": outcome["endpoint"],
                    "white_steps": outcome["white_steps"],
                    "active_composite_ids": sorted(row_active),
                    "conditional_gate_applied_count": row_gate_applied,
                    "conditional_gate_changed_choice_count": row_gate_changed,
                }
            )
    wins = sum(int(value) for value in success_by_row.values())
    total = len(rows)
    return {
        "policy": policy_name,
        "black_reply_policy": "exact_adversarial",
        "mature_only": bool(mature_only),
        "wins": wins,
        "nonwins": total - wins,
        "row_count": total,
        "win_rate": wins / max(1, total),
        "wilson_95": _wilson_local(wins, total),
        "endpoint_counts": dict(sorted(endpoints.items())),
        "success_by_row": success_by_row,
        "endpoint_by_row": endpoint_by_row,
        "active_composite_ids": sorted(all_active),
        "active_composite_ids_by_row": active_by_row,
        "conditional_gate_applied_count": gate_applied_count,
        "conditional_gate_changed_choice_count": gate_changed_count,
        "conditional_gate_composite_ids": sorted(gate_composite_ids),
        "runner_config": _phase38_runner_config(
            cfg,
            seed=int(seed),
            success_kind=success_kind,
            black_reply_policy="exact_adversarial",
            row_count=total,
        ),
        "sample_nonwins": samples,
    }


def _phase42_disabled_non_mature(runtime: _GraphNativeCompositeRuntime) -> set[str]:
    return {
        str(item["composite_id"])
        for item in runtime.population.values()
        if item.get("state") != "MATURE"
    }


def _phase42_ecology_gate_bundle(
    cfg: StageBEcologicalDiscoveryConfig,
    *,
    runtime: _GraphNativeCompositeRuntime,
    score_provider: Any,
    gate_rows: Sequence[Mapping[str, Any]],
    flat_baseline: Mapping[str, Any],
    host_eval: Mapping[str, Any],
    seed: int,
    rung: str,
    success_kind: str,
    gate_margin: int,
) -> dict[str, Any]:
    mature_eval = _phase42_ecology_policy_traces(
        cfg,
        gate_rows,
        runtime,
        score_provider,
        seed=int(seed),
        policy_name=f"phase3_12_{rung}_host_plus_mature",
        success_kind=success_kind,
        mature_only=True,
    )
    live_eval = _phase42_ecology_policy_traces(
        cfg,
        gate_rows,
        runtime,
        score_provider,
        seed=int(seed) + 991,
        policy_name=f"phase3_12_{rung}_host_plus_all_live",
        success_kind=success_kind,
        mature_only=False,
    )
    return {
        "mature_eval": mature_eval,
        "live_eval": live_eval,
        "mature_vs_flat_gate": _phase41_gate_result_paired(
            rung=f"{rung}_host_plus_mature",
            learner=mature_eval,
            flat=flat_baseline,
            margin_wins=gate_margin,
        ),
        "live_vs_flat_gate": _phase41_gate_result_paired(
            rung=f"{rung}_host_plus_all_live",
            learner=live_eval,
            flat=flat_baseline,
            margin_wins=gate_margin,
        ),
        "mature_vs_host_paired": _phase41_paired_outcome_table(
            mature_eval,
            host_eval,
            margin_wins=gate_margin,
            label=f"{rung}_host_plus_mature_vs_host_alone",
        ),
        "live_vs_host_paired": _phase41_paired_outcome_table(
            live_eval,
            host_eval,
            margin_wins=gate_margin,
            label=f"{rung}_host_plus_all_live_vs_host_alone",
        ),
        "mature_minus_host_wins": int(mature_eval["wins"]) - int(host_eval["wins"]),
        "live_minus_host_wins": int(live_eval["wins"]) - int(host_eval["wins"]),
    }


def _wilson_local(wins: int, total: int) -> list[float]:
    if total <= 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    p = wins / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = z * ((p * (1 - p) + z * z / (4 * total)) / total) ** 0.5 / denom
    return [center - half, center + half]


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


def _phase40_acceptance_delta_pass(
    delta: Mapping[str, Any],
    *,
    endpoint_non_regression: bool,
) -> bool:
    if int(delta.get("delta_wins", 0)) < 0:
        return False
    if not endpoint_non_regression:
        return True
    endpoint_deltas = delta.get("endpoint_deltas", {})
    return all(int(endpoint_deltas.get(endpoint, 0)) <= 0 for endpoint in _PHASE40_HARD_ENDPOINTS)


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


def _phase41_paired_gate_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    for row in per_seed:
        gate_items: list[tuple[str, Mapping[str, Any]]] = []
        for rung_name in ("stage_a", "stage_b"):
            rung = row.get(rung_name)
            if isinstance(rung, Mapping):
                gate_items.append((rung_name, rung.get("gate", {})))
        regression_gate = (
            row.get("regression_checks", {})
            .get("stage_a_after_stage_b", {})
            .get("gate", {})
            if isinstance(row.get("regression_checks"), Mapping)
            else {}
        )
        if regression_gate:
            gate_items.append(("stage_a_regression_after_stage_b", regression_gate))
        for rung_name, gate in gate_items:
            paired = gate.get("paired_gate", {})
            table.append(
                {
                    "seed": int(row["seed"]),
                    "flat_seed": int(row["flat_seed"]),
                    "rung": str(gate.get("rung", rung_name)),
                    "passed": bool(gate.get("passed", False)),
                    "wins": int(gate.get("wins", 0)),
                    "baseline_wins": int(gate.get("baseline_wins", 0)),
                    "left_minus_right_wins": int(paired.get("left_minus_right_wins", 0)),
                    "win_win": int(paired.get("win_win", 0)),
                    "win_loss": int(paired.get("win_loss", 0)),
                    "loss_win": int(paired.get("loss_win", 0)),
                    "loss_loss": int(paired.get("loss_loss", 0)),
                    "discordant_delta": int(paired.get("discordant_delta_left_minus_right", 0)),
                    "non_inferiority_margin_wins": int(paired.get("non_inferiority_margin_wins", 0)),
                    "non_inferior": bool(paired.get("non_inferior", False)),
                }
            )
    return table


def _phase41_flip_ply_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    for row in per_seed:
        for rung_name in ("stage_a", "stage_b"):
            training = row.get(rung_name, {}).get("training", {}) if isinstance(row.get(rung_name), Mapping) else {}
            if not training:
                continue
            table.append(
                {
                    "seed": int(row["seed"]),
                    "flat_seed": int(row["flat_seed"]),
                    "rung": rung_name,
                    "hard_fail_episode_count": int(training.get("hard_fail_episode_count", 0)),
                    "flip_ply_identified_count": int(training.get("flip_ply_identified_count", 0)),
                    "flip_ply_identification_rate": float(training.get("flip_ply_identification_rate", 0.0)),
                    "localized_negative_update_count": sum(
                        int(record.get("training", {}).get("localized_negative_update_count", 0))
                        for record in training.get("chunk_records", ())
                    ),
                    "fallback_negative_update_count": sum(
                        int(record.get("training", {}).get("fallback_negative_update_count", 0))
                        for record in training.get("chunk_records", ())
                    ),
                }
            )
    return table


def _phase42_headline_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    for row in per_seed:
        population = row.get("population", {})
        rescue = row.get("pruned_rescue_audit", {})
        ablation = row.get("post_hoc_ablation", {})
        stage_b_gates = row.get("stage_b", {}).get("ecology_gates", {}) if isinstance(row.get("stage_b"), Mapping) else {}
        stage_a_regression = (
            row.get("regression_checks", {}).get("stage_a_ecology_after_stage_b", {})
            if isinstance(row.get("regression_checks"), Mapping)
            else {}
        )
        table.append(
            {
                "seed": int(row["seed"]),
                "flat_seed": int(row["flat_seed"]),
                "stop_reasons": list(row.get("stop_reasons", ())),
                "mature_count": int(population.get("mature_count", 0)),
                "trial_count": int(population.get("trial_count", 0)),
                "pruned_count": int(population.get("pruned_count", 0)),
                "survivors_by_birth_segment": dict(population.get("survivors_by_birth_segment", {})),
                "birth_death_curve": [
                    {
                        "segment": curve.get("segment"),
                        "step": int(curve.get("step", 0)),
                        "trial": int(curve.get("trial", 0)),
                        "mature": int(curve.get("mature", 0)),
                        "pruned": int(curve.get("pruned", 0)),
                        "alive_total": int(curve.get("alive_total", 0)),
                    }
                    for curve in row.get("birth_death_curve", ())
                ],
                "load_bearing_mature": int(ablation.get("load_bearing_count", 0)),
                "inert_mature": int(ablation.get("inert_count", 0)),
                "harmful_mature": int(ablation.get("harmful_count", 0)),
                "helpful_pruned": int(rescue.get("load_bearing_but_pruned_count", 0)),
                "stage_b_host_plus_mature_wins": _phase42_nested_int(stage_b_gates, ("mature_eval", "wins")),
                "stage_b_host_wins": _phase42_nested_int(row.get("stage_b", {}), ("host_gate", "wins")),
                "stage_b_mature_minus_host": int(stage_b_gates.get("mature_minus_host_wins", 0)) if stage_b_gates else None,
                "stage_b_live_minus_host": int(stage_b_gates.get("live_minus_host_wins", 0)) if stage_b_gates else None,
                "stage_b_mature_gate_pass": _phase42_nested_bool(stage_b_gates, ("mature_vs_flat_gate", "passed")),
                "stage_b_live_gate_pass": _phase42_nested_bool(stage_b_gates, ("live_vs_flat_gate", "passed")),
                "stage_a_regression_mature_gate_pass": _phase42_nested_bool(stage_a_regression, ("mature_vs_flat_gate", "passed")),
                "stage_a_regression_live_gate_pass": _phase42_nested_bool(stage_a_regression, ("live_vs_flat_gate", "passed")),
            }
        )
    return table


def _phase43_headline_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    for row in per_seed:
        population = row.get("population", {})
        rescue = row.get("pruned_rescue_audit", {})
        ablation = row.get("post_hoc_ablation", {})
        stage_a = row.get("stage_a", {}) if isinstance(row.get("stage_a"), Mapping) else {}
        stage_b = row.get("stage_b", {}) if isinstance(row.get("stage_b"), Mapping) else {}
        stage_b_gates = stage_b.get("ecology_gates", {}) if isinstance(stage_b, Mapping) else {}
        table.append(
            {
                "seed": int(row["seed"]),
                "flat_seed": int(row["flat_seed"]),
                "stop_reasons": list(row.get("stop_reasons", ())),
                "stage_a_choice_changed_rate": _phase43_choice_change_rate(stage_a.get("ecology_training", {})),
                "stage_b_choice_changed_rate": _phase43_choice_change_rate(stage_b.get("ecology_training", {})),
                "mature_count": int(population.get("mature_count", 0)),
                "trial_count": int(population.get("trial_count", 0)),
                "pruned_count": int(population.get("pruned_count", 0)),
                "births_blocked_by_capacity": int(population.get("births_blocked_by_capacity_total", 0)),
                "stage_a_population_stable": _phase42_nested_bool(stage_a, ("population_stability", "stable")),
                "stage_b_population_stable": _phase42_nested_bool(stage_b, ("population_stability", "stable")),
                "birth_death_curve": [
                    {
                        "segment": curve.get("segment"),
                        "step": int(curve.get("step", 0)),
                        "trial": int(curve.get("trial", 0)),
                        "mature": int(curve.get("mature", 0)),
                        "pruned": int(curve.get("pruned", 0)),
                        "alive_total": int(curve.get("alive_total", 0)),
                    }
                    for curve in row.get("birth_death_curve", ())
                ],
                "load_bearing_mature": int(ablation.get("load_bearing_count", 0)),
                "inert_mature": int(ablation.get("inert_count", 0)),
                "harmful_mature": int(ablation.get("harmful_count", 0)),
                "helpful_pruned": int(rescue.get("load_bearing_but_pruned_count", 0)),
                "stage_b_host_plus_mature_wins": _phase42_nested_int(stage_b_gates, ("mature_eval", "wins")),
                "stage_b_host_wins": _phase42_nested_int(stage_b, ("host_gate", "wins")),
                "stage_b_mature_minus_host": int(stage_b_gates.get("mature_minus_host_wins", 0)) if stage_b_gates else None,
                "stage_b_live_minus_host": int(stage_b_gates.get("live_minus_host_wins", 0)) if stage_b_gates else None,
                "top_alive": list(population.get("top_alive", ())),
            }
        )
    return table


def _phase43_choice_change_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in per_seed:
        segments = [
            ("foundation", row.get("foundation_ecology_training", {})),
        ]
        stage_a = row.get("stage_a", {}) if isinstance(row.get("stage_a"), Mapping) else {}
        stage_b = row.get("stage_b", {}) if isinstance(row.get("stage_b"), Mapping) else {}
        segments.append(("stage_a", stage_a.get("ecology_training", {})))
        segments.append(("stage_b", stage_b.get("ecology_training", {})))
        for segment_name, training in segments:
            if not isinstance(training, Mapping) or not training:
                continue
            rows.append(
                {
                    "seed": int(row["seed"]),
                    "flat_seed": int(row["flat_seed"]),
                    "segment": segment_name,
                    "decision_ply_count": int(training.get("decision_ply_count", 0)),
                    "choice_changed_ply_count": int(training.get("choice_changed_ply_count", 0)),
                    "choice_changed_ply_rate": float(training.get("choice_changed_ply_rate", 0.0)),
                    "changed_choice_outcome_distribution": dict(
                        training.get("changed_choice_outcome_distribution", {})
                    ),
                    "changed_choice_endpoint_distribution": dict(
                        training.get("changed_choice_endpoint_distribution", {})
                    ),
                    "responsible_cell_credit_event_count": int(
                        training.get("responsible_cell_credit_event_count", 0)
                    ),
                    "requested_composite_count": int(training.get("requested_composite_count", 0)),
                    "active_composite_count": int(training.get("active_composite_count", 0)),
                    "births_blocked_by_capacity_delta": int(
                        training.get("births_blocked_by_capacity_delta", 0)
                    ),
                    "births_blocked_by_capacity_total": int(
                        training.get("births_blocked_by_capacity_total", 0)
                    ),
                }
            )
    return rows


def _phase44_headline_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    for row in per_seed:
        population = row.get("population", {})
        rescue = row.get("pruned_rescue_audit", {})
        ablation = row.get("post_hoc_ablation", {})
        stage_a = row.get("stage_a", {}) if isinstance(row.get("stage_a"), Mapping) else {}
        stage_b = row.get("stage_b", {}) if isinstance(row.get("stage_b"), Mapping) else {}
        stage_b_gates = stage_b.get("ecology_gates", {}) if isinstance(stage_b, Mapping) else {}
        stage_a_training = stage_a.get("ecology_training", {}) if isinstance(stage_a, Mapping) else {}
        stage_b_training = stage_b.get("ecology_training", {}) if isinstance(stage_b, Mapping) else {}
        table.append(
            {
                "seed": int(row["seed"]),
                "flat_seed": int(row["flat_seed"]),
                "stop_reasons": list(row.get("stop_reasons", ())),
                "stage_a_auditions_per_cell_mean": _phase42_nested_float(stage_a_training, ("auditions_per_cell_distribution", "mean")),
                "stage_b_auditions_per_cell_mean": _phase42_nested_float(stage_b_training, ("auditions_per_cell_distribution", "mean")),
                "stage_a_verdict_counts": dict(stage_a_training.get("audition_verdict_counts", {})) if isinstance(stage_a_training, Mapping) else {},
                "stage_b_verdict_counts": dict(stage_b_training.get("audition_verdict_counts", {})) if isinstance(stage_b_training, Mapping) else {},
                "stage_a_audition_frames": int(stage_a_training.get("audition_frames_spent", 0)) if isinstance(stage_a_training, Mapping) else 0,
                "stage_b_audition_frames": int(stage_b_training.get("audition_frames_spent", 0)) if isinstance(stage_b_training, Mapping) else 0,
                "mature_count": int(population.get("mature_count", 0)),
                "trial_count": int(population.get("trial_count", 0)),
                "pruned_count": int(population.get("pruned_count", 0)),
                "births_blocked_by_capacity": int(population.get("births_blocked_by_capacity_total", 0)),
                "stage_a_population_stable": _phase42_nested_bool(stage_a, ("population_stability", "stable")),
                "stage_b_population_stable": _phase42_nested_bool(stage_b, ("population_stability", "stable")),
                "birth_death_curve": [
                    {
                        "segment": curve.get("segment"),
                        "step": int(curve.get("step", 0)),
                        "trial": int(curve.get("trial", 0)),
                        "mature": int(curve.get("mature", 0)),
                        "pruned": int(curve.get("pruned", 0)),
                        "alive_total": int(curve.get("alive_total", 0)),
                    }
                    for curve in row.get("birth_death_curve", ())
                ],
                "load_bearing_mature": int(ablation.get("load_bearing_count", 0)),
                "inert_mature": int(ablation.get("inert_count", 0)),
                "harmful_mature": int(ablation.get("harmful_count", 0)),
                "helpful_pruned": int(rescue.get("load_bearing_but_pruned_count", 0)),
                "stage_b_host_plus_mature_wins": _phase42_nested_int(stage_b_gates, ("mature_eval", "wins")),
                "stage_b_host_wins": _phase42_nested_int(stage_b, ("host_gate", "wins")),
                "stage_b_mature_minus_host": int(stage_b_gates.get("mature_minus_host_wins", 0)) if stage_b_gates else None,
                "top_alive": list(population.get("top_alive", ())),
            }
        )
    return table


def _phase44_audition_signal_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in per_seed:
        segments = [
            ("foundation", row.get("foundation_ecology_training", {})),
        ]
        stage_a = row.get("stage_a", {}) if isinstance(row.get("stage_a"), Mapping) else {}
        stage_b = row.get("stage_b", {}) if isinstance(row.get("stage_b"), Mapping) else {}
        segments.append(("stage_a", stage_a.get("ecology_training", {})))
        segments.append(("stage_b", stage_b.get("ecology_training", {})))
        for segment_name, training in segments:
            if not isinstance(training, Mapping) or not training:
                continue
            rows.append(
                {
                    "seed": int(row["seed"]),
                    "flat_seed": int(row["flat_seed"]),
                    "segment": segment_name,
                    "decision_ply_count": int(training.get("decision_ply_count", 0)),
                    "choice_changed_ply_rate": float(training.get("choice_changed_ply_rate", 0.0)),
                    "trial_cell_proposal_count": int(training.get("trial_cell_proposal_count", 0)),
                    "disagreement_ply_count": int(training.get("disagreement_ply_count", 0)),
                    "disagreement_ply_rate": float(training.get("disagreement_ply_rate", 0.0)),
                    "audition_request_count": int(training.get("audition_request_count", 0)),
                    "audition_count": int(training.get("audition_count", 0)),
                    "auditions_per_cell_distribution": dict(
                        training.get("auditions_per_cell_distribution", {})
                    ),
                    "audition_verdict_counts": dict(training.get("audition_verdict_counts", {})),
                    "audition_verdict_rates": dict(training.get("audition_verdict_rates", {})),
                    "audition_verdict_reason_counts": dict(
                        training.get("audition_verdict_reason_counts", {})
                    ),
                    "audition_frames_spent": int(training.get("audition_frames_spent", 0)),
                    "scheduled_audition_stats": dict(training.get("scheduled_audition_stats", {})),
                    "pool_supply_stats": dict(training.get("pool_supply_stats", {})),
                    "court_throughput_per_chunk": int(training.get("court_throughput_per_chunk", 0)),
                    "scheduled_coverage": dict(training.get("scheduled_coverage", {})),
                    "complete_flush": dict(training.get("complete_flush", {})),
                    "backlog_curve": list(training.get("backlog_curve", ())),
                    "births_deferred_by_backlog_total": int(
                        training.get("births_deferred_by_backlog_total", 0)
                    ),
                    "births_deferred_by_backlog_by_trigger": dict(
                        training.get("births_deferred_by_backlog_by_trigger", {})
                    ),
                    "births_deferred_by_backlog_by_parent": dict(
                        training.get("births_deferred_by_backlog_by_parent", {})
                    ),
                    "births_deferred_by_count_homeostasis_total": int(
                        training.get("births_deferred_by_count_homeostasis_total", 0)
                    ),
                    "births_deferred_by_count_homeostasis_by_trigger": dict(
                        training.get("births_deferred_by_count_homeostasis_by_trigger", {})
                    ),
                    "births_deferred_by_count_homeostasis_by_reason": dict(
                        training.get("births_deferred_by_count_homeostasis_by_reason", {})
                    ),
                    "audition_cap_skip_count": int(training.get("audition_cap_skip_count", 0)),
                    "audition_budget_skip_count": int(training.get("audition_budget_skip_count", 0)),
                    "births_blocked_by_capacity_delta": int(
                        training.get("births_blocked_by_capacity_delta", 0)
                    ),
                    "births_blocked_by_capacity_total": int(
                        training.get("births_blocked_by_capacity_total", 0)
                    ),
                }
            )
    return rows


def _phase46_headline_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    table = _phase44_headline_table(per_seed)
    by_seed = {int(row["seed"]): row for row in table}
    for row in per_seed:
        seed = int(row["seed"])
        target = by_seed.get(seed)
        if target is None:
            continue
        stage_a = row.get("stage_a", {}) if isinstance(row.get("stage_a"), Mapping) else {}
        stage_b = row.get("stage_b", {}) if isinstance(row.get("stage_b"), Mapping) else {}
        stage_a_training = stage_a.get("ecology_training", {}) if isinstance(stage_a, Mapping) else {}
        stage_b_training = stage_b.get("ecology_training", {}) if isinstance(stage_b, Mapping) else {}
        family_counts = Counter(
            _phase46_composite_family(item.get("children", ()))
            for item in row.get("candidate_fate_log", ())
            if item.get("state") == "MATURE"
        )
        target.update(
            {
                "stage_a_backlog_curve": list(stage_a_training.get("backlog_curve", ())),
                "stage_b_backlog_curve": list(stage_b_training.get("backlog_curve", ())),
                "stage_a_complete_flush": dict(stage_a_training.get("complete_flush", {})),
                "stage_b_complete_flush": dict(stage_b_training.get("complete_flush", {})),
                "stage_a_births_deferred_by_backlog": int(
                    stage_a_training.get("births_deferred_by_backlog_total", 0)
                ),
                "stage_b_births_deferred_by_backlog": int(
                    stage_b_training.get("births_deferred_by_backlog_total", 0)
                ),
                "mature_family_counts": dict(sorted(family_counts.items())),
            }
        )
    return table


def _phase47_headline_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    table = _phase46_headline_table(per_seed)
    by_seed = {int(row["seed"]): row for row in table}
    for row in per_seed:
        seed = int(row["seed"])
        target = by_seed.get(seed)
        if target is None:
            continue
        stage_a = row.get("stage_a", {}) if isinstance(row.get("stage_a"), Mapping) else {}
        stage_b = row.get("stage_b", {}) if isinstance(row.get("stage_b"), Mapping) else {}
        stage_a_training = stage_a.get("ecology_training", {}) if isinstance(stage_a, Mapping) else {}
        stage_b_training = stage_b.get("ecology_training", {}) if isinstance(stage_b, Mapping) else {}
        fate = list(row.get("candidate_fate_log", ()))
        prune_reasons = Counter(str(item.get("prune_reason")) for item in fate if item.get("state") == "PRUNED")
        target.update(
            {
                "stage_a_pool_supply_stats": dict(stage_a_training.get("pool_supply_stats", {})),
                "stage_b_pool_supply_stats": dict(stage_b_training.get("pool_supply_stats", {})),
                "stage_a_court_throughput_per_chunk": int(
                    stage_a_training.get("court_throughput_per_chunk", 0)
                ),
                "stage_b_court_throughput_per_chunk": int(
                    stage_b_training.get("court_throughput_per_chunk", 0)
                ),
                "stage_a_births_deferred_by_count_homeostasis": int(
                    stage_a_training.get("births_deferred_by_count_homeostasis_total", 0)
                ),
                "stage_b_births_deferred_by_count_homeostasis": int(
                    stage_b_training.get("births_deferred_by_count_homeostasis_total", 0)
                ),
                "prune_reason_counts": dict(sorted(prune_reasons.items())),
            }
        )
    return table


def _phase42_acceptance_margin_table(per_seed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in per_seed:
        for stage_name in ("stage_a", "stage_b"):
            stage = row.get(stage_name)
            if not isinstance(stage, Mapping):
                continue
            training = stage.get("host_training", {})
            if not training:
                continue
            chunk_records = list(training.get("chunk_records", ()))
            accepted_deltas = [
                int(record.get("validation_paired", {}).get("discordant_delta_left_minus_right", 0))
                for record in chunk_records
                if bool(record.get("accepted"))
            ]
            rejected_deltas = [
                int(record.get("validation_paired", {}).get("discordant_delta_left_minus_right", 0))
                for record in chunk_records
                if not bool(record.get("accepted"))
            ]
            rows.append(
                {
                    "seed": int(row["seed"]),
                    "flat_seed": int(row["flat_seed"]),
                    "rung": stage_name,
                    "chunks_consolidated": int(training.get("chunks_consolidated", 0)),
                    "chunks_rejected": int(training.get("chunks_rejected", 0)),
                    "accepted_validation_discordant_deltas": accepted_deltas,
                    "rejected_validation_discordant_deltas": rejected_deltas,
                    "min_accepted_delta": None if not accepted_deltas else min(accepted_deltas),
                    "max_rejected_delta": None if not rejected_deltas else max(rejected_deltas),
                    "hard_fail_flip_identification_rate": float(training.get("flip_ply_identification_rate", 0.0)),
                }
            )
    return rows


def _phase42_cross_rung_load_bearing_survivors(seed_results: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for seed, result in seed_results.items():
        for row in result.get("post_hoc_ablation", {}).get("records", []):
            if row.get("birth_segment") not in {"foundation_mate1_mate2", "stage_a_approach"}:
                continue
            if row.get("classification") != "load_bearing":
                continue
            records.append(
                {
                    "seed": int(seed),
                    "composite_id": str(row.get("composite_id")),
                    "birth_segment": str(row.get("birth_segment")),
                    "ablation_delta": int(row.get("ablation_delta", 0)),
                    "children": list(row.get("children", ())),
                }
            )
    return records


def _phase42_nested_int(row: Mapping[str, Any], path: Sequence[str]) -> int | None:
    current: Any = row
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return int(current)


def _phase42_nested_float(row: Mapping[str, Any], path: Sequence[str]) -> float | None:
    current: Any = row
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return float(current)


def _phase42_nested_bool(row: Mapping[str, Any], path: Sequence[str]) -> bool | None:
    current: Any = row
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return bool(current)
