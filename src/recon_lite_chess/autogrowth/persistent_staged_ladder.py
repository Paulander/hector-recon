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
    _GraphNativeCompositeRuntime,
    _MigratedStageBFlatGraphScoreProvider,
    _NativeFoundationScoreProvider,
    _approach_waypoint_success,
    _choose_migrated_flat_host_move,
    _decision_context,
    _design_spec,
    _foundation_ecology_rows,
    _legal_without_third_repetition,
    _load_weight_table,
    _new_judge_cache,
    _phase32_real_recurring_mature_composites,
    _real_native_ablation_health,
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
    _position_repetition_key,
    _rollout_policy,
    _score_options,
    _sealed_action_key_scales,
    _train_native_foundation_for_ecology,
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
) -> dict[str, Any]:
    disabled = _phase42_disabled_non_mature(runtime) if mature_only else set()
    endpoints: Counter[str] = Counter()
    success_by_row: dict[str, bool] = {}
    endpoint_by_row: dict[str, str] = {}
    active_by_row: dict[str, list[str]] = {}
    all_active: set[str] = set()
    samples: list[dict[str, Any]] = []
    judge_cache = _new_judge_cache()
    for index, row in enumerate(rows):
        row_active: set[str] = set()

        def choose(board: chess.Board, counts: Mapping[Any, int], row_id: int, ply: int, rng: random.Random) -> chess.Move | None:
            selected = runtime.choose_move(
                board,
                counts,
                score_provider,
                seed=int(seed) + int(row_id) * 47 + ply,
                disabled=disabled,
            )
            row_active.update(map(str, selected.get("active_composite_ids", ())))
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


def _phase42_nested_bool(row: Mapping[str, Any], path: Sequence[str]) -> bool | None:
    current: Any = row
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return bool(current)
